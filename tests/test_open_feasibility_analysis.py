import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('feasibility_analysis', ROOT / 'scripts/53_open_feasibility_analysis.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AnalysisTests(unittest.TestCase):
    def rows(self):
        return [dict(review_id=q, model=m, instruction=i, advice=s,
                     outcome='answered', correct=True)
                for q in ('good', 'wrong', 'delivery', 'format')
                for m in a.p.MODELS for i in ('ordinary', 'explicit')
                for s in ('none', 'correct', 'incorrect')]

    def test_complete_case_uses_all_twelve_outcomes_and_keeps_wrong_answers(self):
        rows = self.rows()
        next(r for r in rows if r['review_id'] == 'wrong')['correct'] = False
        next(r for r in rows if r['review_id'] == 'delivery')['outcome'] = 'api_error'
        next(r for r in rows if r['review_id'] == 'format')['outcome'] = 'format_error'
        self.assertEqual(a.common_complete_questions(rows), ['good', 'wrong'])
        duplicate = [dict(r) for r in rows if r['review_id'] == 'good']
        duplicate[-1] = dict(duplicate[0])
        self.assertEqual(a.common_complete_questions(duplicate), [])

    def test_primary_and_answered_denominators_remain_distinct(self):
        rows = self.rows()
        rows[0].update(outcome='api_error', correct=False)
        rows[12].update(correct=False)
        cell = a.cells(rows)[0]
        self.assertEqual((cell['n'], cell['n_answered'], cell['n_correct']), (4, 3, 2))
        self.assertEqual(cell['correct_yield'], .5)
        self.assertEqual(cell['answered_accuracy'], 2 / 3)
        self.assertEqual(cell['outcomes'], {'api_error': 1, 'answered': 3})


if __name__ == '__main__':
    unittest.main()
