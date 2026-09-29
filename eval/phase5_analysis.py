#!/usr/bin/env python3
"""Phase 5 — evaluation of the Phase 4 outputs against the pre-registered prediction.
Analysis of existing outputs only; no replays. METHODOLOGY "Phase 5".

1. Drift decomposition, the same method as plots/lateral_checks.py (the ~74% heading
   share on dsn_tex_r3): over the pinned cruise window,
       errV_lat  = estimated lateral velocity - true lateral velocity
       head      = spd * (sin(psi_est) - sin(psi_true))   (true speed rotated by the yaw error)
       resid     = errV_lat - head
       share     = mean(head) / mean(errV_lat)
   EKF3 (reference, no heading): XKF1 Yaw/VE vs SIM, NED, lateral = East, exactly as
   lateral_checks.py. UKF/FGO: their own frame, which puts yaw 0 along the corridor at spawn
   (the heading arms use the same reference), so GT maps in by a fixed -90 deg rotation:
   x_est = GT north, y_est = -GT east, psi_true = GT ENU yaw - 90 deg. Estimated lateral
   velocity = the time derivative of the estimated lateral position (the trajectories store
   positions only); its window mean equals the lateral displacement over the window / T.
2. End wall (GT y > 140 m): every VALID heading output (support >= S_MIN) whose error
   against GT exceeds 3 deg ("confident wrong"), and whether each estimator's gate fused it.
3. Plain walls over the checkerboard floor: gate acceptance and yaw error, per estimator.

Usage (venv-ardupilot: numpy + pymavlink): python3 eval/phase5_analysis.py [--json OUT]
"""
import argparse, json, math, os
import numpy as np

TD = os.path.expanduser("~/thesis_data/trials")
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
ARMS = {"fwdc": ("baseline", "heading", "heading_yawrate"), "fwdplainc": ("baseline", "heading")}
WRONG_DEG = 3.0          # Phase 3's outlier threshold for heading
_trapz = getattr(np, "trapezoid", None) or np.trapz


def tum(path):
    a = np.loadtxt(path)
    x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    return a[:, 0], a[:, 1], a[:, 2], np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def gt(trial):
    return np.load(f"{TD}/{trial}/fwd_meas/gt_eval_only.npz")["g"]      # t, x(E), y(N), unwrapped ENU yaw


def decompose(t, lat, psi_e, t_gt, vlat_t, psi_t_gt, spd_gt, win):
    w = (t >= win[0]) & (t <= win[1])
    t, lat, psi_e = t[w], lat[w], psi_e[w]
    vlat_e = np.gradient(lat, t)
    vlat_true = np.interp(t, t_gt, vlat_t); psi_t = np.interp(t, t_gt, psi_t_gt); spd = np.interp(t, t_gt, spd_gt)
    err = vlat_e - vlat_true
    head = spd * (np.sin(psi_e) - np.sin(psi_t))
    res = err - head
    yawerr = np.degrees(psi_e - psi_t)
    T = t[-1] - t[0]
    return {"errV_mean": float(err.mean()), "head_mean": float(head.mean()), "resid_mean": float(res.mean()),
            "share": float(head.mean() / err.mean()) if abs(err.mean()) > 1e-9 else None,
            "xtrack_err_m": float(_trapz(err, t)), "xtrack_head_m": float(_trapz(head, t)),
            "xtrack_resid_m": float(_trapz(res, t)),
            "corr_resid_yawerr": float(np.corrcoef(res, yawerr)[0, 1]) if yawerr.std() > 1e-9 else None,
            "window_s": float(T)}


def est_arm(trial, est, arm, win):
    t, x, y, yaw = tum(f"{TD}/{trial}/{est.lower()}_{arm}/{est.lower()}_traj.tum")
    g = gt(trial)
    vE, vN = np.gradient(g[:, 1], g[:, 0]), np.gradient(g[:, 2], g[:, 0])
    return decompose(t, y, yaw, g[:, 0], -vE, g[:, 3] - math.pi / 2, np.hypot(vE, vN), win)


