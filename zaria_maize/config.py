"""
config.py
---------
Site, crop and soil configuration for the Zaria Maize pipeline.

Every value below is tagged with its provenance:
  [FIELD DATA]   -> taken verbatim from the Samaru field dataset (field-data study)
  [STANDARD]  -> taken from the supplied standard irrigation engineering lecture notes 
  [DEMO]     -> not present in either supplied source; a labelled placeholder used only
               so the pipeline can run end-to-end. MUST be replaced with real field data
               before results are used for actual engineering decisions.
"""
from dataclasses import dataclass, field


@dataclass
class SiteConfig:
    """Samaru, Zaria meteorological station. [FIELD DATA] Sheet1 rows 13-15."""
    town: str = "Samaru"
    state: str = "Zaria, Kaduna State, Nigeria"
    latitude_deg: float = 11.11          # [FIELD DATA]
    elevation_m: float = 686.0           # [FIELD DATA]
    season_start: str = "2012-07-01"     # [FIELD DATA]
    season_end: str = "2012-08-31"       # [FIELD DATA]  (62-day window actually documented)
    crop: str = "Maize"                  # [FIELD DATA]


@dataclass
class SoilConfig:
    """
    Soil-water parameters for TAW/RAW (standard irrigation engineering 'Field Application Efficiency Ea' section).
    The field dataset contains NO measured soil texture, field capacity, permanent wilting point,
    or root-zone depth for the Zaria maize plot. standard irrigation engineering gives generic tables (Table 4 & 5,
    p.15) for irrigation-depth estimation by soil/root class and a generic MAD of 0.65
    (James, 1993). Numeric FC/PWP (%) are NOT tabulated for a specific soil texture in the
    supplied notes, so a demonstration loam value (typical FAO/standard irrigation engineering-consistent range) is
    used and explicitly flagged. Replace with lab-measured values when available.
    """
    field_capacity_pct: float = 28.0     # [DEMO/ASSUMED] volumetric %, loam soil
    pwp_pct: float = 14.0                # [DEMO/ASSUMED] volumetric %, loam soil
    root_zone_depth_m: float = 1.0       # [STANDARD] Table 5: maize = deep-rooting crop (0.9-1.5 m); mid value used
    root_zone_depth_init_m: float = 0.15  # [FAO56-STD] typical initial (germination/nursery) effective root
                                           # depth for cereals -- root depth grows from this toward
                                           # root_zone_depth_m as canopy develops (FAO-56 Ch.8), rather than
                                           # being constant all season. A shallow early root zone holds much
                                           # less readily-available water, so short dry spells during
                                           # establishment can trigger irrigation even in a season with
                                           # adequate seasonal rainfall totals -- this is standard agronomic
                                           # behaviour that a constant-depth model misses.
    mad: float = 0.65                    # [STANDARD] Appendix 1 (James, 1993) "MAD for most crops is about 0.65"
    mad_initial: float = 0.25            # [FAO56-STD, Ch.8] germination/nursery-stage MAD is much lower than the
                                          # mature-crop value: seeds/seedlings cannot tolerate meaningful moisture
                                          # depletion at all -- FAO-56 specifies the surface layer must be kept
                                          # continuously moist during germination, unlike the mature root zone
                                          # where a much larger fraction of TAW can safely be depleted between
                                          # irrigations. Using the mature MAD during Initial stage understated
                                          # establishment-phase irrigation need.
    soil_texture: str = "Loam (assumed)"


@dataclass
class IrrigationSystemConfig:
    """
    Irrigation system / efficiency assumptions.
    standard irrigation engineering Table 4 (Ea, p.32) recommends Furrow: 55-70% (57% ICID).
    standard irrigation engineering Table 1 (Ec, p.27) recommends short earthen loam canal: 85%.
    standard irrigation engineering Table 3 (Ed, p.30): rotational system with sufficient communication: 55%.
    These are standard irrigation engineering recommended defaults (not site-measured) and are flagged accordingly.
    """
    method: str = "Furrow irrigation"          # [DEMO/ASSUMED] — not stated for the maize plot in field dataset
    field_application_efficiency_ea: float = 0.57   # [STANDARD] Table 4, furrow, ICID value
    conveyance_efficiency_ec: float = 0.85          # [STANDARD] Table 1, short canal, loam soil
    distribution_efficiency_ed: float = 0.55        # [STANDARD] Table 3, rotational, sufficient comm.
    max_net_application_depth_mm: float = 70.0      # [STANDARD] p.14 "maximum possible net application depth is 70 mm"


@dataclass
class CropCoefficients:
    """
    Maize crop coefficient (Kc).
    [FIELD DATA]: the source dataset uses a SINGLE constant Kc = 1.2 for the entire
    July-August window (mid-season value) for all three ET methods it computes.
    That is the only Kc value actually present in the supplied materials.

    For a full growth-stage breakdown (initial/development/mid-season/late-season),
    the field dataset and standard irrigation engineering notes do NOT supply stage-specific maize Kc values (standard irrigation engineering
    instead tabulates yield-response factors ky, not Kc, in Table 2, p.40). Stage Kc
    values below are standard FAO-56 maize reference figures, included ONLY as an
    optional supplementary mode and clearly labelled — they are NOT field dataset data.
    """
    reference_constant_kc: float = 1.2  # [FIELD DATA] Sheet1, used throughout Blaney-Criddle/Penman/Cropwat tables

    # [DEMO/EXTERNAL-REFERENCE] FAO-56 style stage Kc for maize — NOT in supplied field dataset/standard irrigation engineering.
    stage_kc_reference: dict = field(default_factory=lambda: {
        "Initial": 0.30,
        "Development": 0.70,
        "Mid-season": 1.20,
        "Late-season": 0.60,
    })
    stage_lengths_days_reference: dict = field(default_factory=lambda: {
        "Initial": 20,
        "Development": 35,
        "Mid-season": 40,
        "Late-season": 30,
    })


DEFAULT_SITE = SiteConfig()
DEFAULT_SOIL = SoilConfig()
DEFAULT_IRRIGATION = IrrigationSystemConfig()
DEFAULT_KC = CropCoefficients()
