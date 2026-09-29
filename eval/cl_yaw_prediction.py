#!/usr/bin/env python3
"""Basis for the closed-loop Part 2 bands at the ruled EKF3 yaw sigma (5.00 deg, the
ArduPilot floor; VISO_YAW_M_NSE 0.05). OFFLINE approximation of EKF3's yaw subsystem, NOT
EKF3: states [yaw, gyro-z bias (delta form)], predict every 12.5 ms with EKF3's formulas
(q_att = (dt*GYRO_P_NSE)^2, q_bias = (dt^2*GBIAS_P_NSE)^2, init bias sd 2.5 deg/s * dt),
driven by the recorded /imu/data_raw gyro-z; updates with the frozen Phase 3 heading on every
3rd frame when valid (the node's rate), R = (5 deg)^2, gate |nu| <= 3*sqrt(S)
(EK3_YAW_I_GATE 300). Truth yaw from GT, used only to score. Outputs, over the cruise:
yaw-error p95/max, the cross-track that the yaw error alone would produce at 0.5 m/s, and the
confident-wrong end-wall headings (valid, |err| > 3 deg, GT y > 140 m) that pass the gate.
Usage (venv-evo): python3 eval/cl_yaw_prediction.py TRIAL_DIR [...] [--json OUT]"""
import argparse, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scale_check as S
from cruise_window import cruise_bounds
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
DT, GYRO_P_NSE, GBIAS_P_NSE = 0.0125, 0.015, 0.001
R, NGATE, EVERY_N = math.radians(5.0) ** 2, 3.0, 3
fz = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "fwd_calibration.json")))["frozen"]
out = {}
for path in a.trials:
    S.TD, tr = os.path.dirname(path), os.path.basename(path)
    gt, fl, imu = S.read_bag(tr)
    m = np.load(f"{path}/fwd_meas/meas_frozen.npz"); tm, psi, sup = m["t"], m["psi"][:, 0], m["support"][:, 0]
    g = np.load(f"{path}/fwd_meas/gt_eval_only.npz")["g"]              # t, E, N, unwrapped ENU yaw
    yaw_true = lambda t: np.interp(t, g[:, 0], g[:, 3]) - math.pi / 2   # corridor frame, ENU sense
    yN = lambda t: np.interp(t, g[:, 0], g[:, 2])
    c0, c1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])       # the PINNED dataset cruise window
    # filter in the ENU/FLU sense (gyro z FLU = yaw rate ENU); start at cruise start - 20 s, aligned to truth
    t0 = c0 - 20.0
    x = np.array([yaw_true(t0), 0.0]); P = np.diag([math.radians(1) ** 2, (math.radians(2.5) * DT) ** 2])
    ti, gz = imu[:, 0], imu[:, 3]
    tk = np.arange(t0, c1, DT)
    meas_idx = [k for k in range(len(tm)) if k % EVERY_N == 0 and np.isfinite(psi[k]) and sup[k] >= fz["s_min"] and t0 <= tm[k] <= c1]
    mi = 0; rows = []; fused_wrong = wrong = 0
    for t in tk:
        w = np.interp(t + DT / 2, ti, gz)
        x = np.array([x[0] + w * DT - x[1], x[1]])
        F = np.array([[1, -1], [0, 1]])
        P = F @ P @ F.T + np.diag([(DT * GYRO_P_NSE) ** 2, (DT * DT * GBIAS_P_NSE) ** 2])
        while mi < len(meas_idx) and tm[meas_idx[mi]] <= t + DT:
            k = meas_idx[mi]; mi += 1
            z = math.radians(psi[k]); nu = (z - x[0] + math.pi) % (2 * math.pi) - math.pi
            Sv = P[0, 0] + R
            err = math.degrees(z - yaw_true(tm[k]))
            if yN(tm[k]) > 140 and abs(err) > 3:
                wrong += 1
            if nu * nu <= NGATE ** 2 * Sv:
                K = P[:, 0] / Sv; x = x + K * nu; P = P - np.outer(K, P[0, :])
                if yN(tm[k]) > 140 and abs(err) > 3:
                    fused_wrong += 1
        if c0 <= t <= c1:
            rows.append((t, math.degrees(x[0] - yaw_true(t)), yN(t)))
    r = np.array(rows); e = r[:, 1]; body, wall = r[:, 2] <= 140, r[:, 2] > 140
    xt = np.cumsum(0.5 * np.sin(np.radians(e)) * DT)      # cross-track from the yaw error alone
    out[tr] = {"yaw_err_abs_p95_deg": float(np.percentile(np.abs(e), 95)), "yaw_err_abs_max_deg": float(np.abs(e).max()),
               "yaw_err_mean_deg": float(e.mean()), "xtrack_from_yaw_max_m": float(np.abs(xt).max()),
               "lat_speed_from_yaw_max_ms": float(0.5 * np.sin(np.radians(np.abs(e).max()))),
               "window_s": [float(c0), float(c1)], "window_gt_y_m": [float(r[0, 2]), float(r[-1, 2])],
               "y_le_140": {"p95": float(np.percentile(np.abs(e[body]), 95)), "max": float(np.abs(e[body]).max())},
               "y_gt_140": {"p95": float(np.percentile(np.abs(e[wall]), 95)), "max": float(np.abs(e[wall]).max()),
                            "max_minus_entry_deg": float(np.abs(e[wall]).max() - abs(e[wall][0]))},
               "endwall_wrong": wrong, "endwall_wrong_passing_gate": fused_wrong, "n_updates_available": len(meas_idx)}
    print(tr, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out[tr].items()}, flush=True)
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
