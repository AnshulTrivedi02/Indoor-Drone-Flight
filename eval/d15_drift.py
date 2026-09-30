#!/usr/bin/env python3
"""D15 item 5 basis: each estimator's heading drift over the PINNED cruise window (three_way_eval.cruise_window):
yaw error = estimator TUM yaw - its own reference TUM yaw (ukf/, fgo/: bag GT; ekf3/: SIM), wrapped, linear
slope in deg/min. Also the implied wall-contact time by the set-(a) scaling, 186.2 s * sqrt(8.3 / |drift|),
and the wall: a NEGATIVE ENU yaw error (estimate rotated clockwise of truth) -> the controller steers left of the
corridor axis -> WEST wall (as recorded for pre-D15 dsn_tex_r4: -70 deg/min, west, +64 s). EKF3 is not scored here
(its TUMs carry no orientation; its XKF1-based drift is METHODOLOGY's +6.6...+11.1 deg/min, n = 9).
Old = ~/thesis_data/pre_d15_trials, new = the trial folders.  Usage (venv-ardupilot): d15_drift.py TRIAL... [--json OUT]"""
import argparse, json, math, os, sys
import numpy as np
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import three_way_eval as T
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
H = os.path.expanduser("~/thesis_data")


def yaw(tum):
    d = np.loadtxt(tum)
    return d[:, 0], np.unwrap(Rot.from_quat(d[:, 4:8]).as_euler("xyz")[:, 2])


def drift(est_tum, ref_tum, win):
    if not os.path.exists(est_tum):
        return None
    te, ye = yaw(est_tum); tr, yr = yaw(ref_tum)
    w = (te >= win[0]) & (te <= win[1])
    err = np.degrees(ye[w] - np.interp(te[w], tr, yr))
    err = (err + 180) % 360 - 180 if np.abs(err - err[0]).max() < 170 else err
    return float(np.polyfit((te[w] - te[w][0]) / 60.0, err, 1)[0])


contact = lambda d: None if d is None or abs(d) < 1e-9 else 186.2 * math.sqrt(8.3 / abs(d))
out = {}
for tr in a.trials:
    win = T.cruise_window(tr); r = {"window": list(map(float, win))}
    for est in ("ukf", "fgo"):
        for tag, base in (("old", f"{H}/pre_d15_trials/{tr}"), ("new", f"{H}/trials/{tr}")):
            d = drift(f"{base}/{est}/{est}_traj.tum", f"{H}/trials/{tr}/{est}/ground_truth.tum", win)
            r[f"{est.upper()}_{tag}"] = d
            r[f"{est.upper()}_{tag}_contact_s"] = contact(d)
            r[f"{est.upper()}_{tag}_wall"] = None if d is None else ("west" if d < 0 else "east")
    out[tr] = r
    f = lambda v: "   —  " if v is None else f"{v:+6.1f}"
    print(f"{tr:14s} UKF old {f(r['UKF_old'])} new {f(r['UKF_new'])}  FGO old {f(r['FGO_old'])} new {f(r['FGO_new'])} deg/min")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
