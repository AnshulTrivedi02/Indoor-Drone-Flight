#!/usr/bin/env python3
"""Experiment L: "keyframe FGO with loop closure" (labelled SEPARATELY from the thesis FGO). AprilTags at UNKNOWN
positions; tag re-identification (the decoded id) gives loop-closure factors. Offline replay of a T flight's
/tags/raw (every detection, independent of the T condition).

Pipeline (METHODOLOGY "Experiment L: pre-registration"):
  * before the first sighting of the gauge tag: the thesis FGO (fgo_core.FGO, fixed-lag, unchanged), exactly as T;
  * at the first sighting: re-anchor (as T) so the vehicle is at its measured pose in that tag's frame (that tag =
    origin), and START the retained-history graph: plain iSAM2 (no marginalisation), the thesis keyframes (30 Hz IMU
    clock), the thesis factors (CombinedImuFactor over every IMU sample, flow, range, no yaw cap: as T after the
    anchor) plus tag-landmark factors;
  * tag landmark L_j = (x, y, yaw) of a tag on the (flat) floor: the floor-plane assumption (tag z, roll, pitch known)
    is stated. Measurement = the vehicle (x, y, yaw) in the tag frame from tag_measure.vehicle_pose with the tag at the
    origin (the same information as a T fix), noise 0.05 m / 5 deg (as T), central-third validity rule (as T; the image
    centre from projecting t_cam_tag). The gauge tag has a tight prior at the origin;
  * --mode lc   : one landmark per tag id (re-identification -> loop closures);
    --mode nolc : a NEW landmark for every pass over a tag (a pass ends after > PASS_GAP_S without a sighting), so
                  the only difference from lc is the re-identification;
  * live = the newest keyframe after each iSAM2 update; hindsight = every keyframe from the final estimate, after an
    LM polish (<= 20 iterations) over the full graph.
Ground truth is not read. Output: <trial>/lc_fgo_<mode>/{live.tum, hindsight.tum, stats.json} in the GAUGE-TAG frame.
Usage (venv-fgo): lc_fgo_replay.py <trial> --mode lc|nolc [--t-max S] [--gauge-tag 0]"""
import sys, os, glob, math, json, time, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tags"))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
import gtsam
from gtsam import Pose3, Rot3, NavState, CombinedImuFactor, PriorFactorPose3, PriorFactorConstantBias, CustomFactor
from gtsam.symbol_shorthand import X, V, B, L
from fgo_core import FGO
import factors as F
from measurement_models import FlowFrameGyroAverager, GroundProximityFlow, TAG_SIGMA_POS, TAG_SIGMA_YAW
from imu_timing import dejitter_imu, apply_gap_rule
import tag_measure as TM

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--mode", choices=["lc", "nolc"], required=True)
ap.add_argument("--t-max", type=float, default=None); ap.add_argument("--gauge-tag", type=int, default=0)
ap.add_argument("--no-tags", action="store_true", help="validation V-L: no tags; the retained-history graph starts at the "
                "first keyframe from the thesis initial state, with the thesis factors INCLUDING the yaw cap")
a = ap.parse_args()
PASS_GAP_S = 1.0
FX, CX, CY = 554.3827056884766, 320.0, 240.0; R_VALID = (1.0 / 3.0) * math.hypot(CX, CY)
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); OUT = f"{D}/lc_fgo_{'notags' if a.no_tags else a.mode}" + ("" if a.t_max is None else f"_t{int(a.t_max)}")
os.makedirs(OUT, exist_ok=True)
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
ORIGIN_TAG = {"p": np.zeros(3), "yaw": 0.0}

ev = []; n_raw = n_central = 0
with Reader(f"{D}/bag") as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates", "/tags/raw"]
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
            n_raw += 1
            t_ct = np.array([m.pose.position.x, m.pose.position.y, m.pose.position.z])
            q = m.pose.orientation
            R_ct = Rot3.Quaternion(q.w, q.x, q.y, q.z).matrix()
            u, v = FX * t_ct[0] / t_ct[2] + CX, FX * t_ct[1] / t_ct[2] + CY
            if math.hypot(u - CX, v - CY) > R_VALID:
                continue                                   # central-third validity rule (as T)
            n_central += 1
            p_tb, R_tb = TM.vehicle_pose(ORIGIN_TAG, R_ct, t_ct)
            ev.append((tt, "tagrel", (int(m.header.frame_id.split("_")[1]), float(p_tb[0]), float(p_tb[1]), TM.yaw_of(R_tb))))
ev = apply_gap_rule(ev, a.trial); ev, dj = dejitter_imu(ev); ev.sort(key=lambda e: e[0])


