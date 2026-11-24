"""Qualify SSE delivery, then send only previously unsent calibration slots."""
import argparse
from collections import Counter
import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/filename)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


r = module('stream_execution_helpers', '92_selective_reliance_4096.py')
s = module('strict_stream_parser', '94_stream_transport.py')
l, p, a, c, b = r.l, r.l.p, r.l.a, r.l.c, r.l.b
PREVIOUS = r.BASE
BASE = l.PACKET/'stream_transport_20261025'
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_STREAM_RECOVERY.md'
N = dict(qualification=12, calibration=46, pilot=288)
CAPS = dict(qualification=Decimal('.03'), calibration=Decimal('.10'), pilot=Decimal('.45'))
PRIOR_COST = Decimal('.30809061')
ALIASES = {'qwen/qwen3-32b': ['qwen/qwen3-32b-04-28'], 'openai/gpt-oss-120b': []}
PHASE, OUT = 'qualification', BASE/'qualification'


def configure(phase):
    global PHASE, OUT
    PHASE, OUT = phase, BASE/phase
    a.ROUTES = dict(l.ROUTES)
    c.OUT, b.OUT = OUT, OUT
    c.manifest = manifest
    b.manifest = manifest


def verify_hashes(mapping):
    for name, expected in mapping.items():
        if p.sha(ROOT/name) != expected: raise ValueError('Frozen artifact changed: '+name)


def manifest():
    m = c.load(OUT/'manifest.json')
    verify_hashes(m['input_hashes'])
    if m['phase'] != PHASE or len(m['trials']) != N[PHASE] or len({t['sample_id'] for t in m['trials']}) != N[PHASE]:
        raise ValueError('Incorrect manifest coverage')
    return m


def original_calibration():
    m = c.load(PREVIOUS/'calibration/manifest.json')
    verify_hashes(m['input_hashes'])
    paths = sorted((PREVIOUS/'calibration/finished').glob('*.json'))
    indexed = {c.load(path)['sample_id']: path for path in paths}
    if len(indexed) != 2 or set(indexed) != {t['sample_id'] for t in m['trials'][:2]}:
        raise ValueError('Expected the exact two original attempts')
    if [c.load(indexed[t['sample_id']])['outcome']['status'] for t in m['trials'][:2]] != ['answered', 'uncertain_delivery']:
        raise ValueError('Original observation states changed')
    return m, indexed


def plan(phase, endpoints):
    retained = []
    if phase == 'qualification':
        trials = copy.deepcopy(c.load(PREVIOUS/'resource/manifest.json')['trials'])
    elif phase == 'calibration':
        source, indexed = original_calibration()
        trials = copy.deepcopy(source['trials'][2:])
        for trial in source['trials'][:2]:
            rid = trial['sample_id']
            retained.append(dict(sample_id=rid, trial=trial,
                finished_path=str(indexed[rid].relative_to(ROOT)),
                finished_sha256=p.sha(indexed[rid]), transport='original_nonstreaming', resend_permitted=False))
    else:
        trials = r.plan(r.c.review_gate(), endpoints, 'pilot')
    for trial in trials:
        trial['request']['stream'] = True
        ep = endpoints[trial['model']]
        if trial['request']['max_tokens'] != 4096 or ep.get('max_completion_tokens', 0) < 4096:
            raise ValueError('Unexpected or unsupported output budget')
        if ep.get('context_length', 0) < p.input_bound(trial['request']['messages'])+4096:
            raise ValueError('Insufficient context capacity')
        trial['model_aliases'] = ALIASES[trial['request']['model']]
    if len(trials) != N[phase]: raise ValueError('Wrong new-request count')
    return trials, retained


def audit(phase, complete=True):
    folder = BASE/phase
    m = c.load(folder/'manifest.json'); verify_hashes(m['input_hashes'])
    attempts = [c.load(path) for path in sorted((folder/'attempts').glob('*.json'))]
    if [row['sample_id'] for row in attempts] != [t['sample_id'] for t in m['trials'][:len(attempts)]]:
        raise ValueError('Attempt order changed')
    finals = {row['sample_id']: row for row in (c.load(path) for path in (folder/'finished').glob('*.json'))}
    if set(finals) != {row['sample_id'] for row in attempts}: raise ValueError('Finalization coverage mismatch')
    if complete and len(finals) != N[phase]: raise ValueError('Complete fixed cohort required')
    for rid, final in finals.items():
        if complete and not final['continue_permitted']: raise ValueError('New transport phase failed')
        for directory, suffix, key in [('requests', '.json', 'request_sha256'), ('raw', '.sse', 'raw_sha256'),
                                        ('headers', '.txt', 'headers_sha256')]:
            if p.sha(folder/directory/(rid+suffix)) != final[key]: raise ValueError('Attempt artifact changed')
        trial = next(t for t in m['trials'] if t['sample_id'] == rid)
        if c.load(folder/'requests'/(rid+'.json')) != trial['request']: raise ValueError('Request changed')
        if final['normalized_sha256'] and p.sha(folder/'normalized'/(rid+'.json')) != final['normalized_sha256']:
            raise ValueError('Reconstructed response changed')
    return m, finals


