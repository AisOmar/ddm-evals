# Held-out reliability wording results

Collection data complete: 2100/2100 valid provider responses. Protocol: docs/CROSS_MODEL_FOLLOWUP.md. Status: complete.

Actual providers: {"Qwen3": ["DeepInfra"], "R1": ["DeepInfra"], "gpt-oss": ["DeepInfra"]}. Reused source responses: 0. New-response API-recorded cost: $2.4278.

Collection audit: 2393 saved attempt files; API error attempts {"429": 191}; 102 partial/non-JSON attempt files. 230 completed trials required retries; maximum successful attempt number 6. Model outcomes: {"answered": 2089, "censored": 6, "refusal": 5}. API errors are not model refusals or resistance.

Operational amendments: docs/CROSS_MODEL_FOLLOWUP_OPERATIONS.md (budget batching) and docs/CROSS_MODEL_RATE_LIMIT_AMENDMENT.md (separate capped zero-usage 429 retries with 15-minute cooldowns). The latter was recorded during collection before any treatment-effect analysis. Statistical rules and prompts were unchanged. Raw failed attempts are retained; only a fully recorded valid response for each planned trial enters the analysis.

Final bounded delivery recovery: docs/CROSS_MODEL_CAPACITY_RECOVERY.md, activated before effect analysis, supersedes the earlier delivery backoff for the original collection. Slow serial requests respect server Retry-After instructions. Statistical and model settings remain unchanged.

Primary complete-answer cohort: 97 of 100 questions. The contrast averages the dose response equally across the two new wordings. Excluded: wmdp-0272, wmdp-0611, wmdp-1618. Non-answers are not treated as resistance.

Primary model × reliability test: {"wald": 9.367550333325903, "df": 2, "p": 0.009244050101756555}

| Model | Average 95%−55% change across new wordings | Pointwise 95% interval |
| --- | --- | --- |
| R1 | +9.8 pp | +5.2 to +14.9 pp |
| Qwen3 | -1.0 pp | -7.2 to +5.2 pp |
| gpt-oss | +9.3 pp | +4.1 to +14.4 pp |

| Pair | Difference in 95%−55% changes | Simultaneous 95% family intervals |
| --- | --- | --- |
| R1 minus Qwen3 | +10.8 pp | +2.6 to +19.6 pp |
| R1 minus gpt-oss | +0.5 pp | -7.2 to +8.8 pp |
| Qwen3 minus gpt-oss | -10.3 pp | -20.1 to -0.5 pp |

## Wording dependence

The following six intervals use Bonferroni-adjusted bootstrap quantiles across six contrasts. These use all available answers and can differ from the selected primary cohort.

| Held-out wording and pair | Dose response difference | Simultaneous interval |
| --- | --- | --- |
| frequency: R1 minus Qwen3 | +9.2 pp | -2.0 to +20.5 pp |
| frequency: R1 minus gpt-oss | -0.0 pp | -12.5 to +12.2 pp |
| frequency: Qwen3 minus gpt-oss | -9.3 pp | -23.0 to +3.0 pp |
| probability: R1 minus Qwen3 | +12.1 pp | -0.9 to +25.2 pp |
| probability: R1 minus gpt-oss | +1.8 pp | -12.0 to +16.0 pp |
| probability: Qwen3 minus gpt-oss | -10.3 pp | -25.0 to +4.0 pp |

## Fresh reference comparison

Same-collection wording contrasts; intervals adjusted across six comparisons.

| Model and wording minus reference | Difference in dose response | Simultaneous interval |
| --- | --- | --- |
| R1: frequency minus reference | -4.9 pp | -14.1 to +3.1 pp |
| R1: probability minus reference | -2.0 pp | -12.5 to +8.1 pp |
| Qwen3: frequency minus reference | -6.0 pp | -19.0 to +7.0 pp |
| Qwen3: probability minus reference | -6.0 pp | -20.0 to +8.0 pp |
| gpt-oss: frequency minus reference | +1.0 pp | -11.8 to +13.5 pp |
| gpt-oss: probability minus reference | +2.0 pp | -10.1 to +13.2 pp |

## Missing outcomes and limitations

Available-answer sensitivity omnibus: {"wald": 9.386173733940755, "df": 2, "p": 0.00915837180198756}.

Worst-case missing-outcome bounds for each average dose response (identification bounds, not confidence intervals):
- R1: +9.0 to +10.5 pp.
- Qwen3: -1.0 to -1.0 pp.
- gpt-oss: +8.5 to +9.5 pp.

Primary complete-answer selection can favor easier questions. These are new wordings on existing questions; they do not establish generalization to unseen tasks. Claimed reliability is not calibrated evidence. No internal mechanism, deception or overall safety ranking is established. The historical comparison was post hoc; only this follow-up protocol preceded its new calls.

API-recorded usage cost of all analysis responses, including reused sources: $2.4278. New-response cost is reported above. Fresh controls, per-wording rates and non-answer counts: rates.csv and runs.csv. Full contrasts, bounds and source hashes: analysis.json. wording_comparison.png displays available-answer rates with pointwise question-bootstrap intervals; these differ from the primary complete-answer cohort.
