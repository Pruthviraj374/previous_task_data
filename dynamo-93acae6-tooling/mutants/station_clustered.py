"""REJECT-side: all four covariate adjustments correct, but the standard error is
taken at the station level instead of the site level -- the pseudoreplication
error the task is built around."""
import json
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm


def analyze(csv_path):
    df = pd.read_csv(csv_path)
    df["treat"] = (df["site_type"] == "restored").astype(int)
    df["log_discharge"] = np.log(df["discharge_cms"])
    doy = pd.to_datetime(df["sample_date"]).dt.dayofyear
    df["season_sin"] = np.sin(2 * np.pi * doy / 365.0)
    df["season_cos"] = np.cos(2 * np.pi * doy / 365.0)
    hour = df["sample_time"].str.split(":").apply(lambda x: int(x[0]) + int(x[1]) / 60.0)
    df["diurnal_sin"] = np.sin(2 * np.pi * hour / 24.0)
    df["diurnal_cos"] = np.cos(2 * np.pi * hour / 24.0)
    X = sm.add_constant(df[["treat", "log_discharge", "season_sin", "season_cos",
                            "diurnal_sin", "diurnal_cos"]])
    m = sm.OLS(df["nitrate_mg_l"], X).fit(
        cov_type="cluster", cov_kwds={"groups": df["station_id"]})
    lo, hi = m.conf_int().loc["treat"]
    return {"mean_difference_mg_l": round(float(m.params["treat"]), 4),
            "ci_lower_mg_l": round(float(lo), 4),
            "ci_upper_mg_l": round(float(hi), 4),
            "significant": bool(lo > 0 or hi < 0)}


if __name__ == "__main__":
    json.dump(analyze(sys.argv[1]), open(sys.argv[2], "w"), indent=2)
