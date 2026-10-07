#!/usr/bin/env python3
"""Experiment O scorer (pre-registered in METHODOLOGY "Experiment O: pre-registration"). Absolute world frame, NO
alignment. For one trial:
  * tracks: EKF3 live (XKF1 core 0 PN/PE about EKF3's origin = the GPS sample at the XKFS.GPS_GTA rising edge, from
    eval/extract_gnss.py; SITL clock mapped to the bag clock); UKF live, RTS-UKF (room_ukf/), FGO live, FGO hindsight
    (whole-flight batch) (room_fgo/); ground truth from the bag;
  * indoor segment: 'GNSS OFF' to 'GNSS ON' (fly_trial.log, SITL clock, mapped);
  * per track: indoor horizontal error RMSE / max; error at GNSS return (at the GNSS ON instant); the largest
    position step between consecutive samples in [ON, ON + 10 s] minus the largest step in the 10 s before OFF (the
    "jump"; EKF3's resets show here); error 10 s after ON;
  * EKF3 log facts: active source set (XKFS.SS) transitions, posTimeout (XKF4.TS bit 0) during the indoor segment, the
    last reset delta (XKF4.OFN/OFE) after ON.
Usage (venv-tags): python3 eval/o_score.py TRIAL [--json OUT]"""
import argparse, json, math, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
ts = get_typestore(Stores.ROS2_JAZZY); G, TR = [], []
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
T_OFF, T_ON = mk["GNSS OFF"], mk["GNSS ON"]

g = np.load(f"{D}/gnss.npz"); oE, oN = g["ekf3_origin_EN"]
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1, k4, kfs = [], [], []
while True:
    r = mv.recv_match(type=["XKF1", "XKF4", "XKFS"])
    if r is None: break
    if r.C != 0: continue
    ty = r.get_type(); t = to_bag(r.TimeUS / 1e6)
    if ty == "XKF1": k1.append((t, r.PE + oE, r.PN + oN))
    elif ty == "XKF4": k4.append((t, int(r.TS) & 1, r.OFN, r.OFE, (int(r.SS) >> 13) & 1))   # SS bit 13 = using_gps
    else: kfs.append((t, r.SS))
tracks = {"EKF3 live": np.array(k1)}
for name, p in (("UKF live", "room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", "room_ukf/ukf_rts.tum"), ("RTS-UKF (hindsight, cap-free forward pass)", "room_ukf_rtsnocap/ukf_rts.tum"),
                ("FGO live", "room_fgo/fgo_live.tum"), ("FGO hindsight (whole-flight batch)", "room_fgo/fgo_batch.tum")):
    if os.path.exists(f"{D}/{p}"):
        x = np.loadtxt(f"{D}/{p}", ndmin=2); tracks[name] = x[:, :3]


def herr(T):
    return np.hypot(T[:, 1] - np.interp(T[:, 0], G[:, 0], G[:, 1]), T[:, 2] - np.interp(T[:, 0], G[:, 0], G[:, 2]))


out = {"trial": a.trial, "markers_bag_s": {k: float(v) for k, v in mk.items()}, "indoor_s": T_ON - T_OFF, "tracks": {}}
for n_, T in tracks.items():
    e = herr(T); w = (T[:, 0] >= T_OFF) & (T[:, 0] <= T_ON)
    i_on = np.argmin(np.abs(T[:, 0] - T_ON)); i_10 = np.argmin(np.abs(T[:, 0] - (T_ON + 10)))
    step = np.hypot(np.diff(T[:, 1]), np.diff(T[:, 2])); ts_ = T[1:, 0]
    after = (ts_ > T_ON) & (ts_ <= T_ON + 10); before = (ts_ > T_OFF - 10) & (ts_ <= T_OFF)
    out["tracks"][n_] = {"indoor_rmse_m": float(np.sqrt(np.mean(e[w] ** 2))), "indoor_max_m": float(e[w].max()),
                         "err_at_return_m": float(e[i_on]), "err_10s_after_return_m": float(e[i_10]),
                         "max_step_after_return_m": float(step[after].max()) if after.any() else None,
                         "max_step_before_off_m": float(step[before].max()) if before.any() else None}
k4 = np.array(k4); kfs = np.array(kfs)
wi = (k4[:, 0] >= T_OFF) & (k4[:, 0] <= T_ON)
ss_changes = [(float(kfs[i, 0]), int(kfs[i, 1])) for i in range(1, len(kfs)) if kfs[i, 1] != kfs[i - 1, 1]]
wa = (k4[:, 0] > T_ON) & (k4[:, 0] < T_ON + 10)
out["ekf3"] = {"source_set_changes": ss_changes, "posTimeout_frac_indoor": float(k4[wi, 1].mean()),
               "last_reset_delta_after_return_NE_m": [float(k4[wa, 2][-1]), float(k4[wa, 3][-1])] if wa.any() else None,
               "origin_EN": [float(oE), float(oN)]}
# ---- gates (pre-registered G1-G4) ----
need = ("OUTBACK ALIGN START", "OUTBACK OUT START", "OUTBACK BACK START", "OUTBACK END", "GNSS OFF", "GNSS ON")
n_off = sum("GNSS OFF" in l for l in open(f"{D}/logs/fly_trial.log")); n_on = sum("GNSS ON" in l for l in open(f"{D}/logs/fly_trial.log"))
fl = [c for c in ss_changes if c[0] > mk["OUTBACK ALIGN START"]]
wb = (k4[:, 0] > T_OFF - 5) & (k4[:, 0] < T_OFF)
gates = {"G1": all(k in mk for k in need) and n_off == 1 and n_on == 1,
         "G2": bool([c[1] for c in fl] == [1, 0] and fl[0][0] > T_OFF and fl[1][0] > T_ON),
         "G3_using_gps_5s_before_off": float(k4[wb, 4].mean()) if wb.any() else 0.0}
gates["G3"] = gates["G3_using_gps_5s_before_off"] == 1.0
for nm in ("room_ukf", "room_fgo"):
    st = json.load(open(f"{D}/{nm}/stats.json"))
    gates[f"G4_{nm}"] = bool(st["t_anchor"] is not None and st["t_anchor"] < T_OFF and st.get("n_gnss_fused", st.get("n_gnss_factors", 0)) > 0)
gates["PASS"] = all(gates[k] for k in ("G1", "G2", "G3", "G4_room_ukf", "G4_room_fgo"))
out["gates"] = gates; print("gates:", gates)
for n_, s_ in out["tracks"].items():
    print(f"{n_:36s} indoor RMSE {s_['indoor_rmse_m']:.2f} max {s_['indoor_max_m']:.2f} | at return {s_['err_at_return_m']:.2f} "
          f"+10 s {s_['err_10s_after_return_m']:.2f} | max step after return {s_['max_step_after_return_m']} m")
print("EKF3:", out["ekf3"])
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
