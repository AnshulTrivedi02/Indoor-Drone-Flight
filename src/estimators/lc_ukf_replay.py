#!/usr/bin/env python3
"""E5 (tier-1 extension experiment, pre-registered): "UKF with tag landmarks (loop closure)", labelled SEPARATELY from
the thesis UKF. Harness around ukf_lm.py (the variable-size core). Design: docs/thesis/tier1/e5_design.md (signed off
2026-10-22, with amendment 5); pre-registration: docs/thesis/tier1/preregistration.md §4.

Runs in ~/venv-evo (numpy 2.x, rosbags; the venv that produced the stored room_ukf tracks). No gtsam.

TASKS (exactly one):
  --mode lc | nolc       RESULT runs (e5_design §2-§7). /tags/raw, every central-third detection (lc_fgo_replay.py's
                         rule and constants); the thesis UKF until the first central gauge-tag (0) detection; then
                         re-anchor to it (tag 0 = origin, held EXACT, not augmented; §5.2), landmarks augmented on first
                         sighting (unscented, with cross-covariance; not fused again, §3c), later sightings fused
                         (sequential-scalar, tag frame, no gate, §4); lc = one landmark per id, nolc = one per pass
                         (> PASS_GAP_S on the FGO's keyframe time base, §5.3) with finished passes marginalised (§6).
                         Cut at anchor + --t-max (245) s. Output <out-root>/<trial>/lc_ukf_<mode>_t245/
                         {live.tum, hindsight.tum, stats.json, gate_log.npz}; scored by
                         eval/l_score.py --in-root ~/thesis_data/tier1 --prefix lc_ukf --suffix _t245.
                         Invariants (§5.3; a failure stops E5 before scoring, exit 3): t_anchor and the landmark (pass)
                         count equal the stored FGO run's (~/thesis_data/trials/<trial>/lc_fgo_<mode>_t245/stats.json,
                         read only).
  --validate world       V-E5a (§8.3): this harness with ukf_core's filter ONLY (predict/predict_rts, update_flow,
                         update_range, update_yaw_pseudo, update_tag, rts_smooth); /tags/sent world fixes; uncut.
  --validate known-map   V-E5b: /tags/sent fixes converted to tag-relative measurements with the TRUE map pose of the
                         reported id; ukf_lm's tag-frame update against landmarks FIXED at the map; uncut.
  --validate augmented   V-E5c: as V-E5b, each landmark augmented into the state at its first fix AT the true map with
                         variance 1e-10 (m^2, rad^2), then (that fix included) fused against the in-state landmark.
                         The anchoring fix is a world re-anchor in all three (room_ukf_replay.py:180-183).
                         Validation output <out-root>/<trial>/lc_ukf_val_{world,knownmap,augmented}/
                         {ukf_live.tum, ukf_rts.tum, stats.json, gate_log.npz}; judged by eval/e5_val_compare.py
                         against the stored ~/thesis_data/trials/<trial>/room_ukf/ (§8.4).
Options: --out-root DIR (default ~/thesis_data/tier1; must be under it, tier1_paths.resolve_out: never under
~/thesis_data/trials, no overwrite of a non-empty directory), --t-max S (result runs; default 245),
--tag-update sequential|joint (default sequential, DECIDED §10.4; joint is the design's alternative, never used by a
pre-registered run).
Not read (unlike room_ukf_replay.py): ROOM_TAG_SIGMA_POS, ROOM_TAG_MAX, ROOM_TAG_SKIP, UKF_APIN, UKF_OUT_ROOT. The tag
noise is measurement_models.TAG_SIGMA_POS / TAG_SIGMA_YAW (0.05 m, 5 deg), as both stored references.

Validation and result loops follow room_ukf_replay.py:127-186 line for line (init, IMU gap rule, dejitter, DT_STEP,
ground-proximity flow rule, bias-corrected flow derotation, pseudo-yaw before the anchor only, the live row after each
predict step, the RTS node chain from the re-anchor on).
Usage: lc_ukf_replay.py <trial> (--mode lc|nolc | --validate world|known-map|augmented) [--out-root DIR] [--t-max S]"""
import sys, os, glob, math, json, time, argparse, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "fgo"), os.path.join(HERE, "..", "tags")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import ukf_core as U
import ukf_lm as LM
from imu_timing import dejitter_imu, apply_gap_rule
from measurement_models import (FlowFrameGyroAverager, GroundProximityFlow, TAG_SIGMA_POS, TAG_SIGMA_YAW,
                                reanchor_jacobian, N as NV, BG_SLICE)
