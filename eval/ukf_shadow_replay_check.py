#!/usr/bin/env python3
"""Part 4: check the shadow UKF (AP_NavUKF, ~/ardupilot_ukf) run in ArduPilot Replay on a flown log.
Reads the Replay CSV (ukf_shadow.csv) and the ORIGINAL log's SIM truth; reports health, the
validity rule (horiz_pos_rel from nav_filter_status), its change times relative to cruise start,
and the position error growth (estimate re-referenced to truth at cruise start).
Usage (venv-evo + pymavlink shim): python3 eval/ukf_shadow_replay_check.py CSV ORIGINAL_BIN [--json OUT]"""
import argparse, json, math
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("bin"); ap.add_argument("--json"); a = ap.parse_args()
c = np.genfromtxt(a.csv, delimiter=",", names=True)
g = []; mo = mavutil.mavlink_connection(a.bin)
while True:
    x = mo.recv_match(type=["SIM"])
    if x is None:
        break
    g.append((x.TimeUS / 1e6, x.Lat, x.Lng))
g = np.array(g); lat, lng = g[:, 1], g[:, 2]
if abs(lat).max() > 1000:
    lat = lat / 1e7; lng = lng / 1e7
N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
vN = np.convolve(np.gradient(N, g[:, 0]), np.ones(25) / 25, "same"); cr = g[vN > 0.3, 0]; c0, c1 = cr[0], cr[-1]
tu = c["TimeUS"] / 1e6; ss = c["SS"].astype(np.int64); hpos = (ss >> 3) & 1; dr = (ss >> 18) & 1
w = (tu >= c0) & (tu <= c1); svh = np.hypot(c["SVN"], c["SVE"])
ch = np.where(np.diff(hpos) != 0)[0]
out = {"cruise_s": [float(c0), float(c1)], "healthy_pct": float(100 * c["Healthy"][w].mean()),
       "valid_pct": float(100 * hpos[w].mean()), "dead_reckoning_pct": float(100 * dr[w].mean()),
       "flow_accepted_xy": [int(c["FXa"][-1]), int(c["FYa"][-1])], "range_accepted": int(c["Ra"][-1]),
       "validity_changes": [{"t_rel_cruise_s": round(float(tu[i + 1] - c0), 2), "valid": int(hpos[i + 1]),
                             "flow_age_ms": int(c["FlowAgeMs"][i + 1]), "sigma_vh": round(float(svh[i + 1]), 3)} for i in ch[:20]],
       "error": {}}
i0 = np.argmin(abs(tu - c0)); j0 = np.argmin(abs(g[:, 0] - c0))
for dt in (5, 10, 30, 60, 150, float(c1 - c0 - 2)):
    tq = c0 + dt; i = np.argmin(abs(tu - tq)); j = np.argmin(abs(g[:, 0] - tq))
    out["error"][f"+{dt:.0f}s"] = {"along_N": float((c["PN"][i] - c["PN"][i0]) - (N[j] - N[j0])),
                                   "cross_E": float((c["PE"][i] - c["PE"][i0]) - (E[j] - E[j0])),
                                   "gt_along": float(N[j] - N[j0]), "sigma_vh": float(svh[i]), "valid": int(hpos[i]),
                                   "flow_age_ms": int(c["FlowAgeMs"][i])}
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
