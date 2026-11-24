"""Validate position-only masked repair against prior blind numerical judgments.
Never reads author keys, packets, or position plans. Preserves earlier artifacts.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
NAMES = ['calibration_masked_review.json', 'reserved_masked_review.json']
OLD = [ROOT / 'semantic_revision' / name for name in NAMES]
NEW = [ROOT / 'reviewed_calibration' / 'position_revision' / name for name in NAMES]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    locks = [OUT / name for name in ['INITIAL_SHA256_LOCK.json', 'ADDENDUM_SHA256_LOCK.json', 'FINAL_AUDIT_SHA256_LOCK.json', 'CORRECTION_SHA256_LOCK.json']]
    for lockfile in locks:
        manifest = json.loads(lockfile.read_text())
        for key in ['input_sha256', 'output_sha256', 'sha256']:
            for name, expected in manifest.get(key, {}).items():
                assert digest(Path(name)) == expected, name
    old = {r['item_id']: r for path in OLD for r in json.loads(path.read_text())}
    revised = [r for path in NEW for r in json.loads(path.read_text())]
    baseline = {r['item_id']: r for r in json.loads((OUT / 'initial_judgments.json').read_text())}
    assert len(revised) == len(old) == len(baseline) == 48
    assert len({r['item_id'] for r in revised}) == 48
    assert {r['item_id'] for r in revised} == set(old)
    judgments = []
    for row in revised:
        previous = old[row['item_id']]
        b = baseline[row['item_id']]
        assert row['stem'] == previous['stem']
        assert row['family'] == previous['family']
        assert sorted(row['options'].values()) == sorted(previous['options'].values())
        answer = Fraction(b['derived_numerical_answer'])
        matched = [letter for letter, value in row['options'].items() if Fraction(value) == answer]
        assert len(matched) == 1
        judgments.append({
            'item_id': row['item_id'], 'family': row['family'],
            'derived_numerical_answer': str(answer), 'chosen_letter': matched[0],
            'prior_chosen_letter': b['chosen_letter'],
            'alternatives_checked': {letter: {'value': value, 'equals_derived_answer': Fraction(value) == answer} for letter, value in row['options'].items()},
            'unique_answer': True, 'stem_unchanged': True, 'alternative_value_multiset_unchanged': True,
            'derivation_basis': 'Previously locked blind solution, verified by two independent computational methods; mathematics not rerun because stem and both exact option values are unchanged.',
            'short_derivation': b['short_derivation'], 'evidence': b['evidence'],
            'disposition': 'retain' if row['family'] == 'shortest_path' else 'repair',
            'position_repair_disposition': 'retain: the specific parity cue is resolved',
            'disposition_explanation': 'Restores the initial substantive design judgment; remaining repair judgments concern computation/difficulty/construct coverage, not arithmetic correctness or option position.',
            'difficulty_without_tools': b['difficulty_without_tools'],
            'remaining_issues': b['issues'], 'mostly_computation': True,
        })
    sequences = {}
    family_balance = {}
    suffix_balance = {}
    split_balance = {}
    for split in ['calibration', 'reserved']:
        split_rows = [r for r in judgments if r['item_id'].startswith(split + '-')]
        split_balance[split] = dict(Counter(r['chosen_letter'] for r in split_rows))
        assert split_balance[split] == {'A': 12, 'B': 12} or split_balance[split] == {'B': 12, 'A': 12}
        for family in ['recurrence', 'subset_count', 'shortest_path', 'urn_posterior']:
            rows = sorted([r for r in split_rows if r['family'] == family], key=lambda r: r['item_id'])
            key = split + '-' + family
            sequences[key] = ''.join(r['chosen_letter'] for r in rows)
            assert sequences[key] not in ['ABABAB', 'BABABA']
            family_balance[key] = dict(Counter(r['chosen_letter'] for r in rows))
            assert family_balance[key] == {'A': 3, 'B': 3} or family_balance[key] == {'B': 3, 'A': 3}
        for suffix in range(1, 7):
            rows = [r for r in split_rows if r['item_id'].endswith(f'-{suffix:02}')]
            key = f'{split}-{suffix:02}'
            suffix_balance[key] = dict(Counter(r['chosen_letter'] for r in rows))
            assert suffix_balance[key] == {'A': 2, 'B': 2} or suffix_balance[key] == {'B': 2, 'A': 2}
    assert len(set(sequences.values())) == 8
    summary = {
        'review_type': 'Follow-up by the same fresh-context AI reviewer, not human expert review or independent model training. Only revised masked inputs, original masked inputs, and this reviewer\'s own previously locked artifacts were read. No author keys, packets, or position_plan opened.',
        'status': 'PASS: position-only revision preserves all 48 independent numerical solutions and resolves the specific universal suffix-parity cue.',
        'items_checked': 48, 'unique_matching_answers': 48,
        'unchanged_stems': 48, 'unchanged_option_value_multisets': 48,
        'new_mathematics_required': False,
        'checks': {'all_blocks_non_alternating': True, 'each_split_family_3A_3B': True, 'each_suffix_within_split_2A_2B_across_families': True, 'all_eight_block_sequences_distinct': True, 'previous_locks_verified': True},
        'block_sequences': sequences, 'family_balance': family_balance,
        'suffix_balance': suffix_balance, 'split_balance': split_balance,
        'position_letter_changes': sum(r['chosen_letter'] != r['prior_chosen_letter'] for r in judgments),
        'substantive_dispositions': dict(Counter(r['disposition'] for r in judgments)),
        'specific_position_dispositions': {'retain': 48},
        'remaining_concerns': [
            'All 48 tasks remain mostly computation, with near-neighbour numerical alternatives testing exact arithmetic.',
            'Recurrence and subset items remain burdensome without tools; urn items need exact rational arithmetic; shortest-path items are comparatively accessible.',
            'Four repeated templates still create within-family overlap and potential procedural transfer from calibration to reserved items.',
            'The two shortest-path items with optimal direct source-target edges remain calibration-shortest_path-06 and reserved-shortest_path-01.',
            'Difficulty expectations are qualitative and require empirical piloting.',
            'Passing these specified balance and pattern checks does not establish absence of every possible answer cue. Fixed per-family balance can constrain remaining letters if prior answers are known.'
        ],
        'interpretation': 'The former option-position blocker is resolved. This position-only repair does not address or invalidate the earlier computation, difficulty, distractor, or family-overlap concerns. No question-text changes are needed for arithmetic validity.',
    }
    outputs = [OUT / 'postrepair_judgments.json', OUT / 'postrepair_summary.json']
    for path, payload in zip(outputs, [judgments, summary]):
        assert not path.exists(), 'Never overwrite a prior review artifact'
        path.write_text(json.dumps(payload, indent=2) + '\n')
    manifest = {'status': 'POSTREPAIR BLIND VALIDATION LOCKED; NO KEYS OPENED',
                'input_sha256': {str(p): digest(p) for p in OLD + NEW + [OUT / 'initial_judgments.json']},
                'output_sha256': {str(p): digest(p) for p in outputs + [Path(__file__).resolve()]},
                'previous_lock_sha256': {str(p): digest(p) for p in locks}}
    lockpath = OUT / 'POSTREPAIR_SHA256_LOCK.json'
    assert not lockpath.exists()
    lockpath.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
