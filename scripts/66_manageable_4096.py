"""One bounded resource requalification with a 4096-token cap; preserve 2048 run."""
import argparse
from decimal import Decimal
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tenstorrent_setup',ROOT/'scripts/65_manageable_tenstorrent.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
r=w.r;a,c,p=r.a,r.c,r.p
BASE=r.BASE
EXEC=BASE/'execution_4096'
old_gate=r.check_resource_gate


def configure(phase):
    r.configure(phase);r.OUT=EXEC/phase;r.b.OUT=r.OUT;c.OUT=r.OUT


def resource_gate():
    original=r.BASE
    try:
        r.BASE=EXEC
        return old_gate()
    finally:r.BASE=original


r.check_resource_gate=resource_gate


def freeze():
    a.no_other_collection();rows=r.check_review()
    if r.PHASE=='calibration':resource_gate()
    pointer=r.OUT/'preflight_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:a.endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in a.ROUTES.items()}
        trials=[]
        for qi,row in enumerate(x for x in rows if x['split']==r.PHASE):
            for repeat in range(1 if r.PHASE=='resource' else 2):
                names=list(a.ROUTES)
                if (qi+repeat)%2:names.reverse()
                for name in names:
                    provider,slug,quant=a.ROUTES[name];ep=endpoints[name]
                    text=('Answer the question. Be concise. Reply with A or B only on the final line.\n\n'
                        +row['stem']+'\n\nA. '+row['options']['A']+'\nB. '+row['options']['B'])
                    req=dict(model=p.MODELS[name],messages=[dict(role='user',content=text)],temperature=.7,max_tokens=4096,
                        provider=dict(order=[slug],only=[slug],allow_fallbacks=False,quantizations=[quant],require_parameters=True,
                            max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
                    if ep.get('max_completion_tokens',0)<4096 or ep.get('context_length',0)<p.input_bound(req['messages'])+4096:raise ValueError('Insufficient capacity')
                    trials.append(dict(sample_id=f'{row["item_id"]}__r{repeat+1}__{name}',item_id=row['item_id'],family=row['family'],repeat=repeat+1,
                        model=name,expected_provider=provider,options=row['options'],correct_letter=row['correct_letter'],request=req))
        if len(trials)!=r.N[r.PHASE] or len({t['sample_id'] for t in trials})!=len(trials):raise ValueError('Trial coverage invalid')
        bound=sum(map(p.trial_bound,trials));credits=c.load(folder/'credits.json')['data']
        available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        prior=c.load(BASE/'resource/manifest.json')
        # Count the full earlier resource reserve, not only recorded charges.
        total_ceiling=Decimal('.60')
        if r.PHASE=='resource':
            reserved=Decimal(prior['maximum_cost_usd'])+bound+Decimal('.50')
        else:
            reserved=Decimal(prior['maximum_cost_usd'])+Decimal(c.load(EXEC/'resource/manifest.json')['maximum_cost_usd'])+bound
        if (not available.is_finite() or not 0<bound<=r.CEILINGS[r.PHASE] or available<bound or reserved>total_ceiling):
            raise ValueError('Budget or combined reserve invalid')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<bound):raise ValueError('Key allowance insufficient')
        paths=[Path(__file__),ROOT/'scripts/63_manageable_collect.py',ROOT/'scripts/64_manageable_analysis.py',
            ROOT/'scripts/65_manageable_tenstorrent.py',ROOT/'scripts/60_calibrate_reviewed_packet.py',ROOT/'scripts/61_analyze_baseline_calibration.py',
            ROOT/'scripts/58_alternate_provider_canary.py',ROOT/'scripts/56_reliance_canary.py',ROOT/'scripts/54_reliance_calibration.py',
            ROOT/'scripts/50_open_dataset_feasibility.py',ROOT/'docs/MANAGEABLE_CALIBRATION_V3_PROTOCOL.md',
            ROOT/'docs/MANAGEABLE_DEPLOYMENT_AMENDMENT.md',ROOT/'docs/MANAGEABLE_RESOURCE_4096_AMENDMENT.md',
            BASE/'packet.json',BASE/'packet_hashes.json',BASE/'independent_review/INITIAL_SHA256_LOCK.json',
            BASE/'independent_review/initial_judgments.json',BASE/'resource/manifest.json']
        if r.PHASE=='calibration':paths += [EXEC/'resource/manifest.json']+list((EXEC/'resource/finished').glob('*.json'))
        p.save(r.OUT/'manifest.json',dict(created_at=p.now(),phase=r.PHASE,n_planned=r.N[r.PHASE],preflight_started_at=state['created_at'],trials=trials,
            execution_authorization='User authorized resource tuning and small calibration; one bounded cap requalification before calibration',
            endpoint_snapshot=endpoints,maximum_cost_usd=str(bound),cost_cap_usd=str(r.CEILINGS[r.PHASE]),combined_reserve_ceiling_usd='.60',
            max_attempts_per_trial=1,automatic_retries=0,min_interval_seconds=5,timeout_seconds=180,independent_review_complete=True,
            old_resource_failures_preserved=True,original_study_remains_paused=True,input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(r.json.dumps(dict(phase=r.PHASE,n_planned=len(trials),reserve_usd=str(bound),completion_cap=4096)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();pointer.unlink()


def analyze():
    if r.PHASE!='calibration':raise ValueError('Only calibration has an efficacy-free accuracy analysis')
    spec=importlib.util.spec_from_file_location('manageable_analysis',ROOT/'scripts/64_manageable_analysis.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    h.OUT=EXEC/'calibration';h.r.configure('calibration');h.r.OUT=h.OUT;h.r.b.OUT=h.OUT;h.r.c.OUT=h.OUT
    h.main()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=tuple(r.N),required=True)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh','analyze'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure(args.phase)
    if args.stage=='prepare':r.prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Need actual curl exit and HTTP status')
        r.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':r.status,'refresh-config':r.b.refresh_config,'refresh':r.b.refresh,'analyze':analyze}[args.stage]()