def landmark_factor(noise, key_x, key_l, meas):
    """Vehicle (x, y, yaw) in the frame of landmark L = (xL, yL, yawL), minus the measurement (as a T fix, relative)."""
    mx, my, myaw = meas

    def err(pose, lm):
        c, s = math.cos(lm[2]), math.sin(lm[2]); t = pose.translation()
        dx, dy = t[0] - lm[0], t[1] - lm[1]
        return np.array([c * dx + s * dy - mx, -s * dx + c * dy - my, F._wrap(pose.rotation().yaw() - lm[2] - myaw)])

    def efun(this, values, H):
        pose = values.atPose3(key_x); lm = values.atVector(key_l)
        e = err(pose, lm)
        if H is not None:
            Hp = np.zeros((3, 6)); Hl = np.zeros((3, 3))
            for j in range(6):
                d = np.zeros(6); d[j] = F.EPS
                Hp[:, j] = (err(pose.retract(d), lm) - err(pose.retract(-d), lm)) / (2 * F.EPS)
            for j in range(3):
                d = np.zeros(3); d[j] = F.EPS
                Hl[:, j] = (err(pose, lm + d) - err(pose, lm - d)) / (2 * F.EPS)
            H[0] = Hp; H[1] = Hl
        return e
    return CustomFactor(noise, [key_x, key_l], efun)


def lm_from(pose, meas):
    yawL = F._wrap(pose.rotation().yaw() - meas[2]); c, s = math.cos(yawL), math.sin(yawL); t = pose.translation()
    return np.array([t[0] - (c * meas[0] - s * meas[1]), t[1] - (s * meas[0] + c * meas[1]), yawL])


# ---- pre-anchor: the thesis FGO, unchanged ----
t_imu0 = next(t for t, k, _ in ev if k == "imu")
acc_lvl = [d[0] for t, k, d in ev if k == "imu" and t <= t_imu0 + 0.5]
first_rng = next(d for t, k, d in ev if k == "rng" and 0.05 <= d <= 40.0)
t_init = t_imu0 + 0.5
fgo = FGO(window=0.25, kf_dt=1.0 / 30.0, lm_maxiter=2, log_cov=True)
fgo.init(np.mean(acc_lvl, axis=0), first_rng, t_init)
_gpj = f"{D}/imu_gaps.json"
gp = GroundProximityFlow(json.load(open(_gpj)).get("arm_header_s") if os.path.exists(_gpj) else None)
gyro_avg = FlowFrameGyroAverager(t_init)
tag_noise = gtsam.noiseModel.Diagonal.Sigmas(np.array([TAG_SIGMA_POS, TAG_SIGMA_POS, TAG_SIGMA_YAW]))

isam = None; k = None; prev = None; pim = None
lm_key = {}; last_seen = {}; n_lm = 0; n_lmf = 0; t_anchor = None
live = []; key_t = []; step_ns = []; n_fail = 0
omega = np.zeros(3); flow_omega = np.zeros(3); t_prev_imu = None
flow_pend = rng_pend = None; tags_pend = []
t_kf_next = t_init + 1.0 / 30.0


def start_isam(t_now, meas):
    """Re-anchor (as T) and start the retained-history iSAM2 graph at the newest keyframe state."""
    global isam, k, prev, pim, t_anchor
    p0 = fgo.prev_pose; r_, p_, y_ = p0.rotation().rpy()
    d = F._wrap(meas[3] - y_); c, s_ = math.cos(d), math.sin(d); R3 = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1.0]])
    pose = Pose3(Rot3.Ypr(meas[3], p_, r_), np.array([meas[1], meas[2], p0.translation()[2]]))
    vel = R3 @ np.asarray(fgo.prev_vel, float); bias = fgo.prev_bias; C = fgo.cov_prev
    # loose x, y, yaw on the state prior (the gauge comes from the gauge-tag prior + this first measurement)
    pose_sig = np.array([np.sqrt(C[0, 0]), np.sqrt(C[1, 1]), 0.5, 1.0, 1.0, np.sqrt(C[5, 5])])
    vel_sig = np.sqrt(np.diag(R3 @ C[6:9, 6:9] @ R3.T)); bias_sig = np.sqrt(np.diag(C[9:15, 9:15]))
    prm = gtsam.ISAM2Params(); prm.setFactorization("QR")
    isam = gtsam.ISAM2(prm)
    k = 0; g = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
    g.add(PriorFactorPose3(X(k), pose, gtsam.noiseModel.Diagonal.Sigmas(pose_sig)))
    g.add(gtsam.PriorFactorVector(V(k), vel, gtsam.noiseModel.Diagonal.Sigmas(vel_sig)))
    g.add(PriorFactorConstantBias(B(k), bias, gtsam.noiseModel.Diagonal.Sigmas(bias_sig)))
    vals.insert(X(k), pose); vals.insert(V(k), vel); vals.insert(B(k), bias)
    isam.update(g, vals)
    prev = (pose, vel, bias); pim = fgo.pim; t_anchor = t_now; key_t.append((k, fgo.t_last))


