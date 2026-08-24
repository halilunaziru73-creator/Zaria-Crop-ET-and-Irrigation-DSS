"""
visualization.py
-----------------
Matplotlib figures for the pipeline. All plotted numbers trace back to either the
field dataset CSVs (data_loader) or calculations performed in equations/soil_water/irrigation.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def _save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_method_comparison(days, series_dict, title, fname):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for label, vals in series_dict.items():
        ax.plot(days, vals, marker='o', ms=2, lw=1.2, label=label)
    ax.set_xlabel("Day of season (1 Jul - 31 Aug 2012)")
    ax.set_ylabel("ETc (mm/day)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    return _save(fig, fname)


def plot_cumulative_et(days, series_dict, fname):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for label, vals in series_dict.items():
        cum = [sum(vals[:i + 1]) for i in range(len(vals))]
        ax.plot(days, cum, lw=1.5, label=label)
    ax.set_xlabel("Day of season")
    ax.set_ylabel("Cumulative ETc (mm)")
    ax.set_title("Cumulative Seasonal ETc by Method")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    return _save(fig, fname)


def plot_soil_depletion(days, depletion, raw_mm, taw_mm, irrigation_days, fname):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(days, depletion, color="saddlebrown", lw=1.5, label="Root-zone depletion (mm)")
    ax.axhline(raw_mm, color="orange", ls="--", label=f"RAW threshold ({raw_mm:.0f} mm)")
    ax.axhline(taw_mm, color="red", ls=":", label=f"TAW ({taw_mm:.0f} mm)")
    for d in irrigation_days:
        ax.axvline(d, color="steelblue", alpha=0.4, lw=1)
    ax.set_xlabel("Day of season")
    ax.set_ylabel("Depletion (mm)")
    ax.set_title("Soil-Water Depletion vs RAW Threshold (blue lines = irrigation events)")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    return _save(fig, fname)


def plot_rainfall_vs_etc(days, rainfall, etc, fname):
    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax1.bar(days, rainfall, color="steelblue", alpha=0.5, label="Rainfall (mm)")
    ax1.set_ylabel("Rainfall (mm)")
    ax2 = ax1.twinx()
    ax2.plot(days, etc, color="darkgreen", lw=1.5, label="ETc (mm/day)")
    ax2.set_ylabel("ETc (mm/day)")
    ax1.set_xlabel("Day of season")
    ax1.set_title("Rainfall vs Crop ET (ETc)")
    fig.legend(loc="upper right", bbox_to_anchor=(0.9, 0.88), fontsize=8)
    return _save(fig, fname)


def plot_cumulative_irrigation(irrig_days, irrig_amounts, fname):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    cum = [sum(irrig_amounts[:i + 1]) for i in range(len(irrig_amounts))]
    ax.step(irrig_days, cum, where="post", lw=1.8, color="teal")
    ax.scatter(irrig_days, cum, color="teal", s=20)
    ax.set_xlabel("Day of season")
    ax.set_ylabel("Cumulative net irrigation (mm)")
    ax.set_title("Cumulative Irrigation Applied Over Season")
    ax.grid(alpha=.3)
    return _save(fig, fname)


def plot_water_budget_bar(labels, values, fname, title="Seasonal Water Budget (mm)"):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = ["#2b7a78", "#3aafa9", "#feffff", "#def2f1", "#c94c4c", "#f2a541"][:len(labels)]
    ax.bar(labels, values, color=colors, edgecolor="black")
    ax.set_ylabel("mm")
    ax.set_title(title)
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    plt.xticks(rotation=20, ha="right")
    return _save(fig, fname)


def plot_efficiency_breakdown(ec, ed, ea, ep, fname):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    labels = ["Conveyance\n(Ec)", "Distribution\n(Ed)", "Application\n(Ea)", "Overall\n(Ep)"]
    vals = [ec, ed, ea, ep]
    ax.bar(labels, vals, color=["#264653", "#2a9d8f", "#e9c46a", "#e76f51"], edgecolor="black")
    ax.set_ylabel("Efficiency (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Irrigation System Efficiency Breakdown")
    for i, v in enumerate(vals):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=9)
    return _save(fig, fname)


def plot_kc_stage_reference(stage_kc: dict, stage_lengths: dict, fname):
    """FAO-56 reference maize Kc-stage curve — [DEMO/EXTERNAL-REFERENCE], not field dataset data."""
    fig, ax = plt.subplots(figsize=(8, 4))
    x, y, cum = [], [], 0
    for stage, days_len in stage_lengths.items():
        kc = stage_kc[stage]
        x += [cum, cum + days_len]
        y += [kc, kc]
        ax.axvline(cum, color="grey", ls=":", lw=0.7)
        ax.text(cum + days_len / 2, kc + 0.03, stage, ha="center", fontsize=8)
        cum += days_len
    ax.plot(x, y, color="darkgreen", lw=2)
    ax.set_xlabel("Days after planting (reference lengths — not field dataset data)")
    ax.set_ylabel("Kc")
    ax.set_title("Maize Kc Growth-Stage Curve: FAO-56 reference values (supplementary, not field dataset)")
    ax.set_ylim(0, 1.4)
    ax.grid(alpha=.3)
    return _save(fig, fname)


def plot_et_index(days, et_index, fname):
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = ["seagreen" if v >= 1 else "indianred" for v in et_index]
    ax.bar(days, et_index, color=colors)
    ax.axhline(1.0, color="black", lw=1, ls="--", label="Season mean (Index = 1.0)")
    ax.set_xlabel("Day of season")
    ax.set_ylabel("ET Index (ETc(day) / seasonal mean ETc)")
    ax.set_title("Daily ET Index: Screening Diagnostic")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    return _save(fig, fname)


def plot_thermal_unit_regression(gdd, etc, coeffs, r2, current_point=None, fname="thermal_unit_regression.png"):
    """Reproduces the 'Daily ET vs Thermal Unit' quadratic-regression figure style."""
    import numpy as np
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.scatter(gdd, etc, s=22, color="#f0a500", edgecolor="#8a6d00", alpha=0.85, zorder=2)
    xs = np.linspace(min(gdd), max(gdd), 200)
    a, b, c = coeffs
    ys = a * xs ** 2 + b * xs + c
    ax.plot(xs, ys, color="#333333", lw=1.8, zorder=3)
    sign_b = "+" if b >= 0 else "-"
    sign_c = "+" if c >= 0 else "-"
    eqn = f"y = {a:.1e}x$^2$ {sign_b} {abs(b):.4f}x {sign_c} {abs(c):.4f}\nR$^2$ = {r2:.4f}"
    ax.text(0.05, 0.92, eqn, transform=ax.transAxes, va="top", fontsize=11,
            bbox=dict(boxstyle="round", fc="white", ec="grey", alpha=0.9))
    if current_point is not None:
        ax.scatter([current_point[0]], [current_point[1]], s=140, color="crimson",
                    marker="*", zorder=5, label="Today's prediction")
        ax.legend(loc="lower right", fontsize=9)
    ax.set_xlabel("Thermal unit / cumulative GDD (\u00b0C)")
    ax.set_ylabel("Daily crop evapotranspiration (mm)")
    ax.set_title("Daily Crop ET vs Thermal Unit")
    ax.grid(alpha=.25)
    return _save(fig, fname)


def plot_seasonal_et_vs_reference(dap_series, etc_series, et0_series, current_dap=None,
                                   current_etc=None, fname="seasonal_et_vs_reference.png"):
    """Reproduces the 'Crop ET versus Reference ET' seasonal-curve figure style."""
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(dap_series, et0_series, color="#d62728", lw=2.4, label="Reference ET (ET0)")
    ax.plot(dap_series, etc_series, color="#1f77b4", lw=2.4, label="Crop ET (ETc)")
    ax.fill_between(dap_series, etc_series, color="#1f77b4", alpha=0.08)
    if current_dap is not None and current_etc is not None:
        ax.scatter([current_dap], [current_etc], color="crimson", marker="*", s=160,
                    zorder=5, label="Today")
    ax.set_xlabel("Days after planting")
    ax.set_ylabel("ET (mm/day)")
    ax.set_title("Crop ET versus Reference ET: Season Progression")
    ax.legend(fontsize=9)
    ax.grid(alpha=.25)
    return _save(fig, fname)


def plot_residuals(days, estimated, reference, method_name, fname):
    fig, ax = plt.subplots(figsize=(9, 4))
    resid = [e - r for e, r in zip(estimated, reference)]
    ax.bar(days, resid, color=["crimson" if r < 0 else "seagreen" for r in resid])
    ax.axhline(0, color="black", lw=1)
    ax.set_xlabel("Day of season")
    ax.set_ylabel("Residual (mm/day)")
    ax.set_title(f"{method_name} minus Reference: Daily Residuals")
    ax.grid(alpha=.3)
    return _save(fig, fname)
