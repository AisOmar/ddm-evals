"""Exact reviewer arithmetic and rejection of executable expressions."""
from fractions import Fraction
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tool_review_test', ROOT/'scripts/88_selective_reliance_tool_review.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ExactToolTests(unittest.TestCase):
    def test_fractional_conditioning_retains_exact_denominator(self):
        self.assertEqual(r.exact('((1/5)*(3/4)*(1/3))/((1/5)*(3/4)*(1/3)+(4/5)*(1/4)*(2/3))'), Fraction(3, 11))
        self.assertEqual(r.exact('((1/4)*1)/((1/4)*1+(3/4)*(2/3))'), Fraction(1, 3))

    def test_expected_payoff_includes_loss_and_guaranteed_fee(self):
        self.assertEqual(r.exact('((3/4)*12-(1/4)*6+2)/2-1'), Fraction(15, 4))

    def test_code_names_calls_attributes_and_booleans_are_rejected(self):
        for expression in ('__import__("os")', 'open(".env")', '(1).__class__',
                           '[x for x in range(10)]', '2**1000000', 'True+1', '0.1+0.2', 'a+1'):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                r.exact(expression)

    def test_oversize_and_zero_division_fail_without_result(self):
        with self.assertRaises(ValueError): r.exact('1+'*400+'1')
        with self.assertRaises(ValueError): r.exact('1000001')
        with self.assertRaises(ZeroDivisionError): r.exact('1/(2-2)')


if __name__ == '__main__': unittest.main()
