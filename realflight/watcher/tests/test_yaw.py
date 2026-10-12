"""F7 pre-arm yaw check (yawcheck.py; ruling 2 of "RULINGS (user, 2026-10-12, safety first)"). Unit tests with a fake
clock (core level) and end-to-end tests with the FakeFC (watcher subprocess)."""
import math
import time

from realflight.watcher.core import Config, WatcherCore
from realflight.watcher.mocap import MocapSample
from realflight.watcher.tests.fakes import mavlink, quat_from_euler_zup, wait_for

BOX = (-2, 2, -2, 2, 0, 2.5)
D = math.radians


class YSim:
    """WatcherCore at 100 Hz mocap / 25 Hz FC ATTITUDE / 5 Hz FC heartbeat, fake clock. `hdg` is the mocap heading
    in the FC (NED, clockwise) sense, i.e. the rigid body is yawed by -hdg in the z-up mocap frame."""

    def __init__(self, tie=0.0, **kw):
        kw.setdefault("box", BOX)
        kw.setdefault("require_identity", False)
        kw.setdefault("recover_s", 0.5)
        self.c = WatcherCore(Config(require_yaw=True, yaw_tie_deg=tie, **kw))
        self.c.on_params(True, "ok")
        self.t, self.frame, self.n = 0.0, 0, 0
        self.hdg = 0.0              # mocap heading (rad, NED sense)
        self.fc_yaw = 0.0           # FC ATTITUDE yaw (rad)
        self.tracked = 1
        self.mocap_on = True
        self.armed = False
        self.boot_ms = 10000
        self.acts = []

    def step(self, dt=0.01):
        self.t += dt
        self.n += 1
        c, t = self.c, self.t
        self.acts += c.loop_start(t)
        if self.mocap_on:
            self.frame += 1
            q = quat_from_euler_zup(0.0, 0.0, -self.hdg)
            p = (1e-6 * (self.frame % 3), 0.0, 0.0)
            self.acts += c.on_pose(t, MocapSample(self.frame, t, t, 1, "quad", self.tracked, p, q))
        if self.n % 5 == 0:
            self.boot_ms += 50
            self.acts += c.on_fc_attitude(t, 0.0, 0.0, math.atan2(math.sin(self.fc_yaw), math.cos(self.fc_yaw)),
                                          self.boot_ms)
        if self.n % 20 == 0:
            c.on_fc_heartbeat(t, self.armed)
        self.acts += c.tick(t)

    def run(self, secs):
        for _ in range(int(round(secs / 0.01))):
            self.step()

    def confirmed(self):
        return self.c.confirmed(self.t)

    def reasons(self):
        return "; ".join(self.c.flags(self.t)[1])

    def lands(self):
        return [a for a in self.acts if a[0] == "LAND"]


# ---------------- the rule ----------------
def test_f7_pass_when_yaw_agrees_for_1s():
    s = YSim(); s.run(0.6)
    assert not s.confirmed() and "yaw" in s.reasons()          # 1 s of agreement not yet reached
    s.run(0.6)
    assert s.confirmed(), s.reasons()


def test_f7_refuses_at_6deg_and_passes_at_4deg():
    s = YSim(); s.fc_yaw = D(6.0); s.run(5.0)
    assert not s.confirmed() and "yaw FC/mocap yaw disagree (diff 6.0" in s.reasons(), s.reasons()
    assert any(a[0] == "ALERT" and "arming refused" in a[1] for a in s.acts)
    s2 = YSim(); s2.fc_yaw = D(-4.0); s2.run(2.0)
    assert s2.confirmed(), s2.reasons()


def test_f7_wrap_at_plus_minus_180():
    s = YSim(); s.hdg, s.fc_yaw = D(179.0), D(-179.0); s.run(2.0)       # 2 deg apart across the wrap
    assert s.confirmed(), s.reasons()
    s = YSim(); s.hdg, s.fc_yaw = D(177.0), D(-177.0); s.run(2.0)       # 6 deg apart across the wrap
    assert not s.confirmed() and "diff 6.0" in s.reasons(), s.reasons()
    s = YSim(tie=90.0); s.hdg, s.fc_yaw = D(92.0), D(-179.0); s.run(2.0)  # mocap+tie = 182 = -178: 1 deg apart
    assert s.confirmed(), s.reasons()


def test_f7_sitl_tie_90_gazebo_enu():
    """SITL bench frame: Gazebo ENU (x = East), spawn yaw +90 deg ENU = nose north = FC yaw 0; the mocap heading in the
    NED sense is -90 deg, so the tie (the NED bearing of the mocap +x axis) is +90."""
    s = YSim(tie=90.0); s.hdg = D(-90.0); s.fc_yaw = 0.0; s.run(2.0)
    assert s.confirmed(), s.reasons()


