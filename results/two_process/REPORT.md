# Third candidate on the R1 data: two-process mixture

Generated 2026-10-12 by `scripts/17_two_process.py`. Model `two_process` in `08_robustness.py`; grouped CV by question, question-level SEs, 2-SE rule, diagnostic flags (any divergence, r-hat > 1.05, bulk ESS < 50) as in the pre-registered pipeline. No API calls.

## Held-out comparisons

Joint ELPD differences on held-out questions (positive favours the first-named model). `main` = 400 step-1 runs at 8,192; `augmented` = main + 62 cap-experiment runs at 24,576 as further repeats of their cells, all three models refitted. `*_task` = the same data with the compute/recall task type (`scripts/18_task_type.py`) in place of the has_code covariate in all three models.

| Data | Component | Comparison | ELPD | SE | z | Verdict | max r-hat | min ESS |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| main | joint | two_process - baseline | 51.9 | 16.6 | 3.1 | unreliable fit; no verdict | 1.19 | 15 |
| main | length | two_process - baseline | 51.6 | 16.2 | 3.2 | unreliable fit; no verdict | 1.19 | 15 |
| main | correctness_given_length | two_process - baseline | 0.3 | 1.8 | 0.2 | unreliable fit; no verdict | 1.19 | 15 |
| main | joint | two_process - ddm_sdv_lapse | 29.9 | 33.1 | 0.9 | unreliable fit; no verdict | 1.19 | 15 |
| main | length | two_process - ddm_sdv_lapse | 28.3 | 30.2 | 0.9 | unreliable fit; no verdict | 1.19 | 15 |
| main | correctness_given_length | two_process - ddm_sdv_lapse | 1.5 | 9.8 | 0.2 | unreliable fit; no verdict | 1.19 | 15 |
| main | joint | ddm_sdv_lapse - baseline | 22.0 | 29.8 | 0.7 | inconclusive | 1.03 | 55 |
| main | length | ddm_sdv_lapse - baseline | 23.2 | 27.5 | 0.8 | inconclusive | 1.03 | 55 |
| main | correctness_given_length | ddm_sdv_lapse - baseline | -1.2 | 8.2 | -0.2 | inconclusive | 1.03 | 55 |
| augmented | joint | two_process - baseline | 87.1 | 30.0 | 2.9 | unreliable fit; no verdict | 1.28 | 11 |
| augmented | length | two_process - baseline | 88.3 | 29.4 | 3.0 | unreliable fit; no verdict | 1.28 | 11 |
| augmented | correctness_given_length | two_process - baseline | -1.3 | 2.8 | -0.5 | unreliable fit; no verdict | 1.28 | 11 |
| augmented | joint | two_process - ddm_sdv_lapse | 76.5 | 42.3 | 1.8 | unreliable fit; no verdict | 1.28 | 11 |
| augmented | length | two_process - ddm_sdv_lapse | 76.0 | 39.4 | 1.9 | unreliable fit; no verdict | 1.28 | 11 |
| augmented | correctness_given_length | two_process - ddm_sdv_lapse | 0.4 | 9.1 | 0.0 | unreliable fit; no verdict | 1.28 | 11 |
| augmented | joint | ddm_sdv_lapse - baseline | 10.6 | 24.3 | 0.4 | inconclusive | 1.03 | 249 |
| augmented | length | ddm_sdv_lapse - baseline | 12.3 | 20.7 | 0.6 | inconclusive | 1.03 | 249 |
| augmented | correctness_given_length | ddm_sdv_lapse - baseline | -1.7 | 10.1 | -0.2 | inconclusive | 1.03 | 249 |
| main_task | joint | two_process - baseline | -5.9 | 6.1 | -1.0 | unreliable fit; no verdict | 1.09 | 30 |
| main_task | length | two_process - baseline | -3.8 | 4.8 | -0.8 | unreliable fit; no verdict | 1.09 | 30 |
| main_task | correctness_given_length | two_process - baseline | -2.2 | 2.6 | -0.8 | unreliable fit; no verdict | 1.09 | 30 |
| main_task | joint | two_process - ddm_sdv_lapse | -5.2 | 18.5 | -0.3 | unreliable fit; no verdict | 1.09 | 30 |
| main_task | length | two_process - ddm_sdv_lapse | -2.6 | 17.1 | -0.2 | unreliable fit; no verdict | 1.09 | 30 |
| main_task | correctness_given_length | two_process - ddm_sdv_lapse | -2.5 | 4.3 | -0.6 | unreliable fit; no verdict | 1.09 | 30 |
| main_task | joint | ddm_sdv_lapse - baseline | -0.8 | 19.3 | -0.0 | inconclusive | 1.01 | 497 |
| main_task | length | ddm_sdv_lapse - baseline | -1.2 | 18.5 | -0.1 | inconclusive | 1.01 | 497 |
| main_task | correctness_given_length | ddm_sdv_lapse - baseline | 0.4 | 2.8 | 0.1 | inconclusive | 1.01 | 497 |
| augmented_task | joint | two_process - baseline | -7.3 | 12.2 | -0.6 | inconclusive | 1.03 | 87 |
| augmented_task | length | two_process - baseline | -1.8 | 11.4 | -0.2 | inconclusive | 1.03 | 87 |
| augmented_task | correctness_given_length | two_process - baseline | -5.5 | 2.7 | -2.0 | baseline better | 1.03 | 87 |
| augmented_task | joint | two_process - ddm_sdv_lapse | 11.2 | 24.3 | 0.5 | inconclusive | 1.03 | 87 |
| augmented_task | length | two_process - ddm_sdv_lapse | 20.0 | 22.7 | 0.9 | inconclusive | 1.03 | 87 |
| augmented_task | correctness_given_length | two_process - ddm_sdv_lapse | -8.8 | 6.1 | -1.4 | inconclusive | 1.03 | 87 |
| augmented_task | joint | ddm_sdv_lapse - baseline | -18.5 | 18.1 | -1.0 | inconclusive | 1.01 | 429 |
| augmented_task | length | ddm_sdv_lapse - baseline | -21.8 | 17.2 | -1.3 | inconclusive | 1.01 | 429 |
| augmented_task | correctness_given_length | ddm_sdv_lapse - baseline | 3.3 | 6.3 | 0.5 | inconclusive | 1.01 | 429 |
| main_within | joint | two_process - baseline | -4.3 | 3.2 | -1.4 | inconclusive | nan | nan |
| main_within | length | two_process - baseline | -4.6 | 3.1 | -1.5 | inconclusive | nan | nan |
| main_within | correctness_given_length | two_process - baseline | 0.3 | 0.6 | 0.4 | inconclusive | nan | nan |
| exclude_incomplete | joint | two_process - baseline | 40.0 | 21.8 | 1.8 | inconclusive | nan | nan |
| exclude_incomplete | length | two_process - baseline | 40.4 | 21.2 | 1.9 | inconclusive | nan | nan |
| exclude_incomplete | correctness_given_length | two_process - baseline | -0.4 | 2.4 | -0.2 | inconclusive | nan | nan |
| hidden_only | joint | two_process - baseline | 39.7 | 21.3 | 1.9 | inconclusive | nan | nan |
| hidden_only | length | two_process - baseline | 38.8 | 20.7 | 1.9 | inconclusive | nan | nan |
| hidden_only | correctness_given_length | two_process - baseline | 0.9 | 2.6 | 0.3 | inconclusive | nan | nan |
| deepinfra | joint | two_process - baseline | 11.1 | 8.5 | 1.3 | inconclusive | nan | nan |
| deepinfra | length | two_process - baseline | 9.1 | 8.2 | 1.1 | inconclusive | nan | nan |
| deepinfra | correctness_given_length | two_process - baseline | 2.1 | 1.9 | 1.1 | inconclusive | nan | nan |
| provider_adjusted | joint | two_process - baseline | 34.9 | 25.1 | 1.4 | inconclusive | nan | nan |
| provider_adjusted | length | two_process - baseline | 36.9 | 24.7 | 1.5 | inconclusive | nan | nan |
| provider_adjusted | correctness_given_length | two_process - baseline | -2.1 | 2.2 | -0.9 | inconclusive | nan | nan |

