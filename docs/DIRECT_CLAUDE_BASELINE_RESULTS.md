# Complete baseline: Sonnet has useful headroom; the pair fails the difficulty gate

October 26, 2026. The direct Anthropic setup completed all 12 resource requests
and all 48 calibration requests. All responses had a recognized visible JSON
answer, matching model identity, normal completion and usage within reservation.
No inference request was retried. No advice requests were sent.

| Model | Correct baseline answers | Factual errors | Unknown | Preset difficulty gate |
| --- | --- | --- | --- | --- |
| Claude Haiku 4.5 | 9/24 (37.5%) | 15 | 0 | Fail: below 55% |
| Claude Sonnet 4.5 | 16/24 (66.7%) | 8 | 0 | Pass: between 55% and 90% |

**Conclusion:** reliable collection is now feasible, and Sonnet has measurable
baseline errors on these questions. Haiku falls below the preregistered
development range, so the proposed pair does not qualify for the planned advice
study. These results do not answer whether treating advice as fallible evidence
reduces wrong-advice errors while preserving correct-advice benefits.

The useful next step is a separately specified Sonnet-only development pilot,
comparing ordinary and explicit fallible-evidence instructions under no advice,
correct advice and wrong advice. Preserve the failed Haiku gate and disclose the
model-selection decision; do not present that pilot as the original two-model
study. A second model would need separate calibration before replication.

These are 12 questions from six template families, each repeated twice per
model. The observations are dependent, not 24 independent question types. The
questions are development material, and Claude participated in earlier review.
The short 128-token JSON response cap and disabled extended thinking are part
of the tested configuration; this is not a general comparison of model ability.
Earlier Qwen/gpt-oss cohorts were neither completed nor pooled into this one.

New spending computed from reported input/output usage and the published
[Anthropic rates](https://platform.claude.com/docs/en/about-claude/pricing)
was **$0.040945**. The cumulative conservative bound is **$0.362735**, including
all earlier unreconciled reservations, below the unchanged $1 limit. All 176
offline tests pass. All 210 protected preparation files and 579 prior locked
artifact entries verified unchanged. No collector or request remains active;
the original large study remains paused.

- [Frozen protocol](DIRECT_CLAUDE_BASELINE_PROTOCOL.md)
- [Analysis and per-item results](../results/research_directions/selective_reliance_focus_20261024/direct_claude_native_20261026/analysis.json)
- [Fixed cohort and reservations](../results/research_directions/selective_reliance_focus_20261024/direct_claude_native_20261026/manifest.json)

An initial token-count connection inside a Python subprocess failed at DNS,
before paid inference. Its artifacts remain in `direct_claude_20261026`; a fresh
native curl handoff performed all token counts and inference for this cohort.
The change was made before freezing the inference manifest. This API/model and
output-format change establishes a separate cohort, not a repair of old scores.
