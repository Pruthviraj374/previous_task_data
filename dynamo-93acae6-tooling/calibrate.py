"""Assert the design's separation invariant against the REAL shipped verifier code.

  INVARIANT
    (fairness) every analysis that applies all four adjustments soundly passes on
               every monitoring program; and
    (soundness) no analysis that omits or mis-specifies a required adjustment
               passes on ALL of them.

Grading is all-or-nothing across the programs, so the second clause is exactly
"no incomplete analysis scores 1.0".  Run this before every push.  It fails loudly
if a data or verifier change breaks either clause, which is the whole point --
the predecessor design re-searched for a safe parameter value after every change
and had no assertion to catch it when the value stopped being safe.
"""
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

REPO = Path(os.environ.get(
    "DYNAMO_TASK_REPO",
    r"C:\Users\chara\Downloads\Handshake\dynamo-93acae6-scientific-computing-and-domain-science"))
TESTS = REPO / "task" / "tests" / "test_outputs.py"
FIXTURES = REPO / "task" / "tests" / "fixtures"
SOLUTION = REPO / "task" / "solution" / "solve.py"


def load_verifier():
    """Load the real test_outputs.py without its collection-time staging (which
    deletes the fixture tree)."""
    src = TESTS.read_text(encoding="utf-8")
    # Neutralise the collection-time staging (it deletes the fixture tree and seals
    # /tests) but keep the WHOLE module, so the real _check_result is available --
    # truncating at this line is what previously left calibration checking only the
    # bands and blind to the centring assertion.
    src = src.replace("CASES = _stage()", "CASES = {}")
    ns = {"__name__": "verifier_under_test"}
    exec(compile(src, str(TESTS), "exec"), ns)
    return ns


V = load_verifier()
prep, fit, band, cloud = V["_prep"], V["_fit"], V["_band"], V["_accepted_cloud"]
DISCHARGE, SEASON, DIURNAL = V["DISCHARGE"], V["SEASON"], V["DIURNAL"]
SITE_ESTIMATORS, OLS_ONLY = V["SITE_ESTIMATORS"], V["OLS_ONLY"]

# analyses that violate a stated requirement
BAD_Q = {"rawQ": ["raw_discharge"], "noQ": []}
BAD_S = {"noSeason": []}
BAD_D = {"noDiurnal": []}
BAD_EST = ["ols-station", "ols-plain"]


def prep_plus(df):
    d = prep(df)
    d["raw_discharge"] = d["discharge_cms"]
    return d


def fit_any(d, cols, est):
    if est in ("ols-station", "ols-plain"):
        import patsy
        import statsmodels.api as sm
        rhs = " + ".join(["treat"] + cols) if cols else "treat"
        y, X = patsy.dmatrices(f"nitrate_mg_l ~ {rhs}", d, return_type="dataframe")
        m = (sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": d["station_id"]})
             if est == "ols-station" else sm.OLS(y, X).fit())
        lo, hi = m.conf_int().loc["treat"]
        return float(m.params["treat"]), float((hi - lo) / 2)
    return fit(d, cols, est)


def inside(b, e, h):
    return (b["point_lo"] <= e <= b["point_hi"]) and (b["hw_lo"] <= h <= b["hw_hi"])


def passes_real_check(b, est, lo, hi):
    """Run the verifier's OWN _check_result, not a reimplementation of its bands.

    The earlier version of this script only compared against the two bands and
    rebuilt intervals as est +/- half_width -- symmetric by construction. That made
    it structurally blind to the centring assertion, which is what actually rejected
    a sound percentile-bootstrap submission. Calling the real check removes the
    drift between what is calibrated and what is graded.
    """
    out = {"mean_difference_mg_l": round(float(est), 4),
           "ci_lower_mg_l": round(float(lo), 4),
           "ci_upper_mg_l": round(float(hi), 4),
           "significant": bool(lo > 0 or hi < 0)}
    try:
        V["_check_result"](out, b, "calibration")
        return True, ""
    except AssertionError as exc:
        return False, str(exc).split("\n")[0][:110]


def power_law_interval(d, cols, smeared, resamples):
    """Point estimate plus the bootstrap's ACTUAL asymmetric percentile bounds."""
    import patsy as _p
    y, X = _p.dmatrices("log_nitrate ~ " + " + ".join(["treat"] + cols), d,
                        return_type="dataframe")
    Xa, ya = np.asarray(X, float), np.asarray(y, float).ravel()
    ti = list(X.columns).index("treat")
    point = V["_power_law_ate"](Xa, ya, ti, smeared)
    draws = [V["_power_law_ate"](Xa[r], ya[r], ti, smeared) for r in resamples]
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return point, float(lo), float(hi)


names = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir())
print(f"{len(names)} monitoring programs: {', '.join(names)}\n")

legit_fail = defaultdict(list)
mut_fail = defaultdict(int)
mut_fams = {}
oracle_fail = []

sys.path.insert(0, str(SOLUTION.parent))
import importlib.util

# The mutant battery swaps solution/solve.py in place while it runs. Loading the
# reference without checking produced a confident, wrong "the reference fails on
# h01 and shipped" report once, because calibration and the battery were running
# at the same time and this picked up a mutant. Fail loudly instead.
_sol_src = SOLUTION.read_text(encoding="utf-8")
assert "Four adjustments are required" in _sol_src, (
    f"{SOLUTION} is not the reference solution right now -- a mutant is probably "
    f"swapped in by a running battery. Wait for it to finish and re-run.")

spec = importlib.util.spec_from_file_location("ref_solution", SOLUTION)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)

