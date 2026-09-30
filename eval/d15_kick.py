#!/usr/bin/env python3
"""D15 item 3: the take-off yaw change, DEFINED as in METHODOLOGY (P2 finding, table "UKF yaw change at
take-off"): t0 = first GT time with height > rest height + 0.3 m (rest = GT median z over the first
2 s); change = yaw(t0 + 2 s) - yaw(t0 - 1 s), each estimator's TUM yaw (unwrapped, interpolated).
Old values from the pre-D15 archive (~/thesis_data/pre_d15_trials), new from the trial folders.
Usage: python3 eval/d15_kick.py TRIAL... [--json OUT]"""
import argparse, json, os
import numpy as np
from scipy.spatial.transform import Rotation as Rot
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
H = os.path.expanduser("~/thesis_data")


def yaw_series(tum):
    d = np.loadtxt(tum)
    y = np.unwrap(Rot.from_quat(d[:, 4:8]).as_euler("xyz")[:, 2])
    return d[:, 0], np.degrees(y)


def kick(tum, t0):
    if not os.path.exists(tum):
        return None
    t, y = yaw_series(tum)
    return float(np.interp(t0 + 2, t, y) - np.interp(t0 - 1, t, y))


out = {}
for tr in a.trials:
    gt = np.loadtxt(f"{H}/trials/{tr}/ukf/ground_truth.tum")
    z0 = np.median(gt[gt[:, 0] < gt[0, 0] + 2, 3])
    t0 = float(gt[np.argmax(gt[:, 3] > z0 + 0.3), 0])
    r = {"t0": t0}
    for est, f in (("UKF", "ukf/ukf_traj.tum"), ("FGO", "fgo/fgo_traj.tum")):
        r[est] = {"old": kick(f"{H}/pre_d15_trials/{tr}/{f}", t0), "new": kick(f"{H}/trials/{tr}/{f}", t0)}
    out[tr] = r
    f = lambda v: "   —   " if v is None else f"{v:+7.2f}"
    print(f"{tr:14s} t0 {t0:7.2f}  UKF old {f(r['UKF']['old'])} new {f(r['UKF']['new'])}   FGO old {f(r['FGO']['old'])} new {f(r['FGO']['new'])}")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
