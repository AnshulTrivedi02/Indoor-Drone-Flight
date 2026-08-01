#!/usr/bin/env python3
"""UKF full state-vs-time diagnostic on dsn_tex_r1 — the same set as the EKF3 one.
The UKF logs its own covariance directly (ENU/Euler), so the consistency check is
direct. Reruns the replay logging state + P-diagonal per predict step and the
flow/range innovations + per-axis test ratios per update. Handles the ~90deg
init-yaw gauge (UKF inits yaw=0; truth heading = psi0) by rotating ground truth
into the UKF frame. Run in venv-evo. Existing bag only; no fixes proposed.
"""
import sys, os, glob, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
np.seterr(divide='ignore', invalid='ignore')      # a few duplicate IMU stamps in the derived gyro-truth
sys.path.insert(0, os.path.expanduser("~/thesis_ws/src/estimators"))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
import ukf_core as U
from measurement_models import h_flow, h_range

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
BAG = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/bag")
OUT = os.path.expanduser("~/thesis_ws/plots")
ts = get_typestore(Stores.ROS2_JAZZY)
mp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(mp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec*1e-9

def q2rpy(w, x, y, z):
    return (math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y)),
            math.asin(max(-1, min(1, 2*(w*y-z*x)))),
            math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z)))

# ---------- read bag ----------
ev = []; gt = []
with Reader(BAG) as r:
    c = {x.topic: x for x in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range",
            "/attitude/angular_rates", "/ground_truth/pose"]
    for con, t, raw in r.messages(connections=[c[k] for k in want if k in c]):
        m = ts.deserialize_cdr(raw, con.msgtype); tt = stamp(m.header)
        if con.topic == "/imu/data_raw":
            ev.append((tt, "imu", (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]),
                                   np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z]))))
        elif con.topic == "/downward_lidar/range":
            ev.append((tt, "rng", float(m.range)))
        elif con.topic == "/optical_flow/measurement":
            ev.append((tt, "flow", (np.array([m.flow_x_rad, m.flow_y_rad]), bool(m.valid), float(m.inlier_ratio))))
        elif con.topic == "/attitude/angular_rates":
            ev.append((tt, "att", np.array([m.vector.x, m.vector.y, m.vector.z])))
        elif con.topic == "/ground_truth/pose":
            q = m.pose.orientation
            gt.append((tt, m.pose.position.x, m.pose.position.y, m.pose.position.z, *q2rpy(q.w, q.x, q.y, q.z)))
ev.sort(key=lambda e: e[0]); gt = np.array(sorted(gt))
_u, _i = np.unique(gt[:, 0], return_index=True); gt = gt[_i]     # dedupe/monotonic timestamps (GT has dupes)

# ---------- init + run (logging) ----------
p = U.make_params(dt=0.0125)
t_imu0 = next(t for t, k, _ in ev if k == "imu")
acc_lvl = [d[0] for t, k, d in ev if k == "imu" and t <= t_imu0 + 0.5]
first_rng = next(d for t, k, d in ev if k == "rng" and p['RNG_MIN'] <= d <= p['RNG_MAX'])
x, P = U.init_state(np.mean(acc_lvl, axis=0), first_rng)
t_init = t_imu0 + 0.5

def scalar_diag(x, P, z, hfun, R_scalar, gate_c):     # recompute innovation + test ratio (matches _update_scalar)
    sig, Wm, Wc = U._sigma_points(x, P, p)
    Z = np.array([hfun(s) for s in sig]); zpred = Wm @ Z; dz = Z - zpred
    S = Wc @ (dz*dz) + R_scalar; nu = z - zpred
    return nu, (nu*nu)/(gate_c*S)

st = []; om = np.zeros(3); t_prev = t_init; t_yaw = t_init
da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
finn = []; rinn = []                                   # flow (t,nux,trx,nuy,try), range (t,nu,tr)
gate_f = (0.01*p['FLOW_GATE'])**2; gate_r = (0.01*p['RNG_GATE'])**2
for t, kind, d in ev:
    if t < t_init:
        if kind == "att": om = d
        continue
    if kind == "att":
        om = d
    elif kind == "imu":
        dt_i = t - t_prev; t_prev = t
        if dt_i <= 0 or dt_i > 0.2: continue
        da += d[1]*dt_i; dv += d[0]*dt_i; acc_dt += dt_i
        if acc_dt >= p['dt']:
            x, P = U.predict(x, P, da, dv, p)
            if t - t_yaw >= p['YAW_DT']:
                x, P, _ = U.update_yaw_pseudo(x, P, p); t_yaw = t
            st.append((t, *x, *np.diag(P)))
            da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
    elif kind == "rng":
        if p['RNG_MIN'] <= d <= p['RNG_MAX']:
            nu, tr = scalar_diag(x, P, d, lambda s: h_range(s)[0], p['RNG_M_NSE']**2, gate_r)
            rinn.append((t, nu, tr))
        x, P, _ = U.update_range(x, P, d, p)
    elif kind == "flow":
        fxy, valid, inlier = d
        if valid and inlier > 0 and abs(fxy[0]) < p['FLOW_MAX'] and abs(fxy[1]) < p['FLOW_MAX']:
            nx, trx = scalar_diag(x, P, fxy[0], lambda s: h_flow(s, om)[0], p['FLOW_M_NSE']**2, gate_f)
            ny, tryy = scalar_diag(x, P, fxy[1], lambda s: h_flow(s, om)[1], p['FLOW_M_NSE']**2, gate_f)
            finn.append((t, nx, trx, ny, tryy))
        x, P, _ = U.update_flow(x, P, fxy, om, valid, inlier, p)
