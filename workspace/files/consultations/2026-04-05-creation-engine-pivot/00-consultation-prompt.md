# Strategic Consultation: Model Pipeline Direction for Music Curation x Creation Product

## Context

A startup (2 founders, pre-seed, incorporated March 2026) is building a consumer music product. The core thesis: **merge curation with creation** — AI that takes a user's taste signal and creates novel sonic combinations (mashups, transitions, mixes) they never would have found. Users should feel like magicians, not passive recommendation consumers.

## What Exists Today

### Data Assets (on local SSD)
- **256M Spotify tracks metadata** (33GB SQLite) — title, artist, album, release date, popularity, etc.
- **256M Spotify audio features** (39GB SQLite) — 13 dimensions: BPM, energy, danceability, valence, key, loudness, mode, acousticness, instrumentalness, liveness, speechiness, tempo, time_signature
- **800K MERT audio embeddings** (6.1GB) — 2048d vectors from MERT-v1-330M (layers 5+6 concatenated), computed on Modal A100 for $18
- **27.2M curated DJ transitions** — matched pairs from 76.5M raw transitions across 7 sources (Last.fm 47.5M, ListenBrainz 22.8M, MixesDB 4.2M, KEXP 2.8M, Mixcloud 1.75M, WFMU 958K, NTS 724K). Each pair: (track_A_spotify_id, track_B_spotify_id, score, sources)
- **79M-key name index** — SQLite-backed artist|track to Spotify row ID lookup
- **~250M Spotify preview URLs** — 30s MP3 clips at p.scdn.co, no auth required, free CDN
- **ALS taste vectors** — 12.7M tracks x 128d from implicit collaborative filtering on Spotify playlists. 96.3% near-zero (data sparsity — most tracks in <5 playlists)

### Current Models
- **V8 Transition Scorer** (PRODUCTION): NDCG@20=0.7318. BPR + ALS taste + MERT audio. Predicts DJ-style transitions (what track follows what).
- **V3 Similarity Model**: F1=0.9415. Late fusion MERT+ALS, 100K tracks. Binary "do these tracks go together."
- **Architecture ceiling at ~0.73** — 7 model variants tested (C-16 Phase 2), none broke 0.73. More data and more features won't break it; fundamentally different approach needed.

### Live Services
- **Bridge API** on :8877 — 7-dimension chemistry scoring (neural, curated, rhythmic, harmonic, energy, taste, timbral). Identifies cross-community connections.
- **4 data ingestors** running 24/7 collecting transition data (Last.fm, ListenBrainz, Discogs, Mixcloud)

### Audio Pipeline Capabilities
- MERT-v1-330M encoding (~5s/track on A100, 2048d output)
- Demucs stem separation (vocals, drums, bass, other)
- Librosa analysis (BPM, key, energy, spectral features)
- Mashup renderer v3 (stereo, beat-aligned, per-stem crossfade, bus compression mastering)

## The Problem

The current pipeline solves **sequencing** — predicting what track comes after what in a DJ set. This is curation analysis. But the product goal is **curation x creation** — AI that creates novel sonic combinations from taste signal. Nothing in the current pipeline generates audio, creates mashups, or bridges the gap between understanding what sounds good together and actually producing new listening experiences.

The 0.73 ceiling confirms we've extracted maximum signal from co-occurrence + audio features for transition prediction. More of the same won't help.

## The Hypothesis Under Evaluation

### Proposed New Pipeline (4 models)

**Model 1: Audio Feature Predictor**
- Input: raw audio (30s) → MERT 2048d
- Output: Spotify-compatible 13d features + 32d MERT-derived taste features
- Purpose: Any new audio → predicted features → query 256M tracks by feature similarity for coarse retrieval (256M → 5,000 candidates)
- Training data: 800K tracks where we have both MERT and Spotify features
- Cost: ~1-2 days to train

**Model 2: Stem Compatibility Predictor**
- Input: MERT embeddings of two tracks (2048d x 2 = 4096d)
- Output: compatibility score + compatibility TYPE (rhythmic, harmonic, textural, emotional, surprise)
- Purpose: Given two tracks, predict whether their stems can be combined and HOW
- Training data: 27.2M curated transitions as positives, random pairs as negatives
- Key innovation: compatibility TYPE label enables creation decisions (which stems to combine)
- Cost: ~3-5 days

**Model 3: Mashup Arrangement Model**
- Input: two compatible tracks + compatibility type
- Output: arrangement plan (which stems, BPM adjustment, key shift, transition points)
- Training data: WhoSampled (~700K samples) + our own mashup experiments + transition data
- Could be: fine-tuned small LLM or trained arrangement model
- Cost: TBD

