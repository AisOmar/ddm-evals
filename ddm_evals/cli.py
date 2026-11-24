"""The ``ddm-evals`` command.

* ``ddm-evals info``            -- version, checkout location, frozen model and a count of scripts and docs.
* ``ddm-evals list``            -- every pipeline script with the first line of its docstring.
* ``ddm-evals run 117_cost_ledger [args...]`` -- run a script in place (same as ``python scripts/117_cost_ledger.py``).

Scripts that make paid API calls say so in their docstring and in ``docs/PIPELINE.md``; ``run`` does not add any
safeguard of its own.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from collections.abc import Sequence

from .config import load_config
from .paths import DOCS, RESULTS, ROOT, SCRIPTS
from .scripts import find_script, list_scripts


def _version() -> str:
    from . import __version__

    return __version__


def cmd_info(_: argparse.Namespace) -> int:
    cfg = load_config()
    model = cfg.get("model", {})
    scripts = list_scripts()
    numbered = sum(1 for s in scripts if s.number is not None)
    print(f"ddm-evals {_version()}")
    print(f"root      {ROOT}")
    print(f"model     {model.get('name')} (provider {model.get('provider')}, cap {model.get('max_tokens')} tokens)")
    print(f"scripts   {numbered} numbered, {len(scripts) - numbered} shared modules in {SCRIPTS.name}/")
    print(f"docs      {len(list(DOCS.glob('*.md')))} markdown files in {DOCS.name}/")
    print(f"results   {'present' if RESULTS.is_dir() else 'absent'} ({RESULTS.name}/)")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    for script in list_scripts(include_shared=not args.numbered):
        print(f"{script.name:<44} {script.summary}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    script = find_script(args.script)
    folder = str(script.path.parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    sys.argv = [str(script.path), *args.args]
    runpy.run_path(str(script.path), run_name="__main__")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ddm-evals", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    info = sub.add_parser("info", help="show version, checkout location and the frozen model")
    info.set_defaults(func=cmd_info)

    lst = sub.add_parser("list", help="list the pipeline scripts with their one-line summaries")
    lst.add_argument("--numbered", action="store_true", help="hide the shared modules")
    lst.set_defaults(func=cmd_list)

    run = sub.add_parser("run", help="run one script in place; arguments after the name are passed through")
    run.add_argument("script", help="script name or number, e.g. 117_cost_ledger or 117")
    run.add_argument("args", nargs=argparse.REMAINDER, help="arguments for the script")
    run.set_defaults(func=cmd_run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
