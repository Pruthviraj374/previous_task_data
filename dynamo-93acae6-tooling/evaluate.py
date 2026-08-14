"""Given a dataset, enumerate the LEGITIMATE analysis cloud and the MUTANT cloud
and report the separation invariant:

    INV: the axis-aligned band spanned by the legitimate cloud, padded, must
         contain no mutant -- i.e. every analysis that omits a required
         correction must land outside the range of every fully-correct one.

Reported as a margin in mg/L (point axis) and a ratio (half-width axis), so a
future change can be re-checked rather than re-searched.
"""
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------- covariates
def prep(df):
    df = df.copy()
    df["treat"] = (df["site_type"] == "restored").astype(int)
    df["log_discharge"] = np.log(df["discharge_cms"])
    df["inv_discharge"] = 1.0 / df["discharge_cms"]
    df["raw_discharge"] = df["discharge_cms"]
    df["q2"] = df["discharge_cms"] ** 2
    df["log_nitrate"] = np.log(df["nitrate_mg_l"])
    d = pd.to_datetime(df["sample_date"])
    doy = d.dt.dayofyear
    df["doy_c"] = (doy - doy.mean()) / 100.0
    df["doy_c2"] = df["doy_c"] ** 2
    df["season_sin"] = np.sin(2 * np.pi * doy / 365.0)
    df["season_cos"] = np.cos(2 * np.pi * doy / 365.0)
    df["round"] = d.rank(method="dense").astype(int)          # global round index
    df["round_arm"] = df.groupby("site_type")[d.name].rank(method="dense").astype(int)
    hour = df["sample_time"].str.split(":").apply(lambda x: int(x[0]) + int(x[1]) / 60.0)
    df["hour"] = hour
    df["hour_c"] = (hour - hour.mean()) / 5.0
    df["hour_c2"] = df["hour_c"] ** 2
    df["diurnal_sin"] = np.sin(2 * np.pi * hour / 24.0)
    df["diurnal_cos"] = np.cos(2 * np.pi * hour / 24.0)
    qs = hour.quantile([0.25, 0.5, 0.75]).tolist()
    df["hour_bin"] = pd.cut(hour, bins=[-1] + qs + [99], labels=list("abcd"))
    return df


# What is graded is which ADJUSTMENTS are present, plus the one functional-form
# distinction that is measurably separable: a straight line in discharge is
# rejected, any curve is accepted.  A quadratic in discharge is a curve, and a
# linear day-of-year term is the same kind of approximation as the linear hour
# term -- both were measured inseparable from a correct fit, and both are
# defensible, so both are accepted rather than graded.
Q_OK = {"logQ": ["log_discharge"], "invQ": ["inv_discharge"]}
Q_BAD = {"rawQ": ["raw_discharge"], "noQ": []}
# A quadratic in raw discharge is measured inseparable BOTH ways: as a mutant it
# lands in band on every fixture, and adding it to the accepted set widens the
# bands enough to lose the raw-linear and omitted-season discriminators.  It is
# therefore excluded from both sets and recorded as a known residual gap rather
# than silently accepted or unfairly graded.
Q_RESIDUAL = {"polyQ": ["raw_discharge", "q2"]}
S_OK = {"sincos": ["season_sin", "season_cos"], "roundD": ["C(round_arm)"],
        "poly2": ["doy_c", "doy_c2"], "linS": ["doy_c"]}
S_BAD = {"noS": []}
# A linear hour term IS a legitimate diurnal adjustment: the daily cycle is
# monotone across the sampled 6-19h window, so a straight line removes the
# confound as well as a cyclic encoding does.  A linear day-of-year term is not
# legitimate for season -- the six bi-monthly rounds traverse the whole annual
# cycle, so a straight line is structurally unable to represent it.
D_OK = {"sincos": ["diurnal_sin", "diurnal_cos"], "poly2": ["hour_c", "hour_c2"],
        "binD": ["C(hour_bin)"], "linD": ["hour_c"]}
D_BAD = {"noD": []}


