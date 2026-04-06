# Active Tasks

## Current Focus (updated 2026-04-06 01:00 PDT)

### TASTE ORACLE — Consultation-Validated Build Plan
Strategy validated via dual-model consultation (Opus 4.6 + Sonnet 4.5, Apr 6).
Verdict: `files/consultations/2026-04-06-music-ip/verdict.md`
78% confidence. Both models independently converged: build taste intelligence layer ON TOP of Spotify/Apple Music.

**Phase 1: Taste DNA (Weeks 1-2)** ← CURRENT
- [x] **taste_dna.py MVP** — Full pipeline: Last.fm → Spotify match (87%) → 43,424 Leiden communities → diversity scoring → bridge expeditions. Tested on rj (500 tracks). Committed e918d0a.
- [x] **FAISS 256M×12d index** — IVF4096,PQ6, 254.8M vectors, 39ms search.
- [x] **Taste community detection** — Leiden on 2.5M nodes, modularity=0.67.
- [x] **idx_track_name_artist** — 256M-row index for name+artist matching. One-time build complete.
- [ ] **Web endpoint** — Wire taste_dna.py into kyma.stream (Next.js → FastAPI → pipeline)
- [ ] **Shareable URL** — kyma.stream/dna/{username} with OG meta tags for social sharing
- [ ] **Visual artifact** — Designed shareable image/card (Spotify Wrapped aesthetic)
- [ ] **Improve community descriptions** — Currently too BPM-centric; need genre/mood inference from centroid features + example tracks

**Phase 2: Bridge Expedition Agent (Weeks 3-4)**
- [ ] **Weekly AI-curated discovery queue** — Deep-linked to Spotify/Apple Music
- [ ] **Context inference** — Time, explicit mode selection from day one
- [ ] **In-app rating** — Rate tracks to feed behavioral loop (the real moat)

**Phase 3: Social Taste Exchange (Month 2)**
- [ ] **Friend invitations** — Taste overlap analysis
- [ ] **Shared queues** — Collaborative discovery
- [ ] **k-factor measurement** — Viral coefficient tracking

**Phase 4: Measure & Pivot (Month 3)**
- [ ] k > 0.3 AND monthly churn < 8% → consumer product works
- [ ] If not → pivot toward professional curation tools

### DO NOT BUILD (from verdict)
- No playback service. No p.scdn.co. No audio distribution.
- No more audio embedding models.
- No DJ transition labels for compatibility training.
- No B2B API yet — but architect so intelligence layer IS separable.

### Kyma Engine — Model Status (updated 2026-04-06 23:15)
**Repo:** `/Users/idamo/code/kyma-engine/` — see `TASKS.md` there for full queue.
- **Modal all-layer MERT encoding** — DONE. 200/200 batches, 99971 tracks × 25 layers. 9.5GB. Backed up to R2.
- **Feature predictor v2** — DONE. R²=0.889 loudness, 0.874 acousticness, 0.866 energy. Layers 18+19, per-dim standardization.
- **MODEL-001 v2 taste projector** — DONE. val_cos=0.4934. Ceiling confirmed on re-run.
- **Composite ranker** — TUNED. Sweep winner: 90% taste + 10% transition → NDCG@20=0.5336 (was 0.1796). Now default in code.
- **R2 backup** — DONE. 28.9GB across 2,171 objects. All embeddings + manifests backed up.
- **Repo overhaul** — DONE. README, CONTRIBUTING, MODEL-CATALOG, 9 per-model READMEs, TASKS.md. Droppable task protocol added.
- **Next engine priorities**: Optional finer weight sweep (0.01-step grid), optional 5-layer feature predictor (5120d).

### Existing Infrastructure (KEPT — feeds Taste Oracle)
- FAISS 254.8M × 12d index
- Rule-based compatibility: utils/compatibility.py
- Bridge API on :8877 (7-dim chemistry scoring)
- MODEL-004 bridge predictor (r=0.969)
- All data ingestors (112.5M+ transitions)

### Needs Idam's Attention
- **Tax deadline April 15** (9 days) — Action plan at files/tax-installment-action-plan.md
- **Verra 93A: brief FINAL** — Forward to Gary Allen (617-575-9595). Deposit deadline: Sep 11, 2026.
- **Apolline's birthday April 10** — Turns 28. Reminder jobs set.
- **Emily White: text her** — 304-941-8118 re Shibuya TestFlight.

### Waiting On Others
- **Clerky payment** — Blocked on Jessica Brodsky attorney review. Monitor job #165.

## Recently Completed (Apr 5-6)
- **Taste DNA MVP** — taste_dna.py end-to-end pipeline validated. Apr 6.
- **Music IP consultation** — Dual-model verdict: Taste Oracle, not music player. Apr 6.
- **Creation Engine consultation** — Opus 4.6 + Sonnet 4.5. REBUILD at 80%. Apr 5.
- **Credit program applications** — Mixpanel K, Amplitude ~K secured. Apr 3-5.
- **Self-evolution via Meta-Kai** — 5 CHANGE blocks applied. Apr 5.

## Production State

### Models
- **V8 (FROZEN)**: NDCG@20=0.7318. At ceiling.
- **V3 (similarity)**: F1=0.9415. Useful for candidate pre-filtering.
- **MODEL-004 (bridge)**: r=0.969. Crown jewel per consultation.

### Live Services
- **Bridge API**: PID 47424 on :8877.
- **Ingestors**: ~112.5M total transitions. All feeding future training data.

### Data (SSD)
- Spotify: 256M tracks (33GB metadata), 256M audio features (39GB), 800K MERT (6.1GB)
- FAISS: 254.8M × 12d, 3.3GB index
- Curated transitions: 27.2M matched

## Open (Non-Pivot)
- [ ] **Covered CA eligibility** — Needs Idam login.
- [ ] **Fundraise narrative reframe** — Now framed around Taste Oracle.
