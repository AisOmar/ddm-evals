"""Requalification changes only output budget and rejects insufficient capacity."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('focused_4096_test', ROOT/'scripts/92_selective_reliance_4096.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class Qualification4096Tests(unittest.TestCase):
    def fixture(self):
        rows = r.l.c.load(r.l.PACKET/'author/packet_with_solutions.json')
        endpoints = {name: r.l.a.endpoint(r.l.c.load(r.PREVIOUS/'resource'/(name+'_endpoints.json')), route[0], route[2])
                     for name, route in r.l.ROUTES.items()}
        return rows, endpoints

    def test_question_condition_order_and_parameters_stay_fixed(self):
        rows, endpoints = self.fixture()
        original = r.ORIGINAL_PLAN(rows, endpoints, 'resource')
        updated = r.plan(rows, endpoints, 'resource')
        for old, new in zip(original, updated):
            self.assertEqual(old['sample_id'], new['sample_id'])
            self.assertEqual(old['request']['max_tokens'], 2048)
            self.assertEqual(new['request']['max_tokens'], 4096)
            old['request']['max_tokens'] = 4096
            self.assertEqual(old, new)

    def test_capacity_checks_use_new_cap(self):
        rows, endpoints = self.fixture()
        endpoints = copy.deepcopy(endpoints)
        endpoints['Qwen3']['max_completion_tokens'] = 3000
        with self.assertRaisesRegex(ValueError, 'qualified cap'):
            r.plan(rows, endpoints, 'resource')


if __name__ == '__main__': unittest.main()
