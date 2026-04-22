# Research Queue — Background Intelligence Gathering
> Priority: P0 (urgent) > P1 (this week) > P2 (when idle)
> Status: QUEUED | IN_PROGRESS | DONE | KILLED
> Results go to: .claude/research-results/YYYY-MM-DD-{slug}.md

## Active Queue

### P1 — This Week
- [x] **Claude Code SDK** — DONE 2026-03-17. Results: [research-results/2026-03-17-claude-agent-sdk.md](research-results/2026-03-17-claude-agent-sdk.md). TL;DR: Yes — two paths: (1) Claude Code built-in subagents (free, already working), (2) Agent SDK programmatic (`pip install claude-agent-sdk`, requires API key = paid). Recommendation: use built-in subagents for now, create custom agents in `~/.claude/agents/`.
- [x] **Telegram bot rate limits** — DONE 2026-03-18. Results: [research-results/2026-03-18-telegram-bot-api-rate-limits.md](research-results/2026-03-18-telegram-bot-api-rate-limits.md). TL;DR: ~1 msg/sec per chat, ~30 msg/sec global, groups 20/min, no batch API, 429 blocks ALL users. Self-hosted Bot API doesn't help with message rate limits.
- [x] **APScheduler async patterns** — DONE 2026-03-19. Results: [research-results/2026-03-19-apscheduler-async-patterns.md](research-results/2026-03-19-apscheduler-async-patterns.md). TL;DR: Architecture is correct, no blocking. Three fixes: increase misfire_grace_time (1→300s, jobs silently dropping), add APScheduler error listener, notify user on job failures. Stay on 3.x, 4.x still alpha.

- [x] **OpenClaw RL1 paper (Princeton)** — DONE 2026-03-20. Results: [research-results/2026-03-20-openclaw-rl1-full-analysis.md](research-results/2026-03-20-openclaw-rl1-full-analysis.md). TL;DR: Validates Kyma taste-learning thesis. Two reward-model-free methods (Binary RL + OPD) map to mixing workflows. ~128 turns to personalize = 1-3 mixing sessions. Needs adaptation for continuous audio parameters. Follow-ups: CLAP embedding quality, Bradley-Terry convergence rate, undo classifier accuracy, collaborative filtering threshold.
- [x] **Agent SDK cost model** — DONE 2026-03-21. Results: [research-results/2026-03-21-agent-sdk-cost-model.md](research-results/2026-03-21-agent-sdk-cost-model.md). TL;DR: Stay on Claude Max ($200/mo). At current usage (~120 turns/day), API hybrid model costs ~$198/mo — break-even. Max wins on simplicity + no billing variance. Switch trigger: if usage drops below 80 turns/day or when Kai v2 needs programmatic model routing. Background jobs on Haiku+Batch would save $3.55/mo — not worth engineering yet.

### P1.5 — Kyma Product (from Karpathy interview insights)
- [x] **Karpathy Loop for Kyma pipeline optimization** — DONE 2026-03-22. Results: [research-results/2026-03-22-karpathy-loop-kyma.md](research-results/2026-03-22-karpathy-loop-kyma.md). TL;DR: 3-file architecture, MRR metric, ~200 experiments/hour, 22 seeded ideas, ready to implement.
- [x] **Autonomy slider UX patterns** — DONE 2026-04-04. Results: [research-results/2026-04-04-autonomy-slider-ux.md](research-results/2026-04-04-autonomy-slider-ux.md). TL;DR: Per-domain graduated control (not single slider) + undo-as-trust-accelerator. 4 levels (Scout/Curator/Night Owl/Ambassador). Night Owl overnight crate builder = killer feature (ChatGPT Pulse for music). Earned autonomy > user-set. 20+ sources, 6 product implementations analyzed.
- [x] **Model speciation evaluation for Kyma stack** — DONE 2026-03-23. Results: research-results/2026-03-23-model-speciation-kyma.md. TL;DR: YES, specialist ensemble wins. MuQ + Demucs stems = 90.4% (vs 72.4% alone). MuQ >> MERT 7/9 tasks. MT² 5.3M beats MERT. On-device: 10M total.

