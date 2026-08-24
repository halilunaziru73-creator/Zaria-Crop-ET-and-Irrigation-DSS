"""
crop_icons.py
--------------
Procedurally-drawn (matplotlib primitives, no external images) field-stage icons for
each crop in the registry, parametrised by growth maturity (0=nursery/germination,
1=harvest-ready). Used to build the "stack of field pictures" for the growth-stage
simulation -- this environment has no internet access to fetch real crop photographs,
so a botanically-informed procedural drawing is used instead (tapered, curved leaf
blades via bezier paths rather than simple ellipses, crop-specific proportions and
grain-head shapes) -- more detailed than a schematic icon, but still illustrative line
art, not a photograph.
"""
import math
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath

CROP_COLORS = {
    "maize": {"stem": "#3d7a1f", "leaf": "#4caf50", "leaf_dark": "#3d8b40",
              "fruit": "#e8b23d", "ripe": "#c68a2a", "tassel": "#c9a876"},
    "rice": {"stem": "#5a8f3c", "leaf": "#7cb342", "leaf_dark": "#6a9c38",
             "fruit": "#d4b53a", "ripe": "#c9a227", "tassel": "#e0cf8a"},
    "sorghum": {"stem": "#6b4226", "leaf": "#8d6e3a", "leaf_dark": "#7a5e30",
                "fruit": "#a83232", "ripe": "#8b1e1e", "tassel": "#a83232"},
    "pepper": {"stem": "#2f7d32", "leaf": "#4caf50", "leaf_dark": "#3d8b40",
               "fruit": "#3d9e3f", "ripe": "#c0392b", "tassel": None},
    "cowpea": {"stem": "#4a7c3f", "leaf": "#6fae4f", "leaf_dark": "#5a9640",
               "fruit": "#7fae4f", "ripe": "#4a3520", "tassel": None},
}

# crop-specific leaf silhouette: (length_scale, width_scale, curve_amount, droop)
LEAF_STYLE = {
    "maize":   {"length": 1.15, "width": 0.30, "curve": 0.35, "droop": 0.15, "n_min": 2, "n_max": 7},
    "rice":    {"length": 1.00, "width": 0.14, "curve": 0.55, "droop": 0.35, "n_min": 3, "n_max": 9},
    "sorghum": {"length": 1.05, "width": 0.24, "curve": 0.30, "droop": 0.20, "n_min": 2, "n_max": 7},
    "pepper":  {"length": 0.55, "width": 0.32, "curve": 0.10, "droop": 0.05, "n_min": 3, "n_max": 10},
    "cowpea":  {"length": 0.60, "width": 0.34, "curve": 0.12, "droop": 0.10, "n_min": 3, "n_max": 9},
}


def _leaf_blade_path(base_xy, length, width, angle_deg, curve=0.35, droop=0.15):
    """
    A tapered, gently-curved leaf blade: narrow at the base, widest at ~40% of its
    length, tapering to a point at the tip, with a slight droop -- built from cubic
    Bezier segments rather than an ellipse, for a genuinely leaf-like silhouette.
    """
    bx, by = base_xy
    a = math.radians(angle_deg)
    # local frame: u = along the blade, v = perpendicular
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -math.sin(a), math.cos(a)

    def pt(u, v):
        # droop bends the tip downward as u approaches 1
        bend = -droop * (u ** 2)
        return (bx + ux * u * length + vx * (v * width + 0)
                + 0,
                by + uy * u * length + vy * (v * width) + bend)

    # key points along the blade (base -> widest -> tip), one edge then mirror back
    p0 = pt(0.0, 0.0)
    p_tip = pt(1.0, 0.0)
    left_mid = pt(0.42, 0.5)
    left_ctrl1 = pt(0.15, 0.32)
    left_ctrl2 = pt(0.30, 0.5)
    left_tip_ctrl = pt(0.78, 0.18)
    right_mid = pt(0.42, -0.5)
    right_ctrl1 = pt(0.30, -0.5)
    right_ctrl2 = pt(0.15, -0.32)
    right_tip_ctrl = pt(0.78, -0.18)

    verts = [p0, left_ctrl1, left_ctrl2, left_mid, left_tip_ctrl, p_tip,
             right_tip_ctrl, right_mid, right_ctrl2, right_ctrl1, p0]
    codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.CURVE4, MplPath.CURVE4, MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


