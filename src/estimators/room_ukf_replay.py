#!/usr/bin/env python3
"""Experiment T (and O later): UKF replay in an ABSOLUTE world frame with AprilTag fixes, plus the RTS-smoothed UKF
(hindsight). A thin harness around ukf_core, like ukf_replay.py (which is unchanged; corridor results never use this).

Inputs from the bag: /imu/data_raw, /optical_flow/measurement, /downward_lidar/range, /attitude/angular_rates and
/tags/sent (the fixes the tag bridge SENT to EKF3 in this flight's condition: identical measurements). Ground truth is
read ONLY for the output file used by the scorer.
Pre-registered handling (METHODOLOGY "Experiment T: pre-registration"):
  * same init, IMU gap rule, dejitter, ground-proximity flow rule, predict step and noise as ukf_replay.py;
  * first fix: re-anchor (measurement_models.reanchor_jacobian; as EKF3's position reset + ExtNav yaw alignment):
    P <- diag(J P J^T) with p_E, p_N, yaw variances = the fix noise (cross-covariances zeroed, as the FGO re-anchor);
  * later fixes: ukf_core.update_tag, NO gate, effective EKF3 noise (TAG_SIGMA_POS, TAG_SIGMA_YAW);
  * the zero-innovation pseudo-yaw runs only until the first fix (EKF3 with an ExtNav yaw source fuses its predicted
    yaw only before yaw alignment: AP_NavEKF3_MagFusion.cpp:368-385);
  * RTS: nodes from the re-anchor on; smoothed = ukf_core.rts_smooth.
Output: ~/thesis_data/trials/<trial>/room_ukf/{ukf_live.tum, ukf_rts.tum, ground_truth.tum, stats.json}
Usage: room_ukf_replay.py <trial> [--no-rts]"""
import sys, os, glob, math, json
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
import ukf_core as U
from imu_timing import dejitter_imu, apply_gap_rule
from measurement_models import FlowFrameGyroAverager, GroundProximityFlow, TAG_SIGMA_POS, TAG_SIGMA_YAW, reanchor_jacobian
from measurement_models import GNSS_SIGMA_POS, GNSS_SIGMA_VEL, GNSS_ALIGN_SPEED, GNSS_ALIGN_N

TRIAL = sys.argv[1]; DO_RTS = "--no-rts" not in sys.argv
GNSS = "--gnss" in sys.argv      # experiment O: GNSS fixes from <trial>/gnss.npz; yaw cap kept throughout (EKF3 in O has
#                                  GSF yaw outdoors and no yaw source indoors, where it fuses its predicted yaw)
D = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}"); OUT = f"{D}/room_ukf"; os.makedirs(OUT, exist_ok=True)
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9


def read_events(bag):
    ev, gt = [], []
    with Reader(bag) as r:
        conns = {c.topic: c for c in r.connections}
        want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates",
                "/ground_truth/pose", "/tags/sent"]
        for con, _, raw in r.messages(connections=[conns[w] for w in want if w in conns]):
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
            elif con.topic == "/tags/sent":
                q = m.pose.pose.orientation
                ev.append((tt, "tag", (m.pose.pose.position.x, m.pose.pose.position.y, 2 * math.atan2(q.z, q.w))))
            else:
                q = m.pose.orientation
                gt.append((tt, m.pose.position.x, m.pose.position.y, m.pose.position.z, q.x, q.y, q.z, q.w))
    return ev, np.array(sorted(gt))


def euler_to_quat(r, pch, y):
    cr, sr = np.cos(r/2), np.sin(r/2); cp, sp = np.cos(pch/2), np.sin(pch/2); cy, sy = np.cos(y/2), np.sin(y/2)
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy)


def write_tum(path, T, X):
    with open(path, "w") as f:
        for t, x in zip(T, X):
            q = euler_to_quat(x[6], x[7], x[8])
            f.write(f"{t:.6f} {x[0]:.6f} {x[1]:.6f} {x[2]:.6f} {q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}\n")


ev, gt = read_events(f"{D}/bag")
if GNSS:
    _g = np.load(f"{D}/gnss.npz")
    ev += [(float(t), "gnss", (e, n, ve, vn)) for t, e, n, ve, vn in zip(_g["t"], _g["E"], _g["N"], _g["vE"], _g["vN"])]
TAG_MAX = int(os.environ.get("ROOM_TAG_MAX", "0"))     # DIAGNOSTIC only (never in T results): keep the first N fixes
if TAG_MAX:
    _n = 0; _keep = []
    for e in ev:
        if e[1] == "tag":
            _n += 1
            if _n > TAG_MAX: continue
        _keep.append(e)
    ev = _keep; OUT = OUT + f"_diag_first{TAG_MAX}"; os.makedirs(OUT, exist_ok=True)
