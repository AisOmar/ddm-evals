# Results: answer probe across the reasoning trace of Qwen3-32B under the planted key

Written 2026-11-22 (UTC; evening of 2026-11-21 local) after the run finished. Protocol: `docs/OPEN_WEIGHTS_PROBE_PROTOCOL.md`
(pre-registered 2026-11-21 before any model load; one dated deviation, the last-token-only secondary probe, added before
the run). Machine-generated report: `results/open_weights_probe/qwen3_32b/REPORT.md`, figure `figure.png`, numbers
`bootstrap.json`, per-run per-position scores `scores.csv` / `scores_last.csv`. Activations are kept locally (git-ignored,
14 GB, 800 files) in `results/open_weights_probe/qwen3_32b/acts/`.

## Run

One RunPod A100 SXM 80 GB (Secure Cloud), `Qwen/Qwen3-32B` bf16 through `transformers`, batch 8, cap 8,192, temperature
0.7, top_p 0.95, top_k 20, thinking mode. 800 runs on the 100-question `deference_model2_design.csv`; 799 answered, 1 control
run censored at the cap, no refusals, no unparseable answers. Wall time about 8 h of generation (first batches 340 s, later
ones 70-120 s; ~210 ms per decoding step with the GPU 39% busy, i.e. bound by the generation loop, not the card) plus 40 min
of probe fitting on the box; cost about $18. Weights were cached in the pod's RAM-backed /dev/shm because the pod had only a
50 GB container disk.

## 1. Behavioural replication: the deployment matches DeepInfra

| cell | n | answered | followed the key | correct | mean tokens | median tokens | mentions the key |
|---|---|---|---|---|---|---|---|
| control | 400 | .998 | **.113** | .887 | 467 | 299 | .27 |
| key, audit .55 | 200 | 1.000 | **.280** | .720 | 616 | 469 | .77 |
| key, audit .95 | 200 | 1.000 | **.275** | .725 | 643 | 431 | .65 |

DeepInfra (2026-10-15): follow .105 / .275 / .255, mean tokens 474 / 665 / 638. No "deployment differs" flag. Per question,
the behavioural key effect (key follow rate minus control follow rate) correlates .66 (Spearman, n = 100) between the two
deployments, so per-question effects are reproducible, not noise.

## Probe

Layer selection: control out-of-fold AUROC at the last reasoning token .747 / .876 / **.975** / .875 at layers 16 / 32 /
48 / 60; layer 48 selected; pre-condition (>= .80) met. The same probe reads the pre-trace position (last prompt token)
at AUROC .651 on control runs. The last-token-only secondary probe reaches .994 at the last token but .545 at the pre-trace
position, i.e. it is blind there.

## 2. Primary readout: shape of the key effect

D(k) = key minus control mean probe logit toward the cued (wrong) option, by trace decile, question-level bootstrap:

| position | pre | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D | **.74** | .06 | .43 | .34 | -.14 | .05 | .01 | .28 | .52 | .76 | **.89** |
| 95% interval | .10-1.44 | -.18-.30 | .14-.72 | .00-.69 | -.62-.30 | -.32-.39 | -.41-.39 | -.11-.65 | .14-.90 | .33-1.19 | .55-1.25 |

D(pre)/D(10) = .86 [.12, 1.74]; D(8)/D(10) = .60 [.19, 1.06]. **Pre-registered classification: starting point** (D(pre) at
least half of D(10) and its interval excludes 0). Firmness: low. The lower bound of D(pre) is .10 and the ratio interval
spans .12 to 1.74, so "evidence" is not excluded by the data; the point estimate decides, as the protocol says.

What the curve actually looks like (not a pre-registered class): the key's shift is present at the pre-trace state, drops to
about zero in the first decile, is small and unstable through the middle of the trace (deciles 4-7 cover 0), and grows
steadily over the last three deciles to its largest value at the end. So it is both: a shift before any reasoning token is
written, and growth over the final third. Neither "starting point" nor "evidence" alone describes it.

