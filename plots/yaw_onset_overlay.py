#!/usr/bin/env python3
"""Yaw-error onset overlay — yaw error, altitude and the gyro-Z bias state on one
time axis, with the flight-sequence events marked. Read-only, existing bag.

Usage (venv-ardupilot): python3 plots/yaw_onset_overlay.py [trial]
Writes plots/lateral_diag/<trial>/26_yaw_onset_overlay.png and prints the timeline.

Time axis is `flight time` = XKF1 TimeUS − first XKF1 TimeUS, matching
lateral_drift_diag.py. ArduPilot TimeUS and the Gazebo /clock the bag is
stamped with share an epoch (checked: bag ends 348.34 s, log ends 348.62 s).
"""
import sys, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
BIN = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/ardupilot.bin")
OUT = os.path.expanduser(f"~/thesis_ws/plots/lateral_diag/{TRIAL}")
os.makedirs(OUT, exist_ok=True)
wrap180 = lambda a: (a + 180) % 360 - 180

m = mavutil.mavlink_connection(BIN)
K = {t: [] for t in ['XKF1', 'XKF4', 'XKF5', 'XKV1', 'SIM', 'EV', 'MODE']}
while True:
    x = m.recv_match(type=list(K))
    if x is None:
        break
    if x.get_type().startswith('XK') and getattr(x, 'C', 0) != 0:
        continue
    K[x.get_type()].append(x)
col = lambda ms, *f: np.array([[getattr(x, k) for k in f] for x in ms], float)

t1 = col(K['XKF1'], 'TimeUS')[:, 0] / 1e6
t0 = t1[0]
xk1 = col(K['XKF1'], 'Yaw', 'GZ', 'PD')
ts = col(K['SIM'], 'TimeUS')[:, 0] / 1e6
sim = col(K['SIM'], 'Yaw', 'Alt')
t5 = col(K['XKF5'], 'TimeUS')[:, 0] / 1e6
NI = col(K['XKF5'], 'NI')[:, 0]
tv1 = col(K['XKV1'], 'TimeUS')[:, 0] / 1e6
qv = col(K['XKV1'], 'V00', 'V01', 'V02', 'V03')
t4 = col(K['XKF4'], 'TimeUS')[:, 0] / 1e6
errRP = col(K['XKF4'], 'errRP')[:, 0]

T = t1 - t0
gYaw = np.degrees(np.unwrap(np.radians(sim[:, 0])))
yawErr = wrap180(xk1[:, 0] - np.interp(t1, ts, gYaw))
alt = sim[:, 1] - sim[0, 1]
sig_yaw = np.degrees(np.sqrt(np.clip(4 * qv.sum(1) - np.interp(tv1, t4, errRP) ** 2, 0, None)))

# ---------------- flight-sequence events ----------------
EVN = {10: 'ARMED', 11: 'DISARMED', 15: 'AUTO_ARMED', 17: 'LAND_COMPLETE_MAYBE',
       18: 'LAND_COMPLETE', 28: 'NOT_LANDED', 56: 'MOTORS_INTERLOCK_DISABLED',
       57: 'MOTORS_INTERLOCK_ENABLED'}
events = [(x.TimeUS / 1e6 - t0, EVN.get(x.Id, f'EV{x.Id}')) for x in K['EV']]
MODEN = {4: 'GUIDED', 9: 'LAND'}
modes = [(x.TimeUS / 1e6 - t0, MODEN.get(int(x.Mode), f'mode{int(x.Mode)}')) for x in K['MODE']]
alt_t = ts - t0
climb_start = alt_t[np.argmax(alt > 0.05)]
alt_reached = alt_t[np.argmax(alt >= 1.8)]
land_mode = [t for t, n in modes if n == 'LAND']
cruise_start, cruise_end = alt_reached, (land_mode[0] if land_mode else T[-1])

# ---------------- plot ----------------
f, a = plt.subplots(figsize=(13, 6))
a.fill_between(T, -3 * np.interp(T, tv1 - t0, sig_yaw), 3 * np.interp(T, tv1 - t0, sig_yaw),
               color='#ff7f0e', alpha=0.15, lw=0, label='yaw ±3σ')
a.plot(T, yawErr, color='#d62728', lw=1.5, label='yaw error XKF1−SIM (deg)')
a.axhline(0, color='0.6', lw=0.8)
a.set_xlabel('flight time (s)')
a.set_ylabel('yaw error (deg)', color='#d62728')
a.tick_params(axis='y', labelcolor='#d62728')

a2 = a.twinx()
a2.plot(alt_t, alt, color='#2ca02c', lw=1.2, label='altitude (m, SIM)')
a2.plot(T, xk1[:, 1] * 10, color='#1f77b4', lw=1.2, label='gyro-Z bias ×10 (deg/s)')
a2.set_ylabel('altitude (m)  /  gyro-Z bias ×10 (deg/s)')

