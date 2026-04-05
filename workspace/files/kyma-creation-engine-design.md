# KYMA CREATION ENGINE — Architecture Design & Vision Document
# Version 1.0 | April 5, 2026
# Authors: Idam Obiahu (CTO), Kai (AI Engineering Partner)
# Status: APPROVED — consultation-validated, ready for implementation

---

## PURPOSE OF THIS DOCUMENT

This is the canonical reference for the Kyma Creation Engine — the strategic pivot from curation analysis to curation x creation. Every LLM instance, every agent, every future engineer should read this before touching the pipeline. It captures:

1. **WHY** we pivoted (the ceiling, the thesis, the evidence)
2. **WHAT** we're building (2-system architecture, not 4-model pipeline)
3. **HOW** we validated the direction (dual-model consultation with synthesis)
4. **WHEN** to build each piece (sequenced build plan)
5. **WHAT WE KILLED** and why (with reasoning, not just a list)

If you're reading this 8 months from now with zero context, this document plus the consultation archives in `files/consultations/2026-04-05-creation-engine-pivot/` should give you complete traceability.

---

## PART 1: THE PIVOT — WHY WE CHANGED DIRECTION

### The Ceiling

After C-16 Phase 2 (7 model variants tested), the V8 Transition Scorer hit an architecture ceiling at NDCG@20 = 0.7318. No combination of features, architectures, or training data broke 0.73. The signal from co-occurrence + audio features for DJ transition prediction is maxed out.

More specifically:
- BPR (Bayesian Personalized Ranking) optimizes for "A > B in user's preference ranking" — correct for recommendation, wrong for creation
- The V8 scorer is playlist-driven. DJ transitions were proven to REGRESS BPR training (-0.0121 F1 in V4) because they encode sequencing/flow, not similarity
- The 0.73 ceiling is a fitness landscape problem, not a data problem. We climbed to the local maximum of "predict DJ track sequences from co-occurrence + audio features." More data = hill-climbing on the same hill

### The Gap

The current pipeline solves **sequencing** — predicting what track follows what. The product goal is **curation x creation** — AI that creates novel sonic combinations from taste signal. Nothing in the pipeline generates audio, creates mashups, or bridges the gap between understanding what sounds good together and producing new listening experiences.

### The Thesis

Merge curation with creation. Users should feel like magicians, not passive recommendation consumers. Give 3-5 songs, get back cross-genre sonic combinations you never would have found. Every skip/save/replay trains the taste fingerprint.

### What Made This the Right Time

1. **ACE-Step 1.5 XL** dropped — open-source 4B-param music generator, Apache licensed, runs on Mac locally. Eliminates the need to build generation models from scratch.
2. **Mel-Band-Roformer** outperforming Demucs on vocal separation. Demucs no longer actively maintained at Meta.
3. **Spotify Taste Profile Editor** (SXSW Mar 14) + **Suno v5.5 "My Taste"** = market validation that taste is a first-class product primitive. Free market education.
4. **YC W26**: 196 companies, ZERO in music/audio/taste. Competitive vacuum.
5. **0.73 ceiling** confirmed — no path forward on the current architecture.

---

## PART 2: WHAT WE PROPOSED (AND WHY IT WAS WRONG)

### Original 4-Model Pipeline (Proposed April 5, 2026)

**Model 1: Audio Feature Predictor**
- MERT 2048d -> Spotify 13d audio features + 32d MERT-derived taste features
- Purpose: coarse retrieval (256M -> 5,000 candidates)

**Model 2: Stem Compatibility Predictor**
- Two MERT embeddings (4096d) -> compatibility score + TYPE
- Training data: 27.2M curated transitions

**Model 3: Mashup Arrangement Model**
- Compatible tracks + type -> arrangement plan
- Training data: WhoSampled + experiments

**Model 4: Taste Agent**
- Chains all models: taste input -> retrieval -> compatibility -> arrangement -> generation

