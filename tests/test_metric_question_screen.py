"""Integrity checks for a screen that must not silently approve questions."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('question_screen', ROOT / 'scripts/44_metric_question_screen.py')
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


def item(rid, question):
    return dict(review_id=rid, question=question,
                original_options=['a', 'b', 'c', 'd'], retained_options=['a', 'b'])


class ScreeningIntegrityTests(unittest.TestCase):
    def test_wasm_body_presence_changes_missing_body_flag(self):
        header = 'What number from this assembly function?\nfunc.o: file format wasm'
        rows, _ = screen.screen([item('empty', header), item('body', header + '\n0: i32.const 7')])
        self.assertIn('missing_wasm_function_body', rows[0]['structural_flags'])
        self.assertNotIn('missing_wasm_function_body', rows[1]['structural_flags'])
        self.assertFalse(any(r['eligible_for_collection'] for r in rows))

    def test_packet_families_follow_bytes_instead_of_hex_formatting(self):
        rows, groups = screen.screen([item('A', 'one Packet bytes: 0a0b'),
                                      item('B', 'different field Packet bytes: 0a 0b'),
                                      item('C', 'other Packet bytes: 0a 0c')])
        self.assertEqual(sorted(map(len, groups.values())), [1, 2])
        self.assertEqual(rows[0]['packet_content_family'], rows[1]['packet_content_family'])
        self.assertNotEqual(rows[0]['packet_content_family'], rows[2]['packet_content_family'])
        self.assertEqual(rows[0]['semantic_family_review'], 'pending')

    def test_invalid_packet_is_reported_without_claiming_an_answer(self):
        rows, groups = screen.screen([item('bad', 'Packet bytes: not hex')])
        self.assertIn('invalid_packet_hex', rows[0]['structural_flags'])
        self.assertEqual(groups, {})
        self.assertEqual(rows[0]['answer_review'], 'not_adjudicated')

    def test_label_flag_does_not_turn_a_visible_number_into_a_verified_key(self):
        rows, _ = screen.screen([item('leak', 'packet->register_171_(uint16)->regnum16')])
        self.assertIn('requested_number_visible_in_field_label', rows[0]['structural_flags'])
        self.assertFalse(rows[0]['structural_details']['label_number_is_retained_option'])
        self.assertNotIn('supported_retained_indexes', rows[0])

    def test_invalid_retained_options_fail_instead_of_becoming_eligible(self):
        bad = item('bad', 'question')
        bad['retained_options'] = ['a', 'not an original option']
        with self.assertRaises(AssertionError):
            screen.screen([bad])


if __name__ == '__main__':
    unittest.main()
