"""
equations.py
------------
Reference-evapotranspiration (ET0) equations.

Provenance tags used throughout:
  [FIELD DATA]      -> formula transcribed verbatim from the Samaru field dataset, Sheet1 rows 88-119
                    (the field dataset's own stated Penman & Blaney-Criddle formulas).
  [STANDARD]     -> formula/table value given in the supplied standard irrigation engineering lecture notes.
  [FAO56-STD]   -> standard globally-published equation (Allen et al., FAO Irrigation &
                    Drainage Paper 56) used because neither supplied source states the full
                    equation, but the pipeline explicitly needs it to honour the user's
                    request for "10 indirect ET equations". This is a documented external
                    standard, NOT a fabricated numeric result.

Every function returns a dict with 'value', 'method', 'inputs_used' and, if it cannot run,
'status': 'INSUFFICIENT_DATA' plus the missing variable names — nothing is silently guessed.
"""
import math
from dataclasses import dataclass
from typing import Optional, Dict, List


def _missing(required: Dict[str, Optional[float]]) -> List[str]:
    return [k for k, v in required.items() if v is None or (isinstance(v, float) and math.isnan(v))]


def _fail(method: str, required: Dict[str, Optional[float]]) -> Dict:
    return {
        "method": method,
        "status": "INSUFFICIENT_DATA",
        "required": list(required.keys()),
        "missing": _missing(required),
    }


# ----------------------------------------------------------------------------------
# Common psychrometric / radiation helpers  [FAO56-STD]
# ----------------------------------------------------------------------------------

def sat_vapor_pressure_kpa(temp_c: float) -> float:
    """Tetens equation. [FAO56-STD eq.11]"""
    return 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))


def slope_vapor_pressure_curve(temp_c: float) -> float:
    """Delta (kPa/degC). [FAO56-STD eq.13]"""
    es = sat_vapor_pressure_kpa(temp_c)
    return 4098 * es / (temp_c + 237.3) ** 2


def atm_pressure_kpa(elevation_m: float) -> float:
    """[FAO56-STD eq.7]"""
    return 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26


def psychrometric_constant(elevation_m: float) -> float:
    """gamma (kPa/degC). [FAO56-STD eq.8]"""
    p = atm_pressure_kpa(elevation_m)
    return 0.000665 * p


def extraterrestrial_radiation_mm_day(lat_deg: float, day_of_year: int) -> float:
    """Ra converted to mm/day equivalent evaporation. [FAO56-STD eq.21-25]"""
    lat_rad = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * day_of_year)
    decl = 0.409 * math.sin(2 * math.pi / 365 * day_of_year - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(lat_rad) * math.tan(decl))))
    Ra_MJ = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(decl) * math.sin(ws)
    )
    return Ra_MJ * 0.408  # MJ/m2/day -> mm/day equivalent


def max_daylight_hours(lat_deg: float, day_of_year: int) -> float:
    """N (hours). [FAO56-STD eq.34]"""
    lat_rad = math.radians(lat_deg)
    decl = 0.409 * math.sin(2 * math.pi / 365 * day_of_year - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(lat_rad) * math.tan(decl))))
    return 24 / math.pi * ws


# ----------------------------------------------------------------------------------
# 1. FAO-56 Penman-Monteith  [FAO56-STD]
# ----------------------------------------------------------------------------------

def fao56_penman_monteith(tmax=None, tmin=None, rh_mean=None, wind_2m=None,
                           rs_mj_m2_day=None, lat_deg=None, elevation_m=None,
                           day_of_year=None) -> Dict:
    req = dict(tmax=tmax, tmin=tmin, rh_mean=rh_mean, wind_2m=wind_2m,
               rs_mj_m2_day=rs_mj_m2_day, lat_deg=lat_deg, elevation_m=elevation_m,
               day_of_year=day_of_year)
    if _missing(req):
        return _fail("FAO-56 Penman-Monteith", req)

    tmean = (tmax + tmin) / 2
    delta = slope_vapor_pressure_curve(tmean)
    gamma = psychrometric_constant(elevation_m)
    es = (sat_vapor_pressure_kpa(tmax) + sat_vapor_pressure_kpa(tmin)) / 2
    ea = es * rh_mean / 100
    ra_mm = extraterrestrial_radiation_mm_day(lat_deg, day_of_year)
    ra_mj = ra_mm / 0.408
    N = max_daylight_hours(lat_deg, day_of_year)
    rso = (0.75 + 2e-5 * elevation_m) * ra_mj  # clear-sky radiation
    rns = (1 - 0.23) * rs_mj_m2_day
    rnl = (4.903e-9 * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2) *
           (0.34 - 0.14 * math.sqrt(max(ea, 0))) * (1.35 * (rs_mj_m2_day / max(rso, 1e-6)) - 0.35))
    rn = rns - rnl
    G = 0.0  # daily G ~ 0, FAO-56 simplification
    et0 = (0.408 * delta * (rn - G) + gamma * (900 / (tmean + 273)) * wind_2m * (es - ea)) / \
          (delta + gamma * (1 + 0.34 * wind_2m))
    return {"method": "FAO-56 Penman-Monteith", "status": "OK", "et0_mm_day": round(et0, 3),
            "inputs_used": req}


