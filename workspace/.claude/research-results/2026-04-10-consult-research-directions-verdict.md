# Research Direction Consultation — Verdict v2
## Opus 4.6 + Sonnet 4.5 Extended | 2026-04-10
## Tiebreak Judge: Kai (Claude Code)

### Models
- **Opus 4.6**: 20,646 chars. Chat: https://claude.ai/chat/c5dc8bf4-968b-49eb-a342-8d912884938d
- **Sonnet 4.5 Extended**: 25,776 chars. Chat: https://claude.ai/chat/9e81cefa-b04e-40ee-ae88-006453bc754c
- **Replaced**: Sonnet 4.6 (used in error, file renamed to -INVALID)

---

## CONVERGENCE (both agree)

1. **Layer-wise decomposition is the highest-yield experiment.** Both rank Direction 1 (layer-wise taste decomposition) as the primary recommendation, though each proposes critical modifications.

2. **Bridge model r=0.969 needs diagnostic FIRST.** Opus: 85% confidence it has label leakage. Sonnet: 75% confidence it overfits DJ-specific behavior. CONFIRMED from code analysis (DIAG-01): taste_vector_128d input and participation coefficient P labels both derive from the same playlist co-occurrence matrix. Actual val r=0.958, not 0.969.

3. **90/10 composite = redundancy, not weakness.** Taste and transition models measure overlapping latent structure. Opus: train on residual. Sonnet: transition adds value only where taste communities are disconnected.

4. **Taste may be compositional (not single-vector).** Both predict multiple orthogonal taste dimensions. Opus: at least two peaks (rhythmic + affective). Sonnet: hierarchical (acoustic → pattern → semantic). Both say current single-vector recommenders are fundamentally wrong.

5. **Ultra-small-world topology might be partially artifactual.** Opus: algorithmic playlists inflate gamma, organic probably 1.4-1.8. Sonnet: need time-stratified + degree-cutoff sensitivity analysis.

6. **Research lab mode is correct.** Both frame this as instrument-building, not pipeline optimization. Opus: "microscope, not product." Sonnet: "first-mover advantage on compositional taste structure."

7. **Negative sampling is critical.** Both recommend generating hard negatives (not random) to test genuine compatibility vs co-occurrence.

## DIVERGENCE

| Issue | Opus 4.6 | Sonnet 4.5 | Verdict |
|-------|----------|------------|---------|
| **Method for layer-wise** | Bradley-Terry preference model (counterfactual choices, 15B triples) | Contrastive projectors with feature-delta correlation | **Opus wins.** Bradley-Terry is strictly superior — treats transitions as preference data not association. Same shift that made RLHF > SFT. |
| **Training data** | DJ transitions (15M) | Playlist transitions (9.9M) — DJ transitions have selection bias (beatmatching, crowd, energy curves) | **Sonnet wins.** DJ selection bias is a real concern. Use BOTH: train on playlists as ground truth, validate on DJ transitions to test if DJ-specific patterns are a subset. |
| **Bridge concern framing** | "Leakage" — co-occurrence inputs predicting co-occurrence labels | "DJ-specific overfitting" — learned club constraints, not universal compatibility | **Both correct, different levels.** Leakage is the structural issue (confirmed from code). DJ overfitting is the behavioral issue. Fix leakage first (MERT-only retrain), then test DJ vs playlist generalization. |
| **Wormhole approach** | Friendship Paradox inversion — wormholes are everywhere, ANTI-wormhole paths are scarce | Betweenness centrality + bridging coefficient (Hwang 2008) — identify structural bridges | **Opus has deeper insight.** The inversion is non-obvious: niche-to-niche routing is the real unsolved problem, not wormhole discovery. But Sonnet's betweenness method is the right tool. |
| **Preview asymmetry** | Michaelis-Menten kinetics — uncertainty is the substrate, model is the enzyme | Ensemble confidence thresholding — >95% confidence → trust eliminates evaluation cost | **Complementary.** Opus provides the theoretical framework (kinetics), Sonnet provides the implementation (ensemble confidence). Build the ensemble, evaluate via the kinetics frame. |
| **Strategic reframe** | "Instrument vs data pile" — produces generalizable findings | "Taste is about transitions not tracks" — sequence generator, not recommendation system | **Sonnet's reframe is more actionable for product.** But Opus's instrument framing correctly sets the research posture. Both are true at different levels. |

## UNIQUE INSIGHTS (only one model surfaced)

### Opus-only:
- **Two-peak hypothesis**: layers 6-10 (rhythmic/timbral) + 18-21 (semantic/affective), with BERTology U-curve degradation at 22-25
- **Friendship Paradox inversion**: naively traversing the graph collapses into hub-space within ~2 hops — niche-to-niche routing is the scarce resource
- **Asymmetric transition directionality**: P(B|A)/P(A|B) ratio as taste fingerprint — high-directionality DJs (strict arc) vs low (free association)
- **Residual training**: MODEL-002 v9 on the variance transitions explain that taste doesn't
- **Discovery reversibility**: measurement-alters-system problem — every prediction leaks information into the system being predicted
- **Michaelis-Menten framing**: preview cost = f(unresolved uncertainty), not f(clip length)
- **Plackett-Luce extension**: curators make set choices, not pairwise

