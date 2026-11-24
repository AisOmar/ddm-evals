from datetime import datetime,timezone
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bounded_retry_tests',ROOT/'scripts/82_wording_bounded_recovery.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class BoundedRecoveryTests(unittest.TestCase):
    def test_retry_after_is_never_shorter_than_backoff(self):
        now='2026-10-23T01:00:00+00:00'
        self.assertEqual(r.retry_deadline('Retry-After: 5',now,1)['effective_delay_seconds'],60)
        self.assertEqual(r.retry_deadline('Retry-After: 300',now,2)['effective_delay_seconds'],300)
        self.assertEqual(r.retry_deadline('Retry-After: Fri, 23 Oct 2026 01:05:00 GMT',now,1)['effective_delay_seconds'],300)
        self.assertEqual(r.retry_deadline('Retry-After: invalid',now,3)['effective_delay_seconds'],240)

    def test_only_confirmed_expected_provider_rejection_is_retryable(self):
        trial={'expected_provider':'DekaLLM'}
        raw={'error':{'code':429,'metadata':{'provider_name':'DekaLLM'}}}
        final=dict(outcome={'status':'rate_limited'},continue_permitted=False,curl_exit=0,http_status=429,
                   missing_cost_metadata=True,cost_within_reserve=False,finished_at='2026-10-23T01:00:00+00:00')
        self.assertEqual(r.policy_for(trial,raw,final,'',1)['kind'],'retryable_rejection')
        self.assertEqual(r.policy_for(trial,raw,dict(final,curl_exit=28),'',1)['kind'],'stop')
        self.assertEqual(r.policy_for(trial,raw,final,'',4)['kind'],'stop')
        self.assertEqual(r.policy_for({'expected_provider':'DeepInfra'},raw,final,'',1)['kind'],'stop')
        self.assertEqual(r.policy_for(trial,{},final,'',1)['kind'],'stop')

    def test_delivered_nonanswer_is_not_retried_for_a_better_answer(self):
        for kind in ('answered','censored','refusal','ambiguous_format','incomplete'):
            final=dict(outcome={'status':kind},continue_permitted=True)
            self.assertEqual(r.policy_for({},None,final,'',1),{'kind':'delivered','retry_allowed':False})

    def test_authorization_precedes_any_ledger_access(self):
        with patch.object(r,'manifest',side_effect=AssertionError('must not read')):
            with self.assertRaisesRegex(ValueError,'authorization'):r.prepare(False)

    def test_original_125_deliveries_and_error_are_preserved(self):
        r.configure()
        m,delivered,counts,failures,paths=r.source_deliveries()
        self.assertEqual(len(delivered),125)
        self.assertEqual(len(counts),126)
        self.assertEqual(len(failures),1)
        self.assertEqual(len(m['trials']),288)
        self.assertTrue(all((ROOT/path).exists() for path in delivered.values()))

    def test_incomplete_cohort_analysis_is_blocked(self):
        with patch.object(r,'manifest',return_value={}),patch.object(r,'state',return_value=dict(stop=None,completed={})):
            with self.assertRaisesRegex(ValueError,'288'):r.audit_complete()
