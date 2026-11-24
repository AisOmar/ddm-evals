# Pre-registration: task-type-stratified follow-up on DeepSeek-R1-0528

Draft 2026-10-12 (revised the same day: the within-question slope is the primary outcome; the three-model comparison is secondary), written before any data collection. Supersedes the 400-question × four-condition × two-repeat design in `docs/FINAL_REPORT.md`, which the design power check (2026-10-09) and the third-candidate analysis (2026-10-12) showed to be the wrong experiment: its most likely outcome, a drift-variability DDM win on the length component, is produced equally by a two-process alternative, and once questions are labelled by task type the three candidate models are indistinguishable on the pilot data. Nothing in this document has been run against new model calls. The design check that sizes it is `scripts/19_stratified_power.py`, `results/stratified/REPORT.md`.

## 1. Question

**Primary.** On compute questions (packet-field decodes, function return values and arguments, register traces, program outputs, hex decodes), does DeepSeek-R1-0528 become less reliable the longer it reasons on the same question? The quantity is the within-question slope of correctness on log reasoning length: holding the question fixed, the change in log-odds of a correct answer per doubling of reasoning length. The pilot cap experiment suggests it is negative (accuracy 100% below 12k tokens, 60% past 20k, on selected cells), but every question-adjusted interval at 50 questions includes zero. This is a within-question quantity by construction: it is not the across-model or across-budget relation, where more tokens buy accuracy, and the question random effect removes the across-question relation, where hard questions are both long and missed. This matters for safety because a reasoning model's trace length is observable before its answer is checked: if the slope is negative and large, a long trace on a compute question is a usable flag for an unreliable answer, and because task type is readable from the prompt, the flag can be anticipated before generation. The flag is relative to the model's own length distribution on the task type; the 12,000-token threshold below is R1's and would be re-estimated for any other model.

**Secondary.** Whether a two-process description (fast mode with length-independent accuracy, slow mode with declining accuracy), a single lognormal-logistic description, or a drift-variability diffusion description forecasts the compute stratum best when all three are given the task type, and whether the step-by-step scaffold changes the probability of entering the slow mode across concise and thorough instructions.

What this is not. It is not a test of whether language models accumulate evidence. All three candidates are statistical descriptions of token counts and answers; the design check shows that their comparison is decided by the length distribution rather than by correctness, so a model win would establish a better forecast, not a mechanism (see FINAL_REPORT, "Design power check" and "Third candidate").

## 2. Why task type, and why the compute stratum

In the pilot, censoring at 8,192 tokens was all-or-nothing by question and followed task type, not the presence of code: 0% of recall runs and 71% of compute runs were censored, and every always-censored prose question was a packet-byte decode (`scripts/18_task_type.py`, `data/processed/task_type.csv`; 1,031 compute and 869 recall questions in the two-choice WMDP-cyber set). With the task label as a covariate in all three models, every held-out comparison on the pilot was a tie with threefold smaller SEs than with the code flag. Long traces and errors are a compute-stratum phenomenon: the fitted two-process model puts 38% of compute questions and 16% of recall questions in the slow-prone class, and recall runs have a median near 900 tokens with essentially no censoring. The compute stratum is therefore the population of interest; a small recall stratum is kept as a cheap contrast and to identify the task-type coefficients.

## 3. Design

- **Model and provider.** `deepseek/deepseek-r1-0528` through OpenRouter, pinned to DeepInfra with fallbacks disabled (the only upstream that enforced the cap with zero errors in the pilot). Record the provider's stated precision (fp4 at the time of writing) and price in the run log. Temperature 0.7 as in the pilot.
- **Cap.** 32,768 output tokens, enforced by the provider. At this cap the fitted models predict 4% (two-process), 8% (baseline) and 14% (DDM) censoring on compute runs. Censored runs enter every likelihood as P(T > C); they are not dropped.
- **Questions.** N_c compute and N_r recall questions drawn at random from the two-choice WMDP-cyber set, excluding the 50 pilot questions. The compute draw is stratified in proportion to the six text rules (packet_field, function_return, function_args, hex_decode, program_output, register_trace). The option audit and within-question option-order balancing of `scripts/01_make_two_choice.py` apply. Sizes are fixed in section 6 from the design check.
- **Conditions and repeats.** The pilot's 2×2 (plain vs step-by-step scaffold; concise vs thorough instruction), two repeats per question × condition, option order counterbalanced so that in each repeat two conditions have the correct option as A and two as B, reversing on the second repeat (`scripts/design.py`).
- **Measurement.** Reasoning length = tokenizer count (DeepSeek-R1-0528 tokenizer) of the hidden reasoning channel plus visible text before the final answer line, as in `scripts/03_parse_logs.py`. OpenRouter's reported reasoning-token count is recorded as a cross-check only. Time unit for the DDM = 100 tokens. Outcome categories: answered, censored (provider stop at the cap), incomplete (provider error or empty turn; enters as censored at its own length), zero-token (one-line answer with no hidden reasoning), refusal. Zero-token and refusal rows are excluded from the three-model comparison and reported as counts by condition and stratum.
- **No interim looks.** The collection runs once at the sizes in section 6. Fits run only after the collection is complete and parsed.

