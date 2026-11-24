"""Two-stage versioned collection: 8 resource checks, then 64 baseline trials."""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('old_runner',ROOT/'scripts/60_calibrate_reviewed_packet.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a,c,p=b.a,b.c,b.p
BASE=ROOT/'results/research_directions/manageable_calibration_v3_20261021'
PHASE='resource'
OUT=BASE/PHASE
N={'resource':8,'calibration':64}
CEILINGS={'resource':Decimal('.10'),'calibration':Decimal('.50')}
EXTRA_INPUTS=[]


def configure(phase):
    global PHASE,OUT
    PHASE=phase;OUT=BASE/phase
    b.OUT=OUT;c.OUT=OUT
    b.manifest=manifest;c.manifest=manifest


def check_review():
    b.verify_lock(BASE/'packet_hashes.json')
    b.verify_lock(BASE/'independent_review/INITIAL_SHA256_LOCK.json')
    review=c.load(BASE/'independent_review/initial_judgments.json')
    rows=c.load(BASE/'packet.json')
    indexed={r['item_id']:r for r in review}
    if len(rows)!=36 or len(indexed)!=36 or set(indexed)!={r['item_id'] for r in rows}:raise ValueError('Review coverage mismatch')
    for row in rows:
        judgment=indexed[row['item_id']]
        if (not judgment['unique_answer'] or judgment['must_fix'] or judgment['chosen_letter']!=row['correct_letter']
            or str(judgment['derived_answer'])!=row['answer']):
            raise ValueError('Independent review disagreement or unresolved blocker: '+row['item_id'])
    return rows


def check_resource_gate():
    folder=BASE/'resource';m=c.load(folder/'manifest.json')
    for name,expected in m['input_hashes'].items():
        if p.sha(ROOT/name)!=expected:raise ValueError('Resource frozen input changed')
    finals=[c.load(path) for path in (folder/'finished').glob('*.json')]
    if len(finals)!=8 or {r['sample_id'] for r in finals}!={t['sample_id'] for t in m['trials']}:raise ValueError('Resource gate incomplete')
    for trial in m['trials']:
        rid=trial['sample_id'];final=next(r for r in finals if r['sample_id']==rid)
        if final['outcome']['status']!='answered' or not final['cost_within_reserve'] or final['curl_exit']!=0:raise ValueError('Resource gate failed')
        for foldername,suffix,key in [('raw','.json','raw_sha256'),('headers','.txt','headers_sha256'),('requests','.json','request_sha256')]:
            if p.sha(folder/foldername/(rid+suffix))!=final[key]:raise ValueError('Resource artifact changed')
        if c.load(folder/'requests'/(rid+'.json'))!=trial['request']:raise ValueError('Resource request mismatch')
    return True


def freeze():
    a.no_other_collection();rows=check_review()
    if PHASE=='calibration':check_resource_gate()
    pointer=OUT/'preflight_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:a.endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in a.ROUTES.items()}
        selected=[r for r in rows if r['split']==PHASE]
        trials=[]
        for qi,row in enumerate(selected):
            for repeat in range(1 if PHASE=='resource' else 2):
                names=list(a.ROUTES)
                if (qi+repeat)%2:names.reverse()
                for name in names:
                    provider,slug,quant=a.ROUTES[name];ep=endpoints[name]
                    text=('Answer the question. Be concise. Reply with A or B only on the final line.\n\n'
                        +row['stem']+'\n\nA. '+row['options']['A']+'\nB. '+row['options']['B'])
                    req=dict(model=p.MODELS[name],messages=[dict(role='user',content=text)],temperature=.7,max_tokens=2048,
                        provider=dict(order=[slug],only=[slug],allow_fallbacks=False,quantizations=[quant],require_parameters=True,
                            max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
                    if ep.get('max_completion_tokens',0)<2048 or ep.get('context_length',0)<p.input_bound(req['messages'])+2048:raise ValueError('Insufficient capacity')
                    trials.append(dict(sample_id=f'{row["item_id"]}__r{repeat+1}__{name}',item_id=row['item_id'],family=row['family'],
                        repeat=repeat+1,model=name,expected_provider=provider,options=row['options'],correct_letter=row['correct_letter'],request=req))
        if len(trials)!=N[PHASE] or len({t['sample_id'] for t in trials})!=N[PHASE]:raise ValueError('Bad trial coverage')
        bound=sum(map(p.trial_bound,trials));credits=c.load(folder/'credits.json')['data']
        available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0<bound<=CEILINGS[PHASE] or available<bound:raise ValueError('Budget invalid')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<bound):raise ValueError('Insufficient key allowance')
        inputs=[Path(__file__),ROOT/'scripts/64_manageable_analysis.py',ROOT/'scripts/60_calibrate_reviewed_packet.py',
            ROOT/'scripts/61_analyze_baseline_calibration.py',ROOT/'scripts/58_alternate_provider_canary.py',ROOT/'scripts/56_reliance_canary.py',
            ROOT/'scripts/54_reliance_calibration.py',ROOT/'scripts/50_open_dataset_feasibility.py',ROOT/'docs/MANAGEABLE_CALIBRATION_V3_PROTOCOL.md',
            BASE/'packet.json',BASE/'packet_hashes.json',BASE/'independent_review/INITIAL_SHA256_LOCK.json',BASE/'independent_review/initial_judgments.json']
        inputs += EXTRA_INPUTS
        if PHASE=='calibration':inputs += [BASE/'resource/manifest.json']+[path for path in (BASE/'resource/finished').glob('*.json')]
        p.save(OUT/'manifest.json',dict(created_at=p.now(),phase=PHASE,n_planned=N[PHASE],preflight_started_at=state['created_at'],trials=trials,
            execution_authorization='User: okay lets do it (shorter tasks, independent review, resource checks and small calibration)',
            endpoint_snapshot=endpoints,maximum_cost_usd=str(bound),cost_cap_usd=str(CEILINGS[PHASE]),max_attempts_per_trial=1,automatic_retries=0,
            min_interval_seconds=5,timeout_seconds=180,independent_review_complete=True,original_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in inputs}))
        print(json.dumps(dict(phase=PHASE,n_planned=N[PHASE],reserve_usd=str(bound),readiness_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();pointer.unlink()


def manifest():
    m=c.load(OUT/'manifest.json')
    for name,expected in m['input_hashes'].items():
        if p.sha(ROOT/name)!=expected:raise ValueError('Frozen input changed: '+name)
    if m['phase']!=PHASE or len(m['trials'])!=N[PHASE] or len({t['sample_id'] for t in m['trials']})!=N[PHASE]:raise ValueError('Invalid phase manifest')
    return m


def prepare(authorized=False):
    if not authorized:raise ValueError('Explicit authorized flag required')
    a.no_other_collection();m=manifest()
    checked=m['preflight_started_at']
    for path in sorted((OUT/'preflight_refreshes').glob('*.json')):
        latest=c.load(path)
        if latest['passed'] and latest['manifest_sha256']==p.sha(OUT/'manifest.json'):checked=latest['checked_at']
    if not 0<=c.seconds_since(checked)<3600:raise ValueError('Preflight stale; refresh required')
    if (OUT/'active.json').exists():raise ValueError('Unresolved prior attempt')
    attempts=c.history(m)
    for attempt in attempts:
        finalpath=OUT/'finished'/(attempt['sample_id']+'.json')
        if not finalpath.exists():raise ValueError('Prior attempt not finalized')
        final=c.load(finalpath)
        if not final['continue_permitted']:raise ValueError('Previous operational failure requires stop')
        if PHASE=='resource' and final['outcome']['status']!='answered':raise ValueError('Resource gate failed; stop phase')
    if len(attempts)==N[PHASE]:print('Phase complete; no new request');return
    if attempts and c.seconds_since(attempts[-1]['prepared_at'])<5:raise ValueError('Minimum interval not elapsed')
    t=m['trials'][len(attempts)];rid=t['sample_id']
    for directory in ('requests','raw','headers','http'):(OUT/directory).mkdir(parents=True,exist_ok=True)
    request=OUT/'requests'/(rid+'.json');p.save(request,t['request'])
    attempt=dict(sample_id=rid,prepared_at=p.now(),manifest_sha256=p.sha(OUT/'manifest.json'),request_sha256=p.sha(request),reserved_cost_usd=str(p.trial_bound(t)))
    p.save(OUT/'attempts'/f'{len(attempts)+1:03}.json',attempt);p.save(OUT/'active.json',attempt)
    config=p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',header=['Authorization: Bearer '+p.key(),'Content-Type: application/json'],
        data_binary='@'+str(request),output=OUT/'raw'/(rid+'.json'),dump_header=OUT/'headers'/(rid+'.txt'),write_out='%{http_code}',max_time=180,connect_timeout=20)])
    p.save(OUT/'private_pointer.json',dict(config=config));print('curl --config '+config)


def finish(exitcode,http):
    # Reuse saved-outcome precedence and conservative cost/schema validation.
    b.finish(exitcode,http)
    if PHASE=='resource':
        m=manifest();attempts=c.history(m);rid=attempts[-1]['sample_id'];final=c.load(OUT/'finished'/(rid+'.json'))
        print(json.dumps(dict(resource_delivery_passed=final['outcome']['status']=='answered' and final['continue_permitted'],factual_accuracy_not_used_for_gate=True)))


def status():
    m=manifest();attempts=c.history(m);finals=[c.load(path) for path in (OUT/'finished').glob('*.json')]
    from collections import Counter
    failed=any(not r['continue_permitted'] or (PHASE=='resource' and r['outcome']['status']!='answered') for r in finals)
    print(json.dumps(dict(phase=PHASE,n_planned=N[PHASE],n_attempted=len(attempts),n_finalized=len(finals),outcomes=dict(Counter(r['outcome']['status'] for r in finals)),
        stopped=failed,phase_deliveries_complete=len(attempts)==len(finals)==N[PHASE] and not failed,
        recorded_cost_usd=str(sum((Decimal(r['recorded_cost_usd']) for r in finals if r['recorded_cost_usd'] is not None),Decimal(0))),
        active_attempt=(OUT/'active.json').exists(),accuracy_not_reported=True,original_study_remains_paused=True),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=tuple(N),required=True)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure(args.phase)
    if args.stage=='prepare':prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Need actual curl exit and HTTP status')
        finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':status,'refresh-config':b.refresh_config,'refresh':b.refresh}[args.stage]()
