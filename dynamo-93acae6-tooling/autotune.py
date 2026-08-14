"""Solve each fixture's geometry for a TARGET confounding strength, instead of
hand-tuning.  R^2(treat ~ block) is monotone in each knob, so a bisection lands
it exactly:

  diurnal R^2  <- the gap between the two contractors' typical visit hours
  logQ    R^2  <- the ratio of the two groups' base discharge
  season  R^2  <- the offset between the two contractors' campaign windows

Each fixture then carries a chosen, stated confounding strength rather than
whatever fell out of the parameter soup.
"""
import sys
from pathlib import Path
from dataclasses import replace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import statsmodels.api as sm
from gen import Params, generate
from evaluate import prep

BLOCKS = {
    "season": ["season_sin", "season_cos"],
    "diurnal": ["diurnal_sin", "diurnal_cos"],
    "logQ": ["log_discharge"],
}


def r2_of(p, block):
    df = prep(generate(p))
    X = sm.add_constant(df[BLOCKS[block]])
    return float(sm.OLS(df["treat"], X).fit().rsquared)


def bisect(p, block, setter, lo, hi, target, iters=18):
    """setter(p, x) -> new Params. R^2 must be increasing in x."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        if r2_of(setter(p, mid), block) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def set_hour_gap(p, gap):
    """Keep the midpoint fixed; `gap` is signed so the sign of the imbalance is preserved."""
    mid = (p.restored_hour_typical + p.reference_hour_typical) / 2
    sgn = 1.0 if p.restored_hour_typical < p.reference_hour_typical else -1.0
    return replace(p, restored_hour_typical=mid - sgn * gap / 2,
                   reference_hour_typical=mid + sgn * gap / 2)


def set_q_ratio(p, ratio):
    """Keep the geometric mean fixed; preserve which arm runs higher."""
    gm = float(np.sqrt(p.discharge_base_c * p.discharge_base_r))
    if p.discharge_base_r >= p.discharge_base_c:
        return replace(p, discharge_base_r=gm * np.sqrt(ratio),
                       discharge_base_c=gm / np.sqrt(ratio))
    return replace(p, discharge_base_c=gm * np.sqrt(ratio),
                   discharge_base_r=gm / np.sqrt(ratio))


def set_season_offset(p, off):
    """Keep the earlier contractor fixed; move the later one further out."""
    if p.res_start_doy >= p.ref_start_doy:
        return replace(p, res_start_doy=int(round(p.ref_start_doy + off)))
    return replace(p, ref_start_doy=int(round(p.res_start_doy + off)))


def tune(p, t_season=0.28, t_diurnal=0.33, t_logq=0.50):
    p = replace(p, **{})
    for _ in range(3):                       # the three knobs interact mildly
        gap = bisect(p, "diurnal", set_hour_gap, 0.2, 9.0, t_diurnal)
        p = set_hour_gap(p, gap)
        ratio = bisect(p, "logQ", set_q_ratio, 1.02, 12.0, t_logq)
        p = set_q_ratio(p, ratio)
        off = bisect(p, "season", set_season_offset, 5, 170, t_season)
        p = set_season_offset(p, off)
    return p


if __name__ == "__main__":
    import fixtures
    print(f"{'name':>9} {'seasonR2':>9} {'diurnR2':>8} {'logQR2':>7} | "
          f"{'hours':>13} {'Q base':>13} {'starts':>10} {'Qrange':>12} {'campaign':>9}")
    tuned = {}
    for name, spec in fixtures.ALL:
        p = tune(fixtures.build(spec), **fixtures.TARGETS[name])
        tuned[name] = p
        df = prep(generate(p))
        q = df["discharge_cms"]
        doy = pd.to_datetime(df["sample_date"]).dt.dayofyear
        print(f"{name:>9} {r2_of(p,'season'):9.3f} {r2_of(p,'diurnal'):8.3f} "
              f"{r2_of(p,'logQ'):7.3f} | "
              f"{f'{p.restored_hour_typical:.2f}/{p.reference_hour_typical:.2f}':>13} "
              f"{f'{p.discharge_base_r:.2f}/{p.discharge_base_c:.2f}':>13} "
              f"{f'{p.res_start_doy}/{p.ref_start_doy}':>10} "
              f"{f'{q.min():.2f}-{q.max():.1f}':>12} "
              f"{f'{doy.max()-doy.min()}d':>9}")
    import pickle
    pickle.dump(tuned, open("tuned.pkl", "wb"))
    print("\nwrote tuned.pkl")
