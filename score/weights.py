"""The composite score, in one place.

v2 (current):  100 * (w_facts*facts_score + w_threads*threads_score + w_invention*invention_score)
    facts_score     = facts.net                       0..1 (latest-value credit already inside)
    threads_score   = threads.score                   0..1 (judge verdicts when the judge parsed, else mechanical; PRESERVED=1 PARTIAL=.5 LOST=0)
    invention_score = 1 / (1 + mechanical_inventions / 3)   no saturation: 0->1.00 1->.75 2->.60 3->.50 4->.43 7->.30
v1 (kept as `composite_v1` so older comparisons stay valid): 0.55/0.35/0.10 with 1-min(1, mechanical_inventions/10).
"""
from __future__ import annotations

WEIGHTS = {"facts": 0.45, "threads": 0.30, "invention": 0.25}
WEIGHTS_V1 = {"facts": 0.55, "threads": 0.35, "invention": 0.10}
INVENTION_HALF = 3.0  # invention_score = 1 / (1 + n / INVENTION_HALF)


def parse_weights(spec: str) -> dict:
    """'facts=0.45,threads=0.30,invention=0.25' -> dict; must name all three and sum to 1."""
    w = {k.strip(): float(v) for k, v in (p.split("=") for p in spec.split(","))}
    if set(w) != set(WEIGHTS) or abs(sum(w.values()) - 1) > 1e-6:
        raise ValueError("--weights needs facts,threads,invention summing to 1, got %r" % spec)
    return w


def invention_score(n: int) -> float:
    return 1.0 / (1.0 + n / INVENTION_HALF)


def formula(w: dict | None = None) -> str:
    w = w or WEIGHTS
    return ("composite = 100*(%.2f*facts_score + %.2f*threads_score + %.2f*invention_score); facts_score=facts.net; "
            "threads_score=threads.score (judge, else mechanical); invention_score=1/(1+mechanical_inventions/%g)"
            % (w["facts"], w["threads"], w["invention"], INVENTION_HALF))


FORMULA_V1 = "100*(0.55*facts_net + 0.35*threads + 0.10*(1-min(1,mechanical_inventions/10)))"


def composites(facts_net: float, threads_score: float, inv_mech: int, w: dict | None = None) -> dict:
    w = w or WEIGHTS
    v2 = 100 * (w["facts"] * facts_net + w["threads"] * threads_score + w["invention"] * invention_score(inv_mech))
    v1 = 100 * (WEIGHTS_V1["facts"] * facts_net + WEIGHTS_V1["threads"] * threads_score
                + WEIGHTS_V1["invention"] * (1 - min(1.0, inv_mech / 10.0)))
    return {"composite": round(v2, 2), "composite_v1": round(v1, 2),
            "composite_formula": formula(w), "composite_formula_v1": FORMULA_V1,
            "weights": dict(w), "weights_v1": dict(WEIGHTS_V1),
            "components": {"facts_score": round(facts_net, 4), "threads_score": round(threads_score, 4),
                           "invention_score": round(invention_score(inv_mech), 4), "mechanical_inventions": inv_mech}}
