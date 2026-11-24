"""Guard the protected-input locks under ``results/research_directions``.

Three research-direction packets record SHA-256 hashes of repository files that were frozen when the packet was
built. Two of those files were revised later for documented reasons (``CHANGELOG.md`` 2026-11-15, 2026-11-22 and
2026-11-24): the final report gained later results and ``scripts/24_deference.py`` gained the swapped-option
variants. The locks are not edited, because later manifests record their hashes in turn. This test pins the set
of known, documented drift so that any further change to a protected input is noticed.
"""

import hashlib
import json
import unittest

import ddm_evals

LOCKS = [
    "results/research_directions/selective_reliance_focus_20261024/prior_artifacts.json",
    "results/research_directions/reliance_calibration_v2/prior_artifacts.json",
    "results/research_directions/manageable_calibration_v3_20261021/protected_inputs.json",
]
DOCUMENTED_DRIFT = {"docs/FINAL_REPORT.md", "scripts/24_deference.py"}
PREFIXES = ("docs/", "scripts/", "data/", "config.yaml", "tests/")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _entries(obj):
    """Yield (repo path, expected hash) pairs from a possibly nested lock file."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str) and isinstance(value, str) and key.startswith(PREFIXES) and len(value) == 64:
                yield key, value
            else:
                yield from _entries(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _entries(value)


class FrozenInputTests(unittest.TestCase):
    def test_only_the_documented_files_have_drifted(self):
        drifted, checked = set(), 0
        for lock in LOCKS:
            path = ddm_evals.ROOT / lock
            self.assertTrue(path.is_file(), lock)
            for name, expected in _entries(json.loads(path.read_text(encoding="utf-8"))):
                target = ddm_evals.ROOT / name
                self.assertTrue(target.is_file(), f"{lock} names a missing file {name}")
                checked += 1
                if _sha(target) != expected:
                    drifted.add(name)
        self.assertGreater(checked, 20)
        self.assertEqual(drifted, DOCUMENTED_DRIFT)

    def test_documented_drift_is_explained_in_the_changelog(self):
        changelog = (ddm_evals.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        head = changelog.split("\n- 2026-11-15", 1)[0]
        for name in DOCUMENTED_DRIFT:
            self.assertIn(name, head, f"{name} drifted but is not mentioned in CHANGELOG.md since 2026-11-15")


if __name__ == "__main__":
    unittest.main()
