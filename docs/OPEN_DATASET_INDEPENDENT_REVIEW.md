# Separate AI review of the twenty-question packet

The fresh-context review is complete: **all 20 adapted questions have one supported alternative, and the reviewer agrees with all 20 analyst answers. No further repair was requested.** This clears the question-answer review gate for feasibility planning. It does not establish a validated safety metric or authorize model calls.

Follow-up: the [192-call feasibility setup](OPEN_DATASET_FEASIBILITY_READINESS.md) now has frozen requests/scoring and a passing live budget/endpoint preflight. No model calls were made; the preparation-stage pending flags below describe this review's original checkpoint.

## Independence and reconciliation

One separate AI reviewer began without the author conversation, answer keys, analyst judgments, checked derivations or model results. The reviewer read only the twenty masked v2 questions and review instructions, derived answers, examined both alternatives, and saved an initial SHA256 lock before comparison. The author then checked input hashes, exact option text, supported letters and both-alternative reasoning against the earlier locked review and computational checks. All twenty agree.

The reviewer independently used bracket matching, all 120 object-order permutations, swap tracking and arithmetic checks. This is fresh-context **AI review**, not human expert validation, independent model training, or proof of absence from pretraining. The local hash locks preserve changed-byte detection and ordering of the recorded workflow; they are not third-party signed timestamps. Original judgments, questions, prompt versions and source keys remain unchanged.

## Findings that change the next step

**Difficulty is limited.** The fresh reviewer rates five questions very easy, thirteen easy, and two moderate: bracket matching B03 and swap tracking B09. The author's initial ten-easy/ten-medium judgments are preserved. The rating scales differ, so these counts are not a formal inter-rater reliability estimate. No evaluated-model accuracy has been collected for this packet. High baseline performance could leave little room for helpful advice to improve it.

**Different stories can share a mechanism.** The review groups G01/G06/G10 as percentage-adjusted cost aggregation and G03/G04/G07 as weighted-count totals. G03/G07 have especially close weighted-sum structure; G04 adds a repetition factor. These are conservative dependency groups rather than claims that every member is a near-identical item. Other tasks use materially different mechanisms, such as fixed-direction navigation, Boolean evaluation and alphabetical ordering.

The adjudication adopts **16 local planning groups** for these exact twenty versions. The mapping is fixed for this draft but does not establish statistical independence or a family map for a larger dataset. Arithmetic primitives, source provenance, response format and possible pretraining exposure remain shared across groups.

## Concrete feasibility draft

The full twenty-question packet is retained. A smaller draft selects one representative from each of the sixteen groups, using a fixed within-group hash ranking before any model outcomes. It uses six GSM8K questions and ten BBH questions; the excluded arithmetic variants remain in the original packet and review record.

| Component | Draft |
| --- | --- |
| Reviewed family representatives | 16 |
| Proposed models | Qwen3 32B and gpt-oss 120B; current endpoint availability unverified |
| Instructions | Ordinary answering / explicitly evaluate fallible suggestions |
| Suggestions | None / correct / incorrect |
| Repeats and waves | One response per cell, one wave |
| Total | **16 × 2 × 2 × 3 = 192 calls** |

The original visible prompts and answer choices are preserved. The draft contains 192 distinct model/condition rows; it has no dispatch permission or verified runtime configuration. Model/provider identity, pricing, a conservative full cost envelope, available budget and exact execution manifest still need verification before a separate decision to run. No API balance was queried and no model call was made in this review.

The proposed feasibility purpose is checking response delivery, answer format and the difficulty ceiling. Report baseline, correct-suggestion and incorrect-suggestion accuracy with all response categories. Describe wrong-advice harm and helpful-advice benefit separately. With sixteen questions per denominator and one response per cell, this is descriptive development work; it does not inherit the earlier large-study power estimate or support an efficacy, equivalence, model-ranking or broad safety claim.

No-advice accuracy of at least 95% is proposed as a ceiling warning, not an outcome-based exclusion rule or a reason to change this set mid-run. A harder future cohort must be separately versioned, reviewed and designed; do not select only questions on which misleading advice or the intervention had a favorable effect.

## Current status

- Fresh-context AI question review: complete, 20/20 answer agreement, no additional repairs.
- Human expert validation: not performed.
- Original twenty questions: preserved; sixteen representatives selected only in the new draft.
- Larger-study sample size: undecided.
- Model experiments: **zero calls launched; original study remains paused**.

The next step is to finalize and budget the separate small feasibility run. Before any larger metric-validation study, the question pool needs harder reviewed material and stronger coverage across content families. An easy reasoning packet can check the workflow without validating a safety measure.

## Evidence

All paths below are relative to `results/research_directions/open_dataset_packet_20261020/`:

- `fresh_ai_review/initial_review.json` and `initial_review_lock.json`: separate initial judgments, both-alternative derivations, exact input hashes, exposure disclosure and original family/difficulty analysis.
- `independent_review_adjudication_rules.json`: rules recorded before inspecting the fresh review.
- `review_followup/adjudication.json`: preserved answer, difficulty and family comparisons.
- `review_followup/families_and_representatives.json`: sixteen planning groups, fixed selection rule and omitted variants.
- `review_followup/feasibility_design_draft.json` / `feasibility_draft_prompts.jsonl`: bounded, non-executable 192-call draft.
- `review_followup/readiness.json` / `verification.json`: question-review completion, preserved-input checks and unfulfilled execution gates.

Script 49 performs the read-only input checks and writes new adjudication/draft artifacts, refusing to overwrite saved outputs. It has no network or model-execution code. Separate integrity tests reject changed reviewer inputs, missing judgments, answer/overlap disagreements, duplicate family membership and changed draft messages.

Final verification: **48 offline tests passed; all 2,620 protected input files are unchanged**. Both frozen study manifests still verify, both initial review locks match, and no collection batch is active. These checks are saved in `review_followup/final_verification.json` and `final_artifact_hashes.json`.
