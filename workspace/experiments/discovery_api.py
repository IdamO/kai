#!/usr/bin/env python3
"""
Bath Playlist Agent — Discovery API

No profiles. No deviation charts. No signaling.
Takes listening history, returns discoveries paired with trust anchors.

Each discovery comes with a "trust anchor" — a track from the user's own
library that connects to the discovery. The pairing is the compressed taste
signal: "you love X, so here's Y, and here's why they're connected."

The mashup of anchor + discovery is the preview asymmetry solver:
30-90s evaluation compressed to 15s.

Usage:
    uvicorn discovery_api:app --host 0.0.0.0 --port 8899 --reload

Endpoints:
    POST /api/discover       — Get discoveries with trust anchors
    GET  /health             — Health check
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from numpy.linalg import norm
from pydantic import BaseModel, Field

from taste_dna_experiment import (
    DataSources,
    Discovery,
    ResolvedTrack,
    TasteDNA,
    compute_taste_dna,
    discover_als_neighbors,
    discover_audio_knn,
    discover_bridge_tracks,
    discover_mert_neighbors,
    fetch_lastfm_top_tracks,
    resolve_lastfm_tracks,
    resolve_tracks,
    resolve_tracks_by_name,
    _build_rowid_to_sid_map,
    PRESET_IDAM,
    AUDIO_CONTINUOUS_FEATURES,
)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_ds: Optional[DataSources] = None
_rowid_to_sid: Optional[dict] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ds, _rowid_to_sid
    print("[discovery] Loading data sources...")
    t0 = time.time()
    _ds = DataSources()
    _ = _ds.catalog
    _ = _ds.audio_features
    _ = _ds.mert_vectors
    _ = _ds.mert_index
    _ = _ds.als_vectors
    _ = _ds.als_index
    _ = _ds.bridge_weights
    _rowid_to_sid = _build_rowid_to_sid_map(_ds)
    print(f"[discovery] Ready in {time.time() - t0:.1f}s "
          f"({len(_ds.catalog)} tracks)")
    yield
    if _ds:
        _ds.close()


app = FastAPI(
    title="Kyma Discovery Agent",
    description="Music you'll love. No profiles, no charts, no signaling.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class DiscoverRequest(BaseModel):
    track_ids: Optional[list[str]] = Field(None, description="Spotify track IDs")
    track_names: Optional[list[str]] = Field(None, description="Track names to fuzzy-match")
    lastfm_username: Optional[str] = Field(None, description="Last.fm username")
    lastfm_period: str = Field("overall", description="Last.fm time period")
    lastfm_limit: int = Field(50, ge=5, le=200)
    preset: Optional[str] = Field(None, description="Preset track list")
    count: int = Field(10, ge=1, le=30, description="Number of discoveries")


class TrustAnchor(BaseModel):
    """A track from the user's library that connects to the discovery."""
    name: str
    artist: str
    spotify_id: str
    connection: str  # why this anchor connects to the discovery


class DiscoveryItem(BaseModel):
    """A discovered track paired with its trust anchor."""
    track_name: str
    artist: str
    album: str
    spotify_id: str
    preview_url: Optional[str]
    anchor: TrustAnchor
    algorithm: str
    score: float


class DiscoverResponse(BaseModel):
    discoveries: list[DiscoveryItem]
    query_time_ms: int


# ---------------------------------------------------------------------------
# Trust anchor selection
# ---------------------------------------------------------------------------

