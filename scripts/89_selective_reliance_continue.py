"""Continue fixed development phases after calculator-assisted adjudication.

Reuses the preserved planner, transport and analysis. Never edits prior records.
"""
import argparse
from decimal import Decimal
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('continuation_review', ROOT/'scripts/88_selective_reliance_tool_review.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
l = q.l
OLD = l.BASE
BASE = q.BASE
PHASE = 'resource'
OUT = BASE/PHASE


def configure(phase):
    global PHASE, OUT
    PHASE, OUT = phase, BASE/phase
    l.BASE = BASE
    l.configure(phase)


def review_gate():
    l.f.verify(l.PACKET)
    q.verify_lock(OLD/'final_artifact_hashes.json')
    q.manifest()
    q.verify_lock(q.OUT/'tool_result_lock.json')
    q.verify_lock(q.OUT/'INITIAL_SHA256_LOCK.json')
    q.verify_lock(q.OUT/'schema_interpretation_lock.json')
    adjudication = l.c.load(q.OUT/'review_readiness.json')
    if not adjudication['review_gate_passed']:
        raise ValueError('Tool-assisted adjudication failed')
    rows = l.c.load(l.PACKET/'author/packet_with_solutions.json')
    prior = {row['item_id']: row for row in l.c.load(OLD/'review_v3/initial_judgments.json')['items']}
    new = {row['item_id']: row for row in l.c.load(q.OUT/'normalized_judgments.json')['items']}
    expected = set(q.manifest()['ids'])
    if len(new) != 9 or set(new) != expected or len(prior) != 30:
        raise ValueError('Independent review coverage changed')
    calc = l.c.load(q.OUT/'calculator_result.json')
    for row in rows:
        key = row['item_id']
        judgment = new[key] if key in new else prior[key]
        if (judgment['chosen_letter'] != row['correct_letter']
            or judgment['unique_supported_answer'] is not True
            or judgment['must_fix_before_execution'] is not False
            or judgment['disposition'] != 'retain'):
            raise ValueError('Unresolved review case: '+key)
        if key in new and not Fraction(judgment['derived_answer']) == Fraction(calc[key]) == Fraction(row['answer']):
            raise ValueError('Adjudication numerical mismatch: '+key)
    return rows


def freeze():
    l.a.no_other_collection()
    rows = review_gate()
    if PHASE != 'resource':
        l.audit('resource')
    if PHASE == 'pilot':
        l.audit('calibration')
        if not l.c.load(BASE/'calibration/analysis.json')['advice_pilot_supported']:
            raise ValueError('Calibration does not support advice collection')
    pointer = OUT/'preflight_pointer.json'
    state = l.c.load(pointer)
    folder = Path(state['folder'])
    try:
        if not 0 <= l.c.seconds_since(state['created_at']) < 3600:
            raise ValueError('Stale preflight')
        endpoints = {name: l.a.endpoint(l.c.load(folder/(name+'.json')), route[0], route[2]) for name, route in l.ROUTES.items()}
        trials = l.plan(rows, endpoints, PHASE)
        reserve = sum(map(l.p.trial_bound, trials))
        credit = l.c.load(folder/'credits.json')['data']
        available = Decimal(str(credit['total_credits']))-Decimal(str(credit['total_usage']))
        allowance = l.c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0 < reserve <= l.CEILINGS[PHASE] or available < reserve:
            raise ValueError('Phase reserve exceeds cap or available credit')
        if allowance is not None and (not Decimal(str(allowance)).is_finite() or Decimal(str(allowance)) < reserve):
            raise ValueError('Insufficient key allowance')
        review_cost = q.PRIOR_COST+Decimal(l.c.load(q.OUT/'review_readiness.json')['recorded_new_cost_usd'])
        if review_cost > Decimal('.60') or review_cost+sum(l.CEILINGS.values()) > 1:
            raise ValueError('Aggregate development reserve exceeded')
        for name in endpoints:
            l.p.save(OUT/(name+'_endpoints.json'), l.c.load(folder/(name+'.json')))
        inputs = [Path(__file__), ROOT/'scripts/88_selective_reliance_tool_review.py',
                  ROOT/'scripts/85_selective_reliance_launch.py', ROOT/'scripts/84_selective_reliance_focus.py',
                  q.PROTOCOL, ROOT/'docs/SELECTIVE_RELIANCE_FOCUSED_STUDY.md',
                  l.PACKET/'packet_hashes.json', l.PACKET/'author/packet_with_solutions.json',
                  q.OUT/'manifest.json', q.OUT/'INITIAL_SHA256_LOCK.json', q.OUT/'tool_result_lock.json',
                  q.OUT/'initial_judgments.json', q.OUT/'adjudication.json',
                  q.OUT/'normalized_judgments.json', q.OUT/'schema_interpretation_lock.json',
                  q.OUT/'review_readiness.json', ROOT/'scripts/91_selective_reliance_review_schema.py',
                  ROOT/'docs/SELECTIVE_RELIANCE_REVIEW_SCHEMA_INTERPRETATION.md',
                  OLD/'review_v3/INITIAL_SHA256_LOCK.json', OLD/'final_artifact_hashes.json']
        inputs += [ROOT/'scripts'/filename for filename in ('70_wording_collect.py', '63_manageable_collect.py',
                   '60_calibrate_reviewed_packet.py', '58_alternate_provider_canary.py', '56_reliance_canary.py',
                   '54_reliance_calibration.py', '50_open_dataset_feasibility.py')]
        if PHASE != 'resource':
            inputs += [BASE/'resource/manifest.json']+sorted((BASE/'resource/finished').glob('*.json'))
        if PHASE == 'pilot':
            inputs += [BASE/'calibration/analysis.json']
        l.p.save(OUT/'manifest.json', dict(created_at=l.p.now(), phase=PHASE, n_planned=l.N[PHASE],
            preflight_started_at=state['created_at'], trials=trials, endpoint_snapshot=endpoints,
            maximum_cost_usd=str(reserve), cost_cap_usd=str(l.CEILINGS[PHASE]),
            previous_review_cost_usd=str(review_cost), total_development_ceiling_usd='1.00',
            execution_authorization='User: move in, continuing tool-assisted adjudication and gated development phases.',
            max_attempts_per_trial=1, automatic_retries=0, min_interval_seconds=5, timeout_seconds=180,
            independent_review_complete=True, independent_review_kind='21 prior unflagged + 9 calculator-assisted adjudications',
            human_review=False, original_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)): l.p.sha(path) for path in inputs}))
        print(json.dumps(dict(phase=PHASE, n_planned=l.N[PHASE], full_reserve_usd=str(reserve),
                              previous_review_cost_usd=str(review_cost))))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir(): path.unlink()
        folder.rmdir()
        pointer.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(l.N), default='resource')
    parser.add_argument('--stage', choices=('preflight-config', 'freeze', 'prepare', 'finish', 'status', 'calibration-analysis', 'pilot-analysis'), required=True)
    parser.add_argument('--execute-authorized', action='store_true')
    parser.add_argument('--curl-exit', type=int)
    parser.add_argument('--http-status', type=int)
    args = parser.parse_args()
    configure(args.phase)
    if args.stage == 'prepare': l.prepare(args.execute_authorized)
    elif args.stage == 'finish':
        if args.curl_exit is None or args.http_status is None: parser.error('Actual curl/HTTP status required')
        l.finish(args.curl_exit, args.http_status)
    else:
        {'preflight-config': l.c.preflight_config, 'freeze': freeze, 'status': l.status,
         'calibration-analysis': l.calibration_analysis, 'pilot-analysis': l.pilot_analysis}[args.stage]()
