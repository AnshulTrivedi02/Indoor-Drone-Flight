#!/usr/bin/env python3
"""D9 output-predictor check (PRE-REGISTERED in METHODOLOGY before P2 was looked at): each current-time
output the controllers would receive (XUKO, stamped at the current time) against the fused state later
computed for the same time (XUKF, stamped at its horizon time), XUKF linearly interpolated to the XUKO
times, from take-off (XUKO height > 0.5 m) to landing. Bands (|delta|): position 3-D p95 <= 0.05 m,
max <= 0.15 m; velocity 3-D p95 <= 0.05 m/s, max <= 0.15 m/s; yaw p95 <= 0.10 deg, max <= 0.5 deg.
Also P2's health: XUKO EvO/EvMx, OV; XUKS healthy and horiz_pos_rel over the same span; a trend check.
Usage (venv-evo + pymavlink shim): python3 eval/ukf_predictor_check.py BIN [--json OUT]"""
import argparse, json
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("bin"); ap.add_argument("--json"); a = ap.parse_args()
m = mavutil.mavlink_connection(a.bin)
O, F, S = [], [], []
while True:
    r = m.recv_match(type=["XUKO", "XUKF", "XUKS"])
    if r is None:
        break
    t = r.get_type()
    if t == "XUKO":
        O.append((r.TimeUS / 1e6, r.PN, r.PE, r.PD, r.VN, r.VE, r.VD, r.Yaw, r.OV, r.EvO, r.EvMx))
    elif t == "XUKF":
        F.append((r.TimeUS / 1e6, r.PN, r.PE, r.PD, r.VN, r.VE, r.VD, r.Yaw))
    else:
        S.append((r.TimeUS / 1e6, int(r.SS), int(r.H)))
O, F, S = np.array(O), np.array(sorted(F)), np.array(S)
air = np.where(-O[:, 3] > 0.5)[0]
t0, t1 = O[air[0], 0], O[air[-1], 0]
w = (O[:, 0] >= t0) & (O[:, 0] <= t1) & (O[:, 0] <= F[-1, 0]) & (O[:, 0] >= F[0, 0])
Fi = np.c_[[np.interp(O[w, 0], F[:, 0], F[:, k]) for k in range(1, 7)]].T
yF = np.degrees(np.unwrap(np.radians(F[:, 7])))
yi = np.interp(O[w, 0], F[:, 0], yF)
dp = np.linalg.norm(O[w, 1:4] - Fi[:, 0:3], axis=1)
dv = np.linalg.norm(O[w, 4:7] - Fi[:, 3:6], axis=1)
dy = np.abs((O[w, 7] - yi + 180) % 360 - 180)
st = lambda x: {"p95": float(np.percentile(x, 95)), "max": float(x.max()), "median": float(np.median(x))}
out = {"span_s": [float(t0), float(t1)], "n": int(w.sum()),
       "position_m": st(dp), "velocity_mps": st(dv), "yaw_deg": st(dy)}
out["pass"] = {"position": out["position_m"]["p95"] <= 0.05 and out["position_m"]["max"] <= 0.15,
               "velocity": out["velocity_mps"]["p95"] <= 0.05 and out["velocity_mps"]["max"] <= 0.15,
               "yaw": out["yaw_deg"]["p95"] <= 0.10 and out["yaw_deg"]["max"] <= 0.5}
out["PASS"] = all(out["pass"].values())
# trend (DIAGNOSTIC): the slope of |dp| over the span
tt = O[w, 0]
out["trend_pos_m_per_min"] = float(np.polyfit(tt, dp, 1)[0] * 60)
# P2 health
out["EvO_max"] = int(O[:, 9].max()); out["EvMx_max"] = int(O[:, 10].max()); out["OV_all"] = bool(O[w, 8].min() == 1)
ws = (S[:, 0] >= t0) & (S[:, 0] <= t1)
out["healthy_pct_airborne"] = float(100 * S[ws, 2].mean())
out["horiz_pos_rel_pct_airborne"] = float(100 * ((S[ws, 1].astype(np.int64) >> 3) & 1).mean())
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
