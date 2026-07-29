#!/usr/bin/env python3
"""Offline replay harness — THIN wrapper around ukf_core (a live ROS2 node and a
Term-3 HW node would be equally thin wrappers around the same core). Reads a
recorded bag, runs the UKF, writes a TUM trajectory, prints acceptance metrics.

Usage: ukf_replay.py <trial_name>    (reads ~/thesis_data/trials/<trial>/bag)
Ground truth is used ONLY for evaluation, never as a filter input.
"""
import sys, os, glob, math
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg

import ukf_core as U
from measurement_models import R_world_body

TRIAL = sys.argv[1]
BAG = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/bag")
OUTDIR = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/ukf")
os.makedirs(OUTDIR, exist_ok=True)

ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))


def stamp(h):
    return h.stamp.sec + h.stamp.nanosec*1e-9


# ---------- read all events, time-sorted ----------
ev = []          # (t, kind, payload)
gt = []          # (t, e, n, u)   evaluation only
with Reader(BAG) as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range",
            "/attitude/angular_rates", "/ground_truth/pose"]
    for con, t, raw in r.messages(connections=[conns[w] for w in want if w in conns]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        tt = stamp(m.header)
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
            gt.append((tt, m.pose.position.x, m.pose.position.y, m.pose.position.z))
ev.sort(key=lambda e: e[0]); gt.sort(key=lambda e: e[0])
gt = np.array(gt)

# ---------- init: gravity levelling over first 0.5 s + first valid range ----------
p = U.make_params(dt=0.0125)
t_imu0 = next(t for t, k, _ in ev if k == "imu")
acc_lvl = [d[0] for t, k, d in ev if k == "imu" and t <= t_imu0 + 0.5]
first_rng = next(d for t, k, d in ev if k == "rng" and p['RNG_MIN'] <= d <= p['RNG_MAX'])
x, P = U.init_state(np.mean(acc_lvl, axis=0), first_rng)
t_init = t_imu0 + 0.5
print(f"[init] t={t_init:.2f}s  roll0={math.degrees(x[6]):+.2f} pitch0={math.degrees(x[7]):+.2f} deg  "
      f"p_U0={x[2]:.3f} m (range {first_rng:.3f})")

# ---------- run ----------
def euler_to_quat(r, pch, y):
    cr, sr = np.cos(r/2), np.sin(r/2); cp, sp = np.cos(pch/2), np.sin(pch/2); cy, sy = np.cos(y/2), np.sin(y/2)
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy)

traj = []                       # (t, pE, pN, pU, roll,pitch,yaw, bg_z)
omega = np.zeros(3); t_prev = t_init; t_yaw = t_init
da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
n_flow_acc = [0, 0]; n_flow_rej = [0, 0]; n_rng_acc = n_rng_rej = 0
n_yaw_check = n_yaw_fire = 0     # pseudo-yaw: opportunities checked vs actually fused
att_tr = []                      # attitude-cov trace (P[6..8]) at each yaw check, vs ATT_VAR_GATE
for t, kind, d in ev:
    if t < t_init:
        if kind == "att":
            omega = d
        continue
    if kind == "att":
        omega = d
    elif kind == "imu":
        dt_i = t - t_prev; t_prev = t
        if dt_i <= 0 or dt_i > 0.2:
            continue
        da += d[1]*dt_i; dv += d[0]*dt_i; acc_dt += dt_i
        if acc_dt >= p['dt']:
            x, P = U.predict(x, P, da, dv, p)
            if t - t_yaw >= p['YAW_DT']:              # check opportunity ~7 Hz (EKF3's 140 ms)
                att_tr.append((P[6, 6] + P[7, 7], P[8, 8]))  # (tilt, yaw) cov at each check
                x, P, fired = U.update_yaw_pseudo(x, P, p)   # variance-gated fire (MagFusion.cpp:274)
                n_yaw_check += 1; n_yaw_fire += fired
                t_yaw = t
            traj.append((t, x[0], x[1], x[2], x[6], x[7], x[8], x[U.BG_SLICE.start+2]))
            da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
    elif kind == "rng":
        x, P, acc = U.update_range(x, P, d, p)
        n_rng_acc += acc; n_rng_rej += (not acc)
    elif kind == "flow":
        flow_xy, valid, inlier = d
        x, P, (ax, ay) = U.update_flow(x, P, flow_xy, omega, valid, inlier, p)
        for i, a in enumerate((ax, ay)):
            n_flow_acc[i] += a; n_flow_rej[i] += (not a)
traj = np.array(traj)

# ---------- write TUM (UKF + ground truth), ENU ----------
def write_tum(path, T, XYZ, Q):
    with open(path, "w") as f:
        for i in range(len(T)):
            f.write(f"{T[i]:.6f} {XYZ[i,0]:.6f} {XYZ[i,1]:.6f} {XYZ[i,2]:.6f} "
                    f"{Q[i][0]:.6f} {Q[i][1]:.6f} {Q[i][2]:.6f} {Q[i][3]:.6f}\n")

