"""
growth_video.py
-----------------
A "high-level simulation" layer for the selected crop: a stage-by-stage field-picture
filmstrip (nursery/germination -> harvest) with, at EACH stage, the water accounting
that actually drives the rest of this pipeline: crop coefficient (Kc), crop ET (ETc)
split into evaporation (E) and transpiration (T), soil-moisture retained, and the
irrigation water required for that stage (scaled to the farm's real entered area).

Where every number comes from (nothing here is a second, independent model):
  - Stage ETc, Kc: the SAME growth_simulation.py per-day series already used elsewhere.
  - E/T partition: the standard FAO-56 dual-crop-coefficient simplification,
    T = ETc x fc, E = ETc x (1-fc), where fc is the canopy-cover-fraction proxy
    (already derived from Kc in growth_simulation.py) — disclosed as a proxy, not a
    lysimeter/eddy-covariance measurement.
  - Moisture retained: the mean root-zone storage (as a % of TAW) actually simulated
    by soil_water.py for the days in that stage, from the SAME temperature-anchored
    season already computed for the Overview/Dashboard tabs.
  - Irrigation required: the SAME day-by-day irrigation schedule (soil_water /
    irrigation.py), summed over the days falling in that stage, converted to a volume
    using the farm's real area.

Output: a static filmstrip PNG (4 stage panels) for the report, and — if Pillow is
available — an actual animated GIF cycling through the stages as a lightweight
"video simulation" (no ffmpeg/video codec dependency required).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from . import growth_simulation as gsim
from . import crop_icons as ci

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")

STAGE_ORDER = ["Initial", "Development", "Mid-season", "Late-season"]
STAGE_LABELS = {"Initial": "Nursery / Germination", "Development": "Vegetative Development",
                "Mid-season": "Flowering / Mid-season", "Late-season": "Maturity / Harvest"}
STAGE_MATURITY = {"Initial": 0.08, "Development": 0.40, "Mid-season": 0.75, "Late-season": 1.0}


def compute_stage_water_balance(crop_key: str, area_ha: float, model, downstream: dict) -> list:
    """
    Returns one dict per growth stage with: day range, mean Kc, stage ETc (mm),
    evaporation (E, mm) and transpiration (T, mm) split, mean soil-moisture retained
    (% of TAW), and net/gross irrigation required for that stage (mm and m3, scaled
    to area_ha) — all pulled from the SAME simulated season as the rest of the app.
    """
    sim = gsim.simulate_growth_curve(crop_key, model=model)
    dap, kc, canopy = sim["dap"], sim["kc"], sim["canopy_cover_proxy"]
    stage_bounds = sim["stage_bounds_days"]

    dwb = downstream["dwb"]  # full-season daily water-balance records (day, etc, storage, irrigation...)
    mm_to_m3 = area_ha * 10

    rows = []
    for stage in STAGE_ORDER:
        lo, hi = stage_bounds[stage]
        lo_i, hi_i = int(round(lo)), int(round(hi))
        idx = [i for i in range(len(dap)) if lo_i <= dap[i] < hi_i] or [len(dap) - 1]
        kc_mean = float(np.mean([kc[i] for i in idx]))
        fc_mean = float(np.mean([canopy[i] for i in idx]))

        # Stage ETc from the same daily series used for irrigation scheduling
        # (dwb is indexed 1..365 as "day"; stage boundaries here are days-after-planting
        # within the crop's own season, so map proportionally onto the dwb day range
        # actually driving THIS farm's simulated season).
        n_days = max(hi_i - lo_i, 1)
        etc_stage = float(np.mean([dwb[min(d, len(dwb) - 1)].etc_mm for d in range(lo_i, hi_i)])) * n_days \
            if dwb else kc_mean * n_days * 5.0
        t_stage = etc_stage * fc_mean
        e_stage = etc_stage - t_stage

        storage_vals = [dwb[min(d, len(dwb) - 1)].storage_mm for d in range(lo_i, hi_i)] if dwb else []
        # Use each day's OWN (root-depth-varying) TAW = storage + depletion for that day,
        # not a single season-constant TAW — consistent with the growing-root-zone
        # water balance now driving the simulation (a shallow nursery-stage root zone
        # has a much smaller TAW than the mature crop).
        depletion_vals = [dwb[min(d, len(dwb) - 1)].depletion_mm for d in range(lo_i, hi_i)] if dwb else []
        daily_taw = [s + dep for s, dep in zip(storage_vals, depletion_vals)]
        moisture_pct = (float(np.mean(storage_vals)) / float(np.mean(daily_taw)) * 100
                         if storage_vals and daily_taw and np.mean(daily_taw) > 0 else None)

        net_irrig = sum(dwb[min(d, len(dwb) - 1)].irrigation_mm for d in range(lo_i, hi_i)) if dwb else 0.0
        net_irrig_m3 = net_irrig * mm_to_m3

        rows.append({
            "stage": stage, "label": STAGE_LABELS[stage], "day_range": (lo_i, hi_i),
            "kc_mean": round(kc_mean, 2), "canopy_cover_pct": round(fc_mean * 100, 1),
            "etc_stage_mm": round(etc_stage, 1), "evaporation_mm": round(e_stage, 1),
            "transpiration_mm": round(t_stage, 1), "moisture_retained_pct": round(moisture_pct, 1) if moisture_pct is not None else None,
            "net_irrigation_mm": round(net_irrig, 1), "net_irrigation_m3": round(net_irrig_m3, 1),
        })
    return rows


def generate_filmstrip(crop_key: str, crop_display_name: str, farm_name: str, stage_rows: list,
                        fname: str = "growth_filmstrip.png") -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    fig, axes = plt.subplots(1, 4, figsize=(14, 5.5))
    fig.suptitle(f"Growth-Stage Field Simulation: {crop_display_name} ({farm_name})",
                 fontsize=13, fontweight="bold")

    for ax, row in zip(axes, stage_rows):
        stage = row["stage"]
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="#eef6f0", edgecolor="#123524", lw=1.2, zorder=-1))
        ci.draw_crop_icon(ax, crop_key, STAGE_MATURITY[stage], cy=0.13)
        ax.set_title(row["label"], fontsize=9, fontweight="bold", pad=6)
        moisture_txt = f"{row['moisture_retained_pct']}%" if row["moisture_retained_pct"] is not None else "n/a"
        info = (f"Days {row['day_range'][0]}-{row['day_range'][1]}\n"
                f"Kc: {row['kc_mean']}\n"
                f"Canopy cover: {row['canopy_cover_pct']}%\n"
                f"ETc: {row['etc_stage_mm']} mm\n"
                f"  \u2022 Evap.: {row['evaporation_mm']} mm\n"
                f"  \u2022 Transp.: {row['transpiration_mm']} mm\n"
                f"Moisture retained: {moisture_txt}\n"
                f"Irrigation needed: {row['net_irrigation_mm']} mm\n"
                f"({row['net_irrigation_m3']:,.0f} m\u00b3)")
        ax.text(0.5, -0.06, info, ha="center", va="top", fontsize=7.3, transform=ax.transAxes,
                family="monospace")

    path = os.path.join(OUT_DIR, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_growth_gif(crop_key: str, crop_display_name: str, farm_name: str, stage_rows: list,
                         fname: str = "growth_simulation.gif", frames_per_stage: int = 8) -> dict:
    """Animated GIF cycling nursery -> harvest, one 'video simulation' pass. Requires
    Pillow (matplotlib's GIF writer backend); returns status if unavailable rather than
    crashing the rest of the report."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        return {"status": "SKIPPED", "reason": "Pillow not installed (pip install Pillow) — "
                                                 "static filmstrip PNG generated instead."}

    os.makedirs(OUT_DIR, exist_ok=True)
    maturities = []
    stage_map = []
    bounds = np.linspace(0, 1, len(STAGE_ORDER) + 1)
    for i, stage in enumerate(STAGE_ORDER):
        m0 = STAGE_MATURITY[STAGE_ORDER[i - 1]] if i > 0 else 0.0
        m1 = STAGE_MATURITY[stage]
        for f in range(frames_per_stage):
            maturities.append(m0 + (m1 - m0) * (f + 1) / frames_per_stage)
            stage_map.append(stage_rows[i])

    fig, ax = plt.subplots(figsize=(6, 6.6), dpi=130)

    def _draw(frame_idx):
        ax.clear()
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="#eef6f0", edgecolor="#123524", lw=1.2, zorder=-1))
        ci.draw_crop_icon(ax, crop_key, maturities[frame_idx], cy=0.16)
        row = stage_map[frame_idx]
        ax.set_title(f"{crop_display_name}: {row['label']}\nETc {row['etc_stage_mm']} mm "
                      f"(E {row['evaporation_mm']} / T {row['transpiration_mm']})  |  "
                      f"Irrigation {row['net_irrigation_mm']} mm", fontsize=10.5, fontweight="bold")
        return []

    anim = animation.FuncAnimation(fig, _draw, frames=len(maturities), interval=400, blit=False)
    path = os.path.join(OUT_DIR, fname)
    anim.save(path, writer="pillow", fps=2.2, dpi=130)
    plt.close(fig)
    return {"status": "OK", "path": path, "n_frames": len(maturities)}


