"""
icons.py
--------
Small procedurally-generated icons (matplotlib primitives, no external art) shown
alongside each result section in the GUI, echoing the tile-icon style of a dashboard
without using any copyrighted or external imagery.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "icons")

GREEN = "#2f7d32"
LEAF_GREEN = "#4caf50"
BLUE = "#1f6fb2"
ORANGE = "#e07a1f"
GREY = "#5a6b6a"
BG = "#ffffff"


def _new_ax(size_px=96):
    dpi = 96
    fig = plt.figure(figsize=(size_px / dpi, size_px / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_alpha(0)
    return fig, ax


def _save(fig, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=96, transparent=True)
    plt.close(fig)
    return path


def icon_thermometer_leaf(name="icon_et.png"):
    """ET / temperature icon: thermometer + small leaf."""
    fig, ax = _new_ax()
    ax.add_patch(mpatches.Circle((0.5, 0.5), 0.47, facecolor="#eef6f0", edgecolor="#123524", lw=2))
    # thermometer stem
    ax.add_patch(mpatches.FancyBboxPatch((0.44, 0.35), 0.12, 0.35, boxstyle="round,pad=0.01,rounding_size=0.06",
                                          facecolor="white", edgecolor=ORANGE, lw=2))
    ax.add_patch(mpatches.Circle((0.5, 0.30), 0.10, facecolor=ORANGE, edgecolor=ORANGE, lw=2))
    ax.add_patch(mpatches.Rectangle((0.475, 0.34), 0.05, 0.28, facecolor=ORANGE, edgecolor="none"))
    # small leaf top-right
    leaf = mpatches.Ellipse((0.70, 0.72), 0.24, 0.10, angle=35, facecolor=LEAF_GREEN, edgecolor=GREEN, lw=1)
    ax.add_patch(leaf)
    return _save(fig, name)


def icon_water_drop(name="icon_irrigation.png"):
    fig, ax = _new_ax()
    ax.add_patch(mpatches.Circle((0.5, 0.5), 0.47, facecolor="#eaf3fb", edgecolor="#123524", lw=2))
    tri = mpatches.Polygon([(0.5, 0.80), (0.30, 0.42), (0.70, 0.42)], closed=True,
                            facecolor=BLUE, edgecolor="none", zorder=2)
    circ = mpatches.Circle((0.5, 0.38), 0.20, facecolor=BLUE, edgecolor="#124a75", lw=1.5, zorder=2)
    ax.add_patch(tri)
    ax.add_patch(circ)
    return _save(fig, name)


def icon_soil_layers(name="icon_soil.png"):
    fig, ax = _new_ax()
    ax.add_patch(mpatches.Circle((0.5, 0.5), 0.47, facecolor="#f5efe6", edgecolor="#123524", lw=2))
    browns = ["#8d5a2b", "#a9713a", "#c68a4c"]
    y = 0.22
    for i, c in enumerate(browns):
        h = 0.16
        ax.add_patch(mpatches.Rectangle((0.20, y), 0.60, h, facecolor=c, edgecolor="#5a3a18", lw=0.8))
        y += h
    # roots
    for dx in (-0.06, 0, 0.06):
        ax.plot([0.5 + dx, 0.5 + dx * 2], [0.60, 0.30], color="#2f7d32", lw=1.5)
    return _save(fig, name)


def icon_gauge(name="icon_efficiency.png"):
    fig, ax = _new_ax()
    ax.add_patch(mpatches.Circle((0.5, 0.5), 0.47, facecolor="#fdf2e9", edgecolor="#123524", lw=2))
    ax.add_patch(mpatches.Wedge((0.5, 0.35), 0.32, 20, 160, facecolor="none", edgecolor=ORANGE, lw=6))
    import math
    angle = math.radians(180 - 110)
    ax.plot([0.5, 0.5 + 0.26 * math.cos(angle)], [0.35, 0.35 + 0.26 * math.sin(angle)],
             color=GREY, lw=3, solid_capstyle="round")
    ax.add_patch(mpatches.Circle((0.5, 0.35), 0.03, facecolor=GREY, edgecolor="none"))
    return _save(fig, name)


def generate_all():
    return {
        "et": icon_thermometer_leaf(),
        "irrigation": icon_water_drop(),
        "soil": icon_soil_layers(),
        "efficiency": icon_gauge(),
    }


if __name__ == "__main__":
    print(generate_all())
