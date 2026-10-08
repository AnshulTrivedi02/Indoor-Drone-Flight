#!/usr/bin/env python3
"""Experiment T (and O later): FGO replay in an ABSOLUTE world frame with AprilTag fixes, plus the whole-flight batch
FGO (hindsight, labelled "FGO hindsight (whole-flight batch)"). A thin harness around fgo_core, like fgo_replay.py
(unchanged; corridor results never use this).

Inputs: the same bag topics as fgo_replay.py plus /tags/sent (the fixes the tag bridge SENT to EKF3 in this flight's
condition: identical measurements). Ground truth is not read (the UKF room replay writes it for the scorer).
Pre-registered handling (METHODOLOGY "Experiment T: pre-registration"):
  * the thesis FGO configuration: window 0.25 s, BatchFixedLagSmoother, LM capped at 2 iterations, 30 Hz IMU-clock
    keyframes; same init, IMU gap rule, dejitter and ground-proximity flow rule as fgo_replay.py;
  * first fix: FGO.reanchor (as EKF3's reset + yaw alignment, identical to the UKF's); later fixes: tag factor on the
    next keyframe (the newest fix since the last keyframe), NO gate, effective EKF3 noise;
  * the yaw cap runs only until the first fix;
  * hindsight: ONE batch LM (<= 50 iterations, rel tol 1e-6) over every factor the live smoother received from the
    re-anchor on, initialised from the live estimates.
Output: ~/thesis_data/trials/<trial>/room_fgo/{fgo_live.tum, fgo_batch.tum, stats.json}
Usage (venv-fgo): room_fgo_replay.py <trial> [--no-batch]"""
import sys, os, glob, math, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
import gtsam
from gtsam.symbol_shorthand import X
from fgo_core import FGO
from measurement_models import FlowFrameGyroAverager, GroundProximityFlow, TAG_SIGMA_POS, TAG_SIGMA_YAW
from measurement_models import GNSS_SIGMA_POS, GNSS_SIGMA_VEL, GNSS_ALIGN_SPEED, GNSS_ALIGN_N
from imu_timing import dejitter_imu, apply_gap_rule
import fgo_export

TRIAL = sys.argv[1]; DO_BATCH = "--no-batch" not in sys.argv
# experiment H: the wall-tag fix sigma from S0 (EKF3's VISO_POS_M_NSE), shared by the UKF and FGO; unset = T's 0.05 m
TAG_SIGMA_POS = float(os.environ.get("ROOM_TAG_SIGMA_POS", TAG_SIGMA_POS))
GNSS = "--gnss" in sys.argv      # experiment O (as room_ukf_replay.py --gnss); the yaw cap is kept throughout
WINDOW, LM_ITERS = 0.25, 2
D = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}"); OUT = f"{D}/room_fgo"
# C++-port equivalence export (docs/fgo_cpp_port.md), ALL OFF by default, as in fgo_replay.py: FGO_BAG_ROOT (read the bag from
# <root>/<trial>/), FGO_OUT_ROOT (write to <root>/<trial>/room_fgo/), FGO_DUMP_EVENTS (prefix; fgo_export.py)
BAGDIR = os.path.join(os.environ["FGO_BAG_ROOT"], TRIAL) if os.environ.get("FGO_BAG_ROOT") else f"{D}/bag"
if os.environ.get("FGO_OUT_ROOT"):
    OUT = os.path.join(os.environ["FGO_OUT_ROOT"], TRIAL, "room_fgo")
DUMP = os.environ.get("FGO_DUMP_EVENTS")
os.makedirs(OUT, exist_ok=True)
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9

ev = []
with Reader(BAGDIR) as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates", "/tags/sent"]
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
        else:
            q = m.pose.pose.orientation
            ev.append((tt, "tag", (m.pose.pose.position.x, m.pose.pose.position.y, 2 * math.atan2(q.z, q.w))))
if GNSS:
    _g = np.load(f"{D}/gnss.npz")
    ev += [(float(t), "gnss", (e, n, ve, vn)) for t, e, n, ve, vn in zip(_g["t"], _g["E"], _g["N"], _g["vE"], _g["vN"])]
_raw_ev = list(ev) if DUMP else None   # equivalence export: raw stream before gap rule / dejitter / sort
ev = apply_gap_rule(ev, TRIAL); ev, dj = dejitter_imu(ev); ev.sort(key=lambda e: e[0])

