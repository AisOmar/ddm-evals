# Follow-up readouts on the saved Qwen3-32B probe run

Written 2026-11-22, after the results in `docs/OPEN_WEIGHTS_PROBE_RESULTS.md` and before `scripts/114_probe_followup.py`
was run. Uses only data already on disk (`results/open_weights_probe/qwen3_32b/`: `runs.csv`, `traces.jsonl`,
`scores.csv`, `acts/`), the DeepInfra Qwen run (`results/deference/model2/runs.csv`) and the random-slope fit
(`results/deference/random_slope/per_question_slopes.csv`). No model calls, no GPU.

The parent protocol (`docs/OPEN_WEIGHTS_PROBE_PROTOCOL.md`) says that new readouts or probe families on this data need
a new dated protocol. This is that protocol. Two of its readouts (A0, A) are new tests of a caveat the results doc
raised; readout B was suggested by a post hoc check on the same data and is **not an independent test**: it fixes the
computation and the rules for a future replication and is labelled as a pre-specified re-analysis, not a confirmation.

Fixed throughout: layer 48, the primary ("spread") answer probe of the parent protocol, its fold assignment (seed
20261006, grouped 5-fold by question), its C grid, its score orientation s_key, and its question-level percentile
bootstrap (2,000 draws). Key runs = doses 0.55 and 0.95 pooled, as before.

## The caveat being tested

The primary result, D(pre) = .74 (.10 to 1.44), is a between-prompt contrast: the pre-trace state of a key prompt
against the pre-trace state of the same question's control prompt, read by a probe trained to predict the final
answer on control runs. Two readings fit it: (i) the key moves the model's starting state toward the cued option
("leans"), or (ii) the probe partly reads the identity of the letter that the key names, which is salient at the
last prompt token whether or not the model leans ("cued-letter encoding"). A third, (iii) a generic "a key is
present" signal that is the same whichever letter the key names, would cancel under the s_key orientation only if
hint letters were balanced; they are 55 A / 45 B, so it is tested too.

## Readout A0: D(pre) by cued letter (tests reading iii)

D(pre) computed separately over the 55 questions whose key names A and the 45 whose key names B, each with its own
question bootstrap. A generic presence signal contributes with opposite signs to the two groups; a lean contributes
with the same sign.

- *Not a generic presence signal*: both group estimates have the sign of the overall D(pre) and both intervals
  exclude 0.
- *Generic presence signal dominates*: the two estimates have opposite signs.
- *Undetermined*: otherwise.

## Readout A: cued-letter probe and residualised D (tests reading ii)

1. **Cued-letter probe.** Per fold, an L2 logistic probe (standardised features, C by inner 3-fold grouped CV over
   the same grid) trained on the pre-trace state (row 0) of the key runs outside the fold to predict `hint_letter`
   (A against B). Out-of-fold AUROC on the key runs of the held-out fold is reported. Because the pre-trace state is
   deterministic per prompt, this probe reads "which letter the key names" from the state the model starts
   reasoning in; it is expected to be near-perfect and its AUROC is a sanity check, not a result.
2. **Overlap.** Per fold, the cosine between the answer probe's weight vector and the cued-letter probe's weight
   vector, both mapped to raw activation units (coefficient divided by the scaler's scale). Reported as the mean
   over folds.
3. **Residualised scores.** Per fold, let u be the unit cued-letter direction in raw units. For every scored
   position x of every run in the held-out fold, the residualised answer score is s(x − (x·u)u) = s(x) − (x·u)(w·u),
   with w the answer probe's raw-unit weight vector. The same orientation s_key and the same bins (pre, deciles,
   final) as the parent protocol. The original scores are recomputed in the same pass and checked against
   `scores.csv` (they should agree to numerical precision; any disagreement is reported).
4. **Readout.** D_res(k) for pre, deciles 1 to 10 and final, with intervals, beside the original D(k).
   - *Survives*: the interval of D_res(pre) excludes 0 and D_res(pre) >= 0.5 x D(pre). The pre-trace shift has a
     component along the answer direction that is not the cued-letter direction; reading (i) is strengthened.
   - *Collapses*: the interval of D_res(pre) covers 0. At this layer the answer direction and the cued-letter
     direction are not separable at the pre-trace position; the starting-point class stays a between-prompt
     contrast and readings (i) and (ii) remain tied.
   - *Attenuated*: otherwise (interval excludes 0 but the estimate is below half the original).
   The same table for D_res(10) and D_res(final) says whether the late growth is along the cued-letter direction
   too; no rule is attached to it.

What projection cannot do: if the model's lean toward the cued option is implemented along the same direction
as the cued letter's encoding, projection removes both, and "collapses" is then a limit of the method, not
evidence against a lean. The protocol states this in advance so that "collapses" is not read as a refutation.

## Readout B: per-question probe effect at four positions against three targets (pre-specified re-analysis)

The parent readout 5 compared the per-question probe effect at decile 10 with the random-slope target and found
rho = −.01. A post hoc check found the effect at the final reasoning token tracks this run's own per-question
behavioural effect at .57. That check is close to tautological: at the final token the probe predicts the run's
own answer at AUROC .975, so a per-question final-token effect is nearly the per-question follow-rate difference
computed from the same runs. This readout separates what is informative from what is mechanical.

Per question q, the probe effect at bin b is the mean s_key(b) over q's key runs minus the mean over q's control
runs, from `scores.csv` (layer 48, spread probe), for b in {pre, d5, d10, final}. Targets:

- T1: this run's behavioural key effect, key follow rate minus control follow rate per question;
- T2: the DeepInfra run's behavioural key effect, the same quantity from `results/deference/model2/runs.csv`
  (answered runs only);
- T3: `slope_mean` of the random-slope fit (variant model2, model Mv_step_rs).

Spearman correlation, 2,000-draw question bootstrap, for each of the 12 (bin, target) pairs. Rule as in the parent
readout 5: *consistent* if rho >= 0.3 with lower bound above 0; otherwise *not consistent*.

Independence control for T1 at d10 and final: the probe effect is computed from control reps 0 and 1 and key rep 0
(both doses), and T1 from control reps 2 and 3 and key rep 1, so that no run's own answer enters both sides.
Reported beside the all-reps version, together with the test-retest Spearman of T1 between the two halves, which is
the ceiling any probe-based per-question effect can reach. The pre-trace effect needs no split: it does not depend
on the sampled answer.

Interpretation fixed in advance: the pre-trace row is the informative one (a between-prompt quantity that cannot
be the run's own answer); d5 is the mid-trace check; d10 and final with the independence split show how much of
the post hoc .57 was the run's own answer. T2 and T3 are the external targets. A consistent pre-trace or d5
result against T1 or T2 would say that questions where the key moves the starting state more are the questions
where it is followed more; it would not revive readout 5's verdict on T3, which stands as reported.

## Output

`results/open_weights_probe/qwen3_32b/followup/`: `REPORT.md`, `followup.json`, `curves_residualised.csv`,
`per_question.csv`. The results are appended as a dated section to `docs/OPEN_WEIGHTS_PROBE_RESULTS.md`.
