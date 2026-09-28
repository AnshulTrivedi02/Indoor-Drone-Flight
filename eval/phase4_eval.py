#!/usr/bin/env python3
"""Phase 4 evaluation: every arm of the offline forward-camera fusion (UKF and FGO),
with EKF3 as the fixed no-heading reference. METHODOLOGY "Phase 4 — offline
forward-camera fusion": outputs are REPORTED here; judging them is Phase 5.

Per dataset (fwdc: baseline / heading / heading_yawrate; fwdplainc: baseline / heading):
  1. eval/three_way_eval.py on the 9 bags with EKF3 + every arm -> evo -a (cruise) and
     the transition/blank failure metrics, on the one pinned cruise window
     (-> eval/results/phase4_<ds>_evo.json).
  2. Per arm and bag, over that cruise window:
       yaw error vs GT      psi_true = GT ENU yaw - 90 deg (corridor axis); estimator yaw
                            from its TUM (both frames put yaw 0 along the corridor at
                            spawn). Mean, RMS, end-of-cruise, and linear drift (deg/min).
       gyro-z bias          from the replay's metrics.txt (cruise mean vs the SITL true
                            mean, ramp vs the true ramp).
       forward measurements valid / fused counts (fwd_stats.json), NIS of the tested
                            measurements (median, mean, share > gate).
       timing (DIAGNOSTIC)  per-update wall-clock: UKF predict (12.5 ms period) and
                            forward update (33.3 ms), FGO keyframe step (33.3 ms):
                            median, p95, max and the ratio to the period. Python on the
                            workstation says nothing directly about flight-controller
                            feasibility; it changes no Phase 4 setting.
  -> eval/results/phase4_<ds>_arms.json, and a printed table.

Usage (venv-fwd for rosbags-free numpy; three_way_eval is called via venv-ardupilot):
  python3 eval/phase4_eval.py [fwdc|fwdplainc ...]
"""
import json, math, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
TD = os.path.expanduser("~/thesis_data/trials")
AP = os.path.expanduser("~/venv-ardupilot/bin/python")
ARMS = {"fwdc": ("baseline", "heading", "heading_yawrate"), "fwdplainc": ("baseline", "heading")}
PERIOD = {"ukf_predict": 0.0125, "ukf_fwd": 1 / 30.3, "fgo_keyframe": 1 / 30.0}


def trials(ds):
    return [f"{ds}_{w}_r{r}" for r in (1, 2, 3) for w in ("tex", "trans", "blank")]


def run_evo(ds):
    out = os.path.join(RES, f"phase4_{ds}_evo.json")
    est = []
    for a in ARMS[ds]:
        est += ["--est", f"UKF_{a}=ukf_{a}/ukf_traj.tum", "--est", f"FGO_{a}=fgo_{a}/fgo_traj.tum"]
    only = ",".join(["EKF3"] + [f"{e}_{a}" for a in ARMS[ds] for e in ("UKF", "FGO")])
    subprocess.run([AP, os.path.join(HERE, "three_way_eval.py"), *trials(ds), *est, "--only", only,
                    "--json", out], check=True, stdout=open(os.path.join(RES, f"phase4_{ds}_evo.txt"), "w"))
    return json.load(open(out))["trials"]


def tum_yaw(path):
    a = np.loadtxt(path)
    x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    return a[:, 0], np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def metrics_txt(path):
    return {k: float(v) for k, v in (l.strip().split("=") for l in open(path) if "=" in l)}


def summ(ns, period):
    if len(ns) == 0:
        return None
    ms = np.asarray(ns) / 1e6
    return {"median_ms": float(np.median(ms)), "p95_ms": float(np.percentile(ms, 95)), "max_ms": float(ms.max()),
            "median_over_period": float(np.median(ms) / (1e3 * period)),
            "p95_over_period": float(np.percentile(ms, 95) / (1e3 * period))}


def nis_summ(n, gate=9.0):
    if len(n) == 0:
        return None
    n = np.asarray(n)
    return {"n_tested": int(len(n)), "median": float(np.median(n)), "mean_of_accepted": float(n[n <= gate].mean()) if (n <= gate).any() else None,
            "pct_over_gate": float(100 * (n > gate).mean())}


