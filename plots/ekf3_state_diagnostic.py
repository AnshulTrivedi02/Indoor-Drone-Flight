#!/usr/bin/env python3
"""EKF3 full state-vs-time diagnostic on one trial (dsn_tex_r1 to start).
Existing data only. Run in venv-ardupilot (pymavlink+matplotlib); consumes the
flow-residual .npz produced by diag_flow_residual.py (venv-evo).

Figures (plots/ekf3_diag_*.png):
  1 states     — every state vs time, GT overlaid where available
  2 consistency— error (est-truth) with the filter's own +/-3sigma from XKV1/2
  3 innovations— flow X/Y and range innovations + normalised test ratios
  4 flowresid  — measured flow - h_flow(GT vel, GT att); lateral vs forward
  5 tilt       — roll/pitch error + gyro bias xy vs the lateral flow residual
Prints which states leave their own +/-3sigma and when. No fixes proposed.
"""
import sys, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
BIN = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/ardupilot.bin")
NPZ = os.path.expanduser(f"~/thesis_ws/plots/_diag_{TRIAL}_flowresid.npz")
OUT = os.path.expanduser("~/thesis_ws/plots")
DT = 0.0125  # EKF3 predict dt (delta<->rate for bias variances)

# ---------- parse ----------
m = mavutil.mavlink_connection(BIN)
K = {t: [] for t in ['XKF1', 'XKF2', 'XKF3', 'XKF4', 'XKF5', 'XKV1', 'XKV2', 'SIM', 'IMU']}
while True:
    x = m.recv_match(type=list(K))
    if x is None:
        break
    if x.get_type() in ('XKF1', 'XKF2', 'XKF3', 'XKF4', 'XKF5', 'XKV1', 'XKV2') and getattr(x, 'C', 0) != 0:
        continue
    if x.get_type() == 'IMU' and getattr(x, 'I', 0) != 0:
        continue
    K[x.get_type()].append(x)

def col(msgs, *f):
    return np.array([[getattr(x, k) for k in f] for x in msgs], float)

t1 = col(K['XKF1'], 'TimeUS')[:, 0]/1e6
t0 = t1[0]
xk1 = col(K['XKF1'], 'Roll', 'Pitch', 'Yaw', 'VN', 'VE', 'VD', 'PN', 'PE', 'PD', 'GX', 'GY', 'GZ')
t2 = col(K['XKF2'], 'TimeUS')[:, 0]/1e6; xk2 = col(K['XKF2'], 'AX', 'AY', 'AZ')
tv1 = col(K['XKV1'], 'TimeUS')[:, 0]/1e6; v1 = col(K['XKV1'], *[f'V{i:02d}' for i in range(0, 12)])
tv2 = col(K['XKV2'], 'TimeUS')[:, 0]/1e6; v2 = col(K['XKV2'], *[f'V{i:02d}' for i in range(12, 24)])
t4 = col(K['XKF4'], 'TimeUS')[:, 0]/1e6; errRP = col(K['XKF4'], 'errRP')[:, 0]; SH = col(K['XKF4'], 'SH')[:, 0]
t5 = col(K['XKF5'], 'TimeUS')[:, 0]/1e6; xk5 = col(K['XKF5'], 'FIX', 'FIY', 'NI', 'RI')
ts = col(K['SIM'], 'TimeUS')[:, 0]/1e6; sim = col(K['SIM'], 'Roll', 'Pitch', 'Yaw', 'Lat', 'Lng', 'Alt')
ti = col(K['IMU'], 'TimeUS')[:, 0]/1e6; imu = col(K['IMU'], 'GyrX', 'GyrY', 'GyrZ')

# ---------- ground truth (SIM) in NED ----------
lat = sim[:, 3].copy(); lng = sim[:, 4].copy()
if np.abs(lat).max() > 1000:
    lat /= 1e7; lng /= 1e7