Secondary (deviation 2026-11-21), probe trained at the last reasoning token only, same layer: D(pre) .16 [-.24, .56], D(8)
.21, D(10) .65 [.43, .89]; D(pre)/D(10) = .26, D(8)/D(10) = .33 [.02, .66]; **class: evidence**. The disagreement with the
primary is explained by that probe's blindness at the pre-trace position (AUROC .545): it cannot see a starting-point shift.
Within the trace both probes agree: the effect on the final-answer direction appears in the last 30-40% of the reasoning.
Under the secondary probe D(8)/D(10) = .33 sits just above the late-override threshold of .25.

Note on the pre-trace position: the prefill state is a deterministic function of the prompt (within question x cell the
pre-trace score has SD .018 across repeats), so D(pre) is a within-question contrast of two prompts (with and without the
key). It says the key changes the state the model starts reasoning from, in the direction the probe associates with
choosing the cued option. It cannot say anything about within-prompt variation (see readout 3).

## 3. Followed versus resisted: decided late

Within question, followed and resisted key runs first separate (bootstrap lower bound of the difference above 0) at
**decile 10**. By the protocol's rule (after decile 7) the outcome is decided late in the trace. Across questions the
pre-trace score does predict following (AUROC .70, exploratory table below), but that is between-question difficulty, since
followed and resisted repeats of the same prompt share the same pre-trace state.

## 4. Silent versus explicit followers

111 key runs followed the key; 20 never mention it (rule `META_ACK`), 91 do. Mean s_key at pre / decile 1: silent .36 /
.51, explicit 1.48 / 1.12; followed-group decile-10 mean 1.37. Silent followers are **not** at the followed decile-10 level
by decile 1, so "silent" does not mean "absorbed before writing". If anything the silent followers start with a weaker
leaning than the explicit ones.

## 5. Per-question target from the random-slope fit: not consistent

Spearman between the per-question probe effect (key minus control mean s_key at decile 10) and `slope_mean` of
`per_question_slopes.csv` (model2, Mv_step_rs): **rho = -.01 [-.21, .19]**, n = 100; verdict "not consistent".

Post hoc checks (not pre-registered, labelled as such): the decile-10 probe effect also does not track the per-question
behavioural key effect in this very run (rho -.10), whereas the effect read at the **final** reasoning token does (rho .57,
p < 1e-9). The random-slope target itself correlates only .29 with the DeepInfra per-question behavioural effect, and the
final-token probe effect correlates .13 with it. So readout 5 fails for two reasons at once: the decile-10 average is a
poor per-question summary (the last 10% of a 450-token trace is ~45 tokens of mixed content), and the random-slope
estimates are a weak per-question target. The pre-registered verdict stands; the final-token version is a candidate for a
future protocol, not a result.

## Secondary and exploratory

- **Absolute token position.** D is small in the first 200 tokens (.15, .21), rises to .5-.8 at 200-600 tokens and is
  largest at 600-700 tokens (1.87 [.63, 3.03]); beyond 900 tokens the bins are small and noisy. This is the DDM's time
  axis: the key's effect on the internal leaning grows with elapsed tokens, consistent with a drift reading there.
- **Early warning among key runs** (AUROC for `followed`): probe at pre .70, falling to .61 mid-trace, .71 at decile 10;
  log trace length .72. The internal pre-trace signal equals the best text-side signal (length) and neither is strong.
- **Other layers.** Layer 48 is the only layer with a clear curve; layers 16 and 32 show D near 0 throughout, layer 60 a
  weak late rise. The class depends on the layer in the sense that only one layer reads the leaning well enough to test.

## Reading, against the protocol's "what each outcome means"

