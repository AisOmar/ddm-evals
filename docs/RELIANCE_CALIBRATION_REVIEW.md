# Current calibration review packet and initial option repair

Use `results/research_directions/reliance_calibration_v2/review_revision/` for
the current question packet. The initial script-54 packet and its hash lock
remain unchanged as historical development artifacts.

The author caught a structural cue before any model calls: probability
distractors used an added 1/97, usually creating a much larger denominator than
the true reduced fraction. A model could exploit that pattern without solving
the problem. Script 55 replaces those twelve distractors with nearby, distinct,
reduced fractions having the **same denominator** as the correct fraction.
Whether the distractor is above or below the key varies independently of answer
position. Question stems, keys, splits and other alternatives are unchanged.
This repair removes that particular cue; it does not prove absence of other
shortcuts or demonstrate meaningful difficulty.

All calibration, delivery, scoring and later-evaluation gates in
[the v2 protocol](RELIANCE_CALIBRATION_V2.md) still apply. No inference was run,
no independent reviewer has assessed the questions, and the larger study remains
paused. `review_revision/readiness.json` is the current preparation status.

## Instructions for a separate reviewer

Read only `review_revision/calibration_masked_review.json` and
`review_revision/reserved_masked_review.json` first. Do not open the answer
packet, generation code, repair log or original development keys until your
initial judgments are saved and locked. The current author has seen those keys
and cannot provide a masked independent assessment in this context.

For each item, record:

- Item ID and the independently derived numerical solution and chosen letter.
- A short derivation that checks both alternatives, or an unresolved judgment.
- Whether the wording has one answer under its stated assumptions.
- Difficulty without tools, and whether the item mainly tests lengthy arithmetic.
- Option cues, ambiguity, redundant variants and mechanism overlap.
- A disposition: retain candidate, repair, replace, or unresolved.

Save a review JSON and its SHA-256 before reading author keys. Do not equate key
agreement with calibrated difficulty or safety validity. The same four templates
span both splits, so reserve agreement does not establish unseen-family transfer.
Adjudicate disagreements and preserve the original judgments before preparing
any exact calibration requests. No delivery-canary or calibration collection is
authorized by completing this review.

## Reproduce the append-only repair

```bash
.venv/bin/python scripts/55_repair_calibration_options.py
```

This checks the initial artifact lock, writes only the new `review_revision`
directory and refuses to overwrite it. The revision has its own lock covering
the repaired packet, masked files, repair log, readiness, this document, repair
script and initial-lock file. Verify both locks; checking the initial version
alone does not verify the repaired options.
