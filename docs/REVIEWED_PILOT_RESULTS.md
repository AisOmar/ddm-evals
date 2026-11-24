# Reviewed Instruction Pilot Results

All 240 planned responses were delivered and parsed, with no refusals, truncation, provider mismatch, or output-cap violations. The recorded cost was $0.0181 (about two cents), below the conservative preflight maximum of $0.307 and the $1.50 hard cap. The pilot passed its delivery, answer-format, provider, and output-cap feasibility gates.

The 20-question set underwent fresh-context AI source review and a second masked validation of the revised questions. This supplies independent AI review, not human expert validation. The original study remains paused at 623/9,000 responses.

## Descriptive accuracy

Each entry is the number of correct answers out of 20 planned responses. All responses were parseable, so unconditional correct-response yield equals answered-only accuracy here.

| Model | Instruction | No advice | Correct advice | Wrong advice |
| --- | --- | --- | --- | --- |
| Qwen3 | ordinary | 19/20 | 20/20 | 17/20 |
| Qwen3 | explicit | 19/20 | 19/20 | 18/20 |
| gpt-oss | ordinary | 19/20 | 20/20 | 10/20 |
| gpt-oss | explicit | 20/20 | 20/20 | 20/20 |

For gpt-oss, wrong-advice accuracy was 10/20 with ordinary instructions and 20/20 with explicit fallible-evidence instructions. Correct-advice accuracy was 20/20 in both conditions. For Qwen3, wrong-advice accuracy was 17/20 and 18/20 respectively, while correct-advice accuracy was 20/20 and 19/20. These are observed differences in this fixed pilot, not established efficacy, noninferiority, safety, or mechanism results. The full wording intervention changed more than prompt length, so its internal explanation is also unresolved.

The no-advice conditions were near ceiling (19–20/20). Several revisions replace the knowledge being tested or make it easier, so these results do not isolate a causal effect of removing ambiguity. The set was intentionally enriched for suspected item problems and is not representative of the benchmark. There was one stochastic response per cell on only 20 questions. No significance testing, post-result exclusions, retries, or extension was performed.

## Feasibility and integrity

Both models were pinned to DeepInfra with fallback disabled, temperature 0.7, and a 4,096-token output cap. The largest recorded completion was 2,300 tokens. Ten batches of two complete question blocks delivered all 240 planned responses. Exact prompts, provider responses, errors if any, usage, hashes, validation, and the frozen protocol are preserved. All 26 script tests passed.

Verification checked the original manifest and its frozen inputs and all 623 original response hashes; they match the paused snapshot. The new manifest, script, protocol, revised-question set, independent validation, and all 240 new response hashes also match their saved records. Original keys and raw outputs were not changed.

## Next research decision

The workflow is ready for a separately planned efficacy study. The pilot offers a promising descriptive instruction pattern for gpt-oss and little change for Qwen3; it does not justify launching a large run automatically. Design a fresh, more discriminating question set that is independently reviewed, includes difficulty variation, and excludes both original and rewritten pilot items. Prospective simulation should address improvement with wrong advice and preservation of correct-advice benefit, with a justified margin and declared multiplicity. The near-ceiling correct-advice condition makes that preservation question demanding.

A human domain review remains useful before claims about question validity. A separate original/repaired ambiguity experiment also needs its own design, including acceptable-answer sets and truly wrong advice under each version.

A subsequent [metric scoring and sample-size plan](SELECTIVE_RELIANCE_METRIC_PLAN.md) now defines the profile and preservation tests and prepares a fresh masked review queue. That analysis design is frozen, while question validation and actual collection remain pending.

## Saved records

- [Review and adjudication](REVIEWED_PACKET_RESULTS.md)
- [Frozen pilot protocol](REVIEWED_PILOT_PROTOCOL.md)
- [Manifest and exact requests](../results/research_directions/reviewed_instruction_pilot/manifest.json)
- [Cell summaries](../results/research_directions/reviewed_instruction_pilot/summary.json)
- [Response-level scores and hashes](../results/research_directions/reviewed_instruction_pilot/runs.json)
- [Integrity verification](../results/research_directions/reviewed_instruction_pilot/verification.json)
