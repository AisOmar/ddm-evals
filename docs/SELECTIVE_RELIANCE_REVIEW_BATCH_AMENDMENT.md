# Review batching amendment — October 24, 2026

Recorded after the initial masked review ended at its 12,000-token cap and
before further reviewer or evaluated-model traffic. The initial paid attempt
returned HTTP 200 with a length termination, costing $0.063988. It is incomplete
and ineligible for key adjudication or the review gate. Preserve its raw body,
request, delivery failure and headers unchanged. No original review request is
retried or overwritten.

The revised review is a new three-request protocol: each request sees the same
30 masked questions to assess cross-item relationships, and independently solves
exactly ten designated IDs. Each has its own fresh context with no previous
review response, author keys, solutions, model outcomes or authoring context.
The response schema limits derivations to 35 words and concerns to 20 words.
Each request has a 4,000-token cap and 180-second timeout, at temperature zero,
using the same live-priced Anthropic/Claude Haiku 4.5 route, fallback disabled.
Run batches serially, once each, with no within-version retry.

Freeze all three exact requests before dispatch. Bound their summed full-cap
reserve plus the first attempt's recorded charge at **$0.35**. New phase ceilings
are review $0.35, resource $0.10, calibration $0.25 and advice pilot **$0.30**,
maintaining the **$1.00 total**. The pilot's current live-price envelope is
approximately $0.2442, so the smaller ceiling still covers that draft; check
again at execution. No sample size, evaluated-model prompt, question, key,
advice condition, scoring rule or original study state changes.

Lock all three raw responses and initial judgments before comparing any keys.
Require complete nonduplicated ID coverage and agreement on every uniquely
supported key, with no execution blockers. Do not discard a review batch or
substitute a preferred judgment. A new failure stops this review version.
Cross-item dependence concerns remain explicit development limitations; do
not count all 30 questions as independent content families.

This changes review delivery after a resource failure, not a result-based
selection rule. Neither the failed review nor the replacement review is an
independent behavioral replication. Any eventual report must disclose both.
