# Active Tasks

## 🧠 KYMA OS — v3 COLLAPSED TO "Obsidian for Music" (2026-04-17)

**Decision**: v3's 7 candidate surfaces (Dérive, Lineage, Gift, Bridge, Cross-Modal, 8.6s Radio, Loop Navigator) collapse into ONE primary product + Bridge as growth tactic. The cofounders' Apr 16 brainstorm explicitly named it: **"Obsidian for music"**. The pattern-match into 7 variations was my failure; their vocabulary supports one thing.

**Deliverables shipped today (2026-04-17)**:
- `files/research/kyma-deep-brain-analysis-2026-04-17.md` (49 KB, 7642 words) + PDF (570 KB) — all 5 cofounder voice-memo transcripts ingested, 10 convergent primitives, 11 rejection categories, 7 unresolved tensions, 10 open design questions
- `files/research/kyma-obsidian-for-music-product-pdf-2026-04-17.md` (38 KB, 5465 words) + PDF (430 KB) — primary product spec with product + eng + ML + AI + legal + GTM + a16z SR007 deck skeleton
- 5 voice-memo transcripts saved to `files/transcript-*.md` AND `notion-kyma-space-2/YYYY-MM-DD-*.md` with date prefixes for brain atomizer chronology
- 3 competitive/technical research docs: `s1-derive-*.md` (Spotify SongDNA, Gen Z iPod data), `s2-lineage-graph-*.md` (AllMusic/WhoSampled/HDSR), `s3-s4-gift-bridge-*.md` (Hook $10M, Substack music ecosystem, licensing)
- All research shared to idam self-email (gmail message_id 19d9c762d3aec5c8) at 10:21 PT

**Brain atomize state**: 205 notion atoms after re-atomize with all 5 transcripts included. qmd collection `notion` in sync (90 chunks embedded in this run).

**What's DECIDED (from product PDF §10)**:
- Kyma is Obsidian for music (not DJ tool, not generator, not Taste DNA)
- Local-first / user's own library / zero cloud audio storage
- Session-bounded ritual (15-30 min) with persistent "animal track" artifact
- LLM as narrator (closed-weight Claude Sonnet 4.5 under the hood)
- Bridge widget demoted to growth tactic, not product (already shipped Apr 11)
- No taste-signaling / no Wrapped-equivalent user-facing surface
- ICP: taste-rich-skill-poor (iPod revival subculture as on-ramp)
- Pricing: $4.99/mo Pro tier

**What's FLEX (needs Idam)**:
- Exact session length (15 min default, can A/B 10/15/20)
- Share surface for forkable sessions (Phase 2 design)
- Desktop app timeline (Phase 2 vs Phase 3)
- Pricing exact boundaries (4.99 default, can test 3.99-7.99)
- Agent-swarm protocol design (Nostr-like? bespoke? Phase 3)

**Next actions I can do without unblock**:
- [ ] Draft llm-judge consult prompt for Cognitive Amplifier stress-test of Obsidian-for-music
- [ ] Write arxiv preprint on DeepPref + stem-ablation (~4hr, Sonnet Apr 11 suggestion — produces research moat credibility for a16z speedrun deck)
- [ ] a16z SR007 deck drafting (May 17 deadline, 30 days out)
- [ ] First-session onboarding UX mockup (Obsidian-for-music MVP)

**Blocked on Idam**:
- Confirm Obsidian-for-music collapse thesis (read the brain analysis + product PDF)
- Authorize Bridge curator outreach ("send it" for 10 prepped Substack emails)
- Answer 10 open questions from brain analysis §8
- Pricing $4.99 tier approval

**Supersedes**: prior "Kyma OS pipeline" tasks + v3 decomposition doc. v3 is archived at `files/research/kyma-os-02-v3-decomposition-transcripts-integrated-2026-04-17.md` for reference.

---

## 🚨 URGENT DEADLINES — April 15, 2026 (TODAY)

