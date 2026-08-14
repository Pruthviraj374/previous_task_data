"""Held-out dataset specs.

The discriminating power comes from the CONJUNCTION across datasets, not from any
single band, so the specs deliberately vary each confound in magnitude, in SIGN,
and in geometry:

  * which contractor worked the later part of the season,
  * which contractor sampled earlier in the day,
  * which group sits on the higher-flow channels,
  * how wide the discharge range is (this is what decides whether a raw-linear or
    quadratic discharge term is badly wrong or merely slightly wrong),
  * how much of the annual cycle the campaign spans (this is what decides whether
    a linear day-of-year term can stand in for the seasonal cycle),
  * and the true restoration effect itself.

A submission that omits or mis-specifies a correction is wrong in a direction and
by an amount set by each dataset's own geometry, so it cannot be right on
datasets whose geometry points opposite ways.  Varying b_treat also removes the
hardcoded-constant risk outright: there is no single number that passes.

`r2_targets` are handed to autotune.py, which solves each fixture's contractor
hour gap / discharge ratio / campaign offset to hit them exactly.
"""
from gen import Params

# name -> (generator overrides, r2 targets)
SPECS = [
    ("shipped", dict(
        seed=20260814, b_treat=-0.75,
        ref_start_doy=60, res_start_doy=150, round_spacing=32, atypical_pull=25,
        restored_hour_typical=8.0, reference_hour_typical=12.5,
        discharge_base_c=1.2, discharge_base_r=2.4,
        b_season=1.2, b_diurnal=0.85, b_q=0.8,
        site_re_sd=0.25, site_logq_sd=0.34, obs_logq_sd=0.10,
    ), dict(t_season=0.30, t_diurnal=0.33, t_logq=0.48)),

    # 1. same orientation, narrow discharge range, short campaign
    ("h01", dict(
        seed=101, b_treat=-0.55,
        ref_start_doy=65, res_start_doy=145, round_spacing=26, atypical_pull=20,
        restored_hour_typical=8.5, reference_hour_typical=13.0,
        discharge_base_c=1.0, discharge_base_r=2.6,
        b_season=1.0, b_diurnal=0.9, b_q=0.75,
        site_re_sd=0.22, site_logq_sd=0.18, obs_logq_sd=0.06,
    ), dict(t_season=0.34, t_diurnal=0.28, t_logq=0.58)),

    # 2. SEASON REVERSED, wide discharge range
    ("h02", dict(
        seed=102, b_treat=-0.9,
        ref_start_doy=150, res_start_doy=60, round_spacing=34, atypical_pull=25,
        restored_hour_typical=8.0, reference_hour_typical=12.5,
        discharge_base_c=1.2, discharge_base_r=2.4,
        b_season=1.3, b_diurnal=0.85, b_q=0.8,
        site_re_sd=0.25, site_logq_sd=0.62, obs_logq_sd=0.18,
    ), dict(t_season=0.26, t_diurnal=0.35, t_logq=0.42)),

    # 3. DIURNAL REVERSED, long campaign (most of the annual cycle)
    ("h03", dict(
        seed=103, b_treat=-0.7,
        ref_start_doy=45, res_start_doy=150, round_spacing=45, atypical_pull=25,
        restored_hour_typical=13.0, reference_hour_typical=8.5,
        res_hour_atypical_sites=("R2", "R4"), ref_hour_atypical_sites=("C1", "C6"),
        discharge_base_c=1.1, discharge_base_r=2.5,
        b_season=1.1, b_diurnal=0.95, b_q=0.8,
        site_re_sd=0.24, site_logq_sd=0.30, obs_logq_sd=0.10,
    ), dict(t_season=0.24, t_diurnal=0.36, t_logq=0.52)),

    # 4. DISCHARGE REVERSED, very wide discharge range
    ("h04", dict(
        seed=104, b_treat=-0.65,
        ref_start_doy=60, res_start_doy=145, round_spacing=32, atypical_pull=22,
        restored_hour_typical=8.0, reference_hour_typical=12.5,
        discharge_base_c=2.6, discharge_base_r=1.1,
        b_season=1.15, b_diurnal=0.9, b_q=0.8,
        site_re_sd=0.25, site_logq_sd=0.75, obs_logq_sd=0.22,
    ), dict(t_season=0.31, t_diurnal=0.30, t_logq=0.40)),

    # 5. SEASON AND DIURNAL BOTH REVERSED, long campaign
    ("h05", dict(
        seed=105, b_treat=-0.85,
        ref_start_doy=155, res_start_doy=55, round_spacing=42, atypical_pull=20,
        restored_hour_typical=13.5, reference_hour_typical=8.0,
        res_hour_atypical_sites=("R1", "R5"), ref_hour_atypical_sites=("C2", "C4"),
        discharge_base_c=1.2, discharge_base_r=2.7,
        b_season=1.25, b_diurnal=1.0, b_q=0.85,
        site_re_sd=0.26, site_logq_sd=0.46, obs_logq_sd=0.14,
    ), dict(t_season=0.29, t_diurnal=0.32, t_logq=0.46)),

    # 6. weak diurnal, strong season, narrow discharge
    ("h06", dict(
        seed=106, b_treat=-0.6,
        ref_start_doy=58, res_start_doy=158, round_spacing=30, atypical_pull=18,
        restored_hour_typical=9.5, reference_hour_typical=12.0,
        discharge_base_c=1.15, discharge_base_r=2.3,
        b_season=1.5, b_diurnal=0.7, b_q=0.8,
        site_re_sd=0.24, site_logq_sd=0.20, obs_logq_sd=0.05,
    ), dict(t_season=0.38, t_diurnal=0.22, t_logq=0.60)),

    # 7. strong diurnal, weak season, wide discharge
    ("h07", dict(
        seed=107, b_treat=-0.95,
        ref_start_doy=70, res_start_doy=140, round_spacing=38, atypical_pull=28,
        restored_hour_typical=7.5, reference_hour_typical=13.5,
        discharge_base_c=0.9, discharge_base_r=3.0,
        b_season=0.9, b_diurnal=1.05, b_q=0.9,
        site_re_sd=0.27, site_logq_sd=0.68, obs_logq_sd=0.20,
    ), dict(t_season=0.21, t_diurnal=0.40, t_logq=0.44)),

    # 8. season reversed, discharge reversed, narrowest discharge range
    ("h08", dict(
        seed=108, b_treat=-0.5,
        ref_start_doy=150, res_start_doy=62, round_spacing=28, atypical_pull=24,
        restored_hour_typical=8.5, reference_hour_typical=12.5,
        discharge_base_c=2.4, discharge_base_r=1.3,
        b_season=1.2, b_diurnal=0.9, b_q=0.75,
        site_re_sd=0.25, site_logq_sd=0.16, obs_logq_sd=0.05,
    ), dict(t_season=0.33, t_diurnal=0.26, t_logq=0.62)),

    # 9. diurnal reversed + discharge reversed, mid-width discharge
    ("h09", dict(
        seed=109, b_treat=-0.8,
        ref_start_doy=52, res_start_doy=148, round_spacing=36, atypical_pull=26,
        restored_hour_typical=12.8, reference_hour_typical=8.4,
        res_hour_atypical_sites=("R3", "R6"), ref_hour_atypical_sites=("C2", "C5"),
        discharge_base_c=2.5, discharge_base_r=1.15,
        b_season=1.1, b_diurnal=0.95, b_q=0.85,
        site_re_sd=0.23, site_logq_sd=0.52, obs_logq_sd=0.16,
    ), dict(t_season=0.27, t_diurnal=0.37, t_logq=0.45)),

    # 10. all three imbalances reversed at once
    ("h10", dict(
        seed=110, b_treat=-0.6,
        ref_start_doy=158, res_start_doy=58, round_spacing=40, atypical_pull=22,
        restored_hour_typical=13.2, reference_hour_typical=8.2,
        res_hour_atypical_sites=("R1", "R4"), ref_hour_atypical_sites=("C3", "C6"),
        discharge_base_c=2.8, discharge_base_r=1.0,
        b_season=1.35, b_diurnal=0.9, b_q=0.8,
        site_re_sd=0.28, site_logq_sd=0.40, obs_logq_sd=0.12,
    ), dict(t_season=0.36, t_diurnal=0.24, t_logq=0.55)),

    # 11. weak everything -- the fixture where a wrong method is most likely to
    #     land in band, kept deliberately so the suite is not all easy cases
    ("h11", dict(
        seed=111, b_treat=-1.05,
        ref_start_doy=68, res_start_doy=138, round_spacing=30, atypical_pull=30,
        restored_hour_typical=9.2, reference_hour_typical=11.8,
        discharge_base_c=1.3, discharge_base_r=2.1,
        b_season=0.95, b_diurnal=0.8, b_q=0.7,
        site_re_sd=0.20, site_logq_sd=0.26, obs_logq_sd=0.08,
    ), dict(t_season=0.19, t_diurnal=0.19, t_logq=0.35)),
]

ALL = [(n, s) for n, s, _ in SPECS]
TARGETS = {n: t for n, _, t in SPECS}


def build(spec):
    return Params(**spec)