ev = apply_gap_rule(ev, TRIAL); ev, dj = dejitter_imu(ev); ev.sort(key=lambda e: e[0])
TARGET_DT = 0.0125; period = dj['period_ms'] / 1e3
DT_STEP = math.ceil(TARGET_DT / period - 1e-9) * period
p = U.make_params(dt=DT_STEP)
t_imu0 = next(t for t, k, _ in ev if k == "imu")
acc_lvl = [d[0] for t, k, d in ev if k == "imu" and t <= t_imu0 + 0.5]
first_rng = next(d for t, k, d in ev if k == "rng" and p['RNG_MIN'] <= d <= p['RNG_MAX'])
x, P = U.init_state(np.mean(acc_lvl, axis=0), first_rng, dt=DT_STEP)
t_init = t_imu0 + 0.5
_gpj = f"{D}/imu_gaps.json"
gp = GroundProximityFlow(json.load(open(_gpj)).get("arm_header_s") if os.path.exists(_gpj) else None)
gyro_avg = FlowFrameGyroAverager(t_init)
omega = np.zeros(3); t_prev = t_init; t_yaw = t_init
da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
anchored = False; t_anchor = None; n_tag = 0; n_yaw_fire = 0; n_fast = 0; n_gnss = 0
node_t, xa, Pa, xp, Pp, Dc = [], [], [], [], [], []      # RTS records (from the re-anchor on)
live_t, live_x = [], []
for t, kind, d in ev:
    if t < t_init:
        if kind == "att":
            omega = d
        continue
    if kind == "att":
        omega = d
    elif kind == "imu":
        gp.on_gyro(t, d[1], x[U.BG_SLICE] / DT_STEP); gyro_avg.push(t, d[1])
        dt_i = t - t_prev; t_prev = t
        if dt_i <= 0 or dt_i > 0.2:
            continue
        da += d[1] * dt_i; dv += d[0] * dt_i; acc_dt += dt_i
        if acc_dt >= TARGET_DT - 1e-9:
            if anchored:
                node_t.append(t); xa.append(x.copy()); Pa.append(P.copy())     # filtered node (before this predict)
                x, P, Dk = U.predict_rts(x, P, da, dv, p, dt=acc_dt)
                xp.append(x.copy()); Pp.append(P.copy()); Dc.append(Dk)
            else:
                x, P = U.predict(x, P, da, dv, p, dt=acc_dt)
            if (not anchored or GNSS) and t - t_yaw >= p['YAW_DT']:
                if True:
                    x, P, fired = U.update_yaw_pseudo(x, P, p); n_yaw_fire += fired; t_yaw = t
            live_t.append(t); live_x.append(x.copy())
            da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
    elif kind == "rng":
        gp.on_range(t, d); x, P, _ = U.update_range(x, P, d, p)
    elif kind == "flow":
        flow_xy, valid, inlier = d
        om = gyro_avg.average(t, omega)
        if valid and inlier > 0:
            flow_xy = gp.replace(flow_xy, om, x[6], x[7])
        x, P, _ = U.update_flow(x, P, flow_xy, om, valid, inlier, p)
    elif kind == "gnss":
        e_, n_, ve_, vn_ = d
        if not anchored:
            n_fast = n_fast + 1 if math.hypot(ve_, vn_) > GNSS_ALIGN_SPEED else 0
            if n_fast >= GNSS_ALIGN_N:
                spd = math.hypot(ve_, vn_)
                x, J = reanchor_jacobian(x, (e_, n_), math.atan2(vn_, ve_))
                P = np.diag(np.diag(J @ P @ J.T)); P[0, 0] = P[1, 1] = GNSS_SIGMA_POS ** 2
                P[8, 8] = math.asin(min(1.0, GNSS_SIGMA_VEL / spd)) ** 2
                x[3], x[4] = ve_, vn_; P[3, 3] = P[4, 4] = GNSS_SIGMA_VEL ** 2
                anchored = True; t_anchor = t
        else:
            x, P = U.update_gnss(x, P, d, GNSS_SIGMA_POS, GNSS_SIGMA_VEL, p); n_gnss += 1
    elif kind == "tag":
        pE, pN, yaw = d
        if not anchored:
            x, J = reanchor_jacobian(x, (pE, pN), yaw)
            P = np.diag(np.diag(J @ P @ J.T)); P[0, 0] = P[1, 1] = TAG_SIGMA_POS ** 2; P[8, 8] = TAG_SIGMA_YAW ** 2
            anchored = True; t_anchor = t
        else:
            x, P = U.update_tag(x, P, (pE, pN, yaw), TAG_SIGMA_POS, TAG_SIGMA_YAW, p)
        n_tag += 1
# live track: the state after each predict step, with the updates between steps applied at the next record (causal)
live_x = np.array(live_x); live_t = np.array(live_t)
keep = live_t >= (t_anchor if t_anchor is not None else np.inf)
write_tum(f"{OUT}/ukf_live.tum", live_t[keep], live_x[keep])
stats = {"t_anchor": t_anchor, "n_tag_fused": n_tag, "n_gnss_fused": n_gnss, "mode": "gnss" if GNSS else "tags", "pseudo_yaw_fired_before_anchor": int(n_yaw_fire),
         "dt_step_ms": 1e3 * DT_STEP, "tag_sigma_pos": TAG_SIGMA_POS, "tag_sigma_yaw_deg": math.degrees(TAG_SIGMA_YAW)}
if DO_RTS and len(node_t) > 2:
    # node i: filtered xa[i+1] (posterior after the updates following predict i), prediction xp[i] from xa[i]
    XA = np.array(xa[1:] + [x]); PA = np.array(Pa[1:] + [P]); XP = np.array(xp); PP = np.array(Pp); DD = np.array(Dc)
    # node i filtered = XA[i]; the prediction FROM node i to node i+1 is XP[i+1] with cross-cov DD[i+1]
    xs, Ps = U.rts_smooth(XA, PA, XP, PP, DD)
    write_tum(f"{OUT}/ukf_rts.tum", np.array(node_t), xs)
    np.savez_compressed(f"{OUT}/rts_cov.npz", t=np.array(node_t), Pxy_filt=PA[:, :2, :2], Pxy_smooth=Ps[:, :2, :2])
    stats["rts_nodes"] = int(len(xs))
with open(f"{OUT}/ground_truth.tum", "w") as f:
    for g in gt:
        f.write(f"{g[0]:.6f} {g[1]:.6f} {g[2]:.6f} {g[3]:.6f} {g[4]:.6f} {g[5]:.6f} {g[6]:.6f} {g[7]:.6f}\n")
json.dump(stats, open(f"{OUT}/stats.json", "w"), indent=1)
print(json.dumps(stats))