R = 6378137.0; la0 = math.radians(lat.mean())
gN = np.radians(lat-lat[0])*R; gE = np.radians(lng-lng[0])*R*math.cos(la0); gD = -(sim[:, 5]-sim[5, 5])
def d(a, t): return np.gradient(a, t)
gVN, gVE, gVD = d(gN, ts), d(gE, ts), d(gD, ts)
gRoll, gPitch, gYaw = sim[:, 0], sim[:, 1], np.unwrap(np.radians(sim[:, 2]))*180/np.pi
# true gyro bias = measured gyro - true body rate (~euler rate at small tilt); IMU rad/s
gr = np.radians([np.interp(ti, ts, np.unwrap(np.radians(sim[:, i]))) for i in range(3)]).T  # true euler (rad) at IMU times... unused directly
trueRate = np.c_[d(np.interp(ti, ts, np.unwrap(np.radians(sim[:, 0]))), ti),
                 d(np.interp(ti, ts, np.unwrap(np.radians(sim[:, 1]))), ti),
                 d(np.interp(ti, ts, np.unwrap(np.radians(sim[:, 2]))), ti)]
trueGbias = np.degrees(imu - trueRate)  # deg/s, per IMU sample (noisy — smooth for plotting)
def sm(a, n=201): return np.convolve(a, np.ones(n)/n, mode='same')
trueGbias_s = np.c_[sm(trueGbias[:, 0]), sm(trueGbias[:, 1]), sm(trueGbias[:, 2])]

# ---------- sigmas (per-axis) ----------
# position 7-9, velocity 4-6 from XKV1 (state units, m and m/s)
sig_pos = np.sqrt(v1[:, 7:10]); sig_vel = np.sqrt(v1[:, 4:7])
# attitude: roll/pitch from errRP (tilt 1sig) split /sqrt2; yaw from 4*qtrace - errRP^2
qtr = v1[:, 0:4].sum(1)
errRP_i = np.interp(tv1, t4, errRP)
sig_roll = sig_pitch = np.degrees(errRP_i/math.sqrt(2))
sig_yaw = np.degrees(np.sqrt(np.clip(4*qtr - errRP_i**2, 0, None)))
# gyro bias 10,11 (XKV1) + 12 (XKV2) -> rate deg/s via /dt
sig_gb = np.degrees(np.c_[np.sqrt(v1[:, 10]), np.sqrt(v1[:, 11]), np.sqrt(np.interp(tv1, tv2, v2[:, 0]))]/DT)
# accel bias 13,14,15 (XKV2) -> rate m/s^2 via /dt
sig_ab = np.sqrt(v2[:, 1:4])/DT

# ---------- helper ----------
labels = [['Pos N (m)', 'Pos E (m)', 'Pos D (m)'], ['Vel N (m/s)', 'Vel E (m/s)', 'Vel D (m/s)'],
          ['Roll (deg)', 'Pitch (deg)', 'Yaw (deg)'], ['Gyro bias X (deg/s)', 'Gyro bias Y', 'Gyro bias Z'],
          ['Accel bias X (m/s2)', 'Accel bias Y', 'Accel bias Z']]

def tr(t): return t - t0

# =============== FIGURE 1: states vs time ===============
fig, ax = plt.subplots(5, 3, figsize=(16, 16), sharex=True)
est = [ (t1, xk1[:, 6:9]),        # pos NED
        (t1, xk1[:, 3:6]),        # vel NED
        (t1, xk1[:, 0:3]),        # att rpy
        (t1, xk1[:, 9:12]),       # gyro bias
        (t2, xk2[:, 0:3]) ]       # accel bias
gt = [ (ts, np.c_[gN, gE, gD]), (ts, np.c_[gVN, gVE, gVD]), (ts, np.c_[gRoll, gPitch, gYaw]),
       (ti, trueGbias_s), (None, None) ]
for r in range(5):
    te, ye = est[r]; tg, yg = gt[r]
    for cix in range(3):
        a = ax[r][cix]
        yee = ye[:, cix]; ygg = None if tg is None else yg[:, cix]
        if r == 2 and cix == 2:                         # yaw: wrap to +/-180 for display
            yee = (yee + 180) % 360 - 180
            if ygg is not None: ygg = (ygg + 180) % 360 - 180
        a.plot(tr(te), yee, lw=0.8, color='C0', label='EKF3')
        if tg is not None:
            a.plot(tr(tg), ygg, lw=0.9, color='k', ls='--', label='truth')
        a.set_ylabel(labels[r][cix]); a.grid(alpha=0.3)
