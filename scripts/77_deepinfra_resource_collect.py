"""Independent-review-gated, fresh 16-call resource check on DeepInfra/DekaLLM."""
import argparse
from decimal import Decimal
import importlib.util
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deepinfra_resource_transport',ROOT/'scripts/70_wording_collect.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
r,a,b,c,p=w.r,w.a,w.b,w.c,w.p
BASE=ROOT/'results/research_directions/deepinfra_wording_resource_20261022'
OUT=BASE/'resource'
PROTOCOL=ROOT/'docs/DEEPINFRA_WORDING_RESOURCE_PROTOCOL.md'
ROUTES={'gpt-oss':('DekaLLM','dekallm/bf16','bf16'),
        'Qwen3':('DeepInfra','deepinfra/fp8','fp8')}


def configure():
    w.BASE=BASE;w.N={'resource':16};w.CEILINGS={'resource':Decimal('.10')}
    a.ROUTES=dict(ROUTES)
    w.configure('resource')


def review_gate():
    b.verify_lock(BASE/'packet_hashes.json')
    w.verify_review_lock(BASE/'independent_review/INITIAL_SHA256_LOCK.json')
    rows=c.load(BASE/'packet.json');review=c.load(BASE/'independent_review/initial_judgments.json')['items']
    indexed={j['review_id']:j for j in review}
    if len(rows)!=8 or len(review)!=8 or set(indexed)!={x['review_id'] for x in rows}:
        raise ValueError('Independent review coverage mismatch')
    for row in rows:
        j=indexed[row['review_id']]
        if j['unique_answer'] is not True or j['must_fix'] is not False or j['chosen_letter']!=row['initial_letter']:
            raise ValueError('Independent review blocker or key disagreement: '+row['review_id'])
        if str(j['derived_answer']).strip().casefold()!=row['answer'].strip().casefold():
            raise ValueError('Independent answer differs: '+row['review_id'])
    return rows


def plan(rows,endpoints):
    order=sorted(rows,key=lambda x:x['item_id']);random.Random(20261022077).shuffle(order)
    trials=[]
    for i,row in enumerate(order):
        names=list(ROUTES)
        if i%2:names.reverse()
        for name in names:
            provider,tag,quant=ROUTES[name];ep=endpoints[name]
            req=dict(model=p.MODELS[name],messages=[dict(role='user',content=w.request_text(row,row['options'],'none'))],
                temperature=.7,max_tokens=2048,provider=dict(order=[tag],only=[tag],allow_fallbacks=False,
                    quantizations=[quant],require_parameters=True,
                    max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
            if ep.get('max_completion_tokens',0)<2048 or ep.get('context_length',0)<p.input_bound(req['messages'])+2048:
                raise ValueError('Insufficient endpoint capacity')
            trials.append(dict(sample_id=row['item_id']+'__'+name,item_id=row['item_id'],review_id=row['review_id'],
                family=row['family'],version=row['version'],model=name,expected_provider=provider,
                options=row['options'],correct_letter=row['initial_letter'],request=req))
    if len(trials)!=16 or len({x['sample_id'] for x in trials})!=16:raise ValueError('Incorrect resource coverage')
    return trials


def freeze():
    a.no_other_collection();rows=review_gate()
    pointer=OUT/'preflight_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:a.endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in ROUTES.items()}
        trials=plan(rows,endpoints);reserve=sum(map(p.trial_bound,trials))
        credits=c.load(folder/'credits.json')['data']
        available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0<reserve<=Decimal('.10') or available<reserve:
            raise ValueError('Full reserve exceeds ceiling or credit')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<reserve):
            raise ValueError('Insufficient key allowance')
        paths=[Path(__file__),PROTOCOL,ROOT/'scripts/78_deepinfra_resource_report.py',ROOT/'scripts/76_deepinfra_resource_packet.py',
            ROOT/'scripts/70_wording_collect.py',ROOT/'scripts/63_manageable_collect.py',ROOT/'scripts/60_calibrate_reviewed_packet.py',
            ROOT/'scripts/58_alternate_provider_canary.py',ROOT/'scripts/56_reliance_canary.py',
            ROOT/'scripts/54_reliance_calibration.py',ROOT/'scripts/50_open_dataset_feasibility.py',
            BASE/'packet.json',BASE/'packet_hashes.json',BASE/'design.json',
            ROOT/'results/research_directions/qwen_provider_comparison_20261022/final_artifact_hashes.json']
        paths+=sorted((BASE/'independent_review').glob('*.json'))
        p.save(OUT/'manifest.json',dict(created_at=p.now(),phase='resource',n_planned=16,trials=trials,
            preflight_started_at=state['created_at'],endpoint_snapshot=endpoints,maximum_cost_usd=str(reserve),cost_cap_usd='0.10',
            execution_authorization='User: do that, referring to qualifying DeepInfra on the full resource check before the pilot.',
            min_interval_seconds=5,timeout_seconds=180,max_attempts_per_trial=1,automatic_retries=0,
            independent_review_complete=True,original_study_remains_paused=True,pilot_calls_included=0,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(c.json.dumps(dict(n_planned=16,full_reserve_usd=str(reserve),preflight_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();pointer.unlink()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure()
    if args.stage=='prepare':r.prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Actual curl and HTTP status required')
        r.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':r.status,
          'refresh-config':b.refresh_config,'refresh':b.refresh}[args.stage]()
