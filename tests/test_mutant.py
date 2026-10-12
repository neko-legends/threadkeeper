"""Mutant test: with the summary gate disabled (TK_DISABLE_GATE=1) the self-tests MUST fail."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Mutant(unittest.TestCase):
    def run_selftests(self, env_extra):
        env = dict(os.environ, **env_extra)
        return subprocess.run([sys.executable, "-m", "unittest", "tests.test_selftests.SelfTests", "-q"], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_baseline_passes(self):
        r = self.run_selftests({})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_disabled_gate_is_caught(self):
        r = self.run_selftests({"TK_DISABLE_GATE": "1"})
        self.assertNotEqual(r.returncode, 0, "self-tests still pass with the gate disabled: they cannot fail")
        self.assertIn("test_b_continuations_fail_gate", r.stderr)
        self.assertIn("test_c_empty_fails", r.stderr)

    def test_stripped_breakdown_column_is_caught(self):
        for col in ("invention judge", "threads mech P/PA/L", "transport"):
            env = dict(os.environ, TK_STRIP_COLUMN=col)
            r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_breakdown.Breakdown", "-q"], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0, "breakdown test still passes with %r stripped" % col)
            self.assertIn("test_header_has_every_required_column", r.stderr)


if __name__ == "__main__":
    unittest.main()
