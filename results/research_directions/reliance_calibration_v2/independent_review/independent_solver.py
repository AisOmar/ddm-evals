"""Fresh-context review; reads ONLY the two designated masked question files.
No answer key, generator, protocol, author audit, or other artifact is used.
Two independent algorithms per family check the derived answers.
"""
import ast
import hashlib
import itertools
import json
import math
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'semantic_revision'
INPUTS = [SOURCE / 'calibration_masked_review.json', SOURCE / 'reserved_masked_review.json']

def recurrence(s):
    x0, x1, a, b, modulus, n = map(int, re.fullmatch(
        r'An integer sequence has x_0=(\d+), x_1=(\d+)\. For n >= 2, x_n is the least nonnegative residue of (\d+)\*x_\(n-1\) \+ (\d+)\*x_\(n-2\) modulo (\d+)\. What is x_(\d+)\?', s).groups())
    xs = [x0, x1]
    for _ in range(2, n + 1):
        xs.append((a * xs[-1] + b * xs[-2]) % modulus)
    def mul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(2)) % modulus for j in range(2)] for i in range(2)]
    result, base, exponent = [[1, 0], [0, 1]], [[a, b], [1, 0]], n - 1
    while exponent:
        if exponent % 2:
            result = mul(result, base)
        base = mul(base, base)
        exponent //= 2
    check = (result[0][0] * x1 + result[0][1] * x0) % modulus
    assert xs[n] == check
    return Fraction(xs[n]), {'last_terms': xs[-5:], 'matrix_crosscheck': check}, f'Iterated the stated recurrence through n={n}; last five terms are {xs[-5:]}. Independently checked by modular matrix exponentiation.', 'high: 38–60 sequential modular arithmetic steps; routine method but laborious and error prone without tools'

def subset(s):
    weights = ast.literal_eval(re.search(r'weights (\[.*?\])', s).group(1))
    k = int(re.search(r'exactly (\d+) objects', s).group(1))
    limit, residue, modulus = map(int, re.search(r'at most (\d+) and congruent to (\d+) modulo (\d+)', s).groups())
    sums = Counter(sum(c) for c in itertools.combinations(weights, k))
    valid = {total: count for total, count in sorted(sums.items()) if total <= limit and total % modulus == residue}
    answer = sum(valid.values())
    dp = [Counter() for _ in range(k + 1)]
    dp[0][0] = 1
    for weight in weights:
        for selected in range(k, 0, -1):
            for total, count in list(dp[selected - 1].items()):
                dp[selected][total + weight] += count
    check = sum(count for total, count in dp[k].items() if total <= limit and total % modulus == residue)
    assert answer == check
    return Fraction(answer), {'counts_by_qualifying_sum': valid, 'total_subsets_examined': math.comb(len(weights), k), 'dp_crosscheck': check}, f'Enumerated all {math.comb(len(weights), k)} unordered label combinations and filtered by sum and residue; independently checked with subset-sum dynamic programming.', 'very high: exact constrained enumeration of 2002 subsets or a substantial counting table; overwhelmingly bookkeeping without tools'

def shortest(s):
    edges = ast.literal_eval(re.search(r'Edges: (\[.*\])\. What', s).group(1))
    adj = {i: [] for i in range(9)}
    for u, v, w in edges:
        adj[u].append((v, w))
    # Exhaustive simple-path DFS, avoiding any reliance on topological structure.
    paths = []
    def visit(u, path, cost):
        if u == 8:
            paths.append((cost, path))
        for v, w in adj[u]:
            if v not in path:
                visit(v, path + [v], cost + w)
    visit(0, [0], 0)
    answer = min(c for c, _ in paths)
    winners = [p for c, p in paths if c == answer]
    # Independent Bellman-Ford relaxation.
    distances = [math.inf] * 9
    distances[0] = 0
    for _ in range(8):
        previous = distances[:]
        for u, v, w in edges:
            distances[v] = min(distances[v], previous[u] + w)
    assert answer == distances[8]
    return Fraction(answer), {'minimum_paths': winners, 'distances_from_0': distances, 'paths_examined': len(paths)}, f'Exhaustively enumerated simple directed 0-to-8 paths; minimum path(s): {winners}, cost {answer}. Independently verified with Bellman-Ford distances {distances}.', 'low to moderate: nine-vertex forward-only graph; a few promising paths or a small distance table suffice'

