"""python -m score.chart results/leaderboard.csv [out.png]   (needs matplotlib)

One panel per component, same row order: composite, facts net, threads (judge P/PA/L), invention (mechanical per 100 checked + judge), latency."""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, RED, GREY = "#2a6fb0", "#e08a1e", "#b03a2e", "#8a8f98"
TH = {"P": "#2e8b57", "PA": "#e0b81e", "L": RED}


def _f(v):
    return float(v) if v not in (None, "") else None


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.rsplit(".", 1)[0] + ".png"
    rows = list(csv.DictReader(open(src)))
    rows.reverse()
    n = len(rows)
    labels = ["%s  [effort: %s]\nran via %s · graded by %s" % (r["model"], r["effort"], r.get("transport") or "openai", r.get("judge_model") or "?") for r in rows]
    fig, axs = plt.subplots(1, 5, figsize=(26, 0.62 * n + 2.6), sharey=True, gridspec_kw={"width_ratios": [1.1, 1.1, 1.2, 1.5, 0.9], "wspace": 0.08})
    ac, af, at, ai, al = axs
    vmax_lat = max([_f(r["latency_s"]) or 0 for r in rows] + [1])
    pimax = max([_f(r.get("invention_mech_per100")) or 0 for r in rows] + [1])
    for i, r in enumerate(rows):
        if not r["composite"]:
            for a in axs:
                a.barh(i, 1, color="none", edgecolor=RED, hatch="//", width=1)
            ac.text(0.02, i, r["status"], va="center", fontsize=8, color=RED, transform=ac.get_yaxis_transform())
            continue
        ac.barh(i, float(r["composite"]), color=BLUE)
        ac.text(104, i, r["composite"] if not r.get("composite_v1") else "%s (v1 %s)" % (r["composite"], r["composite_v1"]), va="center", fontsize=8)
        if r.get("composite_v1"):
            ac.plot(float(r["composite_v1"]), i, marker="D", color=ORANGE, markersize=5, linestyle="none", label="composite_v1 (old)" if i == 0 else None)
        fn = _f(r["facts_net_pct"])
        af.barh(i, fn, color=BLUE)
        af.text(101, i, "%s%%\n%s/%s found · stale %s · decoy %s" % (r["facts_net_pct"], r["facts_found"], r["facts_total"], r["stale_facts"], r["decoy_hits"]), va="center", fontsize=7.5)
        if r["threads_judge_preserved"] != "":
            p, pa, l = (int(r["threads_judge_%s" % k]) for k in ("preserved", "partial", "lost"))
            src_t = "judge"
        else:
            p, pa, l = (int(r["threads_mech_%s" % k]) for k in ("preserved", "partial", "lost"))
            src_t = "mech"
        left = 0
        for k, v in (("P", p), ("PA", pa), ("L", l)):
            at.barh(i, v, left=left, color=TH[k], label={"P": "preserved", "PA": "partial", "L": "lost"}[k] if i == 0 else None)
            left += v
        at.text(8.3, i, "%d/%d/%d\nscore %.2f (%s)" % (p, pa, l, (p + 0.5 * pa) / 8, src_t), va="center", fontsize=8)
        pi_ = _f(r.get("invention_mech_per100")) or 0
        ai.barh(i, pi_, color=RED)
        ai.text(pimax * 1.05 + 0.1, i, "mech %s/%s checked\n= %.2f per 100 · judge %s" % (r["invention_mech"], r["invention_checked"], pi_, r["invention_judge"] or "n/a"), va="center", fontsize=7.5)
        lat = _f(r["latency_s"])
        if lat is not None:
            al.barh(i, lat, color=GREY)
            al.text(lat + vmax_lat * 0.02, i, "%.0fs" % lat, va="center", fontsize=8)
        else:
            al.text(2, i, "n/a", va="center", fontsize=8)
    ac.set_yticks(range(n), labels, fontsize=8)
    ac.set_xlim(0, 150)
    ac.set_title("composite v2 (◆ = old v1)", fontsize=10)
    af.set_xlim(0, 175)
    af.axvline(100, color="k", lw=.5)
    af.set_title("facts net % (latest-value credit)", fontsize=10)
    at.set_xlim(0, 15)
    at.set_title("threads (judge P/PA/L of 8)", fontsize=10)
    ai.set_xlim(0, pimax * 2.6)
    ai.set_title("invention: mechanical per 100 checked\n(lower is better; judge count is not comparable across judges)", fontsize=9)
    al.set_xlim(0, vmax_lat * 1.15)
    al.set_title("latency (s)", fontsize=10)
    for a in axs:
        a.grid(axis="x", alpha=0.2)
    for a in (af, at, ai, al):
        a.tick_params(axis="y", left=False)
    ac.legend(loc="lower left", fontsize=7)
    at.legend(loc="lower right", fontsize=7, ncol=3)
    fig.suptitle("threadkeeper: context-compaction quality, %s corpus   composite v2 = 100*(.45 facts + .30 threads + .25 · 1/(1+mech_inventions/3))   hatched = FAILED" % (rows[0]["corpus"] if rows else ""), fontsize=11, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out, dpi=110)
    print("wrote", out)


if __name__ == "__main__":
    main()
