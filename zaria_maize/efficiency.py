"""
efficiency.py
-------------
Irrigation efficiency & water-use efficiency, per standard irrigation engineering definitions:
  Ec = Vd/Vc * 100                    (Conveyance eff., standard irrigation engineering eq.1, p.27)
  Ed = Ec . Et  (or Modi's uniformity form)   (Distribution eff., standard irrigation engineering p.29)
  Ea = Vm/Vs * 100                    (Field application eff., standard irrigation engineering p.31)
  Ep = Ec.Ed.Ea / 1000                (Overall project efficiency, standard irrigation engineering p.34)
  WUE = Yield / ET                    (Crop water-use efficiency WUEc, standard irrigation engineering p.34)
"""
from typing import Optional, Dict


def conveyance_efficiency(vol_delivered: float, vol_diverted: float) -> float:
    """[standard irrigation engineering eq.1]"""
    return round(100 * vol_delivered / vol_diverted, 2) if vol_diverted else None


def distribution_efficiency_from_ec_et(ec_pct: float, et_pct: float) -> float:
    """Ed = Ec . Et  [standard irrigation engineering p.29]"""
    return round((ec_pct / 100) * (et_pct / 100) * 100, 2)


def application_efficiency(vol_stored_root_zone: float, vol_supplied_field: float) -> float:
    """[standard irrigation engineering p.31, eq Ea = Vm/Vs *100]"""
    return round(100 * vol_stored_root_zone / vol_supplied_field, 2) if vol_supplied_field else None


def overall_project_efficiency(ec_pct: float, ed_pct: float, ea_pct: float) -> float:
    """
    Ep = Ec x Ed x Ea, all expressed as fractions, reported as a %.
    standard irrigation engineering (p.34) writes this as 'Ep = Ec.Ed.Ea / 1000' with Ec/Ed/Ea in %, but the
    OCR/table extraction of that page is visibly scrambled (column text interleaved).
    Dividing three percentage values (0-100) by 1000 produces results >100% whenever all
    three efficiencies exceed ~46%, which is physically impossible for a compound
    efficiency. The standard, dimensionally-consistent irrigation-engineering form
    (used here) is Ep(%) = Ec(%) . Ed(%) . Ea(%) / 10,000 -- equivalent to multiplying
    the three efficiencies as fractions. This correction is applied and documented here
    rather than silently reproducing an impossible >100% result.
    """
    return round((ec_pct * ed_pct * ea_pct) / 10000, 2)


def water_use_efficiency(yield_kg_ha: Optional[float], et_mm: float) -> Dict:
    """WUEc = Y / ET  [standard irrigation engineering p.34]. Returns DATA NOT AVAILABLE if yield unknown."""
    if yield_kg_ha is None:
        return {"status": "DATA NOT AVAILABLE IN SUPPLIED MATERIALS",
                "reason": "No maize yield (kg/ha or t/ha) recorded for the Zaria plot in the field dataset."}
    if et_mm <= 0:
        return {"status": "INVALID", "reason": "ET must be > 0"}
    return {"status": "OK", "WUEc_kg_per_mm_per_ha": round(yield_kg_ha / et_mm, 3),
            "definition": "WUEc = Yield / ETc (standard irrigation engineering p.34)"}


def water_loss_accounting(vol_diverted: float, vol_delivered: float, vol_field: float,
                           vol_root_zone: float) -> Dict:
    conveyance_loss = vol_diverted - vol_delivered
    distribution_loss = vol_delivered - vol_field
    application_loss = vol_field - vol_root_zone
    total_loss = conveyance_loss + distribution_loss + application_loss
    pct = lambda x: round(100 * x / vol_diverted, 2) if vol_diverted else None
    return {
        "conveyance_loss": round(conveyance_loss, 2),
        "distribution_loss": round(distribution_loss, 2),
        "application_loss": round(application_loss, 2),
        "total_loss": round(total_loss, 2),
        "conveyance_loss_pct": pct(conveyance_loss),
        "distribution_loss_pct": pct(distribution_loss),
        "application_loss_pct": pct(application_loss),
        "total_loss_pct": pct(total_loss),
        "useful_water": round(vol_root_zone, 2),
        "useful_water_pct": pct(vol_root_zone),
    }
