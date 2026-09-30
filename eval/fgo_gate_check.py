#!/usr/bin/env python3
"""FGO closed-loop gates FG1-FG3 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — the FGO closed-loop gates").
Inputs: the shadow flight's dataflash log (XFGI = FGO states received, XFGO = current-time output), the offline
FGO replay of the same flight's bag (<trial>/fgo/fgo_traj.tum, corridor frame) and the node's stats
(<trial>/fgo_node_stats.npz).
  FG1 (a) evo -a (cruise) of the received trajectory within +-0.15 m of the offline one; (b) received vs offline
      yaw at matched keyframe times p95 <= 0.2 deg, max <= 0.5 deg; (c) received count = node keyframes after the
      clock map settled, 0 late.
  FG2 XFGO.OV = 1 for 100% of samples from arming to disarm.
  FG3 XFGO vs XFGI (state later received for the same time; linear interpolation), take-off to landing:
      position p95 <= 0.05, max <= 0.15 m; velocity p95 <= 0.05, max <= 0.15 m/s; yaw p95 <= 0.10, max <= 0.5 deg;
      FG3b output age <= 250 ms for 100% of samples from arming to disarm.
      DEVIATION (stated): XFGI logs no velocity, so the velocity reference is the time derivative of the received
      positions (3-point centred difference over keyframes), not the node's velocity state.
Frames: XFGI/XFGO are NED; the offline TUM is the corridor frame (x = N, y = W, z = U) -> NED (x, -y, -z).
Usage (venv-evo + pymavlink shim): python3 eval/fgo_gate_check.py TRIAL [--json OUT]"""
import argparse, json, math, os, subprocess, sys, tempfile
import numpy as np
from pymavlink import mavutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
TD = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
m = mavutil.mavlink_connection(f"{TD}/ardupilot.bin"); I, O, S, ARM = [], [], [], []
while True:
    r = m.recv_match(type=["XFGI", "XFGO", "SIM", "ARM"])
    if r is None:
        break
    t = r.get_type()
    if t == "XFGI": I.append((r.TimeUS / 1e6, r.Tv / 1e3, r.PN, r.PE, r.PD, r.Yaw, r.V, r.Late))
    elif t == "XFGO": O.append((r.TimeUS / 1e6, r.PN, r.PE, r.PD, r.VN, r.VE, r.VD, r.Yaw, r.OV, r.Age))
    elif t == "SIM": S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Alt))
    else: ARM.append((r.TimeUS / 1e6, r.ArmState))
I, O, S = np.array(I), np.array(O), np.array(S)
arm = [t for t, s in ARM if s == 1]; dis = [t for t, s in ARM if s == 0 and arm and t > arm[0]]
t_arm, t_dis = arm[0], (dis[0] if dis else O[-1, 0])
out = {"trial": a.trial, "n_XFGI": int(len(I)), "arm_s": t_arm, "disarm_s": t_dis}
un = lambda d: np.degrees(np.unwrap(np.radians(d)))

# ---- FG2 / FG3b ----
w = (O[:, 0] >= t_arm) & (O[:, 0] <= t_dis)
out["FG2"] = {"OV_pct_arm_to_disarm": float(100 * O[w, 8].mean()), "pass": bool(O[w, 8].min() == 1)}
out["FG3b"] = {"age_ms_max": float(O[w, 9].max()), "age_ms_p95": float(np.percentile(O[w, 9], 95)),
               "age_ms_median": float(np.median(O[w, 9])), "pass": bool(O[w, 9].max() <= 250)}

# ---- FG3 predictor: XFGO at its time vs the received state valid for that time ----
lat, lng = S[:, 1], S[:, 2]
if abs(lat).max() > 1000:
    lat, lng = lat / 1e7, lng / 1e7
h = S[:, 3] - S[0, 3]; t_to = S[np.argmax(h > 0.5), 0]; t_ld = S[len(h) - 1 - np.argmax(h[::-1] > 0.5), 0]
Iv = I[np.argsort(I[:, 1])]; tv = Iv[:, 1]
vel = np.zeros((len(Iv), 3))
for k in range(3):
    vel[1:-1, k] = (Iv[2:, 2 + k] - Iv[:-2, 2 + k]) / (tv[2:] - tv[:-2])
wo = (O[:, 0] >= t_to) & (O[:, 0] <= t_ld) & (O[:, 0] >= tv[1]) & (O[:, 0] <= tv[-2])
ref_p = np.c_[[np.interp(O[wo, 0], tv, Iv[:, 2 + k]) for k in range(3)]].T
ref_v = np.c_[[np.interp(O[wo, 0], tv, vel[:, k]) for k in range(3)]].T
ref_y = np.interp(O[wo, 0], tv, un(Iv[:, 5]))
dp = np.linalg.norm(O[wo, 1:4] - ref_p, axis=1); dv = np.linalg.norm(O[wo, 4:7] - ref_v, axis=1)
dy = np.abs((un(O[:, 7])[wo] - ref_y + 180) % 360 - 180)
st = lambda x: {"p95": float(np.percentile(x, 95)), "max": float(x.max()), "median": float(np.median(x))}
out["FG3"] = {"span_s": [float(t_to), float(t_ld)], "n": int(wo.sum()), "position_m": st(dp), "velocity_mps": st(dv), "yaw_deg": st(dy)}
f3 = out["FG3"]
f3["pass"] = {"position": f3["position_m"]["p95"] <= 0.05 and f3["position_m"]["max"] <= 0.15,
              "velocity": f3["velocity_mps"]["p95"] <= 0.05 and f3["velocity_mps"]["max"] <= 0.15,
              "yaw": f3["yaw_deg"]["p95"] <= 0.10 and f3["yaw_deg"]["max"] <= 0.5}

