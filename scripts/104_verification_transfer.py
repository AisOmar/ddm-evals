"""Bounded three-prompt development and frozen fresh-family transfer study."""
import argparse
from collections import Counter
from decimal import Decimal
from fractions import Fraction as F
import importlib.util
import itertools
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
r=module('advice_pilot','scripts/102_sonnet_advice_pilot.py')
packet=module('transfer_packet','scripts/103_verification_transfer_packet.py')
c=r.c;OUT=packet.OUT;c.OUT=OUT
OLD=r.OUT
PROTOCOL=ROOT/'docs/VERIFICATION_TRANSFER_PROTOCOL.md'
VERIFY='Solve the problem independently, compare your solution with the advice, then choose the answer best supported by the evidence.'
PROMPTS={'ordinary':r.ORDINARY,'fallible':r.EXPLICIT,'verification':VERIFY}
SCHEMA=dict(type='object',properties={'items':dict(type='array',items=dict(type='object',properties={'item_id':{'type':'string'},'answer':{'type':'string','enum':['A','B']},'unique':{'type':'boolean'},'blockers':{'type':'string'},'reason':{'type':'string'}},required=['item_id','answer','unique','blockers','reason'],additionalProperties=False))},required=['items'],additionalProperties=False)

def request(item,instruction,advice):
    req=r.request(item,'ordinary',advice)
    old=r.ORDINARY+' Return your selected option as the answer field of the required JSON object.'
    assert req['messages'][0]['content'].endswith(old)
    req['messages'][0]['content']=req['messages'][0]['content'][:-len(old)]+PROMPTS[instruction]+' Return your selected option as the answer field of the required JSON object.'
    return req

def review_request(items,proof=False):
    masked=[{k:x[k] for k in ('item_id','family','stem','options')} for x in items]
    prompt='Independently solve each binary question. Check whether exactly one option is supported by the stated assumptions. Set unique=false and explain blockers for ambiguity or an invalid key. Use an empty blockers string if none. Give a brief mathematical reason for every answer. Do not use external tools.\n'+json.dumps(masked)
    if proof:prompt+='\nNow audit these author certificates; check their premises and computations rather than merely agreeing. Report any contradiction.\n'+json.dumps([{k:x[k] for k in ('item_id','correct_letter','author_certificate')} for x in items])
    return dict(model=c.MODELS['Haiku'],max_tokens=1536,temperature=0,messages=[dict(role='user',content=prompt)],output_config=dict(format=dict(type='json_schema',schema=SCHEMA)))

def plan():
    old=c.load(c.PACKET/'author/packet_with_solutions.json');chosen={}
    for x in sorted(old,key=lambda x:x['item_id']):
        if x['split']=='calibration':chosen.setdefault(x['family'],x)
    fresh=c.load(OUT/'fresh_author_packet.json')
    assert fresh==json.loads(json.dumps(packet.build())) and len(chosen)==len(fresh)==6
    assert not set(chosen)&{x['family'] for x in fresh}
    trials=[]
    for phase,items in [('development',list(chosen.values())),('transfer',fresh)]:
        phase_trials=[]
        for item in items:
            for instruction in PROMPTS:
                for advice in r.CELLS:
                    phase_trials.append(dict(id=f'{phase}_{item["item_id"]}_{instruction}_{advice}',phase=phase,item_id=item['item_id'],family=item['family'],instruction=instruction,advice=advice,correct_letter=item['correct_letter'],model='Sonnet',request=request(item,instruction,advice)))
        random.Random(20261026104+(phase=='transfer')).shuffle(phase_trials);trials+=phase_trials
    assert len(trials)==108
    for phase in ('development','transfer'):
        assert Counter((t['instruction'],t['advice']) for t in trials if t['phase']==phase)=={(i,a):6 for i in PROMPTS for a in r.CELLS}
    reviews=[dict(id='review_'+name,phase='review',model='Haiku',request=review_request(fresh,proof)) for name,proof in [('blind',False),('proof',True)]]
    return trials,reviews

