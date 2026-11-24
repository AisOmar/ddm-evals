# Bounded recovery of confirmed rate-limit rejections

October 26, 2026, before further model traffic or cohort-accuracy inspection.
The completion phase delivered one new Qwen answer and then received an explicit
HTTP/2 429 from DekaLLM for F008/gpt-oss/repetition 2. The body has error code 429,
no choices and no usage. No Retry-After header was returned. This is a confirmed
rejection, not an unknown or unfavorable model answer. Preserve that failed
attempt unchanged. Its generation lookup returned 404, so cost is not assumed
zero; retain the original $0.00090804 reservation as the missing-cost bound.

Keep eleven existing observations: the original two and nine completed HTTP/2
responses. Resume the same fixed 48-slot cohort through **37 logical slots**:
one recovery of this confirmed rejection, plus 36 unsent slots. Prompts, keys,
models, routing/quantization, HTTP/2 streaming, 4,096-token cap, temperature .7,
180-second timeout, parser and scoring remain fixed. Never retry an answered,
ambiguous-format, refused, capped, empty-completed or uncertain-delivery response.

Allow at most two HTTP attempts per logical slot, counting the preserved original
429 as attempt 1 for F008/gpt-oss. Thus that slot gets only one more attempt.
Future slots may get one retry only after curl exit zero, HTTP 429, matching
provider metadata, body error code 429 and no choices. Limit the whole recovery
to four additional retries including the already-needed recovery: at most
40 new calls (37 base calls plus three possible future retries). Every actual
attempt has its own immutable request/raw/header/final files and reservation.
Accept the first complete behavioral response, including a wrong answer, and
never select a preferred answer across attempts.

After a confirmed rejection honor a valid Retry-After (seconds or HTTP date)
with a minimum 60-second cooldown. A repeated 429 at the per-slot/global limit
is retained as a provider nonanswer and the fixed cohort continues; it is not
relabelled as a model error. Stop on three rejected logical slots for one model
without an accepted response for that model, to avoid dispatching into an outage.
Malformed streams, unknown delivery, identity/cap/budget failures and invalid
cost still stop the entire recovery without retry. This version includes no
new provider or transport candidate and no further retry-limit expansion.

Preserve all earlier stops and amendments. This metadata-directed change occurs
before any calibration accuracy inspection; it is exploratory development, not
an untouched confirmatory experiment. Retain planned denominators, both existing
factual unknowns, every rejection and retry count. Analyze only after all 48
logical slots have a retained final outcome; never count retries as independent
questions. The advice pilot remains blocked by the original Qwen nonanswer warning.

Cumulative reported cost before this recovery is $0.31405262, plus up to
$0.00090804 missing cost on the rejected attempt. New recovery reserve must be
at most $0.10, including all conditional retries, covered by fresh live credit
and allowance checks. Total worst-case focused cost remains below $1. No credit
purchase, silent replacement, option change or original-study restart.