## Fitted two-process parameters (full-data fits)

### main

| Quantity | Mean | 95% interval |
| --- | ---: | --- |
| p_slow_floor_other_questions | 0.00386 | 0.000323 to 0.0129 |
| slow_median_tokens_cov0 | 1.21e+04 | 9.79e+03 to 1.77e+04 |
| slow_median_tokens_cov1 | 5.72e+03 | 3.9e+03 to 6.89e+03 |
| slow_sdlog | 0.288 | 0.204 to 0.412 |
| slow_accuracy_slope_per_log_unit | -1.61 | -3.89 to 0.186 |
| p_slope_negative | 0.958 | |
| tau_f | 0.812 | 0.508 to 1.44 |
| tau_bf | 2.17 | 1.28 to 3.39 |
| omega_covariate_log_odds | -0.535 | -2 to 0.928 |
| slow_accuracy_at_8000_tokens | 0.915 | 0.786 to 0.986 |
| slow_accuracy_at_12000_tokens | 0.852 | 0.617 to 0.972 |
| slow_accuracy_at_16000_tokens | 0.781 | 0.462 to 0.966 |
| slow_accuracy_at_20000_tokens | 0.713 | 0.335 to 0.964 |
| slow_accuracy_at_24000_tokens | 0.654 | 0.202 to 0.963 |

