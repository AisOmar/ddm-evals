"""Combined review must retain unflagged checks and exact adjudication values."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('continuation_test', ROOT/'scripts/89_selective_reliance_continue.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ContinuationGateTests(unittest.TestCase):
    def fixture(self):
        rows = c.l.c.load(c.l.PACKET/'author/packet_with_solutions.json')
        ids = c.q.manifest()['ids']
        judgments = [dict(item_id=row['item_id'], chosen_letter=row['correct_letter'],
            derived_answer=row['answer'], unique_supported_answer=True,
            must_fix_before_execution=False, disposition='retain') for row in rows]
        new = [copy.deepcopy(row) for row in judgments if row['item_id'] in ids]
        calc = {row['item_id']: row['derived_answer'] for row in new}
        data = {str(c.q.OUT/'review_readiness.json'): dict(review_gate_passed=True),
                str(c.l.PACKET/'author/packet_with_solutions.json'): rows,
                str(c.OLD/'review_v3/initial_judgments.json'): dict(items=judgments),
                str(c.q.OUT/'normalized_judgments.json'): dict(items=new),
                str(c.q.OUT/'calculator_result.json'): calc}
        return ids, judgments, new, data

    def check(self, ids, data):
        with patch.object(c.l.f, 'verify', return_value={}), \
             patch.object(c.q, 'verify_lock'), \
             patch.object(c.q, 'manifest', return_value=dict(ids=ids)), \
             patch.object(c.l.c, 'load', side_effect=lambda path: data[str(path)]):
            return c.review_gate()

    def test_all_thirty_need_coverage(self):
        ids, prior, new, data = self.fixture()
        self.assertEqual(len(self.check(ids, data)), 30)
        unflagged = next(row for row in prior if row['item_id'] not in ids)
        unflagged['unique_supported_answer'] = False
        with self.assertRaisesRegex(ValueError, 'Unresolved review'):
            self.check(ids, data)

    def test_adjudicator_letter_agreement_cannot_hide_numeric_disagreement(self):
        ids, prior, new, data = self.fixture()
        new[0]['derived_answer'] = '123/456'
        with self.assertRaisesRegex(ValueError, 'numerical mismatch'):
            self.check(ids, data)


if __name__ == '__main__': unittest.main()