def per_arm(trial, est, arm, window):
    sub = f"{est.lower()}_{arm}"; d = f"{TD}/{trial}/{sub}"
    t, yaw = tum_yaw(f"{d}/{est.lower()}_traj.tum")
    g = np.load(f"{TD}/{trial}/fwd_meas/gt_eval_only.npz")["g"]        # t, x, y, unwrapped ENU yaw
    w = (t >= window[0]) & (t <= window[1])
    err = np.degrees(yaw[w] - (np.interp(t[w], g[:, 0], g[:, 3]) - math.pi / 2))
    err = (err + 180) % 360 - 180 if np.abs(err).max() < 170 else err     # keep runaway yaw unwrapped
    slope = np.polyfit((t[w] - t[w][0]) / 60.0, err, 1)[0]
    m = metrics_txt(f"{d}/metrics.txt")
    out = {"yaw_err_mean_deg": float(err.mean()), "yaw_err_rms_deg": float(np.sqrt(np.mean(err ** 2))),
           "yaw_err_end_deg": float(err[-1]), "yaw_err_drift_dpm": float(slope),
           "bgz_mean_dpm": m.get("bgz_mean"), "true_bias_mean_dpm": m.get("true_bias_mean"),
           "bgz_ramp": m.get("bgz_ramp"), "true_ramp": m.get("true_ramp")}
    fs = json.load(open(f"{d}/fwd_stats.json")); out["fwd_counts"] = fs["counts"]
    z = np.load(f"{d}/timing_and_fwd.npz")
    if est == "UKF":
        out["timing"] = {"ukf_predict": summ(z["t_predict_ns"], PERIOD["ukf_predict"]),
                         "ukf_fwd": summ(z["t_fwd_ns"], PERIOD["ukf_fwd"])}
        out["nis_psi"] = nis_summ(z["nis_psi"][:, 1]) if len(z["nis_psi"]) else None
        out["nis_omega"] = nis_summ(z["nis_omega"][:, 1]) if len(z["nis_omega"]) else None
    else:
        out["timing"] = {"fgo_keyframe": summ(z["t_keyframe_ns"], PERIOD["fgo_keyframe"])}
        fl = z["fwd_log"]
        out["nis_psi"] = nis_summ(fl[fl[:, 1] == 0, 2]) if len(fl) else None
        out["nis_omega"] = nis_summ(fl[fl[:, 1] == 1, 2]) if len(fl) else None
    return out


def main(dsets):
    for ds in dsets:
        evo = run_evo(ds)
        res = {}
        for t in trials(ds):
            win = evo[t]["window_s"]; res[t] = {"window_s": win, "EKF3": evo[t]["est"]["EKF3"]}
            for a in ARMS[ds]:
                for e in ("UKF", "FGO"):
                    r = per_arm(t, e, a, win)
                    r["evo"] = evo[t]["est"][f"{e}_{a}"]
                    res[t][f"{e}_{a}"] = r
        json.dump(res, open(os.path.join(RES, f"phase4_{ds}_arms.json"), "w"), indent=1)
        print(f"\n===== {ds} =====")
        for t in trials(ds):
            print(f"{t}  EKF3 evo {res[t]['EKF3']['ate_a_cruise']['+0.00']:.2f}")
            for a in ARMS[ds]:
                for e in ("UKF", "FGO"):
                    r = res[t][f"{e}_{a}"]; f = r["evo"]["failure"]; c = r["fwd_counts"]
                    tm = r["timing"].get("fgo_keyframe") or r["timing"]["ukf_predict"]
                    print(f"   {e}_{a:16} evo {r['evo']['ate_a_cruise']['+0.00']:7.2f}  ratio {f['disp_ratio']:.2f} onset {f['onset_gt_dist'] or float('nan'):5.0f}  "
                          f"yaw err rms {r['yaw_err_rms_deg']:7.2f} end {r['yaw_err_end_deg']:+8.2f} drift {r['yaw_err_drift_dpm']:+7.2f} dpm  "
                          f"bgz {r['bgz_mean_dpm']:+6.2f}/{r['true_bias_mean_dpm']:.2f}  "
                          f"psi {c['psi_fused']}/{c['psi_valid']} om {c['omega_fused']}/{c['omega_valid']}  "
                          f"t {tm['median_ms']:.1f}/{tm['p95_ms']:.1f} ms")


if __name__ == "__main__":
    main(sys.argv[1:] or ["fwdc", "fwdplainc"])
