"""Leaderboard (markdown + CSV) from score.json files."""
from __future__ import annotations

import csv
import glob
import json
import os

from . import weights as weights_mod

COLS = ["model", "effort", "corpus", "transport", "judge_model", "judge_ok", "status", "composite", "composite_v1", "facts_found", "facts_total", "facts_net_pct", "stale_facts", "decoy_hits",
        "threads_judge_preserved", "threads_judge_partial", "threads_judge_lost", "threads_mech_preserved", "threads_mech_partial", "threads_mech_lost", "threads_source",
        "invention_mech", "invention_judge", "latency_s", "prompt_tokens", "completion_tokens", "reasoning_tokens", "cost_usd", "finish_reason"]

# The breakdown is mandatory: a composite is never emitted without these (enforced by check_breakdown + tests/test_breakdown.py).
# (markdown header, row key(s)). Order is the board's column order.
BREAKDOWN = [
    ("status", ["status"]), ("composite", ["composite"]), ("composite_v1", ["composite_v1"]),
    ("facts found/total", ["facts_found", "facts_total"]), ("facts net %", ["facts_net_pct"]),
    ("stale", ["stale_facts"]), ("decoy hits", ["decoy_hits"]),
    ("threads judge P/PA/L", ["threads_judge_preserved", "threads_judge_partial", "threads_judge_lost"]),
    ("threads mech P/PA/L", ["threads_mech_preserved", "threads_mech_partial", "threads_mech_lost"]),
    ("invention mech", ["invention_mech"]), ("invention judge", ["invention_judge"]),
    ("latency s", ["latency_s"]), ("prompt tok", ["prompt_tokens"]), ("completion tok", ["completion_tokens"]), ("reasoning tok", ["reasoning_tokens"]),
    ("judge", ["judge_model"]), ("transport", ["transport"]),
]
# keys that may legitimately be None on a SCORED row (rendered "n/a"): judge-derived, and usage the transport does not report
MAY_BE_NA = {"threads_judge_preserved", "threads_judge_partial", "threads_judge_lost", "invention_judge", "prompt_tokens", "completion_tokens", "reasoning_tokens", "latency_s"}


def _strip():
    """Test hook (mutant): TK_STRIP_COLUMN=<header> drops that column from every output, so the breakdown test must fail."""
    return os.environ.get("TK_STRIP_COLUMN")


class BreakdownMissing(Exception):
    pass


def check_breakdown(row: dict):
    """Raise if a row carries a composite without its full breakdown."""
    if row.get("composite") is None:
        return
    for head, keys in BREAKDOWN:
        for k in keys:
            if k not in row or (row[k] is None and k not in MAY_BE_NA):
                raise BreakdownMissing("composite %s for %s/%s emitted without breakdown field %r (%s)" % (row.get("composite"), row.get("model"), row.get("effort"), k, head))


def _pla(d):
    return [list(d.values()).count(k) for k in ("PRESERVED", "PARTIAL", "LOST")]


