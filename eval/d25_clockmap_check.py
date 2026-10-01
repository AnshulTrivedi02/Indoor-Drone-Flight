#!/usr/bin/env python3
"""D25: old vs new fgo_node._sitl_us on a recorded /imu/time_ref stream (arrival order = bag order), queried at
30 Hz keyframe times. Reports: (1) agreement after the new map settles (identical when no outliers); (2) with one
synthetic -145 ms offset injected at start-up, the old map's future-stamp error and how long it lasts, and the
new map's. Usage (venv-fgo with ROS sourced): python3 eval/d25_clockmap_check.py TRIAL"""
import os, sys, types
from collections import deque
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "estimators", "fgo"))
import fgo_node
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ts = get_typestore(Stores.ROS2_JAZZY); H = []
with Reader(os.path.expanduser(f"~/thesis_data/trials/{sys.argv[1]}/bag")) as r:
    for c, _, raw in r.messages(connections=[c for c in r.connections if c.topic == "/imu/time_ref"]):
        m = ts.deserialize_cdr(raw, c.msgtype)
        H.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.time_ref.sec + m.time_ref.nanosec * 1e-9))
H = np.array(H)
def run(H, outlier):
    new = types.SimpleNamespace(_toff=deque(), _tref_t0=None, _toff_early=[], _n_unsettled=0, _n_outl_max=0, _n_maps_with_outliers=0)
    oldq = deque(); res = []; t_next = H[0, 0]
    for i, (th, ts_) in enumerate(H):
        off = th - ts_ - (0.145 if (outlier and i == 5) else 0.0)
        new._tref_t0 = th if new._tref_t0 is None else new._tref_t0
        new._toff.append((th, off)); oldq.append((th, off))
        while new._toff[0][0] < th - 10.0: new._toff.popleft()
        while oldq[0][0] < th - 10.0: oldq.popleft()
        if th >= t_next:
            t_next += 1 / 30
            true_us = (th - (H[i, 0] - H[i, 1])) * 1e6        # this sample's own SITL time
            o = (th - min(x for _, x in oldq)) * 1e6
            n = fgo_node.FgoNode._sitl_us(new, th)
            res.append((th, o - true_us, np.nan if n is None else n - true_us, np.nan if n is None else n - o))
    return np.array(res), new
for outlier in (False, True):
    R, st = run(H, outlier); t0 = H[0, 0]; s = ~np.isnan(R[:, 2])
    print(f"outlier={outlier}: first new output at +{R[s, 0][0] - t0:.2f} s; after settle new-old max |diff| {np.nanmax(np.abs(R[s, 3])) / 1e3:.3f} ms;"
          f" old future-stamp (old - own SITL time > 0) max {R[:, 1].max() / 1e3:+.1f} ms over {np.sum(R[:, 1] > 1000) / 30:.1f} s;"
          f" new max {np.nanmax(R[s, 2]) / 1e3:+.1f} ms; maps with outliers {st._n_maps_with_outliers}, max outliers {st._n_outl_max}")
