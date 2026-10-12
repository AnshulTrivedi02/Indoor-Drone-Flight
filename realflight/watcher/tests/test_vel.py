"""M2 pre-arm EKF velocity check (velcheck.py; F8 mitigation M2, RULING (user, 2026-10-12)). Unit tests with a fake
clock (core level) and end-to-end tests with the FakeFC (watcher subprocess)."""
import math
import time

from realflight.watcher.core import Config, WatcherCore
from realflight.watcher.mocap import MocapSample
from realflight.watcher.tests.fakes import quat_from_euler_zup, wait_for

BOX = (-2, 2, -2, 2, 0, 2.5)


class VSim:
    """WatcherCore at 100 Hz mocap / 10 Hz FC LOCAL_POSITION_NED / 5 Hz FC heartbeat, fake clock. `vel` is the FC's
    EKF velocity (NED, m/s); `mvel` moves the mocap body (m/s, watch frame)."""

    def __init__(self, **kw):
        kw.setdefault("box", BOX)
        kw.setdefault("require_identity", False)
        kw.setdefault("recover_s", 0.5)
        self.c = WatcherCore(Config(require_vel=True, **kw))
        self.c.on_params(True, "ok")
        self.t, self.frame, self.n = 0.0, 0, 0
        self.p = [0.0, 0.0, 0.2]
        self.mvel = (0.0, 0.0, 0.0)
        self.vel = (0.0, 0.0, 0.0)
        self.lpn_on = True
        self.tracked = 1
        self.mocap_on = True
        self.armed = False
        self.acts = []

    def step(self, dt=0.01):
        self.t += dt
        self.n += 1
        c, t = self.c, self.t
        self.acts += c.loop_start(t)
        for i in range(3):
            self.p[i] += self.mvel[i] * dt
        if self.mocap_on:
            self.frame += 1
            p = (self.p[0] + 1e-4 * math.sin(self.frame), self.p[1], self.p[2])   # 0.1 mm mocap noise
            self.acts += c.on_pose(t, MocapSample(self.frame, t, t, 1, "quad", self.tracked, p,
                                                  quat_from_euler_zup(0, 0, 0)))
        if self.n % 10 == 0 and self.lpn_on:
            self.acts += c.on_fc_lpn(t, *self.vel)
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


def test_m2_pass_after_5s_still_and_slow_not_before():
    s = VSim(); s.run(4.5)
    assert not s.confirmed() and "vel EKF |v| < 0.2 m/s and vehicle still, held < 5.0 s" in s.reasons(), s.reasons()
    s.run(1.2)
    assert s.confirmed(), s.reasons()
    s2 = VSim(); s2.vel = (0.12, -0.1, 0.05); s2.run(6.0)              # |v| = 0.164 < 0.2
    assert s2.confirmed(), s2.reasons()


def test_m2_f8_ground_runaway_refuses_arming():
    """F8: the vehicle sits still (mocap stationary) while EKF3's velocity ramps on the ground (0.145 m/s^2, the F8
    B6b ramp) past 0.2 m/s: the confirmation is withdrawn (so no heartbeat: the FC cannot arm; box=0: the flight
    script refuses), with an ALERT, and no LAND and no latch (it is disarmed: not a breach)."""
    s = VSim(); s.run(6.0); assert s.confirmed()
    a = 0.145
    for _ in range(300):                                                # 3 s ramp: VE 0 -> 0.435 m/s
        s.vel = (0.0, s.vel[1] + a * 0.01, 0.0); s.step()
        if s.vel[1] < 0.19:
            assert s.confirmed(), (s.vel, s.reasons())
    assert not s.confirmed() and "vel EKF velocity |v| >= 0.2 m/s (F8)" in s.reasons(), s.reasons()
    assert s.c.vel.vnorm > 0.4
    assert s.c.flags(s.t)[0]["vel"] == 0 and s.c.flags(s.t)[0]["box"] == 0
    assert any(x[0] == "ALERT" and "arming refused (F8)" in x[1] for x in s.acts)
    s.run(20.0)                                                         # the runaway persists: refused throughout
    assert not s.confirmed()
    assert not s.lands() and s.c.latched is None


