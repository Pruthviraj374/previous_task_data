"""REJECT-side: everything correct except discharge enters on its raw linear
scale -- the weakest member of that family in local calibration."""
import json
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm


def analyze(csv_path):
    df = pd.read_csv(csv_path)
    df["treat"] = (df["site_type"] == "restored").astype(int)
    dates = pd.to_datetime(df["sample_date"])
    df["round_arm"] = df.groupby("site_type")[dates.name].rank(method="dense").astype(int)
    hour = df["sample_time"].str.split(":").apply(lambda x: int(x[0]) + int(x[1]) / 60.0)
    qs = hour.quantile([0.25, 0.5, 0.75]).tolist()
    df["hour_bin"] = pd.cut(hour, bins=[-1] + qs + [99], labels=list("abcd"))
    X = pd.get_dummies(df[["treat", "discharge_cms", "round_arm", "hour_bin"]],
                       columns=["round_arm", "hour_bin"], drop_first=True, dtype=float)
    X = sm.add_constant(X)
    m = sm.OLS(df["nitrate_mg_l"], X).fit(
        cov_type="cluster", cov_kwds={"groups": df["site_id"]})
    lo, hi = m.conf_int().loc["treat"]
    return {"mean_difference_mg_l": round(float(m.params["treat"]), 4),
            "ci_lower_mg_l": round(float(lo), 4),
            "ci_upper_mg_l": round(float(hi), 4),
            "significant": bool(lo > 0 or hi < 0)}


if __name__ == "__main__":
    json.dump(analyze(sys.argv[1]), open(sys.argv[2], "w"), indent=2)
