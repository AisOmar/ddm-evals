"""Versioned mixed-provider canary; reuse tested serial/ledger guards unchanged."""
import argparse
import copy
from decimal import Decimal
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('base_canary',ROOT/'scripts/56_reliance_canary.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
p = c.p
c.OUT = c.BASE/'alternate_provider_canary'
ROUTES = {'gpt-oss':('DekaLLM','dekallm/bf16','bf16'),
          'Qwen3':('DeepInfra','deepinfra/fp8','fp8')}


def endpoint(data,provider,quantization):
    matches = [e for e in data['data']['endpoints'] if e.get('provider_name')==provider
               and e.get('quantization')==quantization and e.get('status')==0]
    if len(matches)!=1:
        raise ValueError('Exactly one active matching endpoint required')
    ep = matches[0]
    if not {'temperature','max_tokens'}<=set(ep.get('supported_parameters',[])):
        raise ValueError('Required parameters unsupported')
    prices = {k:Decimal(str(v or 0)) for k,v in ep['pricing'].items()}
    if any(not v.is_finite() or v<0 for v in prices.values()):
        raise ValueError('Invalid prices')
    if not {'prompt','completion'}<=set(prices):
        raise ValueError('Missing base prices')
    # Cached input replaces ordinary prompt billing; use the full prompt rate
    # for every conservatively bounded input token. Reject a cache surcharge.
    if prices.get('input_cache_read',Decimal(0))>prices['prompt']:
        raise ValueError('Cache reads exceed conservative prompt rate')
    if any(v!=0 for k,v in prices.items() if k not in ('prompt','completion','input_cache_read','discount')):
        raise ValueError('Unhandled nonzero charge')
    return ep


base_result = c.result
base_no_other = c.no_other_collection


def no_other_collection():
    base_no_other()
    if any(path.parent!=c.OUT for path in (ROOT/'results').rglob('active.json')):
        raise ValueError('Another inference attempt is unresolved')


def result(trial,data,http):
    if http==200 and isinstance(data,dict) and not data.get('error'):
        expected = trial['expected_provider']
        if data.get('provider')!=expected:
            return dict(status='provider_or_model_mismatch',choice=None,correct=None,strict_format=None)
        # The legacy validator uses DeepInfra as a literal identity check.
        # Check the actual identity first, then adapt a copy for its remaining
        # schema/refusal/cap logic. Never rewrite the saved provider response.
        data = copy.deepcopy(data)
        data['provider']='DeepInfra'
    return base_result(trial,data,http)


def freeze():
    no_other_collection()
    c.check_locks()
    pointer = c.OUT/'preflight_pointer.json'
    state = c.load(pointer)
    folder = Path(state['folder'])
    try:
        if not 0<=c.seconds_since(state['created_at'])<3600:
            raise ValueError('Stale preflight')
        endpoints = {name:endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in ROUTES.items()}
        draft = c.load(c.BASE/'delivery_canary_draft.json')
        trials=[]
        for question in draft['questions']:
            for name,(provider,slug,quant) in ROUTES.items():
                ep=endpoints[name]
                text=('Answer the question. Be concise. Reply with A or B only on the final line.\n\n'
                      +question['stem']+'\n\nA. '+question['options']['A']+'\nB. '+question['options']['B'])
                req=dict(model=p.MODELS[name],messages=[dict(role='user',content=text)],temperature=0,max_tokens=512,
                    provider=dict(order=[slug],only=[slug],allow_fallbacks=False,quantizations=[quant],require_parameters=True,
                        max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
                if ep.get('max_completion_tokens',0)<512 or ep.get('context_length',0)<p.input_bound(req['messages'])+512:
                    raise ValueError('Insufficient endpoint capacity')
                trials.append(dict(sample_id=name+'__'+question['item_id'],model=name,
                    correct_letter=question['correct_letter'],options=question['options'],
                    expected_provider=provider,request=req))
        bound=sum(map(p.trial_bound,trials))
        credits=c.load(folder/'credits.json')['data']
        available=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0<bound<=c.CAP or available<bound:
            raise ValueError('Invalid budget or insufficient credit')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<bound):
            raise ValueError('Insufficient key allowance')
        paths=[Path(__file__),ROOT/'scripts/56_reliance_canary.py',ROOT/'scripts/50_open_dataset_feasibility.py',
               ROOT/'scripts/54_reliance_calibration.py',ROOT/'docs/ALTERNATE_PROVIDER_PROTOCOL.md',
               c.BASE/'delivery_canary_draft.json']
        p.save(c.OUT/'manifest.json',dict(created_at=p.now(),preflight_started_at=state['created_at'],
            execution_authorization='User: do that, after proposal to test another provider and independently review/calibrate',
            trials=trials,endpoint_snapshot=endpoints,maximum_cost_usd=str(bound),cost_cap_usd=str(c.CAP),
            minimum_start_interval_seconds=20,max_attempts_per_trial=1,automatic_retries=0,
            preflight_passed=True,full_reserve_covered=True,old_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(c.json.dumps(dict(n_planned=len(trials),full_reserve_usd=str(bound),preflight_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir()
        pointer.unlink()


c.no_other_collection=no_other_collection
c.result=result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status'),required=True)
    parser.add_argument('--execute-authorized',action='store_true')
    parser.add_argument('--curl-exit',type=int)
    parser.add_argument('--http-status',type=int)
    args=parser.parse_args()
    if args.stage=='prepare':c.prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Need actual curl exit and HTTP status')
        c.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':c.status}[args.stage]()
