# Active Tasks

## Current Focus (updated 2026-04-11 17:30 PDT)

### BATH PLAYLIST AGENT — Essay-Driven Reframe
Idam's Apple Pages essays (Jan-Feb 2026) reject Taste DNA as Wrapped 2.0 / identity signaling.
Reframe doc: `files/product-v3-bath-playlist.md`
Core thesis: Agent sends you music you'll love without you explaining yourself. Mashup = preview asymmetry solver (30-90s → 15s). No profiles, no deviation charts, no signaling.

**Phase 1: Taste DNA (Weeks 1-2)** ← COMPLETE (infrastructure retained, surface killed)
- [x] taste_dna.py pipeline, FAISS, Leiden communities, Last.fm ingestion — all kept as backend intelligence
- [x] DNA web page, shareable URL, OG card, deviation chart — KILLED as user-facing (kept for internal debug)

**Phase 1 (revised): Silent Agent MVP** ← COMPLETE
- [x] **Discovery endpoint** — ✅ POST /api/discover on :8879. Returns N discoveries + trust anchors + wormhole surprise. Anti-hub α slider. Cold start via Fisher probes. 2ms response, 99,971 tracks. `kyma-engine/api/discover.py`. Commit 533feda.
- [x] **Mashup preview pairs** — ✅ Client-side crossfade: anchor (last 8s) → discovery (first 8s), 12s total. Dual Audio elements + requestAnimationFrame volume crossfade. Zero server-side processing. Uses p.scdn.co 30s previews (CORS: *). Signals: mashup_play + mashup_finish with duration_ms. Commit 36d6e28.
- [x] **Delivery** — ✅ Self-contained HTML at GET / on :8879. Search → history chips → discover → cards with audio + mashup preview. Dark theme. Commit 084a803.
- [x] **Behavioral signal** — ✅ POST /api/signal for play/skip/finish/seek/mashup_play/mashup_finish events. In-memory store, GET /api/signals for debug. Commit 084a803.

**Phase 2: The Gift** ← COMPLETE
- [x] **Gift flow** — ✅ POST /api/gift/create + GET /gift/{id} redemption page. Midpoint bridging in 64d: normalize(A+B), score=proximity×balance. SQLite persistence (gifts.db). "send as gift" button on discovery page. Tested: Radiohead/Aphex→Bon Iver/Calvin Harris = The Marías, girl in red, Fred again.., Arlo Parks (all 99-100% balanced, 9ms). Commit 8ac37e9.
- [x] **Bath playlist moment** — ✅ The gift page IS the bath playlist moment. "someone sent you music" → "music you'd both love" with taste overlap badge. No profiles, no comparison.
- [x] **Signal persistence** — ✅ Signals table in gifts.db (SQLite). play/skip/finish/seek/mashup_play/mashup_finish with rowid_track, duration_ms, timestamp. Survives restarts. Commit 001b733.

**Phase 3: Agent Autonomy (Month 2)** ← COMPLETE
- [x] **Weekly cron** — ✅ POST /api/weekly-digest. Auto-generates fresh discoveries for all users with taste vectors. Delta-filtered (only NEW tracks). Builds synthetic history from most-finished tracks. 4.9ms per user. Commit d0a8ef1.
- [x] **Silent learning** — ✅ EMA taste learning from behavioral signals. finish/play → blend toward (α=0.95), skip → repel (β=0.3). Per-user 64d taste vectors in SQLite. Discovery re-ranked: 70% graph + 30% EMA cosine. Tested: Aphex Twin finishes reshape Bon Iver discoveries (5/8 changed), skip repulsion works (Bon Iver suppressed from 5→1 in top 8). Commit 1e1034a.
- [x] **k-factor tracking** — ✅ GET /api/metrics. k-factor (gift virality = redemption rate), finish/skip ratio, engagement by event type, taste learning stats. All from SQLite. Commit d0a8ef1.

