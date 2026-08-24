"""
validation.py
-------------
Statistical comparison metrics for ET methods, computed only against the field dataset's own
tabulated results (the field dataset's Blaney-Criddle / Modified-Penman / Cropwat ETc columns) —
these are the only "reference/observed-equivalent" series present in the supplied
materials. No independent field-measured ET exists in the field dataset, so all comparisons
here are METHOD-VS-METHOD, not method-vs-ground-truth, and are labelled as such.
"""
import math
from typing import List, Dict


def _pair(a: List[float], b: List[float]):
    return [(x, y) for x, y in zip(a, b) if x is not None and y is not None
            and not (isinstance(x, float) and math.isnan(x))
            and not (isinstance(y, float) and math.isnan(y))]


def rmse(estimated: List[float], reference: List[float]) -> float:
    p = _pair(estimated, reference)
    if not p:
        return None
    return round(math.sqrt(sum((e - r) ** 2 for e, r in p) / len(p)), 4)


def mae(estimated: List[float], reference: List[float]) -> float:
    p = _pair(estimated, reference)
    if not p:
        return None
    return round(sum(abs(e - r) for e, r in p) / len(p), 4)


def bias(estimated: List[float], reference: List[float]) -> float:
    p = _pair(estimated, reference)
    if not p:
        return None
    return round(sum(e - r for e, r in p) / len(p), 4)


def mape(estimated: List[float], reference: List[float]) -> float:
    p = [(e, r) for e, r in _pair(estimated, reference) if r != 0]
    if not p:
        return None
    return round(100 * sum(abs((e - r) / r) for e, r in p) / len(p), 2)


def r_squared(estimated: List[float], reference: List[float]) -> float:
    p = _pair(estimated, reference)
    if len(p) < 2:
        return None
    xs = [r for _, r in p]
    ys = [e for e, _ in p]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return round((num / den) ** 2, 4) if den else None


def nse(estimated: List[float], reference: List[float]) -> float:
    """Nash-Sutcliffe Efficiency."""
    p = _pair(estimated, reference)
    if len(p) < 2:
        return None
    mean_ref = sum(r for _, r in p) / len(p)
    num = sum((r - e) ** 2 for e, r in p)
    den = sum((r - mean_ref) ** 2 for _, r in p)
    return round(1 - num / den, 4) if den else None


def full_report(estimated: List[float], reference: List[float]) -> Dict:
    return {"RMSE": rmse(estimated, reference), "MAE": mae(estimated, reference),
            "Bias": bias(estimated, reference), "MAPE_pct": mape(estimated, reference),
            "R2": r_squared(estimated, reference), "NSE": nse(estimated, reference)}


def rank_methods(method_reports: Dict[str, Dict]) -> List[str]:
    """Rank by RMSE ascending (lower error = better), ignoring methods with no RMSE."""
    ranked = sorted(
        [(name, rep["RMSE"]) for name, rep in method_reports.items() if rep.get("RMSE") is not None],
        key=lambda kv: kv[1]
    )
    return [name for name, _ in ranked]
