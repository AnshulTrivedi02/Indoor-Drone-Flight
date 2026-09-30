#!/usr/bin/env python3
"""D17 V1/V2 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION (D17)"): the UKF port's ExtNav heading input.
Replay mode: the Replay dump (ukf_inputs.csv: H accepted headings, HP processed, P,4 queue, Y pseudo-yaw) and
the Replay CSV (ukf_shadow.csv), against the ORIGINAL log's REPH messages and SIM truth.
  R1 same input: the REPH sequence, run through EKF3's acceptance rule (20 ms on TS; NaN), equals the UKF's
     accepted list 1:1 (TS, delay, angErr); yaw = the quaternion's 321 yaw; event time = max(TS-D-6, now-60)
  R2 queue: each accepted heading processed exactly once (P,4), in time order, >= 60 ms after its event time
  R3 alignment at the first processed heading; no pseudo-yaw fusion (Y) after it
  R4 >= 95% of processed headings in the pinned cruise window accepted by the gate
  R5 UKF yaw (horizon state) vs SIM in the cruise window: p95 <= 1.0 deg, max <= 2.0 deg
Usage (venv-ardupilot): python3 eval/ukf_heading_v1.py TRIAL REPLAY_DIR [--json OUT]"""
import argparse, json, math, os, sys
import numpy as np
from pymavlink import mavutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("dir"); ap.add_argument("--json"); a = ap.parse_args()
m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{a.trial}/ardupilot.bin"))
REPH, S = [], []
while True:
    r = m.recv_match(type=["REPH", "SIM"])
    if r is None:
        break
    if r.get_type() == "REPH":
        REPH.append((r.TS, r.D, r.AEr, r.Q1, r.Q2, r.Q3, r.Q4))
    else:
        S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Yaw))
S = np.array(S)
H, HP, P4, Y = [], [], [], []
for line in open(f"{a.dir}/ukf_inputs.csv"):
    f = line.rstrip().split(",")
    if f[0] == "H": H.append([float(v) for v in f[1:]])
    elif f[0] == "HP": HP.append([float(v) for v in f[1:]])
    elif f[0] == "P" and f[1] == "4": P4.append((int(f[2]), int(f[3])))
    elif f[0] == "Y": Y.append(int(f[1]))
H, HP, P4 = np.array(H), np.array(HP), np.array(P4)
c = np.genfromtxt(f"{a.dir}/ukf_shadow.csv", delimiter=",", names=True)
t_init_ms = c["TimeUS"][0] / 1e3
out = {"trial": a.trial, "n_REPH": len(REPH), "n_accepted": int(len(H)), "n_processed": int(len(HP))}
# R1: EKF3's acceptance rule on the REPH sequence
exp, last = [], 0
for ts, d, ae, q1, q2, q3, q4 in REPH:
    if (ts - last) % 2**32 < 20:
        continue
    last = ts
    if any(math.isnan(v) for v in (q1, q2, q3, q4, ae)):
        continue
    yaw = math.atan2(2 * (q1 * q4 + q2 * q3), 1 - 2 * (q3 * q3 + q4 * q4))
    exp.append((ts, d, ae, yaw))
exp = np.array(exp)
n = min(len(exp), len(H))
ok_len = len(exp) == len(H)
ts_eq = bool(ok_len and np.all(exp[:, 0] == H[:, 1]))
d_eq = bool(ok_len and np.all(exp[:, 1] == H[:, 2]))
ae_eq = bool(ok_len and np.allclose(exp[:, 2], H[:, 5], rtol=0, atol=1e-6))
yaw_err = float(np.max(np.abs((exp[:n, 3] - H[:n, 4] + math.pi) % (2 * math.pi) - math.pi))) if n else None
t_rule = np.maximum(H[:, 1] - H[:, 2] - 6, H[:, 0] - 60)
t_eq = bool(np.all(t_rule == H[:, 3]))
out["R1"] = {"expected_after_rule": int(len(exp)), "accepted": int(len(H)), "all_REPH_after_init": bool(REPH[0][0] >= t_init_ms),
             "ts_match": ts_eq, "delay_match": d_eq, "angErr_match": ae_eq, "yaw_max_diff_rad": yaw_err, "event_time_rule_match": t_eq,
             "pass": bool(ok_len and ts_eq and d_eq and ae_eq and yaw_err is not None and yaw_err < 1e-5 and t_eq)}
# R2
ev_sorted = sorted(H[:, 3].astype(int).tolist()); p_ev = sorted(P4[:, 0].tolist())
lag = P4[:, 1] - P4[:, 0]
out["R2"] = {"processed_once": bool(ev_sorted == p_ev), "time_ordered": bool(np.all(np.diff(P4[:, 0]) >= 0)),
             "lag_min_ms": int(lag.min()), "pass": bool(ev_sorted == p_ev and np.all(np.diff(P4[:, 0]) >= 0) and lag.min() >= 60)}
# R3
first = HP[0]
out["R3"] = {"first_processed_aligns": bool(first[4] == 0 and first[5] == 1 and np.all(HP[1:, 5] == 1)),
             "pseudo_after_align": int(sum(1 for y in Y if y > first[0])), "pseudo_before": int(sum(1 for y in Y if y <= first[0]))}
out["R3"]["pass"] = out["R3"]["first_processed_aligns"] and out["R3"]["pseudo_after_align"] == 0
# cruise window from SIM on the SITL clock
lat, lng = S[:, 1], S[:, 2]
if abs(lat).max() > 1000:
    lat, lng = lat / 1e7, lng / 1e7
N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
c0, c1 = cruise_bounds(S[:, 0], E, N); out["cruise_s"] = [float(c0), float(c1)]
w = (HP[:, 0] / 1e3 >= c0) & (HP[:, 0] / 1e3 <= c1)
out["R4"] = {"n": int(w.sum()), "accepted_pct": float(100 * HP[w, 4].mean()), "rejected": int((HP[w, 4] == 0).sum()), "test_ratio_max": float(HP[w, 3].max())}   # HP: t, yaw, nu, test, acc, aligned
out["R4"]["pass"] = out["R4"]["accepted_pct"] >= 95.0
t = c["TimeUS"] / 1e6; wy = (t >= c0) & (t <= c1)
un = lambda d: np.degrees(np.unwrap(np.radians(d)))
err = np.abs((un(c["Yaw"])[wy] - np.interp(t[wy], S[:, 0], un(S[:, 3])) + 180) % 360 - 180)
out["R5"] = {"p95_deg": float(np.percentile(err, 95)), "max_deg": float(err.max()), "mean_deg": float(err.mean())}
out["R5"]["pass"] = out["R5"]["p95_deg"] <= 1.0 and out["R5"]["max_deg"] <= 2.0
out["PASS"] = all(out[k]["pass"] for k in ("R1", "R2", "R3", "R4", "R5"))
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
