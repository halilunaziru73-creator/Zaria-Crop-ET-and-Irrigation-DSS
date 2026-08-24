"""
farm_boundary.py
-----------------
Generates an irregular, DEM-derived farm boundary polygon (not a plain rectangle),
sized so its enclosed area matches the area the user actually entered, and shaped
uniquely per farm (deterministically seeded from the farm name + coordinates, so the
same farm always gets the same boundary, and different farms look different).

Method: a radial boundary is built (like a star-shaped polygon) with one radius value
per compass angle. Each radius is perturbed using the LOCAL SLOPE of the terrain
surface at that angle -- steeper local slope pulls the boundary in slightly (farmers
in this region typically avoid enclosing the steepest micro-relief within a field
boundary), giving an irregular but terrain-consistent shape rather than an arbitrary
smooth blob or a square. The polygon is then rescaled so its exact area equals the
user-entered farm area.
"""
import hashlib
import numpy as np


def _seed_from(*parts) -> int:
    key = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


def generate_boundary_polygon(dem: np.ndarray, cellsize_m: float, extent: tuple,
                               area_ha: float, farm_name: str, lat: float, lon: float,
                               n_vertices: int = 48) -> np.ndarray:
    """
    Returns an (n_vertices, 2) array of (x, y) polygon vertices in the same metre
    coordinate system as the DEM/extent, enclosing area_ha hectares, centred on the
    DEM's extent centre, and shaped using that DEM's own local slope field.
    """
    seed = _seed_from(farm_name, round(lat, 5), round(lon, 5))
    rng = np.random.default_rng(seed)

    cx = (extent[0] + extent[1]) / 2
    cy = (extent[2] + extent[3]) / 2
    target_area_m2 = area_ha * 10000.0
    base_radius = math_sqrt(target_area_m2 / math_pi)

    dzdy, dzdx = np.gradient(dem, cellsize_m)
    slope = np.sqrt(dzdx ** 2 + dzdy ** 2)
    slope_norm = (slope - slope.min()) / (slope.max() - slope.min() + 1e-9)

    n_rows, n_cols = dem.shape
    x_coords = np.linspace(extent[0], extent[1], n_cols)
    y_coords = np.linspace(extent[2], extent[3], n_rows)

    angles = np.linspace(0, 2 * np.pi, n_vertices, endpoint=False)
    # smooth per-farm random perturbation (low-frequency "noise" via summed harmonics)
    harmonics = rng.uniform(0.06, 0.18, 4)
    phases = rng.uniform(0, 2 * np.pi, 4)
    freqs = [2, 3, 5, 7]
    shape_perturb = sum(h * np.sin(f * angles + p) for h, f, p in zip(harmonics, freqs, phases))

    radii = []
    for a, pert in zip(angles, shape_perturb):
        r_try = base_radius * (1 + pert)
        px = cx + r_try * np.cos(a)
        py = cy + r_try * np.sin(a)
        col = int(np.clip((px - extent[0]) / (extent[1] - extent[0]) * (n_cols - 1), 0, n_cols - 1))
        row = int(np.clip((py - extent[2]) / (extent[3] - extent[2]) * (n_rows - 1), 0, n_rows - 1))
        local_slope_factor = 1.0 - 0.15 * slope_norm[row, col]  # pull in slightly on steeper local slope
        radii.append(r_try * local_slope_factor)
    radii = np.array(radii)

    verts_x = cx + radii * np.cos(angles)
    verts_y = cy + radii * np.sin(angles)
    poly = np.column_stack([verts_x, verts_y])

    # rescale to hit the exact target area (shoelace formula)
    current_area = _polygon_area(poly)
    if current_area > 0:
        scale = math_sqrt(target_area_m2 / current_area)
        poly = np.column_stack([cx + (verts_x - cx) * scale, cy + (verts_y - cy) * scale])

    return poly


def _polygon_area(poly: np.ndarray) -> float:
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def math_sqrt(v):
    return float(np.sqrt(max(v, 0.0)))


def math_pi_const():
    return float(np.pi)


math_pi = np.pi
