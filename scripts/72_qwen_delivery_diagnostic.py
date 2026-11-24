"""Bounded three-mode diagnostic; preserves the failed wording experiment."""
import argparse
from decimal import Decimal
import importlib.util
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('qwen_diagnostic_base',ROOT/'scripts/70_wording_collect.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
r, a, b, c, p = w.r, w.a, w.b, w.c, w.p
BASE = ROOT/'results/research_directions/qwen_visible_answer_diagnostic_20261022'
OUT = BASE/'diagnostic'
PROTOCOL = ROOT/'docs/QWEN_VISIBLE_ANSWER_DIAGNOSTIC_PROTOCOL.md'
MODES = ('default','reasoning_disabled','soft_no_think')
QUESTION_ROWS = [
    dict(item_id='D01',stem='A register starts at 8. First add 5 to its value, then double the result. What is its final value?',answer='26',distractor='21'),
    dict(item_id='D02',stem='A cyclist covers 10 km at 5 km/h and another 10 km at 10 km/h, without stopping. What is total distance divided by total time for the 20 km trip?',answer='20/3 km/h',distractor='15/2 km/h'),
    dict(item_id='D03',stem='Every approved crate has a stamp. This crate has no stamp. Using only these premises, could this crate be approved?',answer='No',distractor='Yes'),
]


def configure():
    w.BASE = BASE
    w.N = {'diagnostic':18}
    w.CEILINGS = {'diagnostic':Decimal('.05')}
    a.ROUTES = {'Qwen3':('Tenstorrent','tenstorrent/fp8','fp8')}
    p.MODELS = {'Qwen3':'qwen/qwen3-32b'}
    w.configure('diagnostic')


def plan(endpoint):
    rng = random.Random(20261022072)
    trials = []
    for i, row in enumerate(QUESTION_ROWS):
        for repeat in range(1,3):
            letter = 'A' if (i+repeat)%2 else 'B'
            options = {k:row['answer'] if k==letter else row['distractor'] for k in 'AB'}
            modes = list(MODES)
            rng.shuffle(modes)
            for mode in modes:
                text = w.INSTRUCTION+'\n\n'+row['stem']+'\n\nA. '+options['A']+'\nB. '+options['B']
                if mode=='soft_no_think':
                    text += '\n\n/no_think'
                req = dict(model='qwen/qwen3-32b',messages=[dict(role='user',content=text)],temperature=.7,max_tokens=2048,
                    provider=dict(order=['tenstorrent/fp8'],only=['tenstorrent/fp8'],allow_fallbacks=False,
                        quantizations=['fp8'],require_parameters=True,
                        max_price={k:float(Decimal(endpoint['pricing'][k])*1000000) for k in ('prompt','completion')}))
                if mode=='reasoning_disabled':
                    req['reasoning'] = {'enabled':False}
                if endpoint.get('max_completion_tokens',0)<2048 or endpoint.get('context_length',0)<p.input_bound(req['messages'])+2048:
                    raise ValueError('Insufficient endpoint capacity')
                trials.append(dict(sample_id=f'{row["item_id"]}__r{repeat}__{mode}',item_id=row['item_id'],mode=mode,
                    repeat=repeat,model='Qwen3',expected_provider='Tenstorrent',options=options,
                    correct_letter=letter,request=req))
    if len(trials)!=18 or len({t['sample_id'] for t in trials})!=18:
        raise ValueError('Invalid diagnostic coverage')
    return trials


def freeze():
    a.no_other_collection()
    pointer=OUT/'preflight_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:
            raise ValueError('Stale preflight')
        ep=a.endpoint(c.load(folder/'Qwen3.json'),'Tenstorrent','fp8')
        if 'reasoning' not in ep.get('supported_parameters',[]):
            raise ValueError('Endpoint does not advertise reasoning support')
        trials=plan(ep)
        previous=ROOT/'results/research_directions/wording_pilot_20261022/packet.json'
        old=c.load(previous)+c.load(ROOT/'results/research_directions/short_reasoning_v4_20261022/author/packet_with_solutions.json')
        if {x['stem'] for x in old}&{x['stem'] for x in QUESTION_ROWS}:
            raise ValueError('Diagnostic questions overlap prior items')
        credits=c.load(folder/'credits.json')['data']
        available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        reserve=sum(map(p.trial_bound,trials))
        if not available.is_finite() or not 0<reserve<=Decimal('.05') or available<reserve:
            raise ValueError('Full reserve exceeds diagnostic budget or credit')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<reserve):
            raise ValueError('Insufficient key allowance')
        original=ROOT/'results/research_directions/wording_pilot_20261022'
        paths=[Path(__file__),PROTOCOL,ROOT/'scripts/73_qwen_diagnostic_report.py',ROOT/'scripts/70_wording_collect.py',
            ROOT/'scripts/63_manageable_collect.py',ROOT/'scripts/60_calibrate_reviewed_packet.py',
            ROOT/'scripts/58_alternate_provider_canary.py',ROOT/'scripts/56_reliance_canary.py',
            ROOT/'scripts/54_reliance_calibration.py',ROOT/'scripts/50_open_dataset_feasibility.py',
            original/'final_artifact_hashes.json',original/'resource/raw/R02__neutral__none__r1__Qwen3.json']
        p.save(OUT/'manifest.json',dict(created_at=p.now(),phase='diagnostic',n_planned=18,trials=trials,
            preflight_started_at=state['created_at'],endpoint_snapshot={'Qwen3':ep},maximum_cost_usd=str(reserve),
            cost_cap_usd='0.05',execution_authorization='User: do that, referring to diagnosing Qwen missing final answers.',
            min_interval_seconds=5,timeout_seconds=180,max_attempts_per_trial=1,automatic_retries=0,
            question_review='self-contained diagnostic author checks; not independent review; correctness never gates success',
            original_study_remains_paused=True,wording_pilot_remains_stopped=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(c.json.dumps(dict(n_planned=18,full_reserve_usd=str(reserve),preflight_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();pointer.unlink()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh'),required=True)
    parser.add_argument('--execute-authorized',action='store_true')
    parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure()
    if args.stage=='prepare':r.prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Actual HTTP/curl result required')
        r.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':r.status,
          'refresh-config':b.refresh_config,'refresh':b.refresh}[args.stage]()
