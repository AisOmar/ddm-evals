# Qwen visible answer diagnostic

October 22, 2026. The user authorized diagnosing the missing visible final answer
that stopped wording resource collection. This is a separate operational
diagnostic, not a retry or continuation of the failed resource phase.

## Observed failure and hypotheses

The preserved response has HTTP 200, a normal stop, 279 completion tokens under
a 2,048 cap, and null visible content. Its reasoning field contains a calculation
and answer-like text, ending in an exposed `<|im_end|>` marker. The request has
no custom stop strings, no reasoning exclusion, and no client-side transformation
of the saved body. The absent answer therefore precedes the local final-line
parser. These observations are consistent with a model/serving-template/reasoning-
parser boundary issue; they do not identify which component caused it.

The [Qwen3-32B model card](https://huggingface.co/Qwen/Qwen3-32B) distinguishes
thinking from non-thinking operation and documents `/no_think` as a soft prompt
switch. [Qwen's vLLM documentation](https://qwen.readthedocs.io/en/latest/deployment/vllm.html)
describes separate reasoning parsing and a server-specific hard template switch.
[OpenRouter's reasoning documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
describes the gateway reasoning controls and distinguishes exclusion of returned
reasoning from disabling generation. This diagnostic tests accepted gateway and
prompt controls; it does not assume access to Tenstorrent's server configuration.

## Fixed diagnostic design

Use only `qwen/qwen3-32b` on Tenstorrent FP8, exact tag `tenstorrent/fp8`, with
fallback disabled. Three fresh self-contained two-choice questions, each with
two preplanned repetitions, are tested under three modes:

1. `default`: omit the reasoning parameter, matching the original configuration.
2. `reasoning_disabled`: send `reasoning: {enabled: false}` with unchanged text.
3. `soft_no_think`: omit the reasoning parameter and append `/no_think` to the
   user message, as documented by the model author.

This gives **18 maximum calls**, all frozen before dispatch. Questions cover
ordered arithmetic, equal-distance average speed, and logical contraposition.
None is a previous pilot, resource, or v4 question. Numeric/key checks are author
checks, not an independent semantic review; diagnostic success never uses the
factual key. The repeated design measures delivery on a tiny development set,
not general reasoning competence or reliable error probabilities.

Temperature 0.7, max completion 2,048, timeout 180 seconds, serial dispatch,
minimum five seconds between preparations, one attempt per trial. Reverse A/B
order at repetition two across all modes, shuffle the three modes within each
question/repetition with seed 20261022072, and use independent conversations.
Keep model, provider, quantization, question text, and decoding fixed except for
the named control. `/no_think` changes the prompt and may change behavior; an
accepted gateway field is not proof a provider honored the intended setting.

## Preflight and accounting

Obtain fresh endpoint metadata, parameter support including `reasoning`, all
pricing components, available credit, and key allowance. Pin price ceilings,
check context/output capacity, conservatively bound prompt input and full-cap
completion costs, and require the full 18-call reserve to be **at most $0.05**.
This lies within the earlier $1 ceiling; no credit purchase or price increase.
Preflight expires after one hour; refresh without changing the frozen requests.
Preserve all requests, reservations, raw/partial bodies, headers, identities,
usage, cost, and timestamps. Remove temporary credentials after finalization.

## Stopping, outcomes, and decision

Visible nonanswers, refusals, ambiguous output, and length stops are measured
outcomes and do not select or replace trials; complete the fixed diagnostic
unless an operational fault occurs. Stop on HTTP/provider errors, uncertain
delivery, identity/schema/provenance failure, missing/invalid cost, cap violation,
or budget failure. No retries, alternate providers, cap increases, or unplanned
extra probes. Honor Retry-After and at least sixty seconds after any 429 before
any future separately specified version.

Use the preserved final-line parser to classify visible content. Report normal
stops with recognized visible choices and strict format separately from factual
correctness. Record null/empty content, reasoning presence/character count,
reasoning token metadata, completion tokens, finish reason, and exposed special
token markers. Never extract a final answer from reasoning as a scoring rescue.
Do not infer generation internals from accounting-token differences.

Compare the fixed 6-call denominators per mode, including every planned trial.
If a mode is accepted and all six produce normal-stop recognized visible choices,
it is a candidate for a new resource qualification, not proof the defect is fixed.
If non-thinking controls work while default fails, that supports a mode-sensitive
delivery problem without isolating server parsing from model generation. If the
default defect does not recur, report non-reproduction. Preserve any failures
under the candidate modes rather than claiming a successful fix.

No restart of the 288-call pilot or the original 9,000-call study is included.
Any new pilot mode requires an explicit new version, resource qualification,
and a statement that the evaluated configuration changed.
