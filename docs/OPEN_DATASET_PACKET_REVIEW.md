# GSM8K and BIG-Bench Hard: twenty-question development packet

Prepared 2026-10-20. **All 20 questions have an analyst answer derivation and a computational cross-check. All 20 answers match the official dataset keys under the recorded interpretations. Eight stems have explicit clarifications. No model calls were made.** The [separate fresh-context AI review is now complete](OPEN_DATASET_INDEPENDENT_REVIEW.md), with 20/20 answer agreement and no further repairs. Collection remains unapproved; the follow-up records the difficulty/family limits and a smaller feasibility draft.

## Read the questions

The current questions, without answers or analyst judgments, are in [the reviewer packet](../results/research_directions/open_dataset_packet_20261020/v2/reviewer_packet/QUESTIONS.md). Any additional reviewer should read only that directory and lock initial judgments before reading this report or the answer-bearing files. One separate AI review has since been completed; no human expert validation has been performed. Stored preparation-stage flags remain historical; current review status is in `review_followup/readiness.json`.

The complete evidence is under `results/research_directions/open_dataset_packet_20261020/`. The current binary questions and prompts are in its `v2/` directory. Version 1, original source questions, initial analyst judgments, proposed source keys, and the reconciliation are preserved. Version 2 changes one editorial phrase in G05 from asking the question author to ask for a total to instructing the evaluated model to report that total; answer choices and intended answer are unchanged.

## Sources, selection and review

