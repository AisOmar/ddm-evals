"""Build an offline, masked development packet. Never calls a model or overwrites files."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'results/research_directions/short_reasoning_v4_20261022'
FAMILIES = ('implication', 'base_rate', 'weighted_rate', 'dependencies',
            'state_updates', 'set_overlap', 'intervention', 'expected_value')
INSTRUCTION = 'Answer the question. Be concise. Reply with A or B only on the final line.'


def fraction(x):
    return str(Fraction(x))


def make(family, i):
    """Five preselected parameterizations per family; no evaluated-model screening."""
    if family == 'implication':
        # Check entailment by a finite truth table as well as a logical derivation.
        names = [('copper', 'round', 'sealed'), ('silver', 'flat', 'marked'),
                 ('green', 'heavy', 'polished'), ('striped', 'small', 'tagged'),
                 ('blue', 'square', 'coated')][i]
        x, y, z = names
        if i % 2 == 0:
            stem = (f'Every {x} token is {y}. No {y} token is {z}. At least one {x} token exists. '
                    f'Which statement must be true? Use only these premises.')
            good, bad = f'Some {x} token is not {z}.', f'Some {z} token is not {x}.'
            # Bits describe existence of each of the eight token types.
            worlds = [w for w in product((False, True), repeat=8)
                      if any(w[t] and t & 4 for t in range(8))
                      and all(not w[t] or (not (t & 4) or t & 2)
                              and not (t & 2 and t & 1) for t in range(8))]
            supported = lambda w: any(w[t] and t & 4 and not t & 1 for t in range(8))
            distractor = lambda w: any(w[t] and t & 1 and not t & 4 for t in range(8))
            rationale = 'An existing first-kind token is second-kind, so it cannot be third-kind. No third-kind existence is implied.'
        else:
            stem = (f'Every {x} token is {y}. Some {y} tokens are {z}. '
                    f'No {x} token is {z}. Which statement must be true? Use only these premises.')
            good, bad = f'Some {y} token is not {x}.', f'No {y} token is {x}.'
            worlds = [w for w in product((False, True), repeat=8)
                      if any(w[t] and t & 2 and t & 1 for t in range(8))
                      and all(not w[t] or (not (t & 4) or t & 2)
                              and not (t & 4 and t & 1) for t in range(8))]
            supported = lambda w: any(w[t] and t & 2 and not t & 4 for t in range(8))
            distractor = lambda w: all(not w[t] or not (t & 2) or not (t & 4) for t in range(8))
            rationale = 'The second-and-third-kind witness cannot be first-kind. Other second-kind tokens can still be first-kind.'
        assert worlds and all(map(supported, worlds)) and not all(map(distractor, worlds))
        check = good
        params = dict(properties=names, n_satisfying_worlds=len(worlds))
        method = 'Entailment and explicit countermodel search over eight possible token types.'
    elif family == 'base_rate':
        n, k, tp, fp = [(100, 10, 8, 18), (200, 40, 30, 20), (150, 30, 24, 12),
                         (120, 20, 15, 25), (180, 60, 45, 30)][i]
        stem = (f'A batch contains {n} parts, exactly {k} defective. A scanner flags {tp} of the defective parts '
                f'and {fp} of the nondefective parts. Choose one flagged part uniformly at random. '
                'What is the probability it is defective?')
        good, bad = fraction(Fraction(tp, tp + fp)), fraction(Fraction(tp, k))
        prior = Fraction(k, n)
        check = fraction((Fraction(tp, k) * prior) /
                         (Fraction(tp, k) * prior + Fraction(fp, n-k) * (1-prior)))
        params = dict(n=n, defective=k, flagged_defective=tp, flagged_nondefective=fp)
        rationale = f'There are {tp + fp} flagged parts, of which {tp} are defective. The alternative divides by all defective parts.'
        method = 'Flagged-population fraction and Bayes formula using exact rational arithmetic.'
    elif family == 'weighted_rate':
        n1, n2, r1, r2 = [(20, 80, 90, 40), (30, 70, 80, 60), (40, 60, 25, 75),
                           (80, 20, 50, 100), (60, 40, 75, 25)][i]
        stem = (f'Team L processed {n1} cases and resolved {r1}% of them. Team M processed {n2} different cases '
                f'and resolved {r2}% of them. Every case belongs to exactly one team. '
                'What percentage of all cases were resolved?')
        answer = Fraction(n1*r1+n2*r2, n1+n2)
        good, bad = fraction(answer)+'%', fraction(Fraction(r1+r2, 2))+'%'
        outcomes = [True] * (n1*r1//100+n2*r2//100) + [False] * (n1*(100-r1)//100+n2*(100-r2)//100)
        assert n1*r1 % 100 == n2*r2 % 100 == 0 and len(outcomes) == n1+n2
        check = fraction(Fraction(100*sum(outcomes), len(outcomes)))+'%'
        params = dict(n1=n1, n2=n2, percent1=r1, percent2=r2)
        rationale = f'Add the resolved counts, then divide by {n1+n2}; do not give the teams equal weight.'
        method = 'Weighted percentage and explicit case-level success accounting.'
    elif family == 'dependencies':
        a, b, c, d = [(3, 5, 4, 2), (4, 3, 5, 2), (2, 6, 3, 4),
                       (5, 4, 2, 3), (3, 7, 6, 2)][i]
        stem = (f'Tasks A, B, C, D take {a}, {b}, {c}, {d} minutes respectively. A and B can start at time 0. '
                'C can start only after A finishes. D can start only after both B and C finish. '
                'There are enough workers to run any ready tasks in parallel, with no setup delays. '
                'What is the earliest time D can finish?')
        good, bad = str(max(b, a+c)+d)+' minutes', str(a+b+c+d)+' minutes'
        durations = dict(A=a, B=b, C=c, D=d)
        parents = dict(A=[], B=[], C=['A'], D=['B', 'C'])
        # Independently simulate completions on integer minute boundaries.
        started, completed = {}, set()
        for t in range(a+b+c+d+1):
            completed.update(k for k, start in started.items() if t >= start+durations[k])
            for task in durations:
                if task not in started and set(parents[task]) <= completed:
                    started[task] = t
            if 'D' in completed:
                check = str(t)+' minutes'
                break
        params = dict(durations=durations, parents=parents)
        rationale = f'C ends at {a+c}; D waits until max({b}, {a+c}), then takes {d} minutes.'
        method = 'Critical-path equation and discrete event simulation.'
    elif family == 'state_updates':
        x, y, inc = [(2, 7, 3), (4, 9, 2), (3, 8, 4), (5, 11, 3), (6, 13, 2)][i]
        stem = (f'Two registers initially hold x={x} and y={y}. Execute these instructions in order: '
                f'(1) replace x with x+{inc}; (2) swap the current values of x and y; '
                '(3) replace y with 2*y-x, using the values after the swap. What is the final value of y?')
        good, bad = str(2*(x+inc)-y), str(2*y-(x+inc))
        state = dict(x=x, y=y)
        state['x'] += inc
        state['x'], state['y'] = state['y'], state['x']
        state['y'] = 2*state['y']-state['x']
        check = str(state['y'])
        params = dict(x=x, y=y, increment=inc)
        rationale = f'After the swap x={y}, y={x+inc}; the final assignment gives {good}. The alternative skips the swap.'
        method = 'Symbolic substitution and imperative register execution.'
    elif family == 'set_overlap':
        n, a, b, neither = [(40, 22, 18, 8), (50, 30, 25, 10), (60, 34, 28, 12),
                             (45, 24, 21, 9), (80, 45, 38, 17)][i]
        both = a+b-(n-neither)
        stem = (f'Among {n} people, {a} speak language L, {b} speak language M, and {neither} speak neither. '
                'Each count refers to these same people. A person is chosen uniformly from those who speak L. '
                'What is the probability that this person also speaks M?')
        good, bad = fraction(Fraction(both, a)), fraction(Fraction(both, n))
        # Recover the four disjoint groups from the supplied marginals.
        feasible = [(ab, a-ab, b-ab, neither) for ab in range(n+1)
                    if ab <= min(a, b) and ab+(a-ab)+(b-ab)+neither == n]
        assert len(feasible) == 1 and all(v >= 0 for v in feasible[0])
        ab, only_l, _, _ = feasible[0]
        check = fraction(Fraction(ab, ab+only_l))
        params = dict(n=n, L=a, M=b, neither=neither)
        rationale = f'{both} speak both languages by inclusion-exclusion. The sampling population has {a} people, not {n}.'
        method = 'Inclusion-exclusion and unique disjoint-group reconstruction.'
    elif family == 'intervention':
        u, add, mult, set_x = [(2, 1, 3, 4), (3, 2, 2, 6), (4, 1, 2, 7),
                               (2, 3, 4, 7), (5, 2, 3, 9)][i]
        stem = (f'A system follows X=U+{add} and Y={mult}*X+U. In this case U={u}. '
                f'An intervention forces X={set_x}, replacing only the equation for X. '
                'The value of U and the equation for Y remain unchanged. What value does Y take after the intervention?')
        good = str(mult*set_x+u)
        bad = str(mult*set_x+(set_x-add))
        # Topological evaluation of a tiny structural equation system.
        values = dict(U=u)
        equations = [('X', lambda v: v['U']+add), ('Y', lambda v: mult*v['X']+v['U'])]
        for variable, equation in equations:
            values[variable] = set_x if variable == 'X' else equation(values)
        check = str(values['Y'])
        params = dict(U=u, add=add, multiplier=mult, forced_X=set_x)
        rationale = f'Keep U={u}; substitute the forced X={set_x} into Y. The alternative incorrectly infers a new U.'
        method = 'Direct substitution under an intervention and structural-equation evaluation.'
    else:
        assert family == 'expected_value'
        chance, prize, fee, sure = [(Fraction(1,4), 20, 2, 4), (Fraction(1,3), 18, 1, 4),
                                    (Fraction(2,5), 15, 3, 4), (Fraction(1,5), 30, 1, 4),
                                    (Fraction(3,10), 20, 3, 4)][i]
        stem = (f'Option R charges a guaranteed fee of {fee} credits and pays a gross prize of {prize} credits '
                f'with probability {chance}; otherwise it pays zero. Option S pays {sure} credits with no fee. '
                'Choose the option with the larger expected net gain, subtracting any fee from the payout. Which should be chosen?')
        net = chance*prize-fee
        good = 'Option R' if net > sure else 'Option S'
        bad = 'Option S' if good == 'Option R' else 'Option R'
        # Expand the rational probability into equally likely elementary outcomes.
        payoffs = [prize-fee]*chance.numerator + [-fee]*(chance.denominator-chance.numerator)
        mean = Fraction(sum(payoffs), len(payoffs))
        assert mean != sure
        check = 'Option R' if mean > sure else 'Option S'
        params = dict(probability=str(chance), gross_prize=prize, fee=fee, sure_gain=sure)
        rationale = f'R has expected net gain {fraction(net)} credits; S has {sure}. Compare expected values, not maximum prizes.'
        method = 'Expected-net-gain expression and elementary-outcome payoff average.'
    assert good == check and good != bad
    return dict(family=family, variant=i, stem=stem, answer=good, distractor=bad,
                parameters=params, author_derivation=rationale, author_check=method,
                author_checks_agree=True, empirical_difficulty='unmeasured')


def build(out):
    if out.exists():
        raise ValueError('Output directory already exists; choose a new version, never overwrite')
    rows = [make(family, i) for family in FAMILIES for i in range(5)]
    # Freeze cohorts by index before any model calls; no rejection based on outcomes.
    for row in rows:
        row['split'] = ('resource', 'calibration', 'calibration', 'reserved', 'reserved')[row['variant']]
    rng = random.Random(20261022067)
    for split in ('resource', 'calibration', 'reserved'):
        group = [r for r in rows if r['split'] == split]
        letters = list('AB'*(len(group)//2))
        rng.shuffle(letters)
        for row, letter in zip(group, letters):
            row['correct_letter'] = letter
            row['options'] = {k: row['answer'] if k == letter else row['distractor'] for k in 'AB'}
    rng.shuffle(rows)
    for i, row in enumerate(rows, 1):
        row['item_id'] = f'Q{i:03}'
    assert len({r['stem'] for r in rows}) == 40
    assert all(len(r['stem'].split()) <= 100 for r in rows)
    masked = [{k:r[k] for k in ('item_id', 'stem', 'options')} for r in rows]
    review_template = dict(reviewer_identity=None, prior_exposure=None, review_date=None,
        items=[dict(item_id=r['item_id'], chosen_letter=None, independently_derived_answer=None,
                    derivation=None, unique_supported_answer=None, other_option_assessment=None,
                    wording_or_assumption_issues=None, must_fix=None, estimated_steps=None,
                    expected_difficulty=None, family_overlap=None, answer_cues=None,
                    disposition=None) for r in masked])
    resource_rows = [r for r in rows if r['split'] == 'resource']
    routes = [('gpt-oss', 'openai/gpt-oss-120b', 'DekaLLM', 'dekallm/bf16', 'bf16'),
              ('Qwen3', 'qwen/qwen3-32b', 'Tenstorrent', 'tenstorrent/fp8', 'fp8')]
    trials = []
    for i, row in enumerate(resource_rows):
        for name, model, provider, slug, quant in routes[::(-1 if i % 2 else 1)]:
            content = INSTRUCTION+'\n\n'+row['stem']+'\n\nA. '+row['options']['A']+'\nB. '+row['options']['B']
            trials.append(dict(trial_id=row['item_id']+'__'+name, item_id=row['item_id'],
                expected_provider=provider, request_draft=dict(model=model,
                messages=[dict(role='user', content=content)], temperature=0.7, max_tokens=2048,
                provider=dict(order=[slug], only=[slug], allow_fallbacks=False,
                              quantizations=[quant], require_parameters=True)),
                live_price_ceiling_required=True))
    status = dict(stage='prepared_for_review', item_count=40, family_count=8,
        splits=dict(Counter(r['split'] for r in rows)), author_checks_passed=40,
        independent_review_complete=False, resource_gate_passed=False,
        resource_planned_calls=16, resource_attempted=0,
        calibration_candidate_calls=64, calibration_attempted=0, advice_attempted=0,
        original_study_remains_paused=True, live_preflight_complete=False,
        execution_ready=False, paid_requests_launched=0)
    proposal = dict(status='draft_for_user_review_not_an_execution_manifest',
        live_metadata_checked=False, live_budget_checked=False, independent_review_required=True,
        resource_gate_required=True, max_attempts_per_trial=1, timeout_seconds=180,
        minimum_preparation_interval_seconds=5, serial=True, cost_ceiling_usd='0.10',
        price_ceilings=None, trials=trials)
    files = {'author/packet_with_solutions.json':rows, 'review/masked_questions.json':masked,
             'review/review_template.json':review_template, 'status.json':status,
             'resource_plan_draft.json':proposal}
    text = '# Short reasoning questions for independent review\n\n'
    text += 'Forty synthetic two-choice questions. Select exactly one supported option, or flag the item if neither or both are supported.\n\n'
    for row in masked:
        text += f"## {row['item_id']}\n\n{row['stem']}\n\nA. {row['options']['A']}\n\nB. {row['options']['B']}\n\n"
    out.mkdir(parents=True)
    for name, value in files.items():
        path = out/name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as f:
            json.dump(value, f, indent=2)
            f.write('\n')
    (out/'review/questions.md').write_text(text)
    paths = [p for p in out.rglob('*') if p.is_file()] + [Path(__file__)]
    paths += [ROOT/'docs/SHORT_REASONING_V4_REVIEW.md', ROOT/'docs/SHORT_REASONING_V4_RESOURCE_PLAN.md']
    hashes = {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):
              hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with (out/'packet_hashes.json').open('x') as f:
        json.dump(hashes, f, indent=2)
        f.write('\n')
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    build(parser.parse_args().out)
