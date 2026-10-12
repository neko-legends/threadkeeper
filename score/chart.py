"""python -m score.chart results/leaderboard.csv [out.png]   (needs matplotlib)"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.rsplit(".", 1)[0] + ".png"
    rows = list(csv.DictReader(open(src)))
    rows.reverse()
    labels = ["%s  [effort: %s]\nran via %s \u00b7 graded by %s" % (r["model"], r["effort"], r.get("transport") or "openai", r.get("judge_model") or "?") for r in rows]
    fig, ax = plt.subplots(figsize=(12, 0.6 * len(rows) + 1.8))
    for i, r in enumerate(rows):
        if r["composite"]:
            ax.barh(i, float(r["composite"]), color="#2a6fb0")
            ax.text(101, i, "%s  (inv mech %s, judge %s)" % (r["composite"], r["invention_mech"], r["invention_judge"] or "n/a"), va="center", fontsize=8)
            if r.get("composite_v1"):
                ax.plot(float(r["composite_v1"]), i, marker="D", color="#e08a1e", markersize=5, linestyle="none", label="composite_v1 (old)" if i == 0 else None)
        else:
            ax.barh(i, 100, color="none", edgecolor="#b03a2e", hatch="//")
            ax.text(3, i, r["status"], va="center", fontsize=8, color="#b03a2e")
    ax.set_yticks(range(len(rows)), labels, fontsize=8)
    ax.set_xlim(0, 130)
    ax.legend(loc="lower left", fontsize=7)
    ax.set_xlabel("composite v2 = 100*(.45 facts + .30 threads + .25 1/(1+inventions/3)); orange diamond = old v1; hatched = FAILED")
    ax.set_title("threadkeeper: context-compaction quality, %s corpus (higher is better)" % (rows[0]["corpus"] if rows else ""))
    ax.set_ylabel("model / reasoning effort")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    print("wrote", out)


if __name__ == "__main__":
    main()
