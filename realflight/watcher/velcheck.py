"""M2 pre-arm EKF velocity check (F8 mitigation M2; RULING (user, 2026-10-12): F8 mitigations M1, M2, M3 APPROVED,
METHODOLOGY; the mechanism in docs/handovers/2026-10-12_f8_investigation.md).

WHY. F8: after a landing, EKF3's flow innovation gate can lock one axis out on the ground while the other axis keeps the
fall-backs (no-aiding, zero-velocity fusion) switched off, so EKF3's velocity runs away (1-2 m/s) while the vehicle sits
still. No stock arming check looks at it (AP_NavEKF3_Outputs.cpp:40-57; the Copter EKF check uses variances, which
stayed small), so the FC armed with it. EKF_STATUS_REPORT cannot see it (its velocity variance stayed ~0).

RULE. While the FC is DISARMED, the watcher withholds its confirmation (so it sends no MAVLink HEARTBEAT, and the FC
cannot arm through the native GCS failsafe or the Lua aux-auth path; the file flag box=0, so the flight script refuses)
unless, CONTINUOUSLY for at least `sustain_s` (5 s):
  (1) the FC's EKF velocity is small: the 3-D Euclidean norm sqrt(vx^2 + vy^2 + vz^2) of MAVLink LOCAL_POSITION_NED
      (vx, vy, vz: the AHRS / primary EKF3 core's NED velocity, GCS_Common.cpp send_local_position) is < `v_max`
      (0.2 m/s) on EVERY LOCAL_POSITION_NED received. All three components are used (the ruling names EKF3's velocity,
      unqualified); F8 was horizontal (the lowest of the five core-0 cases was 0.26 m/s), so the 3-D norm catches every
      F8 case and is stricter. Stored bench logs: |VD| <= 0.08 m/s on the ground before every arm;
  (2) the mocap shows the vehicle STATIONARY: on every mocap pose, the translational speed over a fixed baseline,
      |p(t) - p(t - base_s)| / dt with dt >= 0.8 * base_s (base_s = 0.5 s; p the rigid-body position in the watch frame,
      m), is < `still_mps` (0.05 m/s). A per-frame finite difference is not used (noise-dominated at 100 Hz). Rotation is
      not part of it (a vehicle turned in place does not move; the F7 yaw check covers heading);
  (3) the mocap pose is valid (fresh and tracked, the watcher's own staleness rules);
  (4) LOCAL_POSITION_NED is fresh: the latest received <= `lpn_max_age_s` (0.5 s) ago.
Any single violation (a velocity sample >= v_max, a moving or invalid mocap pose, a stale LOCAL_POSITION_NED, or too
little mocap history to measure the speed) restarts the 5 s.
NO ORIGIN, NO LOCAL_POSITION_NED: the FC sends LOCAL_POSITION_NED only when the AHRS has a position relative to the EKF
origin AND a velocity (GCS_Common.cpp:3042-3051 at 7bac20cbcc), so without an origin the check refuses (fail-closed;
consistent with the flight cards' "no arming without a verified origin").
Once the FC reports ARMED the check is INFORMATIONAL ONLY: still computed and logged, but it never withdraws the
confirmation, never latches an episode and never sends a LAND (in flight the velocity is meant to be non-zero, and an
in-flight withdrawal would stop the heartbeat -> FC GCS failsafe LAND, and box=0 -> fly_trial WatcherLost LAND).
A withdrawal on this check while disarmed is NOT a breach: no latch, no LAND.
"""
import math
from collections import deque


