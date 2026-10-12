"""Mechanical fact scoring: latest value present = credit; uncued stale/decoy value = penalty."""
from __future__ import annotations

import re

from .textnorm import find, has, norm

CUE = re.compile(r"\b(was|were|earlier|previously|originally|before|changed|moved|instead|rather than|not|no longer|switched|replaced|"
                 r"corrected|superseded|from|initially|old|formerly|rescheduled|bumped|raised|updated|revised|stale|dropped|scrapped|"
                 r"rejected|considered|unrelated|ruled out|slipped|slip|ignored?|decoy|never|wasn't|isn't|until|then|now)\b")


def cued(s: str, i: int, j: int, window: int = 70) -> bool:
    """A superseded/decoy value is acceptable when a supersession cue sits next to it on the same line."""
    a = s.rfind("\n", 0, i) + 1
    b = s.find("\n", j)
    b = len(s) if b < 0 else b
    ctx = s[max(a, i - window):min(b, j + window)]
    return bool(CUE.search(ctx))


def _uncued_hits(s: str, aliases):
    hits = []
    for a in aliases:
        for i, j in find(s, a):
            if not cued(s, i, j):
                hits.append(a)
                break
    return hits


def latest_present(s: str, f: dict) -> bool:
    if any(has(s, a) for a in f["aliases"]):
        return True
    return bool(f.get("regex") and re.search(f["regex"], s))


def score_facts(summary: str, gt: dict) -> dict:
    s = norm(summary)
    rows, credit, penalty, total = [], 0.0, 0.0, 0.0
    for f in gt["facts"]:
        w = f.get("weight", 1)
        total += w
        hit = latest_present(s, f)
        stale_hits = []
        for st in f.get("stale", []):
            stale_hits += _uncued_hits(s, st["aliases"])
        rows.append({"id": f["id"], "hit": hit, "stale_hits": stale_hits, "weight": w})
        credit += w if hit else 0
        if stale_hits:
            penalty += 0.5 * w
    decoy_hits = []
    for d in gt.get("decoys", []):
        h = _uncued_hits(s, d["aliases"])
        if h:
            decoy_hits.append({"id": d["id"], "alias": h[0]})
            penalty += 0.5
    return {
        "recall": round(credit / total, 4),
        "net": round(max(0.0, credit - penalty) / total, 4),
        "found": sum(1 for r in rows if r["hit"]), "total": len(rows),
        "stale_fact_count": sum(1 for r in rows if r["stale_hits"]),
        "decoy_hits": decoy_hits,
        "missed": [r["id"] for r in rows if not r["hit"]],
        "rows": rows,
    }
