# Pre-written outcome paragraphs (plan 8.2) — drafted 2026-10-07, before the frozen-model data exist

**Historical draft.** Later additions contain interpretations superseded by the
2026-10-08 accuracy audit and matched-likelihood analyses. Use
[the corrected final report](FINAL_REPORT.md) for current results and conclusions.

Written now so the wording is fixed before the result is known. Each paragraph is scoped to: this DDM specification
(drift ~ condition + question; boundary and non-decision time ~ condition; starting point fixed; code covariate), this
token measurement (reasoning segment before the final answer line, counted with the model's tokenizer, one linear
scale), and this baseline (lognormal length with question and condition effects; logistic correctness given length,
question and condition). The decision rule is the grouped-by-question ELPD difference with its SE; |diff| < 2 SE is
inconclusive. Held-out repeats within question are reported separately and do not drive the verdict.

## If the baseline wins

Under this DDM specification and token measurement, a drift-diffusion account of DeepSeek-R1-0528's answers on
two-choice WMDP-cyber predicts held-out questions worse than a model with no accumulation structure. The baseline, a
lognormal on reasoning length with a logistic correctness term that is allowed to depend on length, out-scores the
DDM by [X] nats per held-out run ([SE]). The loss is carried by the [length / correctness-given-length] component
[and by code-embedding questions rather than prose questions], which points to [the single question-level drift
parameter having to explain both how long the model writes and how often it is right / the fixed-drift DDM's
prediction that correct and incorrect runs share a time distribution, where the data show slower errors]. What this
does and does not mean: the accumulation structure adds nothing that a two-parameter-per-question descriptive model
does not already capture on this measurement. It does not show that the model's reasoning is not accumulation; it
shows that this operationalisation of accumulation, with token count as time, does not earn its parameters here.
The recovery simulations show the comparison can tell DDM data from non-DDM data at this sample size, so the result is
not a power failure.

## If the DDM wins

Under this DDM specification and token measurement, the drift-diffusion model predicts held-out questions better than
the lognormal-plus-logistic baseline by [X] nats per run ([SE]). The gain comes from the [length / correctness-given-
length] component. Because the baseline already has separate question effects on length and on accuracy, the DDM's
advantage is specifically the coupling it imposes between the two through drift and boundary. The fitted parameters
are then reported as the model's description: step-by-step scaffolding [raises drift by / raises the boundary by]
[..] under the concise instruction and [..] under the thorough instruction; the difference between those two effects
is [..]. These are descriptions in token units, not claims about intrinsic capability, and a uniform change in
verbosity would read as lower drift and higher boundary (recovery 4.2).

## If inconclusive

The grouped-by-question ELPD difference between the DDM and the baseline is [X] nats ([SE]), within two standard
errors of zero. Neither model predicts the distribution of correctness and length on new questions better than the
other at this sample size. The within-question held-out repeats [do / do not] separate them, which is the easier
target and does not bear on generalisation to new questions. We report the fitted condition effects as descriptive
only and do not interpret the scaffold-by-instruction comparison as evidence for or against evidence accumulation.

## If the DDM cannot be fit at all (added after the 2026-10-07 pilot diagnostics)

The plan's three outcomes assume a DDM that samples. On the Haiku 4.5 harness-check data it does not: every chain
diverges on every draw, r-hat near 3, and the posterior runs to a boundary of about 5, a drift intercept near 2 and
a question-level drift spread of 3.5 to 5. The reason is a single statistic. Within a question and condition, the
standard deviation of log reasoning length across repeats is 0.13 (IQR 0.09 to 0.18); a DDM simulated at the
pilot's own accuracies and medians gives 0.51. A diffusion process cannot produce near-constant decision times at
70% accuracy, because low accuracy requires low drift and low drift makes first-passage times variable. Length here
is set by the question, not by a noisy race to a threshold. The plan's own fixed-budget generator (4.3), not the DDM,
describes it, and the baseline beats the DDM on data from that generator by about 5 nats per run. If this holds for
the frozen model, the writeup says so directly: on this measurement, reasoning length does not carry the
trial-to-trial variability that an accumulation account needs, and the comparison in phase 7 is moot. The
pre-registered check is therefore one number computed before any fit: the within-question sd of log length. Below
roughly 0.3 at the observed accuracies, no DDM specification considered here can sample, and the study reports that
as its result rather than forcing a fit.

## If the DDM samples but cannot reach the length tail (added after the 2026-10-08 R1 rerun of the same 50 questions)

The frozen model fails the comparison for the opposite reason to Haiku. DeepSeek-R1-0528's reasoning length does vary
within a question (pooled within-cell sd of log length 0.33, Haiku 0.13), and a hierarchical DDM samples on it without
divergences. It still loses the grouped cross-validation to the lognormal-plus-logistic baseline by 2.6 nats per
held-out trial, about six standard errors, with the loss almost entirely in the length component and more than half of
it on censored runs. The reason is a property of the first-passage distribution. At 93-99% accuracy a diffusion
process has a short exponential tail: whatever the boundary, drift or non-decision time, a DDM whose median length
matches the observed 1,300 tokens cannot place more than 0.2% of its mass beyond 8,192 tokens, and one matching the
5,000-token code median cannot place more than 25% there. R1 put 21-29% of prose runs and 61-70% of code runs past
that point while answering 93-100% of the runs that did terminate. A single race to a threshold cannot be both that accurate
and that slow. A follow-up at a 24,576-token cap on the 62 cells that had stalled twice showed what the tail is: 81% of
those runs finish, at a median of 16,000 tokens, and the later they finish the more often they are wrong (100% correct
by 12k, 60% past 20k; the same questions' sub-8k repeats were 26 of 26 correct). That is the slow-error signature,
not a stuck mode. The honest statement is the one the plan reserved for a baseline win, with the mechanism named: the
fixed-drift DDM is excluded analytically, but the data carry the three marks of accumulation with variable drift,
a heavy right tail, accuracy that declines with decision time, and repeat-to-repeat variation within a question. A
drift-variability DDM against the same baseline, at a cap that stops censoring the informative runs, is the next
pre-registration, stated in advance and not fitted post hoc to this data.

## What the harness-check data (Haiku 4.5, thinking off) actually gave, for calibration of the paragraphs above

Bounded DDM, grouped CV: baseline better by 1.30 nats per held-out run. Two thirds of that is 30 runs (1.6%) that
are shorter than the fitted non-decision time, which the DDM scores at its density floor; the rest is 0.41 per run,
almost all on length, and concentrated on code questions (prose −0.10, code −0.76). Correctness given length is a
tie. The positive control on DDM-generated data comes out DDM better. So on this model the honest sentence is: the
DDM predicts *which* answers are right as well as the baseline, and cannot predict *how long* the model writes,
because the model's length is set by the question with almost no trial-to-trial variation.

## Either way, three observations stand

0. Within-question length variability is tiny on Haiku with thinking off (sd of log length 0.13), and the
   slow-error pattern in the pooled data is entirely between questions: within a question, wrong answers are no
   longer than right ones. Whether a reasoning model with a visible trace behaves differently is the first thing
   the frozen-model rerun answers.
1. The concise instruction without a scaffold produces one-line answers with no reasoning segment on about a quarter
   of runs, and those answers are right about 88% of the time. These are retrievals, not decisions, and they are a
   separate outcome category by design. Any account of "how long the model thinks" has to start by saying that on
   some questions it does not.
2. Questions that embed code or hex take three to four times as many tokens as prose questions and are answered
   correctly about 15 points less often. Whether the accumulation story holds may differ between the two, which
   is why the comparison is reported split by this covariate.