# ---------------------------------------------------------------- estimators
def _design(df, cols):
    rhs = " + ".join(["treat"] + cols) if cols else "treat"
    return patsy.dmatrices(f"nitrate_mg_l ~ {rhs}", df, return_type="dataframe")


def fit_cov(df, cols, est):
    if est.startswith("ols"):
        y, X = _design(df, cols)
        if est == "ols-site-t":
            m = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": df["site_id"]})
            lo, hi = m.conf_int().loc["treat"]
            return float(m.params["treat"]), float((hi - lo) / 2)
        if est == "ols-site-z":
            m = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": df["site_id"]},
                                 use_t=False)
            return float(m.params["treat"]), float(1.96 * m.bse["treat"])
        if est == "ols-station":
            m = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": df["station_id"]})
            lo, hi = m.conf_int().loc["treat"]
            return float(m.params["treat"]), float((hi - lo) / 2)
        if est == "ols-plain":
            m = sm.OLS(y, X).fit()
            lo, hi = m.conf_int().loc["treat"]
            return float(m.params["treat"]), float((hi - lo) / 2)
    rhs = " + ".join(["treat"] + cols) if cols else "treat"
    f = f"nitrate_mg_l ~ {rhs}"
    if est == "mixedlm":
        m = smf.mixedlm(f, df, groups=df["site_id"]).fit(reml=True)
    elif est == "mixedlm-ml":
        m = smf.mixedlm(f, df, groups=df["site_id"]).fit(reml=False)
    elif est == "gee":
        m = smf.gee(f, groups="site_id", data=df,
                    cov_struct=sm.cov_struct.Exchangeable()).fit()
    elif est == "mixedlm3":
        m = smf.mixedlm(f, df, groups=df["site_id"], re_formula="1",
                        vc_formula={"station": "0 + C(station_id)"}).fit(reml=True)
    else:
        raise ValueError(est)
    return float(m.params["treat"]), float(1.96 * m.bse["treat"])


def logy_ate(d, cols, smear):
    rhs = " + ".join(["treat"] + cols) if cols else "treat"
    y, X = patsy.dmatrices(f"log_nitrate ~ {rhs}", d, return_type="dataframe")
    Xa, ya = np.asarray(X, float), np.asarray(y, float).ravel()
    beta = np.linalg.lstsq(Xa, ya, rcond=None)[0]
    ti = list(X.columns).index("treat")
    b = beta[ti]
    base = Xa @ beta - Xa[:, ti] * b
    if smear:
        s = np.exp(0.5 * float(np.var(ya - Xa @ beta, ddof=Xa.shape[1])))
        return float(np.mean(np.exp(base + b) * s - np.exp(base) * s))
    return float(np.mean(np.exp(base + b) - np.exp(base)))