### Tax Filing + Payment
**Status:** Return signed, installment plan NOT set up
**Amount:** $91,647 ($88K federal + $3.5K CA)
**Calendar:** 2026-04-15 09:00-10:00 AM PT (event created)
**Action required TODAY:**
  1. Call IRS 800-829-4933 for long-term installment plan (>K requires phone)
     - Have ready: EIN 41-5195123, Name: IDAM Emmanuel Obiahu
     - Expected: monthly payment plan, interest + penalties apply
  2. OR: Short-term 180-day plan at irs.gov/opa (~$15K/month, $0 fee)
**Blocker:** None - both options available
**Notes:** Same day as Verra consultation (1 PM PT)

### Verra 93A Consultation - Clifford Law
**Status:** Scheduled
**When:** 2026-04-15 13:00-14:00 PM PT (event created)
**Zoom:** 843 2538 8506 / 915998
**Brief:** files/verra-93a-litigation-brief-v5.md
**Amount at stake:** $15K-$75K range
**Reminder:** Job #198 fires 12:45 PM PT
**Notes:** Same day as tax deadline (morning)


## Kai Infra Maintenance

- [x] **Proactive Intel has drifted — audit + rewrite the prompt** — SHIPPED 2026-04-17 21:50 PT. Two-phase rewrite: (i) 21:02 first cut as 5-rotating-flavor menu (TASTE-ALIGNED / ORTHOGONAL / INSPO / BUILD-IDEA / PATTERN-READ), user torched as "boring and rigid"; (ii) 21:50 final version driven by dual-model Opus 4.7 + Sonnet 4.5 consult inside Cognitive Amplifier project — character-voice opening ("Kai, not a feature"), three modes (ask-back / atom-send / silence), 8-step decision monologue replacing scoring function, mechanical leak filter on second-person-observation + hedging + try-hard markers with CONDITION_NOT_MET abort (not regenerate), 3am test reframed as "can he tell whether Kai found it on purpose or by accident?". Anti-quota by design — silence is a valid state; quality bar replaces hit-rate quota. Live verification (2026-04-17 09:38 PT): `GET /api/jobs/103` returns 7588-char prompt, 0 occurrences of OLD 5-flavor markers, all 4 NEW markers present, schedule unchanged at 3600s interval. Artifacts: `files/consultations/2026-04-17-proactive-intel-agent/synthesis.md` (5,021-word judge synthesis), log entries § 20:35 (original CORRECTION) + § 21:02 (first cut) + § 21:50 (final ship). Takes effect on next bot restart (pending Job 213 fire at 02:40 PT).


- [x] **Restart Kai — pick up thinking parser widening + settings + bot.py fail-loud + Proactive Intel rewrite** — DONE 2026-04-17 07:15 PT. Verified: Job 213 fired + auto-removed at 02:47 PT. Bot PID 20589, all 4 fixes loaded (bot.py Path-not-pathlib, widened thinking parser capturing raw keys in kai.log, showThinkingSummaries:true both scopes, Job 103 prompt 7588 chars with 5/5 new markers). Per Idam 2026-04-17: KEEP Opus 4.7, do NOT downgrade to 4.6. Run `launchctl kickstart -k gui/$(id -u)/com.kai.telegram` in a shell you control (not from inside a Kai session — kills the subprocess mid-turn). This activates: widened thinking-block parser (`claude.py:991`), `showThinkingSummaries: true` in both settings.json files, fail-loud auto-pickup with state-change rate limiting (`bot.py:1610`), new Proactive Intel prompt + 60-min interval. Thinking WILL still render as `[reasoning — encrypted by Opus 4.7]` until anthropics/claude-code #31143 ships — that's expected and OK. The widened parser captures raw block keys in kai.log when the encrypted path fires, so we're ready to pick up the summary the instant Anthropic emits it.

- [x] **Fix CONDITION_NOT_MET Telegram spam — cron.py universal silence** — DONE 2026-04-17 07:15 PT, commit 6918da31. Problem: Job 103 Proactive Intel gate-failures (CONDITION_NOT_MET) fired ~4 times overnight and each delivered the literal string "[Job: Proactive Intel]\nCONDITION_NOT_MET" to Idam's Telegram because cron.py's CONDITION_NOT_MET branch was gated on `auto_remove=True` (recurring interval jobs are auto_remove=False). One-token fix: removed `auto_remove and` from the elif guard → CONDITION_NOT_MET is now universal silence signal, with `notify_on_check=True` as the existing opt-in for delivery. Job 214 scheduled to fire at 14:16:22Z (~07:16 PT) to kickstart the bot and load the patched cron.py. Idam mid-stream complaint: "Still getting CONDITIONNOTMET" confirmed root cause.

