#!/usr/bin/env python3
"""F2 and F3 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — offline tests F1, F2, F3").
Frames as f1_eval: estimator yaw in the corridor frame; truth psi = GT ENU yaw - 90 deg (gt_eval_only.npz);
cross-track = estimator East (-y, corridor frame) - GT East (x), from the spawn origin.
  f2: fwdc_tex_r1..r3, mask 30 s on / 30 s off from cruise start. OFF-interval yaw RMS and cross-track RMS for
      UKF live, FGO live (0.25 s) and FGO batch (hindsight). Decision: batch hindsight OFF yaw RMS below both
      live arms on all 3 bags.
  f3: fwdc_tex_r1..r3, delta in {10,30,60,90} deg (initial yaw offset, prior sigma = delta, headings from cruise
      start). From cruise start: convergence time (first |yaw err| < 1 deg held 5 s), peak |cross-track| over the
      cruise, integrated |cross-track| over the first 60 s. Decision: FGO/UKF integrated-error ratio decreasing
      monotonically with delta on >= 2 of 3 bags.
Usage (venv-fgo): python3 eval/f23_eval.py f2|f3 [--json OUT]"""
import argparse, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds
TD = os.path.expanduser("~/thesis_data/trials")
BAGS = ("fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3")
wrap = lambda a: (a + np.pi) % (2 * np.pi) - np.pi


def load(path):
    d = np.loadtxt(path); qx, qy, qz, qw = d[:, 4], d[:, 5], d[:, 6], d[:, 7]
    return d[:, 0], d[:, 1], d[:, 2], np.unwrap(np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz)))


def errors(path, g):
    t, x, y, yaw = load(path)
    ye = np.degrees(wrap(yaw - (np.interp(t, g[:, 0], g[:, 3]) - np.pi / 2)))
    xt = -y - np.interp(t, g[:, 0], g[:, 1])
    return t, ye, xt


ap = argparse.ArgumentParser(); ap.add_argument("test", choices=["f2", "f3"]); ap.add_argument("--json"); a = ap.parse_args()
out = {}
for tr in BAGS:
    g = np.load(f"{TD}/{tr}/fwd_meas/gt_eval_only.npz")["g"]
    c0, c1 = cruise_bounds(g[:, 0], g[:, 1], g[:, 2])
    if a.test == "f2":
        arms = {"UKF_live": f"{TD}/{tr}/ukf_heading_F2mask/ukf_traj.tum", "FGO_live": f"{TD}/{tr}/fgo_heading_F2mask/fgo_traj.tum",
                "FGO_batch_hindsight": f"{TD}/{tr}/fgo_heading_F2mask/fgo_batch_traj.tum"}
        r = {}
        for name, p in arms.items():
            t, ye, xt = errors(p, g)
            off = (t >= c0) & (t <= c1) & (((t - c0) % 60.0) >= 30.0)
            on = (t >= c0) & (t <= c1) & ~(((t - c0) % 60.0) >= 30.0)
            r[name] = {"off_yaw_rms_deg": float(np.sqrt(np.mean(ye[off] ** 2))), "off_xtrack_rms_m": float(np.sqrt(np.mean(xt[off] ** 2))),
                       "on_yaw_rms_deg": float(np.sqrt(np.mean(ye[on] ** 2)))}
        out[tr] = r
    else:
        r = {}
        for d in (10, 30, 60, 90):
            for est in ("ukf", "fgo"):
                t, ye, xt = errors(f"{TD}/{tr}/{est}_heading_F3d{d}/{est}_traj.tum", g)
                w = (t >= c0) & (t <= c1); tt, ee, xx = t[w], np.abs(ye[w]), np.abs(xt[w])
                conv = None
                for i in range(len(tt)):
                    if ee[i] < 1.0:
                        j = np.searchsorted(tt, tt[i] + 5.0)
                        if j <= len(tt) and np.all(ee[i:j] < 1.0):
                            conv = float(tt[i] - c0); break
                w60 = tt <= c0 + 60.0
                r[f"{est.upper()}_d{d}"] = {"convergence_s": conv, "xtrack_peak_m": float(xx.max()),
                                            "xtrack_int_60s_ms": float(np.trapz(xx[w60], tt[w60]))}
        ratios = [r[f"FGO_d{d}"]["xtrack_int_60s_ms"] / max(r[f"UKF_d{d}"]["xtrack_int_60s_ms"], 1e-9) for d in (10, 30, 60, 90)]
        r["fgo_over_ukf_int_ratio"] = ratios
        r["ratio_decreasing"] = bool(all(ratios[i + 1] < ratios[i] for i in range(3)))
        out[tr] = r
    print(tr, json.dumps(out[tr], default=lambda v: round(v, 3) if isinstance(v, float) else v))
if a.test == "f2":
    ok = all(out[t]["FGO_batch_hindsight"]["off_yaw_rms_deg"] < min(out[t]["UKF_live"]["off_yaw_rms_deg"], out[t]["FGO_live"]["off_yaw_rms_deg"]) for t in BAGS)
    out["decision"] = {"hindsight_correction": bool(ok)}
else:
    out["decision"] = {"fgo_advantage_grows": bool(sum(out[t]["ratio_decreasing"] for t in BAGS) >= 2)}
print("DECISION", json.dumps(out["decision"]))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
