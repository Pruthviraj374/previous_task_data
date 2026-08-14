"""Cheap probe: for a given round schedule + between-contractor shift, how much
seasonal imbalance actually exists?  No model fits -- just the geometry.

R2(treat ~ [sin,cos]) is the whole story: 0 means season cannot confound.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import statsmodels.api as sm


def r2(ref_doys, res_doys):
    doy = np.array(list(ref_doys) + list(res_doys), float)
    treat = np.array([0] * len(ref_doys) + [1] * len(res_doys), float)
    X = sm.add_constant(np.column_stack([np.sin(2 * np.pi * doy / 365.0),
                                         np.cos(2 * np.pi * doy / 365.0)]))
    return float(sm.OLS(treat, X).fit().rsquared)


def sched(start_doy, n, spacing):
    return [start_doy + k * spacing for k in range(n)]


print("=== rigid shift of the SAME schedule (what the design does today) ===")
print(f"{'window':>22} {'shift':>6} {'R2':>8}")
for label, start, n, sp in [("full year, bi-monthly", 15, 6, 61),
                            ("Mar-Oct campaign", 64, 6, 42),
                            ("Apr-Aug campaign", 95, 5, 30)]:
    for shift in [15, 35, 60, 90, 120]:
        ref = sched(start, n, sp)
        res = [d + shift for d in ref]
        print(f"{label:>22} {shift:6d} {r2(ref, res):8.4f}")

print()
print("=== two contractors with DIFFERENT campaign windows (overlapping) ===")
print(f"{'ref window':>16} {'res window':>16} {'R2':>8}  {'overlap days':>12}")
for (rs, rn, rsp), (ts, tn, tsp) in [
    ((60, 6, 30), (90, 6, 30)),
    ((60, 6, 30), (105, 6, 30)),
    ((60, 6, 30), (120, 6, 30)),
    ((60, 6, 36), (110, 6, 36)),
    ((55, 6, 40), (115, 6, 40)),
    ((50, 6, 45), (125, 6, 45)),
]:
    ref, res = sched(rs, rn, rsp), sched(ts, tn, tsp)
    ov = min(max(ref), max(res)) - max(min(ref), min(res))
    print(f"{f'{min(ref)}-{max(ref)}':>16} {f'{min(res)}-{max(res)}':>16} "
          f"{r2(ref, res):8.4f}  {ov:12d}")

print()
print("=== same window, but contractors interleave rounds unevenly ===")
# reference front-loads its rounds, restored back-loads them, same overall window
ref = [60, 80, 100, 130, 175, 230]
res = [75, 120, 165, 200, 225, 245]
print(f"  ref {ref}\n  res {res}\n  R2={r2(ref, res):.4f}  "
      f"span ref {max(ref)-min(ref)} res {max(res)-min(res)}")
