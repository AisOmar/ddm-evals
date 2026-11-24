# Independent review instructions

Provide a fresh reviewer only this file, `review/questions.md` (or its JSON
equivalent) and the blank `review/review_template.json`. Do not include the
study protocol, generator code, author solutions, cohort assignments, prior
model outputs or this authoring conversation. A fresh AI context provides
context independence, not an independently trained reviewer or human review.

For each literal question:

1. Derive the answer before consulting its two alternatives. Record the
   derivation and chosen letter, or null if unresolved.
2. Check whether exactly one alternative is supported. Explain why the other
   fails. Flag missing assumptions, ambiguous wording and neither/both cases.
3. Assess whether the alternative reflects a plausible reasoning error or is
   easily dismissed by sign, range, syntax or wording alone.
4. Assign expected difficulty and record semantic/template overlap with other
   questions. Flag trivial renamed copies and shared answer patterns.
5. Record retain/repair/exclude/unresolved without silently editing questions.

Identify yourself, date the review and disclose prior exposure. Save all initial
judgments and any solver code and record their SHA-256 hashes before author-key
comparison. Key agreement alone is insufficient to approve wording or difficulty.
Preserve disagreements and initial judgments during subsequent adjudication.
Any repair needs a new masked validation. Do not dispatch model requests.
