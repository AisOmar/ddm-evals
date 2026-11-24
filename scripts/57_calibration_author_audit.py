"""Unblinded author audit of visible stems; not independent semantic review."""
import ast
from collections import Counter
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/research_directions/reliance_calibration_v2'
SOURCE = BASE/'review_revision'
OUT = BASE/'semantic_revision'
spec = importlib.util.spec_from_file_location('audit_oracles',ROOT/'scripts/54_reliance_calibration.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def visible_parameters(row):
    """Recover problem data from the visible wording, never its parameter sidecar."""
    stem,family = row['stem'],row['family']
    if family == 'recurrence':
        match = re.fullmatch(r'An integer sequence has x_0=(\d+), x_1=(\d+)\. For n >= 2, '
            r'x_n is the least nonnegative residue of (\d+)\*x_\(n-1\) \+ '
            r'(\d+)\*x_\(n-2\) modulo (\d+)\. What is x_(\d+)\?',stem)
        x0,x1,a,b,mod,n = map(int,match.groups())
        return dict(x0=x0,x1=x1,a=a,b=b,mod=mod,n=n)
    if family == 'subset_count':
        match = re.fullmatch(r'Fourteen distinct labeled objects have weights (\[.*\]) in label order\. '
            r'How many unordered subsets of exactly (\d+) objects have total weight '
            r'at most (\d+) and congruent to (\d+) modulo (\d+)\? '
            r'Count subsets, not ordered selections; each object is available once\.',stem)
        weights,k,threshold,residue,mod = match.groups()
        values = ast.literal_eval(weights)
        if len(values) != 14 or len(set(values)) != 14 or any(type(x) is not int or x <= 0 for x in values):
            raise ValueError('Invalid visible weights')
        return dict(weights=values,k=int(k),threshold=int(threshold),residue=int(residue),mod=int(mod))
    if family == 'shortest_path':
        match = re.fullmatch(r'A directed graph has vertices 0 through (\d+)\. Each \[u,v,w\] entry below '
            r'is the only directed edge u -> v with positive cost w; there are no other '
            r'edges and reverse edges are not implied\. Edges: (\[.*\])\. '
            r'What is the minimum total cost of a path from vertex 0 to vertex (\d+)\?',stem)
        last,edges,target = match.groups()
        if last != target:
            raise ValueError('Target mismatch')
        edges = ast.literal_eval(edges)
        if len({(u,v) for u,v,w in edges}) != len(edges) or any(not 0 <= u < v <= int(last) or w <= 0 for u,v,w in edges):
            raise ValueError('Invalid graph assumptions')
        return dict(n=int(last)+1,edges=edges)
    if family == 'urn_posterior':
        match = re.fullmatch(r'Choose urn U with prior probability (\d+/\d+), otherwise urn V\. '
            r'U has (\d+) red and (\d+) blue balls; V has (\d+) red and (\d+) blue balls\. '
            r'Draw (\d+) balls uniformly without replacement from the chosen urn and observe '
            r'exactly (\d+) red and (\d+) blue, with order unobserved\. '
            r'What is the posterior probability that U was chosen\? Give an exact fraction\.',stem)
        prior,r1,b1,r2,b2,draws,red,blue = match.groups()
        params = dict(prior=Fraction(prior),r1=int(r1),b1=int(b1),r2=int(r2),b2=int(b2),draws=int(draws),red=int(red))
        if int(red)+int(blue) != int(draws) or any(int(red) > int(r) for r in (r1,r2)) or any(int(blue) > int(b) for b in (b1,b2)):
            raise ValueError('Impossible observation')
        return params
    raise ValueError('Unknown visible family')


def assess(row):
    try:
        params = visible_parameters(row)
    except (AttributeError,TypeError) as e:
        raise ValueError(f'Cannot parse visible question: {row["item_id"]}') from e
    value = oracle.solve(row['family'],params)
    if value != oracle.solve(row['family'],params,True):
        raise ValueError('Visible-stem solvers disagree')
    matches = [letter for letter,option in row['options'].items() if Fraction(option) == value]
    if len(matches) != 1:
        raise ValueError('Visible options lack one unique numerical key')
    if matches[0] != row['correct_letter'] or Fraction(row['answer']) != value:
        raise ValueError('Visible solution disagrees with author key')
    conflict = row['family'] == 'urn_posterior'
    return dict(item_id=row['item_id'],family=row['family'],
        derived_from_visible_stem=str(value),chosen_letter=matches[0],both_options_checked=True,
        computational_agreement=True,author_key_agreement=True,
        disposition='repair wording' if conflict else 'retain candidate pending independent review',
        issues=['Stem asks for a fraction while the future response contract requests a letter'] if conflict else [],
        expected_burden='moderate path comparison' if row['family']=='shortest_path' else 'potentially substantial arithmetic or enumeration',
        difficulty_empirically_measured=False,independent_review=False)


def build():
    if OUT.exists():
        raise ValueError('Semantic revision exists; refusing overwrite')
    for name,expected in json.loads((SOURCE/'artifact_hashes.json').read_text()).items():
        if oracle.digest(ROOT/name) != expected:
            raise ValueError(f'Changed review input: {name}')
    rows = json.loads((SOURCE/'packet.json').read_text())
    audits = [assess(row) for row in rows]
    revisions = []
    for row in rows:
        if row['family'] == 'urn_posterior':
            before = row['stem']
            row['stem'] = before.replace('What is the posterior probability that U was chosen? Give an exact fraction.',
                                        'Which option gives the exact posterior probability that U was chosen?')
            if before == row['stem']:
                raise ValueError('Expected wording not found')
            revisions.append(dict(item_id=row['item_id'],before=before,after=row['stem']))
    documents = {'packet.json':rows,'author_audit.json':dict(
        reviewer='Same author/context with prior key exposure',independent_review=False,
        method='Parse visible stems, solve twice with existing author oracles, check both alternatives',
        limitation='Checks use existing author solvers; not independently authored mathematics or a masked review',
        n_items=len(rows),dispositions=dict(Counter(r['disposition'] for r in audits)),items=audits),
        'revision_log.json':dict(reason='Remove conflicting fraction-output instruction',repairs=revisions),
        'readiness.json':dict(current_review_packet='semantic_revision',n_calibration=24,n_reserved=24,
            author_visible_stem_checks_passed=48,independent_review_complete=False,
            live_delivery_validated=False,delivery_canary_status='stopped after first gpt-oss upstream 429',
            calibration_calls_launched=0,calibration_authorized=False,original_study_remains_paused=True)}
    for split in ('calibration','reserved'):
        documents[f'{split}_masked_review.json'] = [{k:r[k] for k in ('item_id','family','stem','options')}
            for r in rows if r['split']==split]
    OUT.mkdir()
    for name,value in documents.items():
        with (OUT/name).open('x') as f:
            json.dump(value,f,indent=2)
            f.write('\n')
    paths = [Path(__file__),SOURCE/'artifact_hashes.json']+[OUT/name for name in documents]
    with (OUT/'artifact_hashes.json').open('x') as f:
        json.dump({str(path.relative_to(ROOT)):oracle.digest(path) for path in paths},f,indent=2)
        f.write('\n')
    print(json.dumps(dict(visible_stem_checks=48,wording_repairs=len(revisions),independent_review_complete=False)))


if __name__ == '__main__':
    build()
