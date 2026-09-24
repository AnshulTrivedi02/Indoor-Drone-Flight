#!/usr/bin/env python3
"""Phase 3 evaluation of the forward-camera measurements against ground truth.

Ground truth is used HERE ONLY, never in the measurement pipeline (fwd_measure.py /
fwd_run.py). METHODOLOGY "Phase 3 — forward-camera measurements: pre-registration".

  psi_true   = GT ENU yaw - 90 deg (corridor along +Y), at each frame stamp
  omega_true = GT yaw change between consecutive frame stamps / their dt (deg/s)
  cruise     = eval/cruise_window.cruise_bounds on GT

Per bag and per parameter combination: availability (% of cruise frames with a valid
output; also for GT y > 145 m), outlier rate (|err| > 3 deg or 3 deg/s, over valid
outputs), bias and noise (mean and sd of the NON-outlier valid errors; the mean over
all valid errors is also reported), and robust sigma (1.4826 x MAD over valid errors).

Modes:
  --calibrate TRIAL...   grid over (inlier tol, S_MIN) then (box, N_MIN), apply the
                         pre-registered selection rule, write eval/results/fwd_calibration.json
  --validate TRIAL...    frozen parameters from fwd_calibration.json; per-bag metrics and
                         bar verdicts, aggregated per world and per dataset -> --json OUT

Usage (venv-fwd): python3 eval/fwd_eval.py --calibrate p1c_... | --validate fwdc_... [--json OUT]
"""
import argparse, json, math, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds

TD = os.path.expanduser("~/thesis_data/trials")
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
S_GRID = (0, 200, 400, 600, 800, 1000)
NMIN_GRID = (5, 10, 20)
BAR = {"psi": {"avail": 70.0, "bias": 0.5, "noise": 1.0, "outlier": 5.0, "out_thr": 3.0},
       "omega": {"avail": 70.0, "bias": 0.05, "noise": 1.0, "outlier": 5.0, "out_thr": 3.0}}
ts = get_typestore(Stores.ROS2_JAZZY)


def gt(trial):
    p = f"{TD}/{trial}/fwd_meas/gt_eval_only.npz"
    if os.path.exists(p):
        d = np.load(p); return d["g"]
    g = []
    with Reader(f"{TD}/{trial}/bag") as r:
        for con, _, raw in r.messages(connections=[c for c in r.connections if c.topic == "/ground_truth/pose"]):
            m = ts.deserialize_cdr(raw, con.msgtype); q = m.pose.orientation
            yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
            g.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y, yaw))
    g = np.array(sorted(g)); g[:, 3] = np.unwrap(g[:, 3])
    np.savez_compressed(p, g=g)
    return g


def truth(trial, t):
    g = gt(trial)
    t0, t1 = cruise_bounds(g[:, 0], g[:, 1], g[:, 2])
    yaw = np.degrees(np.interp(t, g[:, 0], g[:, 3]))
    psi_true = yaw - 90.0
    om_true = np.full(len(t), np.nan)
    om_true[1:] = np.diff(yaw) / np.diff(t)
    cruise = (t >= t0) & (t <= t1)
    y = np.interp(t, g[:, 0], g[:, 2])
    return psi_true, om_true, cruise, y


def metrics(err, valid, cruise, y, bar):
    n = cruise.sum()
    v = valid & cruise & np.isfinite(err)
    e = err[v]
    out = np.abs(e) > bar["out_thr"]
    en = e[~out]
    late = cruise & (y > 145)
    m = {"avail_pct": float(100 * v.sum() / n) if n else 0.0,
         "avail_pct_y_gt_145": float(100 * (v & late).sum() / max(late.sum(), 1)),
         "n_cruise": int(n), "n_valid": int(v.sum()),
         "outlier_pct": float(100 * out.mean()) if len(e) else float("nan"),
         "bias": float(en.mean()) if len(en) else float("nan"),
         "bias_all_valid": float(e.mean()) if len(e) else float("nan"),
         "noise_sd": float(en.std()) if len(en) > 1 else float("nan"),
         "robust_sigma": float(1.4826 * np.median(np.abs(e - np.median(e)))) if len(e) else float("nan")}
    m["pass"] = bool(m["avail_pct"] >= bar["avail"] and abs(m["bias"]) <= bar["bias"]
                     and m["noise_sd"] <= bar["noise"] and m["outlier_pct"] <= bar["outlier"])
    return m


def load(trial, name="meas.npz"):
    d = np.load(f"{TD}/{trial}/fwd_meas/{name}")
    psi_t, om_t, cruise, y = truth(trial, d["t"])
    return d, psi_t, om_t, cruise, y


def eval_params(trial, data, ti, s_min, bj, n_min):
    d, psi_t, om_t, cruise, y = data
    psi = d["psi"][:, ti]; sup = d["support"][:, ti]
    vpsi = np.isfinite(psi) & (sup >= s_min)
    om = d["omega"][:, ti, bj]; ntr = d["n_trk"][:, ti, bj]
    vom = np.isfinite(om) & (ntr >= n_min)
    return (metrics(psi - psi_t, vpsi, cruise, y, BAR["psi"]),
            metrics(om - om_t, vom, cruise, y, BAR["omega"]),
            psi - psi_t, vpsi & cruise, om - om_t, vom & cruise)