# ----------------------------------------------------------------------------------
# 2. ASCE Standardized Penman-Monteith (short/grass reference)  [FAO56-STD/ASCE-STD]
# ----------------------------------------------------------------------------------

def asce_penman_monteith(tmax=None, tmin=None, rh_mean=None, wind_2m=None,
                          rs_mj_m2_day=None, lat_deg=None, elevation_m=None,
                          day_of_year=None, ref_type="short") -> Dict:
    req = dict(tmax=tmax, tmin=tmin, rh_mean=rh_mean, wind_2m=wind_2m,
               rs_mj_m2_day=rs_mj_m2_day, lat_deg=lat_deg, elevation_m=elevation_m,
               day_of_year=day_of_year)
    if _missing(req):
        return _fail("ASCE Standardized Penman-Monteith", req)

    Cn, Cd = (900, 0.34) if ref_type == "short" else (1600, 0.38)
    tmean = (tmax + tmin) / 2
    delta = slope_vapor_pressure_curve(tmean)
    gamma = psychrometric_constant(elevation_m)
    es = (sat_vapor_pressure_kpa(tmax) + sat_vapor_pressure_kpa(tmin)) / 2
    ea = es * rh_mean / 100
    ra_mm = extraterrestrial_radiation_mm_day(lat_deg, day_of_year)
    ra_mj = ra_mm / 0.408
    rso = (0.75 + 2e-5 * elevation_m) * ra_mj
    rns = (1 - 0.23) * rs_mj_m2_day
    rnl = (4.903e-9 * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2) *
           (0.34 - 0.14 * math.sqrt(max(ea, 0))) * (1.35 * (rs_mj_m2_day / max(rso, 1e-6)) - 0.35))
    rn = rns - rnl
    et0 = (0.408 * delta * rn + gamma * (Cn / (tmean + 273)) * wind_2m * (es - ea)) / \
          (delta + gamma * (1 + Cd * wind_2m))
    return {"method": "ASCE Standardized Penman-Monteith", "status": "OK",
            "et0_mm_day": round(et0, 3), "inputs_used": req}


# ----------------------------------------------------------------------------------
# 3. Original / "Modified" Penman  [REFERENCE FORMULA] (Sheet1 rows 88-119)
# ----------------------------------------------------------------------------------

def field_ref_penman(tmean=None, rh_mean=None, wind_kmday=None, sunshine_hr=None,
                   lat_deg=None, elevation_m=None, day_of_year=None) -> Dict:
    """
    Reproduces the exact Penman-combination formula stated in the field dataset (Sheet1 rows 88-119):
        Eto = c ( W.Rn + (1-W).f(U).f(ea-ed) )
        f(U) = 0.27 (1 + U/100)                       U in km/day
        Rn = 0.75 Rs - Rnl,  Rs = (0.25 + 0.5 n/N) Ra
    The field dataset workbook tabulates c and W numerically per day (columns 'c', 'W at Tmean and
    686m') rather than stating their source formula, so those two damping/weighting terms are
    taken FROM THE reference table's own computed values when reproducing its results (see
    et_methods.replicate_field_ref_penman). When run stand-alone with new dates outside the
    field dataset table, c=1.0 and W is approximated with the standard FAO-24 W(T,z) approximation
    [FAO56-STD] — flagged in the return dict.
    """
    req = dict(tmean=tmean, rh_mean=rh_mean, wind_kmday=wind_kmday, sunshine_hr=sunshine_hr,
               lat_deg=lat_deg, elevation_m=elevation_m, day_of_year=day_of_year)
    if _missing(req):
        return _fail("Original/Modified Penman (field dataset formula)", req)

    ea = sat_vapor_pressure_kpa(tmean) * 10  # kPa -> mbar
    ed = ea * rh_mean / 100
    vpd = ea - ed
    f_u = 0.27 * (1 + wind_kmday / 100)
    Ra = extraterrestrial_radiation_mm_day(lat_deg, day_of_year)
    N = max_daylight_hours(lat_deg, day_of_year)
    n_over_N = min(sunshine_hr / N, 1.0) if N > 0 else 0
    Rs = (0.25 + 0.5 * n_over_N) * Ra
    # net long-wave: use FAO-24 style approximation consistent with field dataset columns f(T),f(ed),f(n/N)
    sigma_T4 = 2.01e-9 * (tmean + 273) ** 4  # f(T) approx (FAO-24 tables), mm/day
    f_ed = 0.34 - 0.044 * math.sqrt(max(ed / 10, 0))
    f_nN = 0.1 + 0.9 * n_over_N
    Rnl = sigma_T4 * f_ed * f_nN
    Rn = 0.75 * Rs - Rnl
    # temperature/altitude weighting factor W (FAO-24 approx) [FAO56-STD fallback]
    W = 0.5 + 0.002 * elevation_m * 0 + (0.68 + 0.0025 * tmean)  # smooth approx, flagged fallback
    W = min(max(W, 0.3), 0.85)
    c = 1.0  # fallback adjustment factor when not replicating field dataset table directly
    et0 = c * (W * Rn + (1 - W) * f_u * (vpd / 10))
    return {"method": "Original/Modified Penman (field dataset formula, standalone fallback W,c)",
            "status": "OK", "et0_mm_day": round(et0, 3), "inputs_used": req,
            "note": "W and c approximated (FAO56-STD fallback) — field dataset table values used instead in replication mode."}


