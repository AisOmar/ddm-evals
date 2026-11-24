"""Calibrate only practice items; deterministically freeze untested items."""
import argparse
from decimal import Decimal
from fractions import Fraction as F
import importlib.util
import itertools
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('timing_controller','scripts/106_advice_timing.py');packet=module('difficulty_packet','scripts/107_separate_difficulty_packet.py')
OLD=r.OUT;OUT=packet.OUT;c=r.c;c.OUT=OUT
PROTOCOL=ROOT/'docs/SEPARATE_DIFFICULTY_PROTOCOL.md'
REVIEW_CAP=1024

def pool():return c.load(OUT/'author_pool.json')

def review_request(items,proof=False):
    body=r.r.review_request(items,proof)
    body['max_tokens']=REVIEW_CAP
    body['messages'][0]['content']='Keep every reason to at most 12 words; return one entry for every supplied item.\n'+body['messages'][0]['content']
    return body

def plans():
    rows=pool();practice=[x for x in rows if x['split']=='practice'];assert len(rows)==72 and len(practice)==36
    trials=[dict(id=x['item_id'],item_id=x['item_id'],level=x['level'],family=x['family'],correct_letter=x['correct_letter'],model='Sonnet',request=c.request(x,'Sonnet')) for x in practice]
    random.Random(20261027108).shuffle(trials)
    reviews=[]
    for level in range(3):
        items=[x for x in practice if x['level']==level]
        for name,proof in [('blind',False),('proof',True)]:reviews.append(dict(id=f'practice_review_L{level}_{name}',level=level,model='Haiku',item_ids=[x['item_id'] for x in items],request=review_request(items,proof)))
    return trials,reviews

def freeze():
    prior=c.load(OLD/'final_status.json');lock=OLD/'final_artifact_hashes.json'
    assert prior['unique_evaluated_calls']==48 and prior['pending_requests']==0
    assert all(c.p.sha(ROOT/k)==v for k,v in c.load(lock).items())
    trials,reviews=plans()
    for t in trials+reviews:
        body={k:v for k,v in t['request'].items() if k not in ('max_tokens','temperature')}
        count=c.call(body,OUT/'counts'/t['id'],True)['input_tokens'];assert type(count)==int and 0<count<=12000
        t['counted_input_tokens']=count;t['input_token_bound']=count+256
        a,b=c.RATES[t['model']]
        t['reservation_usd']=str((Decimal(count+256)*a+t['request']['max_tokens']*b)/1000000)
    reserved_review_each=(Decimal(12000)+REVIEW_CAP*5)/1000000
    reserve=sum((Decimal(t['reservation_usd']) for t in trials+reviews),Decimal(0))+2*reserved_review_each
    previous=Decimal(prior['cumulative_cost_upper_usd']);assert previous+reserve<=1,(previous,reserve)
    paths=[Path(__file__),ROOT/'scripts/107_separate_difficulty_packet.py',ROOT/'scripts/106_advice_timing.py',ROOT/'scripts/104_verification_transfer.py',ROOT/'scripts/103_verification_transfer_packet.py',ROOT/'scripts/102_sonnet_advice_pilot.py',ROOT/'scripts/101_direct_claude_baseline.py',PROTOCOL,OUT/'author_pool.json',OUT/'local_nonuse_check.json',OLD/'final_status.json',lock]
    paths+=list((OUT/'counts').glob('*.json'))
    c.save(OUT/'calibration_manifest.json',dict(created_at=c.p.now(),trials=trials,reviews=reviews,selection_rule='Single level nearest 70%, 55–85% range; otherwise preset family-vector fallback',practice_ids=[x['id'] for x in trials],reserved_ids=[x['item_id'] for x in pool() if x['split']=='reserved'],reserved_review_input_bound=12000,reserved_review_cap=REVIEW_CAP,reserved_review_each_usd=str(reserved_review_each),reservation_usd=str(reserve),prior_cost_upper_usd=str(previous),cumulative_reserved_bound_usd=str(previous+reserve),input_hashes={str(p.relative_to(ROOT)):c.p.sha(p) for p in paths},evaluated_model_reserved_calls=0))
    print(json.dumps(dict(frozen=True,practice_calls=36,reserved_candidates=36,reservation_usd=str(reserve),cumulative_bound_usd=str(previous+reserve))))

