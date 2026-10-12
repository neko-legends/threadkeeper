"""Thread scoring. Mechanical keyword fallback + judge-based (see judge.py)."""
from __future__ import annotations

from .textnorm import has, norm

POINTS = {"PRESERVED": 1.0, "PARTIAL": 0.5, "LOST": 0.0}


def mechanical(summary: str, gt: dict) -> dict:
    s = norm(summary)
    out = {}
    for t in gt["threads"]:
        groups = [any(has(s, k) for k in g) for g in t["keywords"]]
        out[t["id"]] = "PRESERVED" if all(groups) else "PARTIAL" if any(groups) else "LOST"
    return out


def points(verdicts: dict) -> float:
    return round(sum(POINTS[v] for v in verdicts.values()) / max(1, len(verdicts)), 4)