### P2 — When Idle
- [x] **Voice mode optimization** — DONE 2026-04-14. Results: [research-results/2026-04-14-voice-mode-optimization.md](research-results/2026-04-14-voice-mode-optimization.md). TL;DR: Deepgram Nova-2 recommended for Telegram voice transcription. <300ms latency creates "instant" feel (vs 450-500ms Whisper). 8.4% WER sufficient for conversational content. Cost negligible ($0.90/month). AssemblyAI better accuracy (6.88% WER) but overkill for voice notes.
- [x] **Local LLM for relevance filtering** — DONE 2026-04-15. Results: [research-results/2026-04-15-local-llm-message-triage.md](research-results/2026-04-15-local-llm-message-triage.md). TL;DR: YES, highly feasible. Phi-3 mini 3.8B via MLX framework recommended. <2s latency, ~5GB memory, 28-40 tok/s on M3/M4, \/bin/zsh/month cost. 85-90% classification accuracy estimated. MLX 20-40% faster than llama.cpp on Apple Silicon.
- [ ] **Structured outputs from Claude** — Can inner Claude return JSON reliably for outcome tracking? (QUEUED)

### Follow-ups from Local LLM Research (2026-04-15)
- [ ] **Qwen 2.5 1.5B benchmark** — New Dec 2025 model claims 72% MMLU at 1.5B params. Could be faster than Phi-3 mini. Benchmark on M-series (tok/s, latency, memory, classification accuracy). (QUEUED, P2)
- [ ] **Structured output reliability for local LLMs** — Test JSON schema adherence across 1000 sample messages. How often does Phi-3 break schema? Does Llama 3.3 do better? Multi-label classification vs single-label. (QUEUED, P2)
- [ ] **Cold start optimization** — Can we use mmap to keep model weights memory-mapped but not active? Reduce first-message latency from 2s to <500ms without keeping full model in RAM. (QUEUED, P2)
- [ ] **Feedback loop fine-tuning** — After 1000 messages with human corrections, fine-tune Phi-3 on Kai's specific message patterns (question types, urgency markers, entity extraction). Measure accuracy delta vs base model. (QUEUED, P2)

### Follow-ups from Agent SDK Cost Model
- [ ] **Kai token usage instrumentation** — Build actual token counting into Kai to replace estimates with real data. Log input/output tokens per operation type for 7 days. (QUEUED, P2)
- [ ] **Anthropic API rate limits vs Max rate limits** — Compare API tier rate limits to Max 20x limits. If API has higher throughput for burst workloads, that's a reason to switch independent of cost. (QUEUED, P2)


### Follow-ups from EXP-R01 + Per-Stem Research (2026-04-11)
- [x] **EXP-R01.5: Per-stem Bradley-Terry** — DONE 2026-04-13. Results: [research-results/2026-04-13-exp-r01-5-per-stem-bt-research-update.md](research-results/2026-04-13-exp-r01-5-per-stem-bt-research-update.md). TL;DR: Foundational research complete. Two Jan-Mar 2026 papers validate per-stem architecture (+3.6pp over full-mix), BUT they use cosine similarity (collapses under hard negatives). Experiment design ready but DOWNGRADED to P2 — run after Bridge validates PMF. Current DeepPref (min=0.4600) sufficient for MVP. 4x compute + 12x storage not justified until product validation.
- [ ] **Intransitive preference cycles** — From ICLR 2025 "Rethinking BT". Test for A->B, B->C, C->A in DJ transitions. If ProjDot handles intransitivity -> stronger result than ICLR paper expects. (QUEUED, P2)
- [x] **Curriculum training prototype** — DONE 2026-04-11. Completed as EXP-R01 Phase 4c. Results: kyma-engine work/outputs/exp_r01_learned/exp_r01_curriculum_results.json. Curriculum min=0.341 on L24, solves specialization trap.

### Follow-ups from EXP-R01.5 Research (2026-04-13)
- [ ] **Intransitive preference cycles** — Test for A→B, B→C, C→A in DJ transitions. If cycles exist, Bradley-Terry assumptions break. Use curated_transitions.db + EXP-R01 hard negative protocol. Papers: ICLR 2025 "Beyond Bradley-Terry Models" (GPM embedding handles intransitive with near-perfect accuracy vs BT random guessing). (QUEUED, P2)
- [ ] **Per-stem layer routing** — Do vocals peak at L18 (semantic), drums at L5 (acoustic), bass at L6, other/residuals at L24 (holistic)? Run per-stem MERT layer sweep on 1K track sample before committing to full EXP-R01.5 (4x compute). Fast validation experiment. (QUEUED, P2)



