"""REJECT-side: the exact submission qc_gate flagged on the predecessor design --
cluster-robust OLS on the inverse-discharge covariate, with the time-of-day term
and site-level clustering, but the seasonal adjustment omitted entirely."""
import json
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm


def analyze(csv_path):
    df = pd.read_csv(csv_path)
    df["treat"] = (df["site_type"] == "restored").astype(int)
    df["inv_discharge"] = 1.0 / df["discharge_cms"]
    hour = df["sample_time"].str.split(":").apply(lambda x: int(x[0]) + int(x[1]) / 60.0)
    df["diurnal_sin"] = np.sin(2 * np.pi * hour / 24.0)
    df["diurnal_cos"] = np.cos(2 * np.pi * hour / 24.0)
    X = sm.add_constant(df[["treat", "inv_discharge", "diurnal_sin", "diurnal_cos"]])
    m = sm.OLS(df["nitrate_mg_l"], X).fit(
        cov_type="cluster", cov_kwds={"groups": df["site_id"]})
    lo, hi = m.conf_int().loc["treat"]
    return {"mean_difference_mg_l": round(float(m.params["treat"]), 4),
            "ci_lower_mg_l": round(float(lo), 4),
            "ci_upper_mg_l": round(float(hi), 4),
            "significant": bool(lo > 0 or hi < 0)}


if __name__ == "__main__":
    json.dump(analyze(sys.argv[1]), open(sys.argv[2], "w"), indent=2)