### Why This Was Wrong (Consultation Findings)

The consultation (Opus 4.6 + Sonnet 4.5 via Cognitive Amplifier, April 5 2026) identified THREE fatal flaws:

**Fatal Flaw 1: Model 2's Training Signal is a Category Error** [Both models agreed, 95% confidence]

DJ transition data tells you "track A was played before track B." It does NOT tell you "the vocals of A work over the beat of B." These are fundamentally different claims at different levels of musical abstraction.

- Transitions = temporal sequencing events (fade out A, fade in B, BPM matching at transition point)
- Stem mashups = vertical layering events (vocal melody of A plays simultaneously over harmonic substrate of B)
- The compatibility constraints are entirely different
- You cannot learn stem-level compatibility from track-level sequence data
- Concrete failure case: high-energy techno + ambient track appear in transitions (DJs use ambient to cool down), but techno drums + ambient vocals = trainwreck

**Fatal Flaw 2: Model 1 Solves the Wrong Problem** [Both models agreed]

MERT 2048d -> Spotify 13d is a catastrophic information loss (77:1 ratio). The Spotify features are human-interpretable summaries that lose exactly the information needed for stem compatibility: timbral texture, harmonic specificity, rhythmic microstructure.

Solution: FAISS IVF-PQ approximate nearest neighbor search directly in MERT 2048d space. Can search 256M vectors on M3 Max with sub-100ms latency. The entire field of billion-scale vector search is solved — no dimensionality reduction model needed.

**Fatal Flaw 3: Model 3 Has No Training Data** [Opus identified]

WhoSampled tells you THAT a sample was used, not HOW it was arranged. Our own mashup experiments number in dozens, not thousands. ACE-Step's repainting capability replaces this entire model with an off-the-shelf open-source solution.

---

## PART 3: WHAT WE'RE ACTUALLY BUILDING

### The 2-System Architecture

The consultation produced independent convergence on a radically simpler architecture:

```
SYSTEM 1: RETRIEVAL (existing assets, minimal new work)
  User taste input (3-5 songs)
  -> MERT embedding (on-demand from preview URLs, 5s/track)
  -> FAISS IVF-PQ index (800K embeddings, expanding incrementally)
  -> Bridge API chemistry scoring (7-dim, already in production)
  -> Top candidates ranked by taste + bridge novelty

SYSTEM 2: GENERATION (ACE-Step integration)
  Top candidate pairs from System 1
  -> ACE-Step 1.5 audio2audio/repainting (blend two tracks)
  -> Quality validation (spectral analysis, beat alignment check)
  -> User feedback (skip/save/replay)
  -> Taste vector update (Rocchio-style relevance feedback)
```

Two systems. Not four models. Simpler, faster, more defensible.

### Why 2 Systems Instead of 4 Models

1. **FAISS replaces Model 1** — no learned projection needed, search directly in embedding space
2. **ACE-Step replaces Models 3 and 4** — generation model handles arrangement decisions as prompting decisions, not a separate trained model
3. **Model 2 is deferred** — the training signal problem is real. Either solve it with synthetic data (render mashups, label them) or let ACE-Step handle compatibility implicitly (if it can generate a coherent blend, compatibility is solved by the generation model itself)

### Data Assets (What We Keep)

| Asset | Size | Role in New Architecture |
|-------|------|--------------------------|
| 256M Spotify metadata | 33GB SQLite | Track lookup, popularity ranking for FAISS index prioritization |
| 256M audio features | 39GB SQLite | Coarse pre-filtering (BPM range, key compatibility), NOT primary retrieval |
| 800K MERT embeddings | 6.1GB | FAISS index seed. Primary retrieval space |
| 27.2M curated transitions | 3.15GB | Bridge API scoring, candidate pair generation, future synthetic training data |
| 79M-key name index | 10.57GB SQLite | Track resolution |
| ~250M preview URLs | CDN | On-demand MERT computation for any track |
| ALS taste vectors | 12.7M x 128d | Supplementary taste signal (96.3% sparse — use for popular tracks only) |

