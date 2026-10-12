"""python -m score [--results results] [--corpora corpora] [--no-judge] [--judge-model M ...]"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

from .core import Corpus, score_output
from .judge import Judge
from . import report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m score")
    ap.add_argument("--results", default="results")
    ap.add_argument("--corpora", default="corpora")
    ap.add_argument("--no-judge", action="store_true", help="mechanical scoring only")
    ap.add_argument("--judge-base-url", default=os.environ.get("THREADKEEPER_JUDGE_BASE_URL"))
    ap.add_argument("--judge-api-key-env", default="THREADKEEPER_JUDGE_API_KEY")
    ap.add_argument("--judge-model", default=os.environ.get("THREADKEEPER_JUDGE_MODEL"))
    ap.add_argument("--judge-effort", default=None)
    ap.add_argument("--only", help="substring filter on arm directory names")
    a = ap.parse_args(argv)
    judge = None
    if not a.no_judge:
        key = os.environ.get(a.judge_api_key_env)
        if a.judge_base_url and a.judge_model and key:
            judge = Judge(a.judge_base_url, key, a.judge_model, a.judge_effort)
        else:
            print("note: judge not configured (need --judge-base-url, --judge-model and key env %s); scoring mechanically" % a.judge_api_key_env, file=sys.stderr)
    corpora = {}
    for d in sorted(glob.glob(os.path.join(a.results, "*", "meta.json"))):
        arm = os.path.dirname(d)
        if a.only and a.only not in os.path.basename(arm):
            continue
        meta = json.load(open(d))
        if meta.get("status") != "ok":
            json.dump({"status": "REJECTED" if meta.get("status") == "rejected" else "ERROR", "error": meta.get("error")}, open(os.path.join(arm, "score.json"), "w"), indent=1)
            continue
        c = meta["corpus"]
        corpora.setdefault(c, Corpus(os.path.join(a.corpora, c)))
        text = open(os.path.join(arm, "output.md"), encoding="utf-8").read()
        res = score_output(text, corpora[c], meta, judge)
        res.update(model=meta["model"], effort=meta["effort"], corpus=c)
        if judge:
            res["judge_model"] = a.judge_model
        json.dump(res, open(os.path.join(arm, "score.json"), "w"), indent=1, ensure_ascii=False)
        print("%s -> %s %s" % (os.path.basename(arm), res["status"], res.get("composite") if res["status"] == "SCORED" else res["failed_as"]))
    rows = report.write(a.results)
    print("leaderboard: %d arms -> %s" % (len(rows), os.path.join(a.results, "leaderboard.md")))


if __name__ == "__main__":
    main()
