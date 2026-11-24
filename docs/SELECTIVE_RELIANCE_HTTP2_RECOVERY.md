# HTTP/2 streaming qualification

October 25, 2026. Explicit HTTP/1.1 streaming delivered three complete probes,
then stopped on a fourth request: curl exit 28, HTTP 200, a 109,352-byte partial
stream, no visible answer, terminal reason, usage frame or `[DONE]`. The strict
parser correctly rejected it. Generation-ID metadata reports DekaLLM normal
completion and $0.00013107 cost. That reconciles billing but cannot recover an
answer. It does not prove a particular client, gateway or provider caused the
interruption. Preserve all four attempts and eight unsent probe slots.

The three complete probes cost $0.00046547. Total first-version qualification
cost, including metadata reconciliation, is $0.00059654. Cumulative focused
development spending is $0.30868715 before this version.

Local curl 8.7.1 advertises HTTP2 via nghttp2. Test **one separately versioned
HTTP/2 streaming transport** with the same twelve resource requests. Only the
curl HTTP protocol changes: remove the forced `http1.1` option, require `http2`,
and retain unbuffered SSE output. Require the actual saved response status line
to confirm HTTP/2; automatic negotiation to HTTP/1.1 does not pass. Preserve raw
status/header evidence. The SSE parser, terminal/usage requirements, factual
scoring, model/provider/quantization, messages, temperature .7, 4,096-token cap,
180-second timeout, five-second minimum start interval and one attempt per slot
remain fixed. No factual outcome was inspected to choose this transport.

Run all twelve probes in the predeclared order and require twelve successful
deliveries. Repeated resource exposure is transport development, not independent
replication. No filling the failed HTTP/1.1 probe cohort. A failure stops this
version; no automatic retry, parser relaxation or further transport candidate.

If qualification passes, use the same HTTP/2 transport for only the 46 originally
unsent calibration slots. Retain the original two observations and missing answer
exactly as specified in the streaming recovery protocol; do not resend either.
All subsequent calibration and advice gates remain unchanged.

Keep the $1 aggregate ceiling. Allocate at most $0.03 to qualification, $0.10 to
the remaining calibration and $0.45 to the conditional advice pilot. Including
all previous reported/reconciled costs, the maximum remains $0.88868715. Refresh
live endpoints, price/capacity, credit and allowance before calls; stop on drift.
No purchase or old-study restart. Preserve the stopped first-stream version and
its immutable request/response records in their original directory. The new
directory is `http2_stream_20261025` beside it.
