#!/usr/bin/env python3
"""Experiment T: IPLS (iterated posterior linearisation smoother) replay — Stage 1, implement + gates ONLY.

docs/thesis/iterated_smoother/preregistration.md (D152, EXPLORATORY). Reproduces
room_ukf_replay.py's DEFAULT forward pass verbatim (same event handling, same ukf_core
calls, same init/gap-rule/dejitter/ground-proximity-flow/yaw-cap/re-anchor; copied, not
imported, because room_ukf_replay.py runs at top level on import — see its own docstring),
additionally RECORDING the operation sequence (every predict's da/dv/dt, every accepted
measurement's type/value/noise/aux-input, frozen) needed by ukf_ipls.run_ipls.

Refuses: UKF_APIN, ROOM_TAG_SIGMA_POS, ROOM_TAG_MAX, ROOM_TAG_SKIP, UKF_OUT_ROOT (any set),
--gnss, --rts-no-yawcap, --no-rts, --tag-map (any passed) — this stage is the plain T
default path only, no tier-1/E6/diagnostic variants, no GNSS experiment O.

Output (ALWAYS under the trial directory; no redirect support, by design — never
overwrites room_ukf/, a different directory):
  ~/thesis_data/trials/<trial>/room_ukf_ipls/
    ukf_live_check.tum   the forward (live) track, for G1 (diff against room_ukf/ukf_live.tum)
    ukf_ipls_iter0.tum   iteration 0 = ukf_core.rts_smooth on the recorded arrays,
                         bitwise == room_ukf/ukf_rts.tum by construction; for G2
    ukf_ipls.tum         the FINAL iterated track (converged, or iteration max_iter)
    stats.json           t_anchor, n_tag_fused, dt_step_ms, tag_sigma_pos (must match the
                         stored room_ukf/stats.json — a pre-check, not part of G1/G2 itself),
                         iterations, converged, per-iteration cost/max_change_m/chol deltas,
                         run time, interpreter, numpy version, git commit, src_dirty
Usage: room_ukf_ipls_replay.py <trial> [--max-iter N] [--tol-mm X]
"""
import sys, os, glob, math, json, time, subprocess
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
import ukf_core as U
import ukf_ipls as IPLS
from imu_timing import dejitter_imu, apply_gap_rule
from measurement_models import FlowFrameGyroAverager, GroundProximityFlow, TAG_SIGMA_POS, TAG_SIGMA_YAW, reanchor_jacobian

REFUSED_ENV = ("UKF_APIN", "ROOM_TAG_SIGMA_POS", "ROOM_TAG_MAX", "ROOM_TAG_SKIP", "UKF_OUT_ROOT")
REFUSED_FLAGS = ("--gnss", "--rts-no-yawcap", "--no-rts", "--tag-map")
_bad_env = [v for v in REFUSED_ENV if os.environ.get(v)]
_bad_flag = [f for f in REFUSED_FLAGS if f in sys.argv]
if _bad_env or _bad_flag:
    sys.exit(f"[ipls] REFUSED: Stage 1 is the plain T default path only; "
              f"unset {_bad_env} / drop {_bad_flag}")

TRIAL = sys.argv[1]
MAX_ITER = int(sys.argv[sys.argv.index("--max-iter") + 1]) if "--max-iter" in sys.argv else 10
TOL_M = float(sys.argv[sys.argv.index("--tol-mm") + 1]) / 1e3 if "--tol-mm" in sys.argv else 1e-3

D = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}")
OUT = f"{D}/room_ukf_ipls"
os.makedirs(OUT, exist_ok=True)
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
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*cy)


def write_tum(path, T, X):
    with open(path, "w") as f:
        for t, x in zip(T, X):
            q = euler_to_quat(x[6], x[7], x[8])
            f.write(f"{t:.6f} {x[0]:.6f} {x[1]:.6f} {x[2]:.6f} {q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}\n")


T0 = time.time()
ev, gt = read_events(f"{D}/bag")
ev = apply_gap_rule(ev, TRIAL)
ev, dj = dejitter_imu(ev)
ev.sort(key=lambda e: e[0])
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
anchored = False; t_anchor = None; n_tag = 0; n_yaw_fire = 0

