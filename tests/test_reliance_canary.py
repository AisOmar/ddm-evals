"""Canary guard and raw-response scoring checks; no network."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('delivery_canary',ROOT/'scripts/56_reliance_canary.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class CanaryTests(unittest.TestCase):
    def trial(self):
        return dict(sample_id='test',options={'A':'5','B':'6'},correct_letter='A',
                    request=dict(model='qwen/qwen3-32b',max_tokens=512))

    def response(self,text='A'):
        return dict(provider='DeepInfra',model='qwen/qwen3-32b',
                    choices=[dict(message=dict(content=text),finish_reason='stop')],
                    usage=dict(prompt_tokens=50,completion_tokens=10,cost=.00001))

    def test_provider_length_refusal_and_usage_precede_parsing(self):
        t = self.trial()
        for field,value,expected in [('provider','Other','provider_or_model_mismatch'),
                                      ('usage',{'prompt_tokens':True,'completion_tokens':4},'invalid_response')]:
            r = self.response();r[field] = value
            self.assertEqual(c.result(t,r,200)['status'],expected)
        r = self.response();r['choices'][0]['finish_reason']='length'
        self.assertEqual(c.result(t,r,200)['status'],'censored')
        r = self.response();r['choices'][0]['message']['refusal']='refused'
        self.assertEqual(c.result(t,r,200)['status'],'refusal')
        r = self.response();r['usage']['completion_tokens']=513
        self.assertEqual(c.result(t,r,200)['status'],'output_cap_violation')

    def test_http_and_malformed_payloads_are_never_answers(self):
        for data,http,expected in [({},429,'rate_limited'),({'error':{'code':429}},200,'rate_limited'),
                                   (self.response(),503,'http_error'),([],200,'invalid_response'),
                                   ({'choices':['bad']},200,'invalid_response')]:
            self.assertEqual(c.result(self.trial(),data,http)['status'],expected)

    def test_correctness_is_separate_from_strict_format(self):
        result = c.result(self.trial(),self.response('A. 5'),200)
        self.assertTrue(result['correct'])
        self.assertFalse(result['strict_format'])
        self.assertIsNone(c.result(self.trial(),self.response('A. 6'),200)['correct'])

    def test_no_authorization_does_not_read_manifest(self):
        with patch.object(c,'manifest',side_effect=AssertionError('must not load')):
            with self.assertRaises(ValueError):
                c.prepare(False)

    def test_failures_and_uncertain_attempts_block_next_dispatch(self):
        for finished in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                out = Path(directory)
                (out/'attempts').mkdir()
                (out/'attempts/01.json').write_text(json.dumps(dict(sample_id='test',prepared_at='2026-01-01T00:00:00+00:00')))
                if finished:
                    (out/'finished').mkdir()
                    (out/'finished/test.json').write_text(json.dumps(dict(gate_passed=False)))
                m = dict(preflight_started_at=datetime.now(timezone.utc).isoformat(),trials=[self.trial()])
                with patch.object(c,'OUT',out),patch.object(c,'manifest',return_value=m),patch.object(c,'no_other_collection'):
                    with self.assertRaises(ValueError):
                        c.prepare(True)

    def test_stale_preflight_and_duplicate_attempts_block_dispatch(self):
        m = dict(preflight_started_at='2026-01-01T00:00:00+00:00',trials=[self.trial()])
        with patch.object(c,'manifest',return_value=m),patch.object(c,'no_other_collection'):
            with self.assertRaises(ValueError):
                c.prepare(True)
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);(out/'attempts').mkdir()
            for name in ('01','02'):
                (out/'attempts'/(name+'.json')).write_text(json.dumps(dict(sample_id='test')))
            with patch.object(c,'OUT',out):
                with self.assertRaises(ValueError):
                    c.history(m)


if __name__ == '__main__':
    unittest.main()
