#!/usr/bin/env python3
"""Experiment H, S0b check flight (pre-registered checks, METHODOLOGY "Experiment H: pre-registration"):
  * VISO_DELAY_MS basis: min VISP receipt (SITL TimeUS -> bag clock by the /imu/time_ref lower envelope) - capture
    (RTimeUS, the sim capture stamp sent); and the node measure (CSV t_sim_sent - t_capture). D2/D20: the receipt
    measure; <= 60 ms required;
  * VISP count = /tags/sent count;
  * EKF3: 'yaw aligned' message at/after the first fix; XKF1 (PN, PE) in W after the first fix against GT in W
    (N_W = y - 4.998, E_W = x), i.e. the ExtNav position reset into the tag frame; flow fused (XKF5 innovations
    non-zero) through the occluded 5 s.
Usage (venv-tags): python3 eval/h_s0b_check.py TRIAL [--json OUT]"""
import argparse, csv, json, math, os
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
ts = get_typestore(Stores.ROS2_JAZZY); G, TR, SENT = [], [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref", "/tags/sent") if x in cs]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)); continue
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if con.topic == "/ground_truth/pose": G.append((t, m.pose.position.y - 4.998, m.pose.position.x))
        else: SENT.append(t)
G, TR = np.array(G), np.array(TR)
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1); to_bag = lambda x: x + (kk * x + c0)
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); visp, k1, f5, msgs = [], [], [], []
while True:
    r = mv.recv_match(type=["VISP", "XKF1", "XKF5", "MSG"])
    if r is None: break
    ty = r.get_type()
    if ty == "VISP": visp.append((to_bag(r.TimeUS / 1e6), r.RTimeUS / 1e6))
    elif ty == "MSG": msgs.append((to_bag(r.TimeUS / 1e6), r.Message))
    elif r.C == 0 and ty == "XKF1": k1.append((to_bag(r.TimeUS / 1e6), r.PN, r.PE))
    elif r.C == 0: f5.append((to_bag(r.TimeUS / 1e6), r.FIX, r.FIY))
visp, k1, f5 = np.array(visp), np.array(k1), np.array(f5)
lat_b = 1e3 * (visp[:, 0] - visp[:, 1])
rows = [r for r in csv.DictReader(open(f"{D}/logs/tag_bridge_fwd.csv")) if r["sent"] == "1" and r["t_sim_sent"] not in ("", "nan")]
lat_a = np.array([1e3 * (float(r["t_sim_sent"]) - float(r["t_capture"])) for r in rows])
st = lambda x: {"min": float(x.min()), "median": float(np.median(x)), "p95": float(np.percentile(x, 95))}
t_first = float(visp[0, 0])
w = k1[:, 0] > t_first + 1.0
err = np.hypot(k1[w, 1] - np.interp(k1[w, 0], G[:, 0], G[:, 1]), k1[w, 2] - np.interp(k1[w, 0], G[:, 0], G[:, 2]))
occ = [ln for ln in open(f"{D}/logs/fly_trial.log") if "OCCLUDER" in ln]
import re
ton, toff = (to_bag(float(re.search(r"t_sim=([\d.]+)", l)[1])) for l in occ[:2])
wf = (f5[:, 0] > ton) & (f5[:, 0] < toff)
out = {"trial": a.trial, "latency_receipt_ms": st(lat_b), "latency_node_ms": st(lat_a),
       "VISO_DELAY_MS_by_rule": int(round(lat_b.min())), "visp_n": int(len(visp)), "sent_n": len(SENT), "visp_eq_sent": len(visp) == len(SENT),
       "yaw_aligned_msgs": [(round(t, 2), s) for t, s in msgs if "yaw aligned" in s],
       "first_fix_t": t_first, "ekf3_W_err_after_first_fix_m": st(err),
       "flow_fused_during_occlusion_share": float(np.mean((f5[wf, 1] != 0) | (f5[wf, 2] != 0))) if wf.any() else None}
print(json.dumps(out, indent=1))
if a.json: json.dump(out, open(a.json, "w"), indent=1)
