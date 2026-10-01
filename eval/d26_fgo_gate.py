#!/usr/bin/env python3
"""D26 (b), EXPLORATORY: the FGO's own treatment of the heading stream near the end wall, from the node-core replay
of the flight (eval/fgo_core_replay.py --save-npz: fwd_log rows = t, kind 0, NIS, accepted, S [rad^2]; traj rows =
t, x, y, z, roll, pitch, yaw, bgz in the corridor frame). Per bin: headings evaluated / accepted / gated, max NIS,
max |innovation| = sqrt(NIS * S), the predicted heading sigma (sqrt(S - R)), and the replayed FGO's yaw error vs GT.
Usage (venv-fgo): python3 eval/d26_fgo_gate.py TRIAL [--t0 290 --t1 338 --bin 3]"""
import argparse, math, os
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--t0", type=float, default=290)
ap.add_argument("--t1", type=float, default=338); ap.add_argument("--bin", type=float, default=3.0); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
z = np.load(f"{D}/fgo_core/core_replay.npz"); L = z["fwd_log"]; L = L[L[:, 1] == 0]; tr = z["traj"]
gt = np.loadtxt(f"{D}/fgo_core/ground_truth.tum")
qx, qy, qz, qw = gt[:, 4], gt[:, 5], gt[:, 6], gt[:, 7]
gyaw = np.unwrap(np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))) - np.pi / 2
e = np.degrees((np.unwrap(tr[:, 6]) - np.interp(tr[:, 0], gt[:, 0], gyaw) + np.pi) % (2 * np.pi) - np.pi)
R = math.radians(5.0) ** 2
print(f"{a.trial}: headings evaluated {len(L)}, accepted {int(L[:, 3].sum())}, gated {int(len(L) - L[:, 3].sum())}")
for b in np.arange(a.t0, a.t1, a.bin):
    w = (L[:, 0] >= b) & (L[:, 0] < b + a.bin); wt = (tr[:, 0] >= b) & (tr[:, 0] < b + a.bin)
    inn = np.degrees(np.sqrt(L[w, 2] * L[w, 4])) if w.any() else np.array([np.nan])
    sig = np.degrees(np.sqrt(np.maximum(L[w, 4] - R, 0))) if w.any() else np.array([np.nan])
    print(f"  {b:5.0f}-{b + a.bin:3.0f}s FGO hdg eval {w.sum():2d} acc {int(L[w, 3].sum()):2d} | max NIS {L[w, 2].max() if w.any() else np.nan:5.2f}"
          f" max|inn| {inn.max():5.2f} deg | pred sigma med {np.median(sig):.2f} deg | replayed FGO yaw err {e[wt].min():+.2f}..{e[wt].max():+.2f}")