- **GSM8K:** ten questions from the public test split at commit [`3101c7d`](https://github.com/openai/grade-school-math/tree/3101c7d5072418e28b9008a6636bde82a006892c), published by OpenAI with an [MIT license](https://github.com/openai/grade-school-math/blob/3101c7d5072418e28b9008a6636bde82a006892c/LICENSE). Original question and worked-solution files are preserved locally. Attribution: Karl Cobbe et al., *Training Verifiers to Solve Math Word Problems* (2021).
- **BBH:** one question from each of ten objectively checkable task types at commit [`9ee07bd`](https://github.com/suzgunmirac/BIG-Bench-Hard/tree/9ee07bd481feebf959a6b59d61ea57bdcf30964d), whose repository provides an [MIT license](https://github.com/suzgunmirac/BIG-Bench-Hard/blob/9ee07bd481feebf959a6b59d61ea57bdcf30964d/LICENSE). Original task files, including their benchmark canary, are preserved. Attribution: Mirac Suzgun et al., *Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them* (2022), drawing on the BIG-bench collaboration.

Both downloaded license texts are retained in `sources/`. Dataset versions, exact source indices, source URLs and file hashes are recorded. These adaptations add clarifications, reduce alternatives to two, and add suggestions; they are not official GSM8K or BBH benchmark scores.

Selection used a fixed SHA256 ordering with seed `20261020:open-dataset-review-v1`, without evaluated-model outcomes. GSM8K test index 0 was excluded because its question and answer appeared in the discovery preview. BBH selected one item per task, rather than filling the packet with repeated instances of one task. No selected original question exactly matches the normalized stems in the prior WMDP question bank or the earlier twenty revised pilot items. This limited check does not establish absence from all local history or model training.

The AI analyst derived answers from the masked questions and locked twenty initial judgments before comparing with official keys. Programmatic checks use exact rational arithmetic, a restricted arithmetic/Boolean AST evaluator, a bracket stack, date arithmetic, all 120 object-order permutations, vector sums, object counts, state-preserving swaps and word sorting. Dataset text is not passed to `eval` or `exec` and no source-provided code is executed. GSM reductions and selected constraints are grounded by the analyst, so the code is a cross-check of that review, not an independent second reviewer.

## What was clarified

| Item | Clarification |
| --- | --- |
| G01 | The listed transactions are the entire credit-card balance; no other charges or payments. |
| G04 | Count rental instances across exactly eight complete weeks, not distinct physical chairs. |
| G05 | Boxes have equal capacities; report total boxes, including existing boxes. |
| G07 | Explicit US coin denominations, so arithmetic does not rely on implicit locale knowledge. |
| G10 | Insurance is 10% of material plus construction cost, rather than an ambiguous “that.” |
| B02 | The input date means March 5, 1973 in the Gregorian calendar. |
| B03 | Append the shortest closing-bracket-only suffix; whitespace is insignificant. |
| B06 | Directions have a fixed grid heading and equal step lengths. |

These are not eight proven dataset errors. Some are explicit versions of ordinary conventions; others resolve multiple defensible readings. Original conditional judgments remain visible. The two adapted alternatives are distinct and the deliberately incorrect alternative has a recorded error rationale.

## Draft comparison

Each question has three suggestion conditions: none, correct and incorrect. Each is crossed with ordinary answering instructions or explicit instructions to evaluate suggestions as fallible. That produces **20 × 3 × 2 = 120 draft prompts per model**, with no model identifier, provider, price or dispatch configuration selected.

Correct answers appear as A on five of ten GSM8K items and five of ten BBH items, using fixed hash-balanced ordering. The question and option order stay identical across its six conditions. Advice merely suggests a letter; it does not claim a human expert, actual peer-model judgment, or numerical reliability. Condition labels and expected answers stay outside the visible message. The control has no suggestion block.

This is a separate development set. It does not amend the frozen cybersecurity protocol with three advice-source labels, two waves and a conditional 1,000-unit power target. Its prompts cannot be pooled into that study without a new design decision. It measures reasoning under suggestions; it does not yet test an agent taking an unauthorized action or demonstrate overall AI safety.

## Comparison with SycophancyEval

The [author repository](https://github.com/meg-tong/sycophancy-eval) provides factual-answer suggestions, repeated challenges to answers, and feedback tasks. Its [paper](https://arxiv.org/abs/2310.13548) studies matching user views over truth and the possible role of human preferences. That establishes substantial prior overlap; this packet does not discover susceptibility to suggestions.

| Comparison | SycophancyEval | This development packet |
| --- | --- | --- |
| Answer suggestion | Includes a user stating a proposed factual answer. | Uses an unattributed suggested letter, deliberately correct or incorrect. User-belief agreement is not isolated. |
| Reconsideration | Includes a multi-turn challenge to an earlier answer. | Uses fresh contexts for the six conditions; does not measure an individual answer reversal within a conversation. |
| Feedback | Includes free-form argument feedback with user preference cues. | Uses two alternatives and explicit answer derivations; does not evaluate praise or feedback quality. |
| Intended comparison | Varied sycophancy behaviors. | Wrong-suggestion harm, correct-suggestion benefit and ordinary baseline yield, with an explicit-checking instruction contrast. |

These are design comparisons based on the repository documentation and primary paper, not reproduced benchmark results. No SycophancyEval model calls or preference-model training were performed. A defensible extension would test whether the same advice-handling pattern survives reviewed arithmetic and reasoning tasks, while retaining baseline and helpful-advice performance. Claims about user agreement, real expert authority or agent security need their own manipulations.

## Limits and next decision

The analyst provisionally rates ten items easy and ten medium. No hard-item coverage or actual model difficulty has been established. A high baseline could leave little room to detect helpful-advice benefits. Public items may have been memorized; changing wording or numbers alone does not guarantee decontamination. The twenty questions are not established as twenty statistically independent content-family units, and generalization beyond these task families is untested.

The [follow-up](OPEN_DATASET_INDEPENDENT_REVIEW.md) completed the separate masked review and preserved difficulty/family differences before adjudication. It selects sixteen conservative family representatives for a bounded feasibility draft. Exact runtime models, costs, execution configuration and a separate run decision remain pending. Choose a larger sample only after judging whether question coverage and feasibility evidence support it. No large run or sample size is authorized by this packet.

## Files and checks

| File | Purpose |
| --- | --- |
| `selection_manifest.json` | Fixed selection rule, source commits, licenses and source hashes |
| `masked_source_questions.jsonl` | Original selected questions, source answers hidden |
| `initial_analyst_review.json` and `initial_review_lock.json` | Pre-key derivations, assumptions, difficulty, families and hash lock |
| `derivation_checks.json` | Twenty computational cross-checks |
| `key_reconciliation.json` | Twenty source-key agreements, with original caveats retained |
| `v2/binary_items.json` | Adapted questions, two options, truth labels and error rationales |
| `v2/reviewer_packet/` | Twenty questions, blank review form and separate-review instructions without answers |
| `v2/draft_prompts.jsonl` | All 120 draft condition prompts; dispatch disabled |
| `verification.json` | Final source/input integrity and prompt-coverage checks |

Scripts 46–48 perform selection, checked preparation and editorial finalization, respectively. They refuse to overwrite their saved stages and do not contain an experiment runner. All 43 offline tests passed, including seven new checks for safe expression parsing, bracket validity, all twenty derivations, masked-field isolation and exact condition construction. Frozen prior study files and raw responses are checked separately for preservation.
