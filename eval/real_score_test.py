"""Synthetic tests of eval/real_score.py (window rule, mocap-gap masking, drift-segment guard).
Run: ~/venv-ardupilot/bin/python3 -m pytest eval/real_score_test.py -q   (evo_ape from ~/venv-evo is called)"""
import math, os, sys, tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import real_score as RS

M = dict(RS.DEFAULT_PREREG["metrics"])
W = dict(RS.DEFAULT_PREREG["window"])


def flight(rate=120.0, held_start=True):
    """Mocap truth (TUM, z up): held up 1.0 m for the first 4 s (sync wiggle), set down, take-off at 20 s to 1.2 m,
    hover to 45 s, a 4 m x 3 m rectangle at 0.4 m/s from 45 s, hover, land at 150 s, rest to 160 s."""
    t = np.arange(0.0, 160.0, 1.0 / rate)
    z = np.where(t < 4.0, 1.0, 0.0) if held_start else np.zeros_like(t)
    z = z + 1.2 * np.clip((t - 20) / 2, 0, 1) * np.clip((150 - t) / 2, 0, 1)
    s = np.clip(t - 45.0, 0, None) * 0.4                     # path length along the rectangle
    per = 14.0; u = np.mod(s, per)
    x = np.where(u < 4, u, np.where(u < 7, 4.0, np.where(u < 11, 11 - u, 0.0)))
    y = np.where(u < 4, 0.0, np.where(u < 7, u - 4, np.where(u < 11, 3.0, 14 - u)))
    stop = t > 120.0                                         # hover from 120 s
    x[stop] = np.interp(120.0, t, x); y[stop] = np.interp(120.0, t, y)
    q = np.tile([0.0, 0.0, 0.0, 1.0], (len(t), 1))
    return np.c_[t, x, y, z, q]


def as_est(mo, rate=50.0, yaw_deg=20.0, drift=(0.0, 0.0)):
    te = np.arange(mo[0, 0], mo[-1, 0], 1.0 / rate)
    p = np.c_[[np.interp(te, mo[:, 0], mo[:, k]) for k in (1, 2, 3)]].T
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    p = (np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]) @ p.T).T + np.array([3.0, -1.0, 0.2])
    p[:, 0] += drift[0] * (te - te[0]); p[:, 1] += drift[1] * (te - te[0])
    return np.c_[te, p, np.tile([0.0, 0.0, 0.0, 1.0], (len(te), 1))]


def test_airborne_window_ignores_held_start():
    mo = flight()
    t0, t1, info = RS.window_from_rule(mo, W)
    assert abs(info["ground_level_m"]) < 1e-9                 # not 1.0 m from the held sync wiggle
    assert abs(info["takeoff_s"] - 20.5) < 0.02 and abs(info["landing_s"] - 149.5) < 0.02
    assert abs(t0 - (info["takeoff_s"] + 25.0)) < 1e-9 and abs(t1 - (info["landing_s"] - 5.0)) < 1e-9


def test_gap_masking_and_exact_recovery():
    mo = flight(); est = as_est(mo)
    t0, t1, _ = RS.window_from_rule(mo, W)
    gap = (mo[:, 0] > 54.5) & (mo[:, 0] < 56.0)              # 1.5 s mocap dropout across the first corner (55 s)
    with tempfile.TemporaryDirectory() as d:
        full = RS.score_one(mo, est, t0, t1, M, d, "full")
        g = RS.score_one(mo[~gap], est, t0, t1, M, d, "gap")
        nomask = RS.score_one(mo[~gap], est, t0, t1, {**M, "max_mocap_interp_gap_s": 10.0}, d, "nomask")
    assert full["n_dropped_mocap_gap"] == 0 and full["ate_4dof"]["rmse_m"] < 1e-5
    assert 70 <= g["n_dropped_mocap_gap"] <= 80             # 50 Hz x ~1.5 s
    assert g["ate_4dof"]["rmse_m"] < 1e-5                    # masked: no invented truth
    assert nomask["ate_4dof"]["max_m"] > 0.1                 # what interpolating across the corner would have done
    assert abs(full["ate_4dof"]["yaw_deg"] - 20.0) < 1e-6


def test_drift_metric_and_hover_guard():
    mo = flight(); est = as_est(mo, drift=(0.01, 0.0))       # 1 cm/s drift in x
    t0, t1, _ = RS.window_from_rule(mo, W)                   # starts at 45.5 s: moving
    with tempfile.TemporaryDirectory() as d:
        r = RS.score_one(mo, est, t0, t1, M, d, "drift")
        assert "error" not in r["drift_start_aligned"]
        assert r["drift_start_aligned"]["init_segment_extent_h_m"] > 1.0
        assert abs(r["drift_start_aligned"]["final_h_m"] - 0.01 * (t1 - t0)) < 0.15
        h = RS.score_one(mo, est, 25.0, 140.0, M, d, "hover")   # initial segment in the hover
        assert "error" in h["drift_start_aligned"] and h["drift_start_aligned"]["init_segment_extent_h_m"] < 1e-6


if __name__ == "__main__":
    for f in (test_airborne_window_ignores_held_start, test_gap_masking_and_exact_recovery, test_drift_metric_and_hover_guard):
        f(); print("ok", f.__name__)
