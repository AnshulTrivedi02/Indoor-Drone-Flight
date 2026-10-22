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
Usage (venv-fgo): lc_fgo_replay.py <trial> --mode lc|nolc [--t-max S] [--gauge-tag 0]

Tier-1 extension experiments, pre-registered (docs/thesis/tier1/preregistration.md; rulings 2026-10-21), all OFF
by default:
  --out-root DIR      write to DIR/<trial>/lc_fgo_<mode>[_tN]<suffix> instead of <trial>/lc_fgo_...; DIR must be under
                      ~/thesis_data/tier1 (tier1_paths.py). REQUIRED with any flag below; an existing non-empty
                      output directory is refused.
  --tag-ids 0,1,2,3   E2: use only these tag ids from /tags/raw (must include the gauge tag)
  --mislabel-rate P   E3: mislabel each central non-gauge detection with probability P (needs --mislabel-seed and
  --mislabel-seed S       --tag-ids = the valid ids); replacement uniform over the other non-gauge ids
  --tag-robust K:k    E3 arm (b), an estimator variant: robust kernel on the tag landmark factors (e.g. cauchy:2.385)
  --mislabel-keep T1,T2  E3 DIAGNOSIS ONLY (counterfactual, ruling 2026-10-22): the detections stamped T1, T2 (s, matched
                      to 1e-6) keep their TRUE id even if the injector mislabels them. The random stream, every other
                      injection and all counters are unchanged; the kept ones are logged in stats tier1.mislabel_keep.
