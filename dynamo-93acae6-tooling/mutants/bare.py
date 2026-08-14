"""REJECT-side: the maximally degenerate submission -- treatment only, no
covariates, no clustering.  This exact shape scored 1.0 on an earlier revision of
the predecessor design and shipped undetected through several review gates, so it
is worth a real harbor run every time."""
import json
import sys

import pandas as pd
import statsmodels.api as sm


def analyze(csv_path):
    df = pd.read_csv(csv_path)
    df["treat"] = (df["site_type"] == "restored").astype(int)
    X = sm.add_constant(df[["treat"]])
    m = sm.OLS(df["nitrate_mg_l"], X).fit()
    lo, hi = m.conf_int().loc["treat"]
    return {"mean_difference_mg_l": round(float(m.params["treat"]), 4),
            "ci_lower_mg_l": round(float(lo), 4),
            "ci_upper_mg_l": round(float(hi), 4),
            "significant": bool(lo > 0 or hi < 0)}


if __name__ == "__main__":
    json.dump(analyze(sys.argv[1]), open(sys.argv[2], "w"), indent=2)