def generate_irrigation_schedule_animation(crop_key: str, crop_display_name: str, farm_name: str,
                                            recommended_schedule: dict, area_ha: float,
                                            fname: str = "irrigation_schedule_animation.gif") -> dict:
    """
    An animated GIF cycling through the season's recommended irrigation events one by
    one, showing which day/stage each falls in, the field icon at that stage's
    maturity, cumulative water applied so far, and a filling water-drop gauge --
    complementing the crop growth-stage simulation with a dedicated view of the
    irrigation timeline itself.
    """
    try:
        import PIL  # noqa: F401
    except ImportError:
        return {"status": "SKIPPED", "reason": "Pillow not installed (pip install Pillow) -- "
                                                 "no static fallback for this animation."}

    events = recommended_schedule.get("events", [])
    if not events:
        return {"status": "SKIPPED", "reason": "No irrigation events to animate for this run."}

    os.makedirs(OUT_DIR, exist_ok=True)
    mm_to_m3 = area_ha * 10
    cumulative = []
    running = 0.0
    for e in events:
        running += e["net_irrigation_mm"]
        cumulative.append(running)
    total_net = cumulative[-1] if cumulative else 1.0

    fig, (ax_icon, ax_gauge) = plt.subplots(1, 2, figsize=(9, 5), dpi=130,
                                             gridspec_kw={"width_ratios": [1.3, 1]})

    def _draw(i):
        ax_icon.clear(); ax_gauge.clear()
        e = events[i]
        maturity = STAGE_MATURITY.get(e["stage"], 0.5)

        ax_icon.set_xlim(0, 1); ax_icon.set_ylim(0, 1); ax_icon.set_aspect("equal"); ax_icon.axis("off")
        ax_icon.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="#eef6f0", edgecolor="#123524", lw=1.2, zorder=-1))
        ci.draw_crop_icon(ax_icon, crop_key, maturity, cy=0.16)
        ax_icon.set_title(f"Day {e['day']}: {e['stage']}", fontsize=12, fontweight="bold")

        # water gauge: a filling vertical bar showing cumulative progress through the season
        ax_gauge.set_xlim(0, 1); ax_gauge.set_ylim(0, 1); ax_gauge.axis("off")
        frac = cumulative[i] / total_net if total_net else 0
        ax_gauge.add_patch(plt.Rectangle((0.35, 0.05), 0.3, 0.85, facecolor="none",
                                          edgecolor="#1f6fb2", lw=2))
        ax_gauge.add_patch(plt.Rectangle((0.35, 0.05), 0.3, 0.85 * frac, facecolor="#4a90d9",
                                          edgecolor="none"))
        ax_gauge.text(0.5, 0.97, "Season progress", ha="center", fontsize=10.5, fontweight="bold")
        ax_gauge.text(0.5, -0.02,
                      f"Event {i + 1}/{len(events)}\n"
                      f"This event: {e['net_irrigation_mm']} mm net ({e['net_irrigation_mm'] * mm_to_m3:,.0f} m\u00b3)\n"
                      f"Cumulative: {round(cumulative[i], 1)} mm ({round(cumulative[i] * mm_to_m3):,} m\u00b3)",
                      ha="center", va="top", fontsize=10)

        fig.suptitle(f"Irrigation Schedule Simulation: {crop_display_name} ({farm_name})",
                     fontsize=13, fontweight="bold")
        return []

    anim = animation.FuncAnimation(fig, _draw, frames=len(events), interval=450, blit=False)
    path = os.path.join(OUT_DIR, fname)
    anim.save(path, writer="pillow", fps=2.0, dpi=130)
    plt.close(fig)
    return {"status": "OK", "path": path, "n_frames": len(events)}
