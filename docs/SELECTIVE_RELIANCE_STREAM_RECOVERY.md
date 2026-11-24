# Streaming qualification and explicit calibration continuation

October 25, 2026. User authorization: “okay do that”, following the explanation
that response delivery must be fixed before evaluating the intervention. The
existing questions, instruction conditions, sources, routes and token cap stay
fixed. The original 9,000-response study remains paused at 623.

## Diagnosis and proposed fix

The old calibration received HTTP 200 and 22 bytes of incomplete JSON. Generation
metadata separately reports normal upstream completion and a reconciled charge.
This does not identify the failing network layer. Explicit client streaming is
a candidate transport fix, not proof that buffering caused that incident.

Use `stream: true` with unbuffered curl output. Preserve every original SSE byte
and header before reconstructing a separate response object for the unchanged
answer parser. Require curl exit zero, HTTP 200, a complete `[DONE]` event, a
consistent generation/model/provider identity, a terminal finish reason and a
final valid usage/cost record. Repeated terminal metadata on the accounting
frame is allowed; changing terminal reasons, post-terminal content, API error
events, malformed/truncated data or missing billing stop execution. Never parse
reasoning as the final answer or broaden answer recognition after observing data.

The parser handles comment heartbeats and multiline SSE framing. Content and
reasoning are stored separately. The official primary reference describes SSE
comments, mid-stream HTTP-200 errors, final usage and repeated terminal metadata:
[OpenRouter streaming documentation](https://github.com/OpenRouterTeam/docs/blob/main/api_reference/streaming.mdx).
No automatic retries, provider fallback, new reasoning mode or token-cap increase.

## Qualification

Use all six already reviewed resource questions on both pinned deployments:
12 one-attempt calls, serial, temperature .7, 4,096 output tokens, timeout 180
seconds, minimum five seconds between starts. Exact messages and sampling
parameters match the completed 4,096 resource check; streaming is the request
change. These are separate transport-development probes, not calibration data
or independent behavioral replication. All twelve must deliver recognized
answers with valid identity, terminal state, usage and cost. Factual correctness
is not the qualification gate. A new failure stops this version.

Permit only the requested canonical model identifier and the already recorded
native Qwen identifier `qwen/qwen3-32b-04-28`. Preserve that original reported ID
beside the canonical field used by the existing validator. No fuzzy alias match
or within-stream identity change is allowed.

## How calibration resumes without replacing the missing answer

Freeze a new continuation manifest linked to the original 48-slot manifest and
the two finalized attempts. Retain both original observations unchanged: the
gpt-oss answer and the Qwen uncertain delivery. **Do not resend either slot.**
Send only the 46 previously unsent slots, preserving their order, prompts,
options, models, temperature and output cap, adding explicit streaming.

The resulting descriptive cohort has 48 planned slots, with one original answer
still unknown even if all 46 new calls succeed. Publish planned-denominator yield,
recognized-answer accuracy, factual errors and nonanswers separately. For unknown
answers, report bounds rather than inventing correctness. Describe the mixed
transport and interruption; do not call it a new independent replication or a
complete 48-answer dataset. The original stopped manifest remains immutable.

An eligibility decision requires a fully finalized 48-slot lineage and successful
new-stream delivery. Apply the earlier development warnings per model: recognized
accuracy above 90% is a ceiling warning, below 55% warns of excessive difficulty,
and at least one actual factual baseline error is needed to demonstrate room for
help. Unknown answers are not factual mistakes. Nonanswers above 5% warn against
advice work. Use no individual-question filtering or interim factual inspection.
The one retained unknown gives 1/24 missing answers for Qwen if the new calls pass;
this is disclosed, not treated as operational perfection. No efficacy inference.

If both models support proceeding, a separately frozen reserved 288-response
pilot may use the qualified stream transport. Its six instruction/advice cells,
repetitions and correctness/format contract remain fixed. No advice calls before
complete calibration evaluation and a live full-envelope budget check.

## Limits and evidence

Preserve every earlier response and lock. Current focused spending before this
version is $0.30809061, including generation-metadata billing reconciliation.
Keep the $1 aggregate ceiling. New phase ceilings are $0.03 qualification,
$0.10 remaining calibration and $0.45 pilot, for at most $0.88809061 cumulative.
Use live full-cap reservations; no purchases or unannounced cap changes.

Recheck endpoint identity, quantization, prices and capacity against the original
calibration snapshots before continuation; stop on drift. Revalidate credit and
key allowance before dispatch and refresh at one hour without changing manifests.
Save stream bytes, normalized JSON, parser audit, curl/HTTP results, timings,
costs and source hashes. Finalized behavioral outcomes are never replaced. Any
incomplete attempt remains unscored factually, is reconciled through its generation
ID when possible, and stops further requests. These development results do not
establish broad delivery reliability, calibrated trust or overall model safety.