## 4. Candidate models

Exactly the three models in `scripts/08_robustness.py`, with the compute/recall label as the covariate (the `_task` convention) and no other changes:

- `baseline`: lognormal length by condition with the task label and a question effect, censored at the cap; logistic correctness given log length with its own question effect and one slope.
- `ddm_sdv_lapse`: symmetric diffusion with drift depending on scaffold, instruction, their interaction, the task label and a question effect; boundary and non-decision time on the same fixed effects; across-trial drift variability; a 2.5%-prior contaminant with lognormal length and a fair answer; closed-form survival at the cap.
- `two_process`: each question is slow-prone or not (probability by task label); on a slow-prone question a trial enters the slow mode with a condition-dependent probability, elsewhere with a floor; fast mode = lognormal length by condition with a question effect and length-independent accuracy; slow mode = long lognormal length with accuracy declining in log length. Priors as in the file on 2026-10-12.

Sampler budgets are fixed in advance: baseline and two-process 4 chains × 2,000 draws after 2,000 tuning steps, target acceptance 0.99; DDM 4 chains × 1,000 draws after 1,000 tuning steps, target acceptance 0.95, with the dense-mass refit of `scripts/11_refine_fits.py` allowed once per flagged fold. A fit is flagged by any divergence, maximum r-hat above 1.05, or minimum bulk ESS below 50 over sampled parameters (the deterministic per-question class probabilities excluded). A comparison with any flagged fold reads "unreliable fit; no verdict" and is reported with its score verdict beside it.

Refit rule, fixed in advance: a fold whose fit fails the convergence rule is refit once with doubled draws and tuning steps and the same seed offset; if it still fails, the comparison involving it is reported as 'unreliable fit; no verdict'. Held-out scores are reported in both cases.

## 5. Pre-specified analyses

**Primary: the within-question slope on compute questions.** The logistic model of `accuracy_fit` in `08_robustness.py`, fitted to finished compute runs: log-odds of a correct answer on the within-question deviation of log2 reasoning length (the primary coefficient), the between-question mean of log2 length, condition terms, correct-option position, and a question random effect. Censored runs have no answer and are excluded from this model; their count by condition is reported beside it, and a sensitivity fit counts them as wrong at the cap. Decision rule, fixed in advance:

- **Negative slope established** if the 95% interval of the primary coefficient lies entirely below zero. The point estimate is reported as the odds ratio per doubling of length and translated into accuracy at 8k, 12k, 16k, 24k and 32k tokens for a median compute question.
- **No decline of practical size** if the interval lies entirely above −0.3 log-odds per doubling (an odds ratio above 0.74 per doubling, which is less than a 10-point accuracy drop from 8k to 32k tokens at 85% baseline accuracy). This region is declared now.
- **Inconclusive** otherwise.

In the design check, datasets simulated from the fitted two-process model gave slopes of −0.76 to −1.04 per doubling, with 95% intervals of half-width about 0.4 at 200 compute questions; datasets from the fitted baseline gave −0.95 to −1.61. No simulated generator has a true slope near zero (section 6), so the design is sized to establish a decline, not to certify its absence.

**Secondary, in this order.**
1. The pre-registered prediction table (section 7) scored against the observed compute-stratum values: share of finished runs beyond 12,000 tokens, accuracy up to and beyond 12,000 tokens, accuracy in 12–16k, 16–20k, 20–25k and 25–33k, censoring at the cap. Observed values carry a question cluster-bootstrap SE. A model whose 90% predictive interval excludes the observed value is reported as miscalibrated on that quantity.
2. Three-model comparison. Five-fold cross-validation grouped by question, same folds for all models, held-out questions scored with population-marginal question effects; the statistic is the summed held-out log predictive density difference over **compute-stratum trials only** for each pair of models, with the question-level standard error (sample variance of per-question sums, Q−1 denominator); beyond two SEs is a win, otherwise inconclusive; joint first, then the length and correctness-given-length components; then all trials and the recall stratum. Three admissible outcomes per pair; all are reported. The design check shows that these comparisons are decided by the length component, so a win is reported as a forecasting result only.
3. Scaffold effect on the slow-mode probability: the `two_process` coefficient of scaffold on the slow-trial logit, and its interaction with instruction, with 95% intervals. A practical-equivalence region of ±0.2 on the logit scale is declared in advance; "no scaffold effect" is claimed only if the interval lies inside it.
4. The same slope on the recall stratum (expected near zero, few long runs) and on all questions with task type as a covariate.
5. Within-question held-out repeats (even repeats train, odd repeats test) as in the pilot, reported for completeness.

