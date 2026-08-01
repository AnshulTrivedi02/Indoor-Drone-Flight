#!/usr/bin/env python3
"""Cross-trial lateral-drift overview — all nine dsn_* bags in one image, CRUISE
WINDOW ONLY, for spotting patterns that hold across repeats vs ones that don't.

Colour = condition (textured / transition / blank), line style = repeat. Cruise
window per trial uses the same rule as the apparatus metrics (ukf_replay.py:120-135).
All series re-gauged to each trial's own cruise start, and plotted against time
SINCE CRUISE START so the nine are directly comparable.

Read-only. Usage (venv-ardupilot): python3 plots/lateral_overview_all.py
Writes plots/lateral_diag/32_overview_all_trials.png
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

OUT = os.path.expanduser("~/thesis_ws/plots/lateral_diag")
os.makedirs(OUT, exist_ok=True)
WIN, DRIFT_SPEED, DRIFT_TIME = 30.0, 0.05, 5.0
CONDS = {"textured": "#1f77b4", "transition": "#ff7f0e", "blank": "#d62728"}
TRIALS = [(f"dsn_{k}_r{i}", c, i) for k, c in
          [("tex", "textured"), ("trans", "transition"), ("blank", "blank")] for i in (1, 2, 3)]
LS = {1: '-', 2: '--', 3: ':'}
wrap180 = lambda a: (a + 180) % 360 - 180


def cruise_bounds(t, x, y):
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


def tum_yaw(p):
    a = np.loadtxt(p)
    y = np.arctan2(2 * (a[:, 7] * a[:, 6] + a[:, 4] * a[:, 5]),
                   1 - 2 * (a[:, 5] ** 2 + a[:, 6] ** 2))
    return a[:, 0], np.degrees(np.unwrap(y))


def load(trial):
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    gtt = np.loadtxt(f"{D}/ukf/ground_truth.tum")
    T0, T1 = cruise_bounds(gtt[:, 0], gtt[:, 1], gtt[:, 2])
    m = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
    K = {t: [] for t in ['XKF1', 'XKF5', 'SIM', 'IMU']}
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
    xk1 = col(K['XKF1'], 'Yaw', 'VE', 'PN', 'PE', 'GZ')
    ts = col(K['SIM'], 'TimeUS')[:, 0] / 1e6
    sim = col(K['SIM'], 'Yaw', 'Lat', 'Lng')
    t5 = col(K['XKF5'], 'TimeUS')[:, 0] / 1e6
    NI = col(K['XKF5'], 'NI')[:, 0]
    ti = col(K['IMU'], 'TimeUS')[:, 0] / 1e6
    gyrz = col(K['IMU'], 'GyrZ')[:, 0]

    lat, lng = sim[:, 1].copy(), sim[:, 2].copy()
    if np.abs(lat).max() > 1000:
        lat /= 1e7; lng /= 1e7
    R = 6378137.0
    gN = np.radians(lat - lat[0]) * R
    gE = np.radians(lng - lng[0]) * R * math.cos(math.radians(lat.mean()))
    gYaw = np.degrees(np.unwrap(np.radians(sim[:, 0])))
    gN_i, gE_i, gYaw_i = (np.interp(t1, ts, v) for v in (gN, gE, gYaw))
    i0 = int(np.argmin(np.abs(t1 - T0)))
    d = dict(T0=T0, T1=T1, t=t1 - T0, dur=T1 - T0)
    d['errE'] = (xk1[:, 3] - xk1[i0, 3]) - (gE_i - gE_i[i0])
    d['errN'] = (xk1[:, 2] - xk1[i0, 2]) - (gN_i - gN_i[i0])
    ye = wrap180(xk1[:, 0] - gYaw_i)
    d['yawErr'] = ye - ye[i0]
    d['errVE'] = xk1[:, 1] - np.interp(t1, ts, np.gradient(gE, ts))
    d['t5'] = t5 - T0; d['NI'] = NI
    d['gz_est'] = xk1[:, 4] * 60                       # deg/min

    grid = np.arange(WIN / 2, (T1 - T0) - WIN / 2, 5.0)
    d['grid'] = grid
    ws = lambda t, y: np.array([np.polyfit(t[(t >= c-WIN/2) & (t <= c+WIN/2)],
                                           y[(t >= c-WIN/2) & (t <= c+WIN/2)], 1)[0]*60
                                if ((t >= c-WIN/2) & (t <= c+WIN/2)).sum() > 5 else np.nan
                                for c in grid])
    d['r_ekf3'] = ws(t1 - T0, np.degrees(np.unwrap(np.radians(xk1[:, 0]))))
    tu, yu = tum_yaw(f"{D}/ukf/ukf_traj.tum"); d['r_ukf'] = -ws(tu - T0, yu)
    tf, yf = tum_yaw(f"{D}/fgo/fgo_traj.tum"); d['r_fgo'] = -ws(tf - T0, yf)
    true_rate = np.gradient(np.interp(ti, ts, np.radians(gYaw)), ti)
    bt = np.degrees(gyrz - true_rate)
    d['bias_true'] = np.array([np.mean(bt[(ti-T0 >= c-WIN/2) & (ti-T0 <= c+WIN/2)]) for c in grid]) * 60
    mins = np.mod((grid + T0) / 60.0, DRIFT_TIME * 2)
    d['bias_analytic'] = np.where(mins < DRIFT_TIME, mins, DRIFT_TIME*2 - mins) * DRIFT_SPEED * 60
    return d


data = {}
for tr, cond, rep in TRIALS:
    data[tr] = load(tr)
    print(f"  loaded {tr}  cruise [{data[tr]['T0']:.0f},{data[tr]['T1']:.0f}]s", flush=True)

fig, ax = plt.subplots(3, 3, figsize=(19, 12))
crop = lambda d, t: (t >= 0) & (t <= d['dur'])


def overlay(a, key, tkey='t', ylab='', title='', scale=1.0):
    for tr, cond, rep in TRIALS:
        d = data[tr]; t = d[tkey]; c = crop(d, t)
        a.plot(t[c], d[key][c] * scale, color=CONDS[cond], ls=LS[rep], lw=1.2)
    a.set_title(title, fontsize=10)
    a.set_ylabel(ylab, fontsize=9)
    a.set_xlabel('time since cruise start (s)', fontsize=8.5)
    a.grid(alpha=0.3); a.axhline(0, color='0.6', lw=0.7); a.tick_params(labelsize=8)


overlay(ax[0][0], 'errE', title='Cross-track (east) position error — all 9', ylab='m')
overlay(ax[0][1], 'yawErr', title='Yaw error — all 9', ylab='deg')
overlay(ax[0][2], 'errN', title='Along-track (north) position error — all 9', ylab='m')
h = [plt.Line2D([], [], color=c, lw=2, label=k) for k, c in CONDS.items()] + \
    [plt.Line2D([], [], color='0.4', ls=LS[r], lw=1.2, label=f'r{r}') for r in (1, 2, 3)]
ax[0][0].legend(handles=h, fontsize=7.5, ncol=2, loc='upper left')

# row 2: yaw drift rate per condition, one panel each, three estimators
for j, cond in enumerate(CONDS):
    a = ax[1][j]
    trs = [t for t, c, _ in TRIALS if c == cond]
    a.plot(data[trs[0]]['grid'], data[trs[0]]['bias_analytic'], color='#9467bd', lw=2.4, ls='--',
           label='TRUE bias (SITL triangle)')
    for tr in trs:
        d = data[tr]
        rep = int(tr[-1])
        a.plot(d['grid'], d['r_ekf3'], color='#1f77b4', ls=LS[rep], lw=1.2)
        a.plot(d['grid'], d['r_ukf'], color='#d62728', ls=LS[rep], lw=1.2)
        a.plot(d['grid'], d['r_fgo'], color='#2ca02c', ls=LS[rep], lw=1.2)
    a.set_title(f'Yaw drift RATE — {cond} (3 repeats)', fontsize=10)
    a.set_ylabel('deg/min, NED sense', fontsize=9)
    a.set_xlabel('time since cruise start (s)', fontsize=8.5)
    a.grid(alpha=0.3); a.axhline(0, color='0.6', lw=0.7); a.tick_params(labelsize=8)
    if j == 0:
        a.legend(handles=[plt.Line2D([], [], color='#9467bd', ls='--', lw=2.4, label='TRUE bias'),
                          plt.Line2D([], [], color='#1f77b4', lw=1.6, label='EKF3'),
                          plt.Line2D([], [], color='#d62728', lw=1.6, label='UKF'),
                          plt.Line2D([], [], color='#2ca02c', lw=1.6, label='FGO')],
                 fontsize=7.5, loc='lower right')

# row 3
overlay(ax[2][0], 'errVE', title='EKF3 east-velocity error — all 9', ylab='m/s')
a = ax[2][1]
for tr, cond, rep in TRIALS:
    d = data[tr]
    a.plot(d['grid'], d['bias_true'], color='k', ls=LS[rep], lw=0.9, alpha=0.5)
    a.plot(d['t'][crop(d, d['t'])], d['gz_est'][crop(d, d['t'])], color=CONDS[cond], ls=LS[rep], lw=1.2)
a.set_title('Gyro-Z bias: TRUE (black) vs EKF3 estimate (coloured) — all 9', fontsize=10)
a.set_ylabel('deg/min', fontsize=9); a.set_xlabel('time since cruise start (s)', fontsize=8.5)
a.grid(alpha=0.3); a.tick_params(labelsize=8)
a = ax[2][2]
for tr, cond, rep in TRIALS:
    d = data[tr]
    fe, ye = d['errE'][crop(d, d['t'])][-1], d['yawErr'][crop(d, d['t'])][-1]
    a.scatter(ye, fe, color=CONDS[cond], marker=['o', 's', '^'][rep-1], s=70,
              edgecolor='k', lw=0.5, zorder=3)
    a.annotate(tr.replace('dsn_', ''), (ye, fe), fontsize=6.5, xytext=(5, 3),
               textcoords='offset points')
a.set_xlabel('final yaw error (deg)', fontsize=8.5)
a.set_ylabel('final cross-track error (m)', fontsize=9)
a.set_title('Final cross-track vs final yaw error', fontsize=10)
a.grid(alpha=0.3)

fig.suptitle('Lateral-drift patterns across all nine dsn_* trials — CRUISE WINDOW ONLY '
             '(pre-arm, arming, climb, stop and landing excluded; each trial re-gauged to its own '
             'cruise start)', fontsize=12, y=0.998)
fig.tight_layout(rect=[0, 0, 1, 0.978])
fig.savefig(f'{OUT}/32_overview_all_trials.png', dpi=120)
plt.close(fig)

# ---------------- numeric summary ----------------
print(f"\n{'trial':16}{'dur':>6}{'x-track':>9}{'along':>9}{'yaw':>8}{'VE mean':>9}"
      f"{'d(rate)/dt EKF3':>17}{'UKF':>8}{'FGO':>8}")
for tr, cond, rep in TRIALS:
    d = data[tr]; c = crop(d, d['t'])
    sl = lambda y: np.polyfit(d['grid'][np.isfinite(y)] / 60, y[np.isfinite(y)], 1)[0]
    print(f"{tr:16}{d['dur']:6.0f}{d['errE'][c][-1]:9.1f}{d['errN'][c][-1]:9.1f}"
          f"{d['yawErr'][c][-1]:8.1f}{d['errVE'][c].mean():9.3f}"
          f"{sl(d['r_ekf3']):17.2f}{sl(d['r_ukf']):8.2f}{sl(d['r_fgo']):8.2f}")
print(f"\n-> {OUT}/32_overview_all_trials.png")