def _find_trust_anchor(
    discovery: Discovery,
    user_tracks: list[ResolvedTrack],
    ds: DataSources,
) -> TrustAnchor:
    """Find the user's track most connected to a discovery.

    Strategy by algorithm:
    - MERT (deep listening): highest cosine similarity in embedding space.
    - ALS (taste graph): highest cosine similarity in collaborative space.
    - Bridge: similar energy/mood but different genre — the bridge.
    - Audio KNN / fallback: closest audio features.
    """
    best_track = None
    best_score = -1.0
    connection = ""

    disc_sid = discovery.spotify_id
    disc_info = ds.catalog.get(disc_sid)
    disc_rowid = disc_info["rowid"] if disc_info else None

    if discovery.algorithm == "mert":
        disc_mert_pos = ds.mert_index.get(disc_rowid) if disc_rowid else None
        if disc_mert_pos is not None:
            disc_vec = ds.mert_vectors[disc_mert_pos]
            disc_vec = disc_vec / (norm(disc_vec) + 1e-10)
            for track in user_tracks:
                if track.mert_idx is None:
                    continue
                user_vec = ds.mert_vectors[track.mert_idx]
                user_vec = user_vec / (norm(user_vec) + 1e-10)
                sim = float(np.dot(user_vec, disc_vec))
                if sim > best_score:
                    best_score = sim
                    best_track = track
                    connection = "shares sonic DNA"

    elif discovery.algorithm == "als":
        disc_als_pos = ds.als_index.get(disc_rowid) if disc_rowid else None
        if disc_als_pos is not None:
            disc_vec = ds.als_vectors[disc_als_pos]
            disc_norm = norm(disc_vec)
            if disc_norm > 0:
                disc_vec = disc_vec / disc_norm
                for track in user_tracks:
                    if track.als_idx is None:
                        continue
                    user_vec = ds.als_vectors[track.als_idx]
                    user_norm = norm(user_vec)
                    if user_norm > 0:
                        sim = float(np.dot(user_vec / user_norm, disc_vec))
                        if sim > best_score:
                            best_score = sim
                            best_track = track
                            connection = "loved by the same listeners"

    elif discovery.algorithm == "bridge":
        disc_af = ds.audio_features.get(disc_sid, {})
        disc_energy = disc_af.get("energy", 0.5)
        disc_valence = disc_af.get("valence", 0.5)
        for track in user_tracks:
            if track.audio_features is None:
                continue
            user_energy = track.audio_features.get("energy", 0.5)
            user_valence = track.audio_features.get("valence", 0.5)
            mood_sim = 1.0 - abs(user_energy - disc_energy) * 0.5 - abs(user_valence - disc_valence) * 0.5
            if mood_sim > best_score:
                best_score = mood_sim
                best_track = track
                connection = "same energy, different world"

    # Audio KNN or fallback: closest audio features
    if best_track is None:
        disc_af = ds.audio_features.get(disc_sid, {})
        for track in user_tracks:
            if track.audio_features is None:
                continue
            dist = sum(
                (track.audio_features.get(f, 0) - disc_af.get(f, 0)) ** 2
                for f in AUDIO_CONTINUOUS_FEATURES
            ) ** 0.5
            sim = 1.0 / (1.0 + dist)
            if sim > best_score:
                best_score = sim
                best_track = track
                connection = "same sonic fingerprint"

    if best_track is None:
        best_track = user_tracks[0]
        connection = "from your collection"

    return TrustAnchor(
        name=best_track.name,
        artist=", ".join(best_track.artists),
        spotify_id=best_track.spotify_id,
        connection=connection,
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

PRESETS = {"idam": PRESET_IDAM}


def _run_discovery(req: DiscoverRequest) -> DiscoverResponse:
    t0 = time.time()

    # Resolve tracks
    if req.preset and req.preset in PRESETS:
        tracks = resolve_tracks(PRESETS[req.preset], _ds)
        source = f"preset:{req.preset}"
    elif req.lastfm_username:
        lfm = fetch_lastfm_top_tracks(req.lastfm_username, period=req.lastfm_period, limit=req.lastfm_limit)
        if not lfm:
            raise HTTPException(404, f"No tracks for Last.fm user '{req.lastfm_username}'")
        tracks = resolve_lastfm_tracks(lfm, _ds)
        source = f"lastfm:{req.lastfm_username}"
    elif req.track_ids:
        tracks = resolve_tracks(req.track_ids, _ds)
        source = "track_ids"
    elif req.track_names:
        tracks = resolve_tracks_by_name(req.track_names, _ds)
        source = "track_names"
    else:
        raise HTTPException(400, "Provide track_ids, track_names, lastfm_username, or preset")

    if len(tracks) < 3:
        raise HTTPException(422, f"Need at least 3 resolved tracks, got {len(tracks)}")

    # Compute taste (silently — no profile exposed)
    dna = compute_taste_dna(tracks, _ds)

    # Exclusion sets
    exclude_rowids = {t.rowid for t in tracks}
    exclude_artists = {a.lower() for t in tracks for a in t.artists}

    # Run all discovery algorithms
    n = req.count
    n_mert = max(1, n // 4)
    n_als = max(1, n // 4)
    n_bridge = max(1, n // 4)
    n_audio = n - n_mert - n_als - n_bridge

    raw_discoveries = []
    raw_discoveries.extend(discover_mert_neighbors(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_mert))
    raw_discoveries.extend(discover_als_neighbors(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_als))
    raw_discoveries.extend(discover_bridge_tracks(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_bridge))
    raw_discoveries.extend(discover_audio_knn(dna, _ds, exclude_rowids, exclude_artists, _rowid_to_sid, n=n_audio))

    # Pair each discovery with a trust anchor from user's library
    items = []
    for disc in raw_discoveries:
        anchor = _find_trust_anchor(disc, tracks, _ds)
        items.append(DiscoveryItem(
            track_name=disc.track_name,
            artist=disc.artist,
            album=disc.album,
            spotify_id=disc.spotify_id,
            preview_url=disc.preview_url,
            anchor=anchor,
            algorithm=disc.algorithm,
            score=disc.score,
        ))

    return DiscoverResponse(
        discoveries=items,
        query_time_ms=int((time.time() - t0) * 1000),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/discover", response_model=DiscoverResponse)
async def discover(req: DiscoverRequest):
    """
    Discover music you'll love.

    Each discovery is paired with a trust anchor — a track you already love
    that connects to the new one. The anchor is the bridge between your
    taste and the unknown.

    Example:
        curl -X POST http://localhost:8899/api/discover \\
          -H "Content-Type: application/json" \\
          -d '{"lastfm_username": "rj", "lastfm_limit": 50}'
    """
    return _run_discovery(req)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "catalog_size": len(_ds.catalog) if _ds else 0,
    }
