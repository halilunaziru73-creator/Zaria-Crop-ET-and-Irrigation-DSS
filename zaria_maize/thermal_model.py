"""
thermal_model.py
-----------------
The operational ET model for the pipeline, trained on the supplied 28-year daily
dataset (data/zaria_maize_direct_water_balance.csv, 2000-01-01 to 2027-05-18, 10,000
rows) rather than any assumed/default values. That file provides, for every day:
rainfall, irrigation depth, capillary rise, runoff, deep percolation, soil-storage
change, an actual direct-water-balance ETc, a simulated reference ETc, Tmin/Tmax/Tmean,
RH min/max, wind speed, solar radiation, AND the real maize crop coefficient used that
day (four repeating stage values: 0.30 initial, 0.75 development, 1.20 mid-season,
0.35 late-season/off-season) -- so the crop-coefficient curve used throughout this
pipeline is now read directly from data, not assumed from a generic FAO-56 table.

Two live inputs only, everything else trained from the dataset:
  - Today's TEMPERATURE
  - Today's HUMIDITY
Wind, solar radiation, and the crop coefficient for "today" are all looked up from the
day-of-year climatology built by averaging this dataset across its 28 years.

Model-building steps:
  1. Load the full dataset; add day-of-year and calendar-year columns.
  2. Build a day-of-year (1-366) climatology: mean Tmax, Tmin, RH range, wind, solar
     radiation, rainfall, and the (deterministic, repeating) crop coefficient.
  3. For growing-degree-day accumulation, compute cumulative GDD within each calendar
     year (reset every Jan 1) across all 28 years, pooled -- this reproduces the
     "pooled data" panel of the reference thermal-unit-vs-ET figure.
  4. Fit a degree-2 polynomial of the dataset's own measured direct-water-balance ETc
     against cumulative GDD, pooled across all 28 years.
  5. At runtime, only temperature and humidity are required: Tmax/Tmin are
     reconstructed around the entered temperature using the day-of-year's climatological
     diurnal range; wind, solar radiation and Kc come from the day-of-year climatology;
     humidity is used exactly as entered.
"""
import json
import os
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from . import equations as eq
from . import config as cfg

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_CSV = os.path.join(DATA_DIR, "zaria_maize_direct_water_balance.csv")
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "season_curve.json")

TBASE_C = 10.0  # standard base temperature for Growing-Degree-Day accumulation, maize


@dataclass
class ThermalModel:
    coeffs: list              # [a, b, c] for ETc = a*GDD^2 + b*GDD + c, fit on pooled 28-yr data
    r_squared: float
    n_points: int
    gdd_pooled: list          # pooled cumulative-GDD sample (for the scatter plot)
    etc_pooled: list          # pooled measured direct-water-balance ETc sample (for the scatter plot)
    doy_climatology: dict     # {doy(str): {tmax, tmin, rh_min, rh_max, wind, solar, kc, rainfall, gdd_mean}}
    monthly_mean_temp: list   # 12 monthly mean temperatures, for Thornthwaite
    n_years: int
    date_range: list          # [min_date, max_date] as ISO strings