### Sonnet-only:
- **Playlist transitions as ground truth**: 9.9M playlists represent unfiltered human taste, not DJ-filtered
- **Layer-weight vectors for cold start**: 5 transitions → 25D layer weights → full taste characterization
- **Context-specific models**: workout = high weight on early layers, study = high weight on late layers
- **Temporal taste dynamics**: circadian patterns from timestamps — predict optimal recommendation time from audio + chronotype
- **Sequence evaluation**: humans evaluate sequences faster than individuals (story arc > isolated scene) — 5-track sequences compress evaluation cost
- **Curator-amplification paradigm**: instead of replacing curators, amplify them — match users to curators, not tracks
- **Evaluation collapse**: ensemble confidence can substitute for listening — "zero-cost recommendation" at high enough threshold

## TIEBREAK VERDICT

### Execution Order (revised from v1):

**TIER 0: Diagnostics (Week 1)** — DIAG-01 ALREADY RESOLVED from code analysis
- [x] DIAG-01: Bridge leakage test → CONFIRMED. ALS taste vectors + participation coefficient P both from same co-occurrence matrix.
- [ ] DIAG-02: 7D chemistry decomposition → retrain MODEL-004 with MERT-only inputs (zero graph features). Expected: r drops to 0.5-0.7 for clean audio signal.
- [ ] DIAG-03: Transition asymmetry test → compute P(B|A)/P(A|B) for all pairs, measure entropy distribution
- [ ] DIAG-04: Organic vs algorithmic gamma split → fit gamma separately on user-curated vs editorial/algorithmic playlists
- [ ] DIAG-05: Redundancy test → correlation between taste projector scores and transition model scores

**TIER 1: Layer-wise Bradley-Terry on Playlist + DJ Transitions (Weeks 2-4)**
Combined best of both models:
- Use Bradley-Terry (Opus's superior statistical framework)
- Train on BOTH playlist transitions (Sonnet's ground truth argument) AND DJ transitions
- 5-layer MVP first (layers 1, 6, 12, 18, 24) then full 25
- Measure: which layers predict which transition feature-deltas
- Compare DJ vs playlist layer profiles to test DJ overfitting hypothesis
- Falsification: if all layers have similar predictive power → H3 (taste is monolithic)
- Success: if different layers predict different delta-features → H1 (compositional taste)

**TIER 2: Wormhole Characterization + Niche Routing (Weeks 4-6)**
- Betweenness centrality (Sonnet's method) + Friendship Paradox analysis (Opus's insight)
- Key question from Opus: how to stay in low-degree territory — anti-wormhole routing
- Bridging coefficient (Hwang 2008) to identify structural bridges
- Train wormhole predictor from MERT embeddings

**TIER 3: Transition Grammar + Temporal Dynamics (Weeks 6-10)**
- Extract per-transition 9D feature-delta vectors from 15M transitions
- Cluster into K prototypes (start K=50)
- Represent playlists/sets as prototype sequences
- Set-arc grammar extraction (Opus's 5-15 canonical arcs prediction)
- Temporal taste dynamics from timestamps (Sonnet's circadian hypothesis)

**DEFERRED:**
- Evaluation collapse (needs confidence-calibrated models first — after Tier 1)
- Cascade prediction (interesting but lower information yield per both models)
- Curator-amplification paradigm (product-level, not research — revisit after Tier 1 findings)

### Key Decision: Playlist vs DJ Training Data
Sonnet's most actionable contribution. DJ transitions are biased toward performability (beatmatching, energy curves, crowd response). Playlists are unbiased personal taste. The research should train on playlists as primary, use DJ transitions as a specialized test set. If layer profiles differ between DJ and playlist, that's DIAG-02-level finding about what DJs vs listeners actually optimize for.

### Pre-Mortem
1. **Bradley-Terry counterfactual sampling creates trivial negatives** → Opus already warns: use hard negative mining via MERT nearest-neighbor, stratified by tempo/key/year
2. **Layer representations are highly correlated** → Opus suggests residual probing (Hewitt & Manning 2019). Important for clean separation.
3. **Playlist sequences may not be intentional** → tracks added in bulk or imported aren't transitions. Filter to playlists with sequential adds (timestamp deltas < 24h).
4. **MERT might not be the right encoder** → If layer-wise curves are flat, consider MusicFM or fine-tuned models (from Opus)
5. **Discovery reversibility** → Opus's unique concern: deploying discovery intelligence may destroy the topology being studied. Plan conservation policy.

### Pre-Celebration
1. **Compositional taste is real AND publishable** — first quantitative evidence that taste operates at multiple representational depths
2. **DJ vs playlist divergence reveals professional curation as a subset** — listeners want different things than club audiences
3. **Layer-weight vectors solve cold start in 5 transitions** — Sonnet's most product-relevant prediction
4. **Set-arc grammars are dramatically compact** — Opus predicts 5-15 arcs cover most variance. If true, Zipfian compression of all DJ knowledge.
5. **Temporal taste dynamics from timestamps** — chronotype-aware recommendations as unexpected capability
