#!/usr/bin/env python3
"""FGO ground test (PRE-REGISTERED in "PRE-REGISTRATION — the FGO closed-loop gates"; execution deviation in "FGO ground
test fgo_groundtest_half: execution DEVIATION"): G1 config; G2 armed; G3 ATT == XFGO (<= 0.1 deg p95); G4 over the
hold up to the node stop: horizontal <= 0.10 m, height error at the end <= 0.10 m and growth <= 0.05 m, yaw:
|yaw change - integrated raw gyro-z drift| <= 1.0 deg; G5 no failsafe/crash text up to the node stop (later text
reported separately); FG2 node-stop: XFGO.OV falls to 0 within 300 ms sim of the last received state.
Usage (venv-ardupilot): python3 eval/fgo_groundtest_check.py BIN [--json OUT]"""
import argparse, json
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("bin"); ap.add_argument("--json"); a = ap.parse_args()
m = mavutil.mavlink_connection(a.bin)
P, ARM, ATT, O, I, SIM, IMU, MSG = {}, [], [], [], [], [], [], []
while True:
    r = m.recv_match(type=["PARM", "ARM", "ATT", "XFGO", "XFGI", "SIM", "IMU", "MSG"])
    if r is None:
        break
    t = r.get_type(); ts = getattr(r, "TimeUS", 0) / 1e6
    if t == "PARM": P[r.Name] = r.Value
    elif t == "ARM": ARM.append((ts, r.ArmState))
    elif t == "ATT": ATT.append((ts, r.Roll, r.Pitch, r.Yaw))
    elif t == "XFGO": O.append((ts, r.PN, r.PE, r.PD, r.Roll, r.Pitch, r.Yaw, r.OV))
    elif t == "XFGI": I.append((ts, r.Tv / 1e3))
    elif t == "SIM": SIM.append((ts, r.Alt, r.Yaw))
    elif t == "IMU" and r.I == 0: IMU.append((ts, r.GyrZ))
    elif t == "MSG": MSG.append((ts, r.Message))
ATT, O, I, SIM, IMU = map(np.array, (ATT, O, I, SIM, IMU))
wrap = lambda d: (d + 180) % 360 - 180
un = lambda d: np.degrees(np.unwrap(np.radians(d)))
out = {"G1": {k: P.get(k) for k in ("AHRS_EKF_TYPE", "AHRS_FGO_ENABLE", "SERIAL3_PROTOCOL")}}
out["G1"]["pass"] = P.get("AHRS_EKF_TYPE") == 13 and P.get("AHRS_FGO_ENABLE") == 1 and P.get("SERIAL3_PROTOCOL") == 2
arms = [t for t, s in ARM if s == 1]; dis = [t for t, s in ARM if s == 0 and arms and t > arms[0]]
out["G2"] = {"armed_at": arms[0] if arms else None, "pass": bool(arms)}
t0 = arms[0]; t_last = float(I[:, 0].max())                          # the node's last state arrival (the stop)
t_end = min(t_last, dis[0] if dis else O[-1, 0])
wa = (ATT[:, 0] >= t0 + 0.5) & (ATT[:, 0] <= t_end - 0.5); tt = ATT[wa, 0]
d = np.abs(np.c_[ATT[wa, 1] - np.interp(tt, O[:, 0], O[:, 4]), ATT[wa, 2] - np.interp(tt, O[:, 0], O[:, 5]),
                 wrap(ATT[wa, 3] - np.interp(tt, O[:, 0], un(O[:, 6])))]).max(axis=1)
out["G3"] = {"att_vs_xfgo_p95_deg": float(np.percentile(d, 95)), "n": int(wa.sum()), "pass": bool(np.percentile(d, 95) <= 0.1)}
wo = (O[:, 0] >= t0) & (O[:, 0] <= t_end); Oh = O[wo]
dne = float(np.hypot(Oh[:, 1] - Oh[0, 1], Oh[:, 2] - Oh[0, 2]).max())
truth_pd = -(np.interp(Oh[:, 0], SIM[:, 0], SIM[:, 1]) - SIM[0, 1] + 0.195)
herr = np.abs(Oh[:, 3] - truth_pd)
ych = float(un(Oh[:, 6])[-1] - un(Oh[:, 6])[0])
wi = (IMU[:, 0] >= Oh[0, 0]) & (IMU[:, 0] <= Oh[-1, 0])
gyro_int = float(np.degrees(np.trapezoid(IMU[wi, 1], IMU[wi, 0])))
out["G4"] = {"hold_scored_s": float(t_end - t0), "max_dNE_m": dne, "height_err_end_m": float(herr[-1]),
             "height_err_growth_m": float(herr.max() - herr[0]), "yaw_change_deg": ych, "raw_gyro_z_integral_deg": gyro_int,
             "yaw_minus_gyro_deg": ych + gyro_int}      # NED yaw (+cw) vs FLU-? IMU GyrZ is FRD (+cw): yaw change ~ +integral
out["G4"]["yaw_minus_gyro_deg"] = ych - gyro_int
g = out["G4"]
g["pass"] = bool(dne <= 0.10 and g["height_err_end_m"] <= 0.10 and g["height_err_growth_m"] <= 0.05 and abs(g["yaw_minus_gyro_deg"]) <= 1.0)
bad_kw = ("failsafe", "crash", "ekf variance", "fgo invalid", "fgo no state", "error")
bad = [(round(t, 1), s) for t, s in MSG if "PrecLand" not in s and any(k in s.lower() for k in bad_kw)]
out["G5"] = {"disarmed_at": dis[0] if dis else None, "bad_before_stop": [b for b in bad if b[0] <= t_last],
             "after_stop_reported": [b for b in bad if b[0] > t_last] + [(round(t, 1), s) for t, s in MSG if t > t_last][:12]}
out["G5"]["pass"] = bool(dis) and not out["G5"]["bad_before_stop"]
inv = O[(O[:, 0] > t_last) & (O[:, 7] == 0)]
out["FG2_node_stop"] = {"last_state_s": t_last, "first_invalid_s": float(inv[0, 0]) if len(inv) else None,
                        "latency_ms": float(1e3 * (inv[0, 0] - t_last)) if len(inv) else None}
out["FG2_node_stop"]["pass"] = bool(len(inv) and (inv[0, 0] - t_last) <= 0.300)
out["PASS"] = all(out[k]["pass"] for k in ("G1", "G2", "G3", "G4", "G5", "FG2_node_stop"))
print(json.dumps(out, indent=1, default=str))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1, default=str)