for t, n in [(climb_start, 'climb start'), (alt_reached, '1.8 m reached →\ncruise start'),
             (cruise_end, 'LAND')]:
    a.axvline(t, color='0.35', lw=1.0, ls='--')
    a.annotate(n, (t, 1.0), xycoords=('data', 'axes fraction'), xytext=(4, -22),
               textcoords='offset points', fontsize=7.5, color='0.25')
a.axvline(50, color='purple', lw=1.2, ls=':')
a.annotate('t = 50 s', (50, 1.0), xycoords=('data', 'axes fraction'), xytext=(4, -50),
           textcoords='offset points', fontsize=8, color='purple')

h1, l1 = a.get_legend_handles_labels()
h2, l2 = a2.get_legend_handles_labels()
a.legend(h1 + h2, l1 + l2, fontsize=8, loc='upper left')
a.set_title(f'Yaw error onset vs altitude and gyro-Z bias — {TRIAL}', fontsize=11)
a.grid(alpha=0.3)
f.tight_layout()
f.savefig(f'{OUT}/26_yaw_onset_overlay.png', dpi=140)
plt.close(f)

# zoomed 0-120 s
f, a = plt.subplots(figsize=(13, 6))
sel = T < 120
a.plot(T[sel], yawErr[sel], color='#d62728', lw=1.6, label='yaw error (deg)')
a.axhline(0, color='0.6', lw=0.8)
a.set_xlabel('flight time (s)')
a.set_ylabel('yaw error (deg)', color='#d62728')
a.tick_params(axis='y', labelcolor='#d62728')
a2 = a.twinx()
s2 = alt_t < 120
a2.plot(alt_t[s2], alt[s2], color='#2ca02c', lw=1.4, label='altitude (m)')
a2.plot(T[sel], xk1[sel, 1] * 10, color='#1f77b4', lw=1.4, label='gyro-Z bias ×10 (deg/s)')
a2.set_ylabel('altitude (m)  /  gyro-Z bias ×10 (deg/s)')
for t, n in [(climb_start, 'climb start'), (alt_reached, 'cruise start')]:
    a.axvline(t, color='0.35', lw=1.0, ls='--')
    a.annotate(n, (t, 1.0), xycoords=('data', 'axes fraction'), xytext=(4, -14),
               textcoords='offset points', fontsize=7.5, color='0.25')
a.axvline(50, color='purple', lw=1.2, ls=':')
h1, l1 = a.get_legend_handles_labels()
h2, l2 = a2.get_legend_handles_labels()
a.legend(h1 + h2, l1 + l2, fontsize=8, loc='upper left')
a.set_title(f'Same, zoomed to the first 120 s — {TRIAL}', fontsize=11)
a.grid(alpha=0.3)
f.tight_layout()
f.savefig(f'{OUT}/27_yaw_onset_overlay_zoom.png', dpi=140)
plt.close(f)

# ---------------- timeline + what changes at t=50 ----------------
print(f"=== flight sequence — {TRIAL} (flight time = TimeUS − {t0:.3f} s) ===")
print(f"  {'-'+str(round(t0-12.388,2)):>8}  bag recording starts (sim clock 12.388 s)")
print(f"  {0.0:8.2f}  dataflash logging starts (TimeUS {t0:.2f} s)")
for t, n in sorted(events + [(t, 'MODE '+n) for t, n in modes[1:]]):
    print(f"  {t:8.2f}  {n}")
print(f"  {climb_start:8.2f}  altitude leaves ground (SIM alt > 0.05 m)")
print(f"  {alt_reached:8.2f}  1.8 m reached → cruise start")
print(f"  {cruise_end:8.2f}  LAND mode (cruise end, {cruise_end-alt_reached:.1f} s of cruise)")
print(f"  {T[-1]:8.2f}  end of log")

print("\n=== signals across t=50 s (means over 10 s windows) ===")
def win(t, y, a_, b_):
    s = (t >= a_) & (t < b_)
    return float(np.mean(y[s])) if s.any() else float('nan')
rows = [('yaw error (deg)', T, yawErr), ('yaw error rate (deg/min)', T[1:], np.diff(yawErr)/np.diff(T)*60),
        ('gyro-Z bias (deg/s)', T, xk1[:, 1]), ('altitude (m)', alt_t, alt),
        ('yaw 1σ (deg)', tv1 - t0, sig_yaw), ('flow NI', t5 - t0, NI)]
print(f"  {'signal':26} " + " ".join(f"{f'{w}-{w+10}s':>12}" for w in (20, 30, 40, 50, 60, 70)))
for name, tt, yy in rows:
    print(f"  {name:26} " + " ".join(f"{win(tt, yy, w, w+10):12.4f}" for w in (20, 30, 40, 50, 60, 70)))
print(f"\nfigures -> {OUT}/26_yaw_onset_overlay.png, 27_yaw_onset_overlay_zoom.png")