- [x] **Investigate HTTP/proxy header-injection to force `thinking.display=summarized` on Opus 4.7** — SHIPPED 2026-04-17 08:15 PT. Findings: `files/research/2026-04-17-opus-4-7-thinking-display-paths.md`. Task premise CONFIRMED (Anthropic docs: Opus 4.7 defaults `display: "omitted"`; must explicitly set `"summarized"`). Path 2 (hidden flag): DEAD — zero `display` keys in CLI binary, `--betas` is for HTTP headers not body. Path 3 (hook): DEAD — only `PreToolUse/PostToolUse/PreCompact` hooks exist, no request-mutation point. Path 1 (proxy): VIABLE — CLI natively honors `CLAUDE_CODE_PROXY_URL` + `NODE_EXTRA_CA_CERTS` (but `ANTHROPIC_BASE_URL` has `api.anthropic.com` allowlist — not usable). Path 4 (direct API): skipped — docs are definitive. **Secondary blocker:** v2.1.69+ regression (#30958 OPEN) discards summaries client-side; may also affect stream-json path Kai uses. Recommendation: ~1hr mitmproxy POC if Idam wants readable thinking now, else keep `KAI_CLAUDE_MODEL=claude-opus-4-6` escape hatch dormant (claude.py:413) until Anthropic ships fix. — Claude Code CLI does not expose the `thinking` body param to users, but the Anthropic API accepts `thinking: {"type": "adaptive", "display": "summarized"}`. Paths to investigate: (1) run `claude` subprocess behind a local mitmproxy that rewrites the outgoing `/v1/messages` JSON body to inject the display param — should work because the CLI hits `api.anthropic.com` over HTTPS and we control the trust store; (2) check if `--betas` flag accepts an undocumented cleartext-thinking value by scanning the CLI binary strings (`strings $(which claude) | grep -i thinking`); (3) check if Claude Code has a plugin or hook point that can mutate outgoing requests. Dead end if none: wait for #31143 fix, keep the `KAI_CLAUDE_MODEL` env flag in `claude.py:406` as a reversible emergency escape hatch but do NOT set it.

## IMMEDIATE - Account Migrations (2026-04-12)

### GitHub ✅ COMPLETE
**Status:** DONE (2026-04-13)
**Org:** kymacomputer (https://github.com/kymacomputer)
**Repos transferred:** kyma-production, kyma-engine
**Local remotes:** Updated in both repos
**Commits:** Pushed to new org

### PostHog ✅ COMPLETE  
**Status:** DONE (2026-04-13)
**Org:** Kyma (Project ID: 304123, US Cloud)
**Members:** 
- idam@kyma.stream → Owner
- emmanuel.obiahu@gmail.com → Owner (can be demoted if desired)
**Token:** phc_wX1q6eY6I8N04NpOJLgZzOFoMwXBhRDx07SrMthnuaj
**Config:** web/.env.local and web/.env.vercel.production updated
**Commits:** c19b603, 2d588da, bd2c508 (redeploy trigger)
**401 fix:** Project token corrected
**No old org to delete:** Business email logged in via invitation

### Supabase Ownership Transfer
**Status:** IN PROGRESS - invitation sent (Step 1/3 complete)
**What:** Add idam@kyma.stream to existing Supabase project, transfer ownership from emmanuel.obiahu@gmail.com
**Why:** Preserves all data/config without 900MB import. Simpler than dump+restore.
**Progress:**
  ✅ Step 1: Invitation sent to idam@kyma.stream (Developer role) - DONE 2026-04-13 15:00
  ⏳ Step 2: Accept invitation (awaiting email arrival)
  ⏳ Step 3: Transfer ownership from emmanuel.obiahu@gmail.com
**Screenshot:** .playwright-mcp/supabase-invitation-sent.png
**Next:** Monitor idam@kyma.stream for invitation email, accept, then transfer ownership

### Cancel Personal Subscriptions
**Status:** PENDING - verify migrations first
**Services:** Vercel, Railway, Modal (billing where applicable)
**Timing:** Only after confirming business accounts fully working

### Clean Personal References
**Status:** NOT STARTED
**Required:**
- Grep workspace for emmanuel.obiahu@gmail.com
- Update .env files to idam@kyma.stream
- Update code references
- Clean documentation

### MongoDB for Startups
**Status:** READY TO ACTIVATE - code received, browser window opened
**Credit:** $5,000 Atlas credit
**Code:** ACCELERATOR-PARTNER-5000-F8LXYC (valid through program term)
**Action:** (1) Go to cloud.mongodb.com/v2, (2) Login/create account with idam@kyma.stream, (3) Navigate to Billing, (4) Click "Apply Code", (5) Enter activation code
**URL:** Browser window opened at cloud.mongodb.com
**Email:** Acceptance email received Apr 13, 9:47 AM
**Next:** Complete activation, add to reference_startup_credits.md as COMPLETE

### Notion Service Table
**Status:** NOT STARTED
**Location:** Kyma workspace in idam@kyma.stream Notion
**Columns:** Service | Account Email | Billing Status | Mercury Card | Monthly Cost | Purpose

## Current Focus (updated 2026-04-11 17:45 PDT)

### KYMA BRIDGE — Embeddable 12s Mashup Widget (TOP PRIORITY)
**Decision:** Dual-model consultation (Opus 4.6 + Sonnet 4.5, 2026-04-11) converged: ship Bridge.
**What:** Curators paste 2 Spotify track URLs → get permalink with 12s crossfade player + OG cards.
**Why:** Share the MUSIC, not the LISTENER. Bath thesis compatible. Curators = distribution (Burt's structural holes). SoundCloud embed playbook.
**Strategic positioning (updated Apr 15, 2026):** Spotify Prompted Playlists (Jan 2026) validated agentic discovery market but targeted personal consumption. Bridge deliberately positions AWAY from this — curator distribution vs personal discovery. Bridge = open sharing, Spotify = closed personalization. This differentiation is now MORE valuable, not less.
**Kill criterion:** 3+ unprompted curator re-uses in 14 days.
**Code:** `kyma-engine/api/bridge.py` on :8881.
**Synthesis:** `files/consultation-synthesis-2026-04-11.md`

- [x] **Bridge MVP** — DONE. `api/bridge.py` on :8881. Search, create, permalink, 12s crossfade, OG meta, analytics. Commit 2ec2e00.
- [x] **Quality filter** — DONE. DeepPref cosine scoring. Range: -97% (anti-correlated) to 98% (highly compatible).
- [x] **Curator seeding** — DONE. 10 bridges created across genres. 10 Substack curators researched and matched. Outreach plan: `docs/curator-seeding-plan.md`. Commit 0b461fa. **BLOCKED on Idam's "send it"** for outbound emails. Public URL available via Cloudflare tunnel.
- [ ] **Hedge: arxiv preprint** — SKIPPED for now. Preprint stronger with 14-day engagement data from curator seeding. Revisit after kill window.
- [ ] **Hedge: consulting outreach** — SKIPPED. Email-gated + premature before primary bet has 14 days to prove itself.

### BATH PLAYLIST AGENT — Essay-Driven Reframe (PAUSED — infra feeds Bridge)
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
- [ ] **Real user validation** — Gate infrastructure built. Weekly digest cron wired (Job 201, 7-day interval). Need real users to generate meaningful data. Idam notified (Job 200).
  - **Dogfood UI LIVE** on :8880 (`api/dogfood.py`, commit ba40f47). Idam's library: 962/4,280 tracks matched to MERT set. Play-time-weighted 64d taste vector. Discovery + mashup preview + Like/Nope signals with EMA learning. 11ms response.

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

**COMPLETED: 4-Model Consultation Synthesis #1 (2026-04-11 AM)**
- 4 responses: Opus 4.6 + Sonnet 4.5 Extended, each on exploratory AND goal-directed prompts
- Full synthesis: `files/consultation-synthesis-2026-04-11.md`
- **Key insight:** Feedback loop (anchor + mashup + EMA) is cheap to iterate — cosine similarity in 64d, even though the encoder is non-linear.

**COMPLETED: "What's Next?" Consultation #2 (2026-04-11 PM)**
- 2 responses: Opus 4.6 Extended + Sonnet 4.5 Extended on "highest-leverage next work?"
- Full synthesis: `files/consultation-synthesis-2026-04-11.md` (overwritten with #2 synthesis)
- Opus responses: `.playwright-mcp/opus-response.md`, Sonnet: `.playwright-mcp/sonnet-response.md`
- **VERDICT: Ship "Kyma Bridge" — embeddable 12s mashup widget for music curators (B2B2C)**
  - Opus product (Bridge widget for Pitchfork/Substack/NTS) + Sonnet risk framework (Gambler's Ruin)
  - Distribution via curators (they already have the audience), not outbound B2B sales
  - Kill criterion: 3+ unprompted curator re-uses in 14 days
  - Hedge: arxiv preprint (4hr) + consulting outreach ($200/hr stem ablation research)
  - **Core insight:** Share the MUSIC, not the LISTENER — Bridge is shareable AND privacy-compatible
  - STOP: more research phases, dogfood UI expansion, fundraise deck polish

**Build queue (dependency-ordered, no time-boxing — full details in kyma-engine TASKS.md):**
- ~~Behavioral EMA~~ ✅ DONE | ~~Taste Vector Arithmetic~~ ✅ DONE
- ~~Anchor Selection~~ ✅ | ~~Fisher Probes~~ ✅ | ~~Wormhole Detector~~ ✅ | ~~Gift Bridge~~ ✅ | ~~Anti-Hub Router~~ ✅
- ~~MERT Layer Routing~~ ✅ (L6 beats L24 raw, per-user routing +6.8%, 65% users benefit)
- ~~Curator Residual~~ ✅ (curators genuinely distinct, inter-cos 0.376, 2D effective dim, α=0.1 → 91% unique discoveries)
- ~~Koopman Operator~~ ✅ (time-delay DMD τ=3: -65% error vs naive, Takens embedding, zero oscillatory modes)
- ~~Stem-ablation DeepPref~~ ✅ (VOCALS=ZERO preference signal ρ=-0.017; other/texture=91.5% of signal ρ=0.214; bass=80.1%; drums=77.5%. Demucs blocker resolved: .venv-train arm64+MPS)
- ~~Bridge Segment Localization~~ ✅ (signal-processing scorer, 50/50 tracks, score 0.355-0.864, top segments all voc=0, mid-track peaks 34%, 8.6s mean duration)
- ~~Persistent Homology~~ ✅ (4d manifold, 262 persistent loops, 2 permanent voids, fully connected, NOT hierarchical)
- ~~Temporal Community Detection~~ ✅ (674 communities, 18.8% cross-community, Take Me Out = #1 bridge track across 72 comms, language=tightest bubbles)
- **RESEARCH:** Causal Skip Attribution (needs product loop)

### Kai Brain Infrastructure (updated 2026-04-17 22:30 PDT)
Ranks 1-3 shipped + 4 consult-driven fixes (commit 964ebe9e). 634 atoms, 617 supersede edges. top_of_mind ranked-injection of 80 primary + 27 dependencies. Synthesis: `files/consultations/2026-04-17-brain-memory-followup/synthesis.md`.
- [x] **Positional-attention control experiment** — SHIPPED 2026-04-17 22:40 PT. OLD_CONTROL (trailer + old flat stack) reproduced 2/3 wins: `exp_r07_status` positional win confirmed, `state_freshness` duplicated by metadata/log annotation, `focus_now` remained the only genuine architectural claim. Verdict: Sonnet's "wait" strengthened; only cross-atom synthesis clearly earns complexity. Artifacts: `files/consultations/2026-04-17-brain-memory-followup/control_experiment.py`, `files/consultations/2026-04-17-brain-memory-followup/control_experiment_result.md`, `/tmp/brain_ab_results/control-20260417-052051.json`.
- [x] **Unified 15-query battery + blind judges** — SHIPPED 2026-04-17 23:20 PT. Battery v1: 15 queries × 3 conditions (45 calls) plus v2 adversarial/abstention augment. Two independent blind judge writeups converged: new_brain 25 / old_base 19 / old_trailer 7 / ties 9, strongest on temporal-span + long-horizon drift, decisive on adversarial reversal-chain. Consolidated findings: `files/consultations/2026-04-17-brain-memory-followup/FINDINGS.md`. Raw: `/tmp/brain_ab_results/unified-battery-20260417-054129.json`, `/tmp/brain_ab_results/battery-v2-aug-20260417-054618.json`.
- [ ] **Activation-quality calibration** — `sources_cited` / tool-chain instrumentation shipped inside battery v2, but Spearman correlation of cited-atoms vs activation rank is still open. Daily log explicitly deferred this as a 1-hour next session item after the anti-cherry-pick correction.
- [ ] **Atomizer noise fix** — entity-overlap heuristic produces false-positive supersede pairs. Require STRONG topic token (MODEL-/EXP-R-/file-scoped heading-match) instead of generic 2-entity overlap.
- [x] **Task Puller job** — SHIPPED 2026-04-17 23:05 PT. Job #212 on 2-hour cadence reads `TASKS.md`, picks one ready non-claimed item, executes with DoD + [OBSERVED] artifacts, commits/pushes, then marks completion. Safety rails: quiet-period gate (>=90m since last user msg), strict allowlist, one-task-per-fire, ATTENTION.json write on blocked decisions. Prompt: `.claude/task-puller-prompt.md`.
- [x] **Ingest Kyma Space 2.0 Notion workspace** — SHIPPED 2026-04-17 07:45 PT, widened 08:05 PT. 128 pages + 20 DB manifests fetched → `/Users/idamo/kai/notion-kyma-space-2/`. Filter rule (per Idam: "everything in Kyma OS, like meeting notes/transcripts, Document hub etc"): keep 2024+, archive pre-2024. Final: 53 files in main dir (YC app drafts, Kyma investor research, pivot thesis, DJ discovery MVP, meeting notes/transcripts, Active Projects, timeline/deadlines, financial astrology 2026, productivity OS templates, teamspace, personal dashboard, visa logistics), 95 archived to `notion-kyma-space-2-archive-personal/` (2021-2023 journals/bookshelf/movies/habit-tracker/Netflix-notes). qmd collection `notion`: 53 docs indexed. atomize.py patched: `notion` scope + glob walker, `_log_file_date` regex extended for `/notion-kyma-space-2/YYYY-MM-DD-` → 82 notion atoms with proper chronology dates. Brain total: ~744 atoms. `qmd search "DJ discovery MVP"` returns the MVP plan at 39% top. Artifacts: `scripts/notion_ingest.py`, `/Users/idamo/kai/notion-kyma-space-2/`, `.memory/logs/2026-04-17.md` (§ 07:18 STARTED, § 07:45 COMPLETED, § 08:05 AMENDMENT).
- [x] **Wire qmd refresh into brain workflow** — SHIPPED 2026-04-17 07:55 PT. `atomize.py` now runs `qmd update + qmd embed` automatically after writing atoms, keeping atoms / BM25 / vector search aligned. Default ON; skip with `--no-refresh-qmd`. Verified: `--scope notion` returns `[atomize] qmd update: ✓ All collections updated.` + `[atomize] qmd embed: ✓ All content hashes already have embeddings.`. `refresh_qmd()` helper at `src/kai/brain/atomize.py:591` with 300s update timeout + 900s embed timeout + graceful fallback if qmd binary missing.

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
- **Kai dashboard tunnel**: Cloudflare named tunnel `kai-dashboard` → https://kai.kyma.stream (LaunchAgent, auto-starts on boot). Replaced ngrok (killed Apr 11).

### Data (SSD)
- Spotify: 256M tracks (33GB metadata), 256M audio features (39GB), 800K MERT (6.1GB)
- FAISS: 254.8M × 12d, 3.3GB index
- Curated transitions: 27.2M matched

## Open (Non-Pivot)
- [ ] **Covered CA eligibility** — Needs Idam login.
- [ ] **Fundraise narrative reframe** — Now framed around Taste Oracle.
