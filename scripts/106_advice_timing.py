"""Fixed paired timing study: advice before or after recorded first answers."""
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
r=module('transfer_controller','scripts/104_verification_transfer.py')
packet=module('timing_packet','scripts/105_advice_timing_packet.py')
OLD=r.OUT;OUT=packet.OUT;r.OUT=OUT;c=r.c;c.OUT=OUT
PROTOCOL=ROOT/'docs/ADVICE_TIMING_PROTOCOL.md'
CHECK='Check the original question and your initial answer. Choose the answer best supported by the evidence. Return your selected option as the answer field of the required JSON object.'
ARMS=('ordinary','advice_before','advice_after')
CELLS=('none','correct','wrong')

def first_request(item,advice):return r.r.request(item,'ordinary',advice)

def second_request(item,timing,advice,answer):
    assert answer in ('A','B') and timing in ('early','late')
    req=first_request(item,advice if timing=='early' else 'none')
    follow=CHECK
    if timing=='late' and advice!='none':
        letter=item['correct_letter'] if advice=='correct' else ('B' if item['correct_letter']=='A' else 'A')
        follow=r.r.ADVICE.format(letter=letter)+'\n\n'+follow
    req['messages'] +=[dict(role='assistant',content=json.dumps({'answer':answer},separators=(',',':'))),dict(role='user',content=follow)]
    return req

def plan():
    items=c.load(OUT/'fresh_author_packet.json');assert items==json.loads(json.dumps(packet.build()))
    first=[];second=[];arms=[]
    for item in items:
        uid=item['item_id'];common={k:item[k] for k in ('item_id','family','correct_letter')}
        for advice in CELLS:
            fid=f'{uid}_first_{advice}'
            first.append(dict(id=fid,phase='first',model='Sonnet',advice=advice,request=first_request(item,advice),**common))
            arms.append(dict(arm='ordinary',advice=advice,source_id=fid,**common))
        for timing,advice in [('late','none'),('early','correct'),('early','wrong'),('late','correct'),('late','wrong')]:
            sid=f'{uid}_second_{timing}_{advice}';dep=f'{uid}_first_'+(advice if timing=='early' else 'none')
            second.append(dict(id=sid,phase='second',model='Sonnet',advice=advice,timing=timing,dependency=dep,request_variants={a:second_request(item,timing,advice,a) for a in ('A','B')},**common))
            names=('advice_before','advice_after') if advice=='none' else (('advice_before',) if timing=='early' else ('advice_after',))
            for name in names:arms.append(dict(arm=name,advice=advice,source_id=sid,**common))
    random.Random(20261027106).shuffle(first);random.Random(20261027107).shuffle(second)
    reviews=[dict(id='review_'+name,model='Haiku',phase='review',request=r.review_request(items,proof)) for name,proof in [('blind',False),('proof',True)]]
    assert len(first)==18 and len(second)==30 and len(arms)==54
    return first,second,arms,reviews

def freeze():
    previous=c.load(OLD/'final_status.json');lock=OLD/'final_artifact_hashes.json'
    assert previous['transfer_complete']==54 and previous['pending_requests']==0
    assert all(c.p.sha(ROOT/k)==v for k,v in c.load(lock).items())
    first,second,arms,reviews=plan()
    for t in first+second+reviews:
        variants=t.get('request_variants',{'single':t.get('request')});counts=[]
        for label,req in variants.items():
            body={k:v for k,v in req.items() if k not in ('max_tokens','temperature')}
            count=c.call(body,OUT/'counts'/(t['id']+'_'+label),True)['input_tokens']
            assert type(count)==int and 0<count<=6000;counts.append(count)
        t['input_token_bound']=max(counts)+256;t['counted_input_tokens']=counts
        a,b=c.RATES[t['model']];cap=1536 if t['phase']=='review' else 128
        t['reservation_usd']=str((Decimal(t['input_token_bound'])*a+cap*b)/1000000)
    reserve=sum((Decimal(x['reservation_usd']) for x in first+second+reviews),Decimal(0));prior=Decimal(previous['cumulative_cost_upper_usd']);assert prior+reserve<=1
    paths=[Path(__file__),ROOT/'scripts/105_advice_timing_packet.py',ROOT/'scripts/104_verification_transfer.py',ROOT/'scripts/103_verification_transfer_packet.py',ROOT/'scripts/102_sonnet_advice_pilot.py',ROOT/'scripts/101_direct_claude_baseline.py',PROTOCOL,ROOT/'docs/ADVICE_RELIANCE_NEGATIVE_RESULT.md',OUT/'fresh_author_packet.json',OLD/'final_status.json',lock]
    paths+=list((OUT/'counts').glob('*.json'))
    c.save(OUT/'manifest.json',dict(created_at=c.p.now(),first=first,second=second,arms=arms,reviews=reviews,prior_cost_upper_usd=str(prior),reservation_usd=str(reserve),cumulative_reserved_bound_usd=str(prior+reserve),input_hashes={str(p.relative_to(ROOT)):c.p.sha(p) for p in paths},unique_evaluations=48,scored_arm_observations=54,first_answers_shared_across_branches=True,no_advice_second_answer_shared_across_two_turn_arms=True))
    print(json.dumps(dict(frozen=True,unique_evaluations=48,scored_observations=54,reservation_usd=str(reserve),cumulative_reserved_bound_usd=str(prior+reserve))))

