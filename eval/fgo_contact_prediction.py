#!/usr/bin/env python3
"""D19: the FGO no-heading contact prediction by the method VALIDATED in set (a) (the estimator's open-loop
East error against truth, from the spawn origin, reaching 9.58 m; METHODOLOGY "D16 check"). Offline FGO
trajectories (fgo/fgo_traj.tum, CORRIDOR frame: x along the corridor = North, y = West) against the bag GT
(fgo/ground_truth.tum, ENU: x = East). East_est = -y_fgo. Estimate East of truth (+) -> the vehicle is steered
WEST. Usage (venv-evo): python3 eval/fgo_contact_prediction.py TRIAL... [--sub fgo] [--json OUT]"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--sub", default="fgo"); ap.add_argument("--json")
a = ap.parse_args(); TD = os.path.expanduser("~/thesis_data/trials"); out = []
for tr in a.trials:
    f = np.loadtxt(f"{TD}/{tr}/{a.sub}/fgo_traj.tum"); g = np.loadtxt(f"{TD}/{tr}/{a.sub}/ground_truth.tum")
    c0, c1 = cruise_bounds(g[:, 0], g[:, 1], g[:, 2])
    w = (f[:, 0] >= c0) & (f[:, 0] <= c1)
    eE = -f[w, 2] - np.interp(f[w, 0], g[:, 0], g[:, 1])
    hit = np.where(np.abs(eE) >= 9.58)[0]
    r = {"trial": tr, "east_err_c0_m": float(eE[0]), "east_err_end_m": float(eE[-1]),
         "contact_s": None if not len(hit) else float(f[w, 0][hit[0]] - c0),
         "wall": None if not len(hit) else ("west" if eE[hit[0]] > 0 else "east")}
    out.append(r); print(json.dumps(r))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
