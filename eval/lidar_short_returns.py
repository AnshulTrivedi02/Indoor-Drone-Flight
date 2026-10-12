#!/usr/bin/env python3
"""LiDAR short returns (D23 cause): does ArduPilot's range path reject them for EKF3 and the UKF port?
Per flight (dataflash): RFND short returns (airborne, Dist < 50% of true height from SIM.Alt), then over each
burst (+-0.3 s): EKF3's XKF4.SH (squared height innovation test ratio; > 1 = rejected, LogStructure.h:177),
XKF3.IPD (height innovation), and EKF3's height error (XKF1.PD vs truth); for UKF-port flights the XUKS range
accepted/rejected counters (Ra, Rr) and the XUKF height error. Also replays EKF3's 3-sample median
(AP_NavEKF3_Measurements.cpp:56-85; sampled at > 50 ms) on the RFND stream to count shorts that survive it.
Usage (venv-ardupilot): python3 eval/lidar_short_returns.py TRIAL... [--json OUT]"""
import argparse, json, os
import numpy as np
from pymavlink import mavutil
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
out = {}
for tr in a.trials:
    m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{tr}/ardupilot.bin"))
    R, S, K4, K3, K1, US, UF, P = [], [], [], [], [], [], [], {}
    while True:
        r = m.recv_match(type=["RFND", "SIM", "XKF4", "XKF3", "XKF1", "XUKS", "XUKF", "PARM"])
        if r is None:
            break
        t = r.get_type(); ts = getattr(r, "TimeUS", 0) / 1e6
        if t == "PARM": P[r.Name] = r.Value
        elif t == "RFND" and r.Instance == 0: R.append((ts, r.Dist, r.Stat))
        elif t == "SIM": S.append((ts, r.Alt))
        elif t == "XKF4" and r.C == 0: K4.append((ts, r.SH))
        elif t == "XKF3" and r.C == 0: K3.append((ts, r.IPD))
        elif t == "XKF1" and r.C == 0: K1.append((ts, r.PD))
        elif t == "XUKS": US.append((ts, r.Ra, r.Rr))
        elif t == "XUKF": UF.append((ts, r.PD))
    R, S, K4, K3, K1, US, UF = (np.array(x) if len(x) else np.zeros((0, 3)) for x in (R, S, K4, K3, K1, US, UF))
    h = S[:, 1] - S[0, 1] + 0.195                                   # true base_link height (rest 0.195 m)
    th = np.interp(R[:, 0], S[:, 0], h)
    short = (th > 1.0) & (R[:, 1] < 0.5 * th)
    # EKF3 median-of-3 replay: sample the latest RFND (status Good) every > 50 ms
    ts_s, med = [], []
    last = -1.0; buf = []
    for (t, d, st), tt in zip(R, th):
        if t - last > 0.050 and st == 4:                            # RangeFinder::Status::Good = 4
            last = t; buf = (buf + [d])[-3:]
            if len(buf) == 3:
                ts_s.append(t); med.append(sorted(buf)[1])
    ts_s, med = np.array(ts_s), np.array(med)
    msh = (np.interp(ts_s, S[:, 0], h) > 1.0) & (med < 0.5 * np.interp(ts_s, S[:, 0], h))
    r = {"AHRS_EKF_TYPE": P.get("AHRS_EKF_TYPE"), "RNGFND1_GNDCLR": P.get("RNGFND1_GNDCLR"),   # was GNDCLEAR (no such PARM)
         "EK3_RNG_I_GATE": P.get("EK3_RNG_I_GATE"), "n_rfnd_short": int(short.sum()),
         "short_times_s": [round(float(x), 2) for x in R[short, 0]][:20],
         "short_dist_m": [round(float(x), 3) for x in R[short, 1]][:20],
         "n_ekf3_samples_short_after_median": int(msh.sum())}
    if short.any():
        w0, w1 = R[short, 0].min() - 0.3, R[short, 0].max() + 0.5
        k = (K4[:, 0] >= w0) & (K4[:, 0] <= w1); r["ekf3_SH_max_in_burst"] = float(K4[k, 1].max()) if k.any() else None
        r["ekf3_SH_gt1_count"] = int((K4[k, 1] > 1).sum()) if k.any() else None
        k3 = (K3[:, 0] >= w0) & (K3[:, 0] <= w1); r["ekf3_IPD_absmax_in_burst"] = float(np.abs(K3[k3, 1]).max()) if k3.any() else None
        k1 = (K1[:, 0] >= w0) & (K1[:, 0] <= w1 + 1.5)
        if k1.any():
            e = -K1[k1, 1] - np.interp(K1[k1, 0], S[:, 0], h)
            pre = (K1[:, 0] >= w0 - 2.0) & (K1[:, 0] < w0)
            e0 = float(np.median(-K1[pre, 1] - np.interp(K1[pre, 0], S[:, 0], h))) if pre.any() else 0.0
            r["ekf3_height_err_change_min_m"] = float((e - e0).min())
        if len(US):
            ku = (US[:, 0] >= w0) & (US[:, 0] <= w1)
            if ku.any():
                b = US[(US[:, 0] < w0)][-1] if (US[:, 0] < w0).any() else US[ku][0]
                r["ukf_range_acc_in_burst"] = int(US[ku, 1].max() - b[1]); r["ukf_range_rej_in_burst"] = int(US[ku, 2].max() - b[2])
            kf = (UF[:, 0] >= w0) & (UF[:, 0] <= w1 + 1.5)
            if kf.any():
                e = -UF[kf, 1] - np.interp(UF[kf, 0], S[:, 0], h)
                pre = (UF[:, 0] >= w0 - 2.0) & (UF[:, 0] < w0)
                e0 = float(np.median(-UF[pre, 1] - np.interp(UF[pre, 0], S[:, 0], h))) if pre.any() else 0.0
                r["ukf_height_err_change_min_m"] = float((e - e0).min())
    out[tr] = r
    print(tr, json.dumps(r))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
