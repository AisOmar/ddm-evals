# Shorter reviewed tasks and resource qualification before calibration

The user authorized shorter questions, fresh independent review, representative
resource checks and then a small no-advice calibration. This is a new version.
All earlier runs, failures, scores and question versions remain unchanged; the
original 9,000-call study stays paused. No advice-effect collection is included.

## Question changes and fixed cohorts

Script 62 creates 36 synthetic items with checked keys. There are four separate
resource-check items (one per family), sixteen calibration items (four per
family), and sixteen reserved development items. The cohorts share templates,
not exact stems; they do not establish unseen-family generalization.

| Family | Earlier burden | New task |
| --- | --- | --- |
| Recurrence | 35–65 modular recurrence steps | Term 7–10, small coefficients/moduli; off-by-one distractor |
| Subset count | 2,002 five-of-fourteen subsets | Twenty three-of-six subsets; competing congruence-residue count |
| Directed paths | Nine vertices | Six vertices, explicit small positive costs; altered-edge-price distractor |
| Urn inference | Six draws and long exact fractions | Two or three draws, small urns; round posterior to a whole percentage point |

These revisions reduce repetitive bookkeeping, not every source of difficulty.
Probability distractors use the wrong with-replacement assumption rather than
adding an arbitrary tiny fraction. Numeric errors can still be the main source
of mistakes. Actual difficulty and advice usefulness remain unmeasured. Choices
are balanced within each calibration/reserved family and each suffix position
across families. The finite four-item blocks retain assignment structure;
individual requests show no item ID, seed, key, other questions or mappings.

Keys agree between two author computational methods. A fresh-context AI reviewer
must independently solve all 36 masked items, check both options and language,
save judgments and hash locks before author-key comparison, and identify cues,
ambiguities and family overlap. Compare all judgments to author keys before
execution. Resolve any disagreement in an append-only version and obtain masked
validation. AI review is not human expertise or independent model training.

## Two-stage execution

Use gpt-oss-120b on DekaLLM BF16 and Qwen3-32B on DeepInfra FP8, with exact
endpoint tags, quantization filters and fallback disabled. Different deployment
effects remain inseparable from model effects. Check live metadata, all price
components, capacity, account credit and key allowance before each frozen phase.
Preflight expires after one hour. Cache reads are bounded at the full prompt
rate when no higher than it; unknown nonzero charges cause rejection.

Both phases use temperature 0.7, at most **2,048 completion tokens** including
reasoning, and a **180-second timeout**. The smaller cap keeps typical generation
within the timeout at the previously observed Qwen rate; this is a planning
assumption, not a guarantee. Requests are serial, at least **five seconds between
preparations**, with no overlapping collectors and one attempt per trial.
No automatic retries, provider changes, price increases or credit purchase.
Save exact requests, attempt reservations before dispatch, raw/partial bodies,
headers, HTTP status, identities, usage, timings and costs. Delete private curl
configs after finalization. Freeze code/protocol/input hashes before first call.

1. **Resource phase:** four resource items × two models = **eight initial calls**.
   Conservative full-cap reserve must be <=$0.10. Require valid normal-stop
   deliveries, recognized choices, usage and recorded costs within per-attempt
   bounds for all eight. A factual wrong answer does not fail this operational
   gate and must not select or change later calibration questions. A refusal,
   length stop, ambiguous output, rate limit or timeout fails this gate. If it
   fails, stop the version and do not launch calibration; preserve all outcomes.
   Report resource behavior independently from calibration. The resource items
   never enter calibration accuracy or determine item inclusion.
2. **Calibration phase, only after the resource gate passes:** sixteen fixed
   calibration items × two models × two repetitions = **64 initial calls**.
   Fresh preflight and exact request/analysis freeze required; full-cap reserve
   must be <=$0.50. Total phase ceilings sum to $0.60. No reserved item is called.
   Alternate model order over item/repeat pairs. Refusal, censoring, incomplete
   and ambiguous outputs remain behavioral outcomes, not retry opportunities;
   continue fixed trials for those outcomes. Stop the version on HTTP/provider
   errors, uncertain delivery, identity/schema/cap/provenance failures, missing
   or invalid cost, or exhausted budget. Retain failures and all unsent IDs.

At any 429 stop, preserve headers, and honor a valid Retry-After with a minimum
sixty-second delay before any future separately versioned attempt. Do not fill
earlier failed cells or treat HTTP 200 with a partial body as a completed answer.

## Frozen analysis and decisions

Use the v2 final-line parser, reporting factual correctness and strict format
separately. Refusal and length stops override extracted letters. Wrong recognized
answers are false; nonanswers are null correctness, while contributing no correct
delivery to the planned denominator. Do not inspect interim calibration accuracy.

Analyze only all 64 uniquely attempted/finalized calibration trials, with no
operational failure. Otherwise report a stopped delivery cohort without complete
baseline accuracy conclusions. Per model, overall and for each fixed family,
report planned, recognized, correct and strict-format counts, every outcome
category, correct/planned yield, correct/recognized accuracy, format and ambiguity
rates, completion-token/time summaries and recorded costs. The two repetitions
are kept together as one item cluster; four templates are not sixteen independent
mechanisms. Answered-only accuracy is selection-sensitive.

Use 10,000 question-cluster bootstrap draws within each fixed family, seed
20261021065, carrying both repeats together. Compute percentile 95% intervals
for correct yield and recognized-answer accuracy, disclosing undefined accuracy
draws. Small/fixed families and ceiling-degenerate intervals limit inference;
these intervals do not establish equivalence or unseen-family performance.

Development warnings per model: conditional accuracy >90% suggests ceiling,
<55% excessive difficulty, and >5% unrecognized outputs warrants operations or
resource investigation. They are heuristic warnings, not safety thresholds,
statistical tests or rules to retain only favored individual questions. Report
family variation without outcome-selecting questions. No model-ranking, advice
effect or validated safety conclusion follows. Assess these results before any
separately designed advice pilot; no advice experiment launches automatically.
