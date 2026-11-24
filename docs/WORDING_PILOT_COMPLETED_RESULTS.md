# Completed wording pilot reaches an accuracy ceiling

Completed October 22 Boise / October 23 UTC, 2026. **All 288 logical trials
were delivered, and every answer matched the reviewed key.** Qwen3-32B and
gpt-oss-120b each scored 144/144, including the candidate-trap wordings and
incorrect-advice conditions. The bounded recovery worked; this particular
question packet did not reveal a factual wording or advice effect.

## Main results

Each entry is correct answers out of sixteen fixed responses: eight underlying
questions with two repetitions. All outputs were recognized under the frozen
parser, so correct/planned yield and recognized-answer accuracy coincide here.

| Model | Wording | No advice | Correct advice | Wrong advice |
| --- | --- | ---: | ---: | ---: |
| Qwen3 / DeepInfra FP8 | Plain | 16/16 | 16/16 | 16/16 |
| Qwen3 / DeepInfra FP8 | Neutral paraphrase | 16/16 | 16/16 | 16/16 |
| Qwen3 / DeepInfra FP8 | Candidate trap | 16/16 | 16/16 | 16/16 |
| gpt-oss / DekaLLM BF16 | Plain | 16/16 | 16/16 | 16/16 |
| gpt-oss / DekaLLM BF16 | Neutral paraphrase | 16/16 | 16/16 | 16/16 |
| gpt-oss / DekaLLM BF16 | Candidate trap | 16/16 | 16/16 | 16/16 |

All frozen paired contrasts are zero in this fixed sample: trap-minus-plain
no-advice yield, neutral-minus-plain yield, change in wrong-advice harm and
change in correct-advice benefit. The question-cluster bootstrap intervals
collapse to zero because every observed outcome is correct. **Those degenerate
intervals do not establish equivalence or general immunity to misleading
wording or advice.** There are eight underlying development problems, not
288 independent questions.

Baseline accuracy is already at its ceiling, so correct advice had no observed
mistakes to repair. Incorrect advice produced no observed errors. This is
consistent with correct performance under these specific suggestions, but does
not distinguish broad selective reliance from solving these easy/familiar
questions while ignoring suggestions. Several plain/trap changes were already
flagged as weak during independent review. Public/familiar templates and unknown
training exposure further limit a general robustness interpretation.

## What worked and what did not

The delivery workflow completed the original design. The first 125 valid
responses were retained unchanged, the single confirmed DekaLLM HTTP 429 was
preserved, and only unresolved requests were sent. The old rejected slot
succeeded on its first recovery attempt. The remaining 162 previously unsent
requests also delivered, for 163 new calls with no new rate limits or extra
retries. No refusal, truncation, empty visible answer or unrecognized final line
was among the final 288 responses.

The intended measurement was not discriminating on this packet: it cannot show
whether one wording is harder, whether wrong advice causes harm, or whether
correct advice provides a useful benefit when every cell is already perfect.
This is a development result, not an efficacy test or a validated safety metric.

Strict final-line A/B formatting differed from factual correctness. gpt-oss was
strict in 144/144 responses; Qwen was strict in 63/144. Qwen's other responses
were already recognized by the predeclared forms, such as a letter followed by
the exact option text. No broader parser or hidden-reasoning rescue was added.
The existing detailed table reports formatting separately for every condition.

Optional reasoning-token counts exceeded reported completion counts in 31 final
responses. These accounting inconsistencies remain in the raw data. No visible
token counts, reasoning effort, speed ranking or internal mechanism is inferred
from subtracting those fields.

## Recovery and analysis disclosure

The [bounded recovery amendment](WORDING_BOUNDED_RECOVERY_AMENDMENT.md) was
written and frozen before further inference and before factual accuracy or
contrasts were inspected. It allowed only confirmed provider-identified 429
rejections to be retried, with per-trial/global retry bounds, server-aware
cooldowns, a full-cap reserve and a two-hour wall limit. Exactly one new retry
was needed: recovery of the original rejected slot. Every delivered response,
including any potential wrong answer or behavioral nonanswer, was ineligible
for replacement.

The original requests, questions, model/provider/quantization assignments,
temperature, output cap, option reversal, randomization and statistical code
remained fixed. Collection spans an operational interruption and a separately
recorded delivery amendment; it should not be described as uninterrupted or as
an externally registered confirmatory experiment. The first 125 observations
were preserved, not treated as an independent replication.

The final analysis used the original script 69 calculations: paired contrasts,
10,000 resamples of the eight problems with all conditions/models/repeats kept
together, seed 20261022069, pointwise percentile intervals and no confirmatory
p-values. Completeness and exact response lineage passed before analysis.

## Cost

| Component | Recorded cost |
| --- | ---: |
| Original interrupted pilot | $0.00760860 |
| New recovery calls | $0.01068678 |
| Completed pilot, including all attempts with cost metadata | **$0.01829538** |

The completed pilot cost about **1.83 cents recorded**. The original 429 has no
billed-cost metadata; its maximum reservation is preserved, so the recorded
sum is not a billing reconciliation of that error. All new recovery calls have
cost metadata. The full recovery reserve was $0.14447352, including $0.02072320
for bounded retries, and actual full-cap reservations used were $0.12427496.
All spending bounds remained within the $1 development ceiling. Combined
recorded wording-development spending, including the earlier resource checks
and diagnostics, is $0.02170054, about 2.17 cents.

## What should happen next

Do not scale this packet. Build a separately reviewed set of more discriminating
short reasoning problems with genuinely different reasoning traps, explicit
assumptions and unique supported answers. Avoid returning to long enumeration
or arithmetic bookkeeping. Validate the meaning-preserving wording changes
independently, and assess ordinary difficulty separately from ambiguity.

Use a distinct development calibration cohort to find whether the intended
deployments make enough baseline mistakes for correct advice to help. Freeze
a separate later evaluation set without selecting individual questions for a
favorable treatment effect. Only then choose a fresh pilot and sample size for
the desired wording/advice interaction. Deliberately ambiguous questions still
need their own clarification/acceptable-answer task rather than forced A/B keys.

No new question experiment is launched by this report. The original 9,000-call
study remains paused.

## Saved evidence and validation

Artifacts are under `results/research_directions/wording_bounded_recovery_20261023/`:

- [Detailed results and frozen contrasts](../results/research_directions/wording_bounded_recovery_20261023/REPORT.md)
- `pilot/manifest.json`, requests, reservations, raw bodies, headers, HTTP records,
  finalizations and retry policies for every new attempt.
- `delivery_summary.json`: all 289 original/recovery attempt outcomes, costs,
  retry count and empty unresolved list.
- `scored_runs.json`, `analysis.json` and `response_lineage.json`: complete
  scoring, contrasts and one auditable delivered response per original trial.
- `final_status.json` and `final_artifact_hashes.json`: final completion and
  integrity checks, including prior artifact preservation.

All **123 offline tests pass**. The original 125 retained response hashes and
all prior study/review/resource/diagnostic records verify unchanged. No duplicate
logical response, active request, private credential configuration, extra sample
or original-study restart remains.
