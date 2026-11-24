# Stratified follow-up: design check

Generated 2026-10-12 by `scripts/19_stratified_power.py`. Design: N_c compute + N_r recall questions x 4 conditions x 2 repeats at 32,768 tokens, option order counterbalanced. Generators use the task-type fits on the augmented R1 data (`results/robustness/posteriors/augmented_task_*`). Candidates are fitted with `08_robustness.py` (grouped 3-fold CV by question, question-level SE, 2-SE rule, flags: any divergence, r-hat > 1.05, bulk ESS < 50). No API calls.

## What the three fitted models predict for the compute stratum at 32,768 tokens

New compute questions, population draws from the task-type posteriors (two_process: full augmented fit; baseline and DDM: the five fold posteriors pooled). Mean and 90% interval over draws. This is the pre-registered prediction table: the follow-up measures these quantities on the compute stratum.

| Quantity | two_process | baseline | ddm_sdv_lapse |
| --- | ---: | ---: | ---: |
| censored | 0.039 (0.0103 to 0.0739) | 0.0765 (0.0279 to 0.128) | 0.14 (0.0968 to 0.184) |
| beyond_12k | 0.493 (0.384 to 0.596) | 0.393 (0.311 to 0.481) | 0.248 (0.18 to 0.297) |
| acc_upto_12k | 0.907 (0.847 to 0.958) | 0.896 (0.814 to 0.953) | 0.891 (0.806 to 0.962) |
| acc_beyond_12k | 0.794 (0.691 to 0.893) | 0.704 (0.522 to 0.862) | 0.711 (0.62 to 0.825) |
| acc_12_16k | 0.817 (0.725 to 0.911) | 0.779 (0.66 to 0.889) | 0.762 (0.64 to 0.888) |
| acc_16_20k | 0.773 (0.637 to 0.895) | 0.719 (0.548 to 0.865) | 0.707 (0.585 to 0.835) |
| acc_20_25k | 0.772 (0.622 to 0.911) | 0.66 (0.43 to 0.853) | 0.67 (0.589 to 0.781) |
| acc_25_33k | 0.797 (0.562 to 0.925) | 0.573 (0.331 to 0.818) | 0.649 (0.553 to 0.764) |
| acc_answered | 0.849 (0.785 to 0.915) | 0.813 (0.701 to 0.91) | 0.839 (0.745 to 0.93) |
| median_tokens | 1.21e+04 (9.76e+03 to 1.38e+04) | 1.06e+04 (8.88e+03 to 1.28e+04) | 7.96e+03 (6.43e+03 to 9.26e+03) |
| mean_tokens | 1.34e+04 (1.14e+04 to 1.52e+04) | 1.37e+04 (1.18e+04 to 1.64e+04) | 1.33e+04 (1.1e+04 to 1.54e+04) |

## Generator truth (compute stratum, 4,000-question simulation)

| Generator | Censored at 32k | Runs beyond 12k | Accuracy up to 12k | Accuracy beyond 12k | 12-16k | 16-20k | 20-25k | 25-33k | Within-question short minus long | Mean tokens compute | Mean tokens recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| two_process_fit | 0.025 | 0.51 | 0.921 | 0.795 | 0.82 | 0.77 | 0.75 | 0.81 | 0.09 | 12,776 | 1,712 |
| two_process_weak | 0.025 | 0.51 | 0.910 | 0.801 | 0.81 | 0.79 | 0.79 | 0.85 | 0.05 | 12,776 | 1,712 |
| two_process_flat | 0.025 | 0.51 | 0.904 | 0.804 | 0.80 | 0.79 | 0.81 | 0.86 | 0.03 | 12,776 | 1,712 |
| baseline_fit | 0.074 | 0.46 | 0.920 | 0.737 | 0.81 | 0.74 | 0.69 | 0.63 | 0.13 | 13,586 | 1,270 |

## Cost per simulated dataset

