"""Synthetic tests of eval/real_score.py (window rule, mocap-gap masking, drift-segment guard).
Run: ~/venv-ardupilot/bin/python3 -m pytest eval/real_score_test.py -q   (evo_ape from ~/venv-evo is called)"""
import math, os, sys, tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import real_score as RS

M = dict(RS.DEFAULT_PREREG["metrics"])
W = dict(RS.DEFAULT_PREREG["window"])
DT = {"segment_rule": "window_start_time", "init_segment_s": 10.0, "min_extent_m": 1.0}   # the pre-2026-10-11 segment


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
        r = RS.score_one(mo, est, t0, t1, M, d, "drift", DT)
        assert "error" not in r["drift_start_aligned"]
        assert r["drift_start_aligned"]["init_segment_extent_h_m"] > 1.0
        assert abs(r["drift_start_aligned"]["final_h_m"] - 0.01 * (t1 - t0)) < 0.15
        h = RS.score_one(mo, est, 25.0, 140.0, M, d, "hover", DT)   # initial segment in the hover
        assert "error" in h["drift_start_aligned"] and h["drift_start_aligned"]["init_segment_extent_h_m"] < 1e-6



# ---------------- 2026-10-11: the pre-registered drift segment, the strict prereg JSON, the clock-map check ----------------
def test_motion_onset_segment_skips_the_hover():
    mo = flight(); est = as_est(mo, drift=(0.01, 0.0))
    w = {**W, "start_after_takeoff_s": 10.0}                  # window from 30.5 s: 14.5 s of hover before the legs
    t0, t1, _ = RS.window_from_rule(mo, w)
    D = dict(RS.DEFAULT_PREREG["drift"])                       # motion_onset_path, init_path_m 2.0
    s0, s1, why = RS.drift_segment(mo, t0, t1, D)
    assert why is None and 44.5 <= s0 <= 46.0 and abs((s1 - s0) - 2.0 / 0.4) < 0.6     # on the first leg, ~2 m
    with tempfile.TemporaryDirectory() as d:
        r = RS.score_one(mo, est, t0, t1, M, d, "onset", D)["drift_start_aligned"]
        legacy = RS.score_one(mo, est, t0, t1, M, d, "legacy", DT)["drift_start_aligned"]
    assert "error" not in r and r["init_segment_extent_h_m"] >= 1.9
    assert abs(r["final_h_m"] - 0.01 * (t1 - s0)) < 0.15       # drift accrued since the segment
    assert "error" in legacy                                   # the draft's old segment: inside the hover, refused


def _files(d):
    mo = flight(); est = as_est(mo)
    pm, pe = f"{d}/mocap.tum", f"{d}/fgo.tum"
    RS.write_tum(pm, mo); RS.write_tum(pe, est)
    return pm, pe


def _prereg(d, name, **chg):
    import copy, json
    p = copy.deepcopy(RS.DEFAULT_PREREG)
    for k, v in chg.items():
        sec, key = k.split("__")
        p[sec][key] = v
    path = f"{d}/{name}.json"
    json.dump(p, open(path, "w"))
    return path


def test_prereg_is_strict():
    import copy, pytest
    ok = copy.deepcopy(RS.DEFAULT_PREREG)
    RS.load_prereg(ok)
    for bad in ({"metrics": {**ok["metrics"], "primary": "rpe"}},
                {"metrics": {**ok["metrics"], "t_max_diff_s": 0.1}},                 # evo is called with 0.05 only
                {"metrics": {k: v for k, v in ok["metrics"].items() if k != "max_gap_s"}},
                {"window": {**ok["window"], "start_after_takeof_s": 25.0}},          # a typo: unknown key
                {"drift": {**ok["drift"], "segment_rule": "first_10_s"}},
                {"estimator_records": {"UKF": "XUKZ"}},
                {"extra_section": 1}):
        with pytest.raises(SystemExit):
            RS.load_prereg({**copy.deepcopy(ok), **bad})
    with pytest.raises(SystemExit):
        RS.load_prereg({k: v for k, v in ok.items() if k != "drift"})


def test_prereg_json_drives_window_primary_and_records():
    import pytest
    with tempfile.TemporaryDirectory() as d:
        pm, pe = _files(d)
        a = RS.main(["--prereg", _prereg(d, "a"), "--mocap", pm, "--est", f"FGO={pe}",
                     "--work-dir", f"{d}/wa", "--out", f"{d}/a.json"])
        b = RS.main(["--prereg", _prereg(d, "b", window__start_after_takeoff_s=30.0, metrics__primary="ate_4dof"),
                     "--mocap", pm, "--est", f"FGO={pe}", "--work-dir", f"{d}/wb", "--out", f"{d}/b.json"])
        assert abs((b["window_s"][0] - a["window_s"][0]) - 5.0) < 1e-9 and b["window_s"][1] == a["window_s"][1]
        assert a["primary_metric"] == "evo_ape_a_se3" and a["primary"]["FGO"] == a["estimators"]["FGO"]["evo_ape_a_se3"]["rmse_m"]
        assert b["primary_metric"] == "ate_4dof" and b["primary"]["FGO"] == b["estimators"]["FGO"]["ate_4dof"]["rmse_m"]
        assert a["prereg"]["sha256"] != b["prereg"]["sha256"]
        with pytest.raises(SystemExit):                       # the prereg says UKF = XUKO: a TUM may not stand in for it
            RS.main(["--prereg", _prereg(d, "c"), "--mocap", pm, "--est", f"UKF={pe}",
                     "--work-dir", f"{d}/wc", "--out", f"{d}/c.json"])


def test_draft_prereg_loads_and_matches_the_tested_defaults():
    p = RS.load_prereg(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs",
                                    "rung1_preregistration_draft.json"))
    assert "DRAFT for user sign-off" in p["status"]
    for sec in ("window", "metrics", "drift"):
        assert p[sec] == RS.DEFAULT_PREREG[sec], sec            # the tests exercise exactly the draft's definitions
    assert p["estimator_records"]["UKF"] == "XUKO" and p["metrics"]["primary"] == "evo_ape_a_se3"


def test_clock_map_check():
    import pytest
    cm = {"rule": "disarmed_wiggles", "w_thr_rad_s": 2.0, "pad_s": 2.0, "merge_s": 1.0, "min_burst_s": 1.0}
    rule = {"w_thr_rad_s": 2.0, "pad_s": 2.0, "merge_s": 1.0, "min_burst_s": 1.0}
    good = {"window_sources": {"early": "default: last |w| burst before arming",
                               "late": "default: first |w| burst after disarming", "init_seg": "given"},
            "sync_window_rule": rule}
    RS.check_clock_map(cm, good)
    with pytest.raises(SystemExit):
        RS.check_clock_map(cm, {**good, "window_sources": {"early": "given", "late": "default: x"}})
    with pytest.raises(SystemExit):
        RS.check_clock_map(cm, {**good, "sync_window_rule": {**rule, "w_thr_rad_s": 1.5}})
    import mocap_align as MA                                   # the constants mocap_align writes match the draft
    assert (MA.SYNC_W_THR, MA.SYNC_PAD_S, MA.SYNC_MERGE_S, MA.SYNC_MIN_S) == (2.0, 2.0, 1.0, 1.0)

if __name__ == "__main__":
    for f in (test_airborne_window_ignores_held_start, test_gap_masking_and_exact_recovery, test_drift_metric_and_hover_guard,
              test_motion_onset_segment_skips_the_hover, test_prereg_is_strict, test_prereg_json_drives_window_primary_and_records,
              test_clock_map_check):
        f(); print("ok", f.__name__)
