"""
monitoring.py
--------------
Crop-specific monitoring checklist for maximum productivity — what a farmer should
routinely check, tailored to the crop and to what THIS run's own results actually flag
(e.g. if the water-use efficiency is low, water management is called out first).
"""

GENERIC_CHECKS = [
    ("Soil moisture", "Check root-zone moisture (by feel/probe at 10-20 cm) 2-3 times per week, "
                       "especially in the days leading up to a scheduled irrigation event."),
    ("Weather", "Track daily temperature, humidity and rainfall, re-run this tool whenever "
                "conditions change materially, since irrigation need shifts with them."),
    ("Irrigation system", "Inspect the delivery network (mains/submains/laterals or furrows) for "
                           "leaks, blockages or uneven flow at least weekly during the active season."),
    ("Canopy vigour", "Watch leaf colour and turgor for early wilting/yellowing, often the first "
                       "visible sign of water or nutrient stress, well before yield-affecting damage."),
    ("Pests & disease", "Scout the field weekly, more often during humid/rainy periods, for common "
                         "regional pests and fungal pressure that intensify under irrigation."),
    ("Drainage", "Confirm excess water is draining away after heavy rain or irrigation, "
                 "waterlogging suppresses root respiration and yield just as much as drought does."),
]

CROP_SPECIFIC_CHECKS = {
    "maize": [("Tasseling/silking window", "This is maize's single most water-sensitive period "
               "(Table 2, standard sensitivity references), never let depletion approach RAW here."),
              ("Stand establishment", "Confirm uniform germination within 7-10 days of planting; "
               "gaps compound yield loss disproportionately for maize.")],
    "rice": [("Standing water depth", "Maintain the flood layer specified for basin/flood systems, "
              "rice tolerates very little drying, especially at panicle initiation and flowering."),
             ("Water quality", "Check for salinity/alkalinity build-up in standing water, which "
              "concentrates over a flooded season.")],
    "sorghum": [("Panicle exsertion", "Monitor for water stress right at flowering/grain-fill, "
                 "sorghum tolerates drought elsewhere in the season far better."),
                ("Bird/pest pressure", "Grain heads are vulnerable near maturity; scout as heads fill.")],
    "pepper": [("Flower/fruit drop", "Sudden dry spells during flowering cause fruit abortion, "
                "keep the drip system running reliably through this stage."),
               ("Fruit maturity staggering", "Harvest continuously as fruit ripens rather than once, "
                "typical for peppers, to sustain productivity across the season.")],
    "cowpea": [("Pod-filling moisture", "Cowpea's late rain-fed cycle means the final pod-fill weeks "
                "often coincide with the rains ending, watch for an unexpected late dry spell."),
               ("Nodulation/nitrogen status", "Check root nodulation early season; poor nodulation "
                "undermines the crop's usual low-input-nitrogen advantage.")],
}


def build_monitoring_checklist(crop_key: str, wue_status: str = None,
                                overall_efficiency_pct: float = None) -> list:
    checklist = list(GENERIC_CHECKS)
    checklist = CROP_SPECIFIC_CHECKS.get(crop_key, []) + checklist
    if overall_efficiency_pct is not None and overall_efficiency_pct < 35:
        checklist.insert(0, ("Irrigation system efficiency (priority)",
                              f"This farm's overall system efficiency is {overall_efficiency_pct}%, "
                              f"below a typical well-maintained target (~40-50%+), prioritise fixing "
                              f"conveyance/application losses before anything else, since it is the "
                              f"largest lever on actual water reaching the crop."))
    return checklist


# recommended monitoring frequency per check topic (times per week), used to build the chart
_FREQUENCY_PER_WEEK = {
    "Irrigation system efficiency (priority)": 7, "Soil moisture": 3, "Weather": 7,
    "Irrigation system": 1, "Canopy vigour": 3, "Pests & disease": 1, "Drainage": 2,
    "Tasseling/silking window": 7, "Stand establishment": 7, "Standing water depth": 7,
    "Water quality": 1, "Panicle exsertion": 3, "Bird/pest pressure": 2,
    "Flower/fruit drop": 3, "Fruit maturity staggering": 3, "Pod-filling moisture": 3,
    "Nodulation/nitrogen status": 1,
}


def plot_monitoring_chart(crop_key: str, crop_display_name: str, farm_name: str,
                           overall_efficiency_pct: float = None,
                           fname: str = "monitoring_chart.png") -> str:
    """Turns the monitoring checklist into a horizontal bar chart of recommended
    check frequency (times/week) per topic, colour-coded by category, so it reads at
    a glance rather than as a wall of text."""
    import os
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    checklist = build_monitoring_checklist(crop_key, overall_efficiency_pct=overall_efficiency_pct)
    topics = [t for t, _ in checklist]
    freqs = [_FREQUENCY_PER_WEEK.get(t, 1) for t in topics]
    is_priority = [t.endswith("(priority)") for t in topics]
    is_crop_specific = [t in dict(CROP_SPECIFIC_CHECKS.get(crop_key, [])) for t in topics]

    colors = []
    for p, cs in zip(is_priority, is_crop_specific):
        if p:
            colors.append("#c94c4c")
        elif cs:
            colors.append("#8a4b00")
        else:
            colors.append("#2b7a78")

    fig, ax = plt.subplots(figsize=(8, max(3.5, 0.42 * len(topics))))
    y_pos = range(len(topics))
    ax.barh(list(y_pos)[::-1], freqs, color=colors, edgecolor="black", height=0.62)
    ax.set_yticks(list(y_pos)[::-1])
    ax.set_yticklabels(topics, fontsize=8.5)
    ax.set_xlabel("Recommended checks per week")
    ax.set_xlim(0, 8)
    ax.set_title(f"What to Monitor for Maximum Productivity: {crop_display_name} ({farm_name})",
                 fontsize=10.5, fontweight="bold")
    for i, f in enumerate(freqs):
        ax.text(f + 0.15, list(y_pos)[::-1][i], str(f), va="center", fontsize=8)

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color="#c94c4c", label="Priority (flagged by this run's results)"),
        plt.Rectangle((0, 0), 1, 1, color="#8a4b00", label=f"{crop_display_name}-specific"),
        plt.Rectangle((0, 0), 1, 1, color="#2b7a78", label="General good practice"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=7.5, framealpha=0.9)
    ax.grid(axis="x", alpha=0.25)

    OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, fname)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