class VelCheck:
    def __init__(self, v_max=0.2, sustain_s=5.0, still_mps=0.05, base_s=0.5, lpn_max_age_s=0.5):
        self.v_max, self.sustain_s, self.still_mps = v_max, sustain_s, still_mps
        self.base_s, self.lpn_max_age_s = base_s, lpn_max_age_s
        self.phist = deque()         # (t, (x, y, z)) mocap positions, valid poses only, the last ~base_s + margin
        self.mocap_valid = False
        self.moc_speed = None        # latest mocap translational speed over the baseline (m/s), None = not measurable
        self.t_lpn = None
        self.v = None                # (vx, vy, vz) of the latest LOCAL_POSITION_NED
        self.vnorm = None
        self.good_since = None       # start of the current continuous good run
        self.why_bad = "no LOCAL_POSITION_NED yet (needs the EKF origin)"
        self.max_v_disarmed = 0.0
        self.max_v_armed = 0.0
        self.disarmed_bad_alerted = False

    def _reset(self, why):
        self.good_since = None
        self.why_bad = why

    # ---------------- inputs ----------------
    def set_mocap_valid(self, now, valid):
        if not valid:
            if self.mocap_valid or self.good_since is not None:
                self._reset("mocap pose not valid")
            self.phist.clear()
            self.moc_speed = None
        self.mocap_valid = valid

    def on_pose(self, now, p):
        """A fresh, tracked mocap pose (watch-frame position, m)."""
        self.phist.append((now, tuple(p)))
        while len(self.phist) > 2 and now - self.phist[1][0] >= self.base_s:
            self.phist.popleft()
        t0, p0 = self.phist[0]
        dt = now - t0
        if dt < 0.8 * self.base_s:
            self.moc_speed = None
            self._reset("mocap speed not yet measurable (too little pose history)")
            return
        self.moc_speed = math.dist(p, p0) / dt
        if self.moc_speed >= self.still_mps:
            self._reset(f"vehicle not stationary (mocap speed >= {self.still_mps} m/s)")

    def on_lpn(self, now, vx, vy, vz, armed=None):
        """FC LOCAL_POSITION_NED velocity (m/s, NED). Returns actions (LOG/ALERT only; never LAND)."""
        acts = []
        self.t_lpn, self.v = now, (vx, vy, vz)
        self.vnorm = math.sqrt(vx * vx + vy * vy + vz * vz)
        if armed is True:
            self.max_v_armed = max(self.max_v_armed, self.vnorm)
        else:
            self.max_v_disarmed = max(self.max_v_disarmed, self.vnorm)
        if self.vnorm >= self.v_max:
            self._reset(f"EKF velocity |v| >= {self.v_max} m/s (F8)")
            if armed is not True and not self.disarmed_bad_alerted:
                self.disarmed_bad_alerted = True
                acts.append(("ALERT", f"velocity check: EKF |v| {self.vnorm:.3f} m/s >= {self.v_max} while disarmed "
                                      f"(vx {vx:.3f} vy {vy:.3f} vz {vz:.3f}): arming refused (F8)"))
            return acts
        if self.mocap_valid and self.moc_speed is not None and self.moc_speed < self.still_mps:
            if self.good_since is None:
                self.good_since = now
            if self.disarmed_bad_alerted and now - self.good_since >= self.sustain_s:
                self.disarmed_bad_alerted = False
                acts.append(("LOG", f"velocity check: EKF |v| < {self.v_max} m/s with the vehicle still for "
                                    f"{self.sustain_s} s again"))
        return acts

    # ---------------- verdict ----------------
    def ok(self, now, armed, mocap_fresh):
        """(gate_ok, why). Gates only while the FC is not reported ARMED (None counts as disarmed)."""
        if armed is True:
            return True, "armed: informational only"
        if not mocap_fresh or not self.mocap_valid:
            return False, "mocap pose not valid"
        if self.t_lpn is None:
            return False, "no LOCAL_POSITION_NED from the FC (no EKF origin?)"
        if now - self.t_lpn > self.lpn_max_age_s:
            self._reset(f"LOCAL_POSITION_NED stale (> {self.lpn_max_age_s} s)")
            return False, self.why_bad
        if self.good_since is None:
            return False, self.why_bad
        if now - self.good_since < self.sustain_s:
            return False, f"EKF |v| < {self.v_max} m/s and vehicle still, held < {self.sustain_s} s"
        return True, "still"
