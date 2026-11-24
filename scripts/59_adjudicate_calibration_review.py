"""Compare locked blind judgments and repair only option-position patterns."""
from collections import Counter
from fractions import Fraction
from itertools import combinations
import hashlib
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/research_directions/reliance_calibration_v2'
REVIEW=BASE/'independent_review'
OUT=BASE/'reviewed_calibration'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_review_locks():
    for filename in ('INITIAL_SHA256_LOCK.json','ADDENDUM_SHA256_LOCK.json',
                     'FINAL_AUDIT_SHA256_LOCK.json','CORRECTION_SHA256_LOCK.json'):
        lock=json.loads((REVIEW/filename).read_text())
        for field in ('input_sha256','output_sha256','sha256'):
            for name,expected in lock.get(field,{}).items():
                if sha(Path(name))!=expected:raise ValueError(f'Locked reviewer file changed: {name}')


def positions():
    patterns=[]
    for indices in combinations(range(6),3):
        pattern=''.join('A' if j in indices else 'B' for j in range(6))
        if pattern not in ('ABABAB','BABABA','AAABBB','BBBAAA'):patterns.append(pattern)
    rng=random.Random(20261021059)
    result=[]
    for split in ('calibration','reserved'):
        available=[x for x in patterns if x not in result]
        while True:
            chosen=rng.sample(available,4)
            if sum(p[j]=='A' for p in chosen for j in (0,2,4))==6:break
        result+=chosen
    return result


def adjudicate(rows,judgments):
    keys={r['item_id']:r for r in judgments}
    if len(keys)!=48 or len(rows)!=48 or {r['item_id'] for r in rows}!=set(keys):
        raise ValueError('Review coverage invalid')
    for row in rows:
        review=keys[row['item_id']]
        if not review['unique_answer'] or review['chosen_letter']!=row['correct_letter']:
            raise ValueError('Answer-key or uniqueness disagreement')
        if Fraction(review['derived_numerical_answer'])!=Fraction(row['answer']):
            raise ValueError('Numerical solution disagreement')
    return True


def build():
    if OUT.exists():raise ValueError('Adjudicated packet exists; refusing overwrite')
    check_review_locks()
    source=BASE/'semantic_revision/packet.json'
    rows=json.loads(source.read_text())
    judgments=json.loads((REVIEW/'initial_judgments.json').read_text())
    adjudicate(rows,judgments)
    patterns=positions()
    mapping=[]
    families=('recurrence','subset_count','shortest_path','urn_posterior')
    for si,split in enumerate(('calibration','reserved')):
        for fi,family in enumerate(families):
            group=sorted([r for r in rows if r['split']==split and r['family']==family],key=lambda r:r['item_id'])
            for row,letter in zip(group,patterns[si*4+fi]):
                old=row['correct_letter'];wrong='B' if old=='A' else 'A'
                correct_value,wrong_value=row['options'][old],row['options'][wrong]
                row['options']={letter:correct_value,('B' if letter=='A' else 'A'):wrong_value}
                row['options']={k:row['options'][k] for k in ('A','B')}
                row['correct_letter']=letter
                mapping.append(dict(item_id=row['item_id'],before=old,after=letter))
    documents={'packet.json':rows,'adjudication.json':dict(
        n_independent_numerical_agreements=48,independent_review_type='Fresh-context AI; not human or independent training',
        initial_reviewer_dispositions=dict(Counter(r['disposition'] for r in judgments)),
        final_reviewer_dispositions='All 48 repair because of option-position cue',
        repair='Balanced irregular positions; every family 3 A / 3 B; no alternating or grouped pattern; split-level suffix parity balanced',
        seed=20261021059,position_mapping=mapping,unchanged_stems_and_numerical_alternatives=True,
        design_concerns_preserved=['mostly computation','four shared templates','uneven difficulty','near-neighbour alternatives'],
        author_decision='Retain numerical content for descriptive difficulty calibration only; do not claim broad reasoning or safety coverage',
        review_after_repair_required=True,model_calls_on_packet=0),
        'readiness.json':dict(independent_initial_review_complete=True,n_unique_answer_items=48,
            position_cue_repaired=True,postrepair_masked_validation_complete=False,
            calibration_collection_ready=False,model_calls_on_packet=0,original_study_remains_paused=True)}
    for split in ('calibration','reserved'):
        documents[f'{split}_masked_review.json']=[{k:r[k] for k in ('item_id','family','stem','options')} for r in rows if r['split']==split]
    OUT.mkdir()
    for name,value in documents.items():
        with (OUT/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    paths=[Path(__file__),source]+[REVIEW/name for name in ('INITIAL_SHA256_LOCK.json','FINAL_AUDIT_SHA256_LOCK.json','CORRECTION_SHA256_LOCK.json')]+[OUT/name for name in documents]
    with (OUT/'artifact_hashes.json').open('x') as f:json.dump({str(p.relative_to(ROOT)):sha(p) for p in paths},f,indent=2);f.write('\n')
    print(json.dumps(dict(n_answer_agreements=48,position_patterns=patterns,postrepair_validation_pending=True)))


if __name__=='__main__':build()
