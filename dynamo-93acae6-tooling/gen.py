"""Parameterised generator for the wetland-nitrate dataset.

Everything the design depends on is an explicit parameter so the separation
invariant in calibrate.py can be searched over, rather than grid-searched by
hand after the fact.
"""
from dataclasses import dataclass, field, asdict
import numpy as np
import pandas as pd


@dataclass
class Params:
    seed: int = 20260814
    n_sites_per_arm: int = 6
    n_stations: int = 4
    n_rounds: int = 6

    # log-scale structural model for nitrate
    b0: float = 0.55
    b_treat: float = -0.75          # true restoration effect (log scale)
    b_q: float = 0.75               # dilution strength (coefficient on log Q)
    b_season: float = 0.42          # seasonal amplitude (log scale)
    b_diurnal: float = 0.70         # diurnal amplitude (log scale)

    # variance components (log scale)
    site_re_sd: float = 0.02
    station_re_sd: float = 0.06
    resid_sd: float = 0.10

    # discharge
    discharge_base_c: float = 1.2
    discharge_base_r: float = 2.8
    site_logq_sd: float = 0.6
    round_logq_sd: float = 0.0      # seasonal flow variation, shared within a round
    obs_logq_sd: float = 0.0        # per-observation flow jitter

    # --- seasonal timing imbalance -------------------------------------------
    # The two contractors ran their campaigns over DIFFERENT, overlapping windows
    # (not the same schedule rigidly offset -- see BASE_DATES).  `*_start_doy` is
    # the first round; rounds are `round_spacing` days apart.  Sites in
    # `*_atypical_sites` are pulled `atypical_pull` days toward the other
    # contractor's window, so the imbalance survives but no single crosstab
    # separates the groups cleanly.
    ref_start_doy: int = 60
    res_start_doy: int = 135
    round_spacing: int = 36
    atypical_pull: int = 40
    res_atypical_sites: tuple = ("R5", "R6")
    ref_atypical_sites: tuple = ("C5", "C6")

    # diurnal timing imbalance
    restored_hour_typical: float = 8.5
    reference_hour_typical: float = 13.0
    hour_atypical_delta: float = 2.5
    res_hour_atypical_sites: tuple = ("R6", "R3")
    ref_hour_atypical_sites: tuple = ("C5", "C3")
    hour_jitter_sd: float = 1.0

    # phases
    season_phase_doy: float = 30.0   # day-of-year of the seasonal maximum
    diurnal_phase_hr: float = 3.0    # hour of the diurnal maximum (pre-dawn peak)


YEAR = 2025

# Load-bearing design note.  The predecessor dataset ran six evenly-spaced
# bi-monthly rounds across the FULL calendar year, with the restoration
# contractor's rounds a rigid 35 days after the reference contractor's.  Under
# that geometry both contractors' schedules average to the same point on the
# annual cycle no matter what offset separates them, so the seasonal covariate is
# exactly orthogonal to treatment -- measured on the shipped predecessor data,
# R^2(treat ~ [sin,cos] of day-of-year) = 0.0000 -- and season simply cannot be a
# confounder.  A rigid shift of a full-cycle schedule is 0.0000 for every offset
# tested (15/35/60/90/120 days), so this was structural, not a calibration miss.
# Here the two contractors instead work different, partially overlapping
# campaign windows, which produces a genuine seasonal imbalance.


def round_doys(start_doy: int, n: int, spacing: int):
    return [start_doy + k * spacing for k in range(n)]


def doy_to_date(doy: int) -> pd.Timestamp:
    return pd.Timestamp(f"{YEAR}-01-01") + pd.Timedelta(days=int(doy) - 1)


def generate(p: Params) -> pd.DataFrame:
    rng = np.random.default_rng(p.seed)
    sites = ([f"R{i}" for i in range(1, p.n_sites_per_arm + 1)]
             + [f"C{i}" for i in range(1, p.n_sites_per_arm + 1)])

    site_re = {s: rng.normal(0, p.site_re_sd) for s in sites}
    site_logq = {s: rng.normal(0, p.site_logq_sd) for s in sites}
    station_re = {}
    for s in sites:
        for k in range(1, p.n_stations + 1):
            station_re[f"{s}-S{k}"] = rng.normal(0, p.station_re_sd)
    round_logq = rng.normal(0, p.round_logq_sd, size=p.n_rounds) if p.round_logq_sd else np.zeros(p.n_rounds)

    ref_doys = round_doys(p.ref_start_doy, p.n_rounds, p.round_spacing)
    res_doys = round_doys(p.res_start_doy, p.n_rounds, p.round_spacing)

    # An atypical site always moves TOWARD the other contractor's pattern, so it
    # masks the imbalance.  Deriving the direction from the actual values (rather
    # than hardcoding a sign) keeps that true on the fixtures where the imbalance
    # runs the other way -- otherwise the "atypical" sites amplify it instead.
    season_dir = 1 if p.res_start_doy > p.ref_start_doy else -1
    hour_dir = 1 if p.restored_hour_typical < p.reference_hour_typical else -1

    rows = []
    for s in sites:
        restored = s.startswith("R")
        if restored:
            base_doys = res_doys
            pull = -season_dir * p.atypical_pull if s in p.res_atypical_sites else 0
            hour_base = p.restored_hour_typical + (
                hour_dir * p.hour_atypical_delta if s in p.res_hour_atypical_sites else 0.0)
            q_base = p.discharge_base_r
        else:
            base_doys = ref_doys
            pull = +season_dir * p.atypical_pull if s in p.ref_atypical_sites else 0
            hour_base = p.reference_hour_typical - (
                hour_dir * p.hour_atypical_delta if s in p.ref_hour_atypical_sites else 0.0)
            q_base = p.discharge_base_c

        for k in range(1, p.n_stations + 1):
            station = f"{s}-S{k}"
            for r in range(p.n_rounds):
                doy = base_doys[r] + pull
                date = doy_to_date(doy)
                hour = float(np.clip(hour_base + rng.normal(0, p.hour_jitter_sd), 5.0, 19.0))

                log_q = (np.log(q_base) + site_logq[s] + round_logq[r]
                         + (rng.normal(0, p.obs_logq_sd) if p.obs_logq_sd else 0.0))
                q = float(np.exp(log_q))

                season = p.b_season * np.cos(2 * np.pi * (doy - p.season_phase_doy) / 365.0)
                diurnal = p.b_diurnal * np.cos(2 * np.pi * (hour - p.diurnal_phase_hr) / 24.0)

                log_c = (p.b0 + p.b_treat * restored - p.b_q * log_q + season + diurnal
                         + site_re[s] + station_re[station] + rng.normal(0, p.resid_sd))
                rows.append({
                    "site_id": s,
                    "site_type": "restored" if restored else "reference",
                    "station_id": station,
                    "sample_date": date.strftime("%Y-%m-%d"),
                    "sample_time": f"{int(hour):02d}:{int(round((hour % 1) * 60)) % 60:02d}",
                    "discharge_cms": round(q, 3),
                    "nitrate_mg_l": round(float(np.exp(log_c)), 3),
                })

    df = pd.DataFrame(rows)
    order = {s: i for i, s in enumerate(sites)}
    df = df.sort_values(
        ["site_id", "station_id", "sample_date"],
        key=lambda c: c.map(order) if c.name == "site_id" else c,
    ).reset_index(drop=True)
    return df


if __name__ == "__main__":
    d = generate(Params())
    print(d.shape)
    print(d.head())
    print(d.groupby("site_type")[["nitrate_mg_l", "discharge_cms"]].mean())