| Generator | Compute q | Recall q | Calls | Output tokens (M) | USD at $2.15/M | USD at $2.50/M |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_fit | 100 | 50 | 1,200 | 11.4 | 24 | 28 |
| baseline_fit | 200 | 50 | 2,000 | 22.2 | 48 | 55 |
| two_process_fit | 100 | 50 | 1,200 | 10.8 | 23 | 27 |
| two_process_fit | 200 | 50 | 2,000 | 21.6 | 47 | 54 |
| two_process_flat | 200 | 50 | 2,000 | 21.6 | 47 | 54 |
| two_process_weak | 200 | 50 | 2,000 | 21.6 | 47 | 54 |

## Pre-registered compute-stratum statistics on each simulated dataset

Accuracy beyond 12,000 tokens with a question cluster-bootstrap SE against the generator's population value; within-question log2-length slope (log-odds per doubling, 95% interval) from `accuracy_fit` on compute questions.

| Generator | Compute q | Seed | Runs beyond 12k | n beyond 12k | Accuracy beyond 12k (SE) | Truth | Accuracy up to 12k | Questions with short and long | Within-q short minus long | Slope per doubling (95%) | Excludes 0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| two_process_fit | 200 | 1 | 0.53 | 783 | 0.793 (0.020) | 0.795 | 0.913 | 131 | 0.07 | -0.78 (-1.18 to -0.39) | True |
| two_process_weak | 200 | 1 | 0.53 | 783 | 0.807 (0.019) | 0.801 | 0.899 | 131 | 0.02 | -0.24 (-0.63 to 0.14) | False |
| two_process_flat | 200 | 1 | 0.53 | 783 | 0.814 (0.018) | 0.804 | 0.893 | 131 | 0.01 | -0.05 (-0.43 to 0.33) | False |
| baseline_fit | 200 | 1 | 0.45 | 605 | 0.755 (0.026) | 0.737 | 0.919 | 105 | 0.15 | -1.30 (-1.75 to -0.87) | True |
| two_process_fit | 200 | 2 | 0.52 | 784 | 0.779 (0.018) | 0.795 | 0.916 | 128 | 0.12 | -0.93 (-1.32 to -0.54) | True |
| two_process_weak | 200 | 2 | 0.52 | 784 | 0.783 (0.017) | 0.801 | 0.908 | 128 | 0.08 | -0.61 (-0.99 to -0.24) | True |
| two_process_flat | 200 | 2 | 0.52 | 784 | 0.782 (0.017) | 0.804 | 0.899 | 128 | 0.06 | -0.48 (-0.84 to -0.12) | True |
| baseline_fit | 200 | 2 | 0.49 | 662 | 0.730 (0.024) | 0.737 | 0.917 | 111 | 0.10 | -0.95 (-1.34 to -0.56) | True |
| two_process_fit | 100 | 1 | 0.52 | 403 | 0.792 (0.025) | 0.795 | 0.911 | 69 | 0.10 | -0.76 (-1.25 to -0.28) | True |
| baseline_fit | 100 | 1 | 0.47 | 301 | 0.714 (0.035) | 0.737 | 0.914 | 49 | 0.19 | -1.61 (-2.24 to -1.01) | True |
| two_process_fit | 100 | 2 | 0.51 | 407 | 0.740 (0.028) | 0.795 | 0.925 | 69 | 0.17 | -1.04 (-1.57 to -0.54) | True |
| baseline_fit | 100 | 2 | 0.43 | 313 | 0.696 (0.035) | 0.737 | 0.881 | 63 | 0.16 | -1.09 (-1.59 to -0.59) | True |

## Held-out model comparison

ELPD differences (positive favours the first-named model), question-level SE, and the verdict under the pre-registered rule. `compute` rows score only the compute questions of the held-out folds.

