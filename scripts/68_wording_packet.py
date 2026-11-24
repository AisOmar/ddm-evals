"""Create the wording pilot's masked packet and fixed design without model calls."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/research_directions/wording_pilot_20261022'
SOURCE = ROOT/'docs/WORDING_AND_TRICK_QUESTION_PROPOSAL.md'
ANSWERS = ['1 credit', '4 km/h', '9/17', 'Yes', 'Friday', '6', '11', '96 credits']
VERSIONS = ('plain', 'neutral', 'trap')


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    if (BASE/'packet.json').exists():
        raise ValueError('Already built; never overwrite')
    source = SOURCE.read_text()
    sections = re.findall(r'\*\*(W\d{2}) — ([^\n]+)\*\*\n\n(.*?)(?=\n\*\*W\d|\nThese examples)', source, re.S)
    assert len(sections) == 8
    rows = []
    revisions = []
    for index, (problem, family, text) in enumerate(sections):
        fields = dict(re.findall(r'^- (Plain|Neutral|Candidate trap|Options): (.*?)(?=\n- |\Z)', text.strip(), re.S | re.M))
        options = [' '.join(x.split()).rstrip('.') for x in fields['Options'].split(';')]
        assert len(options) == 2 and options[0] == ANSWERS[index]
        for label, version in zip(('Plain', 'Neutral', 'Candidate trap'), VERSIONS):
            stem = ' '.join(fields[label].split())
            if problem == 'W03' and version == 'neutral':
                before = stem
                stem = ('A batch contains 100 devices, of which 20 are infected. The flagged group contains '
                        '18 infected and 16 uninfected devices. One flagged device is sampled uniformly '
                        'at random. What is its probability of being infected?')
                revisions.append(dict(problem_id=problem, version=version, before=before, after=stem,
                    reason='Repair the already-disclosed awkward probability wording before first masked review. No model outcomes used.'))
            rows.append(dict(problem_id=problem, family=family, version=version, cohort='pilot',
                             stem=stem, answer=options[0], distractor=options[1]))
    # Disjoint representative probes: one new problem per reasoning family.
    probes = [
        ('R01', 'difference', 'trap', 'An adult ticket and a child ticket cost 17 credits in total. The adult ticket costs 13 credits more than the child ticket. How much does the child ticket cost?', '2 credits', '4 credits'),
        ('R02', 'average_speed', 'neutral', 'On a nonstop 36 km ride, the first 18 km are covered at 9 km/h and the remaining 18 km at 6 km/h. What is total distance divided by total time?', '7.2 km/h', '7.5 km/h'),
        ('R03', 'conditioning', 'trap', 'A scanner detects 12 of the 16 infected devices in a batch of 80. It also flags 18 uninfected devices. If one flagged device is chosen uniformly at random, what is the probability it is infected?', '2/5', '3/4'),
        ('R04', 'implication', 'plain', 'Every insulated pipe is dry. No dry pipe is wet. At least one insulated pipe exists. Which statement must be true, using only these premises?', 'Some insulated pipe is not wet.', 'Some wet pipe is not insulated.'),
        ('R05', 'relative_time', 'trap', 'The day before yesterday was two days after Tuesday. What weekday will tomorrow be?', 'Sunday', 'Monday'),
        ('R06', 'ratio_difference', 'plain', 'Nora has three times as many tokens as Ben and has 10 more tokens than Ben. How many tokens does Ben have?', '5', '10/3'),
        ('R07', 'intervention', 'neutral', 'Initially U=4, X=U+3, and Y=3*X+U. Override only the X equation with X=2, keep U fixed, and compute the resulting Y.', '10', '5'),
        ('R08', 'successive_percentages', 'plain', 'A price starts at 80 credits, falls by 25%, and then rises by 25% of its reduced value. What is the final price?', '75 credits', '80 credits'),
    ]
    for problem, family, version, stem, good, bad in probes:
        rows.append(dict(problem_id=problem, family=family, version=version, cohort='resource',
                         stem=stem, answer=good, distractor=bad))
    rng = random.Random(20261022068)
    initial = list('AAAABBBB')
    rng.shuffle(initial)
    assignments = dict(zip([s[0] for s in sections], initial))
    resource_letters = list('AAAABBBB')
    rng.shuffle(resource_letters)
    assignments.update({p[0]:letter for p, letter in zip(probes, resource_letters)})
    for row in rows:
        row['initial_letter'] = assignments[row['problem_id']]
        row['options'] = {l:row['answer'] if l == row['initial_letter'] else row['distractor'] for l in 'AB'}
    rng.shuffle(rows)
    for n, row in enumerate(rows, 1):
        row['review_id'] = f'M{n:03}'
    masked = [{k:r[k] for k in ('review_id', 'stem', 'options')} for r in rows]
    # Verify all exact author answers with compact, transparent arithmetic.
    assert Fraction(11-9, 2) == 1
    assert Fraction(24)/(Fraction(12,6)+Fraction(12,3)) == 4
    assert Fraction(18,18+16) == Fraction(9,17)
    assert (3+1) % 7 == 4 and Fraction(6,2-1) == 6
    assert 2*4+3 == 11 and 100*Fraction(4,5)*Fraction(6,5) == 96
    assert Fraction(17-13,2) == 2 and Fraction(36)/5 == Fraction(36,5)
    assert Fraction(12,12+18) == Fraction(2,5)
    assert (1+4+1) % 7 == 6 and Fraction(10,3-1) == 5
    assert 3*2+4 == 10 and 80*Fraction(3,4)*Fraction(5,4) == 75
    old = json.loads((ROOT/'results/research_directions/short_reasoning_v4_20261022/author/packet_with_solutions.json').read_text())
    assert not {r['stem'] for r in old} & {r['stem'] for r in rows}
    assert len({r['stem'] for r in rows}) == 32
    save(BASE/'packet.json', rows)
    save(BASE/'draft_revisions.json', revisions)
    save(BASE/'review/masked_items.json', masked)
    save(BASE/'review/matched_sets.json', [dict(problem_id=problem,
        versions=[dict(review_id=r['review_id'], version=r['version']) for r in rows if r['problem_id']==problem]) for problem, _, _ in sections])
    save(BASE/'review/review_template.json', dict(reviewer=None, date=None, prior_exposure=None,
        items=[dict(review_id=r['review_id'], chosen_letter=None, derived_answer=None,
                    unique_answer=None, must_fix=None, derivation=None, alternative_assessment=None,
                    wording_concerns=None, expected_steps=None, difficulty=None) for r in masked]))
    save(BASE/'design.json', dict(n_pilot_problems=8, n_pilot_versions=24, n_reviewed_candidates=32,
        n_resource_problems=8, resource_calls=16, pilot_calls=288, repetitions=2,
        advice=['none','correct','wrong'], versions=VERSIONS, max_tokens=2048,
        timeout_seconds=180, min_preparation_interval_seconds=5, temperature=0.7,
        resource_ceiling_usd='0.10', pilot_ceiling_usd='0.90', total_ceiling_usd='1.00',
        order_seed=20261022070, independent_review_complete=False, model_calls_launched=0,
        authorization='User: pksy readu tp run, interpreted in context as okay ready to run the proposed wording pilot.',
        ambiguous_question_arm_included=False, original_study_remains_paused=True))
    paths = [BASE/'packet.json', BASE/'draft_revisions.json', BASE/'design.json',
        BASE/'review/masked_items.json', BASE/'review/matched_sets.json', BASE/'review/review_template.json',
        SOURCE, Path(__file__)]
    save(BASE/'packet_hashes.json', {str(p.relative_to(ROOT)):digest(p) for p in paths})
    print('Prepared 24 pilot versions and eight disjoint resource probes; 32 masked items, no model calls.')


if __name__ == '__main__':
    build()
