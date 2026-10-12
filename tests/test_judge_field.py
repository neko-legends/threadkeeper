"""A score.json must never name a judge that did not run (found 2026-10-11)."""
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from score import __main__ as sc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM = "kimi-k3__low__128k"
DEAD = {"status": None, "body": None, "error": "boom", "headers": {}, "latency_s": 0.0, "attempts": 1}


class JudgeField(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "results", ARM), os.path.join(self.tmp, ARM))
        self.sp = os.path.join(self.tmp, ARM, "score.json")
        self.before = open(self.sp).read()
        self.jm = os.path.join(self.tmp, "jm.json")
        json.dump({"rules": [{"match": "kimi", "judge": {"transport": "openai", "base_url": "http://x/v1", "api_key_env": "TK_TEST_KEY", "model": "some-judge"}}]}, open(self.jm, "w"))
        os.environ["TK_TEST_KEY"] = "x"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_main(self, *extra):
        argv = ["--results", self.tmp, "--corpora", os.path.join(ROOT, "corpora")] + list(extra)
        with mock.patch("score.judge.post_chat", return_value=DEAD):
            return sc.main(argv)

    def test_dead_judge_is_refused_and_field_not_written(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_main("--judge-map", self.jm, "--only", "kimi")
        self.assertNotIn(cm.exception.code, (0, None))
        self.assertEqual(open(self.sp).read(), self.before, "score.json must be left untouched when the judge never ran")

    def test_no_judge_configured_refuses_instead_of_scoring_silently(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_main("--only", "kimi")
        self.assertIn("no judge configured", str(cm.exception.code))
        self.assertEqual(open(self.sp).read(), self.before)

    def test_no_judge_flag_writes_no_judge_model(self):
        self.run_main("--no-judge", "--only", "kimi")
        s = json.load(open(self.sp))
        self.assertIsNone(s["judge"]["model"])
        self.assertNotIn("judge_model", s)


if __name__ == "__main__":
    unittest.main()
