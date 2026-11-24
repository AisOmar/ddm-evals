"""Twelve paired delivery probes on DeepInfra FP8 and Tenstorrent FP8."""
import argparse
from decimal import Decimal
import importlib.util
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('provider_comparison_helpers',ROOT/'scripts/72_qwen_delivery_diagnostic.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
w,r,a,b,c,p=d.w,d.r,d.a,d.b,d.c,d.p
BASE=ROOT/'results/research_directions/qwen_provider_comparison_20261022'
OUT=BASE/'diagnostic'
PROTOCOL=ROOT/'docs/QWEN_PROVIDER_COMPARISON_PROTOCOL.md'
ROUTES={'DeepInfra':('DeepInfra','deepinfra/fp8','fp8'),
        'Tenstorrent':('Tenstorrent','tenstorrent/fp8','fp8')}
QUESTIONS=[
    dict(item_id='P01',stem='A register starts at 6. First add 7 to its value, then double the result. What is its final value?',answer='26',distractor='19'),
    dict(item_id='P02',stem='A runner covers 8 km at 4 km/h and another 8 km at 8 km/h, without stopping. What is total distance divided by total time for the 16 km trip?',answer='16/3 km/h',distractor='6 km/h'),
    dict(item_id='P03',stem='Every admitted visitor wears a wristband. This visitor wears no wristband. Using only these premises, could this visitor be admitted?',answer='No',distractor='Yes'),
]


def configure():
    w.BASE=BASE;w.N={'diagnostic':12};w.CEILINGS={'diagnostic':Decimal('.05')}
    a.ROUTES=dict(ROUTES)
    p.MODELS={name:'qwen/qwen3-32b' for name in ROUTES}
    w.configure('diagnostic')


def plan(endpoints):
    rng=random.Random(20261022074);trials=[]
    for i,row in enumerate(QUESTIONS):
        for repeat in (1,2):
            letter='A' if (i+repeat)%2 else 'B'
            options={k:row['answer'] if k==letter else row['distractor'] for k in 'AB'}
            names=list(ROUTES);rng.shuffle(names)
            text=w.INSTRUCTION+'\n\n'+row['stem']+'\n\nA. '+options['A']+'\nB. '+options['B']
            for name in names:
                provider,tag,quant=ROUTES[name];ep=endpoints[name]
                req=dict(model='qwen/qwen3-32b',messages=[dict(role='user',content=text)],temperature=.7,max_tokens=2048,
                    provider=dict(order=[tag],only=[tag],allow_fallbacks=False,quantizations=[quant],require_parameters=True,
                    max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
                if ep.get('max_completion_tokens',0)<2048 or ep.get('context_length',0)<p.input_bound(req['messages'])+2048:
                    raise ValueError('Insufficient endpoint capacity')
                trials.append(dict(sample_id=f'{row["item_id"]}__r{repeat}__{name}',item_id=row['item_id'],
                    repeat=repeat,mode=name,model=name,expected_provider=provider,options=options,
                    correct_letter=letter,request=req))
    if len(trials)!=12 or len({t['sample_id'] for t in trials})!=12:raise ValueError('Invalid provider coverage')
    return trials


def freeze():
    a.no_other_collection()
    pointer=OUT/'preflight_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:a.endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in ROUTES.items()}
        trials=plan(endpoints)
        old=[]
        for path in (ROOT/'results/research_directions/wording_pilot_20261022/packet.json',
                     ROOT/'results/research_directions/short_reasoning_v4_20261022/author/packet_with_solutions.json'):
            old+=c.load(path)
        old+=d.QUESTION_ROWS
        if {x['stem'] for x in old}&{x['stem'] for x in QUESTIONS}:raise ValueError('Question overlaps earlier work')
        credits=c.load(folder/'credits.json')['data']
        available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        reserve=sum(map(p.trial_bound,trials))
        if not available.is_finite() or not 0<reserve<=Decimal('.05') or available<reserve:
            raise ValueError('Full reserve exceeds ceiling or credit')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<reserve):
            raise ValueError('Insufficient key allowance')
        paths=[Path(__file__),PROTOCOL,ROOT/'scripts/75_qwen_provider_report.py',ROOT/'scripts/73_qwen_diagnostic_report.py',
            ROOT/'scripts/72_qwen_delivery_diagnostic.py',ROOT/'scripts/70_wording_collect.py',ROOT/'scripts/63_manageable_collect.py',
            ROOT/'scripts/60_calibrate_reviewed_packet.py',ROOT/'scripts/58_alternate_provider_canary.py',
            ROOT/'scripts/56_reliance_canary.py',ROOT/'scripts/54_reliance_calibration.py',ROOT/'scripts/50_open_dataset_feasibility.py',
            BASE/'selection_snapshot.json',ROOT/'results/research_directions/qwen_visible_answer_diagnostic_20261022/final_artifact_hashes.json']
        p.save(OUT/'manifest.json',dict(created_at=p.now(),phase='diagnostic',n_planned=12,trials=trials,
            preflight_started_at=state['created_at'],endpoint_snapshot=endpoints,maximum_cost_usd=str(reserve),cost_cap_usd='0.05',
            execution_authorization='User: do that, referring to testing another Qwen deployment with unchanged output requirements.',
            min_interval_seconds=5,timeout_seconds=180,max_attempts_per_trial=1,automatic_retries=0,
            question_review='Self-contained author checks; no independent review claimed; correctness never gates delivery',
            original_study_remains_paused=True,wording_pilot_remains_stopped=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(c.json.dumps(dict(n_planned=12,full_reserve_usd=str(reserve),preflight_passed=True)))
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
        if args.curl_exit is None or args.http_status is None:parser.error('Actual HTTP/curl result required')
        r.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':r.status,
          'refresh-config':b.refresh_config,'refresh':b.refresh}[args.stage]()
