"""Freeze/collect the authorized 288-call pilot after reviewed resource qualification."""
import argparse
from decimal import Decimal
import importlib.util
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


w=module('deepinfra_pilot_transport','70_wording_collect.py')
g=module('deepinfra_pilot_resource_gate','77_deepinfra_resource_collect.py')
r,a,b,c,p=w.r,w.a,w.b,w.c,w.p
BASE=ROOT/'results/research_directions/deepinfra_wording_pilot_20261022'
OUT=BASE/'pilot'
SOURCE=ROOT/'results/research_directions/wording_pilot_20261022'
PROTOCOL=ROOT/'docs/DEEPINFRA_WORDING_PILOT_AMENDMENT.md'
ROUTES={'gpt-oss':('DekaLLM','dekallm/bf16','bf16'),
        'Qwen3':('DeepInfra','deepinfra/fp8','fp8')}


def configure(phase='pilot'):
    if phase!='pilot':raise ValueError('Only the pilot phase is implemented in this version')
    w.BASE=BASE;w.N={'pilot':288};w.CEILINGS={'pilot':Decimal('.90')}
    a.ROUTES=dict(ROUTES)
    w.configure('pilot')


def gates():
    # Verify unchanged original questions/reviews in their original directory.
    previous=w.BASE
    try:
        w.BASE=SOURCE
        rows=w.review_gate()
    finally:w.BASE=previous
    rows=[row for row in rows if row['cohort']=='pilot']
    if len(rows)!=24 or len({x['problem_id'] for x in rows})!=8:
        raise ValueError('Reviewed pilot coverage changed')
    g.configure();g.review_gate();g.w.audit_phase('resource')
    return rows


def prior_recorded_cost():
    parents=ROOT/'results/research_directions'
    costs=[c.load(SOURCE/'final_status.json')['recorded_cost_usd'],
        c.load(parents/'qwen_visible_answer_diagnostic_20261022/summary.json')['recorded_cost_usd'],
        c.load(parents/'qwen_provider_comparison_20261022/summary.json')['recorded_cost_usd'],
        c.load(parents/'deepinfra_wording_resource_20261022/summary.json')['recorded_cost_usd']]
    return sum((Decimal(x) for x in costs),Decimal(0))


def freeze():
    a.no_other_collection()
    pointer=OUT/'preflight_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        rows=gates()
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:a.endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in ROUTES.items()}
        trials=w.plan(rows,endpoints,'pilot');reserve=sum(map(p.trial_bound,trials));earlier=prior_recorded_cost()
        credits=c.load(folder/'credits.json')['data']
        available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0<reserve<=Decimal('.90') or available<reserve or earlier+reserve>1:
            raise ValueError('Pilot reserve exceeds phase/development cap or credit')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<reserve):
            raise ValueError('Insufficient key allowance')
        paths=[Path(__file__),PROTOCOL,ROOT/'scripts/80_deepinfra_wording_analysis.py',ROOT/'scripts/69_wording_analysis.py',
            ROOT/'docs/WORDING_PILOT_EXECUTION_PROTOCOL.md',ROOT/'scripts/70_wording_collect.py',
            ROOT/'scripts/77_deepinfra_resource_collect.py',ROOT/'scripts/63_manageable_collect.py',
            ROOT/'scripts/60_calibrate_reviewed_packet.py',ROOT/'scripts/58_alternate_provider_canary.py',
            ROOT/'scripts/56_reliance_canary.py',ROOT/'scripts/54_reliance_calibration.py',ROOT/'scripts/50_open_dataset_feasibility.py',
            SOURCE/'packet.json',SOURCE/'packet_hashes.json',SOURCE/'design.json',SOURCE/'final_artifact_hashes.json',
            g.BASE/'packet.json',g.BASE/'packet_hashes.json',g.BASE/'final_artifact_hashes.json',g.BASE/'resource/manifest.json']
        paths+=sorted((SOURCE/'independent_review').glob('*.json'))
        paths+=sorted((g.BASE/'independent_review').glob('*.json'))
        for subfolder in ('requests','raw','headers','finished'):
            paths+=sorted((g.BASE/'resource'/subfolder).glob('*'))
        p.save(OUT/'manifest.json',dict(created_at=p.now(),phase='pilot',n_planned=288,trials=trials,
            preflight_started_at=state['created_at'],endpoint_snapshot=endpoints,maximum_cost_usd=str(reserve),
            cost_cap_usd='0.90',total_development_ceiling_usd='1.00',earlier_recorded_development_cost_usd=str(earlier),
            execution_authorization='User: go ahead, after proposal to prepare and run the 288-call wording pilot with DeepInfra.',
            max_attempts_per_trial=1,automatic_retries=0,min_interval_seconds=5,timeout_seconds=180,
            resource_gate_passed=True,independent_review_complete=True,original_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(c.json.dumps(dict(n_planned=288,full_reserve_usd=str(reserve),earlier_recorded_cost_usd=str(earlier),preflight_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();pointer.unlink()


def prepare(authorized=False):
    if not authorized:raise ValueError('Explicit authorized flag required')
    # Wait only the remaining portion of the minimum start interval, at most 5 s.
    # The preserved collector rechecks all prerequisites and prior outcomes.
    files=sorted((OUT/'attempts').glob('*.json'))
    if files:
        delay=5-c.seconds_since(c.load(files[-1])['prepared_at'])
        if delay>0:time.sleep(min(delay+.02,5.02))
    r.prepare(True)


def audit_phase(phase='pilot',require_complete=True):
    if phase!='pilot':raise ValueError('Pilot-only audit')
    return w.audit_phase('pilot',require_complete=require_complete)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure()
    if args.stage=='prepare':prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Actual curl and HTTP status required')
        r.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':r.status,
          'refresh-config':b.refresh_config,'refresh':b.refresh}[args.stage]()
