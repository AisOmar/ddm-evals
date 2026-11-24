"""Offline item-review packet with benchmark keys and flag status in a sidecar."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/deference/trust_planning'
OUT=ROOT/'results/research_directions/ambiguity_review'
SEED=20261020


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert json.loads((BASE/'orchestration_state.json').read_text())['status']=='paused_by_user'
    assert not (BASE/'active_batch.json').exists()
    if OUT.exists():raise ValueError('Refusing to overwrite selection')
    rawpath=ROOT/'data/raw/wmdp_cyber.jsonl';adaptedpath=ROOT/'data/processed/two_choice.jsonl'
    raw={x['qid']:x for x in map(json.loads,rawpath.read_text().splitlines())}
    adapted={x['qid']:x for x in map(json.loads,adaptedpath.read_text().splitlines())}
    audit=BASE/'exploratory/trace_audit_20261019/annotations_with_scores.csv'
    annotations=pd.read_csv(audit)
    flags=set(annotations.loc[annotations.option_fit_concern,'qid'])
    assert len(flags)==10
    snapshot=BASE/'exploratory/deep_20261019T210911Z/snapshot.csv'
    pool=set(pd.read_csv(snapshot).qid)-flags
    rank=lambda q:hashlib.sha256(f'{SEED}:{q}'.encode()).hexdigest()
    controls=sorted(pool,key=rank)[:10]
    chosen=sorted(flags|set(controls),key=lambda q:hashlib.sha256(f'mask:{SEED}:{q}'.encode()).hexdigest())
    packets=[];keys=[]
    for i,q in enumerate(chosen,1):
        a=adapted[q];r=raw[q];pair=sorted([a['correct'],a['distractor']],key=lambda text:hashlib.sha256(f'{SEED}:{q}:{text}'.encode()).hexdigest())
        rid=f'R{i:02d}'
        packets.append(dict(review_id=rid,question=r['question'],original_options=r['choices'],retained_options=pair))
        keys.append(dict(review_id=rid,qid=q,selection_group='previously_flagged' if q in flags else 'random_comparison',original_benchmark_answer=r['choices'][r['answer_idx']],retained_benchmark_answer=a['correct'],retained_benchmark_index=pair.index(a['correct'])))
    assert len(packets)==20
    OUT.mkdir(parents=True)
    (OUT/'masked_items.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in packets))
    pd.DataFrame(keys).to_csv(OUT/'keys_and_selection.csv',index=False)
    pd.DataFrame([dict(review_id=x['review_id'],unique_answer='unreviewed',option_overlap='unreviewed',context_sufficient='unreviewed',version_dependency='unreviewed',source_url='',evidence='',reviewer='') for x in packets]).to_csv(OUT/'independent_review_template.csv',index=False)
    (OUT/'metadata.json').write_text(json.dumps(dict(seed=SEED,n=20,flagged=10,random_comparisons=10,independent_review_complete=False,masking='No model answers, scores, trace flags, or official keys in masked_items.jsonl. Original question content can be recognized.',selection='10 previous option-fit flags plus 10 deterministic random other paused questions; not a population prevalence sample',inputs={str(p.relative_to(ROOT)):sha(p) for p in [rawpath,adaptedpath,audit,snapshot,ROOT/'docs/THREE_DIRECTION_ANALYSIS_PLAN.md',Path(__file__)]}),indent=2)+'\n')
    print('Prepared 20 masked items and separate key/selection sidecar:',OUT)


if __name__=='__main__':main()
