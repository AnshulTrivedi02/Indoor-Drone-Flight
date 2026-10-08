#!/usr/bin/env python3
"""Experiment H, far-spawn SITL ground tests (pre-registered 2026-10-08 item 3; docs/h_backends_tag_input.md section 5
with the far-spawn changes). For H_gt_ukf_far (UKF flying) or H_gt_fgo_far (C++ FGO flying):
  anchor BEFORE arming   UKF: the 'UKF tag re-anchor' text; FGO: the node's 'ANCHORED' log line and its first valid XFGI
                         state (in W) - both before the ARM record; EKF3 'using external nav data' before ARM too
  reported reset         UKF: the text's dN/dyaw (~ -3.9 m expected); FGO: none expected (anchored before its first state)
  wait_fix               fly_trial 'WAIT_FIX ok at N .. E ..' within 0.5 m of W(-3.9, 0)
  F1                     pre-arm VALID fixes (/tags/sent) against GT: horizontal p95 <= 0.10 m, yaw p95 <= 2 deg
  G6 hold                the flying estimator (ATT/XUKO or XFGO in W) against GT over the 60 s hold (from +5 s):
                         horizontal mean <= 0.05 m, |yaw| p95 <= 1 deg
  FGO timing             XFGO.OV = 1 and Age <= 250 ms from arming to landing (no wrapped ages)
Usage (venv-tags): python3 eval/h_gt_far_score.py TRIAL [--json OUT]"""
import argparse, json, math, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); TAGY = 4.998
ts = get_typestore(Stores.ROS2_JAZZY); G, TR, F = [], [], []
yaw_q = lambda q: math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref", "/tags/sent")]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)); continue
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if con.topic == "/ground_truth/pose":
            G.append((t, m.pose.position.y - TAGY, m.pose.position.x, yaw_q(m.pose.orientation)))
        else:
            F.append((t, m.pose.pose.position.y, m.pose.pose.position.x, yaw_q(m.pose.pose.orientation)))
G, TR, F = np.array(G), np.array(TR), np.array(F)
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_sitl = lambda tb: tb - (kk * tb + c0)
G[:, 0] = to_sitl(G[:, 0]); F[:, 0] = to_sitl(F[:, 0])
gi = lambda t, c: np.interp(t, G[:, 0], G[:, c])
wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); msgs, arm, ekt, xfgo, xfgi, est_rows = [], [], None, [], [], []
while True:
    r = mv.recv_match(type=["MSG", "ARM", "PARM", "XFGO", "XFGI", "XUKO"])
    if r is None: break
    ty = r.get_type(); t = r.TimeUS / 1e6
    if ty == "PARM":
        if r.Name == "AHRS_EKF_TYPE": ekt = int(r.Value)
    elif ty == "MSG": msgs.append((t, r.Message))
    elif ty == "ARM": arm.append((t, int(r.ArmState)))
    elif ty == "XFGO": xfgo.append((t, int(r.OV), int(r.Age), r.PN, r.PE, math.radians(r.Yaw)))
    elif ty == "XFGI": xfgi.append((t, int(r.V), r.PN, r.PE))
    else: est_rows.append((t, r.PN, r.PE, math.radians(r.Yaw)))
est = {12: "UKF", 13: "FGO"}[ekt]
t_arm = next(t for t, s in arm if s == 1); t_disarm = next((t for t, s in arm if s == 0 and t > t_arm), None)
out = {"trial": a.trial, "flying": est, "t_arm": t_arm, "t_disarm": t_disarm}
t_ekf = next((t for t, s in msgs if "IMU0 is using external nav data" in s), None)
out["EKF3_extnav_before_arm"] = bool(t_ekf is not None and t_ekf < t_arm)
if est == "UKF":
    ua = next(((t, s) for t, s in msgs if "UKF tag re-anchor" in s), None)
    out["anchor"] = {"t": ua[0] if ua else None, "text": ua[1] if ua else None, "before_arm": bool(ua and ua[0] < t_arm),
                     "n_anchor_texts": sum("UKF tag re-anchor" in s for _, s in msgs)}
else:
    nl = open(f"{D}/logs/fgo_node_restart.log" if os.path.exists(f"{D}/logs/fgo_node_restart.log") else f"{D}/logs/fgo_node.log").read()
    v = [(t, pn, pe) for t, vv, pn, pe in xfgi if vv == 1]
    out["anchor"] = {"node_logged_ANCHORED": "ANCHORED" in nl, "first_valid_XFGI": v[0] if v else None,
                     "first_valid_before_arm": bool(v and v[0][0] < t_arm),
                     "first_valid_in_W": bool(v and abs(v[0][1] - (-3.9)) < 0.5), "n_XFGR_in_flight": None}
    w = [(t, ov, age) for t, ov, age, *_ in xfgo if t_arm <= t <= (t_disarm or 1e9)]
    out["fgo_timing"] = {"n": len(w), "OV0_share": float(np.mean([ov == 0 for _, ov, _ in w])),
                         "age_max_ms": int(max(age for _, _, age in w)), "PASS": bool(all(ov == 1 for _, ov, _ in w) and max(age for _, _, age in w) <= 250)}
    est_rows = [(t, pn, pe, y) for t, ov, age, pn, pe, y in xfgo]
log = open(f"{D}/logs/fly_trial.log").read()
m = re.search(r"WAIT_FIX ok at N ([-\d.]+) E ([-\d.]+)", log)
out["wait_fix"] = {"N": float(m[1]), "E": float(m[2]), "PASS": bool(math.hypot(float(m[1]) + 3.9, float(m[2])) <= 0.5)} if m else None
pre = F[:, 0] < t_arm
eh = np.hypot(F[pre, 1] - gi(F[pre, 0], 1), F[pre, 2] - gi(F[pre, 0], 2))
ey = np.degrees(np.abs(wrap(F[pre, 3] - gi(F[pre, 0], 3))))
out["F1"] = {"n": int(pre.sum()), "horiz_p95_m": float(np.percentile(eh, 95)), "yaw_p95_deg": float(np.percentile(ey, 95)),
             "PASS": bool(np.percentile(eh, 95) <= 0.10 and np.percentile(ey, 95) <= 2.0)}
hs = re.search(r"HSEG 2 hold START t_sim=([\d.]+)", log); he = re.search(r"HPROFILE END t_sim=([\d.]+)", log)
E = np.array(est_rows)
if hs and he:
    w = (E[:, 0] >= float(hs[1]) + 5) & (E[:, 0] <= float(he[1]))
    eh = np.hypot(E[w, 1] - gi(E[w, 0], 1), E[w, 2] - gi(E[w, 0], 2))
    gyaw_ned = np.pi / 2 - gi(E[w, 0], 3)          # GT ENU yaw -> NED yaw
    ey = np.degrees(np.abs(wrap(E[w, 3] - gyaw_ned)))
    out["G6_hold"] = {"n": int(w.sum()), "horiz_mean_m": float(eh.mean()), "horiz_max_m": float(eh.max()), "yaw_p95_deg": float(np.percentile(ey, 95)),
                      "PASS": bool(eh.mean() <= 0.05 and np.percentile(ey, 95) <= 1.0)}
print(json.dumps(out, indent=1, default=float))
if a.json: json.dump(out, open(a.json, "w"), indent=1, default=float)
