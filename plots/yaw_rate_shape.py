#!/usr/bin/env python3
"""Is the yaw-drift acceleration shared by all three estimators, or EKF3-only?

Plots the 30 s windowed yaw RATE (deg/min) vs time for EKF3, UKF and FGO on one
axis, against the SITL analytic true gyro-Z bias (the triangle from
AP_InertialSensor_SITL.cpp:390-402). True heading is ~constant along the corridor
(+0.01 deg/min, METHODOLOGY), so an estimator's own yaw slope IS its drift rate —
this is the same assumption ukf_replay.py already makes, and it is needed because
`ground_truth.tum` is written with identity quaternions.

Sign convention: EKF3 yaw is NED (clockwise from North); UKF/FGO yaw is ENU
(anticlockwise from East). The same physical drift therefore appears with
OPPOSITE sign. Both raw and sign-normalised (NED-sense) values are reported.

Read-only. Usage (venv-ardupilot): python3 plots/yaw_rate_shape.py [trial]
"""
import sys, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
D = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}")
OUT = os.path.expanduser(f"~/thesis_ws/plots/lateral_diag/{TRIAL}")
os.makedirs(OUT, exist_ok=True)
WIN, DRIFT_SPEED, DRIFT_TIME = 30.0, 0.05, 5.0

# ---- EKF3 yaw (NED) from XKF1 ----
m = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
xk, sim = [], []
while True:
    x = m.recv_match(type=['XKF1', 'SIM'])
    if x is None:
        break
    if x.get_type() == 'XKF1':
        if getattr(x, 'C', 0) == 0:
            xk.append((x.TimeUS / 1e6, x.Yaw))
    else:
        sim.append((x.TimeUS / 1e6, x.Yaw))
xk = np.array(xk); sim = np.array(sim)
t_e = xk[:, 0]; yaw_e = np.degrees(np.unwrap(np.radians(xk[:, 1])))
t_s = sim[:, 0]; yaw_s = np.degrees(np.unwrap(np.radians(sim[:, 1])))

# ---- UKF / FGO yaw (ENU) from their TUM quaternions ----
def tum_yaw(p):
    a = np.loadtxt(p)
    qx, qy, qz, qw = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    yaw = np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy ** 2 + qz ** 2))
    return a[:, 0], np.degrees(np.unwrap(yaw))

t_u, yaw_u = tum_yaw(f"{D}/ukf/ukf_traj.tum")
t_f, yaw_f = tum_yaw(f"{D}/fgo/fgo_traj.tum")

# ---- windowed slopes on a common grid ----
lo = max(t_e[0], t_u[0], t_f[0]) + WIN / 2
hi = min(t_e[-1], t_u[-1], t_f[-1]) - WIN / 2
grid = np.arange(lo, hi, 5.0)
def rate(t, y):
    out = []
    for c in grid:
        s = (t >= c - WIN / 2) & (t <= c + WIN / 2)
        out.append(np.polyfit(t[s], y[s], 1)[0] * 60 if s.sum() > 5 else np.nan)
    return np.array(out)

r_e, r_u, r_f, r_s = rate(t_e, yaw_e), rate(t_u, yaw_u), rate(t_f, yaw_f), rate(t_s, yaw_s)
period = DRIFT_TIME * 2
mins = np.mod(grid / 60.0, period)
true_bias = np.where(mins < period / 2, mins, period - mins) * DRIFT_SPEED * 60   # deg/min

# NED-sense: EKF3 as logged; ENU estimators negated
n_e, n_u, n_f = r_e, -r_u, -r_f

f, (a, b) = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
a.plot(grid, true_bias, color='#9467bd', lw=2.0, ls='--', label='TRUE gyro-Z bias (SITL analytic triangle)')
a.plot(grid, n_e, color='#1f77b4', lw=1.6, label='EKF3 (XKF1 yaw, NED)')
a.plot(grid, n_u, color='#d62728', lw=1.6, label='UKF (TUM yaw, ENU → NED sense)')
a.plot(grid, n_f, color='#2ca02c', lw=1.6, label='FGO (TUM yaw, ENU → NED sense)')
a.plot(grid, r_s, color='k', lw=1.0, alpha=0.5, label='true heading rate (SIM.Yaw, ≈0)')
a.axhline(0, color='0.6', lw=0.8)
a.set_ylabel('yaw rate (deg/min), NED sense')
a.set_title(f'Yaw drift RATE vs time, 30 s windows — {TRIAL}', fontsize=11)
a.grid(alpha=0.3); a.legend(fontsize=8, loc='upper left')

b.plot(grid, true_bias - n_e, color='#1f77b4', lw=1.6, label='EKF3')
b.plot(grid, true_bias - n_u, color='#d62728', lw=1.6, label='UKF')
b.plot(grid, true_bias - n_f, color='#2ca02c', lw=1.6, label='FGO')
b.axhline(0, color='0.6', lw=0.8)
b.set_xlabel('sim time (s)')
b.set_ylabel('true bias − drift rate (deg/min)')
b.set_title('Shortfall against the true bias (0 = drifting at exactly the physical rate)', fontsize=10)
b.grid(alpha=0.3); b.legend(fontsize=8)
f.tight_layout()
f.savefig(f'{OUT}/30_yaw_rate_shape.png', dpi=140)
plt.close(f)

print(f"=== yaw drift rate shape — {TRIAL} (deg/min, 30 s windows, NED sense) ===")
print(f"{'sim t':>7}{'true bias':>11}{'EKF3':>9}{'UKF':>9}{'FGO':>9}")
for c in (60, 100, 150, 200, 250, 300, 325):
    i = int(np.argmin(np.abs(grid - c)))
    print(f"{grid[i]:7.0f}{true_bias[i]:11.2f}{n_e[i]:9.2f}{n_u[i]:9.2f}{n_f[i]:9.2f}")
print()
for nm, y in (('EKF3', n_e), ('UKF', n_u), ('FGO', n_f)):
    s = np.isfinite(y)
    k = np.polyfit(grid[s] / 60, y[s], 1)
    e1 = np.nanmean(y[(grid > 30) & (grid < 130)])
    e2 = np.nanmean(y[(grid > 230) & (grid < 330)])
    print(f"{nm:5} first 100 s mean {e1:7.2f} | last 100 s mean {e2:7.2f} | ratio {e2/e1 if e1 else float('nan'):5.2f}"
          f" | d(rate)/dt {k[0]:+6.2f} deg/min per min   (true: 3.00)")
print(f"\nRaw (as logged, before sign normalisation): EKF3 {np.nanmean(r_e):+.2f}, "
      f"UKF {np.nanmean(r_u):+.2f}, FGO {np.nanmean(r_f):+.2f} deg/min")
print(f"figure -> {OUT}/30_yaw_rate_shape.png")
