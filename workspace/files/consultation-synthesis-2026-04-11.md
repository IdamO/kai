# Consultation Synthesis: Research Agenda Tiebreak
**Date:** 2026-04-11
**Judge:** Kai (tiebreak across 4 consultant responses)
**Prompt sets:** Exploratory (open-ended) + Goal-Directed (product-mapped)
**Models:** Opus 4.6 + Sonnet 4.5 Extended, each on both prompts

---

## Final Ranking

### #1: Opus 4.6 Goal-Directed (7,766 chars)
**Why it wins:** Highest signal-per-token of any response. Zero ceremony ("I'm going to give you substance, not framework theater"). Every idea traces to what the USER FEELS. The keystone insight — anchor selection model is THE build, everything else supports the feedback loop (anchor + mashup + EMA update) — is the correct strategic reduction. Cold start via mashup triangulation (D-optimal design, 90s to usable preference vector) is the most buildable cold-start solution. Gift bridge as midpoint in 64d is elegant. Curator residual as "secret guest DJ" for the weekly crate is a product idea nobody else surfaced at that level.

**Best for:** "What do I build in the next 2 weeks?"

### #2: Sonnet 4.5 Goal-Directed (27,071 chars)
**Why it's close:** Most architecturally complete response. 15 items in 4 tiers with full input/output/loss/data specs. Contains the two single most novel ideas across ALL 4 responses: (1) Bridge Segment Localization — U-Net to find the 4-8 bar segment where a bridge track maximally activates both communities, making mashups SURGICAL ("it knows exactly why I'll like this"); (2) Persistent Homology of taste space — holes, voids, geodesics, unreachable vectors. Nobody has mapped the TOPOLOGY of musical taste at scale. This is the Nature paper candidate.

The strategic reframe — "The Computational Theory of Taste" — is the strongest framing across all 4 responses. The cancer shell is a REQUIREMENT of the theory (64d projected to 1-2d for a dashboard DESTROYS information), not a UX choice.

**Best for:** "What's our 6-month research agenda + publishable findings?"

### #3: Opus 4.6 Exploratory (8,523 chars)
**Why it's strong:** Stem-ablation ProjDot as "DO FIRST" is the correct first experiment (converts geometric finding into mechanistic musicology in ~1 week). TCAV for music and sparse autoencoders on MERT (Anthropic-style monosemantic features) are genuinely frontier ideas nobody else is pursuing. "Sell the ruler, not the playlist" is the sharpest single strategic line. Bradley-Terry A&R (curator alpha vectors) is a strong B2B play.

**Limitation:** More research catalog than product roadmap. Some ideas (sync licensing search, A&R tool) are B2B plays that don't connect to the core consumer product loop.

**Best for:** "What experiments establish us as THE lab?"

### #4: Sonnet 4.5 Exploratory (26,466 chars)
**Why it's fourth:** Most creative but most scattered. Taste vector arithmetic ("word2vec moment for music") is a great 1-day experiment with high interpretability. Taste Atlas (name the 64 dimensions via RSA) is interesting. But several ideas are whimsical without clear product connection (listener chronotypes, playlist genome). The "preference infrastructure company — music is first vertical" reframe is strategically interesting but generic.

**Best for:** "What wild experiments might lead to unexpected discoveries?"

---

## Per-Question Verdicts

### 1. Which models to train NEXT?
**Winner: Opus Goal.** Anchor Selection Model as keystone is the right call. Input: user history + candidate discovery. Output: which anchor maximizes P(accept | mashup coherent). Data: 4.44M DJ transitions filtered by ListenBrainz follow-through. This directly optimizes the Bath Playlist moment.

**Runner-up: Sonnet Goal.** Multi-Task Preference Decomposition (3x64d with orthogonality constraints + context gating) is more architecturally elegant but harder to validate. Build Opus's version first, upgrade to Sonnet's architecture when you need context-awareness.

### 2. Cold start?
**TIE.** Both converge on the same insight from different angles:
- Opus: "Mashup Triangulation" — D-optimal design over 64d basis, 5 mashups, accept/skip localizes in 90s
- Sonnet: "Fisher Information" — maximize determinant of Fisher info matrix, 7 clips, binary search, <2 min

