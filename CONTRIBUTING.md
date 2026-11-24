# Contributing

Thanks for looking. This is a research repository: the value is in the pre-registered protocols, the frozen
artifacts and the audit trail as much as in the code. Please read the conventions below before changing anything.

## Set up

```bash
git clone https://github.com/AisOmar/ddm-evals.git && cd ddm-evals
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # package + pytest + ruff; add [fit], [collect], [probe] or [all] as needed
cp .env.example .env             # only if you will make API calls; the file is git-ignored
make check                       # ruff + pytest, offline, about ten seconds
```

`pip install -r requirements.txt` still installs the full historical stack (HSSM, Inspect, torch).

## Run the tests

```bash
make test            # or: python -m pytest -q
```

Everything is offline. Two tests are marked as documented expected failures in `conftest.py`; the reason is written
there and in `CHANGELOG.md` (2026-11-24). Four frozen tests open absolute paths recorded in the hash-locked manifests
(the original checkout path `/Users/aisuluomar/Downloads/ddm-evals` and macOS's `/private/tmp`); on another machine
create both as symlinks to your checkout and to `/tmp`, as `.github/workflows/ci.yml` does, or expect those four to
fail with `FileNotFoundError`. If you add code, add tests under `tests/package/` (or a new
`tests/test_<topic>.py` for a new script) and keep them offline: mock the provider, never call an API.

## Conventions that matter here

1. **Pre-register before collecting.** Every experiment that spends money has a protocol under `docs/` written
   before the first call (`*_PREREG.md`, `*_PROTOCOL.md`, `*_AMENDMENT.md`). Deviations get a dated note.
2. **Date every change in `CHANGELOG.md`.** Newest entry first. Say what changed, why, whether API calls were
   made and what they cost. `config.yaml` is the single source of truth for the study and never changes without
   such a note.
3. **Frozen artifacts are not edited.** Many files in `scripts/`, `tests/` and `docs/` are recorded by SHA-256 in
   manifests under `results/research_directions/`. Editing them silently breaks the audit chain. Add a new script
   with the next free number instead, and if a frozen input genuinely has to change, record the old and new hashes
   and the reason in `CHANGELOG.md` (see the 2026-11-24 entry and `tests/package/test_frozen_inputs.py`).
4. **Scripts are numbered and stand-alone.** `scripts/NN_name.py` with a module docstring whose first line says
   what it does and whether it makes paid calls; `--stage` sub-commands for multi-step pipelines; outputs under
   `results/<experiment>/`. `ddm-evals list` shows the index.
5. **No secrets, no personal data.** `.env` holds API keys and is git-ignored. Raw datasets stay upstream
   (`data/raw/` is ignored; see `DATASETS.md`). Activation dumps (`results/open_weights_probe/*/acts/`) and
   posterior samples (`*.nc`) are regenerated, not committed.
6. **Report what happened.** Negative results, stopped runs and cost overruns are written up with the same care
   as positive ones. Smoke runs are labelled as such and are not findings.

## Pull requests

- One topic per PR; a short description of what changed and which docs or results it touches.
- `make check` passes; new behaviour has a test.
- `CHANGELOG.md` has a dated entry.
- If the PR adds an experiment, link its protocol and state whether any model calls were made.

## Questions

Open an issue. For anything about the study design, the final report (`docs/FINAL_REPORT.md`) is the place to
start, then the protocol for the experiment in question.
