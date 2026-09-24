#!/usr/bin/env python3
"""Transition-world forward flow: ceiling vs no-ceiling effect size (user ruling
2026-09-24, bounded quantification: data on disk only, no mechanism investigation).

Per bag, over the cruise window (the same frame selection as eval/flow_quality.py):
mean `flow_y_raw` over all cruise frames, over the textured half (GT y < 75 m) and over
the blank half (GT y > 85 m). The 75/85 m cut-offs are flow_quality's own level
windows, which exclude the 80 m boundary. Then ceiling (8) vs no-ceiling (8) group
means, difference, and Welch's two-sample t-test.

Usage (venv-evo): python3 eval/ceiling_flow_effect.py [--json OUT]
"""
import argparse, glob, json, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds

TD = os.path.expanduser("~/thesis_data/trials")
NO_CEIL = ["dsn_trans_r1", "dsn_trans_r2", "dsn_trans_r3", "fwd_trans_r1", "fwd_trans_r2",
           "fwd_trans_r3", "p1_fwd_trans", "p1plain_trans"]
CEIL = ["p1c_fwdc_trans", "p1c_fwdplainc_trans", "fwdc_trans_r1", "fwdc_trans_r2",
        "fwdc_trans_r3", "fwdplainc_trans_r1", "fwdplainc_trans_r2", "fwdplainc_trans_r3"]
ts = get_typestore(Stores.ROS2_JAZZY)
_msg = glob.glob(os.path.expanduser("~/thesis_ws/src/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(_msg).read(), "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9


def per_bag(trial):
    gt, fl = [], []
    with Reader(f"{TD}/{trial}/bag") as r:
        conns = [c for c in r.connections if c.topic in ("/ground_truth/pose", "/optical_flow/measurement")]
        for con, _, raw in r.messages(connections=conns):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/ground_truth/pose":
                gt.append((st(m.header), m.pose.position.x, m.pose.position.y))
            else:
                fl.append((st(m.header), m.flow_y_raw))
    gt, fl = np.array(sorted(gt)), np.array(sorted(fl))
    t0, t1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
    f = fl[(fl[:, 0] >= t0) & (fl[:, 0] <= t1)]
    gy = np.interp(f[:, 0], gt[:, 0], gt[:, 2])
    return {"all": float(f[:, 1].mean()), "tex_half": float(f[gy < 75, 1].mean()),
            "blank_half": float(f[gy > 85, 1].mean()), "n": int(len(f))}


def welch(a, b):
    a, b = np.asarray(a), np.asarray(b)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    t = (a.mean() - b.mean()) / np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    return float(t), float(df)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
    res = {t: per_bag(t) for t in NO_CEIL + CEIL}
    out = {"per_bag": res, "groups": {}}
    for k in ("all", "tex_half", "blank_half"):
        c, n = [res[t][k] for t in CEIL], [res[t][k] for t in NO_CEIL]
        t, df = welch(c, n)
        out["groups"][k] = {"ceiling_mean": float(np.mean(c)), "ceiling_sd": float(np.std(c, ddof=1)),
                            "no_ceiling_mean": float(np.mean(n)), "no_ceiling_sd": float(np.std(n, ddof=1)),
                            "difference": float(np.mean(c) - np.mean(n)), "welch_t": t, "welch_df": df}
    for t, v in res.items():
        print(f"{t:22} all {v['all']:7.2f}  tex-half {v['tex_half']:7.2f}  blank-half {v['blank_half']:6.2f}")
    for k, g in out["groups"].items():
        print(f"{k:10} ceiling {g['ceiling_mean']:7.3f} (sd {g['ceiling_sd']:.3f})  no-ceiling {g['no_ceiling_mean']:7.3f} (sd {g['no_ceiling_sd']:.3f})  diff {g['difference']:+.3f}  Welch t {g['welch_t']:.3f} df {g['welch_df']:.1f}")
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