st = np.array(st); finn = np.array(finn); rinn = np.array(rinn)
T = st[:, 0]; X = st[:, 1:16]; Pd = st[:, 16:31]; t0 = T[0]

# ---------- ground truth in the UKF frame (rotate by init gauge psi0) ----------
psi0 = np.interp(t_init, gt[:, 0], np.unwrap(gt[:, 6]))            # true heading at init
cN = math.cos(-psi0); sN = math.sin(-psi0)
gE0 = np.interp(t_init, gt[:, 0], gt[:, 1]); gN0 = np.interp(t_init, gt[:, 0], gt[:, 2])
def gt_ukf(tq):
    E = np.interp(tq, gt[:, 0], gt[:, 1]) - gE0; N = np.interp(tq, gt[:, 0], gt[:, 2]) - gN0
    Er = cN*E - sN*N; Nr = sN*E + cN*N                            # rotate into UKF frame
    Uu = np.interp(tq, gt[:, 0], gt[:, 3])
    return Er, Nr, Uu
gvE = np.gradient(gt[:, 1], gt[:, 0]); gvN = np.gradient(gt[:, 2], gt[:, 0]); gvU = np.gradient(gt[:, 3], gt[:, 0])
def gt_vel_ukf(tq):
    E = np.interp(tq, gt[:, 0], gvE); N = np.interp(tq, gt[:, 0], gvN)
    return cN*E - sN*N, sN*E + cN*N, np.interp(tq, gt[:, 0], gvU)
def gt_att_ukf(tq):
    return (np.interp(tq, gt[:, 0], np.unwrap(gt[:, 4])), np.interp(tq, gt[:, 0], np.unwrap(gt[:, 5])),
            (np.interp(tq, gt[:, 0], np.unwrap(gt[:, 6])) - psi0))
# true gyro bias = measured gyro - true body rate (~euler rate); use IMU gyro from ev
imu_t = np.array([t for t, k, _ in ev if k == "imu"]); imu_g = np.array([d[1] for t, k, d in ev if k == "imu"])
trueRate = np.c_[np.gradient(np.interp(imu_t, gt[:, 0], np.unwrap(gt[:, 4])), imu_t),
                 np.gradient(np.interp(imu_t, gt[:, 0], np.unwrap(gt[:, 5])), imu_t),
                 np.gradient(np.interp(imu_t, gt[:, 0], np.unwrap(gt[:, 6])), imu_t)]
trueGb = np.degrees(imu_g - trueRate)                             # deg/s
sm = lambda a, n=201: np.convolve(a, np.ones(n)/n, mode='same')

DT = p['dt']; tr = lambda t: t - t0
# GT arrays on the state time base
gEs, gNs, gUs = gt_ukf(T); gvEs, gvNs, gvUs = gt_vel_ukf(T); grs, gps, gys = gt_att_ukf(T)
def wrap180(a): return (a+180) % 360 - 180
GT = {
    0: (np.c_[gEs, gNs, gUs], ['Pos E (m)', 'Pos N (m)', 'Pos U (m)']),
    1: (np.c_[gvEs, gvNs, gvUs], ['Vel E (m/s)', 'Vel N (m/s)', 'Vel U (m/s)']),
    2: (np.degrees(np.c_[grs, gps, gys]), ['Roll (deg)', 'Pitch (deg)', 'Yaw (deg)']),
    3: (np.c_[np.interp(T, imu_t, sm(trueGb[:, 0])), np.interp(T, imu_t, sm(trueGb[:, 1])),
              np.interp(T, imu_t, sm(trueGb[:, 2]))], ['Gyro bias X (deg/s)', 'Gyro bias Y', 'Gyro bias Z']),
    4: (np.zeros((len(T), 3)), ['Accel bias X (m/s2)', 'Accel bias Y', 'Accel bias Z']),
}
# estimate arrays (convert bias delta->rate)
E0 = X[:, 0:3]; E1 = X[:, 3:6]; E2 = np.c_[np.degrees(X[:, 6]), np.degrees(X[:, 7]), np.degrees(X[:, 8])]
E3 = np.degrees(X[:, 9:12]/DT); E4 = X[:, 12:15]/DT
ESdiag = {0: np.sqrt(Pd[:, 0:3]), 1: np.sqrt(Pd[:, 3:6]),
          2: np.degrees(np.sqrt(Pd[:, 6:9])), 3: np.degrees(np.sqrt(Pd[:, 9:12])/DT), 4: np.sqrt(Pd[:, 12:15])/DT}
EST = {0: E0, 1: E1, 2: E2, 3: E3, 4: E4}

