"""Retry only explicit, answer-free provider rejections; preserve one slot outcome."""
from datetime import datetime,timezone
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bounded_rate_test',ROOT/'scripts/99_rate_limit_calibration_recovery.py')
r = importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class RateRecoveryTests(unittest.TestCase):
    def test_unknown_delivery_wrong_answer_and_wrong_provider_are_not_retryable(self):
        body=dict(error=dict(code=429,metadata=dict(provider_name='DekaLLM')))
        self.assertTrue(r.confirmed_rejection(0,429,body,'DekaLLM'))
        self.assertFalse(r.confirmed_rejection(28,429,body,'DekaLLM'))
        self.assertFalse(r.confirmed_rejection(0,200,body,'DekaLLM'))
        self.assertFalse(r.confirmed_rejection(0,429,body,'DeepInfra'))
        body['choices']=[dict(message=dict(content='A'))]
        self.assertFalse(r.confirmed_rejection(0,429,body,'DekaLLM'))

    def test_cooldown_has_floor_and_honors_server_date_or_seconds(self):
        now=datetime(2026,10,26,12,0,tzinfo=timezone.utc)
        self.assertEqual(r.cooldown('',now),60)
        self.assertEqual(r.cooldown('retry-after: 120\n',now),120)
        self.assertEqual(r.cooldown('Retry-After: Mon, 26 Oct 2026 12:02:00 GMT\n',now),120)

    def test_rejection_is_not_an_independent_or_preferred_answer(self):
        m=dict(trials=[dict(sample_id='x'),dict(sample_id='y')])
        records=[dict(sample_id='x',slot_finalized=False),
                 dict(sample_id='x',slot_finalized=True,outcome=dict(status='answered',correct=False))]
        pending,accepted=r.schedule(m,records)
        self.assertEqual(pending['sample_id'],'y')
        self.assertEqual(len(accepted),1)
        self.assertFalse(accepted['x']['outcome']['correct'])


if __name__=='__main__':unittest.main()
