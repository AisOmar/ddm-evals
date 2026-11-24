# The 192-call feasibility setup is prepared

**Execution update:** the user subsequently authorized this separate bounded run, and all 192 attempts are now complete. See the [results and limitations](OPEN_DATASET_FEASIBILITY_RESULTS.md) and the run's `execution_readiness.json` for current status. The preparation-time statements below and `readiness.json` are preserved as historical records. The original larger study remains paused.

Read-only preflight passed at **2026-10-21 00:00:53 UTC** (October 20 in Boise). Both selected DeepInfra endpoints were listed as active, supported the requested parameters and token capacities, and matched their frozen public metadata. Account credit and API-key allowance cover the conservative full-run reserve. **No inference requests have been sent and no credit was purchased.**

The exact 192 requests, source hashes, endpoint metadata, provider/price restrictions and scoring protocol are frozen separately from earlier studies. All **55 offline tests pass**. The original 9,000-call study remains paused.

## Budget and models

| Model | Quantization | Input price / million tokens | Output price / million tokens | Calls | Conservative reserve |
| --- | --- | ---: | ---: | ---: | ---: |
| Qwen3 32B | FP8 | $0.08 | $0.28 | 96 | $0.158064 |
| gpt-oss 120B | BF16 | $0.037 | $0.17 | 96 | $0.089030 |
| Total | | | | **192** | **$0.247094** |

Prices and endpoint properties were fetched from the official [Qwen3 endpoint API](https://openrouter.ai/api/v1/models/qwen/qwen3-32b/endpoints) and [gpt-oss endpoint API](https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints). The actual snapshots are preserved with hashes; public API values may change. FP8/BF16 matches the earlier reviewed pilot's recorded quantization, although these labels do not identify all backend or weight revisions.

The roughly **25-cent** reserve assumes every request uses all 4,096 completion tokens and an input allowance of `4 * (UTF-8 message-JSON bytes + 1024)`. The largest allowance is 8,052 input tokens. This is intentionally conservative text-only planning, not an exact tokenizer count. The reserve is not an observed charge or expected average cost. The local proposed ceiling is $1.00, with no automatic retries; every trial can be attempted once only.

Requests allow only DeepInfra, disable fallback, pin quantization, require parameter support, and cap per-token prices at the checked rates. OpenRouter documents [price-ceiling routing](https://openrouter.ai/docs/guides/routing/provider-selection#max-price) as blocking a request when the requested prices are unavailable. Readiness must be refreshed after one hour or if metadata changes. Availability has been checked through metadata, not a paid test completion.

## Fixed study and scoring

Sixteen reviewed family representatives × two models × two instructions × three suggestion conditions gives 192 calls, with one response per cell and a single wave. The sixteen questions comprise six GSM8K and ten BBH adaptations. The original twenty-question packet and all initial reviews are preserved. This separate small study does not inherit the larger cybersecurity study's power calculations.

The [frozen protocol](OPEN_DATASET_FEASIBILITY_PROTOCOL.md) specifies exact final-line A/B scoring. Refusals, format errors, incomplete answers, cap truncation and operational failures are recorded separately. Correct-response yield uses every planned trial; operational failures are not described as reasoning failures. Report A0, AC, AW, wrong-suggestion harm and correct-suggestion benefit with sixteen trials per cell. Scores are descriptive; they cannot validate a safety metric or establish equivalence.

This parser deliberately requires a bare final `A` or `B`. It does not inherit the earlier pilot's more permissive answer-extraction rule, so cross-pilot score comparisons need that difference disclosed. Length-stopped responses are censored even when visible text contains a letter. Provider/model mismatch or cap violations stop later paid preparation.

## Execution status

Read-only setup is complete. A separate decision to run the bounded feasibility study is still pending; no paid batch is prepared. Script 50 provides a runner, immutable attempt ledger, four-transfer curl handoff, batch finalization and descriptive scoring. Its preparation stage requires an explicit execution acknowledgement and a passing current preflight. No purchase, retry, model change, old-study resume or sample expansion happens automatically.

The source of current machine status is `results/research_directions/open_dataset_feasibility_192/readiness.json`. Earlier packet flags are preserved as creation-time history. A future run will first refresh preflight if stale, then use only the frozen requests and bounds. A harder, larger study remains a later design decision after feasibility and difficulty are assessed.

## Artifacts and verification

Under `results/research_directions/open_dataset_feasibility_192/`:

- `manifest.json`: 192 exact requests and frozen input/protocol/runner hashes.
- `qwen_endpoints.json`, `gpt_endpoints.json`: public endpoint snapshots.
- `preflight.json` / `preflight_history/`: timestamped endpoint, credit, allowance and cost checks; no credentials.
- `protected_inputs_before.json`, `verification.json`: preservation of previous study/question/review files.
- `readiness.json`: current preflight and non-execution status.

Tests cover cost/coverage/capacity rejection, pinned routes and price ceilings, refusal/cap/strict-format classification, missing or malformed usage, execution acknowledgement, and synthetic scoring with fixed denominators. All 55 tests are offline; synthetic-response output from tests is not a new model result. Private read-only API curl files and temporary credit responses were removed after preflight.
