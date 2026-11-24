# Pipeline runbook

The detailed, dated run instructions for every stage, moved here from `README.md` on 2026-11-24 and kept as written. Commands assume the editable install in `README.md` (`.venv/bin/python` is the repository's virtual environment). Scripts marked as making paid API calls need `OPENROUTER_API_KEY` in `.env`; everything else runs offline from the saved logs and results. The index of all scripts is at the end.

## 1. Environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # add OPENROUTER_API_KEY (or run a local vLLM endpoint)
```

Verified installs (Python 3.13): `inspect_ai 0.3.277`, `inspect_evals`, `hssm 0.5.0`.

## 2. Get the data

WMDP lives on HuggingFace; CyberMetric lives on GitHub.

```bash
# WMDP-cyber (1,987 items; MIT license). Needs HF access.
python scripts/00_fetch_data.py --dataset wmdp
# CyberMetric (80/500/2000/10000 items; check license — repo has no LICENSE file).
python scripts/00_fetch_data.py --dataset cybermetric --size 2000
```

See `DATASETS.md` for the survey of candidates and why WMDP-cyber is the primary choice.

## 3. Pipeline (matches plan phases)

| Step | Script | Plan phase |
|---|---|---|
| Fetch raw data | `scripts/00_fetch_data.py` | 1.1 |
| Two-choice adaptation + option audit + within-question order balancing | `scripts/01_make_two_choice.py` | 1.2–1.3 |
| Pilot run with Inspect (4 conditions × N repeats, logs reasoning tokens) | `scripts/02_run_pilot.py` | 2 |
| Parse Inspect logs → one row per run, with outcome categories | `scripts/03_parse_logs.py` | 2.3 |
| Exploratory tables/plots | `scripts/04_explore.py` | 3 |
| Parameter & model recovery with HSSM | `scripts/05_recovery.py` | 4 |
| Fit hierarchical DDM | `scripts/06_fit_ddm.py` | 6 |
| Joint lognormal+logistic baseline + grouped CV | `scripts/07_baseline_cv.py` | 7 |

Collection settings live in `config.yaml`; exploratory robustness models have
explicit, separate settings in `scripts/08_robustness.py`.

Smoke test without any API key (20 questions, 1 repeat, mock model):

```bash
python scripts/01_make_two_choice.py --input data/raw/cybermetric_80.json --format cybermetric
python scripts/02_run_pilot.py --model mockllm/model --limit 20 --epochs 1
python scripts/03_parse_logs.py
```

## 4. Offline report verification and robustness

Scripts 00–07 are implemented, including the non-DDM generators, censoring term,
baseline and plots. The historical CV files are preserved; their original SEs
treated repeated trials as independent and their HSSM training likelihood used
an implicit lapse mixture missing from held-out scoring. The updated 07 disables
that default, uses question-level SEs and saves scores for held-out repeats.

```bash
.venv/bin/python scripts/08_robustness.py --stage prepare
.venv/bin/python scripts/09_validate_robustness.py
.venv/bin/python scripts/08_robustness.py --stage fits
.venv/bin/python scripts/08_robustness.py --stage recovery
.venv/bin/python scripts/08_robustness.py --stage summarize
.venv/bin/python scripts/10_update_report.py
```

These commands use existing logs and simulated data, without paid model calls.
The fits compare explicit DDM variants with matching training/scoring likelihoods,
test provider, incomplete-row and token-measurement sensitivity, and estimate a
within-question accuracy–length slope. Posterior files, diagnostics, per-trial
scores and recovery checks are checkpointed under `results/robustness`. Fitting
can take substantial laptop time; `--models` and `--scenarios` select subsets.
Completed labels are reused; changing a model specification requires moving its
specific posterior and score checkpoints before rerunning.
For diagnostic failures, `scripts/11_refine_fits.py --labels LABEL ...` reruns
the same models with longer sampling and archives the original checkpoints;
`--dense-mass` can help baseline fits. Then regenerate recovery summaries and
run `08 --stage summarize` and `10_update_report.py`. The report updater refuses
incomplete fold coverage.

Future collection counterbalances answer position across conditions within each
question/repeat and reverses on the next repeat. Historical logs keep their
recorded order. The cap experiment was exploratory and used correct=A throughout.

## 4b. Design power check for the proposed follow-up (2026-10-09)

`scripts/12_power_simulation.py` asks whether the proposed 400-question, two-repeat,
32,768-cap design can separate a drift-variability DDM from the baseline when the data
look like R1. It simulates from (a) the ddm_sdv + contaminant model at the R1 fold
posterior means, (b) the baseline at its R1 posterior means, and (c) a slow-error
mixture that neither model describes, at 100 and 400 questions with three seeds each,
then reuses the fitting, CV and question-level SE code of `08_robustness.py`.

```bash
.venv/bin/python scripts/12_power_simulation.py --stage calibrate   # generator profiles vs the R1 tables
.venv/bin/python scripts/12_power_simulation.py --stage driver --workers 4   # all fits, ~2 h on 14 cores
.venv/bin/python scripts/12_power_simulation.py --stage summarize   # results/power/power_summary.csv, REPORT.md
```

No model API calls. Outputs are under `results/power`.

## 4c. Replicated recovery screening

The broader offline check is in `scripts/12_design_recovery.py` through
`16_report_design_recovery.py`. It uses joint R1 posterior draws, 20 independent
400-question/two-repeat datasets per scenario, paired token caps, timing/outlier
stresses and two exploratory difficulty regimes. `14_recovery_screen.py` is a
composite-likelihood screen; it is not a validated Bayesian power estimate.
The guarded report builder requires all 320 screening comparisons before writing
[docs/DESIGN_RECOVERY.md](docs/DESIGN_RECOVERY.md). Numerical checks, fitting
failures, question-level score uncertainty and Monte Carlo intervals are retained.
Bayesian confirmation checkpoints and diagnostics are separate; incomplete or
nonconverged fits are not counted as successful recovery. No model API calls.

## 4d. Third candidate and task type (2026-10-12)

`scripts/17_two_process.py` fits a two-process mixture (`two_process` in `08_robustness.py`)
against the baseline and the drift-variability DDM on the R1 step-1 runs and on an
augmented set with the cap-experiment runs; `scripts/18_task_type.py` labels every
question compute/recall from its text (`data/processed/task_type.csv`), and the `_task`
scenarios swap that label in for has_code in all three models.

```bash
.venv/bin/python scripts/18_task_type.py
.venv/bin/python scripts/17_two_process.py --stage cv          # has_code comparisons, ~1.5 h
.venv/bin/python scripts/17_two_process.py --stage task_type   # task-type comparisons, ~1.5 h
.venv/bin/python scripts/17_two_process.py --stage summarize   # results/two_process/REPORT.md
```

No model API calls. Fold scores and posteriors go under `results/robustness`.

## 4e. Stratified follow-up design check (2026-10-12)

`scripts/19_stratified_power.py` simulates the task-type-stratified follow-up of
`docs/FOLLOWUP_PREREG.md` (N compute + 50 recall questions, four conditions, two repeats,
32,768 cap) from the augmented task-type fits, runs the pre-registered primary slope and the
three-model grouped CV on each dataset, and writes the prediction table, truth, power and cost
tables to `results/stratified/REPORT.md`.

```bash
.venv/bin/python scripts/19_stratified_power.py --stage predictions          # prediction table from the posteriors
.venv/bin/python scripts/19_stratified_power.py --stage driver --workers 3   # all fits, ~5 h on 14 cores
.venv/bin/python scripts/19_stratified_power.py --stage summarize            # REPORT.md
```

No model API calls. `--stage ddm_driver --ddm-labels generator:compute:recall:seed` adds the
drift-variability DDM to selected datasets.

## 4f. Inside the traces (2026-10-12)

`scripts/20_trace_segments.py` segments and labels the hidden reasoning of every R1 run
(`data/processed/trace_segments.csv`, `trace_runs.csv`); `scripts/21_within_trace_model.py`
fits the stopping hazard, the flip model and the trace monitor with question effects and
writes `results/within_trace/REPORT.md`. Needs the study tokenizer in the HuggingFace cache
(offline) and the Inspect logs under `logs/`. No model API calls.

```bash
.venv/bin/python scripts/20_trace_segments.py
.venv/bin/python scripts/21_within_trace_model.py        # ~10 min
```

## 4g. Hint-injection faithfulness test (2026-10-12)

`scripts/22_hint_injection.py` runs the pre-registered test in `docs/HINT_PREREG.md`: 100 recall
questions, three arms (control, sycophancy cue, metadata answer-key cue, cue always the wrong option),
R1-0528 pinned to DeepInfra at an 8,192-token cap, then fits the cue-effect model and scores
acknowledgment of the cue in the reasoning. **Makes 300 paid API calls (about $0.85).**

```bash
.venv/bin/python scripts/22_hint_injection.py --stage design
.venv/bin/python scripts/22_hint_injection.py --stage probe      # 6 calls; check provider and cost
.venv/bin/python scripts/22_hint_injection.py --stage run        # remaining calls (OPENROUTER_API_KEY in .env)
.venv/bin/python scripts/22_hint_injection.py --stage parse
.venv/bin/python scripts/22_hint_injection.py --stage analyze    # results/hint_injection/REPORT.md
```

## 4h. Deference experiment: recovery checks (2026-10-13)

`scripts/23_deference_recovery.py` checks the design in `docs/DEFERENCE_PREREG.md` before any call:
Part B simulates the own-knowledge integration test (latent knowledge from control repeats, four cue doses)
and Part A fits starting-point, drift, both and null DDM generators with HSSM (`z ~ cue`, `v ~ cue`, both).
Writes `results/deference/REPORT.md`. No model API calls.

```bash
.venv/bin/python scripts/23_deference_recovery.py --stage calibrate
.venv/bin/python scripts/23_deference_recovery.py --stage integration --know-mean 4.1 --know-sd 3.0 --tag _cal   # ~15 min
.venv/bin/python scripts/23_deference_recovery.py --stage ddm_driver --workers 3                                  # ~1 h, HSSM
.venv/bin/python scripts/23_deference_recovery.py --stage loo && .venv/bin/python scripts/23_deference_recovery.py --stage summarize
```

## 4i. Deference experiment: collection and analysis (2026-10-13)

`scripts/24_deference.py` runs the pre-registered experiment of `docs/DEFERENCE_PREREG.md`: the 100 hint-test recall
questions, three more control repeats and the metadata answer-key cue at stated success-rates .55/.70/.86/.95 (cue always
the wrong option), R1-0528 pinned to DeepInfra at an 8,192-token cap, reusing the hint test's control and 0.86 runs as the
first repeat. Then the joint own-knowledge integration model (A1), the dose-response (A2), three HSSM DDM fits
(A3: `z ~ cue`, `v ~ cue`, both) and descriptives (A4). **Makes 1,000 paid API calls ($3.27 on 2026-10-13).** Outputs under
`results/deference/run/`; `--stage ddm_driver --models Mz_step Mv_step Mzv_step` adds the post-hoc step-coded variants.
`DEFERENCE_VARIANT=replication` in the environment runs the same stages for the replication of pre-registration section 10 (key-audit
wording, doses .55/.95, 400 calls, $1.38 on 2026-10-14; controls reused; outputs under `results/deference/replication/`; `--stage excerpts`
prints the low-dose sample for the hand-label void check, which is read from `hand_labels_low.csv`). `DEFERENCE_VARIANT=peer_tag` runs the
section-12 tag check (same wording with the peer-reviewed tag restored, 200 calls, $0.70 on 2026-10-15; `results/deference/peer_tag/`), and
`scripts/27_tag_contrast.py` fits the registered tag contrast across the two runs (no API calls). `DEFERENCE_VARIANT=model2` runs the second
model (Qwen3-32B on DeepInfra, tokenizer `Qwen/Qwen3-32B`, 800 calls, $0.13 on 2026-10-15; `results/deference/model2/`) and
`DEFERENCE_VARIANT=model3` the third (gpt-oss-120b on DeepInfra, tokenizer `openai/gpt-oss-120b`, 800 calls, $0.03; `results/deference/model3/`);
the `SECOND_MODELS` table at the top of the script adds further models.

```bash
.venv/bin/python scripts/24_deference.py --stage design
.venv/bin/python scripts/24_deference.py --stage probe                    # 6 calls
.venv/bin/python scripts/24_deference.py --stage run --max-connections 6  # OPENROUTER_API_KEY in .env; ~2.5 h
.venv/bin/python scripts/24_deference.py --stage parse
.venv/bin/python scripts/24_deference.py --stage analyze                  # PyMC, ~20 min
.venv/bin/python scripts/24_deference.py --stage ddm_driver               # HSSM, ~15 min on 12 cores
.venv/bin/python scripts/24_deference.py --stage report                   # results/deference/run/REPORT.md
```

## 4j. Cue-wording probe for the deference replication (2026-10-14)

`scripts/25_cue_probe.py` tests three rewordings of the planted key's reliability line (so that R1 cannot read it as a
question-difficulty statistic) on six hint-test questions at doses 0.55 and 0.95, labels every trace, and picks the wording
for the replication registered in `docs/DEFERENCE_PREREG.md` section 10. **Makes 36 paid API calls ($0.12 on 2026-10-14).**
Outputs under `results/deference/cue_probe/`; the hand labels are in `hand_labels.csv`.

```bash
.venv/bin/python scripts/25_cue_probe.py --stage design
.venv/bin/python scripts/25_cue_probe.py --stage run        # OPENROUTER_API_KEY in .env; ~7 min
.venv/bin/python scripts/25_cue_probe.py --stage parse
.venv/bin/python scripts/25_cue_probe.py --stage excerpts   # cue-related sentences per trace, for hand labelling
.venv/bin/python scripts/25_cue_probe.py --stage report     # needs hand_labels.csv; writes REPORT.md
```

## 4k. Joint comparison and held-out reliability wordings (2026-10-16)

Completed: 2,100 fresh responses, all DeepInfra, with a 97-question complete-answer cohort. The model × reliability test gives p=0.00924. The pre-specified R1-minus-Qwen difference in dose response, averaged across two new wordings, is +10.8 percentage points (simultaneous question-bootstrap interval +2.6 to +19.6). Individual-wording contrasts are less precise; R1 versus GPT is inconclusive in this follow-up. Results and figure: `results/deference/wording_followup/REPORT.md`, `wording_comparison.png`. API-recorded response cost $2.43.

`scripts/28_cross_model.py` adds an explicitly post hoc joint comparison of R1's clear-wording replication, Qwen3-32B and gpt-oss-120b. It fits a marginal model × reliability interaction, clusters uncertainty by question across all models/repeats, and uses 20,000 paired question-bootstrap draws for probability-scale contrasts. Outputs: `results/deference/cross_model/REPORT.md`, JSON with input hashes, and CSV tables. No API calls.

```bash
.venv/bin/python scripts/28_cross_model.py
.venv/bin/python -m unittest discover -s tests -v
```

The follow-up in `docs/CROSS_MODEL_FOLLOWUP.md` freezes two new reliability paraphrases before collection, with fresh original-wording references and controls: 2,100 calls across the same 100 questions and three models. This holds out wording, not questions. `docs/CROSS_MODEL_FOLLOWUP_OPERATIONS.md` specifies deterministic batches within existing account credit. `scripts/29_wording_followup.py` freezes exact requests, prepares private curl configurations, retains raw provider responses, resumes missing calls and refuses confirmatory analysis on an incomplete collection.

```bash
.venv/bin/python scripts/29_wording_followup.py --stage design
.venv/bin/python scripts/29_wording_followup.py --stage budget-config
# Execute the printed read-only curl command, then validate its results:
.venv/bin/python scripts/29_wording_followup.py --stage budget
.venv/bin/python scripts/29_wording_followup.py --stage prepare --probe
# Execute the printed curl command; remove its private configuration afterwards.
.venv/bin/python scripts/29_wording_followup.py --stage parse
.venv/bin/python scripts/29_wording_followup.py --stage prepare --batch-size 300
# Execute the printed curl command. Repeat prepare/execute for remaining batches.
.venv/bin/python scripts/29_wording_followup.py --stage analyze
```

The budget preflight artifact records pinned endpoint prices and available credit; requests and protocol hashes are checked on resume. `docs/CROSS_MODEL_RATE_LIMIT_AMENDMENT.md` records the first capacity-retry amendment; `docs/CROSS_MODEL_CAPACITY_RECOVERY.md` records the final slow serial recovery round with server `Retry-After` handling. These were recorded before treatment-effect analysis. An alternate-provider six-call probe is archived separately under `results/deference/wording_provider_replication/PROBE_STATUS.md`; none of its data were used in the completed all-DeepInfra comparison. Results and collection status are under `results/deference/wording_followup/`. Collection is complete only when all 2,100 valid provider responses are recorded; non-answers remain behavioral outcomes, while API errors require retries.

## 4l. Planned correct/wrong-key follow-up on new questions

Protocol: `docs/TRUST_FOLLOWUP.md`. Offline design report: `results/deference/trust_planning/REPORT.md`. This is planning, not a new behavioral result; no collection has been launched.

The design crosses actual key correctness with 55%/95% claimed reliability and two fixed wordings, with two fresh controls per model/question. The primary endpoint is the change in accuracy averaged equally across correct-key and wrong-key conditions. Helpful gains and harmful losses are reported separately. It tests claimed credibility, not learned trust or genuinely calibrated evidence.

The conservative exposure screen leaves 746 unused, unflagged, text-deduplicated recall questions. Seven scenarios × seven candidate sizes × 2,000 simulations recommend **300 new questions / 9,000 calls** under the predeclared central-scenario rule. Estimated R1/GPT primary power is 97.3%/92.9%, but power is poor for smaller effects and Qwen's small net change. At the chosen size, the harder-question stress case drops GPT power to 74.1%; the recommendation is conditional on its assumptions.

Historical-usage forecast: $10.25, doubled hinted usage: $19.15, all-cap/1,024-input-token envelope: $65.79. These use archived endpoint prices, not a live quote or available balance. Correct-key response costs are unobserved. Live pricing, input lengths, balance and bounded retry costs must be checked before collection.

```bash
.venv/bin/python scripts/30_trust_design.py --stage power --reps 2000
.venv/bin/python scripts/30_trust_design.py --stage design
MPLCONFIGDIR=/private/tmp/ddm-mpl-cache .venv/bin/python -m unittest discover -s tests -q
```

The design stage freezes selected questions and all 9,000 exact requests in `results/deference/trust_planning/manifest.json`, with protocol, code, source, exposure-record and planning hashes. It refuses to overwrite an existing manifest. The script has no API collection stage. Primary uncertainty is clustered by question; null effects are not interpreted as equivalence or proof of appropriate trust.

### Collection readiness (2026-10-17)

`scripts/31_trust_collect.py` implements resumable collection under `docs/TRUST_COLLECTION_OPERATIONS.md`. A live preflight found healthy DeepInfra endpoints and a $75.59 full-success envelope; with the $5 bounded retry reserve, required account credit is **$80.59**. Available credit is **$2.50**, so collection has **not started (0/9,000)**. The separate API-key allowance is sufficient at the check. No credit was purchased. The live preflight artifact records its timestamp, public endpoint metadata and manifest/operations/runner hashes; account credentials and private curl configurations are removed after use.

```bash
.venv/bin/python scripts/31_trust_collect.py --stage preflight-config
# Execute the printed read-only curl command, then:
.venv/bin/python scripts/31_trust_collect.py --stage preflight
.venv/bin/python scripts/31_trust_collect.py --stage prepare --batch-size 100
# Only after budget passes: execute the printed model-request curl command.
# Wait for curl to exit, then remove its private configuration:
.venv/bin/python scripts/31_trust_collect.py --stage finish-batch
.venv/bin/python scripts/31_trust_collect.py --stage status
```

Refresh preflight before each batch. Prepared/running batches block overlap. Model/provider mismatches, duplicate valid responses, changed requests and stale preflights require resolution before continuation. Refusals and non-answers count as delivered responses and are never retried for a preferred answer. Provider errors have bounded retries and a 429 cooldown respecting Retry-After. The runner does not issue treatment-effect inference; implement and verify the predeclared analysis before reporting any experiment findings. Status and budget shortfall: `results/deference/trust_planning/COLLECTION.md`.

Funding was refreshed later on October 17: account $82.50; required $80.59; preflight passed and the first 100 requests were launched. `scripts/33_trust_analysis.py` now implements the predeclared endpoints, paired bootstrap interval families, common-cohort rule, helpful/harmful secondary outcomes and missingness sensitivities. Its inference guard rejects an incomplete collection. Synthetic analysis tests bring the total to 22 passing offline checks. No treatment effects were inspected while collecting.

`scripts/32_trust_driver.py` can sequence preflight/prepare/curl/finish batches and run the analysis after completion from a terminal with network access. In a managed environment where child curl processes cannot resolve network hosts, execute the printed curl commands through the approved network tool instead; the same sequential batch and hash checks apply. Current delivery status is in `collection_status.json`; tool-managed orchestration status is in `orchestration_state.json` when present. A stopped driver or incomplete status requires resuming the same manifest, not creating a new sample.

After all 9,000 responses exist, `.venv/bin/python scripts/33_trust_analysis.py` writes `REPORT_RESULTS.md`, `analysis.json`, scored runs, outcome/rate tables and separate interval-family CSVs. The planning `REPORT.md` remains separate from actual findings.

## Script index

Generated with `ddm-evals list` (first line of each module docstring). Scripts that make paid calls say so here and refuse to run without a key in `.env`.

| Script | What it does |
|---|---|
| `00_fetch_data` | Fetch raw datasets at the same revisions inspect_evals pins. |
| `01_make_two_choice` | Two-choice adaptation (plan v2, 1.2-1.4). |
| `02_run_pilot` | Run the 2x2 pilot with Inspect AI (plan v2, phase 2). |
| `03_parse_logs` | Parse Inspect logs into one row per run (plan 2.3 deliverable: pilot.csv). |
| `04_explore` | Exploratory look (plan v2, phase 3). Tables + conditional plots. Nothing here is a hypothesis test. |
| `05_recovery` | Recovery simulations (plan v2, phase 4), calibrated to the 2026-10-07 pilot. |
| `06_fit_ddm` | Fit the hierarchical DDM to real pilot/full data (plan v2, phase 6). |
| `07_baseline_cv` | Joint baseline + grouped cross-validation (plan v2, phase 7). |
| `08_robustness` | Offline report corrections and checkpointed Bayesian sensitivity analyses. |
| `09_validate_robustness` | Numerical and design checks required before interpreting new fits. |
| `10_update_report` | Insert completed robustness results into the requested final report. |
| `11_refine_fits` | Refine selected diagnostic failures without discarding the original fits. |
| `12_design_recovery` | Replicated, pilot-calibrated model recovery. Offline: never calls an API. |
| `12_power_simulation` | Realistic design power check for the proposed follow-up study. No API calls. |
| `13_validate_design_recovery` | Independent numerical and design checks for replicated recovery screening. |
| `14_recovery_screen` | Replicated composite-likelihood SCREENING, not full Bayesian power. |
| `15_bayesian_design_recovery` | Full hierarchical Bayesian confirmation of two preselected recovery cases. |
| `16_report_design_recovery` | Build a guarded report of complete replicated screening, not Bayesian power. |
| `17_two_process` | Third candidate on the R1 data: a two-process mixture against the baseline and the |
| `18_task_type` | Task-type labels for the two-choice questions (2026-10-12). |
| `19_stratified_power` | Design check for the task-type-stratified follow-up (2026-10-12). |
| `20_trace_segments` | Segment and label the R1 hidden reasoning traces (2026-10-12). |
| `21_within_trace_model` | Within-trace models on the segmented R1 reasoning traces (2026-10-12). |
| `22_hint_injection` | Hint-injection faithfulness test on DeepSeek-R1-0528 (pre-registered in docs/HINT_PREREG.md). |
| `23_deference_recovery` | Recovery checks for the planned deference experiment (no API calls). |
| `24_deference` | Deference experiment on DeepSeek-R1-0528 (pre-registered in docs/DEFERENCE_PREREG.md). |
| `25_cue_probe` | Probe of unambiguous reliability cues for the deference replication (step 1 of the 2026-10-14 plan). |
| `27_tag_contrast` | Section-12 contrast: the effect of the <peer-reviewed>true</peer-reviewed> tag on following the planted key, holding the key-audit wording fixed. |
| `28_cross_model` | Post hoc joint model comparison; no model API calls. |
| `29_wording_followup` | Frozen wording generalization study; see docs/CROSS_MODEL_FOLLOWUP.md. |
| `30_trust_design` | Offline planning for correct/wrong keys crossed with claimed reliability. |
| `31_trust_collect` | Resumable delivery for the frozen trust experiment; no automatic API spending. |
| `32_trust_driver` | Run sequential budget-checked batches for the already frozen trust study. |
| `33_trust_analysis` | Frozen trust-study endpoints; inference is blocked until every response exists. |
| `34_exploratory_paused` | Offline exploratory audit of the user-paused trust study; never collects data. |
| `35_trace_audit_sample` | Select a fixed, metadata-masked qualitative sample without network access. |
| `36_trace_audit_labels` | First-pass qualitative annotations; refuses to overwrite existing labels. |
| `37_summarize_trace_audit` | Join saved first-pass labels to scores after masked annotation is complete. |
| `38_monitor_feasibility` | Offline, exploratory prediction of observed wrong-key following. |
| `39_ambiguity_review_packet` | Offline item-review packet with benchmark keys and flag status in a sidecar. |
| `40_source_review_items` | Save same-analyst primary-source item assessments, not independent reviews. |
| `41_reviewed_pilot` | Separate bounded feasibility pilot; never resumes the frozen 9,000-call study. |
| `42_metric_validation_plan` | Offline scoring and conditional power planning; contains no model-call client. |
| `43_fresh_metric_questions` | Build an unreviewed fresh candidate queue, excluding prior results and plans. |
| `44_metric_question_screen` | Offline structural screening only: never adjudicates benchmark answers. |
| `45_metric_review_derivations` | Check selected reviewer-authored derivations; never execute dataset code. |
| `46_open_dataset_packet` | Build a separate, offline GSM8K/BBH development packet, never collect. |
| `47_check_open_packet` | Check the locked 20-item analyst review, then build review-only prompts. |
| `48_finalize_open_packet` | Finalize a review-only packet; preserve version 1 and all initial judgments. |
| `49_adjudicate_open_packet` | Reconcile locked AI reviews and prepare a non-executable feasibility draft. |
| `50_open_dataset_feasibility` | Separate bounded pilot: offline planning/scoring and explicit curl handoff. |
| `51_open_feasibility_delivery_status` | Read-only delivery checks; never inspect correct/wrong treatment outcomes. |
| `52_open_feasibility_delivery_guard` | Continue new trials after recorded 429s; never retry failed trial IDs. |
| `53_open_feasibility_analysis` | Offline audit and explicitly exploratory sensitivity checks after all 192 attempts. |
| `54_reliance_calibration` | Offline v2 development packet; no network, credentials, or inference dispatch. |
| `55_repair_calibration_options` | Append-only option repair; preserve script 54's initial locked development draft. |
| `56_reliance_canary` | One-attempt, serial delivery canary; explicit curl handoff, never retries. |
| `57_calibration_author_audit` | Unblinded author audit of visible stems; not independent semantic review. |
| `58_alternate_provider_canary` | Versioned mixed-provider canary; reuse tested serial/ledger guards unchanged. |
| `59_adjudicate_calibration_review` | Compare locked blind judgments and repair only option-position patterns. |
| `60_calibrate_reviewed_packet` | Fixed 96-call no-advice calibration after blind review and delivery gates. |
| `61_analyze_baseline_calibration` | Complete-cohort, descriptive numerical calibration; no partial inference. |
| `62_manageable_packet` | New, shorter synthetic tasks; never modifies earlier versions or calls models. |
| `63_manageable_collect` | Two-stage versioned collection: 8 resource checks, then 64 baseline trials. |
| `64_manageable_analysis` | Complete-cohort descriptive analysis for the separate manageable packet. |
| `65_manageable_tenstorrent` | Explicit pre-execution deployment amendment after inactive Qwen preflight. |
| `66_manageable_4096` | One bounded resource requalification with a 4096-token cap; preserve 2048 run. |
| `67_short_reasoning_packet` | Build an offline, masked development packet. Never calls a model or overwrites files. |
| `68_wording_packet` | Create the wording pilot's masked packet and fixed design without model calls. |
| `69_wording_analysis` | Frozen descriptive analysis; rejects incomplete or operationally failed pilots. |
| `70_wording_collect` | Separate guarded wording collector; reuses preserved transport/scoring helpers. |
| `72_qwen_delivery_diagnostic` | Bounded three-mode diagnostic; preserves the failed wording experiment. |
| `73_qwen_diagnostic_report` | Audit all attempted diagnostic trials and report visible-answer delivery by mode. |
| `74_qwen_provider_comparison` | Twelve paired delivery probes on DeepInfra FP8 and Tenstorrent FP8. |
| `75_qwen_provider_report` | Audit the fixed paired provider cohort and report delivery without accuracy claims. |
| `76_deepinfra_resource_packet` | Eight fresh resource probes, masked for review; no model calls or overwrites. |
| `77_deepinfra_resource_collect` | Independent-review-gated, fresh 16-call resource check on DeepInfra/DekaLLM. |
| `78_deepinfra_resource_report` | Integrity audit and resource-only report; never infers wording/advice effects. |
| `79_deepinfra_wording_pilot` | Freeze/collect the authorized 288-call pilot after reviewed resource qualification. |
| `80_deepinfra_wording_analysis` | Use the frozen original analysis unchanged on the qualified DeepInfra version. |
| `81_deepinfra_wording_delivery_report` | Audit a stopped pilot cohort and report operations only, without accuracy inspection. |
| `82_wording_bounded_recovery` | Immutable-request recovery of rejected/unsent trials; never repeats a delivered answer. |
| `83_wording_recovery_analysis` | Complete-cohort analysis with original statistics and explicit retry/cost lineage. |
| `84_selective_reliance_focus` | Offline development packet for a focused fallible-evidence instruction study. |
| `85_selective_reliance_launch` | Staged, review-gated execution for the October 24 focused study. |
| `86_selective_reliance_review` | One-attempt compact masked-review batches; curl handoff only. |
| `87_selective_reliance_review_audit` | Audit reviewer disagreements without changing keys or declaring review passed. |
| `88_selective_reliance_tool_review` | Two-round masked adjudication with a restricted exact rational calculator. |
| `89_selective_reliance_continue` | Continue fixed development phases after calculator-assisted adjudication. |
| `90_selective_reliance_label_adapter` | Normalize only exact item-ID or item-ID_final calculator result labels. |
| `91_selective_reliance_review_schema` | Strict, recorded interpretation of an affirmative but nonstandard review schema. |
| `92_selective_reliance_4096` | One separately versioned resource qualification and gated development at 4096. |
| `93_selective_reliance_refresh` | Refresh live metadata/credit for a fixed 4096 execution manifest. |
| `94_stream_transport` | Strict OpenRouter SSE reconstruction; no network, scoring or answer rescue. |
| `95_stream_collection` | Qualify SSE delivery, then send only previously unsent calibration slots. |
| `97_http2_stream_collection` | Versioned HTTP/2 transport; identical SSE parser and model requests. |
| `98_complete_calibration` | Finish unsent calibration slots; retain complete behavioral nonanswers. |
| `99_rate_limit_calibration_recovery` | Bounded confirmed-429 recovery; one retained outcome per fixed cohort slot. |
| `100_alternate_deployment_calibration` | Fresh, separate development calibration on active alternate deployments. |
| `101_direct_claude_baseline` | Separate direct API baseline; fixed cohorts, no automatic inference retries. |
| `102_sonnet_advice_pilot` | Frozen Sonnet-only descriptive pilot with matched current controls. |
| `103_verification_transfer_packet` | Exact offline construction of six new local reasoning-template families. |
| `104_verification_transfer` | Bounded three-prompt development and frozen fresh-family transfer study. |
| `105_advice_timing_packet` | Fresh instances of six previously checked mathematical families. |
| `106_advice_timing` | Fixed paired timing study: advice before or after recorded first answers. |
| `107_separate_difficulty_packet` | Offline levels with practice/reserved allocation fixed before calibration. |
| `108_separate_difficulty` | Calibrate only practice items; deterministically freeze untested items. |
| `109_complete_reserved_review` | One prospectively bounded completion of truncated quality-review output. |
| `110_angle_collapsing_bound` | Collapsing-bound (angle) likelihood on the augmented R1 data (docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md, part A). |
| `111_deference_random_slope` | Per-question cue slope in the deference DDM fits (docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md, part B). |
| `112_probe_collect` | Collect Qwen3 reasoning traces with residual-stream activations (docs/OPEN_WEIGHTS_PROBE_PROTOCOL.md). |
| `113_probe_analyze` | Answer probe across the reasoning trace (docs/OPEN_WEIGHTS_PROBE_PROTOCOL.md): probes, decile curves, rules, report. |
| `114_probe_followup` | Follow-up readouts on the saved Qwen3-32B probe run (docs/OPEN_WEIGHTS_PROBE_FOLLOWUP_PROTOCOL.md, 2026-11-22). |
| `115_letter_asymmetry` | Key effect and control error by the letter the key names, for every deference dataset on disk (added 2026-11-22 |
| `116_deference_swap` | Swapped-option re-run of the readable-cue deference design (docs/DEFERENCE_SWAP_AMENDMENT.md, 2026-11-22). |
| `117_cost_ledger` | Cost ledger from the raw API logs (added 2026-11-22 for the BlueDot grant accounting). No model calls. |
| `ddm_censoring` | Analytical censoring term for the DDM: log P(T > C | v, a, z, t)  (plan 4.1 / 6.2). |
| `design` | Reproducible option counterbalancing for future collections. |
| `diffusion_likelihood` | Stable analytical symmetric DDM / normally varying drift likelihoods. |
| `lan_censoring` | Censoring term for network (LAN) likelihoods: log P(T > C | params), by quadrature on the network density. |
| `outcomes` | Shared answer parsing and outcome classification (plan v2, 2.3). |
| `recovery_marginal` | Fast population-parameter fits for replicated model-recovery screening. |