def test_m2_brief_spike_resets_the_5s_window():
    s = VSim(); s.run(4.0)
    assert not s.confirmed()
    s.vel = (0.25, 0.0, 0.0); s.step()                                  # until the next LPN sample (one sample)
    while s.n % 10 != 0:
        s.step()
    s.vel = (0.0, 0.0, 0.0)
    t_spike = s.t
    s.run(2.0)
    assert not s.confirmed() and "held < 5.0 s" in s.reasons(), s.reasons()   # the old window would have passed
    s.run(2.5)
    assert not s.confirmed()                                            # 4.5 s after the spike
    s.run(1.0)
    assert s.confirmed() and s.t - t_spike >= 5.0, s.reasons()


def test_m2_mocap_not_stationary_no_confirmation():
    """The vehicle must be still: a carried / creeping vehicle never confirms even with the EKF velocity at 0."""
    for v in (0.3, 0.06):
        s = VSim(); s.mvel = (v, 0.0, 0.0); s.run(8.0)
        assert not s.confirmed() and "not stationary" in s.reasons(), (v, s.reasons())
    s = VSim(); s.mvel = (0.0, 0.03, 0.0); s.run(6.0)                    # 0.03 m/s < 0.05: counts as still
    assert s.confirmed(), s.reasons()
    s = VSim(); s.mvel = (0.3, 0.0, 0.0); s.run(3.0); s.mvel = (0, 0, 0)  # set down: 5 s of stillness needed
    s.run(4.0); assert not s.confirmed()
    s.run(2.0); assert s.confirmed(), s.reasons()


def test_m2_stale_or_missing_local_position_ned_refuses():
    s = VSim(); s.lpn_on = False; s.run(8.0)                            # never received (no EKF origin)
    assert not s.confirmed() and "no LOCAL_POSITION_NED" in s.reasons(), s.reasons()
    s = VSim(); s.run(6.0); assert s.confirmed()
    s.lpn_on = False; s.run(0.7)                                        # stopped for 0.7 s > 0.5 s
    assert not s.confirmed() and "LOCAL_POSITION_NED stale" in s.reasons(), s.reasons()
    s.lpn_on = True; s.run(3.0)
    assert not s.confirmed()                                            # the 5 s restarts
    s.run(2.5); assert s.confirmed(), s.reasons()


def test_m2_mocap_invalid_refuses():
    s = VSim(); s.run(6.0); assert s.confirmed()
    s.tracked = 0; s.run(0.3)
    assert not s.confirmed() and "vel mocap pose not valid" in s.reasons(), s.reasons()
    s.tracked = 1; s.run(3.0)          # untracked after a confirmation is also a breach (latched episode); it clears
    assert not s.confirmed()           # only when every check, M2's 5 s included, has been good for recover_s
    s.run(4.0); assert s.confirmed(), s.reasons()


def test_m2_vertical_only_runaway_refused():
    """The 3-D norm: a vz-only error also refuses."""
    s = VSim(); s.run(6.0); assert s.confirmed()
    s.vel = (0.0, 0.0, -0.25); s.run(0.3)
    assert not s.confirmed() and "vel EKF velocity |v| >= 0.2" in s.reasons(), s.reasons()
    assert abs(s.c.vel.v[2] + 0.25) < 1e-9


