#!/usr/bin/env python3
"""EKF3 gyro-z bias ramp-tracking, from XKF1.GZ in each dsn_* .BIN, for the three-way
comparison. EKF3's evo -a is unchanged by the h_flow correction (measurement-side vs
prediction-side derotation); only this bias-vs-true-ramp statistic is new.

XKF1.GZ = 100*degrees(gyroBias.z) (cd/s, FRD; AP_NavEKF3_Logging.cpp:48). Cruise gated
on XKF1 speed>0.3. True bias = sitl_gyro_drift(TimeUS/1e6) (triangle wave). Reports
|bias| mean, bias% vs instantaneous true mean, and ramp d|b|/dt vs true. venv-ardupilot.
Usage: ekf3_bias_ramp.py            (all nine dsn_* bags)"""
import os, sys, glob
import numpy as np
sys.path.insert(0, os.path.expanduser("~/thesis_ws/src/estimators"))
from measurement_models import sitl_gyro_drift
from pymavlink import mavutil

TRIALS = [f"dsn_{c}_r{i}" for c in ("tex", "blank", "trans") for i in (1, 2, 3)]
print(f"{'trial':16}{'n_cruise':>9}{'|b|mean':>9}{'true_mean':>10}{'bias%':>8}{'ramp d|b|/dt':>14}{'true_ramp':>10}")
rows = {}
for tr in TRIALS:
    binp = os.path.expanduser(f"~/thesis_data/trials/{tr}/ardupilot.bin")
    if not os.path.exists(binp):
        print(f"{tr:16}  (no .BIN)"); continue
    m = mavutil.mavlink_connection(binp)
    rec = []
    while True:
        msg = m.recv_match(type=['XKF1'], blocking=False)
        if msg is None:
            break
        # first core only (C==0) to avoid duplicate lanes
        if getattr(msg, 'C', 0) != 0:
            continue
        rec.append((msg.TimeUS/1e6, msg.GZ, msg.VN, msg.VE))
    a = np.array(rec, float)
    if len(a) == 0:
        print(f"{tr:16}  (no XKF1)"); continue
    # GZ scaling: stored as 100*deg/s -> deg/min = GZ*0.6 (raw). Detect if DFReader
    # already applied the 0.01 multiplier (then GZ is deg/s -> *60).
    gz = a[:, 1]
    gz_dpm = gz*0.6 if np.median(np.abs(gz)) > 1.0 else gz*60.0
    spd = np.hypot(a[:, 2], a[:, 3])
    cr = spd > 0.30
    if cr.sum() < 20:
        print(f"{tr:16}  (no cruise)"); continue
    t = a[cr, 0]; b = np.abs(gz_dpm[cr]); tb = sitl_gyro_drift(t)
    tmin = (t - t[0]) / 60.0
    bmean = float(np.mean(b)); tmean = float(np.mean(tb))
    pct = 100.0*bmean/tmean
    ramp = float(np.polyfit(tmin, b, 1)[0]); tramp = float(np.polyfit(tmin, tb, 1)[0])
    rows[tr] = dict(bmean=bmean, tmean=tmean, pct=pct, ramp=ramp, tramp=tramp, n=int(cr.sum()))
    print(f"{tr:16}{cr.sum():>9}{bmean:>9.2f}{tmean:>10.2f}{pct:>8.0f}{ramp:>14.2f}{tramp:>10.2f}")
    # persist series for the joint plot
    d = os.path.expanduser(f"~/thesis_data/trials/{tr}/ekf3")
    os.makedirs(d, exist_ok=True)
    np.savetxt(f"{d}/bgz_series.txt", np.column_stack([t, b, tb]),
               header="t_sec est_bias_absdpm true_bias_dpm", comments="# ")