t_imu0 = next(t for t, k, _ in ev if k == "imu")
acc_lvl = [d[0] for t, k, d in ev if k == "imu" and t <= t_imu0 + 0.5]
first_rng = next(d for t, k, d in ev if k == "rng" and 0.05 <= d <= 40.0)
t_init = t_imu0 + 0.5
fgo = FGO(window=WINDOW, kf_dt=1.0 / 30.0, lm_maxiter=LM_ITERS, log_cov=True)   # log_cov: cov_prev for the re-anchor prior
fgo.batch_record = DO_BATCH
fgo.batch_drop_yawcap = True     # the yaw cap is a filtering device; the batch record excludes it (fgo_core; no effect in T,
#                                  where the cap is off from the re-anchor on and the batch starts there)
fgo.init(np.mean(acc_lvl, axis=0), first_rng, t_init)
_gpj = f"{D}/imu_gaps.json"
gp = GroundProximityFlow(json.load(open(_gpj)).get("arm_header_s") if os.path.exists(_gpj) else None)
gyro_avg = FlowFrameGyroAverager(t_init)
omega = np.zeros(3); flow_omega = np.zeros(3); t_prev_imu = None
flow_pend = rng_pend = tag_pend = gnss_pend = None; anchored = False; t_anchor = None; n_fast = 0
t_kf_next = t_init + fgo.kf_dt; traj = []; step_ns = []; n_fail = 0
_dump_flow_om = {}; _dump_kf = []        # equivalence export only (FGO_DUMP_EVENTS)
for _ei, (tt, kind, d) in enumerate(ev):
    if tt < t_init:
        if kind == "att": omega = d
        continue
    if kind == "att":
        omega = d
    elif kind == "rng":
        rng_pend = d; gp.on_range(tt, d)
    elif kind == "flow":
        flow_pend = d; flow_omega = gyro_avg.average(tt, omega)
        if DUMP: _dump_flow_om[_ei] = flow_omega
    elif kind == "gnss":
        if not anchored:
            n_fast = n_fast + 1 if math.hypot(d[2], d[3]) > GNSS_ALIGN_SPEED else 0
            if n_fast >= GNSS_ALIGN_N:
                spd = math.hypot(d[2], d[3])
                fgo.reanchor((d[0], d[1]), math.atan2(d[3], d[2]), GNSS_SIGMA_POS, math.asin(min(1.0, GNSS_SIGMA_VEL / spd)),
                             vel_EN=(d[2], d[3]), sig_vel=GNSS_SIGMA_VEL, keep_yawcap=True)
                fgo.gnss_noise = gtsam.noiseModel.Diagonal.Sigmas(np.array([GNSS_SIGMA_POS] * 2 + [GNSS_SIGMA_VEL] * 2))
                anchored = True; t_anchor = tt
        else:
            gnss_pend = d
    elif kind == "tag":
        if not anchored:
            fgo.reanchor((d[0], d[1]), d[2], TAG_SIGMA_POS, TAG_SIGMA_YAW); anchored = True; t_anchor = tt
            fgo.log_cov = False     # the gate-only covariance recursion was needed only for the re-anchor prior; it never
            #                         touches the smoother (fgo_core), and costs ~45 ms/keyframe
        else:
            tag_pend = d                              # the newest fix since the last keyframe
    elif kind == "imu":
        gp.on_gyro(tt, d[1], fgo.prev_bias.gyroscope()); gyro_avg.push(tt, d[1])
        if t_prev_imu is not None:
            fgo.integrate_imu(d[0], d[1], tt - t_prev_imu)
        t_prev_imu = tt
        while tt >= t_kf_next:
            if DUMP:
                _d = (fgo.k, gp.n_replaced, fgo.n_flow, fgo.n_range, getattr(fgo, "n_tag", 0), getattr(fgo, "n_gnss", 0), n_fail)
            t0 = time.perf_counter_ns()
            if flow_pend is not None and flow_pend[1] and flow_pend[2] > 0.0:
                _rpy = fgo.prev_pose.rotation().rpy()
                flow_pend = (gp.replace(flow_pend[0], flow_omega - fgo.prev_bias.gyroscope(), _rpy[0], _rpy[1]), flow_pend[1], flow_pend[2])
            try:
                fgo.keyframe(t_kf_next, flow=flow_pend, omega=flow_omega, rng=rng_pend, tag=tag_pend, gnss=gnss_pend)
            except Exception as e:
                n_fail += 1; print(f"[warn] keyframe at {t_kf_next:.3f} failed: {type(e).__name__}: {e}")
            step_ns.append(time.perf_counter_ns() - t0)
            t_lat, pose, vel = fgo.latest(); rpy = pose.rotation().rpy()
            if DUMP:   # layout: fgo_export.kf_row
                _dump_kf.append(fgo_export.kf_row(t_kf_next, t_lat, _d[0], fgo.k, gp.n_replaced - _d[1], fgo.n_flow - _d[2],
                                                  fgo.n_range - _d[3], None if flow_pend is None else flow_pend[0], rng_pend,
                                                  pose, vel, fgo.prev_bias, (), getattr(fgo, "n_tag", 0) - _d[4],
                                                  getattr(fgo, "n_gnss", 0) - _d[5], int(anchored), n_fail - _d[6], n_fail))
            if anchored:
                traj.append((t_lat, pose.x(), pose.y(), pose.z(), rpy[0], rpy[1], rpy[2]))
            flow_pend = rng_pend = tag_pend = gnss_pend = None
            t_kf_next += fgo.kf_dt


