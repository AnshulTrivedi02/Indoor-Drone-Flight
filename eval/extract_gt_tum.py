#!/usr/bin/env python3
"""Write `<trial>/ukf/ground_truth.tum` from the bag alone, with no estimator replay.

`three_way_eval.py` pins every trial's cruise window on `ukf/ground_truth.tum`, which
`ukf_replay.py` normally writes. When the UKF replay cannot run (Phase 2 `fwd_trans_r3`:
the dejitter guard refused the bag), EKF3, which runs live in SITL, is still
evaluable if this file exists. The code below copies `ukf_replay.py`'s ground-truth
path exactly (header stamps, ENU position, identity quaternions, same format), so the
output is byte-identical to what the replay would write. That is checked on a trial
that has a replay before this output is trusted.

Usage (venv-evo: rosbags + numpy): python3 eval/extract_gt_tum.py TRIAL [--out PATH]
"""
import argparse, os
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser()
ap.add_argument("trial")
ap.add_argument("--out", help="default: ~/thesis_data/trials/<trial>/ukf/ground_truth.tum")
a = ap.parse_args()

ts = get_typestore(Stores.ROS2_JAZZY)
gt = []
with Reader(os.path.expanduser(f"~/thesis_data/trials/{a.trial}/bag")) as r:
    conns = [c for c in r.connections if c.topic == "/ground_truth/pose"]
    for con, _, raw in r.messages(connections=conns):
        m = ts.deserialize_cdr(raw, con.msgtype)
        tt = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        gt.append((tt, m.pose.position.x, m.pose.position.y, m.pose.position.z))
gt.sort(key=lambda e: e[0])
gt = np.array(gt)

out = a.out or os.path.expanduser(f"~/thesis_data/trials/{a.trial}/ukf/ground_truth.tum")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    for i in range(len(gt)):
        f.write(f"{gt[i, 0]:.6f} {gt[i, 1]:.6f} {gt[i, 2]:.6f} {gt[i, 3]:.6f} "
                f"{0:.6f} {0:.6f} {0:.6f} {1:.6f}\n")
print(f"wrote {out} ({len(gt)} poses)")