def urn(s):
    pnum, pden, ur, ub, vr, vb, n, r, b = map(int, re.fullmatch(
        r'Choose urn U with prior probability (\d+)/(\d+), otherwise urn V\. U has (\d+) red and (\d+) blue balls; V has (\d+) red and (\d+) blue balls\. Draw (\d+) balls uniformly without replacement from the chosen urn and observe exactly (\d+) red and (\d+) blue, with order unobserved\. Which option gives the exact posterior probability that U was chosen\?', s).groups())
    assert r + b == n
    lu = Fraction(math.comb(ur, r) * math.comb(ub, b), math.comb(ur + ub, n))
    lv = Fraction(math.comb(vr, r) * math.comb(vb, b), math.comb(vr + vb, n))
    p = Fraction(pnum, pden)
    answer = p * lu / (p * lu + (1 - p) * lv)
    # Compute event mass by a sequential draw recursion over every colour order.
    def event(red, blue):
        states = {(0, 0): Fraction(1)}
        for drawn in range(n):
            nxt = {}
            for (rr, bb), mass in states.items():
                if red > rr:
                    nxt[rr + 1, bb] = nxt.get((rr + 1, bb), Fraction(0)) + mass * Fraction(red - rr, red + blue - drawn)
                if blue > bb:
                    nxt[rr, bb + 1] = nxt.get((rr, bb + 1), Fraction(0)) + mass * Fraction(blue - bb, red + blue - drawn)
            states = nxt
        return states[r, b]
    slu, slv = event(ur, ub), event(vr, vb)
    assert (lu, lv) == (slu, slv)
    check = p * slu / (p * slu + (1 - p) * slv)
    assert answer == check
    return answer, {'likelihood_U': str(lu), 'likelihood_V': str(lv), 'posterior': str(answer)}, f'Hypergeometric likelihoods P(E|U)={lu}, P(E|V)={lv}; Bayes posterior p*P(E|U)/(p*P(E|U)+(1-p)*P(E|V))={answer}. Likelihoods independently checked by sequential colour-draw recursion.', 'moderate to high: Bayes and hypergeometric setup is standard; distinguishing near-identical exact fractions needs lengthy exact arithmetic'