ax[0][0].legend(loc='upper left', fontsize=8)
for cix in range(3): ax[4][cix].set_xlabel('flight time (s)')
fig.suptitle(f'EKF3 states vs time — {TRIAL}  (est vs ground truth)', y=0.995)
fig.tight_layout(); fig.savefig(f'{OUT}/ekf3_diag_1_states.png', dpi=110); plt.close(fig)

# =============== FIGURE 2: consistency (error +/- 3 sigma) ===============
fig, ax = plt.subplots(5, 3, figsize=(16, 16), sharex=True)
# build error series (est - truth) on the estimate's time base
def err_vs(te, ye, tg, yg):
    return ye - np.interp(te, tg, yg)
breaches = []
rows = [
    ('pos', t1, xk1[:, 6:9], ts, np.c_[gN, gE, gD], tv1, sig_pos, labels[0]),
    ('vel', t1, xk1[:, 3:6], ts, np.c_[gVN, gVE, gVD], tv1, sig_vel, labels[1]),
    ('att', t1, xk1[:, 0:3], ts, np.c_[gRoll, gPitch, gYaw], tv1, np.c_[sig_roll, sig_pitch, sig_yaw], labels[2]),
    ('gbias', t1, xk1[:, 9:12], ti, trueGbias_s, tv1, sig_gb, labels[3]),
    ('abias', t2, xk2[:, 0:3], None, None, tv2, sig_ab, labels[4]),
]
def wrap180(a): return (a + 180) % 360 - 180
for r, (name, te, ye, tg, yg, tsig, sg, labs) in enumerate(rows):
    for cix in range(3):
        a = ax[r][cix]
        if tg is not None:
            e = ye[:, cix] - np.interp(te, tg, yg[:, cix])
            if name == 'att':
                e = wrap180(e)                          # roll/pitch/yaw error wrapped to +/-180
        else:
            e = ye[:, cix] - 0.0                        # accel bias truth = 0 (assumed)
        s3 = 3*np.interp(te, tsig, sg[:, cix])
        a.fill_between(tr(te), -s3, s3, color='C1', alpha=0.25, label='+/-3sigma')
        a.plot(tr(te), e, lw=0.7, color='C0', label='error')
        out = np.abs(e) > s3
        if out.any():
            a.plot(tr(te)[out], e[out], '.', ms=1.5, color='red')
            frac = 100*out.mean()
            tb = tr(te)[out]
            breaches.append((f'{name}:{labs[cix]}', frac, tb.min(), tb.max()))
            a.set_title(f'{100*out.mean():.0f}% outside', fontsize=8, color='red')
        a.set_ylabel('err '+labs[cix]); a.grid(alpha=0.3); a.axhline(0, color='k', lw=0.4)
ax[0][0].legend(loc='upper left', fontsize=8)
for cix in range(3): ax[4][cix].set_xlabel('flight time (s)')
fig.suptitle(f'EKF3 consistency: error vs own +/-3sigma — {TRIAL}  (red = overconfident)', y=0.995)
fig.tight_layout(); fig.savefig(f'{OUT}/ekf3_diag_2_consistency.png', dpi=110); plt.close(fig)

# =============== FIGURE 3: innovations + test ratios ===============
fig, ax = plt.subplots(2, 3, figsize=(16, 8), sharex=True)
ax[0][0].plot(tr(t5), xk5[:, 0]/1000, lw=0.6, color='C3'); ax[0][0].set_title('flow X (lateral) innovation (rad/s)')
ax[0][1].plot(tr(t5), xk5[:, 1]/1000, lw=0.6, color='C0'); ax[0][1].set_title('flow Y (forward) innovation (rad/s)')
ax[0][2].plot(tr(t5), xk5[:, 3], lw=0.6, color='C2'); ax[0][2].set_title('range innovation RI (m)')
ax[1][0].plot(tr(t5), xk5[:, 2], lw=0.6, color='C3'); ax[1][0].axhline(100, color='k', ls='--', lw=0.8)
ax[1][0].set_title('flow test ratio NI (reject >=100, combined X/Y)')
ax[1][1].plot(tr(t4), SH, lw=0.6, color='C2'); ax[1][1].axhline(1.0, color='k', ls='--', lw=0.8)
ax[1][1].set_title('height/range test ratio SH (reject >=1)')
ax[1][2].axis('off')
for a in ax.flat: a.grid(alpha=0.3); a.set_xlabel('flight time (s)')
fig.suptitle(f'EKF3 innovations & normalised test ratios — {TRIAL}', y=0.995)
fig.tight_layout(); fig.savefig(f'{OUT}/ekf3_diag_3_innovations.png', dpi=110); plt.close(fig)

