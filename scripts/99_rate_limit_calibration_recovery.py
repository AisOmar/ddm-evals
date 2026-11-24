"""Bounded confirmed-429 recovery; one retained outcome per fixed cohort slot."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import importlib.util
import json
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rate_recovery_source', ROOT/'scripts/98_complete_calibration.py')
source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
c, h = source.c, source.h
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_RATE_LIMIT_RECOVERY.md'
BASE = h.BASE/'calibration_rate_recovery'
OLD = source.BASE
CAP = Decimal('.10')
PRIOR_UPPER = Decimal('.31496066')


def configure():
    c.OUT, c.c.OUT, c.b.OUT = BASE, BASE, BASE
    c.a.ROUTES = dict(c.l.ROUTES)
    c.b.manifest = manifest; c.c.manifest = manifest


def confirmed_rejection(exitcode, http, body, provider):
    return (exitcode == 0 and http == 429 and isinstance(body, dict)
        and isinstance(body.get('error'), dict) and body['error'].get('code') == 429
        and body['error'].get('metadata', {}).get('provider_name') == provider
        and not body.get('choices'))


def cooldown(headers, now):
    value = next((line.split(':', 1)[1].strip() for line in headers.splitlines()
                  if line.lower().startswith('retry-after:')), None)
    seconds = 60.0
    if value is not None:
        try: seconds = max(seconds, float(value))
        except ValueError:
            try: seconds = max(seconds, (parsedate_to_datetime(value)-now).total_seconds())
            except (ValueError, TypeError): pass
    return max(60.0, seconds)


def manifest():
    m = c.c.load(BASE/'manifest.json'); c.verify_hashes(m['input_hashes'])
    return m


def freeze():
    c.a.no_other_collection(); source.c.r.c.review_gate()
    old = c.c.load(OLD/'manifest.json'); c.verify_hashes(old['input_hashes'])
    observed = {p.stem: p for p in (OLD/'finished').glob('*.json')}
    if set(observed) != {t['sample_id'] for t in old['trials'][:2]}: raise ValueError('Original recovery prefix changed')
    first, rejected = old['trials'][:2]
    final = c.c.load(observed[rejected['sample_id']])
    error_path = OLD/'raw'/(rejected['sample_id']+'.sse')
    if not confirmed_rejection(final['curl_exit'], final['http_status'], c.c.load(error_path), rejected['expected_provider']):
        raise ValueError('Original failure is not a confirmed rejection')
    if c.c.load(observed[first['sample_id']])['outcome']['status'] != 'answered': raise ValueError('Original accepted slot changed')
    retained = list(old['retained'])+[dict(sample_id=first['sample_id'], trial=first,
        finished_path=str(observed[first['sample_id']].relative_to(ROOT)),
        finished_sha256=c.p.sha(observed[first['sample_id']]), resend_permitted=False)]
    trials = old['trials'][1:]
    pointer = BASE/'preflight_pointer.json'; state = c.c.load(pointer); folder = Path(state['folder'])
    try:
        if not 0 <= c.c.seconds_since(state['created_at']) < 3600: raise ValueError('Stale preflight')
        endpoints = {name: c.a.endpoint(c.c.load(folder/(name+'.json')), route[0], route[2]) for name, route in c.l.ROUTES.items()}
        for name, ep in endpoints.items():
            for field in ('provider_name', 'name', 'quantization', 'pricing', 'context_length', 'max_completion_tokens'):
                if ep.get(field) != old['endpoint_snapshot'][name].get(field): raise ValueError('Endpoint drift')
        reserve = sum(map(c.p.trial_bound, trials))+3*max(map(c.p.trial_bound, trials))
        credit = c.c.load(folder/'credits.json')['data']; available = Decimal(str(credit['total_credits']))-Decimal(str(credit['total_usage']))
        allowance = c.c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not 0 < reserve <= CAP or PRIOR_UPPER+reserve > 1 or available < reserve:
            raise ValueError('Recovery envelope or credit exceeded')
        if allowance is not None and Decimal(str(allowance)) < reserve: raise ValueError('Key allowance insufficient')
        paths = [Path(__file__), PROTOCOL, ROOT/'scripts/98_complete_calibration.py',
                 ROOT/'scripts/97_http2_stream_collection.py', ROOT/'scripts/95_stream_collection.py',
                 ROOT/'scripts/94_stream_transport.py', OLD/'manifest.json', error_path, observed[rejected['sample_id']]]
        paths += [ROOT/r['finished_path'] for r in retained]
        c.p.save(BASE/'manifest.json', dict(created_at=c.p.now(), preflight_started_at=state['created_at'],
            authorization='User: okay do that; bounded recovery of explicit provider rejection during the authorized calibration.',
            trials=trials, retained=retained, cohort_planned=48, max_total_attempts_per_slot=2,
            max_extra_retries=4, max_new_calls=40, maximum_cost_usd=str(reserve), cost_cap_usd=str(CAP),
            endpoint_snapshot=endpoints, original_rejection_sample_id=rejected['sample_id'],
            original_rejection_headers=str((OLD/'headers'/(rejected['sample_id']+'.txt')).relative_to(ROOT)),
            original_rejection_finished_at=final['finished_at'], previous_cost_upper_usd=str(PRIOR_UPPER),
            input_hashes={str(p.relative_to(ROOT)): c.p.sha(p) for p in paths}, advice_pilot_permitted=False,
            original_study_remains_paused=True))
        print(json.dumps(dict(logical_slots=len(trials), retained=len(retained), full_reserve_usd=str(reserve))))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir(): path.unlink()
        folder.rmdir(); pointer.unlink()


def ledger():
    return [c.c.load(path) for path in sorted((BASE/'finished').glob('*.json'))]


def schedule(m, records):
    accepted = {}
    for row in records:
        if row['slot_finalized']: accepted[row['sample_id']] = row
    pending = next((t for t in m['trials'] if t['sample_id'] not in accepted), None)
    return pending, accepted


def prepare(authorized):
    if not authorized: raise ValueError('Authorized flag required')
    if (BASE/'active.json').exists(): raise ValueError('Unresolved attempt')
    c.a.no_other_collection(); m = manifest(); checked = m['preflight_started_at']
    for path in sorted((BASE/'preflight_refreshes').glob('*.json')):
        row = c.c.load(path)
        if row['passed'] and row['manifest_sha256'] == c.p.sha(BASE/'manifest.json'): checked = row['checked_at']
    if not 0 <= c.c.seconds_since(checked) < 3600: raise ValueError('Preflight stale')
    records = ledger()
    if any(row['fatal_stop'] for row in records): raise ValueError('Prior fatal transport/integrity stop')
    if len(records) >= m['max_new_calls']: raise ValueError('Global attempt ceiling reached')
    trial, accepted = schedule(m, records)
    if trial is None: print('Cohort complete'); return
    # Honor both the preserved rejection and every new rejection cooldown.
    waits = []
    for row in records:
        if row['confirmed_429']:
            waits.append(row['cooldown_seconds']-c.c.seconds_since(row['finished_at']))
    old_headers = (ROOT/m['original_rejection_headers']).read_text()
    waits.append(cooldown(old_headers, datetime.fromisoformat(m['original_rejection_finished_at']))-
                 c.c.seconds_since(m['original_rejection_finished_at']))
    if max(waits, default=0) > 0:
        print(json.dumps(dict(wait_seconds=max(waits)))); return
    for model in c.l.ROUTES:
        streak = 0
        for old_trial in m['trials']:
            if old_trial['model'] != model or old_trial['sample_id'] not in accepted: continue
            streak = streak+1 if accepted[old_trial['sample_id']]['outcome']['status'] == 'rate_limited' else 0
        if streak >= 3: raise ValueError('Repeated model-specific provider rejection; stop')
    same = [row for row in records if row['sample_id'] == trial['sample_id']]
    number = len(same)+1+(trial['sample_id'] == m['original_rejection_sample_id'])
    if number > 2: raise ValueError('Per-slot attempt limit exceeded')
    if records:
        delay = 5-c.c.seconds_since(records[-1]['prepared_at'])
        if delay > 0: time.sleep(min(delay+.02, 5.02))
    aid = f'{len(records)+1:03}__'+trial['sample_id']+f'__a{number}'
    for name in ('requests', 'raw', 'headers', 'normalized'): (BASE/name).mkdir(parents=True, exist_ok=True)
    request = BASE/'requests'/(aid+'.json'); c.p.save(request, trial['request'])
    attempt = dict(attempt_id=aid, sample_id=trial['sample_id'], attempt_number=number,
        prepared_at=c.p.now(), request_sha256=c.p.sha(request), reserved_cost_usd=str(c.p.trial_bound(trial)))
    c.p.save(BASE/'attempts'/(aid+'.json'), attempt); c.p.save(BASE/'active.json', attempt)
    config = c.p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+c.p.key(), 'Content-Type: application/json'], data_binary='@'+str(request),
        output=BASE/'raw'/(aid+'.sse'), dump_header=BASE/'headers'/(aid+'.txt'), write_out='%{http_code}',max_time=180,connect_timeout=20)])
    h.set_http2(config)
    with Path(config).open('a') as file: file.write('no-buffer\n')
    c.p.save(BASE/'private_pointer.json', dict(config=config)); print('curl --config '+config)


def finish(exitcode, http):
    m = manifest(); at = c.c.load(BASE/'active.json'); aid = at['attempt_id']
    trial = next(t for t in m['trials'] if t['sample_id'] == at['sample_id'])
    raw, headers = BASE/'raw'/(aid+'.sse'), BASE/'headers'/(aid+'.txt')
    header_text = headers.read_text() if headers.exists() else ''
    rejected = False; normalized = None; parse_error = None
    outcome = dict(status='uncertain_delivery', choice=None, correct=None, strict_format=None)
    if http == 429:
        try: body = c.c.load(raw)
        except (OSError, ValueError): body = None
        rejected = confirmed_rejection(exitcode, http, body, trial['expected_provider'])
        if rejected: outcome['status'] = 'rate_limited'
    elif exitcode == 0 and http == 200:
        try:
            normalized, parser_audit = c.s.reconstruct(raw.read_bytes(), trial['request']['model'], trial['expected_provider'], trial['model_aliases'])
            outcome = c.a.result(trial, normalized, http)
            c.p.save(BASE/'normalized'/(aid+'.json'), normalized)
        except (ValueError, OSError) as error: parse_error = str(error)
    try: cost = Decimal(str(normalized.get('usage', {}).get('cost'))) if normalized else Decimal('NaN')
    except Exception: cost = Decimal('NaN')
    cost_ok = cost.is_finite() and 0 <= cost <= c.p.trial_bound(trial)
    complete = exitcode == 0 and http == 200 and h.response_http_version(header_text) == '2' and normalized is not None and cost_ok and outcome['status'] in source.BEHAVIORAL
    extra_so_far = 1+sum(row['attempt_number'] == 2 and row['sample_id'] != m['original_rejection_sample_id'] for row in ledger())
    retry = rejected and at['attempt_number'] < 2 and extra_so_far < m['max_extra_retries']
    slot_finalized = complete or (rejected and not retry)
    result = dict(**at, finished_at=c.p.now(), curl_exit=exitcode,http_status=http,outcome=outcome,
        confirmed_429=rejected, retry_eligible=retry, slot_finalized=slot_finalized,
        fatal_stop=not (complete or rejected), cooldown_seconds=cooldown(header_text, datetime.now(timezone.utc)) if rejected else 0,
        recorded_cost_usd=str(cost) if cost.is_finite() else None,cost_within_reserve=cost_ok,
        raw_sha256=c.p.sha(raw) if raw.exists() else None,headers_sha256=c.p.sha(headers) if headers.exists() else None,
        normalized_sha256=c.p.sha(BASE/'normalized'/(aid+'.json')) if normalized else None,parser_error=parse_error)
    c.p.save(BASE/'finished'/(aid+'.json'), result)
    pointer = BASE/'private_pointer.json'
    if pointer.exists(): Path(c.c.load(pointer)['config']).unlink(missing_ok=True); pointer.unlink()
    (BASE/'active.json').unlink()
    print(json.dumps(dict(sample_id=at['sample_id'],attempt_number=at['attempt_number'],status=outcome['status'],retry_eligible=retry,slot_finalized=slot_finalized,fatal_stop=result['fatal_stop'],accuracy_not_reported=True)))


def status():
    m = manifest(); records = ledger(); _, accepted = schedule(m, records)
    print(json.dumps(dict(logical_slots=len(m['trials']),new_attempts=len(records),new_finalized_slots=len(accepted),retained=len(m['retained']),outcomes=dict(Counter(row['outcome']['status'] for row in records)),fatal_stop=any(row['fatal_stop'] for row in records),active=(BASE/'active.json').exists()),indent=2))


def analyze():
    m = manifest(); records = ledger(); pending, accepted = schedule(m, records)
    if pending is not None or any(row['fatal_stop'] for row in records):
        raise ValueError('Complete fixed logical cohort required')
    for row in records:
        aid = row['attempt_id']
        for directory, suffix, key in [('requests','.json','request_sha256'),('raw','.sse','raw_sha256'),('headers','.txt','headers_sha256')]:
            if c.p.sha(BASE/directory/(aid+suffix)) != row[key]: raise ValueError('Attempt artifact changed')
        trial = next(t for t in m['trials'] if t['sample_id'] == row['sample_id'])
        if c.c.load(BASE/'requests'/(aid+'.json')) != trial['request']: raise ValueError('Request changed')
        if row['normalized_sha256'] and c.p.sha(BASE/'normalized'/(aid+'.json')) != row['normalized_sha256']:
            raise ValueError('Normalized response changed')
    observations = [(t, accepted[t['sample_id']]) for t in m['trials']]
    for retained in m['retained']:
        path = ROOT/retained['finished_path']
        if c.p.sha(path) != retained['finished_sha256']: raise ValueError('Retained outcome changed')
        final = c.c.load(path); parent = path.parent.parent; rid = retained['sample_id']
        raw = parent/'raw'/(rid+'.sse')
        if not raw.exists(): raw = parent/'raw'/(rid+'.json')
        if c.p.sha(raw) != final['raw_sha256']: raise ValueError('Retained response changed')
        observations.append((retained['trial'], final))
    if len(observations) != 48 or len({t['sample_id'] for t, _ in observations}) != 48:
        raise ValueError('Exactly 48 distinct planned slots required')
    models = []
    for model in c.l.ROUTES:
        group = [(t, f) for t, f in observations if t['model'] == model]
        answered = [(t, f) for t, f in group if f['outcome']['status'] == 'answered']
        correct = sum(f['outcome']['correct'] is True for _, f in answered)
        missing = len(group)-len(answered); wrong = len(answered)-correct
        models.append(dict(model=model,planned=len(group),recognized=len(answered),correct=correct,
            factual_errors=wrong,unknown=missing,recognized_answer_accuracy=correct/len(answered) if answered else None,
            correct_yield=correct/len(group),factual_accuracy_bounds=[correct/len(group),(correct+missing)/len(group)],
            ceiling_warning=bool(answered and correct/len(answered)>.90),nonanswer_warning=missing/len(group)>.05,
            outcome_counts=dict(Counter(f['outcome']['status'] for _, f in group)),
            item_results=[dict(item_id=t['item_id'],family=t['family'],repeat=t['repeat'],outcome=f['outcome']) for t,f in group]))
    result = dict(created_at=c.p.now(),planned_slots=48,finalized_slots=48,new_logical_slots=37,
        retained_slots=11,new_http_attempts=len(records),confirmed_rejections=sum(r['confirmed_429'] for r in records),
        retries_are_not_independent_observations=True,original_missing_answer_preserved=True,
        original_format_scores_preserved=True,advice_pilot_supported=False,
        reason='The preserved Qwen nonanswer fraction exceeds the predeclared 5% development warning.',
        models=models,inference='Descriptive development only; no intervention efficacy or safety conclusion.',
        original_study_remains_paused=True)
    c.p.save(BASE/'analysis.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2))
    for row in models: print(json.dumps({k:v for k,v in row.items() if k!='item_results'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh','analyze'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure()
    if args.stage=='prepare':prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Actual statuses required')
        finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.c.preflight_config,'freeze':freeze,'status':status,'refresh-config':c.b.refresh_config,'refresh':c.b.refresh,'analyze':analyze}[args.stage]()