P(question is slow-prone), P(slow trial | slow-prone question) by condition, marginal P(slow trial); fast-mode median tokens and accuracy. Covariate column = code (0/1):

| Code | Condition | P(slow-prone question) | 95% | P(slow given prone) | 95% | P(slow) marginal | Fast median tokens | Fast accuracy |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
| 0 | plain_concise | 0.27 | 0.07-0.45 | 0.94 | 0.82-0.99 | 0.25 | 774 | 0.982 |
| 0 | plain_thorough | 0.27 | 0.07-0.45 | 0.96 | 0.84-1.00 | 0.26 | 1,020 | 0.983 |
| 0 | sbs_concise | 0.27 | 0.07-0.45 | 0.96 | 0.85-1.00 | 0.26 | 1,039 | 0.985 |
| 0 | sbs_thorough | 0.27 | 0.07-0.45 | 0.98 | 0.90-1.00 | 0.26 | 1,471 | 0.970 |
| 1 | plain_concise | 0.18 | 0.05-0.38 | 0.94 | 0.80-1.00 | 0.17 | 10,071 | 0.986 |
| 1 | plain_thorough | 0.18 | 0.05-0.38 | 0.96 | 0.84-1.00 | 0.18 | 13,272 | 0.987 |
| 1 | sbs_concise | 0.18 | 0.05-0.38 | 0.97 | 0.86-1.00 | 0.18 | 13,600 | 0.987 |
| 1 | sbs_thorough | 0.18 | 0.05-0.38 | 0.98 | 0.88-1.00 | 0.18 | 19,213 | 0.976 |

### augmented

| Quantity | Mean | 95% interval |
| --- | ---: | --- |
| p_slow_floor_other_questions | 0.00457 | 0.000353 to 0.0165 |
| slow_median_tokens_cov0 | 1.42e+04 | 1.25e+04 to 1.64e+04 |
| slow_median_tokens_cov1 | 1.88e+04 | 1.26e+04 to 2.96e+04 |
| slow_sdlog | 0.358 | 0.267 to 0.453 |
| slow_accuracy_slope_per_log_unit | -2.99 | -5.12 to -1.07 |
| p_slope_negative | 1 | |
| tau_f | 0.663 | 0.441 to 0.971 |
| tau_bf | 2.14 | 1.29 to 3.29 |
| omega_covariate_log_odds | 0.00837 | -2.08 to 1.45 |
| slow_accuracy_at_8000_tokens | 0.945 | 0.83 to 0.992 |
| slow_accuracy_at_12000_tokens | 0.862 | 0.737 to 0.948 |
| slow_accuracy_at_16000_tokens | 0.735 | 0.587 to 0.87 |
| slow_accuracy_at_20000_tokens | 0.592 | 0.379 to 0.793 |
| slow_accuracy_at_24000_tokens | 0.464 | 0.215 to 0.754 |

