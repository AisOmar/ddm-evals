# Shorter questions reviewed; resource gate still fails on counting

**The new questions were simplified and independently AI-reviewed, but the
representative resource gate did not pass. No calibration questions were sent.**
Qwen reached the token cap on the same small subset-counting resource item at
both 2,048 and 4,096 tokens. Both models normally completed the short recurrence
resource item. These are operational development findings, not baseline accuracy
or advice-effect estimates.

## What changed

The separately versioned packet contains 36 synthetic questions across four
templates: four resource items, sixteen calibration items and sixteen reserved
development items. Resource items are excluded from calibration statistics.

- Recurrences now ask for term 7–10 rather than 35–65.
- Subset questions have twenty three-of-six combinations rather than 2,002
  five-of-fourteen combinations.
- Directed paths use six vertices rather than nine.
- Urn questions use two or three draws and rounded whole percentages rather
  than six draws and long exact fractions. The competing answer uses an incorrect
  with-replacement calculation.

Author keys were cross-checked computationally. A fresh-context AI reviewer read
only masked questions/options, independently solved all 36, checked both options,
and saved an authoritative SHA256 lock before author-key comparison. **All 36
answers agree; there were no unresolved or must-fix blockers.** All nine urn
posteriors and their half-up rounding were checked with exact rational arithmetic.

This is AI review, not human expert validation or independent model training.
Four repeated templates, arithmetic burden, nearby alternatives and unmeasured
difficulty limit broader claims. Some local answer-order structure remains;
individual requests do not reveal IDs, seeds, keys, other questions or mappings.
The reviewer's uppercase `INITIAL_SHA256_LOCK.json` is authoritative; its earlier
lowercase preliminary lock was superseded before author-key comparison.

## Deployment checks

The first read-only preflight did not find the required active deployment pair;
no inference manifest or paid request was produced. Subsequent saved endpoint
snapshots show Qwen/DeepInfra FP8 status -2, while Qwen/Tenstorrent FP8 and
gpt-oss/DekaLLM BF16 were listed active. A recorded pre-execution amendment selected
**Qwen3-32B on Tenstorrent FP8** and **gpt-oss-120b on DekaLLM BF16**.

Both execution versions passed fresh live checks of metadata, supported
parameters, price components, credit and key allowance. Requests pin endpoint
tags, quantization and price ceilings with fallback disabled. These deployment
changes prevent attributing cross-model differences to model weights alone.
The earlier DeepInfra failures and original study were not resumed or repaired.

## Resource checks

Each version planned four resource items × two models, serialized, temperature
0.7, at least five seconds between preparations, with a 180-second timeout and
one attempt per trial. Operational success required a normal stop, recognized
choice and valid identity/usage/cost, **without requiring factual correctness**.
Calibration item inclusion was not selected from model answers.

The first version used 2,048 completion tokens. It stopped after three attempts
when Qwen hit that cap on counting. A single, explicitly recorded requalification
raised the cap to 4,096 for both models, retaining the timeout and total cost
ceiling. It used a new directory and frozen requests; the earlier failure remains
unchanged. Repeated resource items are setup development, not independent
replication or replacement observations. No factual outcomes were used to tune
the packet. The second gate also stopped after three attempts.

| Version | Resource task / deployment | Outcome | Completion tokens | Preparation-to-finalization time |
| --- | --- | --- | ---: | ---: |
| 2,048 cap | Recurrence / gpt-oss DekaLLM | Recognized normal completion | 463 | 23.4 s |
| 2,048 cap | Recurrence / Qwen Tenstorrent | Recognized normal completion | 1,288 | 38.3 s |
| 2,048 cap | Subset count / Qwen Tenstorrent | Length-stopped at cap | 2,048 | 60.6 s |
| 4,096 cap | Recurrence / gpt-oss DekaLLM | Recognized normal completion | 328 | 24.0 s |
| 4,096 cap | Recurrence / Qwen Tenstorrent | Recognized normal completion | 1,173 | 38.0 s |
| 4,096 cap | Subset count / Qwen Tenstorrent | Length-stopped at cap | 4,096 | 148.7 s |

All six calls returned HTTP 200, valid provider/model metadata, usage and cost.
There were no observed 429s, uncertain timeouts or missing cost records in these
new checks. Length stops are censored responses, not scored factual mistakes or
proof the model cannot solve the question. Exact transport/model generation time
is not isolated by the elapsed-time measure.

Each version left five resource requests unsent; the gpt-oss counting item and
both models' path/urn resource items were not reached. **All 64 planned
calibration calls remain unsent**, as do the reserved questions. The two capped
outputs on one item do not establish difficulty across the whole packet or
compare the two models. The fixed resource stop prevented proceeding selectively.

## Cost and preservation

Recorded new costs are $0.00145058 for the 2,048 version and $0.00219948 for the
4,096 version: **$0.00365006 total**, about 0.37 cents. All six attempts have cost
metadata. Full resource reserves of $0.00864300 and $0.01339436 were recorded;
the combined ceiling, including a possible calibration reserve, stayed within
the original $0.60 maximum. No credit purchase or unannounced price increase.

All requests, raw responses, headers, exact outcomes, costs and hash locks are
preserved. No within-version retry, advice request, calibration request or old-study
restart occurred. Credential-bearing curl configurations and temporary account
payloads were removed. Earlier versions and scores remain frozen.

## Meaning and next decision

The shorter recurrence can finish in this setup. But reducing a counting task to
twenty combinations did not make that representative item finish reliably under
the tested budgets. Independent answer-key agreement does not establish suitable
runtime or model difficulty. A short delivery check cannot guarantee resource
adequacy for every task type.

There is **no complete baseline calibration**, helpful-advice benefit estimate,
misleading-advice harm estimate, model ranking or validated safety metric. The
next design should replace enumeration-heavy tasks with short, self-contained
reasoning questions or evaluate a separately specified reasoning-budget mode.
Do not keep raising caps, retry these failed cells, or launch advice work from
this partial resource cohort. Any new setup needs its own review and resource
qualification. The original 9,000-call study remains paused.

## Reproducibility

Artifacts are under `results/research_directions/manageable_calibration_v3_20261021/`:

- `packet.json`, three `*_masked_review.json` files, `packet_hashes.json` and
  `adjudication.json`: fixed cohorts, keys, fresh-review comparison and locks.
- `independent_review/`: independent solver, judgments, summary and authoritative
  uppercase initial lock.
- `resource/`: the first three attempts and frozen 2,048-token setup.
- `execution_4096/resource/`: the three requalification attempts and frozen setup.
- `current_status.json` and `final_artifact_hashes.json`: final verified state.

All **89 offline tests pass**. Integrity checks verify the earlier 17,092-file
snapshot, both new frozen execution inputs, the authoritative question/reviewer
locks, and exact request/raw/header/finalization coverage. Real preparation guards
reject continuing both failed resource versions, and the calibration gate rejects
launching the 64 calls. No batch, request or private configuration remains active.