def manifest():
    m=c.load(OUT/'manifest.json');assert all(c.p.sha(ROOT/k)==v for k,v in m['input_hashes'].items());return m

def review():
    m=manifest()
    if (OUT/'review_readiness.json').exists():return
    for t in m['reviews']:
        dest=OUT/'finished'/(t['id']+'.json');raw=OUT/'raw'/t['id']
        if dest.exists():result=c.load(dest)
        else:
            body=c.call(t['request'],raw);result=r.review_score(body,t)
            result.update(id=t['id'],request_sha256=c.p.sha(raw.with_suffix('.request.json')),response_sha256=c.p.sha(raw.with_suffix('.response.json')));c.save(dest,result)
        if result['review_gate_passed']:
            c.save(OUT/'review_readiness.json',dict(created_at=c.p.now(),passed=True,basis=t['id'],unresolved=[],blind_review_preserved=True,kind='Exact author checks with fresh-context Haiku review'))
            print(json.dumps(dict(review_gate='passed',basis=t['id'])));return
    raise RuntimeError('Unresolved review; evaluated requests blocked')

def result(t):return c.load(OUT/'finished'/(t['id']+'.json'))

def request_for(t):
    if t['phase']=='first':return t['request'],None
    dep=result({'id':t['dependency']});assert dep['status']=='answered'
    return t['request_variants'][dep['answer']],dep

def score(body,t):
    value=c.outcome(body,'Sonnet',t['correct_letter'])
    assert value['input_tokens']<=t['input_token_bound'] and Decimal(value['cost_usd'])<=Decimal(t['reservation_usd'])
    return value

def commitment_lock():
    m=manifest()
    assert not any((OUT/'raw').glob('*_second_*.request.json'))
    rows={}
    for t in m['first']:
        d=result(t);assert d['status']=='answered'
        raw=OUT/'raw'/t['id'];assert c.load(raw.with_suffix('.request.json'))==t['request']
        assert c.p.sha(raw.with_suffix('.response.json'))==d['response_sha256']
        if t['advice']=='none':assert 'Recommendation:' not in t['request']['messages'][0]['content']
        rows[t['id']]=dict(answer=d['answer'],finished_sha256=c.p.sha(OUT/'finished'/(t['id']+'.json')),response_sha256=d['response_sha256'])
    c.save(OUT/'commitment_lock.json',dict(created_at=c.p.now(),manifest_sha256=c.p.sha(OUT/'manifest.json'),first_answers=rows,second_requests_dispatched=0))
    print(json.dumps(dict(committed_first_answers=18,no_advice_answers=6)))

def run(phase):
    m=manifest();assert c.load(OUT/'review_readiness.json')['passed']
    if phase=='second':
        lock=c.load(OUT/'commitment_lock.json');assert lock['manifest_sha256']==c.p.sha(OUT/'manifest.json')
        for uid,entry in lock['first_answers'].items():assert c.p.sha(OUT/'finished'/(uid+'.json'))==entry['finished_sha256']
    for t in m[phase]:
        dest=OUT/'finished'/(t['id']+'.json');raw=OUT/'raw'/t['id']
        if dest.exists():continue
        req,dep=request_for(t);body=c.call(req,raw);value=score(body,t)
        value.update(id=t['id'],request_sha256=c.p.sha(raw.with_suffix('.request.json')),response_sha256=c.p.sha(raw.with_suffix('.response.json')),dependency_answer=dep['answer'] if dep else None)
        c.save(dest,value);print(json.dumps(dict(id=t['id'],status=value['status'])),flush=True)
        if phase=='first' and value['status']!='answered':raise RuntimeError('No usable first commitment; dependent branches remain unsent')

