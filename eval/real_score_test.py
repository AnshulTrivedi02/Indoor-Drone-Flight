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


def test_final_prereg_loads_and_matches_the_tested_defaults():
    """2026-10-12: the SIGNED-OFF prereg (the draft has no `secondary` section and no longer loads)."""
    import json, pytest
    docs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
    p = RS.load_prereg(os.path.join(docs, "rung1_preregistration.json"))
    assert p["status"].startswith("PRE-REGISTERED") and "2026-10-12" in p["status"]
    for sec in ("window", "metrics", "drift", "secondary"):
        assert p[sec] == RS.DEFAULT_PREREG[sec], sec            # the tests exercise exactly the registered definitions
    assert p["estimator_records"]["UKF"] == "XUKO" and p["metrics"]["primary"] == "evo_ape_a_se3"
    d = json.load(open(os.path.join(docs, "rung1_preregistration_draft.json")))
    for sec in ("window", "metrics", "drift", "estimator_records", "clock_map"):
        assert d[sec] == p[sec], sec                            # signed off unchanged; only `secondary` was added
    with pytest.raises(SystemExit):
        RS.load_prereg(d)


def test_xkf1_core_is_explicit_and_filtered():
    """A Replay output log holds the onboard XKF1 (C = 0) AND the replayed one (C = 100): the record names the core."""
    import pytest
    from types import SimpleNamespace as NS
    assert RS.parse_record("XKF1@100") == ("XKF1", 100) and RS.parse_record("XUKO") == ("XUKO", None)
    assert RS.parse_record("XUKO@onboard") == ("XUKO", "onboard") and RS.parse_record("XUKF@onboard") == ("XUKF", "onboard")
    assert RS.physical_name("XUKO", None) == "RUKO" and RS.physical_name("XUKO", "onboard") == "XUKO"
    for bad in ("XKF1", "XKF1@x", "XUKO@100", "XKF9", "XFGO@onboard", "XKF1@onboard", "XUKO@0"):
        with pytest.raises(SystemExit):
            RS.parse_record(bad)
    with pytest.raises(SystemExit):
        RS.load_prereg({**RS.DEFAULT_PREREG, "estimator_records": {"EKF3": "XKF1"}})

    class Reader:
        def __init__(self, rows): self.rows = list(rows)
        def recv_match(self, type):
            while self.rows:
                r = self.rows.pop(0)
                if r.get_type() in type:
                    return r
            return None

    def rec(ty, t, pn, c=None):
        x = NS(TimeUS=int(t * 1e6), PN=pn, PE=0.0, PD=0.0, get_type=lambda: ty)
        if c is not None:
            x.C = c
        return x
    rows = [rec("XKF1", 1.0, 1.0, 0), rec("XKF1", 1.0, 2.0, 1), rec("XKF1", 1.0, 3.0, 100), rec("XKF1", 1.0, 4.0, 101),
            rec("RUKO", 1.0, 5.0), rec("XUKO", 1.0, 7.0), rec("XKF1", 2.0, 10.0, 0), rec("XKF1", 2.0, 30.0, 100)]
    tr = RS.bin_trajs(None, ["XKF1@100", "XKF1@0", "XUKO", "XUKO@onboard"], reader=Reader(rows))
    assert tr["XKF1@100"][:, 1].tolist() == [3.0, 30.0]       # the replayed core 0 only
    assert tr["XKF1@0"][:, 1].tolist() == [1.0, 10.0]         # the onboard core 0 only
    assert tr["XUKO"][:, 1].tolist() == [5.0]                 # the replayed UKF: message RUKO (U10 rule 2)
    assert tr["XUKO@onboard"][:, 1].tolist() == [7.0]         # the flying port's own XUKO


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

# ---------------- 2026-10-12: secondary metrics, the strict dataflash reader, the XUKO source ----------------
def _yaw_quat(yaw_enu_rad):
    from scipy.spatial.transform import Rotation as Rot
    return Rot.from_euler("z", np.asarray(yaw_enu_rad).reshape(-1, 1)).as_quat()


