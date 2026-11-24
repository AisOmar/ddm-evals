# Within-trace models on the R1 reasoning traces

Generated 2026-10-12 by `scripts/21_within_trace_model.py` from `scripts/20_trace_segments.py`. 462 runs (400 step-1 at 8,192 tokens, 62 cap-experiment at 24,576), hidden reasoning split into paragraph segments and labelled by text rules. All models have question random effects; sampler 4 chains, NUTS via numpyro, checkpoints under `results/within_trace/posteriors`. No API calls.

## Segmentation and labelling

Segments carry token counts, event flags (backtrack: segment opens with But/However/No,/Actually or states a mistake; reconsider: opens with Perhaps/Maybe/Alternatively/Another idea; check: verify/double-check/make sure; stuck: not sure/can't determine/guess/unclear) and a leaning (A/B/none from explicit answer phrases, option letters and option text). Validation: among answered runs with any leaning, the final leaning matches the emitted answer in 0.866 of runs (by correctness column below).

## Descriptives, answered runs

| Quantity | wrong (n=22) | correct (n=275) |
| --- | ---: | ---: |
| hidden_tokens | 11,127.95 | 4,481.03 |
| n_segments | 273.14 | 116.24 |
| n_flips | 4.64 | 4.43 |
| n_backtrack | 28.59 | 13.01 |
| n_reconsider | 48.18 | 13.95 |
| n_check | 3.95 | 2.71 |
| n_stuck | 4.09 | 0.83 |
| commit_frac | 0.79 | 0.77 |
| correct_value_mentioned | 0.86 | 0.92 |
| final_leaning_matches_answer | 0.77 | 0.96 |
| stuck_per_k | 0.76 | 0.26 |
| back_per_k | 3.34 | 2.43 |

- First stated leaning correct, then final answer correct: 0.93; first leaning wrong, then correct: 0.92. The first leaning carries almost no information about the outcome.
- Wrong answers whose trace mentions the correct option's text: 0.86.
- Unanswered runs (censored or incomplete, n=165): a leaning is present at the end in 0.52, and that leaning is correct in 0.46: chance level. Runs that hit the cap had not decided.

By task type (answered runs): 

| Task | n | accuracy | median hidden tokens | stuck per run | flips per run |
| --- | ---: | ---: | ---: | ---: | ---: |
| compute | 137 | 0.905 | 7,326 | 1.77 | 4.58 |
| recall | 160 | 0.944 | 711 | 0.47 | 4.32 |

## Model 1: stopping hazard (10,586 blocks of >= 250 tokens)

Log-odds that the run answers in this block, given it has not yet. Positive = more likely to stop. Covariates are the block's own events; `log_ktokens` is log cumulative tokens in thousands.

| Term | Mean | 95% interval | Odds ratio | P(>0) |
| --- | ---: | --- | ---: | ---: |
| intercept | -3.29 | -4.33 to -2.33 | 0.04 | 0.00 |
| log_ktokens | 1.14 | 0.76 to 1.54 | 3.13 | 1.00 |
| compute | -4.39 | -5.67 to -3.19 | 0.01 | 0.00 |
| scaffold | -0.61 | -0.91 to -0.30 | 0.55 | 0.00 |
| thorough | -0.36 | -0.66 to -0.05 | 0.70 | 0.01 |
| backtrack | -0.67 | -1.00 to -0.35 | 0.51 | 0.00 |
| reconsider | -0.39 | -0.79 to -0.01 | 0.67 | 0.02 |
| check | -0.65 | -1.06 to -0.25 | 0.52 | 0.00 |
| stuck | -1.13 | -1.85 to -0.48 | 0.32 | 0.00 |
| has_leaning | 3.12 | 2.63 to 3.64 | 22.76 | 1.00 |
| flip_in_block | -0.89 | -1.24 to -0.53 | 0.41 | 0.00 |
| log1p_flips_so_far | 1.53 | 1.25 to 1.81 | 4.62 | 1.00 |

Question-effect SD 1.87. Observed against predicted hazard (population level, no question effect) by cumulative-token bin:

| Tokens (k) | Blocks | Stops | Observed hazard | Predicted | Stuck rate | Backtrack rate | Leaning rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| (0, 2] | 2,482 | 142 | 0.057 | 0.049 | 0.044 | 0.351 | 0.266 |
| (2, 4] | 2,078 | 40 | 0.019 | 0.038 | 0.033 | 0.489 | 0.197 |
| (4, 8] | 3,374 | 48 | 0.014 | 0.026 | 0.035 | 0.493 | 0.152 |
| (8, 12] | 1,264 | 25 | 0.020 | 0.038 | 0.037 | 0.487 | 0.191 |
| (12, 16] | 706 | 17 | 0.024 | 0.067 | 0.084 | 0.449 | 0.232 |
| (16, 24] | 654 | 25 | 0.038 | 0.144 | 0.063 | 0.411 | 0.344 |
| (24, 33] | 28 | 0 | 0.000 | 0.273 | 0.036 | 0.214 | 0.357 |

Calibration by predicted-probability decile: 0.000/0.000, 0.000/0.000, 0.001/0.000, 0.001/0.003, 0.001/0.003, 0.002/0.002, 0.004/0.002, 0.010/0.013, 0.042/0.053, 0.397/0.205 (predicted/observed).

## Model 2: flips between stated leanings (1,840 blocks with a leaning after an earlier one)

| Term | Mean | 95% interval | Odds ratio | P(>0) |
| --- | ---: | --- | ---: | ---: |
| intercept | -1.34 | -1.87 to -0.80 | 0.26 | 0.00 |
| log_ktokens | -0.10 | -0.32 to 0.14 | 0.91 | 0.21 |
| compute | 0.01 | -0.69 to 0.75 | 1.01 | 0.50 |
| scaffold | 0.09 | -0.12 to 0.30 | 1.09 | 0.79 |
| thorough | 0.04 | -0.17 to 0.26 | 1.04 | 0.65 |
| backtrack | 0.21 | -0.01 to 0.44 | 1.24 | 0.97 |
| reconsider | 0.21 | -0.06 to 0.48 | 1.23 | 0.94 |
| check | 0.07 | -0.21 to 0.34 | 1.08 | 0.69 |
| stuck | 0.41 | -0.02 to 0.83 | 1.51 | 0.97 |
| log1p_flips_so_far | 0.31 | 0.14 to 0.48 | 1.36 | 1.00 |

Question-effect SD 0.77.

## Model 3: trace monitor, held-out questions (grouped 5-fold CV)

P(correct) for answered runs from features available before grading. `length`: log tokens, task type, condition. `trace`: plus stuck/backtrack/reconsider/check rates per 1k tokens, flips, commitment position, leaning rate, and whether the final leaning matches the emitted answer. `prefix`: only what is visible in the first 4,000 tokens (plus whether the run was still going at 4,000).

| Monitor | n | errors | Held-out log score | per run | Brier | AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| length | 297 | 22 | -76.1 | -0.256 | 0.065 | 0.697 |
| trace | 297 | 22 | -57.6 | -0.194 | 0.057 | 0.873 |
| prefix | 297 | 22 | -91.5 | -0.308 | 0.076 | 0.503 |
| constant (prevalence) | 297 | 22 | -78.4 | -0.264 | 0.069 | 0.500 |

Log-score differences with question-level SE: trace - length = +18.5 ± 14.6; prefix - length = -15.4 ± 3.5; trace - prefix = +34.0 ± 16.1.

Files: `blocks.csv`, `hazard_table.csv`, `hazard_by_tokens.csv`, `flip_table.csv`, `monitor_results.csv`, `monitor_per_run.csv`, `descriptives.csv`, `extra.json`.

## Reading

- **The stopping rule, seen from inside.** R1 answers when it has just stated an answer (odds 23 to 1) and nothing in the block casts doubt on it: an objection, a check or a reconsideration roughly halves the odds of stopping and a stuck phrase cuts them by two thirds. The step-by-step scaffold and the thorough instruction lower the stopping odds by about 45% and 30% at every point, which is how they lengthen runs. Compute questions have a stopping hazard about eighty times lower than recall questions at the same length and state. The question-effect SD of 1.9 on the logit scale, and the over-prediction of stopping beyond 12,000 tokens by the population-level model, say that the long runs are not a universal rising-then-falling hazard but specific questions with persistently low hazard: the two-class structure of the two-process model, observed directly.
- **Changing a stated leaning** is rare (about one leaning block in five), more likely after a stuck phrase or an objection, self-exciting (a run that has flipped keeps flipping), and independent of length, task type and condition.
- **A monitor must read to the end.** Full-trace features reach a held-out AUC of 0.87 against 0.70 for length, task type and condition alone; flagging the 20% of answered runs with the lowest predicted probability of being correct catches 17 of the 22 errors, against 12 for the length-based monitor. The gain in held-out log score, +18.5 ± 14.6, does not reach the pipeline's 2-SE rule with only 22 errors. What carries it: the rate of stuck phrases per thousand tokens, whether the final stated leaning matches the emitted answer, length, and how often the run states a leaning at all. The first 4,000 tokens carry nothing: the prefix monitor has an AUC of 0.50 and a worse log score than a constant. Together with the uninformative first leaning, this means the trace tells you how a run ended, not how it will end.
- **Caveats.** 22 errors among 297 answered runs; the text rules were tuned on these traces (R1-0528's idiom: "But", "Perhaps", not "Wait"); the monitor's features were chosen after the descriptive table, so this is exploratory, with grouped CV guarding against question leakage but not against rule design. A pre-registered version would fix the rules and feature set before a new collection.
