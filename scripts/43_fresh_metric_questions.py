"""Build an unreviewed fresh candidate queue, excluding prior results and plans.

Fresh means no local prior use/design found, not absent from model training.
"""
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/research_directions/metric_validation_questions'
SEED=20261020
ID=re.compile(r'wmdp-\d{4}')


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(text): return ' '.join(text.casefold().split())


def template(text):
    """Conservative heuristic grouping; not semantic deduplication certification."""
    text=normalized(text)
    text=re.sub(r'\bvar_\d+\b','VAR',text)
    text=re.sub(r'\b0x[0-9a-f]+\b','HEX',text)
    text=re.sub(r'\b\d+(?:\.\d+)?\b','NUMBER',text)
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    if OUT.exists(): raise ValueError('Refusing to overwrite fresh queue')
    used=set();provenance={}
    for top in ['results','logs']:
        for p in (ROOT/top).rglob('*'):
            if p.is_file(): used.update(ID.findall(str(p.relative_to(ROOT))))
    for p in (ROOT/'results').rglob('*.csv'):
        try:
            with p.open() as f:
                reader=csv.DictReader(f)
                if 'qid' not in (reader.fieldnames or []): continue
                ids={r['qid'] for r in reader if ID.fullmatch(r.get('qid',''))}
            if ids:
                used.update(ids);provenance[str(p.relative_to(ROOT))]=dict(sha256=sha(p),n_qids=len(ids))
        except (OSError,UnicodeError,csv.Error): continue
    paths=list((ROOT/'results').rglob('*manifest*.json'))+list((ROOT/'data/processed').glob('*design.csv'))
    for p in paths:
        ids=set(ID.findall(p.read_text()))
        if ids:
            used.update(ids);provenance[str(p.relative_to(ROOT))]=dict(sha256=sha(p),n_qids=len(ids))
    source=ROOT/'data/processed/two_choice.jsonl';rawpath=ROOT/'data/raw/wmdp_cyber.jsonl'
    adapted=list(map(json.loads,source.read_text().splitlines()))
    raw={x['qid']:x for x in map(json.loads,rawpath.read_text().splitlines())}
    with (ROOT/'data/processed/task_type.csv').open() as f: labels={r['qid']:r for r in csv.DictReader(f)}
    used_text={normalized(x['question']) for x in adapted if x['qid'] in used}
    pilot=ROOT/'results/research_directions/ambiguity_review/revised_candidates/accepted_items.json'
    for x in json.loads(pilot.read_text()):
        used_text.update([normalized(x['question']),normalized(x['original_question'])])
    ranked=sorted(adapted,key=lambda x:hashlib.sha256(f'{SEED}:{x["qid"]}'.encode()).hexdigest())
    queue=[];excluded=Counter();seen=set()
    for x in ranked:
        text=normalized(x['question'])
        if x['qid'] in used: excluded['prior_id']+=1;continue
        if text in used_text: excluded['prior_question_text']+=1;continue
        if x['flag_option_ref']: excluded['option_reference_flag']+=1;continue
        if text in seen: excluded['duplicate_question_text']+=1;continue
        seen.add(text)
        queue.append(x)
    # Round-robin through task type and within-type length thirds. This supplies
    # structural diversity, not measured model difficulty or randomized strata.
    groups=defaultdict(list)
    for kind in ['recall','compute']:
        group=sorted([x for x in queue if labels[x['qid']]['task_type']==kind],key=lambda x:len(x['question']))
        for i,x in enumerate(group):
            band=['short','middle','long'][min(2,3*i//max(1,len(group)))]
            groups[kind,band].append(x)
    for group in groups.values():
        group.sort(key=lambda x:hashlib.sha256(f'queue:{SEED}:{x["qid"]}'.encode()).hexdigest())
    ordered=[]
    while any(groups.values()):
        for key in sorted(groups):
            if groups[key]: ordered.append((groups[key].pop(),key))
    OUT.mkdir(parents=True)
    masked=[];sidecar=[];templates=[]
    for i,(x,(kind,band)) in enumerate(ordered,1):
        rid=f'F{i:04d}'
        options=sorted([x['correct'],x['distractor']],key=lambda s:hashlib.sha256(f'{SEED}:{rid}:{s}'.encode()).hexdigest())
        masked.append(dict(review_id=rid,question=x['question'],original_options=raw[x['qid']]['choices'],retained_options=options))
        family=template(x['question'])
        sidecar.append(dict(review_id=rid,qid=x['qid'],task_type_heuristic=kind,length_band=band,
            question_bytes=len(x['question'].encode()),template_group_heuristic=family,
            proposed_benchmark_index=options.index(x['correct']),question_review_status='unreviewed',
            key_status='original benchmark proposal; not adjudicated truth'))
        templates.append(dict(review_id=rid,unique_answer='unreviewed',supported_retained_indexes='',
            original_options_assessment='',option_overlap='unreviewed',context_sufficient='unreviewed',
            version_dependency='unreviewed',source_url='',evidence='',reviewer=''))
    (OUT/'masked_review_queue.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in masked))
    (OUT/'selection_and_proposed_keys.json').write_text(json.dumps(sidecar,indent=2)+'\n')
    with (OUT/'review_template.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(templates[0]));w.writeheader();w.writerows(templates)
    meta=dict(created_at=datetime.now(timezone.utc).isoformat(),seed=SEED,n_candidates=len(masked),
        prior_ids_excluded=len(used),exclusions=dict(excluded),
        task_types=dict(Counter(x['task_type_heuristic'] for x in sidecar)),
        template_groups_heuristic=len({x['template_group_heuristic'] for x in sidecar}),
        independent_review_complete=False,collection_ready=False,
        meaning_of_fresh='No known local prior response or planned-use ID, no normalized prior original/revised pilot question text; not a training-contamination claim.',
        limitations=['Task and length strata are heuristics, not measured difficulty.',
                    'Benchmark keys remain proposals pending primary-source review.',
                    'Template grouping is heuristic; review semantic duplicates/families before freezing independent units.',
                    'Same cybersecurity dataset; no across-domain generalization claim.'],
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in [source,rawpath,ROOT/'data/processed/task_type.csv',pilot,Path(__file__)]},
        prior_use_sources=provenance,prior_ids=sorted(used),
        masked_queue_sha256=sha(OUT/'masked_review_queue.jsonl'))
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({k:meta[k] for k in ['n_candidates','prior_ids_excluded','task_types','template_groups_heuristic','independent_review_complete','collection_ready']},indent=2))


if __name__=='__main__':main()
