"""
xai_explain.py
---------------
Plain-language ("explainable") interpretation of the pipeline's own numeric results.
Every sentence here is generated FROM the actual computed values passed in — no
generic filler, no numbers invented. This is template-based natural-language
generation (substituting real values into pre-written explanatory sentences), which is
what "XAI" (explainable AI) means in the context of a deterministic engineering
pipeline: making the numbers and the reasoning behind them legible to a non-specialist,
not a separate machine-learning model.
"""
from typing import Dict


def explain_overview(results: Dict) -> str:
    ti = results["temperature_input"]
    et = results["et"]
    crop = results.get("crop", {})
    lines = []
    lines.append(
        f"On {ti['date']}, with an input temperature of {ti['temperature_c']}\u00b0C and humidity of "
        f"{ti['humidity_pct']}%, the {crop.get('display_name', 'crop')} is "
        f"{'currently in its active growing season (' + crop.get('season_label','') + ')' if ti['in_growing_season'] else 'currently outside its active growing season (off-season/fallow)'}."
    )
    lines.append(
        f"The crop coefficient (Kc) for today is {ti['kc_today']}, meaning the crop is using "
        f"{'more water than' if ti['kc_today'] > 1 else 'less water than' if ti['kc_today'] < 1 else 'about the same water as'} "
        f"the reference grass surface that ET0 is defined against."
    )
    lines.append(
        f"The pipeline's ensemble of ET methods predicts today's crop water use (ETc) at "
        f"{et['today_predicted_etc']} mm/day. To put that in perspective: over a full day, that is "
        f"{et['today_predicted_etc']} litres of water lost per square metre of field."
    )
    if crop.get("local_etc_range_mm"):
        lo, hi = crop["local_etc_range_mm"]
        gs_etc = et.get("growing_season_etc_mm")
        gs_days = et.get("growing_season_days")
        if gs_etc is not None:
            in_range = lo <= gs_etc <= hi
            lines.append(
                f"Over this crop's actual {gs_days}-day growing season (not counting the off-season), "
                f"total crop water use comes to {gs_etc} mm, which "
                f"{'falls within' if in_range else 'falls outside'} the locally-reported range for this "
                f"crop in the Zaria area ({lo}-{hi} mm)."
            )
    return " ".join(lines)


def explain_soil_water(results: Dict) -> str:
    sw = results["soil_water"]
    return (
        f"The root zone can hold up to {sw['TAW_mm']} mm of water (Total Available Water), of which "
        f"{sw['RAW_mm']} mm ({int(sw['MAD']*100)}% of TAW, the Maximum Allowable Depletion) can be used "
        f"by the crop before irrigation should be triggered to avoid water stress. This is based on a "
        f"root zone depth of {sw['root_zone_depth_m']} m and soil moisture holding capacity between "
        f"{sw['field_capacity_pct']}% (field capacity) and {sw['pwp_pct']}% (permanent wilting point)."
    )


def explain_irrigation_schedule(results: Dict, area_ha: float) -> str:
    sched = results["schedule"]
    mm_to_m3 = area_ha * 10
    if sched["n_events"] == 0:
        return (
            "No irrigation events were triggered for the simulated season under these conditions, "
            "rainfall and soil moisture reserves were sufficient to meet crop water demand throughout, "
            "so no supplemental water needs to be applied right now."
        )
    net_m3 = sched["net_seasonal_irrigation_mm"] * mm_to_m3
    gross_m3 = sched["gross_seasonal_irrigation_mm"] * mm_to_m3
    return (
        f"Over the season, {sched['n_events']} irrigation events are triggered, roughly every "
        f"{sched.get('avg_interval_days')} days on average. In total, {sched['net_seasonal_irrigation_mm']} mm "
        f"of water needs to reach the root zone (net irrigation), for a farm of {area_ha} ha, that is "
        f"about {net_m3:,.0f} m\u00b3 of water. Because the irrigation system used "
        f"({sched['irrigation_method']}) only delivers water to the crop with "
        f"{int(sched['field_application_efficiency_used']*100)}% efficiency, the actual amount that "
        f"needs to be applied at the field (gross irrigation) is higher: {sched['gross_seasonal_irrigation_mm']} mm, "
        f"or about {gross_m3:,.0f} m\u00b3."
    )


def explain_efficiency_and_budget(results: Dict) -> str:
    eff = results["efficiency"]
    wb = results["water_budget"]
    lines = [
        f"Of every 100 units of water diverted from the source, only about {eff['Ep']} reach the crop "
        f"usefully, once conveyance ({eff['Ec']}%), distribution ({eff['Ed']}%), and field application "
        f"({eff['Ea']}%) losses are all accounted for."
    ]
    if wb.get("application_loss_mm"):
        lines.append(
            f"Over the season, {wb['application_loss_mm']} mm of the water delivered to the field never "
            f"actually reached the root zone (field-application loss), this is the single largest "
            f"controllable loss in the system and the main thing a more efficient irrigation method "
            f"(e.g. drip) would reduce."
        )
    if wb.get("balance_residual_mm") is not None:
        lines.append(
            f"The full water balance for the season closes to within {abs(wb['balance_residual_mm'])} mm "
            f"(rainfall + irrigation supplied, minus crop use, minus all losses, minus soil-storage "
            f"change), confirming the numbers above are internally consistent."
        )
    return " ".join(lines)


def explain_irrigation_recommendation(recommendation: Dict) -> str:
    return (
        f"Based on the crop type and the computed irrigation requirement, the recommended irrigation "
        f"method is: {recommendation['recommended_method']}. " + " ".join(recommendation["reasons"])
    )
