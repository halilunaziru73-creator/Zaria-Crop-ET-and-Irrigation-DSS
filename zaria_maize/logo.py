"""
logo.py
-------
Generates a simple, original pipeline logo procedurally with matplotlib (a stylised
maize leaf pair + water droplet inside a circular badge). Built entirely from primitive
matplotlib patches (circles, ellipses, polygons) -- no external image, icon set, or
copyrighted artwork is used or copied -- so the badge is safe to redistribute and easy
to re-theme.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
LOGO_PATH = os.path.join(OUT_DIR, "logo.png")

GREEN = "#2f7d32"
LEAF_GREEN = "#4caf50"
BLUE = "#1f6fb2"
BLUE_DARK = "#124a75"
DARK = "#123524"
BG = "#e9f5ee"


def _leaf(ax, cx, cy, width, height, angle_deg, color, edge):
    """A leaf blade approximated as a rotated, tapered ellipse."""
    e = mpatches.Ellipse((cx, cy), width, height, angle=angle_deg,
                          facecolor=color, edgecolor=edge, lw=1.2, zorder=2)
    ax.add_patch(e)


def _droplet(ax, cx, cy, r, color, edge):
    """A water droplet = a triangle tip fused with a circle base."""
    tri = mpatches.Polygon([(cx, cy + r * 2.2), (cx - r * 0.95, cy + r * 0.15),
                             (cx + r * 0.95, cy + r * 0.15)],
                            closed=True, facecolor=color, edgecolor="none", zorder=3)
    circ = mpatches.Circle((cx, cy), r, facecolor=color, edgecolor="none", zorder=3)
    ax.add_patch(tri)
    ax.add_patch(circ)
    outline = mpatches.Circle((cx, cy), r, facecolor="none", edgecolor=edge, lw=1.2, zorder=4)
    ax.add_patch(outline)


def generate_logo(path: str = LOGO_PATH, size_px: int = 512) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dpi = 100
    fig = plt.figure(figsize=(size_px / dpi, size_px / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_alpha(0)

    # outer badge ring
    ax.add_patch(mpatches.Circle((0.5, 0.5), 0.47, facecolor=DARK, edgecolor="none", zorder=0))
    ax.add_patch(mpatches.Circle((0.5, 0.5), 0.435, facecolor=BG, edgecolor="none", zorder=1))

    # two maize-leaf blades fanning up from a stem
    _leaf(ax, 0.44, 0.60, 0.42, 0.13, 55, LEAF_GREEN, GREEN)
    _leaf(ax, 0.56, 0.60, 0.42, 0.13, -55, GREEN, GREEN)
    ax.plot([0.5, 0.5], [0.30, 0.62], color=GREEN, lw=4, zorder=2, solid_capstyle="round")

    # water droplet at the base
    _droplet(ax, 0.5, 0.24, 0.11, BLUE, BLUE_DARK)

    fig.savefig(path, dpi=dpi, transparent=True)
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(generate_logo())

