# Instructions for an Independent Question Reviewer

Review only the masked item packet at `results/research_directions/ambiguity_review/masked_items.jsonl`. It contains 20 questions with original four-option and retained two-option alternatives. Do not read study outputs, model explanations, benchmark keys, selection-group labels, previous review notes, or reports containing judgments about these items before saving your initial review.

Assess each retained pair against primary references and the literal stem. Record whether there is exactly one defensible answer, whether alternatives overlap, whether context is sufficient, and whether the answer depends on version or configuration. Separately assess whether an issue already exists in the original four-option item or arises from retaining only two alternatives. Keep factual difficulty separate from ambiguity. An unfamiliar term does not become false solely because one source omits it.

Use `yes`, `no`, or `unclear`, cite supporting sources, state assumptions, and preserve uncertain cases. Where two options are valid or neither is supported, do not force one answer because it sounds like the expected test key. Keep an intended answer distinct from a uniquely defensible one.

For software, note the version and configuration the source describes. For malware, distinguish the analyzed sample, date, and execution stage. For scenarios claiming stealth or lack of attribution, do not infer those properties merely from the name of a technique. This is a question-quality review, not a request to execute attacks, use tools against systems, or develop operational procedures.

The unfilled `independent_review_template.csv` is a schema only; save a new file identifying the actual reviewer and review date. Include an additional field or sidecar listing supported retained option indexes (zero based), with no benchmark-key access. Save initial judgments before any unmasking or discussion with the original analyst. If a second reviewer participates, preserve both reviews before adjudication and report disagreements.

A separate AI reviewer should start without the original conversation or prior labels. An AI review is independent of the original analyst's context, but is not human domain validation. A human reviewer should disclose any prior knowledge of study results. The same original AI analyst's source check is not an independent review.

Collection remains paused. Do not alter the frozen dataset, manifest, or answer keys. Reviewed candidates need a later transparent adjudication and study-specific eligibility decision before any new collection.
