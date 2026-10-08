#!/usr/bin/env python3
"""Experiment H, option (i) safety tests (H ruling 2026-10-08; METHODOLOGY "PRE-REGISTRATION (2026-10-08, before any
run): option (i) safety behaviour ..."). Scores S-A1..S-A4 for one H_safety_* trial.

  t_f    the failure instant: fly_trial.log 'KILL ... t_sim=' (first) or 'PARAM ... t_sim=' (SITL clock = dataflash TimeUS)
  S-A1   |ATT roll/pitch - GT| <= 3 deg and |ATT yaw - GT| <= 5 deg, from t_f to disarm (also reported before t_f)
  S-A2   the 'Thesis nav: ... position lost' text and the mode change to LAND: delay from t_f (bound given by --a2-bound)
  S-A3   disarmed <= 40 s after t_f; max GT tilt <= 15 deg; GT horizontal displacement t_f -> touchdown <= 1.5 m;
         GT vertical speed at touchdown <= 1.0 m/s; no watcher BREACH
  S-A4   (b runs) S-A1..S-A3 and a single landing: one entry to LAND after t_f, no re-arm after the disarm
GT (bag, ENU/FLU, bag clock) -> NED/FRD in the tag frame W (N = world y - 4.998, E = world x); bag clock -> SITL clock by
the /imu/time_ref lower envelope (as eval/h_score.py).
Usage (venv-tags): python3 eval/h_safety_score.py TRIAL --a2-bound S [--json OUT]"""
import argparse, json, math, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
from scipy.spatial.transform import Rotation as Rot

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--a2-bound", type=float, required=True)
ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); CL = os.path.expanduser(f"~/thesis_data/closed_loop/{a.trial}")
wrapd = lambda x: (x + 180.0) % 360.0 - 180.0
ts = get_typestore(Stores.ROS2_JAZZY); G, TR = [], []
A = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1.0]]); B = np.diag([1.0, -1.0, -1.0])     # ENU->NED, FLU->FRD
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref") if x in cs]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)); continue
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9; p, q = m.pose.position, m.pose.orientation
        R = A @ Rot.from_quat([q.x, q.y, q.z, q.w]).as_matrix() @ B
        yaw, pitch, roll = Rot.from_matrix(R).as_euler("ZYX", degrees=True)
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2]))))
        G.append((t, p.y - 4.998, p.x, p.z, roll, pitch, yaw, tilt))
G, TR = np.array(G), np.array(TR)
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
G[:, 0] = np.array([tb - (kk * tb + c0) for tb in G[:, 0]])          # bag -> SITL (offset varies slowly; one pass)
log = open(f"{D}/logs/fly_trial.log").read()
mf = re.search(r"(KILL|PARAM) .*?t_sim=([\d.]+)", log)
t_f = float(mf[2]); kind = mf[1]
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); att, modes, msgs, arm = [], [], [], []
while True:
    r = mv.recv_match(type=["ATT", "MODE", "MSG", "ARM"])
    if r is None: break
    t = r.TimeUS / 1e6; ty = r.get_type()
    if ty == "ATT": att.append((t, r.Roll, r.Pitch, r.Yaw))
    elif ty == "MODE": modes.append((t, int(r.ModeNum), int(r.Rsn)))
    elif ty == "MSG": msgs.append((t, r.Message))
    else: arm.append((t, int(r.ArmState)))
att = np.array(att)
t_dis = next((t for t, s in arm if t > t_f and s == 0), None)
t_end = t_dis if t_dis is not None else att[-1, 0]
gi = lambda t, c: np.interp(t, G[:, 0], G[:, c])
def att_err(t0, t1):
    w = (att[:, 0] >= t0) & (att[:, 0] <= t1)
    er = np.abs(att[w, 1] - gi(att[w, 0], 4)); ep = np.abs(att[w, 2] - gi(att[w, 0], 5))
    ey = np.abs(wrapd(att[w, 3] - gi(att[w, 0], 6)))
    return {"n": int(w.sum()), "roll_max_deg": float(er.max()), "pitch_max_deg": float(ep.max()), "yaw_max_deg": float(ey.max())}
out = {"trial": a.trial, "failure": kind, "t_f": t_f, "t_disarm": t_dis}
out["attitude_err_before_failure_10s"] = att_err(t_f - 10, t_f)
e1 = att_err(t_f, t_end); out["S-A1"] = dict(e1, PASS=bool(max(e1["roll_max_deg"], e1["pitch_max_deg"]) <= 3.0 and e1["yaw_max_deg"] <= 5.0))
t_txt = next((t for t, s in msgs if t >= t_f and "Thesis nav" in s), None)
lands = [(t, rs) for t, mn, rs in modes if t >= t_f and mn == 9]
t_land = lands[0][0] if lands else None
out["S-A2"] = {"text_delay_s": (t_txt - t_f) if t_txt else None, "land_delay_s": (t_land - t_f) if t_land else None,
               "land_reason": lands[0][1] if lands else None, "bound_s": a.a2_bound,
               "fc_text": next((s for t, s in msgs if t >= t_f and "Thesis nav" in s), None),
               "PASS": bool(t_txt is not None and t_land is not None and t_txt - t_f <= a.a2_bound and t_land - t_f <= a.a2_bound)}
w = (G[:, 0] >= t_f) & (G[:, 0] <= t_end); Gw = G[w]
td_i = next((i for i in range(len(Gw)) if Gw[i, 3] < 0.25), None)
if td_i is not None:
    t_td = Gw[td_i, 0]; wv = (G[:, 0] >= t_td - 0.25) & (G[:, 0] <= t_td)
    vz = float(np.polyfit(G[wv, 0], G[wv, 3], 1)[0]) if wv.sum() > 3 else None
    disp = float(math.hypot(Gw[td_i, 1] - gi(t_f, 1), Gw[td_i, 2] - gi(t_f, 2)))
else:
    t_td = vz = disp = None
breach = os.path.exists(f"{CL}/BREACH.txt")
a3 = {"disarm_delay_s": (t_dis - t_f) if t_dis else None, "max_tilt_deg": float(Gw[:, 7].max()),
      "touchdown_t": t_td, "horiz_disp_m": disp, "touchdown_vz_m_s": vz, "breach": breach}
a3["PASS"] = bool(t_dis is not None and t_dis - t_f <= 40 and a3["max_tilt_deg"] <= 15 and disp is not None and disp <= 1.5
                  and vz is not None and abs(vz) <= 1.0 and not breach)
out["S-A3"] = a3
rearm = any(t > t_dis and s == 1 for t, s in arm) if t_dis else None
out["S-A4_single_landing"] = {"n_land_entries_after_t_f": len(lands), "rearmed_after_disarm": rearm,
                              "PASS": bool(len(lands) >= 1 and rearm is False and out["S-A1"]["PASS"] and a3["PASS"])}
out["modes_after_t_f"] = [(round(t - t_f, 3), mn, rs) for t, mn, rs in modes if t >= t_f]
out["msgs_after_t_f"] = [(round(t - t_f, 3), s) for t, s in msgs if t >= t_f][:30]
print(json.dumps(out, indent=1))
if a.json: json.dump(out, open(a.json, "w"), indent=1)
