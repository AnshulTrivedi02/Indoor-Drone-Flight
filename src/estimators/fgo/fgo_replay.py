#!/usr/bin/env python3
"""Thin bag-replay harness around fgo_core (a live ROS2 node would be an equally
thin wrapper). Reads a recorded bag, drives the FGO on the IMU clock, writes a
TUM trajectory, prints acceptance metrics + per-step timing. Ground truth is used
ONLY for evaluation, never as an input.

Usage: fgo_replay.py <trial_name>
"""
import sys, os, glob, math, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # for measurement_models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                    # for factors/fgo_core
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from fgo_core import FGO
import fgo_core as _fc
from measurement_models import h_flow_pose, FlowFrameGyroAverager, sitl_gyro_drift, GroundProximityFlow
from measurement_models import FWD_ARMS, FWD_SIGMA, FWD_CHI2_GATE, forward_events, fwd_dataset, f_variant, f_filter_forward
import json
import fgo_export
from imu_timing import dejitter_imu, apply_gap_rule

TRIAL = sys.argv[1]
# Phase 4 arm (argv[4]; METHODOLOGY): none = legacy run into fgo/ (unchanged); otherwise one
# of baseline / heading / heading_yawrate, written to fgo_<arm>/.
ARM = sys.argv[4] if len(sys.argv) > 4 else None
assert ARM in (None,) + FWD_ARMS, ARM
BAG = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/bag")
# C++-port equivalence export (docs/fgo_cpp_port.md). ALL OFF by default; with none set nothing changes.
#   FGO_BAG_ROOT     read the bag from <root>/<trial>/ instead (e.g. a scratch copy)
#   FGO_OUT_ROOT     write the outputs to <root>/<trial>/fgo_<arm>/ instead of the trial directory
#   FGO_DUMP_EVENTS  path prefix: write <prefix>.init.json, <prefix>.events.f64 (the exact event stream the loop
#                    consumes, after gap rule / dejitter / sort, with each flow's interval-averaged omega) and
#                    <prefix>.kf.f64 (per-keyframe inputs and outputs at full float64 precision). Dump writes sit
#                    outside the timed region and do not touch the estimator.
if os.environ.get("FGO_BAG_ROOT"):
    BAG = os.path.join(os.environ["FGO_BAG_ROOT"], TRIAL)
DUMP = os.environ.get("FGO_DUMP_EVENTS")
FV = f_variant()     # offline F-test variants (all off by default)
OUTDIR = os.path.expanduser((os.path.join(os.environ["FGO_OUT_ROOT"], TRIAL) if os.environ.get("FGO_OUT_ROOT") else f"~/thesis_data/trials/{TRIAL}") + "/fgo" + ("" if ARM is None else f"_{ARM}") + (f"_{FV['F_TAG']}" if FV["F_TAG"] else ""))
os.makedirs(OUTDIR, exist_ok=True)
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec*1e-9

ev = []; gt = []
with Reader(BAG) as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range",
            "/attitude/angular_rates", "/ground_truth/pose"]
    for con, t, raw in r.messages(connections=[conns[w] for w in want if w in conns]):
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
            gt.append((tt, m.pose.position.x, m.pose.position.y, m.pose.position.z))
ev += forward_events(TRIAL, ARM)    # Phase 4 forward-camera measurements ([] for baseline/legacy)
_raw_ev = list(ev) if DUMP else None  # equivalence export: the raw stream, before gap rule / dejitter / sort
ev = apply_gap_rule(ev, TRIAL)      # IMU-gap rule (METHODOLOGY, 2026-09-24)
ev, _imu_dj = dejitter_imu(ev)     # OI-2: regular IMU timing (METHODOLOGY, OI-2 ruling)
print(f"[imu] dejittered: period {_imu_dj['period_ms']:.5f} ms, resid std {_imu_dj['resid_std_ms']:.2f} max {_imu_dj['resid_maxabs_ms']:.2f} ms")
ev.sort(key=lambda e: e[0]); gt = np.array(sorted(gt))
ev = f_filter_forward(ev, gt[:, 0], gt[:, 1], gt[:, 2], FV)

