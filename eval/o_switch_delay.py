#!/usr/bin/env python3
"""Experiment 4 (O): the delay between each GNSS marker (OFF/ON) and EKF3's source-set change. Read-only, stored data
only (dataflash, fly_trial.log, bag for ground truth and the clock map, eval/results/expO/<trial>.json); no replay.
Clock map, markers and EKF3 track exactly as eval/o_score.py; the script checks the markers and the stored
source_set_changes reproduce eval/results/expO/<trial>.json exactly before reporting.
Per trial, on the SITL clock (dataflash TimeUS) and mapped to the bag clock:
  * the harness markers (fly_trial.log t_sim, AP_HAL::millis via MAVLink);
  * the PARM record of SIM_GPS1_ENABLE (logged when the parameter is set);
  * the first GPS[0] sample whose Status changes (below 3 = no 3D fix);
  * the Lua script's MSG texts ("O-switch: ...") and EV 85/86 (EK3_SOURCES_SET_TO_PRIMARY/SECONDARY);
  * XKFS.SS changes (core 0);
  * EKF3 horizontal error (o_score definition) from GNSS ON to the source-set change: at ON, just before and just after
    the change, and a straight-line rate fitted over [ON, change).
Usage (venv-tags, under heavy.py): python3 eval/o_switch_delay.py [--json OUT]"""
import argparse, json, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    mk_sitl = {}
    for ln in open(f"{D}/logs/fly_trial.log"):
        for key in ("GNSS OFF", "GNSS ON", "OUTBACK ALIGN START", "OUTBACK OUT START", "OUTBACK BACK START", "OUTBACK END"):
            m_ = re.search(key + r" (?:START )?t_sim=([\d.]+)", ln) if "START" not in key else re.search(key + r" t_sim=([\d.]+)", ln)
            if m_ and key not in mk_sitl: mk_sitl[key] = float(m_[1])
    mk = {k: to_bag(v) for k, v in mk_sitl.items()}
    assert {k: float(v) for k, v in mk.items()} == stored["markers_bag_s"]
    g = np.load(f"{D}/gnss.npz"); oE, oN = g["ekf3_origin_EN"]
    mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
    k1, kfs, parm, gps, ev, msg, k4 = [], [], [], [], [], [], []
    while True:
        r = mv.recv_match(type=["XKF1", "XKFS", "PARM", "GPS", "EV", "MSG", "XKF4"])
        if r is None: break
        ty = r.get_type(); tu = r.TimeUS / 1e6
        if ty in ("XKF1", "XKFS", "XKF4") and r.C != 0: continue
        if ty == "XKF1": k1.append((to_bag(tu), r.PE + oE, r.PN + oN, tu))
        elif ty == "XKFS": kfs.append((to_bag(tu), r.SS, tu))
        elif ty == "XKF4": k4.append((tu, r.OFN, r.OFE))
        elif ty == "PARM" and r.Name == "SIM_GPS1_ENABLE": parm.append((tu, float(r.Value)))
        elif ty == "GPS" and getattr(r, "I", 0) == 0: gps.append((tu, int(r.Status)))
        elif ty == "EV" and r.Id in (85, 86): ev.append((tu, int(r.Id)))
        elif ty == "MSG" and "O-switch" in r.Message: msg.append((tu, r.Message))
    k1 = np.array(k1)
    ssc = [(float(kfs[i][0]), int(kfs[i][1])) for i in range(1, len(kfs)) if kfs[i][1] != kfs[i - 1][1]]
    assert [list(x) for x in ssc] == stored["ekf3"]["source_set_changes"], "source-set changes differ from stored"
    ssc_sitl = [(float(kfs[i][2]), int(kfs[i][1])) for i in range(1, len(kfs)) if kfs[i][1] != kfs[i - 1][1]]
    gch = [(gps[i][0], gps[i - 1][1], gps[i][1]) for i in range(1, len(gps)) if gps[i][1] != gps[i - 1][1]]
    R = {"clock_map": {"rate_kk": float(kk), "offset_c0_s": float(c0), "note": "bag = sitl + kk*sitl + c0 (o_score.py)"},
         "markers_sitl_s": mk_sitl, "markers_bag_s": stored["markers_bag_s"],
         "parm_SIM_GPS1_ENABLE_sitl_s": parm, "gps0_status_changes_sitl_s": gch,
         "lua_msgs_sitl_s": msg, "ev_85_86_sitl_s": ev, "xkfs_ss_changes_sitl_s": ssc_sitl,
         "xkfs_ss_changes_bag_s_stored": stored["ekf3"]["source_set_changes"], "checks": "PASS (markers, source_set_changes)"}
    # delays per switch (SITL clock and bag clock)
    R["delays"] = {}
    for lab, mkey, to_set in (("OFF", "GNSS OFF", 1), ("ON", "GNSS ON", 0)):
        t_ss_sitl = next(t for t, s in ssc_sitl if s == to_set and t > mk_sitl[mkey] - 1)
        t_ss_bag = next(t for t, s in ssc if s == to_set and t > mk[mkey] - 1)
        t_parm = next(t for t, v in parm if v == (1.0 if lab == "ON" else 0.0) and t > mk_sitl[mkey] - 5)
        t_gps = next(t for t, s0, s1 in gch if t > t_parm and ((s1 < 3) if lab == "OFF" else (s1 >= 3)))
        t_ev = next(t for t, i in ev if i == (86 if lab == "OFF" else 85) and t > t_parm)
        R["delays"][lab] = {"marker_sitl_s": mk_sitl[mkey], "parm_set_sitl_s": t_parm, "gps_status_change_sitl_s": t_gps,
                            "ev_sitl_s": t_ev, "ss_change_sitl_s": t_ss_sitl,
                            "ss_minus_marker_sitl_s": t_ss_sitl - mk_sitl[mkey], "ss_minus_marker_bag_s": t_ss_bag - mk[mkey],
                            "ss_minus_parm_sitl_s": t_ss_sitl - t_parm, "ss_minus_gps_status_sitl_s": t_ss_sitl - t_gps,
                            "marker_minus_parm_sitl_s": mk_sitl[mkey] - t_parm, "gps_status_minus_parm_sitl_s": t_gps - t_parm,
                            "bag_over_sitl_delay_ratio": (t_ss_bag - mk[mkey]) / (t_ss_sitl - mk_sitl[mkey])}
    # EKF3 error between ON and the source-set change
    T_ON = mk["GNSS ON"]; t_sw = R["delays"]["ON"]["ss_change_sitl_s"]; t_sw_bag = to_bag(t_sw)
    e = np.hypot(k1[:, 1] - np.interp(k1[:, 0], G[:, 0], G[:, 1]), k1[:, 2] - np.interp(k1[:, 0], G[:, 0], G[:, 2]))
    i_on = int(np.argmin(np.abs(k1[:, 0] - T_ON)))
    assert float(e[i_on]) == stored["tracks"]["EKF3 live"]["err_at_return_m"]
    w = (k1[:, 0] >= T_ON) & (k1[:, 0] < t_sw_bag)
    ib = int(np.flatnonzero(k1[:, 0] < t_sw_bag)[-1]); ia = int(np.flatnonzero(k1[:, 0] >= t_sw_bag)[0])
    slope, icpt = np.polyfit(k1[w, 0] - T_ON, e[w], 1)
    R["ekf3_err_on_to_switch"] = {"err_at_on_m": float(e[i_on]), "t_on_sample_since_on_s": float(k1[i_on, 0] - T_ON),
                                  "err_last_before_switch_m": float(e[ib]), "t_last_before_since_on_s": float(k1[ib, 0] - T_ON),
                                  "err_first_after_switch_m": float(e[ia]), "t_first_after_since_on_s": float(k1[ia, 0] - T_ON),
                                  "fit_rate_m_per_s": float(slope), "fit_intercept_m": float(icpt), "n_samples": int(w.sum()),
                                  "err_max_in_window_m": float(e[w].max()), "err_min_in_window_m": float(e[w].min()),
                                  "err_10s_after_on_m_stored": stored["tracks"]["EKF3 live"]["err_10s_after_return_m"],
                                  "max_step_after_return_m_stored": stored["tracks"]["EKF3 live"]["max_step_after_return_m"]}
    rs = [(t, n_, e_) for t, n_, e_ in k4 if t_sw - 0.5 <= t <= t_sw + 1.0]
    R["xkf4_reset_offsets_near_switch_sitl"] = [rs[0], rs[-1]] if rs else None
    out[trial] = R
    print(trial, json.dumps(R, indent=1, default=float))
if a.json:
    os.makedirs(os.path.dirname(a.json), exist_ok=True); json.dump(out, open(a.json, "w"), indent=1, default=float)