def test_f7_mocap_invalid_refuses():
    s = YSim(); s.run(2.0); assert s.confirmed()
    s.tracked = 0; s.run(0.3)                                           # body reported NOT tracked
    assert not s.confirmed() and "yaw mocap pose not valid" in s.reasons(), s.reasons()
    s.tracked = 1; s.run(0.6)
    assert not s.confirmed()                                            # 1 s of agreement restarts
    s.run(1.0); assert s.confirmed(), s.reasons()
    s.mocap_on = False; s.run(0.7)                                      # stream stopped: stale
    assert not s.confirmed() and "yaw mocap pose not valid" in s.reasons()


def test_f7_stale_fc_attitude_refuses():
    s = YSim(); s.run(2.0); assert s.confirmed()
    c = s.c
    for _ in range(80):                                                 # no FC ATTITUDE for 0.8 s
        s.t += 0.01; s.frame += 1
        c.on_pose(s.t, MocapSample(s.frame, s.t, s.t, 1, "quad", 1, (1e-6 * (s.frame % 3), 0, 0),
                                   quat_from_euler_zup(0, 0, 0)))
        c.tick(s.t)
    assert not c.confirmed(s.t) and "no fresh FC ATTITUDE" in "; ".join(c.flags(s.t)[1])


def test_f7_disarmed_withdrawal_sends_no_land_and_does_not_latch():
    s = YSim(); s.run(2.0); assert s.confirmed() and s.c.was_confirmed
    s.hdg = D(15.0); s.run(0.25)                                        # rotated, unseen by the FC
    assert s.confirmed()            # the 0.3 s FC-latency allowance still finds a pre-rotation mocap sample
    s.run(0.15)                                                         # ... but not after it
    assert not s.confirmed() and "yaw" in s.reasons()
    s.run(3.0)
    assert not s.lands() and s.c.latched is None
    s.hdg = 0.0; s.run(1.2)                                             # rotated back
    assert s.confirmed(), s.reasons()


def test_f7_armed_is_informational_only():
    """The most safety-critical property: once armed, a disagreement must NOT withdraw the confirmation (that would
    stop the heartbeat -> FC GCS failsafe LAND, and box=0 -> fly_trial WatcherLost LAND) and must not LAND."""
    s = YSim(); s.run(2.0); assert s.confirmed()
    s.armed = True; s.run(0.5)
    s.fc_yaw = D(20.0); s.run(5.0)
    assert s.confirmed(), s.reasons()
    assert s.c.flags(s.t)[0]["yaw"] == 1
    assert not s.lands() and s.c.latched is None
    assert any(a[0] == "LOG" and "INFORMATIONAL" in a[1] for a in s.acts)
    assert not any(a[0] == "ALERT" and "yaw" in a[1] for a in s.acts)
    assert s.c.yaw.max_diff_armed > 19.0
    s.armed = False; s.run(0.5)                                         # landed and disarmed: re-checked
    assert not s.confirmed() and "yaw" in s.reasons()
    assert not s.lands() and s.c.latched is None


# ---------------- the tie captured at the EKF-origin broadcast ----------------
def test_f7_origin_tie_capture_then_rotation_refuses():
    s = YSim(tie=None); s.hdg, s.fc_yaw = D(37.0), D(-120.0)            # arbitrary no-compass FC frame
    s.run(3.0)
    assert not s.confirmed() and "waiting for the FC's EKF-origin broadcast" in s.reasons()
    s.acts += s.c.on_fc_origin(s.t); s.run(1.2)
    assert s.c.yaw.tie is not None
    assert abs(math.degrees(s.c.yaw.tie) - (-157.0)) < 0.01
    s.run(1.2); assert s.confirmed(), s.reasons()
    s.hdg = D(52.0); s.run(0.4)                                         # +15 deg unseen by the FC
    assert not s.confirmed() and "yaw" in s.reasons()
    s.acts += s.c.on_fc_origin(s.t); s.run(2.0)                         # a later origin in the same boot: ignored
    assert not s.confirmed() and abs(math.degrees(s.c.yaw.tie) + 157.0) < 0.01
    s.hdg = D(37.0); s.run(1.2)
    assert s.confirmed(), s.reasons()


def test_f7_origin_tie_capture_wraps():
    s = YSim(tie=None); s.hdg, s.fc_yaw = D(-91.0), D(90.5)             # FC - mocap = 181.5 = -178.5
    s.run(1.0); s.acts += s.c.on_fc_origin(s.t); s.run(1.2)
    assert s.c.yaw.tie is not None and abs(abs(math.degrees(s.c.yaw.tie)) - 178.5) < 0.01
    s.run(1.2); assert s.confirmed(), s.reasons()


