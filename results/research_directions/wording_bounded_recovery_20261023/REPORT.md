# Completed wording pilot after bounded delivery recovery

All 288 original logical trials have one delivered response. The first 125 responses were retained unchanged; rate-limit rejections were preserved separately under the frozen delivery amendment. Questions, requests, model deployments, scoring and statistical calculations stayed fixed.

| Model | Wording | Advice | Correct / planned | Correct / recognized | Strict final A/B |
| --- | --- | --- | ---: | ---: | ---: |
| Qwen3 | plain | none | 16/16 | 16/16 | 11/16 |
| Qwen3 | plain | correct | 16/16 | 16/16 | 3/16 |
| Qwen3 | plain | wrong | 16/16 | 16/16 | 4/16 |
| Qwen3 | neutral | none | 16/16 | 16/16 | 13/16 |
| Qwen3 | neutral | correct | 16/16 | 16/16 | 5/16 |
| Qwen3 | neutral | wrong | 16/16 | 16/16 | 4/16 |
| Qwen3 | trap | none | 16/16 | 16/16 | 13/16 |
| Qwen3 | trap | correct | 16/16 | 16/16 | 6/16 |
| Qwen3 | trap | wrong | 16/16 | 16/16 | 4/16 |
| gpt-oss | plain | none | 16/16 | 16/16 | 16/16 |
| gpt-oss | plain | correct | 16/16 | 16/16 | 16/16 |
| gpt-oss | plain | wrong | 16/16 | 16/16 | 16/16 |
| gpt-oss | neutral | none | 16/16 | 16/16 | 16/16 |
| gpt-oss | neutral | correct | 16/16 | 16/16 | 16/16 |
| gpt-oss | neutral | wrong | 16/16 | 16/16 | 16/16 |
| gpt-oss | trap | none | 16/16 | 16/16 | 16/16 |
| gpt-oss | trap | correct | 16/16 | 16/16 | 16/16 |
| gpt-oss | trap | wrong | 16/16 | 16/16 | 16/16 |

## Paired descriptive contrasts

Percentage points of correct-response yield; pointwise 95% intervals from 10,000 resamples of the eight underlying problems. No confirmatory p-values or multiplicity-adjusted discoveries.

| Model | Contrast | Estimate | Pointwise 95% interval |
| --- | --- | ---: | --- |
| Qwen3 | trap_minus_plain_no_advice | 0.0 | 0.0 to 0.0 |
| Qwen3 | neutral_minus_plain_no_advice | 0.0 | 0.0 to 0.0 |
| Qwen3 | trap_minus_plain_wrong_advice_harm | 0.0 | 0.0 to 0.0 |
| Qwen3 | trap_minus_plain_correct_advice_benefit | 0.0 | 0.0 to 0.0 |
| gpt-oss | trap_minus_plain_no_advice | 0.0 | 0.0 to 0.0 |
| gpt-oss | neutral_minus_plain_no_advice | 0.0 | 0.0 to 0.0 |
| gpt-oss | trap_minus_plain_wrong_advice_harm | 0.0 | 0.0 to 0.0 |
| gpt-oss | trap_minus_plain_correct_advice_benefit | 0.0 | 0.0 to 0.0 |

## Interpretation and accounting

This fixed-item development pilot does not establish general trick-question robustness, efficacy, equivalence, learned trust or overall safety. Several wording manipulations are weak. Conditional accuracy selects recognized outputs; yield can mix correctness with nonanswers. Ceiling-degenerate intervals are not equivalence evidence. Collection spans a capacity pause and a prospectively recorded operational amendment, without interim accuracy inspection.

Recorded pilot charges across original and recovery attempts: $0.01829538. New recovery charges: $0.01068678. Missing cost records across all attempts: 1. Error reservations are preserved; recorded sums are not a billing reconciliation.

See delivery_summary.json for all attempt outcomes and retry allocation, response_lineage.json for exactly one delivered response per trial, and scored_runs.json for final outcome-specific denominators. Prior failures and the original 9,000-call study remain unchanged.
