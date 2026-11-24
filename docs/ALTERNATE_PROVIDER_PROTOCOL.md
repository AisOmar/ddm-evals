# Separate alternate-provider delivery check

The user authorized testing another gpt-oss provider, independent question review
and then a small no-advice calibration if readiness gates pass. This is a new
operational version, not a retry or fill-in of either earlier DeepInfra run.

Use gpt-oss-120b on **DekaLLM BF16** and Qwen3-32B on **DeepInfra FP8**. The
gpt-oss provider change alters the evaluated deployment; retain the explicit
provider distinction in every subsequent report. Backend/weight revisions remain
incompletely identified. No claims transfer automatically from earlier providers.

Reuse the six frozen arithmetic questions per model (twelve requests), but put
gpt-oss first in each pair so an unavailable alternative fails early. Request
temperature zero, 512 maximum completion tokens, at least twenty seconds between
preparations, exact endpoint routing and no provider fallback. No automatic
retries or substitution to additional providers occur. A failure stops the run.
At most $0.10 of full-cap conservative cost is authorized for this check.

Script 58 extends the already tested canary ledger/serial guards without changing
the frozen scripts. It requires fresh live pricing, capacity, credit and key
allowance checks. Input-cache-read pricing is allowed only when nonnegative and
no higher than ordinary prompt pricing; the reserve charges every bounded input
token at the full ordinary rate. Unknown nonzero charges and cache surcharges
are rejected. Freeze exact requests, prices, endpoint snapshots, source hashes
and this protocol before inference. All twelve recognized correct responses,
normal stops, valid identities/usage/costs and per-attempt budget compliance are
required to pass. Strict formatting is reported separately.

The provider response's real identity is checked before adapting a copy for the
legacy schema validator. Raw responses are never rewritten. Preserve request,
response, headers, HTTP status, ledger and costs even on failure. Remove private
curl configs after use. Do not overlap another collector. Respect server retry
delays on any future separately authorized version; this version never retries.

Routing uses endpoint tags with `order`, `only`, `allow_fallbacks: false` and
quantization filters, as described in the current
[OpenRouter provider-selection documentation](https://openrouter.ai/docs/guides/routing/provider-selection).

The independent review receives only the two current masked semantic-revision
files in a fresh context. It must save and lock answers and judgments before
author-key comparison. It is AI review, not human expert validation or independent
training. Adjudicate disagreements before any harder-question calls. A passed
canary alone does not authorize skipping review or demonstrate reliable sustained
delivery. The later calibration requires its own reviewed packet/request freeze,
full-cap budget and complete analysis contract. It remains separate from the
paused original 9,000-call study and cannot establish a safety metric by itself.
