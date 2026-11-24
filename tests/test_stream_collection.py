"""Recovery lineage, retained unknown answers, and strict stream finalization."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stream_collection_test', ROOT/'scripts/95_stream_collection.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class StreamCollectionTests(unittest.TestCase):
    def fixture(self):
        source = r.c.load(r.PREVIOUS/'calibration/manifest.json')
        return source, source['endpoint_snapshot']

    def test_only_46_unsent_slots_are_scheduled_and_original_two_are_retained(self):
        source, endpoints = self.fixture()
        trials, retained = r.plan('calibration', endpoints)
        self.assertEqual(len(trials), 46)
        self.assertEqual([row['sample_id'] for row in retained], [row['sample_id'] for row in source['trials'][:2]])
        self.assertFalse({row['sample_id'] for row in trials} & {row['sample_id'] for row in retained})
        self.assertTrue(all(row['resend_permitted'] is False for row in retained))
        states = [r.c.load(ROOT/row['finished_path'])['outcome']['status'] for row in retained]
        self.assertEqual(states, ['answered', 'uncertain_delivery'])

    def test_streaming_is_the_only_model_request_change(self):
        source, endpoints = self.fixture()
        trials, _ = r.plan('calibration', endpoints)
        for original, current in zip(source['trials'][2:], trials):
            self.assertTrue(current['request']['stream'])
            req = dict(current['request']); req.pop('stream')
            self.assertEqual(req, original['request'])
            self.assertEqual(current['correct_letter'], original['correct_letter'])

    def test_qualification_reuses_only_resource_items(self):
        _, endpoints = self.fixture()
        probes, retained = r.plan('qualification', endpoints)
        resource = r.c.load(r.PREVIOUS/'resource/manifest.json')['trials']
        self.assertEqual([row['sample_id'] for row in probes], [row['sample_id'] for row in resource])
        self.assertEqual(retained, [])

    def test_visible_letter_without_done_is_not_a_delivered_answer(self):
        _, endpoints = self.fixture(); trial = r.plan('qualification', endpoints)[0][0]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp); rid = trial['sample_id']
            for directory in ('raw', 'headers', 'normalized', 'parser_audit', 'finished', 'http'):
                (out/directory).mkdir()
            (out/'active.json').write_text(json.dumps(dict(sample_id=rid)))
            frame = dict(id='gen-test', provider=trial['expected_provider'], model=trial['request']['model'],
                         choices=[dict(index=0, delta=dict(content='A'), finish_reason='stop')],
                         usage=dict(prompt_tokens=1, completion_tokens=1, cost=0))
            (out/'raw'/(rid+'.sse')).write_text('data: '+json.dumps(frame)+'\n\n')
            (out/'headers'/(rid+'.txt')).write_text('HTTP/1.1 200 OK\n')
            with patch.object(r, 'OUT', out), patch.object(r, 'manifest', return_value=dict(trials=[trial])):
                r.finish(0, 200)
            final = json.loads((out/'finished'/(rid+'.json')).read_text())
            self.assertFalse(final['continue_permitted'])
            self.assertEqual(final['outcome']['correct'], None)
            self.assertEqual(final['parser_error'], 'missing_done')


if __name__ == '__main__': unittest.main()
