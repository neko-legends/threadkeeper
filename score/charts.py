"""python -m score.charts results/leaderboard.csv [outdir] [--corpus 128k]   (needs matplotlib)

Writes outdir/chart-{overall,facts,threads,madeup,speed}.png, one per question, rows in the CSV's own rank order
(so the ★ is always CSV row 1 of that corpus). `python -m score.charts --judges results docs` draws the
before/after judge comparison. Plain rectangular bars: a short bar stays a bar, a zero is labelled, never a dot.
Numbers come only from the CSV/score files; nothing is estimated. Sakura theme: score/theme.py."""
from __future__ import annotations

import csv
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .theme import BG, DEEP, GOLD, GREY, GRID, INK, PANEL, PINK, SAGE, SERIF, SOFT, TH

NAME_FS, VAL_FS, SUB_FS = 17, 15, 12.5
DPI = 130


def _f(v):
    return float(v) if v not in (None, "") else None


def load(csv_path, corpus="128k"):
    """Rows of one corpus in CSV (= board rank) order, FAILED rows included at the end."""
    return [r for r in csv.DictReader(open(csv_path)) if r["corpus"] == corpus]


def label(r):
    return "%s · %s" % (r["model"], r["effort"])


def _canvas(rows, title, sub, xlim, width=17.0):
    n = len(rows)
    fig, ax = plt.subplots(figsize=(width, 1.0 + 0.62 * n + 1.6), facecolor=BG)
    ax.set_facecolor(PANEL)
    ax.set_ylim(n - 0.4, -0.7)
    ax.set_xlim(*xlim)
    ax.set_yticks(range(n))
    best = next((i for i, r in enumerate(rows) if r["composite"]), None)
    ax.set_yticklabels([label(r) + (" ★" if i == best else "") for i, r in enumerate(rows)], fontsize=NAME_FS, color=INK)
    for t, i in zip(ax.get_yticklabels(), range(n)):
        if i == best:
            t.set_fontweight("bold")
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", labelsize=12, colors=SOFT, length=0)
    ax.grid(axis="x", color=GRID, lw=1, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    fig.suptitle(title, x=0.01, ha="left", fontsize=26, family=SERIF, color=INK, y=0.985)
    fig.text(0.01, 0.905 if n < 14 else 0.925, sub, ha="left", fontsize=SUB_FS, color=SOFT)
    fig.subplots_adjust(left=0.27, right=0.985, top=0.86, bottom=0.08)
    return fig, ax, best


def _failed(ax, i, r, x):
    ax.text(x, i, "FAILED (%s): %s" % (r["status"].split("(")[-1].rstrip(")"), (r.get("failed_reason") or "")[:60]), va="center", fontsize=SUB_FS + 1, color=SOFT, style="italic")


def _save(fig, outdir, name):
    p = os.path.join(outdir, name)
    fig.savefig(p, dpi=DPI, facecolor=BG)
    plt.close(fig)
    print("wrote", p)
    return p


def overall(rows, outdir, corpus):
    fig, ax, best = _canvas(rows, "Overall score · %s" % corpus, "composite v2 (0-100, higher is better) · ◆ = old v1 · ★ = rank 1 on the board · grey = failed the summary gate", (0, 118))
    ax.set_xticks([0, 25, 50, 75, 100])
    for i, r in enumerate(rows):
        if not r["composite"]:
            _failed(ax, i, r, 2)
            continue
        c = float(r["composite"])
        ax.barh(i, c, height=0.62, color=DEEP if i == best else PINK, zorder=3)
        ax.text(max(c, float(r.get("composite_v1") or 0)) + 1.8, i, r["composite"], va="center", fontsize=VAL_FS, fontweight="bold" if i == best else "normal", color=INK)
        if r.get("composite_v1"):
            ax.plot(float(r["composite_v1"]), i, marker="D", color=GOLD, markersize=9, mec="white", mew=1, ls="none", zorder=5)
    return _save(fig, outdir, "chart-overall.png")


def facts(rows, outdir, corpus):
    fig, ax, best = _canvas(rows, "Facts kept · %s" % corpus, "net % of the 50 planted facts (latest value gets credit, stale values cost points)", (0, 135))
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.axvline(100, color=SOFT, lw=1, ls=":", zorder=2)
    for i, r in enumerate(rows):
        if not r["composite"]:
            _failed(ax, i, r, 2)
            continue
        v = float(r["facts_net_pct"])
        ax.barh(i, max(v, 0), height=0.62, color=DEEP if i == best else PINK, zorder=3)
        ax.text(max(v, 0) + 1.5, i, "%s%%   %s/%s found · stale %s · decoy %s" % (r["facts_net_pct"], r["facts_found"], r["facts_total"], r["stale_facts"], r["decoy_hits"]), va="center", fontsize=VAL_FS - 1, color=INK)
    return _save(fig, outdir, "chart-facts.png")


def threads(rows, outdir, corpus):
    fig, ax, best = _canvas(rows, "Open threads kept · %s" % corpus, "of 8 unfinished tasks: preserved / partial / lost (judge's verdict; mechanical match if no judge ran)", (0, 13.5))
    ax.set_xticks(range(0, 9))
    for i, r in enumerate(rows):
        if not r["composite"]:
            _failed(ax, i, r, 0.1)
            continue
        src = "judge" if r["threads_judge_preserved"] != "" else "mech"
        p, pa, l = (int(r["threads_%s_%s" % (src, k)]) for k in ("preserved", "partial", "lost"))
        left = 0
        for v, k in ((p, "P"), (pa, "PA"), (l, "L")):
            if v:
                ax.barh(i, v, left=left, height=0.62, color=TH[k], edgecolor="white", lw=1.5, zorder=3)
            left += v
        ax.text(8.25, i, "%d / %d / %d   (%s)" % (p, pa, l, src), va="center", fontsize=VAL_FS - 1, color=INK)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=TH[k]) for k in ("P", "PA", "L")], labels=["preserved", "partial", "lost"], loc="lower right", fontsize=13, frameon=False, ncol=3)
    return _save(fig, outdir, "chart-threads.png")