def _mocap_with_heading(mo, psi0_deg=30.0):
    """The synthetic flight's mocap with a real orientation: a constant ENU heading psi0 (the rigid body's yaw)."""
    out = mo.copy(); out[:, 4:8] = _yaw_quat(np.full(len(mo), math.radians(psi0_deg)))
    return out


def _est_dead_reckoned(mo, rate=50.0, frame_yaw_deg=20.0, yaw_rate_dpm=6.0, t_start=None, psi0_deg=30.0):
    """An estimator that dead-reckons the TRUE horizontal velocity rotated by its growing heading error
    e(t) = yaw_rate_dpm * (t - t_start) (NED sense: clockwise), expressed in its own frame (rotated by frame_yaw_deg
    from the mocap frame, ENU). Its heading = truth heading + e (NED) in its frame."""
    te = np.arange(mo[0, 0], mo[-1, 0], 1.0 / rate)
    t_start = mo[0, 0] if t_start is None else t_start
    vx, vy = np.gradient(mo[:, 1], mo[:, 0]), np.gradient(mo[:, 2], mo[:, 0])
    vx, vy = np.interp(te, mo[:, 0], vx), np.interp(te, mo[:, 0], vy)
    e = np.radians(yaw_rate_dpm / 60.0 * np.clip(te - t_start, 0, None))     # NED sense: ENU rotation by -e
    c, s = np.cos(-e), np.sin(-e)
    wx, wy = c * vx - s * vy, s * vx + c * vy                                  # velocity in the mocap frame, mis-headed
    f = math.radians(frame_yaw_deg); cf, sf = math.cos(-f), math.sin(-f)       # into the estimator frame
    ex, ey = cf * wx - sf * wy, sf * wx + cf * wy
    tz = lambda v: np.r_[0.0, np.cumsum(0.5 * (v[1:] + v[:-1]) * np.diff(te))]     # trapezoidal dead reckoning
    px, py = tz(ex), tz(ey)
    pz = np.interp(te, mo[:, 0], mo[:, 3])
    yaw_enu = math.radians(psi0_deg) - f - e                                   # truth heading, frame-rotated, + error
    return np.c_[te, px, py, pz, _yaw_quat(yaw_enu)], 90.0 - np.degrees(yaw_enu)


def test_heading_drift_rate_sign_and_offset_invariance():
    mo = _mocap_with_heading(flight())
    t0, t1, info = RS.window_from_rule(mo, W)
    for rate, fyaw in ((6.0, 20.0), (-9.0, -135.0)):
        est, yaw_ned = _est_dead_reckoned(mo, frame_yaw_deg=fyaw, yaw_rate_dpm=rate)
        r = RS.heading_drift(est[:, 0], yaw_ned, mo[:, 0], RS.yaw_ned_from_tum(mo), t0, t1)
        assert abs(r["heading_drift_deg_per_min_ned"] - rate) < 1e-6, r       # NED sense, any frame offset
        r2 = RS.heading_drift(est[:, 0], RS.yaw_ned_from_tum(est), mo[:, 0], RS.yaw_ned_from_tum(mo), t0, t1)
        assert abs(r2["heading_drift_deg_per_min_ned"] - rate) < 1e-6       # the same from the TUM quaternions
    # wrap: a whole-turn offset is wrapped away (as the corridor rule); a runaway (>= 170 deg) is left unwrapped
    te = np.linspace(0, 120, 1201); tm = te.copy()
    r = RS.heading_drift(te, 370.0 + 0.5 * te / 60, tm, np.zeros_like(tm), 0, 120)
    assert abs(r["heading_drift_deg_per_min_ned"] - 0.5) < 1e-9 and not r["runaway_unwrapped"]
    r = RS.heading_drift(te, 200.0 * te / 60, tm, np.zeros_like(tm), 0, 120)
    assert abs(r["heading_drift_deg_per_min_ned"] - 200.0) < 1e-6 and r["runaway_unwrapped"]


