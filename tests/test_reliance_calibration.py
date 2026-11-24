"""Oracle and scoring boundary tests for the separate offline development packet."""
from fractions import Fraction
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calibration_v2',ROOT/'scripts/54_reliance_calibration.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
repair_spec = importlib.util.spec_from_file_location('repair_calibration',ROOT/'scripts/55_repair_calibration_options.py')
repair = importlib.util.module_from_spec(repair_spec)
repair_spec.loader.exec_module(repair)


class CalibrationTests(unittest.TestCase):
    def test_probability_options_do_not_reveal_key_by_denominator(self):
        for answer in ('4719/37019','605/622','40/51','22/107'):
            value = Fraction(answer)
            for above in (False,True):
                wrong = Fraction(repair.matched_fraction_distractor(answer,above))
                self.assertNotEqual(wrong,value)
                self.assertEqual(wrong.denominator,value.denominator)
                self.assertTrue(0 < wrong < 1)

    def test_known_answers_from_hand_solvable_cases(self):
        cases = [
            ('recurrence',dict(a=1,b=1,x0=0,x1=1,n=10,mod=97),55),
            ('subset_count',dict(weights=[1,2,3,4],k=2,threshold=6,mod=2,residue=0),2),
            ('shortest_path',dict(n=4,edges=[[0,1,4],[1,3,2],[0,2,2],[2,3,9],[0,3,10]]),6),
            ('urn_posterior',dict(r1=2,b1=1,r2=1,b2=2,draws=1,red=1,prior=Fraction(1,2)),Fraction(2,3)),
        ]
        for family,params,expected in cases:
            for alternate in (False,True):
                with self.subTest(family=family,alternate=alternate):
                    self.assertEqual(p.solve(family,params,alternate),expected)

    def test_candidate_solvers_agree_beyond_published_seeds(self):
        for family in p.FAMILIES:
            for seed in range(100,120):
                row = p.candidate(family,seed,'test','calibration')
                self.assertTrue(row['computational_agreement'])
                self.assertEqual(row['options'][row['correct_letter']],row['answer'])
                self.assertEqual(len(set(row['options'].values())),2)

    def test_no_mining_prose_and_no_contradictory_option_recovery(self):
        options = {'A':'Yes','B':'No'}
        for text in ('A or B','Answer: A','A. No','A. Yes because I agree','A/B','A. Yes; B. No'):
            with self.subTest(text=text):
                self.assertEqual(p.parse_choice(text,options),(None,False))
        self.assertEqual(p.parse_choice('Reasoning mentions B.\nA',options),('A',True))
        self.assertEqual(p.parse_choice('**B**',options),('B',False))
        self.assertEqual(p.parse_choice('A. YES',options),('A',False))

    def test_format_correctness_and_nonanswers_are_separate(self):
        options = {'A':'23','B':'25'}
        for status in ('censored','refusal','api_error','incomplete','identity_error','cap_violation'):
            result = p.score(dict(status=status,text='A'),options,'A')
            self.assertIsNone(result['correct'])
            self.assertIsNone(result['strict_format'])
        strict_wrong = p.score(dict(status='completed',text='B'),options,'A')
        self.assertFalse(strict_wrong['correct'])
        self.assertTrue(strict_wrong['strict_format'])
        flexible_correct = p.score(dict(status='completed',text='A. 23'),options,'A')
        self.assertTrue(flexible_correct['correct'])
        self.assertFalse(flexible_correct['strict_format'])
        ambiguous = p.score(dict(status='completed',text='A or B'),options,'A')
        self.assertIsNone(ambiguous['correct'])


if __name__ == '__main__':
    unittest.main()