def freeze():
    a.no_other_collection(); r.c.review_gate()
    verify_hashes(c.load(PREVIOUS/'final_artifact_hashes.json'))
    if PHASE != 'qualification': audit('qualification')
    if PHASE == 'pilot':
        audit('calibration')
        if not c.load(BASE/'calibration/analysis.json')['advice_pilot_supported']:
            raise ValueError('Calibration does not support advice work')
    state = c.load(OUT/'preflight_pointer.json'); folder = Path(state['folder'])
    try:
        if not 0 <= c.seconds_since(state['created_at']) < 3600: raise ValueError('Stale preflight')
        endpoints = {name: a.endpoint(c.load(folder/(name+'.json')), route[0], route[2]) for name, route in l.ROUTES.items()}
        original = c.load(PREVIOUS/'calibration/manifest.json')
        for name, ep in endpoints.items():
            for key in ('provider_name', 'name', 'quantization', 'pricing', 'context_length', 'max_completion_tokens'):
                if ep.get(key) != original['endpoint_snapshot'][name].get(key): raise ValueError('Endpoint drift: '+name+'/'+key)
        trials, retained = plan(PHASE, endpoints)
        reserve = sum(map(p.trial_bound, trials))
        credit = c.load(folder/'credits.json')['data']; allowance = c.load(folder/'allowance.json')['data'].get('limit_remaining')
        available = Decimal(str(credit['total_credits']))-Decimal(str(credit['total_usage']))
        if not available.is_finite() or not 0 < reserve <= CAPS[PHASE] or available < reserve:
            raise ValueError('Insufficient phase reserve or credit')
        if allowance is not None and (not Decimal(str(allowance)).is_finite() or Decimal(str(allowance)) < reserve):
            raise ValueError('Insufficient key allowance')
        if PRIOR_COST+sum(CAPS.values()) > 1: raise ValueError('Aggregate development ceiling exceeded')
        for name in endpoints: p.save(OUT/(name+'_endpoints.json'), c.load(folder/(name+'.json')))
        paths = [Path(__file__), ROOT/'scripts/94_stream_transport.py', PROTOCOL,
            ROOT/'scripts/92_selective_reliance_4096.py', ROOT/'scripts/89_selective_reliance_continue.py',
            ROOT/'scripts/85_selective_reliance_launch.py', ROOT/'scripts/84_selective_reliance_focus.py',
            PREVIOUS/'final_artifact_hashes.json', PREVIOUS/'calibration/manifest.json',
            PREVIOUS/'delivery_diagnostic/billing_reconciliation.json',
            l.PACKET/'author/packet_with_solutions.json', l.PACKET/'design_draft.json',
            r.c.q.OUT/'schema_interpretation_lock.json', r.c.q.OUT/'review_readiness.json']
        paths += [ROOT/'scripts'/name for name in ('54_reliance_calibration.py', '56_reliance_canary.py',
                    '58_alternate_provider_canary.py', '50_open_dataset_feasibility.py', '60_calibrate_reviewed_packet.py')]
        paths += [ROOT/row['finished_path'] for row in retained]
        if PHASE != 'qualification':
            paths += [BASE/'qualification/manifest.json']+sorted((BASE/'qualification/finished').glob('*.json'))
        if PHASE == 'pilot': paths += [BASE/'calibration/analysis.json']
        p.save(OUT/'manifest.json', dict(created_at=p.now(), preflight_started_at=state['created_at'],
            phase=PHASE, n_new_planned=N[PHASE], cohort_planned=48 if PHASE == 'calibration' else N[PHASE],
            trials=trials, retained=retained, endpoint_snapshot=endpoints,
            maximum_cost_usd=str(reserve), cost_cap_usd=str(CAPS[PHASE]),
            previous_recorded_cost_usd=str(PRIOR_COST), total_development_ceiling_usd='1.00',
            max_attempts_per_trial=1, automatic_retries=0, timeout_seconds=180, minimum_start_interval_seconds=5,
            authorization='User: okay do that, referring to delivery qualification and calibration continuation.',
            input_hashes={str(path.relative_to(ROOT)): p.sha(path) for path in paths}, original_study_remains_paused=True))
        print(json.dumps(dict(phase=PHASE, new_calls=N[PHASE], retained=len(retained), full_reserve_usd=str(reserve))))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir(): path.unlink()
        folder.rmdir(); (OUT/'preflight_pointer.json').unlink()


