"""ddm-evals: does AI reasoning behave like evidence accumulation?

A research codebase that fits drift-diffusion models (via HSSM) to a reasoning model's answers and
reasoning-token counts, and runs the pre-registered deference, probe and follow-up experiments described in
``docs/``. The numbered pipeline lives in ``scripts/``; this package is the small, stable entry point:

* :mod:`ddm_evals.paths` -- where the checkout, data, docs, results and scripts are.
* :mod:`ddm_evals.config` -- load ``config.yaml``, the study's single source of truth.
* :mod:`ddm_evals.scripts` -- discover and load the numbered scripts without turning them into a package.
* :mod:`ddm_evals.cli` -- the ``ddm-evals`` command (``info``, ``list``, ``run``).
"""

from .config import load_config
from .paths import CONFIG, DATA, DOCS, LOGS, RESULTS, ROOT, SCRIPTS
from .scripts import Script, find_script, list_scripts, load_script

__version__ = "0.1.0"

__all__ = [
    "CONFIG",
    "DATA",
    "DOCS",
    "LOGS",
    "RESULTS",
    "ROOT",
    "SCRIPTS",
    "Script",
    "__version__",
    "find_script",
    "list_scripts",
    "load_config",
    "load_script",
]
