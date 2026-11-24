"""Fresh, separate development calibration on active alternate deployments."""
import argparse
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('alternate_bounded_transport',ROOT/'scripts/99_rate_limit_calibration_recovery.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c=r.c
OLD_RECOVERY=r.BASE
BASE=c.l.PACKET/'alternate_http2_20261026'
PROTOCOL=ROOT/'docs/SELECTIVE_RELIANCE_ALTERNATE_DEPLOYMENTS.md'
ROUTES={'gpt-oss':('AkashML','akashml/bf16','bf16'),'Qwen3':('Tenstorrent','tenstorrent/fp8','fp8')}
COUNTS={'qualification':12,'calibration':48}
CAPS={'qualification':Decimal('.04'),'calibration':Decimal('.12')}
PHASE,OUT='qualification',BASE/'qualification'


def configure(phase):
    global PHASE,OUT
    PHASE,OUT=phase,BASE/phase
    r.BASE=OUT
    c.l.ROUTES=dict(ROUTES);c.a.ROUTES=dict(ROUTES)
    r.configure()


def plan(phase,endpoints):
    rows=c.r.c.review_gate()
    trials=c.r.plan(rows,endpoints,'resource' if phase=='qualification' else 'calibration')
    for trial in trials:
        trial['request']['stream']=True
        trial['model_aliases']=c.ALIASES[trial['request']['model']]
    if len(trials)!=COUNTS[phase]:raise ValueError('Wrong fixed cohort size')
    return trials


def prior_bound():
    m=c.c.load(OLD_RECOVERY/'manifest.json')
    amount=Decimal(m['previous_cost_upper_usd'])
    for path in (OLD_RECOVERY/'finished').glob('*.json'):
        row=c.c.load(path)
        amount+=Decimal(row['recorded_cost_usd']) if row['recorded_cost_usd'] is not None else Decimal(row['reserved_cost_usd'])
    return amount


def check_qualification():
    m=c.c.load(BASE/'qualification/manifest.json');c.verify_hashes(m['input_hashes'])
    records=[c.c.load(p) for p in (BASE/'qualification/finished').glob('*.json')]
    _,accepted=r.schedule(m,records)
    if len(accepted)!=12 or any(row['outcome']['status']!='answered' for row in accepted.values()):
        raise ValueError('Alternate deployment qualification did not pass')
    if any(row['fatal_stop'] for row in records):raise ValueError('Qualification transport failure')
    for row in records:
        aid=row['attempt_id']
        for directory,suffix,key in [('requests','.json','request_sha256'),('raw','.sse','raw_sha256'),('headers','.txt','headers_sha256')]:
            if c.p.sha(BASE/'qualification'/directory/(aid+suffix))!=row[key]:raise ValueError('Qualification artifact changed')
        if row['normalized_sha256'] and c.p.sha(BASE/'qualification/normalized'/(aid+'.json'))!=row['normalized_sha256']:
            raise ValueError('Qualification normalized response changed')


def freeze():
    c.a.no_other_collection();c.r.c.review_gate()
    if PHASE=='calibration':check_qualification()
    pointer=OUT/'preflight_pointer.json';state=c.c.load(pointer);folder=Path(state['folder'])
    try:
        if not 0<=c.c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:c.a.endpoint(c.c.load(folder/(name+'.json')),route[0],route[2]) for name,route in ROUTES.items()}
        trials=plan(PHASE,endpoints)
        reserve=sum(map(c.p.trial_bound,trials))+3*max(map(c.p.trial_bound,trials))
        previous=prior_bound()
        if PHASE=='calibration':
            for path in (BASE/'qualification/finished').glob('*.json'):
                row=c.c.load(path);previous+=Decimal(row['recorded_cost_usd']) if row['recorded_cost_usd'] is not None else Decimal(row['reserved_cost_usd'])
        credit=c.c.load(folder/'credits.json')['data'];available=Decimal(str(credit['total_credits']))-Decimal(str(credit['total_usage']))
        allowance=c.c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not 0<reserve<=CAPS[PHASE] or previous+reserve>1 or available<reserve:
            raise ValueError('Full phase cost or cumulative development bound exceeded')
        if allowance is not None and Decimal(str(allowance))<reserve:raise ValueError('Key allowance insufficient')
        for name in endpoints:c.p.save(OUT/(name+'_endpoints.json'),c.c.load(folder/(name+'.json')))
        old=c.c.load(OLD_RECOVERY/'manifest.json')
        paths=[Path(__file__),PROTOCOL,ROOT/'scripts/99_rate_limit_calibration_recovery.py',ROOT/'scripts/98_complete_calibration.py',
               ROOT/'scripts/97_http2_stream_collection.py',ROOT/'scripts/95_stream_collection.py',ROOT/'scripts/94_stream_transport.py',
               OLD_RECOVERY/'manifest.json',c.l.PACKET/'author/packet_with_solutions.json',c.r.c.q.OUT/'review_readiness.json']
        paths+=list((OLD_RECOVERY/'finished').glob('*.json'))
        if PHASE=='calibration':paths+=[BASE/'qualification/manifest.json']+list((BASE/'qualification/finished').glob('*.json'))
        c.p.save(OUT/'manifest.json',dict(created_at=c.p.now(),preflight_started_at=state['created_at'],phase=PHASE,
            authorization='User: okay do that; delivery repair and separately versioned calibration after original pair failures.',
            trials=trials,retained=[],cohort_planned=COUNTS[PHASE],new_deployment_cohort=True,old_observations_combined=False,
            endpoint_snapshot=endpoints,max_total_attempts_per_slot=2,max_extra_retries=4,
            actual_conditional_retry_limit=3,legacy_retry_counter_offset=1,max_new_calls=COUNTS[PHASE]+3,
            maximum_cost_usd=str(reserve),cost_cap_usd=str(CAPS[PHASE]),previous_cost_upper_usd=str(previous),
            original_rejection_sample_id=None,original_rejection_headers=old['original_rejection_headers'],
            original_rejection_finished_at=old['original_rejection_finished_at'],
            original_header_is_prior_run_global_cooldown_only=True,
            input_hashes={str(p.relative_to(ROOT)):c.p.sha(p) for p in paths},advice_calls_included=0,original_study_remains_paused=True))
        print(json.dumps(dict(phase=PHASE,planned_slots=COUNTS[PHASE],full_retry_inclusive_reserve_usd=str(reserve),previous_cost_upper_usd=str(previous))))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for p in folder.iterdir():p.unlink()
        folder.rmdir();pointer.unlink()


