# Bounded capacity recovery for the fixed wording pilot

October 22 Boise / October 23 UTC, 2026. The user authorized defining bounded
rate-limit recovery and continuing the interrupted 288-trial pilot. This
prospective delivery amendment is frozen before further inference and before
any factual accuracy or treatment-effect inspection. It changes delivery only.

## Preserved observations and requests

Keep the original DeepInfra pilot manifest and all 126 attempt records unchanged,
including the DekaLLM shared-pool HTTP 429. Retain its 125 valid delivered
responses, whether factually right or wrong, without repeating them. There are
163 unresolved logical trials: the explicitly rejected request plus 162 unsent
requests. Keep every exact request body, model/provider/quantization, prompt,
answer order, temperature, token cap, timeout and analysis endpoint unchanged.
No new questions, provider switches, output-parser changes, preferred-answer
replacement, sample extension or original-study restart.

Continue in original manifest order, first resolving the failed slot. New
attempts receive unique ledger IDs and separate request/raw/header/finalization
paths under a new recovery directory. Each body must equal its original logical
trial request exactly. A complete response, including refusal, truncation,
incomplete normal-stop text or ambiguous formatting, ends that logical trial
and must never be retried for a better answer.

## Exactly which failures can be retried

Retry only a completely received HTTP 429 response with curl exit zero, a parsed
JSON error code 429 and metadata identifying the expected provider. If cost is
reported it must be valid and within that attempt's full reserve. A missing cost
on this explicit rejection is permitted for recovery but remains missing, with
its maximum reservation retained as potentially billed. The rejected request
is not a behavioral model response. The original known 429 meets this rule.

Stop on uncertain delivery, timeouts, other HTTP/API errors, unexpected identity,
malformed error bodies, schema/provenance/cap violations, invalid reported cost,
or missing cost on a delivered model response. Do not retry those outcomes.
Never use a letter found in reasoning to manufacture a visible answer.

For a retryable rejection, wait at least **60, 120, then 240 seconds** after
the first, second and third failed attempts on that logical trial, counting
the original failed attempt. Honor a longer valid Retry-After, whether numeric
seconds or an HTTP date. Preserve the header and parsing outcome. A delay that
would exceed the time budget blocks further dispatch. Invalid/missing guidance
uses the fixed backoff; it is never shortened. All other starts remain serial
and at least five seconds apart.

The HTTP-date/seconds interpretation follows
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after).
[OpenRouter's error documentation](https://openrouter.ai/docs/api/reference/errors)
also describes Retry-After guidance for rate limits. Acceptance of a request is
still determined from the actual saved response, not public endpoint status.

## Hard bounds and live checks

- At most **four total attempts per logical trial**, including the original
  attempt where present; therefore at most three retries for any trial.
- At most **20 new retry attempts globally**, counting the first recovery of
  the old rejected request. There are at most 162 new first attempts plus 20
  retries: **182 new calls maximum**. Stop the version when a required next
  attempt would exceed either bound; do not skip that trial to alter allocation.
- Retry full-cap reserve at most **$0.05**; total new recovery reserve at most
  **$0.90**. Earlier recorded development charges plus the unresolved original
  error's full-cap reservation plus the new reserve must fit the original
  **$1.00 development ceiling**. No credit purchase or price increase.
- At most **two hours from recovery-manifest creation**, including cooldowns.
  Waits and server guidance never extend this cap automatically.

Conservatively reserve each of the 162 still-unsent first attempts and twenty
retries at the maximum original per-request bound. Retain all attempt reserves
for budgeting, including errors without cost metadata; never treat those as
zero billing. Record actual reported charges separately from reservations.

Before freezing and every hour during collection, check exact endpoint identity,
quantization, parameter support, context/output capacity, all prices, credit
and key allowance. Require original relevant endpoint/pricing metadata to match;
pin the unchanged request price ceilings. Fresh live checks and full reserves
must pass. Freeze code, amendment, original manifest/snapshot, retained response
hashes, retry policy, budget and request bodies. Prevent overlapping collectors
and remove temporary credential configs after each attempt or refresh.

## Completeness and analysis

Exactly one valid delivered response per original logical trial is required for
the final 288-trial analysis. Validate every retained and new response, every
request identity/hash, attempt count, retry eligibility, cooldown and budget.
Preserve all rejected attempts and their cost uncertainty in separate accounting.
Do not count an HTTP 429 as an incorrect behavioral response or omit it from the
delivery report. Audit the final chosen response's lineage for each logical ID.

Use the unchanged scoring and statistical calculations in script 69: the same
eight problem clusters, 10,000 bootstrap draws and seed, endpoints and pointwise
intervals. No interim factual/contrast inspection, exclusions, new hypotheses,
pooling with other experiments or post-result repair. Report that collection
spans an operational pause and a metadata-only delivery amendment. All errors,
retry allocation, nonanswers, strict formatting and missing costs stay visible.
If bounded recovery stops short, reject effect inference again.
