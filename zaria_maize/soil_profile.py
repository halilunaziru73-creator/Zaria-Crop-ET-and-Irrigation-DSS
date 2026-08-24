"""
soil_profile.py
------------------
A labelled soil-profile cross-section diagram for the Soil Water tab/report: the
selected crop drawn at the top (using crop_icons.py), with a symbolically-labelled
soil column below it showing field capacity, permanent wilting point, root-zone
depth, and the current depletion/moisture level -- all duly labelled with this run's
own actual values, not a generic textbook diagram.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from . import crop_icons as ci

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")


def plot_soil_profile(crop_key: str, crop_display_name: str, farm_name: str,
                       soil_cfg, taw_raw: dict, storage_mm: float = None, depletion_mm: float = None,
                       root_zone_depth_m: float = None, maturity: float = 0.75,
                       fname: str = "soil_profile.png") -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    fc_pct = soil_cfg.field_capacity_pct
    pwp_pct = soil_cfg.pwp_pct
    zr_m = root_zone_depth_m if root_zone_depth_m is not None else soil_cfg.root_zone_depth_m
    taw_mm = taw_raw["TAW_mm"]
    raw_mm = taw_raw["RAW_mm"]
    mad = soil_cfg.mad

    storage_pct = None
    if storage_mm is not None and taw_mm:
        storage_pct = max(0.0, min(1.0, storage_mm / taw_mm))

    fig, ax = plt.subplots(figsize=(6, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.6, 6.0)
    ax.axis("off")
    ax.set_title(f"Soil-Water Profile: {crop_display_name} ({farm_name})", fontsize=12, fontweight="bold")

    # --- crop at the top, sitting clearly above the soil surface ---
    surface_y = 4.0
    inset = fig.add_axes([0.30, 0.62, 0.40, 0.30])
    inset.set_xlim(0, 1); inset.set_ylim(0, 1); inset.set_aspect("equal"); inset.axis("off")
    inset.patch.set_alpha(0)
    ci.draw_crop_icon(inset, crop_key, maturity, cy=0.02)

    # --- soil column ---
    col_x0, col_x1 = 2.5, 7.5
    ax.add_patch(mpatches.Rectangle((col_x0, 0), col_x1 - col_x0, surface_y,
                                     facecolor="#c9a876", edgecolor="#5a3a18", lw=1.8, zorder=1))

    # root zone shading (darker, moister band, down to root depth)
    depth_scale = surface_y / max(zr_m * 1.3, 0.3)  # visual scale: fit root depth within column with margin
    root_bottom_y = max(surface_y - zr_m * depth_scale, 0.3)
    ax.add_patch(mpatches.Rectangle((col_x0, root_bottom_y), col_x1 - col_x0, surface_y - root_bottom_y,
                                     facecolor="#a9825a", edgecolor="none", alpha=0.55, zorder=2))

    # moisture fill indicator (current storage, if provided) -- drawn with a strong
    # blue tint on top of the root-zone shading so it's clearly visible
    if storage_pct is not None:
        fill_h = (surface_y - root_bottom_y) * storage_pct
        ax.add_patch(mpatches.Rectangle((col_x0, root_bottom_y), col_x1 - col_x0, fill_h,
                                         facecolor="#2f7db5", edgecolor="none", alpha=0.55, zorder=3))

    # root depth line + label
    ax.plot([col_x0 - 0.15, col_x1 + 0.15], [root_bottom_y, root_bottom_y], color="#123524",
            lw=1.6, ls="--", zorder=4)
    ax.text(col_x1 + 0.25, root_bottom_y, f"Root zone depth (Zr)\n{zr_m:.2f} m", fontsize=8.5,
            va="center", ha="left", fontweight="bold")

    # field capacity marker (top of profile = FC reference)
    ax.annotate("", xy=(col_x0 - 0.3, surface_y), xytext=(col_x0 - 0.3, root_bottom_y),
                arrowprops=dict(arrowstyle="<->", color="#1f6fb2", lw=1.4))
    ax.text(col_x0 - 0.45, (surface_y + root_bottom_y) / 2,
            f"Field Capacity\n{fc_pct}%", fontsize=8, ha="right", va="center", color="#1f6fb2", fontweight="bold")

    ax.text(col_x0 - 0.45, root_bottom_y - 0.35, f"Permanent Wilting Point\n{pwp_pct}%",
            fontsize=8, ha="right", va="center", color="#8a4b00", fontweight="bold")
    ax.plot([col_x0 - 0.3, col_x1 + 0.3], [root_bottom_y - 0.05, root_bottom_y - 0.05],
            color="#8a4b00", lw=1.0, ls=":", zorder=4)

    # TAW / RAW labels (right side, bracket style)
    ax.text(col_x1 + 0.25, (surface_y + root_bottom_y) / 2 + 0.3,
            f"TAW = {taw_mm:.1f} mm", fontsize=8.5, va="center", ha="left", color="#123524")
    ax.text(col_x1 + 0.25, (surface_y + root_bottom_y) / 2 - 0.05,
            f"RAW = {raw_mm:.1f} mm\n(MAD = {mad})", fontsize=8.5, va="center", ha="left", color="#c94c4c")

    if storage_mm is not None:
        ax.text(col_x0 + (col_x1 - col_x0) / 2, root_bottom_y - 0.85,
                f"Current moisture: {storage_mm:.1f} mm ({storage_pct * 100:.0f}% of TAW)"
                + (f"\nDepletion: {depletion_mm:.1f} mm" if depletion_mm is not None else ""),
                fontsize=9, ha="center", va="top", fontweight="bold",
                bbox=dict(boxstyle="round", fc="#eef3ea", ec="#123524"))

    ax.text(col_x0 + (col_x1 - col_x0) / 2, -0.45, "Soil surface at 0 m depth (top of column)",
            fontsize=7.5, ha="center", color="#777", style="italic")

    path = os.path.join(OUT_DIR, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
