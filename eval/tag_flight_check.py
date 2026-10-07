#!/usr/bin/env python3
"""Experiment T: check flight analysis for a lap flight with the tag bridge (EKF3 in ExtNav mode). Reads the trial's
dataflash log (PARM, VISP, XKF1, XKF4, MSG), fly_trial.log (LAP markers, SITL clock), the tag bridge CSV and the bag
(/ground_truth/pose, /imu/time_ref, /tags/sent, /tags/raw).
  * clock map SITL -> Gazebo sim: /imu/time_ref lower envelope (as eval/ground_test_check.py, the D2/D20 method);
  * VISO_DELAY_MS basis: VISP receipt (TimeUS mapped to sim) - capture (RTimeUS, the sim capture stamp we sent);
    minimum, as the D2/D20 rule; also the bridge's own processing time (CSV proc_ms);
  * VISP: count, ignored (Ign), resets (Rst); MSG lines mentioning ExtNav/yaw/position;
  * EKF3 (XKF1, core 0) PN/PE/Yaw against GT in the world NED frame (N = world y, E = world x; no alignment);
    XKF4.SS horiz_pos_abs fraction in the lap window;
  * per leg: GT and EKF3 velocity along/across the leg (lateral-flow check on the E/W legs), GT yaw hold;
  * the lap window = first LEG START .. LAPS END (SITL clock), the pre-registered window rule for T.
Usage (venv-evo or venv-tags; needs pymavlink + rosbags): python3 eval/tag_flight_check.py TRIAL [--json OUT]"""
import argparse, json, math, os, re, sys
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
out = {"trial": a.trial}

# --- fly_trial markers (SITL clock, s) ---
legs, laps_end = [], None
for ln in open(f"{D}/logs/fly_trial.log"):
    m = re.search(r"LAP (\d+) LEG (\d+) START t_sim=([\d.]+)", ln)
    if m: legs.append((int(m[1]), int(m[2]), float(m[3])))
    m = re.search(r"LAPS END t_sim=([\d.]+)", ln)
    if m: laps_end = float(m[1])
out["lap_window_sitl_s"] = [legs[0][2], laps_end]

# --- dataflash ---
m = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); par = {}; visp = []; k1 = []; k4 = []; msgs = []
while True:
    r = m.recv_match(type=["PARM", "VISP", "XKF1", "XKF4", "MSG"])
    if r is None: break
    t = r.get_type()
    if t == "PARM": par[r.Name] = r.Value
    elif t == "VISP": visp.append((r.TimeUS, r.RTimeUS, r.PX, r.PY, r.Y, r.Ign, r.Rst, r.PErr, r.AErr))
    elif t == "XKF1" and r.C == 0: k1.append((r.TimeUS / 1e6, r.PN, r.PE, r.VN, r.VE, r.Yaw))
    elif t == "XKF4" and r.C == 0: k4.append((r.TimeUS / 1e6, r.SS))
    elif t == "MSG": msgs.append((r.TimeUS / 1e6, r.Message))
visp, k1, k4 = np.array(visp, float), np.array(k1), np.array(k4)
out["params"] = {k: par.get(k) for k in ("VISO_TYPE", "VISO_DELAY_MS", "VISO_POS_M_NSE", "VISO_YAW_M_NSE", "EK3_SRC1_POSXY",
                                          "EK3_SRC1_YAW", "EK3_SRC1_VELXY", "EK3_SRC1_POSZ", "ARMING_SKIPCHK", "AHRS_EKF_TYPE", "LOG_REPLAY", "LOG_DISARMED")}
out["msgs"] = [(round(t, 2), s) for t, s in msgs if re.search(r"ExtNav|yaw|EKF3 IMU0|position|origin", s, re.I)][:20]

