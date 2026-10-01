#!/usr/bin/env python3
"""Cruise-window audit (user ruling 2026-10-02, after D28): can a spurious ground-truth sample change the PINNED
cruise window (eval/cruise_window.cruise_bounds)? For every trial with a bag, the pinned window is computed on the GT
exactly as the evaluations do, and again after removing spurious samples:
  (1) near-duplicate stamps: a sample < 2 ms after its predecessor (the known GT artefact; it inflates the speed
      gradient), and
  (2) isolated jumps: a sample whose implied speed from BOTH neighbours exceeds 3 m/s (impossible at <= 0.6 m/s).
Reported per trial: pinned [t0, t1] and length, despiked [t0, t1], |delta| at each end, and the number of samples
removed. A trial is FLAGGED if either end moves by more than 0.05 s (about two GT samples).
Usage (venv-evo): python3 eval/cruise_window_audit.py [TRIAL...] [--json OUT]   (default: every trial with a bag)"""
import argparse, glob, json, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="*"); ap.add_argument("--json"); a = ap.parse_args()
TD = os.path.expanduser("~/thesis_data/trials")
trials = a.trials or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(f"{TD}/*/bag/metadata.yaml"))
ts = get_typestore(Stores.ROS2_JAZZY); out = {}
for tr in trials:
    try:
        g = []
        with Reader(f"{TD}/{tr}/bag") as r:
            cs = [c for c in r.connections if c.topic == "/ground_truth/pose"]
            if not cs:
                continue
            for c, _, raw in r.messages(connections=cs):
                m = ts.deserialize_cdr(raw, c.msgtype)
                g.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y))
    except Exception as e:
        out[tr] = {"error": str(e)[:120]}; continue
    g = np.array(sorted(g))
    if len(g) < 100:
        continue
    t, x, y = g[:, 0], g[:, 1], g[:, 2]
    p0, p1 = cruise_bounds(t, x, y)
    keep = np.r_[True, np.diff(t) >= 0.002]
    t2, x2, y2 = t[keep], x[keep], y[keep]
    d = np.hypot(np.diff(x2), np.diff(y2)) / np.diff(t2)
    jump = np.r_[False, (d[:-1] > 3.0) & (d[1:] > 3.0), False]
    t2, x2, y2 = t2[~jump], x2[~jump], y2[~jump]
    q0, q1 = cruise_bounds(t2, x2, y2)
    r = {"pinned": [round(p0, 3), round(p1, 3)], "len_s": round(p1 - p0, 2), "despiked": [round(q0, 3), round(q1, 3)],
         "d0_s": round(abs(q0 - p0), 3), "d1_s": round(abs(q1 - p1), 3), "n_dup_removed": int((~keep).sum()), "n_jump_removed": int(jump.sum())}
    r["flag"] = bool(r["d0_s"] > 0.05 or r["d1_s"] > 0.05)
    out[tr] = r
    if r["flag"]:
        print(f"FLAG {tr}: pinned {r['pinned']} -> despiked {r['despiked']} (dup {r['n_dup_removed']}, jump {r['n_jump_removed']})", flush=True)
n = len([v for v in out.values() if "flag" in v]); f = [k for k, v in out.items() if v.get("flag")]
lens = sorted((v["len_s"], k) for k, v in out.items() if "len_s" in v)
print(f"audited {n} trials; flagged {len(f)}: {f}")
print("shortest windows:", lens[:6]); print("longest windows:", lens[-4:])
print("errors:", {k: v["error"] for k, v in out.items() if "error" in v})
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
