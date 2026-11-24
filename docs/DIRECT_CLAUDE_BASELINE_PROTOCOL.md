# Separate direct-Claude development baseline

Frozen before inference, October 26, 2026. Authorization: the user's repeated
requests to launch and proceed, most recently “do that.” This changes the models
and answer contract; no earlier observations are pooled or replaced.

Use direct Anthropic Messages API, pinned Haiku 4.5 and Sonnet 4.5 snapshots,
temperature .7, max_tokens 128, no extended thinking, no tools, no caching,
nonstreaming HTTP/2 with a 120-second timeout. Require a JSON object containing
only answer, an A/B enum, using output_config.format. Preserve every response.
An answer counts only after HTTP 200, matching model, end_turn, valid usage and
strict visible JSON. Never extract an answer from reasoning or retry a delivered
answer. No automatic retries; any transport/API failure stops collection.

First run all six reviewed resource items on each model (12 requests). Delivery
qualification requires 12 recognized answers, irrespective of correctness.
Then run all twelve calibration items twice on each model (48 requests).
Complete behavioral nonanswers stay unknown and do not halt calibration; true
transport, identity, usage or budget failures halt it. Analyze only a complete
48-slot cohort. Reserved questions are untouched. The six template families and
two repeats are development data, not 48 independent reasoning mechanisms.
Claude also assisted earlier item review; this is not independent model-family
validation or a held-out safety evaluation.

Before paid inference, count tokens for each exact unique request with the free
count_tokens endpoint. Require count <=3000 and reserve 4000 input tokens plus
128 output tokens per request, with no retries. Pricing is $1/$5 per million
input/output tokens for Haiku and $3/$15 for Sonnet. Reserve all 60 requests
($0.5568) on top of the prior conservative $0.321789833 bound, below $1.
Compute new spending from reported usage at these rates; missing usage retains
the entire reservation. Unexpected cache/tool usage halts collection.

Difficulty criterion fixed before collection: each model recognized-answer
accuracy between .55 and .90, at least one factual error, and <=5% nonanswers.
Report correct/planned, recognized accuracy, unknowns and factual bounds.
If either model fails, this pair does not qualify for the planned advice study;
do not claim the fallible-evidence instruction works or fails. A future advice
experiment requires its own frozen design and budget. Original study stays paused.

Sources: [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs),
[token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting),
[pricing](https://platform.claude.com/docs/en/about-claude/pricing).
