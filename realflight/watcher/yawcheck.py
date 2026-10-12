"""F7 pre-arm yaw check (ruling 2 of "RULINGS (user, 2026-10-12, safety first)", METHODOLOGY; finding F7 in
docs/handovers/2026-10-12_watcher_bench_rerun.md §2.3).

RULE. While the FC is DISARMED, the watcher withholds its confirmation (so it sends no MAVLink HEARTBEAT, and the FC
cannot arm through the native GCS failsafe or the Lua aux-auth path) unless the FC's own yaw (MAVLink ATTITUDE.yaw,
i.e. the AHRS/estimator yaw) agrees with the mocap rigid-body heading, mapped into the FC's yaw frame by the TIE, within
`tol_deg` (5 deg), CONTINUOUSLY for at least `sustain_s` (1 s), with the mocap pose valid (fresh and tracked) and the
FC attitude fresh. Any single comparison outside the tolerance, a stale FC attitude, or an invalid mocap pose restarts
the 1 s. It is re-evaluated on every FC ATTITUDE (25 Hz) for as long as the FC is disarmed.
Once the FC reports ARMED the check is INFORMATIONAL ONLY: it is still computed and logged, but it never withdraws the
confirmation, never latches an episode and never sends a LAND (an in-flight withdrawal would stop the heartbeat, and
the FC's GCS failsafe and fly_trial's WatcherLost would then land the vehicle).

FRAMES. Both yaws are NED-sense headings: clockwise from above, in radians, wrapped to (-pi, pi].
  - FC: ATTITUDE.yaw, the FRD body's heading in the FC's NED frame.
  - mocap: `frames.euler_frd(R)[2]`, the heading of the rigid body's +x axis (the nose, after --body-yaw-offset-deg)
    measured CLOCKWISE from the watch frame's +x axis (z-up frame; yaw_frd = -yaw_flu). B6b showed this has the same
    sense as ATTITUDE.yaw (the yaw-change proof compares them directly).
  - TIE: expected FC yaw = mocap heading + tie, compared as wrap(fc_yaw - (mocap_heading + tie)). The tie is the FC yaw
    of a vehicle whose nose points along the mocap +x axis, i.e. the NED bearing of the mocap +x axis IN THE FC'S YAW
    FRAME. Angle wrap is handled everywhere by wrap_pi; the tie capture uses a circular mean.

HOW THE TIE IS SET (one of two, chosen per session; `--yaw-tie`):
  - 'origin' (default; required for the no-compass variant): the watcher CAPTURES the tie at the FC's EKF-origin event.
    With no compass EKF3 starts at yaw 0 (AP_NavEKF3_core.cpp:527, from_euler(roll, pitch, 0)), so the FC yaw frame is
    fixed only by the boot heading and no surveyed constant can apply. The AHRS broadcasts GPS_GLOBAL_ORIGIN on every
    channel ONCE, when the origin first becomes valid (AP_AHRS.cpp:428-440; the origin procedure sends the origin only
    after every EKF3 core has initialised, so this is right after boot, vehicle untouched on the start mark). On the
    FIRST GPS_GLOBAL_ORIGIN in an FC boot the watcher averages wrap(fc_yaw - mocap_heading) over the next
    `capture_s` (1 s) with a circular mean. The capture FAILS (no tie: the watcher then refuses until the FC reboots and
    a new origin is set) unless: >= `capture_min_n` comparisons, the mocap valid throughout, the vehicle still (mocap
    heading spread <= `still_deg`) and the samples consistent (FC-minus-mocap spread <= `still_deg`). Later
    GPS_GLOBAL_ORIGIN messages in the same boot (Copter re-broadcasts it when home is set, AP_AHRS.cpp:3072) are
    ignored. An FC reboot (ATTITUDE.time_boot_ms going backwards) drops the tie.
    RESIDUALS (stated): (a) the watcher must be RUNNING before the origin is set (the broadcast is sent once); a watcher
    started later never ties and refuses (fail-closed), and a restart of the watcher within the boot also refuses until
    the FC reboots. (b) An FC yaw that is already wrong at the origin event is baked into the tie; under no compass
    there is no absolute yaw to be wrong against, and the check then guards the yaw CHANGES from the origin to arming
    (drift, resets, rotations the FC did not sense).
  - a number in degrees (for the compass variant only): a SURVEYED constant, the NED bearing of the mocap +x axis
    (magnetic declination as the FC applies it). This also catches an FC compass yaw that is wrong from the start.
    In the SITL bench (Gazebo ENU world, x = East) it is 90.
"""
import math

from realflight.watcher.frames import wrap_pi