**Model 4: Taste Agent (the product)**
- Chains: user taste input → coarse retrieval (Model 1) → MERT on candidates → stem compatibility (Model 2) → arrangement (Model 3) → audio generation/rendering → mashup preview
- User gives 3-5 songs → gets back a cross-genre mix they never would have imagined
- Every skip/save/replay trains the taste fingerprint

### Proposed Kills
- V8 transition scorer retraining (at ceiling, playlist-based BPR doesn't serve mashup goal)
- Stigmergic experiments (EXP-016, 017, 019) — network science without product signal
- Phase 0 audit via Upwork — evaluates V8 which is at ceiling

### Proposed Keeps
- All 4 ingestors (more transition data feeds Model 2)
- 27.2M curated transitions (training data for Model 2)
- Bridge API (identifies interesting cross-community candidates)
- MERT embedding pipeline (shifted from bulk to on-demand)

### Open Source / Agent Angle
Recent developments suggest everything is becoming local, open, composable:
- **ACE-Step 1.5 XL**: open-source 4B-param music generator, Apache licensed, runs on Mac locally. Could generate bridge/transition audio.
- **Mel-Band-Roformer**: outperforming Demucs on vocal separation. Demucs no longer actively maintained at Meta.
- **Google A2A Protocol v0.3**: agent-to-agent interoperability. Taste agent could expose Agent Cards.
- **MCP (Model Context Protocol)**: tools as composable APIs
- Trend: people building own software, running local models, owning their data/taste

Proposed positioning: Kyma as a **personal taste engine** — local app that turns music taste into creative superpower. Like Cursor for music. Open source models (MERT, ACE-Step, Mel-Band-Roformer) running locally. Taste graph as community commons (like Nostr for taste). Kyma = best tool for interacting with it.

## Competitive Landscape (April 2026)
- **Spotify**: Taste Profile Editor (SXSW Mar 14) — user-editable taste via "SongDNA." Validates taste-as-product but their implementation is manual editing, not behavioral discovery. Defensive lock-in play.
- **Suno v5.5**: "My Taste" — taste profiling in AI music generation. Single-player, no network effects. Gap: generated slop vs real music discovery.
- **Coda Music**: Anti-algorithm streaming, ALL THREE major labels licensed at $10.99/mo. Human only, won't scale.
- **Hangout**: Turntable revival, $8.2M Founders Fund. Synchronous + ephemeral = no compounding.
- **Bandcamp**: Banned AI entirely (Jan 2026). Market bifurcation.
- **YC W26**: 196 companies, ZERO in music/audio/taste. Competitive vacuum.

## Key Constraints
- 2 founders, no funding yet (pre-seed)
- M3 Max laptop for local compute, Modal A100 for heavy GPU ($0.80/hr)
- ~$2.8K year 1 budget with Modal credits
- No audio licensing (taste data + metadata only — facts aren't copyrightable)
- 250M preview URLs available for on-demand MERT computation

## Questions for Analysis

1. **Is the proposed 4-model pipeline the right architecture for merging curation with creation?** What's missing? What's unnecessary? What would you change?

2. **Is the MERT → Spotify audio features mapping (Model 1) the right approach for cold-start retrieval at 256M scale?** The 13d Spotify features are lossy (2048d → 13d). Is that acceptable for coarse filtering? Should the target space be different?

3. **Can stem compatibility actually be learned from transition data?** DJ transitions are track-level events, not stem-level. The training signal is "DJ played A then B" — not "the vocals of A work over the beat of B." Is this signal sufficient, or do we need different training data entirely?

4. **Is the "personal taste engine" / local-first positioning correct?** Or should this be a cloud platform with network effects? The open-source/own-your-data trend vs the need for taste graph network effects — how do these tensions resolve?

5. **What should we build FIRST?** Given 2 founders and no funding, what's the highest-leverage first model/product to validate the thesis?

6. **What are we NOT thinking about?** What failure modes, alternative approaches, or blind spots exist in this plan?

Give the most rigorous, honest analysis possible. Don't soften critique to be polite. Don't agree unless you genuinely believe it's correct after trying to break it. But don't disagree just to seem thorough — if something is right, explain WHY it's right, which is equally valuable.

Think several levels deeper than the surface question. What upstream assumptions, if wrong, invalidate everything downstream? What would a domain expert with 20 years of experience immediately notice?

Structure your response:
1. IMMEDIATE REACTION (2 sentences — gut before deep analysis)
2. WHAT'S ACTUALLY RIGHT HERE (specific, with reasoning)
3. WHAT'S WRONG OR RISKY (ranked by severity, mechanism of failure)
4. WHAT'S MISSING ENTIRELY (things nobody is asking about)
5. WHAT YOU'D DO INSTEAD (specific, implementable)
6. VERDICT (Go/Modify/No-Go, confidence 0-100, one paragraph)