import tier1_paths as T1
import tag_measure as TM

PASS_GAP_S = 1.0                                   # lc_fgo_replay.py:60
KF_DT = 1.0 / 30.0                                 # the FGO's keyframe period (lc_fgo_replay.py:179, :310)
FX, CX, CY = 554.3827056884766, 320.0, 240.0       # lc_fgo_replay.py:80
R_VALID = (1.0 / 3.0) * math.hypot(CX, CY)
TARGET_DT = 0.0125                                 # room_ukf_replay.py:111
GAUGE = 0
VAL_AUG_VAR = 1e-10                                # V-E5c landmark variance at the true map (§8.3)
ORIGIN_TAG = {"p": np.zeros(3), "yaw": 0.0}
MAP_PATH = os.path.join(HERE, "..", "..", "sim", "worlds", "room_tags_map.json")
VAL_DIR = {"world": "world", "known-map": "knownmap", "augmented": "augmented"}   # e5_design §1
STORE_SPILL_BYTES = 4 * 1024 ** 3                  # §7: above 4 GB the RTS nodes go to np.memmap files


# ---------------------------------------------------------------- inputs
def quat_to_R(w, x, y, z):
    """Eigen's Quaterniond::toRotationMatrix (no normalisation), i.e. what gtsam.Rot3.Quaternion(w, x, y, z).matrix()
    returns in lc_fgo_replay.py:112 (checked equal to 0 on 2000 random, incl. non-unit, quaternions, 2026-10-22)."""
    tx, ty, tz = 2 * x, 2 * y, 2 * z
    twx, twy, twz = tx * w, ty * w, tz * w
    txx, txy, txz = tx * x, ty * x, tz * x
    tyy, tyz, tzz = ty * y, tz * y, tz * z
    return np.array([[1 - (tyy + tzz), txy - twz, txz + twy],
                     [txy + twz, 1 - (txx + tzz), tyz - twx],
                     [txz - twy, tyz + twx, 1 - (txx + tyy)]])


def central_tagrel(tid, t_ct, q_wxyz):
    """lc_fgo_replay.py:110-123 without the tier-1 filters: None if outside the central third, else (tid, mx, my, myaw),
    the vehicle (x, y, yaw) in that tag's frame."""
    u, v = FX * t_ct[0] / t_ct[2] + CX, FX * t_ct[1] / t_ct[2] + CY
    if math.hypot(u - CX, v - CY) > R_VALID:
        return None
    p_tb, R_tb = TM.vehicle_pose(ORIGIN_TAG, quat_to_R(*q_wxyz), np.asarray(t_ct, float))
    return (tid, float(p_tb[0]), float(p_tb[1]), TM.yaw_of(R_tb))


def read_events(bag, tag_topic):
    """Bag events in bag order, as room_ukf_replay.read_events (tag_topic /tags/sent) or lc_fgo_replay.py:93-124
    (/tags/raw, central third). Ground truth is never read."""
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore, get_types_from_msg
    ts = get_typestore(Stores.ROS2_JAZZY)
    msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
    ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
    stamp = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
    ev = []; n_raw = n_central = 0
    with Reader(bag) as r:
        conns = {c.topic: c for c in r.connections}
        want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates", tag_topic]
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
                ev.append((tt, "tag", (m.pose.pose.position.x, m.pose.pose.position.y, 2 * math.atan2(q.z, q.w),
                                       int(m.header.frame_id.split("_")[1]))))
            else:                                            # /tags/raw
                n_raw += 1
                q = m.pose.orientation
                d_ = central_tagrel(int(m.header.frame_id.split("_")[1]),
                                    (m.pose.position.x, m.pose.position.y, m.pose.position.z), (q.w, q.x, q.y, q.z))
                if d_ is None:
                    continue
                n_central += 1
                ev.append((tt, "tagrel", d_))
    return ev, n_raw, n_central


