#!/usr/bin/env python3
"""PRE-REGISTERED RTF check (METHODOLOGY "PRE-REGISTRATION — RTF check"): open-loop cruise yaw drift and
cruise evo -a per estimator against RTF and flow latency, textured flights only.
Usage (venv-ardupilot + scipy): python3 eval/rtf_drift_check.py [--json OUT]"""
import argparse, json, math, os, sys
import numpy as np
from scipy import stats
from pymavlink import mavutil
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"); TD = os.path.expanduser("~/thesis_data/trials")
L = lambda f: json.load(open(os.path.join(R, f)))
DSN = [f"dsn_tex_r{i}" for i in range(1, 11)]
FWD = ["fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3", "fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3", "p1c_fwdc_tex", "p1c_fwdplainc_tex"]
score, timing, evo = {}, {}, {}
for f in ("rerun_dsn_score.json", "dsn_extra_score.json", "rerun_fwdc_score.json", "rerun_fwdplainc_score.json", "rerun_p1c_score.json"):
    score.update(L(f)["trials"])
for f in ("input_timing_rerun_all.json", "input_timing_dsn_extra.json"):
    timing.update(L(f))
for f in ("rerun_dsn_evo.json", "dsn_extra_evo.json", "rerun_fwdc_evo.json", "rerun_fwdplainc_evo.json", "rerun_p1c_evo.json"):
    evo.update(L(f)["trials"])
un = lambda d: np.degrees(np.unwrap(np.radians(d)))


def slope(t, e):
    return float(np.polyfit((t - t[0]) / 60.0, e, 1)[0])


def tum_yaw(p):
    d = np.loadtxt(p); return d[:, 0], np.degrees(np.unwrap(Rot.from_quat(d[:, 4:8]).as_euler("xyz")[:, 2]))


rows = []
for tr in DSN + FWD:
    g = np.loadtxt(f"{TD}/{tr}/ekf3/ground_truth.tum") if False else None
    gt = np.loadtxt(f"{TD}/{tr}/ukf/ground_truth.tum") if os.path.exists(f"{TD}/{tr}/ukf/ground_truth.tum") else np.loadtxt(f"{TD}/{tr}/fgo/ground_truth.tum") if os.path.exists(f"{TD}/{tr}/fgo/ground_truth.tum") else None
    r = {"trial": tr, "group": "dsn" if tr in DSN else "fwd",
         "rtf": score[tr]["checks"]["diag RTF (cruise)"]["value"] if tr in score else None,
         "lat_ms": timing[tr]["flow_to_ekf3"]["lat_median_ms"] if tr in timing else None}
    # EKF3: XKF1 core 0 yaw vs SIM yaw over the pinned cruise window (SITL clock; window from SIM, as the closed-loop scoring)
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); X, S = [], []
    while True:
        x = m.recv_match(type=["XKF1", "SIM"])
        if x is None:
            break
        if x.get_type() == "SIM":
            S.append((x.TimeUS / 1e6, x.Lat, x.Lng, x.Yaw))
        elif x.C == 0:
            X.append((x.TimeUS / 1e6, x.Yaw))
    S, X = np.array(S), np.array(X); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    c0, c1 = cruise_bounds(S[:, 0], E, N)
    w = (X[:, 0] >= c0) & (X[:, 0] <= c1)
    e = (un(X[w, 1]) - np.interp(X[w, 0], S[:, 0], un(S[:, 3])) + 180) % 360 - 180
    r["EKF3_drift_dpm_NED"] = slope(X[w, 0], e)
    # UKF / FGO (baseline arms): TUM yaw vs GT TUM yaw (ENU/corridor sense; + = CCW) over the bag-clock cruise window
    if gt is not None:
        g0, g1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
        tg, yg = tum_yaw(f"{TD}/{tr}/ukf/ground_truth.tum" if os.path.exists(f"{TD}/{tr}/ukf/ground_truth.tum") else f"{TD}/{tr}/fgo/ground_truth.tum")
        for est in ("ukf", "fgo"):
            p = f"{TD}/{tr}/{est}/{est}_traj.tum"
            if not os.path.exists(p):
                continue
            t, y = tum_yaw(p); ww = (t >= g0) & (t <= g1)
            ee = y[ww] - np.interp(t[ww], tg, yg); ee = (ee + 180) % 360 - 180 if np.ptp(ee) < 170 else ee
            r[f"{est.upper()}_drift_dpm_ENU"] = slope(t[ww], ee)
    for est in ("EKF3", "UKF", "FGO"):
        try:
            r[f"{est}_evo"] = evo[tr]["est"][est]["ate_a_cruise"]["+0.00"]
        except KeyError:
            r[f"{est}_evo"] = None
    rows.append(r); print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)

out = {"rows": rows, "tests": {}}
for key in ("EKF3_drift_dpm_NED", "UKF_drift_dpm_ENU", "FGO_drift_dpm_ENU", "EKF3_evo", "UKF_evo", "FGO_evo"):
    R_ = [r for r in rows if r.get(key) is not None and r["rtf"] is not None]
    v = np.array([r[key] for r in R_]); rtf = np.array([r["rtf"] for r in R_])
    lat_ok = [r for r in R_ if r["lat_ms"] is not None]
    t = {"n": len(R_)}
    t["spearman_rtf"] = list(map(float, stats.spearmanr(v, rtf)))
    if len(lat_ok) > 3:
        t["spearman_latency"] = list(map(float, stats.spearmanr([r[key] for r in lat_ok], [r["lat_ms"] for r in lat_ok])))
    a_ = [r[key] for r in R_ if r["group"] == "dsn"]; b_ = [r[key] for r in R_ if r["group"] == "fwd"]
    t["dsn_median"], t["fwd_median"] = float(np.median(a_)), float(np.median(b_))
    t["mannwhitney_p"] = float(stats.mannwhitneyu(a_, b_, alternative="two-sided").pvalue)
    t["depends_on_rtf"] = bool((abs(t["spearman_rtf"][0]) >= 0.5 and t["spearman_rtf"][1] < 0.05) or t["mannwhitney_p"] < 0.05)
    out["tests"][key] = t
    print(key, json.dumps(t))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
