#!/usr/bin/env python3
"""Phase 5b: consistency (NEES) of the estimators' own covariance, and the heading
innovation covariance behind the end-wall and checkerboard gate results.

Inputs: the Phase 5b sandbox replays (~/thesis_data/phase5b/home/thesis_data/trials/<t>/):
  UKF  <arm>: ukf_<arm>_dump.npz  x = [t, state(15), diag(P)(15)] per predict step
             ukf_<arm>/timing_and_fwd.npz  nis_psi (t, nis, acc), S_psi
  FGO  <arm>: fgo_<arm>/fgo_traj.tum, timing_and_fwd.npz  cov_log (t, Pxx, Pxy, Pyy, yaw var),
             fwd_log (t, kind, nis, ok), fwd_S
  EKF3: ardupilot.bin XKF1 PE, XKV1 V08 (pos E variance), SIM (as plots/ekf3_state_diagnostic.py)
FGO covariance CAVEAT: this is the gate-only two-keyframe FILTERING covariance recursion
(the Python BatchFixedLagSmoother exposes no marginal), not the smoother's true marginal.

1. Cross-track consistency over the pinned cruise window, in each estimator's own frame
   (UKF/FGO: y with yaw 0 along the corridor, GT mapped by a fixed -90 deg rotation and the
   estimator's start position; EKF3: NED East). Error e vs the filter's own sigma:
   % of samples outside +-3 sigma, mean 1-D NEES e^2/sigma^2 (consistent: ~1), median sigma.
2. Heading innovation covariance S at (a) the end-wall "confident wrong" outputs (GT y > 140 m,
   valid, |err| > 3 deg) and (b) every tested heading on the checkerboard floor
   (fwdplainc_tex), per estimator: sqrt(S), the estimator's own predicted yaw sigma
   sqrt(S - sigma_psi^2), and its actual yaw error at those times (yaw NEES of the prediction).

Usage (venv-ardupilot: numpy + pymavlink): python3 eval/phase5b_consistency.py [--json OUT]
"""
import argparse, json, math, os
import numpy as np

TD = os.path.expanduser("~/thesis_data/trials")
SB = os.path.expanduser("~/thesis_data/phase5b/home/thesis_data/trials")
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
SIG_PSI = {"fwdc": math.radians(0.148), "fwdplainc": math.radians(0.126)}


def gt(trial):
    return np.load(f"{TD}/{trial}/fwd_meas/gt_eval_only.npz")["g"]     # t, x(E), y(N), yaw(ENU, unwrapped)


def consist(e, sig):
    ok = np.isfinite(e) & np.isfinite(sig) & (sig > 0)
    e, sig = e[ok], sig[ok]
    return {"pct_outside_3sigma": float(100 * (np.abs(e) > 3 * sig).mean()), "mean_nees": float(np.mean((e / sig) ** 2)),
            "median_sigma_m": float(np.median(sig)), "final_abs_err_m": float(abs(e[-1])), "n": int(len(e))}


def lateral_truth(g, t, t0):
    x0 = np.interp(t0, g[:, 0], g[:, 1])
    return -(np.interp(t, g[:, 0], g[:, 1]) - x0)          # est-frame y = -(GT east), from the start


def ukf(trial, arm, win):
    d = np.load(f"{SB}/{trial}/ukf_{arm}_dump.npz")["x"]
    t = d[:, 0]; y = d[:, 2]; vy = d[:, 1 + 15 + 1]
    w = (t >= win[0]) & (t <= win[1])
    e = y - lateral_truth(gt(trial), t, t[0])
    return consist(e[w], np.sqrt(vy[w]))


def fgo(trial, arm, win):
    a = np.loadtxt(f"{SB}/{trial}/fgo_{arm}/fgo_traj.tum")
    c = np.load(f"{SB}/{trial}/fgo_{arm}/timing_and_fwd.npz")["cov_log"]
    t = a[:, 0]; y = a[:, 2]
    vy = np.interp(t, c[:, 0], c[:, 3])
    w = (t >= win[0]) & (t <= win[1])
    e = y - lateral_truth(gt(trial), t, t[0])
    return consist(e[w], np.sqrt(vy[w]))


def ekf3(trial, win):
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(f"{TD}/{trial}/ardupilot.bin")
    k1, v1, sm = [], [], []
    while True:
        x = m.recv_match(type=["XKF1", "XKV1", "SIM"])
        if x is None:
            break
        ty = x.get_type()
        if ty in ("XKF1", "XKV1") and getattr(x, "C", 0) != 0:
            continue
        if ty == "XKF1":
            k1.append((x.TimeUS / 1e6, x.PE))
        elif ty == "XKV1":
            v1.append((x.TimeUS / 1e6, x.V08))
        else:
            sm.append((x.TimeUS / 1e6, x.Lat, x.Lng))
    k1, v1, sm = np.array(k1), np.array(v1), np.array(sm)
    lat, lng = sm[:, 1].copy(), sm[:, 2].copy()
    if np.abs(lat).max() > 1000:
        lat /= 1e7; lng /= 1e7
    gE = np.radians(lng - lng[0]) * 6378137.0 * math.cos(math.radians(lat.mean()))
    t = k1[:, 0]; w = (t >= win[0]) & (t <= win[1])
    e = k1[:, 1] - np.interp(t, sm[:, 0], gE)
    return consist(e[w], np.sqrt(np.interp(t[w], v1[:, 0], v1[:, 1])))