# ---------------------------------------------------------------- book-keeping (result runs)
class KeyframeClock:
    """The FGO's keyframe clock (lc_fgo_replay.py:179, :294, :310): t_init + k/30, advanced by IMU events at or after
    t_init with `while tt >= t_next: ...; t_next += 1/30`."""
    def __init__(self, t_init):
        self.t_next = t_init + KF_DT

    def advance(self, tt):
        fired = 0
        while tt >= self.t_next:
            fired += 1
            self.t_next += KF_DT
        return fired


def keyframe_prepass(ev, t_init, gauge, t_max):
    """Replays lc_fgo_replay.py's main-loop control flow (:267-310) for the tag detections only. Returns
    (anchor event index, t_anchor, labels) with labels[i] = the keyframe time detection i is attached to in the FGO
    (the pass rule's time base, §5.3), or None if its keyframe never ran before the cut (never a factor; excluded).
    Pending detections are attached to the FIRST keyframe of the next firing loop; later keyframes of the same loop
    have none pending, so the FGO's `pim.deltaTij() <= 0` early return cannot drop a detection."""
    clock = KeyframeClock(t_init)
    i_anchor = t_anchor = None; pend = []; labels = {}
    for i, (tt, kind, d) in enumerate(ev):
        if t_max is not None and t_anchor is not None and tt > t_anchor + t_max:
            break
        if tt < t_init:
            continue
        if kind == "tagrel":
            if t_anchor is None:
                if d[0] == gauge:
                    i_anchor, t_anchor = i, tt; pend = [i]
            else:
                pend.append(i)
        elif kind == "imu":
            while tt >= clock.t_next:
                for j in pend:
                    labels[j] = clock.t_next
                pend = []
                clock.t_next += KF_DT
    for j in pend:
        labels[j] = None
    return i_anchor, t_anchor, labels


class PassBook:
    """Landmark keys exactly as lc_fgo_replay.landmark_key (:219-225) on the keyframe time base: lc = one key per id,
    nolc = a new key when label - last_seen[id] > PASS_GAP_S. Key 0 is the gauge tag's first pass (the anchoring
    detection): held EXACT at the origin (§5.2), never in the state; in lc every gauge sighting is key 0."""
    def __init__(self, mode):
        assert mode in ("lc", "nolc")
        self.mode = mode; self.cur = {}; self.last_seen = {}; self.n_keys = 0; self.key_tid = {}

    def on_detection(self, tid, label):
        new = tid not in self.cur or (self.mode == "nolc" and label - self.last_seen[tid] > PASS_GAP_S)
        if new:
            self.cur[tid] = self.n_keys; self.key_tid[self.n_keys] = tid; self.n_keys += 1
        self.last_seen[tid] = label
        return self.cur[tid], new

    def finished(self, t_now, keys):
        """Keys among `keys` whose pass has ended: no longer current for their id, or (nolc) t_now - last sighting
        > PASS_GAP_S, so any later sighting (label >= t_now) would open a new pass. lc: never."""
        if self.mode == "lc":
            return []
        out = []
        for k in keys:
            tid = self.key_tid[k]
            if self.cur.get(tid) != k or t_now - self.last_seen[tid] > PASS_GAP_S:
                out.append(k)
        return out


class LandmarkLayout:
    """Which keys are in the state, in order of first sighting (§3): key -> slot; slot k occupies NV + 3k .. NV + 3k + 3."""
    def __init__(self):
        self.keys = []

    def i0(self, key):
        return NV + 3 * self.keys.index(key)

    def ang(self):
        return LM.ang_indices(len(self.keys))


