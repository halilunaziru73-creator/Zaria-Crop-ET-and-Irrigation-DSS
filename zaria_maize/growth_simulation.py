"""
growth_simulation.py
----------------------
A crop growth-stage simulation LAYER: for the selected crop, simulates development
from germination (planting) through to harvest, using the pipeline's own trusted
crop-coefficient (Kc) curve as the physiological driver -- not a separate fabricated
growth model.

What is genuinely computed vs what is a labelled derived proxy:
  - Stage boundaries and Kc values: [FIELD DATA] for maize (real dataset Kc calendar),
    [FAO56-STD, calibrated] for the other four crops -- see crops.py.
  - Canopy-cover-fraction proxy: NOT measured/remote-sensed. Derived directly and
    transparently from the Kc curve as fc(t) = (Kc(t) - Kc_min) / (Kc_max - Kc_min),
    a standard simplification used when no LAI/NDVI observation exists (Allen et al.,
    FAO-56, Ch.7). Clearly labelled as a proxy on the figure itself.
"""
import os
from datetime import date, timedelta
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")

STAGE_DESCRIPTIONS = {
    "Initial": "Germination & early seedling establishment. Minimal canopy cover; crop water use is low.",
    "Development": "Vegetative growth. Canopy expands rapidly; water use rises with leaf area.",
    "Mid-season": "Flowering / grain- or fruit-fill. Maximum canopy cover and peak water demand.",
    "Late-season": "Maturation & senescence toward harvest. Canopy declines; water use tapers off.",
}


def simulate_growth_curve(crop_key: str, model=None, calibration_factor: float = 1.0):
    """
    Returns per-day-after-planting arrays (dap, kc, canopy_cover_fraction, stage_name)
    for the crop's own real season length, using:
      - maize: the field-measured Kc calendar (via thermal_model's trained climatology)
      - other crops: the crops.py FAO-56 curve, rescaled to the crop's real local
        season length (same logic already used for calibration elsewhere).
    """
    from . import crops as crops_mod
    from . import thermal_model as tm

    if crop_key == "maize":
        m = model or tm.load_or_build_model()
        # maize's real Kc calendar, restricted to the in-season days (Kc != 0.35 off-season)
        doy_kc = {int(d): v["kc"] for d, v in m.doy_climatology.items() if v.get("in_growing_season")}
        sorted_doy = sorted(doy_kc.keys())
        kc_series = np.array([doy_kc[d] for d in sorted_doy])
        dap = np.arange(len(kc_series))
        # assign stage labels by position within the season (Initial/Dev/Mid/Late ~ 23/40/45/26 days)
        bounds = np.cumsum([23, 40, 45, 26])
        stage_names = []
        for d in dap:
            if d < bounds[0]:
                stage_names.append("Initial")
            elif d < bounds[1]:
                stage_names.append("Development")
            elif d < bounds[2]:
                stage_names.append("Mid-season")
            else:
                stage_names.append("Late-season")
        stage_bounds_days = {"Initial": (0, bounds[0]), "Development": (bounds[0], bounds[1]),
                              "Mid-season": (bounds[1], bounds[2]), "Late-season": (bounds[2], len(dap))}
    else:
        profile = crops_mod.CROPS[crop_key]
        season = profile.seasons[0]
        n = season.length_days
        dap = np.arange(n)
        kc_series = np.array([crops_mod.kc_at_dap(profile, d, season_length_days=n) * profile.calibration_factor
                               for d in dap])
        lengths = profile.stage_lengths_days
        scale = n / sum(lengths.values())
        cum = 0
        stage_bounds_days = {}
        stage_names = []
        bounds_list = []
        for s, length in lengths.items():
            start = cum
            cum += length * scale
            stage_bounds_days[s] = (start, cum)
            bounds_list.append(cum)
        for d in dap:
            for s, (lo, hi) in stage_bounds_days.items():
                if lo <= d < hi or (s == "Late-season" and d >= lo):
                    stage_names.append(s)
                    break
            else:
                stage_names.append("Late-season")

    kc_min, kc_max = kc_series.min(), kc_series.max()
    canopy = (kc_series - kc_min) / (kc_max - kc_min + 1e-9)
    canopy = np.clip(canopy, 0, 1)

    return {"dap": dap, "kc": kc_series, "canopy_cover_proxy": canopy,
            "stage_names": stage_names, "stage_bounds_days": stage_bounds_days}


def plot_growth_simulation(crop_key: str, crop_display_name: str, farm_name: str,
                            planting_date: date = None, model=None,
                            fname: str = "growth_simulation.png") -> str:
    sim = simulate_growth_curve(crop_key, model=model)
    dap, kc, canopy = sim["dap"], sim["kc"], sim["canopy_cover_proxy"]
    stage_bounds = sim["stage_bounds_days"]
    planting_date = planting_date or date.today()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                                    gridspec_kw={"height_ratios": [1, 3]})

    stage_colors = {"Initial": "#f2e2b1", "Development": "#c8e6a0", "Mid-season": "#7fbf7f",
                     "Late-season": "#d9b382"}
    for s, (lo, hi) in stage_bounds.items():
        ax1.axvspan(lo, hi, color=stage_colors.get(s, "#eee"), alpha=0.8)
        ax2.axvspan(lo, hi, color=stage_colors.get(s, "#eee"), alpha=0.25)
        mid = (lo + hi) / 2
        ax1.text(mid, 0.5, s, ha="center", va="center", fontsize=8.5, fontweight="bold")
    ax1.set_ylim(0, 1)
    ax1.set_yticks([])
    ax1.set_title(f"Growth-Stage Timeline: Germination \u2192 Harvest: {crop_display_name} ({farm_name})",
                   fontsize=12, fontweight="bold")

    ax2.plot(dap, kc, color="#2f7d32", lw=2, label="Crop coefficient (Kc)")
    ax2.plot(dap, canopy, color="#1f6fb2", lw=2, ls="--", label="Canopy-cover proxy (derived from Kc, 0-1)")
    ax2.axvline(0, color="#8d5a2b", lw=1.5, ls=":", label="Germination / planting")
    ax2.axvline(dap[-1], color="#c94c4c", lw=1.5, ls=":", label="Harvest")
    ax2.set_xlabel("Days after planting")
    ax2.set_ylabel("Kc  /  Canopy-cover proxy")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(alpha=0.25)

    harvest_date = planting_date + timedelta(days=int(dap[-1]))
    fig.text(0.5, 0.005,
              f"Planting (germination): {planting_date.isoformat()}   |   Est. harvest: {harvest_date.isoformat()}   |   "
              f"Canopy-cover proxy is derived from the Kc curve (not measured/remote-sensed) -- "
              f"see growth_simulation.py.",
              ha="center", fontsize=7.5, color="#777")

    path = os.path.join(OUT_DIR, fname)
    os.makedirs(OUT_DIR, exist_ok=True)
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {"path": path, "planting_date": planting_date.isoformat(), "harvest_date": harvest_date.isoformat(),
            "season_length_days": int(dap[-1]) + 1, "stage_bounds_days": stage_bounds}
