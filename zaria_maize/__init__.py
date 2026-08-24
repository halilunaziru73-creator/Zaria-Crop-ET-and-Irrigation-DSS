"""
Zaria Maize Evapotranspiration & Irrigation Water Management Pipeline
=======================================================================

Data provenance (STRICT — see README.md "No Fabrication Rule"):
  1) the Samaru field dataset (the field data compiler, field-data study) -> data/case_study_2012_*.csv
     Samaru (Zaria), Lat 11.11 N, 686 m a.s.l., 1 Jul - 31 Aug 2012, Maize, Kc = 1.2 (field dataset-fixed).
  2) standard irrigation engineering Lecture Notes  -> equations.py docstrings cite table/eq numbers.
  3) Samaru daily weather archive (partial extract from field dataset workbook) -> data/samaru_daily_weather_partial.csv
Every numeric constant used in a calculation is tagged in code as FIELD DATA, STANDARD, or
DEMO/ASSUMED. Nothing is silently invented.
"""
__version__ = "1.0.0"
