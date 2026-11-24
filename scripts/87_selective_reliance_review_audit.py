"""Audit reviewer disagreements without changing keys or declaring review passed.

This is an author computational audit, not independent semantic validation.
"""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('focused_launch_audit', ROOT/'scripts/85_selective_reliance_launch.py')
l = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l)


def audit(row):
    stem, family = row['stem'], row['family']
    if family == 'two_tests':
        k = int(re.search(r'defective with probability 1/(\d+)', stem).group(1))
        # Each class label, X coin (4 outcomes), Y coin (3 outcomes) is equiprobable.
        surviving = [(label, x, y) for label in range(k) for x in range(4) for y in range(3)
                     if x < (3 if label == 0 else 1) and y >= (2 if label == 0 else 1)]
        numerator = sum(label == 0 for label, _, _ in surviving)
        answer = F(numerator, len(surviving))
        proof = dict(equiprobable_worlds_before_evidence=12*k,
                     evidence_worlds=len(surviving), defective_evidence_worlds=numerator,
                     calculation=f'{numerator}/{len(surviving)} = {answer}')
    elif family == 'random_reveal':
        n = int(re.search(r'one of (\d+) numbered boxes', stem).group(1))
        surviving = [(prize, opened) for prize in range(1, n+1) for opened in range(2, n+1)
                     if prize != opened]
        numerator = sum(prize == 1 for prize, _ in surviving)
        answer = F(numerator, len(surviving))
        proof = dict(equiprobable_prize_opened_pairs_before_evidence=n*(n-1),
                     empty_reveal_pairs=len(surviving), selected_box_prize_pairs=numerator,
                     calculation=f'{numerator}/{len(surviving)} = {answer}')
    elif family == 'value_of_information':
        prize = int(re.search(r'risky action pays (\d+)', stem).group(1))
        loss = int(re.search(r'loses (\d+)', stem).group(1))
        safe = int(re.search(r'safe action pays (\d+)', stem).group(1))
        fee = int(re.search(r'fee of (\d+)', stem).group(1))
        good_report_risky = F(3*prize-loss, 4)
        bad_report_risky = F(prize-3*loss, 4)
        answer = (max(good_report_risky, safe)+max(bad_report_risky, safe))/2-fee
        proof = dict(report_probabilities=['1/2', '1/2'],
                     risky_expected_payoff_after_good_report=str(good_report_risky),
                     risky_expected_payoff_after_bad_report=str(bad_report_risky),
                     safe_payoff=safe, guaranteed_fee=fee,
                     calculation=f'({max(good_report_risky, safe)}+{max(bad_report_risky, safe)})/2-{fee} = {answer}')
    elif family == 'standardized_rates':
        weight = F(re.search(r'easy-case share is ([\d/]+)', stem).group(1))
        k = weight*F(9, 10)+(1-weight)*F(20, 100)
        other = weight*F(80, 100)+(1-weight)*F(1, 10)
        answer = k-other
        proof = dict(target_easy_share=str(weight), K_target_success=str(k),
                     L_target_success=str(other), calculation=f'{k}-{other} = {answer}')
    else:
        raise ValueError('No disputed case expected in '+family)
    return str(answer), proof


def main():
    out = l.BASE/'review_adjudication'
    if out.exists():
        raise ValueError('Never overwrite adjudication')
    summary = l.c.load(l.BASE/'review_v3/adjudication.json')
    initial = l.c.load(l.BASE/'review_v3/initial_judgments.json')
    indexed = {row['item_id']: row for row in initial['items']}
    rows = l.c.load(l.PACKET/'author/packet_with_solutions.json')
    flagged = set(summary['disagreements']) | set(summary['item_blockers'])
    checks = []
    for row in rows:
        if row['item_id'] not in flagged:
            continue
        answer, proof = audit(row)
        checks.append(dict(item_id=row['item_id'], family=row['family'],
            author_answer=row['answer'], exact_audit_answer=answer,
            audit_matches_author=answer == row['answer'], reviewer=indexed[row['item_id']],
            exact_computational_evidence=proof))
    result = dict(created_at=l.p.now(), flagged_cases=len(checks),
        exact_checks_match_existing_keys=all(row['audit_matches_author'] for row in checks),
        author_audit_only=True, independent_semantic_review_passed=False,
        review_gate_remains_failed=True, keys_changed=False, questions_removed=False,
        interpretation='Computational evidence supports the original keys; it does not substitute for independent adjudication.',
        cases=checks)
    l.p.save(out/'computational_audit.json', result)
    lines = ['# Reviewer disagreement audit', '',
             'The original keys remain unchanged. Exact calculations below support those keys;',
             'this author audit does not pass the independent review gate.', '',
             '| Item | Existing key answer | Exact calculation |', '| --- | --- | --- |']
    for row in checks:
        lines.append(f"| {row['item_id']} | {row['author_answer']} | {row['exact_computational_evidence']['calculation']} |")
    lines += ['', 'Next: obtain an independent tool-assisted or human adjudication of these cases,',
              'preserving the locked initial review and recording every resolution. Do not',
              'drop the difficult items or treat the author audit as independent agreement.',
              'No further paid reviewer request is permitted in the current launch.', '']
    (out/'REPORT.md').write_text('\n'.join(lines))
    l.p.save(out/'artifact_hashes.json', {str(path.relative_to(ROOT)): l.p.sha(path)
        for path in [Path(__file__), out/'computational_audit.json', out/'REPORT.md',
                     l.BASE/'review_v3/INITIAL_SHA256_LOCK.json', l.BASE/'review_v3/adjudication.json']})
    print(json.dumps({key: value for key, value in result.items() if key != 'cases'}, indent=2))


if __name__ == '__main__':
    main()
