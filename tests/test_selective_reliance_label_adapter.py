"""A formatting adapter must not choose between competing final values."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('label_adapter_test', ROOT/'scripts/90_selective_reliance_label_adapter.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class LabelAdapterTests(unittest.TestCase):
    def test_final_suffix_preserves_value_and_provenance(self):
        final, mapping = a.canonical_results(['F001'], {'F001_final': '1/3', 'F001_intermediate': '3/4'})
        self.assertEqual(final, {'F001': '1/3'})
        self.assertEqual(mapping, {'F001': 'F001_final'})

    def test_competing_labels_fail_even_when_values_agree(self):
        with self.assertRaises(ValueError):
            a.canonical_results(['F001'], {'F001': '1/3', 'F001_final': '1/3'})

    def test_partial_or_arbitrary_suffix_is_not_a_final_label(self):
        for label in ('F001_result', 'F0010_final', 'F001_final_extra'):
            with self.subTest(label=label), self.assertRaises(ValueError):
                a.canonical_results(['F001'], {label: '1/3'})


if __name__ == '__main__': unittest.main()
