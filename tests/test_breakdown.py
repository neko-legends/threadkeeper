"""The leaderboard must always carry the full breakdown next to the composite. See also tests/test_mutant.py (strip a column -> this must fail)."""
import csv
import json
import os
import shutil
import tempfile
import unittest

from score import report, weights

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM = os.path.join(ROOT, "results", "opus__max__128k")


class Breakdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        shutil.copytree(ARM, os.path.join(cls.tmp, "arm"))
        report.write(cls.tmp, corpora_dir=os.path.join(ROOT, "corpora"))
        cls.md = open(os.path.join(cls.tmp, "leaderboard.md")).read()
        cls.csv = list(csv.DictReader(open(os.path.join(cls.tmp, "leaderboard.csv"))))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def header(self):
        return next(l for l in self.md.splitlines() if l.startswith("| #"))

    def test_header_has_every_required_column(self):
        cells = [c.strip() for c in self.header().strip("|").split("|")]
        for head, _ in report.BREAKDOWN:
            self.assertIn(head, cells, "leaderboard.md is missing the %r column" % head)

    def test_csv_has_every_required_key(self):
        for _, keys in report.BREAKDOWN:
            for k in keys:
                self.assertIn(k, self.csv[0], "leaderboard.csv is missing %r" % k)

    def test_markdown_states_formula_and_corpus_hash(self):
        self.assertIn(weights.formula(), self.md)
        self.assertIn(weights.FORMULA_V1, self.md)
        self.assertIn("sha256", self.md)

    def test_row_values_match_score_json(self):
        s = json.load(open(os.path.join(ARM, "score.json")))
        row = self.csv[0]
        self.assertEqual(float(row["composite"]), s["composite"])
        self.assertEqual(float(row["composite_v1"]), s["composite_v1"])
        self.assertEqual(int(row["invention_mech"]), s["invention"]["mechanical"]["count"])
        self.assertEqual(int(row["invention_judge"]), s["invention"]["judge"]["count"])

    def test_composite_cannot_be_emitted_without_breakdown(self):
        s = json.load(open(os.path.join(ARM, "score.json")))
        m = json.load(open(os.path.join(ARM, "meta.json")))
        row = report.row_of(s, m)
        report.check_breakdown(row)
        for _, keys in report.BREAKDOWN:
            for k in keys:
                if k == "composite":
                    continue
                bad = {x: v for x, v in row.items() if x != k}
                with self.assertRaises(report.BreakdownMissing, msg=k):
                    report.check_breakdown(bad)
        bad = dict(row, invention_mech=None)
        with self.assertRaises(report.BreakdownMissing):
            report.check_breakdown(bad)
        s2 = dict(s)
        del s2["composite_v1"]
        with self.assertRaises(report.BreakdownMissing):
            report.row_of(s2, m)


class Weights(unittest.TestCase):
    def test_invention_not_saturating(self):
        self.assertEqual([round(weights.invention_score(n), 2) for n in (0, 1, 2, 3, 4, 7)], [1.0, 0.75, 0.6, 0.5, 0.43, 0.3])
        self.assertGreater(weights.invention_score(10), weights.invention_score(20))

    def test_v1_unchanged_and_v2_punishes_invention(self):
        c = weights.composites(0.95, 1.0, 7)
        self.assertEqual(c["composite_v1"], round(100 * (0.55 * 0.95 + 0.35 + 0.10 * 0.3), 2))
        self.assertLess(c["composite"], c["composite_v1"])
        self.assertLess(weights.composites(0.95, 1.0, 7)["composite"], weights.composites(0.90, 1.0, 0)["composite"])

    def test_weights_override_validated(self):
        self.assertEqual(weights.parse_weights("facts=0.5,threads=0.3,invention=0.2")["invention"], 0.2)
        with self.assertRaises(ValueError):
            weights.parse_weights("facts=0.5,threads=0.5")


if __name__ == "__main__":
    unittest.main()
