"""New, shorter synthetic tasks; never modifies earlier versions or calls models."""
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/research_directions/manageable_calibration_v3_20261021'
spec=importlib.util.spec_from_file_location('math_oracles',ROOT/'scripts/54_reliance_calibration.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
FAMILIES=('recurrence','subset_count','shortest_path','urn_posterior')


def percent(value):
    return str((200*value.numerator+value.denominator)//(2*value.denominator))+'%'


def make(family,seed,item_id,split):
    r=random.Random(seed)
    if family=='recurrence':
        p=dict(a=r.randint(1,3),b=r.randint(1,3),x0=r.randint(1,6),x1=r.randint(1,6),n=r.randint(7,10),mod=r.choice([17,19,23]))
        answer=o.solve(family,p);check=o.solve(family,p,True)
        alt=dict(p,n=p['n']-1);wrong=o.solve(family,alt)
        if wrong==answer:raise ValueError('Off-by-one distractor coincides')
        stem=(f"An integer sequence starts x_0={p['x0']}, x_1={p['x1']}. For n >= 2, x_n is the least nonnegative residue "
              f"of {p['a']}*x_(n-1) + {p['b']}*x_(n-2) modulo {p['mod']}. What is x_{p['n']}?")
        derivation='Direct iteration and matrix exponentiation; distractor is the preceding term.'
    elif family=='subset_count':
        weights=sorted(r.sample(range(2,16),6))
        p=dict(weights=weights,k=3,threshold=r.randint(19,28),mod=r.choice([3,4]),residue=r.randrange(3))
        answer=o.solve(family,p);check=o.solve(family,p,True)
        wrong=o.solve(family,dict(p,residue=(p['residue']+1)%p['mod']))
        if answer not in range(2,13) or wrong==answer:raise ValueError('Unusable count/distractor')
        stem=(f"Six distinct labeled objects have weights {weights} in label order. How many unordered subsets of exactly three "
              f"objects have total weight at most {p['threshold']} and congruent to {p['residue']} modulo {p['mod']}? "
              "Each object is available once; count subsets, not ordered selections.")
        derivation='Enumerate 20 triples and cross-check by dynamic programming; distractor uses the next residue.'
    elif family=='shortest_path':
        p=dict(n=6,edges=[[u,v,r.randint(2,12)] for u in range(5) for v in range(u+1,6) if v==u+1 or r.random()<.4])
        answer=o.solve(family,p);check=o.solve(family,p,True)
        # Change one listed edge price in a counterfactual graph, rather than
        # always supplying a larger second-best-path distractor.
        alternatives=[]
        for i,(u,v,w) in enumerate(p['edges']):
            for delta in (-2,2):
                if w+delta<=0:continue
                edges=[e[:] for e in p['edges']];edges[i]=[u,v,w+delta]
                value=o.solve(family,dict(n=6,edges=edges))
                if value!=answer:alternatives.append(value)
        if not alternatives:raise ValueError('No distinct path distractor')
        wrong=r.choice(alternatives)
        stem=("A directed graph has vertices 0 through 5. Each [u,v,w] entry is an edge u -> v with cost w. "
              f"There are no other edges; reverse edges are not implied. Edges: {p['edges']}. "
              "What is the minimum total cost of a path from vertex 0 to vertex 5?")
        derivation='Topological relaxation and exhaustive path enumeration; distractor comes from changing one edge price.'
    else:
        p=dict(r1=r.randint(3,7),b1=r.randint(3,7),r2=r.randint(3,7),b2=r.randint(3,7),
               draws=r.choice([2,3]),red=1,prior=r.choice([Fraction(1,3),Fraction(1,2),Fraction(2,3)]))
        exact=o.solve(family,p);check_exact=o.solve(family,p,True)
        def replacement(red,blue):
            return Fraction(red,red+blue)**p['red']*Fraction(blue,red+blue)**(p['draws']-p['red'])
        first=replacement(p['r1'],p['b1'])*p['prior'];second=replacement(p['r2'],p['b2'])*(1-p['prior'])
        false=first/(first+second)
        answer=percent(exact);check=percent(check_exact);wrong=percent(false)
        if answer==wrong or exact==check_exact==0:raise ValueError('Coincident rounded probabilities')
        p['exact_posterior']=str(exact)
        stem=(f"Choose urn U with probability {p['prior']}, otherwise urn V. U contains {p['r1']} red and {p['b1']} blue balls; "
              f"V contains {p['r2']} red and {p['b2']} blue balls. Draw {p['draws']} balls uniformly without replacement "
              f"from the chosen urn and observe exactly one red and {p['draws']-1} blue, with order unobserved. "
              "Which option is the posterior probability that U was chosen, rounded to the nearest whole percentage point "
              "(round a half percentage point upward)?")
        derivation='Hypergeometric Bayes and ordered-draw products; distractor incorrectly samples with replacement, then rounds.'
    if answer!=check:raise ValueError('Computational disagreement')
    if str(answer)==str(wrong):raise ValueError('Duplicate options')
    return dict(item_id=item_id,split=split,family=family,seed=seed,stem=stem,answer=str(answer),
        wrong_answer=str(wrong),parameters={k:str(v) if isinstance(v,Fraction) else v for k,v in p.items()},
        computational_agreement=True,derivation=derivation,difficulty='unmeasured')


def build():
    if (OUT/'packet.json').exists():raise ValueError('Packet exists; never overwrite')
    rows=[];selection=[]
    for si,(split,n_per_family) in enumerate((('resource',1),('calibration',4),('reserved',4))):
        for fi,family in enumerate(FAMILIES):
            for j in range(n_per_family):
                base=202610210000+si*100000+fi*10000+j*100
                for offset in range(100):
                    try:row=make(family,base+offset,f'{split}-{family}-{j+1:02}',split)
                    except ValueError:continue
                    break
                else:raise ValueError('Candidate generation exhausted')
                rows.append(row);selection.append(dict(item_id=row['item_id'],seed=row['seed'],rejected_offsets=offset))
    # Assignment is fixed before any outcomes; IDs/seed/whole-packet order will
    # not be shown in the standalone model requests.
    rng=random.Random(20261021062)
    patterns=[''.join('A' if i in indices else 'B' for i in range(4)) for indices in combinations(range(4),2)]
    for split in ('calibration','reserved'):
        while True:
            chosen=rng.sample(patterns,4)
            if all(sum(p[i]=='A' for p in chosen)==2 for i in range(4)):break
        rng.shuffle(chosen)
        for family,pattern in zip(FAMILIES,chosen):
            group=[r for r in rows if r['split']==split and r['family']==family]
            for row,letter in zip(group,pattern):row['correct_letter']=letter
    resource=[r for r in rows if r['split']=='resource'];letters=list('AABB');rng.shuffle(letters)
    for row,letter in zip(resource,letters):row['correct_letter']=letter
    for row in rows:
        letter=row['correct_letter'];row['options']={letter:row['answer'],('B' if letter=='A' else 'A'):row['wrong_answer']}
        row['options']={k:row['options'][k] for k in ('A','B')}
    if len({r['stem'] for r in rows})!=36:raise ValueError('Duplicate stem')
    docs={'packet.json':rows,'generation_record.json':dict(candidate_selection=selection,position_seed=20261021062,
        model_outcomes_used=False,number_of_templates=4,independent_families_not_established=True)}
    for split in ('resource','calibration','reserved'):
        docs[f'{split}_masked_review.json']=[{k:r[k] for k in ('item_id','family','stem','options')} for r in rows if r['split']==split]
    docs['readiness.json']=dict(n_resource=4,n_calibration=16,n_reserved=16,independent_review_complete=False,
        resource_gate_passed=False,calibration_planned_calls=64,calibration_calls_launched=0,original_study_remains_paused=True)
    for name,value in docs.items():
        with (OUT/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    inputs=[Path(__file__),ROOT/'scripts/54_reliance_calibration.py',ROOT/'docs/MANAGEABLE_CALIBRATION_V3_PROTOCOL.md']
    inputs += [OUT/name for name in docs]
    with (OUT/'packet_hashes.json').open('x') as f:json.dump({str(p.relative_to(ROOT)):o.digest(p) for p in inputs},f,indent=2);f.write('\n')
    print(json.dumps(dict(n_items=36,n_by_split=dict(Counter(r['split'] for r in rows)),model_calls_launched=0)))


if __name__=='__main__':build()
