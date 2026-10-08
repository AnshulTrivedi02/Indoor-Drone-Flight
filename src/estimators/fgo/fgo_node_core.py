"""FGO node core — the CAUSAL wrapper around the unchanged fgo_core.FGO (ruling D7, 2026-09-30).

PURE: no ROS, no bag. The ROS 2 node (fgo_node.py) and the equivalence drivers
(eval/fgo_node_equiv.py) are thin shells around this class, so the code tested offline is the code
that runs live. METHODOLOGY "FGO track (ruling D7) — the ROS-node route".

Events are pushed in ARRIVAL order. The per-event handler (_process) is the fgo_replay.py loop body,
unchanged, so on identical inputs the node reproduces the offline FGO (FGO step 2). The only
intended differences are the causal forms of the offline replay's non-causal steps (FGO step 3):
  (i)  dejitter="causal": IMU receipt stamps are linearised by a RUNNING least-squares fit of stamp
       against sample index (Welford co-moments), the causal form of imu_timing.dejitter_imu's
       whole-flight fit. dejitter="none": stamps are used as given (the offline stream is already
       dejittered).
  (ii) a stamp-ordered queue (stable on ties, like the offline stable sort) released up to
       newest_stamp - horizon_s, in place of sorting the whole bag.
  (iii) gap="causal": a /imu/time_ref sensor-time step > 10 ms (the IMU-gap rule's gap) before the
       vehicle leaves the ground re-initialises (as the rule's trim); after that it sets
       valid = False for the rest of the flight (the rule's "unusable"). gap="off": no detection.
Initialisation as fgo_replay: gravity levelling over the first 0.5 s of IMU, first valid range,
t_init = t_imu0 + 0.5; before t_init only attitude rates are kept.

Experiment H (2026-10-08; docs/h_backends_tag_input.md): tags=True adds the "tag" kind, (E_W, N_W, yaw ENU) from
/tags/sent, handled exactly as room_fgo_replay.py: the first fix after t_init re-anchors (FGO.reanchor with the fix
noise; the gate-only covariance recursion, needed only for the re-anchor prior, is on until then and off after it);
later fixes give a tag factor on the next keyframe (the newest fix since the last keyframe), NO gate; the yaw cap is
off from the re-anchor on (FGO.reanchor sets no_yawcap). tags=False (default): unchanged.
"""
import heapq, itertools, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # measurement_models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                    # fgo_core, factors
from fgo_core import FGO
from measurement_models import FlowFrameGyroAverager, GroundProximityFlow, TAG_SIGMA_YAW

GAP_S = 0.010          # the IMU-gap rule's gap (METHODOLOGY "RULE — IMU gaps and the replay estimators")
AIRBORNE_DZ = 0.30     # "left the ground": range above the initial range by more than this (m)
FLOW_TIMEOUT_S = 5.0   # EKF3's relative-aiding timeout (flowFusionTimeout, AP_NavEKF3_Control.cpp:306), as the UKF rule


