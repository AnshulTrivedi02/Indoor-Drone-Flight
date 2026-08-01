#!/usr/bin/env python3
"""Single-image lateral-drift overview — 12 panels, CRUISE WINDOW ONLY, shared x.

Columns are cause->effect chains, so scanning down a column tells one story:
  col 1  lateral/position   col 2  heading/bias        col 3  flow/sensor

Cruise window uses the SAME rule as the apparatus metrics in metrics.txt
(ukf_replay.py:120-135): ground-truth speed > 0.30 m/s after a 25-sample boxcar,
largest contiguous run. Everything before it (pre-arm, arming, climb) and after
it (stop, descent, land) is cropped.

Position/attitude errors are RE-GAUGED to cruise-window start, matching the
apparatus convention — so they differ from the aiding-engage gauge used in
lateral_drift_diag.py's individual figures.

Read-only. Usage (venv-ardupilot): python3 plots/lateral_overview.py [trial]
Writes plots/lateral_diag/<trial>/31_overview_cruise.png
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
NPZ = os.path.expanduser(f"~/thesis_ws/plots/_diag_{TRIAL}_flowresid.npz")
os.makedirs(OUT, exist_ok=True)
DT, WIN = 0.0125, 30.0
DRIFT_SPEED, DRIFT_TIME = 0.05, 5.0
wrap180 = lambda a: (a + 180) % 360 - 180
EST, TRU, ERR = "#1f77b4", "#000000", "#d62728"


def cruise_bounds(t, x, y):
    """Identical rule to ukf_replay.py:120-135 / ate_window_check.py."""
    sp = np.convolve(np.hypot(np.gradient(x), np.gradient(y)) / np.gradient(t),
                     np.ones(25) / 25, mode="same")
    cr = sp > 0.30
    bi = bj = i = 0
    while i < len(cr):
        if cr[i]:
            j = i
            while j < len(cr) and cr[j]:
                j += 1
            if j - i > bj - bi:
                bi, bj = i, j
            i = j
        else:
            i += 1
    return t[bi], t[bj - 1]


# ---------------- cruise window from the bag ground truth (same source as metrics.txt) ----------------
gtt = np.loadtxt(f"{D}/ukf/ground_truth.tum")
T0, T1 = cruise_bounds(gtt[:, 0], gtt[:, 1], gtt[:, 2])

# ---------------- parse the dataflash log ----------------
m = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
K = {t: [] for t in ['XKF1', 'XKF4', 'XKF5', 'XKV1', 'SIM', 'IMU']}
while True:
    x = m.recv_match(type=list(K))
    if x is None:
        break
    if x.get_type().startswith('XK') and getattr(x, 'C', 0) != 0:
        continue
    if x.get_type() == 'IMU' and getattr(x, 'I', 0) != 0:
        continue
    K[x.get_type()].append(x)
col = lambda ms, *f: np.array([[getattr(x, k) for k in f] for x in ms], float)

t1 = col(K['XKF1'], 'TimeUS')[:, 0] / 1e6
xk1 = col(K['XKF1'], 'Roll', 'Pitch', 'Yaw', 'VN', 'VE', 'VD', 'PN', 'PE', 'PD', 'GX', 'GY', 'GZ')
ts = col(K['SIM'], 'TimeUS')[:, 0] / 1e6
sim = col(K['SIM'], 'Roll', 'Pitch', 'Yaw', 'Lat', 'Lng', 'Alt')
ti = col(K['IMU'], 'TimeUS')[:, 0] / 1e6
gyrz = col(K['IMU'], 'GyrZ')[:, 0]
t5 = col(K['XKF5'], 'TimeUS')[:, 0] / 1e6
xk5 = col(K['XKF5'], 'FIX', 'FIY', 'NI')
tv1 = col(K['XKV1'], 'TimeUS')[:, 0] / 1e6
v1 = col(K['XKV1'], *[f'V{i:02d}' for i in range(0, 12)])
t4 = col(K['XKF4'], 'TimeUS')[:, 0] / 1e6
errRP = col(K['XKF4'], 'errRP')[:, 0]

lat, lng = sim[:, 3].copy(), sim[:, 4].copy()
if np.abs(lat).max() > 1000:
    lat /= 1e7; lng /= 1e7
R = 6378137.0
gN = np.radians(lat - lat[0]) * R
gE = np.radians(lng - lng[0]) * R * math.cos(math.radians(lat.mean()))
gVN, gVE = np.gradient(gN, ts), np.gradient(gE, ts)
gYaw = np.degrees(np.unwrap(np.radians(sim[:, 2])))

# on the XKF1 base
gN_i, gE_i = np.interp(t1, ts, gN), np.interp(t1, ts, gE)
gVN_i, gVE_i = np.interp(t1, ts, gVN), np.interp(t1, ts, gVE)
gYaw_i = np.interp(t1, ts, gYaw)
gRoll_i, gPitch_i = np.interp(t1, ts, sim[:, 0]), np.interp(t1, ts, sim[:, 1])

i0 = int(np.argmin(np.abs(t1 - T0)))                 # re-gauge at cruise start
errE = (xk1[:, 7] - xk1[i0, 7]) - (gE_i - gE_i[i0])
errN = (xk1[:, 6] - xk1[i0, 6]) - (gN_i - gN_i[i0])
errVE, errVN = xk1[:, 4] - gVE_i, xk1[:, 3] - gVN_i
yawErr = wrap180(xk1[:, 2] - gYaw_i)
yawErr -= yawErr[i0]
rollErr = wrap180(xk1[:, 0] - gRoll_i)
pitchErr = wrap180(xk1[:, 1] - gPitch_i)

sig_pos, sig_vel = np.sqrt(v1[:, 7:10]), np.sqrt(v1[:, 4:7])
errRP_i = np.interp(tv1, t4, errRP)
sig_yaw = np.degrees(np.sqrt(np.clip(4 * v1[:, 0:4].sum(1) - errRP_i ** 2, 0, None)))
s3 = lambda s: 3 * np.interp(t1, tv1, s)

# attribution
spd = np.hypot(gVN_i, gVE_i)
vE_head = spd * (np.sin(np.radians(gYaw_i + yawErr)) - np.sin(np.radians(gYaw_i)))
vE_other = errVE - vE_head
cum = lambda y: np.concatenate([[0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(t1))])
ct_head, ct_other = cum(vE_head), cum(vE_other)
ct_head -= ct_head[i0]; ct_other -= ct_other[i0]

# gyro-Z bias: true vs estimate, 30 s windows
true_rate = np.gradient(np.interp(ti, ts, np.radians(gYaw)), ti)
bias_true = np.degrees(gyrz - true_rate)
grid = np.arange(T0 + WIN / 2, T1 - WIN / 2, 5.0)
wmean = lambda t, y: np.array([np.mean(y[(t >= c - WIN/2) & (t <= c + WIN/2)]) for c in grid])
bt = wmean(ti, bias_true) * 60
be = wmean(t1, xk1[:, 11]) * 60
mins = np.mod(grid / 60.0, DRIFT_TIME * 2)
ba = np.where(mins < DRIFT_TIME, mins, DRIFT_TIME * 2 - mins) * DRIFT_SPEED * 60


def wslope(t, y):
    out = []
    for c in grid:
        s = (t >= c - WIN / 2) & (t <= c + WIN / 2)
        out.append(np.polyfit(t[s], y[s], 1)[0] * 60 if s.sum() > 5 else np.nan)
    return np.array(out)


def tum_yaw(p):
    a = np.loadtxt(p)
    y = np.arctan2(2 * (a[:, 7] * a[:, 6] + a[:, 4] * a[:, 5]),
                   1 - 2 * (a[:, 5] ** 2 + a[:, 6] ** 2))
    return a[:, 0], np.degrees(np.unwrap(y))


r_e = wslope(t1, np.degrees(np.unwrap(np.radians(xk1[:, 2]))))
tu, yu = tum_yaw(f"{D}/ukf/ukf_traj.tum"); r_u = -wslope(tu, yu)      # ENU -> NED sense
tf, yf = tum_yaw(f"{D}/fgo/fgo_traj.tum"); r_f = -wslope(tf, yf)

# ---------------- figure ----------------
crop = lambda t: (t >= T0) & (t <= T1)
c1, c5, cv, cg = crop(t1), crop(t5), crop(tv1), crop(ti)
fig, ax = plt.subplots(4, 3, figsize=(19, 13), sharex=True)


def band(a, t, s, lab='filter ±3σ'):
    a.fill_between(t, -s, s, color='#ff7f0e', alpha=0.22, lw=0, label=lab)


def fin(a, title, ylab, leg=True):
    a.set_title(title, fontsize=9.5)
    a.set_ylabel(ylab, fontsize=8.5)
    a.grid(alpha=0.3)
    a.axhline(0, color='0.6', lw=0.7)
    a.tick_params(labelsize=8)
    if leg:
        a.legend(fontsize=7, loc='best')


# --- column 1: lateral / position ---
a = ax[0][0]; band(a, t1[c1], s3(sig_pos[:, 1])[c1]); a.plot(t1[c1], errE[c1], color=ERR, lw=1.3, label='PE error')
fin(a, 'Cross-track (east) POSITION error', 'm')
a = ax[1][0]; band(a, t1[c1], s3(sig_vel[:, 1])[c1]); a.plot(t1[c1], errVE[c1], color=ERR, lw=0.8, label='VE error')
a.axhline(errVE[c1].mean(), color='0.2', ls=':', lw=1.1, label=f'mean {errVE[c1].mean():+.3f} m/s')
fin(a, 'East VELOCITY error (integrates into cross-track)', 'm/s')
a = ax[2][0]
a.plot(t1[c1], errE[c1], color=ERR, lw=1.4, label='actual cross-track error')
a.plot(t1[c1], ct_head[c1], color='#2ca02c', lw=1.2, label='∫ heading-driven')
a.plot(t1[c1], ct_other[c1], color=EST, lw=1.2, label='∫ remaining (lateral vel)')
a.plot(t1[c1], (ct_head + ct_other)[c1], color='0.45', lw=1.0, ls=':', label='∫ VE err (closure)')
fin(a, 'Cross-track attribution', 'm')
a = ax[3][0]; band(a, t1[c1], s3(sig_pos[:, 0])[c1]); a.plot(t1[c1], errN[c1], color=ERR, lw=1.3, label='PN error')
fin(a, 'Along-track (north) position error', 'm')

# --- column 2: heading / bias ---
a = ax[0][1]; band(a, t1[c1], s3(sig_yaw)[c1]); a.plot(t1[c1], yawErr[c1], color=ERR, lw=1.4, label='yaw error')
fin(a, 'Yaw error (re-gauged to cruise start)', 'deg')
a = ax[1][1]
a.plot(grid, ba, color='#9467bd', lw=2.0, ls='--', label='TRUE bias (SITL triangle)')
a.plot(grid, r_e, color=EST, lw=1.5, label='EKF3')
a.plot(grid, r_u, color=ERR, lw=1.5, label='UKF (ENU→NED sense)')
a.plot(grid, r_f, color='#2ca02c', lw=1.5, label='FGO (ENU→NED sense)')
fin(a, f'Yaw drift RATE ({WIN:.0f} s windows) vs true gyro-Z bias', 'deg/min')
a = ax[2][1]
a.plot(grid, bt, color='k', lw=1.8, label='TRUE gyro-Z bias')
a.plot(grid, be, color=EST, lw=1.5, label='EKF3 estimate')
a.plot(grid, bt - be, color=ERR, lw=1.5, label='estimate ERROR')
a.plot(grid, wslope(t1, wrap180(xk1[:, 2] - gYaw_i)), color='#2ca02c', lw=1.3, ls=':',
       label='observed yaw error rate')
fin(a, 'Gyro-Z bias: true vs EKF3 estimate', 'deg/min')
a = ax[3][1]
a.plot(t1[c1], rollErr[c1], lw=0.7, color=EST, label=f'roll err (mean {rollErr[c1].mean():+.3f}°)')
a.plot(t1[c1], pitchErr[c1], lw=0.7, color='#2ca02c', label=f'pitch err (mean {pitchErr[c1].mean():+.3f}°)')
fin(a, 'Roll / pitch error (tilt couples into flow)', 'deg')

# --- column 3: flow / sensor ---
def roll_stat(t, y, fn, w=10.0):
    """10 s rolling statistic on the plot grid — the raw traces are too dense to read."""
    return np.array([fn(y[(t >= c - w/2) & (t <= c + w/2)]) if ((t >= c-w/2) & (t <= c+w/2)).any()
                     else np.nan for c in grid])


a = ax[0][2]
a.plot(t5[c5], xk5[c5, 0] / 1000, color=ERR, lw=0.4, alpha=0.35, label='FIX (raw)')
a.plot(grid, roll_stat(t5, xk5[:, 0] / 1000, np.mean), color='k', lw=1.6, label='10 s mean')
a.plot(grid, roll_stat(t5, xk5[:, 0] / 1000, lambda v: np.sqrt(np.mean(v**2))),
       color='#9467bd', lw=1.6, label='10 s RMS')
fin(a, 'Flow X (LATERAL) innovation', 'rad/s')
a = ax[1][2]
a.plot(t5[c5], xk5[c5, 1] / 1000, color=EST, lw=0.4, alpha=0.35, label='FIY (raw)')
a.plot(grid, roll_stat(t5, xk5[:, 1] / 1000, np.mean), color='k', lw=1.6, label='10 s mean')
a.plot(grid, roll_stat(t5, xk5[:, 1] / 1000, lambda v: np.sqrt(np.mean(v**2))),
       color='#9467bd', lw=1.6, label='10 s RMS')
fin(a, 'Flow Y (forward) innovation', 'rad/s')
a = ax[2][2]
a.plot(t5[c5], xk5[c5, 2], color='0.2', lw=0.6, label='NI')
a.axhline(100, color=ERR, ls='--', lw=1.0, label=f'reject ≥100 ({100*np.mean(xk5[c5,2]>=100):.1f}% of cruise)')
fin(a, 'Flow normalised innovation test ratio', 'NI')
a = ax[3][2]
if os.path.exists(NPZ):
    z = np.load(NPZ)
    cz = crop(z['t'])
    a.plot(z['t'][cz], z['resid_x'][cz], color=ERR, lw=0.4, alpha=0.3, label='lateral (x) raw')
    a.plot(grid, roll_stat(z['t'], z['resid_x'], np.mean), color='k', lw=1.6, label='lateral 10 s mean')
    a.plot(grid, roll_stat(z['t'], z['resid_x'], lambda v: np.sqrt(np.mean(v**2))),
           color='#9467bd', lw=1.6, label='lateral 10 s RMS')
    a.plot(grid, roll_stat(z['t'], z['resid_y'], np.mean), color=EST, lw=1.4, label='forward 10 s mean')
    fin(a, 'h_flow residual vs GROUND TRUTH', 'rad/s')
else:
    a.text(0.5, 0.5, f'no _diag_{TRIAL}_flowresid.npz\n(run diag_flow_residual.py in venv-evo)',
           ha='center', va='center', transform=a.transAxes, fontsize=9, color='0.4')
    a.set_axis_off()

for j in range(3):
    ax[3][j].set_xlabel('sim time (s)', fontsize=9)
ax[0][0].set_xlim(T0, T1)
fig.suptitle(f'Lateral-drift overview — {TRIAL} — CRUISE WINDOW ONLY  t=[{T0:.0f}, {T1:.0f}] s '
             f'({T1-T0:.0f} s)   |   pre-arm, arming, climb, stop and landing excluded   |   '
             f'position & yaw errors re-gauged to cruise start', fontsize=11.5, y=0.998)
fig.tight_layout(rect=[0, 0, 1, 0.982])
fig.savefig(f'{OUT}/31_overview_cruise.png', dpi=120)
plt.close(fig)

print(f"{TRIAL}: cruise window [{T0:.1f}, {T1:.1f}] s ({T1-T0:.0f} s)")
print(f"  cross-track error   final {errE[c1][-1]:+8.2f} m   (heading {ct_head[c1][-1]:+.2f} | rest {ct_other[c1][-1]:+.2f})")
print(f"  along-track error   final {errN[c1][-1]:+8.2f} m")
print(f"  yaw error           final {yawErr[c1][-1]:+8.2f} deg")
print(f"  VE err mean {errVE[c1].mean():+.4f} m/s | roll err mean {rollErr[c1].mean():+.4f} deg"
      f" | flow reject {100*np.mean(xk5[c5,2]>=100):.1f}%")
print(f"-> {OUT}/31_overview_cruise.png")
