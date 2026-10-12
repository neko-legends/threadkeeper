"""Sakura palette + small drawing helpers for score.chart."""
import math

from matplotlib.patches import Ellipse

BG, PANEL = "#FFF7F5", "#FFFBFA"
INK, SOFT = "#4A2C3A", "#8A6677"
PINK, DEEP, BLUSH = "#F4A7B9", "#E07A9A", "#FBD3DD"
SAGE, GOLD, GREY = "#8FAE8B", "#C9A24B", "#B9A9AF"
GRID = "#F6DDE3"
TH = {"P": "#9FC59A", "PA": "#F2CE8A", "L": "#D9607F"}
SERIF = ["DejaVu Serif", "Noto Serif", "Liberation Serif", "serif"]


def rbar(ax, y, x0, x1, color, lw=11, alpha=1.0, label=None, z=3):
    """Round-ended horizontal bar from x0 to x1 (data units). The cap radius is trimmed so the bar ends exactly at x1."""
    if x1 <= x0:
        return
    bb = ax.get_position()
    w_in = bb.width * ax.figure.get_figwidth()
    lo, hi = ax.get_xlim()
    r = (lw / 72 / 2) / w_in * (hi - lo)
    a, b = x0 + r, x1 - r
    if b <= a:  # shorter than a cap diameter: draw a dot (a zero-length line does not render)
        ax.plot([a], [y], marker="o", markersize=lw, color=color, alpha=alpha, mew=0, ls="none", label=label, zorder=z)
        return
    ax.plot([a, b], [y, y], solid_capstyle="round", lw=lw, color=color, alpha=alpha, label=label, zorder=z)


def petal_flower(ax, cx, cy, r=0.012, rot=0.0, color=PINK, alpha=0.5):
    """Five-petal blossom in axes-fraction coords (ax is a full-figure overlay axes with equal-aspect transform)."""
    for k in range(5):
        a = rot + k * 2 * math.pi / 5
        px, py = cx + r * 0.95 * math.cos(a), cy + r * 0.95 * math.sin(a)
        ax.add_patch(Ellipse((px, py), r * 1.25, r * 0.85, angle=math.degrees(a), color=color, alpha=alpha, lw=0, transform=ax.transAxes))
    ax.add_patch(Ellipse((cx, cy), r * 0.5, r * 0.5, color=DEEP, alpha=min(1, alpha + 0.25), lw=0, transform=ax.transAxes))