1. The DDM reading of Qwen ("evidence", v_cue .13-.20, no starting-point shift) is **partly wrong and partly right**.
   Right: within the trace the key's effect on the answer direction grows, mostly over the final third, and grows with
   absolute token count. Wrong: there is also a shift before the first reasoning token, of about the same size as the
   end-of-trace effect, which the step-coded fit did not attribute to the starting point. The protocol's explanation
   applies: with little change in trace length, a starting-point shift and a drift shift are separated only weakly by
   the length distribution, and the fit put everything on drift.
2. The within-prompt outcome (follow or resist) is not readable early. Followed and resisted repeats of the same prompt
   separate only in the last decile. For the monitoring thread this is the important negative: neither the text monitor
   (earlier work) nor the internal state at the prefix tells which run will cave; both see question difficulty, not the
   run's fate.
3. Silent following is not pre-absorbed deference. The traces that never mention the key are not the ones whose internal
   leaning was already set; they start weaker.
4. The per-question random-slope estimates are not recovered by the probe. The behavioural per-question effects
   themselves replicate across deployments (.66), so the failure is in the targets and the decile summary, not in the
   existence of per-question effects.

## Caveats

- One model, one layer that reads the leaning well, one probe family (linear, control-trained). The protocol forbids
  trying other probe families on this data without a new dated protocol.
- The pre-registered class is decided by point estimates whose intervals are wide; "starting point" should be reported
  with its interval, as above, not as a firm label.
- The pre-trace shift is a between-prompt effect by construction. Whether it is "the leaning" or "the key is in context"
  cannot be separated with a control-trained probe; the followed-versus-resisted contrast within question (readout 3) is
  the within-prompt test and it says the state at the prefix does not decide the run.
- Generation here is HF `transformers` sampling, not the DeepInfra vLLM stack; the behavioural match (follow rates within
  .02 of DeepInfra, lengths within 10%) is the evidence that this does not matter for the readouts.


## Follow-up readouts (protocol `docs/OPEN_WEIGHTS_PROBE_FOLLOWUP_PROTOCOL.md`, dated 2026-11-22; run the same day)

No new model calls. Script `scripts/114_probe_followup.py`; outputs in `results/open_weights_probe/qwen3_32b/followup/`.
The follow-up tested the caveat above (is D(pre) a lean toward the cued option, or the encoding of the letter the key
names, or a letter-blind "a key is present" signal?) and fixed a per-question readout at four positions.

**A0, D(pre) by cued letter.** D(pre) = -.18 (-.97 to .59) over the 55 questions whose key names A and +1.87 (.84 to
2.94) over the 45 whose key names B. By the registered rule (opposite signs) the verdict is **"generic presence
signal dominates"**. The rule's label is misleading here and the post hoc decomposition says why: the symmetric
component (a lean toward the cued option, same sign for both letters) is .85 (.21 to 1.50) and the asymmetric component
(a shift toward option B whichever letter the key names) is 1.03 (.36 to 1.68). The asymmetry is behavioural, not a
probe artefact: in this run a key naming B lifts the follow rate from .16 to .46 (+.29) and a key naming A from .07 to
.13 (+.06), a difference of .24 (.14 to .35); the DeepInfra run shows the same (+.26 against +.08, difference .18, .07
to .29). The model has a standing bias toward B (control follow rate .16 for wrong-B against .07 for wrong-A) that the
key amplifies, and the pre-trace probe shift mirrors it letter by letter. At decile 10 the shift is a clean lean
(L .86, .50 to 1.21; G -.30, -.68 to .06); at the final token both components return (L 1.33, G .90), as they must,
since the final-token score is nearly the answer and the answers are asymmetric. Consequence for the headline: the
pooled D(pre) = .74 is .55 x (-.18) + .45 x 1.87, i.e. it comes from the B-key questions; with exact counterbalancing
it would be about .85. Consequence for the design: `correct_is_A` was randomised at 55/45 and the key's effect depends
strongly on the letter, so future runs should counterbalance exactly and report by letter.

