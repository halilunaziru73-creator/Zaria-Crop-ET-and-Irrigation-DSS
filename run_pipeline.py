"""
run_pipeline.py
----------------
End-to-end driver: runs the full Zaria Maize pipeline, exports tables (CSV), figures
(PNG) and the final Markdown report + text dashboard to /outputs.

Also runs a second, clearly-labelled DEMO scenario (assumed dry spell, zero rainfall)
purely to demonstrate the irrigation-scheduling mechanics, since the actual 2012
Jul-Aug field dataset data is a wet-season period in which rainfall alone satisfied crop
water demand (net irrigation = 0 mm) -- a genuine finding, not a pipeline limitation.
"""
import json
import os
import pandas as pd

from zaria_maize import main as pipeline
from zaria_maize import report as rpt
from zaria_maize import visualization as viz
from zaria_maize import soil_water as sw
from zaria_maize import irrigation as irr
from zaria_maize import config as cfg
from zaria_maize import interpolation as interp

OUT = "outputs"
TAB = os.path.join(OUT, "tables")
os.makedirs(TAB, exist_ok=True)


def main():
    results, data, indirect_results, downstream, days, rainfall_series = pipeline.run_full_pipeline()

    # ---------------- Tables ----------------
    method_rows = []
    for name, r in indirect_results.items():
        method_rows.append({
            "Method": name, "Source": r.get("source", r.get("note", "N/A")),
            "Mean_ET0_mm_day": r.get("mean_et0"), "Mean_ETc_mm_day": r.get("mean_etc"),
            "Seasonal_ETc_mm": r.get("seasonal_etc"),
            "RMSE": r.get("RMSE"), "MAE": r.get("MAE"), "Bias": r.get("Bias"),
            "MAPE_pct": r.get("MAPE_pct"), "R2": r.get("R2"), "NSE": r.get("NSE"),
        })
    method_df = pd.DataFrame(method_rows)
    method_df.to_csv(os.path.join(TAB, "et_method_comparison.csv"), index=False)

    dwb_df = pd.DataFrame([d.__dict__ for d in downstream["dwb"]])
    dwb_df.to_csv(os.path.join(TAB, "daily_soil_water_balance.csv"), index=False)

    sched_df = pd.DataFrame(downstream["schedule"]["events"])
    sched_df.to_csv(os.path.join(TAB, "irrigation_schedule.csv"), index=False)

    with open(os.path.join(TAB, "efficiency_and_water_budget.json"), "w") as f:
        json.dump({"efficiency": downstream["efficiency"], "losses": downstream["losses"],
                    "water_budget": downstream["water_budget"]}, f, indent=2)

    with open(os.path.join(TAB, "full_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    # ---------------- ET Index (point 25: interpolation + index) ----------------
    chosen_name = results["et"]["method_used"]
    chosen_etc = indirect_results[chosen_name]["etc"]
    etc_series_full = pd.Series(chosen_etc, index=days)
    idx_df = interp.compute_et_index(etc_series_full)
    idx_df.to_csv(os.path.join(TAB, "et_index.csv"))

    # demonstrate interpolation on an artificially-gapped copy (days 10,25,40 removed)
    gapped_days = [d for d in days if d not in (10, 25, 40)]
    gapped_vals = [chosen_etc[d - 1] for d in gapped_days]
    interp_df = interp.interpolate_et_series(gapped_days, gapped_vals)
    interp_df.to_csv(os.path.join(TAB, "et_interpolation_demo.csv"), index=False)

    # ---------------- Figures ----------------
    method_series = {name: r["etc"] for name, r in indirect_results.items()
                      if r.get("etc") is not None and all(v is not None for v in r["etc"])}
    viz.plot_method_comparison(days, method_series, "ETc by Method — Samaru Maize, Jul-Aug 2012",
                                "et_method_comparison.png")
    viz.plot_cumulative_et(days, method_series, "cumulative_etc.png")

    irrig_days = [e["day"] for e in downstream["schedule"]["events"]]
    depletion = [d.depletion_mm for d in downstream["dwb"]]
    viz.plot_soil_depletion(days, depletion, downstream["taw_raw"]["RAW_mm"],
                             downstream["taw_raw"]["TAW_mm"], irrig_days, "soil_depletion.png")
    viz.plot_rainfall_vs_etc(days, rainfall_series, chosen_etc, "rainfall_vs_etc.png")

    eff = downstream["efficiency"]
    viz.plot_efficiency_breakdown(eff["Ec"], eff["Ed"], eff["Ea"], eff["Ep"], "efficiency_breakdown.png")

    wb = downstream["water_budget"]
    viz.plot_water_budget_bar(
        ["Rainfall", "Eff. Rainfall", "ETc used", "Runoff", "Deep Perc."],
        [wb["rainfall_mm"], wb["effective_rainfall_mm"], wb["ETc_used_mm"],
         wb["runoff_mm"], wb["deep_percolation_mm"]], "water_budget.png")

    ref_series = list(data["comparison"]["etc_penman"])
    best_r = indirect_results[results["best_method"]]
    if best_r.get("etc"):
        viz.plot_residuals(days, best_r["etc"], ref_series, results["best_method"], "best_method_residuals.png")

    # ---------------- Kc growth-stage reference + ET Index figures ----------------
    viz.plot_kc_stage_reference(pipeline.cfg.DEFAULT_KC.stage_kc_reference,
                                 pipeline.cfg.DEFAULT_KC.stage_lengths_days_reference,
                                 "kc_growth_stage_reference.png")
    viz.plot_et_index(list(idx_df.index), list(idx_df["et_index"]), "et_index.png")

    # ---------------- Direct method + benchmark status ----------------
    direct_result = pipeline.run_direct_method()
    with open(os.path.join(TAB, "direct_method_result.json"), "w") as f:
        json.dump(direct_result, f, indent=2, default=str)

    benchmark_text, benchmark_status = pipeline.benchmark_methods(indirect_results)
    with open(os.path.join(OUT, "method_benchmark.txt"), "w") as f:
        f.write("METHOD AVAILABILITY BENCHMARK\n" + "=" * 40 + "\n" + benchmark_text)

    # ---------------- DEMO dry-spell irrigation scheduling illustration ----------------
    zero_rain = [0.0] * len(days)
    demo_dwb = sw.simulate_daily_soil_water_balance(
        days, chosen_etc, zero_rain, downstream["taw_raw"]["TAW_mm"],
        downstream["taw_raw"]["RAW_mm"], cfg.DEFAULT_IRRIGATION.field_application_efficiency_ea)
    demo_sched = irr.build_schedule(demo_dwb, cfg.DEFAULT_IRRIGATION)
    demo_irrig_days = [e["day"] for e in demo_sched["events"]]
    demo_depletion = [d.depletion_mm for d in demo_dwb]
    viz.plot_soil_depletion(days, demo_depletion, downstream["taw_raw"]["RAW_mm"],
                             downstream["taw_raw"]["TAW_mm"], demo_irrig_days,
                             "DEMO_dry_spell_soil_depletion.png")
    pd.DataFrame(demo_sched["events"]).to_csv(os.path.join(TAB, "DEMO_dry_spell_irrigation_schedule.csv"),
                                               index=False)
    with open(os.path.join(TAB, "DEMO_dry_spell_summary.json"), "w") as f:
        json.dump(demo_sched, f, indent=2)

    # ---------------- Dashboard + Markdown report ----------------
    dashboard_text = rpt.build_dashboard(results)
    with open(os.path.join(OUT, "dashboard.txt"), "w") as f:
        f.write(dashboard_text)

    md = rpt.build_markdown_report(results)
    md += "\n\n## 8. Illustrative Dry-Spell Irrigation-Scheduling Demo\n"
    md += ("The 1 Jul-31 Aug 2012 case study is a wet-season window (592 mm rainfall over 62 "
           "days) in which rainfall alone met crop demand, so the real-data schedule has **0** "
           "triggered irrigation events. To demonstrate the depletion-triggered scheduler "
           "mechanics, a `[DEMO/ASSUMED]` zero-rainfall scenario was also run using the same "
           f"ETc series: it produced **{demo_sched['n_events']}** irrigation events, "
           f"averaging every **{demo_sched['avg_interval_days']}** days, total net irrigation "
           f"**{demo_sched['net_seasonal_irrigation_mm']} mm** "
           f"(gross **{demo_sched['gross_seasonal_irrigation_mm']} mm**). "
           "See `DEMO_dry_spell_irrigation_schedule.csv` and `DEMO_dry_spell_soil_depletion.png`.\n")
    md += "\n\n## 9. Direct Method (Water Balance)\n"
    md += "\n\n## 9. Direct Method (Water Balance) — Verified Against 28-Year Dataset\n"
    md += f"**Status:** {direct_result['status']}\n\n"
    md += direct_result["message"] + "\n\n"
    md += "| Component | Mean annual (mm) |\n|---|---|\n"
    for k, v in direct_result["mean_annual_mm"].items():
        md += f"| {k} | {v} |\n"
    rv = direct_result["reconstruction_validation"]
    md += f"\nFormula reconstruction matches the source data column on **{rv['formula_matches_dataset_column_pct']}%** of days.\n"

    md += "\n\n## 10. Method Availability Benchmark\n```\n" + benchmark_text + "\n```\n"

    with open(os.path.join(OUT, "report.md"), "w") as f:
        f.write(md)

    print(dashboard_text)
    print("\nOutputs written to:", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
