import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('direct_baseline',Path(__file__).resolve().parents[1]/'scripts/101_direct_claude_baseline.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class DirectBaselineTests(unittest.TestCase):
    def setUp(self):
        self.body=dict(type='message',model=m.MODELS['Haiku'],usage=dict(input_tokens=200,output_tokens=8),stop_reason='end_turn',content=[dict(type='text',text='{"answer":"B"}')])

    def test_correct_and_wrong_are_recognized(self):
        self.assertTrue(m.outcome(self.body,'Haiku','B')['correct'])
        self.assertFalse(m.outcome(self.body,'Haiku','A')['correct'])

    def test_reasoning_is_never_used(self):
        self.body['content']=[dict(type='thinking',thinking='The correct answer is B')]
        self.assertIsNone(m.outcome(self.body,'Haiku','B')['correct'])

    def test_extra_fields_and_prose_unknown(self):
        for text in ['B','{"answer":"B","explanation":"proof"}','{"answer":"C"}']:
            self.body['content'][0]['text']=text
            self.assertIsNone(m.outcome(self.body,'Haiku','B')['correct'])

    def test_truncated_answer_unknown(self):
        self.body['stop_reason']='max_tokens'
        self.assertIsNone(m.outcome(self.body,'Haiku','B')['correct'])

    def test_identity_and_budget_fail_closed(self):
        for change in [dict(model='wrong'),dict(usage=dict(input_tokens=4001,output_tokens=8)),dict(usage=dict(input_tokens=200,output_tokens=129)),dict(usage=dict(input_tokens=200,output_tokens=8,cache_read_input_tokens=1))]:
            body=copy.deepcopy(self.body);body.update(change)
            with self.assertRaises(ValueError):m.outcome(body,'Haiku','B')

    def test_full_reservation_below_cumulative_ceiling(self):
        self.assertLess(m.PRIOR+30*sum(map(m.reserve,m.MODELS)),1)

if __name__=='__main__':unittest.main()