Same idea. Opus frames it as mashups (product), Sonnet frames it as clips (research). **Use Opus's framing (mashups as probes) with Sonnet's math (Fisher information for question selection).**

### 3. Gift mechanism / network effects?
**Winner: Opus Goal.** Midpoint track in 64d between A and B's centroids. Find the real track closest to midpoint. Send that. Neither user sees the other's vector. The midpoint operation IS the entire information flow. Elegant, buildable, preserves privacy.

Sonnet's preference intersection approach (shared subspace via PCA) is mathematically richer but harder to explain and implement.

### 4. DJ/listener divergence?
**Winner: Opus Goal.** "Curator Residual" — train a 27d model per active curator (the 27% DJ-specific residual). Weekly crate gets a "secret guest curator" personality. Users feel the crate is alive, not algorithmic. This is product-level thinking.

Sonnet proposed "curator style transfer" (convert listener prefs to curator prefs) which is technically interesting but doesn't clearly map to a user-facing moment.

### 5. Weekly crate improvement?
**Winner: Opus Goal (for v1), Sonnet Goal (for v2).**
- v1: EMA in the rotated basis. Skip = negative gradient, full-listen = positive. Provably stable because preference is linear and basis is orthogonal. Build this first.
- v2: Causal Skip Attribution (Sonnet). WHY did they skip? Acoustic mismatch? Semantic? Transition quality? Per-dimension updates instead of whole-vector. Build this after the EMA loop works.

### 6. "Holy shit" research finding?
**Winner: Sonnet Goal.** Persistent homology of the 64d taste space. Map the topology — holes, voids, attractors, geodesics. "Some preference vectors are UNREACHABLE from others (you can't get from metal to classical without passing through prog rock)." This is genuinely a Nature Human Behaviour paper and a product feature simultaneously ("the agent knows the PATH between where you are and where you're going").

**Runner-up: Opus Goal.** Wormhole audio signature in MERT layer X. "The structure of music discovery is encoded in the audio itself." 70% replication estimate. More specific, more testable, less paradigm-shifting.

**Also notable: Opus Exploratory.** Sparse autoencoders on MERT (Anthropic-style mechanistic interpretability for music). If monosemantic music features exist, that's the equivalent of finding neurons in MERT that encode "sidechain compression" or "jazz harmony."

### 7. Network science?
**Winner: Sonnet Goal.** Temporal community detection — genre birth/death/merger/split over time. Phase transitions (percolation thresholds). Crossover event identification.

Both Opus responses also propose wormhole detection, which is complementary. Run Louvain at multiple resolutions + betweenness centrality to distinguish bridges (adjacent communities) from wormholes (distant communities).

### 8. 80% capabilities to assemble?
**Winner: Sonnet Goal.** Five concrete "Capability A-E" entries:
- A: Real-time preference update (EMA + Kalman filter)
- B: Automatic playlist arc generation (beam search over transitions)
- C: Acoustic fingerprint for mashup synthesis (differentiable DSP)
- D: Bridge discovery via embedding geometry (convex hull surface)
- E: (implied) Composition of all existing models

---

## Convergences (ideas in 3+ responses — HIGH CONVICTION)

| Idea | Appeared In | Verdict |
|---|---|---|
| Wormhole detection | All 4 | DO IT. Run Louvain at multiple resolutions, measure betweenness across distant communities, train audio predictor. |
| Cold start via discriminative probes | All 4 | DO IT. Fisher-optimal mashup probes, 5-7 interactions, <2 min to usable 64d vector. |
| Temporal taste dynamics | Opus Goal, Sonnet Goal, Sonnet Exploratory | DO IT. Start with simple EMA, upgrade to Koopman operator when you have longitudinal data. |
| Gift as private taste intersection | Opus Goal, Sonnet Goal | DO IT. Midpoint in 64d (Opus) is the v1. |
| Curator residual / DJ-listener divergence | Opus Goal, Sonnet Goal, Opus Exploratory | DO IT. 27d residual per curator for weekly crate personality. |
| Anti-hub / niche routing | Opus Goal, Sonnet Goal | DO IT. Penalize hub tracks by degree^alpha, tune alpha per user. |
| Online preference EMA | Opus Goal, Sonnet Goal | DO IT. Linearity finding makes this provably stable. |

