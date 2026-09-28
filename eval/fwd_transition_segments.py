#!/usr/bin/env python3
"""Phase 3 heading/yaw-rate accuracy on the transition world, split by floor segment:
checkerboard (GT y < 80 m) vs blank (GT y > 80 m), frozen parameters. Evaluation only.

Usage (venv-fwd): python3 eval/fwd_transition_segments.py [--json OUT]
"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd_eval as E

ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
cal = json.load(open(os.path.join(E.RES, "fwd_calibration.json")))["frozen"]
out = {}
for d in ("fwdc", "fwdplainc"):
    for r in (1, 2, 3):
        t = f"{d}_trans_r{r}"
        data = E.load(t, "meas_frozen.npz"); g = data[0]
        ti = list(g["inlier_grid"]).index(cal["inlier_deg"]); bj = list(g["box_grid"]).index(cal["box_half_px"])
        _, _, ep, vp, ew, vw = E.eval_params(t, data, ti, cal["s_min"], bj, cal["n_min"])
        _, _, cruise, y = data[1], data[2], data[3], data[4]
        vpsi = np.isfinite(g["psi"][:, ti]) & (g["support"][:, ti] >= cal["s_min"])
        vom = np.isfinite(g["omega"][:, ti, bj]) & (g["n_trk"][:, ti, bj] >= cal["n_min"])
        for seg, m in (("checker_y<80", y < 80), ("blank_y>80", y > 80)):
            c = cruise & m
            out[f"{t}/{seg}"] = {"psi": E.metrics(ep, vpsi, c, y, E.BAR["psi"]),
                                 "omega": E.metrics(ew, vom, c, y, E.BAR["omega"])}
for k, v in out.items():
    p, w = v["psi"], v["omega"]
    print(f"{k:32} psi: avail {p['avail_pct']:5.1f}% bias {p['bias']:+.3f} sd {p['noise_sd']:.3f} out {p['outlier_pct']:5.2f}% | "
          f"omega: avail {w['avail_pct']:5.1f}% bias {w['bias']:+.4f} sd {w['noise_sd']:.3f} out {w['outlier_pct']:5.2f}%")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
