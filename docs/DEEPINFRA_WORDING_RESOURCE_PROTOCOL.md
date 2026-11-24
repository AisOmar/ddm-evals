# DeepInfra wording resource qualification

October 22, 2026. The user authorized the next full resource check after
Qwen/DeepInfra FP8 passed its six-call provider diagnostic. This is a new
qualification with eight fresh probes, not a retry of any earlier failed cell.

## Fixed probes and independent review

Eight short questions cover the wording pilot's eight reasoning types: a price
sum/difference, equal-distance average speed, conditional probability, quantified
implication, relative time, ratio/difference, structural intervention, and
successive percentage changes. There are three plain, two neutral and three
candidate-trap wordings. All stems are disjoint from prior v4, wording-pilot,
resource and diagnostic stems, while sharing their reasoning templates.

Author arithmetic/logical checks support one answer per question. Before live
requests, a fresh-context AI reviewer independently solves all eight anonymous
masked items, checks both options and assumptions, and saves SHA256-locked
judgments before author-key comparison. All eight require matching supported
answers and no unresolved blocker. Any repair requires a preserved new version
and separate validation. This is independent AI review, not human expertise or
an empirical difficulty assessment. Factual correctness never selects probes
or determines resource success.

## Deployments and exact limits

Send each fixed resource item once to each deployment, **16 maximum calls**:

| Model | Provider tag | Quantization |
| --- | --- | --- |
| `qwen/qwen3-32b` | `deepinfra/fp8` | FP8 |
| `openai/gpt-oss-120b` | `dekallm/bf16` | BF16 |

Pin these exact tags and disable fallback. Default reasoning, no `/no_think`,
no custom stops, no structured-output mode. Retain the existing concise A/B
final-line instruction and parser from script 54. Temperature 0.7, completion
cap 2,048, timeout 180 seconds, serial requests, at least five seconds between
preparations. One attempt per trial. Shuffle question order with seed
20261022077 and alternate model order between question pairs. Model requests
show only one question and its options, without IDs, keys, families or other
questions.

## Preflight, preservation and budget

Live metadata, supported parameters, context/output capacity, all price
components, account credit and key allowance must pass before freezing traffic.
Pin live prompt/completion price ceilings. Conservatively reserve all prompt
inputs and completion caps, reject unknown nonzero fees and cache prices above
the full prompt bound, and keep the total reserve **at most $0.10**, within
the prior $1 development ceiling. No credit purchase, cap escalation or price
increase. Refresh a preflight older than one hour without changing requests.

Freeze the packet, independent review, exact requests, code/protocol hashes,
endpoint snapshots and budget before the first call. Save a reservation before
each dispatch, plus raw/partial responses, headers, HTTP/curl status, identity,
finish reason, usage, recorded cost and timestamps. Delete temporary credential
configs after finalization and prevent collector overlap. Preserve all earlier
resource failures, diagnostic outputs and manifests unchanged.

## Gate and stopping rule

Require **16/16 normal-stop responses with recognized unambiguous visible
choices**, correct deployment identity, valid base usage/cost within the frozen
limits, and exact provenance. Strict final-line A/B compliance is reported
separately; the preserved parser also accepts bold A/B and a letter followed
by the exact corresponding option text. Never search hidden reasoning or earlier
prose to rescue a missing/malformed final line. A recognized factual wrong answer
does not fail the gate or permit item replacement.

Stop this whole resource version on the first refusal, length stop, incomplete
or ambiguous output, rate limit, HTTP/provider/transport error, uncertain delivery,
identity/schema/provenance/cap failure, missing/invalid cost or budget failure.
Record unsent IDs. No retries, cell replacement, provider substitution or extra
probes. Honor Retry-After and at least sixty seconds after a 429 before a future
separately specified version. HTTP 200 alone does not guarantee a completed answer.

Optional reasoning-token counts are reported verbatim. Previous diagnostics
found counts exceeding completion counts on both Qwen deployments. Do not
derive visible token counts, reasoning effort or difficulty by subtracting them.
Report any new inconsistencies separately from the base-usage/cost/visible-answer
gate; do not introduce a retrospective outcome rule.

## Report and subsequent decision

Report every attempted trial and unsent ID, recognition/strict-format counts,
all outcome categories, completion-token and elapsed-time summaries, optional
reasoning metadata issues, recorded cost and missing-cost records. Elapsed time
is preparation to finalization, not isolated generation time.

A pass qualifies only this particular deployment pair and these representative
probes. It does not prove sustained reliability, factual competence or a safety
metric. If it passes, the reviewed 288-call wording pilot can be prepared as a
new DeepInfra deployment version with fresh preflight, exact request freeze,
budget and completeness guard. **This task executes only the 16-call resource
qualification; it does not automatically launch the pilot.** The original
9,000-call study remains paused. A failure preserves this cohort and blocks
pilot preparation under this qualification.
