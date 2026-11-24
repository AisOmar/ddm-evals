import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


d=module('qwen_diagnostic_tests','72_qwen_delivery_diagnostic.py')
report=module('qwen_diagnostic_report_tests','73_qwen_diagnostic_report.py')


class QwenDiagnosticTests(unittest.TestCase):
    def plan(self):
        return d.plan(dict(pricing=dict(prompt='.00000014',completion='.0000004'),
                           max_completion_tokens=16400,context_length=20000))

    def test_only_named_control_differs_within_question_repeat(self):
        trials=self.plan()
        self.assertEqual(len({t['sample_id'] for t in trials}),18)
        for item in ('D01','D02','D03'):
            for repeat in (1,2):
                group={t['mode']:t for t in trials if t['item_id']==item and t['repeat']==repeat}
                default=group['default']['request']
                disabled=copy.deepcopy(group['reasoning_disabled']['request'])
                self.assertEqual(disabled.pop('reasoning'),{'enabled':False})
                self.assertEqual(disabled,default)
                soft=copy.deepcopy(group['soft_no_think']['request'])
                self.assertTrue(soft['messages'][0]['content'].endswith('\n\n/no_think'))
                soft['messages'][0]['content']=soft['messages'][0]['content'][:-len('\n\n/no_think')]
                self.assertEqual(soft,default)

    def test_hidden_answer_is_not_a_visible_success(self):
        trial=self.plan()[0]
        raw=dict(choices=[dict(finish_reason='stop',message=dict(content=None,reasoning='A<|im_end|>'))],
                 usage=dict(completion_tokens=20,completion_tokens_details={'reasoning_tokens':12}))
        final=dict(outcome=dict(status='incomplete',choice=None,strict_format=None),
                   recorded_cost_usd='.0001',missing_cost_metadata=False,continue_permitted=True)
        row=report.observations(trial,raw,final)
        self.assertFalse(row['visible_recognized'])
        self.assertTrue(row['content_empty'])
        self.assertTrue(row['leaked_im_end_in_reasoning'])

    def test_partial_cohort_cannot_qualify_a_control(self):
        rows=[dict(mode='reasoning_disabled',visible_recognized=True,strict_format=True,
                   content_empty=False,reasoning_characters=0,status='answered',
                   recorded_cost_usd='.0001',missing_cost_metadata=False)]*5
        summary=report.summarize(rows,False)
        self.assertFalse(any(x['candidate_for_new_qualification'] for x in summary['modes']))

    def test_bad_capacity_is_rejected_before_preparation(self):
        with self.assertRaisesRegex(ValueError,'capacity'):
            d.plan(dict(pricing=dict(prompt='0',completion='0'),max_completion_tokens=100,context_length=20000))
