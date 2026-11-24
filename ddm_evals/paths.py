"""Repository locations.

``ROOT`` is the checkout that holds ``config.yaml`` and ``scripts/``. It is found, in order, from the
``DDM_EVALS_ROOT`` environment variable, from the location of this package (an editable install), and from the
current working directory and its parents. Everything else is a fixed sub-folder of ``ROOT``.
"""

from __future__ import annotations

import os
from pathlib import Path


def _is_root(path: Path) -> bool:
    return (path / "config.yaml").is_file() and (path / "scripts").is_dir()


def find_root() -> Path:
    """Return the repository root, see the module docstring for the search order."""
    env = os.environ.get("DDM_EVALS_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve().parent.parent
    if _is_root(here):
        return here
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if _is_root(candidate):
            return candidate
    return here


ROOT: Path = find_root()
CONFIG: Path = ROOT / "config.yaml"
DATA: Path = ROOT / "data"
DOCS: Path = ROOT / "docs"
LOGS: Path = ROOT / "logs"
RESULTS: Path = ROOT / "results"
SCRIPTS: Path = ROOT / "scripts"
TESTS: Path = ROOT / "tests"
