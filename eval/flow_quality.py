#!/usr/bin/env python3
"""Downward-flow quality per trial — the Phase 1 confound check (b).

This checks that downward-flow conditions on the `corridor_*_fwd` worlds are the
same as on the `dsn_*` worlds. It is read straight from each trial's bag
(`/optical_flow/measurement`, `/ground_truth/pose`), so it needs no estimator replay.

Per trial, over the cruise window (`eval/cruise_window.py`, from the bag's ground truth):
  inlier_ratio   mean, median, % of frames below 0.5
  feature_count  mean
  flow_y_raw     mean (px/s), the forward translational flow
  GT lateral x   min/max (m), which bounds the downward footprint's distance to the walls
  transition     the GT y where the 2 m-binned mean inlier_ratio first falls below 0.65
                 (midpoint of the textured ~0.97 and blank ~0.31 levels) — only
                 reported for trials whose name contains 'trans'. Bins sit on a fixed
                 absolute 2 m grid, so the switch location lines up across trials.

Usage (venv-evo: rosbags + numpy): python3 eval/flow_quality.py TRIAL [TRIAL...] [--json OUT]
"""
import argparse, glob, json, os
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from cruise_window import cruise_bounds

TRIALS_DIR = os.path.expanduser("~/thesis_data/trials")
TRANSITION_LEVEL, BIN_M = 0.65, 2.0

ts = get_typestore(Stores.ROS2_JAZZY)
_msg = glob.glob(os.path.expanduser("~/thesis_ws/src/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(_msg).read(), "optical_flow_interfaces/msg/OpticalFlow"))


def stamp(h):
    return h.stamp.sec + h.stamp.nanosec * 1e-9


def analyse(trial):
    gt, fl = [], []
    with Reader(f"{TRIALS_DIR}/{trial}/bag") as r:
        conns = [c for c in r.connections if c.topic in ("/ground_truth/pose", "/optical_flow/measurement")]
        for con, _, raw in r.messages(connections=conns):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/ground_truth/pose":
                gt.append((stamp(m.header), m.pose.position.x, m.pose.position.y))
            else:
                fl.append((stamp(m.header), m.inlier_ratio, m.feature_count, m.flow_y_raw))
    gt, fl = np.array(sorted(gt)), np.array(sorted(fl))
    t0, t1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
    w = (fl[:, 0] >= t0) & (fl[:, 0] <= t1)
    f = fl[w]
    gy = np.interp(f[:, 0], gt[:, 0], gt[:, 2])
    gw = (gt[:, 0] >= t0) & (gt[:, 0] <= t1)
    out = {"cruise_s": [float(t0), float(t1)], "n_frames": int(len(f)),
           "inlier_mean": float(f[:, 1].mean()), "inlier_median": float(np.median(f[:, 1])),
           "inlier_pct_below_0.5": float(100 * (f[:, 1] < 0.5).mean()),
           "features_mean": float(f[:, 2].mean()), "flow_y_raw_mean": float(f[:, 3].mean()),
           "gt_x_range": [float(gt[gw, 1].min()), float(gt[gw, 1].max())]}
    if "transition" in trial or "trans" in trial:
        edges = np.arange(0.0, 170.0 + BIN_M, BIN_M)        # absolute grid, identical across trials
        k = np.digitize(gy, edges)
        bins = [(edges[i - 1], f[k == i, 1].mean()) for i in range(1, len(edges)) if (k == i).sum() > 5]
        sw = next((lo + BIN_M / 2 for lo, v in bins if v < TRANSITION_LEVEL), None)
        side = lambda a, b: f[(gy >= a) & (gy < b), 1].mean()
        out.update({"switch_gt_y": sw, "inlier_y<75": float(side(-1e9, 75)),
                    "inlier_y>85": float(side(85, 1e9))})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("trials", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = {t: analyse(t) for t in a.trials}
    for t, r in res.items():
        s = (f"{t:22} inlier mean {r['inlier_mean']:.4f} med {r['inlier_median']:.3f} "
             f"<0.5 {r['inlier_pct_below_0.5']:5.1f}%  feat {r['features_mean']:5.1f}  "
             f"flow_y {r['flow_y_raw_mean']:7.2f} px/s  GT x [{r['gt_x_range'][0]:+.2f},{r['gt_x_range'][1]:+.2f}]")
        if "switch_gt_y" in r:
            s += f"  switch y {r['switch_gt_y']}  (y<75 {r['inlier_y<75']:.3f} / y>85 {r['inlier_y>85']:.3f})"
        print(s)
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
