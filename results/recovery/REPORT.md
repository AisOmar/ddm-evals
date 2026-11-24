# Recovery report (plan v2, phase 4) — quick mode, 2026-10-07

**Historical artifact.** Some interpretations below were corrected on 2026-10-08:
question-level uncertainty changes several comparison verdicts, the historical
fit/scorer likelihoods differed, and the pooled tail calculation did not exclude
all fixed-drift DDMs. See [the corrected final report](../../docs/FINAL_REPORT.md)
and `results/robustness/` for matched-likelihood fits and two-repeat recovery.
The original numerical record below is preserved.

Generated from `results/recovery/*.csv` (scripts/05_recovery.py --stage all --quick: 400 draws / 500 tune / 2 chains,
50 questions, 10 repeats unless stated, one simulated dataset per cell). Truth is calibrated to the 2026-10-07 Haiku pilot
(see the module docstring). Parameters: v on the identity scale; a, t as log-ratios; z on the logit scale.
Caveat up front: single replicates. Coverage and interval widths below are indicative; replicate before pre-registering.

## 4.1 Can the design tell a drift effect from a boundary effect?  Yes.

Drift-only truth (+0.15 on v for step-by-step):

| param | true | mean | 94% HDI | covered |
|---|---|---|---|---|
| `v_scaffold[sbs]` | 0.150 | 0.226 | [0.150, 0.294] | no |
| `a_scaffold[sbs]` | 0.000 | -0.011 | [-0.078, 0.068] | yes |
| `v_instruction[thorough]` | -0.081 | -0.066 | [-0.124, 0.000] | yes |
| `a_instruction[thorough]` | 0.168 | 0.131 | [0.067, 0.199] | yes |
| `t_instruction[thorough]` | 0.336 | 0.244 | [0.097, 0.381] | yes |
| `v_scaffold:instruction[sbs, thorough]` | -0.023 | -0.052 | [-0.153, 0.032] | yes |
| `a_scaffold:instruction[sbs, thorough]` | 0.000 | 0.059 | [-0.038, 0.152] | yes |

Boundary-only truth (×1.33 on a, i.e. +0.285 log-ratio):

| param | true | mean | 94% HDI | covered |
|---|---|---|---|---|
| `v_scaffold[sbs]` | 0.000 | 0.032 | [-0.034, 0.094] | yes |
| `a_scaffold[sbs]` | 0.285 | 0.313 | [0.236, 0.375] | yes |
| `v_instruction[thorough]` | -0.081 | -0.070 | [-0.138, -0.009] | yes |
| `a_instruction[thorough]` | 0.168 | 0.150 | [0.080, 0.225] | yes |
| `t_instruction[thorough]` | 0.336 | 0.307 | [0.185, 0.440] | yes |
| `v_scaffold:instruction[sbs, thorough]` | 0.000 | -0.012 | [-0.092, 0.063] | yes |
| `a_scaffold:instruction[sbs, thorough]` | 0.000 | -0.025 | [-0.112, 0.070] | yes |

The effect lands on the parameter that carries it and the other stays at zero. The drift-only run over-estimates the
drift contrast (0.23 vs 0.15, interval edge at 0.15); watch this across replicates. It is the cell where plain_concise,
the reference, loses 21% of its easiest trials to the zero-token category.

**The code covariate must be in the formula.** Refitting the drift-only data without `has_code`: a_Intercept 0.97
(true 0.41), question-level drift sd 0.57 (true 0.25), t_Intercept −1.80 (true −0.69). Condition contrasts survive,
intercepts and the hierarchy do not.

## 4.1 Repeats per question → full-run sample size

Posterior sd of the step-by-step drift contrast at 50 questions: 5 reps → 0.057, 10 reps → 0.044, 20 reps → 0.027.
Scaling by 1/√n_questions from the 10-repeat value:

| questions × 10 reps | sd(v_scaffold) | 94% half-width |
|---|---|---|
| 200 | 0.022 | ±0.042 |
| 300 | 0.018 | ±0.034 |
| 400 | 0.016 | ±0.029 |
| 500 | 0.014 | ±0.026 |

Against a pilot-scale drift effect of 0.15 (or a boundary log-ratio of 0.29), 300–400 questions × 10 repeats resolves
either effect at better than 5 sd. Going from 10 to 20 repeats buys about as much as doubling questions at the same
call count, but held-out-question prediction (phase 7) needs questions, not repeats.

## 4.2 Measurement sensitivity (×1.5 on all durations, choices kept)