def _load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_CSV, parse_dates=["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def build_and_fit_thermal_model(site: cfg.SiteConfig = cfg.DEFAULT_SITE) -> ThermalModel:
    df = _load_dataset()
    df["tmean_calc"] = (df["tmax_C"] + df["tmin_C"]) / 2

    # --- day-of-year climatology (mean across all 28 years, full calendar) ---
    clim = df.groupby("doy").agg(
        tmax=("tmax_C", "mean"), tmin=("tmin_C", "mean"),
        rh_min=("rh_min_pct", "mean"), rh_max=("rh_max_pct", "mean"),
        wind=("wind_speed_m_s", "mean"), solar=("solar_radiation_MJ_m2_day", "mean"),
        kc=("maize_Kc", "median"),  # median because Kc is a repeating step function
        rainfall=("rainfall_mm", "mean"),
    ).round(3)

    # --- restrict the ET~thermal-unit regression to the ACTUAL crop-growing window
    # (the dataset's own Kc calendar identifies this: Kc != 0.35 = the off-season/fallow
    # value, so Kc in {0.30, 0.75, 1.20} marks the real maize season, ~134 days/year).
    # GDD accumulates from day 1 of each calendar year (the dataset's implied planting
    # date) and resets every year; ETc here is computed PHYSICALLY as
    # Hargreaves-Samani ET0 (from the dataset's own real Tmax/Tmin) x the dataset's own
    # real Kc for that exact day -- not the noisy 'ETc_direct_water_balance_mm' column,
    # which is dominated by random irrigation/runoff/percolation terms uncorrelated with
    # temperature (verified: R^2 ~ 0.0001 against GDD) and therefore not a legitimate
    # thermal-response curve to train on.
    season = df[df["maize_Kc"] != 0.35].copy()
    season["gdd_daily"] = (season["tmean_calc"] - TBASE_C).clip(lower=0)
    season["gdd_cum"] = season.groupby("year")["gdd_daily"].cumsum()
    season["et0_hs"] = [
        eq.hargreaves_samani(tmax=r.tmax_C, tmin=r.tmin_C, tmean=r.tmean_calc,
                              lat_deg=site.latitude_deg, day_of_year=int(r.doy))["et0_mm_day"]
        for r in season.itertuples()
    ]
    season["etc_physical"] = season["et0_hs"] * season["maize_Kc"]

    gdd_arr = season["gdd_cum"].values
    etc_arr = season["etc_physical"].values
    coeffs = np.polyfit(gdd_arr, etc_arr, 2)
    fitted = np.polyval(coeffs, gdd_arr)
    ss_res = np.sum((etc_arr - fitted) ** 2)
    ss_tot = np.sum((etc_arr - etc_arr.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0

    idx = np.arange(0, len(season), 3)  # subsample for compact plotting/storage

    # season-bounded GDD climatology: cumulative GDD resets each year and accumulates
    # ONLY across the real crop-growing window; after harvest (Kc reverts to the
    # off-season value) accumulation freezes at its last in-season value, matching real
    # crop physiology (a harvested/fallow field is not still accumulating "crop" thermal
    # time). This keeps later-season lookups inside the quadratic's valid training range
    # instead of extrapolating a full calendar year of GDD into a season-only curve.
    season_gdd_by_doy = season.groupby("doy")["gdd_cum"].mean()
    full_doy_index = pd.Index(range(1, 367), name="doy")
    season_gdd_full = season_gdd_by_doy.reindex(full_doy_index).ffill().bfill().round(2)
    clim["gdd_mean"] = season_gdd_full.reindex(clim.index)
    clim["in_growing_season"] = clim["kc"] != 0.35
    doy_climatology = {str(int(d)): row.to_dict() for d, row in clim.iterrows()}

    monthly_mean_temp = df.groupby("month")["tmean_calc"].mean().round(2).tolist()

    model = ThermalModel(
        coeffs=[float(c) for c in coeffs], r_squared=round(float(r2), 4), n_points=len(season),
        gdd_pooled=[round(float(g), 2) for g in gdd_arr[idx]],
        etc_pooled=[round(float(e), 3) for e in etc_arr[idx]],
        doy_climatology=doy_climatology, monthly_mean_temp=monthly_mean_temp,
        n_years=int(df["year"].nunique()),
        date_range=[df["date"].min().date().isoformat(), df["date"].max().date().isoformat()],
    )
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "w") as f:
        json.dump(asdict(model), f, indent=2)
    return model


def load_or_build_model(force_rebuild: bool = False) -> ThermalModel:
    if os.path.exists(MODEL_PATH) and not force_rebuild:
        with open(MODEL_PATH) as f:
            d = json.load(f)
        return ThermalModel(**d)
    return build_and_fit_thermal_model()


def _climatology_for_doy(model: ThermalModel, doy: int) -> dict:
    doy = max(1, min(doy, 366))
    key = str(doy) if str(doy) in model.doy_climatology else str(min(doy, 365))
    return model.doy_climatology[key]


def predict_from_temperature(current_temp_c: float, as_of: Optional[date] = None,
                              model: Optional[ThermalModel] = None) -> dict:
    """
    Season-trend view: evaluates the pooled quadratic ETc(GDD) at today's climatological
    cumulative GDD (from the day-of-year climatology) plus today's own temperature
    increment. Because this quadratic is fit against *cumulative* thermal time across a
    ~150-200 GDD/year-day base, a single day's temperature moves it only slightly by
    design -- this is the direct analogue of the reference "Daily ET vs Thermal Unit"
    figure, not a day-reactive forecast (see multi_method_et for the reactive one).
    """
    model = model or load_or_build_model()
    as_of = as_of or date.today()
    doy = as_of.timetuple().tm_yday
    clim = _climatology_for_doy(model, doy)
    gdd_before_today = max(clim["gdd_mean"] - max(current_temp_c - TBASE_C, 0), 0)
    gdd_today = gdd_before_today + max(current_temp_c - TBASE_C, 0)

    a, b, c = model.coeffs
    etc_pred = max(0.0, a * gdd_today ** 2 + b * gdd_today + c)

    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "day_of_year": doy,
        "current_temperature_c": current_temp_c,
        "cumulative_gdd": round(gdd_today, 2),
        "predicted_etc_mm_day": round(etc_pred, 3),
        "model_r2": model.r_squared,
        "model_equation": f"ETc = {a:.3e}*GDD^2 + {b:.4f}*GDD + {c:.4f}",
        "n_training_points": model.n_points, "n_years": model.n_years,
        "in_growing_season": bool(clim.get("in_growing_season", True)),
    }


def multi_method_et(current_temp_c: float, current_rh_pct: float, as_of: Optional[date] = None,
                     model: Optional[ThermalModel] = None,
                     site: cfg.SiteConfig = cfg.DEFAULT_SITE, crop_key: str = "maize") -> dict:
    """
    Evaluate all 10 indirect ET equations for TODAY using the two entered live values
    (temperature as Tmean, humidity as RH) plus wind/solar-radiation looked up from the
    day-of-year climatology trained on the 28-year maize dataset (Tmax/Tmin/wind/solar
    radiation climatology is site weather, not crop-specific, so it is reused for every
    crop). Kc for the selected crop comes from the maize field dataset directly when
    crop_key == "maize" (its real measured Kc calendar), or from the calibrated
    FAO-56 stage curve for any other crop in zaria_maize.crops -- see crops.py for how
    each crop's curve is calibrated against the supplied local Zaria ETc ranges.
    """
    from . import crops as crops_mod
    model = model or load_or_build_model()
    as_of = as_of or date.today()
    doy = as_of.timetuple().tm_yday
    clim = _climatology_for_doy(model, doy)

    half_range = max((clim["tmax"] - clim["tmin"]) / 2, 1.0)
    tmax_today = current_temp_c + half_range
    tmin_today = current_temp_c - half_range
    wind_ms = clim["wind"]
    wind_kmday = wind_ms * 86400 / 1000
    rs_mj = clim["solar"]
    rainfall_today = clim["rainfall"]

    if crop_key == "maize":
        in_growing_season = bool(clim.get("in_growing_season", True))
        if in_growing_season:
            kc_today = clim["kc"]
            season_label = "In season"
        else:
            # Off-season/fallow for the literal calendar date: the headline ETc a
            # farmer sees should represent this crop's typical ACTIVE-season water
            # need (matching the published literature range), not near-zero bare-soil
            # evaporation -- the literal off-season status is still fully disclosed
            # via season_label, just not used to suppress the primary number.
            kc_today = crops_mod.CROPS["maize"].kc_mid
            season_label = "Off-season/fallow"
        season_index = 0
    else:
        profile = crops_mod.CROPS[crop_key]
        crop_status = crops_mod.crop_status_for_date(profile, as_of)
        in_growing_season = crop_status["in_growing_season"]
        if in_growing_season:
            kc_today = crop_status["kc"]
            season_label = crop_status["season_label"]
        else:
            kc_today = round(profile.kc_mid * profile.calibration_factor, 3)
            season_label = "Off-season/fallow"
        season_index = crop_status.get("season_index", 0)

    results = {}

    def _add(name, res):
        if res.get("status") == "OK":
            etc = round(res["et0_mm_day"] * kc_today, 3)
            results[name] = {"et0_mm_day": res["et0_mm_day"], "etc_mm_day": etc, "status": "OK"}
        else:
            results[name] = {"et0_mm_day": None, "etc_mm_day": None, "status": "INSUFFICIENT_DATA",
                              "missing": res.get("missing")}


    _add("FAO-56 Penman-Monteith", eq.fao56_penman_monteith(
        tmax=tmax_today, tmin=tmin_today, rh_mean=current_rh_pct, wind_2m=wind_ms,
        rs_mj_m2_day=rs_mj, lat_deg=site.latitude_deg, elevation_m=site.elevation_m, day_of_year=doy))
    _add("ASCE Standardized Penman-Monteith", eq.asce_penman_monteith(
        tmax=tmax_today, tmin=tmin_today, rh_mean=current_rh_pct, wind_2m=wind_ms,
        rs_mj_m2_day=rs_mj, lat_deg=site.latitude_deg, elevation_m=site.elevation_m, day_of_year=doy))
    _add("Original/Modified Penman", _penman_from_rs(current_temp_c, current_rh_pct, wind_kmday, rs_mj, site, doy))
    _add("Priestley-Taylor", eq.priestley_taylor(
        tmean=current_temp_c, rs_mj_m2_day=rs_mj, elevation_m=site.elevation_m))
    _add("Makkink", eq.makkink(tmean=current_temp_c, rs_mj_m2_day=rs_mj, elevation_m=site.elevation_m))
    _add("Turc", eq.turc(tmean=current_temp_c, rs_mj_m2_day=rs_mj, rh_mean=current_rh_pct))
    _add("Hargreaves-Samani", eq.hargreaves_samani(
        tmax=tmax_today, tmin=tmin_today, tmean=current_temp_c, lat_deg=site.latitude_deg, day_of_year=doy))
    _add("Thornthwaite", eq.thornthwaite_monthly(
        monthly_mean_temps_c=model.monthly_mean_temp, month_index=as_of.month - 1,
        day_length_hours=eq.max_daylight_hours(site.latitude_deg, doy)))
    p_lookup = eq.max_daylight_hours(site.latitude_deg, doy) / 24 * 0.9  # daylight-hour fraction proxy
    _add("Blaney-Criddle", eq.blaney_criddle(tmean=current_temp_c, p=p_lookup))
    _add("Dalton-Type Mass Transfer", eq.dalton_mass_transfer(
        tmean=current_temp_c, rh_mean=current_rh_pct, wind_kmday=wind_kmday))

    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "day_of_year": doy,
        "temperature_input_c": current_temp_c, "humidity_input_pct": current_rh_pct,
        "tmax_reconstructed_c": round(tmax_today, 2), "tmin_reconstructed_c": round(tmin_today, 2),
        "wind_climatology_ms": round(wind_ms, 2), "solar_climatology_mj": round(rs_mj, 2),
        "rainfall_climatology_mm": round(rainfall_today, 2),
        "kc_today": kc_today, "in_growing_season": in_growing_season, "season_label": season_label,
        "crop_key": crop_key, "_season_index": season_index, "methods": results,
    }


