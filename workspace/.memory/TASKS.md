# Active Tasks

## Current Focus (updated 2026-04-06 21:10 PDT)

### BATH PLAYLIST AGENT — Essay-Driven Reframe
Idam's Apple Pages essays (Jan-Feb 2026) reject Taste DNA as Wrapped 2.0 / identity signaling.
Reframe doc: `files/product-v3-bath-playlist.md`
Core thesis: Agent sends you music you'll love without you explaining yourself. Mashup = preview asymmetry solver (30-90s → 15s). No profiles, no deviation charts, no signaling.

**Phase 1: Taste DNA (Weeks 1-2)** ← COMPLETE (infrastructure retained, surface killed)
- [x] taste_dna.py pipeline, FAISS, Leiden communities, Last.fm ingestion — all kept as backend intelligence
- [x] DNA web page, shareable URL, OG card, deviation chart — KILLED as user-facing (kept for internal debug)

**Phase 1 (revised): Silent Agent MVP** ← CURRENT
- [ ] **Discovery endpoint** — POST /api/discover. Takes listening history, returns 10 tracks + trust anchors (known track that connects to each discovery). No profile, no analytics display.
- [ ] **Mashup preview pairs** — Each discovery paired with trust anchor. 15s mashup using engine v3. The preview asymmetry hack.
- [ ] **Delivery** — Spotify playlist creation or simple web page with audio. "Here's music for you." Nothing else.
- [ ] **Behavioral signal** — Listen/skip tracking. No thumbs up/down. No ratings UI.

**Phase 2: The Gift (Weeks 3-4)**
- [ ] **Gift flow** — Send discoveries to a friend via link. Friend connects history. Agent bridges both.
- [ ] **Bath playlist moment** — "We both love this" without either person explaining their taste.
- [ ] **No comparison, no competition** — Gifting, not signaling.

**Phase 3: Agent Autonomy (Month 2)**
- [ ] **Weekly cron** — Re-runs pipeline, diffs against previous, sends delta.
- [ ] **Silent learning** — Agent gets better from behavioral signal alone.
- [ ] **k-factor tracking** — Gift viral coefficient.

**Phase 4: Measure & Pivot (Month 3)**
- [ ] "Did the user listen to a track they'd never heard and add it to their library?" ← success metric
- [ ] k > 0.3 AND monthly churn < 8% → consumer product works

### DO NOT BUILD (from verdict)
- No playback service. No p.scdn.co. No audio distribution.
- No more audio embedding models.
- No DJ transition labels for compatibility training.
- No B2B API yet — but architect so intelligence layer IS separable.

### Kyma Engine — RESEARCH LAB MODE (updated 2026-04-11)
**Repo:** `/Users/idamo/code/kyma-engine/` — see `TASKS.md` there for full queue + build priorities.
**Operating mode:** Research lab, not ship mode. Models inspire models. Discoveries rewrite product thesis.

**Production Architecture (decided 2026-04-11):**
- **64d taste vector from curriculum-trained ProjDot64 on MERT L24 (CLS).** Not 192d.
- Preference is LINEAR — ProjDot64 (65K params) >> MLP (262K params). No nonlinearity needed.
- Curriculum training solves specialization trap: min(hard, random) = 0.341 (symmetric).
- Online EMA updates are provably stable because preference is linear + basis is orthogonal.

**Completed models:**
- MODEL-001 taste projector (val_cos=0.4934), MODEL-002 V8 transition scorer (NDCG=0.7318, FROZEN)
- MODEL-004 bridge predictor (r=0.958), Feature Predictor v2 (R²=0.889 loudness)
- Composite ranker (90% taste + 10% transition → NDCG@20=0.5336)
- Modal all-layer MERT encoding (99,971 × 25 × 1024), R2 backup (28.9GB)