def madeup(rows, outdir, corpus):
    mx = max([_f(r.get("invention_mech_per100")) or 0 for r in rows] + [1])
    fig, ax, best = _canvas(rows, "Made-up claims · %s" % corpus, "automatic check: quotes, numbers and hashes not found in the chat, per 100 checked · lower is better · green 0 = none found", (0, mx * 2.4))
    for i, r in enumerate(rows):
        if not r["composite"]:
            _failed(ax, i, r, 0.05)
            continue
        v = _f(r.get("invention_mech_per100")) or 0
        extra = "%s of %s checked · judge flags %s" % (r["invention_mech"], r["invention_checked"], r["invention_judge"] if r["invention_judge"] != "" else "n/a")
        if v > 0:
            ax.barh(i, v, height=0.62, color="#D9607F", zorder=3)
            ax.text(v + mx * 0.04, i, "%.2f   %s" % (v, extra), va="center", fontsize=VAL_FS - 1, color=INK)
        else:
            ax.text(mx * 0.02, i, "0", va="center", fontsize=VAL_FS + 2, fontweight="bold", color=SAGE)
            ax.text(mx * 0.12, i, extra, va="center", fontsize=VAL_FS - 1, color=INK)
    return _save(fig, outdir, "chart-madeup.png")


def speed(rows, outdir, corpus):
    mx = max([_f(r["latency_s"]) or 0 for r in rows] + [1])
    fig, ax, best = _canvas(rows, "Speed · %s" % corpus, "seconds to produce the summary (HTTP and CLI transports differ; see the board)", (0, mx * 1.2))
    for i, r in enumerate(rows):
        lat = _f(r["latency_s"])
        if lat is None:
            ax.text(mx * 0.01, i, "n/a", va="center", fontsize=VAL_FS, color=SOFT)
            continue
        ax.barh(i, lat, height=0.62, color=GREY, zorder=3)
        ax.text(lat + mx * 0.01, i, "%.0fs" % lat, va="center", fontsize=VAL_FS, color=INK)
    return _save(fig, outdir, "chart-speed.png")


def draw_all(csv_path, outdir, corpus="128k"):
    rows = load(csv_path, corpus)
    os.makedirs(outdir, exist_ok=True)
    return [f(rows, outdir, corpus) for f in (overall, facts, threads, madeup, speed)]


