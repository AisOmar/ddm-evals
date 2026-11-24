# Short reasoning replacement packet and independent review

Prepared October 22, 2026, for review. The new development packet replaces the
enumeration-heavy tasks with **40 short, self-contained questions across eight
reasoning families**. Author computations support one answer per question.
Independent semantic review and live resource qualification are still pending.
No model calls have been made for this version.

## What changed

There are no recurrence loops, subset enumerations, graph searches, multi-draw
urn calculations, external factual lookups, or percentage-rounding rules in the
question text. Questions ask for a short implication, fraction, percentage,
finish time, state, or decision. Each stem is at most 100 whitespace-delimited
words; the exact observed range is available from the packet.

| Family | Reasoning required | Typical distractor |
| --- | --- | --- |
| Quantified implications | Follow two premises and track whether existence is guaranteed | Assume a group exists or reverse a one-way inclusion |
| Base-rate conditioning | Restrict the denominator to flagged objects | Confuse sensitivity with posterior probability |
| Weighted rates | Combine unequal group sizes | Average two percentages equally |
| Dependency scheduling | Account for parallel prerequisites | Add all task durations |
| Sequential state updates | Track a change, swap, and assignment | Skip the swap |
| Set overlap | Recover an intersection, then condition on a subgroup | Divide by the entire population |
| Causal intervention | Replace one equation while keeping an external input fixed | Infer a changed input from the overridden equation |
| Expected net value | Subtract a certain fee and compare average payoffs | Prefer a large possible prize or ignore its cost |

Each family has one resource item, two calibration candidates, and two reserved
development candidates: **8 + 16 + 16 = 40**. Cohorts were assigned before any
evaluated-model outcomes. The reserved set shares templates and is not an
untouched test of new reasoning families. No question is an empirical difficulty
anchor yet. These short problems may still be too easy; a successful resource
check will not establish useful calibration difficulty.

The author key file includes a derivation, parameters, and a second computational
check for each item. The checks include truth-table countermodels, exact rational
arithmetic, event simulation, register execution, and elementary-outcome
accounting. These are author checks, not independent review. Options are balanced
within each cohort, then all questions are shuffled and given anonymous IDs.
IDs, cohort labels, and other questions will not be shown in model requests.
Aggregate balancing does not establish the absence of every answer-position cue.

## What to give the independent reviewer

Use only these files, plus the instructions in the next section:

- [Readable masked questions](../results/research_directions/short_reasoning_v4_20261022/review/questions.md)
- [Masked questions as JSON](../results/research_directions/short_reasoning_v4_20261022/review/masked_questions.json)
- [Unfilled review template](../results/research_directions/short_reasoning_v4_20261022/review/review_template.json)

The masked files contain IDs, literal questions, and options. They omit author
keys, solutions, parameters, families, and cohort assignments. Do not give the
reviewer this report's family descriptions, the generator source, the resource
draft, the author folder, previous judgments, or previous model outputs before
the initial review is saved. For an AI review, use a fresh conversation without
the authoring conversation. This makes the review independent of author context,
not independently trained model replication or human expert validation.

## Copyable reviewer instructions

Review all 40 supplied two-choice questions independently using only their literal
stems and options. Do not inspect author solutions, generator code, cohort labels,
model responses, or prior review judgments. Record your identity, date, and prior
exposure in a new copy of the supplied template.

For every question, derive the answer before choosing A or B. Check both options.
For “must be true” questions, test logical entailment, not mere possibility. Treat
fractions as exact. Record whether the supported option is unique, whether all
necessary assumptions are explicit, whether an option or phrase gives away the
answer, and whether any wording could support the other choice. Record a short
derivation and your assessment of the alternative. Mark unclear, both-supported,
or neither-supported items without forcing a choice.

Assign expected difficulty and estimated reasoning steps before seeing model
outcomes. Identify repeated templates or semantic dependencies across questions;
do not count numeric variations as independent mechanisms. For each item use
disposition `retain`, `repair`, `exclude`, or `unresolved`, and a Boolean
`must_fix`. `unique_supported_answer` must be a Boolean; use null only when
unresolved. `chosen_letter` must be `A`, `B`, or null. Do not make silent repairs.

Save the complete first-pass review and any independent solver code. Save a
SHA-256 digest of each before asking for author-key comparison. Preserve those
initial files. An author and reviewer can then compare keys and adjudicate
wording, uniqueness, cues, and family overlap. Save disagreements even if they
are later resolved. Every change needs an append-only version and another masked
validation before execution; agreement on a numerical key alone is insufficient.

## Acceptance and handoff

Review must cover all 40 IDs exactly once. Before resource testing, every retained
item must have a uniquely supported answer matching the author key, a saved
derivation, and no unresolved wording, option, or answer-cue blocker. Any repairs
must have a separately preserved validation. Do not silently discard difficult
or inconvenient items to make a gate pass.

The [resource-test proposal](SHORT_REASONING_V4_RESOURCE_PLAN.md) specifies the
intended deployments, 16 fixed calls, resource limits, budget, and stopping
rules. It is ready for user review; it has not been executed. The original
9,000-call study and all previous packet versions remain unchanged.

Author-only reference: `results/research_directions/short_reasoning_v4_20261022/author/packet_with_solutions.json`.
Keep it out of the initial reviewer handoff. `packet_hashes.json` locks this
version's files. `status.json` records the unfinished gates.
