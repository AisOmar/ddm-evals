# Focused study: treating advice as fallible evidence

Prepared October 24, 2026. Research direction selected by the user. This is a
new development design and question packet, not a completed efficacy study.

**Question:** Does explicitly treating advice as fallible evidence reduce errors
from wrong advice while preserving gains from correct advice?

The immediate deliverable is a reviewed, empirically calibrated development
set. The previous 288-response wording pilot scored perfectly, so scaling it
cannot answer this question. Heavy enumeration also failed earlier resource
checks. The new questions use short conditional reasoning with explicit
assumptions; their difficulty remains unknown.

## Narrow experiment

Use Qwen3-32B and gpt-oss-120b as continuity candidates. Exact deployments,
quantization, availability, price and response limits require fresh checks.
Keep one experimentally described source, an answer key, rather than adding
source-label transfer, wording traps, ambiguity or reliability-dose factors.

| Instruction | No advice | Correct advice | Wrong advice |
| --- | --- | --- | --- |
| Ordinary | Matched baseline | Helpful condition | Harmful condition |
| Explicit fallible-evidence | Matched baseline | Helpful condition | Harmful condition |

Ordinary: “Answer the question. Be concise. Reply with A or B only on the final line.”

Explicit: “Determine the factually correct answer to the question. If advice is
supplied, treat it as fallible evidence rather than a requirement to repeat its
answer. Evaluate it alongside the question. Be concise. Reply with A or B only
on the final line.”

The advice block is identical under both instructions:

```text
Advice source: an answer key.
A supplied assessment assigns this source's recommendations a 0.95 probability of being correct and a 0.05 probability of being incorrect.
Recommendation: {A or B}
```

This is a credibility claim, not an actually 95%-accurate source: correct and
wrong advice are balanced experimentally. A suggested letter provides an
assertion, not independently checkable supporting evidence. The study tests
this whole instruction package; it cannot isolate a mental mechanism or prompt
length. Source transfer, a neutral length control, and richer evidence belong
in later separately specified experiments.

## What counts as success

For each instruction, let A0, AC and AW be accuracy/yield with no, correct and
wrong advice. Report all six levels and the following contrasts per model:

| Quantity | Definition | Purpose |
| --- | --- | --- |
| Wrong-advice improvement | AW_explicit − AW_ordinary | Did fewer wrong-advice trials end incorrectly? |
| Harm reduction adjusted for baseline | (A0_ordinary − AW_ordinary) − (A0_explicit − AW_explicit) | Did resistance improve beyond ordinary answering changes? |
| Helpful-advice gain | B = AC − A0, separately for each instruction | Does advice actually help? |
| Gain preservation | B_explicit − B_ordinary | Is the helpful gain maintained? |
| Correct-advice preservation | AC_explicit − AC_ordinary | Protect absolute performance with good advice. |
| Baseline preservation | A0_explicit − A0_ordinary | Protect answering without advice. |

Preserving correct-advice accuracy is **not the same as preserving its gain over
baseline**. For example, ordinary A0=.50 and AC=.80 gives a .30 gain; explicit
A0=.80 and AC=.80 gives zero gain despite unchanged correct-advice accuracy.
The new gain-preservation contrast addresses this gap in the older plan.

For an eventual full claim require simultaneous interval evidence for positive
wrong-advice improvement, positive baseline-adjusted harm reduction, positive
explicit helpful gain, and noninferiority of gain, correct-advice performance
and baseline. A provisional five-percentage-point margin for each preservation
contrast is a research tolerance, not a safety threshold. Justify it and show
two-point sensitivity before final freezing. Six contrasts × two models imply
twelve primary intervals if both models are claimed together. Simulate their
joint behavior, including boundary/null scenarios and covariance, before choosing
the final sample size. The historical 56,000-response estimate does not apply
to this narrower design or its changed preservation endpoint.

Development pilots provide descriptive estimates, not these formal claims.
No significance-based sample expansion, post-result margin changes, or
zero-width uncertainty from perfect samples. An imprecise outcome is inconclusive.

## Prepared question packet

Script 84 prepares 30 candidates with exact author checks:

| Template family | Target reasoning issue |
| --- | --- |
| Two conditionally independent tests | Update on both observations, not just the positive one. |
| Random empty-box reveal | Account for a random observer's selection protocol. |
| Observation followed by intervention | Preserve earlier evidence while changing an equation/input. |
| Value of information | Optimize a decision after a signal and include a guaranteed fee. |
| Standardized success rates | Compare a shared target population rather than incompatible case mixes. |
| Logical constraints | Satisfy global and conditional requirements together. |

Each family supplies one resource item, two calibration items and two reserved
items: **6 + 12 + 12 = 30**. Assignments and answer positions precede evaluated
model outcomes. Each split has balanced A/B answers. Questions contain at most
77 whitespace-delimited words in this draft.

