# Wording pilot stops at 126 attempts on an upstream rate limit

Executed October 22 Boise / October 22–23 UTC, 2026. **The pilot stopped at
126 of 288 planned attempts when gpt-oss/DekaLLM returned HTTP 429.** There
were 125 recognized answers and one provider error. The other 162 requests
remain unsent. Factual accuracy and wording/advice effects were not inspected.

## What was launched

The user authorized the full pilot after the separate sixteen-call resource
qualification passed. A new deployment version preserved all twenty-four
independently reviewed variants on eight underlying questions, two repetitions,
and absent/correct/wrong suggestions. Qwen was pinned to DeepInfra FP8; gpt-oss
remained pinned to DekaLLM BF16. All 288 exact requests, code, review and
resource prerequisites, settings and analysis rules were frozen before traffic.

Live identity, capacity, parameter, pricing, credit and allowance checks passed.
The full pilot reserve was **$0.22065960**, below the $0.90 pilot ceiling.
Earlier recorded development spending was $0.00340516; that plus the full
reserve remained within the $1 total development ceiling. Requests were serial,
at least five seconds between preparations, temperature 0.7, 2,048 completion
tokens, timeout 180 seconds, fallback off and one attempt per trial.

Collection ran from 23:49:10 UTC on October 22 to 00:06:48 UTC on October 23,
approximately 17 minutes 39 seconds including scheduling and orchestration.
Three complete 36-call question blocks and eighteen calls of the next block
were attempted. No samples, prompts or settings were changed during collection.

## Delivery outcomes

| Deployment | Attempted / planned | Recognized final answers | Upstream rate limits | Strict final A/B | Recorded cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3 / DeepInfra FP8 | 63/144 | 63 | 0 | 28 | $0.00595476 |
| gpt-oss / DekaLLM BF16 | 63/144 | 62 | 1 | 62 | $0.00165384 |
| Total | 126/288 | 125 | 1 | 90 | $0.00760860 |

The thirty-five non-strict Qwen answers were recognized under the existing
permitted final-line forms, such as a letter followed by the exact option text.
They are not retroactively classified as failures or rescued with a broader
parser. Every recognized response had valid expected identity, normal-stop
delivery, base usage/cost and provenance. No refusal, length stop, empty-visible
answer, ambiguous final line, timeout or model/provider mismatch was recorded.

Optional reasoning-token counts exceeded completion counts in eight responses.
Those metadata are preserved without deriving visible token counts, reasoning
effort or competence from their differences. They did not alter the frozen
base-usage/cost/visible-answer contract.

## Why collection stopped

Trial `W05__plain__correct__r1__gpt-oss` returned HTTP 429 and curl exit 0.
The provider error explicitly identifies **DekaLLM** and limit source
`upstream_provider_shared_pool`. It describes gpt-oss as temporarily rate-limited
upstream. No Retry-After header was supplied. This is an operational capacity
failure, not evidence of a reasoning mistake, a Qwen delivery regression or
exhausted account credit.

The first operational failure stopped the version as specified. The failed
request was finalized and preserved; no retry, replacement, provider switch,
token-cap increase, extra sample or subsequent pilot request occurred. A future
separately specified version must observe the minimum sixty-second cooldown
and any applicable server retry guidance.

Recorded new cost is **$0.00760860**, approximately **0.761 cents**. The 429
response has no billed-cost metadata, so the recorded sum is not a billing
reconciliation of that failed request. Combined recorded development spending
across the earlier wording resource run, diagnostics, qualification and this
partial pilot is **$0.01101376**, about **1.10 cents**.

## What the data can support

This run demonstrates that the qualified routes delivered 125 recognized
answers before a DekaLLM capacity failure. Passing a short resource check did
not guarantee uninterrupted delivery of the larger pilot. It does not establish
that any wording or advice condition improved or harmed factual accuracy.

The frozen effect-analysis guard requires all 288 uniquely finalized trials and
operational integrity. The incomplete-cohort guard rejects this run. No pilot
accuracy tables, model ranking, wording contrasts, advice effects or confidence
intervals have been computed from the partial cohort. Do not select the complete
question blocks for a replacement analysis or fill missing cells retrospectively.

The practical next step is to specify bounded capacity-error recovery before
any further collection, with a fixed retry reserve, cooldown/server guidance,
immutable requests and preserved error attempts. Any continuation needs a
separate delivery amendment/version with clear missingness and analysis rules;
the current manifest remains stopped. The original 9,000-call study stays paused.

## Saved records and validation

The [deployment amendment](DEEPINFRA_WORDING_PILOT_AMENDMENT.md) preserves the
original review, scoring and clustered descriptive analysis. Artifacts are under
`results/research_directions/deepinfra_wording_pilot_20261022/`:

- `pilot/manifest.json`: 288 frozen requests, endpoints, reserves and input hashes.
- `pilot/attempts`, `requests`, `raw`, `headers`, `http` and `finished`: exact
  delivery records for all 126 attempted trials, including the error.
- `delivery_summary.json`, `delivery_observations.json` and `DELIVERY_REPORT.md`:
  operational-only audit and the explicit 162-request unsent list.
- `final_status.json` and `final_artifact_hashes.json`: final integrity and guard checks.

All **117 offline tests pass**. Every attempted request/raw/header record and
frozen prerequisite verifies. The stopped-version prepare guard and incomplete
analysis guard reject continuation/inference. Earlier resource, diagnostic,
provider-comparison, wording and v4 artifact locks remain unchanged. No request,
batch or temporary credential configuration remains active.