def manifest():
    m=c.load(OUT/'calibration_manifest.json');assert all(c.p.sha(ROOT/k)==v for k,v in m['input_hashes'].items());return m

def review_score(body,t):
    assert body.get('model')==c.MODELS['Haiku'] and body.get('type')=='message' and body.get('stop_reason')=='end_turn'
    usage=body['usage'];i,o=usage['input_tokens'],usage['output_tokens']
    assert type(i)==type(o)==int and 0<=i<=t['input_token_bound'] and 0<=o<=REVIEW_CAP
    assert not any(usage.get(k,0) for k in ('cache_creation_input_tokens','cache_read_input_tokens')) and not usage.get('server_tool_use')
    blocks=body['content'];assert len(blocks)==1 and blocks[0]['type']=='text'
    data=json.loads(blocks[0]['text']);assert set(data)=={'items'}
    items=data['items'];expected=set(t['item_ids']);assert len(items)==len(expected) and {x['item_id'] for x in items}==expected
    author={x['item_id']:x for x in pool()};flags=[]
    for x in items:
        assert set(x)=={'item_id','answer','unique','blockers','reason'}
        assert x['answer'] in ('A','B') and type(x['unique'])==bool and type(x['blockers'])==type(x['reason'])==str
        if x['answer']!=author[x['item_id']]['correct_letter'] or not x['unique'] or x['blockers'].strip():flags.append(x['item_id'])
    return dict(items=items,flagged_ids=flags,review_gate_passed=not flags,input_tokens=i,output_tokens=o,cost_usd=str((Decimal(i)+5*o)/1000000))

def finish_review(t):
    dest=OUT/'finished'/(t['id']+'.json');raw=OUT/'raw'/t['id']
    if dest.exists():return c.load(dest)
    body=c.call(t['request'],raw);d=review_score(body,t)
    d.update(id=t['id'],request_sha256=c.p.sha(raw.with_suffix('.request.json')),response_sha256=c.p.sha(raw.with_suffix('.response.json')));c.save(dest,d);return d

def review_practice():
    m=manifest()
    if (OUT/'practice_review_gate.json').exists():return
    passed={}
    for level in range(3):
        for t in (x for x in m['reviews'] if x['level']==level):
            d=finish_review(t)
            if d['review_gate_passed']:passed[str(level)]=t['id'];break
        else:raise RuntimeError('Unresolved practice quality review; no calibration launch')
    c.save(OUT/'practice_review_gate.json',dict(created_at=c.p.now(),passed=True,basis=passed))
    print(json.dumps(dict(practice_review='passed',basis=passed)))

def score(body,t):
    d=c.outcome(body,'Sonnet',t['correct_letter'])
    assert d['input_tokens']<=t['input_token_bound'] and Decimal(d['cost_usd'])<=Decimal(t['reservation_usd'])
    return d

def collect():
    m=manifest();assert c.load(OUT/'practice_review_gate.json')['passed']
    for t in m['trials']:
        dest=OUT/'finished'/(t['id']+'.json');raw=OUT/'raw'/t['id']
        if dest.exists():continue
        assert t['id'] in m['practice_ids'] and t['id'] not in m['reserved_ids']
        body=c.call(t['request'],raw);d=score(body,t)
        d.update(id=t['id'],request_sha256=c.p.sha(raw.with_suffix('.request.json')),response_sha256=c.p.sha(raw.with_suffix('.response.json')));c.save(dest,d)
        print(json.dumps(dict(item_id=t['id'],status=d['status'])),flush=True)