**Not pre-registered and reported as exploratory if done:** any analysis that drops rows after seeing scores, any model not listed in section 4, any threshold other than 12,000 tokens.

## 6. Sample size

Sizes are set from `results/stratified/REPORT.md`, which simulates the design from the task-type fits on the pilot data (generators: fitted two-process, two-process with a weak slow-mode slope, two-process with no slow-mode slope, fitted baseline) and fits the baseline and two-process candidates with the pipeline above in grouped three-fold CV. The size rule written before the check was: the smallest compute stratum at which the primary slope interval excludes zero in every dataset simulated from the fitted two-process model and lies above −0.3 in every no-decline dataset. The second clause could not be evaluated, because the generators built as no-decline controls turned out to carry a within-question decline through mode mixing alone (below). The size was therefore set by the first clause, the interval width and the budget.

<!-- SIZE_START -->
**Decision: 200 compute + 50 recall questions, 2,000 calls, about 22 million output tokens, $48 at DeepInfra's $2.15 per million output tokens ($55 at $2.50; cost cap $72).**

What the design check found (`results/stratified/REPORT.md`, 12 simulated datasets, 72 fits, 2026-10-12):

- At 200 compute questions the 95% interval of the primary slope has a half-width of about 0.4 log-odds per doubling (about 0.5 at 100).
- Datasets simulated from the fitted two-process model gave slopes of −0.78 (−1.18 to −0.39) and −0.93 (−1.32 to −0.54) at 200 questions and −0.76 (−1.25 to −0.28) and −1.04 (−1.57 to −0.54) at 100: established in 4 of 4. Datasets from the fitted baseline gave −0.95 to −1.61: established in 4 of 4.
- The two generators intended as no-decline controls are not no-decline. They switch off the length slope inside the slow mode only; the mixture of a fast mode (about 98% correct) and a slow mode (about 72% correct) on the same question still produces a within-question decline. A fixed-effects logistic fit on 4,000 simulated compute questions puts the true slope near −0.35 to −0.41 per doubling for all three two-process generators and near −1.1 to −1.6 for the baseline generator (`truth_slope.json`; approximate, the fixed-effects and hierarchical estimators weight questions differently). On the two control generators the 200-question estimates were −0.05 (−0.43 to 0.33), −0.24 (−0.63 to 0.14), −0.48 (−0.84 to −0.12) and −0.61 (−0.99 to −0.24): two established, two inconclusive, none 'no decline of practical size'.
- Estimates from the same generator differ by up to 0.4 between seeds, more than the posterior width alone implies, because the realized slope depends on how many of the drawn compute questions show both a short and a long run (128 to 131 of 200).
- Consequence: at this size the experiment can establish a decline but cannot certify its absence. The 'no decline of practical size' verdict requires the interval to lie above −0.3, which at half-width 0.4 needs a point estimate above +0.1. Halving the half-width would take about 800 compute questions (about $190), outside the budget. A null result is therefore reported as inconclusive, not as evidence that long traces are safe. Because no fitted generator has a true slope near zero, the false-positive rate of the 'established' verdict under a true null was not measured.
- Secondary comparison on the compute stratum: when the two-process model generates the data it beats the baseline by 3 to 5 SE joint, carried by length (correctness given length within 2 SE in 5 of 8 datasets and 2.6 to 3.0 SE in 3); when the baseline generates, the baseline wins correctness given length by 3.0 to 4.6 SE with length within 2.3 SE either way. 5 of 72 fits fail the convergence rule (all two-process fits, r-hat about 1.5, bulk ESS about 7), which voids the verdict in 5 of 12 datasets under the all-folds rule; the refit step in section 4 applies before any verdict is read.
<!-- SIZE_END -->

## 7. Pre-registered predictions for the compute stratum at 32,768 tokens

Posterior-predictive means and 90% intervals from the task-type fits on the pilot data (two-process: full augmented fit; baseline and DDM: the five fold posteriors pooled), new questions, 60 population draws each (`results/stratified/model_predictions.csv`).

