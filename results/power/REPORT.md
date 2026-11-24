# Design power check for the proposed follow-up (simulation, no API calls)

Generated 2026-10-09 by `scripts/12_power_simulation.py --stage summarize`. Fitting, CV, question-level SE and the 2-SE rule are those of `08_robustness.py`; sampler budget 2 chains x 400 draws after 500 tuning steps, grouped three-fold CV.

## Generators

| Generator | What is true | Source of parameters |
| --- | --- | --- |
| sdv_fit | drift-variability DDM + 6% contaminant | posterior means of the five R1 fold fits of `ddm_sdv_lapse` (`generator_parameters.json`) |
| baseline_fit | lognormal length + logistic correctness | posterior means of the five R1 fold fits of `baseline` |
| mixture | neither: fast fixed-drift DDM, plus a slow lognormal mode (P = 22% prose / 60% code, question-varying) whose accuracy falls with length | hand-set to the step-1 and cap-experiment tables |

Calibration against the data (R1 step 1 at 8,192: 43% censored, prose 26% / code 64%; answered accuracy 0.96; medians 890 / 4,900 tokens):

| Generator | Cap | Censored | Prose | Code | Answered accuracy | Median prose tokens | Median code tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sdv_fit | 8,192 | 0.27 | 0.09 | 0.47 | 0.88 | 1,197 | 4,432 |
| sdv_fit | 32,768 | 0.06 | 0.01 | 0.11 | 0.83 | 1,308 | 6,622 |
| baseline_fit | 8,192 | 0.43 | 0.20 | 0.68 | 0.95 | 1,422 | 3,934 |
| baseline_fit | 32,768 | 0.16 | 0.03 | 0.30 | 0.93 | 2,041 | 8,888 |
| mixture | 8,192 | 0.40 | 0.24 | 0.58 | 0.98 | 644 | 2,823 |
| mixture | 32,768 | 0.07 | 0.02 | 0.13 | 0.88 | 716 | 9,804 |

## Verdicts per dataset (joint held-out-question ELPD, DDM minus baseline)

A dataset gets a verdict only if all three folds pass diagnostics for both models (no divergences, r-hat <= 1.05, bulk ESS >= 50); otherwise it is a fit failure. The valid-fold columns rescore the folds that passed.

| Generator | Questions | Seed | ELPD | SE | z | Verdict | Valid folds | z (valid folds) | Verdict (valid folds) | Censored | Accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |
| sdv_fit | 100 | 1 | 170 | 34 | 5.0 | fit failure (2/3 folds); no verdict | 1/3 | 1.7 | inconclusive | 0.05 | 0.77 |
| sdv_fit | 100 | 2 | 121 | 31 | 3.9 | fit failure (2/3 folds); no verdict | 1/3 | 3.3 | DDM better | 0.07 | 0.81 |
| sdv_fit | 100 | 3 | 172 | 28 | 6.2 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.04 | 0.85 |
| sdv_fit | 400 | 1 | 687 | 64 | 10.7 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.06 | 0.80 |
| sdv_fit | 400 | 2 | 524 | 62 | 8.4 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.06 | 0.83 |
| sdv_fit | 400 | 3 | 822 | 93 | 8.8 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.08 | 0.80 |
| baseline_fit | 100 | 1 | -635 | 73 | -8.7 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.14 | 0.95 |
| baseline_fit | 100 | 2 | -420 | 65 | -6.5 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.12 | 0.93 |
| baseline_fit | 100 | 3 | -509 | 72 | -7.1 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.17 | 0.95 |
| baseline_fit | 400 | 1 | 22,770 | 18,273 | 1.2 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.12 | 0.92 |
| baseline_fit | 400 | 2 | -1,792 | 138 | -13.0 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.13 | 0.93 |
| baseline_fit | 400 | 3 | -1,828 | 135 | -13.6 | fit failure (3/3 folds); no verdict | 0/3 | nan | none | 0.14 | 0.92 |
| mixture | 100 | 1 | 261 | 54 | 4.8 | fit failure (1/3 folds); no verdict | 2/3 | 2.9 | DDM better | 0.07 | 0.86 |
| mixture | 100 | 2 | 269 | 54 | 4.9 | fit failure (1/3 folds); no verdict | 2/3 | 3.5 | DDM better | 0.07 | 0.90 |
| mixture | 100 | 3 | 238 | 46 | 5.1 | DDM better | 3/3 | 5.1 | DDM better | 0.07 | 0.88 |
| mixture | 400 | 1 | 1,485 | 99 | 14.9 | fit failure (1/3 folds); no verdict | 2/3 | 10.5 | DDM better | 0.07 | 0.89 |
| mixture | 400 | 2 | 1,158 | 103 | 11.2 | DDM better | 3/3 | 11.2 | DDM better | 0.07 | 0.88 |
| mixture | 400 | 3 | 933 | 101 | 9.2 | fit failure (1/3 folds); no verdict | 2/3 | 8.4 | DDM better | 0.08 | 0.88 |

