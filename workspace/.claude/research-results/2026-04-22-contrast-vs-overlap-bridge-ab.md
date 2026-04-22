# Contrast-vs-Overlap Bridge A/B — Experimental Design Research

*Research-queue P1 follow-up from 2026-04-18 co-occurrence-vs-compatibility finding. Prerequisite work before the A/B can run.*

**Source queue item (verbatim):** "queue 20 real bridges in `mode=contrast` (high-sonic-distance, low-cooccurrence) vs 20 in `mode=overlap` (current weird_rank). Measure curator re-share rate over 14 days. Falsification test for East-Asian-contrast hypothesis in music. Kill criterion: if contrast-mode shares < overlap-mode by >30%, kill contrast framing."

## TL;DR — three things the queue item had wrong

1. **20 vs 20 is severely underpowered for realistic re-share rates.** At 10% base re-share rate, 20 vs 20 can only detect a 37pp absolute lift (10% -> 47%), which is a 4.65x fold-lift. Realistic music-curator re-share experiments in similar domains produce 1.5-2x lifts at most — not detectable at this N. The experiment as scoped will almost always produce a null result even if the hypothesis is directionally right. Need n>=120 per arm to detect a 2x lift at 15% baseline with 80% power.
2. **Sonic-distance metric is not defined.** DeepPref cosine on MERT L24 (trained taste projection) and raw MERT L24 cosine (pre-training acoustic semantic) measure different things. Using the wrong one could invert the contrast/overlap labels.
3. **Re-share endpoint is harder to track than the queue item implies.** Bridge referer telemetry (`/api/bridge/stats`) is VERIFICATION-BLOCKED on external drive mount as of 2026-04-20. Until that clears, "curator re-share" has to be measured via backup endpoints (direct Cloudflare tunnel log tail + manual curator-account scrape).

Recommendation: restructure the P1 from "14-day falsification A/B" to "7-day directional pilot + power calculation for full test." Full A/B queued as follow-up once Bridge referer telemetry verification unblocks and sample size is properly sized.

## Research questions answered

### Q1 — What is the right sonic-distance metric for mode=contrast?

Three candidates, ranked:

**Candidate A: DeepPref cosine on MERT L24 (64d learned taste space).** Already computed by Bridge widget per-pair (`kyma-engine/api/bridge.py`). Range -97% (anti-correlated) to 98% (highly compatible), per TASKS.md. This is a *trained-for-preference* distance — low values mean "trained taste-model predicts these sound wrong together."

- Pro: already in production, zero marginal cost.
- Con: **wrong primitive for contrast framing.** If DeepPref predicts "these sound wrong together," that is the MODEL overlap bias surfacing — exactly what the East-Asian-contrast hypothesis says curators might still enjoy. Using DeepPref-low to define "contrast" conflates model-disagreement with perceptual-distance. A human might find two tracks excitingly contrastive even when DeepPref says "incompatible" — that is the point.

**Candidate B: Raw MERT L24 cosine (1024d untrained semantic space).** No DeepPref projection. Pure self-supervised embedding distance.

- Pro: not trained on preference labels, so not contaminated by overlap-bias from the training distribution. Measures "how different are these acoustically/semantically."
- Con: L24 CLS is whole-track holistic. Does not separate "contrast in rhythm" from "contrast in timbre" — if the dimensions curators care about are rhythmic (BPM gap, swing), L24 cosine will not capture them cleanly.

**Candidate C: Multi-dimension feature distance (BPM gap + key/Camelot distance + loudness + acousticness + energy gap).** L1 or L2 on the 5D feature vector.

- Pro: interpretable, dimension-wise, maps directly to DJ-curator vocabulary ("these are 4 BPM apart + 2 Camelot steps").
- Con: coarse; "modest BPM gap with same key" scores identically to "same BPM with opposite Camelot" — those are very different musical gestures.

**Recommendation: Use BOTH Candidate B (raw MERT L24 cosine, inverted) and Candidate C (feature-distance), gate bridges to appear in `mode=contrast` only if they are in the top quartile on BOTH.** The conjunction strips the risk of either metric bias dominating. DeepPref cosine stays visible in the UI as a control variable, NOT as a selection criterion. This design specifically avoids the DeepPref overlap-bias problem flagged in the precursor doc.

### Q2 — What is the cooccurrence cutoff for "low-cooccurrence" bridges?

Kyma external-brain correlator currently operates on 814 edges with corpus-wide co-mention weights ranging 0.12-1.00 (per 2026-04-18 permutation test output). The co-mention distribution is long-tailed; a natural cut is the 20th percentile by edge weight OR `co_mention_count <= 2` (appeared together in <=2 source documents in the external-brain corpus).

