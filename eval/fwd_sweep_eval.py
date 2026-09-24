#!/usr/bin/env python3
"""Phase 3 supplementary check: static heading response (METHODOLOGY, pre-registered).

Frames from sim/tools/yaw_sweep.sh: each world at y in {20, 100, 140} m, z = 2.3 m, with
yaw offsets {-10, -5, -2, 0, 2, 5, 10} deg from the corridor axis (positive = nose left,
matching psi). The FROZEN heading method (eval/results/fwd_calibration.json) is applied
per frame. Per world: least-squares fit psi = a + slope * offset over the valid outputs.
Bar: slope within 1 +- 0.05, and every |fit residual| <= 0.5 deg. The direct error
psi - offset is also reported. The commanded pose is the truth: the scene is paused and
stepped only to render, which is what render_check.sh does too.

Usage (venv-fwd): python3 eval/fwd_sweep_eval.py [--json OUT]
"""
import argparse, glob, json, os, sys
import numpy as np
import cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "forward_camera"))
import fwd_measure as F

SW = os.path.expanduser("~/thesis_data/phase3_yaw_sweep")
CAL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "fwd_calibration.json")))["frozen"]

ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
out = {}
for wdir in sorted(glob.glob(f"{SW}/*_fwd*c")):
    world = os.path.basename(wdir); rows = []
    for f in sorted(glob.glob(f"{wdir}/y*_yaw*/forward_camera_image.png")):
        tag = os.path.basename(os.path.dirname(f)); y, off = tag[1:].split("_yaw")
        img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        h = F.heading(img, seed=0, inlier_deg=CAL["inlier_deg"])
        ok = h["psi_deg"] is not None and h["support"] >= CAL["s_min"]
        rows.append({"y": float(y), "offset": float(off), "psi": h["psi_deg"], "support": h["support"], "valid": bool(ok)})
    v = [r for r in rows if r["valid"]]
    if len(v) >= 2:
        x = np.array([r["offset"] for r in v]); p = np.array([r["psi"] for r in v])
        slope, icpt = np.polyfit(x, p, 1); res = p - (icpt + slope * x); err = p - x
        m = {"n_frames": len(rows), "n_valid": len(v), "slope": float(slope), "intercept": float(icpt),
             "max_abs_fit_residual": float(np.abs(res).max()), "max_abs_error": float(np.abs(err).max()),
             "rms_error": float(np.sqrt(np.mean(err ** 2)))}
        m["pass"] = bool(abs(slope - 1) <= 0.05 and m["max_abs_fit_residual"] <= 0.5)
    else:
        m = {"n_frames": len(rows), "n_valid": len(v), "pass": False}
    m["rows"] = rows; out[world] = m
    print(f"{world:22} valid {m['n_valid']}/{m['n_frames']}  " + (f"slope {m['slope']:.4f}  max|fit res| {m['max_abs_fit_residual']:.3f}  max|err| {m['max_abs_error']:.3f}  rms err {m['rms_error']:.3f}  " if 'slope' in m else "") + ("PASS" if m["pass"] else "fail"))
    bad = [r for r in rows if r["valid"] and abs(r["psi"] - r["offset"]) > 0.5] + [r for r in rows if not r["valid"]]
    for r in bad:
        print(f"    y={r['y']:.0f} off={r['offset']:+.0f}: psi={'-' if r['psi'] is None else round(r['psi'], 2)} support={r['support']:.0f} valid={r['valid']}")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
