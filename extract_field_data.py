"""
extract_field_data.py
-----------------------
One-off script that parses the source field-data workbook and writes verbatim CSV extracts into
/data. Kept in the repo for transparency/reproducibility -- re-run it if the source
.xls changes. No values are altered; only cell positions are read and written out.
"""
import xlrd, csv, os

SRC = "/mnt/user-data/uploads/the source field-data workbook"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def main():
    wb = xlrd.open_workbook(SRC)
    sh = wb.sheet_by_name('Sheet1')

    def dump(rows_range, ncols, header, outname):
        rows = []
        for r in rows_range:
            if sh.cell_value(r, 0) == '':
                continue
            rows.append([sh.cell_value(r, c) for c in range(ncols)])
        with open(os.path.join(DATA_DIR, outname), 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        return len(rows)

    dump(range(23, 86), 16,
         ['jday', 'month', 'date', 'rh_10am', 'rh_4pm', 'tmax', 'tmin', 'tavg',
          'earthtemp_10am', 'earthtemp_4pm', 'sunshine_hr', 'windspd_kmday',
          'winddir_10am', 'winddir_4pm', 'rainfall_mm', 'pan_evap_mmday'],
         'case_study_2012_raw_weather.csv')

    dump(range(125, 187), 8,
         ['day', 'tmin', 'tmax', 'tmean', 'p', 'eto_mmday', 'kc', 'etc_mmday'],
         'case_study_2012_blaney_criddle.csv')

    dump(range(193, 255), 27,
         ['day', 'rh_10am', 'rh_4pm', 'rh_mean', 'tmin', 'tmax', 'tmean', 'ea_mbar',
          'ed_mbar', 'vpd_mbar', 'wind_kmday', 'f_u', 'ra_mmday', 'n_hr', 'N_hr',
          'n_over_N', 'rs_mmday', 'f_T', 'f_ed', 'f_nN', 'rnl_mmday', 'rn_mmday',
          'w_factor', 'c_factor', 'eto_mmday', 'kc', 'etc_mmday'],
         'case_study_2012_modified_penman.csv')

    dump(range(260, 322), 10,
         ['day', 'tmin', 'tmax', 'rh', 'wind_kmday', 'sun_hr', 'rad_MJm2day',
          'eto_mmday', 'kc', 'etc_mmday'],
         'case_study_2012_cropwat.csv')

    dump(range(325, 387), 4,
         ['day', 'etc_blaney', 'etc_penman', 'etc_cropwat'],
         'case_study_2012_method_comparison.csv')

    print("Extraction complete.")


if __name__ == "__main__":
    main()