# ---------------------------------------------------------------- RTS node store (§7)
class NodeStore:
    """RTS transition nodes (xf, Pf, ang_f, xp, Pp, D, ang_p) held in RAM; above `spill_bytes` the arrays of further
    nodes are appended to <dir>/rts_nodes.bin and read back through np.memmap (§7)."""
    def __init__(self, spill_dir, spill_bytes=STORE_SPILL_BYTES):
        self.nodes = []; self.bytes = 0; self.spill_bytes = spill_bytes; self.spill_dir = spill_dir
        self.f = None; self.off = 0; self.n_spilled = 0

    def add(self, xf, Pf, ang_f, xp, Pp, D, ang_p):
        arrs = (xf, Pf, xp, Pp, D)
        nb = sum(a.nbytes for a in arrs)
        if self.bytes + nb <= self.spill_bytes:
            self.nodes.append(("ram", (xf.copy(), Pf.copy(), xp.copy(), Pp.copy(), D.copy()), ang_f, ang_p))
        else:
            if self.f is None:
                self.path = os.path.join(self.spill_dir, "rts_nodes.bin"); self.f = open(self.path, "wb")
            meta = []
            for a in arrs:
                a = np.ascontiguousarray(a, dtype=np.float64); self.f.write(a.tobytes()); meta.append((self.off, a.shape))
                self.off += a.nbytes
            self.nodes.append(("disk", meta, ang_f, ang_p)); self.n_spilled += 1
        self.bytes += nb

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, k):
        where, data, ang_f, ang_p = self.nodes[k]
        if where == "ram":
            xf, Pf, xp, Pp, D = data
        else:
            if self.f is not None:
                self.f.flush()
            xf, Pf, xp, Pp, D = (np.array(np.memmap(self.path, dtype=np.float64, mode="r", offset=o, shape=s)) for o, s in data)
        return xf, Pf, ang_f, xp, Pp, D, ang_p

    def close(self):
        if self.f is not None:
            self.f.close(); self.f = None


class _NodeView:
    """Sequence view for LM.rts_backward."""
    def __init__(self, store):
        self.s = store

    def __len__(self):
        return len(self.s)

    def __getitem__(self, k):
        return self.s[k]


# ---------------------------------------------------------------- gate log (§8.4 condition 5)
class GateLog:
    """(t, code, testRatio, accepted) for every GATED flow-axis (code 0 = X, 1 = Y) and range (code 2) decision."""
    def __init__(self):
        self.rows = []

    def add(self, t, code, test, acc):
        self.rows.append((t, code, test, bool(acc)))

    def counts(self):
        c = {}
        for name, code in (("flow_x", 0), ("flow_y", 1), ("range", 2)):
            r = [row for row in self.rows if row[1] == code]
            c[name] = {"accepted": sum(1 for row in r if row[3]), "rejected": sum(1 for row in r if not row[3])}
        return c

    def save(self, path):
        a = np.array([(r[0], r[1], r[2], r[3]) for r in self.rows], dtype=float).reshape(-1, 4)
        np.savez_compressed(path, t=a[:, 0], code=a[:, 1].astype(int), test=a[:, 2], accepted=a[:, 3].astype(bool))


class _CoreScalarRecorder:
    """V-E5a: ukf_core.update_flow / update_range do not return their test ratios. This wrapper around
    ukf_core._update_scalar (resolved through the module global at call time) records (test, accepted) and returns the
    original's result unchanged, so the state path is exactly ukf_core's."""
    def __init__(self):
        self.orig = U._update_scalar; self.buf = []

    def __call__(self, *a, **k):
        res = self.orig(*a, **k)
        self.buf.append((res[3], res[2]))
        return res

    def install(self):
        U._update_scalar = self

    def uninstall(self):
        U._update_scalar = self.orig


# ---------------------------------------------------------------- helpers
def reanchor(x, P, p_EN, yaw):
    """room_ukf_replay.py:181-182: re-anchor to the fix; P <- diag(J P J^T), x, y, yaw variances = the tag noise."""
    x, J = reanchor_jacobian(x, p_EN, yaw)
    P = np.diag(np.diag(J @ P @ J.T)); P[0, 0] = P[1, 1] = TAG_SIGMA_POS ** 2; P[8, 8] = TAG_SIGMA_YAW ** 2
    return x, P


def world_to_tagrel(pE, pN, yaw, tag):
    """V-E5b/c: a world fix as the vehicle (x, y, yaw) in the frame of a tag at its TRUE map pose."""
    c, s = math.cos(tag["yaw"]), math.sin(tag["yaw"]); dx, dy = pE - tag["p"][0], pN - tag["p"][1]
    return (c * dx + s * dy, -s * dx + c * dy, float(U._wrap(yaw - tag["yaw"])))