# =============== FIGURE 4 + 5: flow residual & tilt correlation ===============
z = np.load(NPZ)
fig, ax = plt.subplots(2, 2, figsize=(16, 9))
ax[0][0].plot(z['t'], z['resid_x'], lw=0.5, color='C3')
ax[0][0].axhline(z['resid_x'][(z['t'] > 40)].mean(), color='k', lw=1.2, label=f"mean {z['resid_x'][(z['t']>40)].mean():+.4f}")
ax[0][0].set_title('flow X (lateral) residual: h_flow(GT) - measured (rad/s)'); ax[0][0].legend(fontsize=8)
ax[0][1].plot(z['t'], z['resid_y'], lw=0.5, color='C0')
ax[0][1].axhline(z['resid_y'][(z['t'] > 40)].mean(), color='k', lw=1.2, label=f"mean {z['resid_y'][(z['t']>40)].mean():+.4f}")
ax[0][1].set_title('flow Y (forward) residual (rad/s)'); ax[0][1].legend(fontsize=8)
# item 5: EKF3 roll/pitch error + scatter vs lateral residual
attErr_roll = xk1[:, 0] - np.interp(t1, ts, gRoll); attErr_pitch = xk1[:, 1] - np.interp(t1, ts, gPitch)
ax[1][0].plot(tr(t1), attErr_roll, lw=0.6, label='roll err (deg)')
ax[1][0].plot(tr(t1), attErr_pitch, lw=0.6, label='pitch err (deg)')
ax[1][0].plot(tr(t1), xk1[:, 9], lw=0.6, label='gyro bias X (deg/s)')
ax[1][0].plot(tr(t1), xk1[:, 10], lw=0.6, label='gyro bias Y (deg/s)')
ax[1][0].set_title('EKF3 roll/pitch error & gyro bias X/Y (tilt candidates)'); ax[1][0].legend(fontsize=7); ax[1][0].grid(alpha=0.3)
# scatter: roll RATE vs lateral residual (the dominant coupling)
cc_ang = np.corrcoef(np.degrees(z['gt_roll']), z['resid_x'])[0, 1]
cc_rate = np.corrcoef(z['rollspeed'], z['resid_x'])[0, 1]
ax[1][1].scatter(np.degrees(z['rollspeed']), z['resid_x'], s=1, alpha=0.2, color='C3')
ax[1][1].set_xlabel('roll RATE (deg/s)'); ax[1][1].set_ylabel('lateral flow residual (rad/s)')
ax[1][1].set_title(f'lateral residual vs roll RATE (corr={cc_rate:+.3f}; vs roll ANGLE {cc_ang:+.3f})')
ax[1][1].grid(alpha=0.3)
for a in (ax[0][0], ax[0][1]): a.set_xlabel('flight time (s)'); a.grid(alpha=0.3)
fig.suptitle(f'EKF3 flow residual vs GT & tilt correlation — {TRIAL}', y=0.995)
fig.tight_layout(); fig.savefig(f'{OUT}/ekf3_diag_4_flowresid_tilt.png', dpi=110); plt.close(fig)

# ---------- report ----------
print(f"=== EKF3 consistency — states with error outside own +/-3sigma ({TRIAL}) ===")
if not breaches:
    print("  none")
for name, frac, tmin, tmax in sorted(breaches, key=lambda z: -z[1]):
    tag = "  [truth DERIVED, low-confidence]" if 'bias' in name else ""
    print(f"  {name:28} {frac:5.1f}% of samples outside, t=[{tmin:.0f},{tmax:.0f}]s{tag}")
print("NOTE: pos/vel/att truth = SIM (clean). gyro-bias truth = IMU - d(SIM att)/dt (noisy,"
      " differentiation artefact esp. gyro-X); accel-bias truth = 0 assumed.")
print("saved ekf3_diag_1..4 .png")