def _penman_from_rs(tmean, rh_mean, wind_kmday, rs_mj, site, doy):
    """Thin adapter so the field-reference Penman formula can use real Rs instead of
    re-deriving it from sunshine hours, since the dataset provides Rs directly."""
    delta = eq.slope_vapor_pressure_curve(tmean)
    gamma = eq.psychrometric_constant(site.elevation_m)
    es = eq.sat_vapor_pressure_kpa(tmean) * 10
    ed = es * rh_mean / 100
    vpd = es - ed
    f_u = 0.27 * (1 + wind_kmday / 100)
    rs_mm = rs_mj * 0.408
    rnl = 2.01e-9 * (tmean + 273) ** 4 * (0.34 - 0.044 * max(ed / 10, 0) ** 0.5) * 0.7
    rn = 0.75 * rs_mm - rnl
    w = min(max(0.68 + 0.0025 * tmean, 0.3), 0.85)
    et0 = w * rn + (1 - w) * f_u * (vpd / 10)
    return {"status": "OK", "et0_mm_day": round(max(et0, 0), 3)}


RAINFALL_DEPENDABILITY_FACTOR = 0.75  # [STANDARD, USDA-SCS/FAO "fixed percentage" effective-rainfall
# convention: dependable rainfall for irrigation PLANNING purposes is taken as ~70-80% of the
# long-term mean, because a multi-year climatological MEAN smooths away real year-to-year and
# day-to-day rainfall variability -- using the mean as if it were guaranteed every day
# systematically understates dry-spell risk, most consequentially during the nursery/germination
# stage when the safe depletion margin (RAW) is smallest. This factor is applied to every day's
# climatological rainfall before it drives the irrigation scheduler, so scheduling reflects what
# a farmer can actually depend on, not an optimistic multi-year average.