| Quantity | two_process | baseline | ddm_sdv_lapse |
| --- | ---: | ---: | ---: |
| Censored at 32,768 | 0.04 (0.01 to 0.07) | 0.08 (0.03 to 0.13) | 0.14 (0.10 to 0.18) |
| Finished runs beyond 12,000 tokens | 0.49 (0.38 to 0.60) | 0.39 (0.31 to 0.48) | 0.25 (0.18 to 0.30) |
| Accuracy up to 12,000 tokens | 0.91 (0.85 to 0.96) | 0.90 (0.81 to 0.95) | 0.89 (0.81 to 0.96) |
| Accuracy beyond 12,000 tokens | 0.79 (0.69 to 0.89) | 0.70 (0.52 to 0.86) | 0.71 (0.62 to 0.83) |
| Accuracy 12 to 16k | 0.82 (0.73 to 0.91) | 0.78 (0.66 to 0.89) | 0.76 (0.64 to 0.89) |
| Accuracy 16 to 20k | 0.77 (0.64 to 0.90) | 0.72 (0.55 to 0.87) | 0.71 (0.59 to 0.84) |
| Accuracy 20 to 25k | 0.77 (0.62 to 0.91) | 0.66 (0.43 to 0.85) | 0.67 (0.59 to 0.78) |
| Accuracy 25 to 33k | 0.80 (0.56 to 0.93) | 0.57 (0.33 to 0.82) | 0.65 (0.55 to 0.76) |
| Median finished length, tokens | 12,100 (9,800 to 13,800) | 10,600 (8,900 to 12,800) | 8,000 (6,400 to 9,300) |

Reading, written before the data: the three descriptions agree on accuracy below 12k and overlap on accuracy beyond 12k, so **accuracy beyond 12k on its own will not pick a model**, which is why the model comparison is secondary. They separate on the length side (the DDM predicts half as many long runs and twice the censoring of the two-process model) and on the shape of the far tail (the baseline predicts a monotone decline to about 0.57 at 25–33k; the two-process model predicts a floor near 0.8 because its fast mode also produces long compute runs that stay accurate; the DDM is in between). The table is the calibration check for the secondary comparison: it says which model, if any, is describing the stratum it won on.

## 8. Outcomes and what each would mean

Primary:

- **Negative slope established.** On compute questions, the same question answered after a longer trace is more often answered wrongly. Trace length is a usable unreliability flag on this task type, and the task type is readable from the prompt. The size of the slope sets how useful: the pilot prediction of −0.8 per doubling means roughly 90% accuracy at 8k tokens falling to about 65% at 32k on a median compute question.
- **No decline of practical size.** Long traces on compute questions are slow but not less reliable; the pilot's accuracy-by-length pattern was selection (hard questions are long) rather than a within-question effect. Length is then a cost signal, not a reliability signal.
- **Inconclusive.** Reported with the interval; no further collection is implied by this document.

Secondary:

- **two_process wins the compute-stratum joint comparison and is calibrated on the table.** Errors on compute questions concentrate in an identifiable slow mode, and mode membership is a question property. Safety reading: a long trace on a compute question is a flag for an unreliable answer, and the question text predicts which items will produce one before generation.
- **baseline wins or ties.** A single accuracy slope in log length describes the stratum as well as a mixture; the "two modes" picture adds nothing beyond the task label. The slow-error slope estimate is still reported.
- **ddm_sdv_lapse wins.** A diffusion description forecasts the stratum best. By the power check this is interpretable only if it also beats the two-process candidate, which is in the comparison, and only as a forecast.
- **Unreliable fit; no verdict** on any pair. Reported as such with the score verdict beside it; the dense-mass refit is the only permitted remedy.

## 9. Budget and stopping

One collection, sizes from section 6, cost cap at 1.5× the expected cost in section 6. If the provider changes precision or price before the run, record it and proceed; if DeepInfra is unavailable, pin another upstream that enforced the cap in a 20-call probe and record the change in `CHANGELOG.md` before the run. Compute budget for the analysis: about 1.5 CPU-hours per fold for the three models at the fixed budgets, about 25 CPU-hours in total.

## 10. Reproduction

```bash
.venv/bin/python scripts/18_task_type.py                                   # task labels
.venv/bin/python scripts/19_stratified_power.py --stage predictions       # section 7 table
.venv/bin/python scripts/19_stratified_power.py --stage driver --workers 3 # design check fits
.venv/bin/python scripts/19_stratified_power.py --stage summarize         # results/stratified/REPORT.md
```

Collection and parsing reuse `scripts/02_run_pilot.py` (`--provider DeepInfra --max-tokens 32768`) and `scripts/03_parse_logs.py --max-tokens 32768`; the fits reuse `scripts/08_robustness.py` through a `followup_task` scenario to be added at collection time, with no change to the models.
