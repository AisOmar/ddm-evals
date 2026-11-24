# Fresh Metric Question Review Instructions

The fresh review queue is `results/research_directions/metric_validation_questions/masked_review_queue.jsonl`. Review it before opening proposed keys, previous study outputs, the pilot, or the exposed analyst's interpretations. Do not copy a public benchmark answer key as independent verification. Use primary references, explicit reasoning, or independently checked computation to establish the answer.

Each item contains its original four alternatives and retained two alternatives. Judge them separately. Record whether the retained pair has exactly one defensible answer, which zero-based index is supported, whether alternatives overlap, whether context is sufficient, and whether software version, implementation, or configuration changes the answer. Preserve an intended answer as distinct from a uniquely defensible answer. Mark unresolved cases rather than forcing a choice.

For factual questions, save the primary URL, relevant version or date, and a brief explanation of the evidence. For computation, save a derivation or independently checked result; do not run unsanitized dataset code or perform actions against systems. For language/library behavior, pin the implementation and reject or repair undefined or unspecified behavior. Review the proposed distractor as carefully as the proposed correct answer.

Assign provisional easy, medium, or hard difficulty before any evaluated-model answers are collected. Explain the rating; task type and text length are only structural proxies. Identify semantic duplicates, question families, and near-identical code templates so repeat instances do not falsely increase the count of independent units. Grouping stored by the queue script is only a heuristic.

Save judgments in a new file with reviewer identity, date, and prior exposure, using `review_template.csv` as a schema. Additional fields should include disposition, reviewer-rated difficulty, evidence version/date, and content-family identifier. Lock initial judgments before comparing against the proposed-key sidecar or another review. Reconcile with sources and preserve disagreements, repairs, exclusions, and validation of rewritten versions.

Do not change frozen source questions, benchmark keys, old study manifests, or old raw responses. A repair belongs in a separate version and needs a new answer validation. If two answers are valid, neither can be called wrong advice in the future factorial. If neither is supported, reject or repair before collection.

A separate AI reviewer should begin without the original conversation, model outputs, previous judgments, and proposed keys. Describe that review as fresh-context AI review, not human expert validation. A human domain reviewer should disclose previous study exposure. No external reviewer has been contacted by these instructions.

Only accepted items with a supported unique answer and a settled content-family assignment can enter a later exact collection manifest. The target is 1,000 distinct units, including 600 computational and 400 recall items with varied pre-outcome difficulty. The current queue has only 446 heuristic recall items, so meeting that target after review is uncertain. Do not relax eligibility or screen items using favorable model outcomes.