def circ_mean(angles):
    s = sum(math.sin(a) for a in angles)
    c = sum(math.cos(a) for a in angles)
    return math.atan2(s, c)


def circ_spread(angles):
    """Max |wrap(a - circular mean)| * 2, a wrap-safe range."""
    if not angles:
        return 0.0
    m = circ_mean(angles)
    d = [wrap_pi(a - m) for a in angles]
    return max(d) - min(d)


class YawCheck:
    def __init__(self, tie_deg=None, tol_deg=5.0, sustain_s=1.0, att_max_age_s=0.5, lag_max_s=0.3, capture_s=1.0,
                 capture_min_n=10, still_deg=2.0):
        """tie_deg None = capture at the origin event ('origin' mode); a number = a fixed surveyed tie."""
        self.mode = "origin" if tie_deg is None else "fixed"
        self.tie = None if tie_deg is None else math.radians(tie_deg)
        self.tol = math.radians(tol_deg)
        self.tol_deg = tol_deg
        self.sustain_s, self.att_max_age_s, self.lag_max_s = sustain_s, att_max_age_s, lag_max_s
        self.capture_s, self.capture_min_n, self.still = capture_s, capture_min_n, math.radians(still_deg)
        self.mhist = []                      # (t, mocap heading) for the last lag_max_s, valid poses only
        self.mocap_valid = False
        self.last_boot_ms = None
        self.origin_seen = False             # a GPS_GLOBAL_ORIGIN has been seen in this FC boot
        self.capture = None                  # {"t0", "d": [fc - mocap], "m": [mocap heading], "bad": why or None}
        self.tie_why = ("fixed (surveyed) tie %.1f deg" % tie_deg) if tie_deg is not None else \
            "no tie yet: waiting for the FC's EKF-origin broadcast (GPS_GLOBAL_ORIGIN) in this boot"
        self.agree_since = None
        self.t_att = None
        self.fc_yaw = self.moc_hdg = self.diff = None
        self.armed_bad_since = None
        self.disarmed_bad_alerted = False
        self.max_diff_disarmed = 0.0
        self.max_diff_armed = 0.0

    # ---------------- inputs ----------------
    def set_mocap_valid(self, now, valid):
        if not valid:
            self.agree_since = None
            self.mhist = []
            if self.capture is not None and self.capture["bad"] is None:
                self.capture["bad"] = "mocap invalid during the capture"
        self.mocap_valid = valid

    def on_pose(self, now, heading):
        self.mhist.append((now, heading))
        while self.mhist and now - self.mhist[0][0] > self.lag_max_s:
            self.mhist.pop(0)

    def on_origin(self, now):
        acts = []
        if self.mode != "origin":
            return [("LOG", "yaw check: FC GPS_GLOBAL_ORIGIN received (fixed tie, not used)")]
        if self.origin_seen:
            return [("LOG", "yaw check: a later GPS_GLOBAL_ORIGIN in the same FC boot ignored (the tie is taken at "
                            "the first)")]
        self.origin_seen = True
        self.capture = {"t0": now, "d": [], "m": [], "bad": None}
        self.tie_why = "capturing the tie (1 s after the EKF-origin broadcast)"
        acts.append(("LOG", "yaw check: EKF-origin broadcast seen; capturing the mocap/FC yaw tie over "
                            f"{self.capture_s} s"))
        if not self.mocap_valid:
            self.capture["bad"] = "mocap invalid at the origin event"
        return acts

    def _reboot(self):
        acts = [("ALERT", "yaw check: FC reboot detected (ATTITUDE time_boot_ms went backwards); yaw tie dropped"
                 + ("" if self.mode == "fixed" else ", waiting for the next EKF-origin broadcast"))]
        if self.mode == "origin":
            self.tie, self.origin_seen, self.capture = None, False, None
            self.tie_why = "no tie: FC rebooted; waiting for the EKF-origin broadcast in the new boot"
        self.agree_since = None
        return acts

    def best_diff(self, now, fc_yaw, tie):
        cand = [h for (t, h) in self.mhist if now - self.lag_max_s <= t <= now]
        if not cand:
            return None, None
        best = min(cand, key=lambda h: abs(wrap_pi(fc_yaw - (h + tie))))
        return wrap_pi(fc_yaw - (best + tie)), best

    def on_att(self, now, yaw, boot_ms=None, armed=None):
        """FC ATTITUDE yaw (rad, NED sense). Returns actions (LOG/ALERT only; never LAND)."""
        acts = []
        if boot_ms is not None:
            if self.last_boot_ms is not None and boot_ms + 1000 < self.last_boot_ms:
                acts += self._reboot()
            self.last_boot_ms = boot_ms
        self.t_att, self.fc_yaw = now, yaw
        cap = self.capture
        if cap is not None and self.tie is None:
            if now - cap["t0"] <= self.capture_s:
                if cap["bad"] is None:
                    d, h = self.best_diff(now, yaw, 0.0)
                    if d is None:
                        cap["bad"] = "no valid mocap pose within %.1f s of an FC attitude" % self.lag_max_s
                    else:
                        cap["d"].append(d); cap["m"].append(h)
            elif not cap.get("done"):
                cap["done"] = True
                why = cap["bad"]
                if why is None and len(cap["d"]) < self.capture_min_n:
                    why = f"only {len(cap['d'])} comparisons (< {self.capture_min_n})"
                if why is None and circ_spread(cap["m"]) > self.still:
                    why = f"vehicle not still (mocap heading spread {math.degrees(circ_spread(cap['m'])):.1f} deg)"
                if why is None and circ_spread(cap["d"]) > self.still:
                    why = f"FC-minus-mocap spread {math.degrees(circ_spread(cap['d'])):.1f} deg"
                if why is None:
                    self.tie = circ_mean(cap["d"])
                    self.tie_why = (f"tie {math.degrees(self.tie):.2f} deg captured at the EKF-origin broadcast "
                                    f"(n={len(cap['d'])})")
                    acts.append(("LOG", "yaw check: " + self.tie_why))
                else:
                    self.tie_why = "TIE CAPTURE FAILED (" + why + "): refusing until the FC reboots and sets a new origin"
                    acts.append(("ALERT", "yaw check: " + self.tie_why))
        if self.tie is None:
            self.agree_since = None
            self.diff = None
            return acts
        d, h = self.best_diff(now, yaw, self.tie)
        self.moc_hdg = h
        self.diff = d
        if d is None or not self.mocap_valid:
            self.agree_since = None
            return acts
        dd = abs(math.degrees(d))
        bad = abs(d) > self.tol
        if armed:
            self.max_diff_armed = max(self.max_diff_armed, dd)
            self.agree_since = None if bad else (self.agree_since if self.agree_since is not None else now)
            if bad:
                if self.armed_bad_since is None:
                    self.armed_bad_since = now
                elif now - self.armed_bad_since >= self.sustain_s and not getattr(self, "_armed_logged", False):
                    self._armed_logged = True
                    acts.append(("LOG", f"yaw check (INFORMATIONAL, FC armed; no action): FC yaw "
                                        f"{math.degrees(yaw):.1f} vs mocap+tie {math.degrees(wrap_pi(h + self.tie)):.1f}"
                                        f" deg, diff {dd:.1f} > {self.tol_deg}"))
            else:
                self.armed_bad_since = None
                self._armed_logged = False
            return acts
        self.armed_bad_since = None
        self._armed_logged = False
        self.max_diff_disarmed = max(self.max_diff_disarmed, dd)
        if bad:
            self.agree_since = None
            if not self.disarmed_bad_alerted:
                self.disarmed_bad_alerted = True
                acts.append(("ALERT", f"yaw check: FC yaw {math.degrees(yaw):.1f} vs mocap+tie "
                                      f"{math.degrees(wrap_pi(h + self.tie)):.1f} deg differ by {dd:.1f} > "
                                      f"{self.tol_deg}: arming refused"))
        else:
            if self.agree_since is None:
                self.agree_since = now
            if self.disarmed_bad_alerted and now - self.agree_since >= self.sustain_s:
                self.disarmed_bad_alerted = False
                acts.append(("LOG", f"yaw check: agreement restored (diff {dd:.1f} deg for {self.sustain_s} s)"))
        return acts

    # ---------------- verdict ----------------
    def ok(self, now, armed, mocap_fresh):
        """(gate_ok, why). Gates only while the FC is not reported ARMED (None counts as disarmed)."""
        if armed is True:
            return True, "armed: informational only"
        if self.tie is None:
            return False, self.tie_why
        if not mocap_fresh:
            return False, "mocap pose not valid"
        if self.t_att is None or now - self.t_att > self.att_max_age_s:
            return False, "no fresh FC ATTITUDE"
        if self.agree_since is None:
            d = "n/a" if self.diff is None else f"{abs(math.degrees(self.diff)):.1f}"
            return False, f"FC/mocap yaw disagree (diff {d} deg > {self.tol_deg})"
        if now - self.agree_since < self.sustain_s:
            return False, f"FC/mocap yaw agree for {now - self.agree_since:.2f} s < {self.sustain_s} s"
        return True, "agree"