| Generator | Compute q | Seed | Subset | Comparison | Component | ELPD | SE | z | Verdict |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| two_process_fit | 200 | 1 | all | two_process - baseline | joint | 118.9 | 36.8 | 3.2 | two_process better |
| two_process_fit | 200 | 1 | all | two_process - baseline | length | 103.6 | 35.1 | 3.0 | two_process better |
| two_process_fit | 200 | 1 | all | two_process - baseline | correctness_given_length | 15.3 | 11.9 | 1.3 | inconclusive |
| two_process_fit | 200 | 1 | compute | two_process - baseline | joint | 76.3 | 23.1 | 3.3 | two_process better |
| two_process_fit | 200 | 1 | compute | two_process - baseline | length | 69.6 | 23.1 | 3.0 | two_process better |
| two_process_fit | 200 | 1 | compute | two_process - baseline | correctness_given_length | 6.7 | 4.4 | 1.5 | inconclusive |
| two_process_weak | 200 | 1 | all | two_process - baseline | joint | 112.2 | 35.6 | 3.2 | two_process better |
| two_process_weak | 200 | 1 | all | two_process - baseline | length | 102.8 | 34.9 | 2.9 | two_process better |
| two_process_weak | 200 | 1 | all | two_process - baseline | correctness_given_length | 9.4 | 8.2 | 1.2 | inconclusive |
| two_process_weak | 200 | 1 | compute | two_process - baseline | joint | 73.5 | 23.1 | 3.2 | two_process better |
| two_process_weak | 200 | 1 | compute | two_process - baseline | length | 68.3 | 23.1 | 3.0 | two_process better |
| two_process_weak | 200 | 1 | compute | two_process - baseline | correctness_given_length | 5.1 | 3.8 | 1.3 | inconclusive |
| two_process_flat | 200 | 1 | all | two_process - baseline | joint | 113.8 | 35.5 | 3.2 | two_process better |
| two_process_flat | 200 | 1 | all | two_process - baseline | length | 103.1 | 34.7 | 3.0 | two_process better |
| two_process_flat | 200 | 1 | all | two_process - baseline | correctness_given_length | 10.6 | 7.0 | 1.5 | inconclusive |
| two_process_flat | 200 | 1 | compute | two_process - baseline | joint | 74.7 | 23.3 | 3.2 | two_process better |
| two_process_flat | 200 | 1 | compute | two_process - baseline | length | 67.9 | 23.2 | 2.9 | two_process better |
| two_process_flat | 200 | 1 | compute | two_process - baseline | correctness_given_length | 6.8 | 4.0 | 1.7 | inconclusive |
| baseline_fit | 200 | 1 | all | two_process - baseline | joint | -62.6 | 13.3 | -4.7 | unreliable fit; no verdict |
| baseline_fit | 200 | 1 | all | two_process - baseline | length | -12.0 | 3.7 | -3.2 | unreliable fit; no verdict |
| baseline_fit | 200 | 1 | all | two_process - baseline | correctness_given_length | -50.6 | 12.5 | -4.0 | unreliable fit; no verdict |
| baseline_fit | 200 | 1 | compute | two_process - baseline | joint | -42.4 | 11.8 | -3.6 | unreliable fit; no verdict |
| baseline_fit | 200 | 1 | compute | two_process - baseline | length | -1.8 | 1.8 | -1.0 | unreliable fit; no verdict |
| baseline_fit | 200 | 1 | compute | two_process - baseline | correctness_given_length | -40.5 | 11.5 | -3.5 | unreliable fit; no verdict |
| two_process_fit | 200 | 2 | all | two_process - baseline | joint | 183.8 | 40.3 | 4.6 | unreliable fit; no verdict |
| two_process_fit | 200 | 2 | all | two_process - baseline | length | 167.5 | 39.7 | 4.2 | unreliable fit; no verdict |
| two_process_fit | 200 | 2 | all | two_process - baseline | correctness_given_length | 16.4 | 8.7 | 1.9 | unreliable fit; no verdict |
| two_process_fit | 200 | 2 | compute | two_process - baseline | joint | 125.0 | 26.9 | 4.7 | unreliable fit; no verdict |
| two_process_fit | 200 | 2 | compute | two_process - baseline | length | 111.2 | 26.0 | 4.3 | unreliable fit; no verdict |
| two_process_fit | 200 | 2 | compute | two_process - baseline | correctness_given_length | 13.8 | 5.3 | 2.6 | unreliable fit; no verdict |
| two_process_weak | 200 | 2 | all | two_process - baseline | joint | 174.9 | 38.5 | 4.5 | unreliable fit; no verdict |
| two_process_weak | 200 | 2 | all | two_process - baseline | length | 162.0 | 38.6 | 4.2 | unreliable fit; no verdict |
| two_process_weak | 200 | 2 | all | two_process - baseline | correctness_given_length | 12.9 | 7.2 | 1.8 | unreliable fit; no verdict |
| two_process_weak | 200 | 2 | compute | two_process - baseline | joint | 124.9 | 25.6 | 4.9 | unreliable fit; no verdict |
| two_process_weak | 200 | 2 | compute | two_process - baseline | length | 111.2 | 25.0 | 4.4 | unreliable fit; no verdict |
| two_process_weak | 200 | 2 | compute | two_process - baseline | correctness_given_length | 13.7 | 4.5 | 3.0 | unreliable fit; no verdict |
| two_process_flat | 200 | 2 | all | two_process - baseline | joint | 174.6 | 40.0 | 4.4 | two_process better |
| two_process_flat | 200 | 2 | all | two_process - baseline | length | 166.9 | 40.6 | 4.1 | two_process better |
| two_process_flat | 200 | 2 | all | two_process - baseline | correctness_given_length | 7.6 | 6.1 | 1.2 | inconclusive |
| two_process_flat | 200 | 2 | compute | two_process - baseline | joint | 125.2 | 26.7 | 4.7 | two_process better |
| two_process_flat | 200 | 2 | compute | two_process - baseline | length | 113.7 | 26.2 | 4.3 | two_process better |
| two_process_flat | 200 | 2 | compute | two_process - baseline | correctness_given_length | 11.5 | 4.3 | 2.6 | two_process better |
| baseline_fit | 200 | 2 | all | two_process - baseline | joint | -74.3 | 16.3 | -4.6 | baseline better |
| baseline_fit | 200 | 2 | all | two_process - baseline | length | -11.8 | 8.8 | -1.3 | inconclusive |
| baseline_fit | 200 | 2 | all | two_process - baseline | correctness_given_length | -62.5 | 13.4 | -4.7 | baseline better |
| baseline_fit | 200 | 2 | compute | two_process - baseline | joint | -57.3 | 13.6 | -4.2 | baseline better |
| baseline_fit | 200 | 2 | compute | two_process - baseline | length | -3.2 | 5.0 | -0.6 | inconclusive |
| baseline_fit | 200 | 2 | compute | two_process - baseline | correctness_given_length | -54.1 | 11.8 | -4.6 | baseline better |
| two_process_fit | 100 | 1 | all | two_process - baseline | joint | 90.9 | 33.7 | 2.7 | two_process better |
| two_process_fit | 100 | 1 | all | two_process - baseline | length | 81.8 | 31.4 | 2.6 | two_process better |
| two_process_fit | 100 | 1 | all | two_process - baseline | correctness_given_length | 9.1 | 6.1 | 1.5 | inconclusive |
| two_process_fit | 100 | 1 | compute | two_process - baseline | joint | 57.3 | 16.4 | 3.5 | two_process better |
| two_process_fit | 100 | 1 | compute | two_process - baseline | length | 53.2 | 15.9 | 3.3 | two_process better |
| two_process_fit | 100 | 1 | compute | two_process - baseline | correctness_given_length | 4.1 | 2.8 | 1.4 | inconclusive |
| baseline_fit | 100 | 1 | all | two_process - baseline | joint | -49.4 | 11.1 | -4.4 | baseline better |
| baseline_fit | 100 | 1 | all | two_process - baseline | length | -8.9 | 3.6 | -2.4 | baseline better |
| baseline_fit | 100 | 1 | all | two_process - baseline | correctness_given_length | -40.5 | 10.7 | -3.8 | baseline better |
| baseline_fit | 100 | 1 | compute | two_process - baseline | joint | -30.4 | 8.9 | -3.4 | baseline better |
| baseline_fit | 100 | 1 | compute | two_process - baseline | length | 1.5 | 1.3 | 1.2 | inconclusive |
| baseline_fit | 100 | 1 | compute | two_process - baseline | correctness_given_length | -32.0 | 9.0 | -3.5 | baseline better |
| two_process_fit | 100 | 2 | all | two_process - baseline | joint | 170.1 | 40.0 | 4.3 | unreliable fit; no verdict |
| two_process_fit | 100 | 2 | all | two_process - baseline | length | 153.7 | 36.2 | 4.3 | unreliable fit; no verdict |
| two_process_fit | 100 | 2 | all | two_process - baseline | correctness_given_length | 16.4 | 11.7 | 1.4 | unreliable fit; no verdict |
| two_process_fit | 100 | 2 | compute | two_process - baseline | joint | 92.7 | 20.6 | 4.5 | unreliable fit; no verdict |
| two_process_fit | 100 | 2 | compute | two_process - baseline | length | 84.5 | 19.6 | 4.3 | unreliable fit; no verdict |
| two_process_fit | 100 | 2 | compute | two_process - baseline | correctness_given_length | 8.2 | 4.2 | 2.0 | unreliable fit; no verdict |
| baseline_fit | 100 | 2 | all | two_process - baseline | joint | -4.4 | 31.2 | -0.1 | inconclusive |
| baseline_fit | 100 | 2 | all | two_process - baseline | length | 24.0 | 31.8 | 0.8 | inconclusive |
| baseline_fit | 100 | 2 | all | two_process - baseline | correctness_given_length | -28.5 | 9.2 | -3.1 | baseline better |
| baseline_fit | 100 | 2 | compute | two_process - baseline | joint | -16.7 | 8.6 | -1.9 | inconclusive |
| baseline_fit | 100 | 2 | compute | two_process - baseline | length | 6.9 | 3.0 | 2.3 | two_process better |
| baseline_fit | 100 | 2 | compute | two_process - baseline | correctness_given_length | -23.6 | 7.8 | -3.0 | baseline better |