# init: gravity levelling over first 0.5 s + first valid range
t_imu0 = next(t for t, k, _ in ev if k == "imu")
acc_lvl = [d[0] for t, k, d in ev if k == "imu" and t <= t_imu0 + 0.5]
first_rng = next(d for t, k, d in ev if k == "rng" and 0.05 <= d <= 40.0)
t_init = t_imu0 + 0.5
WINDOW = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
LM_ITERS = int(sys.argv[3]) if len(sys.argv) > 3 else 2
sig_fwd = FWD_SIGMA[fwd_dataset(TRIAL)] if ARM not in (None, "baseline") else None
fgo = FGO(window=WINDOW, kf_dt=1.0/30.0, lm_maxiter=LM_ITERS, fwd_sigma=sig_fwd,
          fwd_gate=(float("inf") if FV["F_ROBUST"] else FWD_CHI2_GATE), fwd_robust=FV["F_ROBUST"],
          log_cov=bool(os.environ.get("FGO_COV_LOG")))   # diagnostic covariance log (Phase 5b)
fgo.batch_record = bool(FV["F_BATCH"])
fgo.init(np.mean(acc_lvl, axis=0), first_rng, t_init,
         yaw0=(np.radians(float(FV["F_YAW0_DEG"])) if FV["F_YAW0_DEG"] else 0.0),
         yaw_sigma=(np.radians(float(FV["F_YAW0_SIGMA_DEG"] or FV["F_YAW0_DEG"])) if FV["F_YAW0_DEG"] else None))
fgo.no_yawcap = bool(FV["F_NO_YAWCAP"])   # F3b: yaw-cap prior off
print(f"[init] t={t_init:.2f}s first_range={first_rng:.3f}")

# run: integrate every IMU sample; create a keyframe on the fixed IMU-clock cadence
traj = []                       # (t, pE, pN, pU, roll, pitch, yaw, bgz_rate)
omega = np.zeros(3); t_prev_imu = None
gyro_avg = FlowFrameGyroAverager(t_init)     # interval-avg gyro for h_flow derotation (FINDING 4)
flow_omega = np.zeros(3)
flow_pend = None; rng_pend = None; fwd_pend = None
fwd_avg = FlowFrameGyroAverager(t_init)      # gyro over the forward-frame interval (Phase 4 h_yawrate)
t_kf_next = t_init + fgo.kf_dt
# ground-proximity flow rule (ruling D15): EKF3's, identical to the UKF's (measurement_models.GroundProximityFlow)
_gpj = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/imu_gaps.json")
gp = GroundProximityFlow(json.load(open(_gpj)).get("arm_header_s") if os.path.exists(_gpj) else None)
step_ns = []; n_kf = 0
vmag = []; fresid = []          # diag: cruise velocity magnitude, flow-factor residual at converged state
_dump_flow_om = {}; _dump_fwd_gz = {}; _dump_kf = []        # equivalence export only (FGO_DUMP_EVENTS)
for _ei, (tt, kind, d) in enumerate(ev):
    if tt < t_init:
        if kind == "att": omega = d
        continue
    if kind == "att":
        omega = d
    elif kind == "rng":
        rng_pend = d
        gp.on_range(tt, d)
    elif kind == "flow":
        flow_pend = d
        flow_omega = gyro_avg.average(tt, omega)   # interval-avg over the flow frame (FINDING 4)
        if DUMP: _dump_flow_om[_ei] = flow_omega
    elif kind == "fwd":
        fwd_pend = (d[0], d[1], float(fwd_avg.average(tt, omega)[2]))   # latest forward frame
        if DUMP: _dump_fwd_gz[_ei] = fwd_pend[2]
    elif kind == "imu":
        gp.on_gyro(tt, d[1], fgo.prev_bias.gyroscope())
        gyro_avg.push(tt, d[1])                     # co-sampled gyro, for the flow-frame average
        fwd_avg.push(tt, d[1])
        if t_prev_imu is not None:
            fgo.integrate_imu(d[0], d[1], tt - t_prev_imu)
        t_prev_imu = tt
        while tt >= t_kf_next:
            if DUMP: _d_k, _d_nr, _d_nf, _d_nrg, _d_nfw = fgo.k, gp.n_replaced, fgo.n_flow, fgo.n_range, len(fgo.fwd_log)
            t0 = time.perf_counter_ns()
            if flow_pend is not None and flow_pend[1] and flow_pend[2] > 0.0:
                _rpy = fgo.prev_pose.rotation().rpy()    # the FGO's flow factor uses omega - bias: zero translation in that model
                flow_pend = (gp.replace(flow_pend[0], flow_omega - fgo.prev_bias.gyroscope(), _rpy[0], _rpy[1]), flow_pend[1], flow_pend[2])
            try:
                fgo.keyframe(t_kf_next, flow=flow_pend, omega=flow_omega, rng=rng_pend, fwd=fwd_pend)
            except Exception as e:
                print(f"[warn] keyframe at {t_kf_next:.3f} failed: {type(e).__name__}: {e}")
            step_ns.append(time.perf_counter_ns() - t0); n_kf += 1
            t_lat, pose, vel = fgo.latest()
            rpy = pose.rotation().rpy()          # [roll, pitch, yaw]
            bgz = fgo.prev_bias.gyroscope()[2]
            traj.append((t_lat, pose.x(), pose.y(), pose.z(), rpy[0], rpy[1], rpy[2], bgz))
            if DUMP:   # layout: fgo_export.kf_row
                _dump_kf.append(fgo_export.kf_row(t_kf_next, t_lat, _d_k, fgo.k, gp.n_replaced - _d_nr, fgo.n_flow - _d_nf,
                                                  fgo.n_range - _d_nrg, None if flow_pend is None else flow_pend[0], rng_pend,
                                                  pose, vel, fgo.prev_bias, fgo.fwd_log[_d_nfw:]))
            # diag (read-only): |V(k)| and the flow-factor residual at the converged state
            vmag.append((t_lat, float(np.linalg.norm(vel))))
            if flow_pend is not None and flow_pend[1] and flow_pend[2] > 0.0 \
                    and abs(flow_pend[0][0]) < 4.2 and abs(flow_pend[0][1]) < 4.2:
                om = flow_omega - fgo.prev_bias.gyroscope()
                pred = h_flow_pose(pose.rotation().matrix(), vel, pose.translation()[2], om)
                fresid.append((t_lat, pred[0]-flow_pend[0][0], pred[1]-flow_pend[0][1]))
            flow_pend = None; rng_pend = None; fwd_pend = None
            t_kf_next += fgo.kf_dt