def analyze():
    m=r.manifest();records=r.ledger();pending,accepted=r.schedule(m,records)
    if pending is not None or len(accepted)!=48 or any(row['fatal_stop'] for row in records):
        raise ValueError('Complete 48-slot alternate calibration required')
    for row in records:
        aid=row['attempt_id']
        for directory,suffix,key in [('requests','.json','request_sha256'),('raw','.sse','raw_sha256'),('headers','.txt','headers_sha256')]:
            if c.p.sha(OUT/directory/(aid+suffix))!=row[key]:raise ValueError('Attempt artifact changed')
    models=[]
    for model in ROUTES:
        group=[(t,accepted[t['sample_id']]) for t in m['trials'] if t['model']==model]
        answered=[(t,f) for t,f in group if f['outcome']['status']=='answered']
        correct=sum(f['outcome']['correct'] is True for _,f in answered);missing=len(group)-len(answered)
        accuracy=correct/len(answered) if answered else None
        models.append(dict(model=model,provider=ROUTES[model][0],planned=len(group),recognized=len(answered),correct=correct,
            factual_errors=len(answered)-correct,unknown=missing,recognized_answer_accuracy=accuracy,
            correct_yield=correct/len(group),factual_accuracy_bounds=[correct/len(group),(correct+missing)/len(group)],
            ceiling_warning=bool(accuracy is not None and accuracy>.90),nonanswer_warning=missing/len(group)>.05,
            development_difficulty_supported=accuracy is not None and .55<=accuracy<=.90 and correct<len(answered) and missing/len(group)<=.05,
            outcome_counts=dict(Counter(f['outcome']['status'] for _,f in group)),
            item_results=[dict(item_id=t['item_id'],family=t['family'],repeat=t['repeat'],outcome=f['outcome']) for t,f in group]))
    result=dict(created_at=c.p.now(),planned_slots=48,finalized_slots=48,http_attempts=len(records),retained_old_observations=0,
        new_deployment_cohort=True,question_families=6,models=models,
        advice_development_supported=all(row['development_difficulty_supported'] for row in models),
        inference='Descriptive development; no intervention efficacy or overall safety claim.',original_study_remains_paused=True)
    c.p.save(OUT/'analysis.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2))
    for row in models:print(json.dumps({k:v for k,v in row.items() if k!='item_results'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=tuple(COUNTS),default='qualification')
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh','analyze'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure(args.phase)
    if args.stage=='prepare':r.prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Actual statuses required')
        r.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.c.preflight_config,'freeze':freeze,'status':r.status,'refresh-config':c.b.refresh_config,'refresh':c.b.refresh,'analyze':analyze}[args.stage]()
