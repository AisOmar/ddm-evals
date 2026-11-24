"""Checks for the ``ddm_evals`` package and the ``ddm-evals`` command. Offline; no model calls."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ddm_evals
from ddm_evals import cli


class PathsAndConfigTests(unittest.TestCase):
    def test_root_is_the_checkout(self):
        self.assertTrue((ddm_evals.ROOT / "config.yaml").is_file())
        self.assertTrue((ddm_evals.SCRIPTS / "outcomes.py").is_file())
        self.assertEqual(ddm_evals.DOCS, ddm_evals.ROOT / "docs")
        self.assertEqual(ddm_evals.RESULTS, ddm_evals.ROOT / "results")

    def test_config_has_the_frozen_study_settings(self):
        cfg = ddm_evals.load_config()
        self.assertEqual(cfg["study"]["seed"], 20261006)
        self.assertIn("deepseek-r1-0528", cfg["model"]["name"])
        self.assertEqual(cfg["model"]["max_tokens"], 8192)
        self.assertEqual(set(cfg["conditions"]), {"plain_concise", "plain_thorough", "sbs_concise", "sbs_thorough"})

    def test_config_rejects_a_non_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "not_a_mapping.yaml"
            bad.write_text("- just\n- a list\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                ddm_evals.load_config(bad)

    def test_version_is_a_dotted_string(self):
        self.assertRegex(ddm_evals.__version__, r"^\d+\.\d+\.\d+")


class ScriptDiscoveryTests(unittest.TestCase):
    def test_every_numbered_script_has_a_one_line_summary(self):
        scripts = ddm_evals.list_scripts()
        numbered = [s for s in scripts if s.number is not None]
        self.assertGreaterEqual(len(numbered), 110)
        missing = [s.name for s in numbered if not s.summary]
        self.assertEqual(missing, [], f"scripts without a module docstring: {missing}")
        self.assertEqual([s.number for s in numbered], sorted(s.number for s in numbered))

    def test_shared_modules_are_listed_after_the_numbered_ones(self):
        names = [s.name for s in ddm_evals.list_scripts()]
        self.assertIn("outcomes", names)
        self.assertGreater(names.index("outcomes"), names.index("24_deference"))
        self.assertNotIn("outcomes", [s.name for s in ddm_evals.list_scripts(include_shared=False)])

    def test_find_script_by_name_number_and_filename(self):
        self.assertEqual(ddm_evals.find_script("24_deference").number, 24)
        self.assertEqual(ddm_evals.find_script("24").name, "24_deference")
        self.assertEqual(ddm_evals.find_script("scripts/24_deference.py").name, "24_deference")
        with self.assertRaises(FileNotFoundError):
            ddm_evals.find_script("no_such_script")

    def test_find_script_refuses_an_ambiguous_number(self):
        # 12_design_recovery.py and 12_power_simulation.py share a number.
        with self.assertRaises(ValueError):
            ddm_evals.find_script("12")

    def test_load_script_imports_in_place(self):
        outcomes = ddm_evals.load_script("outcomes")
        self.assertEqual(outcomes.parse_answer("some reasoning\nAnswer: B"), "B")
        self.assertIsNone(outcomes.parse_answer("A buffer overflow is bad"))
        design = ddm_evals.load_script("design")
        self.assertTrue(callable(design.correct_is_a))


class CommandLineTests(unittest.TestCase):
    def _run(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(list(argv))
        return code, out.getvalue()

    def test_info_reports_version_root_and_model(self):
        code, text = self._run("info")
        self.assertEqual(code, 0)
        self.assertIn(f"ddm-evals {ddm_evals.__version__}", text)
        self.assertIn(str(ddm_evals.ROOT), text)
        self.assertIn("deepseek-r1-0528", text)

    def test_list_prints_every_script_once(self):
        code, text = self._run("list")
        self.assertEqual(code, 0)
        lines = [line for line in text.splitlines() if line.strip()]
        self.assertEqual(len(lines), len(ddm_evals.list_scripts()))
        self.assertTrue(any(line.startswith("117_cost_ledger") for line in lines))
        code, numbered = self._run("list", "--numbered")
        self.assertFalse(any(line.startswith("outcomes") for line in numbered.splitlines()))

    def test_run_passes_arguments_through(self):
        # A throw-away script in a temporary folder, so that no real pipeline script runs inside the tests.
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            script = folder / "01_echo.py"
            script.write_text('"""Echo."""\nimport sys\nprint("ARGS", sys.argv[1:])\n', encoding="utf-8")
            with mock.patch.object(cli, "find_script", lambda name: ddm_evals.find_script(name, scripts_dir=folder)):
                code, text = self._run("run", "01_echo", "--stage", "design")
        self.assertEqual(code, 0)
        self.assertIn("ARGS ['--stage', 'design']", text)

    def test_version_flag(self):
        with self.assertRaises(SystemExit) as ctx:
            self._run("--version")
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
