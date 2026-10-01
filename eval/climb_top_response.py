#!/usr/bin/env python3
"""Climb-top response (D23; for the FGO flight predictions). Per flight: the flying estimator's output height
error dip at the climb-to-cruise short LiDAR returns (output minus SIM truth, relative to its median over the 2 s
before the burst; EKF3 XKF1, UKF port XUKO, FGO XFGO), and the TRUE height overshoot (true peak in the 10 s after
the burst minus the true median over cruise +20..+60 s). Truth = SIM.Alt relative to the first sample + 0.195 m.
Usage (venv-ardupilot): python3 eval/climb_top_response.py TRIAL:EST ... [--json OUT]   (EST: ekf3|ukf|fgo)"""
import argparse, json, os
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("items", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
MSG = {"ekf3": "XKF1", "ukf": "XUKO", "fgo": "XFGO"}; out = {}
for it in a.items:
    tr, est = it.split(":")
    m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{tr}/ardupilot.bin"))
    R, S, E = [], [], []
    while True:
        r = m.recv_match(type=["RFND", "SIM", MSG[est]])
        if r is None:
            break
        t = r.get_type(); ts = r.TimeUS / 1e6
        if t == "RFND" and r.Instance == 0: R.append((ts, r.Dist))
        elif t == "SIM": S.append((ts, r.Alt))
        elif t == MSG[est] and (est != "ekf3" or r.C == 0): E.append((ts, -r.PD))
    R, S, E = np.array(R), np.array(S), np.array(E)
    h = S[:, 1] - S[0, 1] + 0.195
    th = np.interp(R[:, 0], S[:, 0], h); sh = (th > 1.0) & (R[:, 1] < 0.5 * th)
    tb = R[sh, 0].min(); te = R[sh, 0].max()
    err = E[:, 1] - np.interp(E[:, 0], S[:, 0], h)
    pre = (E[:, 0] >= tb - 2.0) & (E[:, 0] < tb); post = (E[:, 0] >= tb) & (E[:, 0] <= te + 3.0)
    dip = float((err[post] - np.median(err[pre])).min())
    cr = (S[:, 0] >= te + 20) & (S[:, 0] <= te + 60); pk = (S[:, 0] >= tb) & (S[:, 0] <= te + 10)
    r = {"est": est, "burst_s": [round(float(tb), 2), round(float(te), 2)], "n_short": int(sh.sum()),
         "output_height_err_dip_m": dip, "true_peak_m": float(h[pk].max()),
         "true_cruise_median_m": float(np.median(h[cr])), "true_overshoot_m": float(h[pk].max() - np.median(h[cr])),
         "t_peak_after_burst_s": float(S[pk, 0][np.argmax(h[pk])] - tb)}
    out[it] = r; print(it, json.dumps(r))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
