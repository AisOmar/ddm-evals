"""One prospectively bounded completion of truncated quality-review output."""
from decimal import Decimal
import argparse
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('difficulty_controller',ROOT/'scripts/108_separate_difficulty.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
c=r.c;OUT=r.OUT;BASE=OUT/'review_completion';PROTOCOL=ROOT/'docs/SEPARATE_DIFFICULTY_REVIEW_COMPLETION.md'

def truncated_score(body,t):
    assert body.get('model')==c.MODELS['Haiku'] and body.get('type')=='message' and body.get('stop_reason')=='max_tokens'
    u=body['usage'];i,o=u['input_tokens'],u['output_tokens']
    assert type(i)==type(o)==int and 0<=i<=t['input_token_bound'] and o==1024
    assert not any(u.get(k,0) for k in ('cache_creation_input_tokens','cache_read_input_tokens')) and not u.get('server_tool_use')
    cost=(Decimal(i)+5*o)/1000000;assert cost<=Decimal(t['reservation_usd'])
    return dict(review_status='truncated',items=[],flagged_ids=t['item_ids'],review_gate_passed=False,input_tokens=i,output_tokens=o,cost_usd=str(cost),stop_reason='max_tokens',no_partial_judgments_used=True)

def freeze():
    original=r.manifest();selection=c.load(OUT/'selection.json');assert selection['qualified']
    old_t=c.load(OUT/'reserved_review_requests/reserved_review_proof.json');raw=OUT/'raw/reserved_review_proof'
    d=truncated_score(c.load(raw.with_suffix('.response.json')),old_t)
    d.update(id=old_t['id'],request_sha256=c.p.sha(raw.with_suffix('.request.json')),response_sha256=c.p.sha(raw.with_suffix('.response.json')))
    old_dest=OUT/'finished/reserved_review_proof.json'
    if not old_dest.exists():c.save(old_dest,d)
    else:assert c.load(old_dest)==d
    items=[x for x in r.pool() if x['item_id'] in selection['reserved_item_ids']];assert len(items)==12
    req=r.review_request(items,True);req['max_tokens']=2048
    req['messages'][0]['content']='Return complete JSON for all twelve items. A reason may be only a few words.\n'+req['messages'][0]['content']
    uid='reserved_review_completion_1';body={k:v for k,v in req.items() if k not in ('max_tokens','temperature')}
    count=c.call(body,OUT/'counts'/uid,True)['input_tokens'];assert type(count)==int and count>0
    reserve=(Decimal(count+256)+2048*5)/1000000
    full=Decimal(original['cumulative_reserved_bound_usd'])+reserve;assert full<=1
    t=dict(id=uid,model='Haiku',item_ids=selection['reserved_item_ids'],request=req,input_token_bound=count+256,reservation_usd=str(reserve))
    paths=[Path(__file__),PROTOCOL,OUT/'calibration_manifest.json',OUT/'selection.json',OUT/'practice_analysis.json',OUT/'author_pool.json',old_dest,raw.with_suffix('.response.json')]
    c.save(BASE/'manifest.json',dict(created_at=c.p.now(),trial=t,input_hashes={str(p.relative_to(ROOT)):c.p.sha(p) for p in paths},extra_reservation_usd=str(reserve),full_original_plus_extra_reservation_usd=str(full),maximum_additional_inference_calls=1,original_truncation_preserved=True,evaluated_model_test_responses=0))
    print({'completion_frozen':True,'extra_reservation_usd':str(reserve),'full_reserved_bound_usd':str(full)})

def score(body,t):
    before=r.REVIEW_CAP
    try:
        r.REVIEW_CAP=2048
        return r.review_score(body,t)
    finally:r.REVIEW_CAP=before

def run():
    r.manifest();m=c.load(BASE/'manifest.json');assert all(c.p.sha(ROOT/k)==v for k,v in m['input_hashes'].items())
    t=m['trial'];raw=OUT/'raw'/t['id'];dest=OUT/'finished'/(t['id']+'.json')
    if dest.exists():d=c.load(dest)
    else:
        body=c.call(t['request'],raw);d=score(body,t)
        d.update(id=t['id'],request_sha256=c.p.sha(raw.with_suffix('.request.json')),response_sha256=c.p.sha(raw.with_suffix('.response.json')));c.save(dest,d)
    assert d['review_gate_passed'],'Completion review still unresolved; no further calls'
    if not (OUT/'reserved_review_gate.json').exists():c.save(OUT/'reserved_review_gate.json',dict(created_at=c.p.now(),passed=True,basis=t['id'],selection_sha256=c.p.sha(OUT/'selection.json'),items=t['item_ids'],evaluated_model_reserved_calls=0,addendum=str(PROTOCOL.relative_to(ROOT)),completion_manifest_sha256=c.p.sha(BASE/'manifest.json'),truncated_review_preserved=True))
    print({'reserved_review':'passed','basis':t['id']})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['freeze','run']);a=p.parse_args();{'freeze':freeze,'run':run}[a.stage]()
