"""Immutable-request recovery of rejected/unsent trials; never repeats a delivered answer."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bounded_recovery_source',ROOT/'scripts/79_deepinfra_wording_pilot.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
a,b,c,p=q.a,q.b,q.c,q.p
BASE=ROOT/'results/research_directions/wording_bounded_recovery_20261023'
OUT=BASE/'pilot'
PROTOCOL=ROOT/'docs/WORDING_BOUNDED_RECOVERY_AMENDMENT.md'
DELIVERED={'answered','ambiguous_format','censored','refusal','incomplete'}
MAX_ATTEMPTS=4
MAX_RETRIES=20
WALL_SECONDS=7200


def configure():
    q.configure()
    b.OUT=OUT;c.OUT=OUT;b.manifest=manifest;c.manifest=manifest


def timestamp(value):
    return datetime.fromisoformat(value)


def retry_deadline(headers,finished_at,ordinal):
    backoff=(60,120,240)[min(max(ordinal,1),3)-1]
    waits=[];invalid=[]
    for line in headers.splitlines():
        if not line.lower().startswith('retry-after:'):continue
        value=line.split(':',1)[1].strip()
        try:
            if value.isdigit():seconds=int(value)
            else:
                date=parsedate_to_datetime(value)
                if date.tzinfo is None:date=date.replace(tzinfo=timezone.utc)
                seconds=max(0,(date-timestamp(finished_at)).total_seconds())
            waits.append(seconds)
        except (ValueError,TypeError,OverflowError):invalid.append(value)
    delay=max([backoff]+waits)
    return dict(not_before=(timestamp(finished_at)+timedelta(seconds=delay)).isoformat(),
                backoff_seconds=backoff,retry_after_seconds=waits,invalid_retry_after=invalid,effective_delay_seconds=delay)


def policy_for(trial,raw,final,headers,ordinal):
    if final['outcome']['status'] in DELIVERED and final['continue_permitted']:
        return dict(kind='delivered',retry_allowed=False)
    error=raw.get('error') if isinstance(raw,dict) else None
    metadata=error.get('metadata') if isinstance(error,dict) else None
    explicit=(final['curl_exit']==0 and final['http_status']==429 and isinstance(error,dict)
        and error.get('code')==429 and isinstance(metadata,dict)
        and metadata.get('provider_name')==trial['expected_provider'])
    price_ok=final['missing_cost_metadata'] or final['cost_within_reserve']
    if explicit and price_ok and ordinal<MAX_ATTEMPTS:
        return dict(kind='retryable_rejection',retry_allowed=True,
                    **retry_deadline(headers,final['finished_at'],ordinal))
    return dict(kind='stop',retry_allowed=False,reason='attempt_limit' if explicit and ordinal>=MAX_ATTEMPTS else 'nonretryable_operational_failure')


def manifest():
    m=c.load(OUT/'manifest.json')
    for name,expected in m['input_hashes'].items():
        if p.sha(ROOT/name)!=expected:raise ValueError('Frozen recovery input changed: '+name)
    if len(m['trials'])!=288 or len({t['sample_id'] for t in m['trials']})!=288:
        raise ValueError('Logical trial coverage changed')
    return m


def source_deliveries():
    q.gates();q.b.verify_lock(q.BASE/'final_artifact_hashes.json');original=q.w.manifest()
    ledger=[c.load(path) for path in sorted((q.OUT/'attempts').glob('*.json'))]
    if [x['sample_id'] for x in ledger]!=[t['sample_id'] for t in original['trials'][:len(ledger)]]:
        raise ValueError('Original attempt order changed')
    deliveries={};counts={};failures={};paths=[]
    for record,trial in zip(ledger,original['trials']):
        rid=trial['sample_id'];fpath=q.OUT/'finished'/(rid+'.json');final=c.load(fpath)
        if record['sample_id']!=rid or final['manifest_sha256']!=p.sha(q.OUT/'manifest.json'):
            raise ValueError('Original attempt lineage changed')
        for folder,suffix,key in [('requests','.json','request_sha256'),('raw','.json','raw_sha256'),('headers','.txt','headers_sha256')]:
            path=q.OUT/folder/(rid+suffix)
            if p.sha(path)!=final[key]:raise ValueError('Original artifact changed: '+rid)
            paths.append(path)
        if c.load(q.OUT/'requests'/(rid+'.json'))!=trial['request']:raise ValueError('Original request mismatch')
        counts[rid]=1;paths.append(fpath)
        if final['outcome']['status'] in DELIVERED and final['continue_permitted']:
            deliveries[rid]=str(fpath.relative_to(ROOT))
        else:
            raw=c.load(q.OUT/'raw'/(rid+'.json'))
            policy=policy_for(trial,raw,final,(q.OUT/'headers'/(rid+'.txt')).read_text(),1)
            if policy['kind']!='retryable_rejection':raise ValueError('Original failure is not safely retryable')
            failures[rid]=policy
    if len(deliveries)!=125 or len(ledger)!=126 or len(failures)!=1:
        raise ValueError('Expected original 125 deliveries and one explicit rejection')
    return original,deliveries,counts,failures,paths


def freeze():
    a.no_other_collection();pointer=OUT/'preflight_pointer.json';state=c.load(pointer);folder=Path(state['folder'])
    try:
        original,retained,counts,failures,source_paths=source_deliveries()
        if not 0<=c.seconds_since(state['created_at'])<3600:raise ValueError('Stale preflight')
        endpoints={name:a.endpoint(c.load(folder/(name+'.json')),route[0],route[2]) for name,route in q.ROUTES.items()}
        for name,ep in endpoints.items():
            for field in ('provider_name','name','quantization','pricing','context_length','max_completion_tokens'):
                if ep.get(field)!=original['endpoint_snapshot'][name].get(field):raise ValueError('Relevant endpoint drift: '+name+'/'+field)
        trials=original['trials']
        firsts=[t for t in trials if t['sample_id'] not in counts]
        maximum=max(map(p.trial_bound,trials));retry_reserve=MAX_RETRIES*maximum
        reserve=sum(map(p.trial_bound,firsts))+retry_reserve
        old_unknown=sum(p.trial_bound(t) for t in trials if t['sample_id'] in failures)
        earlier=q.prior_recorded_cost()+Decimal(c.load(q.BASE/'delivery_summary.json')['recorded_cost_usd'])
        credit=c.load(folder/'credits.json')['data'];available=Decimal(str(credit['total_credits']))-Decimal(str(credit['total_usage']))
        remaining=c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if retry_reserve>Decimal('.05') or reserve>Decimal('.90') or earlier+old_unknown+reserve>1:
            raise ValueError('Fixed recovery/development reserve exceeds ceilings')
        if not available.is_finite() or available<reserve or (remaining is not None and Decimal(str(remaining))<reserve):
            raise ValueError('Insufficient live credit/key allowance')
        paths=[Path(__file__),PROTOCOL,ROOT/'scripts/83_wording_recovery_analysis.py',ROOT/'scripts/69_wording_analysis.py',
            ROOT/'scripts/79_deepinfra_wording_pilot.py',ROOT/'scripts/70_wording_collect.py',ROOT/'scripts/77_deepinfra_resource_collect.py',
            ROOT/'scripts/63_manageable_collect.py',ROOT/'scripts/60_calibrate_reviewed_packet.py',ROOT/'scripts/58_alternate_provider_canary.py',
            ROOT/'scripts/56_reliance_canary.py',ROOT/'scripts/54_reliance_calibration.py',ROOT/'scripts/50_open_dataset_feasibility.py',
            q.OUT/'manifest.json',q.BASE/'final_artifact_hashes.json',q.BASE/'delivery_summary.json']+source_paths
        p.save(OUT/'manifest.json',dict(created_at=p.now(),phase='pilot',n_planned=288,trials=trials,
            original_manifest_sha256=p.sha(q.OUT/'manifest.json'),retained_deliveries=retained,prior_attempt_counts=counts,
            initial_rejections=failures,endpoint_snapshot=endpoints,preflight_started_at=state['created_at'],
            maximum_cost_usd=str(reserve),retry_reserve_usd=str(retry_reserve),maximum_trial_reserve_usd=str(maximum),
            cost_cap_usd='0.90',earlier_recorded_development_cost_usd=str(earlier),old_unknown_cost_reserve_usd=str(old_unknown),
            max_attempts_per_trial=4,max_new_retries=20,max_new_calls=182,wall_seconds=7200,
            execution_authorization='User: t do thay, in context authorizing bounded rate-limit recovery and continuation.',
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(c.json.dumps(dict(retained=125,unresolved=163,maximum_new_calls=182,
            full_recovery_reserve_usd=str(reserve),retry_reserve_usd=str(retry_reserve),preflight_passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():path.unlink()
        folder.rmdir();pointer.unlink()


def state(m=None,allow_active=False):
    m=manifest() if m is None else m
    completed=dict(m['retained_deliveries']);counts=dict(m['prior_attempt_counts']);waiting=dict(m['initial_rejections'])
    records=[];retried=0;reserved=Decimal(0);stop=None;previous=None
    for index,path in enumerate(sorted((OUT/'attempts').glob('*.json')),1):
        record=c.load(path);rid=record['logical_sample_id'];aid=record['sample_id']
        pending=next((t for t in m['trials'] if t['sample_id'] not in completed),None)
        if record['manifest_sha256']!=p.sha(OUT/'manifest.json') or aid!=f'a{index:04}' or pending is None or rid!=pending['sample_id']:
            raise ValueError('Recovery ledger/order invalid')
        if record['total_attempt_number']!=counts.get(rid,0)+1 or record['is_retry']!=(counts.get(rid,0)>0):
            raise ValueError('Attempt ordinal/retry flag invalid')
        if previous and (timestamp(record['prepared_at'])-timestamp(previous['prepared_at'])).total_seconds()<5:
            raise ValueError('Preparation interval violated')
        if rid in waiting and timestamp(record['prepared_at'])<timestamp(waiting[rid]['not_before']):
            raise ValueError('Retry cooldown violated')
        if stop:raise ValueError('Attempt after terminal stop')
        counts[rid]=record['total_attempt_number'];retried+=record['is_retry']
        reserved+=Decimal(record['reserved_cost_usd'])
        if counts[rid]>4 or retried>20 or reserved>Decimal(m['maximum_cost_usd']):raise ValueError('Recovery limit exceeded')
        req=OUT/'requests'/(aid+'.json')
        if p.sha(req)!=record['request_sha256'] or c.load(req)!=pending['request']:raise ValueError('Frozen request changed')
        fpath=OUT/'finished'/(aid+'.json');ppath=OUT/'policies'/(aid+'.json')
        if not fpath.exists() or not ppath.exists():
            if allow_active and index==len(list((OUT/'attempts').glob('*.json'))):
                records.append(record);return dict(completed=completed,counts=counts,retries=retried,reserved=reserved,records=records,stop='active',waiting=waiting)
            raise ValueError('Unresolved recovery attempt')
        final=c.load(fpath);policy=c.load(ppath)
        for key in ('sample_id','logical_sample_id','manifest_sha256','request_sha256','total_attempt_number','is_retry','prepared_at','reserved_cost_usd'):
            if final.get(key)!=record.get(key):raise ValueError('Finalization differs from reservation')
        for folder,suffix,key in [('raw','.json','raw_sha256'),('headers','.txt','headers_sha256')]:
            target=OUT/folder/(aid+suffix)
            if target.exists():
                if p.sha(target)!=final[key]:raise ValueError('Recovery raw/header changed')
            elif final[key] is not None:raise ValueError('Missing recovery artifact')
        if p.sha(fpath)!=policy['final_sha256']:raise ValueError('Recovery finalization changed')
        try:raw=c.load(OUT/'raw'/(aid+'.json'))
        except (ValueError,OSError):raw={}
        scored=a.result(pending,raw,final['http_status']) if final['curl_exit']==0 else dict(status='uncertain_delivery',correct=None,choice=None,strict_format=None)
        if scored!=final['outcome']:raise ValueError('Saved outcome differs from raw response')
        header=(OUT/'headers'/(aid+'.txt')).read_text() if (OUT/'headers'/(aid+'.txt')).exists() else ''
        expected=policy_for(pending,raw,final,header,counts[rid])
        if {k:v for k,v in policy.items() if k!='final_sha256'}!=expected:raise ValueError('Recovery policy changed')
        if policy['kind']=='delivered':completed[rid]=str(fpath.relative_to(ROOT));waiting.pop(rid,None)
        elif policy['kind']=='retryable_rejection':waiting[rid]=policy
        else:stop=policy.get('reason','operational_failure')
        records.append(record);previous=record
    return dict(completed=completed,counts=counts,retries=retried,reserved=reserved,records=records,stop=stop,waiting=waiting)


def prepare(authorized=False):
    if not authorized:raise ValueError('Explicit execution authorization required')
    a.no_other_collection();m=manifest()
    if (OUT/'active.json').exists():raise ValueError('Unresolved active attempt')
    s=state(m)
    if s['stop']:raise ValueError('Recovery stopped: '+s['stop'])
    if len(s['completed'])==288:print(c.json.dumps(dict(action='complete',completed=288)));return
    if c.seconds_since(m['created_at'])>=WALL_SECONDS:raise ValueError('Recovery wall-time limit reached')
    checked=m['preflight_started_at']
    for path in sorted((OUT/'preflight_refreshes').glob('*.json')):
        refresh=c.load(path)
        if refresh['passed'] and refresh['manifest_sha256']==p.sha(OUT/'manifest.json'):checked=refresh['checked_at']
    if not 0<=c.seconds_since(checked)<3600:raise ValueError('Preflight stale; refresh required')
    trial=next(t for t in m['trials'] if t['sample_id'] not in s['completed']);rid=trial['sample_id']
    total=s['counts'].get(rid,0)+1;retry=total>1
    if total>4 or (retry and s['retries']>=20) or len(s['records'])>=182:
        raise ValueError('Recovery retry/attempt cap reached')
    delay=0
    if rid in s['waiting']:delay=max(delay,-c.seconds_since(s['waiting'][rid]['not_before']))
    if s['records']:delay=max(delay,5-c.seconds_since(s['records'][-1]['prepared_at']))
    if delay>0:
        if c.seconds_since(m['created_at'])+delay>=WALL_SECONDS:raise ValueError('Required cooldown exceeds wall budget')
        print(c.json.dumps(dict(action='wait',wait_seconds=delay,completed=len(s['completed']))));return
    bound=p.trial_bound(trial)
    if s['reserved']+bound>Decimal(m['maximum_cost_usd']):raise ValueError('Recovery reserve exhausted')
    aid=f'a{len(s["records"])+1:04}'
    for folder in ('requests','raw','headers','http'):(OUT/folder).mkdir(parents=True,exist_ok=True)
    req=OUT/'requests'/(aid+'.json');p.save(req,trial['request'])
    record=dict(sample_id=aid,logical_sample_id=rid,total_attempt_number=total,is_retry=retry,prepared_at=p.now(),
        manifest_sha256=p.sha(OUT/'manifest.json'),request_sha256=p.sha(req),reserved_cost_usd=str(bound))
    p.save(OUT/'attempts'/f'{len(s["records"])+1:04}.json',record);p.save(OUT/'active.json',record)
    config=p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+p.key(),'Content-Type: application/json'],data_binary='@'+str(req),
        output=OUT/'raw'/(aid+'.json'),dump_header=OUT/'headers'/(aid+'.txt'),write_out='%{http_code}',max_time=180,connect_timeout=20)])
    p.save(OUT/'private_pointer.json',dict(config=config));print('curl --config '+config)


def finish(exitcode,http):
    m=manifest();active=c.load(OUT/'active.json')
    trial=next(t for t in m['trials'] if t['sample_id']==active['logical_sample_id'])
    transport=dict(trial,sample_id=active['sample_id'])
    original=b.manifest
    try:
        b.manifest=lambda:dict(m,trials=[transport])
        b.finish(exitcode,http)
    finally:b.manifest=original
    aid=active['sample_id'];fpath=OUT/'finished'/(aid+'.json');final=c.load(fpath)
    try:raw=c.load(OUT/'raw'/(aid+'.json'))
    except (OSError,ValueError):raw={}
    header=(OUT/'headers'/(aid+'.txt')).read_text() if (OUT/'headers'/(aid+'.txt')).exists() else ''
    policy=policy_for(trial,raw,final,header,active['total_attempt_number'])
    p.save(OUT/'policies'/(aid+'.json'),dict(policy,final_sha256=p.sha(fpath)))
    print(c.json.dumps(dict(logical_sample_id=trial['sample_id'],recovery_disposition=policy['kind'],accuracy_not_reported=True)))


def status():
    m=manifest();s=state(m,allow_active=True)
    outcomes=[];cost=Decimal(0);missing=0
    for rec in s['records']:
        path=OUT/'finished'/(rec['sample_id']+'.json')
        if path.exists():
            f=c.load(path);outcomes.append(f['outcome']['status']);missing+=f['missing_cost_metadata']
            if f['recorded_cost_usd'] is not None:cost+=Decimal(f['recorded_cost_usd'])
    print(c.json.dumps(dict(logical_completed=len(s['completed']),logical_planned=288,new_attempts=len(s['records']),
        new_retry_attempts=s['retries'],new_outcomes=dict(Counter(outcomes)),stop=s['stop'],recorded_new_cost_usd=str(cost),
        missing_new_cost_metadata=missing,reserved_new_attempts_usd=str(s['reserved']),accuracy_not_reported=True),indent=2))


def audit_complete():
    m=manifest();s=state(m)
    if s['stop'] or len(s['completed'])!=288:raise ValueError('All 288 logical responses required for recovery analysis')
    return m,s


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();configure()
    if args.stage=='prepare':prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Actual curl/HTTP status required')
        finish(args.curl_exit,args.http_status)
    else:{'preflight-config':c.preflight_config,'freeze':freeze,'status':status,
          'refresh-config':b.refresh_config,'refresh':b.refresh}[args.stage]()
