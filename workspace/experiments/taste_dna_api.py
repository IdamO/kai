#!/usr/bin/env python3
"""
Taste DNA API — FastAPI endpoint for taste profiling.

Wraps taste_dna_experiment.py pipeline as an HTTP service.
Runs locally from cached data (no external drives needed after cache build).

Usage:
    uvicorn taste_dna_api:app --host 0.0.0.0 --port 8899 --reload

Endpoints:
    POST /api/dna           — Generate taste DNA from track IDs or Last.fm username
    GET  /api/dna/presets   — List available presets (idam, etc.)
    GET  /health            — Health check
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from taste_dna_experiment import (
    DataSources,
    Discovery,
    FEATURE_DESCRIPTORS,
    FEATURE_LABELS,
    PRESET_IDAM,
    TasteDNA,
    compute_taste_dna,
    describe_sonic_identity,
    discover_als_neighbors,
    discover_audio_knn,
    discover_bridge_tracks,
    discover_mert_neighbors,
    fetch_lastfm_top_tracks,
    infer_mood,
    resolve_lastfm_tracks,
    resolve_tracks,
    resolve_tracks_by_name,
    _build_rowid_to_sid_map,
)

# ---------------------------------------------------------------------------
# Global data (loaded once at startup, shared across requests)
# ---------------------------------------------------------------------------
_ds: Optional[DataSources] = None
_rowid_to_sid: Optional[dict] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ds, _rowid_to_sid
    print("[taste-dna-api] Loading data sources...")
    t0 = time.time()
    _ds = DataSources()
    # Force-load catalog + vectors into memory
    _ = _ds.catalog
    _ = _ds.audio_features
    _ = _ds.mert_vectors
    _ = _ds.mert_index
    _ = _ds.als_vectors
    _ = _ds.als_index
    _ = _ds.bridge_weights
    _rowid_to_sid = _build_rowid_to_sid_map(_ds)
    print(f"[taste-dna-api] Ready in {time.time() - t0:.1f}s "
          f"({len(_ds.catalog)} tracks, {_ds.mert_vectors.shape[0]} MERT, "
          f"{_ds.als_vectors.shape[0]} ALS)")
    yield
    if _ds:
        _ds.close()
    print("[taste-dna-api] Shut down.")


app = FastAPI(
    title="Kyma Taste DNA",
    description="Taste profiling and music discovery from your listening history",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP — tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class DNARequest(BaseModel):
    """Request body for taste DNA generation."""
    track_ids: Optional[list[str]] = Field(None, description="Spotify track IDs")
    track_names: Optional[list[str]] = Field(None, description="Track names to fuzzy-match")
    lastfm_username: Optional[str] = Field(None, description="Last.fm username")
    lastfm_period: str = Field("overall", description="Last.fm period: overall, 7day, 1month, 3month, 6month, 12month")
    lastfm_limit: int = Field(50, ge=5, le=200, description="Number of Last.fm tracks to fetch")
    preset: Optional[str] = Field(None, description="Use a preset track list (e.g. 'idam')")
    include_mashups: bool = Field(False, description="Generate mashup audio (slower)")
    discovery_count: int = Field(10, ge=0, le=30, description="Total discovery tracks to return")


class TrackInfo(BaseModel):
    name: str
    artist: str
    spotify_id: str
    has_mert: bool
    has_als: bool
    has_audio: bool


class DiscoveryInfo(BaseModel):
    track_name: str
    artist: str
    album: str
    spotify_id: str
    preview_url: Optional[str]
    algorithm: str
    score: float
    reason: str
    popularity: int


class DNAResponse(BaseModel):
    # User profile
    tracks_analyzed: int
    tracks_in_mert: int
    tracks_in_als: int
    tracks_with_audio: int
    top_genres: list[str]
    edge_genres: list[str]
    audio_centroid: dict
    audio_stddev: dict
    deviation_profile: dict
    sonic_identity: str
    moods: list[str]
    feature_labels: dict
    tracks: list[TrackInfo]

    # Discoveries
    discoveries: list[DiscoveryInfo]

    # Agent narrative
    agent_briefing: str

    # Metadata
    query_time_ms: int
    input_source: str


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

PRESETS = {
    "idam": PRESET_IDAM,
}


def _build_agent_briefing(dna: TasteDNA, discoveries: list[Discovery]) -> str:
    """Generate the agent narrative text."""
    mert_disc = [d for d in discoveries if d.algorithm == "mert"]
    als_disc = [d for d in discoveries if d.algorithm == "als"]
    bridge_disc = [d for d in discoveries if d.algorithm == "bridge"]
    audio_disc = [d for d in discoveries if d.algorithm == "audio_knn"]

    identity = describe_sonic_identity(dna)
    moods = infer_mood(dna.audio_centroid)

    parts = []
    parts.append(f"Your taste agent scanned {dna.n_total} of your tracks across "
                 f"3 signal layers and {len(_ds.catalog):,} candidates. "
                 f"Your sonic identity: {identity}.")

    if mert_disc:
        names = ", ".join(f'"{d.track_name}" by {d.artist}' for d in mert_disc)
        parts.append(f"DEEP LISTENING: I analyzed the sonic DNA of your music. "
                     f"I found {names}. These tracks share your sonic signature "
                     f"in ways a playlist algorithm would never catch.")

    if als_disc:
        names = ", ".join(f'"{d.track_name}" by {d.artist}' for d in als_disc)
        parts.append(f"TASTE GRAPH: I traced the listening patterns of people who "
                     f"share your DNA across 1.7 billion playlist connections. "
                     f"They led me to {names}.")

    if bridge_disc:
        names = ", ".join(f'"{d.track_name}" by {d.artist}' for d in bridge_disc)
        mood_str = " and ".join(moods[:2]) if moods else "your sound"
        genre_bridge = ""
        if dna.top_genres and len(dna.top_genres) >= 2:
            genre_bridge = f" between {dna.top_genres[0]} and {dna.edge_genres[0]}" if dna.edge_genres else ""
        parts.append(f"GENRE BRIDGES: I found tracks sitting at the boundary{genre_bridge} "
                     f"-- {mood_str} energy that connects worlds in your taste -- {names}.")

    if audio_disc:
        top_dev = sorted(dna.deviation_profile.items(), key=lambda x: abs(x[1]), reverse=True)
        if top_dev:
            feat, z = top_dev[0]
            direction = "high" if z > 0 else "low"
            descriptor = FEATURE_DESCRIPTORS.get((feat, direction), feat)
            label = FEATURE_LABELS.get(feat, feat)
            parts.append(f"SONIC MATCH: Your ears are unusually tuned to {label.lower()} -- "
                         f"a {descriptor} sensibility that sets you apart. "
                         f"I weighted my search by what makes YOU different.")

    parts.append("I'm still hunting. Check back tomorrow.")
    return "\n\n".join(parts)


def _run_pipeline(req: DNARequest) -> DNAResponse:
    """Execute the full taste DNA pipeline."""
    t0 = time.time()

    # Determine input source and resolve tracks
    if req.preset and req.preset in PRESETS:
        track_ids = PRESETS[req.preset]
        tracks = resolve_tracks(track_ids, _ds)
        source = f"preset:{req.preset}"
    elif req.lastfm_username:
        lfm_tracks = fetch_lastfm_top_tracks(
            req.lastfm_username, period=req.lastfm_period, limit=req.lastfm_limit
        )
        if not lfm_tracks:
            raise HTTPException(status_code=404, detail=f"No tracks found for Last.fm user '{req.lastfm_username}'")
        tracks = resolve_lastfm_tracks(lfm_tracks, _ds)
        source = f"lastfm:{req.lastfm_username}"
    elif req.track_ids:
        tracks = resolve_tracks(req.track_ids, _ds)
        source = "track_ids"
    elif req.track_names:
        tracks = resolve_tracks_by_name(req.track_names, _ds)
        source = "track_names"
    else:
        raise HTTPException(status_code=400, detail="Provide track_ids, track_names, lastfm_username, or preset")

    if len(tracks) < 3:
        raise HTTPException(status_code=422, detail=f"Need at least 3 resolved tracks, got {len(tracks)}")

    # Compute taste DNA
    dna = compute_taste_dna(tracks, _ds)

    # Build exclusion sets (don't recommend what they already listen to)
    exclude_rowids = {t.rowid for t in tracks}
    exclude_artists = {a.lower() for t in tracks for a in t.artists}

    # Run discovery algorithms (allocate slots proportionally)
    n_total = req.discovery_count
    n_mert = max(1, n_total // 4)
    n_als = max(1, n_total // 4)
    n_bridge = max(1, n_total // 4)
    n_audio = n_total - n_mert - n_als - n_bridge

    discoveries = []
    discoveries.extend(discover_mert_neighbors(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_mert))
    discoveries.extend(discover_als_neighbors(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_als))
    discoveries.extend(discover_bridge_tracks(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_bridge))
    discoveries.extend(discover_audio_knn(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_audio))

    briefing = _build_agent_briefing(dna, discoveries)
    identity = describe_sonic_identity(dna)
    moods = infer_mood(dna.audio_centroid)

    elapsed_ms = int((time.time() - t0) * 1000)

    return DNAResponse(
        tracks_analyzed=len(tracks),
        tracks_in_mert=dna.n_with_mert,
        tracks_in_als=dna.n_with_als,
        tracks_with_audio=dna.n_with_audio,
        top_genres=dna.top_genres,
        edge_genres=dna.edge_genres,
        audio_centroid={k: round(v, 4) for k, v in dna.audio_centroid.items()},
        audio_stddev={k: round(v, 4) for k, v in dna.audio_stddev.items()},
        deviation_profile={k: round(v, 3) for k, v in dna.deviation_profile.items()},
        sonic_identity=identity,
        moods=moods,
        feature_labels=FEATURE_LABELS,
        tracks=[
            TrackInfo(
                name=t.name,
                artist=", ".join(t.artists),
                spotify_id=t.spotify_id,
                has_mert=t.mert_idx is not None,
                has_als=t.als_idx is not None,
                has_audio=t.audio_features is not None,
            )
            for t in tracks
        ],
        discoveries=[
            DiscoveryInfo(
                track_name=d.track_name,
                artist=d.artist,
                album=d.album,
                spotify_id=d.spotify_id,
                preview_url=d.preview_url,
                algorithm=d.algorithm,
                score=d.score,
                reason=d.reason,
                popularity=d.popularity,
            )
            for d in discoveries
        ],
        agent_briefing=briefing,
        query_time_ms=elapsed_ms,
        input_source=source,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/dna", response_model=DNAResponse)
async def generate_dna(req: DNARequest):
    """
    Generate a Taste DNA profile.

    Provide one of: track_ids, track_names, lastfm_username, or preset.
    Returns taste profile, discoveries, and agent narrative.

    Example:
        curl -X POST http://localhost:8899/api/dna \\
          -H "Content-Type: application/json" \\
          -d '{"lastfm_username": "rj", "lastfm_limit": 50}'
    """
    return _run_pipeline(req)


@app.get("/api/dna/presets")
async def list_presets():
    """List available preset track lists."""
    return {
        name: {"track_count": len(ids), "track_ids": ids}
        for name, ids in PRESETS.items()
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "catalog_size": len(_ds.catalog) if _ds else 0,
        "mert_tracks": _ds.mert_vectors.shape[0] if _ds else 0,
        "als_tracks": _ds.als_vectors.shape[0] if _ds else 0,
    }