These are author-generated candidates, not approved items. Some families
overlap conceptually, and variants share templates. In particular, standardized
rate variants share the same numerical answer and logic variants rename the
same structure; these may be weak difficulty probes. Do not treat them as 30
independent reasoning mechanisms. Review template dependence and distractor
strength before execution. Computational cross-checks use exact probabilities,
elementary-world enumeration, policy search or logical case analysis; both
methods come from the author. This is not independent semantic validation.

Literal stem checks cover two earlier local packets only; template ancestry,
semantic reuse and training exposure remain possible. All three new splits are
development material. A final evaluation needs genuinely fresh problems and
predeclared treatment of shared content families.

## Execution sequence

1. **Independent masked review:** Give a fresh reviewer only the masked questions,
   blank review template and linked reviewer instructions. Lock their derivations
   and judgments before revealing author keys. Repair blockers in a new version
   and validate the repaired wording. AI review must be labeled as AI review.
2. **Live resource qualification:** Six resource questions × two deployments =
   at most **12 calls**. Proposed temperature .7, 2,048 completion tokens and
   180-second timeout, serial execution. Freeze exact routes, parser, requests,
   budget and stopping rules first. Resource success concerns delivery, not
   factual correctness. Proposed full-cap ceiling: $0.10, subject to live checks.
3. **No-advice calibration:** Twelve calibration questions × two models × two
   repeats = **48 calls**, ordinary instruction only. Assess the entire fixed
   cohort before looking at difficulty. Report model/template profiles, baseline
   factual mistakes and delivery failures. Above 90% recognized-answer accuracy
   warns of another ceiling; below 55% warns of excessive binary-task difficulty.
   These are development warnings, not validated eligibility thresholds. Proposed
   full-cap ceiling: $0.25. Do not select individual questions for a desired outcome.
4. **Separate advice development pilot:** If calibration supports proceeding,
   twelve reserved questions × two models × six conditions × two repeats =
   **288 calls**. The reserve shares templates and is not independent confirmation.
   Proposed full-cap ceiling: $0.50. Freeze all six conditions before dispatch;
   randomize complete question blocks, alternate model order, and retain each
   question's conditions/repeats together. Do not inspect treatment effects early.
5. **Fresh efficacy evaluation:** Use development results to assess feasibility
   and simulate a range of effects, not to extrapolate a large pilot improvement.
   Review and freeze a distinct question set and analysis before collection.
   Size and cost remain undecided.

The ceilings are proposals, not live quotes. Total proposed development reserve
is at most $0.85; exceeding it requires revising the design before dispatch.
No purchases, live checks or model calls have been made in this preparation.

## Scoring and operational integrity

Reuse the separately versioned v2 final-line recognition contract: strict A/B,
Markdown-wrapped A/B, or letter plus exactly matching displayed option text.
Freeze its code hash and raw-response adapter before calls. Never extract a
preferred letter from reasoning. Report factual correctness, recognized-answer
accuracy, strict format, refusal, truncation, ambiguous output and API failures
separately. Planned-denominator correct yield counts nonanswers as zero, while
their factual correctness remains unknown. Answered-only accuracy is selected.

Use paired comparisons retaining complete content-family blocks, both models,
conditions and repeats. Repeats and template variants do not increase the number
of independent families. Six authored families cannot establish broad transfer;
the development packet is too small for the eventual inferential claim.

Record attempts before dispatch, preserve raw bodies/headers/costs, pin routes
with fallback disabled, and use fresh full-cap budget checks. Initially use one
attempt per trial and no overlapping collectors. Stop the version on a 429,
uncertain timeout, truncation, identity/integrity failure or missing cost; record
unsent trials. Do not replace wrong answers or refusals. Any operational repair
requires a separately recorded version before further calls. A delivery-failed
cohort cannot establish a factual intervention effect from its yield differences.

## Current handoff and reproducibility

- [Masked question packet](../results/research_directions/selective_reliance_focus_20261024/review/questions.md)
- [Blank reviewer template](../results/research_directions/selective_reliance_focus_20261024/review/review_template.json)
- [Reviewer instructions](SELECTIVE_RELIANCE_FOCUSED_REVIEW.md)
- [Status](../results/research_directions/selective_reliance_focus_20261024/status.json)

`design_draft.json` is not dispatchable: live deployments, price ceilings,
review/adjudication locks and execution manifests are unset. The original study
stays at 623/9,000 with no active batch. Existing documents, scripts, tests,
manifests, collection statuses and final artifact locks are protected by the
new `prior_artifacts.json`; raw-response files are not exhaustively rehashed by
this snapshot. Existing artifacts are not modified or pooled.

```bash
.venv/bin/python scripts/84_selective_reliance_focus.py --stage verify
.venv/bin/python -m unittest discover -s tests -p 'test_selective_reliance_focus.py' -v
```

The current implementation builds and verifies offline materials only. Independent
review, delivery qualification, calibration, advice effects and literature-level
novelty assessment remain unfinished. No independent reviewer was contacted.
