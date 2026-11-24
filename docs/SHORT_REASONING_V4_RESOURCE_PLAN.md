# Short reasoning resource test proposal for review

This proposal tests whether the reviewed short questions can finish within a
fixed budget on the exact intended deployments. **It is a proposal, with zero
calls executed.** Independent question review comes first. A passing resource
test would permit planning a baseline calibration; it would not demonstrate
factual competence, useful advice taking, or a safety metric.

## Intended deployments

| Model ID | Provider | Exact routing tag | Quantization |
| --- | --- | --- | --- |
| `openai/gpt-oss-120b` | DekaLLM | `dekallm/bf16` | BF16 |
| `qwen/qwen3-32b` | Tenstorrent | `tenstorrent/fp8` | FP8 |

These are the latest intended deployments from the preserved v3 amendment, not
new live availability claims. Disable fallback, allow only the listed tag, and
require the requested parameters and quantization. Do not substitute DeepInfra
or another provider if these routes are unavailable. Different providers and
quantizations prevent attributing cross-model differences to weights alone.

## Frozen resource design

- Eight resource questions, one from each family, each sent once to each model:
  **16 maximum calls**. Resource items never enter calibration statistics.
- Use the preselected order in `resource_plan_draft.json`, alternating model
  order between question pairs. Each request contains only one stem and its two
  options; IDs, other items, keys, and solutions are omitted.
- User instruction: “Answer the question. Be concise. Reply with A or B only on
  the final line.” No advice, reliability claim, tool use, or special reasoning
  mode. Temperature **0.7**, completion cap **2,048 tokens**, timeout **180 seconds**.
- Run serially, with at least **five seconds between preparations**, one attempt
  per trial, no automatic retries, no overlapping collectors, no cap increases.
- Total conservative full-cap reserve must be **at most $0.10**, covered by both
  account credit and key allowance. This is a spending ceiling, not a live quote.
  No credit purchase or automatic increase is included.

Before execution, obtain a live endpoint/parameter/capacity snapshot and all
price components, including caching and any fixed request fees. Pin prompt and
completion price ceilings in every request. Bound inputs conservatively, reserve
the full completion cap for every trial, and reject unknown nonzero charges.
Use a preflight no more than one hour old; refresh if it expires during the run.
If routes, pricing, or capacity fail the checks, stop before model traffic.

The saved JSON is explicitly a **request draft**. It omits live price ceilings,
live endpoint snapshots, and execution/review locks. It must not be dispatched
directly. A separate v4 runner and execution manifest must bind those fields,
review/adjudication hashes, protocol and code hashes before the first call.
The v3 runners hard-code their original item counts and review paths; do not
point them at this new packet or change their frozen files.

## Evidence to save

For every trial, save the exact request, budget reservation before dispatch,
raw response or partial body, HTTP status and headers, curl exit status,
expected and returned model/provider identity, termination reason, usage, cost,
and preparation/dispatch/completion timestamps. Hash request and response files.
Report total elapsed time separately from provider generation time, when
available. Missing timing components must stay missing rather than be inferred.
Remove credential-bearing temporary curl configurations after finalization.

## Passing and stopping rules

All **16/16** trials must return a complete valid response with the expected
identity, a normal stop, a recognized unambiguous A/B final choice, and valid
usage/cost within the frozen cap and reserve. A final line exactly `A` or `B`
passes strict format; a plain letter followed by option text or a letter enclosed
in Markdown may be recognized under the existing v2 final-line parser, while
strict-format compliance is reported separately. Freeze the exact parser/code
hash before dispatch; do not introduce a new rescue rule after viewing responses.

Factual correctness is **not** a resource-gate condition. Record it separately
after operational finalization; do not select, alter, or replace calibration
items using resource answers. One normal response per family cannot guarantee
all parameterizations or later repetitions will finish.

Stop the version at the first rate limit, timeout, incomplete body, refusal,
length stop, unrecognized/ambiguous output, identity mismatch, schema error,
missing/invalid usage or cost, provenance failure, or budget failure. Record all
unsent trial IDs. Preserve the failure; do not refill its cell or retry the same
version. HTTP 200 with an incomplete body is uncertain delivery, not a completed
answer. A capped response is a resource failure, not a scored factual mistake.
Honor any Retry-After and a minimum sixty-second cooldown before any future
separately planned version after a 429.

## Report and subsequent decision

Report an outcome row for each attempted trial, all unsent IDs, finish reasons,
recognized/strict-format counts, completion tokens, available timings, recorded
cost and missing cost records. Distinguish the execution gate from factual
correctness; missing billing metadata is not zero cost.

If the gate fails, diagnose the task or deployment limitation before proposing
another version. Do not automatically raise caps or start advice work. If it
passes, propose a separate **64-call no-advice calibration**: sixteen fixed
calibration questions × two models × two repetitions. This is future work,
requiring its own reviewed analysis, live reserve, and execution manifest; it is
not included in this resource proposal. Reserved items remain unsent. No
restart of the original study or large-scale collection is implied.