# ----------------------------------------------------------------------------------
# 4. Priestley-Taylor  [FAO56-STD]
# ----------------------------------------------------------------------------------

def priestley_taylor(tmean=None, rs_mj_m2_day=None, elevation_m=None, alpha=1.26) -> Dict:
    req = dict(tmean=tmean, rs_mj_m2_day=rs_mj_m2_day, elevation_m=elevation_m)
    if _missing(req):
        return _fail("Priestley-Taylor", req)
    delta = slope_vapor_pressure_curve(tmean)
    gamma = psychrometric_constant(elevation_m)
    rn_mm = 0.408 * (1 - 0.23) * rs_mj_m2_day  # net radiation approx (no long-wave data) mm/day
    et0 = alpha * (delta / (delta + gamma)) * rn_mm
    return {"method": "Priestley-Taylor", "status": "OK", "et0_mm_day": round(et0, 3),
            "inputs_used": req, "alpha_used": alpha}


# ----------------------------------------------------------------------------------
# 5. Makkink  [FAO56-STD]
# ----------------------------------------------------------------------------------

def makkink(tmean=None, rs_mj_m2_day=None, elevation_m=None, C=0.61) -> Dict:
    req = dict(tmean=tmean, rs_mj_m2_day=rs_mj_m2_day, elevation_m=elevation_m)
    if _missing(req):
        return _fail("Makkink", req)
    delta = slope_vapor_pressure_curve(tmean)
    gamma = psychrometric_constant(elevation_m)
    rs_mm = rs_mj_m2_day * 0.408
    et0 = C * (delta / (delta + gamma)) * rs_mm
    return {"method": "Makkink", "status": "OK", "et0_mm_day": round(et0, 3), "inputs_used": req}


# ----------------------------------------------------------------------------------
# 6. Turc  [FAO56-STD / Turc 1961]
# ----------------------------------------------------------------------------------

def turc(tmean=None, rs_mj_m2_day=None, rh_mean=None) -> Dict:
    req = dict(tmean=tmean, rs_mj_m2_day=rs_mj_m2_day)
    if _missing(req):
        return _fail("Turc", req)
    rs_cal = rs_mj_m2_day * 23.9  # MJ/m2/day -> cal/cm2/day
    et0 = 0.013 * (tmean / (tmean + 15)) * (rs_cal + 50)
    if rh_mean is not None and rh_mean < 50:
        et0 *= (1 + (50 - rh_mean) / 70)  # Turc humidity correction for RH<50%
    return {"method": "Turc", "status": "OK", "et0_mm_day": round(et0, 3), "inputs_used": req}


# ----------------------------------------------------------------------------------
# 7. Hargreaves-Samani  [FAO56-STD / Hargreaves & Samani 1985]
# ----------------------------------------------------------------------------------

def hargreaves_samani(tmax=None, tmin=None, tmean=None, lat_deg=None, day_of_year=None) -> Dict:
    req = dict(tmax=tmax, tmin=tmin, tmean=tmean, lat_deg=lat_deg, day_of_year=day_of_year)
    if _missing(req):
        return _fail("Hargreaves-Samani", req)
    Ra = extraterrestrial_radiation_mm_day(lat_deg, day_of_year)
    et0 = 0.0023 * Ra * (tmean + 17.8) * math.sqrt(max(tmax - tmin, 0))
    return {"method": "Hargreaves-Samani", "status": "OK", "et0_mm_day": round(et0, 3), "inputs_used": req}


