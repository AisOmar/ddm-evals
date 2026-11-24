import importlib.util
from fractions import Fraction as F
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('verification_transfer',Path(__file__).resolve().parents[1]/'scripts/104_verification_transfer.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class VerificationTransferTests(unittest.TestCase):
    def test_packet_exact_checks(self):
        rows=m.packet.build()
        self.assertEqual([r['answer'] for r in rows],['6','252','269','7','18','84'])
        self.assertEqual(len({r['family'] for r in rows}),6)
        self.assertEqual([r['options'][r['correct_letter']] for r in rows],[r['answer'] for r in rows])

    def test_stage_balance_and_new_templates(self):
        trials,reviews=m.plan()
        self.assertEqual(len(trials),108);self.assertEqual(len(reviews),2)
        self.assertEqual(trials,m.plan()[0])
        self.assertEqual(len({r['id'] for r in trials}),108)
        self.assertFalse({r['family'] for r in trials if r['phase']=='development'}&{r['family'] for r in trials if r['phase']=='transfer'})

    def test_new_prompt_exactly_changes_instruction(self):
        item=m.packet.build()[0]
        for advice in m.r.CELLS:
            ordinary=m.request(item,'ordinary',advice)['messages'][0]['content']
            verify=m.request(item,'verification',advice)['messages'][0]['content']
            self.assertEqual(ordinary.replace(m.r.ORDINARY,m.VERIFY),verify)
            self.assertEqual('Recommendation:' in verify,advice!='none')

    def test_exact_contrast_no_cancellation_false_positive(self):
        ordinary=dict(none=F(16,24),correct=F(24,24),wrong=F(2,24))
        candidate=dict(none=F(20,24),correct=F(24,24),wrong=F(6,24))
        self.assertEqual(m.contrast(ordinary,candidate)['baseline_adjusted_harm_reduction'],0)

    def test_unknowns_keep_factual_bounds(self):
        rows=[(dict(instruction=i,advice=a),dict(status='behavioral_nonanswer',correct=None)) for i in m.PROMPTS for a in m.r.CELLS]
        summary=m.summary(rows)
        self.assertFalse(summary['all_answered'])
        for contrast in summary['comparisons'].values():
            self.assertIsNone(contrast['descriptive_full_pattern'])
            self.assertEqual(contrast['factual_bounds']['baseline_adjusted_harm_reduction'],[-2,2])

    def test_harm_only_pattern_does_not_pass(self):
        rows=[]
        for i in m.PROMPTS:
            for a in m.r.CELLS:
                correct=not(i=='verification' and a=='correct')
                rows.append((dict(instruction=i,advice=a),dict(status='answered',correct=correct)))
        self.assertFalse(m.summary(rows)['comparisons']['verification_vs_ordinary']['descriptive_full_pattern'])

if __name__=='__main__':unittest.main()