def euler_to_quat(r, pch, y):
    cr, sr = np.cos(r/2), np.sin(r/2); cp, sp = np.cos(pch/2), np.sin(pch/2); cy, sy = np.cos(y/2), np.sin(y/2)
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy)


def write_rows(path, rows):
    with open(path, "w") as f:
        for t, x, y, z, r_, p_, yw in rows:
            q = euler_to_quat(r_, p_, yw)
            f.write(f"{t:.6f} {x:.6f} {y:.6f} {z:.6f} {q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}\n")


write_rows(f"{OUT}/fgo_live.tum", traj)
stats = {"t_anchor": t_anchor, "n_tag_factors": getattr(fgo, "n_tag", 0), "n_gnss_factors": getattr(fgo, "n_gnss", 0),
         "mode": "gnss" if GNSS else "tags", "keyframe_failures": n_fail,
         "step_median_ms": float(np.median(step_ns) / 1e6), "window_s": WINDOW, "lm_iters": LM_ITERS}
if DO_BATCH and anchored:
    t0b = time.perf_counter()
    prm = gtsam.LevenbergMarquardtParams(); prm.setMaxIterations(50); prm.setRelativeErrorTol(1e-6)
    init_vals = gtsam.Values()
    for key, val in fgo.all_est.items():
        init_vals.insert(key, val)
    opt = gtsam.LevenbergMarquardtOptimizer(fgo.all_g, init_vals, prm); res = opt.optimize()
    rows = []
    for kk, tk in fgo.key_t:
        if res.exists(X(kk)):
            p_ = res.atPose3(X(kk)); rpy = p_.rotation().rpy(); rows.append((tk, p_.x(), p_.y(), p_.z(), rpy[0], rpy[1], rpy[2]))
    write_rows(f"{OUT}/fgo_batch.tum", rows)
    if DUMP:
        _batch_rows = [[kk, tk] + list(res.atPose3(X(kk)).translation()) + list(res.atPose3(X(kk)).rotation().matrix().reshape(-1))
                       for kk, tk in fgo.key_t if res.exists(X(kk))]
    stats.update({"batch_factors": int(fgo.all_g.size()), "batch_error": float(opt.error()), "batch_iterations": int(opt.iterations()),
                  "batch_s": time.perf_counter() - t0b})
json.dump(stats, open(f"{OUT}/stats.json", "w"), indent=1)
if DUMP:
    fgo_export.write(DUMP, {"trial": TRIAL, "mode": "room", "gnss": GNSS, "batch": DO_BATCH,
                            "accel_mean": [float(a) for a in np.mean(acc_lvl, axis=0)], "first_range": float(first_rng),
                            "t_init": float(t_init), "t_arm": gp.t_arm, "window": WINDOW, "lm_iters": LM_ITERS,
                            "kf_dt": fgo.kf_dt, "log_cov": True, "tag_sigma_pos": float(TAG_SIGMA_POS),
                            "tag_sigma_yaw": float(TAG_SIGMA_YAW), "gnss_sigma_pos": float(GNSS_SIGMA_POS),
                            "gnss_sigma_vel": float(GNSS_SIGMA_VEL), "gnss_align_speed": float(GNSS_ALIGN_SPEED),
                            "gnss_align_n": int(GNSS_ALIGN_N), "t_anchor": t_anchor,
                            "imu_gaps": (json.load(open(_gpj)) if os.path.exists(_gpj) else None)},
                     _raw_ev, ev, _dump_flow_om, {}, _dump_kf, _batch_rows if (DO_BATCH and anchored) else None)
print(json.dumps(stats))