P(question is slow-prone), P(slow trial | slow-prone question) by condition, marginal P(slow trial); fast-mode median tokens and accuracy. Covariate column = code (0/1):

| Code | Condition | P(slow-prone question) | 95% | P(slow given prone) | 95% | P(slow) marginal | Fast median tokens | Fast accuracy |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
| 0 | plain_concise | 0.30 | 0.16-0.46 | 0.96 | 0.89-0.99 | 0.29 | 769 | 0.983 |
| 0 | plain_thorough | 0.30 | 0.16-0.46 | 0.98 | 0.93-1.00 | 0.29 | 994 | 0.983 |
| 0 | sbs_concise | 0.30 | 0.16-0.46 | 0.98 | 0.94-1.00 | 0.30 | 992 | 0.986 |
| 0 | sbs_thorough | 0.30 | 0.16-0.46 | 0.99 | 0.96-1.00 | 0.30 | 1,303 | 0.957 |
| 1 | plain_concise | 0.32 | 0.05-0.62 | 0.96 | 0.86-1.00 | 0.31 | 6,199 | 0.982 |
| 1 | plain_thorough | 0.32 | 0.05-0.62 | 0.98 | 0.91-1.00 | 0.32 | 8,035 | 0.982 |
| 1 | sbs_concise | 0.32 | 0.05-0.62 | 0.98 | 0.92-1.00 | 0.32 | 7,921 | 0.985 |
| 1 | sbs_thorough | 0.32 | 0.05-0.62 | 0.99 | 0.96-1.00 | 0.32 | 10,379 | 0.953 |

### main_task

| Quantity | Mean | 95% interval |
| --- | ---: | --- |
| p_slow_floor_other_questions | 0.00434 | 0.000321 to 0.015 |
| slow_median_tokens_cov0 | 5.06e+03 | 3.99e+03 to 9.43e+03 |
| slow_median_tokens_cov1 | 9.33e+03 | 2.81e+03 to 2.8e+04 |
| slow_sdlog | 0.282 | 0.171 to 0.432 |
| slow_accuracy_slope_per_log_unit | -1.26 | -2.97 to 0.448 |
| p_slope_negative | 0.912 | |
| tau_f | 0.636 | 0.378 to 0.897 |
| tau_bf | 2.16 | 1.25 to 3.42 |
| omega_covariate_log_odds | -0.319 | -2.69 to 2.36 |
| slow_accuracy_at_8000_tokens | 0.85 | 0.636 to 0.972 |
| slow_accuracy_at_12000_tokens | 0.778 | 0.491 to 0.956 |
| slow_accuracy_at_16000_tokens | 0.711 | 0.342 to 0.95 |
| slow_accuracy_at_20000_tokens | 0.653 | 0.249 to 0.944 |
| slow_accuracy_at_24000_tokens | 0.605 | 0.185 to 0.947 |

P(question is slow-prone), P(slow trial | slow-prone question) by condition, marginal P(slow trial); fast-mode median tokens and accuracy. Covariate column = compute task (0/1):

| Compute task | Condition | P(slow-prone question) | 95% | P(slow given prone) | 95% | P(slow) marginal | Fast median tokens | Fast accuracy |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
| 0 | plain_concise | 0.13 | 0.03-0.29 | 0.84 | 0.57-0.96 | 0.12 | 656 | 0.983 |
| 0 | plain_thorough | 0.13 | 0.03-0.29 | 0.89 | 0.61-0.99 | 0.12 | 864 | 0.983 |
| 0 | sbs_concise | 0.13 | 0.03-0.29 | 0.89 | 0.61-0.99 | 0.12 | 864 | 0.982 |
| 0 | sbs_thorough | 0.13 | 0.03-0.29 | 0.92 | 0.54-1.00 | 0.13 | 1,181 | 0.978 |
| 1 | plain_concise | 0.14 | 0.01-0.65 | 0.86 | 0.49-0.99 | 0.13 | 8,986 | 0.990 |
| 1 | plain_thorough | 0.14 | 0.01-0.65 | 0.90 | 0.47-1.00 | 0.14 | 11,774 | 0.990 |
| 1 | sbs_concise | 0.14 | 0.01-0.65 | 0.90 | 0.51-1.00 | 0.14 | 11,788 | 0.989 |
| 1 | sbs_thorough | 0.14 | 0.01-0.65 | 0.93 | 0.47-1.00 | 0.14 | 15,995 | 0.987 |