def prepare(authorized):
    if not authorized: raise ValueError('Authorized flag required')
    if (OUT/'active.json').exists(): raise ValueError('Unresolved attempt')
    a.no_other_collection(); m = manifest()
    checked = m['preflight_started_at']
    for path in sorted((OUT/'preflight_refreshes').glob('*.json')):
        refresh = c.load(path)
        if refresh['passed'] and refresh['manifest_sha256'] == p.sha(OUT/'manifest.json'): checked = refresh['checked_at']
    if not 0 <= c.seconds_since(checked) < 3600: raise ValueError('Preflight stale; refresh required')
    attempts = [c.load(path) for path in sorted((OUT/'attempts').glob('*.json'))]
    if [row['sample_id'] for row in attempts] != [t['sample_id'] for t in m['trials'][:len(attempts)]]:
        raise ValueError('Attempt ledger changed')
    for attempt in attempts:
        final = OUT/'finished'/(attempt['sample_id']+'.json')
        if not final.exists() or not c.load(final)['continue_permitted']: raise ValueError('Prior attempt failed; stop')
    if len(attempts) == N[PHASE]: print('Phase complete; no new request'); return
    if attempts:
        delay = 5-c.seconds_since(attempts[-1]['prepared_at'])
        if delay > 0: time.sleep(min(delay+.02, 5.02))
    trial = m['trials'][len(attempts)]; rid = trial['sample_id']
    request = OUT/'requests'/(rid+'.json'); p.save(request, trial['request'])
    for directory in ('raw', 'headers', 'http', 'normalized', 'parser_audit'): (OUT/directory).mkdir(parents=True, exist_ok=True)
    attempt = dict(sample_id=rid, prepared_at=p.now(), manifest_sha256=p.sha(OUT/'manifest.json'),
                   request_sha256=p.sha(request), reserved_cost_usd=str(p.trial_bound(trial)), curl_no_buffer=True)
    p.save(OUT/'attempts'/f'{len(attempts)+1:03}.json', attempt); p.save(OUT/'active.json', attempt)
    config = p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+p.key(), 'Content-Type: application/json'], data_binary='@'+str(request),
        output=OUT/'raw'/(rid+'.sse'), dump_header=OUT/'headers'/(rid+'.txt'),
        write_out='%{http_code}', max_time=180, connect_timeout=20)])
    with Path(config).open('a') as file: file.write('no-buffer\n')
    p.save(OUT/'private_pointer.json', dict(config=config))
    print('curl --config '+config)


def finish(exitcode, http):
    m = manifest(); attempt = c.load(OUT/'active.json'); rid = attempt['sample_id']
    trial = next(t for t in m['trials'] if t['sample_id'] == rid)
    raw, headers = OUT/'raw'/(rid+'.sse'), OUT/'headers'/(rid+'.txt')
    normalized, parser_error, parser_audit = None, None, None
    scored = dict(status='uncertain_delivery', choice=None, correct=None, strict_format=None)
    if exitcode == 0 and http == 200:
        try:
            normalized, parser_audit = s.reconstruct(raw.read_bytes(), trial['request']['model'],
                                                    trial['expected_provider'], trial['model_aliases'])
            scored = a.result(trial, normalized, http)
            p.save(OUT/'normalized'/(rid+'.json'), normalized)
            p.save(OUT/'parser_audit'/(rid+'.json'), parser_audit)
        except (s.StreamFailure, OSError, ValueError) as error:
            parser_error = str(error)
            scored['status'] = 'stream_failure'
    elif http == 429: scored['status'] = 'rate_limited'
    elif http not in (0, 200): scored['status'] = 'http_error'
    amount = normalized.get('usage', {}).get('cost') if normalized else None
    try: charge = Decimal(str(amount))
    except Exception: charge = Decimal('NaN')
    cost_ok = charge.is_finite() and 0 <= charge <= p.trial_bound(trial)
    continued = exitcode == 0 and http == 200 and scored['status'] == 'answered' and cost_ok and headers.exists()
    final = dict(**attempt, finished_at=p.now(), curl_exit=exitcode, http_status=http, outcome=scored,
        continue_permitted=continued, retry_permitted=False, parser_error=parser_error,
        cost_within_reserve=cost_ok, recorded_cost_usd=str(charge) if charge.is_finite() else None,
        raw_sha256=p.sha(raw) if raw.exists() else None, headers_sha256=p.sha(headers) if headers.exists() else None,
        normalized_sha256=p.sha(OUT/'normalized'/(rid+'.json')) if normalized else None,
        generation_id=normalized.get('id') if normalized else None)
    p.save(OUT/'finished'/(rid+'.json'), final)
    p.save(OUT/'http'/(rid+'.json'), dict(curl_exit=exitcode, http_status=http))
    pointer = OUT/'private_pointer.json'
    if pointer.exists(): Path(c.load(pointer)['config']).unlink(missing_ok=True); pointer.unlink()
    (OUT/'active.json').unlink()
    print(json.dumps(dict(sample_id=rid, status=scored['status'], continue_permitted=continued,
                          parser_error=parser_error, accuracy_not_reported=True)))


