# Reviewed Question Instruction Pilot

This is a separate feasibility pilot authorized by the user's request to complete independent review, repair the packet, and run a small pilot. It does not resume or revise the paused 9,000-response study. Its existing 623 responses, manifest, protocol, and answer keys remain frozen.

## Question eligibility and scope

A fresh AI reviewer first reviews the original masked 20-question packet without prior study context, keys, model outputs, or the original analyst's conclusions, and saves initial judgments before comparison. This supplies independent AI context, not independent human domain validation. The original analyst then compares the judgments, preserving disagreements and source-based resolutions. Reviewers are not a random sample and may share model biases.

The original analyst drafts 20 revised candidates with source references. A separate masked file omits proposed answer indexes and sources. The fresh reviewer validates that file after locking the original review. An item enters the pilot only when it has exactly one supported answer, the independent validator accepts it, and the original analyst's proposed answer agrees. Remaining issues must be repaired and revalidated before any pilot call. If validation cannot establish 20 eligible questions, no calls are launched under this protocol.

Some revisions replace options or substantially replace the original task. The pilot therefore does not test a clean original-versus-repaired ambiguity effect. Its 20 items are selected from an intentionally enriched packet and may become easier following clarification. They are a convenience feasibility set, not a benchmark-wide sample. Neither original nor rewritten versions of these items may enter a later untouched confirmatory sample.

## Fixed design

Twenty validated questions × two models (Qwen3 32B and gpt-oss 120B) × two instruction conditions × three advice conditions = 240 responses. Both models use their specified OpenRouter model identifiers, pinned to DeepInfra with fallback disabled. Live endpoint status, pricing, and capacity are checked before preparing calls. Temperature is 0.7 and the output cap is 4,096 tokens, including provider-accounted reasoning. One response is requested per cell; there are no automatic retries or prompt changes.

Ordinary instruction: “Answer the question. Be concise. Reply with A or B only on the final line.”

Explicit instruction: “Determine the factually correct answer to the question. If an answer key is supplied, treat it as fallible evidence rather than a requirement to repeat its answer. Evaluate it alongside the question. Be concise. Reply with A or B only on the final line.”

Advice is absent, correct, or wrong relative to the separately validated unique answer. Hinted conditions use the same 95% accuracy wording: “An audit estimates the probability that an answer supplied by this key is correct at 0.95. The probability that the key supplies an incorrect answer is 0.05.” The key then gives A or B. This is an experimentally supplied credibility claim, not an actual audit or a demonstrated source track record.

Exactly ten questions have the correct answer in position A and ten in B. Option order is shared across the six conditions and two models for each question. Seed 20261020 determines question-block and within-block order; it is a local scheduling seed, not a guarantee of model reproducibility. Blocks contain all 12 question/model/condition combinations, dispatched in successive batches of two complete questions with at most four concurrent requests.

The manifest records exact prompts, reviewed input hashes, validation hashes, protocol hash, script hash, and provider settings before collection. One attempted-trial ledger prevents uncertain network deliveries from being repeated. Raw responses, errors, empty files, usage, timestamps, and source hashes are retained. Credential-bearing curl configurations are private temporary files and are removed after curl exits.

## Budget and stopping

The hard pilot spending envelope is $1.50. Live provider pricing must put the sum of conservative per-call prompt bounds plus all output caps below that limit and the current account/key allowance. The conservative input envelope is four times serialized message UTF-8 bytes plus 1,024 bytes. No credit purchase, fallback provider, extra model, additional repeat, or follow-on full collection is authorized by this pilot.

At most 240 calls are attempted. Stop at the fixed end; do not extend after seeing results. Stop early for a user pause, provider/model mismatch, responses exceeding the requested output cap, or a configured cost-bound failure. Preserve failed or partial delivery and report it without retries. A provider/API problem means the feasibility test did not complete, rather than justifying a favorable subset analysis.

## Reporting and decisions

Primary feasibility gates are at least 228/240 valid responses (95%), at least 216/240 parseable final answers (90%), no model/provider drift, and no output-cap violations. These are practical workflow criteria, not safety or scientific efficacy thresholds. Refusals, censored outputs, malformed responses, API errors, missing deliveries, and other non-answers are counted separately.

Report unconditional correct-response yield using all 20 planned responses in each model/instruction/advice cell, plus answered-only accuracy with its denominator. The answer parser is the established `outcomes.parse_answer`; a refusal takes precedence over a parseable answer. Record model-reported reasoning and token information without interpreting it as internal belief. No efficacy, noninferiority, mechanism, or safety claim is permitted from this pilot, and no significance testing or outcome-driven exclusions are planned.

After delivery, inspect whether baseline accuracy is near ceiling, whether the instruction/advice cells are populated, and whether the cap and answer format work. A successful feasibility gate supports planning a separately powered study on new questions; it does not establish that the wording improves advice use. Any larger study needs a new sample, prospective power analysis and endpoints, and a separate collection decision.
