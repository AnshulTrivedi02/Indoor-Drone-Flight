#!/usr/bin/env python3
"""B5 window check (2026-10-02, a CHECKER BUG found in the robust-FGO set): closed_loop_score.py's B5 window is
(r0 + 5, r1 - 5) with r0/r1 the FIRST/LAST GT sample with smoothed vy > 0.3 m/s. A spurious vy > 0.3 sample at
landing (GT jump at touchdown) moves r1 to ~344 s, so the window takes in the end-of-cruise deceleration (pitch rate
~11 deg/s). Corrected window: the LONGEST CONTIGUOUS run of vy > 0.3 (gaps <= 1 s), then (start + 5, end - 5).
Reports, per flight: both windows and B5 gyro rms (roll/pitch/yaw, band 0.05/0.0108/0.02) with each.
Usage (venv-evo): python3 eval/b5_window_check.py TRIAL... [--json OUT]"""
import argparse, json, os
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
ts = get_typestore(Stores.ROS2_JAZZY); out = {}; BAND = (0.05, 0.0108, 0.02)
for tr in a.trials:
    g, imu = [], []
    with Reader(os.path.expanduser(f"~/thesis_data/trials/{tr}/bag")) as r:
        for c, _, raw in r.messages(connections=[c for c in r.connections if c.topic in ("/ground_truth/pose", "/imu/data_raw")]):
            m = ts.deserialize_cdr(raw, c.msgtype); t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if c.topic == "/ground_truth/pose": g.append((t, m.pose.position.y))
            else: imu.append((t, m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z))
    g = np.array(sorted(g)); imu = np.array(sorted(imu)); t, y = g[:, 0], g[:, 1]
    vy = np.convolve(np.gradient(y, t), np.ones(51) / 51, "same"); tc = t[vy > 0.3]
    def rms(a0, a1):
        s = (imu[:, 0] > a0) & (imu[:, 0] < a1); return [float(imu[s, k].std()) for k in (1, 2, 3)]
    old = (tc[0], tc[-1])
    br = np.where(np.diff(tc) > 1.0)[0]; seg = np.split(tc, br + 1); main = max(seg, key=lambda s: s[-1] - s[0])
    new = (main[0], main[-1])
    ro, rn = rms(old[0] + 5, old[1] - 5), rms(new[0] + 5, new[1] - 5)
    out[tr] = {"window_old": [round(old[0] + 5, 2), round(old[1] - 5, 2)], "rms_old": ro, "pass_old": all(v <= b for v, b in zip(ro, BAND)),
               "window_corrected": [round(new[0] + 5, 2), round(new[1] - 5, 2)], "rms_corrected": rn, "pass_corrected": all(v <= b for v, b in zip(rn, BAND))}
    o = out[tr]
    print(f"{tr:30s} old {o['window_old']} r/p/y {ro[0]:.4f}/{ro[1]:.4f}/{ro[2]:.4f} {'PASS' if o['pass_old'] else 'FAIL'} | corrected {o['window_corrected']} "
          f"{rn[0]:.4f}/{rn[1]:.4f}/{rn[2]:.4f} {'PASS' if o['pass_corrected'] else 'FAIL'}")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
