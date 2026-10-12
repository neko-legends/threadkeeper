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
    labels = ["%s  [effort: %s]\ngraded by %s via %s" % (r["model"], r["effort"], r.get("judge_model") or "?", r.get("transport") or "openai") for r in rows]
    fig, ax = plt.subplots(figsize=(10, 0.6 * len(rows) + 1.8))
    for i, r in enumerate(rows):
        if r["composite"]:
            ax.barh(i, float(r["composite"]), color="#2a6fb0")
            ax.text(float(r["composite"]) + 0.3, i, r["composite"], va="center", fontsize=8)
        else:
            ax.barh(i, 100, color="none", edgecolor="#b03a2e", hatch="//")
            ax.text(3, i, r["status"], va="center", fontsize=8, color="#b03a2e")
    ax.set_yticks(range(len(rows)), labels, fontsize=8)
    ax.set_xlim(0, 105)
    ax.set_xlabel("composite score (0-100); hatched = FAILED, not a summary")
    ax.set_title("threadkeeper: context-compaction quality, %s corpus (higher is better)" % (rows[0]["corpus"] if rows else ""))
    ax.set_ylabel("model / reasoning effort")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    print("wrote", out)


if __name__ == "__main__":
    main()