class FgoNodeCore:
    def __init__(self, window=0.25, lm_iters=2, fwd_sigma=None, fwd_gate=9.0, horizon_s=0.10,
                 dejitter="causal", gap="causal", t_arm=None, fwd_robust=None, tags=False, tag_sigma_pos=0.02,
                 tag_sigma_yaw=TAG_SIGMA_YAW):
        self.window, self.lm_iters, self.fwd_sigma, self.fwd_gate = window, lm_iters, fwd_sigma, fwd_gate
        # experiment H: tag fixes (room_fgo_replay.py's handling); sigma_pos = the S0 wall-tag sigma (EKF3's
        # VISO_POS_M_NSE 0.02), sigma_yaw = EKF3's 5 deg floor
        self.tags, self.tag_sigma_pos, self.tag_sigma_yaw = tags, tag_sigma_pos, tag_sigma_yaw
        self.n_anchors = 0                     # re-anchors so far (the ODOMETRY reset_counter)
        self.t_anchor = None
        self.anchor_log = []                   # (anchored, n_anchors) per traj row: the frame each keyframe is in
        self.fwd_robust = fwd_robust          # plan step 2(b): e.g. "cauchy:2.385" (the caller sets fwd_gate = inf), as fgo_replay F1
        self.horizon_s, self.dejitter, self.gap = horizon_s, dejitter, gap
        self._q, self._seq, self._newest = [], itertools.count(), -np.inf
        # running dejitter fit (index -> stamp)
        self._n = 0; self._mx = self._my = self._cxx = self._cxy = 0.0
        self._tref_prev = None
        self.gaps_seen = []                    # (sensor t, gap s, airborne) - diagnostics
        self.n_pushed = {}                     # message counts by kind - diagnostics
        self.valid = True                      # validity signal: see valid_now()
        self._gap_invalid = False              # a post-take-off IMU gap (the IMU-gap rule): invalid for good
        self._t_last_flow_fused = None         # keyframe time of the last keyframe that fused a flow factor
        self.valid_log = []                    # (keyframe t, valid) - one per keyframe
        self.traj = []                         # (t, pE, pN, pU, roll, pitch, yaw, bgz_rate)
        self.states = []                       # D19 backend: (t, p ENU, v ENU, R world<-body FLU, gyro bias FLU, accel bias FLU)
        self.step_ns = []                      # per-keyframe processing time
        self.lag = []                          # (event stamp, wall-clock seconds from push to processing) for keyframes
        self.reinits = 0
        # ground-proximity flow rule (ruling D15), identical to fgo_replay / the UKF. t_arm: the arming time on the
        # bag clock (offline: imu_gaps.json; live: set by the node from the vehicle's arm state)
        self.gp = GroundProximityFlow(t_arm)
        self._reset_filter()

    # ---------------- inputs (arrival order) ----------------
    def push(self, t, kind, payload, t_wall=None):
        self.n_pushed[kind] = self.n_pushed.get(kind, 0) + 1
        if kind == "imu" and self.dejitter == "causal":
            t = self._dejitter(t)
        if kind == "tref":                   # (sensor time s,) - gap detection only, never queued
            self._gap_check(payload)
            return
        self._newest = max(self._newest, t)
        heapq.heappush(self._q, (t, next(self._seq), kind, payload, time.perf_counter() if t_wall is None else t_wall))
        self._release(self._newest - self.horizon_s)

    def flush(self):
        self._release(np.inf)

    # ---------------- causal pieces ----------------
    def _dejitter(self, t):
        x = float(self._n); self._n += 1
        dx = x - self._mx; self._mx += dx / self._n; self._my += (t - self._my) / self._n
        self._cxx += dx * (x - self._mx); self._cxy += dx * (t - self._my)
        if self._cxx <= 0:
            return t
        return self._my + (self._cxy / self._cxx) * (x - self._mx)

    def _gap_check(self, t_sensor):
        if self.gap != "causal":
            return
        if self._tref_prev is not None and t_sensor - self._tref_prev > GAP_S:
            self.gaps_seen.append((t_sensor, t_sensor - self._tref_prev, self._airborne()))
            if not self._airborne():
                self.reinits += 1
                self._reset_filter()           # the rule's trim: start again after the gap
                self._n = 0; self._mx = self._my = self._cxx = self._cxy = 0.0
            else:
                self._gap_invalid = True       # the rule's "unusable": invalid for the rest of the flight
                self.valid = False
        self._tref_prev = t_sensor

    def _airborne(self):
        return self._first_rng is not None and self._last_rng is not None and self._last_rng > self._first_rng + AIRBORNE_DZ

    def valid_now(self, t):
        """VALIDITY RULE (FGO; the UKF port's rule translated, METHODOLOGY): INVALID if a post-take-off
        IMU gap occurred, or if no flow factor has been fused for more than FLOW_TIMEOUT_S (EKF3's own
        relative-aiding timeout). Before the first fused flow the estimate counts as valid only on the
        ground (no horizontal aiding is needed there). The UKF's second condition (velocity 1-sigma >
        0.5 m/s) has no FGO counterpart: the smoother exposes no marginal covariance (the gate-only
        recursion is a gating approximation, not a covariance to trust), so it is not used."""
        if self._gap_invalid:
            return False
        if self._t_last_flow_fused is None:
            return not self._airborne()
        return (t - self._t_last_flow_fused) <= FLOW_TIMEOUT_S

    def _release(self, upto):
        while self._q and self._q[0][0] <= upto:
            t, _, kind, payload, tw = heapq.heappop(self._q)
            self._process(t, kind, payload, tw)

    # ---------------- the fgo_replay.py loop, unchanged ----------------
    def _reset_filter(self):
        self.fgo = None
        self._t_imu0 = None; self._acc_lvl = []; self._first_rng = None; self._last_rng = None
        self.t_init = None
        self.omega = np.zeros(3); self.t_prev_imu = None
        self.flow_omega = np.zeros(3); self.flow_pend = self.rng_pend = self.fwd_pend = None
        self.anchored = False; self.tag_pend = None

    def _try_init(self, t):
        if self._t_imu0 is None or self._first_rng is None or t < self._t_imu0 + 0.5:
            return False
        self.t_init = self._t_imu0 + 0.5
        self.fgo = FGO(window=self.window, kf_dt=1.0 / 30.0, lm_maxiter=self.lm_iters, fwd_sigma=self.fwd_sigma,
                       fwd_gate=self.fwd_gate, fwd_robust=self.fwd_robust,
                       log_cov=bool(os.environ.get("FGO_COV_LOG")) or self.tags)   # tags: cov_prev for the re-anchor prior
        self.fgo.init(np.mean(self._acc_lvl, axis=0), self._first_rng, self.t_init)
        self.gyro_avg = FlowFrameGyroAverager(self.t_init)
        self.fwd_avg = FlowFrameGyroAverager(self.t_init)
        self.t_kf_next = self.t_init + self.fgo.kf_dt
        return True

    def _process(self, tt, kind, d, t_wall):
        if kind == "rng" and 0.05 <= d <= 40.0:
            self._last_rng = d
        if self.fgo is None:
            # offline init: levelling over [t_imu0, t_imu0 + 0.5], the first valid range
            if kind == "imu":
                if self._t_imu0 is None:
                    self._t_imu0 = tt
                if tt <= self._t_imu0 + 0.5:
                    self._acc_lvl.append(d[0])
            if kind == "rng" and self._first_rng is None and 0.05 <= d <= 40.0:
                self._first_rng = d
            if kind == "att":
                self.omega = d
            if not self._try_init(tt):
                return
        if tt < self.t_init:
            if kind == "att":
                self.omega = d
            return
        if kind == "att":
            self.omega = d
        elif kind == "rng":
            self.rng_pend = d
            self.gp.on_range(tt, d)
        elif kind == "flow":
            self.flow_pend = d
            self.flow_omega = self.gyro_avg.average(tt, self.omega)
        elif kind == "fwd":
            self.fwd_pend = (d[0], d[1], float(self.fwd_avg.average(tt, self.omega)[2]))
        elif kind == "tag":
            if not self.tags:
                return
            if not self.anchored:                  # room_fgo_replay.py, verbatim
                self.fgo.reanchor((d[0], d[1]), d[2], self.tag_sigma_pos, self.tag_sigma_yaw)
                self.anchored = True; self.t_anchor = tt; self.n_anchors += 1
                self.fgo.log_cov = False
            else:
                self.tag_pend = d                  # the newest fix since the last keyframe
        elif kind == "imu":
            self.gp.on_gyro(tt, d[1], self.fgo.prev_bias.gyroscope())
            self.gyro_avg.push(tt, d[1])
            self.fwd_avg.push(tt, d[1])
            if self.t_prev_imu is not None:
                self.fgo.integrate_imu(d[0], d[1], tt - self.t_prev_imu)
            self.t_prev_imu = tt
            while tt >= self.t_kf_next:
                t0 = time.perf_counter_ns()
                if self.flow_pend is not None and self.flow_pend[1] and self.flow_pend[2] > 0.0:
                    _rpy = self.fgo.prev_pose.rotation().rpy()
                    self.flow_pend = (self.gp.replace(self.flow_pend[0], self.flow_omega - self.fgo.prev_bias.gyroscope(), _rpy[0], _rpy[1]),
                                      self.flow_pend[1], self.flow_pend[2])
                try:
                    self.fgo.keyframe(self.t_kf_next, flow=self.flow_pend, omega=self.flow_omega, rng=self.rng_pend, fwd=self.fwd_pend,
                                      tag=self.tag_pend)
                except Exception as e:
                    print(f"[warn] keyframe at {self.t_kf_next:.3f} failed: {type(e).__name__}: {e}")
                self.step_ns.append(time.perf_counter_ns() - t0)
                # validity (does not touch the estimate): a flow factor fused at this keyframe?
                if self.fgo.n_flow > getattr(self, "_n_flow_prev", 0):
                    self._t_last_flow_fused = self.t_kf_next
                self._n_flow_prev = self.fgo.n_flow
                self.valid = self.valid_now(self.t_kf_next)
                self.valid_log.append((self.t_kf_next, self.valid))
                t_lat, pose, vel = self.fgo.latest()
                rpy = pose.rotation().rpy()
                self.traj.append((t_lat, pose.x(), pose.y(), pose.z(), rpy[0], rpy[1], rpy[2], self.fgo.prev_bias.gyroscope()[2]))
                self.states.append((t_lat, np.array([pose.x(), pose.y(), pose.z()]), np.asarray(vel, float).copy(),
                                    np.asarray(pose.rotation().matrix(), float).copy(),
                                    np.asarray(self.fgo.prev_bias.gyroscope(), float).copy(),
                                    np.asarray(self.fgo.prev_bias.accelerometer(), float).copy()))
                self.lag.append((self.t_kf_next, time.perf_counter() - t_wall))
                self.anchor_log.append((self.anchored, self.n_anchors))
                self.flow_pend = self.rng_pend = self.fwd_pend = self.tag_pend = None
                self.t_kf_next += self.fgo.kf_dt


