#!/usr/bin/env python3
"""SITL regression of the rung-1 SECONDARY metrics (eval/real_score.py heading_drift / cross_track; prereg sec. 4.4)
against stored corridor values. Read-only on ~/thesis_data. ~/venv-ardupilot (numpy, scipy).

  H1  heading drift, TUM path (ENU quaternions), UKF and FGO, dsn_tex_r1..r3: eval/results/d15_drift.json `UKF_new` /
      `FGO_new` (ENU sense, eval/d15_drift.py) on its stored window. Expected: real_score's NED value = -(stored).
  H2  heading drift, NED-yaw path (the port's Replay CSV Yaw, as XUKO/XKF1 carry it): d15_port dsn_tex_r8
      ukf_shadow.csv against SIM.Yaw, the pinned cruise window; stored score.json `cruise_yaw_drift_dpm_NED`.
  X1  cross-track per minute, EKF3 (XKF1 core 0 against SIM, both in the shared NED frame), dsn_tex_r1..r3, the
      VELOCITY variant: eval/results/heading_share_restated.json `xtrack_err_m` / (`window_s` / 60) on the
      rerun_dsn_evo window, which integrated XKF1 VE (ve_given). Proves the window, sign, axis and integration.
  X2  the REGISTERED rule (d/dt of the positions) against the corridor's position-growth form (eval/
      ukf_shadow_replay_check.py cross_E, re-referenced at the window start) on the same samples. X1 and X2 differ by
      EKF3's own VE-vs-PE inconsistency (info_int_VE_minus_dPE_m), not by the metric.
      Anchor `identity` for both (the corridor's frames are shared by construction); the pre-registered `takeoff_yaw`
      anchor (here at the window start) is reported as information.
Writes regression_secondary_2026-10-12.json next to this script."""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, EV)
import real_score as RS
from df_reader import read_records

TD = os.path.expanduser("~/thesis_data")
TOL_H = 1e-6           # deg/min: same arithmetic, so equal to rounding
TOL_X1 = 0.005         # relative: same velocity (XKF1 VE/VN); lateral axis = mocap-velocity normal vs fixed East
TOL_X2 = 0.005         # relative: same positions; integral of d/dt PE (normal axis) vs end-point difference (East)


def sim_enu(path):
    r, _ = read_records(path, ["XKF1", "SIM"])
    x = np.array([(a["TimeUS"] / 1e6, a["PN"], a["PE"], a["PD"], a["Yaw"], a["VE"], a["VN"]) for a in r["XKF1"] if a["C"] == 0])
    s = np.array([(a["TimeUS"] / 1e6, a["Lat"], a["Lng"], a["Alt"], a["Yaw"]) for a in r["SIM"]])
    R = 6378137.0
    n = np.radians(s[:, 1] - s[0, 1]) * R; e = np.radians(s[:, 2] - s[0, 2]) * R * math.cos(math.radians(s[:, 1].mean()))
    return x[:, :5], np.c_[s[:, 0], e, n, s[:, 3] - s[0, 3]], s[:, 4], x[:, 5:7]