**Completed experiments (EXP-R01 Phases 1-5b + DIAG 01-05):**
- All 5 diagnostics RESOLVED. Bridge leakage confirmed, chemistry genuinely 4D, asymmetry is noise, topology lognormal small-world, embeddings unbiased.
- EXP-R01: 8 phases. Two-peak confirmed (L5 acoustic + L24 CLS). Preference composes across layers. Subspaces orthogonal. DJs peak at CLS, listeners at acoustic. Hard negatives prove preference is real (81% retention). Curriculum solves specialization. Multi-layer redundant under curriculum.
- Full results: kyma-engine `TASKS.md` § Experiment Results

**COMPLETED: 4-Model Consultation Synthesis (2026-04-11)**
- 4 responses: Opus 4.6 + Sonnet 4.5 Extended, each on exploratory AND goal-directed prompts
- Full synthesis: `files/consultation-synthesis-2026-04-11.md`
- Ranking: #1 Opus Goal (best product intuition), #2 Sonnet Goal (best research depth + novel ideas), #3 Opus Exploratory (best first experiment), #4 Sonnet Exploratory (most creative but scattered)
- **Meta-finding:** Opus = product strategist, Sonnet = research scientist. Use Opus for prioritization, raid Sonnet for architecture specs.
- **The single most important insight:** Linearity means feedback loop (anchor + mashup + EMA) is cheap to iterate with linear algebra. Build the loop first.

**Build queue (from synthesis — full details in kyma-engine TASKS.md):**
- Week 1-2: Stem-ablation ProjDot → Anchor Selection Model → Behavioral EMA → Taste Vector Arithmetic
- Week 3-4: Fisher-Optimal Mashup Probes → MERT Layer Routing → Curator Residual
- Month 2: Gift Bridge Midpoint → Anti-Hub Router → Wormhole Detector
- Month 3+: Bridge Segment Localization, Causal Skip Attribution, Koopman Operator, Persistent Homology

### Existing Infrastructure (KEPT — feeds Taste Oracle)
- FAISS 254.8M × 12d index
- Rule-based compatibility: utils/compatibility.py
- Bridge API on :8877 (7-dim chemistry scoring)
- MODEL-004 bridge predictor (r=0.969)
- All data ingestors (112.5M+ transitions)

### Needs Idam's Attention
- **Tax deadline April 15** (5 days) — $91,647 owed. Action plan at files/tax-installment-action-plan.md. Call IRS 800-829-1040 for installment agreement.
- **Apolline birthday morning deliveries**: Flowers (Rossi & Rovetti), pastries (DoorDash Arsicault), balloons (DoorDash Party City) — Idam was researching last night, confirm orders placed.
- **Apolline birthday gift**: ✅ SHIPPED v4.7. Latest: bobbing balloon pop game (28 reasons), "See You Again" background music, yay SFX, two-sided hair. Live at Vercel: https://birthday-gift-three-pied.vercel.app + cloudflared tunnel (PID 74161 :8901, PID 77031).
- **Verra 93A — Clifford consultation Wed Apr 15, 1 PM PT** (4 PM ET). Zoom: 843 2538 8506 / 915998. Reminder job #198 fires 12:45 PM PT. NOTE: Apr 15 is also tax deadline day.
- **Share payment**: Both founders owe $45 each to Kyma Computer Inc. Deferred to Monday (Mercury login).
- **Emily White: text her** — 304-941-8118 re Shibuya TestFlight.

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
- **Bridge API**: DOWN — no process on :8877 as of Apr 9. Needs restart.
- **Ingestors**: ALL DEAD — no ingestor processes found as of Apr 9. ~112.5M total transitions in DB.

### Data (SSD)
- Spotify: 256M tracks (33GB metadata), 256M audio features (39GB), 800K MERT (6.1GB)
- FAISS: 254.8M × 12d, 3.3GB index
- Curated transitions: 27.2M matched

## Open (Non-Pivot)
- [ ] **Covered CA eligibility** — Needs Idam login.
- [ ] **Fundraise narrative reframe** — Now framed around Taste Oracle.
