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
- **Tax deadline April 15** (6 days) — $91,647 owed. Action plan at files/tax-installment-action-plan.md. Call IRS 800-829-1040 for installment agreement.
- **Apolline birthday Apr 10 — place 3 orders TONIGHT**: (1) email orders@rossirovetti.com for flowers, (2) DoorDash Arsicault pastries 8:30 AM, (3) DoorDash Party City balloons 8:30 AM. All to 555 Bryant St.
- **Apolline birthday gift**: Direction TBD. Musical bridge infrastructure built (index.html + compute_bridge.py). Paused per Idam instruction — waiting for creative direction.
- **Verra 93A — Clifford consultation TOMORROW 1 PM PT** (4 PM ET). Zoom: 843 2538 8506 / Passcode 915998. Key Qs: contingency/hybrid fee, settlement range, timeline. Reminder job #197 set for 12:45 PM PT.
- **Verra 93A — Ellen Tanowitz**: Has full doc package, rates unknown. Compare after Clifford.
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
- **93A attorney analysis** — 6 attorneys contacted, 2 engaged (Clifford + Tanowitz). Consultation booked Apr 10. Apr 9.
- **Birthday gift infrastructure** — index.html + compute_bridge.py built. Paused for direction. Apr 9.
- **Birthday logistics** — Rossi & Rovetti (same block), DoorDash pastries/balloons. Apr 9.
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