### Follow-ups from Co-occurrence vs Compatibility Research (2026-04-18)
- [x] **[P1] Contrast-vs-overlap A/B on Bridge creation rate** — DONE 2026-04-22 (experimental-design phase). Results: [research-results/2026-04-22-contrast-vs-overlap-bridge-ab.md](research-results/2026-04-22-contrast-vs-overlap-bridge-ab.md). TL;DR: original 20 vs 20 scope is severely underpowered (need ~196/arm for realistic 2x lift detection). DOWNGRADED to N=20 directional pilot. Sonic-distance metric must be conjunction of raw-MERT-L24-cosine + feature-distance, NOT DeepPref cosine (overlap-biased). Re-share tracking blocked on Bridge referer telemetry verification — Cloudflare tunnel log tail as fallback. 3 follow-ups queued.
- [ ] **[P2] DeepPref cosine × co-mention weight joint distribution** — plot scatter on current 814 edges. Any 4-quadrant structure? Does the joint distribution give us "overlap + sonic-agree" vs "overlap + sonic-surprise" vs "no-overlap + sonic-agree" vs "no-overlap + sonic-surprise"? Kill: if strongly anti-correlated, the two signals are literally the same with a sign flip. (QUEUED)
- [ ] **[P2] metapath2vec prototype on source-item-entity walks** — FlavorGraph's approach was heterogeneous. Our analog: (source → item → entity → item → source) random walks, skip-gram embedding. Does this capture edges our homogeneous graph misses? Small test: 1000 edges, compare ranking vs current correlator. (QUEUED)
- [ ] **[P3] Text-conditioned retrieval epistemic consult** — philosophical question: does text-conditioned retrieval (MuQ-MuLan, LAION CLAP) fundamentally optimize for overlap at the expense of contrast? If Nature Commun. 2025 BPM/key gap + FlavorGraph finding converge, text-conditioning is wrong encoder strategy for discovery specifically. Worth a dual-model consult before further encoder investment. (QUEUED)

### Follow-ups from Contrast-vs-Overlap A/B Experimental Design (2026-04-22)
- [ ] **[P1] Make Spotify enrichment optional in bridge.py** — unblock `/api/bridge/stats` referer telemetry (currently gated on external drive mount). ~1hr change. Needed for contrast-vs-overlap A/B and future Bridge measurement. (QUEUED)
- [ ] **[P2] Empirical re-share base rate for bridge/mashup widgets** — SoundCloud embed CTR, Substack track-click rates, Apple Music share-card CTR. Validates the 10% baseline assumption in the power calc. (QUEUED)
- [ ] **[P2] Per-dimension contrast taxonomy** — rhythmic (BPM gap >= 20) vs timbral (spectral centroid) vs emotional (valence gap) vs structural (song-form mismatch). Which dimension produces the best FlavorGraph-East-Asian analog in music? (QUEUED)
- [ ] **[P3] ISMIR 2026 short paper** — if contrast-vs-overlap pilot produces any signal, publish as "First empirical test of the FlavorGraph East-Asian-contrast hypothesis in music recommendation." Strategic fundraise benefit: MIR credential. (QUEUED, post-pilot only)


- [ ] **[P2] Auto-continuation task picker defect** — 2026-04-22: the periodic-refresh auto-picker offered the deferred arxiv-preprint task despite its own description saying "do NOT auto-pick during Apr 18–May 17 window." Picker should filter on DEFERRED/BLOCKED/kill-list markers before offering. Same class of bug as Task Puller #212 might have (check its prompt at .claude/task-puller-prompt.md). Add a marker-regex filter: grep for "DEFERRED|do NOT auto-pick|BLOCKED|KILLED" in candidate task body, skip if matched. (QUEUED)

## Completed Research
<!-- Move here when done, with link to results file -->

## Killed
<!-- Move here with reason -->

### Follow-ups from Karpathy Loop Design
- [x] **MERT layer selection for DJ similarity** — RESOLVED by EXP-R01 (2026-04-10). Layers 5 (acoustic), 18 (semantic), 24 (CLS/holistic) are the production layers. L24 most robust under hard negatives (87.5% retention).
- [ ] **Chunk-level vs set-level matching** — Does matching DJ sets at the chunk level (then aggregating scores) outperform averaging chunks into a single embedding? Requires architectural change in the pipeline. (QUEUED, P2)

