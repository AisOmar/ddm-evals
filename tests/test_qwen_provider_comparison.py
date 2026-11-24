import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


q=module('provider_test','74_qwen_provider_comparison.py')
report=module('provider_report_test','75_qwen_provider_report.py')


class QwenProviderTests(unittest.TestCase):
    def trials(self):
        endpoints={name:dict(pricing=dict(prompt='.0000001',completion='.0000004'),
                            context_length=40960,max_completion_tokens=16384) for name in q.ROUTES}
        return q.plan(endpoints)

    def test_payloads_match_except_provider_route(self):
        trials=self.trials()
        self.assertEqual(len({x['sample_id'] for x in trials}),12)
        for item in ('P01','P02','P03'):
            for repeat in (1,2):
                pair=[x for x in trials if x['item_id']==item and x['repeat']==repeat]
                first=copy.deepcopy(pair[0]['request']);second=copy.deepcopy(pair[1]['request'])
                route1=first.pop('provider');route2=second.pop('provider')
                self.assertEqual(first,second)
                self.assertNotEqual(route1['only'],route2['only'])
                self.assertEqual(route1['quantizations'],['fp8'])
                self.assertEqual(route2['quantizations'],['fp8'])
                self.assertFalse(route1['allow_fallbacks'])
                self.assertNotIn('reasoning',first)
                self.assertNotIn('/no_think',first['messages'][0]['content'])

    def test_option_reversal_is_shared_by_both_routes(self):
        trials=self.trials()
        for item in ('P01','P02','P03'):
            a={t['correct_letter'] for t in trials if t['item_id']==item and t['repeat']==1}
            b={t['correct_letter'] for t in trials if t['item_id']==item and t['repeat']==2}
            self.assertEqual(len(a),1);self.assertEqual(len(b),1);self.assertNotEqual(a,b)

    def test_incomplete_comparison_never_qualifies(self):
        rows=[dict(mode='DeepInfra',visible_recognized=True,strict_format=True,
                   content_empty=False,status='answered',recorded_cost_usd='.0001',missing_cost_metadata=False)]*6
        s=report.summarize(rows,False)
        self.assertFalse(any(x['candidate_for_new_resource_gate'] for x in s['providers']))
