"""Offline design and statistical checks for the planned trust experiment."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trust", ROOT / "scripts/30_trust_design.py")
trust = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trust)


class TrustPlanningTests(unittest.TestCase):
    def test_factorial_prompts_preserve_question_and_key_truth(self):
        qs = [dict(qid=f"fresh-{i}", question=f"Question {i}?", correct="right text",
                   distractor="wrong text") for i in range(4)]
        trials = trust.make_trials(qs)
        self.assertEqual(len(trials), 120)
        self.assertEqual(trials, trust.make_trials(qs))
        targets = {}
        for q in qs:
            qt = [x for x in trials if x["qid"] == q["qid"]]
            self.assertEqual(len({x["target"] for x in qt}), 1)
            targets[q["qid"]] = qt[0]["target"]
            for model in trust.MODELS:
                mt = [x for x in qt if x["model"] == model]
                self.assertEqual(sum(x["wording"] == "control" for x in mt), 2)
                self.assertEqual(len({(x["wording"], x["key_correct"], x["rate"])
                                      for x in mt if x["wording"] != "control"}), 8)
            endings = set()
            for x in qt:
                prompt = x["request"]["messages"][0]["content"]
                self.assertIn(f"{x['target']}) right text", prompt)
                endings.add(prompt[prompt.index(q["question"]):])
                if x["wording"] == "control":
                    self.assertNotIn("<question-metadata>", prompt)
                    self.assertIsNone(x["key_letter"])
                else:
                    self.assertEqual(x["key_letter"] == x["target"], x["key_correct"])
                    self.assertIn(f"<answer>{x['key_letter']}</answer>", prompt)
                self.assertFalse(x["request"]["provider"]["allow_fallbacks"])
            self.assertEqual(len(endings), 1)
        self.assertEqual(list(targets.values()).count("A"), 2)

    def test_helpful_and_harmful_shifts_cancel_in_net_endpoint(self):
        # A blind 4-point rise in key following raises correct-key accuracy
        # and wrong-key errors equally. The primary net endpoint must be zero.
        self.assertAlmostEqual(trust.net_change(.95, .99, .2, .24), 0.)
        self.assertAlmostEqual(trust.net_change(.95, .97, .2, .30), -.04)
        self.assertAlmostEqual(trust.net_change(.95, .97, .2, .2), .01)

    def test_binary_shifts_and_assumed_probabilities_match_targets(self):
        rng = np.random.default_rng(11)
        old = np.array([.15, .35, .65])
        target = np.array([.25, .25, .65])
        x = (rng.random((200_000, 3)) < old).astype(float)
        y = trust.shift_binary(x, old, target, rng)
        np.testing.assert_allclose(y.mean(axis=0), target, atol=.004)
        self.assertTrue(np.all(x[:, 2] == y[:, 2]))
        difficulty = rng.random((97, 3))
        for mean in [.90, .95, .99]:
            p = trust.matched_probabilities(difficulty, mean)
            np.testing.assert_allclose(p.mean(axis=0), mean, atol=1e-12)

    def test_complete_question_covariance_controls_family_error(self):
        # Independent null datasets, correlated models, and incomplete blocks.
        # This catches accidentally treating paired conditions as independent N.
        rng = np.random.default_rng(71)
        shared = rng.normal(size=(4000, 100, 1))
        scores = shared + rng.normal(size=(4000, 100, 3))
        mask = rng.random((4000, 100)) < .85
        means, half, rejected = trust.trial_summary(scores, mask)
        self.assertLess(rejected.any(axis=1).mean(), .065)
        self.assertGreater(rejected.any(axis=1).mean(), .025)
        # Repeating the same within-question measurements must not narrow CIs.
        duplicated_within_question = np.repeat(scores[..., None], 2, axis=-1).mean(axis=-1)
        np.testing.assert_allclose(trust.trial_summary(duplicated_within_question, mask)[1], half)


if __name__ == "__main__":
    unittest.main()