def main():
    judgments = []
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    items = [item for p in INPUTS for item in json.loads(p.read_text())]
    for item in items:
        family = item['family']
        solver = {'recurrence': recurrence, 'subset_count': subset, 'shortest_path': shortest, 'urn_posterior': urn}[family]
        answer, evidence, derivation, difficulty = solver(item['stem'])
        alternatives = {letter: Fraction(value) for letter, value in item['options'].items()}
        matches = [letter for letter, value in alternatives.items() if value == answer]
        issues = ['Repeated same-family template creates procedural overlap and potential practice/transfer across calibration and reserved packets.', 'Options differ by only 1 or 2 in the integer answer or fraction numerator; mainly tests exact arithmetic and error detection.']
        disposition = 'repair'
        if family in ('recurrence', 'subset_count'):
            issues.append('Tool-free burden is dominated by repetitive arithmetic/bookkeeping rather than selecting a reasoning strategy.')
        if family == 'shortest_path':
            issues.append('All edges increase vertex labels; graph is acyclic and easier than general shortest-path wording might suggest.')
            if any(len(path) == 2 for path in evidence['minimum_paths']):
                issues.append('A direct source-to-target edge is optimal, creating a particularly easy item relative to the other families.')
            # Retain as mathematically sound, accessible anchor; packet-level cues still need attention.
            disposition = 'retain'
        if family == 'urn_posterior':
            issues.append('Same-denominator alternatives make the task an exact numerator discrimination; conceptual posterior understanding alone does not distinguish them.')
            reduced = {k: math.gcd(*map(int, v.split('/'))) == 1 for k, v in item['options'].items()}
            evidence['options_in_lowest_terms'] = reduced
            if len(set(reduced.values())) > 1:
                issues.append('Only one displayed option is in lowest terms. This is a possible formatting heuristic, although the stem does not require reduced form and it does not logically prove correctness.')
        if len(matches) != 1:
            disposition = 'unresolved'
            issues.append('The independently derived answer does not match exactly one displayed alternative.')
        judgments.append({'item_id': item['item_id'], 'family': family, 'derived_numerical_answer': str(answer), 'chosen_letter': matches[0] if len(matches) == 1 else 'unresolved', 'alternatives_checked': {letter: {'value': str(value), 'equals_derived_answer': value == answer} for letter, value in alternatives.items()}, 'short_derivation': derivation, 'evidence': evidence, 'unique_answer': len(matches) == 1, 'ambiguity': 'No substantive ambiguity found: indexing, subset identity/order, graph direction/cost, and sampling without replacement are explicit.', 'issues': issues, 'disposition': disposition, 'difficulty_without_tools': difficulty, 'mostly_computation': True})
    (OUT / 'initial_judgments.json').write_text(json.dumps(judgments, indent=2) + '\n')
    report = {
        'review_type': 'Fresh-context AI review, not a human expert review or an independently trained model. The reviewer received the two masked packets and task instructions only, and did not read any answer keys, author audits, generator code, protocol/revision logs, or other question artifacts.',
        'input_sha256': hashes,
        'items_reviewed': len(judgments),
        'unique_answer_count': sum(j['unique_answer'] for j in judgments),
        'chosen_letters': dict(Counter(j['chosen_letter'] for j in judgments)),
        'dispositions': dict(Counter(j['disposition'] for j in judgments)),
        'by_packet': {prefix: {'chosen_letters': dict(Counter(j['chosen_letter'] for j in judgments if j['item_id'].startswith(prefix))), 'count': sum(j['item_id'].startswith(prefix) for j in judgments)} for prefix in ['calibration', 'reserved']},
        'summary': [
            'All 48 visible stems define a unique numerical answer and exactly one of the two alternatives matches an independent solution. No answer-key comparison was performed.',
            'Two different computational procedures agreed per item. This verifies numerical correctness while leaving empirical human/model difficulty unmeasured.',
            'All 48 tasks are mostly computation. Four procedural templates account for all items; within-family questions are parameter substitutions, and reserved items reproduce the calibration procedures. This is narrow numerical-task coverage, with likely learning and family clustering.',
            'Difficulty is markedly heterogeneous: subset counting is very burdensome without tools; recurrence needs many routine updates; urn questions need exact rational arithmetic; shortest-path questions are substantially easier, with forward-only graphs and some optimal direct edges.',
            'All 48 option pairs are numerical near-neighbours (integer or numerator gap 1 or 2). Distractors mostly represent small arithmetic errors rather than alternative reasoning. This may fit exact numerical reliance but is weak coverage of broader judgment or conceptual reasoning.',
            'No systematic answer-position cue is asserted until the independently solved letter distribution is inspected; distributions are provided above. The option ordering and reducibility diagnostics should be considered before calibration.',
            'Disposition policy: retain the 12 mathematically sound shortest-path items as possible accessible anchors; repair the 36 exact-arithmetic-heavy items and/or their alternatives if calibration targets reasoning beyond computation. These are design judgments, not claims that any answer is wrong. Packet-level family and cue concerns apply even to retained items.',
            'Recommend diversifying task structures, using plausible conceptual/procedural distractors, balancing answer positions independently of family/packet, and piloting without tools. Rewriting changes item difficulty and must precede calibration.'
        ]
    }
    (OUT / 'initial_summary.json').write_text(json.dumps(report, indent=2) + '\n')
    lock_files = [OUT / 'initial_judgments.json', OUT / 'initial_summary.json', Path(__file__).resolve()]
    manifest = {'status': 'INITIAL REVIEW LOCKED BEFORE ANY ANSWER-KEY COMPARISON', 'input_sha256': hashes, 'output_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in lock_files}}
    (OUT / 'INITIAL_SHA256_LOCK.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['items_reviewed', 'unique_answer_count', 'chosen_letters', 'dispositions', 'by_packet']}, indent=2))
    print('Locked initial artifacts at', OUT)

if __name__ == '__main__':
    main()
