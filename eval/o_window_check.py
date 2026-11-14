#!/usr/bin/env python3
"""Experiment 4 (O) window sensitivity, read-only from the STORED tracks (no replay, no flight). Ground truth, clock map,
markers, EKF3 track and the error definition exactly as eval/o_score.py; the script first checks it reproduces the
stored markers, source_set_changes and the three live indoor_rmse_m values of eval/results/expO/<trial>.json exactly.
Per trial:
  1. EKF3 live error at the GNSS OFF marker and at the OFF source-set change (nearest sample, as o_score's
     err_at_return_m);
  2. indoor RMSE of EKF3, UKF and FGO live over the pre-registered window [GNSS OFF, GNSS ON] and over
     [OFF source-set change, GNSS ON] (same window for all three live tracks), and the live max / min ratio (H-O2 / H4.2:
     PASS iff <= 1.5 in every flight) both ways; which live track is largest both ways.
Usage (venv-tags, under heavy.py): python3 eval/o_window_check.py [--json OUT]"""
import argparse, json, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = ("EKF3 live", "UKF live", "FGO live")
ts = get_typestore(Stores.ROS2_JAZZY); out = {}
for trial in ("O_r1", "O_r2", "O_r3b"):
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    stored = json.load(open(f"{REPO}/eval/results/expO/{trial}.json"))
    G, TR = [], []
    with Reader(f"{D}/bag") as rd:
        cs = {c.topic: c for c in rd.connections}
        for con, _, raw in rd.messages(connections=[cs["/ground_truth/pose"], cs["/imu/time_ref"]]):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/imu/time_ref":
                TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
            else:
                G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y))
    G, TR = np.array(G), np.array(TR)
    sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        w = (sitl >= lo) & (sitl < lo + 5)
        if w.sum() > 50:
            i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
    env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
    to_bag = lambda x: x + (kk * x + c0)
    mk = {}
    for ln in open(f"{D}/logs/fly_trial.log"):
        for key in ("GNSS OFF", "GNSS ON", "OUTBACK ALIGN START", "OUTBACK OUT START", "OUTBACK BACK START", "OUTBACK END"):
            m_ = re.search(key + r" (?:START )?t_sim=([\d.]+)", ln) if "START" not in key else re.search(key + r" t_sim=([\d.]+)", ln)
            if m_ and key not in mk: mk[key] = to_bag(float(m_[1]))
    assert {k: float(v) for k, v in mk.items()} == stored["markers_bag_s"]
    T_OFF, T_ON = mk["GNSS OFF"], mk["GNSS ON"]
    g = np.load(f"{D}/gnss.npz"); oE, oN = g["ekf3_origin_EN"]
    mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1, kfs = [], []
    while True:
        r = mv.recv_match(type=["XKF1", "XKFS"])
        if r is None: break
        if r.C != 0: continue
        t = to_bag(r.TimeUS / 1e6)
        if r.get_type() == "XKF1": k1.append((t, r.PE + oE, r.PN + oN))
        else: kfs.append((t, r.SS))
    ssc = [[float(kfs[i][0]), int(kfs[i][1])] for i in range(1, len(kfs)) if kfs[i][1] != kfs[i - 1][1]]
    assert ssc == stored["ekf3"]["source_set_changes"]
    T_SS = next(t for t, s in ssc if s == 1 and t > T_OFF)
    tracks = {"EKF3 live": np.array(k1), "UKF live": np.loadtxt(f"{D}/room_ukf/ukf_live.tum", ndmin=2)[:, :3],
              "FGO live": np.loadtxt(f"{D}/room_fgo/fgo_live.tum", ndmin=2)[:, :3]}
    err = {}
    for n_, T in tracks.items():
        err[n_] = (T[:, 0], np.hypot(T[:, 1] - np.interp(T[:, 0], G[:, 0], G[:, 1]), T[:, 2] - np.interp(T[:, 0], G[:, 0], G[:, 2])))
    R = {"t_off_marker_bag_s": T_OFF, "t_off_ss_change_bag_s": T_SS, "t_on_marker_bag_s": T_ON,
         "ss_change_minus_off_marker_s": T_SS - T_OFF, "checks": "PASS (markers, source_set_changes, 3 live indoor_rmse_m)"}
    t, e = err["EKF3 live"]
    i0 = int(np.argmin(np.abs(t - T_OFF))); i1 = int(np.argmin(np.abs(t - T_SS)))
    R["ekf3_err_at_off_marker_m"] = float(e[i0]); R["ekf3_err_at_off_marker_sample_dt_s"] = float(t[i0] - T_OFF)
    R["ekf3_err_at_off_ss_change_m"] = float(e[i1]); R["ekf3_err_at_off_ss_change_sample_dt_s"] = float(t[i1] - T_SS)
    for lab, lo in (("full", T_OFF), ("from_ss_change", T_SS)):
        rm = {}
        for n_ in LIVE:
            t, e = err[n_]; w = (t >= lo) & (t <= T_ON); rm[n_] = float(np.sqrt(np.mean(e[w] ** 2)))
            if lab == "full":
                assert rm[n_] == stored["tracks"][n_]["indoor_rmse_m"], (trial, n_)
        R[f"indoor_rmse_{lab}_m"] = rm
        R[f"live_max_over_min_{lab}"] = max(rm.values()) / min(rm.values())
        R[f"live_largest_{lab}"] = max(rm, key=rm.get)
        R[f"live_smallest_{lab}"] = min(rm, key=rm.get)
    out[trial] = R
    print(trial, json.dumps(R, indent=1))
summary = {}
for lab in ("full", "from_ss_change"):
    ratios = [out[t][f"live_max_over_min_{lab}"] for t in out]
    summary[lab] = {"ratio_min": min(ratios), "ratio_max": max(ratios), "H-O2_pass_every_flight_le_1.5": all(r <= 1.5 for r in ratios),
                    "ekf3_largest_every_flight": all(out[t][f"live_largest_{lab}"] == "EKF3 live" for t in out)}
out["summary"] = summary; print(json.dumps(summary, indent=1))
if a.json:
    os.makedirs(os.path.dirname(a.json), exist_ok=True); json.dump(out, open(a.json, "w"), indent=1)
