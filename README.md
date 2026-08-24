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

## How to Run It

```bash
pip install -r requirements.txt
python gui.py
```

Select a crop, enter temperature and humidity, click "Update All Results." Set farm
area in the Irrigation Schedule tab to see volumes. Enter the farm owner's name in
Save Farm Report to generate a full Word report.

CLI equivalent: `python -m zaria_maize.main --mode {interactive,direct,indirect,compare}`
