"""
report.py
---------
Builds the final text dashboard and Markdown report from a results dict assembled by
main.py. Every field is populated only from actual pipeline calculations/field dataset data;
unavailable fields are rendered explicitly as "DATA NOT AVAILABLE".
"""
from typing import Dict


def _fmt(v, unit=""):
    if v is None:
        return "DATA NOT AVAILABLE"
    if isinstance(v, float):
        return f"{v:.2f}{unit}"
    return f"{v}{unit}"


def build_dashboard(r: Dict) -> str:
    lines = []
    A = lines.append
    A("=" * 62)
    A("ZARIA CROP ET AND IRRIGATION DSS")
    A("=" * 62)
    A("")
    A(f"Location:      {r['site']['town']}, {r['site']['state']} "
      f"(Lat {r['site']['latitude_deg']} N, {r['site']['elevation_m']} m a.s.l.)")
    crop = r.get("crop")
    if crop:
        A(f"Crop:          {crop['display_name']}")
        A(f"  Locally-reported seasonal ETc range: {crop['local_etc_range_mm'][0]}-{crop['local_etc_range_mm'][1]} mm")
        if crop.get("context"):
            A(f"  {crop['context']}")
    else:
        A(f"Crop:          {r['site']['crop']}")
    ti = r.get("temperature_input")
    if ti:
        A(f"Date:          {ti['date']}   (day {ti['day_of_year']} of year)")
        A(f"INPUT TEMPERATURE:        {ti['temperature_c']} \u00b0C  <-- entered")
        A(f"INPUT HUMIDITY:           {ti['humidity_pct']} %  <-- entered")
        A(f"  (reconstructed Tmax/Tmin: {ti['tmax_reconstructed_c']}/{ti['tmin_reconstructed_c']} \u00b0C; "
          f"wind/solar from trained climatology: {ti['wind_climatology_ms']} m/s, {ti['solar_climatology_mj']} MJ/m2/day)")
        A(f"  Crop coefficient (Kc) today: {ti['kc_today']}")
    else:
        A(f"Season:        {r['site']['season_start']} to {r['site']['season_end']}")
    if r.get("area_ha") is not None:
        A(f"Area:          {_fmt(r.get('area_ha'))} ha")
    A("")
    A(f"SELECTED ET METHOD:      {r['et']['method_used']}")
    if "today_predicted_etc" in r["et"]:
        A(f"TODAY'S PREDICTED ETc:   {_fmt(r['et'].get('today_predicted_etc'), ' mm/day')}  "
          f"(ensemble mean of the live methods that ran for this temperature)")
        A(f"  Season-trend model R\u00b2:  {r['et'].get('today_model_r2')}   "
          f"({r['et'].get('today_model_equation')})")
    A(f"Mean ET0 (season):       {_fmt(r['et'].get('mean_et0'), ' mm/day')}")
    A(f"Mean ETc (season):       {_fmt(r['et'].get('mean_etc'), ' mm/day')}")
    A(f"Seasonal ETc (full simulated year): {_fmt(r['et'].get('seasonal_etc'), ' mm')}")
    if r["et"].get("growing_season_etc_mm") is not None:
        A(f"Growing-season ETc ({r['et'].get('growing_season_days')} days): "
          f"{_fmt(r['et'].get('growing_season_etc_mm'), ' mm')}")
    A("")
    A("WATER DEMAND  [Predicted from weather data: entered temperature/humidity + trained climatology]")
    A(f"EFFECTIVE RAINFALL (season):     {_fmt(r['water'].get('effective_rainfall_mm'), ' mm')}")
    A(f"NET IRRIGATION REQUIREMENT:      {_fmt(r['water'].get('net_irrigation_mm'), ' mm')}")
    A(f"GROSS IRRIGATION REQUIREMENT:    {_fmt(r['water'].get('gross_irrigation_mm'), ' mm')}")
    A("")
    sch = r["schedule"]
    A(f"NUMBER OF IRRIGATION EVENTS:     {sch.get('n_events')}")
    if sch.get("avg_interval_days") is not None:
        A(f"AVERAGE IRRIGATION INTERVAL:     {_fmt(sch.get('avg_interval_days'), ' days')}")
    if sch.get("next_irrigation_day_after_series") is not None:
        A(f"NEXT IRRIGATION (day index):     {_fmt(sch.get('next_irrigation_day_after_series'))}")
    A("")
    wb = r["water_budget"]
    A("WATER BUDGET  [Predicted from weather data (rainfall/ETc) + irrigation-system assumptions below]")
    A(f"TOTAL WATER SUPPLIED (I+P):      {_fmt(wb.get('total_supplied_mm'), ' mm')}")
    A(f"TOTAL WATER USED (ETc):          {_fmt(wb.get('total_used_mm'), ' mm')}")
    A(f"TOTAL WATER LOST (RO+DP+AppLoss):{_fmt(wb.get('total_lost_mm'), ' mm')}")
    if wb.get("storage_change_mm") is not None:
        A(f"SOIL STORAGE CHANGE:             {_fmt(wb.get('storage_change_mm'), ' mm')}")
    if wb.get("balance_residual_mm") is not None:
        A(f"WATER BALANCE RESIDUAL:          {_fmt(wb.get('balance_residual_mm'), ' mm')}  (should be ~0)")
    A("")
    eff = r["efficiency"]
    A("SYSTEM EFFICIENCY  [Standard irrigation-engineering assumptions for the configured system, "
      "NOT measured for this specific farm; replace with your system's real measured values if known]")
    A(f"CONVEYANCE EFFICIENCY (Ec):      {_fmt(eff.get('Ec'), ' %')}")
    A(f"DISTRIBUTION EFFICIENCY (Ed):    {_fmt(eff.get('Ed'), ' %')}")
    A(f"APPLICATION EFFICIENCY (Ea):     {_fmt(eff.get('Ea'), ' %')}")
    A(f"OVERALL SYSTEM EFFICIENCY (Ep):  {_fmt(eff.get('Ep'), ' %')}")
    A("")
    wue = r["wue"]
    if wue.get("status") == "OK":
        A(f"WATER USE EFFICIENCY:            {wue.get('WUEc_kg_per_mm_per_ha')} kg/mm/ha")
        A("")
    A(f"ET MODEL:                {r.get('best_method', 'N/A')}")
    A("=" * 62)
    return "\n".join(lines)


