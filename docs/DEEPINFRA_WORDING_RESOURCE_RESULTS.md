# DeepInfra and DekaLLM pass the full resource qualification

Completed October 22, 2026. **All 16 fixed calls returned recognized visible
answers with strict A/B final lines.** Qwen3-32B on DeepInfra FP8 and
gpt-oss-120b on DekaLLM BF16 each completed all eight reasoning types. The new
resource gate passed; no 288-call pilot requests were sent in this qualification.

## Review and execution

Eight new probes covered price differences, average speed, conditional
probability, implication, relative time, ratio/difference, intervention, and
successive percentages. Stems were disjoint from earlier questions and
diagnostics; reasoning templates overlap. A fresh-context AI reviewer solved
all eight masked questions before author-key access, saved locked initial
judgments, and agreed with all author answers. There were no blocking issues.
A fractional-token distractor cue on one item was recorded as nonblocking for
this delivery check. This is independent AI review, not human validation.

Fresh endpoint, supported-parameter, capacity, price, credit and key-allowance
checks passed. Exact requests pinned `deepinfra/fp8` and `dekallm/bf16` with
fallback off. All used default reasoning, temperature 0.7, a 2,048-token cap,
180-second timeout, serial dispatch, and at least five seconds between
preparations. No retries or response substitutions occurred.

| Deployment | Recognized final answers | Strict final A/B | Completion-token range | Preparation-to-finalization range |
| --- | ---: | ---: | ---: | ---: |
| Qwen3 / DeepInfra FP8 | 8/8 | 8/8 | 190–534 | 7.31–17.53 seconds |
| gpt-oss / DekaLLM BF16 | 8/8 | 8/8 | 66–252 | 1.21–5.41 seconds |

All calls returned HTTP 200, curl exit 0, normal stops, expected model/provider
identities and valid base usage/cost within the frozen limits. There were no
rate limits, empty answers, format failures, refusals, truncations, timeouts,
missing-cost outcomes or unsent trials. Factual correctness did not determine
the gate, select questions, or change any later evaluation item.

Elapsed times include preparation and orchestration, not isolated generation.
Optional reasoning-token counts exceeded completion counts in two responses,
continuing the accounting issue seen in earlier diagnostics. Raw metadata is
preserved. Those fields were not subtracted to estimate visible token counts,
reasoning effort or factual competence, and did not alter the fixed delivery
criterion.

Recorded new cost is **$0.00094809**, approximately **0.095 cents**, against a
full resource reserve of **$0.01210120** and a $0.10 ceiling. All cost metadata
is present. Combined recorded spending for the earlier failed wording resource
run, reasoning-control diagnostic, provider comparison and this qualification
is **$0.00340516**, approximately **0.341 cents**.

## What the pass permits

This qualifies the selected deployment pair on eight representative development
probes. It does not guarantee sustained availability, establish factual
competence, demonstrate wording/advice effects or validate a safety metric.
Earlier Tenstorrent and other resource failures remain unchanged.

The next step is to prepare the reviewed **288-call wording pilot as a new
DeepInfra deployment version**. Keep the existing reviewed pilot questions and
analysis definitions; obtain fresh live prices/credit, freeze exact requests and
the new routing amendment, and bind this successful resource manifest and
response hashes to its launch gate. Do not resume the failed Tenstorrent
resource manifest or present the old collection as repaired.

The existing pilot runner is still bound to its earlier route and failed
resource gate, so it must not be used to dispatch the new version without that
adaptation and freeze. No pilot or advice calls were made during this resource
qualification. The original 9,000-call study stays paused.

## Saved evidence

The [frozen qualification protocol](DEEPINFRA_WORDING_RESOURCE_PROTOCOL.md)
describes the review, budget, deployment, output and stopping rules. Artifacts
are under `results/research_directions/deepinfra_wording_resource_20261022/`:

- `packet.json`, `review/`, `packet_hashes.json` and `design.json`: new fixed
  questions, masked packet, cohort definition and provenance.
- `independent_review/`: locked independent judgments and author comparison.
- `resource/`: frozen manifest, exact requests, reservations, raw responses,
  headers, HTTP records and finalizations for all sixteen calls.
- `REPORT.md`, `summary.json` and `observations.json`: gate, cost and per-trial
  resource outcomes, without factual-effect inference.
- `final_status.json` and `final_artifact_hashes.json`: final integrity checks.

All **113 offline tests pass**. New input and response hashes verify, earlier
provider/diagnostic/wording/v4 locks remain unchanged, and no inference request
or temporary credential configuration is active.
