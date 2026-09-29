#!/usr/bin/env python3
"""Heading share of EKF3's lateral drift on the pinned cruise window (the batched correction
(iii) method: eval/phase5_analysis.ekf3 on dsn_tex_r1..r3, window from the dsn evo JSON).
Usage (venv-ardupilot): python3 eval/heading_share.py DSN_EVO_JSON --json OUT"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase5_analysis import ekf3
ap = argparse.ArgumentParser(); ap.add_argument("evo"); ap.add_argument("--json", required=True); a = ap.parse_args()
tr = json.load(open(a.evo))["trials"]; out = {}
for t in ("dsn_tex_r3", "dsn_tex_r1", "dsn_tex_r2"):
    out[t] = ekf3(t, tr[t]["window_s"])
    print(t, {k: round(v, 4) for k, v in out[t].items() if v is not None})
json.dump(out, open(a.json, "w"), indent=1)
