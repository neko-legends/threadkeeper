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


FAMILIES = [("kimi", "moonshot"), ("glm", "zai"), ("deepseek", "deepseek"), ("gpt", "openai"), ("astra", "openai"),
            ("opus", "anthropic"), ("claude", "anthropic"), ("sonnet", "anthropic"), ("haiku", "anthropic"), ("fable", "anthropic")]


def family(model):
    m = model.lower()
    return next((f for k, f in FAMILIES if k in m), m)


def same_model_or_family(graded, judge):
    """Return a reason string if the judge is the graded model or in its family, else None."""
    if graded.split("/")[-1] == judge.split("/")[-1]:
        return "judge %s is the graded model" % judge
    if family(graded) == family(judge):
        return "judge %s is in the same family (%s) as graded model %s" % (judge, family(judge), graded)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m score")
    ap.add_argument("--results", default="results")
    ap.add_argument("--corpora", default="corpora")
    ap.add_argument("--no-judge", action="store_true", help="mechanical scoring only")
    ap.add_argument("--judge-base-url", default=os.environ.get("THREADKEEPER_JUDGE_BASE_URL"))
    ap.add_argument("--judge-api-key-env", default="THREADKEEPER_JUDGE_API_KEY")
    ap.add_argument("--judge-model", default=os.environ.get("THREADKEEPER_JUDGE_MODEL"))
    ap.add_argument("--judge-effort", default=None)
    ap.add_argument("--judge-map", help="JSON file: {\"rules\": [{\"match\": substring of arm dir name, \"judge\": {transport, model, base_url, api_key_env, effort}}]}; "
                    "first matching rule grades that arm. The judge must not be the graded model or in its family.")
    ap.add_argument("--allow-same-family", action="store_true", help="NOT recommended: allow a judge from the graded model's family")
    ap.add_argument("--only", help="substring filter on arm directory names")
    a = ap.parse_args(argv)
    judge = None
    if not a.no_judge:
        key = os.environ.get(a.judge_api_key_env)
        if a.judge_base_url and a.judge_model and key:
            judge = Judge(a.judge_base_url, key, a.judge_model, a.judge_effort)
        else:
            print("note: judge not configured (need --judge-base-url, --judge-model and key env %s); scoring mechanically" % a.judge_api_key_env, file=sys.stderr)
    rules = json.load(open(a.judge_map))["rules"] if a.judge_map else []
    judges = {}
    corpora = {}
    for d in sorted(glob.glob(os.path.join(a.results, "*", "meta.json"))):
        arm = os.path.dirname(d)
        if a.only and a.only not in os.path.basename(arm):
            continue
        meta = json.load(open(d))
        if meta.get("status") == "failed":
            json.dump({"status": "FAILED", "failed_as": meta.get("failed_as") or "error", "composite": None, "error": meta.get("error")},
                      open(os.path.join(arm, "score.json"), "w"), indent=1)
            continue
        if meta.get("status") != "ok":
            json.dump({"status": "REJECTED" if meta.get("status") == "rejected" else "ERROR", "error": meta.get("error")}, open(os.path.join(arm, "score.json"), "w"), indent=1)
            continue
        c = meta["corpus"]
        corpora.setdefault(c, Corpus(os.path.join(a.corpora, c)))
        text = open(os.path.join(arm, "output.md"), encoding="utf-8").read()
        arm_judge, jspec, jnote = judge, None, None
        if a.judge_map and not a.no_judge:
            arm_judge = None
            rule = next((r for r in rules if r["match"] in os.path.basename(arm)), None)
            if rule is None:
                jnote = "no judge-map rule matches; graded mechanically (NOT self-graded)"
            else:
                jspec = rule["judge"]
                bad = None if a.allow_same_family else same_model_or_family(meta["model"], jspec["model"])
                if bad:
                    jnote, jspec = "judge refused: " + bad, None
                else:
                    key = json.dumps(jspec, sort_keys=True)
                    if key not in judges:
                        try:
                            judges[key] = Judge.from_spec(jspec)
                        except Exception as e:
                            judges[key] = e
                    if isinstance(judges[key], Exception):
                        jnote, jspec = "judge unavailable: %s" % judges[key], None
                    else:
                        arm_judge = judges[key]
        elif judge:
            jspec = {"transport": "openai", "model": a.judge_model, "base_url": a.judge_base_url, "effort": a.judge_effort}
            bad = None if a.allow_same_family else same_model_or_family(meta["model"], a.judge_model)
            if bad:
                arm_judge, jspec, jnote = None, None, "judge refused: " + bad
        n_calls = len(arm_judge.calls) if arm_judge else 0
        res = score_output(text, corpora[c], meta, arm_judge)
        res.update(model=meta["model"], effort=meta["effort"], corpus=c)
        if arm_judge:
            jc = arm_judge.calls[n_calls:]
            res["judge"] = {"model": jspec["model"], "transport": jspec["transport"], "effort": jspec.get("effort"),
                            "calls": jc, "failed_calls": sum(1 for x in jc if x.get("status") not in (200, "ok"))}
            res["judge_model"] = jspec["model"]
        else:
            res["judge"] = {"model": None, "note": jnote or "no judge"}
        meta["judge_model"] = res["judge"]["model"]
        meta["judge"] = res["judge"]
        json.dump(meta, open(d, "w"), indent=1, ensure_ascii=False)
        json.dump(res, open(os.path.join(arm, "score.json"), "w"), indent=1, ensure_ascii=False)
        print("%s -> %s %s" % (os.path.basename(arm), res["status"], res.get("composite") if res["status"] == "SCORED" else res["failed_as"]))
    rows = report.write(a.results)
    print("leaderboard: %d arms -> %s" % (len(rows), os.path.join(a.results, "leaderboard.md")))


if __name__ == "__main__":
    main()
