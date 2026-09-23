#!/usr/bin/env python3
"""Is the accelerating yaw drift a diverging bias ESTIMATE, or a ramping TRUE bias?

Compares, all in deg/min on one axis:
  - true gyro-Z bias      = IMU.GyrZ - d(SIM.Yaw)/dt   (smoothed)
  - EKF3's bias estimate  = XKF1.GZ  (deg/s, verified: LogStructure.h XKF1 fmt 'c'
                            = int16*0.01, unit 'k' = deg/s; getGyroBias divides the
                            delta-form state by dtEkfAvg)
  - bias estimate error   = true - estimate
  - observed yaw error rate = windowed slope of (XKF1.Yaw - SIM.Yaw)
  - SITL analytic drift   = triangle wave, AP_InertialSensor_SITL.cpp:390-402:
                            period = 2*SIM_DRIFT_TIME min; ramp = minutes*SIM_DRIFT_SPEED

Absent any yaw correction, yaw error rate == bias estimate error exactly, so the
magnitude match (not just the correlation) is the mechanism test.

Read-only. Usage (venv-ardupilot): python3 plots/yaw_bias_mechanism.py [trial]
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
BIN = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/ardupilot.bin")
OUT = os.path.expanduser(f"~/thesis_ws/plots/lateral_diag/{TRIAL}")
os.makedirs(OUT, exist_ok=True)
DRIFT_SPEED, DRIFT_TIME = 0.05, 5.0        # SIM_DRIFT_SPEED deg/s/min, SIM_DRIFT_TIME min
WIN = 30.0                                  # slope window, s

m = mavutil.mavlink_connection(BIN)
K = {t: [] for t in ['XKF1', 'SIM', 'IMU']}
while True:
    x = m.recv_match(type=list(K))
    if x is None:
        break
    if x.get_type() == 'XKF1' and getattr(x, 'C', 0) != 0:
        continue
    if x.get_type() == 'IMU' and getattr(x, 'I', 0) != 0:
        continue
    K[x.get_type()].append(x)
col = lambda ms, *f: np.array([[getattr(x, k) for k in f] for x in ms], float)

t1 = col(K['XKF1'], 'TimeUS')[:, 0] / 1e6           # ArduPilot sim clock (= Gazebo /clock)
yaw_e = col(K['XKF1'], 'Yaw')[:, 0]
gz_est = col(K['XKF1'], 'GZ')[:, 0]                  # deg/s
ts = col(K['SIM'], 'TimeUS')[:, 0] / 1e6
yaw_t = np.degrees(np.unwrap(np.radians(col(K['SIM'], 'Yaw')[:, 0])))
ti = col(K['IMU'], 'TimeUS')[:, 0] / 1e6
gyrz = col(K['IMU'], 'GyrZ')[:, 0]                   # rad/s

# ---- true gyro-Z bias: measured gyro minus true yaw rate ----
true_rate = np.gradient(np.interp(ti, ts, np.radians(yaw_t)), ti)      # rad/s
bias_true = np.degrees(gyrz - true_rate)                               # deg/s
sm = lambda a, n: np.convolve(a, np.ones(n) / n, mode='same')
n_s = max(3, int(round(5.0 / np.median(np.diff(ti)))))                 # 5 s boxcar
bias_true_s = sm(bias_true, n_s)
edge = n_s                                                             # boxcar edge artefact

# ---- SITL analytic triangle (function of absolute sim time) ----
def sitl_drift(t_sim):
    period = DRIFT_TIME * 2
    mins = np.mod(t_sim / 60.0, period)
    return np.where(mins < period / 2, mins, period - mins) * DRIFT_SPEED   # deg/s

# ---- windowed rates on a common grid ----
yaw_err = (yaw_e - np.interp(t1, ts, yaw_t) + 180) % 360 - 180
grid = np.arange(t1[0] + WIN / 2, t1[-1] - WIN / 2, 5.0)
def slope(tt, yy, c):
    s = (tt >= c - WIN / 2) & (tt <= c + WIN / 2)
    return np.polyfit(tt[s], yy[s], 1)[0] * 60 if s.sum() > 5 else np.nan
rate_obs = np.array([slope(t1, yaw_err, c) for c in grid])              # deg/min
bt = np.array([np.mean(bias_true_s[(ti >= c - WIN/2) & (ti <= c + WIN/2)]) for c in grid]) * 60
be = np.array([np.mean(gz_est[(t1 >= c - WIN/2) & (t1 <= c + WIN/2)]) for c in grid]) * 60
ba = sitl_drift(grid) * 60
bias_err = bt - be                                                      # deg/min

ok = np.isfinite(rate_obs) & np.isfinite(bias_err) & (grid > ti[0] + edge * np.median(np.diff(ti)))
r = np.corrcoef(bias_err[ok], rate_obs[ok])[0, 1]
fit = np.polyfit(bias_err[ok], rate_obs[ok], 1)

# ================= FIGURE 28: the three bias series =================
f, a = plt.subplots(figsize=(13, 6))
a.plot(ti, bias_true_s * 60, color='k', lw=0.6, alpha=0.25,
       label='TRUE gyro-Z bias, 5 s smooth (controller yaw oscillation)')
a.plot(grid, bt, color='k', lw=2.0, label='TRUE gyro-Z bias, 30 s windowed mean')
a.plot(grid, ba, color='#9467bd', lw=1.6, ls='--',
       label=f'SITL analytic triangle (SIM_DRIFT_SPEED={DRIFT_SPEED}, TIME={DRIFT_TIME} min)')
a.plot(t1, gz_est * 60, color='#1f77b4', lw=1.2, label='EKF3 bias ESTIMATE (XKF1.GZ)')
a.plot(grid, bias_err, color='#d62728', lw=1.6, label='bias estimate ERROR (true − estimate)')
a.plot(grid, rate_obs, color='#2ca02c', lw=1.6, ls=':', label='observed yaw error rate (30 s windowed slope)')
a.axhline(0, color='0.6', lw=0.8)
a.axhline(9.8, color='0.5', lw=0.9, ls='-.', label='the "9.8 deg/min" cruise-mean constant')
a.set_xlabel('sim time (s)  [ArduPilot TimeUS = Gazebo /clock]')
a.set_ylabel('deg/min')
a.set_title(f'Yaw drift mechanism — {TRIAL}: the TRUE bias ramps; the estimate does not follow it', fontsize=11)
a.grid(alpha=0.3)
a.legend(fontsize=8, loc='upper left')
a.set_ylim(-2, 18)
f.tight_layout()
f.savefig(f'{OUT}/28_yaw_bias_mechanism.png', dpi=140)
plt.close(f)

# ================= FIGURE 29: rate vs bias error, coloured by time =================
f, (a, b) = plt.subplots(1, 2, figsize=(13, 5.5))
sc = a.scatter(bias_err[ok], rate_obs[ok], c=grid[ok], cmap='viridis', s=26)
lim = [min(bias_err[ok].min(), rate_obs[ok].min()) - 1, max(bias_err[ok].max(), rate_obs[ok].max()) + 1]
a.plot(lim, lim, color='k', lw=1.0, ls='--', label='1:1 (pure uncorrected bias)')
a.plot(lim, np.polyval(fit, lim), color='#d62728', lw=1.2,
       label=f'fit slope {fit[0]:.2f}, intercept {fit[1]:+.2f}\nr = {r:+.3f}')
a.set_xlabel('bias estimate error (deg/min)')
a.set_ylabel('observed yaw error rate (deg/min)')
a.set_title('Yaw error rate vs bias estimate error')
a.grid(alpha=0.3)
a.legend(fontsize=8)
f.colorbar(sc, ax=a, label='sim time (s)')
b.plot(grid, rate_obs - bias_err, color='#8c564b', lw=1.5)
b.axhline(0, color='0.6', lw=0.8)
b.set_xlabel('sim time (s)')
b.set_ylabel('deg/min')
b.set_title('Residual: yaw error rate − bias estimate error\n(what the flow-driven yaw correction removes)')
b.grid(alpha=0.3)
f.tight_layout()
f.savefig(f'{OUT}/29_rate_vs_bias_error.png', dpi=140)
plt.close(f)

# ================= report =================
print(f"=== yaw-drift mechanism — {TRIAL} ===")
print(f"XKF1.GX/GY/GZ units: deg/s (LogStructure.h:436 fmt 'c'=int16*0.01, unit 'k'=deg/s;")
print(f"  AP_NavEKF3_Logging.cpp:50 stores 100*degrees(gyroBias); getGyroBias = state/dtEkfAvg)")
print(f"SITL drift (AP_InertialSensor_SITL.cpp:390-402): TRIANGLE, period 2*{DRIFT_TIME:.0f}=10 min,")
print(f"  ramp = minutes*{DRIFT_SPEED} deg/s -> d(bias)/dt = {DRIFT_SPEED*60:.1f} deg/min per minute, peak")
print(f"  {DRIFT_SPEED*DRIFT_TIME*60:.1f} deg/min at sim t=300 s. Function of absolute sim time, not arming.")
print()
print(f"{'sim t':>7} {'true bias':>10} {'analytic':>10} {'EKF3 est':>10} {'est error':>10} {'yaw rate':>10}")
print(f"{'(s)':>7} {'(deg/min)':>10} {'(deg/min)':>10} {'(deg/min)':>10} {'(deg/min)':>10} {'(deg/min)':>10}")
for c in (50, 100, 150, 200, 250, 300, 330):
    i = int(np.argmin(np.abs(grid - c)))
    print(f"{grid[i]:7.0f} {bt[i]:10.2f} {ba[i]:10.2f} {be[i]:10.2f} {bias_err[i]:10.2f} {rate_obs[i]:10.2f}")
print()
print(f"correlation(bias estimate error, yaw error rate) = {r:+.4f}   (n={ok.sum()} windows)")
print(f"regression  yaw_rate = {fit[0]:.3f} x bias_error {fit[1]:+.3f}   (1:1 would be slope 1, intercept 0)")
print(f"mean |yaw_rate - bias_error| = {np.mean(np.abs(rate_obs[ok]-bias_err[ok])):.2f} deg/min")
print(f"true bias range over flight: {bt[ok].min():+.2f} .. {bt[ok].max():+.2f} deg/min")
print(f"EKF3 estimate range        : {be[ok].min():+.2f} .. {be[ok].max():+.2f} deg/min")
print(f"  -> estimate covers {100*np.mean(be[ok]/np.maximum(bt[ok],1e-9)):.0f}% of the true bias on average")
print(f"\nfigures -> {OUT}/28_yaw_bias_mechanism.png, 29_rate_vs_bias_error.png")
