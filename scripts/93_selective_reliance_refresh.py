"""Refresh live metadata/credit for a fixed 4096 execution manifest."""
import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('qualified_refresh', ROOT/'scripts/92_selective_reliance_4096.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(r.l.N), required=True)
    parser.add_argument('--stage', choices=('config', 'finish'), required=True)
    args = parser.parse_args()
    r.configure(args.phase)
    (r.l.b.refresh_config if args.stage == 'config' else r.l.b.refresh)()