### Models (What We Keep vs Kill)

| Model | Status | Reasoning |
|-------|--------|-----------|
| V8 Transition Scorer | **KILLED** | At ceiling (0.73), playlist-driven BPR doesn't serve mashup goal |
| V3 Similarity Model | **KEPT** | F1=0.9415, useful for candidate pre-filtering |
| Bridge API | **KEPT** | 7-dim chemistry scoring identifies cross-community connections. Structural holes (Burt) = where discovery value lives |
| MERT pipeline | **KEPT, shifted** | From bulk embedding to on-demand computation |

### Services (What We Keep vs Kill)

| Service | Status | Reasoning |
|---------|--------|-----------|
| Bridge API (:8877) | **KEPT** | Core infrastructure for cross-cluster discovery |
| 4 data ingestors | **KEPT** | More transition data feeds Bridge API scoring and future synthetic training |
| Stigmergic experiments (EXP-016/017/019) | **KILLED** | Network science without product signal. Interesting but pre-product |
| Phase 0 Upwork audit | **KILLED** | Evaluates V8 which is at ceiling |
| V8 retraining pipeline | **KILLED** | See above |

---

## PART 4: BUILD SEQUENCE

### Week 0: ACE-Step Quality Gate (BLOCKING — do this first)

Before committing to the architecture, validate the generation primitive:

1. Install ACE-Step 1.5 XL on M3 Max
2. Test audio2audio/repainting mode with 10 high-chemistry Bridge API track pairs
3. Evaluate output quality: does it cross the uncanny valley?
4. If quality is sufficient -> proceed with build sequence
5. If quality is insufficient -> fallback to Demucs/Mel-Band-Roformer stem separation + mashup renderer v3

**Success metric**: >=6/10 generated blends sound "interesting or better" to Idam and Apolline

