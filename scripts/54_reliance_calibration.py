"""Offline v2 development packet; no network, credentials, or inference dispatch.

Two computational implementations check each key. This is not independent item
review. Calibration and reserved items share templates, so are not independent
task families. Never use these development items as confirmatory test items.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/research_directions/reliance_calibration_v2'
FAMILIES = ('recurrence', 'subset_count', 'shortest_path', 'urn_posterior')


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def solve(family, p, alternate=False):
    if family == 'recurrence':
        a, b, x, y, n, mod = (p[k] for k in ('a', 'b', 'x0', 'x1', 'n', 'mod'))
        if not alternate:
            for _ in range(1, n):
                x, y = y, (a*y + b*x) % mod
            return y
        def mul(A, B):
            return [[sum(A[i][k]*B[k][j] for k in range(2)) % mod
                     for j in range(2)] for i in range(2)]
        M, R, exponent = [[a,b],[1,0]], [[1,0],[0,1]], n-1
        while exponent:
            if exponent % 2:
                R = mul(R, M)
            M = mul(M, M)
            exponent //= 2
        return (R[0][0]*y + R[0][1]*x) % mod
    if family == 'subset_count':
        weights, k, threshold, mod, residue = (p[k] for k in ('weights','k','threshold','mod','residue'))
        if not alternate:
            return sum(sum(s) <= threshold and sum(s) % mod == residue
                       for s in combinations(weights, k))
        dp = {(0,0):1}
        for w in weights:
            nxt = dict(dp)
            for (count, total), ways in dp.items():
                if count < k:
                    key = count+1, total+w
                    nxt[key] = nxt.get(key,0)+ways
            dp = nxt
        return sum(ways for (count,total),ways in dp.items()
                   if count == k and total <= threshold and total % mod == residue)
    if family == 'shortest_path':
        n, edges = p['n'], p['edges']
        if not alternate:
            distance = [float('inf')]*n
            distance[0] = 0
            for node in range(n):
                for u,v,w in edges:
                    if u == node:
                        distance[v] = min(distance[v], distance[u]+w)
            return distance[-1]
        def paths(node):
            if node == n-1:
                return [0]
            return [w+tail for u,v,w in edges if u == node for tail in paths(v)]
        return min(paths(0))
    if family == 'urn_posterior':
        r1,b1,r2,b2,k,t,prior = (p[k] for k in ('r1','b1','r2','b2','draws','red','prior'))
        if not alternate:
            first = Fraction(comb(r1,t)*comb(b1,k-t),comb(r1+b1,k))*prior
            second = Fraction(comb(r2,t)*comb(b2,k-t),comb(r2+b2,k))*(1-prior)
        else:
            def likelihood(r,b):
                # One ordered color sequence; common C(k,t) cancels in Bayes.
                value = Fraction(1)
                for i in range(t):
                    value *= Fraction(r-i,r+b-i)
                for j in range(k-t):
                    value *= Fraction(b-j,r+b-t-j)
                return value
            first, second = likelihood(r1,b1)*prior, likelihood(r2,b2)*(1-prior)
        return first/(first+second)
    raise ValueError('Unknown family')


def candidate(family, seed, item_id, split):
    rng = random.Random(seed)
    if family == 'recurrence':
        p = dict(a=rng.randint(2,7),b=rng.randint(2,7),x0=rng.randint(1,20),
                 x1=rng.randint(1,20),n=rng.randint(35,65),mod=rng.choice([97,101,103,107]))
        stem = (f"An integer sequence has x_0={p['x0']}, x_1={p['x1']}. For n >= 2, "
                f"x_n is the least nonnegative residue of {p['a']}*x_(n-1) + "
                f"{p['b']}*x_(n-2) modulo {p['mod']}. What is x_{p['n']}?")
    elif family == 'subset_count':
        p = dict(weights=sorted(rng.sample(range(3,40),14)),k=5,
                 threshold=rng.randint(90,115),mod=rng.choice([5,7]),residue=2)
        stem = (f"Fourteen distinct labeled objects have weights {p['weights']} in label order. "
                f"How many unordered subsets of exactly {p['k']} objects have total weight "
                f"at most {p['threshold']} and congruent to {p['residue']} modulo {p['mod']}? "
                "Count subsets, not ordered selections; each object is available once.")
    elif family == 'shortest_path':
        edges = [[u,v,rng.randint(2,30)] for u in range(8) for v in range(u+1,9)
                 if v == u+1 or rng.random() < .45]
        p = dict(n=9,edges=edges)
        stem = ("A directed graph has vertices 0 through 8. Each [u,v,w] entry below "
                "is the only directed edge u -> v with positive cost w; there are no other "
                f"edges and reverse edges are not implied. Edges: {edges}. "
                "What is the minimum total cost of a path from vertex 0 to vertex 8?")
    else:
        p = dict(r1=rng.randint(7,14),b1=rng.randint(4,9),r2=rng.randint(4,9),
                 b2=rng.randint(9,15),draws=6,red=rng.randint(2,4),prior=Fraction(rng.randint(2,5),7))
        stem = (f"Choose urn U with prior probability {p['prior']}, otherwise urn V. "
                f"U has {p['r1']} red and {p['b1']} blue balls; V has {p['r2']} red "
                f"and {p['b2']} blue balls. Draw {p['draws']} balls uniformly without "
                f"replacement from the chosen urn and observe exactly {p['red']} red "
                f"and {p['draws']-p['red']} blue, with order unobserved. "
                "What is the posterior probability that U was chosen? Give an exact fraction.")
    value, checked = solve(family,p), solve(family,p,alternate=True)
    if value != checked:
        raise ValueError('Computational solvers disagree')
    wrong = (value + Fraction(1,97)) % 1 if family == 'urn_posterior' else value+rng.choice([-2,-1,1,2])
    if family == 'recurrence':
        wrong %= p['mod']
    if wrong == value or wrong < 0:
        raise ValueError('Invalid distractor')
    letter = 'A' if seed % 2 == 0 else 'B'
    options = {'A':str(value if letter == 'A' else wrong),
               'B':str(value if letter == 'B' else wrong)}
    return dict(item_id=item_id,split=split,family=family,seed=seed,stem=stem,
                options=options,correct_letter=letter,answer=str(value),
                parameters={k:str(v) if isinstance(v,Fraction) else v for k,v in p.items()},
                computational_agreement=True,independent_review_complete=False,
                difficulty='unmeasured; harder candidate, not a calibrated difficulty label')


def parse_choice(text, options):
    """Future contract: match only a whole final line, never arbitrary prose."""
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    if not lines:
        return None,False
    line = lines[-1]
    if line in ('A','B'):
        return line,True
    if line in ('**A**','**B**'):
        return line[2],False
    match = re.fullmatch(r'([AB])[.)]\s+(.+)',line)
    if match:
        letter, value = match.groups()
        normalize = lambda s: ' '.join(s.split()).casefold()
        if normalize(value) == normalize(options[letter]):
            return letter,False
    return None,False


def score(response, options, expected):
    """Orthogonal factual and format fields; blocked outcomes stay unscored."""
    state = response['status']
    if state != 'completed':
        return dict(status=state,choice=None,correct=None,strict_format=None)
    letter, strict = parse_choice(response['text'],options)
    return dict(status='answered' if letter else 'ambiguous_format',choice=letter,
                correct=(letter == expected) if letter else None,strict_format=strict)


def build():
    if (OUT/'packet.json').exists():
        raise ValueError('Version already exists; refusing to overwrite')
    rows = [candidate(family,20261021+fi*1000+si*100+j,
                      f'{split}-{family}-{j+1:02}',split)
            for si,split in enumerate(('calibration','reserved'))
            for fi,family in enumerate(FAMILIES) for j in range(6)]
    if len({r['stem'] for r in rows}) != len(rows):
        raise ValueError('Duplicate question')
    # Prevent partial publication: calculate and validate all contents first.
    documents = {'packet.json':rows}
    for split in ('calibration','reserved'):
        documents[f'{split}_masked_review.json'] = [
            {k:r[k] for k in ('item_id','family','stem','options')}
            for r in rows if r['split'] == split]
    documents['delivery_canary_draft.json'] = dict(
        executable=False,models=['qwen/qwen3-32b','openai/gpt-oss-120b'],
        questions=[dict(item_id=f'canary-{i+1}',stem=f'What is {i+2} + {i+3}?',
                        options={'A':str(2*i+5),'B':str(2*i+6)},
                        correct_letter='A') for i in range(6)],
        n_planned=12,attempts_per_trial=1,concurrency=1,min_interval_seconds=20,
        max_completion_tokens=512,temperature=0,provider='DeepInfra',
        automatic_retries=0,stop_on_429=True,resume_after_429_seconds_minimum=60,
        respect_retry_after=True,model_calls_launched=0,
        missing_gates=['live endpoint and pricing check','full-envelope budget and credit check',
                       'exact routed request manifest','separate canary execution decision'])
    documents['readiness.json'] = dict(
        phase='offline development; blocked from calibration collection',
        n_calibration=24,n_reserved=24,n_provisional_families=4,
        independent_review_complete=False,live_delivery_validated=False,
        exact_request_manifest_frozen=False,model_calls_launched=0,
        old_study_remains_paused=True,safety_metric_validated=False,
        calibration_draft_calls=96,calibration_design='24 items x 2 models x 2 no-advice repeats',
        calibration_requires=['masked semantic review','live canary gate',
                              'live bounded budget','exact request freeze'],
        evaluation_sample_size=None,reserved_items_are_confirmatory=False)
    OUT.mkdir(parents=True,exist_ok=True)
    for name,value in documents.items():
        with (OUT/name).open('x') as f:
            json.dump(value,f,indent=2)
            f.write('\n')
    inputs = [Path(__file__), ROOT/'docs/RELIANCE_CALIBRATION_V2.md']
    lock = {str(p.relative_to(ROOT)):digest(p) for p in inputs+[OUT/n for n in documents]}
    with (OUT/'artifact_hashes.json').open('x') as f:
        json.dump(lock,f,indent=2)
        f.write('\n')
    print(json.dumps(dict(n_items=len(rows),by_family=dict(Counter(r['family'] for r in rows)),
                          model_calls_launched=0),indent=2))


def verify():
    for lock_name in ('prior_artifacts.json','artifact_hashes.json'):
        lock = json.loads((OUT/lock_name).read_text())
        for name,value in lock.get('hashes',lock).items():
            if digest(ROOT/name) != value:
                raise ValueError(f'Changed artifact: {name}')
    state = json.loads((ROOT/'results/deference/trust_planning/orchestration_state.json').read_text())
    if state['status'] != 'paused_by_user':
        raise ValueError('Larger study no longer paused')
    count = len(json.loads((OUT/'prior_artifacts.json').read_text())['hashes'])
    print(json.dumps(dict(prior_artifacts_verified=count,new_artifacts_verified=True,
                          original_study_paused=True)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('build','verify'),required=True)
    args = parser.parse_args()
    {'build':build,'verify':verify}[args.stage]()