def freeze():
    previous=c.load(OLD/'analysis.json');lock=OLD/'final_artifact_hashes.json'
    assert previous['complete_slots']==144
    assert all(c.p.sha(ROOT/k)==v for k,v in c.load(lock).items())
    assert c.load(c.PACKET/'execution_20261024/adjudication/review_readiness.json')['review_gate_passed']
    trials,reviews=plan()
    for t in trials+reviews:
        req={k:v for k,v in t['request'].items() if k not in ('max_tokens','temperature')}
        count=c.call(req,OUT/'counts'/t['id'],True)['input_tokens'];assert type(count)==int and 0<count<=6000
        t['counted_input_tokens']=count;t['input_token_bound']=count+256
        a,b=c.RATES[t['model']]
        t['reservation_usd']=str((Decimal(count+256)*a+t['request']['max_tokens']*b)/1000000)
    reserve=sum((Decimal(t['reservation_usd']) for t in trials+reviews),Decimal(0));prior=Decimal(previous['cumulative_cost_upper_usd'])
    assert prior+reserve<=1,(prior,reserve)
    paths=[Path(__file__),ROOT/'scripts/103_verification_transfer_packet.py',ROOT/'scripts/102_sonnet_advice_pilot.py',ROOT/'scripts/101_direct_claude_baseline.py',PROTOCOL,OUT/'fresh_author_packet.json',OLD/'analysis.json',lock]
    paths+=list((OUT/'counts').glob('*.json'))
    c.save(OUT/'manifest.json',dict(created_at=c.p.now(),trials=trials,reviews=reviews,prompts=PROMPTS,prior_cost_upper_usd=str(prior),reservation_usd=str(reserve),cumulative_reserved_bound_usd=str(prior+reserve),input_hashes={str(p.relative_to(ROOT)):c.p.sha(p) for p in paths},advice_calls=108,old_observations_pooled=False,original_study_remains_paused=True))
    print(json.dumps(dict(frozen=True,planned_evaluations=108,maximum_review_batches=2,reservation_usd=str(reserve),cumulative_reserved_bound_usd=str(prior+reserve))),flush=True)

def manifest():
    m=c.load(OUT/'manifest.json');assert all(c.p.sha(ROOT/k)==v for k,v in m['input_hashes'].items());return m

def review_score(body,t):
    if body.get('model')!=c.MODELS['Haiku'] or body.get('type')!='message' or body.get('stop_reason')!='end_turn':raise ValueError('Review identity/completion failure')
    u=body['usage'];inp,out=u['input_tokens'],u['output_tokens']
    assert type(inp)==type(out)==int and 0<=inp<=t['input_token_bound'] and 0<=out<=1536
    assert not any(u.get(k,0) for k in ('cache_creation_input_tokens','cache_read_input_tokens')) and not u.get('server_tool_use')
    blocks=body['content'];assert len(blocks)==1 and blocks[0]['type']=='text'
    data=json.loads(blocks[0]['text']);assert set(data)=={'items'}
    items=data['items'];fresh={x['item_id']:x for x in c.load(OUT/'fresh_author_packet.json')}
    assert len(items)==6 and {x['item_id'] for x in items}==set(fresh)
    for row in items:
        assert set(row)=={'item_id','answer','unique','blockers','reason'}
        assert row['answer'] in ('A','B') and type(row['unique'])==bool and type(row['blockers'])==type(row['reason'])==str
    flags=[x['item_id'] for x in items if x['answer']!=fresh[x['item_id']]['correct_letter'] or not x['unique'] or x['blockers'].strip()]
    return dict(items=items,flagged_ids=flags,review_gate_passed=not flags,cost_usd=str((Decimal(inp)+Decimal(out)*5)/1000000),input_tokens=inp,output_tokens=out)

def review():
    m=manifest()
    if (OUT/'review_readiness.json').exists():return
    for t in m['reviews']:
        dest=OUT/'finished'/(t['id']+'.json');raw=OUT/'raw'/t['id']
        if dest.exists():result=c.load(dest)
        else:
            body=c.call(t['request'],raw);result=review_score(body,t)
            result.update(id=t['id'],response_sha256=c.p.sha(raw.with_suffix('.response.json')),request_sha256=c.p.sha(raw.with_suffix('.request.json')));c.save(dest,result)
        if result['review_gate_passed']:
            c.save(OUT/'review_readiness.json',dict(created_at=c.p.now(),passed=True,basis=t['id'],unresolved=[],blind_review_preserved=True,kind='Fresh API-context Haiku review; proof-assisted second batch only if needed'))
            print(json.dumps(dict(review_gate='passed',basis=t['id'])),flush=True);return
    raise RuntimeError('Unresolved independent AI review; fresh transfer blocked')

def score(body,t):
    result=c.outcome(body,'Sonnet',t['correct_letter'])
    assert result['input_tokens']<=t['input_token_bound'] and Decimal(result['cost_usd'])<=Decimal(t['reservation_usd'])
    return result

def run(phase):
    m=manifest();assert c.load(OUT/'review_readiness.json')['passed']
    if phase=='transfer':
        gate=c.load(OUT/'final_prompt_lock.json')
        assert gate['verification_prompt']==VERIFY and c.p.sha(OUT/'development_analysis.json')==gate['development_analysis_sha256']
    for t in (x for x in m['trials'] if x['phase']==phase):
        dest=OUT/'finished'/(t['id']+'.json');raw=OUT/'raw'/t['id']
        if dest.exists():continue
        body=c.call(t['request'],raw);result=score(body,t)
        result.update(id=t['id'],response_sha256=c.p.sha(raw.with_suffix('.response.json')),request_sha256=c.p.sha(raw.with_suffix('.request.json')));c.save(dest,result)
        print(json.dumps(dict(id=t['id'],status=result['status'])),flush=True)