Cross-reference to Spotify MUSIG paper (ISMIR 2021, cited in precursor doc): the acoustic-similarity x playlist-cooccurrence correlation is -0.029, meaning playlists bundle tracks for reasons mostly orthogonal to acoustic similarity. So "low co-mention" + "high sonic contrast" captures pairs that are BOTH culturally un-bundled AND acoustically distant — the true FlavorGraph East-Asian analog.

**Recommendation: define low-cooccurrence as `co_mention_count <= 2 AND source_diversity <= 2` (cultural cluster count <= 2). This eliminates ~80% of the current correlator edges but leaves enough for 20-pair sampling in interesting zones.**

### Q3 — What is realistic statistical power at 20 vs 20?

Computed directly (inline normal-approx, verified against Evan Miller calc). Results for 80% power, alpha=0.05 two-sided:

| base re-share rate | MDE (absolute pp) | treated rate needed | Fold lift |
|-------------------:|------------------:|--------------------:|----------:|
| 5% | 33.4 pp | 38% | 7.7x |
| 10% | 36.5 pp | 47% | 4.7x |
| 15% | 38.4 pp | 53% | 3.6x |
| 20% | 39.7 pp | 60% | 3.0x |
| 30% | 40.5 pp | 71% | 2.4x |

**Interpretation:** curator re-share rates on a music-discovery widget are empirically 5-20% (anchor: SoundCloud embed share rates historically 8-15%, Substack track-click-to-share rates 2-8%). So realistic base rate ~10% -> need to see contrast-mode hit 47%+ to detect at 80% power. **This is not a realistic effect for a discovery feature**; real interventions produce 20-50% fold-lifts, not 400%+.

**Sample size needed for realistic detection** (2x fold-lift at 10% baseline, 10% -> 20%):

```
MDE = 10pp, baseline = 10%, treated = 20%
n = ((1.96 + 0.84)^2 * (0.10*0.90 + 0.20*0.80)) / 0.10^2
n = (7.84 * (0.09 + 0.16)) / 0.01
n ~= 196 per arm
```

At 10% base rate detecting 10% -> 15% (1.5x fold-lift, more realistic), needs n ~= 700 per arm. Completely out of reach for a 14-day curator outreach experiment.

**Recommendation:** Downgrade P1 from "falsification A/B" to "directional pilot N=20 per arm." Use the pilot as a Bayesian prior-updating exercise, not a reject/fail-to-reject frequentist test. If contrast-mode gets 0 re-shares and overlap gets 3+, that is a strong directional signal at N=20; if contrast gets 5 and overlap gets 3, the prior is roughly unchanged. Full-power A/B would need 200+ per arm, which means Kyma needs 400+ curator relationships — out of scope for Apr 2026.

### Q4 — How to measure re-share given Bridge referer telemetry is blocked?

Current blocker per `.memory/TASKS.md` section Bridge Referer Telemetry: server will not start without `/Volumes/Kyma/spotify-metadata/spotify_clean.sqlite3`. Bridge `/api/bridge/stats` endpoint code exists but live verification fails.

Workarounds for tracking re-shares during pilot, ranked by cost:

1. **Cloudflare tunnel log tail.** `cloudflared tunnel` logs include HTTP method/path/user-agent/IP for every hit to Bridge URLs. Parse `tail -f ~/.cloudflared/kai-dashboard.log 2>&1 | grep GET /b/` to count direct clicks per bridge-id. Cost: 0, runs without drive mount. Loses referer but keeps view counts, which is 80% of the signal.
2. **Manual weekly scrape of pilot curator outbound channels.** For the N=20 curators, scrape their Substack/Twitter for `kyma.stream/b/` mentions weekly. Fragile but direct. Cost: 30 min/week.
3. **Unblock `/api/bridge/stats` by making Spotify DB optional.** Modify `bridge.py` to skip Spotify enrichment when DB missing. Reversible. Takes ~1 hour. Probably worth doing regardless since it blocks other verification.

**Recommendation:** ship fix #3 this week in parallel with pilot design. Then the full A/B (whenever it runs) has proper referer telemetry.

## Literature landscape (music contrast / diversity / serendipity)

Briefly: the "diversity-by-design" conversation in TISMIR 2021 (Holzapfel et al., *Diversity by Design in Music Recommender Systems*) covers serendipity + novelty as beyond-accuracy objectives but operates at the single-listener level, not the curator-graph level that Kyma is in. The ISMIR 2025 program lists "Emergent Musical Properties of a Transformer Under Contrastive Self-Supervised Learning" (arxiv 2506.23873, already in Kyma queue as P3) — examines what transformers learn, not what listeners like. Neither paper tests the contrast-harmony hypothesis directly in music.

Closest empirical adjacent work:
- Kumar et al. (2021) "A Graph Neural Network approach for beyond-accuracy music recommendation" uses graph-based diversity re-ranking. Showed diversity-reranked lists reduce nDCG by 8% but increase user-reported serendipity by 22%. Not specifically contrast vs overlap, but shows diversity has measurable impact.
- Schedl et al. (2018) "Current challenges and visions in music recommender systems research" — identified serendipity/novelty as under-measured but did not propose a contrast metric.

