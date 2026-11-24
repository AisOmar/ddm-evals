import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


w = module('wording_test_collector', '70_wording_collect.py')
analysis = module('wording_test_analysis', '69_wording_analysis.py')


class WordingPilotTests(unittest.TestCase):
    def test_independent_review_locks_keys_and_equivalence(self):
        self.assertEqual(len(w.review_gate()), 32)

    def test_all_matched_conditions_reverse_together(self):
        rows = w.review_gate()
        endpoints = {name:dict(pricing=dict(prompt='0.0000001',completion='0.0000004'),
                              max_completion_tokens=4096,context_length=32768) for name in w.p.MODELS}
        trials = w.plan(rows,endpoints,'pilot')
        self.assertEqual(len(trials),288)
        for problem in {t['item_id'] for t in trials}:
            group = [t for t in trials if t['item_id']==problem]
            first = {t['correct_letter'] for t in group if t['repeat']==1}
            second = {t['correct_letter'] for t in group if t['repeat']==2}
            self.assertEqual(len(first),1)
            self.assertEqual(len(second),1)
            self.assertNotEqual(first,second)
        for trial in trials:
            text = trial['request']['messages'][0]['content']
            self.assertNotIn(trial['item_id'],text)
            self.assertEqual('A suggested answer is' in text,trial['advice']!='none')

    def test_incomplete_and_duplicate_scoring_is_blocked(self):
        with self.assertRaisesRegex(ValueError,'288'):
            analysis.summarize([])
        records = self.synthetic()
        records[-1] = copy.deepcopy(records[0])
        with self.assertRaisesRegex(ValueError,'288'):
            analysis.summarize(records)

    def synthetic(self):
        records = []
        for i in range(1,9):
            for model in w.p.MODELS:
                for version in analysis.VERSIONS:
                    for advice in analysis.ADVICE:
                        for repeat in (1,2):
                            correct = version != 'trap' and advice != 'wrong'
                            records.append(dict(item_id=f'W{i:02}',model=model,version=version,advice=advice,
                                repeat=repeat,outcome=dict(status='answered',correct=correct,strict_format=True)))
        return records

    def test_paired_contrast_signs_follow_prespecified_definitions(self):
        result = analysis.summarize(self.synthetic())
        for row in result['contrasts']:
            expected = dict(trap_minus_plain_no_advice=-1,neutral_minus_plain_no_advice=0,
                            trap_minus_plain_wrong_advice_harm=-1,
                            trap_minus_plain_correct_advice_benefit=0)[row['contrast']]
            self.assertEqual(row['estimate'],expected)

    def test_nonanswer_yield_and_conditional_accuracy_stay_distinct(self):
        records = self.synthetic()
        for row in records:
            if row['version']=='trap':
                row['outcome'] = dict(status='censored',correct=None,strict_format=None)
        result = analysis.summarize(records)
        for row in result['cells']:
            if row['version']=='trap':
                self.assertEqual(row['correct_planned'],0)
                self.assertIsNone(row['correct_recognized'])
                self.assertEqual(row['outcomes'],{'censored':16})

    def test_unauthorized_dispatch_does_not_read_or_create_a_manifest(self):
        w.configure('resource')
        with patch.object(w.r,'manifest',side_effect=AssertionError('must not load')):
            with self.assertRaisesRegex(ValueError,'authorized'):
                w.r.prepare(False)

    def test_reasoning_channel_without_visible_answer_is_incomplete(self):
        trial = dict(expected_provider='Tenstorrent',options={'A':'7.2 km/h','B':'7.5 km/h'},
            correct_letter='A',request=dict(model='qwen/qwen3-32b',max_tokens=2048))
        response = dict(provider='Tenstorrent',model='qwen/qwen3-32b',
            choices=[dict(finish_reason='stop',message=dict(content=None,reasoning='The answer is A.'))],
            usage=dict(prompt_tokens=88,completion_tokens=279,cost=.00012392))
        outcome = w.a.result(trial,response,200)
        self.assertEqual(outcome['status'],'incomplete')
        self.assertIsNone(outcome['correct'])

    def test_resource_nonanswer_blocks_next_preparation(self):
        w.configure('resource')
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            w.p.save(out/'finished/trial.json',dict(continue_permitted=True,outcome={'status':'incomplete'}))
            with patch.object(w.r,'OUT',out),patch.object(w.a,'no_other_collection'),\
                 patch.object(w.r,'manifest',return_value=dict(preflight_started_at=w.p.now())),\
                 patch.object(w.c,'history',return_value=[dict(sample_id='trial',prepared_at=w.p.now())]):
                with self.assertRaisesRegex(ValueError,'Resource gate failed'):
                    w.r.prepare(True)
