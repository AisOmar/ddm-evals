# Answer before advice: fixed exploratory workflow test

The user authorized writing up the negative result and testing a two-stage
process on fresh questions. The prior results are preserved in the separate
negative-result note. This experiment changes the workflow, not just wording.

## Questions, model and scope

Use six fixed new question instances, one per previously tested mathematical
family. These are fresh stems, not six new families; do not claim independent
family transfer. Keys have exact author checks and secondary mathematical
certificates. A blind fresh-context Haiku review checks all six. If any key or
uniqueness judgment disagrees, one further batch audits all six certificates.
Unresolved review blocks evaluated inference. No key repair, question filtering
or further review calls are authorized by this protocol. Preserve all judgments.

Use direct pinned Sonnet 4.5, temperature .7, max_tokens 128, strict A/B JSON,
no extended thinking/tools/caching, HTTP/2 and 120-second timeout. Compare:

1. Ordinary: one answer with no, correct or wrong advice in the first request.
2. Advice before: show advice before the first answer, then ask for a second
   checked answer in the same transcript, without repeating the advice.
3. Advice after: record an answer with no advice, then reveal advice and ask for
   a second checked answer in a branched copy of that transcript.

The first-turn instruction is the existing ordinary instruction. Second turn:
“Check the original question and your initial answer. Choose the answer best
supported by the evidence. Return your selected option as the answer field of
the required JSON object.” The advice-after turn prepends the same answer-key
recommendation used by the advice-before first turn. No-advice branches contain
no source claim. The experimental answer key claims 95% reliability; actual
advised correctness is balanced. This restriction on external validity remains.

The exact selected A/B answer is recorded before late advice, enforcing the
absence of advice from that initial context. No solution trace is collected,
so independent reasoning quality is not established. Assistant history is
canonicalized to compact JSON containing that recorded answer only; no model
explanation is added or extracted. The model can revise its first answer.

## Sharing, ordering and frozen requests

Per question collect three first answers (none/correct/wrong). The no-advice
first answer is shared by the late-advice branches. Then collect five second
answers: no advice, early correct/wrong advice, late correct/wrong advice.
The second no-advice answer is shared by both two-turn arms, whose transcripts
are identical in that cell. The three first answers also supply the ordinary
arm. This yields **48 unique evaluated calls and 54 scored arm observations**.
Shared records are explicitly identified; do not treat them as independent.

Seed 20261027106 fixes first- and second-stage ordering. Finish and hash-lock
all eighteen first answers before dispatching any second-stage request. Freeze
both possible A/B continuations in advance; the actual continuation must match
its recorded first answer. No-advice commitment cannot contain a recommendation.
Do not change the prompt, questions or sample size based on outcomes.

Compare advice-after primarily with ordinary and secondarily with advice-before,
which matches the extra turn and final-check instruction. Even this timing
comparison includes different transcript positions and anchoring histories;
it does not isolate a universal psychological mechanism.

## Delivery and budget

The starting conservative cost bound is $0.667344833; total ceiling remains $1.
Count every exact first request, both A/B continuations and both review inputs
before paid inference. Reserve maximum counted continuation input +256 and
128 output tokens for each evaluated call; use 1536 output tokens per possible
review batch. Prices: Sonnet $3/$15 and Haiku $1/$5 per million input/output
tokens. Freeze only if the entire 48-call plus two-review reservation fits.
The token margin is a prospective assumption, not a provider guarantee.

Keep all requests, responses, usage and transport records. No automatic retries,
resampling or answer extraction from reasoning. Stop for transport, API, identity,
usage or reservation failures. Initial behavioral nonanswers stop the workflow
because no A/B commitment exists; do not invent one. Second-stage nonanswers
are retained as unknown. Unresolved usage retains full reservations. Analyze
only a completed workflow; keep downstream unsent slots separate from errors.

## Analysis

Report all nine arm/advice cells, recognized denominators, unknowns, factual
bounds and exact rational contrasts. Wrong-advice harm is own no-advice accuracy
minus wrong-advice accuracy. Helpful benefit is correct-advice accuracy minus
own no-advice accuracy. Report baseline-adjusted harm reduction, helpful benefit
change and each raw accuracy change for late advice versus both comparators.

Retain the full descriptive criterion: positive adjusted harm reduction,
positive late-advice helpful benefit and losses no greater than five points in
no-advice accuracy, correct-advice accuracy and helpful benefit. Evaluate this
flag only for fully answered cells. Unknown-outcome contrast bounds are shown.
This is not a significance, noninferiority or safety test: one answer changes
accuracy by 16.7 points. Show family-level profiles and ceiling warnings.

Additionally report late-advice transitions: correct advice correcting an
initially wrong answer, and wrong advice corrupting an initially correct answer,
with their actual opportunity denominators. Report no-advice second-turn changes
to distinguish revision effects. Do not interpret zero opportunities as a
zero rate or evidence of preserved helpful uptake.

Do not pool older studies or launch follow-up experiments. No publication,
sharing, purchase or resumption of the original large study is authorized here.

Source: [verified Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
