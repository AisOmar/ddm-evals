# Qwen provider delivery comparison

October 22, 2026. The user authorized testing another Qwen3-32B deployment with
the same visible-answer requirements after the reasoning-control diagnostic did
not qualify any setting. This is a separate bounded comparison, not a retry,
replacement of an earlier response, or pilot restart.

## Provider selection and fixed design

A public endpoint check lists DeepInfra, Tenstorrent and SiliconFlow active for
`qwen/qwen3-32b` in FP8. Select **DeepInfra FP8** (`deepinfra/fp8`) as the alternate
route: it matches the previous quantization and has lower listed base token
prices than the other alternate. This selection uses metadata and previous
operational history, not response accuracy. The prior DeepInfra capacity and
resource issues remain in their original records; listed activity is not a
delivery guarantee. Preserve the selection snapshot.

Compare DeepInfra with a fresh **Tenstorrent FP8** (`tenstorrent/fp8`) cohort on
exactly the same three new questions, two preplanned repetitions each. This
gives **12 calls: six per provider**. Questions cover ordered arithmetic,
equal-distance average speed and contraposition. None is an earlier v4, pilot,
resource or diagnostic stem. They share reasoning templates; no unseen-family
or competence claim is intended. The simple author-checked keys never determine
delivery success or select trials; no independent question-review claim.

Default reasoning configuration only: no reasoning parameter, no `/no_think`,
no custom stops, no structured-output mode. Same user instruction and preserved
visible final-line parser as earlier. Temperature 0.7, cap 2,048 completion
tokens, 180-second timeout. Reverse option order on repetition two and keep it
identical across both providers within a question/repetition. Shuffle provider
order independently per question/repetition with seed 20261022074. Use fresh
independent conversations, serial requests, and at least five seconds between
preparations. Both provider routes and quantizations are explicitly pinned with
fallback disabled; do not automatically move to SiliconFlow if a route fails.

## Preflight and budget

Check both exact deployments live for active status, required parameters,
context/output capacity, all price components, account credit and key allowance.
Pin prompt/completion price ceilings. Use conservative input bounds and reserve
all twelve completion caps. Full reserve must be **at most $0.05**, within the
earlier $1 development ceiling. No credit purchase, unannounced price increase
or cap increase. A preflight older than one hour requires a metadata/budget
refresh that leaves requests unchanged. Save exact requests and code/protocol/
snapshot hashes before the first paid call.

Record reservations before dispatch; preserve requests, raw/partial responses,
headers, HTTP/curl status, expected/returned identities, usage, cost, finish
reason and timestamps. Delete temporary credential configurations after
finalization. Do not overlap collectors.

## Outcomes, stops and decision

For each fixed six-call provider denominator, report recognized visible choices,
strict final-line A/B compliance, empty content, all nonanswer categories,
completion/reasoning token metadata, available elapsed times, and recorded cost.
Recognition permits only the preserved v2 final-line forms: A/B, bold A/B, or
a letter followed by that exact option text. Do not search earlier prose or
hidden reasoning to rescue a response. Factual correctness is separate from
delivery and is not used to qualify a provider.

Complete all fixed trials for behavioral nonanswers, ambiguous formatting,
refusals and length stops; do not replace them. Stop the **whole version** on
HTTP/provider errors, uncertain delivery, identity/schema/provenance/cap failure,
missing/invalid cost, or exhausted budget. Preserve unsent IDs. No retries or
unplanned probes. Honor Retry-After and at least sixty seconds after a 429 before
any future separately specified version.

Only an operationally complete comparison with **six of six normal-stop,
recognized visible answers** for a provider qualifies that route as a candidate
for new resource checks. Report strict formatting separately. If both pass,
report non-reproduction of the earlier intermittent failure; if only DeepInfra
passes, describe a delivery difference on these fixed questions, not proof of
an exclusive root cause. Account for price, timing and backend differences.
No hypothesis tests, accuracy ranking, sustained-reliability claim or overall
safety conclusion follows from six calls per route.

Any subsequent resource gate must be a new version with fresh disjoint probes,
frozen requests and live budget. A passing provider comparison does not launch
the 288-call wording pilot. The earlier failed resource phase and 9,000-call
study remain stopped and paused, respectively.
