"""Fixed 96-call no-advice calibration after blind review and delivery gates."""
import argparse
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('alternate_helpers',ROOT/'scripts/58_alternate_provider_canary.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,p=a.c,a.p
CANARY=c.OUT
OUT=c.BASE/'baseline_calibration_96'
PACKET=c.BASE/'reviewed_calibration/position_revision'
REVIEW=c.BASE/'independent_review'
CAP=Decimal('1.00')


def verify_lock(path):
    lock=c.load(path)
    maps=[lock[k] for k in ('input_sha256','output_sha256','sha256','previous_lock_sha256') if k in lock]
    for mapping in maps or [lock]:
        for name,expected in mapping.items():
            target=Path(name) if Path(name).is_absolute() else ROOT/name
            if p.sha(target)!=expected:raise ValueError('Locked input changed: '+name)


def gates():
    verify_lock(PACKET/'artifact_hashes.json')
    verify_lock(REVIEW/'POSTREPAIR_SHA256_LOCK.json')
    judgments=c.load(REVIEW/'postrepair_judgments.json')
    rows=c.load(PACKET/'packet.json')
    # The independent validator explicitly reports all 48 successful remaps.
    summary=c.load(REVIEW/'postrepair_summary.json')
    if (len(judgments)!=48 or summary['items_checked']!=48 or summary['unique_matching_answers']!=48
        or not all(summary['checks'].values())):raise ValueError('Postrepair review incomplete')
    reviewed={r['item_id']:r for r in judgments}
    if len(reviewed)!=48 or set(reviewed)!={r['item_id'] for r in rows}:raise ValueError('Postrepair coverage mismatch')
    originals=c.load(REVIEW/'initial_judgments.json')
    values={r['item_id']:Fraction(r['derived_numerical_answer']) for r in originals}
    for row in rows:
        if not reviewed[row['item_id']]['unique_answer'] or reviewed[row['item_id']]['chosen_letter']!=row['correct_letter']:
            raise ValueError('Repaired key disagrees with blind validation')
        if Fraction(row['options'][row['correct_letter']])!=values[row['item_id']]:
            raise ValueError('Reviewed numerical answer changed')
    old=c.load(CANARY/'manifest.json')
    for name,digest in old['input_hashes'].items():
        if p.sha(ROOT/name)!=digest:raise ValueError('Canary input changed')
    finished=[c.load(path) for path in (CANARY/'finished').glob('*.json')]
    if len(finished)!=12 or {r['sample_id'] for r in finished}!={t['sample_id'] for t in old['trials']} or not all(r['gate_passed'] for r in finished):
        raise ValueError('Alternate-provider canary has not passed all twelve trials')
    for trial in old['trials']:
        rid=trial['sample_id'];final=next(r for r in finished if r['sample_id']==rid)
        for folder,suffix,key in [('raw','.json','raw_sha256'),('headers','.txt','headers_sha256'),('requests','.json','request_sha256')]:
            if p.sha(CANARY/folder/(rid+suffix))!=final[key]:raise ValueError('Canary artifact changed')
        if c.load(CANARY/'requests'/(rid+'.json'))!=trial['request']:raise ValueError('Canary request mismatch')
    return rows


def refresh_config():
    a.no_other_collection();manifest()
    pointer=OUT/'refresh_pointer.json'
    if pointer.exists():raise ValueError('Unresolved refresh')
    folder=Path(tempfile.mkdtemp(prefix='ddm-calibration-refresh-',dir='/private/tmp'))
    entries=[dict(url='https://openrouter.ai/api/v1/'+route,header='Authorization: Bearer '+p.key(),output=folder/(name+'.json'),max_time=30)
             for name,route in [('credits','credits'),('allowance','auth/key')]]
    entries += [dict(url=f'https://openrouter.ai/api/v1/models/{mid}/endpoints',output=folder/(name+'.json'),max_time=30) for name,mid in p.MODELS.items()]
    config=p.private_config(entries)
    p.save(pointer,dict(folder=str(folder),config=config,created_at=p.now()))
    print('curl --parallel --parallel-max 4 --config '+config)


def refresh():
    m=manifest();pointer=OUT/'refresh_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale refresh')
        for name,(provider,slug,quant) in a.ROUTES.items():
            ep=a.endpoint(c.load(folder/(name+'.json')),provider,quant)
            for field in ('provider_name','name','quantization','pricing','context_length','max_completion_tokens'):
                if ep.get(field)!=m['endpoint_snapshot'][name].get(field):raise ValueError('Endpoint drift on refresh')
        credits=c.load(folder/'credits.json')['data'];available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining');bound=Decimal(m['maximum_cost_usd'])
        if not available.is_finite() or available<bound:raise ValueError('Budget unavailable on refresh')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<bound):raise ValueError('Key allowance unavailable')
        check=dict(checked_at=state['created_at'],manifest_sha256=p.sha(OUT/'manifest.json'),passed=True)
        p.save(OUT/'preflight_refreshes'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'),check)
        print('Read-only preflight refreshed; requests and manifest unchanged')
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();pointer.unlink()


def freeze():
    a.no_other_collection();rows=gates()
    state=c.load(OUT/'preflight_pointer.json');folder=Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:a.endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in a.ROUTES.items()}
        trials=[]
        for qi,row in enumerate(r for r in rows if r['split']=='calibration'):
            for repeat in range(2):
                names=list(a.ROUTES)
                if (qi+repeat)%2:names.reverse()
                for name in names:
                    provider,slug,quant=a.ROUTES[name];ep=endpoints[name]
                    text=('Answer the question. Be concise. Reply with A or B only on the final line.\n\n'
                        +row['stem']+'\n\nA. '+row['options']['A']+'\nB. '+row['options']['B'])
                    req=dict(model=p.MODELS[name],messages=[dict(role='user',content=text)],temperature=.7,max_tokens=4096,
                        provider=dict(order=[slug],only=[slug],allow_fallbacks=False,quantizations=[quant],require_parameters=True,
                            max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
                    if ep.get('max_completion_tokens',0)<4096 or ep.get('context_length',0)<p.input_bound(req['messages'])+4096:
                        raise ValueError('Insufficient endpoint capacity')
                    trials.append(dict(sample_id=f'{row["item_id"]}__r{repeat+1}__{name}',item_id=row['item_id'],
                        family=row['family'],repeat=repeat+1,model=name,expected_provider=provider,
                        options=row['options'],correct_letter=row['correct_letter'],request=req))
        if len(trials)!=96 or len({t['sample_id'] for t in trials})!=96:raise ValueError('Bad calibration coverage')
        bound=sum(map(p.trial_bound,trials))
        credits=c.load(folder/'credits.json')['data'];available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0<bound<=CAP or available<bound:raise ValueError('Budget invalid')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<bound):raise ValueError('Key allowance insufficient')
        paths=[Path(__file__),ROOT/'scripts/61_analyze_baseline_calibration.py',ROOT/'scripts/58_alternate_provider_canary.py',ROOT/'scripts/56_reliance_canary.py',
            ROOT/'scripts/54_reliance_calibration.py',ROOT/'scripts/50_open_dataset_feasibility.py',
            ROOT/'docs/BASELINE_CALIBRATION_PROTOCOL.md',PACKET/'packet.json',PACKET/'artifact_hashes.json',
            REVIEW/'POSTREPAIR_SHA256_LOCK.json',REVIEW/'postrepair_judgments.json',CANARY/'manifest.json']
        p.save(OUT/'manifest.json',dict(created_at=p.now(),preflight_started_at=state['created_at'],trials=trials,
            execution_authorization='User: do that (independent review, reliable alternative and no-advice calibration)',
            endpoint_snapshot=endpoints,maximum_cost_usd=str(bound),cost_cap_usd=str(CAP),
            max_attempts_per_trial=1,automatic_retries=0,min_interval_seconds=20,
            independent_review_complete=True,delivery_canary_passed=True,original_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(json.dumps(dict(n_planned=96,reserve_usd=str(bound),readiness_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();(OUT/'preflight_pointer.json').unlink()


def manifest():
    m=c.load(OUT/'manifest.json')
    for name,digest in m['input_hashes'].items():
        if p.sha(ROOT/name)!=digest:raise ValueError('Frozen calibration input changed: '+name)
    if len(m['trials'])!=96 or len({t['sample_id'] for t in m['trials']})!=96:raise ValueError('Bad manifest')
    return m


def prepare(authorized=False):
    if not authorized:raise ValueError('Explicit authorized flag required')
    a.no_other_collection();m=manifest()
    checked=m['preflight_started_at']
    for path in sorted((OUT/'preflight_refreshes').glob('*.json')):
        check=c.load(path)
        if check['passed'] and check['manifest_sha256']==p.sha(OUT/'manifest.json'):checked=check['checked_at']
    if not 0<=c.seconds_since(checked)<3600:raise ValueError('Preflight stale; refresh required')
    if (OUT/'active.json').exists():raise ValueError('Unresolved attempt')
    attempts=c.history(m)
    for row in attempts:
        path=OUT/'finished'/(row['sample_id']+'.json')
        if not path.exists() or not c.load(path)['continue_permitted']:raise ValueError('Previous attempt requires stop')
    if attempts and c.seconds_since(attempts[-1]['prepared_at'])<20:raise ValueError('Minimum interval not elapsed')
    if len(attempts)==96:print('Collection complete');return
    t=m['trials'][len(attempts)];rid=t['sample_id']
    for folder in ('requests','raw','headers','http'):(OUT/folder).mkdir(parents=True,exist_ok=True)
    request=OUT/'requests'/(rid+'.json');p.save(request,t['request'])
    attempt=dict(sample_id=rid,prepared_at=p.now(),manifest_sha256=p.sha(OUT/'manifest.json'),request_sha256=p.sha(request),reserved_cost_usd=str(p.trial_bound(t)))
    p.save(OUT/'attempts'/f'{len(attempts)+1:03}.json',attempt);p.save(OUT/'active.json',attempt)
    config=p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+p.key(),'Content-Type: application/json'],data_binary='@'+str(request),
        output=OUT/'raw'/(rid+'.json'),dump_header=OUT/'headers'/(rid+'.txt'),write_out='%{http_code}',max_time=180,connect_timeout=20)])
    p.save(OUT/'private_pointer.json',dict(config=config));print('curl --config '+config)


def finish(exitcode,http):
    m=manifest();attempt=c.load(OUT/'active.json');rid=attempt['sample_id'];t=next(t for t in m['trials'] if t['sample_id']==rid)
    raw=OUT/'raw'/(rid+'.json');headers=OUT/'headers'/(rid+'.txt')
    try:data=c.load(raw)
    except (OSError,ValueError):data=None
    scored=a.result(t,data,http) if exitcode==0 else dict(status='uncertain_delivery',correct=None,choice=None,strict_format=None)
    amount=data.get('usage',{}).get('cost') if isinstance(data,dict) and isinstance(data.get('usage'),dict) else None
    charge=None
    try:charge=Decimal(str(amount)) if amount is not None else None
    except Exception:pass
    cost_ok=charge is not None and charge.is_finite() and 0<=charge<=p.trial_bound(t)
    # Behavioral nonanswers are retained, not retried or used for interim selection.
    continued=scored['status'] in ('answered','ambiguous_format','censored','refusal','incomplete') and cost_ok and headers.exists()
    final=dict(**attempt,finished_at=p.now(),curl_exit=exitcode,http_status=http,outcome=scored,
        recorded_cost_usd=str(charge) if charge is not None else None,missing_cost_metadata=amount is None,
        cost_within_reserve=cost_ok,continue_permitted=continued,
        raw_sha256=p.sha(raw) if raw.exists() else None,headers_sha256=p.sha(headers) if headers.exists() else None)
    p.save(OUT/'http'/(rid+'.json'),dict(curl_exit=exitcode,http_status=http));p.save(OUT/'finished'/(rid+'.json'),final)
    pointer=OUT/'private_pointer.json'
    if pointer.exists():Path(c.load(pointer)['config']).unlink(missing_ok=True);pointer.unlink()
    (OUT/'active.json').unlink()
    print(json.dumps(dict(sample_id=rid,status=scored['status'],continue_permitted=continued,accuracy_not_reported=True)))


def status():
    m=manifest();attempts=c.history(m);rows=[c.load(path) for path in (OUT/'finished').glob('*.json')]
    print(json.dumps(dict(n_planned=96,n_attempted=len(attempts),n_finalized=len(rows),outcomes=dict(Counter(r['outcome']['status'] for r in rows)),
        stopped=any(not r['continue_permitted'] for r in rows),active_attempt=(OUT/'active.json').exists(),
        recorded_cost_usd=str(sum((Decimal(r['recorded_cost_usd']) for r in rows if r['recorded_cost_usd'] is not None),Decimal(0))),
        accuracy_not_reported=True,original_study_remains_paused=True),indent=2))


c.OUT=OUT
c.manifest=manifest
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['preflight-config','freeze','prepare','finish','status','refresh-config','refresh'],required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args()
    if args.stage=='prepare':prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Need curl exit and HTTP status')
        finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':status,'refresh-config':refresh_config,'refresh':refresh}[args.stage]()
