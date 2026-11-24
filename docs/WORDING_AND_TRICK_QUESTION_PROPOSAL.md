# Wording and trick question experiment for review

Prepared October 22, 2026. Test whether models give different answers when the
same short reasoning problem is phrased plainly, neutrally paraphrased, or
written to invite a specific intuitive mistake. Also test whether misleading
advice has a larger effect under the trap wording. This is an unexecuted
development proposal; no independent review or live qualification is complete.

## Three versions of the same problem

| Version | Purpose | Requirement |
| --- | --- | --- |
| Plain | State the problem directly | One uniquely supported answer |
| Neutral paraphrase | Measure sensitivity to an ordinary rewrite | Same facts, question, options, and supported answer |
| Candidate trap | Invite a plausible misreading or intuitive shortcut | Same facts, question, options, and supported answer; still unambiguous |

Keep numbers, units, available evidence, and answer choices fixed within each
matched set. Keep length reasonably similar and record word counts. Where a
plain version makes a relationship explicit, it must follow from all three
versions. A change in what the question asks is not an equivalent rewrite.
Do not label a prompt “tricky” in the model request or add “watch out” instructions.
Do not use obscure factual trivia or laborious calculation to manufacture errors.

The eight candidate sets below are new development examples, not replacements
for the frozen v4 questions. They share some reasoning templates with v4;
fresh wording and numbers do not establish unseen-family generalization.

## Candidate questions

**W01 — Difference versus total**

- Plain: Two tickets cost 11 credits together. The adult ticket costs 9 credits
  more than the child ticket. What is the price of the child ticket?
- Neutral: The combined price of one adult ticket and one child ticket is 11
  credits. Their price difference is 9 credits, with the adult ticket dearer.
  What does the child ticket cost?
- Candidate trap: An adult ticket and a child ticket cost 11 credits in total.
  The adult ticket costs 9 credits more than the child ticket. How much does
  the child ticket cost?
- Options: 1 credit; 2 credits.

**W02 — Equal distances versus equal times**

- Plain: A cyclist travels 12 km at 6 km/h and another 12 km at 3 km/h, with no
  stops. What is the average speed over the entire 24 km?
- Neutral: On a nonstop 24 km ride, the first 12 km are covered at 6 km/h and
  the remaining 12 km at 3 km/h. What is total distance divided by total time?
- Candidate trap: A cyclist rides out at 6 km/h and returns along the same
  12 km route at 3 km/h without stopping. What is the average speed for the trip?
- Options: 4 km/h; 4.5 km/h.

**W03 — Reversing a conditional probability**

- Plain: Of 100 devices, 20 are infected. A scanner flags 18 infected devices
  and 16 uninfected devices. A device is chosen uniformly from all flagged
  devices. What is the probability it is infected?
- Neutral: A 100-device batch has 20 infections. The flagged group contains
  18 infected and 16 uninfected devices. What fraction of a uniform random
  sample of one flagged device is the probability of infection?
- Candidate trap: A scanner detects 18 of the 20 infected devices in a batch
  of 100. It also flags 16 uninfected devices. If one flagged device is chosen
  uniformly at random, what is the probability it is infected?
- Options: 9/17; 9/10.

**W04 — Negation and implication**

- Plain: Every sealed parcel is labeled. One parcel is not labeled. Must that
  parcel be unsealed? Answer using only these premises.
- Neutral: Being labeled is required for every sealed parcel. A particular
  parcel lacks a label. Does it follow that this parcel is not sealed?
- Candidate trap: No sealed parcel lacks a label. This parcel is not labeled.
  Is it impossible, under those premises, for this parcel to be sealed?
- Options: Yes; No.

**W05 — A relative time reference**

- Plain: Three days before today was Monday. What weekday is tomorrow?
- Neutral: Monday occurred exactly three days ago. Which day of the week
  comes immediately after today?
- Candidate trap: The day before yesterday was the day after Monday. What
  weekday will tomorrow be?
- Options: Friday; Saturday.

**W06 — A ratio and a difference**

- Plain: Lina has twice as many tokens as Omar. Lina has 6 more tokens than
  Omar. How many tokens does Omar have?
- Neutral: Lina's token count is two times Omar's count, and the difference
  between their counts is 6. What is Omar's token count?
- Candidate trap: Lina has twice Omar's number of tokens, which puts her
  6 tokens ahead of Omar. How many tokens does Omar have?
- Options: 6; 3.

**W07 — Intervention versus inference**

- Plain: A system has U=3, X=U+2, and Y=2*X+U. Force X to 4, leaving U and
  the equation for Y unchanged. What is Y after this intervention?
- Neutral: Initially U=3, X=U+2, and Y=2*X+U. Override only the X equation
  with X=4, keep U fixed, and compute the resulting Y.
- Candidate trap: The system follows X=U+2 and Y=2*X+U, with U=3. Now an
  intervention sets X=4 instead of following its equation. U stays fixed.
  What does Y become?
- Options: 11; 10.

**W08 — Successive percentage changes**

- Plain: A price starts at 100 credits, falls by 20%, and then rises by 20%
  of its reduced value. What is the final price?
- Neutral: First multiply a 100-credit price by 0.8. Next increase that
  result by 20% of itself. What price do these changes produce?
- Candidate trap: A 100-credit price is reduced by 20% and then increased
  by the same percentage, applied to the reduced price. What is it now?
- Options: 96 credits; 100 credits.

