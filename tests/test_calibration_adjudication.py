from collections import Counter
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review_adjudication',ROOT/'scripts/59_adjudicate_calibration_review.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class ReviewAdjudicationTests(unittest.TestCase):
    def test_balanced_irregular_positions_remove_suffix_parity_cue(self):
        patterns=a.positions()
        self.assertEqual(len(set(patterns)),8)
        for p in patterns:
            self.assertEqual(Counter(p),{'A':3,'B':3})
            self.assertNotIn(p,('ABABAB','BABABA','AAABBB','BBBAAA'))
        for group in (patterns[:4],patterns[4:]):
            self.assertEqual(sum(p[j]=='A' for p in group for j in (0,2,4)),6)

    def test_blind_review_agreement_and_changed_keys_fail_closed(self):
        rows=json.loads((a.BASE/'semantic_revision/packet.json').read_text())
        judgments=json.loads((a.REVIEW/'initial_judgments.json').read_text())
        self.assertTrue(a.adjudicate(rows,judgments))
        rows[0]['correct_letter']='A' if rows[0]['correct_letter']=='B' else 'B'
        with self.assertRaises(ValueError):a.adjudicate(rows,judgments)

    def test_locked_reviewer_inputs_verify(self):
        a.check_review_locks()
