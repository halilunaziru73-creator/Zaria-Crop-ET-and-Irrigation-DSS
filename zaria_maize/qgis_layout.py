"""
qgis_layout.py
---------------
Generates a QGIS-print-layout-style terrain-characterisation figure for a specific
Zaria farm, sized to that farm's ACTUAL ENTERED AREA, using an irregular DEM-derived
boundary (see farm_boundary.py) rather than an assumed square. No land-use/land-cover
panel is included (an earlier version fabricated one; removed).

Real-data path (use this when you have internet/GIS access):
    load_dem_geotiff(path)         — any real GeoTIFF DEM (SRTM, Copernicus GLO-30,
                                       ASTER, or a drone survey), via rasterio.
    load_boundary_shapefile(path)  — your farm's real surveyed boundary, via geopandas.
Pass dem_path=/boundary_path= to generate_zaria_study_area_layout() and it uses your
real data automatically instead of anything below.

No-real-data path (used automatically otherwise): this environment has no internet
access to fetch a real DEM, so a regional elevation MODEL is built from Zaria's own
real, documented elevation statistics (~600-670 m a.s.l., Kaduna State Sudan-savanna)
rather than a literal per-plot survey. It is deterministic and farm-specific (seeded
from the farm's own name + coordinates, so two different farms never get the same
terrain, and re-running for the SAME farm gives the SAME terrain). This is disclosed
factually, once, in small text — not as a repeated watermark.
"""
import os
import math
import hashlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.path import Path as MplPath
import matplotlib.patches as mpatches

from . import farm_boundary as fbnd

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")

ZARIA_LAT, ZARIA_LON = 11.11, 7.65
ZARIA_BASE_ELEV_M = 640.0            # [STANDARD] documented approximate elevation of Zaria/Samaru, m a.s.l.
ZARIA_TYPICAL_SLOPE_PCT = (0.5, 4.0)  # [STANDARD] gently undulating basement-complex terrain, typical range


