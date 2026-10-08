#!/usr/bin/env python3
"""T lap flights: optical-flow tracker validity in the post-corner catch-up segments vs the straight segments (user
request 2026-10-08; a shared sensor condition, recorded, no result change unless invalid). Per flow frame in the lap
window: GT horizontal speed (0.2 s boxcar on 20 ms resampled GT, interpolated at the frame stamp).
  catch-up = smoothed speed >= 0.8 m/s; straight = 0.4-0.6 m/s.
Reported per segment: valid-frame share (OpticalFlow.valid), tracked feature count (feature_count) median / p5,
inlier ratio median, and the share of frames with inlier_ratio > 0 (EKF3's acceptance condition: quality > 0).
Usage (venv-tags): python3 eval/t_flow_catchup.py [--json OUT]"""
import argparse, glob, json, os
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "expT")
out = {}; pool = {"catch-up": [], "straight": []}
for c in "ABCD":
    for r in (1, 2, 3):
        t = f"T_{c}_r{r}"; w0, w1 = json.load(open(f"{R}/{t}.json"))["window_s"]
        G, Fl = [], []
        with Reader(os.path.expanduser(f"~/thesis_data/trials/{t}/bag")) as rd:
            cs = {x.topic: x for x in rd.connections}
            for con, _, raw in rd.messages(connections=[cs["/ground_truth/pose"], cs["/optical_flow/measurement"]]):
                m = ts.deserialize_cdr(raw, con.msgtype); tt = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
                if con.topic == "/ground_truth/pose": G.append((tt, m.pose.position.x, m.pose.position.y))
                elif w0 <= tt <= w1: Fl.append((tt, float(m.valid), m.feature_count, m.inlier_ratio))
        G = np.array(G); Fl = np.array(Fl)
        g = np.arange(w0, w1, 0.02); k = np.ones(10) / 10
        xs = np.convolve(np.interp(g, G[:, 0], G[:, 1]), k, "same"); ys = np.convolve(np.interp(g, G[:, 0], G[:, 2]), k, "same")
        sp = np.hypot(np.gradient(xs, g), np.gradient(ys, g)); sp[:10] = sp[-10:] = np.nan
        s_f = np.interp(Fl[:, 0], g, sp)
        out[t] = {}
        for name, sel in (("catch-up", s_f >= 0.8), ("straight", (s_f >= 0.4) & (s_f <= 0.6))):
            F = Fl[sel]; pool[name].append(F)
            out[t][name] = {"frames": int(len(F)), "valid_share": float(F[:, 1].mean()), "features_median": float(np.median(F[:, 2])),
                            "features_p5": float(np.percentile(F[:, 2], 5)), "inlier_median": float(np.median(F[:, 3])),
                            "quality_gt0_share": float((F[:, 3] > 0).mean())}
        print(t, " | ".join(f"{n}: n {v['frames']} valid {v['valid_share']:.3f} feat {v['features_median']:.0f} (p5 {v['features_p5']:.0f}) "
                              f"inlier {v['inlier_median']:.3f}" for n, v in out[t].items()))
for name, L in pool.items():
    F = np.vstack(L)
    out[f"pooled {name}"] = {"frames": int(len(F)), "valid_share": float(F[:, 1].mean()), "features_median": float(np.median(F[:, 2])),
                             "features_p5": float(np.percentile(F[:, 2], 5)), "inlier_median": float(np.median(F[:, 3])),
                             "quality_gt0_share": float((F[:, 3] > 0).mean())}
    print(f"POOLED {name}:", out[f"pooled {name}"])
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
