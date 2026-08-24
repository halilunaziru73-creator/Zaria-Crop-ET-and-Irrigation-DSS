# Zaria Crop ET and Irrigation DSS, Report

## 1. Project Information

| Parameter | Value |
|---|---|
| Location | Samaru, Zaria, Kaduna State, Nigeria |
| Latitude / Elevation | 11.11 N / 686.0 m |
| Crop | Maize (Corn) |
| Locally-reported seasonal ETc range | 420-550 mm |
| Date | 2026-08-24 05:08:51 (day 236 of year) |
| **Input temperature** | **32.0 °C** |
| **Input humidity** | **55.0 %** |
| Reconstructed Tmax/Tmin | 36.58 / 27.42 °C |
| Wind / Solar radiation (trained climatology) | 1.94 m/s / 21.25 MJ/m2/day |
| Crop coefficient (Kc) today | 1.2 |

## 2. ET Results, All Methods, Evaluated at the Entered Temperature

| Method | ET0 today (mm/d) | ETc today (mm/d) | Status |
|---|---|---|---|
| FAO-56 Penman-Monteith | 6.035 | 7.242 | OK |
| ASCE Standardized Penman-Monteith | 6.035 | 7.242 | OK |
| Original/Modified Penman | 2.825 | 3.39 | OK |
| Priestley-Taylor | 6.831 | 8.197 | OK |
| Makkink | 4.295 | 5.154 | OK |
| Turc | 4.937 | 5.924 | OK |
| Hargreaves-Samani | 5.316 | 6.379 | OK |
| Thornthwaite | 3.886 | 4.663 | OK |
| Blaney-Criddle | 10.463 | 12.556 | OK |
| Dalton-Type Mass Transfer | 0.86 | 1.032 | OK |

## 3. Soil Water Parameters

| Parameter | Value | Unit |
|---|---|---|
| field_capacity_pct | 28.0 | % |
| pwp_pct | 14.0 | % |
| root_zone_depth_m | 1.0 | m |
| TAW_mm | 140.0 | mm |
| RAW_mm | 91.0 | mm |
| MAD | 0.65 | - |

## 4. Irrigation Schedule (first 15 events shown)

| Day | Net Irrigation (mm) | Gross Irrigation (mm) |
|---|---|---|
| 38 | 31.57 | 55.39 |
| 52 | 30.33 | 53.21 |
| 75 | 74.93 | 131.46 |
| 92 | 74.66 | 130.98 |
| 108 | 73.4 | 128.77 |
| 125 | 76.79 | 134.72 |
| 185 | 7.37 | 12.93 |
| 198 | 7.66 | 13.44 |
| 213 | 7.5 | 13.16 |
| 232 | 7.67 | 13.46 |
| 361 | 7.2 | 12.63 |

## 5. System Efficiency

| Parameter | Result | Unit |
|---|---|---|
| Conveyance efficiency (Ec) | 85.0 | % |
| Distribution efficiency (Ed) | 55.0 | % |
| Application efficiency (Ea) | 57.0 | % |
| Overall efficiency (Ep) | 26.65 | % |

## 6. Seasonal Water Budget

| Component | Value (mm) |
|---|---|
| rainfall_mm | 445.4 |
| effective_rainfall_mm | 292.0 |
| gross_irrigation_mm | 700.1 |
| net_irrigation_mm | 399.1 |
| ETc_used_mm | 906.4 |
| runoff_mm | 0.0 |
| deep_percolation_mm | 153.4 |
| application_loss_mm | 301.0 |
| root_zone_growth_gain_mm | 216.4 |
| storage_change_mm | 1.0 |
| total_supplied_mm | 1361.9 |
| total_used_mm | 906.4 |
| total_lost_mm | 454.4 |
| balance_residual_mm | 0.1 |

## 7. Data Provenance & Methodology

- Every result on this report is anchored to the single temperature you entered.
  All other same-day inputs (RH, wind, sunshine) are the site's own historical climatological
  normal for this position in the growing season, see `thermal_model.py` for the exact method.
- Weather/ET data: the Samaru field weather dataset, Samaru station.
- ET, irrigation-scheduling and efficiency formulas: standard irrigation-engineering relationships.
- Soil FC/PWP, irrigation-system efficiencies and yield are **not present** in the supplied data;
  demonstration/standard-default values are used and flagged `[DEMO]`/`[STANDARD]` in the code.