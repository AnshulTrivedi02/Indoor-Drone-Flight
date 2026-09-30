#!/usr/bin/env python3
"""F3b (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — F3b"): the nonlinearity test. fwdc_tex_r1..r3; delta in
{10,30,60,90} deg with prior sigma 90 deg for all; yaw-bounding priors off in both; headings from cruise start.
Metrics from cruise start as F3 (convergence: |yaw err| < 1 deg held 5 s; peak |cross-track|; integrated
|cross-track| over the first 60 s), plus each estimator's predicted heading sigma and acceptance at the first 40
headings (gate logs). Decisions: (a) FGO convergence <= UKF at every delta on >= 2 of 3 bags ("never" = inf);
(b) FGO/UKF integrated ratio decreasing monotonically with delta on >= 2 of 3 bags.
Usage (venv-fgo): python3 eval/f3b_eval.py [--json OUT]"""
import argparse, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds
TD = os.path.expanduser("~/thesis_data/trials"); BAGS = ("fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3"); DS = (10, 30, 60, 90)
wrap = lambda a: (a + np.pi) % (2 * np.pi) - np.pi
ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args(); out = {}
for tr in BAGS:
    g = np.load(f"{TD}/{tr}/fwd_meas/gt_eval_only.npz")["g"]; c0, c1 = cruise_bounds(g[:, 0], g[:, 1], g[:, 2]); r = {}
    for d in DS:
        for est in ("ukf", "fgo"):
            sub = f"{TD}/{tr}/{est}_heading_F3bd{d}"
            D = np.loadtxt(f"{sub}/{est}_traj.tum"); t = D[:, 0]; qx, qy, qz, qw = D[:, 4], D[:, 5], D[:, 6], D[:, 7]
            yaw = np.unwrap(np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz)))
            ye = np.abs(np.degrees(wrap(yaw - (np.interp(t, g[:, 0], g[:, 3]) - np.pi / 2))))
            xt = np.abs(-D[:, 2] - np.interp(t, g[:, 0], g[:, 1]))
            w = (t >= c0) & (t <= c1); tt, ee, xx = t[w], ye[w], xt[w]
            conv = None
            for i in range(len(tt)):
                if ee[i] < 1.0:
                    j = np.searchsorted(tt, tt[i] + 5.0)
                    if np.all(ee[i:j] < 1.0):
                        conv = float(tt[i] - c0); break
            w60 = tt <= c0 + 60.0
            z = np.load(f"{sub}/timing_and_fwd.npz")
            if est == "ukf":
                L = z["nis_psi"][:40]; acc = int(L[:, 2].sum()); sig = float(np.degrees(np.sqrt(np.median(z["S_psi"][:40]))))
            else:
                L = z["fwd_log"]; L = L[L[:, 1] == 0][:40]; acc = int(L[:, 3].sum()); sig = float(np.degrees(np.sqrt(np.median(z["fwd_S"][:40]))))
            r[f"{est.upper()}_d{d}"] = {"convergence_s": conv, "xtrack_peak_m": float(xx.max()),
                                        "xtrack_int_60s_ms": float(np.trapz(xx[w60], tt[w60])),
                                        "first40_accepted": acc, "first40_pred_sigma_deg": sig}
    inf = lambda v: math.inf if v is None else v
    r["fgo_le_ukf_all_deltas"] = bool(all(inf(r[f"FGO_d{d}"]["convergence_s"]) <= inf(r[f"UKF_d{d}"]["convergence_s"]) for d in DS))
    ratios = [r[f"FGO_d{d}"]["xtrack_int_60s_ms"] / max(r[f"UKF_d{d}"]["xtrack_int_60s_ms"], 1e-9) for d in DS]
    r["ratio"] = ratios; r["ratio_decreasing"] = bool(all(ratios[i + 1] < ratios[i] for i in range(3)))
    out[tr] = r
    for d in DS:
        u, f = r[f"UKF_d{d}"], r[f"FGO_d{d}"]
        print(f"{tr} d{d:2d}: UKF conv {u['convergence_s']} peak {u['xtrack_peak_m']:.2f} int {u['xtrack_int_60s_ms']:.1f} acc {u['first40_accepted']}/40 sig {u['first40_pred_sigma_deg']:.2f} | "
              f"FGO conv {f['convergence_s']} peak {f['xtrack_peak_m']:.2f} int {f['xtrack_int_60s_ms']:.1f} acc {f['first40_accepted']}/40 sig {f['first40_pred_sigma_deg']:.2f}")
    print(f"  ratios {np.round(ratios, 3)}, FGO<=UKF all deltas {r['fgo_le_ukf_all_deltas']}, decreasing {r['ratio_decreasing']}")
out["decision"] = {"a_fgo_at_least_as_fast": bool(sum(out[t]["fgo_le_ukf_all_deltas"] for t in BAGS) >= 2),
                   "b_advantage_grows": bool(sum(out[t]["ratio_decreasing"] for t in BAGS) >= 2)}
print("DECISION", json.dumps(out["decision"]))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