def euler_to_quat(r, pch, y):
    cr, sr = np.cos(r/2), np.sin(r/2); cp, sp = np.cos(pch/2), np.sin(pch/2); cy, sy = np.cos(y/2), np.sin(y/2)
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy)


def write_tum(path, T, X):
    """room_ukf_replay.write_tum (6 dp)."""
    with open(path, "w") as f:
        for t, x in zip(T, X):
            q = euler_to_quat(x[6], x[7], x[8])
            f.write(f"{t:.6f} {x[0]:.6f} {x[1]:.6f} {x[2]:.6f} {q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}\n")


def provenance():
    g = lambda *c: subprocess.run(["git", "-C", HERE, *c], capture_output=True, text=True).stdout.strip()
    return {"argv": sys.argv, "commit": g("rev-parse", "HEAD"), "src_dirty": g("status", "--porcelain", "--", ".."),
            "python": sys.executable, "numpy": np.__version__}


# ---------------------------------------------------------------- the replay
def run(trial, task, out_root, t_max=245.0, tag_update="sequential"):
    RESULT = task in ("lc", "nolc"); CORE = task == "world"
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    base = f"lc_ukf_{task}_t{int(t_max)}" if RESULT else "lc_ukf_val_" + VAL_DIR[task]
    OUT = T1.resolve_out(trial, base, out_root)
    t_wall0 = time.perf_counter()
    ev, n_raw, n_central = read_events(f"{D}/bag", "/tags/raw" if RESULT else "/tags/sent")
    ev = apply_gap_rule(ev, trial); ev, dj = dejitter_imu(ev); ev.sort(key=lambda e: e[0])
    period = dj['period_ms'] / 1e3
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
    tag_map = TM.load_map(MAP_PATH)
    omega = np.zeros(3); t_prev = t_init; t_yaw = t_init
    da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
    anchored = False; t_anchor = None; n_tag = 0; n_yaw_fire = 0
    live_t, live_x = [], []
    glog = GateLog()
    lay = LandmarkLayout()
    store = NodeStore(OUT)
    pred_nodes, pred_t = [], []                        # store index of every predict node, and its time
    xa, Pa, xp, Pp, Dc, node_t = [], [], [], [], [], []   # V-E5a: room_ukf_replay's own RTS records
    n_aug = n_upd_tag = n_drop = n_excl_cut = n_ignored_pre = 0; n_max = NV; drops = []
    if RESULT:
        i_anchor, t_anchor_pre, labels = keyframe_prepass(ev, t_init, GAUGE, t_max)
        clock = KeyframeClock(t_init); book = PassBook(task)
        if i_anchor is None:
            raise SystemExit(f"{trial}: no central gauge-tag detection after t_init; no anchor")
    rec = None
    if CORE:
        rec = _CoreScalarRecorder(); rec.install()

    def add_node(xf, Pf, ang_f, xp_, Pp_, D_, ang_p):
        store.add(xf, Pf, ang_f, xp_, Pp_, D_, ang_p)

    def drop_finished(t_now):
        nonlocal x, P, n_drop
        for k in book.finished(t_now, list(lay.keys)):
            i0 = lay.i0(k); ang_f = lay.ang()
            xn, Pn, Dn = LM.remove_block(x, P, i0)
            lay.keys.remove(k)
            add_node(x, P, ang_f, xn, Pn, Dn, lay.ang()); x, P = xn, Pn; n_drop += 1; drops.append((t_now, int(k)))

    try:
        for ie, (t, kind, d) in enumerate(ev):
            if RESULT and anchored and t > t_anchor + t_max:
                break                                                      # lc_fgo_replay.py:268-269
            if t < t_init:
                if kind == "att":
                    omega = d
                continue
            if kind == "att":
                omega = d
            elif kind == "imu":
                if RESULT:
                    clock.advance(t)
                gp.on_gyro(t, d[1], x[BG_SLICE] / DT_STEP); gyro_avg.push(t, d[1])
                dt_i = t - t_prev; t_prev = t
                if dt_i <= 0 or dt_i > 0.2:
                    continue
                da += d[1] * dt_i; dv += d[0] * dt_i; acc_dt += dt_i
                if acc_dt >= TARGET_DT - 1e-9:
                    if CORE:
                        if anchored:
                            node_t.append(t); xa.append(x.copy()); Pa.append(P.copy())
                            x, P, Dk = U.predict_rts(x, P, da, dv, p, dt=acc_dt)
                            xp.append(x.copy()); Pp.append(P.copy()); Dc.append(Dk)
                        else:
                            x, P = U.predict(x, P, da, dv, p, dt=acc_dt)
                        if not anchored and t - t_yaw >= p['YAW_DT']:
                            x, P, fired = U.update_yaw_pseudo(x, P, p); n_yaw_fire += fired; t_yaw = t
                    else:
                        if RESULT and anchored and task == "nolc":
                            drop_finished(clock.t_next)
                        ang = lay.ang()
                        xn, Pn, Dk = LM.predict(x, P, da, dv, p, ang, dt=acc_dt)
                        if anchored:
                            add_node(x, P, ang, xn, Pn, Dk, ang); pred_nodes.append(len(store) - 1); pred_t.append(t)
                        x, P = xn, Pn
                        if not anchored and t - t_yaw >= p['YAW_DT']:
                            x, P, fired = LM.update_yaw_pseudo(x, P, p, ang); n_yaw_fire += fired; t_yaw = t
                    live_t.append(t); live_x.append(x[:NV].copy())
                    da = np.zeros(3); dv = np.zeros(3); acc_dt = 0.0
            elif kind == "rng":
                gp.on_range(t, d)
                if CORE:
                    rec.buf = []
                    x, P, acc = U.update_range(x, P, d, p)
                    if rec.buf:
                        assert len(rec.buf) == 1 and rec.buf[0][1] == acc; glog.add(t, 2, rec.buf[0][0], acc)
                else:
                    x, P, acc, tr = LM.update_range(x, P, d, p, lay.ang())
                    if tr is not None:
                        glog.add(t, 2, tr, acc)
            elif kind == "flow":
                flow_xy, valid, inlier = d[:3]
                om = gyro_avg.average(t, omega)
                om = om - x[BG_SLICE] / DT_STEP                  # room_ukf_replay.py:159 (bias-corrected derotation)
                if valid and inlier > 0:
                    flow_xy = gp.replace(flow_xy, om, x[6], x[7])
                if CORE:
                    rec.buf = []
                    x, P, acc = U.update_flow(x, P, flow_xy, om, valid, inlier, p)
                    if rec.buf:
                        assert len(rec.buf) == 2 and tuple(b[1] for b in rec.buf) == tuple(acc)
                        for ax in (0, 1):
                            glog.add(t, ax, rec.buf[ax][0], acc[ax])
                else:
                    x, P, acc, trs = LM.update_flow(x, P, flow_xy, om, valid, inlier, p, lay.ang())
                    if trs[0] is not None:
                        for ax in (0, 1):
                            glog.add(t, ax, trs[ax], acc[ax])
            elif kind == "tag":                                          # validation runs: /tags/sent world fixes
                pE, pN, yaw, tid = d
                if not anchored:
                    x, P = reanchor(x, P, (pE, pN), yaw)
                    anchored = True; t_anchor = t
                    if task == "augmented":
                        ang_f = lay.ang(); m = tag_map[tid]
                        xn, Pn, Dn = LM.augment_fixed(x, P, (m["p"][0], m["p"][1], m["yaw"]), VAL_AUG_VAR)
                        lay.keys.append(tid); add_node(x, P, ang_f, xn, Pn, Dn, lay.ang()); x, P = xn, Pn; n_aug += 1
                else:
                    if CORE:
                        x, P = U.update_tag(x, P, (pE, pN, yaw), TAG_SIGMA_POS, TAG_SIGMA_YAW, p)
                    else:
                        m = tag_map[tid]; z = world_to_tagrel(pE, pN, yaw, m)
                        if task == "known-map":
                            lm = ("fixed", (m["p"][0], m["p"][1], m["yaw"]))
                        else:
                            if tid not in lay.keys:
                                ang_f = lay.ang()
                                xn, Pn, Dn = LM.augment_fixed(x, P, (m["p"][0], m["p"][1], m["yaw"]), VAL_AUG_VAR)
                                lay.keys.append(tid); add_node(x, P, ang_f, xn, Pn, Dn, lay.ang()); x, P = xn, Pn
                                n_aug += 1
                            lm = ("state", lay.i0(tid))
                        x, P = LM.update_tag_rel(x, P, z, TAG_SIGMA_POS, TAG_SIGMA_YAW, p, lay.ang(), lm, tag_update)
                        n_upd_tag += 1
                n_tag += 1
            elif kind == "tagrel":                                       # result runs: /tags/raw, tag-relative
                tid, mx, my, myaw = d
                if not anchored:
                    if ie != i_anchor:
                        n_ignored_pre += 1
                        continue
                    lab = labels[ie]
                    assert lab is not None and lab == clock.t_next, "keyframe label mismatch at the anchor"
                    x, P = reanchor(x, P, (mx, my), myaw)
                    anchored = True; t_anchor = t
                    k, new = book.on_detection(tid, lab)
                    assert k == 0 and new
                    n_tag += 1
                    continue
                lab = labels.get(ie)
                if lab is None:
                    n_excl_cut += 1                                      # its keyframe never ran: never a factor
                    continue
                assert lab == clock.t_next, "keyframe label mismatch"
                if task == "nolc":
                    drop_finished(lab)
                k, new = book.on_detection(tid, lab)
                if k == 0:                                               # gauge first pass (nolc) / gauge (lc): EXACT
                    x, P = LM.update_tag_rel(x, P, (mx, my, myaw), TAG_SIGMA_POS, TAG_SIGMA_YAW, p, lay.ang(),
                                             ("fixed", (0.0, 0.0, 0.0)), tag_update)
                    n_upd_tag += 1
                elif new:                                                # first sighting: augment, NOT fused (§3c)
                    ang_f = lay.ang()
                    xn, Pn, Dn = LM.augment_unscented(x, P, (mx, my, myaw),
                                                      np.diag([TAG_SIGMA_POS ** 2, TAG_SIGMA_POS ** 2, TAG_SIGMA_YAW ** 2]),
                                                      p, ang_f)
                    lay.keys.append(k); add_node(x, P, ang_f, xn, Pn, Dn, lay.ang()); x, P = xn, Pn; n_aug += 1
                else:
                    x, P = LM.update_tag_rel(x, P, (mx, my, myaw), TAG_SIGMA_POS, TAG_SIGMA_YAW, p, lay.ang(),
                                             ("state", lay.i0(k)), tag_update)
                    n_upd_tag += 1
                n_tag += 1
            n_max = max(n_max, x.shape[0])
    finally:
        if rec is not None:
            rec.uninstall()

    live_x = np.array(live_x); live_t = np.array(live_t)
    keep = live_t >= (t_anchor if t_anchor is not None else np.inf)    # room_ukf_replay.py:189
    stats = {"task": task, "trial": trial, "t_anchor": t_anchor, "n_tag_fused": n_tag, "dt_step_ms": 1e3 * DT_STEP,
             "pseudo_yaw_fired_before_anchor": int(n_yaw_fire), "tag_sigma_pos": TAG_SIGMA_POS,
             "tag_sigma_yaw_deg": math.degrees(TAG_SIGMA_YAW), "tag_update": tag_update,
             "gate_counts": glog.counts(), "n_landmarks_augmented": n_aug, "n_tag_updates": n_upd_tag,
             "max_state_dim": int(n_max), "imu_dejitter": dj,
             "chol": dict(LM.CHOL_STATS) if not CORE else dict(U.CHOL_STATS)}
    if RESULT:
        stats.update({"mode": task, "t_max": t_max, "gauge_tag": GAUGE, "raw_detections": n_raw, "central": n_central,
                      "landmarks": book.n_keys, "tag_measurements_used": n_tag,
                      "excluded_pending_at_cut": n_excl_cut, "ignored_before_anchor": n_ignored_pre,
                      "landmarks_dropped": n_drop, "landmarks_in_state_at_end": len(lay.keys)})
    trk_live, trk_rts = ("live.tum", "hindsight.tum") if RESULT else ("ukf_live.tum", "ukf_rts.tum")
    write_tum(f"{OUT}/{trk_live}", live_t[keep], live_x[keep])
    if CORE:
        if len(node_t) > 2:                                              # room_ukf_replay.py:193-198
            XA = np.array(xa[1:] + [x]); PA = np.array(Pa[1:] + [P]); XP = np.array(xp); PP = np.array(Pp); DD = np.array(Dc)
            xs, _ = U.rts_smooth(XA, PA, XP, PP, DD)
            write_tum(f"{OUT}/{trk_rts}", np.array(node_t), xs); stats["rts_nodes"] = int(len(xs))
    elif len(pred_nodes) > 2:
        sm, xfin = LM.rts_backward(_NodeView(store), x, P)
        rows = [sm[pred_nodes[i + 1]] for i in range(len(pred_nodes) - 1)] + [xfin]
        write_tum(f"{OUT}/{trk_rts}", np.array(pred_t), np.array(rows))
        stats.update({"rts_nodes": len(rows), "rts_transition_nodes": len(store), "rts_store_bytes": int(store.bytes),
                      "rts_nodes_spilled_to_memmap": store.n_spilled})
    store.close()
    if RESULT:
        lms = {}
        for k in lay.keys:
            i0 = lay.i0(k); lms[str(k)] = {"tag": int(book.key_tid[k]), "pose": [float(v) for v in x[i0:i0 + 3]]}
        stats["landmarks_in_state_final_filtered"] = lms
        stats["invariants"] = check_invariants(trial, task, t_max, t_anchor, book.n_keys, n_tag)
    stats["gate_log"] = "gate_log.npz"; glog.save(f"{OUT}/gate_log.npz")
    stats["wall_s"] = time.perf_counter() - t_wall0; stats["tier1"] = dict(provenance(), out=OUT)
    json.dump(stats, open(f"{OUT}/stats.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in stats.items() if k not in ("landmarks_in_state_final_filtered", "tier1")}))
    if RESULT and not stats["invariants"]["pass"]:
        print("[E5] INVARIANT FAILURE: E5 stops before scoring (e5_design §5.3)", file=sys.stderr)
        sys.exit(3)
    return OUT, stats


def check_invariants(trial, mode, t_max, t_anchor, n_keys, n_used):
    """§5.3: t_anchor and the landmark (pass) count equal the stored FGO run's; the tag measurements used are reported
    against its landmark_factors (not a stop)."""
    ref = os.path.expanduser(f"~/thesis_data/trials/{trial}/lc_fgo_{mode}_t{int(t_max)}/stats.json")
    if not os.path.exists(ref):
        return {"pass": False, "reason": f"no stored FGO stats {ref}"}
    s = json.load(open(ref))
    inv = {"ref": ref,
           "t_anchor": {"e5": t_anchor, "fgo": s["t_anchor"], "ok": t_anchor == s["t_anchor"]},
           "landmarks": {"e5": n_keys, "fgo": s["landmarks"], "ok": n_keys == s["landmarks"]},
           "tag_measurements_used_vs_landmark_factors (reported, not a stop)": {"e5": n_used, "fgo": s["landmark_factors"]}}
    inv["pass"] = inv["t_anchor"]["ok"] and inv["landmarks"]["ok"]
    return inv


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("trial")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mode", choices=["lc", "nolc"])
    g.add_argument("--validate", choices=["world", "known-map", "augmented"])
    ap.add_argument("--out-root", default=T1.TIER1_DATA_ROOT)
    ap.add_argument("--t-max", type=float, default=245.0)
    ap.add_argument("--tag-update", choices=["sequential", "joint"], default="sequential")
    a = ap.parse_args(argv)
    if a.validate is not None and a.tag_update != "sequential":
        T1.refuse("the V-E5 gates run in sequential-scalar mode (§4, §10.4)")
    task = a.mode if a.mode is not None else a.validate
    run(a.trial, task, os.path.expanduser(a.out_root), t_max=a.t_max, tag_update=a.tag_update)


if __name__ == "__main__":
    main()