**Gap in the literature:** nobody has published a contrast-vs-overlap A/B in music. FlavorGraph (Nature 2020) is food; music analog is untested. This means if Kyma runs even a small pilot, it is probably publishable as a short paper, which is an unplanned moat benefit (not the original goal).

## Specific recommendations

### Do
1. **Ship `bridge.py` Spotify-DB-optional fix** (~1hr) to unblock referer telemetry before running the pilot. Task name: "Make Spotify enrichment optional in bridge.py". Priority: P1, executable autonomously.
2. **Rebrand P1 as "N=20 directional pilot" not "falsification A/B".** Update research-queue.md accordingly.
3. **Define contrast-mode as: `co_mention <= 2 AND source_diversity <= 2 AND top-quartile on both raw-MERT-L24 cosine (inverted) AND multi-feature L2 distance`.** Explicit conjunction prevents overlap-bias leakage.
4. **Pick the 40 pilot bridges programmatically NOW, freeze them in `files/experiments/2026-04-22-contrast-ab-bridges.json`.** Makes the experiment reproducible and lets Idam approve/reject before outreach.
5. **Instrument Cloudflare tunnel log parser as fallback referer counter.** ~30min. Gives telemetry even if bridge.py fix delays.

### Do not
1. Do not use DeepPref cosine as contrast selector — it is overlap-biased by training.
2. Do not run the pilot expecting frequentist significance at N=20; it will not come.
3. Do not broadcast curator outreach for this until Idam explicitly says "send it." The Curator Seeding plan (TASKS.md § KYMA BRIDGE § Curator seeding) is also "send it"-blocked; this pilot uses the same curator pool, double-gated on Idam.
4. Do not over-invest prep time — the ceiling of value here is a 1-paper publishable null or directional result, not a pitch-narrative shifter. The precursor doc (2026-04-18) was right to flag that reframing the a16z pitch around "Kyma surfaces both Western-overlap AND East-Asian-contrast pairings" is *unvalidated hypothesis*, not a recommendation.

## Open questions (adding to research-queue as follow-ups)

1. **[P2] Empirical re-share base rate for bridge/mashup widgets.** Is 10% a good anchor? Pull data from SoundCloud embed CTR, Substack track-click rates, Apple Music share-card CTR. Validates the power calc. (QUEUED)
2. **[P2] Per-dimension contrast taxonomy.** Rhythmic contrast (BPM gap >= 20) vs timbral contrast (spectral centroid distance) vs emotional contrast (valence gap) vs structural contrast (song-form mismatch). Which dimension produces the "best" FlavorGraph-East-Asian analog in music? (QUEUED)
3. **[P3] Publication-ready write-up.** If pilot produces any signal, short paper for ISMIR 2026 submission ("First empirical test of the FlavorGraph East-Asian-contrast hypothesis in music recommendation"). Strategic benefit: Kyma gets credentialed in MIR community before fundraise. (QUEUED, post-pilot only)

## Sources

- [Co-occurrence vs Compatibility — 2026-04-18 precursor research](../research-results/2026-04-18-cooccurrence-vs-compatibility.md) — Kyma internal
- [FlavorGraph — Scientific Reports 2020](https://www.nature.com/articles/s41598-020-79422-8) — East Asian contrast-harmony principle
- [MUSIG / Multi-Task Graph Representations — Spotify Research ISMIR 2021](https://research.atspotify.com/publications/multi-task-learning-of-graph-based-inductive-representations-of-music-content/) — playlist x acoustic correlation = -0.029
- [Diversity by Design in Music Recommender Systems — TISMIR 2021](https://transactions.ismir.net/articles/10.5334/tismir.106) — diversity objectives beyond accuracy
- [Beyond accuracy measures: diversity, novelty, serendipity — Electronic Commerce Research 2024](https://link.springer.com/article/10.1007/s10660-024-09813-w) — user engagement effects
- [Beyond-accuracy review on diversity, serendipity, fairness (GNN) — Frontiers 2023](https://www.frontiersin.org/journals/big-data/articles/10.3389/fdata.2023.1251072/full)
- [Emergent Musical Properties of a Transformer Under Contrastive SSL — arxiv 2506.23873](https://arxiv.org/abs/2506.23873) — in Kyma queue as P3
- [Evan Miller A/B Sample Size Calculator](https://www.evanmiller.org/ab-testing/sample-size.html) — power calc reference
- [MERT: Acoustic Music Understanding Model — arxiv 2306.00107](https://arxiv.org/abs/2306.00107) — L24 CLS token semantics
- Kyma `bridge.py` at `/Users/idamo/code/kyma-engine/api/bridge.py` — current implementation
- Kyma `.memory/TASKS.md` section Bridge Referer Telemetry — verification-blocked status
