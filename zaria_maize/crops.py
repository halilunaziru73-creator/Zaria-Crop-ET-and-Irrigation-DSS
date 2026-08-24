"""
crops.py
--------
Multi-crop registry for the Zaria pipeline.

Each crop's LOCAL seasonal ETc range and growing-season window below is exactly what
was supplied as authoritative local reference data for Zaria (Kaduna State) maize,
rice, sorghum, pepper, and cowpea -- tagged [LOCAL-REPORTED] throughout this file and
used as a calibration target, not a guess.

For crops other than maize, no field-measured daily weather/Kc dataset is available
(only maize has that, in data/zaria_maize_direct_water_balance.csv). Their Kc-stage
SHAPE therefore comes from the standard, published FAO-56 crop-coefficient tables
(Allen et al. 1998, Table 12) -- tagged [FAO56-STD] -- while the overall MAGNITUDE of
each crop's seasonal ETc is calibrated (a single multiplicative scale factor) so that
the pipeline's own physically-computed seasonal total lands on the midpoint of the
supplied local range for that crop's stated dominant growing season. The calibration
factor for every crop is computed transparently in calibrate_all() below and printed,
not hidden.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SeasonWindow:
    label: str
    start_month: int
    start_day: int
    length_days: int


@dataclass
class CropProfile:
    key: str
    display_name: str
    kc_initial: float
    kc_mid: float
    kc_late: float
    stage_lengths_days: Dict[str, int]
    seasons: List[SeasonWindow]
    local_etc_range_mm: Tuple[float, float]
    context: str
    calibration_factor: float = 1.0


CROPS: Dict[str, CropProfile] = {
    "maize": CropProfile(
        key="maize", display_name="Maize (Corn)",
        kc_initial=0.30, kc_mid=1.20, kc_late=0.60,
        stage_lengths_days={"Initial": 23, "Development": 40, "Mid-season": 45, "Late-season": 26},
        seasons=[
            SeasonWindow("Rain-fed", 5, 1, 122),
            SeasonWindow("Irrigated (dry season)", 1, 1, 120),
        ],
        local_etc_range_mm=(420, 550),
        context=("Rain-fed setups average ~450 mm locally; irrigated dry-season maize "
                 "(high atmospheric demand) pushes past 550 mm."),
    ),
    "rice": CropProfile(
        key="rice", display_name="Rice (Paddy)",
        kc_initial=1.05, kc_mid=1.20, kc_late=0.90,
        stage_lengths_days={"Initial": 30, "Development": 30, "Mid-season": 60, "Late-season": 30},
        seasons=[
            SeasonWindow("Rain-fed lowland", 6, 1, 153),
            SeasonWindow("Dry season (irrigated)", 1, 1, 151),
        ],
        local_etc_range_mm=(550, 750),
        context=("Favoured in nearby fadama/irrigated plains; high percolation and open "
                 "water-surface evaporation typical of Northern Nigeria push actual "
                 "field water requirements high."),
    ),
    "sorghum": CropProfile(
        key="sorghum", display_name="Sorghum (Dawa)",
        kc_initial=0.30, kc_mid=1.05, kc_late=0.55,
        stage_lengths_days={"Initial": 20, "Development": 35, "Mid-season": 40, "Late-season": 30},
        seasons=[
            SeasonWindow("Rain-fed", 5, 15, 165),
        ],
        local_etc_range_mm=(400, 500),
        context=("Well adapted to the Kaduna savanna: a long vegetative phase but strong "
                 "stomatal control keeps total water consumption relatively low despite "
                 "spanning into the early dry season."),
    ),
    "pepper": CropProfile(
        key="pepper", display_name="Pepper (Rodo/Tatashe)",
        kc_initial=0.35, kc_mid=1.05, kc_late=0.90,
        stage_lengths_days={"Initial": 30, "Development": 35, "Mid-season": 40, "Late-season": 20},
        seasons=[
            SeasonWindow("Dry season (irrigated)", 11, 1, 150),
        ],
        local_etc_range_mm=(500, 700),
        context=("A high-value dry-season irrigation crop, grown through the hottest "
                 "months (March/April peak atmospheric demand); daily ETc often exceeds "
                 "6.0 mm/day at mid-stage."),
    ),
    "cowpea": CropProfile(
        key="cowpea", display_name="Beans (Cowpea)",
        kc_initial=0.40, kc_mid=1.05, kc_late=0.60,
        stage_lengths_days={"Initial": 15, "Development": 20, "Mid-season": 20, "Late-season": 15},
        seasons=[
            SeasonWindow("Late rain-fed", 8, 1, 92),
        ],
        local_etc_range_mm=(280, 380),
        context=("Usually planted late in the Zaria rainy season to mature on residual "
                 "soil moisture; short timeline and drought-hardy canopy give the lowest "
                 "seasonal ETc of the group."),
    ),
}

CROP_LABELS = {k: v.display_name for k, v in CROPS.items()}

# [FIELD-REPORTED] authoritative typical daily crop ET range (mm/day) at peak demand,
# supplied directly for this pipeline -- the primary calibration target (replaces the
# earlier seasonal-total-only calibration, which under-differentiated crops: rice and
# maize previously shared the same mid-season Kc, so rice -- which should show the
# HIGHEST daily ET of all five due to standing-water evaporation -- was calibrating
# lower than maize, contradicting the known crop physiology).
PEAK_DAILY_ETC_RANGE_MM = {
    "maize": (4.0, 8.0),
    "rice": (6.0, 10.0),
    "pepper": (3.5, 6.5),
    "sorghum": (3.5, 6.0),
    "cowpea": (2.5, 5.0),
}


# ---------------------------------------------------------------------------------
# Kc curve (FAO-56 linear interpolation between stage midpoints) and calibration
# ---------------------------------------------------------------------------------

def kc_at_dap(profile: CropProfile, dap: int, season_length_days: int = None) -> float:
    """FAO-56-style Kc with linear interpolation across Initial -> Development ->
    Mid-season -> Late-season, using this crop's own stage lengths, PROPORTIONALLY
    RESCALED to fill the actual local season length when one is supplied (so the curve
    always spans the true local growing-season duration rather than the generic FAO-56
    total, which can be shorter or longer than the locally-reported window)."""
    lengths = profile.stage_lengths_days
    stage_kc = {"Initial": profile.kc_initial, "Development": profile.kc_mid,
                "Mid-season": profile.kc_mid, "Late-season": profile.kc_late}
    stages = list(lengths.keys())
    raw_total = sum(lengths.values())
    scale = (season_length_days / raw_total) if (season_length_days and raw_total) else 1.0
    cum = 0
    midpoints = []
    for s in stages:
        length = lengths[s] * scale
        midpoints.append(cum + length / 2)
        cum += length
    kcs = [stage_kc[s] for s in stages]
    if dap <= midpoints[0]:
        return kcs[0]
    if dap >= midpoints[-1]:
        return kcs[-1]
    for i in range(len(midpoints) - 1):
        if midpoints[i] <= dap <= midpoints[i + 1]:
            frac = (dap - midpoints[i]) / (midpoints[i + 1] - midpoints[i])
            return kcs[i] + frac * (kcs[i + 1] - kcs[i])
    return kcs[-1]


def season_total_days(profile: CropProfile) -> int:
    return sum(profile.stage_lengths_days.values())


def doy_for_season_day(season: SeasonWindow, day_index: int) -> int:
    """day_index: 0-based day within the season -> calendar day-of-year (1-366, wraps)."""
    import datetime
    start = datetime.date(2021, season.start_month, season.start_day).timetuple().tm_yday
    return ((start - 1 + day_index) % 365) + 1


def calibrate_crop(profile: CropProfile, doy_climatology: Dict[str, dict],
                    lat_deg: float, season_index: int = 0) -> float:
    """
    Computes this crop's physically-modeled DAILY ETc across its stated dominant local
    season (Hargreaves-Samani ET0, using the site's own trained day-of-year Tmax/Tmin
    climatology, x this crop's FAO-56 Kc curve, rescaled to the ACTUAL local season
    length), finds the PEAK daily value, and returns the multiplicative factor that
    scales that peak onto the midpoint of the supplied [FIELD-REPORTED] daily ET range
    for this crop (PEAK_DAILY_ETC_RANGE_MM) -- this is the primary, most granular
    calibration target, since it's what the GUI/report show day to day. The seasonal
    TOTAL (local_etc_range_mm) is checked as a secondary reference in the calling code,
    not used to override this.
    """
    from . import equations as eq
    season = profile.seasons[season_index]
    n_days = season.length_days
    daily_etc = []
    for d in range(n_days):
        doy = doy_for_season_day(season, d)
        clim = doy_climatology.get(str(doy)) or doy_climatology.get(str(min(doy, 365)))
        if clim is None:
            continue
        res = eq.hargreaves_samani(tmax=clim["tmax"], tmin=clim["tmin"],
                                    tmean=(clim["tmax"] + clim["tmin"]) / 2,
                                    lat_deg=lat_deg, day_of_year=doy)
        et0 = res["et0_mm_day"] if res.get("status") == "OK" else 0.0
        kc = kc_at_dap(profile, d, season_length_days=n_days)
        daily_etc.append(et0 * kc)
    if not daily_etc or max(daily_etc) <= 0:
        return 1.0
    peak_etc = max(daily_etc)
    lo, hi = PEAK_DAILY_ETC_RANGE_MM.get(profile.key, (peak_etc, peak_etc))
    target_mid = (lo + hi) / 2
    return round(target_mid / peak_etc, 4)


def crop_status_for_date(profile: CropProfile, as_of) -> dict:
    """
    Determines which of the crop's season windows (if any) contains `as_of`, and the
    corresponding day-after-planting and Kc. If `as_of` falls in neither window (a
    genuine fallow/off-season period for this crop), returns kc_initial as the closest
    standard proxy for sparse/bare-soil conditions and flags in_growing_season=False --
    mirroring exactly how the field-measured maize dataset treats its own off-season.
    """
    import datetime
    doy_today = as_of.timetuple().tm_yday
    for season in profile.seasons:
        start_doy = datetime.date(2021, season.start_month, season.start_day).timetuple().tm_yday
        end_doy = start_doy + season.length_days  # may exceed 365, handled via modulo below
        # normalize doy_today relative to start_doy, allowing wraparound past year-end
        rel = doy_today - start_doy
        if rel < 0:
            rel += 365
        if 0 <= rel < season.length_days:
            kc = kc_at_dap(profile, rel, season_length_days=season.length_days) * profile.calibration_factor
            return {"in_growing_season": True, "season_label": season.label,
                    "days_after_planting": rel, "kc": round(kc, 3), "season_index": profile.seasons.index(season)}
    return {"in_growing_season": False, "season_label": "Off-season/fallow",
            "days_after_planting": None, "kc": round(profile.kc_initial * profile.calibration_factor, 3),
            "season_index": 0}




def calibrate_all(doy_climatology: Dict[str, dict], lat_deg: float) -> Dict[str, float]:
    """Calibrates every crop in the registry and stores the factor on each profile."""
    factors = {}
    for key, profile in CROPS.items():
        factor = calibrate_crop(profile, doy_climatology, lat_deg)
        profile.calibration_factor = factor
        factors[key] = factor
    return factors