def odom_ned(p, v, R, bg, ba, anchored):
    """The FGO state -> ArduPilot ODOMETRY values (NED/FRD), as fgo_node.py sends them. PURE (tested offline by
    eval/fgo_odom_mapping_check.py). Before the tag re-anchor (and in every non-H use): the CORRIDOR frame
    (x forward = N, y = W, z up) -> NED (x, -y, -z). After it (experiment H): W written as ENU (x = E_W, y = N_W, z up)
    -> NED (y, x, -z), so yaw_NED = pi/2 - yaw_ENU.
    Returns (pos NED, vel NED, quaternion (w, x, y, z) NED<-FRD, gyro bias FRD, accel bias FRD)."""
    C = (np.array([[0.0, 1, 0], [1, 0, 0], [0, 0, -1]]) if anchored
         else np.array([[1.0, 0, 0], [0, -1, 0], [0, 0, -1]]))
    Fb = np.diag([1.0, -1, -1])                          # FLU <-> FRD
    pn, vn, Rn = C @ p, C @ v, C @ R @ Fb
    tr = np.trace(Rn)
    if tr > 0:
        S = np.sqrt(tr + 1.0) * 2; qw = 0.25 * S; qx = (Rn[2, 1] - Rn[1, 2]) / S; qy = (Rn[0, 2] - Rn[2, 0]) / S; qz = (Rn[1, 0] - Rn[0, 1]) / S
    elif Rn[0, 0] > Rn[1, 1] and Rn[0, 0] > Rn[2, 2]:
        S = np.sqrt(1.0 + Rn[0, 0] - Rn[1, 1] - Rn[2, 2]) * 2; qw = (Rn[2, 1] - Rn[1, 2]) / S; qx = 0.25 * S; qy = (Rn[0, 1] + Rn[1, 0]) / S; qz = (Rn[0, 2] + Rn[2, 0]) / S
    elif Rn[1, 1] > Rn[2, 2]:
        S = np.sqrt(1.0 + Rn[1, 1] - Rn[0, 0] - Rn[2, 2]) * 2; qw = (Rn[0, 2] - Rn[2, 0]) / S; qx = (Rn[0, 1] + Rn[1, 0]) / S; qy = 0.25 * S; qz = (Rn[1, 2] + Rn[2, 1]) / S
    else:
        S = np.sqrt(1.0 + Rn[2, 2] - Rn[0, 0] - Rn[1, 1]) * 2; qw = (Rn[1, 0] - Rn[0, 1]) / S; qx = (Rn[0, 2] + Rn[2, 0]) / S; qy = (Rn[1, 2] + Rn[2, 1]) / S; qz = 0.25 * S
    return pn, vn, (float(qw), float(qx), float(qy), float(qz)), Fb @ bg, Fb @ ba
