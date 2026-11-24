# Delivery gate stopped: gpt-oss shared-pool rate limit persists

Executed October 20 Boise / October 21 UTC, 2026, following the user's request
to continue. **The live delivery gate failed.** Serial scheduling did not prevent
the gpt-oss endpoint's upstream 429. No harder-question calibration was started.

## Attempts and accounting

The frozen design had twelve trivial arithmetic requests: six per model, with
DeepInfra only, pinned quantizations and live price ceilings, temperature zero,
512 completion tokens, serial dispatch and a minimum twenty-second preparation
interval. The live full-cap reserve was **$0.004651380**, below the $0.10 ceiling;
account credit and key allowance covered that full reserve. Preflight passed
before either inference request.

| Attempt | Deployment | HTTP/outcome | Correctness | Strict final format |
| --- | --- | --- | --- | --- |
| Qwen3, canary 1 | DeepInfra FP8 | 200, answered | Correct, A | Yes |
| gpt-oss, canary 1 | DeepInfra BF16 | 429, upstream rate limit | Unscored | Unscored |

Both attempts are finalized. The other ten planned requests were **not sent**.
There were no retries, provider/model substitutions or original-study requests.
The preparations were 26.53 seconds apart. The first failure stopped the version
as specified; no further paid configuration remains active.

The provider error names DeepInfra and reports `engine_overloaded`, with limit
source `upstream_provider_shared_pool`. This is not evidence of a reasoning
failure or an exhausted account balance. Public endpoint metadata still marks
the endpoint active; that status does not guarantee capacity for a request.
No Retry-After header was supplied. The protocol's minimum sixty-second future
cooldown applies, but this run does not retry after that delay.

Recorded cost is **$0.00004188** for Qwen's successful response. The 429 has no
cost metadata, so this sum is not a billing reconciliation of the failed
request. The full reserve remains recorded. Raw bodies, response headers, HTTP
codes, immutable requests, endpoint snapshots, and attempt/finalization records
are under `results/research_directions/reliance_calibration_v2/delivery_canary/`.
Credential-bearing curl files and temporary account responses were removed.

## Question audit and the current review packet

The same author parsed and solved the visible wording of **all 48 candidates**,
checking both options and comparing with the saved keys. Each visible stem has
one computationally matching alternative. This is an **unblinded author audit**,
using the existing author solvers, not a separate independent review.

The audit caught twelve probability stems asking for an exact fraction while
the planned response instruction asks for a letter. A new append-only
`semantic_revision/` changes those endings to ask which option gives the exact
posterior probability. Keys, options, parameters and splits remain unchanged.
Both earlier drafts and their locks are preserved. The previous denominator
repair remains in effect.

Use these current masked files for a separate reviewer:

- `results/research_directions/reliance_calibration_v2/semantic_revision/calibration_masked_review.json`
- `results/research_directions/reliance_calibration_v2/semantic_revision/reserved_masked_review.json`

Follow the masked-review procedure in
[the review instructions](RELIANCE_CALIBRATION_REVIEW.md), using the paths above
instead of the earlier `review_revision` files. The author audit, complete
solution packet and revision logs disclose keys and must stay out of that
reviewer's initial context. Empirical difficulty remains unknown; recurrence,
subset-counting and fraction tasks may mainly impose computation demands. Four
shared templates do not create 48 independent task families.

## What must change before calibration

The serial DeepInfra setup has not passed its delivery gate. Do not resume its
remaining requests or begin the 96-call calibration design automatically. A
separate operational version must address gpt-oss capacity and pass a new
bounded canary before calibration.

Read-only public endpoint snapshots were saved after the stop. They list other
BF16 gpt-oss deployments, including DekaLLM, AkashML and Crusoe. None was probed
with inference and none is validated as a substitute. Several introduce explicit
cache pricing fields that the current conservative runner rejects; a future
version must account for those charges before execution. Changing provider also
changes the deployment being evaluated. These observations are planning inputs,
not permission to reroute this frozen run or evidence that another endpoint will
be reliable.

Independent semantic review, a passed live delivery check, live full-budget
verification and a frozen calibration request manifest remain required. No new
safety-metric claim or sample-size conclusion follows. The original 9,000-call
study remains paused.

## Verification

All **71 offline tests pass**. Both canary attempts match their frozen requests,
saved responses and final outcomes; all prior packet locks and the 16,919-file
earlier-artifact snapshot verify. No batch or private canary configuration is
active. Script 56's guards reject further preparation after the failed canary.
Scripts 50 and 54 and the original 192-attempt scores remain unchanged.
