#!/usr/bin/env python3
"""D26 (b), EXPLORATORY: the same heading stream through the UKF port's gate (Replay of the flight's own log with
UKF_EXTYAW=1: ukf_inputs.csv HP rows = event time ms, heading, innovation, test ratio, accepted, aligned) and EKF3
(passive in the flight, EK3_SRC1_YAW 6: XKF1 yaw). Per bin: UKF processed/accepted/gated, max |innovation|, and the
yaw error against SIM of the UKF (Replay ukf_shadow.csv) and EKF3 (XKF1), passive, and of the flying FGO (XFGO).
Usage (venv-ardupilot): python3 eval/d26_ukf_ekf3_gate.py TRIAL REPLAY_DIR [--t0 290 --t1 338 --bin 3]"""
import argparse, os
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("dir"); ap.add_argument("--t0", type=float, default=290)
ap.add_argument("--t1", type=float, default=338); ap.add_argument("--bin", type=float, default=3.0); a = ap.parse_args()
m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{a.trial}/ardupilot.bin")); S, K, F = [], [], []
while True:
    r = m.recv_match(type=["SIM", "XKF1", "XFGO"])
    if r is None:
        break
    t = r.TimeUS / 1e6
    if r.get_type() == "SIM": S.append((t, r.Yaw))
    elif r.get_type() == "XKF1" and r.C == 0: K.append((t, r.Yaw))
    elif r.get_type() == "XFGO": F.append((t, r.Yaw))
S, K, F = map(np.array, (S, K, F))
un = lambda d: np.degrees(np.unwrap(np.radians(d)))
def yerr(X):
    e = un(X[:, 1]) - np.interp(X[:, 0], S[:, 0], un(S[:, 1])); return (e + 180) % 360 - 180
HP = np.array([[float(v) for v in l.split(",")[1:]] for l in open(f"{a.dir}/ukf_inputs.csv") if l.startswith("HP,")])
c = np.genfromtxt(f"{a.dir}/ukf_shadow.csv", delimiter=",", names=True)
U = np.c_[c["TimeUS"] / 1e6, c["Yaw"]]
eU, eK, eF = yerr(U), yerr(K), yerr(F)
th = HP[:, 0] / 1e3
def rng(t, e, b):
    w = (t >= b) & (t < b + a.bin); return (e[w].min(), e[w].max()) if w.any() else (np.nan, np.nan)
print(f"{a.trial}: UKF processed {len(HP)}, accepted {int(HP[:, 4].sum())}, gated {int(len(HP) - HP[:, 4].sum())}")
for b in np.arange(a.t0, a.t1, a.bin):
    w = (th >= b) & (th < b + a.bin)
    print(f"  {b:5.0f}-{b + a.bin:3.0f}s UKF hdg proc {w.sum():2d} acc {int(HP[w, 4].sum()):2d} | max|nu| {np.degrees(np.abs(HP[w, 2])).max() if w.any() else np.nan:5.2f} deg"
          f" max TR {HP[w, 3].max() if w.any() else np.nan:5.2f} | yaw err  UKF %+.2f..%+.2f  EKF3 %+.2f..%+.2f  FGO(flying) %+.2f..%+.2f" % (*rng(U[:, 0], eU, b), *rng(K[:, 0], eK, b), *rng(F[:, 0], eF, b)))
