"""Scorer self-tests. These must be able to FAIL: see tests/test_mutant.py."""
import os
import unittest

from score.core import Corpus, score_output

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures")


def fx(n):
    with open(os.path.join(FIX, n), encoding="utf-8") as fh:
        return fh.read()


class SelfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Corpus(os.path.join(ROOT, "corpora", "32k"))
        cls.perfect = score_output(fx("handwritten_32k.md"), cls.c)

    def test_a_perfect_summary_near_max(self):
        self.assertEqual(self.perfect["status"], "SCORED")
        self.assertGreaterEqual(self.perfect["composite"], 95)
        self.assertEqual(self.perfect["facts"]["found"], self.perfect["facts"]["total"])

    def test_a2_reference_summary_max(self):
        r = score_output(open(os.path.join(ROOT, "corpora", "32k", "reference_summary.md")).read(), self.c)
        self.assertGreaterEqual(r["composite"], 99)

    def test_b_continuations_fail_gate(self):
        for f in ("continuation.md", "continuation_planlist.md"):
            r = score_output(fx(f), self.c)
            self.assertEqual(r["status"], "FAILED", f)
            self.assertEqual(r["failed_as"], "continuation", f)
            self.assertIsNone(r["composite"])

    def test_b2_chat_reply_and_toolcall(self):
        self.assertEqual(score_output(fx("chat_reply.md"), self.c)["failed_as"], "chat-reply")
        self.assertEqual(score_output(fx("tool_call.md"), self.c)["failed_as"], "tool-call")
        r = score_output("a perfectly fine looking text " * 30, self.c, {"tool_calls": [{"id": "x"}]})
        self.assertEqual(r["failed_as"], "tool-call")

    def test_c_empty_fails(self):
        for t in ("", "   \n  "):
            r = score_output(t, self.c)
            self.assertEqual((r["status"], r["failed_as"]), ("FAILED", "empty"))

    def test_d_stale_values_penalised(self):
        gt = self.c.gt
        stale = [f for f in gt["facts"] if f["superseded"]]
        self.assertGreaterEqual(len(stale), 7)
        # same summary, but the current-state section now asserts the OLD values with no supersession cue
        bad = fx("handwritten_32k.md") + "\n\n## Current state (per notes)\n" + "\n".join("- " + f["line_stale"] for f in stale) + "\n"
        r = score_output(bad, self.c)
        self.assertEqual(r["status"], "SCORED")
        self.assertGreaterEqual(r["facts"]["stale_fact_count"], len(stale) - 1)
        self.assertLess(r["facts"]["net"], r["facts"]["recall"])
        self.assertLess(r["composite"], self.perfect["composite"] - 3)

    def test_d2_cued_stale_not_penalised(self):
        self.assertEqual(self.perfect["facts"]["stale_fact_count"], 0)

    def test_e_invented_number_flagged(self):
        text = fx("handwritten_32k.md") + '\n- The batch job handles 48213 records per run, see commit deadbee1f2 and the note "ship it on a Sunday night".\n'
        r = score_output(text, self.c)
        m = r["invention"]["mechanical"]
        self.assertIn("48213", m["unsupported_numbers"])
        self.assertIn("deadbee1f2", m["unsupported_hashes"])
        self.assertTrue(any("sunday" in q for q in m["unsupported_quotes"]))
        self.assertEqual(self.perfect["invention"]["mechanical"]["count"], 0)

    def test_f_judge_fabricated_quotes_dropped(self):
        from score.judge import Judge
        import json
        def fake(prompt):
            if "THREADS:" in prompt:
                return json.dumps({"T1": {"verdict": "PRESERVED", "quote": "this sentence is not in the summary"}, "T2": {"verdict": "PRESERVED", "quote": "snoozed_until"}})
            return json.dumps([{"summary_quote": "invented words here", "why": "x"}, {"summary_quote": "Nudgewell is a small web app", "why": "y"}])
        r = score_output(fx("handwritten_32k.md"), self.c, judge=Judge("", "", "m", chat=fake))
        j = r["threads"]["judge"]
        self.assertEqual(j["verdicts"]["T1"], "PARTIAL")
        self.assertEqual(j["verdicts"]["T2"], "PRESERVED")
        self.assertEqual(j["judge_fabricated_quotes"], 1)
        self.assertEqual(r["invention"]["judge"]["count"], 1)
        self.assertEqual(r["invention"]["judge"]["dropped_unverified"], 1)


class CorpusIntegrity(unittest.TestCase):
    def test_every_fact_planted_and_stale_present(self):
        from score.textnorm import has, norm
        for size in ("32k", "128k", "200k"):
            c = Corpus(os.path.join(ROOT, "corpora", size))
            t = norm(c.text)
            for f in c.gt["facts"]:
                self.assertTrue(f["planted_at"], (size, f["id"]))
                self.assertTrue(has(t, f["value"]), (size, f["id"], f["value"]))
                for s in f["stale"]:
                    self.assertTrue(has(t, s["value"]), (size, f["id"], s["value"]))

    def test_generator_deterministic(self):
        import hashlib, json
        from gen import build
        cfg = build.SIZES["32k"]
        out = []
        for _ in range(2):
            b, w = build.build(cfg["seed"], cfg["target_chars"])
            out.append(hashlib.sha256("\n".join(json.dumps(m, sort_keys=True) for m in b.msgs).encode()).hexdigest())
        self.assertEqual(out[0], out[1])
        man = json.load(open(os.path.join(ROOT, "corpora", "MANIFEST.json")))
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            build.write(d, b, w, cfg["seed"], "32k")
            self.assertEqual(build.sha256_file(os.path.join(d, "session.jsonl")), man["32k"]["sha256"]["session.jsonl"])


if __name__ == "__main__":
    unittest.main()


class QuoteMatcher(unittest.TestCase):
    """Mechanical quote check: flag real misquotes, not punctuation / placeholders / scare-quote words (v4 audit)."""

    @classmethod
    def setUpClass(cls):
        from score import invention
        cls.inv = invention
        cls.idx = invention.corpus_index("[assistant] set up: nightly pg_dump at 02:40 utc. migration 0020 applied. nothing depends on it yet. "
                                         "log.debug('formatExportForQueue dry run') and inv_c0dad2 in the list")

    def unsupported(self, summary):
        return self.inv.check(summary, self.idx)["unsupported_quotes"]

    def test_edge_punctuation_is_not_part_of_the_quote(self):
        self.assertEqual(self.unsupported('the agent claimed "set up: nightly pg_dump," earlier'), [])
        self.assertEqual(self.unsupported('claimed "nightly pg_dump at 02:40 utc," and left'), [])

    def test_placeholder_and_ellipsis_fragments_are_checked_around_the_gap(self):
        self.assertEqual(self.unsupported("log.debug('<name> dry run')"), [])
        self.assertEqual(self.unsupported('ids like "inv_…" were returned'), [])
        self.assertEqual(self.unsupported('wrote "<fn> missing words here"'), ['<fn> missing words here'])

    def test_short_scare_quotes_are_skipped_not_flagged(self):
        r = self.inv.check('it said "all good" and "fixes" a lot', self.idx)
        self.assertEqual(r["unsupported_quotes"], [])
        self.assertEqual(r["checked"]["quotes"], 0)
        self.assertEqual(sorted(r["skipped_short_quotes"]), ["all good", "fixes"])

    def test_a_real_misquote_is_still_flagged(self):
        self.assertEqual(self.unsupported('"nothing depends on yet" it said'), ["nothing depends on yet"])
