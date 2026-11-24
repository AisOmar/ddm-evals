"""Execution guards: reviewed inputs, complete conditions, and fail-stop delivery."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('focus_launch_test', ROOT/'scripts/85_selective_reliance_launch.py')
l = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l)


class FocusLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = l.c.load(l.PACKET/'author/packet_with_solutions.json')
        cls.endpoints = {name: l.a.endpoint(l.c.load(l.BASE/(name+'.json')), route[0], route[2])
                         for name, route in l.ROUTES.items()}

    def test_pilot_has_all_six_cells_and_repeats_per_item_model(self):
        trials = l.plan(self.rows, self.endpoints, 'pilot')
        self.assertEqual(len(trials), 288)
        self.assertEqual(len({trial['sample_id'] for trial in trials}), 288)
        for item in {trial['item_id'] for trial in trials}:
            for model in l.ROUTES:
                actual = {(t['instruction'], t['advice'], t['repeat']) for t in trials
                          if t['item_id'] == item and t['model'] == model}
                expected = {(inst, advice, repeat) for inst in ('ordinary', 'explicit')
                            for advice in ('none', 'correct', 'wrong') for repeat in (1, 2)}
                self.assertEqual(actual, expected)

    def test_advice_changes_only_recommendation_across_correctness(self):
        trials = l.plan(self.rows, self.endpoints, 'pilot')
        for trial in trials:
            req = trial['request']
            content = req['messages'][0]['content']
            self.assertFalse(req['provider']['allow_fallbacks'])
            self.assertNotIn(trial['item_id'], content)
            self.assertNotIn('author_derivation', content)
            if trial['advice'] == 'none':
                self.assertNotIn('Recommendation:', content)
            else:
                letter = content.rsplit('Recommendation: ', 1)[1]
                self.assertEqual(letter == trial['correct_letter'], trial['advice'] == 'correct')

    def test_cohorts_are_disjoint_and_calibration_has_no_advice(self):
        ids = {}
        for phase in l.N:
            trials = l.plan(self.rows, self.endpoints, phase)
            ids[phase] = {trial['item_id'] for trial in trials}
            if phase != 'pilot':
                self.assertTrue(all(t['instruction'] == 'ordinary' and t['advice'] == 'none' for t in trials))
        self.assertFalse(ids['resource'] & ids['calibration'])
        self.assertFalse(ids['resource'] & ids['pilot'])
        self.assertFalse(ids['calibration'] & ids['pilot'])

    def test_review_blocker_prevents_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base/'review_v3').mkdir()
            (base/'review_v3/INITIAL_SHA256_LOCK.json').write_text('{}')
            (base/'review_v3/adjudication.json').write_text('{"review_gate_passed": false}')
            with patch.object(l, 'BASE', base), patch.object(l.f, 'verify', return_value={}):
                with self.assertRaisesRegex(ValueError, 'unresolved blockers'):
                    l.review_gate()

    def test_wrong_answer_is_retained_but_truncation_stops(self):
        for status, expected_continue in [('answered', True), ('censored', False),
                                          ('rate_limited', False), ('uncertain_delivery', False)]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                trial = l.plan(self.rows, self.endpoints, 'resource')[0]
                rid = trial['sample_id']
                for directory in ('raw', 'headers', 'finished', 'http'):
                    (out/directory).mkdir()
                (out/'active.json').write_text(json.dumps(dict(sample_id=rid, request_sha256='fixture')))
                (out/'raw'/(rid+'.json')).write_text('{"usage":{"cost":0}}')
                (out/'headers'/(rid+'.txt')).write_text('HTTP/1.1 200 OK\n')
                result = dict(status=status, correct=False if status == 'answered' else None,
                              choice='A' if status == 'answered' else None, strict_format=True)
                with patch.object(l, 'OUT', out), patch.object(l, 'manifest', return_value=dict(trials=[trial])), \
                        patch.object(l.a, 'result', return_value=result):
                    l.finish(0, 200)
                final = json.loads((out/'finished'/(rid+'.json')).read_text())
                self.assertEqual(final['continue_permitted'], expected_continue)
                self.assertFalse(final['retry_permitted'])
                self.assertFalse((out/'active.json').exists())


if __name__ == '__main__':
    unittest.main()