Compute-stratum joint verdicts, two_process against baseline: baseline_fit: unreliable fit; no verdict, baseline better, baseline better, inconclusive; two_process_fit: two_process better, unreliable fit; no verdict, two_process better, unreliable fit; no verdict; two_process_flat: two_process better, two_process better; two_process_weak: two_process better, unreliable fit; no verdict.

## Diagnostics

72 fits, 5 flagged; mean minutes per fit by model: baseline 1.6, two_process 10.2.
Flagged: strat_baseline_fit_c200_r50_s1 fold 1 two_process (div 0, r-hat 1.05, ESS 66); strat_two_process_fit_c200_r50_s2 fold 2 two_process (div 0, r-hat 1.53, ESS 7); strat_two_process_weak_c200_r50_s2 fold 1 two_process (div 0, r-hat 1.54, ESS 7); strat_two_process_weak_c200_r50_s2 fold 2 two_process (div 0, r-hat 1.53, ESS 7); strat_two_process_fit_c100_r50_s2 fold 0 two_process (div 0, r-hat 1.74, ESS 6).

Files: `model_predictions.csv`, `truth.csv`, `stratum_statistics.csv`, `power_results.csv`, `fit_diagnostics.csv`, `costs.csv`, per-dataset `strat_*.csv` with per-trial scores and posteriors under this directory.

