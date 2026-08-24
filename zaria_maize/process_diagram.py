"""
process_diagram.py
--------------------
Draws the ET / soil-water decision process using the grouped INPUT -> CORE PROCESSING
-> OUTPUT layout format (dashed rounded group containers, solid rounded boxes inside,
each group colour-coded), populated with THIS report's own actual computed values at
every box -- not a generic template.

The OUTPUT stage includes a genuine per-input stress attribution: when the crop is
under water stress today, the diagram identifies WHICH input is the dominant driver
(high temperature/VPD, low humidity, or a still-shallow root zone) using a simple,
disclosed rule-based comparison of this run's own values -- not a black box.
"""
import os
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

from . import equations as eq

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")

GROUP_COLORS = {
    "INPUT": {"label": "#2E75B6", "border": "#a8c8e8", "box": "#2E75B6"},
    "CORE PROCESSING": {"label": "#8B5A2B", "border": "#d4b896", "box": "#8B5A2B"},
    "OUTPUT": {"label": "#2E7D46", "border": "#a8d8b8", "box": "#2E7D46"},
}


def compute_process_values(current_temp_c: float, current_rh_pct: float, today_multi: dict,
                            downstream: dict, taw_raw: dict, today_index: int = None) -> dict:
    """Pulls/derives every number the diagram needs from THIS run's own results.

    today_index: the 0-based index into the 365-day dwb/raw_series/zr_series arrays
    that actually corresponds to "today" (pass season['dap_today']). Previously this
    always used index -1 (the LAST day of the array, 31 December's year-end
    climatology) regardless of what date/crop/inputs were actually being analysed --
    a real bug, since that made every box below the weather-input line (Kcb, Ke, Zr,
    ETc demand, depletion, RAW, TAW, stress diagnosis) look identical across
    different runs. Fixed here by indexing the correct day when today_index is given.
    """
    es = eq.sat_vapor_pressure_kpa(current_temp_c)
    ea = es * current_rh_pct / 100
    vpd = round(es - ea, 3)

    kc_today = today_multi["kc_today"]
    dwb = downstream["dwb"]
    idx = today_index if (today_index is not None and dwb and 0 <= today_index < len(dwb)) else -1
    today_dwb = dwb[idx] if dwb else None
    raw_series = downstream.get("raw_series")
    zr_series = downstream.get("zr_series")
    taw_today = (today_dwb.storage_mm + today_dwb.depletion_mm) if today_dwb else taw_raw["TAW_mm"]
    # Use the ACTUAL day-varying RAW threshold that drove today's scheduling decision
    # (the growing-root-zone value), not the season-constant/mature figure -- a
    # shallow-rooted nursery-stage day has a much smaller RAW than a mature crop.
    raw_today = raw_series[idx] if raw_series and -len(raw_series) <= idx < len(raw_series) else taw_raw["RAW_mm"]
    fc = max(0.05, min(1.0, kc_today / 1.2)) if kc_today else 0.5
    kcb = round(kc_today * fc, 3)
    ke = round(max(kc_today - kcb, 0), 3)

    dr = today_dwb.depletion_mm if today_dwb else 0.0
    stressed = dr > raw_today
    if stressed and taw_today > raw_today:
        ks = round(max(0.0, (taw_today - dr) / (taw_today - raw_today)), 3)
    else:
        ks = 1.0
    etc_potential = today_dwb.etc_mm if today_dwb else 0.0
    etc_actual = round(etc_potential * ks, 3)

    zr_today_m = round(zr_series[idx], 2) if zr_series and -len(zr_series) <= idx < len(zr_series) else None

    # --- per-input stress attribution: which input is the dominant driver today? ---
    dominant_factor = None
    if stressed:
        temp_score = max(0.0, (current_temp_c - 30) / 10)
        humidity_score = max(0.0, (40 - current_rh_pct) / 40)
        rootzone_score = max(0.0, (0.5 - (zr_today_m or 0.5)) / 0.5)
        scores = {"High temperature": temp_score, "Low humidity": humidity_score,
                  "Shallow root zone (early growth stage)": rootzone_score}
        top_factor, top_score = max(scores.items(), key=lambda kv: kv[1])
        if top_score <= 0:
            dominant_factor = "Elevated crop water demand outpacing rainfall for this stage"
        elif top_factor == "High temperature":
            dominant_factor = f"High temperature ({current_temp_c}\u00b0C) driving VPD to {vpd} kPa"
        elif top_factor == "Low humidity":
            dominant_factor = f"Low humidity ({current_rh_pct}%) driving VPD to {vpd} kPa"
        else:
            dominant_factor = f"Still-shallow root zone ({zr_today_m} m) limiting the water buffer"
    else:
        dominant_factor = "No stress \u2014 inputs are balanced for today's crop stage"

    return {
        "temp_c": current_temp_c, "rh_pct": current_rh_pct,
        "vpd_kpa": vpd, "es_kpa": round(es, 3), "ea_kpa": round(ea, 3),
        "kcb": kcb, "ke": ke, "kc_total": kc_today,
        "zr_m": zr_today_m,
        "taw_today_mm": round(taw_today, 1), "raw_mm": round(raw_today, 1),
        "dr_mm": round(dr, 1), "stressed": stressed, "ks": ks,
        "etc_potential_mm": round(etc_potential, 2), "etc_actual_mm": etc_actual,
        "dominant_factor": dominant_factor,
    }


