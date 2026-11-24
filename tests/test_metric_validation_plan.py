"""Meaningful scoring tests for a proposed selective-reliance metric."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('metric_plan',ROOT/'scripts/42_metric_validation_plan.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class MetricTests(unittest.TestCase):
    def test_ignoring_all_advice_cannot_pass_selective_reliance(self):
        y=np.ones((200,2,2,7,2))
        out=p.evaluate(y)
        self.assertFalse(out['model_claim'].any())
        np.testing.assert_array_equal(out['mean'],0)
        self.assertTrue((out['upper']>out['lower']).all())

    def test_baseline_adjustment_catches_changed_question_answering(self):
        y=np.full((2,2,2,7,2),.8)
        y[:,:,0,2::2,:]=.5
        y[:,:,1,2::2,:]=.8
        y[:,:,1,0,:]=1.
        x=p.scores(y)['primary']
        np.testing.assert_allclose(x[:,:,0],.1)
        np.testing.assert_allclose(x[:,:,2],.2)
        # More baseline skill does not itself constitute correct-advice benefit.
        np.testing.assert_allclose(x[:,:,3],-.2)

    def test_source_and_repeat_averaging_preserves_question_units(self):
        y=np.zeros((10,2,2,7,2));y[:,:,1,2,0]=1
        out=p.scores(y)
        self.assertEqual(out['primary'].shape,(10,2,4))
        np.testing.assert_allclose(out['primary'][:,:,0],1/6)
        np.testing.assert_allclose(out['g_source'][:,:,0],.5)

    def test_invalid_or_missing_data_rejected(self):
        for y in [np.zeros((10,2,2,6,2)),np.full((10,2,2,7,2),np.nan)]:
            with self.assertRaises(ValueError):p.scores(y)
        with self.assertRaises(ValueError):p.evaluate(np.ones((20,2,2,7,2)))

    def test_null_generator_calibrates_declared_target(self):
        s=dict(gain=[0.,0.,0.],correct_change=0.,baseline_change=0.,sigma=1.)
        y=p.synthetic_items(s,n=6000,repeats=2,seed=34)
        x=p.scores(y)['primary'].mean(axis=0)
        np.testing.assert_allclose(x[:,:3],0,atol=.035)
        np.testing.assert_allclose(x[:,3],.10,atol=.035)


if __name__=='__main__':unittest.main()
