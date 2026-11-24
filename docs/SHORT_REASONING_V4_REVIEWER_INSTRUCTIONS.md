# Independent reviewer instructions for the short reasoning packet

Use a fresh conversation or reviewer without the authoring context. Review only
these files and these instructions:

- [Readable masked questions](../results/research_directions/short_reasoning_v4_20261022/review/questions.md)
- [The same questions as JSON](../results/research_directions/short_reasoning_v4_20261022/review/masked_questions.json)
- [Unfilled review template](../results/research_directions/short_reasoning_v4_20261022/review/review_template.json)

Do not open author solutions, generator source, cohort assignments, resource
request drafts, previous reports, or previous model outputs before saving your
initial review. Save your work in a new file. State reviewer identity, date, and
prior exposure. A fresh AI context is not human expert validation or independent
model training.

For each of the 40 IDs:

1. Solve the literal question independently, before choosing a letter. Give a
   short derivation and the resulting answer, checking units and assumptions.
2. Assess both alternatives. For a “must be true” question, test entailment,
   not just possibility. Use exact fractions where applicable.
3. Record whether exactly one option is supported, the chosen letter, and why
   the other choice fails the question. Flag both-supported, neither-supported,
   or unresolved items without guessing the intended key.
4. Record ambiguities, missing assumptions, answer cues, expected difficulty,
   and estimated reasoning steps. Check whether superficial option ordering or
   size could substitute for solving the task.
5. Identify shared reasoning templates or semantic dependencies. Numerical
   variations are not independent reasoning mechanisms. Assess the whole packet
   for repeated patterns without assuming a particular answer balance.
6. Set disposition to `retain`, `repair`, `exclude`, or `unresolved`; record
   `must_fix` and `unique_supported_answer` as Booleans, using null only for
   unresolved uniqueness. Use `A`, `B`, or null for `chosen_letter`.

Fill the template exactly once for every supplied ID. Preserve uncertainty and
do not silently rewrite any question. Save your complete initial judgments and
any independent calculation code, then save their SHA-256 digests before asking
for author-key comparison. Do not replace the first-pass files after comparison.

After the initial review is locked, the author may compare keys and discuss
disagreements. Save the disagreement record and adjudication separately. Repaired
questions need new versions and another masked validation. Key agreement alone
does not resolve wording or cue concerns. Do not make model calls as part of
this item review.