def ekf3(trial, win):
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(f"{TD}/{trial}/ardupilot.bin")
    xk, sm = [], []
    while True:
        x = m.recv_match(type=["XKF1", "SIM"])
        if x is None:
            break
        if x.get_type() == "XKF1":
            if getattr(x, "C", 0) == 0:
                xk.append((x.TimeUS / 1e6, x.Yaw, x.VN, x.VE, x.PN, x.PE))
        else:
            sm.append((x.TimeUS / 1e6, x.Yaw, x.Lat, x.Lng))
    xk, sm = np.array(xk), np.array(sm)
    lat, lng = sm[:, 2].copy(), sm[:, 3].copy()
    if np.abs(lat).max() > 1000:
        lat /= 1e7; lng /= 1e7
    R = 6378137.0
    gN = np.radians(lat - lat[0]) * R; gE = np.radians(lng - lng[0]) * R * math.cos(math.radians(lat.mean()))
    gVN, gVE = np.gradient(gN, sm[:, 0]), np.gradient(gE, sm[:, 0])
    gyaw = np.unwrap(np.radians(sm[:, 1]))
    t = xk[:, 0]; w = (t >= win[0]) & (t <= win[1])
    vE_e = xk[w, 3]; psi_e = np.unwrap(np.radians(xk[w, 1])); tt = t[w]
    vE_t = np.interp(tt, sm[:, 0], gVE); psi_t = np.interp(tt, sm[:, 0], gyaw)
    spd = np.interp(tt, sm[:, 0], np.hypot(gVN, gVE))
    # NED yaw: body forward -> (cos psi, sin psi) in (N, E), so lateral (East) = spd*sin(psi)
    err = vE_e - vE_t; head = spd * (np.sin(psi_e) - np.sin(psi_t)); res = err - head
    yawerr = np.degrees(psi_e - psi_t)
    return {"errV_mean": float(err.mean()), "head_mean": float(head.mean()), "resid_mean": float(res.mean()),
            "share": float(head.mean() / err.mean()) if abs(err.mean()) > 1e-9 else None,
            "xtrack_err_m": float(_trapz(err, tt)), "xtrack_head_m": float(_trapz(head, tt)),
            "xtrack_resid_m": float(_trapz(res, tt)),
            "corr_resid_yawerr": float(np.corrcoef(res, yawerr)[0, 1]), "window_s": float(tt[-1] - tt[0])}


def endwall(trial, est, arm):
    """Valid heading outputs at GT y > 140 m that are wrong by > 3 deg, and their fate."""
    cal = json.load(open(os.path.join(RES, "fwd_calibration.json")))["frozen"]
    d = np.load(f"{TD}/{trial}/fwd_meas/meas_frozen.npz")
    tm, psi, sup = d["t"], d["psi"][:, 0], d["support"][:, 0]
    valid = np.isfinite(psi) & (sup >= cal["s_min"])
    g = gt(trial)
    y = np.interp(tm, g[:, 0], g[:, 2]); psit = np.degrees(np.interp(tm, g[:, 0], g[:, 3]) - math.pi / 2)
    err = psi - psit
    sel = valid & (y > 140)
    wrong = sel & (np.abs(err) > WRONG_DEG)
    z = np.load(f"{TD}/{trial}/{est.lower()}_{arm}/timing_and_fwd.npz")
    if est == "UKF":
        log = z["nis_psi"]                         # (t_meas, nis, accepted)
        acc = {round(float(r[0]), 4): bool(r[2]) for r in log}
        fate = [acc.get(round(float(t), 4)) for t in tm[wrong]]
    else:
        fl = z["fwd_log"]; fl = fl[fl[:, 1] == 0]  # (t_keyframe, kind, nis, ok); heading only
        # the keyframe at t_k used the latest valid forward frame in (t_{k-1}, t_k]
        kt = fl[:, 0]
        fate = []
        for t in tm[wrong]:
            j = np.searchsorted(kt, t)             # first keyframe at or after the frame
            if j >= len(kt):
                fate.append(None); continue
            prev_kf = kt[j - 1] if j > 0 else -np.inf
            later = tm[valid & (tm > t) & (tm <= kt[j])]
            fate.append(None if len(later) else bool(fl[j, 3] > 0))   # superseded by a later frame -> never tested
    fused = sum(1 for f in fate if f is True); rej = sum(1 for f in fate if f is False)
    return {"valid_y_gt_140": int(sel.sum()), "wrong_gt_3deg": int(wrong.sum()), "fused": fused, "rejected": rej,
            "not_tested": len(fate) - fused - rej,
            "max_abs_err_deg_wrong": float(np.abs(err[wrong]).max()) if wrong.any() else None}


def main(out_json):
    out = {"decomposition": {}, "endwall": {}, "plain_checker": {}}
    for ds, arms in ARMS.items():
        evo = json.load(open(os.path.join(RES, f"phase4_{ds}_evo.json")))["trials"]
        arm_res = json.load(open(os.path.join(RES, f"phase4_{ds}_arms.json")))
        for w in ("tex", "trans", "blank"):
            for r in (1, 2, 3):
                t = f"{ds}_{w}_r{r}"; win = evo[t]["window_s"]
                row = {"EKF3": ekf3(t, win)}
                for e in ("UKF", "FGO"):
                    for a in arms:
                        row[f"{e}_{a}"] = est_arm(t, e, a, win)
                out["decomposition"][t] = row
                for e in ("UKF", "FGO"):
                    for a in arms[1:]:
                        out["endwall"][f"{t}/{e}_{a}"] = endwall(t, e, a)
                if ds == "fwdplainc" and w == "tex":
                    for e in ("UKF", "FGO"):
                        c = arm_res[t][f"{e}_heading"]
                        out["plain_checker"][f"{t}/{e}"] = {
                            "accept_pct": 100 * c["fwd_counts"]["psi_fused"] / c["fwd_counts"]["psi_valid"],
                            "yaw_err_rms_deg": c["yaw_err_rms_deg"], "yaw_err_end_deg": c["yaw_err_end_deg"]}
                print(t, "done", flush=True)
    json.dump(out, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=os.path.join(RES, "phase5_analysis.json"))
    main(ap.parse_args().json)
