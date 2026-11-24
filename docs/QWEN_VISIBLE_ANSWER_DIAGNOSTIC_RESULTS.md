# Qwen delivery diagnostic finds intermittent output and formatting problems

Completed October 22, 2026. All **18 planned diagnostic calls** were delivered
with valid identity, usage, and cost records. The earlier empty-visible-answer
symptom did not recur, but seven responses failed the fixed final-answer parser.
**Neither disabling reasoning nor adding `/no_think` demonstrated a reliable fix.**
No new resource version or wording pilot was launched.

## What the original response establishes

The earlier failed response already contained the average-speed calculation and
answer-like text in `message.reasoning`, while `message.content` was null. It
ended normally after 279 completion tokens under a 2,048-token limit and exposed
an `<|im_end|>` marker in the reasoning text. The saved request specified no
custom stop strings or reasoning-exclusion setting. The local runner saved the
raw body before applying its visible final-line parser.

The missing visible answer therefore exists in the returned API response; it
was not removed by the local scoring parser. It was not the observed consequence
of exhausting the completion cap or a transport timeout. A generation/template/
reasoning-field boundary problem is plausible, but the available gateway body
does not isolate model generation, Tenstorrent serving, and OpenRouter parsing.
The answer-like reasoning is not substituted for the missing final response.

## Controlled diagnostic

Three fresh questions covered ordered arithmetic, average speed, and logical
contraposition. Each had two fixed repetitions and three settings on exactly
the same Qwen3-32B / Tenstorrent FP8 deployment. The requests changed only the
named control within each question/repetition. Mode order was frozen before
dispatch and option order reversed on repetition two.

| Setting | Recognized visible answer | Strict A/B final line | Empty visible content | Responses with reasoning |
| --- | ---: | ---: | ---: | ---: |
| Original/default | 5/6 | 2/6 | 0/6 | 6/6 |
| `reasoning: {enabled: false}` | 3/6 | 0/6 | 0/6 | 0/6 |
| `/no_think` prompt switch | 3/6 | 0/6 | 0/6 | 6/6 |

The soft-switch responses had two characters in their reasoning fields and
reported one reasoning token each; that is not substantive returned reasoning.
The explicit disable responses reported zero reasoning tokens. These observations
show changed response behavior; they do not expose or verify the server's full
internal implementation.

Recognized answers include the already-permitted final-line forms such as
`A. No`; strict format requires only `A` or `B`. Failed examples included final
lines `BB: B**`, `Answer: BB**`, `A: A`, `Final. 26`, and a lone trailing `p`.
Some earlier text contained a numerically matching answer, but the frozen
contract does not allow searching arbitrary prose to rescue the response.
All seven remain format failures. No factual accuracy estimate is claimed from
this operational diagnostic.

All eighteen calls had HTTP 200, curl exit 0, normal stops, expected identities,
and completion counts below the cap. There were no rate limits, refusals,
timeouts, truncations, missing-cost records, or endpoint substitutions. None of
the new reasoning fields contained the exposed `<|im_end|>` marker observed in
the original failure. This is non-reproduction in a small fresh set, not proof
that the earlier intermittent failure disappeared.

## Decision

No setting passed the predeclared six-of-six visible-answer criterion. Keep the
288-call wording pilot stopped. Do not switch to non-thinking operation as an
assumed repair, raise caps, relabel format failures, or retry the original cell.

The next useful operational comparison is a separately fixed check of another
Qwen3-32B deployment using fresh disjoint questions and the same visible-output
contract. Inspect live endpoint availability, supported parameters, price and
quantization before selecting it. A backend comparison could test whether the
failure depends on this serving route, but changing the endpoint changes the
evaluated deployment. It needs a new bounded version and resource qualification
before any pilot resumption. No alternate-provider inference was made here.

If reliable delivery is obtained later, retain this diagnostic as evidence of
the earlier failures. A future deliberately broader output contract must be
defined and checked before new collection, with factual scoring and formatting
still reported separately; it cannot retroactively repair these outputs.

## Cost and records

Recorded new cost is **$0.00104148**, approximately **0.104 cents**, against a
full reserve of $0.02764464 and a diagnostic ceiling of $0.05. All cost metadata
is present. This is separate from the earlier $0.00023543 resource run; combined
recorded wording-development spending across these two runs is $0.00127691.

The [frozen diagnostic protocol](QWEN_VISIBLE_ANSWER_DIAGNOSTIC_PROTOCOL.md)
links the model-author and gateway documentation used to select controls.
Artifacts are under
`results/research_directions/qwen_visible_answer_diagnostic_20261022/`:
`REPORT.md`, `summary.json`, `observations.json`, and the `diagnostic/` manifest,
requests, attempts, raw responses, headers, HTTP records, and finalizations.
Final verification is in `final_status.json` and `final_artifact_hashes.json`.

All **107 offline tests pass**. Integrity checks cover all diagnostic attempts,
frozen requests and inputs, and earlier wording/v4 locks. No request or temporary
credential configuration remains active. The earlier failed resource phase and
the original 9,000-call study remain unchanged and stopped/paused respectively.
