# Alternate Qwen provider passes the small delivery check

Completed October 22, 2026. **DeepInfra FP8 returned recognized visible answers
on all six planned calls.** A fresh Tenstorrent FP8 comparison also passed six
of six on exactly the same new questions and settings. The earlier intermittent
missing/malformed-answer failures were not reproduced in this cohort. No
exclusive provider cause or permanent fix is established.

## What ran

Twelve fixed calls: three new questions × two repetitions × two providers.
The two routes served `qwen/qwen3-32b` in FP8. Both used the same prompt text,
temperature 0.7, 2,048-token cap, 180-second timeout and preserved final-line
parser. Provider order was randomized within each question/repetition, option
order reversed on repetition two, and fallback was disabled. No reasoning
disable field or `/no_think` was used.

DeepInfra was selected from a saved live public snapshot because it matched the
previous FP8 quantization and had the lowest listed base token prices among the
active alternates. Fresh endpoint, parameter, context/output, price, credit and
key-allowance checks passed. The full twelve-call reserve was $0.01510896 under
the $0.05 ceiling. Earlier DeepInfra operational failures remain preserved.

| Deployment | Recognized final choice | Strict A/B final line | Empty visible content | Recorded cost |
| --- | ---: | ---: | ---: | ---: |
| Qwen3 / DeepInfra FP8 | 6/6 | 3/6 | 0/6 | $0.00050956 |
| Qwen3 / Tenstorrent FP8 | 6/6 | 4/6 | 0/6 | $0.00067060 |

Recognition includes the already-allowed final line containing a letter followed
by its exact option text. Strict formatting requires the final line to be only
`A` or `B`. No parser changes or extraction from hidden reasoning were used.
Correctness did not select or qualify trials; this is not an accuracy comparison.

All twelve calls had HTTP 200, curl exit 0, normal stops, expected model/provider
identities, nonnegative prompt/completion counts below the completion cap, and
cost metadata within the frozen reserves. No rate limits, refusals, timeout,
truncation, retry, provider substitution or missing-cost outcome occurred.

Completion-token counts ranged from 134 to 509 on DeepInfra and 142 to 376 on
Tenstorrent. Preparation-to-finalization times ranged from 6.08 to 21.48 seconds
and 3.68 to 8.16 seconds respectively. These elapsed times include orchestration
and are not isolated model-generation-time measurements or a speed benchmark.

## Reasoning-token accounting limitation

For both logical-contraposition repetitions on both providers, the reported
reasoning-token count exceeded the reported completion-token count: four of
twelve responses. Exact pairs, in completion/reasoning order, are 228/249 and
316/356 on DeepInfra, and 269/299 and 273/295 on Tenstorrent. These optional
metadata counts are inconsistent with treating reasoning as a subset of that
same completion count. The records alone do not identify a tokenizer, provider
or gateway accounting cause.

Raw counts remain unchanged. They were not used to infer visible token counts,
answer correctness or reasoning effort. The fixed delivery criterion uses
actual visible content; conservative spending and cap checks use the reported
base usage and recorded cost. A future token-effort analysis needs an explicit
validated measurement contract and must not silently subtract these fields.

## Decision and limits

DeepInfra qualifies as a candidate for a **new resource gate** under the fixed
six-of-six delivery rule. Tenstorrent also meets that rule in this fresh cohort;
its earlier failures remain evidence against assuming sustained reliability.
The small check does not establish that DeepInfra is categorically better or
that either route has been repaired. Do not pool these calls with earlier
diagnostics as independent replications.

The next step is a separately versioned resource check using Qwen/DeepInfra FP8
alongside gpt-oss/DekaLLM BF16, with fresh disjoint probes, live budget, pinned
routes and the same visible-answer contract. A passing comparison does not
replace that prerequisite. No new resource phase or 288-call wording pilot
was launched in this task. The original 9,000-call study remains paused.

Recorded new cost is **$0.00118016**, approximately **0.118 cents**, with all
cost records present. Combined recorded spending for the failed wording resource
run, reasoning-control diagnostic and this comparison is **$0.00245707**.

## Reproducibility

See the [frozen comparison protocol](QWEN_PROVIDER_COMPARISON_PROTOCOL.md).
Artifacts are under
`results/research_directions/qwen_provider_comparison_20261022/`:
`selection_snapshot.json`, `REPORT.md`, `summary.json`, `observations.json`,
and `diagnostic/` with exact requests, manifest, reservations, raw responses,
headers and finalizations. `final_status.json` and `final_artifact_hashes.json`
record final verification.

All **110 offline tests pass**. Every new request/response and frozen input
verifies. Earlier diagnostic, wording and v4 artifact locks remain unchanged.
No inference request or temporary credential configuration remains active.