def test_cross_track_closed_path_known_value_and_anchor():
    """A heading error growing at k deg/min makes the dead-reckoned path veer; for a small error the lateral error RATE
    is v * e(t) (to the RIGHT for a clockwise, NED-positive error: the corridor sign, +8 deg/min with +40 m East),
    whatever the leg direction; on a closed rectangle a fixed-axis
    (East) measure would cancel, the path-normal one accumulates."""
    mo = _mocap_with_heading(flight())
    t0, t1, info = RS.window_from_rule(mo, W)
    cfg = dict(RS.DEFAULT_PREREG["secondary"]["cross_track_drift"])
    k = 6.0
    est, yaw_ned = _est_dead_reckoned(mo, frame_yaw_deg=20.0, yaw_rate_dpm=k, t_start=info["takeoff_s"])
    r = RS.cross_track(est[:, 0], est[:, 1:4], yaw_ned, mo[:, 0], mo[:, 1:4], RS.yaw_ned_from_tum(mo), t0, t1, cfg,
                       t_anchor=info["takeoff_s"])
    assert abs(r["anchor_yaw_deg_enu"] - 20.0) < 1e-4                           # est -> mocap rotation, at take-off
    # expected: integral over cruise samples of +v * sin(e(t)) (right = positive), v = 0.4 m/s on the legs
    te = np.arange(t0, t1, 0.001); sp = np.hypot(np.gradient(np.interp(te, mo[:, 0], mo[:, 1]), te),
                                                   np.gradient(np.interp(te, mo[:, 0], mo[:, 2]), te))
    cr = RS._boxcar_t(te, sp, 1.0) > 0.15
    e = np.radians(k / 60.0 * (te - info["takeoff_s"]))
    want = float(np.sum(sp * np.sin(e) * cr) * 0.001)
    assert r["cross_track_m"] > 0 and abs(r["cross_track_m"] / want - 1) < 0.03, (r, want)
    assert abs(r["cruise_s"] - 75.0) < 1.5                                     # legs 45 s .. 120 s; hovers excluded
    # the corridor's fixed-East integral nearly cancels on the closed path; the path normal does not
    east = float(np.sum(np.gradient(est[:, 1], est[:, 0])[(est[:, 0] >= t0) & (est[:, 0] <= t1)]) * 0.02)
    assert abs(r["cross_track_m"]) > 2 * abs(east - (np.interp(t1, mo[:, 0], mo[:, 1]) - np.interp(t0, mo[:, 0], mo[:, 1])))
    # no heading error -> zero cross-track, whatever the frame yaw
    e0, y0 = _est_dead_reckoned(mo, frame_yaw_deg=-75.0, yaw_rate_dpm=0.0)
    z = RS.cross_track(e0[:, 0], e0[:, 1:4], y0, mo[:, 0], mo[:, 1:4], RS.yaw_ned_from_tum(mo), t0, t1, cfg,
                       t_anchor=info["takeoff_s"])
    assert abs(z["cross_track_m_per_min"]) < 0.01, z


def test_main_reports_secondary_from_the_final_prereg():
    import json
    mo = _mocap_with_heading(flight())
    est, _ = _est_dead_reckoned(mo, frame_yaw_deg=20.0, yaw_rate_dpm=6.0)
    pre = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "rung1_preregistration.json")
    p = json.load(open(pre)); del p["clock_map"]                    # no mocap_align JSON in this synthetic test
    with tempfile.TemporaryDirectory() as d:
        pm, pe = f"{d}/mocap.tum", f"{d}/fgo.tum"
        RS.write_tum(pm, mo); RS.write_tum(pe, est); json.dump(p, open(f"{d}/p.json", "w"))
        out = RS.main(["--prereg", f"{d}/p.json", "--mocap", pm, "--est", f"FGO={pe}", "--work-dir", f"{d}/w",
                       "--out", f"{d}/o.json"])
    r = out["estimators"]["FGO"]
    assert abs(r["heading_drift"]["heading_drift_deg_per_min_ned"] - 6.0) < 1e-3
    assert r["cross_track_drift"]["cross_track_m"] > 0 and r["cross_track_drift"]["anchor"] == "takeoff_yaw"
    assert r["cross_track_drift"]["anchor_sensitivity_m_per_min_per_deg"] > 0.3     # ~0.4 m/s * 1 deg * 60 s


