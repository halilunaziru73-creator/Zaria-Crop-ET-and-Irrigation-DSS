### Hi, this is a research repository by Naziru Halilu 👋


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22076048.svg)](https://doi.org/10.5281/zenodo.22076048)

**Zaria Crop ET and Irrigation DSS**

A modular Python pipeline, with a Tkinter desktop GUI, for reference/crop
evapotranspiration (ET0/ETc), soil-water balance, irrigation scheduling,
irrigation-system efficiency, direct water-balance verification, full
farm-report generation, QGIS-style study-area layouts, and a crop
growth-stage video simulation, for five crops grown around Zaria, Nigeria:
maize, rice, sorghum, pepper, and cowpea.

📫 halilunaziru73@gmail.com

---

## Problem, Methodology, and Results

**Workflow sketch**

![Workflow Sketch](workflow_sketch.png)

[View interactive graphical walkthrough →](https://halilunaziru73-creator.github.io/Zaria-Crop-ET-and-Irrigation-DSS/)

**Problem.** Smallholder and mid-scale farmers around Zaria, Nigeria need to know how much to irrigate and when, but the standard tools for this (FAO-56 ET equations, soil-water balance models) are scattered across spreadsheets, published tables, and disconnected scripts, with no single accessible tool that turns live weather input into a specific, farm-sized irrigation schedule and report.

**Methodology.** The pipeline runs ten indirect ET equations alongside a direct water-balance equation, a trained growing-degree-day/ET thermal model, and a daily soil-water depletion simulation (TAW/RAW), then generates a dynamic irrigation schedule, compares four delivery methods (furrow, basin/flood, sprinkler, drip) for the farm's actual area, and assembles a full Word report with a farm-specific QGIS-style terrain layout and a stage-by-stage crop growth simulation. Every numeric constant is explicitly tagged as `[FIELD DATA]`, `[LOCAL-REPORTED]`, `[STANDARD]`/`[FAO56-STD]`, or `[DEMO/ASSUMED]`, and results with no underlying data are removed from the display automatically rather than shown as a plausible-looking placeholder.

**Results.** For a sample 3-hectare maize farm, the pipeline predicted 6.178 mm/day of crop water use on the day tested, 546.11 mm of growing-season water use over 135 days, 399.1 mm of net seasonal irrigation, and recommended drip irrigation across 32 scheduled events at 26.65% overall system efficiency, closing the seasonal water balance to within 0.1 mm. Two real water-balance bugs were found and fixed during development: effective rainfall could exceed total rainfall (infiltration was capped against total rather than remaining soil storage capacity), and the seasonal ledger left roughly 213 mm unaccounted for because two different irrigation totals were being mixed together.

## Contents

```
zaria_maize/            Core pipeline: equations, thermal model, soil-water balance,
                         irrigation scheduling, efficiency accounting, XAI explanation,
                         farm mapping, QGIS-style terrain layout, report assembly
data/                    28-year maize training dataset, weather data, case-study CSVs
outputs/                 Sample dashboard, report, and figures for a demonstration farm
assets/                  App icon and author image
gui.py                   Desktop GUI (Tkinter)
run_pipeline.py          CLI entry point
```

## Download the Desktop App

A packaged Windows desktop app is available, no Python installation required:

**[⬇ Download ZariaCropETIrrigationDSS.exe](https://github.com/halilunaziru73-creator/Zaria-Crop-ET-and-Irrigation-DSS/releases/tag/v1.1.0)**

(~284 MB, Windows only. Run the .exe directly.)

## How to Run It

```bash
pip install -r requirements.txt
python gui.py
```

Select a crop, enter temperature and humidity, click "Update All Results." Set farm
area in the Irrigation Schedule tab to see volumes. Enter the farm owner's name in
Save Farm Report to generate a full Word report.

CLI equivalent: `python -m zaria_maize.main --mode {interactive,direct,indirect,compare}`

---

## Figures

![Cumulative crop water use (ETc) accumulated over the growing season.](outputs/figures/cumulative_etc.png)
*Cumulative crop water use (ETc) accumulated over the growing season.*

![Irrigation-system efficiency breakdown: conveyance, distribution, application, and overall efficiency.](outputs/figures/efficiency_breakdown.png)
*Irrigation-system efficiency breakdown: conveyance, distribution, application, and overall efficiency.*

![Schematic farm map with delineated boundary and irrigation-method recommendation.](outputs/figures/farm_map_Sample_Farm_Owner.png)
*Schematic farm map with delineated boundary and irrigation-method recommendation.*

![Stage-by-stage filmstrip of the crop growth simulation, germination through harvest.](outputs/figures/growth_filmstrip_Sample_Farm_Owner.png)
*Stage-by-stage filmstrip of the crop growth simulation, germination through harvest.*

![Crop growth-stage simulation with per-stage water accounting.](outputs/figures/growth_simulation_Sample_Farm_Owner.png)
*Crop growth-stage simulation with per-stage water accounting.*

![Seasonal monitoring chart for routine field checks.](outputs/figures/monitoring_chart_Sample_Farm_Owner.png)
*Seasonal monitoring chart for routine field checks.*

![Combined evapotranspiration and climate panel for the season.](outputs/figures/panel_et_climate_Sample_Farm_Owner.png)
*Combined evapotranspiration and climate panel for the season.*

![Combined soil-water and irrigation-efficiency panel.](outputs/figures/panel_soil_efficiency_Sample_Farm_Owner.png)
*Combined soil-water and irrigation-efficiency panel.*

![Input / Core Processing / Output diagram of the full pipeline (also the workflow sketch above).](outputs/figures/process_diagram_Sample_Farm_Owner.png)
*Input / Core Processing / Output diagram of the full pipeline (also the workflow sketch above).*

![Comparison view of the QGIS-style terrain layout against the schematic farm map.](outputs/figures/qgis_comparison_Sample_Farm_Owner.png)
*Comparison view of the QGIS-style terrain layout against the schematic farm map.*

![Farm-specific QGIS-style terrain characterisation: location, altitude, slope, W-E and N-S profiles, aspect.](outputs/figures/qgis_terrain_Sample_Farm_Owner.png)
*Farm-specific QGIS-style terrain characterisation: location, altitude, slope, W-E and N-S profiles, aspect.*

![Rainfall versus crop water use (ETc) across the season.](outputs/figures/rainfall_vs_etc.png)
*Rainfall versus crop water use (ETc) across the season.*

![Seasonal crop ET compared against reference ET (ET0).](outputs/figures/seasonal_et_vs_reference.png)
*Seasonal crop ET compared against reference ET (ET0).*

![Daily soil-water depletion tracked against Total and Readily Available Water (TAW/RAW).](outputs/figures/soil_depletion.png)
*Daily soil-water depletion tracked against Total and Readily Available Water (TAW/RAW).*

![Soil profile used for the water-balance simulation.](outputs/figures/soil_profile_Sample_Farm_Owner.png)
*Soil profile used for the water-balance simulation.*

![Growing-degree-day (thermal unit) regression underlying the crop-stage model.](outputs/figures/thermal_unit_regression.png)
*Growing-degree-day (thermal unit) regression underlying the crop-stage model.*

![Comparison of ET calculation methods for the day tested.](outputs/figures/today_method_comparison.png)
*Comparison of ET calculation methods for the day tested.*

![Full seasonal water budget: rainfall, effective rainfall, ETc used, runoff, and deep percolation.](outputs/figures/water_budget.png)
*Full seasonal water budget: rainfall, effective rainfall, ETc used, runoff, and deep percolation.*

