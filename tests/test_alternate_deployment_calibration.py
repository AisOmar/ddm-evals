"""New deployments use a complete new cohort, with fixed questions and budgets."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('alternate_pair_test',ROOT/'scripts/100_alternate_deployment_calibration.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class AlternateDeploymentTests(unittest.TestCase):
    def test_routing_and_full_calibration_size(self):
        a.configure('calibration')
        endpoints={name:dict(pricing=dict(prompt='.00000014' if name=='Qwen3' else '.00000003',completion='.0000004' if name=='Qwen3' else '.000000187'),max_completion_tokens=16384,context_length=40960) for name in a.ROUTES}
        rows=a.plan('calibration',endpoints)
        self.assertEqual(len(rows),48)
        self.assertEqual(len({r['sample_id'] for r in rows}),48)
        self.assertEqual(sum(r['model']=='Qwen3' for r in rows),24)
        for row in rows:
            provider,tag,quant=a.ROUTES[row['model']]
            self.assertEqual(row['expected_provider'],provider)
            self.assertEqual(row['request']['provider']['only'],[tag])
            self.assertEqual(row['request']['provider']['quantizations'],[quant])
            self.assertEqual(row['request']['max_tokens'],4096)
            self.assertTrue(row['request']['stream'])


if __name__=='__main__':unittest.main()
