# Consultation Verdict: Kyma Creation Engine Pipeline Direction
# Synthesized: 2026-04-05
# Models consulted: Opus 4.6, Sonnet 4.5 (via Cognitive Amplifier project on claude.ai)
# Judge: Independent subagent (Model A/B blind, no identity revealed during synthesis)

## Consultation Setup

- **Opus 4.6 Extended**: https://claude.ai/chat/a67b3d8d-2fbd-4d46-bb01-72e592d82096
- **Sonnet 4.5 Extended**: https://claude.ai/chat/4f0c1a74-5f18-48ae-bc22-7253b4fc9bd2
- **Prompt**: Neutral, non-leading. Presented all data assets, current models, proposed 4-model pipeline, competitive landscape, constraints, and 6 open questions. No position stated.
- **Prompt file**: `00-consultation-prompt.md` in this directory

## Overall Verdict: REBUILD at 80% Confidence

Both models independently recommended against the proposed 4-model pipeline and converged on a simpler 2-system architecture. The convergence on fatal flaws is high-confidence signal.

## Where Both Agree (Accept — independent convergence)

1. **Model 2's training signal is a category error** — DJ transitions are track-level temporal sequences, NOT stem-level vertical layering events. Training stem compatibility from transition data will fail. [95% confidence from both]

2. **Model 1 is unnecessary** — FAISS/ANN search directly in MERT 2048d space replaces the learned 2048d->13d projection. The dimensionality reduction throws away exactly the information needed for compatibility.

3. **ACE-Step obsoletes Models 3 and 4** — The generation model handles arrangement as prompting decisions. No training data needed for an arrangement model.

4. **Wizard of Oz MVP first** — Validate the product thesis with real users before building ANY models. Manual mashup creation + polished UI.

5. **Kills are correct** — V8 retraining (at ceiling), stigmergic experiments (pre-product), Phase 0 Upwork audit (evaluates killed model). All dead investment.

6. **Keeps are correct** — Ingestors (compounding data asset), 27.2M transitions (training data for future work), Bridge API (structural holes = discovery value), MERT pipeline (shifted to on-demand).

7. **Competitive timing is exceptional** — Spotify and Suno validating taste-as-product = free market education. YC W26 vacuum = first credible entrant gets disproportionate attention.

8. **Local-first positioning is strategically correct** — Spotify can't go local (label DRM), Suno can't do taste (no listening history), Bandcamp won't do AI (ideological). ACE-Step + MERT + Mel-Band-Roformer all run locally.

## Where They Disagree (The Gold)

### 1. Protocol Timing
- **Opus**: Single-player magic first, network effects second. Don't try to solve both simultaneously.
- **Sonnet**: Design the Taste Graph Protocol NOW — it's the actual moat. Specifies event types, relay model, monetization.
- **Judge**: Sonnet's instinct is right (the protocol IS the moat long-term), but Opus's sequencing is right (building protocol infrastructure before validating product thesis is premature optimization). **Resolution**: Design the protocol schema now (cheap, informative), build the infrastructure after MVP validation.

### 2. Mashup Framing
- **Opus**: Mashups are the product experience. Users want novel sonic combinations.
- **Sonnet**: Mashups are the DISCOVERY MECHANISM, not the end product. Users want taste insights. The mashup is a probe that reveals connections. "Like how A/B tests aren't the product; learning is."
- **Judge**: Sonnet's reframe is more defensible. It avoids the quality uncanny valley problem (if mashups are probes, 70% quality is fine; if they're the product, 70% quality kills retention). It also opens more product surface area (taste maps, listening journeys, compatibility scores with friends — not just mashups). **Both models should be heard**: the UX should deliver the EXPERIENCE of a mashup (Opus) while framing the VALUE as discovery (Sonnet).

### 3. Synthetic Training Data
- **Sonnet**: Generate 10K mashups with known stem combinations, label them (human or model), train classifier.
- **Opus**: Let ACE-Step handle compatibility implicitly — if it can generate a coherent blend, compatibility is solved.
- **Judge**: Both are valid paths. ACE-Step implicit is faster and requires no labeling infrastructure. Synthetic is more controllable and produces an evaluable model. **Recommendation**: Start with ACE-Step implicit (faster to validate), build synthetic dataset in parallel for future Model 2 if needed.

## Unique to Opus (Not Raised by Sonnet)

1. **ACE-Step LoRA as taste primitive** — User taste distilled into a portable, shareable LoRA adapter for ACE-Step. Taste becomes a 10MB digital artifact. "Share your taste LoRA from 2026" = cultural object. This is potentially the most novel idea in the entire consultation. Nobody is building this.

2. **"Strava for taste" positioning** — Alternative to "Cursor for music." Core loop isn't "make a mashup" but "discover and share your sonic identity," with mashups as one expression.

3. **Kelly Criterion for compute budget** — Information value of 20 user reactions exceeds information value of 0.02 NDCG improvement.

4. **CLAP as MERT alternative** — Joint text-audio embedding space would let users describe taste in natural language.

5. **Spotify acquired WhoSampled (Nov 2025)** — Timeline pressure for competitive distance.

## Unique to Sonnet (Not Raised by Opus)

1. **Taste Graph Protocol (TGP)** — Full protocol design: event types (taste.input, mashup.created, mashup.feedback, transition.observed, bridge.discovered), Nostr-style relays, monetization via premium relays. "Building the SMTP for taste discovery."

2. **Uncanny valley for mashup quality** — 0-40% quality = tolerable (clearly AI). 40-80% = danger zone (almost real, flaws MORE jarring). 80-100% = magic. Must target either <40% or >80%, never the middle.

3. **Wundt curve optimization** — 3-5 seed songs + AI mashup = novelty bounded by familiarity. Not too random, not too safe.

4. **Multi-dimensional feedback design** — Binary (save/skip) + Explicit ("rhythmically tight / emotionally resonant / surprising") + Contextual (time of day, skip point, session depth). Each dimension trains different system components.

5. **Cold-start confidence-aware output** — "I don't know you well yet — here's an exploratory mix. Tell me what works." Frame as collaborative exploration when taste signal is weak.

6. **Discovery vs engagement fitness functions** — Spotify optimizes for engagement (maximize listening time). We optimize for discovery (maximize aha moments). These are DIFFERENT fitness functions. Spotify can't pivot to discovery without cannibalizing engagement.

## What Neither Addressed (Judge Addition)

1. **Latency budget**: User gives 3-5 songs. How long before they hear output? MERT encoding (5s/track) + FAISS search (<100ms) + ACE-Step generation (??? on M3 Max) + quality validation. If total is >30 seconds, the magic dies. Need to benchmark end-to-end latency.

2. **Preview URL deprecation strategy**: Both mention the risk but neither proposes a systematic cache-ahead strategy. Should proactively cache MERT embeddings for the top 10M tracks by popularity, reducing dependency on CDN availability.

3. **Apolline's role in the new architecture**: CEO's perspective on the pivot — product positioning, fundraise narrative impact, investor framing. The consultation is purely technical/strategic; the co-founder alignment step is missing.

## Confidence Intervals (Synthesized)

- [90%] The 4-model pipeline as proposed has fatal flaws
- [85%] FAISS + ACE-Step 2-system architecture is the right simplification
- [80%] MVP validates that SOME users find value in taste-guided sonic discovery
- [65%] ACE-Step quality crosses the uncanny valley on M3 Max
- [60%] Mashup quality is sufficient for user retention (not just demo wow)
- [50%] This becomes a venture-scale business (vs tool for power users)
