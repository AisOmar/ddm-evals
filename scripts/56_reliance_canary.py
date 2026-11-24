"""One-attempt, serial delivery canary; explicit curl handoff, never retries."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/research_directions/reliance_calibration_v2'
OUT = BASE/'delivery_canary'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


p = module('canary_helpers','50_open_dataset_feasibility.py')
s = module('canary_scoring','54_reliance_calibration.py')
CAP = Decimal('.10')


def load(path):
    return json.loads(path.read_text())


def seconds_since(timestamp):
    return (datetime.now(timezone.utc)-datetime.fromisoformat(timestamp)).total_seconds()


def no_other_collection():
    active = list((ROOT/'results').rglob('active_batch.json'))
    if active:
        raise ValueError('Unresolved collection batch exists')
    if load(ROOT/'results/deference/trust_planning/orchestration_state.json')['status'] != 'paused_by_user':
        raise ValueError('Original study must remain paused')


def check_locks():
    for filename in ('artifact_hashes.json','review_revision/artifact_hashes.json'):
        for name,expected in load(BASE/filename).items():
            if p.sha(ROOT/name) != expected:
                raise ValueError(f'Changed locked development input: {name}')


def preflight_config():
    no_other_collection()
    if (OUT/'preflight_pointer.json').exists() or (OUT/'manifest.json').exists():
        raise ValueError('Existing preflight or manifest; do not overwrite')
    folder = Path(tempfile.mkdtemp(prefix='ddm-canary-preflight-',dir='/private/tmp'))
    entries = [dict(url='https://openrouter.ai/api/v1/'+route,
                    header='Authorization: Bearer '+p.key(),output=folder/(name+'.json'),max_time=30)
               for name,route in [('credits','credits'),('allowance','auth/key')]]
    entries += [dict(url=f'https://openrouter.ai/api/v1/models/{mid}/endpoints',
                     output=folder/(name+'.json'),max_time=30) for name,mid in p.MODELS.items()]
    config = p.private_config(entries)
    p.save(OUT/'preflight_pointer.json',dict(folder=str(folder),config=config,created_at=p.now()))
    print(f'curl --parallel --parallel-max 4 --config {config}')


def freeze():
    no_other_collection()
    check_locks()
    pointer = OUT/'preflight_pointer.json'
    state = load(pointer)
    folder = Path(state['folder'])
    try:
        if not 0 <= seconds_since(state['created_at']) < 3600:
            raise ValueError('Stale preflight')
        endpoints = {name:p.endpoint(load(folder/(name+'.json'))) for name in p.MODELS}
        draft = load(BASE/'delivery_canary_draft.json')
        trials = []
        for question in draft['questions']:
            for name,mid in p.MODELS.items():
                ep = endpoints[name]
                text = ('Answer the question. Be concise. Reply with A or B only on the final line.\n\n'
                        +question['stem']+'\n\nA. '+question['options']['A']+'\nB. '+question['options']['B'])
                req = dict(model=mid,messages=[dict(role='user',content=text)],temperature=0,max_tokens=512,
                    provider=dict(order=['DeepInfra'],only=['DeepInfra'],allow_fallbacks=False,
                        quantizations=[ep['quantization']],require_parameters=True,
                        max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
                if ep.get('max_completion_tokens',0) < 512 or ep.get('context_length',0) < p.input_bound(req['messages'])+512:
                    raise ValueError('Insufficient endpoint capacity')
                trials.append(dict(sample_id=name+'__'+question['item_id'],model=name,
                    correct_letter=question['correct_letter'],options=question['options'],request=req))
        bound = sum(map(p.trial_bound,trials))
        credit = load(folder/'credits.json')['data']
        available = Decimal(str(credit['total_credits']))-Decimal(str(credit['total_usage']))
        remaining = load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not Decimal(0) <= bound <= CAP or available < bound:
            raise ValueError('Full reserve exceeds cap or available balance')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining)) < bound):
            raise ValueError('Insufficient key allowance')
        inputs = [Path(__file__),ROOT/'scripts/50_open_dataset_feasibility.py',
                  ROOT/'scripts/54_reliance_calibration.py',ROOT/'docs/RELIANCE_CANARY_OPERATIONS.md',
                  BASE/'delivery_canary_draft.json']
        p.save(OUT/'manifest.json',dict(created_at=p.now(),preflight_started_at=state['created_at'],
            execution_authorization='User: okay move pm; interpreted as continue to bounded next stage',
            trials=trials,endpoint_snapshot=endpoints,maximum_cost_usd=str(bound),cost_cap_usd=str(CAP),
            minimum_start_interval_seconds=20,max_attempts_per_trial=1,automatic_retries=0,
            preflight_passed=True,full_reserve_covered=True,old_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in inputs}))
        print(json.dumps(dict(n_planned=len(trials),full_reserve_usd=str(bound),preflight_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():
            path.unlink()
        folder.rmdir()
        pointer.unlink()


def manifest():
    m = load(OUT/'manifest.json')
    for name,expected in m['input_hashes'].items():
        if p.sha(ROOT/name) != expected:
            raise ValueError(f'Frozen canary input changed: {name}')
    if len(m['trials']) != 12 or len({t['sample_id'] for t in m['trials']}) != 12:
        raise ValueError('Incorrect canary coverage')
    return m


def result(trial, data, http_status):
    if http_status == 429 or (isinstance(data,dict) and isinstance(data.get('error'),dict) and data['error'].get('code') == 429):
        return dict(status='rate_limited',choice=None,correct=None,strict_format=None)
    if http_status != 200:
        return dict(status='http_error',choice=None,correct=None,strict_format=None)
    if not isinstance(data,dict):
        return dict(status='invalid_response',choice=None,correct=None,strict_format=None)
    choices = data.get('choices')
    if not data.get('error') and (not isinstance(choices,list) or len(choices) != 1
                                 or not isinstance(choices[0],dict)
                                 or not isinstance(choices[0].get('message'),dict)):
        return dict(status='invalid_response',choice=None,correct=None,strict_format=None)
    try:
        kind,_ = p.classify(trial,data)
    except (ValueError,KeyError,TypeError,AttributeError,IndexError):
        kind = 'invalid_response'
    if kind not in ('answered','format_error'):
        return s.score(dict(status=kind),trial['options'],trial['correct_letter'])
    return s.score(dict(status='completed',text=data['choices'][0]['message']['content']),
                   trial['options'],trial['correct_letter'])


def history(m):
    attempts = sorted((OUT/'attempts').glob('*.json'))
    ids = [load(path)['sample_id'] for path in attempts]
    if len(ids) != len(set(ids)) or ids != [t['sample_id'] for t in m['trials'][:len(ids)]]:
        raise ValueError('Attempt ledger invalid')
    return [load(path) for path in attempts]


def prepare(authorized=False):
    if not authorized:
        raise ValueError('Explicit authorized execution flag required')
    no_other_collection()
    m = manifest()
    if not 0 <= seconds_since(m['preflight_started_at']) < 3600:
        raise ValueError('Preflight expired; stop without dispatch')
    if (OUT/'active.json').exists():
        raise ValueError('An uncertain or active attempt exists')
    attempts = history(m)
    for attempt in attempts:
        final = OUT/'finished'/(attempt['sample_id']+'.json')
        if not final.exists() or not load(final)['gate_passed']:
            raise ValueError('Prior attempt incomplete or failed; no further dispatch')
    if attempts and seconds_since(attempts[-1]['prepared_at']) < 20:
        raise ValueError('Minimum 20-second interval has not elapsed')
    if len(attempts) == 12:
        print('All canary trials attempted; no new request.')
        return
    t = m['trials'][len(attempts)]
    rid = t['sample_id']
    for folder in ('requests','raw','headers','http'):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    request = OUT/'requests'/(rid+'.json')
    p.save(request,t['request'])
    # Record before emitting the credential-bearing dispatch configuration.
    attempt = dict(sample_id=rid,prepared_at=p.now(),manifest_sha256=p.sha(OUT/'manifest.json'),
                   request_sha256=p.sha(request),reserved_cost_usd=str(p.trial_bound(t)))
    p.save(OUT/'attempts'/f'{len(attempts)+1:02}.json',attempt)
    p.save(OUT/'active.json',attempt)
    config = p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+p.key(),'Content-Type: application/json'],
        data_binary='@'+str(request),output=OUT/'raw'/(rid+'.json'),
        dump_header=OUT/'headers'/(rid+'.txt'),write_out='%{http_code}',max_time=120,connect_timeout=20)])
    p.save(OUT/'private_pointer.json',dict(config=config))
    print(f'curl --config {config}')


def finish(curl_exit, http_status):
    m = manifest()
    attempt = load(OUT/'active.json')
    rid = attempt['sample_id']
    t = next(t for t in m['trials'] if t['sample_id'] == rid)
    raw,headers = OUT/'raw'/(rid+'.json'),OUT/'headers'/(rid+'.txt')
    try:
        data = load(raw)
    except (OSError,ValueError):
        data = None
    scored = result(t,data,http_status) if curl_exit == 0 else dict(
        status='uncertain_delivery',choice=None,correct=None,strict_format=None)
    amount = data.get('usage',{}).get('cost') if isinstance(data,dict) and isinstance(data.get('usage'),dict) else None
    charge = None
    if amount is not None:
        try:
            charge = Decimal(str(amount))
        except Exception:
            charge = None
    cost_valid = charge is not None and charge.is_finite() and Decimal(0) <= charge <= p.trial_bound(t)
    final = dict(**attempt,finished_at=p.now(),curl_exit=curl_exit,http_status=http_status,
        outcome=scored,recorded_cost_usd=str(charge) if charge is not None else None,
        missing_cost_metadata=amount is None,cost_within_reserve=cost_valid,
        raw_sha256=p.sha(raw) if raw.exists() else None,
        headers_sha256=p.sha(headers) if headers.exists() else None,
        gate_passed=(scored['status']=='answered' and scored['correct'] is True and cost_valid and headers.exists()),
        retry_permitted=False,minimum_429_cooldown_seconds=60 if scored['status']=='rate_limited' else None)
    p.save(OUT/'http'/(rid+'.json'),dict(curl_exit=curl_exit,http_status=http_status))
    p.save(OUT/'finished'/(rid+'.json'),final)
    pointer = OUT/'private_pointer.json'
    if pointer.exists():
        Path(load(pointer)['config']).unlink(missing_ok=True)
        pointer.unlink()
    (OUT/'active.json').unlink()
    print(json.dumps(dict(sample_id=rid,outcome=scored,gate_passed=final['gate_passed'])))


def status():
    m = manifest()
    attempts = history(m)
    rows = [load(path) for path in (OUT/'finished').glob('*.json')]
    passed = len(attempts)==len(rows)==12 and all(r['gate_passed'] for r in rows)
    costs = [Decimal(r['recorded_cost_usd']) for r in rows if r['recorded_cost_usd'] is not None]
    total = sum((x for x in costs if x.is_finite() and x >= 0),Decimal(0))
    result = dict(n_planned=12,n_attempted=len(attempts),n_finalized=len(rows),
        outcomes=dict(Counter(r['outcome']['status'] for r in rows)),
        n_correct=sum(r['outcome']['correct'] is True for r in rows),
        n_strict_format=sum(r['outcome']['strict_format'] is True for r in rows),
        missing_cost_metadata=sum(r['missing_cost_metadata'] for r in rows),
        recorded_cost_usd=str(total),full_reserve_usd=m['maximum_cost_usd'],
        gate_passed=passed,active_attempt=(OUT/'active.json').exists(),
        calibration_authorized=False,original_study_remains_paused=True)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status'),required=True)
    parser.add_argument('--execute-authorized',action='store_true')
    parser.add_argument('--curl-exit',type=int)
    parser.add_argument('--http-status',type=int)
    args = parser.parse_args()
    if args.stage == 'prepare':
        prepare(args.execute_authorized)
    elif args.stage == 'finish':
        if args.curl_exit is None or args.http_status is None:
            parser.error('finish requires curl exit and HTTP status')
        finish(args.curl_exit,args.http_status)
    else:
        {'preflight-config':preflight_config,'freeze':freeze,'status':status}[args.stage]()