def logy_fit(d, cols, smear, seed=20260814, B=400):
    sites = d["site_id"].unique()
    point = logy_ate(d, cols, smear)
    rng = np.random.default_rng(seed)
    boot = [logy_ate(pd.concat([d[d.site_id == x] for x in
                                rng.choice(sites, size=len(sites), replace=True)],
                               ignore_index=True), cols, smear) for _ in range(B)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float((hi - lo) / 2)


FAST_EST = ["ols-site-t", "ols-site-z", "mixedlm", "gee"]
FULL_EST = ["ols-site-t", "ols-site-z", "mixedlm", "mixedlm-ml", "gee", "mixedlm3"]
BAD_EST = ["ols-station", "ols-plain"]


def clouds(df, fast=True, boot_B=400, invq_all_estimators=False):
    """Return (legit, mutants) as lists of dicts."""
    est_list = FAST_EST if fast else FULL_EST
    s_ok = ["sincos", "poly2"] if fast else list(S_OK)
    d_ok = ["sincos", "linD"] if fast else list(D_OK)

    legit, mut = [], []

    def add(store, label, e, h):
        store.append({"label": label, "est": e, "hw": h})

    # ---- legit: raw-scale covariate families
    for qn in Q_OK:
        ests = est_list if (qn == "logQ" or invq_all_estimators) else ["ols-site-t", "ols-site-z"]
        for sn in s_ok:
            for dn in d_ok:
                cols = Q_OK[qn] + S_OK[sn] + D_OK[dn]
                for e in ests:
                    try:
                        add(legit, f"{qn}|{sn}|{dn}|{e}", *fit_cov(df, cols, e))
                    except Exception:
                        pass
    # ---- legit: log-outcome power law
    for sn in s_ok:
        for dn in d_ok:
            cols = Q_OK["logQ"] + S_OK[sn] + D_OK[dn]
            for smear in (False, True):
                add(legit, f"logY{'S' if smear else ''}|{sn}|{dn}|boot",
                    *logy_fit(df, cols, smear, B=boot_B))

    # ---- mutants: any wrong discharge form / missing season / missing diurnal /
    #      clustering below site level, crossed with legit choices elsewhere
    for qn, qc in {**Q_OK, **Q_BAD}.items():
        for sn, sc in {**{k: S_OK[k] for k in s_ok}, **S_BAD}.items():
            for dn, dc in {**{k: D_OK[k] for k in d_ok}, **D_BAD}.items():
                for e in est_list + BAD_EST:
                    bad = (qn in Q_BAD) or (sn in S_BAD) or (dn in D_BAD) or (e in BAD_EST)
                    if not bad:
                        continue
                    if qn == "invQ" and not invq_all_estimators and e not in (
                            "ols-site-t", "ols-site-z", "ols-station", "ols-plain"):
                        continue
                    try:
                        add(mut, f"{qn}|{sn}|{dn}|{e}", *fit_cov(df, qc + sc + dc, e))
                    except Exception:
                        pass
    return legit, mut


def invariant(legit, mut, pad=0.0, hw_lo_mult=1.0, hw_hi_mult=1.0, verbose=True):
    le = np.array([r["est"] for r in legit]); lh = np.array([r["hw"] for r in legit])
    plo, phi = le.min() - pad, le.max() + pad
    hlo, hhi = hw_lo_mult * lh.min(), hw_hi_mult * lh.max()
    inside = [r for r in mut
              if plo <= r["est"] <= phi and hlo <= r["hw"] <= hhi]

    # per-family margin: how far outside the band is the *closest* mutant?
    fam = defaultdict(lambda: 1e9)
    for r in mut:
        qn, sn, dn, e = r["label"].split("|")
        keys = []
        if qn in Q_BAD: keys.append(f"discharge={qn}")
        if sn in S_BAD: keys.append(f"season={sn}")
        if dn in D_BAD: keys.append(f"diurnal={dn}")
        if e in BAD_EST: keys.append(f"cluster={e}")
        dp = 0.0 if plo <= r["est"] <= phi else min(abs(r["est"] - plo), abs(r["est"] - phi))
        dh = 0.0 if hlo <= r["hw"] <= hhi else min(abs(r["hw"] - hlo), abs(r["hw"] - hhi))
        m = max(dp, dh)
        for k in keys:
            fam[k] = min(fam[k], m)
    if verbose:
        print(f"  LEGIT n={len(legit)} est [{le.min():+.4f},{le.max():+.4f}] "
              f"span {le.max()-le.min():.4f}  hw [{lh.min():.4f},{lh.max():.4f}] "
              f"ratio {lh.max()/lh.min():.3f}")
        print(f"  band point [{plo:+.4f},{phi:+.4f}]  hw [{hlo:.4f},{hhi:.4f}]")
        print(f"  MUT n={len(mut)}   INSIDE (false accepts) = {len(inside)}")
        for k in sorted(fam):
            print(f"    min margin, {k:22s} = {fam[k]:.4f}")
        for r in sorted(inside, key=lambda x: x["label"])[:25]:
            print(f"      IN: {r['label']:40s} est={r['est']:+.4f} hw={r['hw']:.4f}")
    return len(inside), dict(fam)
