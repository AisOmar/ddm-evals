import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


q=module('qualified_pilot_tests','79_deepinfra_wording_pilot.py')


class DeepInfraWordingPilotTests(unittest.TestCase):
    def test_gates_require_the_completed_new_resource_phase(self):
        q.configure()
        self.assertEqual(len(q.gates()),24)
        with patch.object(q.g.w,'audit_phase',side_effect=ValueError('resource unavailable')):
            with self.assertRaisesRegex(ValueError,'resource unavailable'):q.gates()

    def test_unchanged_reviewed_questions_with_new_route_only(self):
        q.configure();rows=q.gates()
        ep={name:dict(pricing=dict(prompt='.0000001',completion='.0000004'),
                      max_completion_tokens=4096,context_length=32768) for name in q.ROUTES}
        trials=q.w.plan(rows,ep,'pilot')
        self.assertEqual(len(trials),288)
        for t in trials:
            tag='deepinfra/fp8' if t['model']=='Qwen3' else 'dekallm/bf16'
            self.assertEqual(t['request']['provider']['only'],[tag])
            self.assertNotIn('reasoning',t['request'])

    def test_unauthorized_prepare_never_reads_ledger(self):
        with patch.object(q.c,'load',side_effect=AssertionError('must not read')):
            with self.assertRaisesRegex(ValueError,'authorized'):q.prepare(False)

    def test_incomplete_pilot_cannot_be_analyzed(self):
        q.configure()
        with patch.object(q.w,'audit_phase',side_effect=ValueError('All 288 finalized trials required')):
            with self.assertRaisesRegex(ValueError,'288'):q.audit_phase()