def row_of(score: dict, meta: dict) -> dict:
    u = (meta.get("usage") or {})
    if "modelUsage" in u:  # claude CLI json
        c = u.get("usage") or {}
        u = {"prompt_tokens": sum(c.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
             "completion_tokens": c.get("output_tokens"),
             "completion_tokens_details": {"reasoning_tokens": (c.get("output_tokens_details") or {}).get("thinking_tokens")}}
    det = u.get("completion_tokens_details") or {}
    r = {"model": meta.get("model"), "effort": meta.get("effort"), "corpus": meta.get("corpus"),
         "transport": meta.get("transport", "openai"), "latency_s": meta.get("latency_s"), "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
         "reasoning_tokens": det.get("reasoning_tokens"), "cost_usd": meta.get("cost_usd"), "finish_reason": meta.get("finish_reason")}
    st = score["status"]
    j = score.get("judge") or {}
    r["judge_model"] = j.get("model") or "none"
    r["judge_ok"] = (j.get("failed_calls", 0) == 0) if j.get("model") else None
    if j.get("model") is None and j.get("note"):
        r["judge_model"] = "none (%s)" % j["note"][:60]
    if st == "FAILED":
        r["status"] = "FAILED (%s)" % score["failed_as"]
        r["composite"] = r["composite_v1"] = None
    elif st == "SCORED":
        f, t, inv = score["facts"], score["threads"], score["invention"]
        jt = t.get("judge") or {}
        jc = _pla(jt["verdicts"]) if jt.get("verdicts") and jt.get("parsed") else [None] * 3
        mc = _pla(t["mechanical"])
        r.update(status="SCORED", composite=score["composite"], composite_v1=score.get("composite_v1"), facts_found=f["found"], facts_total=f["total"],
                 facts_net_pct=round(100 * f["net"], 1), stale_facts=f["stale_fact_count"], decoy_hits=len(f["decoy_hits"]),
                 threads_judge_preserved=jc[0], threads_judge_partial=jc[1], threads_judge_lost=jc[2],
                 threads_mech_preserved=mc[0], threads_mech_partial=mc[1], threads_mech_lost=mc[2],
                 threads_source=t["final_source"], invention_mech=inv["mechanical"]["count"],
                 invention_judge=(inv["judge"]["count"] if inv["judge"] else None))
    else:
        r["status"] = st
        r["composite"] = r["composite_v1"] = None
    check_breakdown(r)
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


def _cell(r, keys, scored):
    if not scored and keys[0] not in ("status", "judge_model", "transport", "latency_s", "prompt_tokens", "completion_tokens", "reasoning_tokens"):
        return "-"
    vals = ["n/a" if r.get(k) is None else r.get(k) for k in keys]
    if keys[0] in ("composite", "composite_v1"):
        return "%.1f" % r[keys[0]]
    if len(keys) == 2:
        return "%s/%s" % tuple(vals)
    if len(keys) == 3:
        return "/".join(str(v) for v in vals)
    return str(vals[0])


def corpus_hashes(rows, corpora_dir):
    try:
        man = json.load(open(os.path.join(corpora_dir, "MANIFEST.json")))
    except OSError:
        return {}
    return {c: man[c]["sha256"]["session.jsonl"] for c in sorted({r["corpus"] for r in rows}) if c in man}


def write(results_dir, w=None, corpora_dir="corpora"):
    rows = collect(results_dir)
    drop = _strip()
    cols = [c for c in COLS if not (drop and drop in [h for h, ks in BREAKDOWN if c in ks])]
    with open(os.path.join(results_dir, "leaderboard.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=cols)
        wr.writeheader()
        for r in rows:
            wr.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})
    bd = [(h, ks) for h, ks in BREAKDOWN if h != drop]
    hdr = ["#", "model", "effort", "corpus"] + [h for h, _ in bd]
    hashes = corpus_hashes(rows, corpora_dir)
    lines = ["# threadkeeper leaderboard", "",
             "**composite** (v2): `%s`" % weights_mod.formula(w), "",
             "**composite_v1** (kept for old comparisons): `%s`" % weights_mod.FORMULA_V1, "",
             "Corpus session.jsonl sha256: " + ("; ".join("%s=`%s`" % kv for kv in hashes.items()) or "n/a"), "",
             "Never read a composite alone: every row carries its breakdown, the judge that graded it and the transport. "
             "FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. "
             "`invention mech` is the mechanical cross-check; `invention judge` is a ranking signal, never ground truth.", "",
             "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for i, r in enumerate(rows, 1):
        scored = r["composite"] is not None
        cells = [i if scored else "-", r["model"], r["effort"], r["corpus"]] + [_cell(r, ks, scored) for _, ks in bd]
        if not r.get("judge_ok", True):
            cells[-2] = str(cells[-2]) + " (JUDGE CALL FAILED)"
        lines.append("| " + " | ".join(str(x) for x in cells) + " |")
    open(os.path.join(results_dir, "leaderboard.md"), "w").write("\n".join(lines) + "\n")
    return rows
