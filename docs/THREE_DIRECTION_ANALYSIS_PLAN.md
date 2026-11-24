# Offline Research Plan for Three Follow Up Directions

Recorded before running the new monitoring evaluation on 2026-10-19. Existing treatment effects and qualitative examples have already been inspected. All work is exploratory. Collection remains paused at 623/9,000; no new model requests are authorized by this plan.

## Instruction framing

Research whether an explicit distinction between fallible source content and the task instruction reduces wrong-key following while retaining the benefit of correct keys. Review advice-taking, source-authority, instruction-hierarchy, and epistemic-framing studies. Draft a separate experiment with correct/wrong keys and ordinary versus explicit fallible-evidence instructions. Include controls matched to each instruction condition. Do not describe a reduction in all advice following as selective improvement. Do not modify or replace the paused study's manifest.

## Offline monitoring feasibility

Use the completed wording study's answered frequency/probability hinted trials as training data. Every key there is wrong; the label is observed wrong-key following, which equals a benchmark-incorrect answer in this binary task. It does not identify causal influence on an individual response. Use the 623-response paused snapshot's answered wrong-key frequency/probability trials as the cross-collection test set. Exclude any shared question IDs or normalized question texts. Both collections have already been inspected by the analyst, so this is not a previously untouched confirmation set.

Compare four fixed logistic regressions: model/wording/claimed-reliability context; context plus available-text length; context plus length and uncertainty markers; and context plus length, uncertainty, and source-conflict/task-language markers. Feature definitions use the already observed audit categories. Do not give models the final completion, chosen answer, ground truth, hint letter, correctness, question ID, or outcome. Use fixed C=1 and no hyperparameter search. Fit preprocessing inside each training fold and final training fit.

Evaluate two separately trained modes: full returned reasoning, which is an end-of-trace diagnostic; and the first 80 whitespace-delimited words, restricting eligibility to reasoning longer than 80 words. The latter represents an observation after 80 words for traces that continue, not a monitor available for short traces. Prefix models never receive total future length. No tokenization equivalence to 80 model tokens is claimed.

Use five training folds grouped by question, with all models and conditions for a question in the same fold. Report pooled and per-model AUROC, average precision, Brier score, and log loss, plus precision and recall at a fixed top-20% review budget. Test labels are used only for evaluation. Report question-bootstrap pointwise intervals for test AUROC and Brier differences against context-only prediction, without multiplicity correction. Do not tune on test results, claim a causal detector, or interpret a selective-review metric as an intervention's effectiveness.

## Question ambiguity

Extract the ten questions flagged for perceived option-fit problems in the earlier trace audit and a deterministic random sample of ten other paused-study questions. Produce review packets with original four-option items, the two-choice transformation, and hidden answer keys. A separate key file permits later adjudication. Retain difficult or ambiguous items without changing the frozen study.

Inspect primary references for clear examples of overlapping or context-dependent alternatives. Distinguish source-supported overlap from a model merely claiming that options overlap. A targeted flagged sample cannot estimate benchmark-wide ambiguity prevalence or the relationship between ambiguity and deference. Draft a future paired original/disambiguated experiment with independent item adjudication before any model outcomes are collected.

## Reporting

Produce a comparison of prior work, results of work possible offline, and a separate prospective design for each direction. State unresolved novelty questions and validation needs. Preserve the original frozen manifest and all raw-response hashes; record scripts and analysis hashes. A pilot's sample size is for feasibility, not an assurance of inferential power. No future data collection, intervention efficacy claim, or independent human review is implied by these offline outputs.
