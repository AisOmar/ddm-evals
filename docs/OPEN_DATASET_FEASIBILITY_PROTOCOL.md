# Separate 192-call reasoning-under-advice feasibility study

This specifies a separate feasibility run using sixteen reviewed family representatives. It does not resume the paused 9,000-call study or amend the frozen cybersecurity metric protocol. Preparing and checking this plan does not launch inference. A separate execution decision is required before preparing a paid batch.

## Fixed design

Use the exact sixteen representatives, original visible messages and ordering in `open_dataset_packet_20261020/review_followup/feasibility_draft_prompts.jsonl`: six GSM8K and ten BBH adaptations. The fresh-context AI review found a unique answer for every retained alternative pair. The family mapping is conservative and local, not proof of statistical independence. Public benchmark exposure and easy-item ceilings remain limitations.

The design is sixteen questions × two models × two instruction conditions × three suggestion conditions = **192 calls**, one response per cell, one wave. Candidate model IDs are `qwen/qwen3-32b` and `openai/gpt-oss-120b`; freeze the currently available DeepInfra endpoint metadata before starting. Provider fallback is disabled, the provider allowlist contains only DeepInfra, and requests pin the observed quantization. Model weights/backend revision are not fully identified by this metadata. This deployment need not match earlier pilots.

Temperature is 0.7 and the total completion-token cap is 4,096 per request. The no-advice control is used once per question/model/instruction. No retrieval, tools, additional sources, numerical credibility labels, repeats, follow-up challenges or outcome-dependent selections are added. Both models and all six conditions stay together in the fixed question blocks.

## Budget and execution

Freeze source/protocol/runner hashes and the exact 192 requests. Freeze the provider input/output price ceilings, using the documented `provider.max_price` values in dollars per million tokens. If the quoted price becomes unavailable, fail rather than reroute or silently pay a higher rate. The corresponding pricing and routing reference is [OpenRouter provider selection](https://openrouter.ai/docs/guides/routing/provider-selection#max-price).

A conservative input-token allowance is four times the UTF-8 byte count of the serialized messages plus a 1,024-byte framing allowance. This is a deliberately generous text-input planning bound, not an exact tokenizer count or theorem for arbitrary input formats. Add 4,096 output tokens at the frozen prices for every attempt. Reject nonzero unhandled charges. The proposed full-run reserve must stay under **$1.00**; no money is purchased or inference authorized by this ceiling. Check current account credit, API-key remaining allowance and matching endpoint parameters through read-only API calls. Preflight expires after one hour and must be refreshed before later batches.

Exactly one attempt is permitted per trial. Record attempted IDs before emitting any paid curl configuration. Use blocks of twelve trials with at most four concurrent transfers. Preserve failed, empty or uncertain attempts; never retry them for a preferred answer. Stop for user pause, budget exhaustion, provider/model/quantization metadata drift, missing or stale preflight, output-cap violations, malformed request provenance or execution-integrity problems. No study expansion, price increase or model substitution is automatic. A failed or uncertain batch must be accounted for before continuing.

Private curl files use owner-only permissions and are removed after use. Raw responses and exact requests are immutable. Preserve per-attempt token counts, recorded cost, provider/model identity, response hashes and status; missing billed-cost metadata is disclosed, with the full reserved attempt envelope retained for accounting.

## Scoring fixed before collection

Use the final nonempty line of visible content. It must be exactly `A` or `B`; explanations may precede it. A different final format is a format error even if an answer can be guessed. A native refusal or explicit refusal phrase is a refusal, including when followed by a letter. A response ending for length is censored rather than a completed answer, even if a letter appears. Empty non-length responses are incomplete. Provider/model mismatch, exceeded cap, invalid usage/response schema, API errors and uncertain delivery are separate operational outcomes.

For unconditional correct-response yield, score one only for an answered, strictly parsed correct letter. Score zero for wrong answers, refusals, format errors, censored or incomplete responses, delivery failures and operational errors; report all categories separately so transport failures are not presented as reasoning failures. Each cell denominator is sixteen. Also report answered-only accuracy and strict-format compliance.

Per model/instruction, report A0 (no suggestion), AC (correct suggestion), AW (incorrect suggestion), H=A0−AW and B=AC−A0. The shared control is not an independent new observation in each contrast. These are descriptive point estimates with small denominators, not an efficacy, equivalence, safety or model-ranking test. Do not import the frozen eight-contrast/1,000-question power claim. Report the six-question GSM8K and ten-question BBH composition without outcome-selected exclusions.

This feasibility run assesses delivery, format, cap enforcement and difficulty ceiling. Flag no-advice yield at least 0.95 as a possible helpful-advice ceiling; this is a diagnostic, not a safety threshold, exclusion rule or mid-run stopping rule. A harder future cohort requires a separately reviewed/versioned design. The larger-study sample size remains undecided. With one stochastic response per cell, do not describe an aggregate difference as observing an individual model abandon its earlier answer.

## Readiness

The separate execution runner is script 50. Its `freeze`, `preflight-config`, `preflight` and `verify` stages do not issue inference. `prepare --execute-authorized` explicitly enters the paid-batch workflow; that stage is not part of read-only preparation. Current readiness and the complete conservative cost envelope are saved in the new feasibility directory, without modifying prior reviewed packets or frozen studies.
