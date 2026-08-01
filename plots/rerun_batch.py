#!/usr/bin/env python3
"""Re-run UKF + FGO across the nine dsn_* bags with the CORRECTED h_flow (interval-avg
gyro), cruise-window metrics. Collects evo -a / -u, yaw drift, along/cross, bias%, and
the ramp-tracking statistic. Assembles the three-way table (EKF3 reused — unchanged by
the correction) and the ramp table. Writes a JSON for downstream table assembly.
Runs UKF (venv-evo) first (fast), then FGO (venv-fgo, ~40 min)."""
import os, re, json, subprocess
import numpy as np

HOME = os.path.expanduser("~")
PYE = f"{HOME}/venv-evo/bin/python3"
PYF = f"{HOME}/venv-fgo/bin/python3"
EVO = f"{HOME}/venv-evo/bin/evo_ape"
UKF = f"{HOME}/thesis_ws/src/estimators/ukf_replay.py"
FGO = f"{HOME}/thesis_ws/src/estimators/fgo/fgo_replay.py"
CONDS = {"tex": [f"dsn_tex_r{i}" for i in (1, 2, 3)],
         "blank": [f"dsn_blank_r{i}" for i in (1, 2, 3)],
         "trans": [f"dsn_trans_r{i}" for i in (1, 2, 3)]}
TRIALS = [t for v in CONDS.values() for t in v]
EKF3_A = {"tex": 4.97, "trans": 23.41, "blank": 37.79}   # unchanged by h_flow correction


def evo_rmse(trial, sub, tum, aligned):
    d = f"{HOME}/thesis_data/trials/{trial}/{sub}"
    cmd = [EVO, "tum", f"{d}/ground_truth.tum", f"{d}/{tum}", "--t_max_diff", "0.05", "--no_warnings"]
    if aligned:
        cmd.append("-a")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    m = re.search(r'rmse\s+([\d.]+)', out)
    return float(m.group(1)) if m else float('nan')


def metrics(trial, sub):
    p = f"{HOME}/thesis_data/trials/{trial}/{sub}/metrics.txt"
    return dict(l.strip().split("=") for l in open(p))


res = {}
print("===== UKF re-run (corrected h_flow) =====", flush=True)
for tr in TRIALS:
    subprocess.run([PYE, UKF, tr], capture_output=True, text=True)
    mm = metrics(tr, "ukf")
    res.setdefault(tr, {})["ukf"] = dict(
        ate_a=evo_rmse(tr, "ukf", "ukf_traj.tum", True), ate_u=evo_rmse(tr, "ukf", "ukf_traj.tum", False),
        yaw=float(mm["yaw_drift"]), along=float(mm["along_pN"]), cross=float(mm["cross_track"]),
        bgz_pct=float(mm["bgz_pct"]), ramp=float(mm["bgz_ramp"]), tramp=float(mm["true_ramp"]))
    r = res[tr]["ukf"]
    print(f"  {tr:15} UKF  ate_a={r['ate_a']:.2f} ate_u={r['ate_u']:.1f} yaw={r['yaw']:+.1f} "
          f"cross={r['cross']:+.1f} bgz%={r['bgz_pct']:.0f} ramp={r['ramp']:+.2f}", flush=True)

print("\n===== FGO re-run (corrected h_flow, window 0.25) — ~40 min =====", flush=True)
for tr in TRIALS:
    subprocess.run([PYF, FGO, tr, "0.25"], capture_output=True, text=True)
    mm = metrics(tr, "fgo")
    res[tr]["fgo"] = dict(
        ate_a=evo_rmse(tr, "fgo", "fgo_traj.tum", True), ate_u=evo_rmse(tr, "fgo", "fgo_traj.tum", False),
        yaw=float(mm["yaw_drift"]), along=float(mm["along_pN"]), cross=float(mm["cross_track"]),
        bgz_pct=float(mm.get("bgz_pct", "nan")), ramp=float(mm.get("bgz_ramp", "nan")),
        tramp=float(mm.get("true_ramp", "nan")))
    r = res[tr]["fgo"]
    print(f"  {tr:15} FGO  ate_a={r['ate_a']:.2f} ate_u={r['ate_u']:.1f} yaw={r['yaw']:+.1f} "
          f"cross={r['cross']:+.1f} bgz%={r['bgz_pct']:.0f} ramp={r['ramp']:+.2f}", flush=True)

json.dump(res, open(f"{HOME}/thesis_ws/plots/rerun_results.json", "w"), indent=1)

# ---- three-way table (evo -a), per-condition mean ----
def cmean(cond, est, key):
    return np.mean([res[t][est][key] for t in CONDS[cond]])

print("\n===== THREE-WAY (evo -a, per-condition mean; EKF3 reused, UKF/FGO corrected) =====")
print(f"{'condition':12}{'EKF3':>8}{'UKF':>10}{'FGO(0.25)':>11}")
for cond in ("tex", "trans", "blank"):
    print(f"{cond:12}{EKF3_A[cond]:>8.2f}{cmean(cond,'ukf','ate_a'):>10.2f}{cmean(cond,'fgo','ate_a'):>11.2f}")

print("\n===== RAMP-TRACKING d|b|/dt (deg/min per min; true ~2.8 windowed, ideal 3.00) =====")
print(f"{'trial':15}{'EKF3':>8}{'UKF':>8}{'FGO':>8}{'true':>8}")
# EKF3 ramp from ekf3_bias_ramp.py output (re-read the persisted series slope)
def ekf3_ramp(tr):
    p = f"{HOME}/thesis_data/trials/{tr}/ekf3/bgz_series.txt"
    if not os.path.exists(p):
        return float('nan'), float('nan')
    a = np.loadtxt(p); tmin = (a[:, 0]-a[0, 0])/60.0
    return float(np.polyfit(tmin, a[:, 1], 1)[0]), float(np.polyfit(tmin, a[:, 2], 1)[0])
for tr in TRIALS:
    er, tr_ramp = ekf3_ramp(tr)
    print(f"{tr:15}{er:>8.2f}{res[tr]['ukf']['ramp']:>8.2f}{res[tr]['fgo']['ramp']:>8.2f}{tr_ramp:>8.2f}")
print("\nyaw drift (deg/min):")
print(f"{'trial':15}{'UKF':>8}{'FGO':>8}")
for tr in TRIALS:
    print(f"{tr:15}{res[tr]['ukf']['yaw']:>8.1f}{res[tr]['fgo']['yaw']:>8.1f}")
print("\nDONE", flush=True)