def heading_S(trial, est, ds, sel):
    """Rows of tested heading measurements: (t_meas, meas err vs GT deg, estimator yaw err deg,
    sqrt(S) deg, predicted yaw sigma deg, accepted). sel(t_meas, y, err) picks the points."""
    d = np.load(f"{TD}/{trial}/fwd_meas/meas_frozen.npz"); tm, psi = d["t"], d["psi"][:, 0]
    g = gt(trial)
    psit = lambda tt: np.degrees(np.interp(tt, g[:, 0], g[:, 3]) - math.pi / 2)
    z = np.load(f"{SB}/{trial}/{est.lower()}_heading/timing_and_fwd.npz")
    a = np.loadtxt(f"{SB}/{trial}/{est.lower()}_heading/{est.lower()}_traj.tum")
    x, y, zz, ww = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    yaw = np.degrees(np.unwrap(np.arctan2(2 * (ww * zz + x * y), 1 - 2 * (y * y + zz * zz))))
    if est == "UKF":
        rows = [(r[0], r[0], r[2] > 0, s) for r, s in zip(z["nis_psi"], z["S_psi"])]
    else:
        fl, S = z["fwd_log"], z["fwd_S"]
        rows = []
        valid_t = tm[np.isfinite(psi)]
        for r, s in zip(fl, S):
            if r[1] != 0:
                continue
            j = np.searchsorted(valid_t, r[0], side="right") - 1          # latest valid frame at or before the keyframe
            if j < 0:
                continue
            rows.append((valid_t[j], r[0], r[3] > 0, s))
    out = []
    for t_meas, t_upd, acc, s in rows:
        k = np.argmin(np.abs(tm - t_meas))
        merr = psi[k] - psit(t_meas)
        ygt = np.interp(t_meas, g[:, 0], g[:, 2])
        if not sel(t_meas, ygt, merr):
            continue
        i = max(np.searchsorted(a[:, 0], t_upd) - 1, 0)                    # estimate just before the update
        yerr = yaw[i] - psit(a[i, 0])
        pred_sig = math.degrees(math.sqrt(max(s - SIG_PSI[ds] ** 2, 0.0)))
        out.append((t_meas, merr, yerr, math.degrees(math.sqrt(s)), pred_sig, bool(acc)))
    return np.array(out, dtype=float).reshape(-1, 6)


def summ_S(rows):
    if len(rows) == 0:
        return None
    acc = rows[:, 5] > 0
    f = lambda m: None if not m.any() else {
        "n": int(m.sum()), "median_sqrtS_deg": float(np.median(rows[m, 3])),
        "median_pred_yaw_sigma_deg": float(np.median(rows[m, 4])),
        "median_abs_est_yaw_err_deg": float(np.median(np.abs(rows[m, 2]))),
        "median_abs_meas_err_deg": float(np.median(np.abs(rows[m, 1]))),
        "yaw_pred_nees_mean": float(np.mean((rows[m, 2] / np.maximum(rows[m, 4], 1e-6)) ** 2))}
    return {"all": f(np.ones(len(rows), bool)), "accepted": f(acc), "rejected": f(~acc)}


def main(out_json):
    res = {"consistency": {}, "endwall_S": {}, "checker_S": {}}
    for ds in ("fwdc", "fwdplainc"):
        evo = json.load(open(os.path.join(RES, f"phase4_{ds}_evo.json")))["trials"]
        ew = {"UKF": [], "FGO": []}
        for w in ("tex", "trans", "blank"):
            for r in (1, 2, 3):
                t = f"{ds}_{w}_r{r}"; win = evo[t]["window_s"]
                row = {"EKF3": ekf3(t, win)}
                for a in ("baseline", "heading"):
                    row[f"UKF_{a}"] = ukf(t, a, win); row[f"FGO_{a}"] = fgo(t, a, win)
                res["consistency"][t] = row
                for e in ("UKF", "FGO"):
                    ew[e].append(heading_S(t, e, ds, lambda tt, yy, err: yy > 140 and abs(err) > 3.0))
                    if w == "tex":
                        res["checker_S"].setdefault(f"{ds}/{e}", []).append(heading_S(t, e, ds, lambda tt, yy, err: True))
                print(t, "done", flush=True)
        for e in ("UKF", "FGO"):
            res["endwall_S"][f"{ds}/{e}"] = summ_S(np.vstack(ew[e]))
    for k, v in list(res["checker_S"].items()):
        res["checker_S"][k] = summ_S(np.vstack(v))
    json.dump(res, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=os.path.join(RES, "phase5b_consistency.json"))
    main(ap.parse_args().json)