def start_isam_plain(t_now):
    """V-L: start the retained graph from the thesis FGO's first keyframe state, thesis gauge (x, y 1e-3). The yaw sigma
    is the thesis FGO's own (cov_prev; from fgo_core.YAW0_SIGMA), no longer a hard 1e-3 (D18 initial-sigma audit,
    2026-10-10)."""
    global isam, k, prev, pim, t_anchor
    pose, vel, bias = fgo.prev_pose, np.asarray(fgo.prev_vel, float), fgo.prev_bias; C = fgo.cov_prev
    pose_sig = np.array([np.sqrt(C[0, 0]), np.sqrt(C[1, 1]), np.sqrt(C[2, 2]), 1e-3, 1e-3, np.sqrt(C[5, 5])])
    prm = gtsam.ISAM2Params(); prm.setFactorization("QR"); isam = gtsam.ISAM2(prm)
    k = 0; g = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
    g.add(PriorFactorPose3(X(k), pose, gtsam.noiseModel.Diagonal.Sigmas(pose_sig)))
    g.add(gtsam.PriorFactorVector(V(k), vel, gtsam.noiseModel.Diagonal.Sigmas(np.sqrt(np.diag(C[6:9, 6:9])))))
    g.add(PriorFactorConstantBias(B(k), bias, gtsam.noiseModel.Diagonal.Sigmas(np.sqrt(np.diag(C[9:15, 9:15])))))
    vals.insert(X(k), pose); vals.insert(V(k), vel); vals.insert(B(k), bias)
    isam.update(g, vals); prev = (pose, vel, bias); pim = fgo.pim; t_anchor = t_now; key_t.append((k, fgo.t_last))


def landmark_key(tid, t_now):
    global n_lm
    new = tid not in lm_key or (a.mode == "nolc" and t_now - last_seen[tid] > PASS_GAP_S)
    if new:
        lm_key[tid] = n_lm; n_lm += 1
    last_seen[tid] = t_now
    return lm_key[tid], new


def isam_keyframe(t, flow, omega_f, rng, tags):
    global k, prev, n_lmf
    if pim.deltaTij() <= 0:
        return
    km1, k = k, k + 1
    pred = pim.predict(NavState(prev[0], prev[1]), prev[2])
    g = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
    vals.insert(X(k), pred.pose()); vals.insert(V(k), pred.velocity()); vals.insert(B(k), prev[2])
    g.add(CombinedImuFactor(X(km1), V(km1), X(k), V(k), B(km1), B(k), pim))
    if a.no_tags:                                   # V-L: the thesis yaw cap (zero innovation vs the predicted yaw)
        g.add(F.yaw_prior_factor(fgo.yaw_noise, X(k), pred.pose().rotation().yaw()))
    if rng is not None and 0.05 <= rng <= 40.0:
        g.add(F.range_factor(fgo.range_noise, X(k), rng))
    if flow is not None:
        fxy, valid, inlier = flow
        if valid and inlier > 0.0 and abs(fxy[0]) < 4.2 and abs(fxy[1]) < 4.2:
            g.add(F.flow_factor(fgo.flow_noise, X(k), V(k), B(k), fxy, omega_f))
    for tid, mx, my, myaw in tags:
        j, new = landmark_key(tid, t)
        if new:
            if j == 0:                                      # the gauge tag: tight prior at the origin
                vals.insert(L(0), np.zeros(3))
                g.add(gtsam.PriorFactorVector(L(0), np.zeros(3), gtsam.noiseModel.Isotropic.Sigma(3, 1e-4)))
            else:
                vals.insert(L(j), lm_from(pred.pose(), (mx, my, myaw)))
        g.add(landmark_factor(tag_noise, X(k), L(j), (mx, my, myaw))); n_lmf += 1
    isam.update(g, vals)
    est = isam.calculateEstimate()
    prev = (est.atPose3(X(k)), est.atVector(V(k)), est.atConstantBias(B(k)))
    pim.resetIntegrationAndSetBias(prev[2]); key_t.append((k, t))
    if k % 1000 == 0:
        print(f"[progress] keyframe {k} t {t:.1f} landmarks {n_lm} wall {time.perf_counter() - t_wall0:.0f} s", flush=True)
    rpy = prev[0].rotation().rpy(); live.append((t, prev[0].x(), prev[0].y(), prev[0].z(), rpy[0], rpy[1], rpy[2]))


