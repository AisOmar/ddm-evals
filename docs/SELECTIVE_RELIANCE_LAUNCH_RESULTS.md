# Focused study launch: review gate did not pass

October 24, 2026. The user authorized launch. The independent AI-review phase
was executed; **resource checks, calibration and advice collection were not
launched because the review gate failed**. No instruction-effect result exists
from this launch. The original study remains paused at 623/9,000 responses.

## What ran

| Review version | Delivery | Recorded cost |
| --- | --- | ---: |
| Haiku, all 30 items | Hit 12,000-token cap; incomplete review | $0.063988 |
| Haiku batches, first ten items | Complete response; no standalone full-packet gate | $0.020867 |
| Haiku batches, second ten items | Hit 4,000-token cap; third batch blocked | $0.023837 |
| Sonnet, all 30 items | Complete response; five key disagreements and four uncertain items | $0.097167 |
| **Total, four API requests** | **All cost metadata present** | **$0.205859** |

All reviewer requests used fresh contexts with masked questions and no author
keys, solutions, earlier reviewer responses or evaluated-model outcomes. The
reviewer models are separate from Qwen3 and gpt-oss. This is AI review, not human
validation. The two delivery amendments were saved before further requests;
failed attempts were preserved rather than overwritten or counted as completed
reviews. The final review's judgments and hashes were locked before comparing
against author keys. No further paid reviewer request is permitted in this launch.

## Why collection stopped

The final review agreed with 25/30 author keys. Disagreements were F001, F007,
F011, F016 and F024. It also marked answer uniqueness uncertain for F004, F021,
F028 and F029, despite retaining their proposed letters. These unresolved cases
cannot supply the required clean review gate.

An exact author computational audit supports the existing keys on all nine
flagged cases. For example, the random-reveal item has nine equiprobable
prize/opened-box pairs after observing an empty box; three put the prize in
box 1, giving 1/3 rather than the reviewer's 1/4. The two-test item with prior
1/5 yields 3/11 rather than 3/7. The review contains arithmetic and conditional-
reasoning mistakes, so disagreement alone does not show that the packet is wrong.

However, **the author audit is not independent semantic adjudication**. It does
not turn the failed gate into a pass. No keys, questions, cohorts or condition
definitions were changed; no items were dropped to force agreement.

## Concrete next step

Obtain an independent tool-assisted or human adjudication of the nine cases,
using the locked initial judgments and reproducible exact calculations. Review
the literal stems, both options and the sampling/intervention assumptions.
Save resolutions separately, preserving every original judgment. Any actual
wording repair needs a new packet version and masked validation.

Only after that gate passes should the 12-call resource check run. The next
48-call baseline calibration and 288-response advice pilot remain conditional
on their respective delivery and difficulty gates. No empirical difficulty,
helpful-advice gain, wrong-advice harm or model comparison is available yet.

## Saved evidence and verification

- [Current launch status](../results/research_directions/selective_reliance_focus_20261024/launch_20261024/final_status.json)
- [Locked final review](../results/research_directions/selective_reliance_focus_20261024/launch_20261024/review_v3/initial_judgments.json)
- [Exact disagreement audit](../results/research_directions/selective_reliance_focus_20261024/launch_20261024/review_adjudication/REPORT.md)
- [Full audit evidence](../results/research_directions/selective_reliance_focus_20261024/launch_20261024/review_adjudication/computational_audit.json)

Live checks found sufficient credit and active intended evaluation deployments;
this does not guarantee future availability. Resource preflight account payloads
and private curl configurations were removed after cancellation. No request or
collector is active. All 210 files protected by the preparation snapshot verify
unchanged; raw files from previous studies were not exhaustively rehashed.
The original packet's preparation-time status remains immutable history; the
linked launch status records execution. The full offline test suite passes
135 tests, including complete condition coverage and fail-stop execution checks.
