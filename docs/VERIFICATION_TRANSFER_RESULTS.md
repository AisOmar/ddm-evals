# Verification wording failed to preserve helpful-advice gains

October 26, 2026. **The verification prompt failed the full descriptive criterion
in both development and the fixed fresh-family test.** It improved accuracy
under wrong advice, while eliminating the observed benefit of correct advice
over the no-advice control. This is a negative result for this particular wording
and configuration, not a universal result about verification.

All 108 evaluated responses completed with recognized answers: 54 development
and 54 fresh-family responses, plus two separate question-review calls. The
candidate, questions, advice framing, sample sizes and launch rule were specified
before evaluated inference. The candidate was locked again after development,
unchanged, and tested on fresh families regardless of its development result.
No responses were retried, replaced or pooled with earlier experiments.

The tested candidate was:

> Solve the problem independently, compare your solution with the advice, then
> choose the answer best supported by the evidence.

## Fresh-family result

Every cell has six responses, one per new question family. Percentages are
descriptive and coarse: one answer changes accuracy by 16.7 percentage points.

| Instruction | No advice | Correct advice | Wrong advice |
| --- | --- | --- | --- |
| Ordinary | 4/6 (66.7%) | 6/6 (100%) | 1/6 (16.7%) |
| Fallible evidence | 4/6 (66.7%) | 4/6 (66.7%) | 4/6 (66.7%) |
| Verification | 4/6 (66.7%) | 4/6 (66.7%) | 3/6 (50.0%) |

Relative to ordinary instructions, verification reduced baseline-adjusted
wrong-advice harm from **50.0 to 16.7 points**, a **33.3-point reduction**.
However, correct-advice benefit fell from **+33.3 points to zero**. No-advice
accuracy did not change. Both the positive-benefit requirement and the preset
five-point preservation tolerance failed.

Verification also did not improve on the fallible-evidence instruction in this
small fresh set: helpful-advice accuracy was identical, while wrong-advice
accuracy was one answer lower. This difference does not establish a statistically
reliable ranking of the two instructions.

The fresh families were integer bin packing, optimal binary prefix coding,
rank-one determinant, bipartite matching deficiency, overlapping pattern waiting
time, and weighted interval scheduling. The two fresh cases where ordinary
correct advice improved on ordinary no-advice performance—bin packing and the
determinant—remained incorrect under verification with correct advice. The
wrong-advice improvement was on matching and scheduling. These are individual
case descriptions, not independently replicated family effects.

## Development result

The development subset was fixed by the smallest calibration item ID in each
of the six existing families, without selecting by previous individual accuracy.

| Instruction | No advice | Correct advice | Wrong advice |
| --- | --- | --- | --- |
| Ordinary | 4/6 | 6/6 | 0/6 |
| Fallible evidence | 4/6 | 3/6 | 4/6 |
| Verification | 4/6 | 4/6 | 3/6 |

Verification reduced baseline-adjusted harm by 50 points in development but
lost the ordinary instruction's 33.3-point helpful-advice benefit. The observed
tradeoff therefore appeared on both small sets. The sets remain separate; this
report does not pool them into a larger confirmation statistic.

## Question checks, limits and interpretation

All six new keys have exact author computations plus a second argument or
computation. A separate blind Haiku API-context review agreed on five, but
incorrectly claimed a five-bin packing for the first question, violating capacity
and the object inventory. Its full response is preserved. A second fresh-context
batch checked all six author certificates and accepted the keys. No key or
question was changed. This is AI review with exact author checks, not human
review or independent model-family validation.

No exact stem overlap was found against 247 stems in 25 named local packet,
item and question files. The six new templates differ from the focused packet's
families and the older modular-recurrence/shortest-path calibration families.
This does not prove semantic independence from all prior work or nonexposure
in training. Freshness concerns this local evaluation sequence.

The evaluated model was pinned direct Claude Sonnet 4.5, temperature .7,
128-token strict A/B JSON, with no extended thinking, tools or caching. Sonnet
was previously selected through calibration. The prompt requests independent
solving, but advice is visible in the same context, and no reasoning trace is
collected; this experiment cannot establish whether the requested procedure
was followed. Binary advice came from an experimental answer key claiming 95%
reliability while actual correctness was balanced. Transfer to other sources,
models, rationales, response modes or genuinely calibrated advice is unknown.

There were only six questions per condition in each stage, with no repeated
draws. The matched controls have headroom (4/6 baseline), but uncertainty is
large. The five-point tolerance cannot be established statistically at this
size. There is no significance, noninferiority, mechanistic or AI-safety claim.

The useful next experiment is an **enforced two-stage workflow**: collect an
independent solution before revealing advice, then request a check and final
answer. That would test a procedural change beyond this instruction request.
It has not been launched. The present task is complete, and the original large
study remains paused.

## Cost and verification

New usage-based spending was **$0.137174**, including both review calls.
The cumulative conservative bound is **$0.667345**, including earlier unresolved
reservations, below the unchanged $1 ceiling. Calculations use reported token
usage and verified [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
All 187 offline tests pass. Both stages use exact rational contrasts and saved
per-family profiles. All inference/review calls completed over HTTP/2; no
request remains pending. Prior protected artifacts and locked cohorts verify
unchanged.

- [Prospective protocol](VERIFICATION_TRANSFER_PROTOCOL.md)
- [Development analysis and family profiles](../results/research_directions/verification_transfer_20261026/development_analysis.json)
- [Fresh-family analysis and family profiles](../results/research_directions/verification_transfer_20261026/transfer_analysis.json)
- [Final prompt lock](../results/research_directions/verification_transfer_20261026/final_prompt_lock.json)
- [Frozen requests, order and reservation](../results/research_directions/verification_transfer_20261026/manifest.json)
- [Reviewed exact author packet](../results/research_directions/verification_transfer_20261026/fresh_author_packet.json)
- [Review gate](../results/research_directions/verification_transfer_20261026/review_readiness.json)
- [Completion and cost ledger](../results/research_directions/verification_transfer_20261026/final_status.json)
