"""Schema interpretation cannot override substantive uncertainty or blocker text."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('schema_test', ROOT/'scripts/91_selective_reliance_review_schema.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class SchemaInterpretationTests(unittest.TestCase):
    def item(self):
        return dict(disposition='CONFIDENT', item_id='F001', unique_supported_answer=True,
                    must_fix_before_execution=False, concerns='None. Assumptions explicit.')

    def test_confidence_without_uniqueness_or_with_blockers_fails(self):
        for field, value in [('unique_supported_answer', False), ('must_fix_before_execution', True),
                             ('concerns', 'Ambiguous selection protocol')]:
            item = self.item(); item[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                s.normalize(dict(items=[item], overall_execution_blockers=[]))

    def test_only_exact_affirmative_blocker_text_is_interpreted(self):
        result, changes = s.normalize(dict(items=[self.item()], overall_execution_blockers=s.NO_BLOCKERS_PROSE))
        self.assertEqual(result['overall_execution_blockers'], [])
        self.assertEqual(result['items'][0]['disposition'], 'retain')
        self.assertEqual(len(changes), 2)
        with self.assertRaises(ValueError):
            s.normalize(dict(items=[self.item()], overall_execution_blockers=s.NO_BLOCKERS_PROSE+' But one key is uncertain.'))


if __name__ == '__main__': unittest.main()
