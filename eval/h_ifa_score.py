#!/usr/bin/env python3
"""Experiment H, in-flight-anchor transient check (pre-registered 2026-10-08, amended 2026-10-09; METHODOLOGY).
The anchor instant t_a = the FLYING estimator's own anchor record in the dataflash log:
  EKF3 (AHRS type 3): the first 'EKF3 IMU0 is using external nav data' text; UKF (12): 'UKF tag re-anchor';
  FGO (13): the first XFGR row (the FC's reset report on the node's reset_counter change).
Bound, over [t_a, t_a + 5 s] against GT: max tilt <= 10 deg; max horizontal displacement from the GT position at t_a
<= 0.30 m; max |yaw - yaw(t_a)| <= 5 deg. Also reported: the same over [t_a - 5, t_a] (the pre-anchor reference) and
the reported reset (dN, dE, dyaw) where the log has it.
GT bag clock -> SITL clock by the /imu/time_ref lower envelope (as eval/h_safety_score.py).
Usage (venv-tags): python3 eval/h_ifa_score.py TRIAL [--json OUT]"""
import argparse, json, math, os
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
from scipy.spatial.transform import Rotation as Rot

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
ts = get_typestore(Stores.ROS2_JAZZY); G, TR = [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref")]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)); continue
        p, q = m.pose.position, m.pose.orientation
        R = Rot.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
        G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, p.x, p.y, p.z,
                  math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2])))), math.degrees(math.atan2(R[1, 0], R[0, 0]))))
G, TR = np.array(G), np.array(TR)
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
G[:, 0] = G[:, 0] - (kk * G[:, 0] + c0)
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); msgs, xfgr, ekf_type = [], [], None
while True:
    r = mv.recv_match(type=["MSG", "XFGR", "PARM"])
    if r is None: break
    if r.get_type() == "PARM":
        if r.Name == "AHRS_EKF_TYPE": ekf_type = int(r.Value)
    elif r.get_type() == "MSG": msgs.append((r.TimeUS / 1e6, r.Message))
    else: xfgr.append((r.TimeUS / 1e6, r.DN, r.DE, r.DY))
est = {3: "EKF3", 12: "UKF", 13: "FGO"}[ekf_type]
if est == "EKF3": t_a = next(t for t, s in msgs if "IMU0 is using external nav data" in s); reset = None
elif est == "UKF":
    t_a, s_ = next((t, s) for t, s in msgs if "UKF tag re-anchor" in s); reset = s_
else:
    t_a, dn, de, dy = xfgr[0]; reset = {"dN": dn, "dE": de, "dyaw_deg": dy}
wrapd = lambda x: (x + 180.0) % 360.0 - 180.0
def win(t0, t1, tref):
    w = (G[:, 0] >= t0) & (G[:, 0] <= t1); g = G[w]
    i = np.argmin(np.abs(G[:, 0] - tref)); x0, y0, yaw0 = G[i, 1], G[i, 2], G[i, 5]
    return {"max_tilt_deg": float(g[:, 4].max()), "max_disp_m": float(np.hypot(g[:, 1] - x0, g[:, 2] - y0).max()),
            "max_yaw_change_deg": float(np.abs(wrapd(g[:, 5] - yaw0)).max()), "z_mean_m": float(g[:, 3].mean())}
after = win(t_a, t_a + 5.0, t_a); before = win(t_a - 5.0, t_a, t_a - 5.0)
out = {"trial": a.trial, "flying": est, "t_anchor": t_a, "reported_reset": reset, "after_5s": after, "before_5s_reference": before,
       "PASS": bool(after["max_tilt_deg"] <= 10 and after["max_disp_m"] <= 0.30 and after["max_yaw_change_deg"] <= 5)}
print(json.dumps(out, indent=1))
if a.json: json.dump(out, open(a.json, "w"), indent=1)
