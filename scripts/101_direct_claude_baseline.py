"""Separate direct API baseline; fixed cohorts, no automatic inference retries."""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'results/research_directions/selective_reliance_focus_20261024'
OUT=PACKET/'direct_claude_native_20261026'
PROTOCOL=ROOT/'docs/DIRECT_CLAUDE_BASELINE_PROTOCOL.md'
MODELS={'Haiku':'claude-haiku-4-5-20251001','Sonnet':'claude-sonnet-4-5-20250929'}
RATES={'Haiku':(Decimal('1'),Decimal('5')),'Sonnet':(Decimal('3'),Decimal('15'))}
PRIOR=Decimal('0.3217898330000000000037779502')
spec=importlib.util.spec_from_file_location('private_curl',ROOT/'scripts/50_open_dataset_feasibility.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def load(path):return json.loads(path.read_text())
def save(path,value):p.save(path,value)
def reserve(model):
    a,b=RATES[model];return (4000*a+128*b)/1000000

def request(item,model):
    prompt=item['stem']+'\n\nA: '+item['options']['A']+'\nB: '+item['options']['B']+'\n\nSolve the question. Return your selected option as the answer field of the required JSON object.'
    return dict(model=MODELS[model],max_tokens=128,temperature=.7,messages=[dict(role='user',content=prompt)],
        output_config=dict(format=dict(type='json_schema',schema=dict(type='object',properties={'answer':{'type':'string','enum':['A','B']}},required=['answer'],additionalProperties=False))))

def call(body,path,count=False):
    """Persist body before dispatch; private credential config always removed."""
    if path.with_suffix('.transport.json').exists():
        meta=load(path.with_suffix('.transport.json'))
        if meta['curl_exit'] or meta['http_status']!=200:raise RuntimeError('Recorded transport failure; no automatic retry')
        assert load(path.with_suffix('.request.json'))==body
        return load(path.with_suffix('.response.json'))
    if path.with_suffix('.request.json').exists():raise RuntimeError('Unfinalized dispatch; do not retry')
    save(path.with_suffix('.request.json'),body)
    config=p.private_config([dict(url='https://api.anthropic.com/v1/messages'+('/count_tokens' if count else ''),
        header=['x-api-key: '+dotenv_values(ROOT/'.env')['ANTHROPIC_API_KEY'],'anthropic-version: 2023-06-01','content-type: application/json'],
        data_binary='@'+str(path.with_suffix('.request.json')),output=path.with_suffix('.response.json'),
        dump_header=path.with_suffix('.headers.txt'),write_out='%{http_code}',max_time=120)])
    cfg=Path(config);cfg.write_text(cfg.read_text().replace('\nhttp1.1\n','\nhttp2\n'))
    save(OUT/'pending.json',dict(path=str(path),config=config))
    print(json.dumps(dict(curl_config=config)),flush=True)
    raise SystemExit(0)

def finish(curl_exit,http_status):
    pending=load(OUT/'pending.json');path=Path(pending['path'])
    save(path.with_suffix('.transport.json'),dict(curl_exit=curl_exit,http_status=http_status,finished_at=p.now()))
    Path(pending['config']).unlink(missing_ok=True);(OUT/'pending.json').unlink()
    if curl_exit or http_status!=200:raise RuntimeError('Transport/API failure; stopped without retry')

def freeze():
    ready=PACKET/'execution_20261024/adjudication/review_readiness.json'
    assert load(ready)['review_gate_passed']
    items=load(PACKET/'author/packet_with_solutions.json');trials=[]
    for phase,split,repeats in [('qualification','resource',1),('calibration','calibration',2)]:
        for item in sorted((x for x in items if x['split']==split),key=lambda x:x['item_id']):
            for model in MODELS:
                req=request(item,model)
                countpath=OUT/'counts'/(item['item_id']+'_'+model)
                if countpath.with_suffix('.response.json').exists():
                    assert load(countpath.with_suffix('.request.json'))=={k:v for k,v in req.items() if k not in ('max_tokens','temperature')}
                    count=load(countpath.with_suffix('.response.json'))
                else:count=call({k:v for k,v in req.items() if k not in ('max_tokens','temperature')},countpath,True)
                assert 0<count['input_tokens']<=3000
                for rep in range(repeats):
                    trials.append(dict(id=f'{phase}_{item["item_id"]}_{model}_{rep}',phase=phase,item_id=item['item_id'],family=item['family'],model=model,repeat=rep,correct_letter=item['correct_letter'],request=req,counted_input_tokens=count['input_tokens'],reservation_usd=str(reserve(model))))
    total=sum((Decimal(t['reservation_usd']) for t in trials),Decimal(0))
    assert len(trials)==60 and PRIOR+total<1
    paths=[Path(__file__),PROTOCOL,ready,PACKET/'author/packet_with_solutions.json']
    save(OUT/'manifest.json',dict(created_at=p.now(),trials=trials,prior_cost_upper_usd=str(PRIOR),full_reservation_usd=str(total),input_hashes={str(x.relative_to(ROOT)):p.sha(x) for x in paths},rates_per_million={k:list(map(str,v)) for k,v in RATES.items()}))
    print(json.dumps(dict(frozen=True,slots=60,reservation_usd=str(total),cumulative_bound_usd=str(PRIOR+total))),flush=True)

def outcome(body,model,key):
    if body.get('model')!=MODELS[model] or body.get('type')!='message':raise ValueError('Response identity mismatch')
    usage=body['usage']
    if any(usage.get(k,0) for k in ('cache_creation_input_tokens','cache_read_input_tokens')) or usage.get('server_tool_use'):raise ValueError('Unexpected billed features')
    inp,out=usage['input_tokens'],usage['output_tokens']
    if type(inp)!=int or type(out)!=int or not 0<=inp<=4000 or not 0<=out<=128:raise ValueError('Usage outside reservation')
    a,b=RATES[model];cost=(inp*a+out*b)/1000000
    status,answer='behavioral_nonanswer',None
    if body.get('stop_reason')=='end_turn':
        blocks=body.get('content',[])
        if len(blocks)==1 and blocks[0].get('type')=='text':
            try:
                obj=json.loads(blocks[0]['text'])
                if type(obj)==dict and set(obj)=={'answer'} and obj['answer'] in ('A','B'):status,answer='answered',obj['answer']
            except (ValueError,TypeError):pass
    return dict(status=status,answer=answer,correct=(answer==key if answer else None),cost_usd=str(cost),input_tokens=inp,output_tokens=out,stop_reason=body.get('stop_reason'))

def run(phase):
    m=load(OUT/'manifest.json')
    assert all(p.sha(ROOT/k)==v for k,v in m['input_hashes'].items())
    if phase=='calibration':
        quals=[load(OUT/'finished'/(t['id']+'.json')) for t in m['trials'] if t['phase']=='qualification']
        assert len(quals)==12 and all(x['status']=='answered' for x in quals)
    for trial in (t for t in m['trials'] if t['phase']==phase):
        dest=OUT/'finished'/(trial['id']+'.json');raw=OUT/'raw'/trial['id']
        if dest.exists():continue
        body=call(trial['request'],raw)
        result=outcome(body,trial['model'],trial['correct_letter'])
        result.update(id=trial['id'],response_sha256=p.sha(raw.with_suffix('.response.json')),request_sha256=p.sha(raw.with_suffix('.request.json')))
        save(dest,result)
        print(json.dumps(dict(id=trial['id'],status=result['status'],cost_usd=result['cost_usd'])),flush=True)
        if phase=='qualification' and result['status']!='answered':raise RuntimeError('Qualification delivery failure')

def analyze():
    m=load(OUT/'manifest.json');rows=[]
    for trial in m['trials']:
        result=load(OUT/'finished'/(trial['id']+'.json'))
        raw=OUT/'raw'/trial['id']
        assert p.sha(raw.with_suffix('.response.json'))==result['response_sha256']
        assert p.sha(raw.with_suffix('.request.json'))==result['request_sha256']
        rows.append((trial,result))
    report=dict(created_at=p.now(),complete_calibration_slots=48,models=[],advice_calls=0,old_observations_pooled=False,original_study_remains_paused=True)
    for model in MODELS:
        group=[(t,r) for t,r in rows if t['phase']=='calibration' and t['model']==model]
        n=len(group);recognized=sum(r['status']=='answered' for t,r in group);correct=sum(r['correct'] is True for t,r in group);unknown=n-recognized;acc=correct/recognized if recognized else None
        report['models'].append(dict(model=model,planned=n,recognized=recognized,correct=correct,factual_errors=recognized-correct,unknown=unknown,accuracy=acc,correct_yield=correct/n,factual_bounds=[correct/n,(correct+unknown)/n],difficulty_supported=acc is not None and .55<=acc<=.90 and correct<recognized and unknown/n<=.05,item_results=[dict(item_id=t['item_id'],family=t['family'],repeat=t['repeat'],**r) for t,r in group]))
    report['advice_development_supported']=all(x['difficulty_supported'] for x in report['models'])
    report['new_usage_based_cost_usd']=str(sum((Decimal(r['cost_usd']) for t,r in rows),Decimal(0)))
    report['cumulative_cost_upper_usd']=str(PRIOR+Decimal(report['new_usage_based_cost_usd']))
    save(OUT/'analysis.json',report)
    print(json.dumps({k:([{a:b for a,b in x.items() if a!='item_results'} for x in v] if k=='models' else v) for k,v in report.items()},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['freeze','qualification','calibration','analyze','finish']);parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int);args=parser.parse_args()
    if args.stage=='finish':
        assert args.curl_exit is not None and args.http_status is not None
        finish(args.curl_exit,args.http_status)
    elif args.stage=='freeze':freeze()
    elif args.stage=='analyze':analyze()
    else:run(args.stage)
