"""Decision logic of the mocap watcher: I/O-free, clock-injected (every method takes `now`, a monotonic time in s),
so every rule is unit-testable with a fake clock.

Outputs:
  - `flags(now)`: the confirmation flags. box=1 means "the geofence is armed and every non-dependency check passes"
    (fresh tracked pose for >= recover_s, inside the 3-D box, tilt OK, rigid-body identity proven, FC parameters
    verified, FC link up, no latched episode). bridge=1 means "every watched dependency is alive" (and no latched
    episode). CONFIRMED = box and bridge. Only while CONFIRMED does the watcher send its MAVLink HEARTBEAT.
  - actions returned by the event methods: ("LAND", reason) at most once per episode, ("ALERT", text), ("LOG", text).

An EPISODE starts at the first breach/withdrawal (latched). It ends only when the FC reports DISARMED and every
check has passed continuously for recover_s; until then no further LAND is sent and nothing is confirmed. LAND is
sent only if the watcher had been confirmed in this episode (a vehicle that was never confirmed cannot have armed
via the flight script; the never-started/never-confirmed case is the arming gate's job, G6).

Gap map (docs/real_flights_plan.md 7.2.0): G2 stale/untracked/frozen pose, G3 identity, G4 latched one-shot LAND,
G7 dependency liveness (via LivenessMonitor), G8 dep-loss stop == land on hardware, G10 3-D box. Self-stall
(the watcher's own loop stopped, e.g. SIGSTOP; B3b) latches WITHOUT a LAND and without resuming the heartbeat.
"""
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Tuple

from realflight.watcher.frames import FrameConverter, euler_frd, tilt_deg, wrap_pi
from realflight.watcher.liveness import LivenessMonitor


@dataclass
class Config:
    box: Tuple[float, float, float, float, float, float]    # xmin, xmax, ymin, ymax, zmin, zmax (watch frame, m)
    tilt_max_deg: float = 60.0                              # as wall_watch.py
    stale_s: float = 0.5                                    # pre-registered (7.2)
    recover_s: float = 2.0                                  # B5c
    frozen_s: float = 0.5                                   # B5b fallback, only when the source gives no tracked flag
    deps: tuple = ()
    dep_timeout_s: float = 1.0
    progress_timeout_s: float = 2.0
    dep_loss: str = "land"                                  # 'land' | 'stop' (both LAND on hardware, G8)
    stall_s: float = 1.0                                    # own-loop gap that counts as a watcher hang
    fc_link_timeout_s: float = 3.0
    body_name: Optional[str] = None
    body_id: Optional[int] = None
    up_axis: str = "z"
    body_yaw_offset_deg: float = 0.0
    require_identity: bool = True
    id_rp_tol_deg: float = 5.0                              # B6
    id_rp_excite_deg: float = 8.0                           # hand roll/pitch ~10 deg (B6)
    id_rp_sustain_s: float = 0.5
    id_yaw_excite_deg: float = 45.0                         # hand yaw 90 deg (B6)
    id_yaw_tol_deg: float = 10.0                            # B6
    id_yaw_window_s: float = 1.0                            # B6
    id_yaw_span_s: float = 3.0                              # yaw changes compared over this sliding span (drift-free)
    att_max_age_s: float = 0.2                              # FC ATTITUDE must stream at >= 20 Hz to the watcher
    require_fc_params: bool = True


