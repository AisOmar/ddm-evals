"""Discover and load the pipeline scripts in ``scripts/``.

The scripts are numbered, stand-alone programs (``24_deference.py``) plus a few shared modules (``outcomes.py``,
``design.py``). Many are recorded by SHA-256 in the manifests under ``results/``, so they are never moved or
renamed into a package; this module loads them in place, the same way the test-suite does.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from .paths import SCRIPTS

_NUMBERED = re.compile(r"^(\d+)_(.+)\.py$")


@dataclass(frozen=True, order=True)
class Script:
    """One file in ``scripts/``."""

    sort_key: tuple[int, int, str]
    name: str
    path: Path
    number: int | None
    summary: str

    def __str__(self) -> str:
        return self.name


def _summary(path: Path) -> str:
    """First line of the module docstring, or an empty string."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return ""
    doc = (ast.get_docstring(tree) or "").strip()
    return doc.splitlines()[0].strip() if doc else ""


def list_scripts(include_shared: bool = True, scripts_dir: Path | None = None) -> list[Script]:
    """All scripts, numbered ones first in numeric order, then the shared modules alphabetically."""
    folder = scripts_dir or SCRIPTS
    found: list[Script] = []
    for path in sorted(folder.glob("*.py")):
        match = _NUMBERED.match(path.name)
        if match:
            number = int(match.group(1))
            found.append(Script((0, number, path.stem), path.stem, path, number, _summary(path)))
        elif include_shared:
            found.append(Script((1, 0, path.stem), path.stem, path, None, _summary(path)))
    return sorted(found)


def find_script(name: str, scripts_dir: Path | None = None) -> Script:
    """Resolve ``"24_deference"``, ``"24_deference.py"`` or the bare number ``"24"`` to one script."""
    wanted = Path(name).name.removesuffix(".py")
    scripts = list_scripts(scripts_dir=scripts_dir)
    exact = [s for s in scripts if s.name == wanted]
    if exact:
        return exact[0]
    if wanted.isdigit():
        by_number = [s for s in scripts if s.number == int(wanted)]
        if len(by_number) == 1:
            return by_number[0]
        if by_number:
            names = ", ".join(s.name for s in by_number)
            raise ValueError(f"{name!r} is ambiguous: {names}")
    raise FileNotFoundError(f"no script matches {name!r} in {scripts_dir or SCRIPTS}")


def load_script(name: str, scripts_dir: Path | None = None) -> ModuleType:
    """Import a script as a module without running its ``__main__`` block.

    ``scripts/`` is put on ``sys.path`` first so that ``from outcomes import parse_answer`` inside a script works.
    """
    script = find_script(name, scripts_dir=scripts_dir)
    folder = str(script.path.parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    module_name = "ddm_evals_script_" + re.sub(r"\W", "_", script.name)
    spec = importlib.util.spec_from_file_location(module_name, script.path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {script.path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
