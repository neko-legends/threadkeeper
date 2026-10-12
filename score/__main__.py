"""python -m score [--results results] [--corpora corpora] [--no-judge] [--judge-model M ...]"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

from .core import Corpus, score_output
from .judge import Judge
from . import envscrub, invention, report, weights as weights_mod


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


def rescore(results_dir, w=None, extra=()):
    """Recompute the composites from what score.json already stores (facts.net, threads.score, mechanical invention count)."""
    for sp in report.score_files(results_dir, *extra):
        res = json.load(open(sp))
        if res.get("status") != "SCORED":
            continue
        invention.with_rate(res["invention"]["mechanical"])
        old = res.get("composite_v1_stored", res.get("composite") if "composite_v1" not in res else res["composite_v1"])
        res.update(weights_mod.composites(res["facts"]["net"], res["threads"]["score"], res["invention"]["mechanical"]["count"], w))
        json.dump(res, open(sp, "w"), indent=1, ensure_ascii=False)
        print("%s: v1 %s -> v1 %s, v2 %s" % (os.path.basename(os.path.dirname(sp)), old, res["composite_v1"], res["composite"]))
    rows = report.write(results_dir, w, extra=extra)
    print("leaderboard: %d arms -> %s" % (len(rows), os.path.join(results_dir, "leaderboard.md")))


def remechanical(results_dir, corpora_dir, w=None, extra=()):
    """Re-run ONLY the mechanical invention check on each stored output.md (no model calls) and recompute the composites.
    The previous mechanical block is kept as invention.mechanical_prev."""
    corpora = {}
    for sp in report.score_files(results_dir, *extra):
        res = json.load(open(sp))
        if res.get("status") != "SCORED":
            continue
        arm = os.path.dirname(sp)
        c = res["corpus"]
        corpora.setdefault(c, Corpus(os.path.join(corpora_dir, c)))
        meta = json.load(open(os.path.join(arm, "meta.json")))
        seen, stripped = envscrub.scrub(open(os.path.join(arm, "output.md"), encoding="utf-8").read(), corpora[c].text, envscrub.run_dates(meta))
        new = invention.check(seen, corpora[c].index)
        res["environment_stripped"] = stripped
        ji = res["invention"].get("judge")
        if ji and ji.get("items") is not None:  # judge flags that only name an environment string are not invention (no model call)
            kept, excl = envscrub.drop_env_items(ji["items"], stripped)
            if excl:
                ji["items"], ji["count"], ji["excluded_environment"] = kept, len(kept), excl
        old = res["invention"].get("mechanical_prev") or res["invention"]["mechanical"]
        res["invention"]["mechanical_prev"] = old
        res["invention"]["mechanical"] = new
        res.update(weights_mod.composites(res["facts"]["net"], res["threads"]["score"], new["count"], w))
        json.dump(res, open(sp, "w"), indent=1, ensure_ascii=False)
        print("%s: mech %d -> %d (checked %d -> %d)" % (os.path.basename(arm), old["count"], new["count"], old.get("checked_total", 0), new["checked_total"]))
    rows = report.write(results_dir, w, corpora_dir, extra)
    print("leaderboard: %d arms -> %s" % (len(rows), os.path.join(results_dir, "leaderboard.md")))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m score")
    ap.add_argument("--results", default="results")
    ap.add_argument("--corpora", default="corpora")
    ap.add_argument("--no-judge", action="store_true", help="mechanical scoring only")
    ap.add_argument("--judge-base-url", default=os.environ.get("THREADKEEPER_JUDGE_BASE_URL"))
    ap.add_argument("--judge-api-key-env", default="THREADKEEPER_JUDGE_API_KEY")
    ap.add_argument("--judge-model", help="REQUIRED unless --no-judge or --judge-map: no judge field is ever written from a default or an env var")
    ap.add_argument("--judge-effort", default=None)
    ap.add_argument("--judge-map", help="JSON file: {\"rules\": [{\"match\": substring of arm dir name, \"judge\": {transport, model, base_url, api_key_env, effort}}]}; "
                    "first matching rule grades that arm. The judge must not be the graded model or in its family.")
    ap.add_argument("--allow-same-family", action="store_true", help="NOT recommended: allow a judge from the graded model's family")
    ap.add_argument("--weights", help="override composite weights, e.g. facts=0.45,threads=0.30,invention=0.25 (default: score/weights.py)")
    ap.add_argument("--rescore", action="store_true", help="recompute composite/composite_v1 from the STORED score.json fields (no model calls, no judge), then rebuild the board")
    ap.add_argument("--remechanical", action="store_true", help="re-run only the mechanical invention check on stored outputs (no model calls) and rebuild the board")
    ap.add_argument("--include", action="append", default=[], help="extra results directory whose score.json files go on the same board (repeatable, e.g. results-200k)")
    ap.add_argument("--board-only", action="store_true", help="rebuild the board from every score.json (recursive) and exit; no scoring, no model calls")
    ap.add_argument("--only", help="substring filter on arm directory names")
    a = ap.parse_args(argv)
    w = weights_mod.parse_weights(a.weights) if a.weights else None
    if a.board_only:
        rows = report.write(a.results, w, a.corpora, a.include)
        print("leaderboard: %d arms (%d score.json) -> %s" % (len(rows), len(report.score_files(a.results, *a.include)), os.path.join(a.results, "leaderboard.md")))
        return
    if a.rescore:
        return rescore(a.results, w, a.include)
    if a.remechanical:
        return remechanical(a.results, a.corpora, w, a.include)
    judge = None
    if a.no_judge and (a.judge_model or a.judge_map):
        sys.exit("error: --no-judge conflicts with --judge-model/--judge-map")
    if a.judge_base_url and not (a.judge_model or a.judge_map) and not a.no_judge:
        sys.exit("error: --judge-base-url given but no --judge-model: pass --judge-model explicitly (or --no-judge for mechanical-only scoring)")
    if not a.no_judge:
        key = os.environ.get(a.judge_api_key_env)
        if a.judge_base_url and a.judge_model and key:
            judge = Judge(a.judge_base_url, key, a.judge_model, a.judge_effort)
        elif not a.judge_map:
            sys.exit("error: no judge configured (need --judge-base-url, --judge-model and key env %s, or --judge-map). "
                     "Refusing to score silently without a judge; pass --no-judge for mechanical-only scoring." % a.judge_api_key_env)
    rules = json.load(open(a.judge_map))["rules"] if a.judge_map else []
    judges = {}
    corpora = {}
    refused = []
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
        res = score_output(text, corpora[c], meta, arm_judge, w)
        res.update(model=meta["model"], effort=meta["effort"], corpus=c, versions=meta.get("versions"))
        jc = arm_judge.calls[n_calls:] if arm_judge else []
        if arm_judge and not jc:
            jnote = "judge not invoked (arm status %s)" % res["status"]
            arm_judge = None
        if arm_judge:
            jt, ji = (res.get("threads") or {}).get("judge"), (res.get("invention") or {}).get("judge")
            if res["status"] == "SCORED" and (any(x.get("status") not in (200, "ok") for x in jc) or not (jt and jt["parsed"] and ji and ji["parsed"])):
                # a judge that did not actually run must not be written into score.json as if it had
                refused.append(os.path.basename(arm))
                print("%s: REFUSED - judge %s produced no usable output (%d call(s), %d failed); score.json left untouched"
                      % (os.path.basename(arm), jspec["model"], len(jc), sum(1 for x in jc if x.get("status") not in (200, "ok"))), file=sys.stderr)
                continue
            res["judge"] = {"model": jspec["model"], "transport": jspec["transport"], "effort": jspec.get("effort"),
                            "calls": jc, "versions": next((x["versions"] for x in jc if x.get("versions")), None), "failed_calls": sum(1 for x in jc if x.get("status") not in (200, "ok"))}
            res["judge_model"] = jspec["model"]
        else:
            res["judge"] = {"model": None, "note": jnote or "no judge"}
        if res["judge"]["model"]:
            meta["judge_model"], meta["judge"] = res["judge"]["model"], res["judge"]
        else:  # mechanical-only: no judge field in meta either
            meta.pop("judge_model", None)
            meta.pop("judge", None)
        json.dump(meta, open(d, "w"), indent=1, ensure_ascii=False)
        json.dump(res, open(os.path.join(arm, "score.json"), "w"), indent=1, ensure_ascii=False)
        print("%s -> %s %s" % (os.path.basename(arm), res["status"], res.get("composite") if res["status"] == "SCORED" else res["failed_as"]))
    rows = report.write(a.results, w, a.corpora, a.include)
    print("leaderboard: %d arms -> %s" % (len(rows), os.path.join(a.results, "leaderboard.md")))
    if refused:
        sys.exit("error: %d arm(s) not scored because the judge never produced usable output: %s" % (len(refused), ", ".join(refused)))


if __name__ == "__main__":
    main()
