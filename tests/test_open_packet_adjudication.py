"""Fail-closed review reconciliation and family selection checks."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/research_directions/open_dataset_packet_20261020'
spec = importlib.util.spec_from_file_location('open_adjudication', ROOT / 'scripts/49_adjudicate_open_packet.py')
adjudication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adjudication)


class OpenPacketAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = json.loads((BASE / 'v2/binary_items.json').read_text())
        cls.review = json.loads((BASE / 'fresh_ai_review/initial_review.json').read_text())

    def test_missing_or_duplicate_reviews_do_not_pass(self):
        judgments = self.review['judgments']
        for bad in [judgments[:-1], judgments + [judgments[0]]]:
            with self.assertRaises(ValueError):
                adjudication.validate_judgments(self.items, bad)

    def test_answer_disagreement_or_overlap_needs_adjudication(self):
        for change in [{'supported_letter': self.items[0]['wrong_letter']},
                       {'answer_overlap': True}, {'exactly_one_supported': False},
                       {'repair_proposal': 'Change wording'}, {'alternative_analysis': {'A': 'Only A checked'}}]:
            altered = copy.deepcopy(self.review['judgments'])
            altered[0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                adjudication.validate_judgments(self.items, altered)

    def test_answer_agreement_cannot_hide_different_question_or_options(self):
        for change in [{'question_sha256': '0'*64}, {'options': list(reversed(self.items[0]['options']))}]:
            altered = copy.deepcopy(self.review['judgments'])
            altered[0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                adjudication.validate_judgments(self.items, altered)

    def test_families_partition_items_and_selection_ignores_input_order(self):
        families = self.review['family_assignment']['families']
        ids = {x['review_id'] for x in self.items}
        selected = adjudication.representatives(families, ids)
        reversed_groups = {k: list(reversed(v)) for k,v in reversed(list(families.items()))}
        self.assertEqual(selected, adjudication.representatives(reversed_groups, ids))
        self.assertEqual(len(selected), 16)
        broken = copy.deepcopy(families)
        broken['duplicate'] = [self.items[0]['review_id']]
        with self.assertRaises(ValueError):
            adjudication.representatives(broken, ids)

    def test_draft_has_all_conditions_and_preserves_original_visible_prompts(self):
        base_prompts = {p['draft_id']:p for p in map(json.loads, (BASE / 'v2/draft_prompts.jsonl').read_text().splitlines())}
        draft = list(map(json.loads, (BASE / 'review_followup/feasibility_draft_prompts.jsonl').read_text().splitlines()))
        self.assertEqual(len(draft), 192)
        self.assertEqual(len({p['draft_id'] for p in draft}), 192)
        ids = {p['review_id'] for p in draft}
        self.assertEqual(len(ids), 16)
        for rid in ids:
            rows = [p for p in draft if p['review_id']==rid]
            self.assertEqual(len(rows), 12)
            self.assertEqual({(p['candidate_model']['label'],p['instruction_condition'],p['advice_condition']) for p in rows},
                             {(m,i,a) for m in ['Qwen3','gpt-oss'] for i in ['ordinary','explicit'] for a in ['none','correct','incorrect']})
        for row in draft:
            old_id = '__'.join([row['review_id'],row['instruction_condition'],row['advice_condition']])
            self.assertEqual(row['messages'],base_prompts[old_id]['messages'])
            self.assertEqual(row['expected_answer'],base_prompts[old_id]['expected_answer'])
            self.assertFalse(row['dispatch_ready'])
            self.assertFalse(row['collection_authorized'])


if __name__ == '__main__':
    unittest.main()
