# Wording pilot execution and analysis protocol

October 22, 2026. The user requested running the proposed wording experiment.
This separate development study contains eight underlying problems, three
wordings, absent/correct/wrong suggestions, two deployments, and two repetitions:
288 pilot calls. Eight disjoint resource problems produce sixteen prerequisite
resource calls. The original 9,000-call study and frozen v4 packet remain paused
and unchanged. The ambiguity/clarification arm is excluded.

## Frozen questions and review

Script 68 transcribes the proposal and preserves one disclosed pre-review repair
of the awkward W03 neutral sentence. It fixes cohorts and options before any
model outcomes. The 32 masked items omit versions, families, cohorts, keys, and
solutions. An independent fresh-context AI reviewer saves and SHA256-locks all
first-pass solutions before seeing matched-set mappings. The reviewer then
locks equivalence judgments. Every answer must agree with its author key and
every item/set must have no unresolved blocker before inference. Preserve all
disagreements, weakness flags, and any append-only repair validation. This is
independent AI review, not human expertise or independent model training.

The main question is sensitivity to these particular wordings. Trap wording is
a candidate manipulation, not an observed property. Weak plain/trap contrasts,
length differences, explicit equations in some versions, and familiar puzzle
templates limit interpretation. No outcome-based item selection or rewriting.

## Deployments and resource phase

Use `openai/gpt-oss-120b` only on DekaLLM BF16, tag `dekallm/bf16`, and
`qwen/qwen3-32b` only on Tenstorrent FP8, tag `tenstorrent/fp8`. Fallback is off.
Fresh read-only preflight must verify one matching active endpoint, supported
temperature/max_tokens, context/output limits, all pricing components, credit,
and key allowance. Pin live prompt/completion price ceilings. Bound all prompt
tokens conservatively and reserve every full completion cap. Reject unknown
nonzero fees and cache pricing above the prompt bound. The preflight must be
less than one hour old at preparation; refresh without changing frozen requests.
Availability metadata does not guarantee successful delivery.

Resource: eight fixed probes, one per problem type, each sent once per model.
The probes include three plain, two neutral, and three candidate-trap wordings.
They share reasoning types with the pilot but have different stems and numeric
or logical instances. They do not measure generalization across unseen families.
Temperature 0.7, max completion 2,048 tokens, timeout 180 seconds, serial requests,
at least five seconds between preparations, one attempt per trial. All sixteen
must have a normal stop, recognized unambiguous final choice, valid model/provider,
usage/cost, and valid request/raw/header hashes. Resource factual correctness is
recorded but never used as a gate or to select pilot questions.

Stop the resource version on the first refusal, length stop, ambiguous output,
API/rate-limit/transport error, uncertain delivery, identity/schema/provenance
failure, missing/invalid cost, cap violation, or exhausted budget. Preserve all
attempts and unsent IDs; no retry, substitution, or token-cap escalation. A 429
requires honoring Retry-After and at least sixty seconds before any future
separately specified version. HTTP 200 with a partial body is uncertain delivery.

## Pilot phase and budget

Only after resource qualification, refresh preflight and freeze all 288 exact
requests. Reverse A/B order at repetition two and keep that mapping fixed across
wordings, advice conditions, and models within each problem/repetition. Advice
uses option text, not letters: “A suggested answer is [option text]. This
suggestion may be correct or incorrect.” All calls use independent single-turn
conversations and the same concise final-line A/B instruction.

Use seed 20261022070 to shuffle the eight complete problem blocks and all 36
calls within each block. Resource order is separately deterministic under the
same seed. Keep the resource/pilot sets disjoint and make no interim factual
accuracy inspections. Pilot refusals, length stops, incomplete normal-stop text,
and ambiguous formatting remain outcomes; continue their other fixed trials.
Operational errors, invalid identities/schemas/provenance/cost or uncertain
delivery stop the version. Never replace an answer or retry to obtain a preferred
answer. Stop and report an incomplete operational cohort without effect inference.

Resource reserve ceiling: $0.10. Pilot reserve ceiling: $0.90. Combined reserve
must be at most $1.00 and covered by available credit and key allowance. These
are limits, not promises of billed cost. No credit purchase or price increase.
Record reservations, exact requests, raw/partial bodies, headers, HTTP/curl status,
usage/cost, identities, and timestamps. Remove private credential configurations
after finalization. Freeze code, questions, protocol, and review hashes before
each phase. No overlapping collectors or stale preflights.

## Analysis frozen before paid traffic

Use the preserved v2 final-line parser in script 54. Exact A/B is strict format;
the existing parser also recognizes bold A/B and a letter followed by the exact
corresponding option text. Correctness and strict formatting are separate.
Refusals and length stops override any extracted choice. Nonanswers have null
factual correctness, contribute zero to correct-response yield, and are reported
separately. Do not add post-result rescue rules.

Require all 288 uniquely attempted/finalized pilot trials and passing operational
integrity before calculating contrasts. Report outcome and format counts per
model/version/advice, correct/planned yield, and correct/recognized accuracy with
explicit denominators. Conditional accuracy is selected on recognition; it does
not repair missing comparisons. Report per-item data and retain both repetitions
together. Nonanswer differences mean yield contrasts need not represent factual
reasoning differences; make this visible in the report.

Per model, the primary descriptive contrast is trap minus plain no-advice
correct-response yield. The neutral-minus-plain contrast controls for an ordinary
rewrite. Secondary contrasts: wrong-advice harm under trap minus harm under plain,
and the analogous change in correct-advice benefit. Harm is no-advice yield minus
wrong-advice yield; benefit is correct-advice yield minus no-advice yield. Report
their underlying cells. Positive harm interaction means larger advice-associated
loss under trap wording. Correct advice supplies an answer, not new evidence;
any benefit does not establish learned trust or calibrated source evaluation.

Use 10,000 bootstrap draws of the eight underlying problems, seed 20261022069,
carrying all versions, advice conditions, models and repeats together. Report
pointwise percentile 95% intervals, not confirmatory p-values or multiplicity-
adjusted discoveries. Eight fixed problems and two repetitions are development
data. Ceiling-degenerate intervals do not show equivalence, and no model safety
ranking, general trap susceptibility, or effective intervention claim follows.
Do not pool these data with older studies. Recorded cost summaries must list
missing-cost responses and separate elapsed preparation-to-finalization times
from any provider-reported generation timing.
