"""Offline integrity and safe-computation checks for the development packet."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/research_directions/open_dataset_packet_20261020'
spec = importlib.util.spec_from_file_location('open_packet_checks', ROOT / 'scripts/47_check_open_packet.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class OpenDatasetPacketTests(unittest.TestCase):
    def test_arithmetic_and_boolean_precedence(self):
        self.assertEqual(checks.expression_value('(-7 * -9 + 8 * -3) * (5 + -7 - 4 * -5)'), 702)
        self.assertTrue(checks.expression_value('not False or False', boolean=True))
        self.assertFalse(checks.expression_value('False or True and False', boolean=True))

    def test_expression_whitelist_rejects_code_and_unbounded_operators(self):
        for text in ['f()', '__import__("os")', '2**1000000', '[x for x in []]', 'True + 1', '1 / 0', '10'*1100]:
            with self.subTest(text=text[:40]), self.assertRaises((ValueError, SyntaxError)):
                checks.expression_value(text)
        with self.assertRaises(ValueError):
            checks.expression_value('not 1', boolean=True)

    def test_bracket_matching_is_shortest_and_rejects_invalid_prefixes(self):
        self.assertEqual(checks.bracket_completion('< [ ('), ') ] >')
        self.assertEqual(checks.bracket_completion('([])'), '')
        for text in ['([)]', '>', '< import']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                checks.bracket_completion(text)

    def test_canonical_answers_do_not_confuse_format_with_value(self):
        self.assertEqual(checks.canonical('31.00'), checks.canonical('31'))
        self.assertEqual(checks.canonical('> >'), checks.canonical('>>'))
        self.assertNotEqual(checks.canonical('> >'), checks.canonical('} >'))
        stem, options = checks.native_options('Question\nOptions:\n(A) first\n(B) second')
        self.assertEqual(stem, 'Question')
        self.assertEqual(options, {'A': 'first', 'B': 'second'})

    def test_all_twenty_derivations_agree_without_loading_official_keys(self):
        questions = [json.loads(s) for s in (BASE / 'masked_source_questions.jsonl').read_text().splitlines()]
        derived = checks.cross_checks(questions)
        reviewed = {x['review_id']: x for x in json.loads((BASE / 'initial_analyst_review.json').read_text())['items']}
        self.assertEqual(len(derived), 20)
        for rid, result in derived.items():
            self.assertEqual(checks.canonical(result['answer']), checks.canonical(reviewed[rid]['analyst_answer']))

    def test_prompt_conditions_change_only_instruction_or_suggestion(self):
        items = {x['review_id']: x for x in json.loads((BASE / 'v2/binary_items.json').read_text())}
        prompts = [json.loads(s) for s in (BASE / 'v2/draft_prompts.jsonl').read_text().splitlines()]
        templates = json.loads((BASE / 'prompt_templates.json').read_text())
        self.assertEqual(len(prompts), 120)
        self.assertEqual(len({p['draft_id'] for p in prompts}), 120)
        for p in prompts:
            item = items[p['review_id']]
            base = templates['instructions'][p['instruction_condition']] + '\n\n' + item['question']
            base += '\n\nA. ' + item['options'][0] + '\nB. ' + item['options'][1]
            if p['advice_condition'] != 'none':
                letter = item['correct_letter'] if p['advice_condition'] == 'correct' else item['wrong_letter']
                base += '\n\n' + templates['advice_template'].format(letter=letter)
            self.assertEqual(p['messages'], [{'role': 'user', 'content': base}])
            self.assertEqual(p['expected_answer'], item['correct_letter'])
            self.assertFalse(p['dispatch_ready'])
        for prefix in ['G', 'B']:
            self.assertEqual(sum(x['correct_letter'] == 'A' for rid, x in items.items() if rid.startswith(prefix)), 5)

    def test_masked_review_packet_has_no_answer_or_advice_metadata(self):
        rows = [json.loads(s) for s in (BASE / 'v2/reviewer_packet/questions.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 20)
        for row in rows:
            self.assertEqual(set(row), {'review_id', 'dataset', 'task', 'version', 'question', 'options'})
            self.assertEqual(len(set(row['options'])), 2)
            self.assertNotIn('Ask for the total number', row['question'])
        summary = json.loads((BASE / 'v2/packet_summary.json').read_text())
        self.assertFalse(summary['collection_ready'])
        self.assertFalse(summary['independent_review_complete'])
        self.assertEqual(summary['n_model_calls_launched'], 0)


if __name__ == '__main__':
    unittest.main()