def _judge_rows(results):
    out = []
    for sp in sorted(glob.glob(os.path.join(results, "*", "score_multijudge.json"))):
        old, new = json.load(open(sp)), json.load(open(sp.replace("_multijudge", "")))
        if old.get("status") != "SCORED" or new.get("status") != "SCORED":
            continue
        inv = lambda d: ((d.get("invention") or {}).get("judge") or {}).get("count")
        out.append({"name": "%s · %s" % (old["model"], old["effort"]), "old": old["composite"], "old_judge": (old.get("judge") or {}).get("model"), "old_inv": inv(old),
                    "new": new["composite"], "new_judge": (new.get("judge") or {}).get("model"), "new_inv": inv(new)})
    return out


def judges(results, outdir):
    """chart-judges-before.png (superseded multi-judge board) and chart-judges-after.png (one neutral judge)."""
    data = _judge_rows(results)
    paths = []
    for which in ("old", "new"):
        rows = sorted(data, key=lambda d: -d[which])
        n = len(rows)
        before = which == "old"
        fig, ax = plt.subplots(figsize=(17, 1.0 + 0.66 * n + 1.8), facecolor=BG)
        ax.set_facecolor(PANEL)
        ax.set_ylim(n - 0.4, -0.7)
        ax.set_xlim(60, 178 if before else 118)
        ax.set_yticks(range(n))
        ax.set_yticklabels([r["name"] for r in rows], fontsize=NAME_FS, color=INK)
        ax.tick_params(axis="y", length=0, pad=8)
        ax.tick_params(axis="x", labelsize=12, colors=SOFT, length=0)
        ax.grid(axis="x", color=GRID, lw=1, zorder=0)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        for i, r in enumerate(rows):
            hot = r["name"].startswith("opus") and r["name"].endswith("max")
            ax.barh(i, r[which] - 60, left=60, height=0.62, color=DEEP if hot else PINK, zorder=3)
            ax.text(r[which] + 1, i, "%.1f   judge: %s · flagged inventions: %s" % (r[which], r["old_judge" if before else "new_judge"], r["old_inv" if before else "new_inv"]),
                    va="center", fontsize=VAL_FS - 2, color=INK, fontweight="bold" if hot else "normal")
            if hot and before:
                ax.annotate("Opus looked worst here only because Astra\n(a competitor) judged it: 7 flagged inventions\n-> 0 under a neutral judge",
                            xy=(140, i - 0.2), xytext=(126, i - 2.0), fontsize=13, color="#B23A5E", fontweight="bold", va="center", ha="left",
                            arrowprops=dict(arrowstyle="->", color="#B23A5E", lw=2), bbox=dict(boxstyle="round,pad=0.5", fc="#FFF0F3", ec="#B23A5E"))
        title = "SUPERSEDED: original multi-judge board (128k)" if before else "After: one neutral judge for every arm (128k)"
        sub = ("each arm graded by a DIFFERENT model, some of them competitors on this board: NOT comparable across rows. Kept for the record."
               if before else "judge: venice/gemini-3-8-flash, a family that is graded nowhere on this board. Same outputs, same mechanical checks. Axis starts at 60.")
        fig.suptitle(title, x=0.01, ha="left", fontsize=26, family=SERIF, color="#B23A5E" if before else INK, y=0.985)
        fig.text(0.01, 0.915, sub, ha="left", fontsize=SUB_FS, color=SOFT)
        fig.subplots_adjust(left=0.235, right=0.985, top=0.86, bottom=0.07)
        paths.append(_save(fig, outdir, "chart-judges-%s.png" % ("before" if before else "after")))
    return paths


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "text.color": INK, "axes.labelcolor": INK})
    if a and a[0] == "--judges":
        return judges(a[1], a[2])
    corpus = "128k"
    if "--corpus" in a:
        i = a.index("--corpus")
        corpus = a[i + 1]
        del a[i:i + 2]
    return draw_all(a[0], a[1] if len(a) > 1 else os.path.dirname(a[0]) or ".", corpus)


if __name__ == "__main__":
    main()
