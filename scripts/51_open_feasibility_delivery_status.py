"""Read-only delivery checks; never inspect correct/wrong treatment outcomes."""
from collections import Counter
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('open_pilot', ROOT / 'scripts/50_open_dataset_feasibility.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def main():
    m = p.manifest()
    outcomes = Counter()
    recorded_cost = Decimal(0)
    attempted = []
    for path in (p.OUT / 'attempts').glob('*.json'):
        attempted += json.loads(path.read_text())['trials']
    if len(attempted) != len(set(attempted)):
        raise ValueError('Duplicate attempted trial')
    for t in m['trials']:
        path = p.OUT / 'raw' / (t['sample_id'] + '.json')
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
            outcome, _ = p.classify(t, data)
            cost = (data.get('usage') or {}).get('cost')
            if cost is not None:
                charge = Decimal(str(cost))
                if not charge.is_finite() or charge < 0:
                    raise ValueError('Invalid reported charge')
                if charge > p.trial_bound(t):
                    raise RuntimeError('Reported charge exceeds frozen per-attempt reserve')
                recorded_cost += charge
        except (ValueError, TypeError, AttributeError, KeyError):
            outcome = 'malformed'
        outcomes[outcome] += 1
    fatal = ['provider_or_model_mismatch', 'output_cap_violation', 'invalid_response', 'api_error', 'malformed']
    result = dict(n_attempted=len(attempted), n_raw=sum(outcomes.values()), outcomes=dict(outcomes),
                  recorded_cost_usd=str(recorded_cost), fatal_delivery_issue=any(outcomes[x] for x in fatal),
                  active_batch=(p.OUT / 'active_batch.json').exists(), treatment_accuracy_not_inspected=True)
    print(json.dumps(result))
    if result['fatal_delivery_issue']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