## Divergences (unique to one response — EXPLORE)

| Idea | Source | Verdict |
|---|---|---|
| Bridge Segment Localization (U-Net) | Sonnet Goal | EXPLORE. Novel, testable, high product impact if it works. |
| Persistent Homology of taste space | Sonnet Goal | EXPLORE. "Nature paper" candidate. Requires topological data analysis expertise. |
| Causal Skip Attribution | Sonnet Goal | BUILD AFTER EMA loop works. Per-dimension skip understanding. |
| Taste Vector Arithmetic | Sonnet Exploratory | 1-DAY EXPERIMENT. High interpretability, validates compositionality. |
| Stem-ablation ProjDot | Opus Exploratory | DO FIRST. 1-week experiment on existing MERT cache. Mechanistic musicology. |
| TCAV / SAE on MERT | Opus Exploratory | EXPLORE. Mechanistic interpretability for music. |
| Curator Residual as "secret guest DJ" | Opus Goal | BUILD. Makes weekly crate feel alive. |
| MERT Layer Routing per user | Opus Goal | BUILD. Softmax over 25 layers. "Some users are L18 people." Zero new data needed. |

---

## The Build Queue (synthesized from all 4)

### Week 1-2: The Feedback Loop
1. **Stem-ablation ProjDot** (Opus Exploratory) — mechanistic musicology, 1 week
2. **Anchor Selection Model** (Opus Goal) — the keystone build
3. **Behavioral EMA Update** (Opus Goal) — provably stable preference updates
4. **Taste Vector Arithmetic** (Sonnet Exploratory) — 1-day compositionality validation

### Week 3-4: Cold Start + Crate
5. **Fisher-Optimal Mashup Probes** (Opus Goal + Sonnet Goal) — cold start in 90s
6. **MERT Layer Routing** (Opus Goal) — instant personalization axis
7. **Curator Residual** (Opus Goal) — weekly crate personality

### Month 2: Network Effects + Discovery
8. **Gift Bridge Midpoint** (Opus Goal) — private taste sharing
9. **Anti-Hub Router** (Opus Goal + Sonnet Goal) — niche discovery
10. **Wormhole Detector** (All 4) — the "holy shit" product feature

### Month 3+: Research Frontier
11. **Bridge Segment Localization** (Sonnet Goal) — surgical mashups
12. **Causal Skip Attribution** (Sonnet Goal) — per-dimension learning
13. **Koopman Operator** (Sonnet Goal) — temporal taste dynamics
14. **Persistent Homology** (Sonnet Goal) — topology of taste space
15. **Temporal Community Detection** (Sonnet Goal) — genre emergence in real time

---

## Meta-Observation

Opus 4.6 is the better product strategist. Sonnet 4.5 is the better research scientist. The ideal synthesis: follow Opus's prioritization and product framing, raid Sonnet's novel ideas and architectural detail for the builds. Opus tells you WHAT to build and WHY in terms of user experience. Sonnet tells you HOW to build it with full architecture specs.

The exploratory prompts produced more B2B/tool/research-catalog ideas. The goal-directed prompts produced more product-connected builds. For future consultations: bias toward goal-directed framing with product constraints.

**The single most important insight across all 4 responses:** Your linearity finding means you can update, compose, and interpolate preference vectors with linear algebra. This makes the feedback loop (anchor + mashup + EMA) CHEAP TO ITERATE ON. Build the loop first, improve components independently. The loop is the product. Everything else is enrichment.

---

## Chat URLs
- Opus Exploratory: https://claude.ai/chat/1d412276-3236-4521-a48c-fbadd2dea4c9
- Sonnet Exploratory: https://claude.ai/chat/044a082d-b57d-4d4c-b4a3-cc88a8ae7485
- Opus Goal-Directed: https://claude.ai/chat/12bb6beb-08e0-4922-ad4e-6f00aaa70cee
- Sonnet Goal-Directed: https://claude.ai/chat/60c55c41-8428-4d88-a340-e9fdb649655c