**Risk being tested**: The uncanny valley (Sonnet's insight). 40-80% quality is the DANGER ZONE — almost good enough to be real, which makes flaws MORE jarring. We need to be clearly in the 80%+ zone or clearly frame outputs as "discovery probes, not finished music."

### Week 1: Wizard of Oz MVP

Don't build models. Build a demo that proves the product thesis.

1. Pick 5 compelling cross-genre track pairs from Bridge API (high multi-dimensional chemistry)
2. Run Mel-Band-Roformer stem separation on 30s previews
3. Use mashup renderer v3 to create 5 mashups (swap pairs until 5 sound magical)
4. Build dead-simple UI: user enters 3 Spotify tracks -> present closest pre-computed mashup
5. Show to 20 people. Measure:
   - Emotional reaction (film faces if possible)
   - "Very disappointed" if this disappeared (Sean Ellis test)
   - What they try to do next

**Success metric**: >=8/20 people spontaneously share output or ask to try more tracks
**Kill criterion**: <40% "very disappointed" -> iterate on experience before building any models

### Weeks 2-3: ACE-Step Integration

Replace mashup renderer with ACE-Step 1.5 audio2audio/repainting pipeline:
- Feed two source tracks, prompt for coherent blend
- Test on 100 track pairs from high-chemistry Bridge API results
- Evaluate with 10 listener judges
- Compare quality against renderer v3 output

### Weeks 4-5: FAISS Indexing

Build the taste-to-retrieval pipeline:
- FAISS IVF-PQ index on 800K MERT embeddings
- User gives 3-5 seed tracks -> compute MERT on-demand from preview URLs
- ANN search -> Bridge API chemistry scoring on top candidates
- ACE-Step generation on top pair
- This is a 2-system pipeline (retrieval + generation), not 4 models

### Weeks 6-8: Taste Feedback Loop

- Every skip/save/replay updates user-local taste vector
- Start with weighted average of MERT embeddings for liked outputs (Rocchio-style relevance feedback)
- Use taste vector to re-rank retrieval results
- Ship to 50 beta users

**Key decision point at week 5**: Is ACE-Step output quality sufficient for the "magician" feeling? If yes, continue. If no, pivot to curated DJ transitions (which V8 already supports at 0.73) as initial product, with mashup as a future feature.

### Post-Seed (6-12 months)

1. **Custom ACE-Step LoRA** conditioned on transition data — specifically for bridge/blend audio between two input tracks. Focused fine-tuning with clear training data (27.2M transitions provide pairs, quality scores provide reward signal).

2. **Taste LoRA primitive** (Opus's unique insight, potentially the most powerful idea): Each user's interaction history distills into a LoRA adapter that conditions ACE-Step generation. Taste becomes a portable, shareable, composable artifact. "Share your taste LoRA" = social primitive. The taste graph IS the LoRA collection.

3. **Taste Graph Protocol** (Sonnet's unique insight): Nostr-style decentralized protocol for taste discovery. Events: taste.input, mashup.created, mashup.feedback, transition.observed, bridge.discovered. Users publish to relays. Kyma = best client (like Gmail for email). Revenue from premium relays + advanced Bridge API queries.

---

## PART 5: CONSULTATION EVIDENCE

### Process

Consultation conducted April 5, 2026 via LLM Judge skill on claude.ai Cognitive Amplifier project.

- **Opus 4.6 Extended**: Chat URL https://claude.ai/chat/a67b3d8d-2fbd-4d46-bb01-72e592d82096
- **Sonnet 4.5 Extended**: Chat URL https://claude.ai/chat/4f0c1a74-5f18-48ae-bc22-7253b4fc9bd2
- **Judge synthesis**: Independent subagent with Model A/B labeling (no model identity revealed)

Full responses archived at `files/consultations/2026-04-05-creation-engine-pivot/`

### Verdict

**REBUILD** at 80% confidence (judge synthesis).

Both models independently converged on:
- The 4-model pipeline has fatal flaws (category error in training signal, unnecessary dimensionality reduction, no training data for arrangement)
- FAISS replaces Model 1
- ACE-Step replaces Models 3-4
- Model 2 needs fundamentally different training data (synthetic, not transition-based)
- Wizard of Oz MVP before ANY model building
- 2-system architecture (retrieval + generation) instead of 4-model pipeline

### Where They Agreed (High Confidence)

1. Model 2's training signal is a category error (track-level transitions != stem-level compatibility)
2. FAISS/ANN search directly in MERT space, skip dimensionality reduction
3. ACE-Step obsoletes Models 3-4
4. Wizard of Oz demo first, models second
5. Kills are correct (V8 retraining, stigmergic experiments, Upwork audit)
6. Keeps are correct (ingestors, transitions, Bridge API, MERT pipeline)
7. Bridge API is high-value (structural holes theory)
8. Local-first positioning is strategically correct
9. Competitive timing is excellent

### Where They Disagreed (The Gold)

1. **Protocol timing**: Opus says protocol is post-product (single-player magic first). Sonnet says design the Taste Graph Protocol NOW (it's the actual moat). Judge assessment: Sonnet's instinct is right (design now) but Opus's sequencing is right (build later).

2. **Mashup framing**: Opus frames mashups as the product experience. Sonnet frames mashups as DISCOVERY MECHANISM, not end product ("users don't want mashups — they want taste insights"). Judge: Sonnet's reframe is more defensible and avoids the quality uncanny valley.

3. **Synthetic training data**: Sonnet proposes rendering 10K mashups with known stem combinations as Model 2 training data. Opus proposes letting ACE-Step handle compatibility implicitly. Both are valid — ACE-Step implicit is faster, synthetic is more controllable.

### Unique Insights

**From Opus (not raised by Sonnet)**:
- ACE-Step LoRA as taste primitive — user taste distilled into portable, shareable LoRA adapter. Potentially the most novel idea in the entire consultation. Nobody is building this.
- "Strava for taste" positioning alternative (social identity, not tool metaphor)
- Kelly Criterion for compute budget allocation

**From Sonnet (not raised by Opus)**:
- Taste Graph Protocol (Nostr-style decentralized protocol for taste). The protocol IS the moat, not the software.
- Wundt curve optimization (novelty bounded by familiarity)
- Uncanny valley for mashup quality (40-80% quality zone is danger zone)
- Feedback loop design with multi-dimensional signals (rhythmic, emotional, technical)
- Cold-start confidence-aware output ("I don't know you well yet")
- Mashups as discovery probes, not finished products

---

## PART 6: RISK REGISTRY

### CRITICAL

| Risk | Mechanism | Mitigation | Owner |
|------|-----------|------------|-------|
| ACE-Step quality ceiling | Unnatural transitions in repainting, coarse vocal synthesis | Week 0 quality gate. 10 pairs, pass/fail before committing. Fallback: Demucs + renderer v3 | Idam |
| Users don't want mashups | Mashup as art form has existed since Grey Album (2004) and never achieved mass appeal | Wizard of Oz test catches this in week 1 before building models. Frame as discovery, not product | Idam |
| Preview URL instability | Spotify can revoke 250M unauthenticated CDN links at any time | Cache MERT embeddings for every processed track. System degrades gracefully (retrieval works, generation needs re-sourcing) | Kai |

### HIGH

| Risk | Mechanism | Mitigation |
|------|-----------|------------|
| Legal cease-and-desist | Processing copyrighted audio for derivative works | ACE-Step generation path (novel audio, not direct stems) more defensible. Consult music IP attorney before public shipping |
| Local-first kills network effects | Isolated taste graphs, no Metcalfe's law | Design Taste Graph Protocol schema NOW, build later. Single-player magic first, multiplayer second |
| Model 2 training signal insufficient | Even with synthetic data, stem compatibility may be too high-dimensional | Let ACE-Step handle compatibility implicitly as fallback. If generation works, compatibility is solved |

### MEDIUM

| Risk | Mechanism | Mitigation |
|------|-----------|------------|
| Spotify ships taste-guided mashups | 500M users, full catalog, billions in funding | Protocol > Platform. Local-first (they can't do this). 6-12 month head start. Vertical niches they ignore |
| Mashup quality uncanny valley | 40-80% zone more jarring than clearly-AI output | Frame as discovery probes. "This reveals rhythmic compatibility" not "listen to this perfect mix" |

---

## PART 7: EVALUATION METRICS

### System 1 (Retrieval)
- **Recall@K**: Of ground-truth similar tracks (MERT nearest neighbors), what % in top-K?
- **Diversity**: How many unique artist/genre clusters in top-K?
- **Bridge novelty**: % of candidates from different taste communities than seed tracks

### System 2 (Generation)
- **Pass rate**: % of generated blends rated "interesting or better" by listeners
- **Beat alignment accuracy**: % of bars on-beat
- **Spectral balance**: RMS levels of each component in final output

### Product (The One That Matters)
- **Session depth**: How many mashups per session?
- **Retention**: % users returning next day/week
- **Discovery rate**: % of surfaced tracks outside user's historical genres
- **Aha moments per session**: qualitative, but crucial
- **Sean Ellis score**: % "very disappointed" if product disappeared (target: >=40%)

---

## PART 8: COMPETITIVE POSITIONING

### The Map (April 2026)

| Player | What They Do | Why They Can't Do What We Do |
|--------|-------------|------|
| Spotify | Taste Profile Editor (manual taste editing via SongDNA) | Label contracts require centralized DRM. Won't generate/recombine audio. Defensive lock-in play |
| Suno v5.5 | "My Taste" (taste profiling in AI generation) | Generated slop, not real music discovery. Single-player, no network effects |
| Coda Music | Anti-algorithm streaming, all 3 major labels | Human only, won't scale. $10.99/mo |
| Hangout | Turntable revival ($8.2M Founders Fund) | Synchronous + ephemeral = no compounding |
| Bandcamp | Banned AI entirely (Jan 2026) | Market bifurcation |
| Apple Music | Playlist Playground (NLP playlists) | Table stakes feature, not product thesis |

### Our Positioning

**Cursor for music** — AI that amplifies human taste into creative output. Local-first. Open-source models. Taste graph as community commons.

What makes us structurally different:
1. We optimize for **discovery** (maximize aha moments), not **engagement** (maximize listening time). Spotify can't pivot to discovery without cannibalizing engagement.
2. We use **real music DNA** (MERT embeddings of actual recordings), not generated audio (Suno) or manual metadata (Spotify SongDNA).
3. We run **locally** with open-source models. No label relationships to protect, no centralized DRM to enforce.
4. Our **27.2M curated transitions** from 7 sources are a cornered resource nobody else has.

---

## PART 9: OPEN QUESTIONS

These are decisions that were explicitly deferred, not forgotten:

1. **ACE-Step vs Demucs+renderer**: Depends on Week 0 quality gate results
2. **Taste Graph Protocol timing**: Design schema now, build infrastructure post-MVP
3. **Taste LoRA vs taste vector**: LoRA is more powerful but requires ACE-Step fine-tuning infrastructure. Start with Rocchio-style vectors, evolve to LoRA post-seed
4. **Monetization model**: Freemium SaaS ($9.99/mo pro) vs protocol-based (premium relays). Not urgent pre-seed — validate product first
5. **UX paradigm**: "Give 3-5 songs, get mashups" is validated by consultation. But what's the 30-second first-use experience? What does output feel like — continuous mix? Individual mashups? Taste radio station? Needs user research
6. **CLAP as alternative to MERT for retrieval**: CLAP operates in joint text-audio embedding space — users could describe taste in natural language ("heavy bass, dreamy synths, unexpected key changes") instead of seed tracks. Worth exploring after FAISS is working

---

## PART 10: GLOSSARY

| Term | Definition |
|------|-----------|
| MERT | Music Encoder from Representations and Transformers. Apache 2.0 licensed. Produces 2048d audio embeddings. Production encoder |
| ACE-Step | Open-source 4B-param music generation model. Apache licensed. Supports audio2audio repainting |
| FAISS IVF-PQ | Facebook AI Similarity Search with Inverted File + Product Quantization. Approximate nearest neighbor search at billion scale |
| Bridge API | Our 7-dimension chemistry scoring service on :8877. Identifies cross-community connections |
| Mel-Band-Roformer | Stem separation model outperforming Demucs. For vocal/drum/bass/other isolation |
| Taste LoRA | Low-Rank Adaptation fine-tuning of ACE-Step conditioned on user taste. Makes taste a portable artifact |
| Taste Graph Protocol (TGP) | Proposed Nostr-style decentralized protocol for taste discovery events |
| Rocchio feedback | Classical relevance feedback: query vector = alpha * original + beta * relevant - gamma * irrelevant |
| Sean Ellis test | "How would you feel if you could no longer use this product?" >=40% "very disappointed" = product-market fit |
| Structural holes (Burt) | Theory that bridges between network clusters concentrate information advantage and discovery value |
| Wundt curve | Inverted-U relationship between novelty and preference. Too familiar = boring, too novel = alien |

---

## CHANGELOG

| Date | Change | Author |
|------|--------|--------|
| 2026-04-05 | v1.0 — Initial design doc. Consultation-validated 2-system architecture | Kai |

---

_This document is the single source of truth for the Creation Engine architecture. Update it when decisions change. Don't let it go stale._