Expected: v/√k, a·√k, t·k. Observed intercepts: v 0.48 (expect 0.42), a 0.57 (0.62), t −0.26 (−0.29); all condition
contrasts unchanged within noise. The scaling identity holds, so uniform length inflation will read as "less skilled,
more cautious" exactly as the plan's limitation paragraph says. Nothing in the data can distinguish that from a real change.

## 4.1 Censoring check (C = 10.4 time units, 15% of answered runs censored)

HSSM 0.5's own deadline path is broken for the analytical DDM (its omission network is not downloadable), so
`scripts/ddm_censoring.py` supplies log P(T>C) in closed form. Posterior means:

| param | true | uncensored | P(T>C) term | censored dropped |
|---|---|---|---|---|
| `a_Intercept` | 0.412 | 0.425 | 0.451 | 0.423 |
| `t_Intercept` | -0.693 | -0.678 | -0.708 | -0.657 |
| `v_has_code` | -0.370 | -0.421 | -0.406 | -0.390 |
| `a_has_code` | 0.588 | 0.616 | 0.618 | 0.234 |
| `t_has_code` | 1.386 | 1.382 | 1.392 | 1.668 |
| `a_instruction[thorough]` | 0.168 | 0.132 | 0.099 | 0.073 |

Coverage: uncensored 94%, survival term 88%, dropped 75%.
The survival term reproduces the uncensored fit at the same sampling cost; dropping censored rows biases every
parameter that governs long trials (the code effects) and halves the instruction effect on a.

## 1.4 Position bias (option coding, z free)

z recovered: logit 0.19 [0.14, 0.23] vs true 0.20 (z = 0.55). The drift terms recover; but the option-coded fit
mis-states a_Intercept (0.33 vs 0.41) and the t terms (t_Intercept −0.54 vs −0.69). Treat option coding as the bias
sensitivity analysis it is meant to be, not as the primary fit.

## 4.3 Model recovery: does the DDM invent condition effects on non-DDM data?

| generator (no scaffold effect in truth) | scaffold terms whose 94% HDI excludes 0 |
|---|---|
| answer flip 20% after correct accumulation | none |
| fixed budget (no accumulation) | `a_scaffold[sbs]` = 0.20 [0.06, 0.36] |
| lognormal length + logistic correctness | `a_scaffold:instruction[sbs, thorough]` = -0.13 [-0.21, -0.04]; `a_scaffold[sbs]` = 0.15 [0.09, 0.21] |