def status():
    m = manifest(); rows = [c.load(path) for path in (OUT/'finished').glob('*.json')]
    print(json.dumps(dict(phase=PHASE, planned_new=N[PHASE], attempted=len(list((OUT/'attempts').glob('*.json'))),
        finalized=len(rows), retained=len(m['retained']), outcomes=dict(Counter(row['outcome']['status'] for row in rows)),
        stopped=any(not row['continue_permitted'] for row in rows), active_attempt=(OUT/'active.json').exists(),
        recorded_new_cost_usd=str(sum((Decimal(row['recorded_cost_usd']) for row in rows if row['recorded_cost_usd'] is not None), Decimal(0))),
        original_study_remains_paused=True), indent=2))


def calibration_analysis():
    m, finals = audit('calibration')
    observations = [(trial, finals[trial['sample_id']]) for trial in m['trials']]
    for source in m['retained']:
        if p.sha(ROOT/source['finished_path']) != source['finished_sha256']: raise ValueError('Retained observation changed')
        observations.append((source['trial'], c.load(ROOT/source['finished_path'])))
    if len(observations) != 48 or len({t['sample_id'] for t, _ in observations}) != 48:
        raise ValueError('Full 48-slot lineage required')
    models = []
    for model in l.ROUTES:
        selected = [(t, final) for t, final in observations if t['model'] == model]
        answered = [(t, final) for t, final in selected if final['outcome']['status'] == 'answered']
        correct = sum(final['outcome']['correct'] is True for _, final in answered)
        factual_errors = len(answered)-correct; missing = len(selected)-len(answered)
        accuracy = correct/len(answered) if answered else None
        eligible = accuracy is not None and .55 <= accuracy <= .90 and factual_errors > 0 and missing/len(selected) <= .05
        models.append(dict(model=model, planned=len(selected), recognized=len(answered), correct=correct,
            factual_errors=factual_errors, unknown=missing, recognized_answer_accuracy=accuracy,
            correct_yield=correct/len(selected), factual_accuracy_bounds=[correct/len(selected), (correct+missing)/len(selected)],
            development_difficulty_supported=eligible,
            item_results=[dict(item_id=t['item_id'], family=t['family'], repeat=t['repeat'], outcome=final['outcome']) for t, final in selected]))
    result = dict(created_at=p.now(), planned_slots=48, newly_attempted=46, retained_slots=2,
        original_missing_answer_preserved=True, mixed_transport_development_cohort=True,
        advice_pilot_supported=all(row['development_difficulty_supported'] for row in models), models=models,
        inference='Descriptive development only; no efficacy or safety claim.', original_study_remains_paused=True)
    p.save(OUT/'analysis.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'models'}, indent=2))
    for row in models: print(json.dumps({k: v for k, v in row.items() if k != 'item_results'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(N), default='qualification')
    parser.add_argument('--stage', choices=('preflight-config', 'freeze', 'prepare', 'finish', 'status', 'refresh-config', 'refresh', 'calibration-analysis'), required=True)
    parser.add_argument('--execute-authorized', action='store_true')
    parser.add_argument('--curl-exit', type=int); parser.add_argument('--http-status', type=int)
    args = parser.parse_args(); configure(args.phase)
    if args.stage == 'prepare': prepare(args.execute_authorized)
    elif args.stage == 'finish':
        if args.curl_exit is None or args.http_status is None: parser.error('Actual curl/HTTP status required')
        finish(args.curl_exit, args.http_status)
    else:
        {'preflight-config': c.preflight_config, 'freeze': freeze, 'status': status,
         'refresh-config': b.refresh_config, 'refresh': b.refresh, 'calibration-analysis': calibration_analysis}[args.stage]()
