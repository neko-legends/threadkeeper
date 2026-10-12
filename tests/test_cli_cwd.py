"""pi/claude CLIs put their working directory in the system prompt; it must never be the repo (found 2026-10-11)."""
import os
import unittest
from unittest import mock

from run import cli


class CliCwd(unittest.TestCase):
    def run_arm(self, transport):
        seen = {}

        def fake(cmd, stdin=None, capture_output=None, timeout=None, cwd=None):
            seen.update(cmd=cmd, cwd=cwd, listing=os.listdir(cwd), prompt=stdin.read().decode())
            return mock.Mock(returncode=0, stdout=b"a summary", stderr=b"")

        with mock.patch("run.cli.subprocess.run", side_effect=fake):
            cli.call_cli(transport, "venice/qwen-3-8-flash", "chat transcript", "default")
        return seen

    def test_pi_runs_in_empty_dir_and_prompt_has_no_home_path(self):
        s = self.run_arm("pi")
        self.assertEqual(s["listing"], [])
        self.assertNotIn("/home/jun", s["cwd"])
        self.assertNotIn("/home/jun", s["prompt"])
        self.assertNotIn("/home/jun", " ".join(s["cmd"]))

    def test_claude_runs_in_empty_dir(self):
        s = self.run_arm("claude")
        self.assertEqual(s["listing"], [])
        self.assertNotIn("/home/jun", s["cwd"])


if __name__ == "__main__":
    unittest.main()