def main():
    out = {"H1": {}, "H2": {}, "X1": {}}; ok = True
    d15 = json.load(open(f"{EV}/results/d15_drift.json"))
    for tr in ("dsn_tex_r1", "dsn_tex_r2", "dsn_tex_r3"):
        win = d15[tr]["window"]; gt = np.loadtxt(f"{TD}/trials/{tr}/ukf/ground_truth.tum")
        for est in ("ukf", "fgo"):
            a = np.loadtxt(f"{TD}/trials/{tr}/{est}/{est}_traj.tum")
            r = RS.heading_drift(a[:, 0], RS.yaw_ned_from_tum(a), gt[:, 0], RS.yaw_ned_from_tum(gt), *win)
            want = -d15[tr][f"{est.upper()}_new"]
            d = r["heading_drift_deg_per_min_ned"] - want; ok &= abs(d) < TOL_H
            out["H1"][f"{tr}/{est}"] = {"real_score_ned": r["heading_drift_deg_per_min_ned"], "stored_enu": -want,
                                        "diff": d, "pass": bool(abs(d) < TOL_H)}
    tr = "dsn_tex_r8"
    import three_way_eval as T
    win = T.cruise_window(tr)
    c = np.genfromtxt(f"{TD}/d15_port/{tr}/ukf_shadow.csv", delimiter=",", names=True)
    r_, _ = read_records(f"{TD}/trials/{tr}/ardupilot.bin", ["SIM"])
    S = np.array([(a["TimeUS"] / 1e6, a["Yaw"]) for a in r_["SIM"]])
    r = RS.heading_drift(c["TimeUS"] / 1e6, c["Yaw"], S[:, 0], S[:, 1], *win)
    want = json.load(open(f"{TD}/d15_port/{tr}/score.json"))["cruise_yaw_drift_dpm_NED"]
    d = r["heading_drift_deg_per_min_ned"] - want; ok &= abs(d) < TOL_H
    out["H2"][tr] = {"real_score_ned": r["heading_drift_deg_per_min_ned"], "stored_ned": want, "diff": d,
                     "pass": bool(abs(d) < TOL_H)}
    hs = json.load(open(f"{EV}/results/heading_share_restated.json"))
    wins = json.load(open(f"{EV}/results/rerun_dsn_evo.json"))["trials"]
    cfg = dict(RS.DEFAULT_PREREG["secondary"]["cross_track_drift"]); cid = {**cfg, "anchor": "identity"}
    for tr in ("dsn_tex_r1", "dsn_tex_r2", "dsn_tex_r3"):
        x, g, gy, v = sim_enu(f"{TD}/trials/{tr}/ardupilot.bin")
        pe = np.c_[x[:, 2], x[:, 1], -x[:, 3]]
        t0, t1 = wins[tr]["window_s"]
        rv = RS.cross_track(x[:, 0], pe, x[:, 4], g[:, 0], g[:, 1:4], gy, t0, t1, cid, ve_given=v)       # XKF1 VE/VN
        rp = RS.cross_track(x[:, 0], pe, x[:, 4], g[:, 0], g[:, 1:4], gy, t0, t1, cid)                   # registered
        ra = RS.cross_track(x[:, 0], pe, x[:, 4], g[:, 0], g[:, 1:4], gy, t0, t1, cfg, t_anchor=t0)
        want = hs[tr]["xtrack_err_m"] / (hs[tr]["window_s"] / 60.0)
        rel1 = rv["cross_track_m_per_min"] / want - 1.0; ok &= abs(rel1) < TOL_X1
        # the corridor's position-growth form (eval/ukf_shadow_replay_check.py cross_E, re-referenced at the window
        # start), on the same XKF1 samples: (PE(t_end) - PE(t_start)) - (E_true(t_end) - E_true(t_start))
        w = (x[:, 0] >= t0) & (x[:, 0] <= t1); ta, tb = x[w, 0][0], x[w, 0][-1]
        growth = (pe[w, 0][-1] - pe[w, 0][0]) - (np.interp(tb, g[:, 0], g[:, 1]) - np.interp(ta, g[:, 0], g[:, 1]))
        want2 = growth / ((tb - ta) / 60.0)
        rel2 = rp["cross_track_m_per_min"] / want2 - 1.0; ok &= abs(rel2) < TOL_X2
        out["X1"][tr] = {"stored_xtrack_err_m": hs[tr]["xtrack_err_m"], "stored_window_s": hs[tr]["window_s"],
                         "stored_m_per_min": want,
                         "X1_velocity_variant_m_per_min": rv["cross_track_m_per_min"], "X1_rel_diff": rel1,
                         "X1_pass": bool(abs(rel1) < TOL_X1),
                         "X2_position_growth_m_per_min": want2, "X2_registered_rule_m_per_min": rp["cross_track_m_per_min"],
                         "X2_rel_diff": rel2, "X2_pass": bool(abs(rel2) < TOL_X2),
                         "info_int_VE_minus_dPE_m": rv["cross_track_m"] - rp["cross_track_m"],
                         "info_takeoff_anchor_at_window_start_m_per_min": ra.get("cross_track_m_per_min"),
                         "info_anchor_yaw_deg_enu": ra.get("anchor_yaw_deg_enu")}
    # H3 (information; no stored per-bag value with a stated window exists): EKF3's heading drift from XKF1@0 Yaw (the
    # bin path, read with df_reader) against SIM Yaw on the pinned window: inside METHODOLOGY's +6.6...+11.1 deg/min?
    out["H3"] = {}
    for tr in ("dsn_tex_r1", "dsn_tex_r2", "dsn_tex_r3"):
        x, g, gy, v = sim_enu(f"{TD}/trials/{tr}/ardupilot.bin")
        t0, t1 = wins[tr]["window_s"]
        r = RS.heading_drift(x[:, 0], x[:, 4], g[:, 0], gy, t0, t1)
        h = r["heading_drift_deg_per_min_ned"]
        out["H3"][tr] = {"ekf3_xkf1_ned_deg_per_min": h, "inside_6p6_11p1": bool(6.6 <= h <= 11.1)}
    out["all_pass"] = bool(ok)
    out["tolerances"] = {"heading_deg_per_min": TOL_H, "X1_relative": TOL_X1, "X2_relative": TOL_X2}
    json.dump(out, open(f"{HERE}/regression_secondary_2026-10-12.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