def build_markdown_report(r: Dict) -> str:
    md = []
    A = md.append
    A(f"# Zaria Crop ET and Irrigation DSS, Report\n")
    A("## 1. Project Information\n")
    A(f"| Parameter | Value |\n|---|---|")
    A(f"| Location | {r['site']['town']}, {r['site']['state']} |")
    A(f"| Latitude / Elevation | {r['site']['latitude_deg']} N / {r['site']['elevation_m']} m |")
    crop = r.get("crop")
    if crop:
        A(f"| Crop | {crop['display_name']} |")
        A(f"| Locally-reported seasonal ETc range | {crop['local_etc_range_mm'][0]}-{crop['local_etc_range_mm'][1]} mm |")
    else:
        A(f"| Crop | {r['site']['crop']} |")
    ti = r.get("temperature_input")
    if ti:
        A(f"| Date | {ti['date']} (day {ti['day_of_year']} of year) |")
        A(f"| **Input temperature** | **{ti['temperature_c']} \u00b0C** |")
        A(f"| **Input humidity** | **{ti['humidity_pct']} %** |")
        A(f"| Reconstructed Tmax/Tmin | {ti['tmax_reconstructed_c']} / {ti['tmin_reconstructed_c']} \u00b0C |")
        A(f"| Wind / Solar radiation (trained climatology) | {ti['wind_climatology_ms']} m/s / {ti['solar_climatology_mj']} MJ/m2/day |")
        A(f"| Crop coefficient (Kc) today | {ti['kc_today']} |")
    else:
        A(f"| Season | {r['site']['season_start']} to {r['site']['season_end']} |")
    A("")
    A("## 2. ET Results, All Methods, Evaluated at the Entered Temperature\n")
    has_rmse = any(m.get("RMSE") is not None for m in r["et"]["all_methods"])
    if has_rmse:
        A("| Method | Mean ET0 (mm/d) | Mean ETc (mm/d) | Seasonal ETc (mm) | RMSE | MAE | R2 |")
        A("|---|---|---|---|---|---|---|")
        for m in r["et"]["all_methods"]:
            A(f"| {m['method']} | {m.get('mean_et0','-')} | {m.get('mean_etc','-')} | "
              f"{m.get('seasonal_etc','-')} | {m.get('RMSE','-')} | {m.get('MAE','-')} | {m.get('R2','-')} |")
    else:
        A("| Method | ET0 today (mm/d) | ETc today (mm/d) | Status |")
        A("|---|---|---|---|")
        for m in r["et"]["all_methods"]:
            A(f"| {m['method']} | {m.get('mean_et0','-')} | {m.get('mean_etc','-')} | {m.get('status','-')} |")
    A("")
    A("## 3. Soil Water Parameters\n")
    A("| Parameter | Value | Unit |\n|---|---|---|")
    sw = r["soil_water"]
    for k, unit in [("field_capacity_pct", "%"), ("pwp_pct", "%"), ("root_zone_depth_m", "m"),
                    ("TAW_mm", "mm"), ("RAW_mm", "mm"), ("MAD", "-")]:
        A(f"| {k} | {sw.get(k)} | {unit} |")
    A("")
    A("## 4. Irrigation Schedule (first 15 events shown)\n")
    A("| Day | Net Irrigation (mm) | Gross Irrigation (mm) |\n|---|---|---|")
    for e in r["schedule"]["events"][:15]:
        A(f"| {e['day']} | {e['net_irrigation_mm']} | {e['gross_irrigation_mm']} |")
    A("")
    A("## 5. System Efficiency\n")
    A("| Parameter | Result | Unit |\n|---|---|---|")
    eff = r["efficiency"]
    A(f"| Conveyance efficiency (Ec) | {eff.get('Ec')} | % |")
    A(f"| Distribution efficiency (Ed) | {eff.get('Ed')} | % |")
    A(f"| Application efficiency (Ea) | {eff.get('Ea')} | % |")
    A(f"| Overall efficiency (Ep) | {eff.get('Ep')} | % |")
    if r["wue"].get("status") == "OK":
        A(f"| Water use efficiency | {r['wue']['WUEc_kg_per_mm_per_ha']} kg/mm/ha | - |")
    A("")
    A("## 6. Seasonal Water Budget\n")
    A("| Component | Value (mm) |\n|---|---|")
    for k, v in r["water_budget"].items():
        A(f"| {k} | {v} |")
    A("")
    A("## 7. Data Provenance & Methodology\n")
    A("- Every result on this report is anchored to the single temperature you entered.")
    A("  All other same-day inputs (RH, wind, sunshine) are the site's own historical climatological")
    A("  normal for this position in the growing season, see `thermal_model.py` for the exact method.")
    A("- Weather/ET data: the Samaru field weather dataset, Samaru station.")
    A("- ET, irrigation-scheduling and efficiency formulas: standard irrigation-engineering relationships.")
    A("- Soil FC/PWP, irrigation-system efficiencies and yield are **not present** in the supplied data;")
    A("  demonstration/standard-default values are used and flagged `[DEMO]`/`[STANDARD]` in the code.")
    return "\n".join(md)
