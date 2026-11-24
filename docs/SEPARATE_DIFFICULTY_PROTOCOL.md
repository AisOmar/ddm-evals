# Practice-only difficulty selection and untouched test freeze

October 27, 2026 UTC. User instruction: “Use a separate practice set to find a
suitable difficulty level, then freeze untouched test questions.” This authorizes
calibration and freezing, not the next advice experiment. The previous timing
study and all earlier artifacts remain unchanged. Starting cumulative cost
upper bound: $0.735394833; total ceiling stays $1.

## Allocation fixed before calibration

Construct three nominal difficulty levels across six mathematical families:
bin packing, optimal binary prefix coding, dense determinant, bipartite matching,
overlapping pattern waiting time, and weighted interval scheduling. Complexity
changes through object/matrix/job counts, arithmetic size and coin bias; nominal
levels are hypotheses until measured. These are related mathematical templates,
not 72 independent reasoning mechanisms.

For every level and family, generate four distinct instances using fixed seeds.
Variants 0 and 1 are practice; variants 2 and 3 are reserved test candidates.
This creates 36 practice and 36 reserved items. Hash-lock the entire author pool,
exact keys, split, generation source and selection rule before any model answers.
Never move an item between splits, repair a key after calibration, or replace
an item based on model behavior. Verify exact local stem nonuse.

Practice calls use the same pinned Sonnet 4.5 setup as the recent studies:
ordinary no-advice prompt, temperature .7, 128-token cap, strict A/B JSON and no
extended thinking/tools/caching. One fresh context per practice item, 36 total.
Seed 20261027108 fixes collection order. No reserved question is submitted to
the evaluated Sonnet model, even for a baseline or qualification call.

Exact author computations have second algorithms/arguments. Before practice
collection, Haiku reviews each level's twelve practice questions in a separate
blind batch. A single proof-assisted batch per level is allowed if any answer
or uniqueness judgment disagrees. Preserve all reviews and unresolved flags.
Unresolved practice review blocks collection; it is never a factual model error.
This is fresh-context AI review, not human or independent model-family review.

## Selection rule

Analyze only the complete 36-item practice cohort. A level qualifies if all
12 answers are recognized, factual accuracy is between 55% and 85% inclusive,
and both correct and incorrect answers occur. Choose the qualifying level
closest to 70% accuracy; ties prefer the lower nominal level. Keep every family
and both reserved instances at that level: twelve test questions. Do not select
individual questions or favorable instruction effects.

If no single level qualifies, a prespecified fallback may choose one level per
family. Enumerate all 3^6 level vectors using the two practice items per family.
Apply the same 55–85%, fully recognized, correct-and-incorrect requirements to
the resulting twelve practice observations. Prefer accuracy closest to 70%,
then smallest sum of levels, then lexicographically smallest vector. Disclose
this more adaptive selection and its overfitting risk. The corresponding two
reserved variants from every family remain fixed. No practice item is itself
eligible for the test.

If no configuration qualifies, report calibration failure and leave the reserved
pool sealed; do not declare a ready test. No extra calibration wave or relaxed
threshold is authorized. Even successful practice selection does not guarantee
held-out accuracy, prevent a future ceiling or establish statistical power.

## Reserved-item quality review and freeze

Only after saving practice results and the deterministic selection, Haiku may
review the twelve selected reserved questions. One blind and, if needed, one
proof-assisted batch are permitted. This quality review does not use Sonnet
test outcomes and cannot change the selected level, questions or keys. If it
does not resolve every item, save the blocked-quality status and do not label
the test ready. Reviewer exposure is disclosed: “untouched” means no evaluated
Sonnet answers, not that no author, reviewer or system has read the questions.

After review passes, save masked test questions, a separate answer key, source
pool and selection hashes, item/family IDs, practice summary and a final freeze
manifest. Record zero evaluated-model test calls. No advice experiment, test
baseline, model change, Google Doc edit or external publication is launched.

## Budget and collection integrity

Count exact inputs for all 36 practice requests and the six possible practice
review requests before paid work. Reserve counted input +256 and 128 output
tokens per practice request; reviews use 1024 output tokens. Reserve two later
selected-item review calls prospectively at 12,000 input tokens each, plus 1024
output. Count their actual selected inputs after selection and require count
+256 <=12,000 before dispatch. At verified per-million rates Sonnet is $3/$15
and Haiku $1/$5 input/output. Freeze only if all reservations plus the prior
bound fit within $1. The margin is an assumption, not a provider guarantee.

Use HTTP/2 and 120-second timeout. No automatic retries, resampling, reasoning
rescue or intermediate-accuracy stopping. Keep delivered nonanswers unknown;
stop on transport/API/identity/usage/budget failure. Preserve raw requests,
responses, headers and usage. Missing costs keep full reservations. Review
truncation is an unresolved review, not agreement. Report recognized accuracy,
correct/planned yield, unknowns and factual bounds by level and family. These
small repeated-family samples do not warrant independent-question confidence
intervals or claims of validated held-out difficulty.

Source: [verified Anthropic prices](https://platform.claude.com/docs/en/about-claude/pricing).