def test_m2_armed_is_informational_only():
    """Once armed, a large EKF velocity and a moving vehicle must NOT withdraw the confirmation (that would stop the
    heartbeat -> FC GCS failsafe LAND, and box=0 -> fly_trial WatcherLost LAND) and must not LAND or ALERT."""
    s = VSim(); s.run(6.0); assert s.confirmed()
    s.armed = True; s.run(0.5)
    s.vel = (1.0, 0.5, -0.3); s.mvel = (0.5, 0.0, 0.0); s.run(3.0)
    assert s.confirmed(), s.reasons()
    assert s.c.flags(s.t)[0]["vel"] == 1
    assert not s.lands() and s.c.latched is None
    assert not any(x[0] == "ALERT" for x in s.acts)
    assert s.c.vel.max_v_armed > 1.0
    s.vel = (0.0, 0.0, 0.0); s.mvel = (0, 0, 0)
    s.armed = False; s.run(0.5)                                         # landed and disarmed: gated again
    assert not s.confirmed() and "vel" in s.reasons()
    s.run(5.5); assert s.confirmed(), s.reasons()
    assert not s.lands() and s.c.latched is None


def test_m2_off_by_default_in_library_config():
    c = WatcherCore(Config(box=BOX))
    assert not c.c.require_vel and c.on_fc_lpn(0.0, 5.0, 0, 0) == []


# ---------------- end to end: the real watcher process, the FakeFC ----------------
SYS = 211


def test_e2e_m2_runaway_withdraws_heartbeat_fc_refuses_then_allowed(rig):
    rig.start(vel_check="require")
    rig.fc.vel = (0.0, 0.0, 0.0)
    assert wait_for(lambda: rig.fc.received("HEARTBEAT", src=SYS), 10), rig.stoplog()
    assert "vel=1" in open(rig.out + "/watch_heartbeat").read()
    rig.fc.vel = (0.05, 0.45, 0.0)                                      # the EKF runaway, vehicle still (F8)
    t0 = time.monotonic()
    assert wait_for(lambda: "arming refused (F8)" in rig.stoplog(), 3), rig.stoplog()
    time.sleep(1.5)
    assert not rig.fc.received("HEARTBEAT", src=SYS, since=t0 + 1.2)    # heartbeat withdrawn
    assert wait_for(lambda: rig.fc.fs_gcs, 5)                           # FC model: GCS failsafe latched (disarmed)
    ok, why = rig.fc.try_arm()
    assert not ok and "GCS failsafe" in why
    assert not rig.fc.lands() and "BREACH" not in rig.stoplog()
    rig.fc.vel = (0.0, 0.01, 0.0)                                       # converged: 5 s of stillness, then allowed
    t1 = time.monotonic()
    assert wait_for(lambda: rig.fc.received("HEARTBEAT", src=SYS, since=t1), 9), rig.stoplog()
    assert time.monotonic() - t1 >= 4.5
    assert wait_for(lambda: not rig.fc.fs_gcs, 5)
    assert rig.fc.try_arm()[0]


def test_e2e_m2_no_lpn_never_confirms(rig):
    rig.start(vel_check="require")                                      # FakeFC sends no LOCAL_POSITION_NED (no origin)
    time.sleep(7.0)
    assert not rig.fc.received("HEARTBEAT", src=SYS), rig.stoplog()
    assert "no LOCAL_POSITION_NED" in rig.stoplog()


def test_e2e_m2_armed_runaway_no_land_heartbeat_continues(rig):
    rig.start(vel_check="require")
    rig.fc.vel = (0.0, 0.0, 0.0)
    assert wait_for(lambda: rig.fc.received("HEARTBEAT", src=SYS), 10), rig.stoplog()
    rig.fc.armed = True
    time.sleep(0.6)
    rig.fc.vel = (1.5, 0.0, 0.0)
    t0 = time.monotonic()
    time.sleep(4.5)
    hbs = [r[0] for r in rig.fc.received("HEARTBEAT", src=SYS, since=t0)]
    assert len(hbs) >= 3, hbs
    assert not rig.fc.lands() and rig.fc.armed and not rig.fc.fs_gcs
    assert "BREACH" not in rig.stoplog() and "arming refused" not in rig.stoplog()