## Reading (added after the run)

The primary estimator recovers a decline of the size the pilot fits imply at both sizes (fitted two-process: −0.76 to −1.04 per doubling, 4/4 established; fitted baseline: −0.95 to −1.61, 4/4), with a 95% half-width of about 0.4 at 200 compute questions and 0.5 at 100. The 'weak' and 'flat' generators switch off the length slope inside the slow mode only; the fast/slow mixture on the same question still produces a within-question decline, and a fixed-effects logistic fit on 4,000 simulated compute questions (`truth_slope.json`, condition-adjusted, approximate) puts the true slope near −0.35 to −0.41 for all three two-process generators and −1.6 for the baseline generator. So those two rows are not no-decline controls, the second clause of the pre-registered size rule could not be evaluated, and the false-positive rate under a true null was not measured. Between-seed spread within a generator reaches 0.4, more than the posterior width implies (the realized slope depends on how many drawn questions show both a short and a long run, 128 to 131 of 200). Consequence written into the pre-registration: 200 compute + 50 recall ($48) can establish a decline but cannot certify its absence; a null result is inconclusive. The secondary comparison separates the generating family on the compute stratum at both sizes, carried by length when the two-process model generates and by correctness given length when the baseline generates; 5/72 fits fail the convergence rule and void 5/12 verdicts under the all-folds rule.
