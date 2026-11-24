# Protocol: collapsing-bound (angle) likelihood on R1, and a per-question cue slope in the deference fits

Written 2026-11-15, before either fit was run. No API calls: both analyses reuse collected data.

## A. Collapsing bound on the augmented R1 data

**Question.** Does a collapsing decision bound describe DeepSeek-R1's answers and reasoning lengths better than the
fixed-bound DDM? A collapsing bound is the standard account of slow errors, which the cap experiment showed
(accuracy falls with finish length). In Part 1 the fixed-bound DDM tied with the baseline and the two-process model
once task type was in every model.

**Data.** The augmented, task-type dataset from `scripts/17_two_process.py`: the 400 R1 step-1 runs (8,192 cap;
incomplete runs censored at their own length; over-cap answered runs censored at the cap) plus the 62 cap-experiment
runs (24,576 cap), 462 rows. Time unit for this analysis: 2,000 reasoning tokens per unit (not the study's 100),
because the HSSM networks are trained on reaction times below about 20 units; the two caps become 4.10 and 12.29.

**Likelihoods.** (1) `angle`: HSSM's network likelihood (`franklab/HSSM/angle.onnx`, downloaded 2026-11-15), with a
censoring term computed by quadrature on the network density (`scripts/lan_censoring.py`), normalised by the
network's total mass because the network is not exactly normalised. (2) `angle` with the collapse angle fixed at 0,
which is the fixed-bound DDM evaluated through the same network: it separates "network vs analytical" from
"collapse vs no collapse". (3) The analytical DDM with the closed-form survival term (`scripts/ddm_censoring.py`),
as in Part 1. The `ddm.onnx` network is not used: its density integrates to 1.2 at slow drift (checked
2026-11-15), so it is not a fair comparator.

**Structure, identical across the three.** Accuracy coding (correct = +1), z fixed at 0.5. Drift: intercept,
scaffold, instruction, their interaction, task type (compute = 1), and a question random intercept. Boundary:
intercept, scaffold, instruction, interaction, task type. Non-decision time: intercept, task type. Collapse angle
(angle only): intercept, task type. Bounds for the network fits are the network's training bounds, with the boundary
restricted to (0.3, 2.5) because the network's tail is unreliable above about 2.8. Sampler: numpyro NUTS, 4 chains,
1,000 draws, 1,000 tune, target_accept 0.95. Diagnostics rule as in the deference analysis: a fit is flagged if any
divergence, r-hat above 1.05, or bulk ESS below 50 on a population-level parameter; a flagged fit is refit once at
double budget.

**Pre-specified readouts.**
1. Collapse angle posterior (intercept and compute effect), back-transformed. "Collapse established" if the 95%
   interval of the intercept is above 0.05 radians.
2. Pointwise LOO (`az.compare`) across the three fits. A difference counts only if it exceeds 2 standard errors and
   the fit is not flagged and fewer than 5% of Pareto k values exceed 0.7.
3. Posterior predictive check: censored share (step-1 rows and cap-experiment rows separately) and accuracy among
   finishers by finish-length bin, observed against 200 posterior simulations. The fixed-bound DDM in Part 1 predicted
   27% censored against 43% observed; the test is whether the collapsing bound closes that gap.

**What each outcome means.** Collapse established and LOO favours angle: the slow-error pattern is captured by an
urgency-like mechanism, and the within-trace stopping hazard (Part 1, step 8) has a model-level counterpart.
Collapse established but LOO ties: the data cannot separate collapse from question heterogeneity, same lesson as
Part 1. Collapse not established: the slow-error pattern comes from the question mix, as the two-process model says.

## B. Per-question cue slope in the deference fits

**Question.** Do questions differ in how much the planted key moves the drift? The control-error pattern (flips
concentrate on questions the model gets wrong without a key) suggests yes.

**Data.** The answered runs of the three clear-wording deference datasets: R1 replication, Qwen3-32B (model2),
gpt-oss-120b (model3); time unit 100 tokens as in the original fits; rows with rt below 0.1 dropped as before.

**Models.** The step-coded models already fitted (`Mv_step`: cue on drift and boundary; `Mzv_step`: cue on drift,
boundary and starting point), each extended with a question random slope on the cue: `v ~ 1 + cue_present +
(1 + cue_present | qid)`. Priors, bounds and sampler budget as in `scripts/24_deference.py`; flagged fits refit once
at double budget.

**Pre-specified readouts.**
1. Standard deviation of the question cue slope, with its 95% interval. "Heterogeneity established" if the lower
   bound exceeds 0.2 (drift units; the population cue effects were 0.02 to 0.13).
2. LOO difference against the matching fit without the random slope; counts only beyond 2 standard errors.
3. Spearman correlation between each question's posterior-mean cue slope and its control error rate, and the share
   of questions whose slope interval excludes zero.
4. Whether the population cue effects (drift, starting point, boundary) change by more than their own 95% interval
   once the random slope is in.

**What each outcome means.** Heterogeneity established with a positive correlation to control error: the key acts
mainly where the model's own knowledge is weak, which sharpens the "knowledge-dominant" reading. Heterogeneity
established without that correlation: susceptibility is a question property not explained by difficulty, worth a
look at the question texts. Not established: the population effect is a fair summary and no further stratification is
needed.

## Dated deviations

- 2026-11-15, before the full fits: the smoke test (2 chains x 20 tune + 20 draws) took 42 minutes for the angle
  model with the first survival implementation, which evaluated the network 512 times per censored row. The survival
  term was rewritten to one 96-point grid pass per row (4x fewer evaluations; checked against simulation, same
  accuracy), and the first full pass runs at 4 chains x 500 tune + 500 draws instead of 1,000 + 1,000, with the
  same flag-and-refit rule. If a fit passes diagnostics at this budget it stands; if flagged, the refit is at
  1,000 + 1,000. The smoke test also showed that HSSM 0.5's `sample_posterior_predictive` takes `dt=`, not
  `idata=`; the manual simulation fallback remains in place.
- 2026-11-15, after the first pass: the two network fits took about 11 hours each for 4 chains x 500 + 500. In each,
  chains whose NUTS step size adapted to zero never moved (per-chain posterior sd 0, maximum tree depth every
  iteration): chains 1 and 2 of `angle`, chains 0 and 1 of `angle_theta0`. The log density and gradient are finite at
  those points and at 20 jittered initial points, so this is a step-size-adaptation failure during warm-up, not a
  likelihood failure. The flag-and-refit at doubled budget that the driver launched was stopped after it had started:
  a longer run cannot repair a chain with step size zero, and would have overwritten nothing but cost about 20 more
  hours. Instead the moving chains are kept (`--stage finish`, label `*_kept`, dropped chains listed in
  `fit_<model>.csv`) and the protocol's r-hat/ESS/divergence thresholds are applied to the kept chains. For `angle`
  the two kept chains pass (r-hat 1.009, min ESS 201); the `angle_theta0` kept chains are reported with their own
  diagnostics. The analytical `ddm` fit converged in its first pass (0.5 minutes).
- 2026-11-15, after the finish stage (post hoc, labelled as such in `results/angle/REPORT.md`): (i) HSSM re-arranges
  the data with censored rows on top, and the first posterior-predictive tables compared simulated rows with masks in
  the original order; `pps()` now maps the simulated rows back to input order (and raises if the re-arrangement is not
  "censored first, otherwise stable"); all posterior predictives were recomputed. (ii) A control fit `ddm_bounded`
  (the analytical DDM under the network's parameter range: a in 0.3-2.5, v in -3..3) was added to separate the
  effect of the parameter range from the effect of the network likelihood. It was not pre-specified; it does not
  change the pre-registered theta rule and is reported as a control. (iii) The collapse rule's outcome: not
  established (recall theta 0.061 rad, interval 0.011-0.115).
