"""
irrigation_types.py
--------------------
Computes water required for THIS FARM'S specific area under each of several
irrigation methods, using the pipeline's own computed net irrigation depth (mm) and
each method's standard field-application efficiency. Every result scales directly
with the farm's own entered area (ha) -- nothing here is generic; it is calculated
per farm.

Field application efficiency values: [STANDARD] published irrigation-engineering
ranges (consistent with the values already used elsewhere in this pipeline for the
configured system, e.g. config.py's furrow default).
"""
from typing import Dict, List

IRRIGATION_METHODS = {
    "Furrow": {"ea": 0.57, "note": "Low-cost, widely practised locally; moderate losses to deep percolation."},
    "Basin/Flood": {"ea": 0.60, "note": "Simple, low equipment cost; suited to paddy rice and heavy soils."},
    "Sprinkler": {"ea": 0.75, "note": "Uniform application; reduces deep-percolation loss vs furrow/basin."},
    "Drip": {"ea": 0.88, "note": "Highest efficiency; best for high-value crops or water-scarce conditions."},
}


def water_required_by_method(net_irrigation_mm: float, area_ha: float) -> List[Dict]:
    """Returns, for each irrigation method, the gross depth (mm) and volume (m3 and
    litres) required for THIS FARM's specific area to deliver the same net irrigation
    (net_irrigation_mm) to the root zone."""
    mm_to_m3_per_ha = 10.0  # 1 mm over 1 ha = 10 m3
    rows = []
    for name, cfg in IRRIGATION_METHODS.items():
        ea = cfg["ea"]
        gross_mm = net_irrigation_mm / ea if ea else None
        gross_m3 = gross_mm * area_ha * mm_to_m3_per_ha if gross_mm is not None else None
        rows.append({
            "method": name,
            "application_efficiency_pct": round(ea * 100, 1),
            "gross_depth_mm": round(gross_mm, 2) if gross_mm is not None else None,
            "gross_volume_m3": round(gross_m3, 1) if gross_m3 is not None else None,
            "gross_volume_litres": round(gross_m3 * 1000, 0) if gross_m3 is not None else None,
            "note": cfg["note"],
        })
    rows.sort(key=lambda r: r["gross_volume_m3"] if r["gross_volume_m3"] is not None else 0)
    return rows