def test_f7_origin_tie_capture_fails_if_moving_or_mocap_invalid():
    s = YSim(tie=None); s.run(1.0); s.acts += s.c.on_fc_origin(s.t)
    for _ in range(100):
        s.hdg += D(0.1); s.fc_yaw += D(0.1); s.step()                   # carried round 10 deg during the capture
    s.run(1.0)
    assert s.c.yaw.tie is None and "TIE CAPTURE FAILED (vehicle not still" in s.reasons(), s.reasons()
    assert not s.confirmed()
    s2 = YSim(tie=None); s2.tracked = 0; s2.run(1.0); s2.acts += s2.c.on_fc_origin(s2.t); s2.run(0.5)
    s2.tracked = 1; s2.run(2.0)
    assert s2.c.yaw.tie is None and "TIE CAPTURE FAILED (mocap invalid" in s2.reasons(), s2.reasons()


def test_f7_fc_reboot_drops_the_tie():
    s = YSim(tie=None); s.run(1.0); s.acts += s.c.on_fc_origin(s.t); s.run(2.5)
    assert s.confirmed()
    s.boot_ms = 500; s.run(0.5)                                         # FC rebooted (time_boot_ms backwards)
    assert s.c.yaw.tie is None and not s.confirmed() and "FC rebooted" in s.reasons()
    s.acts += s.c.on_fc_origin(s.t); s.run(2.5)                         # the new boot's origin: a new tie
    assert s.confirmed(), s.reasons()


def test_f7_off_by_default_in_library_config():
    c = WatcherCore(Config(box=BOX))
    assert not c.c.require_yaw and c.on_fc_origin(0.0) == []


# ---------------- end to end: the real watcher process, the FakeFC ----------------
SYS = 211


def _origin(fc):
    fc.conn.mav.gps_global_origin_send(-353632610, 1491652300, 584000, int(time.time() * 1e6))


def test_e2e_f7_refuse_no_heartbeat_fc_cannot_arm_then_allowed(rig):
    rig.start(yaw_check="require", extra=("--yaw-tie", "origin"))
    rig.fc.att = (0.0, 0.0, 0.3)
    rig.feeder.quat = quat_from_euler_zup(0, 0, -0.1)                   # mocap heading +0.1 rad; tie = 0.2 rad
    wait_for(lambda: rig.fc.received("HEARTBEAT") or rig.fc.received("PARAM_REQUEST_READ"), 5)
    time.sleep(0.5)
    assert not rig.fc.received("HEARTBEAT", src=SYS)                    # no tie yet: never confirmed
    _origin(rig.fc)
    assert wait_for(lambda: rig.fc.received("HEARTBEAT", src=SYS), 6), rig.stoplog()
    assert "tie 11.46 deg captured" in rig.stoplog()
    rig.fc.att = (0.0, 0.0, 0.3 + D(15.0))                              # FC yaw now 15 deg off (F7)
    t0 = time.monotonic()
    assert wait_for(lambda: "yaw FC/mocap yaw disagree" in rig.stoplog(), 3), rig.stoplog()
    time.sleep(1.5)                                                     # heartbeat withdrawn
    assert not rig.fc.received("HEARTBEAT", src=SYS, since=t0 + 1.2)
    assert wait_for(lambda: rig.fc.fs_gcs, 5)                           # FC model: GCS failsafe latched (disarmed)
    ok, why = rig.fc.try_arm()
    assert not ok and "GCS failsafe" in why
    assert not rig.fc.lands()
    rig.fc.att = (0.0, 0.0, 0.3)                                        # agreement restored
    t1 = time.monotonic()
    assert wait_for(lambda: rig.fc.received("HEARTBEAT", src=SYS, since=t1), 5), rig.stoplog()
    assert wait_for(lambda: not rig.fc.fs_gcs, 5)
    assert rig.fc.try_arm()[0]


def test_e2e_f7_armed_disagreement_no_land_heartbeat_continues(rig):
    rig.start(yaw_check="require", extra=("--yaw-tie", "0"))
    assert wait_for(lambda: rig.fc.received("HEARTBEAT", src=SYS), 8), rig.stoplog()
    rig.fc.armed = True
    time.sleep(0.6)
    rig.fc.att = (0.0, 0.0, D(25.0))
    t0 = time.monotonic()
    time.sleep(4.5)
    hbs = [r[0] for r in rig.fc.received("HEARTBEAT", src=SYS, since=t0)]
    assert len(hbs) >= 3, hbs                                           # still sent every 1 s tick
    assert not rig.fc.lands() and rig.fc.armed and not rig.fc.fs_gcs
    assert "INFORMATIONAL" in rig.stoplog() and "BREACH" not in rig.stoplog()