def choose(records):
    def eligible(group):
        return len(group)==12 and all(x['status']=='answered' for x in group) and F(55,100)<=F(sum(x['correct'] is True for x in group),12)<=F(85,100)
    def rank(group,levels):return (abs(F(sum(x['correct'] is True for x in group),12)-F(7,10)),sum(levels),tuple(levels))
    singles=[]
    for level in range(3):
        group=[x for x in records if x['level']==level]
        if eligible(group):singles.append((rank(group,[level]*6),[level]*6,group))
    candidates=singles;mode='single_level'
    if not candidates:
        mode='family_vector_fallback';candidates=[]
        for levels in itertools.product(range(3),repeat=6):
            group=[x for x in records if x['level']==levels[packet.FAMILIES.index(x['family'])]]
            if eligible(group):candidates.append((rank(group,levels),list(levels),group))
    if not candidates:return dict(qualified=False,reason='No complete practice configuration met 55–85% factual accuracy; reserved candidates remain untested')
    _,levels,group=min(candidates,key=lambda x:x[0])
    return dict(qualified=True,mode=mode,levels_by_family=dict(zip(packet.FAMILIES,levels)),practice_correct=sum(x['correct'] is True for x in group),practice_total=12,selected_practice_ids=[x['id'] for x in group],reserved_item_ids=[x['item_id'] for x in pool() if x['split']=='reserved' and x['level']==levels[packet.FAMILIES.index(x['family'])]])

def analyze_practice():
    m=manifest();records=[]
    for t in m['trials']:
        d=c.load(OUT/'finished'/(t['id']+'.json'));raw=OUT/'raw'/t['id']
        assert c.load(raw.with_suffix('.request.json'))==t['request']
        assert c.p.sha(raw.with_suffix('.request.json'))==d['request_sha256'] and c.p.sha(raw.with_suffix('.response.json'))==d['response_sha256']
        assert score(c.load(raw.with_suffix('.response.json')),t)=={k:v for k,v in d.items() if k not in ('id','request_sha256','response_sha256')}
        records.append(dict(**t,**{k:v for k,v in d.items() if k not in t}))
    assert len(records)==36
    profiles=[]
    for level in range(3):
        group=[x for x in records if x['level']==level];n=len(group);recognized=sum(x['status']=='answered' for x in group);correct=sum(x['correct'] is True for x in group);unknown=n-recognized
        profiles.append(dict(level=level,planned=n,recognized=recognized,correct=correct,unknown=unknown,recognized_accuracy=correct/recognized if recognized else None,correct_yield=correct/n,factual_bounds=[correct/n,(correct+unknown)/n],family_correct={f:sum(x['correct'] is True for x in group if x['family']==f) for f in packet.FAMILIES}))
    selection=choose(records)
    c.save(OUT/'practice_analysis.json',dict(created_at=c.p.now(),complete_practice_calls=36,levels=profiles,selection=selection,evaluated_model_reserved_calls=0))
    c.save(OUT/'selection.json',dict(created_at=c.p.now(),**selection,practice_analysis_sha256=c.p.sha(OUT/'practice_analysis.json'),author_pool_sha256=c.p.sha(OUT/'author_pool.json')))
    print(json.dumps(dict(levels=profiles,selection=selection),indent=2))

