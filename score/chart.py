"""python -m score.chart results/leaderboard.csv [out.png]   (needs matplotlib)

One panel per component, same row order: composite, facts net, threads (judge P/PA/L), invention (mechanical per 100 checked + judge), latency.
Sakura theme: see score/theme.py."""
import csv
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

from .theme import BG, BLUSH, DEEP, GOLD, GREY, GRID, INK, PANEL, PINK, SAGE, SERIF, SOFT, TH, petal_flower, rbar

W_IN, DPI = 21.0, 110  # ~2310 px wide at dpi 110; saved at 2x -> sharp on phones


def _f(v):
    return float(v) if v not in (None, "") else None


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.rsplit(".", 1)[0] + ".png"
    rows = list(csv.DictReader(open(src)))
    n = len(rows)
    rows.reverse()
    corpus = rows[0]["corpus"] if rows else ""
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "text.color": INK, "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": INK})
    row_h = 0.78
    fig_h = row_h * n + 3.3
    fig = plt.figure(figsize=(W_IN, fig_h), facecolor=BG)
    top, bot = 1 - 1.95 / fig_h, 0.55 / fig_h
    left, right = 0.175, 0.985
    ratios = [1.15, 1.45, 1.35, 1.5, 0.95]
    gap = 0.012
    tot = (right - left) - gap * 4
    axs, x = [], left
    for rt in ratios:
        w = tot * rt / sum(ratios)
        axs.append(fig.add_axes([x, bot, w, top - bot], facecolor=PANEL))
        x += w + gap
    ac, af, at, ai, al = axs
    vmax_lat = max([_f(r["latency_s"]) or 0 for r in rows] + [1])
    pimax = max([_f(r.get("invention_mech_per100")) or 0 for r in rows] + [1])
    ac.set_xlim(0, 150)
    af.set_xlim(0, 225)
    at.set_xlim(0, 15)
    ai.set_xlim(0, pimax * 2.6)
    al.set_xlim(0, vmax_lat * 1.45)
    for a in axs:
        a.set_ylim(-0.6, n - 0.4)

    best = max(range(n), key=lambda i: (_f(rows[i]["composite"]) or -1, i))
    # leader highlight band across all panels
    for a in axs:
        a.add_patch(FancyBboxPatch((a.get_xlim()[0], best - 0.46), a.get_xlim()[1] - a.get_xlim()[0], 0.92, boxstyle="round,pad=0,rounding_size=0.25", fc=BLUSH, ec="none", alpha=0.45, zorder=0, mutation_aspect=1 / 60 * (a.get_xlim()[1] - a.get_xlim()[0]) / 1))

    for i, r in enumerate(rows):
        if not r["composite"]:
            for a in axs:
                rbar(a, i, a.get_xlim()[0], a.get_xlim()[1] * 0.98, "#E4DDE0", lw=11, alpha=0.7)
            ac.text(3, i, "FAILED · " + r["status"], va="center", fontsize=10, color=SOFT, style="italic", zorder=5)
            continue
        lead = i == best
        comp = float(r["composite"])
        rbar(ac, i, 0, comp, DEEP if lead else PINK)
        ac.text(104, i + 0.1, r["composite"], va="center", fontsize=11, fontweight="bold" if lead else "normal")
        if r.get("composite_v1"):
            v1 = float(r["composite_v1"])
            ac.plot(v1, i, marker="D", color=GOLD, markersize=6, mec="white", mew=0.8, linestyle="none", zorder=6)
            ac.text(104, i - 0.2, "◆ v1 %s" % r["composite_v1"], va="center", fontsize=9.5, color=GOLD)
        fn = _f(r["facts_net_pct"])
        rbar(af, i, 0, fn, DEEP if lead else PINK)
        af.text(104, i, "%s%%" % r["facts_net_pct"], va="center", fontsize=10.5, fontweight="bold" if lead else "normal")
        af.text(104, i - 0.2, "%s/%s found · stale %s · decoy %s" % (r["facts_found"], r["facts_total"], r["stale_facts"], r["decoy_hits"]), va="center", fontsize=9.5, color=SOFT)
        if r["threads_judge_preserved"] != "":
            p, pa, l = (int(r["threads_judge_%s" % k]) for k in ("preserved", "partial", "lost"))
            src_t = "judge"
        else:
            p, pa, l = (int(r["threads_mech_%s" % k]) for k in ("preserved", "partial", "lost"))
            src_t = "mech"
        lf = 0
        for k, v in (("P", p), ("PA", pa), ("L", l)):
            rbar(at, i, lf, lf + v, TH[k], lw=11)
            lf += v
        at.text(8.4, i + 0.1, "%d/%d/%d" % (p, pa, l), va="center", fontsize=10.5)
        at.text(8.4, i - 0.2, "score %.2f (%s)" % ((p + 0.5 * pa) / 8, src_t), va="center", fontsize=9.5, color=SOFT)
        pi_ = _f(r.get("invention_mech_per100")) or 0
        if pi_ > 0:
            rbar(ai, i, 0, pi_, "#D9607F")
        else:
            ai.plot(0.02, i, marker="o", color=SAGE, markersize=7, zorder=4)
        ai.text(pimax * 1.08 + 0.1, i + 0.1, "%.2f per 100" % pi_, va="center", fontsize=10.5)
        ai.text(pimax * 1.08 + 0.1, i - 0.2, "mech %s/%s checked · judge %s" % (r["invention_mech"], r["invention_checked"], r["invention_judge"] or "n/a"), va="center", fontsize=9.5, color=SOFT)
        lat = _f(r["latency_s"])
        if lat is not None:
            rbar(al, i, 0, lat, GREY, alpha=0.8)
            al.text(max(lat, vmax_lat * 0.04) + vmax_lat * 0.05, i, "%.0fs" % lat, va="center", fontsize=10)
        else:
            al.text(2, i, "n/a", va="center", fontsize=10, color=SOFT)

    ac.set_yticks(range(n))
    ac.set_yticklabels([""] * n)
    for i, r in enumerate(rows):
        m = r["model"] + (" ★" if i == best else "")
        ac.text(-0.03, i + 0.12, "%s · %s" % (m, r["effort"]), transform=ac.get_yaxis_transform(), ha="right", va="center", fontsize=11.5, fontweight="bold" if i == best else "normal")
        ac.text(-0.03, i - 0.2, "ran via %s · graded by %s" % (r.get("transport") or "openai", r.get("judge_model") or "?"), transform=ac.get_yaxis_transform(), ha="right", va="center", fontsize=9.5, color=SOFT)
    titles = ["composite v2", "facts net %", "threads of 8", "made-up claims per 100 checked", "latency"]
    subs = ["◆ = old v1", "latest-value credit", "preserved / partial / lost", "lower is better", "seconds"]
    for a, t, s in zip(axs, titles, subs):
        a.set_title(t, fontsize=13, family=SERIF, color=INK, loc="left", pad=22)
        a.text(0, 1.012, s, transform=a.transAxes, fontsize=8.5, color=SOFT, va="bottom")
        a.grid(axis="x", color=GRID, lw=0.8, ls=(0, (3, 4)), zorder=1)
        a.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            a.spines[sp].set_visible(False)
        a.spines["bottom"].set_color(GRID)
        a.tick_params(axis="y", left=False, labelleft=False)
        a.tick_params(axis="x", length=0, labelsize=8.5)
    af.axvline(100, color=SOFT, lw=0.8, ls=":", zorder=2)
    ac.set_xticks([0, 25, 50, 75, 100])
    af.set_xticks([0, 25, 50, 75, 100])
    at.set_xticks([0, 2, 4, 6, 8])
    ai.set_xticks(range(0, int(pimax) + 2))
    ai.set_xlim(0, pimax * 2.6)
    al.set_xticks(range(0, int(vmax_lat) + 1, 100 if vmax_lat > 200 else 20))
    al.set_xlim(0, vmax_lat * 1.45)

    handles = [Line2D([], [], marker="D", color=GOLD, ls="none", markersize=6, label="composite v1 (old)"),
               *[Line2D([], [], marker="o", color=TH[k], ls="none", markersize=8, label=lab) for k, lab in (("P", "preserved"), ("PA", "partial"), ("L", "lost"))],
               Line2D([], [], marker="o", color=SAGE, ls="none", markersize=7, label="zero made-up claims")]
    fig.legend(handles=handles, loc="lower right", ncol=5, fontsize=9, frameon=False, bbox_to_anchor=(right, 0.0), labelcolor=INK)
    fig.text(left, 0.012, "composite v2 = 100·(0.45 facts + 0.30 threads + 0.25 · 1/(1+auto_flags/3))   ·   grey bars FAILED" , fontsize=8.5, color=SOFT)

    fig.text(0.03, 1 - 0.62 / fig_h, "threadkeeper · summary leaderboard (%s)" % corpus, fontsize=27, family=SERIF, color=INK, va="center")
    fig.text(0.03, 1 - 1.12 / fig_h, "corpus %s  ·  grader rule: graded by a different model than the one run  ·  CLI arms ran in text mode" % corpus, fontsize=11, color=SOFT, va="center")
    # ornament: blossoms in header margin (overlay axes, behind nothing important)
    ov = fig.add_axes([0, 0, 1, 1], facecolor="none", zorder=-1)
    ov.set_axis_off()
    ov.set_xlim(0, 1)
    ov.set_ylim(0, 1)
    hy = 1 - 0.7 / fig_h
    ov.plot([0.80, 0.86, 0.915, 0.985], [hy + 0.012, hy + 0.028, hy + 0.012, hy + 0.034], color="#B98C7A", lw=2.2, alpha=0.45, solid_capstyle="round")
    rnd = random.Random(7)
    for bx, by, br in [(0.83, hy + 0.034, .011), (0.885, hy + 0.036, .013), (0.945, hy + 0.024, .010), (0.975, hy + 0.044, .012)]:
        petal_flower(ov, bx, by, r=br * 0.62 / (fig_h / 6) * 1.0, rot=rnd.random() * 6, alpha=0.6)
    for _ in range(9):
        petal_flower(ov, rnd.uniform(0.55, 0.78), 1 - rnd.uniform(0.25, 1.5) / fig_h, r=rnd.uniform(0.004, 0.007), rot=rnd.random() * 6, color=PINK, alpha=rnd.uniform(0.25, 0.5))
    fig.savefig(out, dpi=DPI * 2 // 1, facecolor=BG)
    print("wrote", out)


if __name__ == "__main__":
    main()