traj = np.array(traj)
if DUMP:
    assert not any(FV[k] for k in FV), "equivalence export: no F-variants"
    fgo_export.write(DUMP, {"trial": TRIAL, "mode": "corridor", "arm": ARM,
                            "accel_mean": [float(a) for a in np.mean(acc_lvl, axis=0)], "first_range": float(first_rng),
                            "t_init": float(t_init), "t_arm": gp.t_arm, "window": WINDOW, "lm_iters": LM_ITERS,
                            "kf_dt": fgo.kf_dt, "log_cov": bool(fgo.log_cov),
                            "fwd_sigma_psi": None if sig_fwd is None else float(sig_fwd["psi"]),
                            "fwd_sigma_omega": None if (sig_fwd is None or sig_fwd.get("omega") is None) else float(sig_fwd["omega"]),
                            "fwd_gate": float(fgo.fwd_gate), "imu_gaps": (json.load(open(_gpj)) if os.path.exists(_gpj) else None)},
                     _raw_ev, ev, _dump_flow_om, _dump_fwd_gz, _dump_kf, yawgate=fgo.yawgate_log)
fl = np.array([r[:4] for r in fgo.fwd_log]).reshape(-1, 4)          # (t, kind, nis, ok): unchanged format
fS = np.array([r[4] for r in fgo.fwd_log])                              # innovation covariance S (Phase 5b)
np.savez_compressed(f"{OUTDIR}/timing_and_fwd.npz", t_keyframe_ns=np.array(step_ns, np.int64), fwd_log=fl,
                    fwd_S=fS, cov_log=np.array(fgo.cov_log).reshape(-1, 5))