def _wrap(text, width=30):
    lines = []
    for segment in text.split("\n"):
        wrapped = textwrap.wrap(segment, width=width, break_long_words=False) or [""]
        lines.extend(wrapped)
    return "\n".join(lines)


def _group_container(ax, x, y, w, h, label, color):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.05",
                                          facecolor="none", edgecolor=color["border"], lw=1.6,
                                          linestyle=(0, (4, 3)), zorder=1))
    ax.text(x + 0.15, y + h - 0.30, label, fontsize=10, fontweight="bold",
            color=color["label"], ha="left", va="top", zorder=3)


def _inner_box(ax, x, y, w, h, text, color, fontsize=8.6):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.035",
                                          facecolor="white", edgecolor=color, lw=1.7, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
            zorder=3, linespacing=1.5, wrap=True)


def _v_arrow(ax, x, y_top, y_bot, color):
    ax.add_patch(FancyArrowPatch((x, y_top), (x, y_bot), arrowstyle="-|>", mutation_scale=13,
                                  color=color, lw=1.8, zorder=2))


def plot_process_diagram(values: dict, farm_name: str, crop_display_name: str,
                          fname: str = "process_diagram.png") -> str:
    os.makedirs(OUT_DIR, exist_ok=True)

    box_w, box_h, gap = 5.0, 1.15, 0.30
    label_pad, bottom_pad, inter_group_gap = 0.58, 0.20, 0.32
    group_h = label_pad + 2 * box_h + gap + bottom_pad
    total_h = 3 * group_h + 2 * inter_group_gap + 0.55  # + title space

    fig, ax = plt.subplots(figsize=(5.2, total_h * 0.62))
    ax.set_xlim(0, 6)
    ax.set_ylim(0, total_h)
    ax.axis("off")
    ax.set_title(f"{crop_display_name}: {farm_name}", fontsize=10.5, fontweight="bold", pad=6)

    x0 = 0.5
    y_top = total_h - 0.55

    # ---------------- INPUT group ----------------
    ic = GROUP_COLORS["INPUT"]
    gy = y_top - group_h
    _group_container(ax, 0, gy, 6, group_h, "INPUT", ic)
    b1y = gy + group_h - label_pad - box_h
    _inner_box(ax, x0, b1y, box_w, box_h,
               _wrap(f"Live Weather Input\nT={values['temp_c']}\u00b0C, RH={values['rh_pct']}%\n"
                     f"VPD = {values['vpd_kpa']} kPa", 34), ic["box"], fontsize=7.8)
    b2y = b1y - gap - box_h
    _inner_box(ax, x0, b2y, box_w, box_h,
               _wrap(f"Dual-Kc Engine\nKcb (transpiration) = {values['kcb']}\n"
                     f"Ke (soil evaporation) = {values['ke']}", 32), ic["box"], fontsize=7.8)
    _v_arrow(ax, 3, b1y, b2y + box_h, ic["box"])

    # arrow between groups
    _v_arrow(ax, 3, gy, gy - inter_group_gap, "#999999")

    # ---------------- CORE PROCESSING group ----------------
    cc = GROUP_COLORS["CORE PROCESSING"]
    gy2 = gy - inter_group_gap - group_h
    _group_container(ax, 0, gy2, 6, group_h, "CORE PROCESSING", cc)
    c1y = gy2 + group_h - label_pad - box_h
    zr_txt = f"{values['zr_m']} m" if values["zr_m"] is not None else "n/a"
    _inner_box(ax, x0, c1y, box_w, box_h,
               _wrap(f"Dynamic Root Zone Depth\nZr = {zr_txt}\n"
                     f"Potential ETc demand = {values['etc_potential_mm']} mm/day", 32), cc["box"], fontsize=7.8)
    c2y = c1y - gap - box_h
    _inner_box(ax, x0, c2y, box_w, box_h,
               _wrap(f"Soil-Water Depletion\nDr = {values['dr_mm']} mm  vs  "
                     f"RAW = {values['raw_mm']} mm (TAW={values['taw_today_mm']} mm)", 34), cc["box"], fontsize=7.8)
    _v_arrow(ax, 3, c1y, c2y + box_h, cc["box"])

    _v_arrow(ax, 3, gy2, gy2 - inter_group_gap, "#999999")

    # ---------------- OUTPUT group ----------------
    oc = GROUP_COLORS["OUTPUT"]
    gy3 = gy2 - inter_group_gap - group_h
    _group_container(ax, 0, gy3, 6, group_h, "OUTPUT", oc)
    o1y = gy3 + group_h - label_pad - box_h
    status_txt = "WATER STRESS TODAY" if values["stressed"] else "No stress today"
    _inner_box(ax, x0, o1y, box_w, box_h,
               _wrap(f"Stress Diagnosis: {status_txt}\nDominant factor: {values['dominant_factor']}", 36),
               oc["box"], fontsize=7.4)
    o2y = o1y - gap - box_h
    _inner_box(ax, x0, o2y, box_w, box_h,
               _wrap(f"Result\nKs (stress coefficient) = {values['ks']}\n"
                     f"Actual ETc today = {values['etc_actual_mm']} mm/day", 32), oc["box"], fontsize=7.8)
    _v_arrow(ax, 3, o1y, o2y + box_h, oc["box"])

    fig.tight_layout()
    path = os.path.join(OUT_DIR, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