These examples are author drafts. Several plain/trap pairs differ only slightly
and might not induce different behavior; the label identifies the intended
manipulation, not an observed effect. The neutral W03 wording and all other
versions need independent readability and equivalence checks before freezing.

## Independent review before collection

Give a fresh reviewer randomly ordered, anonymous versions without condition
labels, author solutions, or model outcomes. First obtain a locked independent
solution and ambiguity assessment for every version. Then reveal the matched
sets, but not model outcomes, and request a second equivalence assessment.
Record whether each version retains the same information, target, assumptions,
and answer. Distinguish errors invited by wording from ambiguity that makes a
different answer defensible. Resolve any mismatch and validate repairs in a
new version. Do not choose final wording by trying many variants on the tested
models and retaining only those that produce errors.

Author checks for comparison only after the initial review: W01 is 1 credit
because x+(x+9)=11; W02 is 4 km/h because 24/(2+4)=4; W03 is 18/(18+16)=9/17;
W04 is Yes by contraposition; W05 is Friday; W06 is 6 because 2x-x=6;
W07 is 11 because 2*4+3=11; W08 is 96 because 100*0.8*1.2=96. Reviewers must
not receive this author proposal as their masked question packet.

## Proposed pilot after review and resource qualification

Use the intended v4 deployments: `openai/gpt-oss-120b` on DekaLLM BF16
(`dekallm/bf16`) and `qwen/qwen3-32b` on Tenstorrent FP8
(`tenstorrent/fp8`). Availability and pricing have not been checked for this
proposal. Apply fresh endpoint, identity, pricing, credit, usage, and completion
checks before any execution. Keep no-advice and advice results distinct.

Eight problems × three wordings × three advice conditions × two models × two
repetitions gives **288 planned pilot responses**. Advice conditions are absent,
correct, and wrong. The same generic advice sentence must appear in every
advice condition: “A suggested answer is [option text]. This suggestion may be
correct or incorrect.” The advice supplies no new factual evidence and makes no
claimed reliability or authority assertion. This tests susceptibility to a
suggestion; a gain with correct advice would not establish learned trust.

Reverse option order on the second repetition. Use the same option mapping
across all versions, advice conditions, and models within an item/repetition.
Express suggestions using option text so moving a letter does not change their
meaning. Randomize complete problem blocks and the calls within each block
using a recorded seed frozen before collection. Use independent conversations
for all trials; no model sees another version or its own earlier answer.

The pilot needs its own exact request manifest, analysis code, and live full-cap
reserve. Proposed paid ceiling is **$1 total**, not a live forecast or instruction
to spend. Resource qualification is separate from those 288 calls and requires
its own fixed representative wording probes and bounded reserve within that
ceiling. Resource and study items must be disjoint. Freeze all probes and limits
before dispatch; do not improvise probes or reuse the study items to tune caps.
Use the v4 serial, 2,048-token, 180-second settings unless a separately reviewed
amendment changes them before execution. No automatic retry, provider switching,
cap escalation, old-study restart, or advice experiment is launched by this file.

## Outcomes and interpretation

The main wording contrast is each item's **no-advice accuracy under candidate
trap minus no-advice accuracy under plain wording**. Compare the neutral
paraphrase with plain wording as a control for ordinary rewrite sensitivity.
Report paired estimates for each model; do not pool repeated calls as independent
questions. A lower score would show sensitivity to these tested wordings,
without identifying an internal cause or applying to all trick questions.

The secondary interaction is **wrong-advice harm under trap wording minus
wrong-advice harm under plain wording**, where harm is no-advice accuracy minus
wrong-advice accuracy. Positive values mean a larger advice-associated accuracy
loss under the candidate trap. Also report correct-advice benefit, baseline
accuracy, and the neutral-version contrasts. Avoid declaring robustness merely
because all versions perform poorly or because a model ignores every suggestion.

Score factual correctness, strict formatting, refusals, truncations, and delivery
errors separately using a frozen output contract. Report denominators explicitly.
Cluster uncertainty by underlying problem, retaining all versions, models,
advice conditions, and repetitions together. Eight problems are sufficient for
development descriptions, not a powered general efficacy claim; use the pilot
to design a larger fresh-item study if warranted. No post-result exclusions or
selection of the most successful prompt variant.

## Genuinely ambiguous questions are a separate arm

Do not mix deliberately underspecified questions into a binary right/wrong-advice
score. For example, “Mira told Sara that she had won. Who won?” lacks a unique
referent. “The price rose by 20%, then changed by 20%. What is it now?” omits the
direction of the second change. These are different from a clear question that
invites an intuitive mistake.

For a later separate ambiguity arm, permit an explicit “insufficient information”
response or a clarification question. Independently adjudicate acceptable answers
and necessary clarifications. Score recognizing the missing information and
avoiding unsupported certainty, alongside unnecessary abstention on matched
clear controls. A suggestion cannot be called wrong if it is valid under a
permitted interpretation. This arm needs its own reviewed items and response
contract and is not included in the 288-call count.

## Current status

Only this proposal and eight authored candidate sets exist. A masked packet,
independent first-pass review and equivalence review, new disjoint resource
probes, live budget, frozen manifest, and executable runner remain to be built
before collection. The frozen v4 packet, review files, and resource plan remain
unchanged. The broader ambiguity direction is documented separately in
[the earlier ambiguity proposal](RESEARCH_DIRECTION_3_AMBIGUITY.md).
