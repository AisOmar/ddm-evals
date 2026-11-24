"""Collection safeguards exercised offline, without credentials or API calls."""
import importlib.util
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("trust_collect", ROOT / "scripts/31_trust_collect.py")
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)


class TrustCollectionTests(unittest.TestCase):
    def test_insufficient_budget_blocks_before_credentials_or_request_files(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(collect, "OUT", Path(folder)), patch.object(collect, "manifest", return_value={"trials": [1]}), patch.object(collect, "api_key", side_effect=AssertionError("Credentials accessed")):
            (Path(folder) / "live_preflight.json").write_text(json.dumps(dict(passed=False)))
            with self.assertRaisesRegex(ValueError, "Insufficient"):
                collect.prepare(1)
            self.assertFalse((Path(folder) / "requests").exists())
            self.assertFalse((Path(folder) / "active_batch.json").exists())

    def test_overlapping_batches_and_stale_preflight_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(collect, "OUT", Path(folder)), patch.object(collect, "OPS", Path(folder) / "ops.md"):
            root = Path(folder)
            (root / "active_batch.json").write_text('{}')
            with self.assertRaisesRegex(ValueError, "prepared/running"):
                collect.require_no_batch()
            (root / "active_batch.json").unlink()
            (root / "manifest.json").write_text('{}')
            collect.OPS.write_text("delivery rules")
            budget = dict(passed=True, manifest_sha256=collect.sha(root / "manifest.json"),
                          operations_sha256=collect.sha(collect.OPS), runner_sha256=collect.sha(Path(collect.__file__)),
                          checked_at=(datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(), planned_calls=1)
            with self.assertRaisesRegex(ValueError, "Stale"):
                collect.validate_budget(dict(trials=[1]), budget)

    def test_valid_refusals_are_delivered_and_provider_or_duplicates_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            trial = dict(sample_id="q1", request=dict(model="model-a"))
            raw = dict(provider="DeepInfra", model="model-a", usage=dict(completion_tokens=5),
                       choices=[dict(message=dict(content="I cannot help with that."), finish_reason="stop")])
            p = root / 'q1.attempt1.json'
            p.write_text(json.dumps(raw))
            self.assertIsNotNone(collect.delivered(trial, [p])[1])
            raw["provider"] = "another-provider"
            p.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "Unexpected model/provider"):
                collect.delivered(trial, [p])
            raw["provider"] = "DeepInfra"
            p.write_text(json.dumps(raw))
            other = root / 'q1.attempt2.json'
            other.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                collect.delivered(trial, [p, other])

    def test_rate_limit_cooldown_honors_larger_retry_after(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'q1.attempt1.json'
            p.write_text(json.dumps(dict(error=dict(code=429))))
            os.utime(p, (1000, 1000))
            p.with_suffix('.retry_after').write_text('1800')
            self.assertEqual(collect.retry_state([p]), (0, 1, 2800))
            p.with_suffix('.retry_after').write_text('invalid')
            self.assertEqual(collect.retry_state([p]), (0, 1, 1900))
            # A partial response counts against ordinary attempts, not rate limits.
            p.write_text('{partial')
            self.assertEqual(collect.retry_state([p]), (1, 0, 0.))

    def test_frozen_manifest_and_live_cost_envelope(self):
        m = collect.manifest()
        self.assertEqual(len(m["trials"]), 9000)
        price = dict(pricing=dict(prompt="0.0000005", completion="0.00000215"))
        trial = m["trials"][0]
        expected_input = 4 * (len(json.dumps(trial["request"]["messages"], ensure_ascii=False).encode()) + 1024)
        self.assertAlmostEqual(collect.cap_cost(trial, price), expected_input * .0000005 + 8192 * .00000215)


if __name__ == "__main__":
    unittest.main()
