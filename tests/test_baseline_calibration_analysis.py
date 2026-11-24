import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('baseline_analysis',ROOT/'scripts/61_analyze_baseline_calibration.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class BaselineAnalysisTests(unittest.TestCase):
    def test_nonanswers_do_not_become_factual_errors_or_disappear_from_yield(self):
        rows=[dict(outcome=dict(status='answered',correct=True,strict_format=True)),
              dict(outcome=dict(status='censored',correct=None,strict_format=None))]
        result=a.counts(rows)
        self.assertEqual(result['answered_accuracy'],1)
        self.assertEqual(result['correct_yield'],.5)
        self.assertTrue(result['ceiling_warning'])
        self.assertTrue(result['unavailable_warning'])

    def test_repeats_remain_together_and_empty_answer_bootstraps_report_undefined(self):
        rows=[dict(item_id='q',family='one',outcome=dict(status='answered',correct=c,strict_format=True)) for c in (True,False)]
        self.assertEqual(a.bootstrap(rows,n_draws=100)['correct_yield_95'],[.5,.5])
        rows=[dict(item_id='q',family='one',outcome=dict(status='censored',correct=None,strict_format=None))]
        result=a.bootstrap(rows,n_draws=100)
        self.assertIsNone(result['answered_accuracy_95'])
        self.assertEqual(result['undefined_accuracy_draws'],100)

    def test_partial_collection_cannot_be_analyzed(self):
        with patch.object(a.b,'manifest',return_value={'trials':[]}),patch.object(a.b.c,'history',return_value=[]):
            with self.assertRaisesRegex(ValueError,'96 attempts required'):a.audit()
