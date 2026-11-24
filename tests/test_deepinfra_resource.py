import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


q=module('deepinfra_resource_tests','77_deepinfra_resource_collect.py')
report=module('deepinfra_resource_report_tests','78_deepinfra_resource_report.py')


class DeepInfraResourceTests(unittest.TestCase):
    def test_review_locks_and_keys_match_all_eight_new_probes(self):
        q.configure()
        rows=q.review_gate()
        self.assertEqual(len(rows),8)
        self.assertEqual(len({r['family'] for r in rows}),8)

    def test_exact_routes_and_single_question_requests(self):
        q.configure();rows=q.review_gate()
        endpoints={name:dict(pricing=dict(prompt='.0000001',completion='.0000004'),
                            max_completion_tokens=4096,context_length=32768) for name in q.ROUTES}
        trials=q.plan(rows,endpoints)
        self.assertEqual(len(trials),16)
        for trial in trials:
            provider,tag,quant=q.ROUTES[trial['model']]
            req=trial['request']
            self.assertEqual(req['provider']['only'],[tag])
            self.assertEqual(req['provider']['quantizations'],[quant])
            self.assertFalse(req['provider']['allow_fallbacks'])
            self.assertNotIn('reasoning',req)
            self.assertNotIn('/no_think',req['messages'][0]['content'])
            self.assertNotIn(trial['item_id'],req['messages'][0]['content'])

    def test_gate_ignores_factual_correctness_but_requires_all_deliveries(self):
        rows=[dict(status='answered',continue_permitted=True,correct=False,strict_format=False) for _ in range(16)]
        self.assertTrue(report.gate_passed(rows))
        self.assertFalse(report.gate_passed(rows[:-1]))
        rows[-1]['status']='ambiguous_format'
        self.assertFalse(report.gate_passed(rows))
        rows[-1]['status']='answered';rows[-1]['continue_permitted']=False
        self.assertFalse(report.gate_passed(rows))
