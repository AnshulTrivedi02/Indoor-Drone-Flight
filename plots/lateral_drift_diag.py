#!/usr/bin/env python3
"""Lateral-drift diagnostic — one state per figure, EKF3 (XKF1) vs SIM truth.

Companion to ekf3_state_diagnostic.py, which packs everything into 5x3 grids.
This writes each quantity to its own PNG so individual states can be read
closely. Existing trial data only, read-only, no interpretation baked in.

Usage (venv-ardupilot):
    python3 plots/lateral_drift_diag.py [trial]      # default dsn_tex_r1

Output: plots/lateral_diag/<trial>/NN_<name>.png  + a printed summary table.

Frames: XKF1 is NED (North=along-corridor, East=cross-track). SIM truth is
converted to the same NED origin. Both position series are re-referenced to
the sample where flow aiding engages (EKF position leaves exactly 0), because
before that point EKF3 holds position at 0 by design (const_pos_mode).
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
OUT = os.path.expanduser(f"~/thesis_ws/plots/lateral_diag/{TRIAL}")
DT = 0.0125                      # EKF3 predict dt (delta <-> rate for bias sigmas)
os.makedirs(OUT, exist_ok=True)

EST, TRU, ERR = "#1f77b4", "#000000", "#d62728"


def wrap180(a):
    return (a + 180) % 360 - 180


# ---------------- parse ----------------
m = mavutil.mavlink_connection(BIN)
K = {t: [] for t in ['XKF1', 'XKF2', 'XKF4', 'XKF5', 'XKV1', 'XKV2', 'SIM', 'IMU', 'ATT']}
while True:
    x = m.recv_match(type=list(K))
    if x is None:
        break
    T = x.get_type()
    if T.startswith('XK') and getattr(x, 'C', 0) != 0:
        continue
    if T == 'IMU' and getattr(x, 'I', 0) != 0:
        continue
    K[T].append(x)


def col(msgs, *f):
    return np.array([[getattr(x, k) for k in f] for x in msgs], float)


t1 = col(K['XKF1'], 'TimeUS')[:, 0] / 1e6
xk1 = col(K['XKF1'], 'Roll', 'Pitch', 'Yaw', 'VN', 'VE', 'VD', 'PN', 'PE', 'PD', 'GX', 'GY', 'GZ')
t4 = col(K['XKF4'], 'TimeUS')[:, 0] / 1e6
SS = col(K['XKF4'], 'SS')[:, 0]
t5 = col(K['XKF5'], 'TimeUS')[:, 0] / 1e6
xk5 = col(K['XKF5'], 'FIX', 'FIY', 'NI', 'RI')
tv1 = col(K['XKV1'], 'TimeUS')[:, 0] / 1e6
v1 = col(K['XKV1'], *[f'V{i:02d}' for i in range(0, 12)])
ts = col(K['SIM'], 'TimeUS')[:, 0] / 1e6
sim = col(K['SIM'], 'Roll', 'Pitch', 'Yaw', 'Lat', 'Lng', 'Alt')
ti = col(K['IMU'], 'TimeUS')[:, 0] / 1e6
imu = col(K['IMU'], 'GyrX', 'GyrY', 'GyrZ')

# ---------------- ground truth in NED ----------------
lat, lng = sim[:, 3].copy(), sim[:, 4].copy()
if np.abs(lat).max() > 1000:
    lat /= 1e7
    lng /= 1e7
R = 6378137.0
gN = np.radians(lat - lat[0]) * R
gE = np.radians(lng - lng[0]) * R * math.cos(math.radians(lat.mean()))
gD = -(sim[:, 5] - sim[5, 5])
gVN, gVE = np.gradient(gN, ts), np.gradient(gE, ts)
gRoll, gPitch = sim[:, 0], sim[:, 1]
gYaw = np.degrees(np.unwrap(np.radians(sim[:, 2])))

# on the XKF1 time base
T = t1 - t1[0]
gN_i, gE_i = np.interp(t1, ts, gN), np.interp(t1, ts, gE)
gVN_i, gVE_i = np.interp(t1, ts, gVN), np.interp(t1, ts, gVE)
gYaw_i = np.interp(t1, ts, gYaw)
gRoll_i, gPitch_i = np.interp(t1, ts, gRoll), np.interp(t1, ts, gPitch)

# aiding-engage index: EKF position first leaves exactly 0 (const_pos_mode ends)
i0 = int(np.argmax((np.abs(xk1[:, 6]) + np.abs(xk1[:, 7])) > 0.05))
t_aid = T[i0]

# gauge-fixed at aiding engage
PN = xk1[:, 6] - xk1[i0, 6]
PE = xk1[:, 7] - xk1[i0, 7]
tN = gN_i - gN_i[i0]
tE = gE_i - gE_i[i0]
errN, errE = PN - tN, PE - tE
errVN, errVE = xk1[:, 3] - gVN_i, xk1[:, 4] - gVE_i
yawErr = wrap180(xk1[:, 2] - gYaw_i)
rollErr = wrap180(xk1[:, 0] - gRoll_i)
pitchErr = wrap180(xk1[:, 1] - gPitch_i)

# ---------------- filter's own sigmas ----------------
sig_pos = np.sqrt(v1[:, 7:10])
sig_vel = np.sqrt(v1[:, 4:7])
errRP = np.interp(tv1, t4, col(K['XKF4'], 'errRP')[:, 0])
sig_yaw = np.degrees(np.sqrt(np.clip(4 * v1[:, 0:4].sum(1) - errRP ** 2, 0, None)))
s3 = lambda s: 3 * np.interp(t1, tv1, s)

# ---------------- cross-track attribution ----------------
# Split the east-velocity error into the part a heading error alone would
# produce (true speed rotated by the yaw error) and the remainder. Assumes
# velocity ~ body-forward (small sideslip), which the corridor profile satisfies.
spd = np.hypot(gVN_i, gVE_i)
psi_t, psi_e = np.radians(gYaw_i), np.radians(gYaw_i + yawErr)
vE_head = spd * (np.sin(psi_e) - np.sin(psi_t))     # heading-driven east-vel error
vE_other = errVE - vE_head                          # everything else
cum = lambda y: np.concatenate([[0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(t1))])
ct_head, ct_other = cum(vE_head), cum(vE_other)
ct_head -= ct_head[i0]
ct_other -= ct_other[i0]

# cruise window for means: aiding engaged onwards
cru = T > t_aid


# ---------------- plot helpers ----------------
def fig1(name, title, ylab, series, hlines=(), bands=None, xlab="flight time (s)"):
    """series: list of (x, y, label, colour, lw, ls)"""
    f, a = plt.subplots(figsize=(11, 4.2))
    if bands is not None:
        bx, blo, bhi, blab = bands
        a.fill_between(bx, blo, bhi, color="#ff7f0e", alpha=0.22, lw=0, label=blab)
    for x, y, lab, c, lw, ls in series:
        a.plot(x, y, label=lab, color=c, lw=lw, ls=ls)
    for yv, lab, c in hlines:
        a.axhline(yv, color=c, lw=1.0, ls=':', label=lab)
    a.axvline(t_aid, color='0.4', lw=0.9, ls='--')
    a.annotate('flow aiding engages', (t_aid, 1.0), xycoords=('data', 'axes fraction'),
               xytext=(4, -12), textcoords='offset points', fontsize=7, color='0.35')
    a.set_xlabel(xlab)
    a.set_ylabel(ylab)
    a.set_title(f"{title}  —  {TRIAL}", fontsize=11)
    a.grid(alpha=0.3)
    a.legend(fontsize=8, loc='best')
    f.tight_layout()
    f.savefig(f"{OUT}/{name}.png", dpi=140)
    plt.close(f)


S = lambda x, y, lab, c="C0", lw=1.0, ls='-': (x, y, lab, c, lw, ls)

# ============ 00 — is the AIRCRAFT drifting, or only the estimate? ============
f, a = plt.subplots(figsize=(11, 4.2))
a.plot(T, tE, color=TRU, lw=1.2, label='true east (cross-track) position')
a.plot(T, PE, color=EST, lw=1.2, label='EKF3 PE (estimated east)')
a.axhline(0, color='0.6', lw=0.8)
a.axvline(t_aid, color='0.4', lw=0.9, ls='--')
a.set_xlabel("flight time (s)")
a.set_ylabel("east position (m)")
a.set_title(f"Physical vs estimated cross-track position — {TRIAL}\n"
            f"(true excursion {tE[cru].min():+.2f} .. {tE[cru].max():+.2f} m; "
            f"estimated {PE[cru].min():+.2f} .. {PE[cru].max():+.2f} m)", fontsize=11)
a.grid(alpha=0.3)
a.legend(fontsize=8)
f.tight_layout()
f.savefig(f"{OUT}/00_physical_vs_estimated_crosstrack.png", dpi=140)
plt.close(f)

# ============ 01 — top-down trajectory ============
f, a = plt.subplots(figsize=(6.5, 8))
a.plot(tE, tN, color=TRU, lw=1.4, label='ground truth')
a.plot(PE, PN, color=EST, lw=1.4, label='EKF3 (XKF1)')
a.plot(tE[i0], tN[i0], 'o', color='0.4', ms=6, label='aiding engages')
a.set_xlabel("east / cross-track (m)")
a.set_ylabel("north / along-corridor (m)")
a.set_title(f"Top-down trajectory — {TRIAL}", fontsize=11)
a.grid(alpha=0.3)
a.legend(fontsize=8)
a.set_aspect('equal', adjustable='datalim')
f.tight_layout()
f.savefig(f"{OUT}/01_trajectory_topdown.png", dpi=140)
plt.close(f)

# ============ position ============
fig1("02_crosstrack_error", "Cross-track (east) POSITION ERROR vs time", "PE error (m)",
     [S(T, errE, 'EKF3 − truth', ERR, 1.2)],
     bands=(T, -s3(sig_pos[:, 1]), s3(sig_pos[:, 1]), "filter ±3σ"))

fig1("03_alongtrack_error", "Along-track (north) position error vs time", "PN error (m)",
     [S(T, errN, 'EKF3 − truth', ERR, 1.2)],
     bands=(T, -s3(sig_pos[:, 0]), s3(sig_pos[:, 0]), "filter ±3σ"))

fig1("04_pos_east", "East position — estimate vs truth", "east (m)",
     [S(T, PE, 'EKF3 PE', EST, 1.2), S(T, tE, 'truth', TRU, 1.2, '--')])

fig1("05_pos_north", "North position — estimate vs truth", "north (m)",
     [S(T, PN, 'EKF3 PN', EST, 1.2), S(T, tN, 'truth', TRU, 1.2, '--')])

# ============ velocity ============
fig1("06_vel_east", "East velocity — estimate vs truth", "VE (m/s)",
     [S(T, xk1[:, 4], 'EKF3 VE', EST, 0.9), S(T, gVE_i, 'truth', TRU, 0.9, '--')])

fig1("07_vel_east_error", "East velocity ERROR vs time  (integrates into cross-track)",
     "VE error (m/s)", [S(T, errVE, 'EKF3 − truth', ERR, 0.8)],
     hlines=[(float(errVE[cru].mean()), f"cruise mean {errVE[cru].mean():+.4f} m/s", '0.2')],
     bands=(T, -s3(sig_vel[:, 1]), s3(sig_vel[:, 1]), "filter ±3σ"))

fig1("08_vel_north", "North velocity — estimate vs truth", "VN (m/s)",
     [S(T, xk1[:, 3], 'EKF3 VN', EST, 0.9), S(T, gVN_i, 'truth', TRU, 0.9, '--')])

fig1("09_vel_north_error", "North velocity error vs time", "VN error (m/s)",
     [S(T, errVN, 'EKF3 − truth', ERR, 0.8)],
     hlines=[(float(errVN[cru].mean()), f"cruise mean {errVN[cru].mean():+.4f} m/s", '0.2')],
     bands=(T, -s3(sig_vel[:, 0]), s3(sig_vel[:, 0]), "filter ±3σ"))

# ============ attitude ============
fig1("10_yaw", "Yaw — estimate vs truth (unwrapped)", "yaw (deg)",
     [S(T, np.degrees(np.unwrap(np.radians(xk1[:, 2]))), 'EKF3 yaw', EST, 1.2),
      S(T, gYaw_i, 'truth', TRU, 1.2, '--')])

fit = np.polyfit(T[cru], yawErr[cru], 1)
fig1("11_yaw_error", f"Yaw ERROR vs time  (linear fit {fit[0]*60:+.2f} deg/min)",
     "yaw error (deg)",
     [S(T, yawErr, 'EKF3 − truth', ERR, 1.2),
      S(T[cru], np.polyval(fit, T[cru]), 'linear fit', '0.2', 1.0, '--')],
     bands=(T, -s3(sig_yaw), s3(sig_yaw), "filter ±3σ"))

fig1("12_roll", "Roll — estimate vs truth", "roll (deg)",
     [S(T, xk1[:, 0], 'EKF3 roll', EST, 0.7), S(T, gRoll_i, 'truth', TRU, 0.7, '--')],
     hlines=[(float(gRoll_i[cru].mean()), f"true cruise mean {gRoll_i[cru].mean():+.3f}°", '0.2')])

fig1("13_roll_error", "Roll error vs time  (a bias here tilts the flow measurement)",
     "roll error (deg)", [S(T, rollErr, 'EKF3 − truth', ERR, 0.7)],
     hlines=[(float(rollErr[cru].mean()), f"cruise mean {rollErr[cru].mean():+.4f}°", '0.2')])

fig1("14_pitch", "Pitch — estimate vs truth", "pitch (deg)",
     [S(T, xk1[:, 1], 'EKF3 pitch', EST, 0.7), S(T, gPitch_i, 'truth', TRU, 0.7, '--')],
     hlines=[(float(gPitch_i[cru].mean()), f"true cruise mean {gPitch_i[cru].mean():+.3f}°", '0.2')])

fig1("15_pitch_error", "Pitch error vs time", "pitch error (deg)",
     [S(T, pitchErr, 'EKF3 − truth', ERR, 0.7)],
     hlines=[(float(pitchErr[cru].mean()), f"cruise mean {pitchErr[cru].mean():+.4f}°", '0.2')])

# ============ biases ============
for j, (ax_name, lab) in enumerate([('16_gyro_bias_x', 'X (roll)'), ('17_gyro_bias_y', 'Y (pitch)'),
                                    ('18_gyro_bias_z', 'Z (yaw)')]):
    fig1(ax_name, f"EKF3 gyro bias {lab}", "bias (deg/s)",
         [S(T, xk1[:, 9 + j], f'GB{lab[0]}', EST, 1.0)],
         hlines=[(0, 'zero', '0.6')])

# ============ flow innovations ============
fig1("19_flow_innovation_x", "Flow X (LATERAL) innovation", "innovation (rad/s)",
     [S(t5 - t1[0], xk5[:, 0] / 1000, 'FIX', ERR, 0.6)], hlines=[(0, '', '0.6')])

fig1("20_flow_innovation_y", "Flow Y (forward) innovation", "innovation (rad/s)",
     [S(t5 - t1[0], xk5[:, 1] / 1000, 'FIY', EST, 0.6)], hlines=[(0, '', '0.6')])

fig1("21_flow_test_ratio", "Flow normalised innovation test ratio (reject at 100)", "NI",
     [S(t5 - t1[0], xk5[:, 2], 'NI', '0.2', 0.6)], hlines=[(100, 'reject threshold', ERR)])

# ============ cross-track attribution ============
f, a = plt.subplots(figsize=(11, 4.6))
a.plot(T, errE, color=ERR, lw=1.4, label='actual cross-track error')
a.plot(T, ct_head, color='#2ca02c', lw=1.2, label='∫ heading-driven component')
a.plot(T, ct_other, color=EST, lw=1.2, label='∫ remaining (lateral-velocity) component')
a.plot(T, ct_head + ct_other, color='0.45', lw=1.0, ls=':',
       label='∫ VE error (closure check vs actual)')
a.axvline(t_aid, color='0.4', lw=0.9, ls='--')
a.axhline(0, color='0.6', lw=0.8)
a.set_xlabel("flight time (s)")
a.set_ylabel("cross-track (m)")
a.set_title(f"Cross-track error attribution — {TRIAL}\n"
            f"east-velocity error split into (true speed × yaw error) and the remainder",
            fontsize=11)
a.grid(alpha=0.3)
a.legend(fontsize=8)
f.tight_layout()
f.savefig(f"{OUT}/22_crosstrack_attribution.png", dpi=140)
plt.close(f)

# ============ flow residual (needs the npz from diag_flow_residual.py) ============
if os.path.exists(NPZ):
    z = np.load(NPZ)
    mask = z['t'] > t_aid
    fig1("23_lateral_flow_residual", "Lateral flow residual: h_flow(GT) − measured",
         "residual (rad/s)", [S(z['t'], z['resid_x'], 'lateral (x)', ERR, 0.5)],
         hlines=[(float(z['resid_x'][mask].mean()),
                  f"cruise mean {z['resid_x'][mask].mean():+.4f}", '0.2')])
    fig1("24_forward_flow_residual", "Forward flow residual: h_flow(GT) − measured",
         "residual (rad/s)", [S(z['t'], z['resid_y'], 'forward (y)', EST, 0.5)],
         hlines=[(float(z['resid_y'][mask].mean()),
                  f"cruise mean {z['resid_y'][mask].mean():+.4f}", '0.2')])
    f, a = plt.subplots(figsize=(7, 5.5))
    rr = np.degrees(z['rollspeed'])
    a.scatter(rr, z['resid_x'], s=2, alpha=0.18, color=ERR)
    p = np.polyfit(rr, z['resid_x'], 1)
    xs = np.linspace(rr.min(), rr.max(), 50)
    a.plot(xs, np.polyval(p, xs), color='0.1', lw=1.4,
           label=f"fit {p[0]:+.4f}·rollrate {p[1]:+.4f}\ncorr {np.corrcoef(rr, z['resid_x'])[0,1]:+.3f}")
    a.set_xlabel("roll rate (deg/s)")
    a.set_ylabel("lateral flow residual (rad/s)")
    a.set_title(f"Lateral flow residual vs roll RATE — {TRIAL}", fontsize=11)
    a.grid(alpha=0.3)
    a.legend(fontsize=8)
    f.tight_layout()
    f.savefig(f"{OUT}/25_lateral_residual_vs_rollrate.png", dpi=140)
    plt.close(f)
else:
    print(f"[skip 23-25] no {NPZ} — run diag_flow_residual.py {TRIAL} in venv-evo first")

# ---------------- summary ----------------
pct = lambda e, s: 100 * np.mean(np.abs(e[cru]) > s3(s)[cru])
print(f"\n=== lateral-drift summary — {TRIAL} ===")
print(f"flight length            {T[-1]:.1f} s;  flow aiding engages at {t_aid:.1f} s")
print(f"TRUE cross-track (east) excursion   {tE[cru].min():+8.2f} .. {tE[cru].max():+8.2f} m"
      f"   (final {tE[-1]:+.2f} m)")
print(f"EKF3 estimated east position        {PE[cru].min():+8.2f} .. {PE[cru].max():+8.2f} m"
      f"   (final {PE[-1]:+.2f} m)")
print(f"cross-track ERROR (est − truth)     final {errE[-1]:+8.2f} m,  max |{np.abs(errE).max():.2f}| m")
print(f"along-track error                   final {errN[-1]:+8.2f} m")
print(f"  attribution at end:  heading-driven {ct_head[-1]:+.2f} m | remainder {ct_other[-1]:+.2f} m")
print(f"yaw error   final {yawErr[-1]:+.2f} deg,  linear drift {fit[0]*60:+.2f} deg/min")
print(f"cruise means:  VE err {errVE[cru].mean():+.4f} m/s | VN err {errVN[cru].mean():+.4f} m/s"
      f" | roll err {rollErr[cru].mean():+.4f} deg | true roll {gRoll_i[cru].mean():+.4f} deg")
print(f"outside own ±3σ (cruise):  PE {pct(errE, sig_pos[:,1]):.0f}%  PN {pct(errN, sig_pos[:,0]):.0f}%"
      f"  VE {pct(errVE, sig_vel[:,1]):.0f}%  yaw {pct(yawErr, sig_yaw):.0f}%")
nrej = np.mean(xk5[:, 2] >= 100) * 100
print(f"flow innovations rejected (NI≥100): {nrej:.1f}% of {len(xk5)} samples")
print(f"\nfigures -> {OUT}/")