class Identity:
    """G3 / B6. UNPROVEN until the vehicle has been hand-moved (roll/pitch >= excite, yaw >= 45 deg) with the mocap
    body agreeing with the FC ATTITUDE; FAILED (final, until restart) on a sustained disagreement. Gates CONFIRMATION
    only. After it is proven, later disagreements are logged and alerted, never acted on (not pre-registered)."""

    def __init__(self, cfg: Config):
        self.c = cfg
        self.state = "unproven"
        self.why = "not yet excited (hand-tilt >= %.0f deg and hand-yaw >= %.0f deg)" % (
            cfg.id_rp_excite_deg, cfg.id_yaw_excite_deg)
        self.att = None               # (t, roll, pitch, yaw) FC
        self.fc_yaw_u = self.moc_yaw_u = None
        self.fc_prev = self.moc_prev = None
        self.hist = deque()           # (t, fc_yaw_unwrapped, mocap_yaw_unwrapped)
        self.rp_bad_since = self.rp_good_since = None
        self.rp_proven = self.yaw_proven = False
        self.yaw_excite_since = None
        self.post_bad_since = None
        self.max_rp_diff = 0.0

    def on_att(self, now, roll, pitch, yaw):
        self.att = (now, roll, pitch, yaw)
        if self.fc_prev is None:
            self.fc_yaw_u = yaw
        else:
            self.fc_yaw_u += wrap_pi(yaw - self.fc_prev)
        self.fc_prev = yaw

    def on_pose(self, now, R):
        """Returns actions (log/alert)."""
        acts = []
        if self.att is None or now - self.att[0] > self.c.att_max_age_s:
            return acts
        r_m, p_m, y_m = euler_frd(R)
        if self.moc_prev is None:
            self.moc_yaw_u = y_m
        else:
            self.moc_yaw_u += wrap_pi(y_m - self.moc_prev)
        self.moc_prev = y_m
        _, r_f, p_f, _ = self.att
        d = max(abs(wrap_pi(r_m - r_f)), abs(wrap_pi(p_m - p_f)))
        dd = math.degrees(d)
        self.max_rp_diff = max(self.max_rp_diff, dd)
        if self.state == "confirmed":                       # monitoring only
            if dd > self.c.id_rp_tol_deg:
                if self.post_bad_since is None:
                    self.post_bad_since = now
                elif now - self.post_bad_since > self.c.id_rp_sustain_s:
                    acts.append(("ALERT", f"identity: mocap/FC roll-pitch disagree by {dd:.1f} deg after proof "
                                           "(logged only, not acted on)"))
                    self.post_bad_since = now + 1e9               # alert once per disagreement spell
            else:
                self.post_bad_since = None
            return acts
        if self.state == "failed":
            return acts
        self.hist.append((now, self.fc_yaw_u, self.moc_yaw_u))
        while self.hist and now - self.hist[0][0] > self.c.id_yaw_span_s:
            self.hist.popleft()
        # roll / pitch
        excited = max(abs(r_f), abs(p_f), abs(r_m), abs(p_m)) >= math.radians(self.c.id_rp_excite_deg)
        if dd > self.c.id_rp_tol_deg:
            self.rp_good_since = None
            if self.rp_bad_since is None:
                self.rp_bad_since = now
            if now - self.rp_bad_since >= self.c.id_rp_sustain_s:
                return acts + self._fail(f"roll/pitch disagree by {dd:.1f} deg > {self.c.id_rp_tol_deg} "
                                         f"for {self.c.id_rp_sustain_s} s (mocap r/p {math.degrees(r_m):.1f}/"
                                         f"{math.degrees(p_m):.1f}, FC {math.degrees(r_f):.1f}/{math.degrees(p_f):.1f})")
        else:
            self.rp_bad_since = None
            if excited:
                if self.rp_good_since is None:
                    self.rp_good_since = now
                if now - self.rp_good_since >= self.c.id_rp_sustain_s and not self.rp_proven:
                    self.rp_proven = True
                    acts.append(("LOG", f"identity: roll/pitch agreement proven (diff {dd:.1f} deg)"))
            else:
                self.rp_good_since = None
        # yaw CHANGES over a sliding span (the mocap/FC yaw offset is arbitrary, and slow FC yaw drift cancels)
        t0, f0, m0 = self.hist[0]
        dfc = math.degrees(self.fc_yaw_u - f0)
        dmo = math.degrees(self.moc_yaw_u - m0)
        if not self.yaw_proven and max(abs(dfc), abs(dmo)) < self.c.id_yaw_excite_deg:
            self.yaw_excite_since = None
        if not self.yaw_proven and max(abs(dfc), abs(dmo)) >= self.c.id_yaw_excite_deg:
            if self.yaw_excite_since is None:
                self.yaw_excite_since = now
            if abs(dmo - dfc) <= self.c.id_yaw_tol_deg:
                self.yaw_proven = True
                acts.append(("LOG", f"identity: yaw change agreement proven (FC {dfc:.1f}, mocap {dmo:.1f} deg)"))
            elif now - self.yaw_excite_since > self.c.id_yaw_window_s:
                return acts + self._fail(f"yaw change FC {dfc:.1f} deg vs mocap {dmo:.1f} deg: not within "
                                         f"{self.c.id_yaw_tol_deg} deg within {self.c.id_yaw_window_s} s")
        if self.rp_proven and self.yaw_proven:
            self.state, self.why = "confirmed", "proven (roll/pitch and yaw change agree)"
            acts.append(("LOG", "identity CONFIRMED: the configured rigid body is this vehicle"))
        else:
            self.why = f"unproven (roll/pitch proven={self.rp_proven}, yaw proven={self.yaw_proven})"
        return acts

    def _fail(self, why):
        self.state, self.why = "failed", "FAILED: " + why
        return [("ALERT", "identity check FAILED (wrong rigid body?): " + why)]


