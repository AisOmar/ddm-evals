import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


g=module('short_packet','62_manageable_packet.py')
r=module('short_collect','63_manageable_collect.py')
h=module('short_analysis','64_manageable_analysis.py')


class ManageableTests(unittest.TestCase):
    def test_half_percentage_rounds_up_exactly(self):
        from fractions import Fraction
        self.assertEqual(g.percent(Fraction(105,200)),'53%')
        self.assertEqual(g.percent(Fraction(1,3)),'33%')

    def test_review_keys_match_all_current_items(self):
        rows=r.check_review()
        self.assertEqual(len(rows),36)
        self.assertTrue(all(x['parameters']['n']<=10 for x in rows if x['family']=='recurrence'))
        self.assertTrue(all(len(x['parameters']['weights'])==6 for x in rows if x['family']=='subset_count'))

    def test_unauthorized_preparation_never_reads_manifest(self):
        with patch.object(r,'manifest',side_effect=AssertionError('must not read')):
            with self.assertRaises(ValueError):r.prepare(False)

    def test_calibration_requires_all_resource_deliveries(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);r.p.save(base/'resource/manifest.json',dict(input_hashes={},trials=[]))
            with patch.object(r,'BASE',base):
                with self.assertRaisesRegex(ValueError,'Resource gate incomplete'):r.check_resource_gate()

    def test_incomplete_calibration_cannot_be_analyzed(self):
        with patch.object(h.r,'manifest',return_value={'trials':[]}),patch.object(h.r.c,'history',return_value=[]):
            with self.assertRaisesRegex(ValueError,'All 64'):h.audit()

    def test_resource_gate_uses_delivery_not_factual_accuracy(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);out=base/'resource';trials=[]
            for i in range(8):
                rid=str(i);trial=dict(sample_id=rid,request={'model':'test'});trials.append(trial)
                r.p.save(out/'requests'/(rid+'.json'),trial['request'])
                r.p.save(out/'raw'/(rid+'.json'),{'test':True})
                (out/'headers').mkdir(exist_ok=True);(out/'headers'/(rid+'.txt')).write_text('HTTP/1.1 200')
                final=dict(sample_id=rid,outcome=dict(status='answered',correct=False),cost_within_reserve=True,curl_exit=0,
                    request_sha256=r.p.sha(out/'requests'/(rid+'.json')),raw_sha256=r.p.sha(out/'raw'/(rid+'.json')),
                    headers_sha256=r.p.sha(out/'headers'/(rid+'.txt')))
                r.p.save(out/'finished'/(rid+'.json'),final)
            r.p.save(out/'manifest.json',dict(input_hashes={},trials=trials))
            with patch.object(r,'BASE',base):self.assertTrue(r.check_resource_gate())
