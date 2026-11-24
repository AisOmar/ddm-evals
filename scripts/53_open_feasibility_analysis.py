"""Offline audit and explicitly exploratory sensitivity checks after all 192 attempts.

Does not change primary scoring, retry requests, or inspect partial collections.
"""
from collections import Counter
from datetime import datetime
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import statistics

from outcomes import parse_answer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('frozen_open_pilot', ROOT / 'scripts/50_open_dataset_feasibility.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def cells(rows):
    result = []
    for model in p.MODELS:
        for instruction in ('ordinary', 'explicit'):
            for advice in ('none', 'correct', 'incorrect'):
                group = [r for r in rows if (r['model'], r['instruction'], r['advice']) == (model, instruction, advice)]
                answered = sum(r['outcome'] == 'answered' for r in group)
                correct = sum(r['correct'] for r in group)
                result.append(dict(model=model, instruction=instruction, advice=advice,
                    n=len(group), n_answered=answered, n_correct=correct,
                    outcomes=dict(Counter(r['outcome'] for r in group)),
                    correct_yield=correct / len(group) if group else None,
                    answered_accuracy=correct / answered if answered else None))
    return result


def common_complete_questions(rows):
    """Keep a question only when all twelve prespecified outputs are answered."""
    expected = {(m, i, a) for m in p.MODELS for i in ('ordinary', 'explicit')
                for a in ('none', 'correct', 'incorrect')}
    retained = []
    for rid in sorted({r['review_id'] for r in rows}):
        group = [r for r in rows if r['review_id'] == rid]
        if (len(group) == 12 and
                {(r['model'], r['instruction'], r['advice']) for r in group} == expected and
                all(r['outcome'] == 'answered' for r in group)):
            retained.append(rid)
    return retained


def audit():
    m = p.manifest()
    if (p.OUT / 'active_batch.json').exists():
        raise ValueError('Collection still active; no partial behavioral analysis')
    trials = {t['sample_id']: t for t in m['trials']}
    ledger = [json.loads(path.read_text()) for path in (p.OUT / 'attempts').glob('*.json')]
    attempts = [rid for batch in ledger for rid in batch['trials']]
    if len(attempts) != 192 or len(set(attempts)) != 192 or set(attempts) != set(trials):
        raise ValueError('All 192 unique attempts must be accounted for first')
    batches = [json.loads(path.read_text()) for path in (p.OUT / 'finished_batches').glob('*.json')]
    finalized = [rid for batch in batches for rid in batch['attempted']]
    if Counter(finalized) != Counter(attempts):
        raise ValueError('Finalized batches do not exactly cover the attempt ledger')
    for batch in batches:
        if not all(batch['raw_exists'].values()):
            raise ValueError('Missing raw output in completed batch')
    for folder in ('raw', 'requests'):
        if {path.stem for path in (p.OUT / folder).glob('*.json')} != set(trials):
            raise ValueError(f'Unexpected or missing {folder} file')
    rows = json.loads((p.OUT / 'runs.json').read_text())
    if len(rows) != 192 or {r['sample_id'] for r in rows} != set(trials):
        raise ValueError('Run primary frozen summary first')
    cost, missing_cost, raw_hashes, request_hashes = Decimal(0), [], {}, {}
    format_diagnostics, wrong_answers = [], []
    for row in rows:
        rid = row['sample_id']
        trial = trials[rid]
        request = p.OUT / 'requests' / (rid + '.json')
        raw = p.OUT / 'raw' / (rid + '.json')
        if json.loads(request.read_text()) != trial['request']:
            raise ValueError('Request differs from frozen manifest')
        data = json.loads(raw.read_text())
        outcome, chosen = p.classify(trial, data)
        if (outcome, chosen, p.sha(raw)) != (row['outcome'], row['chosen'], row['raw_sha256']):
            raise ValueError('Primary row differs from immutable raw response')
        if row['correct'] != (outcome == 'answered' and chosen == trial['correct_letter']):
            raise ValueError('Incorrect primary score')
        raw_hashes[rid] = p.sha(raw)
        request_hashes[rid] = p.sha(request)
        amount = (data.get('usage') or {}).get('cost')
        if amount is None:
            missing_cost.append(rid)
        else:
            amount = Decimal(str(amount))
            if not amount.is_finite() or not 0 <= amount <= p.trial_bound(trial):
                raise ValueError('Invalid recorded cost or reserve exceeded')
            cost += amount
        if outcome == 'format_error':
            text = data['choices'][0]['message'].get('content') or ''
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            legacy = parse_answer(text)
            format_diagnostics.append(dict(sample_id=rid, final_line=lines[-1] if lines else '',
                legacy_parser_letter=legacy, legacy_letter_correct=legacy == trial['correct_letter']))
        if outcome == 'answered' and not row['correct']:
            wrong_answers.append(rid)
    if cost > Decimal(m['maximum_cost_usd']):
        raise ValueError('Total recorded charge exceeds full reserve')
    protected = json.loads((p.OUT / 'protected_inputs_before.json').read_text())['hashes']
    changed = [name for name, digest in protected.items()
               if not (ROOT / name).exists() or p.sha(ROOT / name) != digest]
    if changed:
        raise ValueError(f'Prior study/review artifacts changed: {changed}')
    snapshot = json.loads((p.OUT / 'pre_execution_hashes.json').read_text())
    refreshable = str((p.OUT / 'preflight.json').relative_to(ROOT))
    for name, digest in snapshot.items():
        if name == refreshable:
            if not any(p.sha(path) == digest for path in (p.OUT / 'preflight_history').glob('*.json')):
                raise ValueError('Original preflight not preserved in history')
        elif not (ROOT / name).exists() or p.sha(ROOT / name) != digest:
            raise ValueError(f'Preparation-time artifact changed: {name}')
    old_state = json.loads((ROOT / 'results/deference/trust_planning/orchestration_state.json').read_text())
    if old_state['status'] != 'paused_by_user':
        raise ValueError('Original collection no longer paused')
    common = common_complete_questions(rows)
    durations = []
    for batch in batches:
        source = next(b for b in ledger if b['trials'] == batch['attempted'])
        durations.append(dict(prepared_at=source['prepared_at'], finished_at=batch['finished_at'],
            question_ids=sorted({trials[rid]['review_id'] for rid in batch['attempted']}),
            elapsed_seconds=(datetime.fromisoformat(batch['finished_at']) -
                             datetime.fromisoformat(source['prepared_at'])).total_seconds()))
    token_summary = []
    for model in p.MODELS:
        tokens = [r['usage']['completion_tokens'] for r in rows
                  if r['model'] == model and 'completion_tokens' in r['usage']]
        token_summary.append(dict(model=model, n_with_usage=len(tokens),
            median_completion_tokens=statistics.median(tokens) if tokens else None,
            maximum_completion_tokens=max(tokens) if tokens else None))
    result = dict(created_at=p.now(), manifest_sha256=p.sha(p.OUT / 'manifest.json'),
        n_attempted=192, n_finalized=192, n_raw=192, n_requests=192,
        exact_requests_verified=True, duplicate_attempts=0,
        protected_prior_files_verified=len(protected), preparation_snapshot_verified=True,
        old_study_remains_paused=True, outcomes=dict(Counter(r['outcome'] for r in rows)),
        recorded_cost_usd=str(cost), missing_cost_metadata_ids=missing_cost,
        full_attempt_reserve_usd=m['maximum_cost_usd'],
        batch_durations=sorted(durations, key=lambda b: b['prepared_at']),
        completion_token_summary=token_summary,
        cells=cells(rows), strictly_answered_wrong_ids=wrong_answers,
        exploratory_common_complete_case=dict(posthoc=True, replaces_primary=False,
            selection='All twelve outputs strictly answered; not selected by correctness',
            selection_can_bias_results=True, question_ids=common, n_questions=len(common),
            cells=cells([r for r in rows if r['review_id'] in common])),
        exploratory_format_diagnostics=dict(posthoc=True, replaces_primary=False,
            parser='Existing scripts/outcomes.py.parse_answer, unchanged', rows=format_diagnostics),
        raw_sha256=raw_hashes, request_sha256=request_hashes,
        efficacy_claim_permitted=False, safety_metric_validated=False)
    p.save(p.OUT / 'execution_analysis.json', result)
    print(json.dumps({k: result[k] for k in ('n_attempted', 'outcomes', 'recorded_cost_usd',
          'protected_prior_files_verified', 'strictly_answered_wrong_ids')}, indent=2))


if __name__ == '__main__':
    audit()