### augmented_task

| Quantity | Mean | 95% interval |
| --- | ---: | --- |
| p_slow_floor_other_questions | 0.005 | 0.000376 to 0.0159 |
| slow_median_tokens_cov0 | 5.23e+03 | 3.95e+03 to 1.63e+04 |
| slow_median_tokens_cov1 | 1.5e+04 | 1.33e+04 to 1.77e+04 |
| slow_sdlog | 0.273 | 0.204 to 0.368 |
| slow_accuracy_slope_per_log_unit | -1.67 | -3.53 to -0.23 |
| p_slope_negative | 0.99 | |
| tau_f | 0.629 | 0.476 to 0.833 |
| tau_bf | 2.18 | 1.31 to 3.24 |
| omega_covariate_log_odds | 1.25 | -0.299 to 2.61 |
| slow_accuracy_at_8000_tokens | 0.879 | 0.743 to 0.971 |
| slow_accuracy_at_12000_tokens | 0.799 | 0.646 to 0.91 |
| slow_accuracy_at_16000_tokens | 0.714 | 0.514 to 0.869 |
| slow_accuracy_at_20000_tokens | 0.633 | 0.384 to 0.839 |
| slow_accuracy_at_24000_tokens | 0.563 | 0.285 to 0.827 |

P(question is slow-prone), P(slow trial | slow-prone question) by condition, marginal P(slow trial); fast-mode median tokens and accuracy. Covariate column = compute task (0/1):

| Compute task | Condition | P(slow-prone question) | 95% | P(slow given prone) | 95% | P(slow) marginal | Fast median tokens | Fast accuracy |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
| 0 | plain_concise | 0.16 | 0.05-0.34 | 0.85 | 0.65-0.97 | 0.14 | 673 | 0.985 |
| 0 | plain_thorough | 0.16 | 0.05-0.34 | 0.90 | 0.68-0.99 | 0.15 | 866 | 0.979 |
| 0 | sbs_concise | 0.16 | 0.05-0.34 | 0.92 | 0.76-0.99 | 0.15 | 854 | 0.981 |
| 0 | sbs_thorough | 0.16 | 0.05-0.34 | 0.94 | 0.71-1.00 | 0.16 | 1,141 | 0.965 |
| 1 | plain_concise | 0.38 | 0.16-0.58 | 0.90 | 0.69-0.99 | 0.35 | 7,184 | 0.985 |
| 1 | plain_thorough | 0.38 | 0.16-0.58 | 0.94 | 0.76-1.00 | 0.36 | 9,346 | 0.979 |
| 1 | sbs_concise | 0.38 | 0.16-0.58 | 0.95 | 0.81-1.00 | 0.37 | 9,275 | 0.980 |
| 1 | sbs_thorough | 0.38 | 0.16-0.58 | 0.97 | 0.81-1.00 | 0.37 | 12,263 | 0.963 |

## Posterior predictive checks

Observed step 1 at 8,192: censored 0.43 (prose 0.26, code 0.64), answered accuracy 0.956, medians 887 / 4,895 tokens. Observed cap experiment (selected cells, 24,576): finished 0.81, accuracy 0.76, median finish 15,944; accuracy by length 0_12k: 1.00, 12_16k: 0.80, 16_20k: 0.67, 20_24k: 0.60. The simulated accuracy-by-length rows are for all 400 step-1 cells at a 24,576 cap, not the selected cells, so they are a population prediction rather than a like-for-like replication.

