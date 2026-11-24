# Alternate provider passes short checks; longer calibration stops

Executed October 20 Boise / October 21 UTC, 2026, after the user authorized the
next steps. **The independent AI review is complete, and the alternate-provider
canary passed. The separate 96-attempt numerical calibration then stopped after
three attempts because of an uncertain delivery timeout.** No complete-cohort
accuracy analysis or advice-effect experiment was performed. The original
9,000-call study remains paused.

## Model access

The separately versioned canary used gpt-oss-120b on **DekaLLM BF16** and
Qwen3-32B on **DeepInfra FP8**, pinned to endpoint tags with fallback disabled.
All twelve trivial arithmetic requests completed, returned correct strictly
formatted answers, and supplied valid usage and costs. There were no rate limits,
retries, truncations, missing costs or identity failures. Recorded cost was
**$0.00042616**, versus the full-cap reserve of $0.00448652.

This establishes successful short-request delivery in that run, not sustained
availability on difficult questions. DekaLLM is a different deployment from the
earlier failing gpt-oss DeepInfra endpoint. These results do not establish that
DeepInfra's shared pool has recovered or that backend behavior is identical.

## Independent review and repairs

A fresh-context AI reviewer received only the 48 masked stems/options, solved
them with independently written computational checks, and saved and locked
initial judgments before author-key comparison. All **48/48** numerical answers
agree. This is AI review, not human expert validation or independently trained
model replication.

The reviewer found a critical answer-position pattern: every six-item family
block originally had B,A,B,A,B,A keys. All 48 therefore received a final initial
repair disposition. Earlier design judgments separately recommended repair of
36 arithmetic-heavy items and retained twelve path items as possible anchors;
these concerns are preserved and not reclassified as broad approval.

The author repaired the position assignment in new append-only drafts. The
current packet is `reviewed_calibration/position_revision/`. Each split/family
has three A and three B answers, and each suffix position has two A and two B
answers across families within a split. All eight block patterns are distinct
and non-alternating. The reviewer verified all 48 remaps using only the revised
masked files and their own locked numerical solutions, with no author-key access.
Stems and numerical alternatives are unchanged.

This resolves the universal parity cue. Complementary and reversed block
relationships remain and are disclosed in the reviewer's locked addendum; no
claim of absence of every positional structure is made. Individual requests do
not expose item IDs, seeds, other questions, keys or the mapping plan.

The reviewer also found narrow template coverage, heavy computation, nearby
numerical distractors and uneven expected difficulty. Only four procedural
families are represented; the reserved split uses the same templates. The author
retained the numerical content specifically to measure its baseline difficulty
and resource burden, despite the initial design-repair recommendations. These
items are not approved as a broad reasoning or safety benchmark.

## Calibration stopped after three attempts

After fresh endpoint, credit and key-allowance checks, script 60 froze the exact
96 no-advice requests: 24 calibration questions × two models × two repetitions.
Temperature was 0.7, completion cap 4,096, and timeout 180 seconds, with serial
dispatch and at least twenty seconds between preparations. Full-cap reserve:
**$0.12139456**, within the $1.00 ceiling and available credit.

All three attempts concerned the first recurrence question; other questions and
families were not reached. No interim factual accuracy was inspected or reported.

| Attempt | Delivery outcome | Recorded cost |
| --- | --- | ---: |
| gpt-oss / DekaLLM, repetition 1 | Normally completed, recognized answer | $0.00045168 |
| Qwen3 / DeepInfra, repetition 1 | Length-stopped at the 4,096-token cap | $0.00115504 |
| Qwen3 / DeepInfra, repetition 2 | Curl exit 28 after 180 seconds; incomplete delivery | Missing |

The third attempt had received HTTP 200 headers, but the response body did not
complete. HTTP 200 alone does not make it a successfully delivered model answer.
It is preserved as **uncertain delivery**, with missing cost metadata, not a
factual wrong answer, completed refusal, or proved provider rate limit. No retry
or preferred-answer replacement was made. The other **93 requests were not sent**.

Recorded calibration cost is **$0.00160672**; combined with the canary, recorded
new cost is **$0.00203288**. The timeout may still have consumed provider resources
or incurred charges, so the recorded sum is not a billing reconciliation. The
full reserve and per-attempt reservations remain saved.

The operational stop guard prevents further preparation under this calibration
manifest. The analysis guard rejects fewer than 96 finalized attempts. Accordingly
there is no baseline accuracy estimate, complete difficulty profile, model
ranking, or advice-effect inference from this partial calibration.

## What this changes

Changing gpt-oss providers resolved the short-canary failure in this run. The
next obstacle is a mix of resource burden and uncertain delivery on a long Qwen
request. One capped response and one timeout on one item cannot establish that
the full packet is too hard or that either model reasons poorly.

Before another calibration version, reduce repetitive bookkeeping in the heavy
templates, independently review those changes, and check long-response handling
on the exact intended deployments. Decide token/time limits before collection;
preserve this incomplete cohort rather than filling its missing cells or tuning
items around a preferred accuracy outcome. The original long study and any
advice-effect collection remain paused/unlaunched.

## Evidence and checks

All paths are under `results/research_directions/reliance_calibration_v2/`:

- `independent_review/`: initial, final, correction, postrepair and structural
  addendum judgments, independent solver/validator and separate SHA256 locks.
- `reviewed_calibration/position_revision/`: current packet, masked packets,
  position mapping and hash lock; all previous drafts remain preserved.
- `alternate_provider_canary/`: frozen requests/endpoints, twelve attempts,
  raw bodies, headers, HTTP/cost/finalization records.
- `baseline_calibration_96/`: frozen 96-request manifest and analysis protocol,
  three attempted/finalized records, raw and partial responses, headers and costs.

All **83 offline tests pass**, including cache-price bounds, provider identity,
masked-review key agreement, position balancing, behavioral-versus-operational
stopping, and rejection of partial-cohort analysis. All 16,919 protected earlier
artifacts remain unchanged. Current execution status and final hash verification
are saved separately from historical readiness snapshots. No request/config is
active, temporary credential files are removed, and no old collection resumed.
