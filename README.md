# ddm-evals

[![CI](https://github.com/AisOmar/ddm-evals/actions/workflows/ci.yml/badge.svg)](https://github.com/AisOmar/ddm-evals/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Does AI reasoning behave like evidence accumulation?** This repository fits drift-diffusion models (DDMs, via
[HSSM](https://github.com/lnccbrown/HSSM)) to a reasoning model's answers and reasoning-token counts, and runs a
series of pre-registered experiments on how a planted answer key changes what DeepSeek-R1-0528, Qwen3-32B and
gpt-oss-120b answer, including a linear probe read along the reasoning trace of Qwen3-32B. It was built during the
BlueDot Impact Technical AI Safety Project programme (2026) and is organised so that every result can be traced to
a protocol written before the data existed, a script, a log and a cost.

The full account is the [final report](docs/FINAL_REPORT.md). The [documentation index](docs/README.md) lists every
protocol and results document, and [`CHANGELOG.md`](CHANGELOG.md) is the dated record of every change.

## Main findings

- **The DDM versus the baseline is inconclusive once likelihoods are matched.** At an 8,192-token cap 43% of R1
  runs hit the cap; the original DDM lost on censoring, and matched-likelihood comparisons tie. A two-process
  mixture is the first model to beat the baseline on held-out questions, and what it finds is task type: compute
  questions censor, recall questions do not. ([final report](docs/FINAL_REPORT.md#summary))
- **Inside the traces the stopping rule is visible, but the first 4,000 tokens predict nothing.** R1 stops when it
  has just stated an answer and no doubt marker follows. ([results/within_trace](results/within_trace/REPORT.md))
- **A planted answer key flips half the questions, and the reasoning says so.** A metadata block naming the wrong
  option moved R1 from 12% to 51% wrong; every flipped run names the key as the reason.
  ([pre-registration](docs/HINT_PREREG.md), [results](results/hint_injection/REPORT.md))
- **Deference to stated reliability is model-specific.** With a readable reliability line R1 weighs the key's
  stated accuracy about one-for-one against its own knowledge, Qwen3-32B ignores it, gpt-oss-120b sits between;
  replicated on held-out wordings, 2,100 calls. ([pre-registration](docs/DEFERENCE_PREREG.md),
  [research report](docs/DEFERENCE_RESEARCH_REPORT.md), [wording follow-up](results/deference/wording_followup/REPORT.md))
- **In Qwen3-32B the key shifts the state before the first reasoning token, washes out, and grows again late.**
  An answer probe trained on control runs reads a prefill shift of .74 logits and a decile-10 shift of .89;
  followed and resisted runs separate only in the last decile. The key's effect is larger when it names option B
  in all three models. ([protocol](docs/OPEN_WEIGHTS_PROBE_PROTOCOL.md), [results](docs/OPEN_WEIGHTS_PROBE_RESULTS.md),
  [letter asymmetry](results/deference/letter_asymmetry/REPORT.md))

Every experiment's calls and cost, computed from the logs, are in [`results/COST_LEDGER.md`](results/COST_LEDGER.md).

## Installation

```bash
git clone https://github.com/AisOmar/ddm-evals.git && cd ddm-evals
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"              # package, offline analyses, pytest, ruff
```

Optional extras: `[fit]` (HSSM, ArviZ, NumPyro for the DDM fits), `[collect]` (Inspect and the provider SDKs for
new data), `[probe]` (torch and transformers for the activation probe), or `[all]`. `pip install -r requirements.txt`
installs the full historical stack; `requirements-probe.txt` is the bare GPU-box install. Python 3.11 or newer.

For new model calls copy `.env.example` to `.env` and add `OPENROUTER_API_KEY`. Nothing in the test-suite or the
offline analyses needs a key.

## Quick start

```bash
ddm-evals info                               # version, checkout, frozen study model, counts
ddm-evals list                               # every script with its one-line summary
make check                                   # ruff + pytest, offline, about ten seconds

python scripts/117_cost_ledger.py            # rebuild the cost ledger from the logs
python scripts/115_letter_asymmetry.py       # letter-asymmetry readout on the saved deference data
ddm-evals run 113_probe_analyze --reuse-scores   # rebuild the probe readouts from saved scores
```

A smoke run of the original pipeline with a mock model and no key:

```bash
python scripts/00_fetch_data.py --dataset cybermetric --size 80
python scripts/01_make_two_choice.py --input data/raw/cybermetric_80.json --format cybermetric
python scripts/02_run_pilot.py --model mockllm/model --limit 20 --epochs 1
python scripts/03_parse_logs.py
```

The step-by-step commands for every experiment, with their dates, costs and `--stage` sequences, are in
[`docs/PIPELINE.md`](docs/PIPELINE.md).

## Repository layout

```
ddm_evals/        the installable package: paths, config loader, script discovery, the ddm-evals command
scripts/          the numbered pipeline (00_fetch_data.py ... 117_cost_ledger.py) and shared modules
tests/            offline test-suite (pytest; tests/package/ covers the package and the frozen-input guard)
docs/             protocols, pre-registrations, results documents, the final report, this runbook
results/          every experiment's outputs: REPORT.md, tables, figures, manifests and hash locks
data/processed/   derived question sets and designs (raw data is fetched, see DATASETS.md)
config.yaml       the study's single source of truth: model, cap, conditions, measurement rules
CHANGELOG.md      dated record of every change, cost and deviation
```

Logs (`logs/`), raw datasets, activation dumps and posterior samples are git-ignored and regenerated by the scripts.

## How the work is organised

| Script family | Numbers | What it does |
|---|---|---|
| Data and pilot | 00–04 | fetch WMDP-cyber or CyberMetric, build the two-choice set, run and parse the Inspect pilot |
| DDM fits, baseline, robustness | 05–11 | HSSM recovery, hierarchical fits, grouped CV, matched-likelihood robustness |
| Design power and recovery screening | 12–16, 19 | simulated follow-up designs, Bayesian design recovery, stratified power |
| Two-process model and task type | 17–18 | the mixture that beats the baseline; compute/recall labels |
| Inside the traces | 20–21 | segment and label hidden reasoning; stopping hazard and trace monitor |
| Hint injection and deference | 22–28 | pre-registered cue experiments on R1, Qwen3-32B and gpt-oss-120b |
| Wording and trust follow-ups | 29–33 | held-out reliability wordings; the frozen correct/wrong-key design |
| Research directions and selective reliance | 34–109 | question packets, independent reviews, calibration and delivery qualification |
| Re-analyses and the open-weights probe | 110–117 | collapsing bound, random slopes, activation probe, letter asymmetry, swap design, cost ledger |

Each experiment follows the same sequence: a protocol under `docs/` written first, a `--stage design` that freezes
the exact requests, a budgeted collection, a parse, and an analysis that writes `results/<experiment>/REPORT.md`.
Scripts, tests and documents that fed a frozen packet are hash-recorded under `results/research_directions/` and
are not edited afterwards; see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the conventions.

## Development

```bash
make test        # pytest; two documented expected failures are explained in conftest.py
make lint        # ruff on the package, conftest.py and tests/package
make format      # apply ruff formatting to those files only
```

Continuous integration runs the same checks on Python 3.11, 3.12 and 3.13 ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
The earlier dated status paragraphs that headed this file are preserved in [`docs/STATUS_LOG.md`](docs/STATUS_LOG.md).

## Citation

See [`CITATION.cff`](CITATION.cff). Please also cite HSSM and the WMDP benchmark if you use the fits or the data.

## Licenses

This repository is released under the [MIT License](LICENSE). Data and dependencies carry their own terms:

- WMDP: MIT. CyberMetric: no license file in repo — email authors before redistributing.
- HSSM: source-available (Brown University license; non-commercial). Cite the HSSM paper.