Fixed-budget and lognormal+logistic data both produce a spurious boundary effect of scaffold. The answer-flip
generator does not (it is a DDM with a contaminated response, so its condition structure is a DDM's). This is the
argument for phase 7: parameter estimates alone cannot certify the accumulation story; the held-out comparison must.
The DDM-vs-baseline comparison on these same datasets is in `results/cv_model_gen_*.csv` (07_baseline_cv.py).


## 4.3b Cross-validated comparison on the generator data (07_baseline_cv.py, grouped by question, quick mode)

DDM minus baseline, per held-out trial (total ± SE in brackets). Positive favours the DDM.

| generator | joint | length | correctness \| length | verdict | max DDM divergences / fold |
|---|---|---|---|---|---|
| fixed budget (no accumulation) | -1.09 (-2180 ± 322) | -1.08 | -0.01 | baseline better | 0 |
| lognormal length + logistic correctness | -0.10 (-207 ± 64) | -0.09 | -0.01 | baseline better | 0 |
| answer flip 20% after correct accumulation | +0.04 (+70 ± 11) | +0.03 | +0.00 | DDM better | 0 |

The comparison points the right way on all three: it rejects the two non-accumulation generators and prefers the DDM on
answer-flip data, which is a DDM with a corrupted response. On fixed-budget data the entire loss is in the length
component, the same signature the Haiku pilot shows (within-question length spread far below what a diffusion process
produces). The positive control on data the DDM did generate is reported in `results/cv_model_gen_ddm_truth.csv`.

Numerical note. Early runs of this comparison on the fixed-budget data and on the pilot produced per-trial log densities
in the hundreds. Cause: hssm's analytical DDM density is unstable for |v|·a above ~50 (CHANGELOG 2026-10-07). Fits now
bound v to (−8, 8) and a to (0.1, 5), and the held-out scorer excludes draws with |v|·a > 40 and flags the fold. With
those in place the fixed-budget fits sample with zero divergences and no excluded draws.


## Pilot (Haiku 4.5, thinking off): the phase-7 comparison on the harness-check data

Grouped 5-fold CV by question, quick mode, bounded fits, zero divergences in every fold. DDM minus baseline per
held-out trial: **joint −1.30 (total −2420 ± 313)**, length −1.28, correctness-given-length −0.03 (−51 ± 12).
Within-question held-out repeats: joint −1.06 per trial. Verdict on this data: baseline better.

Where the loss sits.
* 30 of 1855 held-out trials (1.6%) are shorter than the fitted non-decision time of their cell. The DDM assigns
  them its density floor (log density −66) and they carry **69% of the total deficit**. A new question can be faster
  than every training question in its cell; a fixed t per cell has no way to say so. A lapse/outlier mixture
  (HSSM `p_outlier`) or a question-level effect on t is the standard remedy and is a specification decision.
* On the other 1825 trials the DDM still loses 0.41 per trial (SE 0.04): length −0.39, correctness-given-length
  −0.02. Split by covariate: prose questions −0.10, code questions −0.76. So once the floor trials are set aside,
  the DDM is close to the baseline on prose and loses on code. By condition the deficit is largest in plain_concise
  (−1.96 incl. floor trials) and step-by-step/thorough (−1.63).
* Correctness given length is a near tie throughout: the DDM predicts which answers are right as well as the
  baseline does. What it cannot predict is how long the model writes (3.4b: within-question sd of log length 0.13
  against the DDM's 0.51).

Positive control (data the DDM generated, same size, bounded fits, zero divergences): DDM better, +0.03 per trial
(+48 ± 14) on held-out questions and +0.04 on held-out repeats. The comparison therefore recognises accumulation when
it is there and rejects it when it is not (4.3b), and the pilot verdict is not a power or implementation failure.

## Overall calibration

91% of 138 parameter checks across stages fell inside their 94% HDI (nominal 94%; single
replicates, quick chains). Misses cluster in the `has_code` terms (22 of 50 questions carry code) and the option-coded
intercepts.

## What the design can and cannot distinguish

Can: a drift change from a boundary change between conditions; a real condition effect from none, at pilot effect
sizes, with ≥300 questions; censoring handled correctly. Cannot: a uniform change in token length from a change in
drift+boundary (4.2); and, from parameter estimates alone, accumulation from a budget or a length-logistic process
(4.3). Zero-token traces are a design feature of the concise instruction and remove ~20% of the reference cell.

## Frozen model, step 1 (DeepSeek-R1-0528 via OpenRouter, same 50 questions, 2 repeats, 2026-10-08)

Data: results/pilot_r1.csv, 400 runs. 247 answered, 138 censored at the 8,192-token cap, 15 incomplete (ended with no
visible answer, 13 of them provider-side errors), no zero-token traces, no refusals. Censoring is 21% on prose
questions and 52% on code questions; ten questions (eight code) never produced an answer in any of eight runs.
Answered accuracy is 0.93 to 0.97 in every condition, which is selection: the hard questions are the censored ones.
Position bias is absent (0.95 vs 0.97). Median answered trace 1,300 tokens; code questions six times longer.

Pre-fit check (04_explore 3.4c, pooled over cells with 2 repeats): within-question sd of log length 0.33 (Haiku 0.13;
a Wiener process at this accuracy with t0 = 0 gives 0.66). 24 of 186 cells have one answered and one censored repeat.
So R1's length does vary within a question, and a DDM samples on it (0 divergences in every fold, r-hat warnings only).

Phase-7 comparison (07_baseline_cv.py --quick, grouped 5-fold by question; incomplete runs censored at their own
length; 18 answers that an upstream let overrun the cap censored at C post hoc; results/cv_pilot_r1*.csv):

| target | component | DDM - baseline, nats per trial | SE (total) |
|---|---|---|---|
| held-out questions | joint | -2.63 | 177 of -1054 |
| held-out questions | length | -2.57 | 176 |
| held-out questions | correctness given length | -0.06 | 6.8 |
| within-question held-out repeat | joint | -2.52 | 106 of -505 |

Baseline better, about six standard errors. Where the loss sits (per-trial file):
- 171 censored rows: -606 of -1054. The DDM's log P(T > C) averages -4.5 (it predicts 1 to 7% censoring per cell);
  the baseline's averages -0.95. Observed censoring is 21-29% (prose) and 61-70% (code).
- 8 trials at the density floor (-66 each, -490 total; 4 prose runs of 120-380 tokens, 4 code runs of 1,150-3,700 tokens):
  all shorter than the fitted non-decision time of their cell (t = 230-340 tokens prose, 2,100-3,100 tokens code).
- Runs of 500-1,500 tokens: the DDM is slightly better (+0.1 to +0.9 per trial). Beyond 1,500 tokens it loses 1-2 per trial.

Why the DDM cannot reach this data, and why it is not the bounds. With a bounded at 5 the fit pins a at 4.8 in every
cell. Relaxing the bound to 15 lets a run to 10-14, and the fit then buys tail mass in the code cells by driving
drift to 0.06-0.12, which implies 64-76% accuracy against the observed 92-100% among answered runs, and still gives
0% censoring in prose cells against 21-29%. The constraint is analytic: at fixed accuracy p the shape of the
first-passage distribution is fixed (time scales with a^2), and its tail is exponential with rate
(va)^2/2 + pi^2/8 in units of a^2. For a DDM whose median length equals the observed median, the largest P(T > 8,192)
reachable with t0 = 0 is:

| accuracy | median 1,300 tokens (prose) | median 5,000 tokens (code) |
|---|---|---|
| 0.93 | 0.002 | 0.25 |
| 0.96 | 0.001 | 0.24 |
| 0.99 | 0.000 | 0.21 |

Observed: prose 0.21-0.29, code 0.61-0.70. A nondecision time only shortens the tail further. So no boundary, drift
or t0 setting produces R1's pattern: almost every run that terminates is correct, and a quarter to two thirds never
terminate by six to ten medians. That is two populations (a fast, accurate mode and a stuck mode), not one race to a
threshold; a single-process DDM must trade accuracy against the tail and loses on both.

Provider caveat. OpenRouter routed the 400 calls to four upstreams; SiliconFlow (50 runs) never enforced max_tokens
(traces to 21,800 tokens) and Novita partly; all 12 mid-stream errors came from those two. The fixed deadline was
therefore applied post hoc here. The full run must pin one upstream (Inspect openrouter `provider` arg,
allow_fallbacks=false) and record its quantisation.

Open question for the pre-registration: the cap. At 8,192 tokens a third of runs and half of code runs are censored,
and the censored runs carry the signal that separates the models. A higher cap (R1's context is 163k) would show
whether the stuck mode terminates at all; cost scales with it (this run: 2.0M output tokens, about $5).

## Cap experiment (2026-10-08): what the runs that hit 8,192 tokens do with three times the room

Not pre-registered; run after the result above to pin the mechanism. The 62 question x condition cells where both
step-1 repeats were censored or incomplete (44 code, 18 prose) got one fresh repeat each at max_tokens 24,576,
pinned to one upstream (DeepInfra, fp4, cap enforced in all 62). results/cap_experiment.csv, $2.34.

| | prose cells | code cells | all |
|---|---|---|---|
| finished before 24,576 | 17 of 18 | 33 of 44 | 50 of 62 (81%) |
| correct among finished | 12 of 17 | 26 of 33 | 38 of 50 (76%) |
| still running at the cap | 1 | 11 | 12 (19%) |

Finish lengths: median 15,900 tokens, 10th-90th percentile 11,400 to 21,900; only one finished under 8,192, so these
cells are genuinely slow, not unlucky. Only one question (code) produced no answer in any of its four cells.

Accuracy falls with finishing time. Among the formerly stuck runs: 100% correct when finished by 12k tokens (10 runs),
80% at 12-16k (15), 67% at 16-20k (15), 60% at 20-24.6k (10). The other repeats of these same questions that finished
under 8k in step 1 were 26 of 26 correct. So the length tail is not a separate stuck mode: given room, four in five
of these runs terminate, and the later they terminate the more often they are wrong.

What this does to the interpretation.
- The pure DDM is still excluded, for the analytic reason given above: one drift rate cannot be 96% accurate at
  1,300 tokens and leave a quarter of runs past 8,192.
- "Two populations" was too strong. The pattern is the classic slow-error signature: accuracy that declines with
  decision time, a heavy right tail, and repeat-to-repeat variation within a question. That is what a diffusion model
  with across-run drift variability produces (trials whose drift is near zero are slow and near chance; zero-drift
  first-passage tails are long), and it is also consistent with a collapsing bound. A single fixed-drift DDM cannot
  produce it; the baseline's lognormal does not explain it either, it merely has a fat enough tail to fit it.
- The decisive design change is the cap. At 8,192 tokens the informative runs are censored and no model can be
  compared on them. The full run needs a cap near 32k (the pinned upstream's maximum), at roughly 2.5x the per-run
  cost on the long questions.

Next pre-registration, if the project continues: HSSM's ddm_sdv (drift variability) against the same baseline, with
the survival term extended by Gauss-Hermite quadrature over drift, pinned upstream, cap 32k, and the slow-error
slope (accuracy against length within question) as a stated prediction. The 12 runs that did not finish at 24k are the
test of the tail: ddm_sdv predicts them; a fixed-drift DDM does not.