### Follow-ups from Model Speciation Research
- [x] **MuQ migration path** — DONE 2026-03-25. Results: [research-results/2026-03-25-muq-migration-path.md](research-results/2026-03-25-muq-migration-path.md). TL;DR: MuQ beats MERT 7/9 tasks but same MLM objective = likely same collapse. MuQ-MuLan (contrastive, 700M) better for retrieval. CC-BY-NC license. Test 100 sets before committing.
- [x] **Per-stem MuQ embeddings architecture** — DONE 2026-04-11. Results: [research-results/2026-04-11-per-stem-embeddings-architecture.md](research-results/2026-04-11-per-stem-embeddings-architecture.md). TL;DR: Stay MERT, don't migrate to MuQ. Add per-stem as EXP-R01.5 (Demucs stems x MERT layers x ProjDot64). Two 2025-2026 papers validate architecture but use cosine (collapses under hard negatives). MERT multi-layer is more advanced.
- [ ] **MT² on-device feasibility** — Benchmark MT² (5.3M) inference latency on Apple Silicon. Can it run real-time on iPhone/iPad? (QUEUED, P2)
- [ ] **Moises-Light vs Demucs quality** — Run both on 20 test tracks, compare SDR and downstream similarity accuracy. If competitive, plan migration. (QUEUED, P2)

### Follow-ups from MuQ Migration Research
- [x] **MuQ-MuLan taste-conditioned retrieval** — KILLED 2026-04-17. Results: [research-results/2026-04-17-muq-mulan-taste-retrieval.md](research-results/2026-04-17-muq-mulan-taste-retrieval.md). TL;DR: Two blockers converge — (1) CC-BY-NC 4.0 weights kill commercial use (confirmed on HF page), (2) text-audio contrastive models have known BPM/key gap (chance-level per Nature Commun. 2025). Stay on DeepPref L24. Added follow-up: LAION CLAP zero-shot (Apache-2.0) as cheap alternative.
- [ ] **Apache 2.0 encoder fine-tuning** — Can M2D-CLAP + LoRA contrastive fine-tuning on DJ pairs match MuQ-MuLan quality while staying commercially licensable? Critical for fundraise. (QUEUED, P2)
- [ ] **LAION CLAP zero-shot on Kyma preference set** — Run LAION `larger_clap_music` (Apache-2.0) zero-shot on 1K sampled tracks, score a 100-pair held-out taste-preference set with cosine similarity, compare vs DeepPref L24 baseline. Kill criterion: AUC < DeepPref - 10pp = stop. Cost: <2hr Apple Silicon, no training. From 2026-04-17 MuQ-MuLan research. (QUEUED, P2)
- [ ] **Text-conditioned vs structural-graph discovery** — Strategic question: does text-conditioned retrieval fundamentally optimize for the wrong thing (overlap) while discovery requires contrast? FlavorGraph East-Asian cuisine finding isomorphic. Worth a deeper epistemic consultation. From 2026-04-17 MuQ-MuLan research. (QUEUED, P3)


### From Proactive Intel Scan (2026-04-11 05:16 PDT)
- **ICMR '25: Bridging Semantic and User Preference Spaces** (arxiv 2505.23298) — hierarchical two-stage contrastive learning for music. Directly relevant to ProjDot64 preference projection. Priority: P2 (validate/differentiate).
- **Emergent musical properties of transformer under contrastive SSL** (arxiv 2506.23873) — layer-wise analysis of what transformers learn. Compare against Phase 3b orthogonality findings. Priority: P3.


## DONE - Co-occurrence vs Compatibility Hypothesis Challenge (2026-04-18)
**Status:** DONE. Results: [research-results/2026-04-18-cooccurrence-vs-compatibility.md](research-results/2026-04-18-cooccurrence-vs-compatibility.md).
**TL;DR:** Confirmed. Spotify Research (ISMIR 2021) measured playlist-cooccurrence × acoustic-similarity correlation = **-0.029** (essentially zero with negative tilt). FlavorGraph (Nature 2020) East-Asian result validates the contrast-creates-harmony principle as a real alternative pairing philosophy. Our regularized weird_rank (shipped 2026-04-18) is a cultural-cluster detector, NOT a taste-compatibility predictor. The real compatibility signal is DeepPref cosine on MERT vectors — already computed in Bridge widget but NOT used in weird_rank. Strategic reframe for a16z pitch: "Kyma is the first music taste graph that surfaces both Western-overlap AND East-Asian-contrast pairings." Generated 4 follow-ups below.

## DONE - Heterogeneous Graph Architecture (FlavorGraph Analog) (2026-04-18)
**Status:** Rolled into above research (same ~~FlavorGraph~~ source material). metapath2vec prototype queued as P2 follow-up `metapath2vec prototype on source-item-entity walks` below.