### main fit, simulated at cap 8,192

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.42 | 0.395 to 0.445 |
| censored_cov0 | 0.249 | 0.214 to 0.277 |
| censored_cov1 | 0.636 | 0.597 to 0.676 |
| acc_answered | 0.946 | 0.917 to 0.971 |
| median_cov0 | 919 | 833 to 1e+03 |
| median_cov1 | 4.81e+03 | 4.26e+03 to 5.33e+03 |
| p_slow_mean | 0.216 | 0.113 to 0.256 |
| share_slow_prone_questions | 0.221 | 0.12 to 0.26 |
| acc_0_12k | 0.946 | 0.917 to 0.971 |
| acc_12_16k | nan | nan to nan |
| acc_16_20k | nan | nan to nan |
| acc_20_24k | nan | nan to nan |

### main fit, simulated at cap 24,576

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.124 | 0.065 to 0.195 |
| censored_cov0 | 0.00904 | 0 to 0.0449 |
| censored_cov1 | 0.271 | 0.142 to 0.398 |
| acc_answered | 0.93 | 0.888 to 0.968 |
| median_cov0 | 1.22e+03 | 1.11e+03 to 1.34e+03 |
| median_cov1 | 8.2e+03 | 6.57e+03 to 9.88e+03 |
| p_slow_mean | 0.216 | 0.113 to 0.256 |
| share_slow_prone_questions | 0.221 | 0.12 to 0.26 |
| acc_0_12k | 0.941 | 0.908 to 0.972 |
| acc_12_16k | 0.891 | 0.741 to 1 |
| acc_16_20k | 0.887 | 0.727 to 1 |
| acc_20_24k | 0.899 | 0.727 to 1 |

### augmented fit, simulated at cap 8,192

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.431 | 0.41 to 0.453 |
| censored_cov0 | 0.265 | 0.241 to 0.286 |
| censored_cov1 | 0.642 | 0.602 to 0.682 |
| acc_answered | 0.941 | 0.909 to 0.969 |
| median_cov0 | 908 | 830 to 992 |
| median_cov1 | 4.64e+03 | 4.1e+03 to 5.26e+03 |
| p_slow_mean | 0.292 | 0.196 to 0.394 |
| share_slow_prone_questions | 0.295 | 0.2 to 0.4 |
| acc_0_12k | 0.941 | 0.909 to 0.969 |
| acc_12_16k | nan | nan to nan |
| acc_16_20k | nan | nan to nan |
| acc_20_24k | nan | nan to nan |

### augmented fit, simulated at cap 24,576

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.0757 | 0.0499 to 0.103 |
| censored_cov0 | 0.0196 | 0 to 0.0491 |
| censored_cov1 | 0.147 | 0.0963 to 0.199 |
| acc_answered | 0.888 | 0.847 to 0.924 |
| median_cov0 | 1.2e+03 | 1.08e+03 to 1.32e+03 |
| median_cov1 | 1e+04 | 8.79e+03 to 1.14e+04 |
| p_slow_mean | 0.292 | 0.196 to 0.394 |
| share_slow_prone_questions | 0.295 | 0.2 to 0.4 |
| acc_0_12k | 0.938 | 0.906 to 0.963 |
| acc_12_16k | 0.84 | 0.735 to 0.936 |
| acc_16_20k | 0.735 | 0.542 to 0.9 |
| acc_20_24k | 0.628 | 0.392 to 0.822 |

### main_task fit, simulated at cap 8,192

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.422 | 0.403 to 0.443 |
| censored_cov0 | 0.00325 | 0 to 0.0128 |
| censored_cov1 | 0.701 | 0.667 to 0.738 |
| acc_answered | 0.945 | 0.918 to 0.97 |
| median_cov0 | 880 | 805 to 957 |
| median_cov1 | 4.75e+03 | 4.18e+03 to 5.29e+03 |
| p_slow_mean | 0.123 | 0.0333 to 0.391 |
| share_slow_prone_questions | 0.129 | 0.04 to 0.4 |
| acc_0_12k | 0.945 | 0.918 to 0.97 |
| acc_12_16k | nan | nan to nan |
| acc_16_20k | nan | nan to nan |
| acc_20_24k | nan | nan to nan |