def test_secondary_section_is_strict():
    import copy, pytest
    ok = copy.deepcopy(RS.DEFAULT_PREREG)
    for bad in ({"heading_drift": {**ok["secondary"]["heading_drift"], "sense": "ENU"}},
                {"cross_track_drift": {**ok["secondary"]["cross_track_drift"], "anchor": "identity"}},
                {"cross_track_drift": {k: v for k, v in ok["secondary"]["cross_track_drift"].items() if k != "smooth_s"}},
                {"lateral": {}}):
        p = copy.deepcopy(ok); p["secondary"] = {**p["secondary"], **bad}
        with pytest.raises(SystemExit):
            RS.load_prereg(p)


def _df_log(xuko_fmt=True, replay_mismatch=False, dup_xuko=False, undeclared=True, name="RUKO", uk_id=151,
            onboard_id=None, redeclare=False):
    """A tiny dataflash log: XKF1 cores 0 and 100, a UKF current-time record `name` (RUKO = the replayed one, from the
    U10 rule-2 Replay on; XUKO = the onboard one or an older Replay's) with or without its FMT, optionally an onboard
    XUKO as well (onboard_id: its type id, as a fork-flown Replay output carries), and an undeclared record type."""
    import df_reader as D
    kf = ("QBffffffffffff", "TimeUS,C,Roll,Pitch,Yaw,VN,VE,VD,dPD,PN,PE,PD,GX,GY")
    uk = ("QfffffffffBIBBI", ",".join(RS.XUKO_COLUMNS))
    b = D.write_fmt(150, "XKF1", *kf)
    if xuko_fmt:
        b += D.write_fmt(uk_id, name, *uk)
    if onboard_id is not None:
        b += D.write_fmt(onboard_id, "XUKO", *uk)
    for i in range(20):
        t = 1_000_000 + 100_000 * i
        b += D.write_rec(150, kf[0], t, 0, 0, 0, 10.0, 0, 0, 0, 0, 1.0 * i, 0.5 * i, -1.0, 0, 0)
        if undeclared:
            b += D.write_rec(229, "Qff", t, 1.0, 2.0)                  # a UKF-like record with NO FMT
        if not (replay_mismatch and i == 7):
            b += D.write_rec(150, kf[0], t, 100, 0, 0, 11.0, 0, 0, 0, 0, 2.0 * i, 0.5 * i, -1.0, 0, 0)
        b += D.write_rec(uk_id, uk[0], t + (0 if not (dup_xuko and i == 5) else -200_000), 3.0 * i, 0, -1, 0, 0, 0,
                         0, 0, 12.0, 1, 0, 0, 0, 0)
        if onboard_id is not None:                                     # the onboard series, at its own stamps
            b += D.write_rec(onboard_id, uk[0], t + 20_000, 3.0 * i + 0.5, 0, -1, 0, 0, 0, 0, 0, 13.0, 1, 0, 0, 0, 0)
        if redeclare and i == 10:
            b += D.write_fmt(uk_id, "ZZZZ", "Qff", "TimeUS,A,B")
    return b


def test_df_reader_survives_undeclared_records_and_bin_trajs_checks():
    import pytest
    with tempfile.TemporaryDirectory() as d:
        p = f"{d}/x.bin"; open(p, "wb").write(_df_log())
        info = {}
        tr = RS.bin_trajs(p, ["XKF1@100", "XKF1@0", "XUKO"], info_out=info)
        assert len(tr["XKF1@100"]) == 20 and tr["XKF1@100"][3, 1] == 6.0 and tr["XKF1@0"][3, 1] == 3.0
        assert tr["XKF1@100"][0, 4] == 11.0 and tr["XUKO"][2, 1] == 6.0 and tr["XUKO"][0, 4] == 12.0
        assert info["undeclared_types"] and info["skipped_bytes"] == 20 * (3 + 16)
        open(p, "wb").write(_df_log(xuko_fmt=False))                   # a stock-log Replay: UKF written without FMT
        with pytest.raises(SystemExit) as e:
            RS.bin_trajs(p, ["XUKO"])
        assert "no FMT for RUKO" in str(e.value) and "--est-csv" in str(e.value)
        tr = RS.bin_trajs(p, ["XKF1@100"])                             # ... but EKF3 is still read in full
        assert len(tr["XKF1@100"]) == 20
        open(p, "wb").write(_df_log(replay_mismatch=True))
        with pytest.raises(SystemExit) as e:
            RS.bin_trajs(p, ["XKF1@100"])
        assert "TimeUS" in str(e.value)
        open(p, "wb").write(_df_log(dup_xuko=True))                    # two interleaved series under one name
        with pytest.raises(SystemExit) as e:
            RS.bin_trajs(p, ["XUKO"])
        assert "interleaved" in str(e.value)


