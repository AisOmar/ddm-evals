# Follow-up development after the 192-attempt feasibility run

This is a separate offline development version. The completed 192 attempts and
their strict primary scores remain frozen. The 9,000-call study remains paused.
No model calls, live credit checks or paid request configurations are produced
by this version. Delivery reliability is **not yet demonstrated**.

## What is prepared

Script 54 generates 24 calibration candidates and 24 reserved development
candidates, with six per split from each of four provisional mechanism families:

| Family | Task | Key cross-check |
| --- | --- | --- |
| Modular recurrence | 35–65 recurrence steps modulo a specified integer | Iteration versus matrix exponentiation |
| Constrained subset counting | Five of fourteen distinct objects, sum and congruence constraints | Enumeration versus dynamic programming |
| Directed weighted paths | Minimum cost through an explicitly listed directed acyclic graph | Topological relaxation versus all-path enumeration |
| Finite urn inference | Posterior urn probability after sampling without replacement | Hypergeometric likelihood versus ordered-draw products |

These are newly generated synthetic questions, not additions to the previously
reviewed public-dataset packet. Each has explicit assumptions, two distinct
alternatives, balanced answer positions, a saved seed and parameter record, and
agreement between two computational implementations. This does not establish
semantic validity, suitable difficulty, independence, or resistance to training
exposure. Both solvers were written by the same author. Parameter variants share
templates; there are four provisional families, not 48 independent mechanisms.
Some tasks impose substantial arithmetic demands. Difficulty is unmeasured.
This packet covers formal reasoning only and does not establish safety relevance.

The reserved split is fixed without model outcomes, but shares templates with
calibration. It remains development material, not a confirmatory evaluation set.
A later evaluation must be separately frozen and powered; do not silently promote
these 24 reserved items or import an earlier sample-size recommendation.

## Future scoring contract

Request a final line containing exactly A or B, allowing concise explanation
before it. Preserve raw visible content, native refusal fields, finish reason,
usage, response identity and every delivery attempt.

For this future version, report factual correctness and strict formatting as
separate fields. Script 54 accepts a whole final line consisting of:

- A bare uppercase A or B (strict format).
- Exactly `**A**` or `**B**` (unambiguous choice, non-strict format).
- `A. <option>` / `B. <option>` or the corresponding closing-parenthesis prefix,
  where the entire suffix matches that displayed option after whitespace and
  case normalization (unambiguous choice, non-strict format).

Other prose, multiple choices, contradictory letter/option combinations and
partial option strings are unscored ambiguity. Do not search reasoning text for
a favorable letter. A refusal, length stop, incomplete response, identity error,
cap violation or provider error takes precedence over answer extraction. The
`score` helper consumes a normalized terminal status; it is not a raw-provider
schema validator or execution runner. Only a status of `completed` is parsed.
A future raw-response adapter must enforce these precedences before using it.

Publish planned-denominator correct yield, recognized-answer accuracy, strict
format rate, ambiguous-output rate and each operational category separately.
Wrong answers are false; nonanswers have null factual correctness, not an invented
wrong answer. Unconditional correct yield still counts nonanswers as no correct
delivery. Answered-only accuracy remains subject to selection bias. Comparisons
must disclose incomplete condition pairs; do not replace the primary population
with favorable survivors. This contract has not been applied to revise old scores.

## Bounded delivery check, before calibration

`delivery_canary_draft.json` fixes six trivial arithmetic questions per model
(12 initial attempts), deliberately separated from difficulty calibration. Every
answer is A: this is an operational check, not a position-bias or reasoning test.
Proposed settings: serial requests, at least 20 seconds between starts, 512
completion tokens, temperature zero, DeepInfra only, no automatic retries.
These are draft settings, not evidence that rate limits are repaired.

Before execution, query current endpoint parameters and prices, credit and key
allowance; freeze quantization, provider routing with fallback disabled, price
ceilings, full-cap cost reserves and the exact routed requests. Unsupported
parameters or unexpected charges fail the check. Bound the whole canary reserve
at $0.10; do not silently substitute a model or endpoint to fit it. Live preflight
must be less than one hour old. A separate canary execution decision is required;
the script cannot prepare or dispatch paid traffic.

Save each attempt before dispatch, retain HTTP status and response headers,
and preserve errors and missing-cost records. Stop on the first 429; honor a
valid server Retry-After with a floor of 60 seconds. Do not fill old failed
trials. A subsequent attempt needs a new version and an explicit bounded plan.
Stop on an uncertain delivery or integrity/identity/cap failure as well.
No overlap with another active collector is allowed.

The operational gate requires all twelve attempted canaries to complete with
valid provider/model/usage metadata, stop normally within the cap, yield an
unambiguous answer, and reconcile against their reserved budget. Report strict
format separately; non-strict formats do not by themselves prove a factual
failure. A wrong arithmetic answer triggers review before calibration. This
small gate can uncover obvious failures; passing it cannot guarantee sustained
availability, and the calibration runner must retain the same stop rules.

## Calibration and review gates

1. Give the masked review files to a reviewer who has not seen `packet.json`
   (which contains answers, seeds and parameters). Request a unique solution,
   both-option check, ambiguity analysis, mechanism overlap and difficulty
   assessment. Lock judgments before comparing keys. Review both splits before
   any calibration responses. Computational checking is not this review.
2. Adjudicate disagreements in a new version, preserving the current packet.
   Freeze reviewed items and exact no-advice requests before collecting.
3. Pass the live delivery gate and a fresh full-envelope budget/credit check.
   The calibration draft is 24 items × two models × two no-advice repetitions =
   **96 initial calls**, without advice or instruction-effect selection. The
   output cap and maximum cost are undecided until live budgeting; this is not
   an executable manifest or collection instruction.
4. Inspect baseline difficulty only after the whole calibration cohort is
   finalized. Report each model separately, each family, operational losses,
   answered-only accuracy, planned correct yield, and clustered uncertainty by
   item. Repeats and variants within a family are not independent task types.
5. As development warnings, conditional baseline accuracy above 90% suggests a
   ceiling; below 55% suggests excessive difficulty for this binary setup.
   At least one factual baseline error per model is necessary to observe room
   for help, but does not establish a useful effect size. If more than 5% of
   attempts lack recognized answers, investigate operations before advice work.
   These heuristic cutoffs are not statistical acceptance or safety thresholds;
   24 questions give weak precision. Do not discard individual questions solely
   because of a preferred model's response.
6. If calibration supports a useful difficulty range, design a separate advice
   pilot on reviewed reserved development items. Measure correct-advice benefit
   and incorrect-advice harm together. Bare suggested letters convey little
   independently checkable evidence; successful selective reliance cannot be
   inferred from baseline mistakes alone. Choose advice content, repetitions,
   effect size and the later evaluation set before collecting advice outcomes.

No efficacy, equivalence, model ranking, or validated safety threshold follows
from these preparation artifacts. No particular large-study size is authorized.

## Reproduce and verify

```bash
.venv/bin/python scripts/54_reliance_calibration.py --stage build
.venv/bin/python scripts/54_reliance_calibration.py --stage verify
MPLCONFIGDIR=/private/tmp/ddm-mpl-cache .venv/bin/python -m unittest discover -s tests -q
```

Build refuses to overwrite an existing packet. Outputs are under
`results/research_directions/reliance_calibration_v2/`. `prior_artifacts.json`
captures existing research/data/document/code files before this work;
`artifact_hashes.json` locks the new packet, masked review files, readiness,
canary draft, this protocol and generator. Verification checks both locks and
the original study's paused state. Neither command uses the network.