## Summary

| Generator | Questions | Datasets | Fit failures | DDM better | Baseline better | Inconclusive | Mean z (valid folds) | Fit hours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_fit | 100 | 3.0 | 3.0 | 0.0 | 0.0 | 0.0 | nan | 1.8 |
| baseline_fit | 400 | 3.0 | 3.0 | 0.0 | 0.0 | 0.0 | nan | 3.9 |
| mixture | 100 | 3.0 | 2.0 | 1.0 | 0.0 | 0.0 | 3.8 | 0.6 |
| mixture | 400 | 3.0 | 2.0 | 1.0 | 0.0 | 0.0 | 10.0 | 2.7 |
| sdv_fit | 100 | 3.0 | 3.0 | 0.0 | 0.0 | 0.0 | 2.5 | 0.6 |
| sdv_fit | 400 | 3.0 | 3.0 | 0.0 | 0.0 | 0.0 | nan | 2.9 |

## Power against question count (subsampled from the 400-question datasets)

Question-level differences from the scored 400-question datasets are resampled without replacement; the fits used two thirds of 400 questions, so this understates the loss of training data at small sizes. Direct 100-question fits are in the tables above.

| Generator | Questions | Mean z | P(DDM better) | P(baseline better) | P(inconclusive) |
| --- | ---: | ---: | ---: | ---: | ---: |
| mixture | 50 | 4.1 | 0.99 | 0.00 | 0.01 |
| mixture | 100 | 5.7 | 1.00 | 0.00 | 0.00 |
| mixture | 150 | 7.0 | 1.00 | 0.00 | 0.00 |
| mixture | 200 | 8.1 | 1.00 | 0.00 | 0.00 |
| mixture | 300 | 9.7 | 1.00 | 0.00 | 0.00 |
| mixture | 400 | 11.2 | 1.00 | 0.00 | 0.00 |

## Heavy-budget refits of flagged folds

Single folds refitted with `--stage refine` (longer tuning, more chains, higher target acceptance); the fold difference is rescored on the same held-out questions. The default-budget column is the same fold scored from the flagged fits.

| Dataset | Fold | Model | Draws x chains (tune) | Dense mass | Minutes | Divergences | r-hat | ESS | Diagnostics | Fold ELPD diff (refit) | SE | Fold ELPD diff (default) |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| baseline_fit_q400_s1 | 0 | baseline | 1000 x 4 (2000) | True | 53 | 0 | 1.002 | 2226 | pass | -588.2 | 82.0 | -597.8 |
| baseline_fit_q400_s1 | 0 | ddm_sdv_lapse | 1000 x 4 (2000) | True | 107 | 0 | 1.546 | 7 | FLAG | -588.2 | 82.0 | -597.8 |
| sdv_fit_q400_s1 | 0 | baseline | 1000 x 4 (2000) | False | 4 | 0 | 1.011 | 446 | pass | 227.2 | 36.3 | 228.4 |
| sdv_fit_q400_s1 | 0 | ddm_sdv_lapse | 1000 x 4 (2000) | False | 60 | 0 | 1.046 | 67 | pass | 227.2 | 36.3 | 228.4 |

## Fit diagnostics