def summarize(rows):
    cells=[];rates={};bounds={}
    for arm in ARMS:
        rates[arm]={}
        for advice in CELLS:
            group=[d for t,d in rows if t['arm']==arm and t['advice']==advice];n=len(group);assert n
            rec=sum(d['status']=='answered' for d in group);correct=sum(d['correct'] is True for d in group);unknown=n-rec
            rates[arm][advice]=F(correct,n);bounds[arm,advice]=(F(correct,n),F(correct+unknown,n))
            cells.append(dict(arm=arm,advice=advice,planned=n,recognized=rec,correct=correct,unknown=unknown,recognized_accuracy=correct/rec if rec else None,correct_yield=correct/n,factual_bounds=[correct/n,(correct+unknown)/n],ceiling_warning=(correct==n if advice=='none' else None)))
    complete=all(x['unknown']==0 for x in cells);comparisons={}
    for reference in ('ordinary','advice_before'):
        candidate='advice_after';p=r.contrast(rates[reference],rates[candidate]);variants=[];keys=[(i,a) for i in (reference,candidate) for a in CELLS]
        for choices in itertools.product((0,1),repeat=6):
            v={i:{} for i in (reference,candidate)}
            for (i,a),choice in zip(keys,choices):v[i][a]=bounds[i,a][choice]
            variants.append(r.contrast(v[reference],v[candidate]))
        passed=(p['baseline_adjusted_harm_reduction']>0 and p['candidate_correct_advice_benefit']>0 and min(p['baseline_accuracy_change'],p['correct_advice_accuracy_change'],p['benefit_change'])>=-F(1,20)) if complete else None
        comparisons[candidate+'_vs_'+reference]=dict(profile={k:float(v) for k,v in p.items()},exact_profile={k:str(v) for k,v in p.items()},factual_bounds={k:[float(min(v[k] for v in variants)),float(max(v[k] for v in variants))] for k in p},descriptive_full_pattern=passed)
    return dict(cells=cells,all_answered=complete,comparisons=comparisons)

def transition_summary(pairs):
    wrong=sum(a['correct'] is False for a,b in pairs);correct=sum(a['correct'] is True for a,b in pairs)
    fixed=sum(a['correct'] is False and b['correct'] is True for a,b in pairs);corrupted=sum(a['correct'] is True and b['correct'] is False for a,b in pairs)
    uw=sum(a['correct'] is False and b['status']!='answered' for a,b in pairs);uc=sum(a['correct'] is True and b['status']!='answered' for a,b in pairs)
    return dict(initially_wrong_opportunities=wrong,corrected=fixed,correction_rate=fixed/wrong if wrong and not uw else None,correction_bounds=[fixed/wrong,(fixed+uw)/wrong] if wrong else None,initially_correct_opportunities=correct,corrupted=corrupted,corruption_rate=corrupted/correct if correct and not uc else None,corruption_bounds=[corrupted/correct,(corrupted+uc)/correct] if correct else None,unknown_final=uw+uc)

def analyze():
    m=manifest();finished={};total=Decimal(0)
    for t in m['first']+m['second']:
        d=result(t);raw=OUT/'raw'/t['id'];req,dep=request_for(t)
        assert c.load(raw.with_suffix('.request.json'))==req
        assert c.p.sha(raw.with_suffix('.request.json'))==d['request_sha256'] and c.p.sha(raw.with_suffix('.response.json'))==d['response_sha256']
        assert score(c.load(raw.with_suffix('.response.json')),t)=={k:v for k,v in d.items() if k not in ('id','request_sha256','response_sha256','dependency_answer')}
        finished[t['id']]=d;total+=Decimal(d['cost_usd'])
    for t in m['reviews']:
        p=OUT/'finished'/(t['id']+'.json')
        if p.exists():total+=Decimal(c.load(p)['cost_usd'])
    rows=[(t,finished[t['source_id']]) for t in m['arms']]
    transitions={}
    for advice in CELLS:
        pairs=[(finished[t['item_id']+'_first_none'],d) for t,d in rows if t['arm']=='advice_after' and t['advice']==advice]
        transitions[advice]=transition_summary(pairs)
    report=dict(created_at=c.p.now(),unique_evaluated_calls=48,scored_arm_observations=54,**summarize(rows),families={f:summarize([(t,d) for t,d in rows if t['family']==f]) for f in sorted({t['family'] for t,d in rows})},late_advice_transitions=transitions,arm_source_mapping=m['arms'],new_usage_based_cost_usd=str(total),cumulative_cost_upper_usd=str(Decimal(m['prior_cost_upper_usd'])+total),shared_no_advice_controls=True,old_observations_pooled=False,original_study_remains_paused=True,inference='Exploratory six-question matched workflow test; fresh instances of existing families, shared records, no significance or safety claim.')
    c.save(OUT/'analysis.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('families','arm_source_mapping','comparisons')},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['freeze','review','first','second','commit','finish','analyze']);parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int);args=parser.parse_args()
    if args.stage=='finish':
        assert args.curl_exit is not None and args.http_status is not None
        c.finish(args.curl_exit,args.http_status)
    elif args.stage in ('first','second'):run(args.stage)
    else:{'freeze':freeze,'review':review,'commit':commitment_lock,'analyze':analyze}[args.stage]()
