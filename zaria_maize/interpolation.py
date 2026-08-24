"""
interpolation.py
-----------------
(Point 25 of the request) Fills gaps in a daily ET time series by interpolation and
derives a simple, transparently-defined "ET Index" for quick visual/tabular screening.

No fabricated ET values are produced for days that ARE reported in the field dataset — this
module only fills genuinely missing calendar days between the first and last available
date, and every interpolated point is flagged `is_interpolated=True` in the output so it
can never be mistaken for an observed/field dataset value.
"""
from typing import List, Dict
import pandas as pd
import numpy as np


def interpolate_et_series(days: List[int], values: List[float], method: str = "linear") -> pd.DataFrame:
    """
    days: e.g. [1,2,3,5,6,...] (day 4 missing)
    values: corresponding ET values (NaN or None where missing)
    Returns a DataFrame with columns [day, value, is_interpolated].
    """
    full_days = list(range(min(days), max(days) + 1))
    s = pd.Series(index=full_days, dtype=float)
    for d, v in zip(days, values):
        s.loc[d] = v
    was_missing = s.isna()
    s_interp = s.interpolate(method=method, limit_direction="both")
    df = pd.DataFrame({"day": full_days, "value": s_interp.values,
                        "is_interpolated": was_missing.values})
    return df


def compute_et_index(etc_series: pd.Series) -> pd.DataFrame:
    """
    ET Index definition (transparent, simple, documented — not a literature-standard index):
        ET_Index(day) = ETc(day) / mean(ETc over season)
    Values > 1 indicate above-average crop water demand for that day relative to the
    season; values < 1 indicate below-average demand. This is provided purely as a
    diagnostic/screening aid requested for the pipeline, not a published agronomic index.
    """
    mean_etc = etc_series.mean()
    idx = etc_series / mean_etc if mean_etc else etc_series * 0
    return pd.DataFrame({"etc_mm_day": etc_series, "et_index": idx.round(3)})
