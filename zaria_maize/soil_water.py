"""
soil_water.py
-------------
Soil-water balance calculations per standard irrigation engineering notes:
  TAW = 1000 (theta_FC - theta_PWP) * Zr                [standard irrigation engineering / FAO56-consistent]
  RAW = MAD * TAW                                        [standard irrigation engineering Appendix 1, eq {RAW}]
  d_net = p . W . D  (root-zone available-water depth)   [standard irrigation engineering p.44 eq {9}]
"""
from dataclasses import dataclass
from typing import List, Dict
from .config import SoilConfig


def compute_taw_raw(soil: SoilConfig) -> Dict:
    fc = soil.field_capacity_pct / 100
    pwp = soil.pwp_pct / 100
    taw_mm = 1000 * (fc - pwp) * soil.root_zone_depth_m
    raw_mm = soil.mad * taw_mm
    return {
        "field_capacity_pct": soil.field_capacity_pct,
        "pwp_pct": soil.pwp_pct,
        "root_zone_depth_m": soil.root_zone_depth_m,
        "MAD": soil.mad,
        "TAW_mm": round(taw_mm, 1),
        "RAW_mm": round(raw_mm, 1),
        "soil_texture": soil.soil_texture,
    }


@dataclass
class DailyWaterBalanceResult:
    day: int
    etc_mm: float
    rainfall_mm: float
    eff_rainfall_mm: float
    irrigation_mm: float
    deep_percolation_mm: float
    runoff_mm: float
    depletion_mm: float
    storage_mm: float
    irrigation_triggered: bool


def simulate_daily_soil_water_balance(days: List[int], etc_series: List[float],
                                       rainfall_series: List[float],
                                       taw_series, raw_series,
                                       gross_ea: float) -> List[DailyWaterBalanceResult]:
    """
    Dynamic day-by-day depletion-based scheduler.
    Irrigation is triggered whenever cumulative root-zone depletion reaches RAW
    (standard irrigation engineering definition of readily available water as the safe
    depletion threshold).

    taw_series / raw_series: EITHER a single float (constant all season) OR a per-day
    list the same length as `days` -- the growing-root-depth case. As the crop's roots
    deepen (TAW grows day to day), the newly-accessed soil layer is assumed to start at
    field capacity (a standard, defensible simplification), so that capacity increase is
    added directly to storage rather than appearing as a sudden jump in depletion.

    Effective rainfall (Pe) is defined as the portion of that day's rainfall that
    actually fits in the REMAINING root-zone storage capacity that day:
        Pe = min(rainfall, TAW - storage_before_rain)
    Any rainfall beyond that remaining capacity cannot be "effective" -- it becomes
    deep percolation immediately, the same day, before ETc is even applied.

    Runoff is not separately modelled (no infiltration-rate/rainfall-intensity data is
    available), so it is reported as 0.0 for every day; this is a stated model
    limitation, not a fabricated zero.
    """
    n = len(days)
    taw_arr = list(taw_series) if hasattr(taw_series, "__len__") else [taw_series] * n
    raw_arr = list(raw_series) if hasattr(raw_series, "__len__") else [raw_series] * n

    results = []
    storage = taw_arr[0]  # start at field capacity for the FIRST day's (shallow) root zone
    for i, (day, etc, rain) in enumerate(zip(days, etc_series, rainfall_series)):
        taw_mm = taw_arr[i]
        raw_mm = raw_arr[i]
        if i > 0 and taw_mm > taw_arr[i - 1]:
            # roots have deepened since yesterday -- the newly-accessed layer is
            # assumed to start at field capacity, so add that capacity straight to storage
            storage += taw_mm - taw_arr[i - 1]

        # --- rainfall infiltration, capped by the REMAINING storage capacity today ---
        capacity_room = max(taw_mm - storage, 0.0)
        eff_rain = min(rain, capacity_room)          # only what actually fits is "effective"
        deep_perc = max(0.0, rain - capacity_room)    # excess rainfall percolates immediately
        runoff = 0.0                                  # not modelled -- see docstring
        storage += eff_rain

        # --- crop water use ---
        storage -= etc
        storage = max(storage, 0.0)  # soil moisture cannot go negative
        depletion = taw_mm - storage

        irrigation_mm = 0.0
        triggered = False
        if depletion >= raw_mm:
            net_irrig = depletion  # refill back to field capacity
            irrigation_mm = net_irrig
            storage += net_irrig
            depletion = taw_mm - storage
            triggered = True

        results.append(DailyWaterBalanceResult(
            day=day, etc_mm=round(etc, 3), rainfall_mm=round(rain, 2),
            eff_rainfall_mm=round(eff_rain, 2), irrigation_mm=round(irrigation_mm, 2),
            deep_percolation_mm=round(deep_perc, 2), runoff_mm=round(runoff, 2),
            depletion_mm=round(depletion, 2), storage_mm=round(storage, 2),
            irrigation_triggered=triggered
        ))
    return results
