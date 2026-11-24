# Delivery changes tested; live calibration remains incomplete

October 26, 2026. **The client now captures and validates streaming responses,
but the tested live deployments still do not reliably supply usable answers.
No complete baseline calibration or instruction/advice-effect result exists.**
No request or collector is currently active.

## Current status

| Work | Result |
| --- | --- |
| Question review | All 30 covered; nine disputes resolved with independent calculator-assisted AI review |
| Original HTTP/2 resource qualification | 12/12 recognized, complete responses |
| Original calibration | 18/48 distinct slots attempted; 13 recognized answers, two provider nonanswers, two uncertain deliveries and one format nonanswer |
| Alternate pair qualification | Three logical slots attempted through four HTTP calls; two recognized answers and one complete stream with no visible final answer |
| Alternate calibration | Not launched; qualification did not pass |
| Advice experiment | Not launched |

The original calibration has 30 unsent slots. Its thirteen recognized answers
are not thirteen known correct answers: factual cohort accuracy has not been
analyzed. Neither incomplete cohort can answer the intervention question.

## Implemented and verified

The new client requests explicit streaming and saves all SSE bytes and headers.
It reconstructs visible text separately from reasoning, requires consistent
generation/provider/model identity, completion markers and usage/cost records,
and rejects incomplete or error streams. It handles comment heartbeats and the
repeated terminal accounting frame described in the [official OpenRouter
streaming reference](https://github.com/OpenRouterTeam/docs/blob/main/api_reference/streaming.mdx).
It never extracts an answer from reasoning or changes the frozen answer parser.

Unbuffered HTTP/1.1 streaming delivered three probes but the fourth timed out
mid-reasoning. Its billing was reconciled through generation metadata; the
missing answer was not recovered. A separately frozen HTTP/2 version then passed
all twelve resource slots. Actual HTTP/2 negotiation is recorded from response
headers, not inferred from the requested curl flag.

The original calibration resumed only previously unsent slots, preserving the
first answer and missing response. One complete Qwen response failed the frozen
format contract; its factual result stayed unknown. A documented completion
version retained complete behavioral nonanswers and kept transport failures
fatal. It then encountered an explicit DekaLLM 429 rejection.

A bounded recovery retried only confirmed, answer-free HTTP 429 rejections,
honoring minimum 60-second cooldowns. Every rejected attempt remains saved.
Wrong answers and delivered nonanswers were never retried. DekaLLM accepted
some subsequent calls, but another Qwen stream later timed out. That recovery
stopped without retrying the uncertain stream. The original study remains paused.

## Separate alternate-deployment qualification

An available pair was frozen prospectively: gpt-oss/AkashML BF16 and
Qwen/Tenstorrent FP8, with the same questions, HTTP/2 transport, temperature .7,
4,096-token cap and 180-second timeout. Old observations were not pooled with
this pair. Quantization labels do not establish identical serving behavior.

AkashML initially rejected a request with 429, then supplied a recognized answer
on its one bounded retry. The first Qwen probe also supplied a recognized answer.
The next Qwen probe returned a complete, normally terminated stream with valid
usage/cost, but **zero visible answer characters**. Reasoning was present and was
not used to rescue an answer. This failed the resource answer-delivery gate;
nine resource slots and all fresh calibration requests remain unsent.

These observations distinguish client stream handling, provider availability,
model final-channel behavior and strict formatting. They do not prove a single
root cause, show that either model cannot solve the questions, or establish
selective reliance or overall safety.

## Costs and integrity

Focused development has **$0.3172 reported/reconciled spending**. Five confirmed
rejection attempts still lack billing records; their full reservations total
$0.004625032. Including those reservations gives a conservative cumulative upper
bound of **$0.3218**, below the unchanged $1 ceiling. A 404 generation lookup is
not treated as proof of zero cost. No credits were purchased.

All **170 offline tests pass**, covering interrupted/error streams, accounting
frames, identity checks, answer-channel separation, HTTP negotiation, retention
of unknowns and bounded rejection handling. Earlier manifests and scoring remain
unchanged. The 210 preparation-protected files and previous locked launch records
verify. Current incomplete attempts, empty outputs, missing-cost bounds and
unattempted slots are preserved. No hidden answer replacement or primary rescoring.

## What remains

A usable model deployment must first demonstrate both complete stream delivery
and a visible final answer under the fixed budget. The two tested pairs did not
remain usable through calibration. A further deployment or model change needs
its own prospective qualification and separate calibration data; do not quietly
fill this incomplete cohort with responses from another backend.

Even after reliable delivery is obtained, the full baseline cohort must establish
actual factual mistakes and room for helpful advice. Only then can the explicit
fallible-evidence instruction be tested. At present the main research question
is still unanswered.

- [Current status](../results/research_directions/selective_reliance_focus_20261024/alternate_http2_20261026/final_status.json)
- [Empty-visible-answer diagnostic](../results/research_directions/selective_reliance_focus_20261024/alternate_http2_20261026/visible_answer_diagnostic.json)
- [Billing reconciliation and missing-cost bounds](../results/research_directions/selective_reliance_focus_20261024/delivery_reconciliation_20261026/reconciliation.json)
- [Streaming recovery protocol](SELECTIVE_RELIANCE_STREAM_RECOVERY.md)
- [HTTP/2 qualification protocol](SELECTIVE_RELIANCE_HTTP2_RECOVERY.md)
- [Bounded rate-limit recovery protocol](SELECTIVE_RELIANCE_RATE_LIMIT_RECOVERY.md)
- [Separate-deployment protocol](SELECTIVE_RELIANCE_ALTERNATE_DEPLOYMENTS.md)
