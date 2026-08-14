"""ACCEPT-side probe: a fully sound analysis using a different convention from the
reference -- a log-log power-law rating curve on the outcome, back-transformed via
the average marginal effect, with a site-level cluster bootstrap interval and a
survey-round indicator for season.  It shares no modelling choice with the
reference solution except the four adjustments themselves, so it must score 1.0.

A verifier that only rejects wrong answers is half-tested; this is the half that
catches a band tightened until it fits the reference and nothing else."""
import json
import sys

import numpy as np
import pandas as pd


def _ate(d, cols):
    X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in cols])
    y = np.log(d["nitrate_mg_l"].to_numpy(float))
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    b = beta[1]                                  # treat is column 1
    base = X @ beta - X[:, 1] * b
    return float(np.mean(np.exp(base + b) - np.exp(base)))


def analyze(csv_path):
    df = pd.read_csv(csv_path)
    df["treat"] = (df["site_type"] == "restored").astype(float)
    df["logq"] = np.log(df["discharge_cms"])
    dates = pd.to_datetime(df["sample_date"])
    rnd = df.groupby("site_type")[dates.name].rank(method="dense").astype(int)
    for r in sorted(rnd.unique())[1:]:
        df[f"rnd{r}"] = (rnd == r).astype(float)
    hour = df["sample_time"].str.split(":").apply(lambda x: int(x[0]) + int(x[1]) / 60.0)
    df["hsin"] = np.sin(2 * np.pi * hour / 24.0)
    df["hcos"] = np.cos(2 * np.pi * hour / 24.0)
    cols = (["treat", "logq"] + [c for c in df.columns if c.startswith("rnd")]
            + ["hsin", "hcos"])

    point = _ate(df, cols)
    sites = df["site_id"].unique()
    rng = np.random.default_rng(7)
    draws = []
    for _ in range(400):
        picked = rng.choice(sites, size=len(sites), replace=True)
        draws.append(_ate(pd.concat([df[df.site_id == s] for s in picked],
                                    ignore_index=True), cols))
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"mean_difference_mg_l": round(point, 4),
            "ci_lower_mg_l": round(float(lo), 4),
            "ci_upper_mg_l": round(float(hi), 4),
            "significant": bool(lo > 0 or hi < 0)}


if __name__ == "__main__":
    json.dump(analyze(sys.argv[1]), open(sys.argv[2], "w"), indent=2)
