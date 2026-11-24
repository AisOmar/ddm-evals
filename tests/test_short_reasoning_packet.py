"""Check review masking, arithmetic distinctions, and the unexecuted handoff."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/research_directions/short_reasoning_v4_20261022'
spec = importlib.util.spec_from_file_location('short_reasoning', ROOT/'scripts/67_short_reasoning_packet.py')
packet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet)


class ShortReasoningTests(unittest.TestCase):
    def test_posterior_is_not_sensitivity_even_in_last_variant(self):
        row = packet.make('base_rate', 4)
        self.assertEqual(row['answer'], '3/5')
        self.assertEqual(row['distractor'], '3/4')

    def test_parallel_tasks_are_not_serial_and_swap_changes_operand_roles(self):
        self.assertEqual(packet.make('dependencies', 0)['answer'], '9 minutes')
        self.assertEqual(packet.make('dependencies', 0)['distractor'], '14 minutes')
        self.assertEqual(packet.make('state_updates', 0)['answer'], '3')
        self.assertEqual(packet.make('state_updates', 0)['distractor'], '9')

    def test_intervention_holds_external_input_fixed_and_fee_is_certain(self):
        self.assertEqual(packet.make('intervention', 0)['answer'], '14')
        self.assertEqual(packet.make('intervention', 0)['distractor'], '15')
        self.assertEqual(packet.make('expected_value', 0)['answer'], 'Option S')
        self.assertEqual(packet.make('expected_value', 1)['answer'], 'Option R')

    def test_masking_and_fixed_cohorts(self):
        rows = json.loads((BASE/'author/packet_with_solutions.json').read_text())
        masked = json.loads((BASE/'review/masked_questions.json').read_text())
        self.assertEqual(len(rows), 40)
        self.assertEqual(Counter(r['split'] for r in rows), dict(resource=8, calibration=16, reserved=16))
        self.assertEqual(Counter(r['family'] for r in rows), dict.fromkeys(packet.FAMILIES, 5))
        self.assertEqual({r['item_id'] for r in rows}, {r['item_id'] for r in masked})
        for row, hidden in zip(rows, masked):
            self.assertEqual(set(hidden), {'item_id', 'stem', 'options'})
            self.assertEqual(hidden, {k:row[k] for k in hidden})
            self.assertEqual(row['options'][row['correct_letter']], row['answer'])
            self.assertNotEqual(row['answer'], row['distractor'])

    def test_request_draft_is_resource_only_and_excludes_solutions(self):
        proposal = json.loads((BASE/'resource_plan_draft.json').read_text())
        rows = json.loads((BASE/'author/packet_with_solutions.json').read_text())
        resource_ids = {r['item_id'] for r in rows if r['split'] == 'resource'}
        self.assertEqual(len(proposal['trials']), 16)
        self.assertEqual({r['item_id'] for r in proposal['trials']}, resource_ids)
        self.assertIsNone(proposal['price_ceilings'])
        self.assertFalse(proposal['live_budget_checked'])
        for trial in proposal['trials']:
            self.assertNotIn('correct_letter', trial)
            request = trial['request_draft']
            self.assertFalse(request['provider']['allow_fallbacks'])
            self.assertEqual(request['max_tokens'], 2048)
            self.assertNotIn(trial['item_id'], request['messages'][0]['content'])
            self.assertNotIn('max_price', request['provider'])

    def test_hashes_and_nonoverwrite_guard(self):
        hashes = json.loads((BASE/'packet_hashes.json').read_text())
        for name, expected in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected, name)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'never overwrite'):
                packet.build(Path(folder))