# ---- FG1 backend equivalence against the offline FGO on the same bag ----
fg1 = {}
off = np.loadtxt(f"{TD}/fgo/fgo_traj.tum"); gt = np.loadtxt(f"{TD}/fgo/ground_truth.tum")
c0, c1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
# the received states are stamped on the SITL clock (Tv); map to the bag clock with the node's own stats traj
# (bag-clock keyframe times, same keyframes): match by nearest in position sequence order
st_ = np.load(f"{TD}/fgo_node_stats.npz", allow_pickle=True); ntraj = st_["traj"]      # t_bag, x, y, z, r, p, yaw, bgz
fg1["node_keyframes"] = int(len(ntraj))
# SITL -> bag clock offset: the received Tv are the node's keyframe times mapped by its /imu/time_ref lower
# envelope (a few tens of ms). Estimated by matching the received PN to the node's own x over a +-0.5 s grid.
# (FIRST VERSION, a bug: it aligned the LAST N keyframes by count, but the node runs ~6 s past the end of the
# dataflash log, giving a false 5.4 s offset and a false constant ~1.26 deg yaw difference.)
grid = np.arange(-0.5, 0.5001, 0.001)
cost = [np.median(np.abs(Iv[:, 2] - np.interp(Iv[:, 1] + d, ntraj[:, 0], ntraj[:, 1]))) for d in grid]
off_c = float(grid[int(np.argmin(cost))])
Tb = Iv[:, 1] + off_c                                  # received states on the bag clock
fg1["sitl_to_bag_offset_s"] = float(off_c)
fg1["late_max"] = int(I[:, 7].max()); fg1["count_received"] = int(len(I))
fg1["count_match_after_settle"] = bool(abs(len(ntraj) - len(I)) <= int(0.02 * len(ntraj)) + 30)
# received (NED) -> corridor frame (x = N, y = -E, z = -D) as TUM for evo
def tum(path, t, x, y, z, yaw_deg):
    q = np.c_[np.zeros(len(t)), np.zeros(len(t)), np.sin(np.radians(yaw_deg) / 2), np.cos(np.radians(yaw_deg) / 2)]
    np.savetxt(path, np.c_[t, x, y, z, q], fmt="%.6f")
tmp = tempfile.mkdtemp()
wr = (Tb >= c0) & (Tb <= c1)
tum(f"{tmp}/recv.tum", Tb[wr], Iv[wr, 2], -Iv[wr, 3], -Iv[wr, 4], -Iv[wr, 5])
wo_ = (off[:, 0] >= c0) & (off[:, 0] <= c1)
np.savetxt(f"{tmp}/off.tum", off[wo_], fmt="%.6f")
wg = (gt[:, 0] >= c0) & (gt[:, 0] <= c1)
np.savetxt(f"{tmp}/gt.tum", gt[wg], fmt="%.6f")
def evo_a(est):
    r = subprocess.run([os.path.expanduser("~/venv-evo/bin/evo_ape"), "tum", f"{tmp}/gt.tum", est, "-a", "--no_warnings"],
                       capture_output=True, text=True).stdout
    for line in r.splitlines():
        if line.strip().startswith("rmse"):
            return float(line.split()[1])
fg1["evo_a_received"] = evo_a(f"{tmp}/recv.tum"); fg1["evo_a_offline"] = evo_a(f"{tmp}/off.tum")
fg1["evo_diff"] = None if None in (fg1["evo_a_received"], fg1["evo_a_offline"]) else fg1["evo_a_received"] - fg1["evo_a_offline"]
qx, qy, qz, qw = off[:, 4], off[:, 5], off[:, 6], off[:, 7]
yaw_off = np.degrees(np.unwrap(np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))))
yr = np.interp(Tb[wr], off[:, 0], yaw_off); dyy = np.abs(((-un(Iv[:, 5]))[wr] - yr + 180) % 360 - 180)
fg1["yaw_diff_deg"] = {"p95": float(np.percentile(dyy, 95)), "max": float(dyy.max())}
fg1["pass"] = bool(fg1["evo_diff"] is not None and abs(fg1["evo_diff"]) <= 0.15 and fg1["yaw_diff_deg"]["p95"] <= 0.2
                   and fg1["yaw_diff_deg"]["max"] <= 0.5 and fg1["late_max"] == 0 and fg1["count_match_after_settle"])
out["FG1"] = fg1
out["PASS"] = bool(out["FG1"]["pass"] and out["FG2"]["pass"] and all(f3["pass"].values()) and out["FG3b"]["pass"])
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
