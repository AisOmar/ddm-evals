"""Cohort completion preserves unknowns and distinguishes behavior from delivery."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cohort_completion_test', ROOT/'scripts/98_complete_calibration.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class CompletionTests(unittest.TestCase):
    def valid(self, status):
        return dict(curl_exit=0, http_status=200, http_version_matches=True,
                    normalized_sha256='fixture', cost_within_reserve=True, outcome=dict(status=status, correct=None))

    def test_completed_behavioral_nonanswers_are_not_retried_or_changed(self):
        for status in ('ambiguous_format', 'censored', 'refusal', 'incomplete'):
            row = self.valid(status)
            self.assertTrue(c.behavioral_continue(row))
            self.assertIsNone(row['outcome']['correct'])
            self.assertEqual(row['outcome']['status'], status)

    def test_failed_stream_identity_or_billing_cannot_continue(self):
        for status in ('stream_failure', 'provider_or_model_mismatch', 'output_cap_violation', 'uncertain_delivery'):
            self.assertFalse(c.behavioral_continue(self.valid(status)))
        for field, value in [('curl_exit', 28), ('cost_within_reserve', False), ('normalized_sha256', None),
                             ('http_version_matches', False)]:
            row = self.valid('ambiguous_format'); row[field] = value
            self.assertFalse(c.behavioral_continue(row))

    def test_only_38_new_slots_and_ten_original_observations(self):
        trials, retained = c.plan(c.PHASE, {})
        self.assertEqual(len(trials), 38)
        self.assertEqual(len(retained), 10)
        self.assertFalse({t['sample_id'] for t in trials} & {t['sample_id'] for t in retained})
        self.assertTrue(all(t['resend_permitted'] is False for t in retained))
        original = c.c.c.load(c.c.PREVIOUS/'calibration/manifest.json')['trials']
        self.assertEqual({t['sample_id'] for t in trials+retained}, {t['sample_id'] for t in original})


if __name__ == '__main__': unittest.main()
