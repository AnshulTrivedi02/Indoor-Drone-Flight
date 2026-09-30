#!/usr/bin/env python3
"""D15: score the UKF PORT run in Replay (ukf_shadow.csv, SITL clock) as three_way_eval scores EKF3: against the
flight's SIM truth (ekf3/ground_truth.tum, same clock), pinned cruise window, evo -a. Also the take-off yaw
change (t0 = first port height > rest + 0.3 m; yaw(t0 + 2 s) - yaw(t0 - 1 s), NED yaw) and the cruise yaw drift
(port yaw minus SIM yaw, deg/min; NED sense, so the sign is opposite to the ENU offline figures).
Usage (venv-ardupilot): python3 eval/d15_port_score.py TRIAL CSV [--json OUT]"""
import argparse, json, os, sys
import numpy as np
from pymavlink import mavutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import three_way_eval as T
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("csv"); ap.add_argument("--json"); a = ap.parse_args()
TD = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
c = np.genfromtxt(a.csv, delimiter=",", names=True)
t = c["TimeUS"] / 1e6
T.ekf3_tums(a.trial)
sim = np.loadtxt(f"{TD}/ekf3/ground_truth.tum")
t0w, t1w = T.cruise_window(a.trial)
est = np.c_[t, c["PN"], c["PE"], c["PD"], np.tile([0., 0., 0., 1.], (len(t), 1))]
ref = T.crop(sim, t0w, t1w); est = T.crop(est, t0w, t1w)
d = os.path.dirname(os.path.abspath(a.csv)); rp, ep = f"{d}/_ref.tum", f"{d}/_est.tum"
T.write_tum(rp, ref); T.write_tum(ep, est)
out = {"trial": a.trial, "evo_a_cruise": T.evo_ape_a(rp, ep)}
y = np.degrees(np.unwrap(np.radians(c["Yaw"]))); z = -c["PD"]
z0 = np.median(z[:50]); tk = t[np.argmax(z > z0 + 0.3)]
out["takeoff_yaw_change_deg"] = float(np.interp(tk + 2, t, y) - np.interp(tk - 1, t, y))
m = mavutil.mavlink_connection(f"{TD}/ardupilot.bin"); S = []
while True:
    r = m.recv_match(type=["SIM"])
    if r is None:
        break
    S.append((r.TimeUS / 1e6, r.Yaw))
S = np.array(S); ys = np.degrees(np.unwrap(np.radians(S[:, 1])))
w = (t >= t0w) & (t <= t1w)
err = y[w] - np.interp(t[w], S[:, 0], ys); err = (err + 180) % 360 - 180 if np.ptp(err) < 170 else err
out["cruise_yaw_drift_dpm_NED"] = float(np.polyfit((t[w] - t[w][0]) / 60, err, 1)[0])
print(json.dumps(out))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
