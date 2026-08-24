"""
farm_map.py
-----------
IMPORTANT LIMITATION (disclosed in the report text, not stamped across the image):
this environment has no internet access to Google Earth Engine and no GEE
authentication credentials, so real satellite imagery of a farm cannot be pulled
here. This module draws a farm-location diagram using the same irregular,
terrain-derived boundary as qgis_layout.py (see farm_boundary.py) — sized exactly to
the entered area and shaped uniquely per farm, not a plain rectangle — with a
water-flow arrow and a transparent, rule-based irrigation-method recommendation.

If real GEE imagery is later available, replace generate_farm_map() with an
ee.Image export call and keep recommend_irrigation_method(), which is
imagery-independent.
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from . import farm_boundary as fbnd
from . import qgis_layout as ql

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")


def recommend_irrigation_method(crop_key: str, net_irrigation_mm: float, gross_irrigation_mm: float,
                                 soil_texture_hint: str = "loam") -> dict:
    """Simple, transparent decision logic (not a black box): matches crop
    water-delivery characteristics + the pipeline's own computed irrigation
    requirement to a method."""
    reasons = []
    if crop_key == "rice":
        method = "Basin/Flood irrigation"
        reasons.append("Paddy rice requires standing water in the root zone for most of the season; "
                        "basin/flood systems are the only common method that maintains that condition.")
    elif net_irrigation_mm <= 1.0:
        method = "Rainfall-fed (no supplemental irrigation currently needed)"
        reasons.append("The computed net irrigation requirement for the entered conditions is "
                        "essentially zero, rainfall/soil moisture already meets crop demand.")
    elif crop_key == "pepper" or (gross_irrigation_mm and net_irrigation_mm / gross_irrigation_mm < 0.6):
        method = "Drip irrigation"
        reasons.append("High-value/high-demand crop with a meaningful irrigation requirement, drip "
                        "irrigation's high field-application efficiency (typically 85-95%) reduces water "
                        "loss and matches the precision this crop rewards.")
    elif net_irrigation_mm > 60:
        method = "Sprinkler irrigation"
        reasons.append("A large net irrigation requirement was computed; sprinkler systems apply water "
                        "more uniformly and efficiently than furrow at this scale, reducing deep "
                        "percolation losses.")
    else:
        method = "Furrow irrigation"
        reasons.append("A moderate irrigation requirement for a field crop on loam soil, "
                        "furrow irrigation is the standard, low-cost, locally-practiced method that "
                        "fits this demand level.")
    return {"recommended_method": method, "reasons": reasons}


def _plant_positions_inside_boundary(boundary, n_rows=8, n_cols=8):
    """Grid of candidate plant positions, kept only where they fall inside the
    irregular farm boundary polygon (matplotlib point-in-polygon test)."""
    from matplotlib.path import Path as MplPath
    poly_path = MplPath(boundary)
    xmin, xmax = boundary[:, 0].min(), boundary[:, 0].max()
    ymin, ymax = boundary[:, 1].min(), boundary[:, 1].max()
    xs = np.linspace(xmin + (xmax - xmin) * 0.06, xmax - (xmax - xmin) * 0.06, n_cols)
    ys = np.linspace(ymin + (ymax - ymin) * 0.10, ymax - (ymax - ymin) * 0.10, n_rows)
    pts = []
    for y in ys:
        for x in xs:
            if poly_path.contains_point((x, y)):
                pts.append((x, y))
    return pts, (xmin, xmax, ymin, ymax)


def _draw_mini_plant(ax, x, y, crop_key, size, colors_override=None):
    """A small, fast-to-render individual-plant marker (not the full detailed
    crop_icons blade drawing, which would be too slow repeated dozens of times) --
    still visually distinct in shape/colour per crop rather than a generic dot."""
    from . import crop_icons as ci
    colors = ci.CROP_COLORS.get(crop_key, ci.CROP_COLORS["maize"])
    ax.plot([x, x], [y, y + size * 0.5], color=colors["stem"], lw=1.2, solid_capstyle="round", zorder=6)
    for dx, dy, ang in [(-size * 0.35, size * 0.28, 35), (size * 0.35, size * 0.28, -35),
                        (0, size * 0.55, 0)]:
        leaf = mpatches.Ellipse((x + dx, y + dy), size * 0.55, size * 0.22, angle=ang,
                                 facecolor=colors["leaf"], edgecolor=colors["stem"], lw=0.35, zorder=7)
        ax.add_patch(leaf)


def _draw_irrigation_infrastructure(ax, boundary, bbox, method: str, plant_rows_y):
    """Draws the irrigation delivery network appropriate to the recommended method,
    clipped inside the farm boundary, main line / sub-mains / laterals or furrows,
    matched to the actual recommendation for this farm, not a generic drawing."""
    xmin, xmax, ymin, ymax = bbox
    main_color = "#1f6fb2"

    if method.startswith("Basin") or method.startswith("Rainfall"):
        # bunded basin cells: a grid of rectangular compartments + one supply channel
        n_cells_x, n_cells_y = 3, 3
        xs = np.linspace(xmin, xmax, n_cells_x + 1)
        ys = np.linspace(ymin, ymax, n_cells_y + 1)
        for x in xs:
            ax.plot([x, x], [ymin, ymax], color="#6b4a2a", lw=1.2, alpha=0.7, zorder=3)
        for y in ys:
            ax.plot([xmin, xmax], [y, y], color="#6b4a2a", lw=1.2, alpha=0.7, zorder=3)
        ax.plot([xmin, xmin], [ymin, ymax], color=main_color, lw=3.5, zorder=4)  # supply channel

    elif method.startswith("Furrow"):
        n_furrows = 9
        for y in np.linspace(ymin, ymax, n_furrows):
            ax.plot([xmin, xmax], [y, y], color="#8d6a3f", lw=1.0, alpha=0.6, zorder=3, ls=(0, (4, 2)))
        ax.plot([xmin, xmin], [ymin, ymax], color=main_color, lw=3.5, zorder=4)  # main canal
        ax.plot([xmin, xmax * 0.5 + xmin * 0.5], [ (ymin + ymax) / 2] * 2,
                color=main_color, lw=1.8, zorder=4)  # sub-main branch

    elif method.startswith("Drip"):
        ax.plot([xmin, xmin], [ymin, ymax], color=main_color, lw=3.2, zorder=4)  # mainline
        for y in plant_rows_y:
            ax.plot([xmin, xmax], [y, y], color=main_color, lw=1.0, zorder=4, alpha=0.85)  # submain per row
            for x in np.linspace(xmin, xmax, 10):
                ax.plot(x, y, marker="o", ms=2.2, color="#0d3a5c", zorder=5)  # drip emitters

    elif method.startswith("Sprinkler"):
        ax.plot([xmin, xmin], [ymin, ymax], color=main_color, lw=3.2, zorder=4)  # mainline
        ax.plot([xmin, xmax], [(ymin + ymax) / 2] * 2, color=main_color, lw=1.6, zorder=4)  # submain
        head_positions = [(x, y) for y in plant_rows_y[::2] for x in np.linspace(xmin, xmax, 4)]
        r = (xmax - xmin) / 10
        for hx, hy in head_positions:
            ax.add_patch(mpatches.Circle((hx, hy), r, facecolor="none", edgecolor=main_color,
                                          lw=0.7, ls="dashed", alpha=0.6, zorder=4))
            ax.plot(hx, hy, marker="+", ms=5, color=main_color, zorder=5)


def generate_farm_map(farm_name: str, lat: float, lon: float, area_ha: float,
                       crop_display_name: str, irrigation_recommendation: dict,
                       crop_key: str = "maize",
                       water_flow_direction_deg: float = 200.0,
                       fname: str = "farm_map_schematic.png") -> str:
    os.makedirs(OUT_DIR, exist_ok=True)

    dem, cellsize, extent = ql.generate_farm_terrain(farm_name, lat, lon, area_ha)
    boundary = fbnd.generate_boundary_polygon(dem, cellsize, extent, area_ha, farm_name, lat, lon)
    cx = (extent[0] + extent[1]) / 2
    cy = (extent[2] + extent[3]) / 2

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.set_aspect("equal")
    span = (extent[1] - extent[0]) * 0.65
    ax.set_xlim(cx - span, cx + span)
    ax.set_ylim(cy - span, cy + span)
    ax.axis("off")
    ax.add_patch(mpatches.Rectangle((cx - span, cy - span), 2 * span, 2 * span,
                                     facecolor="#eef3ea", edgecolor="none", zorder=0))

    poly_patch = mpatches.Polygon(boundary, closed=True, facecolor="#e8dcb8",
                                   edgecolor="#2f7d32", lw=2.2, zorder=1)
    ax.add_patch(poly_patch)
    top_y = boundary[:, 1].max()
    ax.text(cx, top_y + span * 0.12, f"{farm_name} \u2014 Delineated Farm Boundary",
            ha="center", fontsize=10, fontweight="bold", color="#123524")
    ax.text(cx, top_y + span * 0.03, f"Area: {area_ha} ha", ha="center", fontsize=8, color="#444")

    # --- irrigation infrastructure + individual plants, clipped inside the boundary ---
    plant_pts, bbox = _plant_positions_inside_boundary(boundary, n_rows=8, n_cols=8)
    plant_rows_y = sorted(set(round(y, 3) for _, y in plant_pts))
    method = irrigation_recommendation["recommended_method"]
    _draw_irrigation_infrastructure(ax, boundary, bbox, method, plant_rows_y)
    plant_size = span * 0.10
    for px, py in plant_pts:
        _draw_mini_plant(ax, px, py, crop_key, plant_size)
    for artist in ax.patches + ax.lines:
        if artist is not poly_patch:
            artist.set_clip_path(poly_patch)

    ax.plot(cx, cy, marker="*", ms=10, color="#c94c4c", markeredgecolor="black", zorder=8)
    bottom_lat_y = boundary[:, 1].min() - span * 0.06
    ax.text(cx, bottom_lat_y, f"Lat {lat:.4f}, Lon {lon:.4f}", ha="center", fontsize=7.5, color="#333")

    bottom_y = boundary[:, 1].min()
    rec_text = f"Recommended irrigation: {method}"
    ax.text(cx, bottom_y - span * 0.22, rec_text, ha="center", fontsize=10, fontweight="bold",
            color="#8a4b00", bbox=dict(boxstyle="round", fc="#fff3e0", ec="#e07a1f"))

    ax.set_title(f"{crop_display_name}: Farm Layout and Irrigation Infrastructure", fontsize=12, pad=14)

    path = os.path.join(OUT_DIR, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
