#!/usr/bin/env python3
"""UKF port validation STEP 2, part 3: compare the C++ port's states (UKF_Equiv harness output)
with the offline Python UKF's (ukf_event_export.py), E1-E5 as PRE-REGISTERED (METHODOLOGY
"Step 1. Agreement criterion, PRE-REGISTERED before any equivalence test"):
  E1 3-D position diff, dsn_tex_r2: max <= 0.05 m, rms <= 0.01 m
  E2 3-D position diff, dsn_blank_r1: max <= 0.05 m + 1e-4 x the offline UKF's displacement from cruise start
  E3 yaw diff: max <= 0.05 deg (both logs)
  E4 gyro-z bias (rate form) |d| <= 0.1 deg/min; accel bias |d| <= 0.001 m/s^2
  E5 gate decisions (flow X/Y, range, yaw-pseudo firings) >= 99.9% identical; accepted counts within 0.1%
over the PINNED cruise window (cruise_window.cruise_bounds on the replay's GT). Event times: the
k-th predict is the k-th row of the replay's ukf_traj.tum (one row per predict); every other event
takes the time of the preceding predict.
Usage (~/venv-evo): python3 eval/ukf_equivalence.py PREFIX --log tex|blank [--json OUT]
  PREFIX = the export prefix (PREFIX.npz, PREFIX_port.bin, PREFIX_replay_out/ukf/)"""
import argparse, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds

ap = argparse.ArgumentParser(); ap.add_argument("prefix"); ap.add_argument("--log", required=True, choices=["tex", "blank"])
ap.add_argument("--json"); a = ap.parse_args()
e = np.load(a.prefix + ".npz")
typ, inp, xp, flp = e["type"], e["inputs"], e["x_after"], e["flags"]
n = len(typ)
raw = np.fromfile(a.prefix + "_port.bin", dtype=np.uint8)
rec = 15 * 8 + 2
assert raw.size == n * rec, (raw.size, n * rec)
raw = raw.reshape(n, rec)
xc = raw[:, :120].copy().view(np.float64).reshape(n, 15)
flc = raw[:, 120:].astype(np.int8)

tum = np.loadtxt(a.prefix + "_replay_out/ukf/ukf_traj.tum")
gt = np.loadtxt(a.prefix + "_replay_out/ukf/ground_truth.tum")
pred_idx = np.where(typ == 0)[0]
assert len(pred_idx) == len(tum), (len(pred_idx), len(tum))
t_ev = np.full(n, np.nan); t_ev[pred_idx] = tum[:, 0]
last = tum[0, 0]
for i in range(n):                       # forward-fill: time of the preceding predict
    if np.isnan(t_ev[i]):
        t_ev[i] = last
    else:
        last = t_ev[i]
c0, c1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
w = (t_ev >= c0) & (t_ev <= c1)

dpos = np.linalg.norm(xc[:, 0:3] - xp[:, 0:3], axis=1)
dyaw = np.degrees(np.abs((xc[:, 8] - xp[:, 8] + math.pi) % (2 * math.pi) - math.pi))
dt_step = inp[pred_idx, 6].mean()
dbgz = np.abs(xc[:, 11] - xp[:, 11]) / dt_step * (180 / math.pi) * 60           # deg/min
dba = np.abs(xc[:, 12:15] - xp[:, 12:15]).max(1) / dt_step                        # m/s^2
out = {"log": a.log, "events": int(n), "window_s": [float(c0), float(c1)], "events_in_window": int(w.sum()),
       "dt_step_s": float(dt_step)}
out["E1_E2"] = {"max_m": float(dpos[w].max()), "rms_m": float(np.sqrt(np.mean(dpos[w] ** 2))),
                "at_end_m": float(dpos[w][-1])}
if a.log == "tex":
    out["E1_E2"]["band"] = "max <= 0.05, rms <= 0.01"
    out["E1_E2"]["pass"] = out["E1_E2"]["max_m"] <= 0.05 and out["E1_E2"]["rms_m"] <= 0.01
else:
    i0 = np.where(w)[0][0]
    disp = np.linalg.norm(xp[:, 0:3] - xp[i0, 0:3], axis=1)
    allow = 0.05 + 1e-4 * disp
    out["E1_E2"]["band"] = "diff <= 0.05 + 1e-4 x offline displacement from cruise start (per event)"
    out["E1_E2"]["worst_margin_ratio"] = float((dpos[w] / allow[w]).max())
    out["E1_E2"]["offline_disp_end_m"] = float(disp[w][-1])
    out["E1_E2"]["pass"] = bool((dpos[w] <= allow[w]).all())
out["E3"] = {"max_deg": float(dyaw[w].max()), "pass": float(dyaw[w].max()) <= 0.05}
out["E4"] = {"max_gyro_z_bias_deg_per_min": float(dbgz[w].max()), "max_accel_bias_mps2": float(dba[w].max())}
out["E4"]["pass"] = out["E4"]["max_gyro_z_bias_deg_per_min"] <= 0.1 and out["E4"]["max_accel_bias_mps2"] <= 0.001
E5 = {}
ok = True
for name, tsel, col in (("flow_x", 2, 0), ("flow_y", 2, 1), ("range", 1, 0), ("yaw_pseudo", 3, 0)):
    s = (typ == tsel) & w
    same = float(np.mean(flp[s, col] == flc[s, col])) if s.any() else 1.0
    ap_, ac_ = int(flp[s, col].sum()), int(flc[s, col].sum())
    rel = abs(ap_ - ac_) / max(ap_, 1)
    E5[name] = {"n": int(s.sum()), "identical_frac": same, "accepted_python": ap_, "accepted_port": ac_, "count_rel_diff": rel}
    ok = ok and same >= 0.999 and rel <= 0.001
E5["pass"] = ok
out["E5"] = E5
# where does the difference start? (diagnostic): first event with |dpos| > 1e-6 m or |dyaw| > 1e-6 deg
bad = np.where((dpos > 1e-6) | (dyaw > 1e-6))[0]
out["diag_first_divergence"] = None if not len(bad) else {"event": int(bad[0]), "type": int(typ[bad[0]]), "t": float(t_ev[bad[0]]),
                                                            "dpos_m": float(dpos[bad[0]]), "dyaw_deg": float(dyaw[bad[0]])}
out["diag_first_event_diff"] = {"dpos_m": float(dpos[0]), "dyaw_deg": float(dyaw[0])}
out["pass"] = all(out[k]["pass"] for k in ("E1_E2", "E3", "E4", "E5"))
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
