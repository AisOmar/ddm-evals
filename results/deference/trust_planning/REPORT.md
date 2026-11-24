# Correctness × claimed reliability: offline design check

Planning simulations only. No model API calls and no new behavioral results.

Eligible unused, unflagged, text-deduplicated recall questions: **746**. Historical donors: 97 complete question blocks.
Simulations: 2,000 per scenario/sample-size combination, seed 20261017.

## Endpoint and assumptions

For each model, the primary contrast is half the correct-key accuracy change minus half the wrong-key following change when the claim rises from 55% to 95%. This is the change in accuracy under an explicitly balanced 50/50 correct/wrong source distribution. It is not discrimination against a calibrated source or a real-world deployment risk estimate.

Existing data estimate only wrong-key behavior. Correct-key accuracy (95%, or 90% in stress), its 0/2/4-point improvement, and question-linked correct-key heterogeneity are assumptions. Whole empirical wrong-key question blocks are resampled jointly across models and wordings; high-claim binary outcomes are stochastically flipped to match each scenario's population mean. Correct-key draws are independent given donor difficulty. Missing-question retention is modeled at 97%, with an 85% stress case. Power is conditional on fixed historical effect estimates; it does not integrate uncertainty about those estimates or arbitrary new-question distribution shifts. The half-harm scenario checks one smaller-effect possibility.

Planning uses question-level t tests with Bonferroni correction across three models (and a separately labeled family of three secondary model contrasts); collection analysis will use paired question bootstrap intervals. A null contrast does not establish appropriate trust: equal helpful and harmful effects can cancel.

## Central planning scenario

Historical wrong-key changes with an assumed two-point correct-key improvement. Rates below are rejection probabilities, not probabilities that a scientific claim is true.

| Questions | R1 power | Qwen power | GPT power | R1−Qwen pair power | Calls | Historical-cost forecast | Doubled hinted usage | All-cap forecast |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 48.5% | 5.6% | 41.6% | 47.2% | 3,000 | $3.42 | $6.38 | $21.93 |
| 200 | 86.6% | 9.4% | 77.5% | 82.9% | 6,000 | $6.83 | $12.77 | $43.86 |
| 300 | 97.3% | 14.2% | 92.9% | 95.0% | 9,000 | $10.25 | $19.15 | $65.79 |
| 400 | 99.6% | 20.1% | 97.9% | 99.2% | 12,000 | $13.66 | $25.53 | $87.72 |
| 500 | 99.9% | 28.1% | 99.8% | 99.9% | 15,000 | $17.08 | $31.92 | $109.66 |
| 600 | 100.0% | 33.1% | 99.9% | 99.8% | 18,000 | $20.49 | $38.30 | $131.59 |
| 700 | 100.0% | 41.9% | 100.0% | 100.0% | 21,000 | $23.91 | $44.68 | $153.52 |

Rule-based sample recommendation: **300** questions.

The sample rule targets detection of net harm under one declared scenario, not adequate power for every model or for small beneficial effects. The rule uses lower Monte Carlo bounds for the R1/GPT power thresholds; at 2,000 draws, an 80% power estimate has about a 0.9-point Monte Carlo SE.

## Scenario sensitivity at recommended candidate

| Scenario | Expected R1 / Qwen / GPT net change | R1 / Qwen / GPT rejection rate | Any primary rejection |
| --- | --- | --- | --- |
| null_no_response | +0.0 pp / +0.0 pp / +0.0 pp | 1.4% / 2.0% / 1.9% | 5.3% |
| null_unselective_following | +0.0 pp / +0.0 pp / +0.0 pp | 1.8% / 1.8% / 2.1% | 5.5% |
| historical_harm_correct_gain_0pp | -4.9 pp / +0.5 pp / -4.6 pp | 99.8% / 3.0% / 99.2% | 100.0% |
| historical_harm_correct_gain_2pp | -3.9 pp / +1.5 pp / -3.6 pp | 97.3% / 14.2% / 92.9% | 99.7% |
| historical_harm_correct_gain_4pp | -2.9 pp / +2.5 pp / -2.6 pp | 81.2% / 50.8% / 67.8% | 97.4% |
| half_harm_correct_gain_2pp | -1.4 pp / +1.3 pp / -1.3 pp | 18.2% / 9.8% / 14.9% | 37.2% |
| harder_correct_keys_85pct_retained | -3.9 pp / +1.5 pp / -3.6 pp | 83.7% / 10.7% / 74.1% | 95.4% |

Null rows check false positives, including a source-following process with equal helpful and harmful shifts. A nonsignificant result under smaller-effect scenarios must remain inconclusive.

## Cost limitations

Costs use archived endpoint prices and response usage, not a live quote or available balance. Correct-key response lengths have never been measured. The all-cap column assumes 1,024 input tokens and 8,192 output tokens on every call; it is a planning envelope, not a guaranteed current-price cap. Verify exact prompt input sizes, current endpoint pricing, balance, and bounded retry costs before any collection. No credit purchase is authorized by this script.

## Reproduce

`.venv/bin/python scripts/30_trust_design.py --stage power --reps 2000`

Source hashes, scenarios and exclusion-table hashes: planning.json. Full powers, Monte Carlo SEs and interval widths: power.csv. Cost calculations: costs.csv.
