# Candidate datasets (surveyed 6 Oct 2026)

Criteria: single-answer multiple choice (so a two-choice adaptation is clean), cyber domain,
already wired into `inspect_evals` (so Jess can help and the harness is trusted), enough items
for 300–500 questions after the option-reference audit, and a usable license.

| Dataset | Items | Options | Source | In inspect_evals | License | Option-reference flags* | Verdict |
|---|---|---|---|---|---|---|---|
| **WMDP-cyber** (`cais/wmdp`, config `wmdp-cyber`) | 1,987 | 4 | HuggingFace | `wmdp_cyber` | MIT | not checked here (HF blocked in sandbox) — run `01_make_two_choice.py --audit` | **Primary.** The dangerous-capability eval labs actually use; fields `question, choices, answer`; no topic tags |
| **CyberMetric** (`cybermetric/CyberMetric`) | 80 / 500 / 2,000 / 10,180 | 4 | GitHub JSON | `cybermetric_80/500/2000/10000` | none in repo | 4 / 16 / 70 / 200 | **Backup / second domain.** Answer positions balanced by construction. Knowledge-style questions (NIST-flavored), easier than WMDP; useful if WMDP accuracy is too high for error identifiability, or as a generalization set. License unclear — ask authors before publishing. |
| SecQA (`zefang-liu/secqa`, v1/v2) | ~110 (v1) + ~100 (v2) | 4 | HuggingFace | `sec_qa_v1`, `sec_qa_v2` | CC BY-NC-SA 4.0 | — | Too small for the hierarchy; fine as a sanity set |
| SEvenLLM MCQ (`Multilingual-Multimodal-NLP/SEVENLLM-Dataset`) | ~1,300 (en+zh) | 4 | HuggingFace | `sevenllm_mcq_en` | see repo | — | Chinese/English mix; cyber threat intelligence; possible second domain, lower priority |
| CyberSecEval 4 / CyberSOCEval | few hundred | multi-select | GitHub | `cyberseceval_4_*` | MIT (Meta) | n/a | Multi-correct answers, scored by Jaccard — **not** a two-choice DDM task |
| MMLU computer_security | 100 | 4 | HF | `mmlu` subset | MIT | — | Too small; same format as WMDP, could pad |

\* Count of items where an option text matches "both", "all/none of the above", "A and C", etc. These must be
repaired or excluded before the two-choice conversion (plan 1.2).

## Recommendation

1. **WMDP-cyber** for the pilot and main study. It is the dataset whose score drives safety decisions,
   so the measurement question is asked where it matters.
2. **CyberMetric-2000** as the pre-registered second dataset for a stretch goal: same pipeline, different
   question style. It also gives a fallback if WMDP-cyber accuracy on your chosen model is so high that
   errors are too sparse (plan 3.3). Resolve its license first.
3. Keep SecQA aside as a 100-item smoke test; don't fit on it.

## Known data issues to handle in `01_make_two_choice.py`

- WMDP `answer` is an integer index 0–3 into `choices`; CyberMetric `solution` is a letter into an `answers` dict.
- Both contain options that reference other options; the audit regex catches most, but spot-check 30 flagged items by hand.
- Some WMDP-cyber questions embed code/hex; keep them (they are the realistic part) but record `has_code` as a question-level covariate for later.
- No topic field in either; if you want stratified sampling, annotate (a cheap LLM pass with a fixed taxonomy, then hand-check 50).

## Access notes

- HuggingFace was not reachable from the Claude sandbox; download on your machine or in the Runpod/Vast VM.
- `inspect_evals` pins a dataset revision for WMDP (`7125571f…`) and CyberMetric (`205262c…`); `00_fetch_data.py` uses the same pins so your data matches the public eval.