With none of these flags the behaviour and outputs are unchanged."""
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
ap.add_argument("--out-root", default=None, help="tier-1 output root (must be under ~/thesis_data/tier1)")
ap.add_argument("--tag-ids", default=None, help="E2: comma-separated tag ids to use (must include the gauge tag)")
ap.add_argument("--mislabel-rate", type=float, default=None, help="E3: per central non-gauge detection")
ap.add_argument("--mislabel-seed", type=int, default=None, help="E3: numpy default_rng seed")
ap.add_argument("--tag-robust", default=None, help="E3 arm (b): 'cauchy:k' or 'huber:k' on the tag landmark factors")
ap.add_argument("--mislabel-keep", default=None, help="E3 diagnosis only: comma-separated detection stamps (s) not altered")
a = ap.parse_args()
PASS_GAP_S = 1.0
TIER1 = a.out_root is not None or a.tag_ids is not None or a.mislabel_rate is not None or a.mislabel_seed is not None \
    or a.tag_robust is not None or a.mislabel_keep is not None
if TIER1:
    import tier1_paths as T1
    if a.out_root is None:
        T1.refuse("--tag-ids / --mislabel-* / --tag-robust need --out-root under " + T1.TIER1_DATA_ROOT)
    if a.no_tags and (a.tag_ids is not None or a.mislabel_rate is not None or a.tag_robust is not None):
        T1.refuse("tag flags with --no-tags")
    if (a.mislabel_rate is None) != (a.mislabel_seed is None):
        T1.refuse("--mislabel-rate and --mislabel-seed go together")
    if a.mislabel_rate is not None and a.tag_ids is None:
        T1.refuse("--mislabel-rate needs --tag-ids (the condition's valid ids)")
    if a.tag_robust is not None and (len(a.tag_robust.split(":")) != 2 or a.tag_robust.split(":")[0] not in ("cauchy", "huber")):
        T1.refuse(f"--tag-robust {a.tag_robust!r}: expected cauchy:k or huber:k")
    if a.mislabel_keep is not None and a.mislabel_rate is None:
        T1.refuse("--mislabel-keep needs --mislabel-rate/--mislabel-seed")
    TAG_IDS = None if a.tag_ids is None else T1.parse_tag_ids(a.tag_ids, a.gauge_tag)
    MIS = None if a.mislabel_rate is None else T1.Mislabeller(a.mislabel_rate, a.mislabel_seed, TAG_IDS, a.gauge_tag)
else:
    TAG_IDS = MIS = None
n_tagfilt = 0; n_lm_first_mis = 0
KEEP = None if a.mislabel_keep is None else [float(x) for x in a.mislabel_keep.split(",")]; kept = []
FX, CX, CY = 554.3827056884766, 320.0, 240.0; R_VALID = (1.0 / 3.0) * math.hypot(CX, CY)
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); OUT = f"{D}/lc_fgo_{'notags' if a.no_tags else a.mode}" + ("" if a.t_max is None else f"_t{int(a.t_max)}")
if TIER1:   # tier-1: same base name, under the tier-1 root, plus the configuration suffix (guarded, no overwrite)
    OUT = T1.resolve_out(a.trial, os.path.basename(OUT) + T1.run_suffix(TAG_IDS, a.mislabel_rate, a.mislabel_seed,
                                                                          a.tag_robust)
                         + ("" if KEEP is None else "_cfkeep" + "-".join(f"{x:.3f}" for x in KEEP)), a.out_root)
else:
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
            tid = int(m.header.frame_id.split("_")[1]); mis = False
            if TAG_IDS is not None and tid not in TAG_IDS:
                n_tagfilt += 1; continue                   # E2: only the condition's tags
            if MIS is not None:
                tid_true = tid
                tid, mis = MIS(tt, tid)                    # E3: after the central filter (geometry-only, id-independent)
                if mis and KEEP is not None and any(abs(tt - x) < 1e-6 for x in KEEP):
                    kept.append((float(tt), int(tid_true), int(tid))); tid, mis = tid_true, False   # diagnosis only
            d_ = (tid, float(p_tb[0]), float(p_tb[1]), TM.yaw_of(R_tb))
            ev.append((tt, "tagrel", T1.MisDet(d_) if mis else d_))
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
if a.tag_robust is not None:     # E3 arm (b), estimator variant: robust kernel on the landmark factors only (not the L(0) prior)
    _kind, _k = a.tag_robust.split(":")
    tag_noise = gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Cauchy.Create(float(_k)) if _kind == "cauchy"
                                               else gtsam.noiseModel.mEstimator.Huber.Create(float(_k)), tag_noise)

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
    global k, prev, n_lmf, n_lm_first_mis
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
    for dd in tags:
        tid, mx, my, myaw = dd
        j, new = landmark_key(tid, t)
        if new and MIS is not None and isinstance(dd, T1.MisDet):
            n_lm_first_mis += 1                             # E3 covariate: a landmark initialised from a wrong id
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
if TIER1:   # provenance; absent in the default configuration (stats.json keys unchanged there)
    import subprocess
    _here = os.path.dirname(os.path.abspath(__file__))
    _git = lambda *c: subprocess.run(["git", "-C", _here, *c], capture_output=True, text=True).stdout.strip()
    st["tier1"] = {"argv": sys.argv, "commit": _git("rev-parse", "HEAD"), "src_dirty": _git("status", "--porcelain", "--", ".."),
                   "out": OUT, "tag_ids": None if TAG_IDS is None else list(TAG_IDS), "n_filtered_out_by_tag_ids": n_tagfilt,
                   "tag_robust": a.tag_robust, "landmarks_first_sighting_mislabelled": n_lm_first_mis,
                   **({} if KEEP is None else {"mislabel_keep": {"requested_t": KEEP, "kept_t_true_new": kept,
                       "note": "diagnosis counterfactual: these injections were drawn and counted but NOT applied"}}),
                   "mislabel": None if MIS is None else {
                       "rate": MIS.rate, "seed": MIS.seed, "rng": "numpy.random.default_rng (PCG64), 2 draws per call",
                       "valid_ids": list(MIS.valid), "gauge": MIS.gauge, "n_calls": MIS.n_calls,
                       "n_eligible_non_gauge": MIS.n_eligible, "n_mislabelled": MIS.n_mislabelled,
                       "events_t_true_new": MIS.events}}
json.dump(st, open(f"{OUT}/stats.json", "w"), indent=1)
print(json.dumps({k_: v for k_, v in st.items() if k_ != "landmarks_final"}))