### main_task fit, simulated at cap 24,576

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.115 | 0.015 to 0.195 |
| censored_cov0 | 3.13e-05 | 0 to 0 |
| censored_cov1 | 0.192 | 0.025 to 0.321 |
| acc_answered | 0.933 | 0.847 to 0.971 |
| median_cov0 | 883 | 805 to 961 |
| median_cov1 | 1.07e+04 | 9.34e+03 to 1.23e+04 |
| p_slow_mean | 0.123 | 0.0333 to 0.391 |
| share_slow_prone_questions | 0.129 | 0.04 to 0.4 |
| acc_0_12k | 0.944 | 0.909 to 0.971 |
| acc_12_16k | 0.912 | 0.714 to 1 |
| acc_16_20k | 0.908 | 0.681 to 1 |
| acc_20_24k | 0.892 | 0.539 to 1 |

### augmented_task fit, simulated at cap 8,192

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.433 | 0.412 to 0.45 |
| censored_cov0 | 0.00219 | 0 to 0.0125 |
| censored_cov1 | 0.72 | 0.688 to 0.75 |
| acc_answered | 0.943 | 0.92 to 0.966 |
| median_cov0 | 883 | 808 to 961 |
| median_cov1 | 4.55e+03 | 4.07e+03 to 5.1e+03 |
| p_slow_mean | 0.26 | 0.159 to 0.35 |
| share_slow_prone_questions | 0.273 | 0.16 to 0.36 |
| acc_0_12k | 0.943 | 0.92 to 0.966 |
| acc_12_16k | nan | nan to nan |
| acc_16_20k | nan | nan to nan |
| acc_20_24k | nan | nan to nan |

### augmented_task fit, simulated at cap 24,576

| Quantity | Mean | 90% interval |
| --- | ---: | --- |
| censored | 0.0652 | 0.0475 to 0.085 |
| censored_cov0 | 6.25e-05 | 0 to 0 |
| censored_cov1 | 0.109 | 0.0792 to 0.142 |
| acc_answered | 0.891 | 0.855 to 0.929 |
| median_cov0 | 884 | 808 to 961 |
| median_cov1 | 1.2e+04 | 1.11e+04 to 1.29e+04 |
| p_slow_mean | 0.26 | 0.159 to 0.35 |
| share_slow_prone_questions | 0.273 | 0.16 to 0.36 |
| acc_0_12k | 0.936 | 0.911 to 0.96 |
| acc_12_16k | 0.816 | 0.698 to 0.911 |
| acc_16_20k | 0.757 | 0.605 to 0.896 |
| acc_20_24k | 0.724 | 0.533 to 0.917 |

## Diagnostics

Flagged fits among two_process and augmented fits: augmented_fold4_two_process (div 0, r-hat 1.28, ESS 11); main_fold3_two_process (div 0, r-hat 1.05, ESS 82); deepinfra_fold0_two_process (div 0, r-hat 1.08, ESS 39); main_task_fold1_two_process (div 0, r-hat 1.09, ESS 30); main_fold1_two_process (div 0, r-hat 1.08, ESS 40); deepinfra_fold2_two_process (div 0, r-hat 1.16, ESS 16); exclude_incomplete_fold2_two_process (div 0, r-hat 1.53, ESS 7); main_task_fold3_two_process (div 0, r-hat 1.06, ESS 45); deepinfra_fold1_two_process (div 1, r-hat 1.01, ESS 332); main_fold2_two_process (div 0, r-hat 1.19, ESS 15); hidden_only_fold2_two_process (div 0, r-hat 1.38, ESS 9); main_fold4_two_process (div 0, r-hat 1.05, ESS 58); main_within_two_process (div 4, r-hat 1.04, ESS 80).

Files: `comparisons.csv`, `main_three_way_per_trial.csv`, `augmented_three_way_per_trial.csv`, `parameters.json`, `*_p_slow_by_condition.csv`, `*_ppc_cap*.csv`, `observed.json`; posteriors and per-fold scores under `results/robustness`.
