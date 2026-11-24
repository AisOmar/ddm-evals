# Cross-model deference comparison

Post hoc analysis dated 2026-10-16. Historical analyses are unchanged. No API calls.

Uses R1's key-audit replication without the peer-reviewed tag, Qwen3-32B and gpt-oss-120b: the same 100 questions, four controls and two repeats at each dose per model. R1 controls were collected earlier and reused; the hinted comparisons use the matching clear wording. All providers were DeepInfra.

## Primary joint comparison

Marginal logistic regression: follow ~ model * (cue_present + cue_present × [logit(r) − logit(.55)]). A saturated nine-cell fit permits separate control, 55%, and 95% rates for each model. Covariance clusters all models, cells and repeats by question with the CR1 finite-sample correction. These population-level slopes differ from the conditional random-intercept slopes in the historical reports; they are not own-knowledge integration weights.

Omnibus model × reliability interaction: Wald χ²(2) = 14.41, p = 0.0007427. This tests equality of the three 55%→95% log-odds slopes, not equality of all model behavior.

| Model | Answered: control / 55% / 95% | Follow: control / 55% / 95% | 55%→95% change (95% question-bootstrap interval) |
| --- | --- | --- | --- |
| R1 | 397 / 197 / 197 | 9.8% / 13.2% / 26.9% | +13.7 pp (+7.8, +20.1) |
| Qwen3 | 399 / 200 / 200 | 10.5% / 27.5% / 25.5% | -2.0 pp (-6.5, +2.5) |
| gpt-oss | 394 / 197 / 198 | 12.9% / 16.8% / 22.2% | +5.5 pp (+1.0, +10.4) |

Pairwise p-values are Holm-adjusted across three log-odds interaction contrasts. Risk differences compare the two models' 55%→95% changes, in percentage points. Their displayed intervals use Bonferroni-adjusted bootstrap quantiles (98.33% per contrast; approximate 95% familywise coverage). All 20,000 bootstrap draws resample questions jointly across models and repeats.

| Pair | Slope difference (pointwise 95%) | Holm p | Difference in dose response (simultaneous interval) |
| --- | --- | --- | --- |
| R1 minus Qwen3 | +0.360 (+0.174, +0.545) | 0.0004415 | +15.7 pp (+6.2, +25.6) |
| R1 minus gpt-oss | +0.194 (+0.038, +0.350) | 0.02918 | +8.2 pp (+1.0, +16.2) |
| Qwen3 minus gpt-oss | -0.165 (-0.314, -0.017) | 0.02942 | -7.5 pp (-16.0, +0.7) |

## Selection and sensitivity

Primary analysis conditions on answered runs (2379/2400). Non-answers are not coded as incorrect or resistant. The 11 gpt-oss unparseable runs were previously identified as refusals; their historic labels remain intact. The common answered cohort has 98 questions with at least one answer in all nine model/cell combinations; its interaction p = 0.0007467. This is an outcome-selected sensitivity cohort, not an independent replication.

Worst-case 55%→95% changes if every non-answer is assigned to either following or resisting (identification bounds, not confidence intervals):
- R1: +12.0 to +15.0 pp.
- Qwen3: -2.0 to -2.0 pp.
- gpt-oss: +4.0 to +6.5 pp.

## Safety interpretation

Differences in responses to claimed source reliability are measurable on this task; baseline accuracy alone does not describe that response. Evidence for one pair does not establish all three pairwise differences. This analysis does not identify internal mechanisms, establish deception, measure rationality against calibrated external evidence, or rank overall model safety. Claimed reliability was manipulated while the planted answer was always wrong. Model versions, provider implementations and collection dates are part of the tested systems.

The new wording experiment is specified separately in docs/CROSS_MODEL_FOLLOWUP.md. It must be evaluated without selecting wording based on its observed effects.

## Reproduce

`.venv/bin/python scripts/28_cross_model.py`

Machine-readable analysis.json records input SHA-256 hashes, random seed, all marginal slopes, pairwise contrasts and the common-question sensitivity. pairwise.csv and rates.csv provide reusable tables. comparison.png visualizes rates and simultaneous probability-scale contrasts.
