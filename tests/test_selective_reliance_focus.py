"""Scientific failure cases and integrity checks for the focused development design."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('focused', ROOT/'scripts/84_selective_reliance_focus.py')
focus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(focus)


class FocusedRelianceTests(unittest.TestCase):
    def test_unchanged_correct_accuracy_can_hide_lost_advice_gain(self):
        profile = focus.descriptive_profile(dict(none=.5, correct=.8, wrong=.2),
                                            dict(none=.8, correct=.8, wrong=.7))
        self.assertAlmostEqual(profile['correct_advice_accuracy_change'], 0)
        self.assertAlmostEqual(profile['benefit_change'], -.3)
        self.assertAlmostEqual(profile['explicit_benefit'], 0)

    def test_ignoring_all_advice_does_not_show_helpfulness(self):
        profile = focus.descriptive_profile(dict(none=.7, correct=.7, wrong=.7),
                                            dict(none=.7, correct=.7, wrong=.7))
        self.assertTrue(all(value == 0 for value in profile.values()))

    def test_lowering_baseline_cannot_count_as_harm_reduction(self):
        profile = focus.descriptive_profile(dict(none=.8, correct=.9, wrong=.5),
                                            dict(none=.5, correct=.9, wrong=.5))
        # Less measured harm arises solely from damaging ordinary answering.
        self.assertAlmostEqual(profile['baseline_adjusted_harm_reduction'], .3)
        self.assertEqual(profile['wrong_advice_accuracy_change'], 0)
        self.assertAlmostEqual(profile['baseline_accuracy_change'], -.3)

    def test_selection_and_intervention_protocols_change_the_answer(self):
        self.assertEqual(focus.make('random_reveal', 0)['answer'], '1/2')
        self.assertEqual(focus.make('random_reveal', 0)['distractor'], '1/3')
        self.assertEqual(focus.make('observed_then_intervened', 0)['answer'], '2/3')
        self.assertEqual(focus.make('two_tests', 0)['answer'], '3/7')
        self.assertEqual(focus.make('value_of_information', 0)['answer'], '15/4')

    def test_packet_masking_balance_and_provenance(self):
        rows = json.loads((focus.OUT/'author/packet_with_solutions.json').read_text())
        masked = json.loads((focus.OUT/'review/masked_questions.json').read_text())
        self.assertEqual(Counter(row['split'] for row in rows), dict(resource=6, calibration=12, reserved=12))
        for split in ('resource', 'calibration', 'reserved'):
            counts = Counter(row['correct_letter'] for row in rows if row['split'] == split)
            self.assertEqual(counts['A'], counts['B'])
        for row, visible in zip(rows, masked):
            self.assertEqual(set(visible), {'item_id', 'stem', 'options'})
            self.assertEqual(visible, {key: row[key] for key in visible})
            self.assertEqual(row['options'][row['correct_letter']], row['answer'])
        self.assertTrue(focus.verify(focus.OUT)['packet_verified'])

    def test_no_overwrite_or_executable_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'Never overwrite'):
                focus.build(Path(tmp))
        draft = json.loads((focus.OUT/'design_draft.json').read_text())
        self.assertIsNone(draft['execution_manifest'])
        self.assertIsNone(draft['live_price_ceilings'])
        self.assertFalse(draft['live_budget_verified'])

    def test_invalid_rates_are_rejected(self):
        for value in (float('nan'), float('inf'), -1, 2):
            with self.assertRaises(ValueError):
                focus.descriptive_profile(dict(none=value, correct=.8, wrong=.2),
                                          dict(none=.5, correct=.8, wrong=.2))


if __name__ == '__main__':
    unittest.main()
