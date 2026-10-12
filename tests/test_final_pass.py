"""Final-pass regressions: FAILED rows, explicit judge flags, environment strings, board completeness, path redaction."""
import csv
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from score import envscrub, gate, report
from score import __main__ as sc
from score.core import Corpus, score_output

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROK = os.path.join(ROOT, "results", "venice-grok-4-7__default__128k")
KIMI = os.path.join(ROOT, "results", "kimi-k3__low__128k")
HOME = "/home/" + "jun"  # built so this file does not trip its own leak check


def board(*arms):
    tmp = tempfile.mkdtemp()
    for a in arms:
        shutil.copytree(a, os.path.join(tmp, os.path.basename(a)))
    report.write(tmp, corpora_dir=os.path.join(ROOT, "corpora"))
    md = open(os.path.join(tmp, "leaderboard.md")).read()
    rows = list(csv.DictReader(open(os.path.join(tmp, "leaderboard.csv"))))
    return tmp, md, rows


class FailedRow(unittest.TestCase):
    def test_failed_arm_shows_gate_reason_and_no_judge_claim(self):
        tmp, md, rows = board(GROK)
        self.addCleanup(shutil.rmtree, tmp)
        line = next(l for l in md.splitlines() if "venice/grok-4-7" in l and l.startswith("| -"))
        self.assertNotIn("JUDGE CALL FAILED", md)
        self.assertIn("FAILED (prompt-echo)", line)
        self.assertIn("compaction prompt echoed back", line)
        cells = [c.strip() for c in line.strip("|").split("|")]
        hdr = [c.strip() for c in next(l for l in md.splitlines() if l.startswith("| #")).strip("|").split("|")]
        self.assertEqual(cells[hdr.index("tool version")], "0.99.1")
        self.assertIn("not graded", cells[hdr.index("judge")])
        self.assertEqual(rows[0]["composite"], "")

    def test_judge_failure_is_stamped_on_judge_column_only(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        arm = os.path.join(tmp, "kimi")
        shutil.copytree(KIMI, arm)
        s = json.load(open(os.path.join(arm, "score.json")))
        s["judge"]["failed_calls"] = 2
        json.dump(s, open(os.path.join(arm, "score.json"), "w"))
        report.write(tmp, corpora_dir=os.path.join(ROOT, "corpora"))
        md = open(os.path.join(tmp, "leaderboard.md")).read()
        line = next(l for l in md.splitlines() if "kimi-k3" in l and l.startswith("| 1"))
        cells = [c.strip() for c in line.strip("|").split("|")]
        hdr = [c.strip() for c in next(l for l in md.splitlines() if l.startswith("| #")).strip("|").split("|")]
        self.assertIn("JUDGE CALL FAILED", cells[hdr.index("judge")])
        self.assertNotIn("JUDGE CALL FAILED", cells[hdr.index("tool version")])


class GateEcho(unittest.TestCase):
    def test_prompt_echo_is_classified(self):
        corpus = Corpus(os.path.join(ROOT, "corpora", "128k"))
        r = score_output(open(os.path.join(GROK, "output.md")).read(), corpus)
        self.assertEqual((r["status"], r["failed_as"]), ("FAILED", "prompt-echo"))

    def test_real_summary_is_not_an_echo(self):
        self.assertFalse(gate.echoes_prompt(open(os.path.join(KIMI, "output.md")).read()))


class ExplicitJudge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        shutil.copytree(KIMI, os.path.join(self.tmp, "kimi-k3__low__128k"))
        self.meta = os.path.join(self.tmp, "kimi-k3__low__128k", "meta.json")
        m = json.load(open(self.meta))
        m.pop("judge", None), m.pop("judge_model", None)
        json.dump(m, open(self.meta, "w"))

    def run_main(self, *extra):
        return sc.main(["--results", self.tmp, "--corpora", os.path.join(ROOT, "corpora")] + list(extra))

    def test_env_var_judge_model_is_not_a_default(self):
        env = {"THREADKEEPER_JUDGE_MODEL": "some-judge", "THREADKEEPER_JUDGE_API_KEY": "x", "THREADKEEPER_JUDGE_BASE_URL": "http://x/v1"}
        with mock.patch.dict(os.environ, env), self.assertRaises(SystemExit) as cm:
            self.run_main()
        self.assertIn("--judge-model", str(cm.exception.code))

    def test_mechanical_run_writes_no_judge_field_anywhere(self):
        self.run_main("--no-judge")
        m = json.load(open(self.meta))
        self.assertNotIn("judge_model", m)
        self.assertNotIn("judge", m)
        s = json.load(open(os.path.join(self.tmp, "kimi-k3__low__128k", "score.json")))
        self.assertIsNone(s["judge"]["model"])
        self.assertNotIn("judge_model", s)

    def test_no_judge_conflicts_with_judge_model(self):
        with self.assertRaises(SystemExit):
            self.run_main("--no-judge", "--judge-model", "x")


class EnvironmentStrings(unittest.TestCase):
    def test_scrub_strips_cwd_and_run_date_but_not_session_strings(self):
        txt = "cwd `/tmp/tk-cwd-abc123` and `%s/git/x`; date 2026-10-12; session date 2026-03-04; path /srv/app" % HOME
        out, gone = envscrub.scrub(txt, "the session mentions 2026-03-04 and /srv/app", {"2026-10-12"})
        self.assertNotIn("tk-cwd", out)
        self.assertNotIn("2026-10-12", out)
        self.assertNotIn(HOME, out)
        self.assertIn("2026-03-04", out)
        self.assertIn("/srv/app", out)
        self.assertEqual(sorted(gone), sorted(["/tmp/tk-cwd-abc123", HOME + "/git/x", "2026-10-12"]))

    def test_session_own_date_and_path_are_kept(self):
        out, gone = envscrub.scrub("on 2026-10-12 in /home/founder/code", "2026-10-12 /home/founder/code", {"2026-10-12"})
        self.assertEqual((out, gone), ("on 2026-10-12 in /home/founder/code", []))

    def test_judge_and_mechanical_check_never_see_the_environment(self):
        corpus = Corpus(os.path.join(ROOT, "corpora", "128k"))
        text = open(os.path.join(KIMI, "output.md")).read() + "\n- Temporary session cwd: `/tmp/tk-cwd-xyz9`.\n- Current date: 2026-10-12.\n"
        seen = {}

        class Spy:
            calls = []

            def threads(self, summary, gt):
                seen["t"] = summary
                return {"verdicts": {t["id"]: "LOST" for t in gt["threads"]}, "parsed": True, "raw": ""}

            def invention(self, summary, session):
                seen["i"] = summary
                return {"items": [], "count": 0, "parsed": True, "raw": ""}

        meta = {"started_at_unix": 1791787047, "versions": {"resolved_on": "2026-10-12"}}
        base = score_output(open(os.path.join(KIMI, "output.md")).read(), corpus, meta)
        r = score_output(text, corpus, meta, Spy())
        for k in ("t", "i"):
            self.assertNotIn("tk-cwd", seen[k])
            self.assertNotIn("2026-10-12", seen[k])
        self.assertIn("/tmp/tk-cwd-xyz9", r["environment_stripped"])
        self.assertEqual(r["invention"]["mechanical"]["count"], base["invention"]["mechanical"]["count"])

    def test_judge_items_naming_environment_are_excluded(self):
        items = [{"summary_quote": "cwd `/tmp/tk-cwd-abc`"}, {"summary_quote": "Current date in environment: 2026-10-12"}, {"summary_quote": "port 9999"}]
        kept, excl = envscrub.drop_env_items(items, ["2026-10-12"])
        self.assertEqual([i["summary_quote"] for i in kept], ["port 9999"])
        self.assertEqual(len(excl), 2)


class Shipped(unittest.TestCase):
    def test_board_has_a_row_for_every_score_json(self):
        files = report.score_files(os.path.join(ROOT, "results"), os.path.join(ROOT, "results-200k"))
        rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "leaderboard.csv"))))
        self.assertEqual(len(rows), len(files))
        for r in rows:
            self.assertTrue(r["judge_model"], r["model"])

    def test_no_home_path_in_tracked_files(self):
        out = subprocess.run(["git", "grep", "-l", HOME], cwd=ROOT, capture_output=True, text=True).stdout.split()
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
