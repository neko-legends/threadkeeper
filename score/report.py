"""Leaderboard (markdown + CSV) from score.json files."""
from __future__ import annotations

import csv
import glob
import json
import os

COLS = ["model", "effort", "corpus", "status", "composite", "facts_found", "facts_total", "facts_net_pct", "stale_facts", "decoy_hits",
        "threads_preserved", "threads_partial", "threads_lost", "threads_source", "invention_mech", "invention_judge",
        "latency_s", "prompt_tokens", "completion_tokens", "reasoning_tokens", "cost_usd", "finish_reason"]


def row_of(score: dict, meta: dict) -> dict:
    u = (meta.get("usage") or {})
    det = u.get("completion_tokens_details") or {}
    r = {"model": meta.get("model"), "effort": meta.get("effort"), "corpus": meta.get("corpus"),
         "latency_s": meta.get("latency_s"), "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
         "reasoning_tokens": det.get("reasoning_tokens"), "cost_usd": meta.get("cost_usd"), "finish_reason": meta.get("finish_reason")}
    st = score["status"]
    if st == "FAILED":
        r["status"] = "FAILED (%s)" % score["failed_as"]
        r["composite"] = None
    elif st == "SCORED":
        f, t, inv = score["facts"], score["threads"], score["invention"]
        r.update(status="SCORED", composite=score["composite"], facts_found=f["found"], facts_total=f["total"],
                 facts_net_pct=round(100 * f["net"], 1), stale_facts=f["stale_fact_count"], decoy_hits=len(f["decoy_hits"]),
                 threads_preserved=t["counts"]["PRESERVED"], threads_partial=t["counts"]["PARTIAL"], threads_lost=t["counts"]["LOST"],
                 threads_source=t["final_source"], invention_mech=inv["mechanical"]["count"],
                 invention_judge=(inv["judge"]["count"] if inv["judge"] else None))
    else:
        r["status"] = st
        r["composite"] = None
    return r


def collect(results_dir):
    rows = []
    for sp in sorted(glob.glob(os.path.join(results_dir, "*", "score.json"))):
        d = os.path.dirname(sp)
        score = json.load(open(sp))
        meta = json.load(open(os.path.join(d, "meta.json")))
        rows.append(row_of(score, meta))
    rows.sort(key=lambda r: (r["composite"] is None, -(r["composite"] or 0), str(r["model"]), str(r["effort"])))
    return rows


def write(results_dir):
    rows = collect(results_dir)
    with open(os.path.join(results_dir, "leaderboard.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in COLS})
    hdr = ["#", "model", "effort", "corpus", "status", "score", "facts", "stale/decoy", "threads P/PA/L", "invention mech/judge", "latency s", "tok p/c/r", "cost $"]
    lines = ["# threadkeeper leaderboard", "",
             "FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. `invention judge` is a ranking signal, not ground truth.", "",
             "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for i, r in enumerate(rows, 1):
        sc = r["composite"]
        lines.append("| " + " | ".join(str(x) for x in [
            i if sc is not None else "-", r["model"], r["effort"], r["corpus"], r["status"],
            "%.1f" % sc if sc is not None else "-",
            "%s/%s (%s%%)" % (r.get("facts_found"), r.get("facts_total"), r.get("facts_net_pct")) if sc is not None else "-",
            "%s/%s" % (r.get("stale_facts"), r.get("decoy_hits")) if sc is not None else "-",
            "%s/%s/%s" % (r.get("threads_preserved"), r.get("threads_partial"), r.get("threads_lost")) if sc is not None else "-",
            "%s/%s" % (r.get("invention_mech"), r.get("invention_judge") if r.get("invention_judge") is not None else "n/a") if sc is not None else "-",
            r.get("latency_s"), "%s/%s/%s" % (r.get("prompt_tokens"), r.get("completion_tokens"), r.get("reasoning_tokens")),
            r.get("cost_usd") if r.get("cost_usd") is not None else "n/a"]) + " |")
    open(os.path.join(results_dir, "leaderboard.md"), "w").write("\n".join(lines) + "\n")
    return rows
