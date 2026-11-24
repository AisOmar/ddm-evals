import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('sonnet_pilot',Path(__file__).resolve().parents[1]/'scripts/102_sonnet_advice_pilot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SonnetPilotTests(unittest.TestCase):
    def setUp(self):
        self.items=m.c.load(m.c.PACKET/'author/packet_with_solutions.json')

    def test_complete_balanced_reproducible_plan(self):
        plan=m.plan(self.items)
        self.assertEqual(len(plan),144);self.assertEqual(plan,m.plan(self.items))
        self.assertEqual(len({t['id'] for t in plan}),144)
        self.assertEqual({t['family'] for t in plan},{x['family'] for x in self.items})
        self.assertEqual({t['item_id'] for t in plan},{x['item_id'] for x in self.items if x['split']=='calibration'})

    def test_advice_uses_keys_and_matched_instructions(self):
        for x in self.items:
            for i in m.INSTRUCTIONS:
                none=m.request(x,i,'none')['messages'][0]['content']
                self.assertNotIn('Recommendation:',none)
                correct=m.request(x,i,'correct')['messages'][0]['content']
                wrong=m.request(x,i,'wrong')['messages'][0]['content']
                other='A' if x['correct_letter']=='B' else 'B'
                self.assertIn('Recommendation: '+x['correct_letter'],correct)
                self.assertIn('Recommendation: '+other,wrong)
                self.assertEqual(correct.replace('Recommendation: '+x['correct_letter'],'Recommendation: X'),wrong.replace('Recommendation: '+other,'Recommendation: X'))

    def test_baseline_change_adjusts_raw_gain(self):
        p=m.profile(dict(none=.5,correct=.8,wrong=.2),dict(none=.6,correct=.9,wrong=.5))
        self.assertAlmostEqual(p['wrong_advice_accuracy_change'],.3)
        self.assertAlmostEqual(p['baseline_adjusted_harm_reduction'],.2)
        self.assertAlmostEqual(p['benefit_change'],0)

    def test_ignoring_all_advice_cannot_pass_full_pattern(self):
        rows=[]
        for i in m.INSTRUCTIONS:
            for a in m.CELLS:
                rows.append((dict(instruction=i,advice=a),dict(status='answered',correct=True)))
        s=m.summary(rows)
        self.assertFalse(s['correct_yield_profile']['descriptive_full_pattern'])

    def test_nonanswer_unknowns_and_bounds(self):
        rows=[]
        for i in m.INSTRUCTIONS:
            for a in m.CELLS:
                rows.append((dict(instruction=i,advice=a),dict(status='behavioral_nonanswer',correct=None)))
        s=m.summary(rows)
        self.assertIsNone(s['correct_yield_profile']['descriptive_full_pattern'])
        self.assertEqual(s['factual_contrast_bounds']['baseline_adjusted_harm_reduction'],[-2,2])
        self.assertTrue(all(x['recognized_accuracy'] is None for x in s['cells']))

if __name__=='__main__':unittest.main()