def test_u10_rule2_replayed_and_onboard_ukf_records_are_separate():
    """U10 rule 2 (2026-10-12): the replayed UKF is RUKO, the onboard XUKO; both readable, never mixed; an XUKO-only log
    is refused for the replayed record (older Replay or a flight log); an XUKO in Replay's id window is refused as
    'onboard'; a re-declared type id is refused."""
    import pytest
    with tempfile.TemporaryDirectory() as d:
        p = f"{d}/x.bin"
        open(p, "wb").write(_df_log(undeclared=False, uk_id=229, onboard_id=248))   # a fork-flown Replay output
        tr = RS.bin_trajs(p, ["XUKO", "XUKO@onboard", "XKF1@100"])
        assert len(tr["XUKO"]) == 20 and len(tr["XUKO@onboard"]) == 20
        assert tr["XUKO"][3, 1] == 9.0 and tr["XUKO@onboard"][3, 1] == 9.5            # each its own series
        assert tr["XUKO"][0, 4] == 12.0 and tr["XUKO@onboard"][0, 4] == 13.0
        open(p, "wb").write(_df_log(undeclared=False, name="XUKO", uk_id=248))       # a flight log (onboard only)
        with pytest.raises(SystemExit) as e:
            RS.bin_trajs(p, ["XUKO"])
        assert "no RUKO" in str(e.value) and "@onboard" in str(e.value)
        assert len(RS.bin_trajs(p, ["XUKO@onboard"])["XUKO@onboard"]) == 20
        open(p, "wb").write(_df_log(undeclared=False, name="XUKO", uk_id=229))       # an older (e82c050b) Replay output
        with pytest.raises(SystemExit) as e:
            RS.bin_trajs(p, ["XUKO@onboard"])
        assert "id window" in str(e.value)
        open(p, "wb").write(_df_log(undeclared=False, redeclare=True))
        with pytest.raises(SystemExit) as e:
            RS.bin_trajs(p, ["XKF1@100"])
        assert "re-declared" in str(e.value)


def test_xuko_csv_source():
    import pytest
    with tempfile.TemporaryDirectory() as d:
        p = f"{d}/ukf_output.csv"
        rows = [[1_000_000 + 40_000 * i, 0.1 * i, 0.2 * i, -1.0, 0, 0, 0, 0, 0, 5.0, 1, 0, 3, 0, 0] for i in range(30)]
        open(p, "w").write(",".join(RS.XUKO_COLUMNS) + "\n" + "\n".join(",".join(str(v) for v in r) for r in rows))
        a = RS.csv_traj(p, "XUKO")
        assert a.shape == (30, 5) and a[2, 0] == 1.08 and a[2, 2] == 0.4 and a[0, 4] == 5.0
        with pytest.raises(SystemExit):
            RS.csv_traj(p, "XUKF")
        open(p, "w").write("TimeUS,PN,PE,PD,VN,VE,VD,Roll,Pitch,Yaw,SVN,SVE,SS,Healthy,FlowAgeMs,FXa,FYa,Ra\n1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n")
        with pytest.raises(SystemExit):                                # the horizon-state ukf_shadow.csv is NOT XUKO
            RS.csv_traj(p, "XUKO")


if __name__ == "__main__":
    for f in (test_airborne_window_ignores_held_start, test_gap_masking_and_exact_recovery, test_drift_metric_and_hover_guard,
              test_motion_onset_segment_skips_the_hover, test_prereg_is_strict, test_prereg_json_drives_window_primary_and_records,
              test_clock_map_check):
        f(); print("ok", f.__name__)
