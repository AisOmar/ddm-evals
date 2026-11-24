# Practice calibration complete; twelve untouched test questions frozen

October 27, 2026 UTC. **The separate practice step found a level with 8/12
correct answers (66.7%). Its twelve reserved test questions are now frozen,
with zero evaluated Sonnet answers collected on them.** No practice questions
are included in the frozen test, and no new advice experiment was launched.

## What was done

Before evaluated inference, the author pool, exact keys, generation code, split
and selection rule were fixed. Each of three nominal difficulty levels had
twelve practice questions and twelve reserved candidates: two of each per
mathematical family. The entire pool therefore contained 72 distinct stems,
split into 36 practice and 36 reserved candidates.

Sonnet 4.5 answered only the 36 practice items, with ordinary instructions and
no advice, in fresh contexts. Its settings match the recent studies: temperature
.7, 128-token strict A/B JSON, no extended thinking, tools or caching. All 36
responses were recognized and normally completed.

| Nominal level | Practice correct | Accuracy | Unknown |
| --- | --- | --- | --- |
| Level 0 | 8/12 | 66.7% | 0 |
| Level 1 | 10/12 | 83.3% | 0 |
| Level 2 | 7/12 | 58.3% | 0 |

The preset rule required 55–85% accuracy and chose the qualifying level closest
to 70%. Level 0 was selected. The more adaptive per-family fallback was not
used. Nominal complexity was not monotonically related to observed accuracy;
these labels should not be presented as validated ordered difficulty levels.

Level 0 practice results by family were bin packing 2/2, prefix coding 2/2,
dense determinant 0/2, matching 1/2, pattern waiting time 2/2, and scheduling
1/2. This supplies four actual baseline errors in the practice subset, rather
than a perfect-accuracy ceiling. It does not establish the same error rate on
the reserved instances.

## What is frozen

The test contains variants 2 and 3 from all six Level 0 families, twelve items
total. Variants 0 and 1 were practice. No item was moved between splits or
selected by an individual test outcome. All six families were retained.

Saved artifacts include masked questions, a separate exact answer key, item and
family IDs, the practice-only selection, and SHA-256 hashes linking the final
freeze to the original pool and protocol. All 36 evaluated-model request IDs
were audited against the practice split; none belongs to the reserved split.

“Untouched” means **no evaluated Sonnet responses** on the test questions. The
author and Haiku quality reviewer have read them. They are new local instances
of related templates, not six wholly independent new reasoning mechanisms, and
training nonexposure is unknown. No exact stem overlap was found with the 259
prior stems in the named local packet/question files checked.

## Quality review and completion addendum

Exact computations and secondary algorithms/arguments checked every author key.
Each level's twelve practice questions received blind Haiku review followed by
proof-assisted review to resolve disagreements. All blind judgments are saved;
the practice reviews did not change the questions or keys.

Only after the practice selection, Haiku reviewed the twelve selected reserved
items. Its blind batch flagged three. The proof-assisted batch hit its output
limit and remained unresolved; no partial answers were scored as agreement.
A prospective completion addendum allowed exactly one further proof review
with a 2048-token cap, preserving the original response and its cost. That
review completed and accepted all twelve fixed keys without blockers.

The addendum did not change calibration, selection, split, keys or Sonnet
configuration. The full original reservation plus the additional review bound
remained below $1. This is exact author checking plus fresh-context AI review,
not human or independent model-family validation.

## What this establishes

The requested preparation is complete: select difficulty using practice data,
then freeze distinct test items before evaluating them. The practice estimate
has headroom, but twelve observations per level and shared family templates
make it uncertain. Calibration selection can be optimistic. Held-out accuracy
is still unknown and may differ, including reaching a ceiling.

This step does not show that any advice intervention works, establish power
for five-point preservation, or authorize selecting replacements after viewing
test outcomes. The next experiment still needs its own frozen comparisons and
budget. The original large study remains paused.

## Cost and verification

New usage-based cost was **$0.102523**: 36 practice calls and nine quality-review
calls, including the truncated one. The cumulative conservative upper bound
is **$0.837918**, including earlier unresolved reservations. The full original
plus completion reservation was **$0.962395**, below the unchanged $1 ceiling.
Calculations use recorded usage and verified
[Anthropic prices](https://platform.claude.com/docs/en/about-claude/pricing).

All **206 offline tests pass**. Paid requests completed over HTTP/2 with valid
usage; the one truncated review remains explicitly unresolved in its original
record. Earlier protected files and locked artifacts verify unchanged. No
request is pending.

- [Frozen masked questions](../results/research_directions/separate_difficulty_20261027/frozen_test/questions.md)
- [Machine-readable masked questions](../results/research_directions/separate_difficulty_20261027/frozen_test/questions.json)
- [Separate answer key](../results/research_directions/separate_difficulty_20261027/frozen_test/answer_key.json)
- [Final test manifest and hashes](../results/research_directions/separate_difficulty_20261027/frozen_test/manifest.json)
- [Practice-only analysis](../results/research_directions/separate_difficulty_20261027/practice_analysis.json)
- [Deterministic selection](../results/research_directions/separate_difficulty_20261027/selection.json)
- [Original protocol](SEPARATE_DIFFICULTY_PROTOCOL.md)
- [Review completion addendum](SEPARATE_DIFFICULTY_REVIEW_COMPLETION.md)
- [Completion and cost ledger](../results/research_directions/separate_difficulty_20261027/final_status.json)