cnt = {"psi_valid": int((fl[:, 1] == 0).sum()), "psi_fused": int(((fl[:, 1] == 0) & (fl[:, 3] > 0)).sum()),
       "omega_valid": int((fl[:, 1] == 1).sum()), "omega_fused": int(((fl[:, 1] == 1) & (fl[:, 3] > 0)).sum())}
json.dump({"arm": ARM, "counts": cnt, "sigma": sig_fwd and {k: (None if v is None else float(v)) for k, v in sig_fwd.items()},
           "gate": FWD_CHI2_GATE}, open(f"{OUTDIR}/fwd_stats.json", "w"), indent=1)

# write TUM (ENU, euler->quat)
def euler_to_quat(r, pch, y):
    cr, sr = np.cos(r/2), np.sin(r/2); cp, sp = np.cos(pch/2), np.sin(pch/2); cy, sy = np.cos(y/2), np.sin(y/2)
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy)   # w fixed (ruling D10, 2026-09-30): was sr*sp*cy
with open(f"{OUTDIR}/fgo_traj.tum", "w") as f:
    for row in traj:
        q = euler_to_quat(row[4], row[5], row[6])
        f.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f} {row[3]:.6f} {q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}\n")
with open(f"{OUTDIR}/ground_truth.tum", "w") as f:
    for g in gt:
        f.write(f"{g[0]:.6f} {g[1]:.6f} {g[2]:.6f} {g[3]:.6f} 0 0 0 1\n")

# apparatus metrics (cruise window from GT speed, origin gauge-fix, no alignment)
t_u = traj[:, 0]
gE = np.interp(t_u, gt[:, 0], gt[:, 1]); gN = np.interp(t_u, gt[:, 0], gt[:, 2])
sp = np.convolve(np.hypot(np.gradient(gE), np.gradient(gN))/np.gradient(t_u), np.ones(25)/25, mode="same")
cr = sp > 0.30; bi = bj = 0; i = 0
while i < len(cr):
    if cr[i]:
        j = i
        while j < len(cr) and cr[j]: j += 1
        if j-i > bj-bi: bi, bj = i, j
        i = j
    else: i += 1
w = slice(bi, bj)
duE = traj[w, 1]-traj[bi, 1]; duN = traj[w, 2]-traj[bi, 2]
dgE = gE[w]-gE[bi]; dgN = gN[w]-gN[bi]
ate = float(np.sqrt(np.mean((duE-dgE)**2 + (duN-dgN)**2)))
along = float(math.hypot(duE[-1], duN[-1])); true_travel = float(math.hypot(dgE[-1], dgN[-1]))
cross = float((duE-dgE)[-1])
yaw_w = np.unwrap(traj[w, 6]); tt_w = traj[w, 0]
yaw_drift = math.degrees(np.polyfit(tt_w-tt_w[0], yaw_w, 1)[0]) * 60.0
# gyro-z bias vs INSTANTANEOUS true bias (triangle wave, sitl_gyro_drift; NOT the old
# constant 9.8). B is a rate (rad/s) -> deg/min. Report bias% + ramp-tracking.
bgz_series = np.degrees(traj[w, 7]) * 60.0                 # est bias per keyframe, deg/min (FLU)
bgz_mean = float(np.mean(bgz_series))
tt_bmin = (traj[w, 0] - traj[w, 0][0]) / 60.0
true_bias = sitl_gyro_drift(traj[w, 0])                    # instantaneous true |bias| deg/min
true_mean = float(np.mean(true_bias))
bgz_frac = 100.0 * abs(bgz_mean) / true_mean
est_slope = float(np.polyfit(tt_bmin, np.abs(bgz_series), 1)[0])   # ramp d|b|/dt, deg/min per min
true_slope = float(np.polyfit(tt_bmin, true_bias, 1)[0])
np.savetxt(f"{OUTDIR}/bgz_series.txt",
           np.column_stack([traj[w, 0], np.abs(bgz_series), true_bias]),
           header="t_sec  est_bias_absdpm  true_bias_dpm", comments="# ")
step_ms = np.array(step_ns)/1e6

print(f"[ground-proximity] flows replaced {gp.n_replaced}; take-off detected {gp.takeoff} at t {gp.t_takeoff}; arm t {gp.t_arm}")
print(f"[run] {n_kf} keyframes, window t=[{t_u[bi]:.0f},{t_u[bj-1]:.0f}]s   "
      f"flow factors {fgo.n_flow}  range factors {fgo.n_range}  imu {fgo.n_imu}")
