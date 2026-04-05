# Active Tasks

## Current Focus (updated 2026-04-05 07:30 PDT)

### CREATION ENGINE PIVOT — New Direction
Architecture validated via dual-model consultation. Design doc at `files/kyma-creation-engine-design.md`.

**Build Sequence:**
- [ ] **Week 0: ACE-Step quality gate** — Install ACE-Step 1.5 XL on M3 Max, test audio2audio/repainting on 10 high-chemistry Bridge API pairs. BLOCKING — determines architecture commitment.
- [ ] **Week 1: Wizard of Oz MVP** — 5 manual mashups via Mel-Band-Roformer + renderer v3, simple UI, show to 20 people, Sean Ellis test (>=40% "very disappointed")
- [ ] **Weeks 2-3: ACE-Step integration** — Replace mashup renderer with ACE-Step pipeline. Test on 100 pairs. 10 listener judges.
- [ ] **Weeks 4-5: FAISS indexing** — IVF-PQ on 800K MERT embeddings. Taste input -> ANN search -> Bridge API scoring -> generation.
- [ ] **Weeks 6-8: Taste feedback loop** — Rocchio-style relevance feedback from skip/save/replay. Ship to 50 beta users.

### In Progress
- **Data ingestors** — Last.fm (61840), ListenBrainz (61872), Discogs (62236), Mixcloud (89088). All alive.
- **Unified transition rebuild** — PID 61050, 27.2M matched pairs from 76.5M raw. Streaming save fix applied (bcaaa65).

### Needs Idam's Attention
- **Tax deadline April 15** (10 days) — Action plan at files/tax-installment-action-plan.md. Steps: (1) confirm extension with Georges + pay $500 + call 800-829-1040, (2) evaluate CNC/OIC within 30 days.
- **Verra 93A: brief FINAL** — Forward to Gary Allen (617-575-9595). Deposit deadline: Sep 11, 2026. Drive folder: https://drive.google.com/drive/folders/1ps8cYkThnGC1cLllkJKQa_PJAG1sW6Ml
- **Apolline's birthday April 10** — Turns 28. Reminder jobs #183 (Apr 8) and #184 (Apr 9) set.
- **Emily White: text her** — 304-941-8118 re Shibuya TestFlight.

### Waiting On Others
- **Clerky payment** — Blocked on Jessica Brodsky (VC attorney) completing review of 18 docs. $819 lifetime. Monitor job #165 checking daily.

## KILLED (April 5, 2026 — Creation Engine Pivot)

These are permanently stopped. Do not restart without explicit instruction from Idam.

- ~~V8 transition scorer retraining~~ — At 0.73 ceiling. Playlist-driven BPR doesn't serve mashup goal.
- ~~EXP-016: Leiden CPM clustering~~ — Network science without product signal.
- ~~EXP-017: Curator Emergence Scoring~~ — Same.
- ~~EXP-019: Learned Stigmergic Weights~~ — Same.
- ~~Phase 0 audit via Upwork~~ — Evaluates V8 which is at ceiling.
- ~~Stigmergic recommendation engine~~ — Pre-product.
- ~~Preview asymmetry baseline study~~ — Pre-product.

## Recently Completed (Apr 3-5)
- **Creation Engine consultation** — Opus 4.6 + Sonnet 4.5 via Cognitive Amplifier. Verdict: REBUILD at 80% confidence. Design doc + archives written.
- Bridge API curated scoring + SQLite-backed lookup (d25b29b, 7becb05)
- Streaming JSON save fix for unified_transition_loader (bcaaa65)
- Watcher skip V8 retrain (b40f30b)
- Unified transition rebuild — 27.2M matched pairs from 76.5M raw (35.5%), 3.15GB output
- Verra 93A brief v4+v5 FINAL — full rewrites from attorney feedback
- Weekly self-evolution + CI triage
- Proactive intel: Spotify Taste Profile, Suno My Taste, Gradient Fund V

## Production State

### Models
- **V8 (FROZEN)**: NDCG@20=0.7318. At ceiling. No further retraining.
- **V3 (similarity)**: F1=0.9415. Kept — useful for candidate pre-filtering in new architecture.

### Live Services
- **Bridge API**: PID 47424 on :8877. 7-dim chemistry scoring. Curated SQLite DB (436MB, 7.4M entries). KEPT — core infrastructure for new architecture.
- **Ingestors**: Last.fm 68.1M | ListenBrainz 33.3M | MixesDB 4.4M | KEXP 2.8M | Mixcloud 1.8M | WFMU 1.2M | NTS 728K | Discogs 37M. Total ~112.5M. KEPT — feeds Bridge API and future synthetic training data.

### Data (SSD)
- Spotify: 256M tracks metadata (33GB), 256M audio features (39GB), 800K MERT embeddings (6.1GB)
- Name index: 79M keys, 10.57GB SQLite
- Curated transitions: 27.2M matched (rebuilding with streaming save)

## Open (Non-Pivot)
- [ ] **EXP-009: Taste Vector Quality by Community** — Stratify eval by community size. Low priority.
- [ ] **Covered CA eligibility** — Needs Idam login.
- [ ] **Fundraise narrative reframe** — Now framed around Creation Engine, not taste graph infra.

## Agent Specs (REWRITE needed)
All 9 agent specs in kyma-engine are behavioral drafts written for the OLD architecture. Must be rewritten against the 2-system Creation Engine architecture after Week 1 MVP validation.
