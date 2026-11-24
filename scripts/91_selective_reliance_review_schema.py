"""Strict, recorded interpretation of an affirmative but nonstandard review schema."""
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('schema_review', ROOT/'scripts/88_selective_reliance_tool_review.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_REVIEW_SCHEMA_INTERPRETATION.md'
NO_BLOCKERS_PROSE = "None. All nine problems have clear mathematical models, unambiguous derivations, and unique answers that match exactly one of the two provided options. The problems follow consistent templates: F001 is a probability update with an uninformed inspector; F004, F021, F029 are weighted success rate comparisons; F007, F016, F028 are decision problems with test information and fees; F011, F024 are Bayesian updates with independent tests."


def normalize(raw):
    result = json.loads(json.dumps(raw))
    changes = []
    for item in result['items']:
        if item['disposition'] == 'CONFIDENT':
            if (item['unique_supported_answer'] is not True
                or item['must_fix_before_execution'] is not False
                or not item['concerns'].startswith('None.')):
                raise ValueError('Confidence cannot override an unresolved concern')
            changes.append(dict(item_id=item['item_id'], field='disposition', original='CONFIDENT', normalized='retain'))
            item['disposition'] = 'retain'
        elif item['disposition'] != 'retain':
            raise ValueError('Unsupported or unresolved disposition')
    blockers = result['overall_execution_blockers']
    if blockers == NO_BLOCKERS_PROSE:
        changes.append(dict(field='overall_execution_blockers', original=blockers, normalized=[]))
        result['overall_execution_blockers'] = []
    elif blockers != []:
        raise ValueError('Blocker prose is not the exact affirmative statement')
    return result, changes


def main():
    q.manifest()
    q.verify_lock(q.OUT/'INITIAL_SHA256_LOCK.json')
    q.verify_lock(q.OUT/'tool_result_lock.json')
    source = q.OUT/'initial_judgments.json'
    raw = q.l.c.load(source)
    normalized, changes = normalize(raw)
    q.save(q.OUT/'normalized_judgments.json', normalized)
    q.save(q.OUT/'schema_interpretation.json', dict(created_at=q.l.p.now(), source_sha256=q.l.p.sha(source),
        author_interpretation_of_schema=True, numerical_results_changed=False,
        independent_review_repeated=False, changes=changes))
    q.lock([Path(__file__), PROTOCOL, source, q.OUT/'normalized_judgments.json', q.OUT/'schema_interpretation.json'],
           q.OUT/'schema_interpretation_lock.json')
    # Raw and normalized representations are locked before rechecking keys.
    author = q.l.c.load(q.l.PACKET/'author/packet_with_solutions.json')
    original = {row['item_id']: row for row in q.l.c.load(q.l.BASE/'review_v3/initial_judgments.json')['items']}
    new = {row['item_id']: row for row in normalized['items']}
    ids = set(q.manifest()['ids'])
    if len(normalized['items']) != 9 or set(new) != ids or len(original) != 30:
        raise ValueError('Review coverage failed')
    calc = q.l.c.load(q.OUT/'calculator_result.json')
    issues = []
    for row in author:
        key = row['item_id']
        judgment = new[key] if key in new else original[key]
        if (judgment['chosen_letter'] != row['correct_letter'] or judgment['unique_supported_answer'] is not True
            or judgment['must_fix_before_execution'] is not False or judgment['disposition'] != 'retain'):
            issues.append(key)
        if key in new and not Fraction(judgment['derived_answer']) == Fraction(calc[key]) == Fraction(row['answer']):
            issues.append(key)
    prior = q.l.c.load(q.OUT/'adjudication.json')
    readiness = dict(created_at=q.l.p.now(), review_gate_passed=not issues,
        total_items_covered=30, calculator_assisted_adjudications=9, prior_unflagged_items=21,
        unresolved_ids=sorted(set(issues)), keys_changed=False, questions_removed=False, human_review=False,
        original_schema_result_preserved=True, author_schema_interpretation_disclosed=True,
        recorded_new_cost_usd=prior['recorded_new_cost_usd'],
        cumulative_recorded_cost_usd=prior['cumulative_recorded_cost_usd'], original_study_remains_paused=True)
    q.save(q.OUT/'review_readiness.json', readiness)
    print(json.dumps(readiness, indent=2))


if __name__ == '__main__': main()
