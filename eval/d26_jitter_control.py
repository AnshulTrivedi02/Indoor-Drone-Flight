#!/usr/bin/env python3
"""D26 (b), EXPLORATORY: does the flying estimator's fast heading jitter become control activity in closed loop?
Per flight, over cruise start + 10 s .. the last time y <= 135 m (before the end-wall heading degradation):
  e(t)   = flying estimator yaw - SIM yaw (deg), resampled at 25 Hz;
  jitter = e minus its 2 s centred moving average: std (deg) and the std of its time derivative (deg/s);
  vehicle activity = IMU[0] gyro std per axis (deg/s), same window;
  coupling = max over lags 0..1.0 s of corr(true yaw rate, -de/dt), both band-limited by a 0.4 s moving average.
    Rationale: the yaw controller steers the ESTIMATED yaw to its target, so true yaw ~ target - e; a jitter in e
    appears as true yaw motion of opposite sign, delayed by the controller's response.
Flying estimator: ekf3 = XKF1 (C 0), ukf = XUKO, fgo = XFGO. For shadow runs (truth flies) the same is computed for
the passive estimator named, as the open-loop reference (no feedback).
Usage (venv-ardupilot): python3 eval/d26_jitter_control.py TRIAL:EST ... [--json OUT]"""
import argparse, json, math, os
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("items", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
MSG = {"ekf3": "XKF1", "ukf": "XUKO", "fgo": "XFGO"}; out = {}
un = lambda d: np.degrees(np.unwrap(np.radians(d)))
ma = lambda x, n: np.convolve(x, np.ones(n) / n, "same")
for it in a.items:
    tr, est = it.split(":")
    m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{tr}/ardupilot.bin")); S, E, G = [], [], []
    while True:
        r = m.recv_match(type=["SIM", MSG[est], "IMU"])
        if r is None:
            break
        t = r.TimeUS / 1e6; ty = r.get_type()
        if ty == "SIM": S.append((t, r.Yaw, r.Lat, r.Lng))
        elif ty == "IMU":
            if r.I == 0: G.append((t, r.GyrX, r.GyrY, r.GyrZ))
        elif est != "ekf3" or r.C == 0: E.append((t, r.Yaw))
    S, E, G = map(np.array, (S, E, G))
    lat, lng = S[:, 2], S[:, 3]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137                      # along the corridor (y)
    v = np.gradient(ma(N, 25), S[:, 0]); cr = S[v > 0.3, 0]; c0, c1 = cr[0], cr[-1]
    t_end = S[(S[:, 0] < c1) & (N <= 135.0), 0].max()
    tg = np.arange(c0 + 10, t_end, 0.04)
    e = np.interp(tg, E[:, 0], un(E[:, 1])) - np.interp(tg, S[:, 0], un(S[:, 1])); e = (e + 180) % 360 - 180
    jit = e - ma(e, 50)
    de = np.gradient(ma(e, 10), 0.04)
    gz = np.degrees(np.interp(tg, G[:, 0], G[:, 3])); gx = np.degrees(np.interp(tg, G[:, 0], G[:, 1])); gy = np.degrees(np.interp(tg, G[:, 0], G[:, 2]))
    rz = ma(gz - gz.mean(), 10)
    best = (0.0, 0.0)
    for lag in range(0, 26):                                    # 0 .. 1.0 s, true rate lagging -de/dt
        x, y = -de[:len(de) - lag] if lag else -de, rz[lag:]
        c = float(np.corrcoef(x[25:-25], y[25:-25])[0, 1])
        if abs(c) > abs(best[0]):
            best = (c, lag * 0.04)
    r = {"est": est, "window_s": [round(float(tg[0]), 1), round(float(tg[-1]), 1)],
         "yaw_jitter_std_deg": float(jit.std()), "yaw_jitter_rate_std_dps": float(np.gradient(jit, 0.04).std()),
         "gyro_std_dps": {"x": float(gx.std()), "y": float(gy.std()), "z": float(gz.std())},
         "coupling_corr": best[0], "coupling_lag_s": best[1]}
    out[it] = r
    print(f"{it:34s} jitter {r['yaw_jitter_std_deg']:.3f} deg ({r['yaw_jitter_rate_std_dps']:.2f} deg/s) | gyro std x/y/z "
          f"{gx.std():.3f}/{gy.std():.3f}/{gz.std():.3f} deg/s | corr(true yaw rate, -de/dt) {best[0]:+.2f} at lag {best[1]:.2f} s")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
