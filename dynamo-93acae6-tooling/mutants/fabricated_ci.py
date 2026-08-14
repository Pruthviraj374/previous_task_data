"""REJECT-side: computes the point estimate correctly (all four adjustments, site
clustering) but fabricates the interval -- same width, shifted so the estimate sits
at its lower edge. This is the attack AVA found on the predecessor design, and it
is what the centring assertion exists to catch. Must score 0."""
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
        cov_type="cluster", cov_kwds={"groups": df["site_id"]})
    est = float(m.params["treat"])
    lo, hi = m.conf_int().loc["treat"]
    width = float(hi - lo)
    # keep the width, put the estimate at the bottom edge
    return {"mean_difference_mg_l": round(est, 4),
            "ci_lower_mg_l": round(est, 4),
            "ci_upper_mg_l": round(est + width, 4),
            "significant": bool(est > 0 or est + width < 0)}


if __name__ == "__main__":
    json.dump(analyze(sys.argv[1]), open(sys.argv[2], "w"), indent=2)