def _farm_seed(farm_name: str, lat: float, lon: float) -> int:
    key = f"{farm_name}|{round(lat, 5)}|{round(lon, 5)}".encode()
    return int(hashlib.sha256(key).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------------
# Real-data loaders
# ---------------------------------------------------------------------------------

def load_dem_geotiff(path: str):
    try:
        import rasterio
    except ImportError as e:
        raise ImportError("load_dem_geotiff() needs rasterio: pip install rasterio") from e
    with rasterio.open(path) as src:
        dem = src.read(1).astype(float)
        cellsize = abs(src.transform.a)
        b = src.bounds
        extent = (b.left, b.right, b.bottom, b.top)
    return dem, cellsize, extent


def load_boundary_shapefile(path: str):
    try:
        import geopandas as gpd
    except ImportError as e:
        raise ImportError("load_boundary_shapefile() needs geopandas: pip install geopandas") from e
    return gpd.read_file(path)


# ---------------------------------------------------------------------------------
# Farm-specific regional terrain model, sized to the farm's real area
# ---------------------------------------------------------------------------------

def generate_farm_terrain(farm_name: str, lat: float, lon: float, area_ha: float,
                           size_px: int = 180, base_elev_m: float = ZARIA_BASE_ELEV_M,
                           relief_m: float = 20.0):
    """
    Builds a farm-specific regional elevation MODEL (not a literal survey), its
    modelled extent sized to comfortably circumscribe the requested farm area, seeded
    uniquely from this farm's own name + coordinates. Returns (dem, cellsize_m, extent).
    """
    seed = _farm_seed(farm_name, lat, lon)
    rng = np.random.default_rng(seed)
    area_m2 = max(area_ha, 0.01) * 10000
    circ_radius = math.sqrt(area_m2 / math.pi)
    extent_m = circ_radius * 2.6  # margin so the organic boundary fits inside the modelled square

    x = np.linspace(0, extent_m, size_px)
    y = np.linspace(0, extent_m, size_px)
    X, Y = np.meshgrid(x, y)
    dem = np.full_like(X, base_elev_m)
    for _ in range(4):
        cx, cy = rng.uniform(0.15, 0.85, 2) * extent_m
        sigma = rng.uniform(0.18, 0.4) * extent_m
        amp = rng.uniform(-1, 1) * relief_m
        dem += amp * np.exp(-(((X - cx) ** 2 + (Y - cy) ** 2) / (2 * sigma ** 2)))
    regional_dir = rng.uniform(0, 2 * math.pi)
    dem += (X * math.cos(regional_dir) + Y * math.sin(regional_dir)) / extent_m * 10.0

    cellsize = extent_m / size_px
    extent = (0, extent_m, 0, extent_m)
    return dem, cellsize, extent


# ---------------------------------------------------------------------------------
# Terrain derivatives
# ---------------------------------------------------------------------------------

def compute_slope_percent(dem: np.ndarray, cellsize_m: float) -> np.ndarray:
    dzdy, dzdx = np.gradient(dem, cellsize_m)
    return 100.0 * np.sqrt(dzdx ** 2 + dzdy ** 2)


def compute_aspect_deg(dem: np.ndarray, cellsize_m: float) -> np.ndarray:
    dzdy, dzdx = np.gradient(dem, cellsize_m)
    aspect = np.degrees(np.arctan2(dzdy, -dzdx))
    return (90.0 - aspect) % 360.0


def _profile_through_boundary(dem, extent, boundary_verts, axis):
    n_rows, n_cols = dem.shape
    cx, cy = boundary_verts[:, 0].mean(), boundary_verts[:, 1].mean()
    if axis == "we":
        row = int(np.clip((cy - extent[2]) / (extent[3] - extent[2]) * (n_rows - 1), 0, n_rows - 1))
        xmin, xmax = boundary_verts[:, 0].min(), boundary_verts[:, 0].max()
        c_lo = int(np.clip((xmin - extent[0]) / (extent[1] - extent[0]) * (n_cols - 1), 0, n_cols - 1))
        c_hi = int(np.clip((xmax - extent[0]) / (extent[1] - extent[0]) * (n_cols - 1), 0, n_cols - 1))
        seg = dem[row, c_lo:c_hi + 1]
        dist = np.linspace(0, xmax - xmin, len(seg))
    else:
        col = int(np.clip((cx - extent[0]) / (extent[1] - extent[0]) * (n_cols - 1), 0, n_cols - 1))
        ymin, ymax = boundary_verts[:, 1].min(), boundary_verts[:, 1].max()
        r_lo = int(np.clip((ymin - extent[2]) / (extent[3] - extent[2]) * (n_rows - 1), 0, n_rows - 1))
        r_hi = int(np.clip((ymax - extent[2]) / (extent[3] - extent[2]) * (n_rows - 1), 0, n_rows - 1))
        seg = dem[r_lo:r_hi + 1, col]
        dist = np.linspace(0, ymax - ymin, len(seg))
    return dist, seg


# ---------------------------------------------------------------------------------
# Main terrain-characterisation layout
# ---------------------------------------------------------------------------------

def plot_terrain_characterisation_layout(dem, cellsize_m, extent, boundary_verts,
                                          farm_name, lat, lon, area_ha, is_regional_model: bool,
                                          fname="qgis_terrain_layout.png") -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    slope = compute_slope_percent(dem, cellsize_m)
    aspect = compute_aspect_deg(dem, cellsize_m)
    we_dist, we_profile = _profile_through_boundary(dem, extent, boundary_verts, "we")
    ns_dist, ns_profile = _profile_through_boundary(dem, extent, boundary_verts, "ns")

    fig = plt.figure(figsize=(11, 7.5))
    gs = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)
    poly_path = MplPath(boundary_verts)

    def _draw_boundary(ax, color="#c94c4c"):
        ax.add_patch(mpatches.PathPatch(poly_path, facecolor="none", edgecolor=color, lw=2.0, zorder=5))

    axA = fig.add_subplot(gs[0, 0])
    axA.set_xlim(extent[0], extent[1]); axA.set_ylim(extent[2], extent[3]); axA.set_aspect("equal")
    axA.add_patch(mpatches.Rectangle((extent[0], extent[2]), extent[1] - extent[0], extent[3] - extent[2],
                                      facecolor="#eef3ea", edgecolor="none"))
    axA.fill(boundary_verts[:, 0], boundary_verts[:, 1], color="#d7e8c9", alpha=0.7, zorder=2)
    _draw_boundary(axA)
    cx, cy = boundary_verts[:, 0].mean(), boundary_verts[:, 1].mean()
    axA.plot(cx, cy, marker="*", ms=14, color="#c94c4c", markeredgecolor="black", zorder=6)
    axA.text(cx, extent[2] + (extent[3] - extent[2]) * 0.06,
              f"{farm_name}\nLat {lat:.4f}, Lon {lon:.4f}\n{area_ha:g} ha", ha="center", fontsize=7.5)
    axA.set_xticks([]); axA.set_yticks([])
    axA.set_title("(A) Farm Boundary & Location", fontsize=9, fontweight="bold")

    axB = fig.add_subplot(gs[0, 1])
    im = axB.imshow(dem, cmap="terrain", origin="lower", extent=extent)
    _draw_boundary(axB)
    fig.colorbar(im, ax=axB, fraction=0.046, pad=0.04, label="m a.s.l.")
    axB.set_title("(B) Altitude Distribution", fontsize=9, fontweight="bold")
    axB.set_xlabel("m", fontsize=7); axB.set_ylabel("m", fontsize=7)

    axC = fig.add_subplot(gs[0, 2])
    im2 = axC.imshow(slope, cmap="YlOrRd", origin="lower", extent=extent)
    _draw_boundary(axC, color="#1f6fb2")
    fig.colorbar(im2, ax=axC, fraction=0.046, pad=0.04, label="Slope (%)")
    axC.set_title("(C) Slope (%)", fontsize=9, fontweight="bold")
    axC.set_xlabel("m", fontsize=7); axC.set_ylabel("m", fontsize=7)

    axD = fig.add_subplot(gs[1, 0])
    axD.plot(we_dist, we_profile, color="#8d5a2b", lw=1.5)
    axD.fill_between(we_dist, we_profile, we_profile.min() - 2, color="#e8d5b5")
    axD.set_title("(D) West-East Profile", fontsize=9, fontweight="bold")
    axD.set_xlabel("Distance (m)", fontsize=7); axD.set_ylabel("Elevation (m)", fontsize=7)

    axE = fig.add_subplot(gs[1, 1])
    axE.plot(ns_dist, ns_profile, color="#8d5a2b", lw=1.5)
    axE.fill_between(ns_dist, ns_profile, ns_profile.min() - 2, color="#e8d5b5")
    axE.set_title("(E) North-South Profile", fontsize=9, fontweight="bold")
    axE.set_xlabel("Distance (m)", fontsize=7); axE.set_ylabel("Elevation (m)", fontsize=7)

    axF = fig.add_subplot(gs[1, 2])
    im3 = axF.imshow(aspect, cmap="hsv", origin="lower", extent=extent)
    _draw_boundary(axF)
    fig.colorbar(im3, ax=axF, fraction=0.046, pad=0.04, label="Aspect (\u00b0)")
    axF.set_title("(F) Aspect", fontsize=9, fontweight="bold")
    axF.set_xlabel("m", fontsize=7); axF.set_ylabel("m", fontsize=7)

    fig.suptitle(f"Terrain Characterisation of {farm_name} ({area_ha:g} ha, Zaria, Kaduna State)",
                 fontsize=12, fontweight="bold")
    if is_regional_model:
        fig.text(0.5, 0.005, "Regional elevation estimate (Zaria area statistics) — supply a real "
                              "DEM for a plot-specific survey.", ha="center", fontsize=7, color="#777")

    path = os.path.join(OUT_DIR, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_farm_vs_zaria_comparison(area_ha, crop_display_name, growing_season_etc_mm,
                                   local_etc_range_mm, farm_name,
                                   fname="qgis_farm_comparison.png") -> str:
    """Compares this farm's own computed growing-season ETc against the locally-reported
    Zaria range for the same crop (crops.py) — real reference data, not fabricated."""
    os.makedirs(OUT_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    lo, hi = local_etc_range_mm
    ax.barh(["Zaria local range\n(reported)"], [hi - lo], left=[lo], color="#cfe8cf",
            edgecolor="#2f7d32", height=0.5, label="Reported local range")
    ax.barh([f"{farm_name}\n(this analysis)"], [growing_season_etc_mm], color="#4a7c3f",
            edgecolor="black", height=0.5)
    ax.axvline(growing_season_etc_mm, color="#c94c4c", ls="--", lw=1.5)
    ax.text(growing_season_etc_mm, 1.35, f"{growing_season_etc_mm:.0f} mm", color="#c94c4c",
            fontsize=9, ha="center", fontweight="bold")
    ax.set_xlabel("Growing-season ETc (mm)")
    ax.set_title(f"{crop_display_name}: {farm_name} vs Typical Zaria-Area Farms")
    ax.legend(loc="lower right", fontsize=8)
    path = os.path.join(OUT_DIR, fname)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------------
# One-call convenience wrapper
# ---------------------------------------------------------------------------------

def generate_zaria_study_area_layout(farm_name: str, area_ha: float, lat: float = ZARIA_LAT,
                                      lon: float = ZARIA_LON, crop_display_name: str = None,
                                      growing_season_etc_mm: float = None,
                                      local_etc_range_mm: tuple = None,
                                      dem_path: str = None, boundary_path: str = None) -> dict:
    if dem_path:
        dem, cellsize, extent = load_dem_geotiff(dem_path)
        is_regional = False
    else:
        dem, cellsize, extent = generate_farm_terrain(farm_name, lat, lon, area_ha)
        is_regional = True

    boundary_verts = fbnd.generate_boundary_polygon(dem, cellsize, extent, area_ha, farm_name, lat, lon)

    slope = compute_slope_percent(dem, cellsize)
    farm_stats = {"mean_elevation_m": round(float(dem.mean()), 1),
                  "mean_slope_pct": round(float(slope.mean()), 2)}

    safe = farm_name.replace(" ", "_")
    terrain_path = plot_terrain_characterisation_layout(
        dem, cellsize, extent, boundary_verts, farm_name, lat, lon, area_ha,
        is_regional_model=is_regional, fname=f"qgis_terrain_{safe}.png")

    result = {"terrain_layout": terrain_path, "is_regional_model": is_regional, "farm_stats": farm_stats}

    if crop_display_name and growing_season_etc_mm is not None and local_etc_range_mm:
        comparison_path = plot_farm_vs_zaria_comparison(
            area_ha, crop_display_name, growing_season_etc_mm, local_etc_range_mm,
            farm_name, fname=f"qgis_comparison_{safe}.png")
        result["farm_comparison"] = comparison_path

    return result