def calibrate(trials):
    data = {t: load(t) for t in trials}
    grid = data[trials[0]][0]
    tol, box = list(grid["inlier_grid"]), list(grid["box_grid"])
    # heading first: (tolerance, S_MIN)
    rows = []
    for ti, tv in enumerate(tol):
        for s in S_GRID:
            ms = [eval_params(t, data[t], ti, s, 0, 0)[0] for t in trials]
            rows.append({"inlier_deg": float(tv), "s_min": s, "n_pass": sum(m["pass"] for m in ms),
                         "mean_avail": float(np.mean([m["avail_pct"] for m in ms])),
                         "per_bag": dict(zip(trials, ms))})
    best_h = max(rows, key=lambda r: (r["n_pass"], r["mean_avail"]))
    ti = tol.index(best_h["inlier_deg"])
    rows_w = []
    for bj, bv in enumerate(box):
        for n in NMIN_GRID:
            ms = [eval_params(t, data[t], ti, best_h["s_min"], bj, n)[1] for t in trials]
            rows_w.append({"box_half_px": int(bv), "n_min": n, "n_pass": sum(m["pass"] for m in ms),
                           "mean_avail": float(np.mean([m["avail_pct"] for m in ms])),
                           "per_bag": dict(zip(trials, ms))})
    best_w = max(rows_w, key=lambda r: (r["n_pass"], r["mean_avail"]))
    bj = box.index(best_w["box_half_px"])
    # measurement noise, pooled per dataset type (robust sigma of valid calibration errors)
    sig = {}
    for kind in ("fwdc", "fwdplainc"):
        ep, ew = [], []
        for t in trials:
            if f"_{kind}_" not in t:
                continue
            _, _, e1, v1, e2, v2 = eval_params(t, data[t], ti, best_h["s_min"], bj, best_w["n_min"])
            ep.append(e1[v1]); ew.append(e2[v2])
        ep, ew = np.concatenate(ep), np.concatenate(ew)
        rs = lambda e: float(1.4826 * np.median(np.abs(e - np.median(e))))
        sig[kind] = {"sigma_psi_deg": rs(ep), "sigma_omega_dps": rs(ew)}
    out = {"calibration_trials": trials,
           "frozen": {"inlier_deg": best_h["inlier_deg"], "s_min": best_h["s_min"],
                      "box_half_px": best_w["box_half_px"], "n_min": best_w["n_min"]},
           "noise_for_phase4": sig, "heading_grid": rows, "yawrate_grid": rows_w}
    json.dump(out, open(f"{RES}/fwd_calibration.json", "w"), indent=1)
    print("FROZEN:", out["frozen"], "noise:", sig)
    for r in sorted(rows, key=lambda r: (-r["n_pass"], -r["mean_avail"]))[:6]:
        print(f"  heading tol {r['inlier_deg']} S_MIN {r['s_min']:4d}: {r['n_pass']}/6 pass, mean avail {r['mean_avail']:.1f}%")
    for r in sorted(rows_w, key=lambda r: (-r["n_pass"], -r["mean_avail"]))[:6]:
        print(f"  yaw-rate box {r['box_half_px']} N_MIN {r['n_min']}: {r['n_pass']}/6 pass, mean avail {r['mean_avail']:.1f}%")
    show(best_h["per_bag"], best_w["per_bag"])


def show(ph, pw):
    for t in ph:
        a, b = ph[t], pw[t]
        print(f"  {t:22} psi: avail {a['avail_pct']:5.1f}% (y>145 {a['avail_pct_y_gt_145']:5.1f}%) bias {a['bias']:+.3f} sd {a['noise_sd']:.3f} out {a['outlier_pct']:5.2f}% {'PASS' if a['pass'] else 'fail'}"
              f" | omega: avail {b['avail_pct']:5.1f}% bias {b['bias']:+.4f} sd {b['noise_sd']:.3f} out {b['outlier_pct']:5.2f}% {'PASS' if b['pass'] else 'fail'}")


def validate(trials, out_json):
    cal = json.load(open(f"{RES}/fwd_calibration.json"))["frozen"]
    res = {}
    for t in trials:
        data = load(t, "meas_frozen.npz"); g = data[0]
        ti = list(g["inlier_grid"]).index(cal["inlier_deg"]); bj = list(g["box_grid"]).index(cal["box_half_px"])
        mp, mw, *_ = eval_params(t, data, ti, cal["s_min"], bj, cal["n_min"])
        res[t] = {"psi": mp, "omega": mw}
    show({t: v["psi"] for t, v in res.items()}, {t: v["omega"] for t, v in res.items()})
    agg = {}
    for key in ("psi", "omega"):
        for grp in ("fwdc", "fwdplainc"):
            for w in ("tex", "trans", "blank", "all"):
                ts_ = [t for t in res if t.startswith(grp + "_") and (w == "all" or f"_{w}_" in t)]
                if not ts_:
                    continue
                ms = [res[t][key] for t in ts_]
                agg[f"{key}/{grp}/{w}"] = {k: float(np.mean([m[k] for m in ms])) for k in
                                           ("avail_pct", "avail_pct_y_gt_145", "bias", "bias_all_valid", "noise_sd", "robust_sigma", "outlier_pct")}
                agg[f"{key}/{grp}/{w}"]["n_pass"] = f"{sum(m['pass'] for m in ms)}/{len(ms)}"
    print("\nAGGREGATE (means over bags):")
    for k, v in agg.items():
        print(f"  {k:24} avail {v['avail_pct']:5.1f}%  bias {v['bias']:+.4f}  sd {v['noise_sd']:.3f}  robust {v['robust_sigma']:.3f}  out {v['outlier_pct']:5.2f}%  pass {v['n_pass']}")
    if out_json:
        json.dump({"frozen": cal, "per_bag": res, "aggregate": agg}, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--calibrate", nargs="+"); g.add_argument("--validate", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args()
    calibrate(a.calibrate) if a.calibrate else validate(a.validate, a.json)