108 fits; 55 flagged. Flagged fits: sdv_fit q100 s1 fold0 baseline (div 0, r-hat 1.06, ESS 40); sdv_fit q100 s1 fold0 ddm_sdv_lapse (div 0, r-hat 1.05, ESS 50); sdv_fit q100 s1 fold2 ddm_sdv_lapse (div 0, r-hat 1.04, ESS 46); sdv_fit q100 s2 fold1 baseline (div 0, r-hat 1.09, ESS 32); sdv_fit q100 s2 fold2 baseline (div 0, r-hat 1.06, ESS 65); sdv_fit q100 s3 fold0 ddm_sdv_lapse (div 0, r-hat 1.08, ESS 27); sdv_fit q100 s3 fold1 ddm_sdv_lapse (div 0, r-hat 1.08, ESS 29); sdv_fit q100 s3 fold2 baseline (div 0, r-hat 1.07, ESS 56); sdv_fit q400 s1 fold0 ddm_sdv_lapse (div 0, r-hat 1.27, ESS 6); sdv_fit q400 s1 fold1 ddm_sdv_lapse (div 0, r-hat 1.24, ESS 7); sdv_fit q400 s1 fold2 baseline (div 0, r-hat 1.05, ESS 42); sdv_fit q400 s1 fold2 ddm_sdv_lapse (div 0, r-hat 1.12, ESS 12); sdv_fit q400 s2 fold0 ddm_sdv_lapse (div 0, r-hat 2.62, ESS 2); sdv_fit q400 s2 fold1 baseline (div 0, r-hat 1.03, ESS 49); sdv_fit q400 s2 fold1 ddm_sdv_lapse (div 0, r-hat 1.25, ESS 7); sdv_fit q400 s2 fold2 ddm_sdv_lapse (div 0, r-hat 1.15, ESS 11); sdv_fit q400 s3 fold0 ddm_sdv_lapse (div 0, r-hat 2.37, ESS 3); sdv_fit q400 s3 fold1 baseline (div 0, r-hat 1.06, ESS 36); sdv_fit q400 s3 fold1 ddm_sdv_lapse (div 0, r-hat 1.88, ESS 3); sdv_fit q400 s3 fold2 ddm_sdv_lapse (div 0, r-hat 1.10, ESS 15); baseline_fit q100 s1 fold0 ddm_sdv_lapse (div 0, r-hat 1.84, ESS 3); baseline_fit q100 s1 fold1 baseline (div 0, r-hat 1.06, ESS 50); baseline_fit q100 s1 fold1 ddm_sdv_lapse (div 0, r-hat 1.85, ESS 3); baseline_fit q100 s1 fold2 ddm_sdv_lapse (div 0, r-hat 1.07, ESS 24); baseline_fit q100 s2 fold0 baseline (div 0, r-hat 1.02, ESS 38); baseline_fit q100 s2 fold0 ddm_sdv_lapse (div 0, r-hat 2.13, ESS 3); baseline_fit q100 s2 fold1 baseline (div 0, r-hat 1.07, ESS 37); baseline_fit q100 s2 fold1 ddm_sdv_lapse (div 0, r-hat 1.26, ESS 6); baseline_fit q100 s2 fold2 baseline (div 0, r-hat 1.12, ESS 13); baseline_fit q100 s2 fold2 ddm_sdv_lapse (div 0, r-hat 1.14, ESS 13); baseline_fit q100 s3 fold0 ddm_sdv_lapse (div 0, r-hat 1.04, ESS 44); baseline_fit q100 s3 fold1 ddm_sdv_lapse (div 0, r-hat 1.09, ESS 17); baseline_fit q100 s3 fold2 ddm_sdv_lapse (div 0, r-hat 1.83, ESS 3); baseline_fit q400 s1 fold0 baseline (div 0, r-hat 1.30, ESS 6); baseline_fit q400 s1 fold0 ddm_sdv_lapse (div 0, r-hat 1.88, ESS 3); baseline_fit q400 s1 fold1 baseline (div 0, r-hat 1.09, ESS 15); baseline_fit q400 s1 fold1 ddm_sdv_lapse (div 213, r-hat 2.53, ESS 2); baseline_fit q400 s1 fold2 baseline (div 0, r-hat 1.28, ESS 6); baseline_fit q400 s1 fold2 ddm_sdv_lapse (div 0, r-hat 1.85, ESS 3); baseline_fit q400 s2 fold0 baseline (div 0, r-hat 1.11, ESS 13); baseline_fit q400 s2 fold0 ddm_sdv_lapse (div 0, r-hat 1.82, ESS 3); baseline_fit q400 s2 fold1 baseline (div 0, r-hat 1.20, ESS 8); baseline_fit q400 s2 fold1 ddm_sdv_lapse (div 0, r-hat 1.83, ESS 3); baseline_fit q400 s2 fold2 baseline (div 0, r-hat 1.24, ESS 7); baseline_fit q400 s2 fold2 ddm_sdv_lapse (div 0, r-hat 1.64, ESS 3); baseline_fit q400 s3 fold0 baseline (div 0, r-hat 1.12, ESS 14); baseline_fit q400 s3 fold0 ddm_sdv_lapse (div 0, r-hat 2.19, ESS 3); baseline_fit q400 s3 fold1 baseline (div 0, r-hat 1.32, ESS 7); baseline_fit q400 s3 fold1 ddm_sdv_lapse (div 0, r-hat 1.84, ESS 3); baseline_fit q400 s3 fold2 baseline (div 0, r-hat 1.25, ESS 6); baseline_fit q400 s3 fold2 ddm_sdv_lapse (div 0, r-hat 1.67, ESS 3); mixture q100 s1 fold0 ddm_sdv_lapse (div 0, r-hat 2.42, ESS 3); mixture q100 s2 fold0 ddm_sdv_lapse (div 0, r-hat 1.48, ESS 4); mixture q400 s1 fold0 ddm_sdv_lapse (div 0, r-hat 1.83, ESS 3); mixture q400 s3 fold0 ddm_sdv_lapse (div 0, r-hat 2.35, ESS 3).

Files: `power_results.csv` (all components), `power_summary.csv`, `power_curve_subsampled.csv`, `fit_diagnostics.csv`, `generator_calibration.csv`, `generator_parameters.json`, per-dataset `power_*_cv_per_trial.csv` and posteriors.