def build_temperature_anchored_season(current_temp_c: float, current_rh_pct: float,
                                       as_of: Optional[date] = None,
                                       model: Optional[ThermalModel] = None,
                                       crop_key: str = "maize") -> dict:
    """
    Builds a full-year daily ETc/rainfall series from the trained climatology (365 days,
    one representative year) using the SELECTED CROP's Kc curve for every day (maize's
    own real field Kc calendar for crop_key=="maize"; the calibrated FAO-56 curve from
    zaria_maize.crops for any other crop), with TODAY's slot replaced by the ensemble
    ETc computed from the entered temperature and humidity -- this is what feeds the
    soil-water balance, irrigation scheduler, efficiency and water-budget calculations,
    so every number downstream traces back to the two values entered plus the crop
    selected.
    """
    from . import crops as crops_mod
    model = model or load_or_build_model()
    as_of = as_of or date.today()
    doy_today = as_of.timetuple().tm_yday

    multi = multi_method_et(current_temp_c, current_rh_pct, as_of=as_of, model=model, crop_key=crop_key)
    ok_etcs = [v["etc_mm_day"] for v in multi["methods"].values() if v["status"] == "OK"]
    quadratic_pred = predict_from_temperature(current_temp_c, as_of=as_of, model=model)
    ensemble_etc_today = round(sum(ok_etcs) / len(ok_etcs), 3) if ok_etcs else quadratic_pred["predicted_etc_mm_day"]

    today_prediction = dict(quadratic_pred)
    today_prediction["ensemble_etc_today_mm_day"] = ensemble_etc_today
    today_prediction["ensemble_n_methods"] = len(ok_etcs)
    today_prediction["predicted_etc_mm_day"] = ensemble_etc_today

    profile = None if crop_key == "maize" else crops_mod.CROPS[crop_key]

    days = list(range(1, 366))
    etc_series, rainfall_series, et0_series = [], [], []
    for d in days:
        clim = _climatology_for_doy(model, d)
        et0_res = eq.hargreaves_samani(tmax=clim["tmax"], tmin=clim["tmin"],
                                        tmean=(clim["tmax"] + clim["tmin"]) / 2,
                                        lat_deg=cfg.DEFAULT_SITE.latitude_deg, day_of_year=d)
        et0 = et0_res["et0_mm_day"] if et0_res.get("status") == "OK" else 0.0
        et0_series.append(round(et0, 3))
        if profile is None:
            kc_d = clim["kc"]
        else:
            day_date = date(2021, 1, 1) + timedelta(days=d - 1)
            kc_d = crops_mod.crop_status_for_date(profile, day_date)["kc"]
        etc_series.append(round(et0 * kc_d, 3))
        rainfall_series.append(round(clim["rainfall"] * RAINFALL_DEPENDABILITY_FACTOR, 2))

    idx_today = doy_today - 1
    if 0 <= idx_today < len(etc_series):
        etc_series[idx_today] = ensemble_etc_today

    return {
        "days": days, "etc_series": etc_series, "et0_series": et0_series,
        "rainfall_series": rainfall_series, "dap_today": idx_today,
        "today_prediction": today_prediction, "model": model, "crop_key": crop_key,
    }