for name in names:
    csv = FIXTURES / name / "water_quality.csv"
    raw = pd.read_csv(csv)
    d = prep_plus(raw)
    b = band(cloud(prep(raw)))

    # --- the shipped reference solution must pass ---
    r = ref.analyze(csv)
    hw = (r["ci_upper_mg_l"] - r["ci_lower_mg_l"]) / 2
    if not inside(b, r["mean_difference_mg_l"], hw):
        oracle_fail.append(name)

    # --- fairness: the rating-curve convention computed with a DIFFERENT bootstrap
    #     seed and draw count must still pass.  That is exactly the numerical slop
    #     the pad exists for, and an accept-side probe using seed 7 / 400 draws was
    #     measured falling outside the band before the convention was enumerated
    #     across encodings.
    import numpy as _np
    _order = d["site_id"].to_numpy()
    _sites = d["site_id"].unique()
    _rows = {s: _np.flatnonzero(_order == s) for s in _sites}
    # Fairness bar: a CONVERGED bootstrap. A 250-500 draw percentile interval on
    # twelve clusters is genuinely unstable seed-to-seed (measured ~1.37x spread at
    # 300 draws, ~1.08x at 2000), so a handful of such variants fall outside the
    # band on 2 of the 12 programs. That is a property of an under-powered resample,
    # not of the band; it is recorded as a residual rather than padded for, because
    # padding for it costs the raw-linear-discharge discriminator.
    # Seeds and draw counts an agent might plausibly pick, none of them the
    # reference's own, including deliberately under-converged ones.
    for seed, draws in ((7, 400), (99, 250), (2, 600), (555, 1000), (31337, 2000),
                        (404, 5000)):
        _rng = _np.random.default_rng(seed)
        rs = [_np.concatenate([_rows[s] for s in _rng.choice(_sites, len(_sites), replace=True)])
              for _ in range(draws)]
        for sn, sc in SEASON.items():
            for dn, dc in DIURNAL.items():
                for sm in (False, True):
                    est, lo, hi = power_law_interval(d, DISCHARGE["log"] + sc + dc, sm, rs)
                    ok, why = passes_real_check(b, est, lo, hi)
                    if not ok:
                        legit_fail[
                            f"powerlaw|{sn}|{dn}|smear={sm}|seed{seed}/{draws} [{why}]"
                        ].append(name)

    # --- fairness: every accepted analysis must pass ---
    for qn, qc in DISCHARGE.items():
        ests = SITE_ESTIMATORS if qn == "log" else OLS_ONLY
        for sn, sc in SEASON.items():
            for dn, dc in DIURNAL.items():
                for e in ests:
                    est, h = fit(d, qc + sc + dc, e)
                    if not inside(b, est, h):
                        legit_fail[f"{qn}|{sn}|{dn}|{e}"].append(name)

    # --- soundness: incomplete analyses must not pass everywhere ---
    allq = {**DISCHARGE, **BAD_Q}
    alls = {**SEASON, **BAD_S}
    alld = {**DIURNAL, **BAD_D}
    for qn, qc in allq.items():
        for sn, sc in alls.items():
            for dn, dc in alld.items():
                for e in SITE_ESTIMATORS + BAD_EST:
                    fams = []
                    if qn in BAD_Q: fams.append(qn)
                    if sn in BAD_S: fams.append(sn)
                    if dn in BAD_D: fams.append(dn)
                    if e in BAD_EST: fams.append(e)
                    if not fams:
                        continue
                    if qn == "inverse" and e in ("mixedlm", "gee"):
                        continue        # documented as not an accepted pairing
                    key = f"{qn}|{sn}|{dn}|{e}"
                    mut_fams[key] = fams
                    try:
                        est, h = fit_any(d, qc + sc + dc, e)
                    except Exception:
                        mut_fail[key] += 1
                        continue
                    if not inside(b, est, h):
                        mut_fail[key] += 1
    print(f"  {name}: band pt[{b['point_lo']:+.3f},{b['point_hi']:+.3f}] "
          f"hw[{b['hw_lo']:.3f},{b['hw_hi']:.3f}] over {b['n_accepted']} accepted analyses")

n = len(names)
print()
ok = True

if oracle_fail:
    ok = False
    print(f"FAIL  reference solution outside band on: {oracle_fail}")
else:
    print(f"ok    reference solution passes all {n} programs")

if legit_fail:
    ok = False
    print(f"FAIL  {len(legit_fail)} accepted analyses rejected somewhere:")
    for k, v in list(legit_fail.items())[:15]:
        print(f"        {k:34s} on {v}")
else:
    print(f"ok    all accepted analyses pass all {n} programs (no false rejection)")

survivors = [k for k in mut_fams if mut_fail.get(k, 0) == 0]
if survivors:
    ok = False
    print(f"FAIL  {len(survivors)} incomplete analyses pass every program:")
    for k in survivors[:15]:
        print(f"        {k:34s} {mut_fams[k]}")
else:
    print(f"ok    no incomplete analysis passes all {n} programs ({len(mut_fams)} checked)")

per_fam = defaultdict(list)
for k, fams in mut_fams.items():
    for f in fams:
        per_fam[f].append(mut_fail.get(k, 0))
print()
print("  per-family: programs failed by the WEAKEST member of each family")
weakest = defaultdict(list)
for k, fams in mut_fams.items():
    for f in fams:
        weakest[f].append((mut_fail.get(k, 0), k))
for f in sorted(per_fam):
    v = per_fam[f]
    lo_n, lo_k = min(weakest[f])
    print(f"    {f:14s} n={len(v):4d}  min={min(v)}  median={int(np.median(v))}  "
          f"max={max(v)}   weakest: {lo_k}")

print()
print("PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