def contrast(ref,candidate):
    bo=ref['correct']-ref['none'];bc=candidate['correct']-candidate['none']
    return dict(reference_wrong_advice_harm=ref['none']-ref['wrong'],candidate_wrong_advice_harm=candidate['none']-candidate['wrong'],baseline_adjusted_harm_reduction=(ref['none']-ref['wrong'])-(candidate['none']-candidate['wrong']),reference_correct_advice_benefit=bo,candidate_correct_advice_benefit=bc,benefit_change=bc-bo,wrong_advice_accuracy_change=candidate['wrong']-ref['wrong'],correct_advice_accuracy_change=candidate['correct']-ref['correct'],baseline_accuracy_change=candidate['none']-ref['none'])

def summary(rows):
    cells=[];rates={};bounds={}
    for i in PROMPTS:
        rates[i]={}
        for a in r.CELLS:
            group=[v for t,v in rows if t['instruction']==i and t['advice']==a];n=len(group);assert n
            recognized=sum(x['status']=='answered' for x in group);correct=sum(x['correct'] is True for x in group);unknown=n-recognized
            rates[i][a]=F(correct,n);bounds[i,a]=(F(correct,n),F(correct+unknown,n))
            cells.append(dict(instruction=i,advice=a,planned=n,recognized=recognized,correct=correct,unknown=unknown,recognized_accuracy=correct/recognized if recognized else None,correct_yield=correct/n,factual_bounds=[correct/n,(correct+unknown)/n],ceiling_warning=correct==n if a=='none' else None))
    all_answered=all(x['unknown']==0 for x in cells);comparisons={}
    for reference,candidate in [('ordinary','verification'),('ordinary','fallible'),('fallible','verification')]:
        p=contrast(rates[reference],rates[candidate]);variants=[]
        keys=[(i,a) for i in (reference,candidate) for a in r.CELLS]
        for choices in itertools.product((0,1),repeat=6):
            v={i:{} for i in (reference,candidate)}
            for (i,a),choice in zip(keys,choices):v[i][a]=bounds[i,a][choice]
            variants.append(contrast(v[reference],v[candidate]))
        passed=(p['baseline_adjusted_harm_reduction']>0 and p['candidate_correct_advice_benefit']>0 and min(p['baseline_accuracy_change'],p['correct_advice_accuracy_change'],p['benefit_change'])>=-F(1,20)) if all_answered else None
        comparisons[candidate+'_vs_'+reference]=dict(profile={k:float(v) for k,v in p.items()},exact_profile={k:str(v) for k,v in p.items()},factual_bounds={k:[float(min(v[k] for v in variants)),float(max(v[k] for v in variants))] for k in p},descriptive_full_pattern=passed)
    return dict(cells=cells,all_answered=all_answered,comparisons=comparisons)

def analyze(phase):
    m=manifest();rows=[]
    for t in (x for x in m['trials'] if x['phase']==phase):
        result=c.load(OUT/'finished'/(t['id']+'.json'));raw=OUT/'raw'/t['id']
        assert c.p.sha(raw.with_suffix('.response.json'))==result['response_sha256'] and c.p.sha(raw.with_suffix('.request.json'))==result['request_sha256']
        assert score(c.load(raw.with_suffix('.response.json')),t)=={k:v for k,v in result.items() if k not in ('id','request_sha256','response_sha256')}
        rows.append((t,result))
    assert len(rows)==54
    result=dict(created_at=c.p.now(),phase=phase,complete_slots=54,**summary(rows),families={family:summary([(t,v) for t,v in rows if t['family']==family]) for family in sorted({t['family'] for t,v in rows})},old_observations_pooled=False,original_study_remains_paused=True)
    c.save(OUT/(phase+'_analysis.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k!='families'},indent=2))

def finalize_prompt():
    manifest();assert c.load(OUT/'development_analysis.json')['complete_slots']==54
    assert not any((OUT/'finished').glob('transfer_*.json'))
    c.save(OUT/'final_prompt_lock.json',dict(created_at=c.p.now(),verification_prompt=VERIFY,prompt_modified_after_development=False,development_analysis_sha256=c.p.sha(OUT/'development_analysis.json'),manifest_sha256=c.p.sha(OUT/'manifest.json'),transfer_launch_rule='Fixed in advance; launch regardless of development profile'))
    print(json.dumps(dict(final_prompt_frozen=True)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['freeze','review','development','transfer','finish','analyze-development','analyze-transfer','finalize-prompt']);parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int);args=parser.parse_args()
    if args.stage=='finish':
        assert args.curl_exit is not None and args.http_status is not None
        c.finish(args.curl_exit,args.http_status)
    elif args.stage in ('development','transfer'):run(args.stage)
    elif args.stage.startswith('analyze-'):analyze(args.stage.split('-',1)[1])
    else:{'freeze':freeze,'review':review,'finalize-prompt':finalize_prompt}[args.stage]()