quats = [euler_to_quat(row[4], row[5], row[6]) for row in traj]
write_tum(f"{OUTDIR}/ukf_traj.tum", traj[:, 0], traj[:, 1:4], quats)
qid = [(0, 0, 0, 1)]*len(gt)
write_tum(f"{OUTDIR}/ground_truth.tum", gt[:, 0], gt[:, 1:4], qid)

# ---------- acceptance metrics (apparatus method, like the EKF3 17.76 m) ----------
# true cruise window from ground-truth speed; ATE = RMSE ||UKF-GT|| over it,
# origin gauge-fixed to window start, NO yaw/SE(3) alignment.
t_u = traj[:, 0]
gE = np.interp(t_u, gt[:, 0], gt[:, 1]); gN = np.interp(t_u, gt[:, 0], gt[:, 2])
sp = np.convolve(np.hypot(np.gradient(gE), np.gradient(gN))/np.gradient(t_u), np.ones(25)/25, mode="same")
cr = sp > 0.30
bi = bj = 0; i = 0
while i < len(cr):
    if cr[i]:
        j = i
        while j < len(cr) and cr[j]:
            j += 1
        if j-i > bj-bi:
            bi, bj = i, j
        i = j
    else:
        i += 1
w = slice(bi, bj)
duE = traj[w, 1]-traj[bi, 1]; duN = traj[w, 2]-traj[bi, 2]
dgE = gE[w]-gE[bi]; dgN = gN[w]-gN[bi]
ate = float(np.sqrt(np.mean((duE-dgE)**2 + (duN-dgN)**2)))
along = float(math.hypot(duE[-1], duN[-1]))
true_travel = float(math.hypot(dgE[-1], dgN[-1]))

# yaw drift rate: slope of unwrapped UKF yaw over the cruise window (true heading
# is ~constant along the corridor, so the slope IS the drift). deg/min.
yaw_w = np.unwrap(traj[w, 6])
tt_w = traj[w, 0]
yaw_slope = np.polyfit(tt_w - tt_w[0], yaw_w, 1)[0]        # rad/s
yaw_drift = math.degrees(yaw_slope) * 60.0                # deg/min

# gyro-z bias convergence: state is delta-form (rad per predict step); as a rate
# = delta / dt. Report the cruise-window mean, and as a fraction of the physical
# SIM_DRIFT the raw gyro carries (~8.9 deg/min, measured in the yaw diagnosis).
bgz_rate = np.degrees(traj[w, 7] / p['dt']) * 60.0        # deg/min, per-sample
bgz_mean = float(np.mean(bgz_rate))
PHYS_DRIFT = 8.9                                          # deg/min (raw gyro-z, both bags)
bgz_frac = 100.0 * abs(bgz_mean) / PHYS_DRIFT

print(f"[run] {len(traj)} predict steps (80 Hz), window t=[{t_u[bi]:.0f},{t_u[bj-1]:.0f}]s")
print(f"[flow] axis-X accept {n_flow_acc[0]}/{n_flow_acc[0]+n_flow_rej[0]}  "
      f"axis-Y accept {n_flow_acc[1]}/{n_flow_acc[1]+n_flow_rej[1]}   "
      f"[range] accept {n_rng_acc}/{n_rng_acc+n_rng_rej}")
att_tr = np.array(att_tr)                    # columns: (tilt cov, yaw cov)
tilt_c, yaw_c = att_tr[:, 0], att_tr[:, 1]
print(f"[pseudo-yaw] fired {n_yaw_fire}/{n_yaw_check} checks "
      f"({100.0*n_yaw_fire/max(n_yaw_check,1):.0f}% — variance-gated, was 100%)")
print(f"[att-cov] tilt(P66+P77) median={np.median(tilt_c):.5f}  "
      f"yaw(P88) median={np.median(yaw_c):.4f} rad^2   "
      f"gate={p['ATT_VAR_GATE']} (EKF3 0.01 x4; EKF3 tilt var ~1e-4, yaw-dominated)")
print(f"[yaw] drift rate = {yaw_drift:+.2f} deg/min")
print(f"[gyro-z bias] cruise mean = {bgz_mean:+.2f} deg/min "
      f"({bgz_frac:.0f}% of the ~{PHYS_DRIFT:.1f} deg/min physical drift)")
print(f"[result] along-track = {along:.1f} m  (true {true_travel:.1f} m)   ATE = {ate:.2f} m")
print(f"[out] {OUTDIR}/ukf_traj.tum")

# machine-readable summary for the batch driver (apparatus, cruise-window, gauge-fixed)
cross_track = float((duE - dgE)[-1])         # final east (perpendicular) error vs truth
along_pN = float(duN[-1])                     # UKF north displacement over window
with open(f"{OUTDIR}/metrics.txt", "w") as f:
    f.write(f"along_pN={along_pN:.3f}\ntrue_travel={true_travel:.3f}\n"
            f"cross_track={cross_track:.3f}\nate_apparatus={ate:.3f}\n"
            f"yaw_drift={yaw_drift:.3f}\nbgz_mean={bgz_mean:.3f}\nbgz_pct={bgz_frac:.1f}\n"
            f"yaw_fire={n_yaw_fire}\nyaw_check={n_yaw_check}\n")
