"""Synthetic endpoint/selection/missingness checks; never inspect live treatment effects."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("trust_analysis", ROOT / "scripts/33_trust_analysis.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def synthetic():
    rows = []
    qids = [f"q{i:03d}" for i in range(100)]
    for i, qid in enumerate(qids):
        for model, word, key, rate in analysis.GROUPS:
            threshold = (95 if rate == .55 else 97) if key else (80 if rate == .55 else 70)
            rows.append(dict(qid=qid, model=model, wording=word, key_correct=key, rate=rate,
                             rep=0, correct=float(i < threshold)))
        for model in analysis.MODELS:
            for rep in [0, 1]:
                rows.append(dict(qid=qid, model=model, wording="control", key_correct=None,
                                 rate=None, rep=rep, correct=float(i < 90)))
    return pd.DataFrame(rows), qids


class TrustAnalysisTests(unittest.TestCase):
    def test_factorial_scoring_and_helpful_harmful_signs(self):
        d, qids = synthetic()
        result = analysis.estimate(d, qids, draws=1000)
        self.assertTrue(result["confirmatory_cohort_passed"])
        self.assertEqual(result["n_primary_questions"], 100)
        np.testing.assert_allclose([r["estimate"] for r in result["primary"]], -.04)
        np.testing.assert_allclose([r["estimate"] for r in result["pairs"]], 0, atol=1e-14)
        expected = [.05, .10, .07, .20] * 3
        np.testing.assert_allclose([r["estimate"] for r in result["helpful_harmful"]], expected, atol=1e-14)
        np.testing.assert_allclose([r["estimate"] for r in result["wordings"]], -.04)

    def test_nonanswers_change_cohorts_and_identification_bounds(self):
        d, qids = synthetic()
        hinted = (d.qid == qids[0]) & (d.model == "R1") & (d.wording == "frequency") & (d.key_correct == True) & (d.rate == .95)
        d.loc[hinted, "correct"] = np.nan
        control = (d.qid == qids[1]) & (d.model == "Qwen3") & (d.wording == "control") & (d.rep == 0)
        d.loc[control, "correct"] = np.nan
        result = analysis.estimate(d, qids, draws=1000)
        self.assertEqual(result["n_primary_questions"], 99)
        self.assertEqual(result["n_helpful_harmful_questions"], 98)
        self.assertEqual(result["within_model_complete"][0]["n_questions"], 99)
        self.assertEqual(result["within_model_complete"][1]["n_questions"], 100)
        r1 = result["worst_case_missing_bounds"][0]
        self.assertAlmostEqual(r1["hi"] - r1["lo"], .0025)
        self.assertLessEqual(r1["lo"], -.04)
        self.assertGreaterEqual(r1["hi"] + 1e-14, -.04)

    def test_low_complete_cohort_is_inconclusive(self):
        d, qids = synthetic()
        d.loc[d.qid.isin(qids[:21]) & (d.model == "R1") & (d.wording == "frequency"), "correct"] = np.nan
        result = analysis.estimate(d, qids, draws=1000)
        self.assertEqual(result["n_primary_questions"], 79)
        self.assertFalse(result["confirmatory_cohort_passed"])

    def test_incomplete_collection_blocks_before_any_inference_or_outputs(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(analysis, "OUT", Path(folder)), patch.object(analysis.collect, "require_no_batch"), patch.object(analysis.collect, "manifest", return_value=dict(trials=[dict(sample_id="missing")])), patch.object(analysis.collect, "index_attempts", return_value={"missing": []}), patch.object(analysis.collect, "delivered", return_value=(None, None)):
            with self.assertRaisesRegex(ValueError, "Incomplete collection"):
                analysis.read_completed()
            self.assertFalse(list(Path(folder).iterdir()))


if __name__ == "__main__":
    unittest.main()