print(f"[timing] per-keyframe update: median={np.median(step_ms):.1f}ms  p99={np.percentile(step_ms,99):.1f}ms  "
      f"(deployability budget 33ms)")
print(f"[yaw-cap gate] fired {fgo.n_yaw_fire}/{fgo.n_yaw_check} checks (trace(P_att) > {_fc.ATT_VAR_GATE}, "
      f"every {_fc.YAW_DT} s; FGO_DESIGN §9.4)")
print(f"[yaw] drift = {yaw_drift:+.2f} deg/min   (physical 9.8; EKF3 ~8.4; UKF-Euler 12.7)")
print(f"[gyro-z bias] cruise mean = {bgz_mean:+.2f} deg/min  ({bgz_frac:.0f}% of true mean "
      f"{true_mean:.1f})   ramp d|b|/dt = {est_slope:+.2f} vs true {true_slope:+.2f} deg/min/min (ideal 3.00)")
print(f"[result] along-track = {along:.1f} m (true {true_travel:.1f})  cross-track = {cross:+.1f} m  ATE = {ate:.2f} m")
vmag = np.array(vmag); fresid = np.array(fresid)
vw = (vmag[:, 0] > t_u[bi]) & (vmag[:, 0] < t_u[bj-1])
fw = (fresid[:, 0] > t_u[bi]) & (fresid[:, 0] < t_u[bj-1])
print(f"[scale] cruise |V(k)| median = {np.median(vmag[vw,1]):.4f} m/s   (true ~0.50; EKF3 ~0.556)")
print(f"[flow resid] cruise median (pred-meas): x={np.median(fresid[fw,1]):+.4f}  y={np.median(fresid[fw,2]):+.4f} rad/s "
      f"(systematic != 0 => FGO not tracking flow)")
print(f"[out] {OUTDIR}/fgo_traj.tum")
with open(f"{OUTDIR}/metrics.txt", "w") as f:
    f.write(f"along_pN={duN[-1]:.3f}\ntrue_travel={true_travel:.3f}\ncross_track={cross:.3f}\n"
            f"ate_apparatus={ate:.3f}\nyaw_drift={yaw_drift:.3f}\nbgz_mean={bgz_mean:.3f}\n"
            f"bgz_pct={bgz_frac:.1f}\ntrue_bias_mean={true_mean:.3f}\nbgz_ramp={est_slope:.3f}\ntrue_ramp={true_slope:.3f}\n"
            f"n_flow={fgo.n_flow}\nn_range={fgo.n_range}\nn_kf={n_kf}\n"
            f"step_median_ms={np.median(step_ms):.3f}\nstep_p99_ms={np.percentile(step_ms,99):.3f}\n")


# ---- F2 (offline, F_BATCH): ONE batch LM over every factor the live smoother received ----
if FV["F_BATCH"]:
    import time as _t
    import gtsam
    from gtsam.symbol_shorthand import X as _X
    t0b = _t.perf_counter()
    prm = gtsam.LevenbergMarquardtParams(); prm.setMaxIterations(50); prm.setRelativeErrorTol(1e-6)
    init_vals = gtsam.Values()
    for key, val in fgo.all_est.items():
        init_vals.insert(key, val)
    opt = gtsam.LevenbergMarquardtOptimizer(fgo.all_g, init_vals, prm)
    res = opt.optimize()
    with open(f"{OUTDIR}/fgo_batch_traj.tum", "w") as f:
        for kk, tk in fgo.key_t:
            key = _X(kk)
            if not res.exists(key):
                continue
            p_ = res.atPose3(key); rpy = p_.rotation().rpy(); q = euler_to_quat(rpy[0], rpy[1], rpy[2])
            f.write(f"{tk:.6f} {p_.x():.6f} {p_.y():.6f} {p_.z():.6f} {q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}\n")
    print(f"[batch] {fgo.all_g.size()} factors, error {opt.error():.3f}, {opt.iterations()} iterations, "
          f"{_t.perf_counter() - t0b:.1f} s")
