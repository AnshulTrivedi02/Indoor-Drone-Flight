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

traj = []                       # (t, pE, pN, pU, roll,pitch,yaw)
omega = np.zeros(3); t_prev = t_init
da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
n_flow_acc = [0, 0]; n_flow_rej = [0, 0]; n_rng_acc = n_rng_rej = 0
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
            traj.append((t, x[0], x[1], x[2], x[6], x[7], x[8]))
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

quats = [euler_to_quat(r, pch, y) for _, _, _, _, r, pch, y in traj]
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

print(f"[run] {len(traj)} predict steps (80 Hz), window t=[{t_u[bi]:.0f},{t_u[bj-1]:.0f}]s")
print(f"[flow] axis-X accept {n_flow_acc[0]}/{n_flow_acc[0]+n_flow_rej[0]}  "
      f"axis-Y accept {n_flow_acc[1]}/{n_flow_acc[1]+n_flow_rej[1]}   "
      f"[range] accept {n_rng_acc}/{n_rng_acc+n_rng_rej}")
print(f"[result] along-track = {along:.1f} m  (true {true_travel:.1f} m)   ATE = {ate:.2f} m")
print(f"[out] {OUTDIR}/ukf_traj.tum")