t_wall0 = time.perf_counter()
for tt, kind, d in ev:
    if a.t_max is not None and t_anchor is not None and tt > t_anchor + a.t_max:
        break
    if tt < t_init:
        if kind == "att": omega = d
        continue
    if kind == "att":
        omega = d
    elif kind == "rng":
        rng_pend = d; gp.on_range(tt, d)
    elif kind == "flow":
        flow_pend = d; flow_omega = gyro_avg.average(tt, omega)
    elif kind == "tagrel":
        if a.no_tags:
            continue
        if isam is None:
            if d[0] == a.gauge_tag:
                start_isam(tt, d)
                tags_pend = [d]          # first measurement on the next keyframe; it creates the gauge landmark L(0)
        else:
            tags_pend.append(d)
    elif kind == "imu":
        bias_g = (prev[2] if isam is not None else fgo.prev_bias).gyroscope()
        gp.on_gyro(tt, d[1], bias_g); gyro_avg.push(tt, d[1])
        if t_prev_imu is not None:
            fgo.integrate_imu(d[0], d[1], tt - t_prev_imu)       # the same pim object is used after the anchor
        t_prev_imu = tt
        while tt >= t_kf_next:
            if flow_pend is not None and flow_pend[1] and flow_pend[2] > 0.0:
                rp = (prev[0] if isam is not None else fgo.prev_pose).rotation().rpy()
                flow_pend = (gp.replace(flow_pend[0], flow_omega - bias_g, rp[0], rp[1]), flow_pend[1], flow_pend[2])
            t0 = time.perf_counter_ns()
            try:
                if isam is None:
                    fgo.keyframe(t_kf_next, flow=flow_pend, omega=flow_omega, rng=rng_pend)
                    if a.no_tags:
                        start_isam_plain(t_kf_next)
                else:
                    isam_keyframe(t_kf_next, flow_pend, flow_omega, rng_pend, tags_pend)
            except Exception as e:
                n_fail += 1; print(f"[warn] keyframe {t_kf_next:.3f}: {type(e).__name__}: {e}")
            step_ns.append(time.perf_counter_ns() - t0)
            flow_pend = rng_pend = None; tags_pend = []
            t_kf_next += 1.0 / 30.0


def euler_to_quat(r, pch, y):
    cr, sr = np.cos(r/2), np.sin(r/2); cp, sp = np.cos(pch/2), np.sin(pch/2); cy, sy = np.cos(y/2), np.sin(y/2)
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy)


def write_rows(path, rows):
    with open(path, "w") as f:
        for t, x, y, z, r_, p_, yw in rows:
            q = euler_to_quat(r_, p_, yw)
            f.write(f"{t:.6f} {x:.6f} {y:.6f} {z:.6f} {q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}\n")


write_rows(f"{OUT}/live.tum", live)
t_h0 = time.perf_counter()
# DEVIATION (recorded, 2026-10-08): the pre-registered final LM polish over the whole graph did not finish within
# 5000 s on the 300 s V-L flight (Python CustomFactors, ~10k keyframes). Hindsight = iSAM2's own full-graph estimate
# after 5 extra update() calls with no new factors (each relinearises every variable over the threshold).
for _ in range(5):
    isam.update()
res = isam.calculateEstimate()
rows = []
for kk, tk in key_t:
    if res.exists(X(kk)):
        p_ = res.atPose3(X(kk)); rpy = p_.rotation().rpy(); rows.append((tk, p_.x(), p_.y(), p_.z(), rpy[0], rpy[1], rpy[2]))
write_rows(f"{OUT}/hindsight.tum", rows)
lms = {int(j): [float(v) for v in res.atVector(L(j))] for j in range(n_lm) if res.exists(L(j))}
st = {"mode": a.mode, "t_anchor": t_anchor, "keyframes": len(key_t), "landmarks": n_lm, "landmark_factors": n_lmf,
      "raw_detections": n_raw, "central": n_central, "keyframe_failures": n_fail,
      "step_median_ms": float(np.median(step_ns) / 1e6), "step_p99_ms": float(np.percentile(step_ns, 99) / 1e6),
      "wall_s": time.perf_counter() - t_wall0, "hindsight_polish_s": time.perf_counter() - t_h0, "landmarks_final": lms}
json.dump(st, open(f"{OUT}/stats.json", "w"), indent=1)
print(json.dumps({k_: v for k_, v in st.items() if k_ != "landmarks_final"}))