def review_reserved():
    m=manifest();selection=c.load(OUT/'selection.json');assert selection['qualified']
    if (OUT/'reserved_review_gate.json').exists():return
    assert c.p.sha(OUT/'practice_analysis.json')==selection['practice_analysis_sha256'] and c.p.sha(OUT/'author_pool.json')==selection['author_pool_sha256']
    items=[x for x in pool() if x['item_id'] in selection['reserved_item_ids']];assert len(items)==12
    for name,proof in [('blind',False),('proof',True)]:
        uid='reserved_review_'+name;req=review_request(items,proof);body={k:v for k,v in req.items() if k not in ('max_tokens','temperature')}
        count=c.call(body,OUT/'counts'/uid,True)['input_tokens'];assert count+256<=m['reserved_review_input_bound']
        t=dict(id=uid,model='Haiku',item_ids=[x['item_id'] for x in items],request=req,input_token_bound=m['reserved_review_input_bound'],reservation_usd=m['reserved_review_each_usd'])
        dest=OUT/'reserved_review_requests'/(uid+'.json')
        if not dest.exists():c.save(dest,t)
        else:assert c.load(dest)==t
        d=finish_review(t)
        if d['review_gate_passed']:
            c.save(OUT/'reserved_review_gate.json',dict(created_at=c.p.now(),passed=True,basis=uid,selection_sha256=c.p.sha(OUT/'selection.json'),items=[x['item_id'] for x in items],evaluated_model_reserved_calls=0))
            print(json.dumps(dict(reserved_review='passed',basis=uid)));return
    raise RuntimeError('Unresolved reserved question review; ready-test freeze blocked')

def freeze_test():
    m=manifest();selection=c.load(OUT/'selection.json');gate=c.load(OUT/'reserved_review_gate.json')
    assert selection['qualified'] and gate['passed'] and c.p.sha(OUT/'selection.json')==gate['selection_sha256']
    items=[x for x in pool() if x['item_id'] in selection['reserved_item_ids']];assert len(items)==12
    assert not any(x['item_id'] in m['practice_ids'] for x in items)
    for path in (OUT/'raw').glob('*.request.json'):
        req=c.load(path)
        if req['model']==c.MODELS['Sonnet']:assert path.name.removesuffix('.request.json') in m['practice_ids']
    masked=[{k:x[k] for k in ('item_id','level','family','stem','options')} for x in items]
    c.save(OUT/'frozen_test/questions.json',masked)
    c.save(OUT/'frozen_test/answer_key.json',[{k:x[k] for k in ('item_id','correct_letter','answer','author_certificate')} for x in items])
    text='# Frozen untouched test questions\n\nNo evaluated Sonnet responses collected. Two instances per family.\n\n'
    for x in items:text+=f'## {x["item_id"]} — {x["family"]}\n\n{x["stem"]}\n\nA: {x["options"]["A"]}\nB: {x["options"]["B"]}\n\n'
    with (OUT/'frozen_test/questions.md').open('x') as f:f.write(text)
    paths=[OUT/'calibration_manifest.json',OUT/'author_pool.json',OUT/'selection.json',OUT/'practice_analysis.json',OUT/'reserved_review_gate.json',OUT/'frozen_test/questions.json',OUT/'frozen_test/answer_key.json',OUT/'frozen_test/questions.md']
    c.save(OUT/'frozen_test/manifest.json',dict(created_at=c.p.now(),ready=True,items=12,families=6,practice_items_included=0,evaluated_model_test_responses=0,review_model='Haiku 4.5, fresh API context; may have seen author certificates',selection_mode=selection['mode'],levels_by_family=selection['levels_by_family'],sha256={str(p.relative_to(ROOT)):c.p.sha(p) for p in paths},held_out_difficulty='Unknown until a separately authorized test; no guarantee against ceiling',next_experiment_launched=False))
    print(json.dumps(dict(ready=True,frozen_test_items=12,evaluated_model_test_responses=0)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['freeze','review-practice','collect','analyze','review-reserved','freeze-test','finish']);parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int);a=parser.parse_args()
    if a.stage=='finish':
        assert a.curl_exit is not None and a.http_status is not None
        c.finish(a.curl_exit,a.http_status)
    else:{'freeze':freeze,'review-practice':review_practice,'collect':collect,'analyze':analyze_practice,'review-reserved':review_reserved,'freeze-test':freeze_test}[a.stage]()