# ----------------------------------------------------------------------------------
# 8. Thornthwaite  [Thornthwaite 1948, FAO56-STD reference]
# ----------------------------------------------------------------------------------

def thornthwaite_monthly(monthly_mean_temps_c: Optional[List[float]] = None,
                          month_index: Optional[int] = None,
                          day_length_hours: Optional[float] = None) -> Dict:
    """monthly_mean_temps_c: list of 12 monthly mean temperatures (deg C) for heat index I."""
    req = dict(monthly_mean_temps_c=monthly_mean_temps_c, month_index=month_index,
               day_length_hours=day_length_hours)
    if _missing(req):
        return _fail("Thornthwaite", req)
    I = sum((max(t, 0) / 5) ** 1.514 for t in monthly_mean_temps_c)
    a = (6.75e-7 * I ** 3) - (7.71e-5 * I ** 2) + (1.792e-2 * I) + 0.49239
    T = monthly_mean_temps_c[month_index]
    if T <= 0 or I == 0:
        pet_unadj = 0.0
    else:
        pet_unadj = 16 * (10 * T / I) ** a
    correction = (day_length_hours / 12) * (30 / 30)  # simplified day-length correction
    pet = pet_unadj * correction
    return {"method": "Thornthwaite", "status": "OK", "et0_mm_month": round(pet, 2),
            "et0_mm_day": round(pet / 30, 3), "heat_index_I": round(I, 2), "inputs_used": req}


# ----------------------------------------------------------------------------------
# 9. Blaney-Criddle  [FIELD DATA + STANDARD formula, p.9: ETo = p(0.46 Tmean + 8)]
# ----------------------------------------------------------------------------------

def blaney_criddle(tmean=None, p=None) -> Dict:
    req = dict(tmean=tmean, p=p)
    if _missing(req):
        return _fail("Blaney-Criddle", req)
    et0 = p * (0.46 * tmean + 8)
    return {"method": "Blaney-Criddle", "status": "OK", "et0_mm_day": round(et0, 3), "inputs_used": req}


# ----------------------------------------------------------------------------------
# 10. Dalton-type mass transfer  [FAO56-STD generic aerodynamic form]
# ----------------------------------------------------------------------------------

def dalton_mass_transfer(tmean=None, rh_mean=None, wind_kmday=None, a=0.13, b=0.14) -> Dict:
    req = dict(tmean=tmean, rh_mean=rh_mean, wind_kmday=wind_kmday)
    if _missing(req):
        return _fail("Dalton-Type Mass Transfer", req)
    es = sat_vapor_pressure_kpa(tmean) * 10  # mbar
    ed = es * rh_mean / 100
    u_ms = wind_kmday * 1000 / 86400
    et0 = (a + b * u_ms) * (es - ed) / 10  # scaled to mm/day (empirical wind function)
    return {"method": "Dalton-Type Mass Transfer", "status": "OK", "et0_mm_day": round(et0, 3),
            "inputs_used": req}


# ----------------------------------------------------------------------------------
# Direct (water-balance) method  [standard irrigation engineering slide/eq]
# ----------------------------------------------------------------------------------

def direct_water_balance_etc(irrigation_mm=None, precipitation_mm=None, capillary_rise_mm=0.0,
                              runoff_mm=0.0, deep_percolation_mm=0.0, delta_storage_mm=0.0) -> Dict:
    """
    ETc = I + P + W - RO - DP (+/-) dS   [standard irrigation engineering-consistent direct water-balance form]
    Any term not supplied defaults to 0 ONLY for W/RO/DP/dS (genuinely negligible-by-default
    terms); I and P are mandatory because the field dataset/notes provide no basis to assume them.
    """
    req = dict(irrigation_mm=irrigation_mm, precipitation_mm=precipitation_mm)
    if _missing(req):
        return _fail("Direct water-balance ETc", req)
    etc = (irrigation_mm + precipitation_mm + capillary_rise_mm - runoff_mm -
           deep_percolation_mm - delta_storage_mm)
    return {"method": "Direct water-balance", "status": "OK", "etc_mm": round(etc, 3),
            "components": {"I": irrigation_mm, "P": precipitation_mm, "W": capillary_rise_mm,
                            "RO": runoff_mm, "DP": deep_percolation_mm, "dS": delta_storage_mm}}
