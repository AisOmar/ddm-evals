"""Load ``config.yaml``, the single source of truth for the study.

The file is read fresh on every call so that a script always sees the current settings. Changing it mid-study
requires a dated note in ``CHANGELOG.md`` (see the comment at the top of the file).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .paths import CONFIG


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Return the parsed study configuration as a dictionary."""
    with open(path or CONFIG, encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path or CONFIG} did not parse to a mapping")
    return loaded
