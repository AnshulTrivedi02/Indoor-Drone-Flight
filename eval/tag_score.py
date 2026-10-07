#!/usr/bin/env python3
"""Experiment T scorer (pre-registered in METHODOLOGY "Experiment T: pre-registration"). Absolute world frame, NO
alignment. For one trial:
  * tracks: EKF3 live (dataflash XKF1 core 0: E = PE, N = PN, on the SITL clock mapped to the bag clock by the
    /imu/time_ref lower envelope, as eval/ground_test_check.py); UKF live and RTS-UKF (room_ukf/); FGO live and
    "FGO hindsight (whole-flight batch)" (room_fgo/); ground truth from the bag;
  * lap window: first 'LAP 0 LEG 0 START' to 'LAPS END' (fly_trial.log, SITL clock, mapped);
  * per track: horizontal error |p - p_gt| (m) at the track's own samples in the window: RMSE, median, p95, max;
    yaw error |wrap(yaw - yaw_gt)| (deg) median, p95;
  * gaps: the intervals between consecutive /tags/sent fixes inside the window that are >= GAP_MIN_S long (the
    no-fix stretches); per gap and track: mean and max horizontal error over the gap interior. Gap length = the
    interval. The hindsight improvement of a gap = (live mean error - hindsight mean error), FGO and UKF.
Usage (venv-evo with the pymavlink shim, or venv-tags): python3 eval/tag_score.py TRIAL [--json OUT]"""
import argparse, json, math, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

GAP_MIN_S = 1.0
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")


def wrap(x):
    return (x + np.pi) % (2 * np.pi) - np.pi