# --- IPLS recording state. ONLY active from the re-anchor's FIRST PREDICT on: V_0 (anchor_m/
# anchor_P) is captured right before that first predict_rts call, matching room_ukf_replay.py's
# own xa[0] (raw) EXACTLY -- which already bakes in any rng/flow/tag updates that land between
# the re-anchor event and the first predict (same code path as any other update, in the original).
# Those updates are therefore NOT recorded as ops (nothing to re-linearise: they are inside the
# fixed V_0, never iterated), gated by `chain_started` below.
anchor_m = anchor_P = None
chain_started = False
predict_ops = []          # [(da, dv, dt), ...] length n
batch_ops = []             # [[op, ...], ...] length n; op = (kind, z, R, aux)
cur_batch = []             # ops accumulated since the last predict (becomes batch_ops[-1] at the NEXT predict)
node_t, xa, Pa, xp, Pp, Dc = [], [], [], [], [], []      # same construction as room_ukf_replay.py (for G1/G2)
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
                if not chain_started:                # THIS predict is the first since the re-anchor: x,P right
                    anchor_m, anchor_P = x.copy(), P.copy()  # now == xa[0] raw, baking in any pre-predict updates
                    chain_started = True
                elif predict_ops:                      # close out the batch belonging to the PREVIOUS node
                    batch_ops.append(cur_batch)
                cur_batch = []
                node_t.append(t); xa.append(x.copy()); Pa.append(P.copy())
                x, P, Dk = U.predict_rts(x, P, da, dv, p, dt=acc_dt)
                xp.append(x.copy()); Pp.append(P.copy()); Dc.append(Dk)
                predict_ops.append((da.copy(), dv.copy(), acc_dt))
            else:
                x, P = U.predict(x, P, da, dv, p, dt=acc_dt)
            if not anchored and t - t_yaw >= p['YAW_DT']:
                x, P, fired = U.update_yaw_pseudo(x, P, p); n_yaw_fire += fired; t_yaw = t
            live_t.append(t); live_x.append(x.copy())
            da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
    elif kind == "rng":
        gp.on_range(t, d)
        x, P, acc = U.update_range(x, P, d, p)
        if chain_started and acc:
            cur_batch.append(("rng", float(d), p['RNG_M_NSE'] ** 2, None))
    elif kind == "flow":
        flow_xy, valid, inlier = d[:3]
        om = gyro_avg.average(t, omega)
        om = om - x[U.BG_SLICE] / DT_STEP
        if valid and inlier > 0:
            flow_xy = gp.replace(flow_xy, om, x[6], x[7])
        x, P, acc = U.update_flow(x, P, flow_xy, om, valid, inlier, p)
        if chain_started:
            if acc[0]:
                cur_batch.append(("flow_x", float(flow_xy[0]), p['FLOW_M_NSE'] ** 2, om.copy()))
            if acc[1]:
                cur_batch.append(("flow_y", float(flow_xy[1]), p['FLOW_M_NSE'] ** 2, om.copy()))
    elif kind == "tag":
        pE, pN, yaw = d
        if not anchored:
            x, J = reanchor_jacobian(x, (pE, pN), yaw)
            P = np.diag(np.diag(J @ P @ J.T)); P[0, 0] = P[1, 1] = TAG_SIGMA_POS ** 2; P[8, 8] = TAG_SIGMA_YAW ** 2
            anchored = True; t_anchor = t
        else:
            x, P = U.update_tag(x, P, (pE, pN, yaw), TAG_SIGMA_POS, TAG_SIGMA_YAW, p)
            if chain_started:
                cur_batch.append(("tag_pE", float(pE), TAG_SIGMA_POS ** 2, None))
                cur_batch.append(("tag_pN", float(pN), TAG_SIGMA_POS ** 2, None))
                cur_batch.append(("tag_yaw", float(yaw), TAG_SIGMA_YAW ** 2, None))
        n_tag += 1
batch_ops.append(cur_batch)        # the final node's ops (predict n-1 .. end of flight)

live_x = np.array(live_x); live_t = np.array(live_t)
keep = live_t >= (t_anchor if t_anchor is not None else np.inf)
write_tum(f"{OUT}/ukf_live_check.tum", live_t[keep], live_x[keep])

assert len(predict_ops) == len(batch_ops) == len(node_t), \
    f"[ipls] recording length mismatch: predict_ops={len(predict_ops)} batch_ops={len(batch_ops)} node_t={len(node_t)}"
n = len(node_t)
stats = {"t_anchor": t_anchor, "n_tag_fused": n_tag, "pseudo_yaw_fired_before_anchor": int(n_yaw_fire),
         "dt_step_ms": 1e3 * DT_STEP, "tag_sigma_pos": TAG_SIGMA_POS, "tag_sigma_yaw_deg": math.degrees(TAG_SIGMA_YAW),
         "rts_nodes": n, "max_iter": MAX_ITER, "tol_mm": TOL_M * 1e3}

if n <= 2 or anchor_m is None:
    json.dump(stats, open(f"{OUT}/stats.json", "w"), indent=1)
    sys.exit(f"[ipls] {TRIAL}: too few RTS nodes ({n}) or never anchored; nothing to smooth (stats.json written)")

# node i filtered = XA[i]; the prediction FROM node i to node i+1 is XP[i+1] with cross-cov DD[i+1]
# (room_ukf_replay.py's own convention, reused verbatim)
XA_fwd = np.array(xa[1:] + [x]); PA_fwd = np.array(Pa[1:] + [P])
XP_fwd = np.array(xp); PP_fwd = np.array(Pp); DD_fwd = np.array(Dc)

t_pre_ipls = time.time()
Vs, Ps, history, converged = IPLS.run_ipls(anchor_m, anchor_P, predict_ops, batch_ops,
                                           XA_fwd, PA_fwd, XP_fwd, PP_fwd, DD_fwd,
                                           p, max_iter=MAX_ITER, tol_m=TOL_M)
t_ipls = time.time() - t_pre_ipls

# iteration 0's own trajectory (the bypass inside run_ipls): recomputed once more here, cheaply,
# via the IDENTICAL call (same args, same pure function) so ukf_ipls_iter0.tum cannot drift from
# what run_ipls actually used as its own iteration-0 reference.
xs0, _ = U.rts_smooth(XA_fwd, PA_fwd, XP_fwd, PP_fwd, DD_fwd)
write_tum(f"{OUT}/ukf_ipls_iter0.tum", np.array(node_t), xs0)
write_tum(f"{OUT}/ukf_ipls.tum", np.array(node_t), np.array(Vs[1:]))

here = os.path.dirname(os.path.abspath(__file__))
git = lambda *c: subprocess.run(["git", "-C", here, *c], capture_output=True, text=True).stdout.strip()
stats.update({
    "iterations_run": history[-1]["iter"], "converged": converged,
    "history": history,
    "run_time_s_forward_pass": t_pre_ipls - T0, "run_time_s_ipls": t_ipls, "run_time_s_total": time.time() - T0,
    "interpreter": sys.executable, "numpy_version": np.__version__,
    "git_commit": git("rev-parse", "HEAD"), "src_dirty": git("status", "--porcelain", "--", "."),
})
json.dump(stats, open(f"{OUT}/stats.json", "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in stats.items() if k != "history"}, default=str))
print(json.dumps({"history": history}, default=str))
