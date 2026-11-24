# Developer shortcuts. Everything here runs offline; scripts that make paid API calls are listed in docs/PIPELINE.md.
PY ?= .venv/bin/python

.PHONY: install install-all test lint format check ledger clean

install:            ## editable install with the test and lint tools
	$(PY) -m pip install -e ".[dev]"

install-all:        ## everything, including the HSSM, Inspect and probe stacks
	$(PY) -m pip install -e ".[all]"

test:               ## offline test-suite (pytest; two documented expected failures, see conftest.py)
	$(PY) -m pytest -q

lint:               ## ruff on the package, conftest.py and tests/package
	$(PY) -m ruff check .
	$(PY) -m ruff format --check ddm_evals conftest.py tests/package

format:             ## apply ruff formatting to the linted files only
	$(PY) -m ruff format ddm_evals conftest.py tests/package
	$(PY) -m ruff check --fix .

check: lint test    ## what CI runs

ledger:             ## rebuild results/COST_LEDGER.md from the logs (no API calls)
	$(PY) scripts/117_cost_ledger.py

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -not -path "./.venv*" -exec rm -rf {} +
