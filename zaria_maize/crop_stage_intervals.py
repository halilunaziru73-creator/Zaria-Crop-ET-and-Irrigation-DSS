"""
crop_stage_intervals.py
-------------------------
Stage-specific irrigation intervals per crop [FIELD-REPORTED reference table supplied
directly for this pipeline], replacing the earlier single-interval-for-the-whole-season
approach. Real irrigation practice genuinely varies interval by growth stage -- a
germinating seedling needs frequent light watering, a mid-season flowering/fruiting
crop needs the tightest interval of the whole season (its critical water-sensitivity
window), and a maturing crop can usually go longer between waterings.

Soil-type variation in the source table (sandy vs light loam/clay) is intentionally
NOT used here, per instruction -- the loam/clay column is used throughout, consistent
with this pipeline's own soil assumptions (config.py's field-capacity/PWP values
already represent a loam soil).

The source table gives explicit values only for the Vegetative and Flowering/Fruiting
stages. The Initial (nursery/germination) and Late-season (maturity) stages are not
covered by the table, so a disclosed, standard convention is used for those two:
  - Initial: half the Vegetative-stage interval (rounded up, floor 2 days) -- reflecting
    the well-established practice of frequent light watering during establishment.
  - Late-season: equal to the Vegetative-stage interval -- water demand tapers as the
    crop matures, intermediate between the flowering peak and vegetative growth.
"""

# [FIELD-REPORTED] loam/clay column, days between irrigations
_TABLE = {
    "maize": {"vegetative": 5, "flowering": 4,
              "critical_window": "Tasseling & Silking (Day 45-65). Moisture stress here stops grain formation."},
    "cowpea": {"vegetative": 7, "flowering": 5,
               "critical_window": "Flowering & Pod Setting. Avoid overwatering early on to prevent root rot."},
    "sorghum": {"vegetative": 9, "flowering": 6,
                "critical_window": "Booting to Grain Filling. Highly drought-tolerant, but needs water for good head size."},
    "rice": {"vegetative": 4, "flowering": 3,
             "critical_window": "Panicle Initiation to Flowering. Low humidity puts rice at extreme risk of empty grains."},
    "pepper": {"vegetative": 4, "flowering": 3,
               "critical_window": "Flowering & Fruit Set. Shallow roots and dry air cause flower drop if delayed."},
}

# growth_simulation.py's stage names -> this table's stage names
_STAGE_MAP = {"Initial": None, "Development": "vegetative", "Mid-season": "flowering", "Late-season": None}


def get_stage_interval_days(crop_key: str, growth_stage: str) -> int:
    entry = _TABLE.get(crop_key, _TABLE["maize"])
    veg, flow = entry["vegetative"], entry["flowering"]
    mapped = _STAGE_MAP.get(growth_stage)
    if mapped == "vegetative":
        return veg
    if mapped == "flowering":
        return flow
    if growth_stage == "Initial":
        return max(2, -(-veg // 2))  # ceil(veg/2), floor 2 days
    if growth_stage == "Late-season":
        return veg
    return veg


def get_critical_window_note(crop_key: str) -> str:
    return _TABLE.get(crop_key, _TABLE["maize"])["critical_window"]


def get_all_stage_intervals(crop_key: str) -> dict:
    return {stage: get_stage_interval_days(crop_key, stage)
            for stage in ["Initial", "Development", "Mid-season", "Late-season"]}
