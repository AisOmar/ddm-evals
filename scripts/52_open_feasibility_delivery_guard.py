"""Continue new trials after recorded 429s; never retry failed trial IDs."""
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
    counts = Counter()
    errors = []
    fatal = []
    cost = Decimal(0)
    attempted = []
    for path in (p.OUT / 'attempts').glob('*.json'):
        attempted += json.loads(path.read_text())['trials']
    if len(attempted) != len(set(attempted)) or not set(attempted) <= {t['sample_id'] for t in m['trials']}:
        raise ValueError('Unknown/duplicate attempt ledger IDs')
    for t in m['trials']:
        path = p.OUT / 'raw' / (t['sample_id'] + '.json')
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
            outcome, _ = p.classify(t, data)
            if outcome == 'api_error' and (data.get('error') or {}).get('code') == 429:
                errors.append(t['sample_id'])
            elif outcome in ('api_error', 'provider_or_model_mismatch', 'output_cap_violation', 'invalid_response'):
                fatal.append(t['sample_id'])
            amount = (data.get('usage') or {}).get('cost')
            if amount is not None:
                charge = Decimal(str(amount))
                if not charge.is_finite() or charge < 0 or charge > p.trial_bound(t):
                    raise RuntimeError('Invalid charge or frozen reserve exceeded')
                cost += charge
        except (ValueError, KeyError, TypeError, AttributeError):
            outcome = 'malformed'
            fatal.append(t['sample_id'])
        counts[outcome] += 1
    for rid in attempted:
        if not (p.OUT / 'raw' / (rid + '.json')).exists():
            fatal.append(rid)
    result = dict(n_attempted=len(attempted), n_raw=sum(counts.values()), outcomes=dict(counts),
        recorded_cost_usd=str(cost), rate_limit_failure_ids=errors, fatal_issue_ids=fatal,
        active_batch=(p.OUT / 'active_batch.json').exists(), treatment_accuracy_not_inspected=True)
    print(json.dumps(result))
    if fatal:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
