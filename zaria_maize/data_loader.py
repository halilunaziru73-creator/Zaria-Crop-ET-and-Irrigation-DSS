"""
data_loader.py
---------------
Loads the real data extracted from the Samaru field dataset (the source field-data workbook).
No values are synfield dataseted here — this module only reads the CSV extracts that were
parsed verbatim from the field dataset workbook (see /data/*.csv, produced by extract_field_data.py).
"""
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_case_study_raw_weather() -> pd.DataFrame:
    """[FIELD DATA] Daily raw Samaru weather, 1 Jul - 31 Aug 2012 (62 days), Sheet1 rows 23-85."""
    df = pd.read_csv(os.path.join(DATA_DIR, "case_study_2012_raw_weather.csv"))
    return df


def load_case_study_blaney_criddle() -> pd.DataFrame:
    """[FIELD DATA] Field Dataset's own Blaney-Criddle ETo/ETc computation, Sheet1 rows 125-186 & Sheet2."""
    return pd.read_csv(os.path.join(DATA_DIR, "case_study_2012_blaney_criddle.csv"))


def load_case_study_modified_penman() -> pd.DataFrame:
    """[FIELD DATA] Field Dataset's own (Modified) Penman full computation chain, Sheet1 rows 193-254."""
    return pd.read_csv(os.path.join(DATA_DIR, "case_study_2012_modified_penman.csv"))


def load_case_study_cropwat() -> pd.DataFrame:
    """[FIELD DATA] Field Dataset's own CROPWAT/FAO-Penman-style ETo/ETc table, Sheet1 rows 260-321."""
    return pd.read_csv(os.path.join(DATA_DIR, "case_study_2012_cropwat.csv"))


def load_case_study_method_comparison() -> pd.DataFrame:
    """[FIELD DATA] Field Dataset's own side-by-side ETc comparison table (Blaney/Penman/Cropwat), rows 325-386."""
    return pd.read_csv(os.path.join(DATA_DIR, "case_study_2012_method_comparison.csv"))


def load_samaru_weather_archive() -> pd.DataFrame:
    """
    [FIELD DATA, PARTIAL] Two single-year blocks of Samaru daily climate extracted from the
    '1994-2008' and '2009-2023' workbook sheets. Each sheet in the source workbook in fact
    contains only ONE populated 365-day year of daily data (not a full multi-decade series
    despite the sheet name) — this is exactly what is present in the file, no rows invented.
    Used only for supplementary long-term ET demonstrations (e.g. Thornthwaite monthly means).
    """
    return pd.read_csv(os.path.join(DATA_DIR, "samaru_daily_weather_partial.csv"))
