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
    labels = ["%s | %s | %s" % (r["model"], r["effort"], r["corpus"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(rows) + 1.5))
    for i, r in enumerate(rows):
        if r["composite"]:
            ax.barh(i, float(r["composite"]), color="#2a6fb0")
            ax.text(float(r["composite"]) + 1, i, r["composite"], va="center", fontsize=8)
        else:
            ax.barh(i, 100, color="none", edgecolor="#b03a2e", hatch="//")
            ax.text(3, i, r["status"], va="center", fontsize=8, color="#b03a2e")
    ax.set_yticks(range(len(rows)), labels, fontsize=8)
    ax.set_xlim(0, 105)
    ax.set_xlabel("composite score (0-100); hatched = FAILED, not a summary")
    ax.set_title("threadkeeper")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    print("wrote", out)


if __name__ == "__main__":
    main()