# ---- bag: GT, /imu/time_ref, /tags/sent ----
ts = get_typestore(Stores.ROS2_JAZZY); G, TR, SENT, SENTV = [], [], [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref", "/tags/sent") if x in cs]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)); continue
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if con.topic == "/ground_truth/pose":
            q = m.pose.orientation
            G.append((t, m.pose.position.x, m.pose.position.y, math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
        else:
            q = m.pose.pose.orientation
            SENT.append(t); SENTV.append((t, int(m.header.frame_id.split("_")[1]), m.pose.pose.position.x, m.pose.pose.position.y,
                                         2 * math.atan2(q.z, q.w)))
G, TR, SENT = np.array(G), np.array(TR), np.array(sorted(SENT))
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_sim = lambda x: x + (kk * x + c0)

# ---- lap window ----
starts, end = [], None
for ln in open(f"{D}/logs/fly_trial.log"):
    m_ = re.search(r"LAP (\d+) LEG (\d+) START t_sim=([\d.]+)", ln)
    if m_: starts.append(float(m_[3]))
    m_ = re.search(r"LAPS END t_sim=([\d.]+)", ln)
    if m_: end = float(m_[1])
W0, W1 = to_sim(starts[0]), to_sim(end)

# ---- tracks: (t, E, N, yaw) ----
tracks = {}
m = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1 = []; k4 = []; n_visp = 0; n_visp_ign = 0; par = {}
while True:
    r = m.recv_match(type=["XKF1", "XKF4", "VISP", "PARM"])
    if r is None: break
    ty = r.get_type()
    if ty == "PARM": par[r.Name] = r.Value
    elif ty == "VISP": n_visp += 1; n_visp_ign += int(r.Ign > 0)
    elif r.C != 0: continue
    elif ty == "XKF1": k1.append((r.TimeUS / 1e6, r.PE, r.PN, math.radians(90.0 - r.Yaw)))
    else: k4.append((r.TimeUS / 1e6, (int(r.SS) >> 4) & 1))      # nav_filter_status bit 4 = horiz_pos_abs
k4 = np.array(k4, float); k4[:, 0] = to_sim(k4[:, 0])
k1 = np.array(k1); k1[:, 0] = to_sim(k1[:, 0]); tracks["EKF3 live"] = k1


def tum(path):
    if not os.path.exists(path): return None
    x = np.loadtxt(path, ndmin=2)
    qx, qy, qz, qw = x[:, 4], x[:, 5], x[:, 6], x[:, 7]
    return np.c_[x[:, 0], x[:, 1], x[:, 2], np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy ** 2 + qz ** 2))]


for name, p in (("UKF live", "room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", "room_ukf/ukf_rts.tum"),
                ("FGO live", "room_fgo/fgo_live.tum"), ("FGO hindsight (whole-flight batch)", "room_fgo/fgo_batch.tum")):
    t_ = tum(f"{D}/{p}")
    if t_ is not None: tracks[name] = t_


def err(tr):
    w = (tr[:, 0] >= W0) & (tr[:, 0] <= W1); T = tr[w]
    eE = T[:, 1] - np.interp(T[:, 0], G[:, 0], G[:, 1]); eN = T[:, 2] - np.interp(T[:, 0], G[:, 0], G[:, 2])
    gy = np.interp(T[:, 0], G[:, 0], np.unwrap(G[:, 3]))
    return T[:, 0], np.hypot(eE, eN), np.degrees(np.abs(wrap(T[:, 3] - gy)))


def st(x):
    return {"rmse": float(np.sqrt(np.mean(x ** 2))), "median": float(np.median(x)), "p95": float(np.percentile(x, 95)),
            "max": float(np.max(x)), "n": int(len(x))}


out = {"trial": a.trial, "window_s": [W0, W1], "clock_map": {"rate_ppm": 1e6 * float(kk)}, "tracks": {}, "gaps": []}
E = {}
for n_, tr in tracks.items():
    t_, eh, ey = err(tr); E[n_] = (t_, eh)
    out["tracks"][n_] = {"horiz_err_m": st(eh), "yaw_err_deg": {"median": float(np.median(ey)), "p95": float(np.percentile(ey, 95))}}
# gaps between consecutive sent fixes inside the window (window edges count as boundaries only if a fix is there)
S = SENT[(SENT >= W0) & (SENT <= W1)]
for g0, g1 in zip(S[:-1], S[1:]):
    if g1 - g0 < GAP_MIN_S: continue
    row = {"t0": float(g0), "t1": float(g1), "length_s": float(g1 - g0)}
    for n_, (t_, eh) in E.items():
        w = (t_ > g0) & (t_ < g1)
        if w.any(): row[n_] = {"mean": float(eh[w].mean()), "max": float(eh[w].max())}
    w4 = (k4[:, 0] > g0) & (k4[:, 0] < g1)
    row["ekf3_horiz_pos_abs_frac"] = float(k4[w4, 1].mean()) if w4.any() else None
    out["gaps"].append(row)
out["n_sent_in_window"] = int(len(S))
# ---- gates (pre-registered G1-G3; G4 from the replays' stats.json) ----
V_ = np.array(SENTV)
gxe = np.interp(V_[:, 0], G[:, 0], G[:, 1]); gyn = np.interp(V_[:, 0], G[:, 0], G[:, 2]); gyw = np.interp(V_[:, 0], G[:, 0], np.unwrap(G[:, 3]))
fix_dxy = np.hypot(V_[:, 2] - gxe, V_[:, 3] - gyn); fix_dyaw = np.degrees(np.abs(wrap(V_[:, 4] - gyw)))
meta = open(f"{D}/metadata.yaml").read(); mt = re.search(r"tag_ids:\s*\"?([^\"\n]+)", meta)
subset = None if (mt is None or mt[1].strip() == "all") else {int(x) for x in mt[1].split(",")}
laps_ids = []
ls = [to_sim(x) for x in starts[::4]] + [W1]
for a0, a1 in zip(ls[:-1], ls[1:]):
    laps_ids.append(sorted({int(i) for t_, i, *_ in SENTV if a0 <= t_ < a1}))
need = subset if subset is not None else set(range(8))
gates = {"G1_laps": len(starts) == 20 and end is not None, "G1_params": par.get("AHRS_EKF_TYPE") == 10 and par.get("LOG_REPLAY") == 1
         and par.get("VISO_DELAY_MS") == 15,
         "G2_visp_eq_sent": n_visp == len(SENTV), "G2_ids_in_subset": subset is None or {int(r[1]) for r in SENTV} <= subset,
         "G2_every_tag_every_lap": all(need <= set(l) for l in laps_ids),
         "G3_fix_max_dxy_m": float(fix_dxy.max()), "G3_fix_max_dyaw_deg": float(fix_dyaw.max()),
         "G3": bool(fix_dxy.max() < 0.3 and fix_dyaw.max() < 3.0)}
for nm in ("room_ukf", "room_fgo"):
    sp = f"{D}/{nm}/stats.json"
    if os.path.exists(sp): gates[f"G4_{nm}"] = json.load(open(sp))
gates["n_visp"], gates["n_visp_ignored"], gates["n_sent"], gates["laps_ids"] = n_visp, n_visp_ign, len(SENTV), laps_ids
out["gates"] = gates; print("gates:", {k: v for k, v in gates.items() if not k.startswith("G4")})
for n_, s_ in out["tracks"].items():
    print(f"{n_:36s} horiz RMSE {s_['horiz_err_m']['rmse']:.3f} median {s_['horiz_err_m']['median']:.3f} p95 {s_['horiz_err_m']['p95']:.3f} "
          f"max {s_['horiz_err_m']['max']:.3f} m | yaw median {s_['yaw_err_deg']['median']:.2f} p95 {s_['yaw_err_deg']['p95']:.2f} deg")
print(f"gaps >= {GAP_MIN_S} s: {len(out['gaps'])}; lengths {[round(g['length_s'], 1) for g in out['gaps']]}")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
