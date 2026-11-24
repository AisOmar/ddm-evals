"""Verify visible-stem checks catch incorrect keys and incomplete wording."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('author_audit',ROOT/'scripts/57_calibration_author_audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AuthorAuditTests(unittest.TestCase):
    def rows(self):
        return json.loads((a.SOURCE/'packet.json').read_text())

    def test_all_visible_stems_have_one_agreed_key_and_probability_wording_flagged(self):
        results = [a.assess(row) for row in self.rows()]
        self.assertEqual(sum(r['disposition']=='repair wording' for r in results),12)
        self.assertTrue(all(r['both_options_checked'] and not r['independent_review'] for r in results))

    def test_wrong_key_and_duplicate_options_are_rejected(self):
        row = copy.deepcopy(self.rows()[0]);row['correct_letter'] = 'A' if row['correct_letter']=='B' else 'B'
        with self.assertRaises(ValueError):a.assess(row)
        row = copy.deepcopy(self.rows()[0]);row['options']={'A':row['answer'],'B':row['answer']}
        with self.assertRaises(ValueError):a.assess(row)

    def test_visible_problem_changes_cannot_hide_behind_unchanged_parameter_sidecar(self):
        row = next(r for r in self.rows() if r['family']=='shortest_path')
        row = copy.deepcopy(row);row['stem']=row['stem'].replace('vertex 8?','vertex 7?')
        with self.assertRaises(ValueError):a.assess(row)


if __name__ == '__main__':
    unittest.main()
