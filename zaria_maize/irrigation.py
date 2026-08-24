"""
irrigation.py
-------------
Irrigation scheduling built on top of soil_water.simulate_daily_soil_water_balance.
Net/gross irrigation formulas: [standard irrigation engineering p.15, eq d_gross = 100.d_net/ea]
"""
from typing import List, Dict
from .soil_water import DailyWaterBalanceResult
from .config import IrrigationSystemConfig


def compute_recommended_schedule(crop_key: str, stage_bounds_days: dict, mean_etc_active_season: float,
                                  season_length_days: int, irr_cfg: IrrigationSystemConfig,
                                  canopy_series=None, soil_cfg=None, raw_mm_fallback: float = 91.0) -> Dict:
    """
    A STANDARDIZED, predictable recommended irrigation schedule whose INTERVAL VARIES
    by growth stage, following a [FIELD-REPORTED] reference table of stage-specific
    intervals for this crop (crop_stage_intervals.py) -- not a single constant interval
    for the whole season. A germinating/nursery-stage crop is watered far more often
    than a maturing one; the flowering/fruiting stage (this crop's critical water-
    sensitivity window) gets the tightest interval of all.

    Net depth per application is computed from the SAME growing-root-zone formula used
    elsewhere in this pipeline, evaluated at each event's own days-after-planting via
    canopy_series (indexed by days-after-planting, NOT calendar day-of-year -- using a
    calendar-day-indexed array here was a real bug for any crop whose season doesn't
    start 1 January, since days-after-planting and calendar-day-of-year are different
    things once the season start date shifts).
    """
    from . import crop_stage_intervals as csi

    def _stage_for_day(day):
        for stage, (lo, hi) in stage_bounds_days.items():
            if lo <= day < hi:
                return stage
        return "Late-season"

    def _raw_at_dap(dap):
        if canopy_series is None or soil_cfg is None or dap >= len(canopy_series):
            return raw_mm_fallback
        fc = canopy_series[dap]
        zr = soil_cfg.root_zone_depth_init_m + (soil_cfg.root_zone_depth_m - soil_cfg.root_zone_depth_init_m) * fc
        taw = 1000 * (soil_cfg.field_capacity_pct / 100 - soil_cfg.pwp_pct / 100) * zr
        mad = soil_cfg.mad_initial + (soil_cfg.mad - soil_cfg.mad_initial) * fc
        return mad * taw

    ea = irr_cfg.field_application_efficiency_ea
    events = []
    day = csi.get_stage_interval_days(crop_key, "Initial")
    while day <= season_length_days:
        stage = _stage_for_day(day)
        interval = csi.get_stage_interval_days(crop_key, stage)
        d_net = round(_raw_at_dap(day - 1), 1)
        d_gross = round(d_net / ea, 1) if ea else d_net
        events.append({"day": day, "net_irrigation_mm": d_net, "gross_irrigation_mm": d_gross,
                       "stage": stage, "interval_used_days": interval})
        day += interval

    net_total = round(sum(e["net_irrigation_mm"] for e in events), 1)
    gross_total = round(sum(e["gross_irrigation_mm"] for e in events), 1)
    stage_intervals = csi.get_all_stage_intervals(crop_key)

    return {
        "stage_intervals_days": stage_intervals,
        "critical_window": csi.get_critical_window_note(crop_key),
        "net_depth_per_application_mm": None,  # varies by day now, see per-event depth
        "gross_depth_per_application_mm": None,
        "events": events, "n_events": len(events),
        "net_seasonal_irrigation_mm": net_total, "gross_seasonal_irrigation_mm": gross_total,
        "basis": (f"Stage-specific intervals [FIELD-REPORTED reference table]: "
                  f"Initial={stage_intervals['Initial']}d, Development={stage_intervals['Development']}d, "
                  f"Mid-season={stage_intervals['Mid-season']}d, Late-season={stage_intervals['Late-season']}d. "
                  f"Depth per event uses the day's own root-zone RAW threshold."),
    }


def build_schedule(dwb_results: List[DailyWaterBalanceResult], irr_cfg: IrrigationSystemConfig) -> Dict:
    events = [r for r in dwb_results if r.irrigation_triggered]
    net_total = sum(e.irrigation_mm for e in events)
    gross_total = net_total / irr_cfg.field_application_efficiency_ea if irr_cfg.field_application_efficiency_ea else net_total

    intervals = []
    if len(events) > 1:
        for a, b in zip(events[:-1], events[1:]):
            intervals.append(b.day - a.day)

    return {
        "n_events": len(events),
        "events": [{"day": e.day, "net_irrigation_mm": e.irrigation_mm,
                    "gross_irrigation_mm": round(e.irrigation_mm / irr_cfg.field_application_efficiency_ea, 2)
                    if irr_cfg.field_application_efficiency_ea else e.irrigation_mm}
                   for e in events],
        "net_seasonal_irrigation_mm": round(net_total, 1),
        "gross_seasonal_irrigation_mm": round(gross_total, 1),
        "avg_interval_days": round(sum(intervals) / len(intervals), 1) if intervals else None,
        "next_irrigation_day_after_series": (
            events[-1].day + round(sum(intervals) / len(intervals))
            if events and intervals else (events[-1].day if events else None)),
        "field_application_efficiency_used": irr_cfg.field_application_efficiency_ea,
        "irrigation_method": irr_cfg.method,
    }


def net_irrigation_requirement(etc_mm: float, effective_rainfall_mm: float) -> float:
    """I_net = ETc - Pe  [STANDARD]; never negative."""
    return max(0.0, etc_mm - effective_rainfall_mm)


def gross_irrigation_requirement(net_mm: float, ea: float) -> float:
    """I_gross = I_net / Ea  [standard irrigation engineering p.15]"""
    return net_mm / ea if ea > 0 else net_mm