def _midrib_path(base_xy, length, angle_deg, droop=0.15):
    bx, by = base_xy
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    n = 8
    pts = []
    for i in range(n + 1):
        u = i / n
        bend = -droop * (u ** 2)
        pts.append((bx + ux * u * length, by + uy * u * length + bend))
    return pts


def draw_crop_icon(ax, crop_key: str, maturity: float, cx: float = 0.5, cy: float = 0.15):
    """
    Draws a field icon for the given crop at the given maturity (0-1) onto an
    already-created matplotlib Axes (expected xlim/ylim = 0..1). maturity controls
    plant height, leaf count/spread, and whether fruit/grain heads are shown.
    """
    colors = CROP_COLORS.get(crop_key, CROP_COLORS["maize"])
    style = LEAF_STYLE.get(crop_key, LEAF_STYLE["maize"])
    maturity = max(0.0, min(1.0, maturity))
    rng = np.random.default_rng(abs(hash((crop_key, round(maturity, 3)))) % (2 ** 32))

    # soil strip
    ax.add_patch(mpatches.Rectangle((0, 0), 1, cy, facecolor="#c9a876", edgecolor="none", zorder=0))

    height = (0.10 + 0.55 * maturity) * (0.85 if crop_key in ("pepper", "cowpea") else 1.0)
    n_leaves = style["n_min"] + int(round((style["n_max"] - style["n_min"]) * maturity))

    # main stem (tapered width, slight natural curve)
    stem_pts = 10
    stem_x = [cx + 0.01 * math.sin(3 * t) * maturity for t in np.linspace(0, 1, stem_pts)]
    stem_y = [cy + height * t for t in np.linspace(0, 1, stem_pts)]
    ax.plot(stem_x, stem_y, color=colors["stem"], lw=2.2 + 2.0 * maturity, solid_capstyle="round", zorder=2)

    # leaves: alternating sides, growing in size toward mid-height, botanically-shaped
    for i in range(n_leaves):
        frac = (i + 1) / (n_leaves + 1)
        ly = cy + height * frac
        lx = cx + 0.01 * math.sin(3 * frac) * maturity
        side = 1 if i % 2 == 0 else -1
        size_factor = 0.5 + 0.5 * math.sin(frac * math.pi)  # leaves largest mid-stem
        leaf_len = style["length"] * (0.18 + 0.30 * maturity) * size_factor
        leaf_w = style["width"] * (0.18 + 0.30 * maturity) * size_factor
        jitter = rng.uniform(-6, 6)
        base_angle = side * (40 + 25 * style["curve"]) + jitter
        path = _leaf_blade_path((lx, ly), leaf_len, leaf_w, base_angle,
                                 curve=style["curve"], droop=style["droop"])
        blade_color = colors["leaf"] if i % 2 == 0 else colors["leaf_dark"]
        patch = mpatches.PathPatch(path, facecolor=blade_color, edgecolor=colors["stem"],
                                    lw=0.5, zorder=3, alpha=0.95)
        ax.add_patch(patch)
        midrib = _midrib_path((lx, ly), leaf_len * 0.92, base_angle, droop=style["droop"])
        xs, ys = zip(*midrib)
        ax.plot(xs, ys, color=colors["stem"], lw=0.5, alpha=0.6, zorder=4)

    # fruit/grain head appears from mid-season onward, crop-specific shape
    if maturity >= 0.45:
        top = cy + height
        ripe_frac = max(0.0, (maturity - 0.72) / 0.28)
        fruit_color = _blend(colors["fruit"], colors["ripe"], ripe_frac)

        if crop_key == "maize":
            # tassel at the very top
            for k in range(3):
                ang = 90 + (k - 1) * 18
                tx = cx + 0.03 * (k - 1)
                ax.plot([cx, tx], [top, top + 0.06], color=colors.get("tassel", "#c9a876"),
                         lw=1.2, alpha=0.8, zorder=5)
            # cob emerging from the side
            cob = mpatches.FancyBboxPatch((cx + 0.035, top - 0.20), 0.045, 0.16,
                                           boxstyle="round,pad=0.004,rounding_size=0.02",
                                           facecolor=fruit_color, edgecolor="#5a3a18", lw=0.6, zorder=4)
            ax.add_patch(cob)
            husk = mpatches.Ellipse((cx + 0.06, top - 0.10), 0.03, 0.15, angle=8,
                                     facecolor="#d8e8b0", edgecolor="none", alpha=0.5, zorder=4.5)
            ax.add_patch(husk)

        elif crop_key in ("sorghum", "rice"):
            # drooping panicle head
            head_pts = []
            n_grain = 10
            for k in range(n_grain):
                t = k / (n_grain - 1)
                gx = cx + 0.025 * math.sin(t * 5) * (1 - t * 0.3)
                gy = top + 0.02 + t * 0.11 * (1.2 if crop_key == "sorghum" else 0.9)
                head_pts.append((gx, gy))
                ax.add_patch(mpatches.Circle((gx, gy), 0.008 + 0.004 * (1 - t), facecolor=fruit_color,
                                              edgecolor="#5a3a18", lw=0.3, zorder=5))
            xs, ys = zip(*head_pts)
            ax.plot(xs, ys, color=colors["stem"], lw=0.8, zorder=4)

        elif crop_key == "pepper":
            for dx, dy, ang in [(-0.045, -0.02, -20), (0.05, -0.06, 15), (0.01, -0.10, 5)]:
                pod = mpatches.FancyBboxPatch((cx + dx, top + dy), 0.022, 0.075,
                                               boxstyle="round,pad=0.003,rounding_size=0.012",
                                               facecolor=fruit_color, edgecolor="#7a2f1a", lw=0.5,
                                               zorder=5, transform=ax.transData)
                pod.set_transform(mpatches.transforms.Affine2D().rotate_deg_around(
                    cx + dx + 0.011, top + dy + 0.0375, ang) + ax.transData)
                ax.add_patch(pod)

        elif crop_key == "cowpea":
            for dx, dy, ang in [(-0.04, -0.05, -15), (0.045, -0.08, 20)]:
                pod = mpatches.FancyBboxPatch((cx + dx, top + dy), 0.018, 0.11,
                                               boxstyle="round,pad=0.002,rounding_size=0.009",
                                               facecolor=fruit_color, edgecolor="#3a2a10", lw=0.5, zorder=5)
                pod.set_transform(mpatches.transforms.Affine2D().rotate_deg_around(
                    cx + dx + 0.009, top + dy + 0.055, ang) + ax.transData)
                ax.add_patch(pod)

    # germination dot for very early stage
    if maturity < 0.10:
        ax.add_patch(mpatches.Circle((cx, cy - 0.008), 0.016, facecolor="#8d5a2b", edgecolor="none", zorder=1))
        ax.add_patch(mpatches.Ellipse((cx, cy + 0.01), 0.03, 0.018, angle=20,
                                       facecolor=colors["leaf"], edgecolor=colors["stem"], lw=0.4, zorder=2))
        ax.add_patch(mpatches.Ellipse((cx, cy + 0.01), 0.03, 0.018, angle=-20,
                                       facecolor=colors["leaf"], edgecolor=colors["stem"], lw=0.4, zorder=2))


def _blend(hex1, hex2, t):
    t = max(0.0, min(1.0, t))
    c1 = tuple(int(hex1[i:i + 2], 16) for i in (1, 3, 5))
    c2 = tuple(int(hex2[i:i + 2], 16) for i in (1, 3, 5))
    c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return "#%02x%02x%02x" % c
