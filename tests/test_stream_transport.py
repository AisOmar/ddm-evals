"""Stream termination, accounting repeats, errors and answer-channel separation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('strict_sse', ROOT/'scripts/94_stream_transport.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
MODEL, PROVIDER = 'qwen/qwen3-32b', 'DeepInfra'


def frame(delta=None, finish=None, usage=None, **extra):
    value = dict(id='gen-test', model=MODEL, provider=PROVIDER,
                 choices=[dict(index=0, delta=delta or {}, finish_reason=finish)])
    if usage is not None: value['usage'] = usage
    value.update(extra)
    return value


def encode(frames, done=True):
    text = ': OPENROUTER PROCESSING\r\n\r\n'
    text += ''.join('data: '+json.dumps(f, ensure_ascii=False)+'\r\n\r\n' for f in frames)
    if done: text += 'data: [DONE]\r\n\r\n'
    return text.encode('utf-8')


class StreamTransportTests(unittest.TestCase):
    def fixture(self):
        usage = dict(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost=.0001)
        return [frame(dict(role='assistant', reasoning='A is mentioned only in reasoning.')),
                frame(dict(content='Réponse:\n')), frame(dict(content='B'), 'stop'),
                frame(dict(role='assistant', content=''), 'stop', usage)]

    def test_usage_terminal_repeat_and_utf8_preserve_visible_answer(self):
        result, audit = s.reconstruct(encode(self.fixture()), MODEL, PROVIDER)
        self.assertEqual(result['choices'][0]['message']['content'], 'Réponse:\nB')
        self.assertIn('A is mentioned', result['choices'][0]['message']['reasoning'])
        self.assertEqual(audit['accounting_frames'], 1)
        self.assertFalse(audit['reasoning_used_as_answer'])

    def test_missing_done_usage_or_terminal_fails_closed(self):
        with self.assertRaisesRegex(s.StreamFailure, 'missing_done'):
            s.reconstruct(encode(self.fixture(), done=False), MODEL, PROVIDER)
        with self.assertRaisesRegex(s.StreamFailure, 'missing_usage'):
            s.reconstruct(encode(self.fixture()[:-1]), MODEL, PROVIDER)
        frames = [frame(dict(content='B')), frame({}, usage=dict(prompt_tokens=1, completion_tokens=1))]
        with self.assertRaisesRegex(s.StreamFailure, 'missing_terminal'):
            s.reconstruct(encode(frames), MODEL, PROVIDER)

    def test_http_200_stream_error_cannot_become_answer(self):
        frames = self.fixture()[:2]+[frame({}, 'error', error=dict(code=429, message='capacity'))]
        with self.assertRaisesRegex(s.StreamFailure, 'stream_api_error'):
            s.reconstruct(encode(frames), MODEL, PROVIDER)

    def test_identity_change_and_content_after_stop_fail(self):
        frames = self.fixture(); frames[1]['id'] = 'another-generation'
        with self.assertRaisesRegex(s.StreamFailure, 'identity_changed'):
            s.reconstruct(encode(frames), MODEL, PROVIDER)
        frames = self.fixture(); frames[-1]['choices'][0]['delta']['content'] = 'A'
        with self.assertRaisesRegex(s.StreamFailure, 'content_after_terminal'):
            s.reconstruct(encode(frames), MODEL, PROVIDER)

    def test_empty_usage_choices_and_multiline_sse_are_valid(self):
        frames = self.fixture(); frames[-1]['choices'] = []
        self.assertEqual(s.reconstruct(encode(frames), MODEL, PROVIDER)[0]['usage']['completion_tokens'], 20)
        payload = json.dumps(self.fixture()[0], indent=2)
        first = '\n'.join('data: '+line for line in payload.splitlines())+'\n\n'
        raw = first.encode()+encode(self.fixture()[1:])
        self.assertEqual(s.reconstruct(raw, MODEL, PROVIDER)[0]['id'], 'gen-test')

    def test_malformed_or_post_done_payload_is_not_ignored(self):
        for body in (b'data: {oops}\n\ndata: [DONE]\n\n',
                     encode(self.fixture())+b'data: {}\n\n',
                     encode(self.fixture())[:-2], b'data: \xff\n\n'):
            with self.subTest(body=body[:30]), self.assertRaises(s.StreamFailure):
                s.reconstruct(body, MODEL, PROVIDER)

    def test_reasoning_only_is_not_promoted_to_visible_content(self):
        frames = self.fixture(); frames[1]['choices'][0]['delta'] = {}; frames[2]['choices'][0]['delta'] = {}
        result, _ = s.reconstruct(encode(frames), MODEL, PROVIDER)
        self.assertEqual(result['choices'][0]['message']['content'], '')
        spec = importlib.util.spec_from_file_location('legacy_answer_contract', ROOT/'scripts/56_reliance_canary.py')
        legacy = importlib.util.module_from_spec(spec); spec.loader.exec_module(legacy)
        trial = dict(request=dict(model=MODEL, max_tokens=4096), options=dict(A='yes', B='no'), correct_letter='A')
        self.assertEqual(legacy.result(trial, result, 200)['status'], 'incomplete')

    def test_conflicting_usage_or_terminal_cannot_pass(self):
        frames = self.fixture(); extra = copy.deepcopy(frames[-1]); extra['usage']['cost'] = 1
        with self.assertRaisesRegex(s.StreamFailure, 'usage_changed'):
            s.reconstruct(encode(frames+[extra]), MODEL, PROVIDER)
        frames = self.fixture(); frames[-1]['choices'][0]['finish_reason'] = 'length'
        with self.assertRaisesRegex(s.StreamFailure, 'inconsistent_terminal'):
            s.reconstruct(encode(frames), MODEL, PROVIDER)

    def test_only_explicit_model_alias_can_be_normalized(self):
        frames = self.fixture()
        for frame in frames: frame['model'] = 'qwen/qwen3-32b-04-28'
        with self.assertRaisesRegex(s.StreamFailure, 'model_mismatch'):
            s.reconstruct(encode(frames), MODEL, PROVIDER)
        result, audit = s.reconstruct(encode(frames), MODEL, PROVIDER, ('qwen/qwen3-32b-04-28',))
        self.assertEqual(result['model'], MODEL)
        self.assertEqual(result['reported_model'], 'qwen/qwen3-32b-04-28')
        self.assertTrue(audit['model_alias_applied'])


if __name__ == '__main__': unittest.main()