# --- bag ---
ts = get_typestore(Stores.ROS2_JAZZY); G, TR, SENT, RAW = [], [], [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref", "/tags/sent", "/tags/raw") if x in cs]):
        mm = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((mm.time_ref.sec + mm.time_ref.nanosec * 1e-9, mm.header.stamp.sec + mm.header.stamp.nanosec * 1e-9)); continue
        t = mm.header.stamp.sec + mm.header.stamp.nanosec * 1e-9
        if con.topic == "/ground_truth/pose":
            q = mm.pose.orientation
            G.append((t, mm.pose.position.x, mm.pose.position.y, mm.pose.position.z, math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
        elif con.topic == "/tags/sent": SENT.append((t, int(mm.header.frame_id.split("_")[1])))
        else: RAW.append((t, int(mm.header.frame_id.split("_")[1])))
G, TR = np.array(G), np.array(TR)
out["bag_counts"] = {"tags_sent": len(SENT), "tags_raw": len(RAW), "sent_ids": sorted({i for _, i in SENT})}

# clock map (SITL -> sim), as ground_test_check.py
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_sim = lambda x: x + (kk * x + c0)
out["clock_map"] = {"offset_ms_at_start": 1e3 * float(kk * env[0, 0] + c0), "rate_ppm": 1e6 * float(kk),
                    "envelope_resid_ms_max": 1e3 * float(np.abs(env[:, 1] - (kk * env[:, 0] + c0)).max())}

# --- latency (VISO_DELAY_MS basis) ---
lat = 1e3 * (to_sim(visp[:, 0] / 1e6) - visp[:, 1] / 1e6)
proc = np.array([float(l.split(",")[-1]) for l in open(f"{D}/logs/tag_bridge.csv").readlines()[1:]])
def st(x): return {"min": float(np.min(x)), "p5": float(np.percentile(x, 5)), "median": float(np.median(x)),
                   "p95": float(np.percentile(x, 95)), "max": float(np.max(x)), "n": int(len(x))}
out["latency_visp_receipt_minus_capture_ms"] = st(lat)
out["bridge_proc_ms"] = st(proc)
import csv
rows = [r for r in csv.DictReader(open(f"{D}/logs/tag_bridge.csv")) if r.get("sent") == "1" and r.get("t_sim_sent") not in (None, "", "nan")]
if rows:   # (a) node measure: bridge sim clock at send - capture (excludes the loopback/serial transport)
    lat_a = np.array([1e3 * (float(r["t_sim_sent"]) - float(r["t_capture"])) for r in rows])
    out["latency_a_node_sent_minus_capture_ms"] = st(lat_a)
    out["latency_min_agree_within_5ms"] = bool(abs(lat_a.min() - lat.min()) <= 5.0)
out["VISO_DELAY_MS_by_rule"] = int(round(lat.min()))
out["visp"] = {"n": len(visp), "ignored": int((visp[:, 5] > 0).sum()), "resets": int(np.diff(visp[:, 6]).astype(bool).sum()),
               "PErr_median": float(np.median(visp[:, 7])), "AErr_median": float(np.median(visp[:, 8]))}

# --- EKF3 vs GT (world NED, no alignment), lap window ---
t0, t1 = legs[0][2], laps_end
gs = G[:, 0]
def gt_at(t_sitl, col): return np.interp(to_sim(t_sitl), gs, G[:, col])
w = (k1[:, 0] >= t0) & (k1[:, 0] <= t1); K = k1[w]
eN = K[:, 1] - gt_at(K[:, 0], 2); eE = K[:, 2] - gt_at(K[:, 0], 1)
yaw_gt_ned = 90.0 - np.degrees(gt_at(K[:, 0], 4))
eyaw = (K[:, 5] - yaw_gt_ned + 180) % 360 - 180
eh = np.hypot(eN, eE)
out["ekf3_lap"] = {"horiz_err_m": st(eh), "yaw_err_deg": st(np.abs(eyaw))}
SS = k4[(k4[:, 0] >= t0) & (k4[:, 0] <= t1), 1].astype(int)
out["ekf3_lap"]["horiz_pos_abs_frac"] = float(((SS >> 4) & 1).mean())      # nav_filter_status bit 4 = horiz_pos_abs
out["ekf3_lap"]["horiz_pos_rel_frac"] = float(((SS >> 3) & 1).mean())      # bit 3 = horiz_pos_rel

# --- per leg (central 60% of each leg, to skip the turn transients) ---
ends = [l[2] for l in legs[1:]] + [laps_end]; dirs = {0: (1, 0), 1: (0, 1), 2: (-1, 0), 3: (0, -1)}   # (N, E) unit
gt_vN = np.gradient(G[:, 2], gs); gt_vE = np.gradient(G[:, 1], gs)
out["legs"] = []
for (lap, leg, ts0), te in zip(legs, ends):
    a0, a1 = ts0 + 0.2 * (te - ts0), te - 0.2 * (te - ts0)
    u = np.array(dirs[leg]); perp = np.array([-u[1], u[0]])
    gw = (gs >= to_sim(a0)) & (gs <= to_sim(a1)); kw = (k1[:, 0] >= a0) & (k1[:, 0] <= a1)
    gv = np.c_[gt_vN[gw], gt_vE[gw]]; kv = k1[kw][:, 3:5]
    out["legs"].append({"lap": lap, "leg": leg, "dir_NE": list(map(int, u)),
                        "gt_along_mps": float(np.median(gv @ u)), "gt_across_mps": float(np.median(gv @ perp)),
                        "ekf3_along_mps": float(np.median(kv @ u)), "ekf3_across_mps": float(np.median(kv @ perp)),
                        "gt_yaw_enu_deg_range": [float(np.degrees(G[gw, 4]).min()), float(np.degrees(G[gw, 4]).max())],
                        "tags_sent_in_leg": int(sum(to_sim(a0) <= t <= to_sim(a1) for t, _ in SENT))})
print(json.dumps(out, indent=1))
if a.json: json.dump(out, open(a.json, "w"), indent=1)