class WatcherCore:
    def __init__(self, cfg: Config):
        self.c = cfg
        self.conv = FrameConverter(cfg.up_axis, cfg.body_yaw_offset_deg)
        self.ident = Identity(cfg)
        self.live = LivenessMonitor(cfg.deps, cfg.dep_timeout_s, cfg.progress_timeout_s)
        # pose
        self.last_frame = None
        self.last_fresh = None        # monotonic time of the last fresh (new frame, not untracked) sample
        self.fresh_since = None       # start of the current continuous fresh run
        self.last_change = None       # last time the pose bits changed (frozen fallback)
        self.last_raw = None
        self.untracked = False
        self.tracked_flag_seen = None  # True if the source provides a tracked flag
        self.p = self.R = None
        self.tilt = 0.0
        self.inside = False
        self.wrong_bodies = {}
        # FC
        self.params_ok, self.params_why = (None, "not yet read") if cfg.require_fc_params else (True, "not required")
        self.fc_armed = None
        self.fc_last_hb = None
        self.collision = None
        # deps
        self.dep_seen = {n: False for n in cfg.deps}
        # episode
        self.latched = None
        self.land_sent = False
        self.was_confirmed = False
        self.good_since = None
        self.last_loop = None
        self.max_gap = 0.0
        self.n_breach = 0

    # ---------------- events ----------------
    def loop_start(self, now):
        """Call FIRST in every loop iteration, before any input is drained or anything is sent (self-stall, B3b)."""
        acts = []
        if self.last_loop is not None:
            gap = now - self.last_loop
            self.max_gap = max(self.max_gap, gap)
            if gap > self.c.stall_s:
                acts += self._breach(f"watcher stalled: own loop gap {gap:.2f} s > {self.c.stall_s} s "
                                     "(hung/SIGSTOP); no LAND sent, heartbeat stays withdrawn", land=False)
        self.last_loop = now
        return acts

    def on_fc_heartbeat(self, now, armed: bool):
        self.fc_last_hb, self.fc_armed = now, armed

    def on_fc_attitude(self, now, roll, pitch, yaw):
        self.ident.on_att(now, roll, pitch, yaw)

    def on_params(self, ok: bool, why: str):
        self.params_ok, self.params_why = ok, why

    def on_sysid_collision(self, now, what):
        if self.collision is None:
            self.collision = what
            return self._breach(f"MAVLink system-ID collision: {what} (would mask the FC's GCS failsafe, G11)",
                                land=False)
        return []

    def on_beacon(self, now, data: bytes):
        self.live.feed(data, now)

    def on_pose(self, now, s):
        """s: mocap.MocapSample. Breach rules are evaluated on arrival (B4: <= 0.1 s)."""
        if (self.c.body_name is not None and s.body_name != self.c.body_name) or \
                (self.c.body_id is not None and s.body_id != self.c.body_id):
            k = f"{s.body_name}#{s.body_id}"
            self.wrong_bodies[k] = self.wrong_bodies.get(k, 0) + 1
            return []
        if self.last_frame is not None and s.frame_no == self.last_frame:
            return []                                        # duplicate frame: not fresh
        self.last_frame = s.frame_no
        self.tracked_flag_seen = s.tracked in (0, 1)
        if s.tracked == 0:
            self.untracked = True
            self.fresh_since = None
            return []
        self.untracked = False
        raw = (s.pos, s.quat)
        if raw != self.last_raw or self.last_change is None:
            self.last_change = now
        self.last_raw = raw
        if s.tracked == -1 and now - self.last_change > self.c.frozen_s:
            return []                                        # frozen (no tracked flag): not fresh
        self.last_fresh = now
        if self.fresh_since is None:
            self.fresh_since = now
        self.p, self.R = self.conv.convert(s.pos, s.quat)
        self.tilt = tilt_deg(self.R)
        x0, x1, y0, y1, z0, z1 = self.c.box
        x, y, z = self.p
        self.inside = x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1
        acts = self.ident.on_pose(now, self.R) if self.c.require_identity else []
        if not self.inside:
            acts += self._breach(f"box left: ({x:.3f}, {y:.3f}, {z:.3f}) outside x[{x0},{x1}] y[{y0},{y1}] "
                                 f"z[{z0},{z1}]", land=True)
        elif self.tilt > self.c.tilt_max_deg:
            acts += self._breach(f"tilt {self.tilt:.1f} deg > {self.c.tilt_max_deg}", land=True)
        return acts

    def tick(self, now):
        """Evaluate time-based rules (stale pose, dependencies, FC link) and the episode state."""
        acts = []
        pose_fresh, why = self.pose_fresh(now)
        if not pose_fresh:
            self.fresh_since = None
            if self.was_confirmed and self.latched is None:
                acts += self._breach(f"mocap pose {why}", land=True)
        st = self.live.status(now)
        for n, (ok, w) in st.items():
            if ok:
                self.dep_seen[n] = True
            elif self.dep_seen[n] and self.latched is None and self.was_confirmed:
                note = "" if self.c.dep_loss == "land" else \
                    " (--dep-loss stop has no hardware meaning: mapped to LAND + alert, G8)"
                acts += self._breach(f"dependency {n} lost: {w}{note}", land=True)
        if self.fc_last_hb is not None and now - self.fc_last_hb > self.c.fc_link_timeout_s \
                and self.was_confirmed and self.latched is None:
            acts += self._breach(f"FC link lost: no FC HEARTBEAT for {now - self.fc_last_hb:.1f} s", land=False)
        good = self._checks_ok(now, st, need_duration=False)[0]
        if self.latched is not None:
            if good and self.fc_armed is False:
                if self.good_since is None:
                    self.good_since = now
                if now - self.good_since >= self.c.recover_s:
                    acts.append(("LOG", f"episode cleared (FC disarmed, all checks good for {self.c.recover_s} s): "
                                        f"was '{self.latched}'"))
                    self.latched, self.land_sent, self.good_since = None, False, None
                    self.was_confirmed = False
            else:
                self.good_since = None
        if self.confirmed(now):
            if not self.was_confirmed:
                acts.append(("LOG", "CONFIRMED: all checks pass; MAVLink heartbeat to the FC enabled"))
            self.was_confirmed = True
        return acts

    # ---------------- state ----------------
    def pose_fresh(self, now):
        if self.last_fresh is None:
            return False, "never received"
        if self.untracked:
            return False, "reported NOT TRACKED by the mocap"
        if now - self.last_fresh > self.c.stale_s:
            return False, f"stale ({now - self.last_fresh:.2f} s > {self.c.stale_s} s)"
        if not self.tracked_flag_seen and now - self.last_change > self.c.frozen_s:
            return False, f"frozen (bit-identical for {now - self.last_change:.2f} s, no tracked flag)"
        return True, "fresh"

    def _checks_ok(self, now, st=None, need_duration=True):
        """(all_ok, (box_ok, bridge_ok), reasons), ignoring the latch. need_duration=False drops the 'fresh for
        recover_s' requirement (the episode-clear timer applies its own recover_s hold)."""
        reasons = []
        fresh, why = self.pose_fresh(now)
        if not fresh:
            reasons.append(f"pose {why}")
        elif need_duration and (self.fresh_since is None or now - self.fresh_since < self.c.recover_s):
            reasons.append(f"pose fresh for < {self.c.recover_s} s")
        if self.p is not None and not self.inside:
            reasons.append("outside box")
        if self.tilt > self.c.tilt_max_deg:
            reasons.append("tilt")
        if self.c.require_identity and self.ident.state != "confirmed":
            reasons.append(f"identity {self.ident.why}")
        if self.params_ok is not True:
            reasons.append(f"FC params {self.params_why}")
        if self.fc_last_hb is None or now - self.fc_last_hb > self.c.fc_link_timeout_s:
            reasons.append("FC link down")
        if self.collision:
            reasons.append(f"sysid collision {self.collision}")
        box_ok = not reasons
        st = st if st is not None else self.live.status(now)
        dead = {n: w for n, (ok, w) in st.items() if not ok}
        if dead:
            reasons.append(f"deps {dead}")
        return box_ok and not dead, (box_ok, not dead), reasons

    def flags(self, now):
        _, (box_ok, bridge_ok), reasons = self._checks_ok(now)
        lat = self.latched is not None
        if lat:
            reasons = [f"LATCHED: {self.latched}"] + reasons
        fresh = self.pose_fresh(now)[0]
        return {"box": int(box_ok and not lat), "bridge": int(bridge_ok and not lat), "pose": int(fresh),
                "id": int(self.ident.state == "confirmed" or not self.c.require_identity),
                "fc": int(self.params_ok is True), "latch": int(lat)}, reasons

    def confirmed(self, now):
        f, _ = self.flags(now)
        return f["box"] == 1 and f["bridge"] == 1

    # ---------------- breach ----------------
    def _breach(self, why, land):
        if self.latched is not None:
            return [("LOG", f"(already latched) {why}")]
        self.latched = why
        self.n_breach += 1
        self.good_since = None
        acts = [("ALERT", f"BREACH: {why}")]
        if land and self.was_confirmed and not self.land_sent:
            self.land_sent = True
            acts.append(("LAND", why))
        return acts