# =============== FIGURE 1: states ===============
fig, ax = plt.subplots(5, 3, figsize=(16, 16), sharex=True)
for r in range(5):
    yg, labs = GT[r]; ye = EST[r]
    for cix in range(3):
        a = ax[r][cix]
        ee = ye[:, cix]; gg = yg[:, cix]
        if r == 2 and cix == 2: ee = wrap180(ee); gg = wrap180(gg)
        a.plot(tr(T), ee, lw=0.8, color='C0', label='UKF')
        a.plot(tr(T), gg, lw=0.9, color='k', ls='--', label='truth (UKF frame)')
        a.set_ylabel(labs[cix]); a.grid(alpha=0.3)
ax[0][0].legend(loc='upper left', fontsize=8)
for cix in range(3): ax[4][cix].set_xlabel('flight time (s)')
fig.suptitle(f'UKF states vs time — {TRIAL}  (est vs GT in UKF frame)', y=0.995)
fig.tight_layout(); fig.savefig(f'{OUT}/ukf_diag_1_states.png', dpi=110); plt.close(fig)

# =============== FIGURE 2: consistency ===============
fig, ax = plt.subplots(5, 3, figsize=(16, 16), sharex=True)
breaches = []
for r in range(5):
    yg, labs = GT[r]; ye = EST[r]; sg = ESdiag[r]
    for cix in range(3):
        a = ax[r][cix]
        e = ye[:, cix] - yg[:, cix]
        if r == 2: e = wrap180(e)
        s3 = 3*sg[:, cix]
        a.fill_between(tr(T), -s3, s3, color='C1', alpha=0.25, label='+/-3sigma')
        a.plot(tr(T), e, lw=0.7, color='C0', label='error')
        out = np.abs(e) > s3
        if out.any():
            a.plot(tr(T)[out], e[out], '.', ms=1.5, color='red')
            tb = tr(T)[out]; breaches.append((f'{labs[cix]}', 100*out.mean(), tb.min(), tb.max(), r >= 3))
            a.set_title(f'{100*out.mean():.0f}% outside', fontsize=8, color='red')
        a.set_ylabel('err '+labs[cix]); a.grid(alpha=0.3); a.axhline(0, color='k', lw=0.4)
ax[0][0].legend(loc='upper left', fontsize=8)
for cix in range(3): ax[4][cix].set_xlabel('flight time (s)')
fig.suptitle(f'UKF consistency: error vs own +/-3sigma — {TRIAL}  (red=overconfident; truth in UKF frame)', y=0.995)
fig.tight_layout(); fig.savefig(f'{OUT}/ukf_diag_2_consistency.png', dpi=110); plt.close(fig)

# =============== FIGURE 3: innovations + test ratios ===============
fig, ax = plt.subplots(2, 3, figsize=(16, 8), sharex=True)
ax[0][0].plot(tr(finn[:, 0]), finn[:, 1], lw=0.6, color='C3'); ax[0][0].set_title('flow X (lateral) innovation (rad/s)')
ax[0][1].plot(tr(finn[:, 0]), finn[:, 3], lw=0.6, color='C0'); ax[0][1].set_title('flow Y (forward) innovation (rad/s)')
ax[0][2].plot(tr(rinn[:, 0]), rinn[:, 1], lw=0.6, color='C2'); ax[0][2].set_title('range innovation (m)')
ax[1][0].plot(tr(finn[:, 0]), finn[:, 2], lw=0.6, color='C3', label='X'); ax[1][0].plot(tr(finn[:, 0]), finn[:, 4], lw=0.6, color='C0', label='Y')
ax[1][0].axhline(1.0, color='k', ls='--', lw=0.8); ax[1][0].set_title('flow test ratio per axis (reject >1)'); ax[1][0].legend(fontsize=8); ax[1][0].set_ylim(0, 3)
ax[1][1].plot(tr(rinn[:, 0]), rinn[:, 2], lw=0.6, color='C2'); ax[1][1].axhline(1.0, color='k', ls='--', lw=0.8); ax[1][1].set_title('range test ratio (reject >1)')
ax[1][2].axis('off')
for a in ax.flat: a.grid(alpha=0.3); a.set_xlabel('flight time (s)')
fig.suptitle(f'UKF innovations & per-axis test ratios — {TRIAL}', y=0.995)
fig.tight_layout(); fig.savefig(f'{OUT}/ukf_diag_3_innovations.png', dpi=110); plt.close(fig)

# ---------- report ----------
print(f"=== UKF consistency — states outside own +/-3sigma ({TRIAL}) ===")
for lab, frac, tmn, tmx, derived in sorted(breaches, key=lambda z: -z[1]):
    tag = "  [truth DERIVED/assumed, low-confidence]" if derived else ""
    print(f"  {lab:20} {frac:5.1f}% outside, t=[{tmn:.0f},{tmx:.0f}]s{tag}")
print(f"init-yaw gauge psi0 = {math.degrees(psi0):.1f} deg (GT rotated into UKF frame). "
      "pos/vel/att truth clean; gyro-bias truth derived; accel-bias truth = 0.")
print("saved ukf_diag_1..3 .png")
