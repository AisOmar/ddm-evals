import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('baseline_calibration',ROOT/'scripts/60_calibrate_reviewed_packet.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


class BaselineCalibrationTests(unittest.TestCase):
    def test_unauthorized_preparation_never_loads_manifest(self):
        with patch.object(b,'manifest',side_effect=AssertionError('must not load')):
            with self.assertRaises(ValueError):b.prepare(False)

    def test_failure_to_pass_canary_blocks_calibration(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'finished').mkdir()
            b.p.save(out/'manifest.json',dict(input_hashes={},trials=[]))
            with patch.object(b,'CANARY',out):
                with self.assertRaisesRegex(ValueError,'canary has not passed'):b.gates()

    def test_behavioral_nonanswer_is_retained_but_transport_error_stops(self):
        trial=dict(sample_id='trial',expected_provider='DekaLLM',correct_letter='A',options={'A':'5','B':'6'},
            request=dict(model='openai/gpt-oss-120b',max_tokens=4096,messages=[],provider=dict(max_price={'prompt':.03,'completion':.18})))
        for http,finish,expected in [(200,'length',True),(429,'stop',False)]:
            with tempfile.TemporaryDirectory() as folder:
                out=Path(folder)
                b.p.save(out/'active.json',dict(sample_id='trial',prepared_at='2026-01-01T00:00:00+00:00'))
                b.p.save(out/'raw/trial.json',dict(provider='DekaLLM',model='openai/gpt-oss-120b',
                    choices=[dict(message=dict(content='A'),finish_reason=finish)],
                    usage=dict(prompt_tokens=50,completion_tokens=10,cost=.00001)))
                (out/'headers').mkdir();(out/'headers/trial.txt').write_text('HTTP/1.1 '+str(http))
                with patch.object(b,'OUT',out),patch.object(b,'manifest',return_value={'trials':[trial]}),contextlib.redirect_stdout(io.StringIO()):
                    b.finish(0,http)
                saved=b.c.load(out/'finished/trial.json')
                self.assertEqual(saved['continue_permitted'],expected)
                self.assertIsNone(saved['outcome']['correct'])
