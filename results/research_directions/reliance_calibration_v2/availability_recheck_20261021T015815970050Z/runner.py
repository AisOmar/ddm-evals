import argparse
from datetime import datetime, timezone
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT=Path('/Users/aisuluomar/Downloads/ddm-evals')
spec=importlib.util.spec_from_file_location('canary_recheck',ROOT/'scripts/56_reliance_canary.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
p=c.p
POINTER=Path('/private/tmp/ddm-availability-recheck-pointer.json')

def init():
 c.no_other_collection()
 if POINTER.exists():raise ValueError('A recheck already has unresolved state')
 old=c.load(c.OUT/'finished/gpt-oss__canary-1.json')
 if c.seconds_since(old['finished_at'])<60:raise ValueError('Cooldown has not elapsed')
 # Previous saved headers have no Retry-After. Keep that evidence unchanged.
 headers=(c.OUT/'headers/gpt-oss__canary-1.txt').read_text()
 if 'retry-after:' in headers.lower():raise ValueError('Resolve saved Retry-After before recheck')
 folder=Path(tempfile.mkdtemp(prefix='ddm-recheck-preflight-',dir='/private/tmp'))
 out=c.BASE/('availability_recheck_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 out.mkdir()
 entries=[dict(url='https://openrouter.ai/api/v1/'+route,header='Authorization: Bearer '+p.key(),output=folder/(name+'.json'),max_time=30) for name,route in [('credits','credits'),('allowance','auth/key')]]
 entries.append(dict(url='https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints',output=folder/'endpoint.json',max_time=30))
 config=p.private_config(entries)
 p.save(POINTER,dict(out=str(out),folder=str(folder),config=config,started_at=p.now()))
 p.save(out/'protocol.json',dict(purpose='Single newly authorized availability check; not the twelve-trial delivery gate',authorization='User: can yoi check now',max_attempts=1,automatic_retries=0,cost_cap_usd='.01',model='openai/gpt-oss-120b',provider='DeepInfra',quantization='bf16',completion_cap=512,old_attempts_preserved=True,original_study_remains_paused=True))
 print('curl --parallel --parallel-max 3 --config '+config)

def prepare():
 c.no_other_collection();state=c.load(POINTER);out=Path(state['out']);folder=Path(state['folder'])
 if (out/'attempt.json').exists():raise ValueError('Already attempted; no retries')
 try:
  if not 0<=c.seconds_since(state['started_at'])<3600:raise ValueError('Preflight stale')
  ep=p.endpoint(c.load(folder/'endpoint.json'))
  old=c.manifest();trial=next(t for t in old['trials'] if t['model']=='gpt-oss')
  frozen=old['endpoint_snapshot']['gpt-oss']
  for field in ('provider_name','name','quantization','context_length','max_completion_tokens','pricing'):
   if ep.get(field)!=frozen.get(field):raise ValueError('Endpoint drift: '+field)
  bound=p.trial_bound(trial)
  credits=c.load(folder/'credits.json')['data'];allowance=c.load(folder/'allowance.json')['data']
  balance=Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
  remaining=allowance.get('limit_remaining')
  if not balance.is_finite() or not 0<bound<=Decimal('.01') or balance<bound:raise ValueError('Budget invalid')
  if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining))<bound):raise ValueError('Key allowance insufficient')
  p.save(out/'endpoint.json',ep)
  p.save(out/'manifest.json',dict(created_at=p.now(),trial=trial,maximum_cost_usd=str(bound),preflight_passed=True,previous_manifest_sha256=p.sha(c.OUT/'manifest.json'),protocol_sha256=p.sha(out/'protocol.json'),runner_sha256=p.sha(Path(__file__)),inherited_runner_sha256=p.sha(ROOT/'scripts/56_reliance_canary.py')))
 finally:
  Path(state['config']).unlink(missing_ok=True)
  for path in folder.iterdir():path.unlink()
  folder.rmdir()
 request=out/'request.json';p.save(request,trial['request'])
 p.save(out/'attempt.json',dict(prepared_at=p.now(),request_sha256=p.sha(request),manifest_sha256=p.sha(out/'manifest.json')))
 config=p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',header=['Authorization: Bearer '+p.key(),'Content-Type: application/json'],data_binary='@'+str(request),output=out/'raw.json',dump_header=out/'headers.txt',write_out='%{http_code}',max_time=120,connect_timeout=20)])
 state['config']=config;POINTER.write_text(json.dumps(state))
 print(json.dumps(dict(preflight_passed=True,reserve_usd=str(bound))))
 print('curl --config '+config)

def finish(exitcode,http):
 state=c.load(POINTER);out=Path(state['out']);m=c.load(out/'manifest.json')
 try:
  try:data=c.load(out/'raw.json')
  except (ValueError,OSError):data=None
  score=c.result(m['trial'],data,http) if exitcode==0 else dict(status='uncertain_delivery',correct=None,choice=None,strict_format=None)
  amount=data.get('usage',{}).get('cost') if isinstance(data,dict) and isinstance(data.get('usage'),dict) else None
  charge=None
  try:charge=Decimal(str(amount)) if amount is not None else None
  except Exception:pass
  cost_ok=charge is not None and charge.is_finite() and 0<=charge<=Decimal(m['maximum_cost_usd'])
  error=data.get('error') if isinstance(data,dict) else None
  result=dict(finished_at=p.now(),n_attempted=1,curl_exit=exitcode,http_status=http,outcome=score,recorded_cost_usd=str(charge) if charge is not None else None,missing_cost_metadata=amount is None,cost_valid=cost_ok,single_request_succeeded=score['status']=='answered' and score['correct'] is True and cost_ok,full_delivery_gate_passed=False,provider_error=error,raw_sha256=p.sha(out/'raw.json') if (out/'raw.json').exists() else None,headers_sha256=p.sha(out/'headers.txt') if (out/'headers.txt').exists() else None,old_study_remains_paused=True,calibration_calls_launched=0)
  p.save(out/'result.json',result)
  print(json.dumps(result,indent=2))
  print('Saved: '+str(out/'result.json'))
 finally:
  Path(state['config']).unlink(missing_ok=True);POINTER.unlink()

parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['init','prepare','finish']);parser.add_argument('--exit',type=int);parser.add_argument('--http',type=int);args=parser.parse_args()
if args.stage=='init':init()
elif args.stage=='prepare':prepare()
else:
 if args.exit is None or args.http is None:parser.error('Need actual curl exit and HTTP status')
 finish(args.exit,args.http)
