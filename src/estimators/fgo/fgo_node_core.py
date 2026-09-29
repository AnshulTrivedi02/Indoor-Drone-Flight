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
"""
import heapq, itertools, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # measurement_models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                    # fgo_core, factors
from fgo_core import FGO
from measurement_models import FlowFrameGyroAverager

GAP_S = 0.010          # the IMU-gap rule's gap (METHODOLOGY "RULE — IMU gaps and the replay estimators")
AIRBORNE_DZ = 0.30     # "left the ground": range above the initial range by more than this (m)


class FgoNodeCore:
    def __init__(self, window=0.25, lm_iters=2, fwd_sigma=None, fwd_gate=9.0, horizon_s=0.10,
                 dejitter="causal", gap="causal"):
        self.window, self.lm_iters, self.fwd_sigma, self.fwd_gate = window, lm_iters, fwd_sigma, fwd_gate
        self.horizon_s, self.dejitter, self.gap = horizon_s, dejitter, gap
        self._q, self._seq, self._newest = [], itertools.count(), -np.inf
        # running dejitter fit (index -> stamp)
        self._n = 0; self._mx = self._my = self._cxx = self._cxy = 0.0
        self._tref_prev = None
        self.valid = True
        self.traj = []                         # (t, pE, pN, pU, roll, pitch, yaw, bgz_rate)
        self.step_ns = []                      # per-keyframe processing time
        self.lag = []                          # (event stamp, wall-clock seconds from push to processing) for keyframes
        self.reinits = 0
        self._reset_filter()

    # ---------------- inputs (arrival order) ----------------
    def push(self, t, kind, payload, t_wall=None):
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
            if not self._airborne():
                self.reinits += 1
                self._reset_filter()           # the rule's trim: start again after the gap
                self._n = 0; self._mx = self._my = self._cxx = self._cxy = 0.0
            else:
                self.valid = False             # the rule's "unusable": invalid for the rest of the flight
        self._tref_prev = t_sensor

    def _airborne(self):
        return self._first_rng is not None and self._last_rng is not None and self._last_rng > self._first_rng + AIRBORNE_DZ

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

    def _try_init(self, t):
        if self._t_imu0 is None or self._first_rng is None or t < self._t_imu0 + 0.5:
            return False
        self.t_init = self._t_imu0 + 0.5
        self.fgo = FGO(window=self.window, kf_dt=1.0 / 30.0, lm_maxiter=self.lm_iters, fwd_sigma=self.fwd_sigma,
                       fwd_gate=self.fwd_gate, log_cov=bool(os.environ.get("FGO_COV_LOG")))
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
        elif kind == "flow":
            self.flow_pend = d
            self.flow_omega = self.gyro_avg.average(tt, self.omega)
        elif kind == "fwd":
            self.fwd_pend = (d[0], d[1], float(self.fwd_avg.average(tt, self.omega)[2]))
        elif kind == "imu":
            self.gyro_avg.push(tt, d[1])
            self.fwd_avg.push(tt, d[1])
            if self.t_prev_imu is not None:
                self.fgo.integrate_imu(d[0], d[1], tt - self.t_prev_imu)
            self.t_prev_imu = tt
            while tt >= self.t_kf_next:
                t0 = time.perf_counter_ns()
                try:
                    self.fgo.keyframe(self.t_kf_next, flow=self.flow_pend, omega=self.flow_omega, rng=self.rng_pend, fwd=self.fwd_pend)
                except Exception as e:
                    print(f"[warn] keyframe at {self.t_kf_next:.3f} failed: {type(e).__name__}: {e}")
                self.step_ns.append(time.perf_counter_ns() - t0)
                t_lat, pose, vel = self.fgo.latest()
                rpy = pose.rotation().rpy()
                self.traj.append((t_lat, pose.x(), pose.y(), pose.z(), rpy[0], rpy[1], rpy[2], self.fgo.prev_bias.gyroscope()[2]))
                self.lag.append((self.t_kf_next, time.perf_counter() - t_wall))
                self.flow_pend = self.rng_pend = self.fwd_pend = None
                self.t_kf_next += self.fgo.kf_dt