**A, cued-letter probe and residualised D.** A probe trained on key runs to read which letter the key names from the
pre-trace state is near perfect out of fold (AUROC .999), as expected for a deterministic function of the prompt.
Its direction is orthogonal to the answer probe's (cosine -.03, folds -.05 to -.01). Projecting it out of every
scored state leaves the key-minus-control shift intact or larger: D_res(pre) = .96 (.33 to 1.60) against the
recomputed D(pre) = .62 (.05 to 1.20); D_res(10) = .76, D_res(final) = 1.07, unchanged. **Verdict: survives.** The
pre-trace shift is not the cued-letter encoding; reading (i) of the caveat, a change in the starting state along the
answer direction, is strengthened. Note on reproduction: the laptop refit of the answer probe chose C = 0.1 in all five
folds where the pod fit had chosen C = 1.0 in one, so per-run scores differ for those 20 questions and the recomputed
curve is D(pre) .62, D(10) .76 instead of .74 and .89; the class is unchanged.

**B, per-question probe effect at four positions against three targets.** Spearman with question bootstrap, n = 100:

| position | T1 this run's behavioural effect | T2 DeepInfra behavioural effect | T3 random-slope `slope_mean` |
|---|---|---|---|
| pre | .02 (-.18 to .23) | -.01 (-.20 to .19) | .10 (-.10 to .29) |
| d5 | .00 (-.19 to .20) | .16 (-.02 to .33) | .03 (-.17 to .23) |
| d10 | -.10 (-.29 to .10) | -.17 (-.34 to .02) | -.01 (-.21 to .19) |
| final | **.57 (.40 to .70)** | **.37 (.17 to .54)** | .13 (-.08 to .32) |

Only the final token is "consistent" by the rule, and the independence split shows why: with the probe effect from
one half of the repeats and the behavioural effect from the other, final vs T1 falls to .28 (.06 to .48), against a
test-retest ceiling for the behavioural effect itself of .47 (.22 to .68), and d10 vs T1 is -.15. The final-token
score carries the per-question effect because it carries the run's own answer; no earlier position carries it, and the
pre-trace shift, which does predict following across questions on average (AUROC .70), does not rank questions by how
much the key moves them. The parent readout 5's verdict on T3 stands.

**What the follow-up changes.** The starting-point reading is firmer in one respect and narrower in another. Firmer:
the pre-trace shift survives projection of the cued-letter encoding and is orthogonal to it. Narrower: it is concentrated
on the questions where the key names B, which is also where the key moves behaviour, so "the key changes the state the
model starts from" holds for the letter the model is already biased toward and is near zero for the other. Whether the
asymmetry is a position bias of Qwen3-32B on this two-option format, or something about which questions had A as the
correct answer, cannot be separated here, since `correct_is_A` is fixed per question.

**Addendum, same day: the letter asymmetry is in every model and dataset** (`scripts/115_letter_asymmetry.py`,
`results/deference/letter_asymmetry/REPORT.md`). On the October DeepInfra runs, a key naming B beats a key naming A by
+.08 (.00 to .17) for R1, +.18 (.07 to .28) for Qwen3-32B and +.05 (-.01 to .12) for gpt-oss-120b; on the held-out
wordings by +.07, +.17 and +.05; on the pod run by +.24. Control wrong-B rates exceed wrong-A rates in all three models.
Part of this is difficulty: six of the 45 B-key questions are wrong in all three models in control, against two of the
55 A-key questions. But the asymmetry survives among questions the model always gets right in control (Qwen +.22, .11 to
.35; pod +.29; gpt-oss +.07, .01 to .14; R1 +.07, -.01 to .16), so it is not only difficulty. Position bias toward the
second option and properties of the 45 A-correct questions cannot be separated in this design, since the correct letter
is fixed per question; a re-run with the options swapped would separate them for under a dollar per model on DeepInfra.