**Phase 4: Measure & Pivot (Month 3)** ← INFRASTRUCTURE COMPLETE
- [x] **Success metric** — ✅ discovery_completion_rate in GET /api/metrics. 57% of unique discovered tracks finished (4/7). Proxy for "listened to unheard track" (can't detect library add without Spotify OAuth). Commit 2670ca7.
- [x] **Consumer product gate** — ✅ phase4_gate in /api/metrics. Automated check: k > 0.3 AND monthly_churn < 8%. Currently passing on test data (k=1.0, churn=0%). MAU/WAU computed from 28d/7d signal windows. Commit 2670ca7.
- [ ] **Real user validation** — Gate infrastructure built. External tunnel live: https://guitar-frequency-stuck-processes.trycloudflare.com (ephemeral, PID 53739). Weekly digest cron wired (Job 201, 7-day interval). Need real users to generate meaningful data. Idam notified (Job 200).

### DO NOT BUILD (from verdict)
- No playback service. No p.scdn.co. No audio distribution.
- No more audio embedding models.
- No DJ transition labels for compatibility training.
- No B2B API yet — but architect so intelligence layer IS separable.

### Kyma Engine — RESEARCH LAB MODE (updated 2026-04-11)
**Repo:** `/Users/idamo/code/kyma-engine/` — see `TASKS.md` there for full queue + build priorities.
**Operating mode:** Research lab, not ship mode. Models inspire models. Discoveries rewrite product thesis.

**Production Architecture (decided 2026-04-11, REVISED by Phase 6):**
- **⚠️ REVISED:** Phase 6 kernel baselines showed **DeepPref (674K params) beats ProjDot64 (65K) by 32%**. New production encoder: `1024 → 512 (LN+GELU+DO) → 256 (LN+GELU+DO) → 64` with cosine scoring.
- Output: 64d taste vector from MERT L24 (CLS token). Same dimensionality, better encoding.
- **Refined finding:** Preference is linear **in a learned non-linear subspace**. The 1024d→64d mapping needs depth (GELU, LayerNorm), but comparison in 64d is still linear (cosine similarity).
- **✅ Production checkpoint:** `artifacts/deeppref/deeppref_production.pt` — min(hard,rand) = 0.4600, +35% over ProjDot64.
- **✅ Phase 7 CONFIRMED:** Multi-layer DOES NOT help even with deep encoding. cls_only > peak2 > peak3. L24 CLS = all preference info.
- **✅ MERT Layer Routing:** Raw MERT cosine peaks at L6 (acoustic), not L24 (semantic). 59% of users are "acoustic listeners." Per-user routing +6.8% mean accuracy. Compatible with DeepPref L24 — trained projection vs raw retrieval are two different mechanisms.
- Curriculum with 70% hard ratio cap → monotonic improvement. 80% overshoots (Phase 4c).
- Online EMA updates still stable — cosine comparison in 64d is still linear. Only the encoder changed.

**Completed models:**
- MODEL-001 taste projector (val_cos=0.4934), MODEL-002 V8 transition scorer (NDCG=0.7318, FROZEN)
- MODEL-004 bridge predictor (r=0.958), Feature Predictor v2 (R²=0.889 loudness)
- Composite ranker (90% taste + 10% transition → NDCG@20=0.5336)
- Modal all-layer MERT encoding (99,971 × 25 × 1024), R2 backup (28.9GB)

**Completed experiments (EXP-R01 Phases 1-5b + DIAG 01-05):**
- All 5 diagnostics RESOLVED. Bridge leakage confirmed, chemistry genuinely 4D, asymmetry is noise, topology lognormal small-world, embeddings unbiased.
- EXP-R01: 10 phases (1-7 + diagnostics). Two-peak confirmed (L5 acoustic + L24 CLS). Subspaces orthogonal. DJs peak at CLS, listeners at acoustic. Hard negatives prove preference is real (81% retention). Curriculum solves specialization. **Phase 6: DeepPref +32% over ProjDot64 (linear in learned non-linear subspace). Phase 7: multi-layer CONFIRMED redundant even with deep encoding. Architecture FINAL: DeepPref L24, 674K params, 64d, min=0.4600.**
- Full results: kyma-engine `TASKS.md` § Experiment Results

**COMPLETED: 4-Model Consultation Synthesis (2026-04-11)**
- 4 responses: Opus 4.6 + Sonnet 4.5 Extended, each on exploratory AND goal-directed prompts
- Full synthesis: `files/consultation-synthesis-2026-04-11.md`
- Ranking: #1 Opus Goal (best product intuition), #2 Sonnet Goal (best research depth + novel ideas), #3 Opus Exploratory (best first experiment), #4 Sonnet Exploratory (most creative but scattered)
- **Meta-finding:** Opus = product strategist, Sonnet = research scientist. Use Opus for prioritization, raid Sonnet for architecture specs.
- **The single most important insight:** Feedback loop (anchor + mashup + EMA) is cheap to iterate — comparison is still cosine similarity in 64d (linear), even though the encoder is non-linear. Build the loop first.

**Build queue (dependency-ordered, no time-boxing — full details in kyma-engine TASKS.md):**
- ~~Behavioral EMA~~ ✅ DONE | ~~Taste Vector Arithmetic~~ ✅ DONE
- ~~Anchor Selection~~ ✅ | ~~Fisher Probes~~ ✅ | ~~Wormhole Detector~~ ✅ | ~~Gift Bridge~~ ✅ | ~~Anti-Hub Router~~ ✅
- ~~MERT Layer Routing~~ ✅ (L6 beats L24 raw, per-user routing +6.8%, 65% users benefit)
- ~~Curator Residual~~ ✅ (curators genuinely distinct, inter-cos 0.376, 2D effective dim, α=0.1 → 91% unique discoveries)
- ~~Koopman Operator~~ ✅ (time-delay DMD τ=3: -65% error vs naive, Takens embedding, zero oscillatory modes)
- **BLOCKED:** Stem-ablation DeepPref (Demucs venv), Bridge Segment Localization (needs stems)
- **RESEARCH:** Causal Skip Attribution (needs product loop), Persistent Homology, Temporal Community Detection

### Existing Infrastructure (KEPT — feeds Taste Oracle)
- FAISS 254.8M × 12d index
- Rule-based compatibility: utils/compatibility.py
- Bridge API on :8877 (7-dim chemistry scoring)
- MODEL-004 bridge predictor (r=0.969)
- All data ingestors (112.5M+ transitions)

### Needs Idam's Attention (updated 2026-04-11)
- **Tax deadline April 15** (4 days) — $91,647 owed. >$50K = must CALL IRS 800-829-4933 for long-term installment (online portal caps at $50K). Short-term (180 days, $0 fee) available online at irs.gov/opa but requires ~$15K/month.
- **Verra 93A — Clifford consultation Tue Apr 15, 1 PM PT** (4 PM ET). Zoom: 843 2538 8506 / 915998. Reminder job #198 fires 12:45 PM PT. Brief: `files/verra-93a-litigation-brief-v5.md`. NOTE: Apr 15 is also tax deadline day.
- **Share payment**: Both founders owe $45 each to Kyma Computer Inc via Mercury ACH/check.
- **Emily White: text her** — 304-941-8118 re Shibuya TestFlight.

### Recently Resolved
- **Apolline birthday gift**: ✅ SHIPPED v4.7. Live at Vercel: https://birthday-gift-three-pied.vercel.app
- **Apolline birthday deliveries**: Research completed Apr 9 (flowers, pastries, balloons). Idam handling placement.

### Waiting On Others
- **Clerky payment** — DONE. $819 paid Apr 8, $100 refund pending from Clerky (Venturous Counsel discount).
- **Clerky 83(b) managed elections** — DONE. Both founders filed Apr 9. $298 total. Clerky mails to IRS.
- **Notion for Startups** — BLOCKED. "Kyma Space 2.0" showing ineligible despite support confirming eligibility. Follow-up sent Apr 9, awaiting human response.
- **Share payment** — Both founders owe $45 each to Kyma Computer Inc via ACH/check. Idam aware.
- **Domestic partner listing** — Michael Young recommends listing Apolline as domestic partner in Clerky docs (investor cleanliness). Needs Idam decision.

### Deadlines (Startup Credits)
- **Mixpanel**: Must send data within 90 days of Apr 7 → **deadline Jul 6, 2026**. Reminder job set.
- **Scaleway**: 100 EUR credit expires **~May 6, 2026**. Needs billing info + valid ID to activate. Reminder job set.
- **Scaleway Startup Program**: Application under review, 21 business day response → follow up by **~May 5, 2026** if no reply.

## Recently Completed (Apr 5-9)
- **Clerky 83(b) managed elections** — Both founders filed. $298 total. Clerky mails to IRS. Apr 9.
- **93A attorney analysis** — 6 attorneys contacted, Clifford consultation Apr 15. Apr 9.
- **Venturous doc upload** — 18 Clerky PDFs uploaded to Dropbox K. CLIENT UPLOADS. Audit deferred until fundraise. Apr 10.
- **Birthday gift v4 SHIPPED** — 9-page journal overhaul: songbirds, star chart (May 16 2020), slingshot game, 28 hearts, Spotify link, CSS scroll-snap book. Apr 10.
- **Birthday gift v3.1 SHIPPED** — Pencil scribble love letter, PencilJitter engine, 7 scenes, deployed via cloudflared. Apr 9-10.
- **Birthday logistics** — Rossi & Rovetti (same block), DoorDash pastries/balloons researched. Apr 9.
- **3-day catch-up (Apr 7-9)** — Full email read of both accounts, all state changes cataloged. Apr 9.
- **Sentry credits** — $5,000 secured (1yr expiry). Apr 9.
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
- **Bridge API**: DOWN since Apr 9. NOT BLOCKING — research uses direct DB queries, not the API.
- **Ingestors**: ALL DEAD since Apr 9. NOT BLOCKING — 112.5M transitions already in DB is sufficient for current research. Restart when we need fresh data.

### Data (SSD)
- Spotify: 256M tracks (33GB metadata), 256M audio features (39GB), 800K MERT (6.1GB)
- FAISS: 254.8M × 12d, 3.3GB index
- Curated transitions: 27.2M matched

## Open (Non-Pivot)
- [ ] **Covered CA eligibility** — Needs Idam login.
- [ ] **Fundraise narrative reframe** — Now framed around Taste Oracle.
