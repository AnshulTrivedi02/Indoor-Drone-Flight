#!/usr/bin/env python3
"""D26 (b), EXPLORATORY: the heading stream the estimators received in a flight (logs/heading_bridge.csv, sent rows),
against truth. Heading error = wrap(-yaw_ap - (GT ENU yaw - 90 deg)) (the FGO's measurement in the corridor frame),
minus its median over cruise +10..+200 s (yaw_ap is offset-referenced). Per bin: frames, valid frames, sent with
quality >= 50 (what the FGO node and ArduPilot accept as input), heading error median/max, image support.
Usage (venv-fgo): python3 eval/d26_heading_stream.py TRIAL [--t0 290 --t1 338 --bin 3]"""
import argparse, csv, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--t0", type=float, default=290); ap.add_argument("--t1", type=float, default=338)
ap.add_argument("--bin", type=float, default=3.0); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); ts = get_typestore(Stores.ROS2_JAZZY); G = []
with Reader(f"{D}/bag") as r:
    for c, _, raw in r.messages(connections=[c for c in r.connections if c.topic == "/ground_truth/pose"]):
        m = ts.deserialize_cdr(raw, c.msgtype); q = m.pose.orientation
        G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.y, np.arctan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))))
G = np.array(G)
rows = list(csv.DictReader(open(f"{D}/logs/heading_bridge.csv")))
t = np.array([float(r["t_capture"]) for r in rows]); valid = np.array([r["valid"] == "1" for r in rows])
q = np.array([int(r["quality"]) for r in rows]); sent = np.array([r["sent"] == "1" for r in rows])
ya = np.array([float(r["yaw_ap_rad"]) if r["yaw_ap_rad"] not in ("", "nan") else np.nan for r in rows])
sup = np.array([float(r["support"]) if r["support"] else np.nan for r in rows])
wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi
gy = np.interp(t, G[:, 0], np.unwrap(G[:, 2])); y = np.interp(t, G[:, 0], G[:, 1])
err = np.degrees(wrap(-ya - (gy - np.pi / 2)))
use = sent & (q >= 50) & np.isfinite(err)
c0 = t[use][0]; base = np.nanmedian(err[use & (t > c0 + 10) & (t < c0 + 200)]); err = err - base
print(f"{a.trial}: heading error baseline {base:+.3f} deg removed; cruise +10..+200 s |err| p95 {np.percentile(np.abs(err[use & (t > c0 + 10) & (t < c0 + 200)]), 95):.3f} deg")
for b in np.arange(a.t0, a.t1, a.bin):
    w = (t >= b) & (t < b + a.bin); wu = w & use
    e = err[wu]
    print(f"  {b:5.0f}-{b + a.bin:3.0f}s y {y[w].min() if w.any() else np.nan:5.1f}-{y[w].max() if w.any() else np.nan:5.1f} m | frames {w.sum():2d} valid {valid[w].sum():2d} "
          f"sent q>=50 {wu.sum():2d} | err med {np.median(e) if len(e) else np.nan:+.2f} max|.| {np.abs(e).max() if len(e) else np.nan:.2f} deg | support med {np.nanmedian(sup[w]) if w.any() else np.nan:.0f}")
