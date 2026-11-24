"""Safety checks for the separate budget-bounded pilot, using synthetic responses."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('reviewed_pilot', ROOT/'scripts/41_reviewed_pilot.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ReviewedPilotTests(unittest.TestCase):
    def items(self):
        return [dict(candidate_id=f'P{i:02d}', question='Question?', options=['right', 'wrong'],
                     correct_index=0, validation_status='accepted') for i in range(1,21)]

    def test_design_and_advice_remain_matched(self):
        rows=p.plan(self.items())
        self.assertEqual(len(rows),240)
        self.assertEqual(rows,p.plan(self.items()))
        self.assertEqual(len({r['sample_id'] for r in rows}),240)
        for i in range(1,21):
            group=[r for r in rows if r['candidate_id']==f'P{i:02d}']
            self.assertEqual(len(group),12)
            self.assertEqual(len({r['correct_letter'] for r in group}),1)
            for r in group:
                self.assertEqual(r['request']['provider'],{'order':['DeepInfra'],'allow_fallbacks':False})
                if r['advice']=='wrong': self.assertNotEqual(r['correct_letter'],r['advice_letter'])
                if r['advice']=='correct': self.assertEqual(r['correct_letter'],r['advice_letter'])
                if r['advice']=='none': self.assertNotIn('Answer key:',r['request']['messages'][0]['content'])
        self.assertEqual(sum(r['correct_letter']=='A' for r in rows),120)

    def test_unvalidated_inputs_blocked(self):
        items=self.items(); items[0]['validation_status']='pending'
        with self.assertRaises(ValueError): p.plan(items)
        with self.assertRaises(ValueError): p.plan(self.items()[:-1])

    def test_provider_drift_and_invalid_delivery_rejected(self):
        trial=p.plan(self.items())[0]
        response=dict(provider='Elsewhere',model=trial['request']['model'],
                      choices=[dict(message={'content':'A'},finish_reason='stop')],usage={'completion_tokens':1})
        self.assertEqual(p.classify(trial,response)[0],'provider_or_model_mismatch')
        response['provider']='DeepInfra';response['usage']={}
        self.assertEqual(p.classify(trial,response)[0],'invalid_response')
        response['usage']={'completion_tokens':4097}
        self.assertEqual(p.classify(trial,response)[0],'output_cap_violation')

    def test_refusal_and_censoring_not_scored_as_answers(self):
        trial=p.plan(self.items())[0]
        response=dict(provider='DeepInfra',model=trial['request']['model'],
                      choices=[dict(message={'content':"I cannot help with that.\nA"},finish_reason='stop')],
                      usage={'completion_tokens':12})
        self.assertEqual(p.classify(trial,response),('refusal',None))
        response['choices']=[dict(message={'content':''},finish_reason='length')]
        self.assertEqual(p.classify(trial,response),('censored',None))


if __name__=='__main__': unittest.main()
