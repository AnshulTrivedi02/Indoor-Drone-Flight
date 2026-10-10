"""Unit tests of the decision logic (fake clock, no I/O). Gap ids refer to docs/real_flights_plan.md 7.2.0."""
import json
import math

from realflight.watcher.core import Config, WatcherCore
from realflight.watcher.mocap import MocapSample
from realflight.watcher.tests.fakes import quat_from_euler_zup

BOX = (-2, 2, -2, 2, 0, 2.5)


class Sim:
    """Drives a WatcherCore with a fake clock at 100 Hz mocap / 50 Hz FC attitude."""

    def __init__(self, **kw):
        kw.setdefault("box", BOX)
        kw.setdefault("require_identity", False)
        self.c = WatcherCore(Config(**kw))
        self.c.on_params(True, "ok")
        self.t = 0.0
        self.frame = 0
        self.pos, self.quat, self.tracked, self.name = (0.0, 0.0, 1.0), (1, 0, 0, 0), 1, None
        self.mocap_on = True
        self.att = (0.0, 0.0, 0.0)
        self.armed = False
        self.beacons = {}           # name -> progress (None = no progress field); remove key = silent
        self.acts = []
        self.jitter = True

    def step(self, dt=0.01):
        self.t += dt
        c, t = self.c, self.t
        self.acts += c.loop_start(t)
        if self.mocap_on:
            self.frame += 1
            p = self.pos
            if self.jitter:
                p = (p[0] + 1e-6 * (self.frame % 3), p[1], p[2])
            s = MocapSample(self.frame, t, t, 1, self.name or (c.c.body_name or "quad"), self.tracked, p, self.quat)
            self.acts += c.on_pose(t, s)
        if self.frame % 2 == 0:
            c.on_fc_attitude(t, *self.att)
        if self.frame % 10 == 0:
            c.on_fc_heartbeat(t, self.armed)
            for n, prog in self.beacons.items():
                c.on_beacon(t, json.dumps({"n": n, "seq": 1, "prog": prog}).encode())
        self.acts += c.tick(t)

    def run(self, secs, dt=0.01, **kw):
        for _ in range(int(round(secs / dt))):
            self.step(dt)

    def lands(self):
        return [a for a in self.acts if a[0] == "LAND"]

    def confirmed(self):
        return self.c.confirmed(self.t)


# ---------------- G2: stale / untracked / frozen pose ----------------
def test_g2_confirms_only_after_recover_s_of_fresh_poses():
    s = Sim(recover_s=2.0)
    s.run(1.9)
    assert not s.confirmed()
    s.run(0.2)
    assert s.confirmed()


def test_g2_stale_pose_lands_within_stale_s():
    s = Sim(); s.run(3.0); assert s.confirmed()
    s.mocap_on = False
    t_last = s.t
    s.run(0.45); assert s.confirmed() and not s.lands()
    s.run(0.1)
    assert not s.confirmed()
    assert len(s.lands()) == 1 and "stale" in s.lands()[0][1]
    assert s.c.latched is not None
    assert s.t - t_last <= 0.5 + 0.06


def test_g2_untracked_flag_is_stale_immediately():
    s = Sim(); s.run(3.0)
    s.tracked = 0
    s.run(0.02)
    assert not s.confirmed() and len(s.lands()) == 1 and "NOT TRACKED" in s.lands()[0][1]


def test_g2_frozen_pose_without_tracked_flag_is_stale():
    s = Sim(); s.tracked = -1; s.run(3.0); assert s.confirmed()
    s.jitter = False                                   # bit-identical poses, frames still arriving
    s.run(0.45); assert s.confirmed()
    s.run(0.2)
    assert not s.confirmed() and "frozen" in s.lands()[0][1]


def test_g2_identical_poses_with_tracked_flag_stay_fresh():
    s = Sim(); s.jitter = False; s.run(5.0)
    assert s.confirmed() and not s.lands()


def test_g2_recovery_needs_disarmed_and_recover_s_and_sends_no_second_land():
    s = Sim(recover_s=2.0); s.armed = True; s.run(3.0); assert s.confirmed()
    s.mocap_on = False; s.run(1.0)
    assert len(s.lands()) == 1
    s.mocap_on = True; s.run(5.0)                      # stream back, FC still armed: stays latched
    assert not s.confirmed() and len(s.lands()) == 1
    s.armed = False; s.run(1.9)
    assert not s.confirmed()
    s.run(0.3)
    assert s.confirmed() and len(s.lands()) == 1


def test_g2_never_received_does_not_land():
    s = Sim(); s.mocap_on = False; s.run(3.0)
    assert not s.confirmed() and not s.lands()


# ---------------- G3: rigid-body identity ----------------
def test_g3_wrong_body_name_samples_are_ignored():
    s = Sim(body_name="quad"); s.name = "other"; s.run(3.0)
    assert not s.confirmed() and s.c.wrong_bodies == {"other#1": 300}


def _hand_motion(s, wrong_body=False):
    """B6: hand roll ~10 deg, then hand yaw 90 deg. FC attitude follows the vehicle; the mocap follows the vehicle
    only for the right body."""
    yaw0, off = 0.0, 1.234                              # FC FRD yaw = -yaw_zup + an arbitrary constant offset
    for i in range(300):                                # roll up to 10 deg and back over 3 s
        r = math.radians(10) * math.sin(math.pi * i / 300)
        s.att = (r, 0.0, -yaw0 + off)
        if not wrong_body:
            s.quat = quat_from_euler_zup(r, 0.0, yaw0)
        s.step()
    for i in range(200):                                # yaw +90 deg (z-up CCW) over 2 s, then hold 1 s
        y = yaw0 + math.radians(90) * min(1.0, i / 100)
        s.att = (0.0, 0.0, -y + off)
        if not wrong_body:
            s.quat = quat_from_euler_zup(0.0, 0.0, y)
        s.step()


def test_g3_identity_proven_by_hand_motion_with_the_right_body():
    s = Sim(require_identity=True)
    s.att = (0.0, 0.0, 1.234)
    s.run(3.0)
    assert not s.confirmed() and s.c.ident.state == "unproven"     # level and still: nothing proven
    _hand_motion(s)
    assert s.c.ident.state == "confirmed", s.c.ident.why
    s.run(0.1)
    assert s.confirmed()


def test_g3_identity_fails_with_a_wrong_body_and_never_confirms_or_lands():
    s = Sim(require_identity=True)
    s.att = (0.0, 0.0, 1.234)
    s.run(3.0)
    _hand_motion(s, wrong_body=True)
    assert s.c.ident.state == "failed" and "roll/pitch" in s.c.ident.why
    s.run(2.0)
    assert not s.confirmed() and not s.lands()


def test_g3_identity_fails_when_only_yaw_is_moved_on_a_wrong_body():
    s = Sim(require_identity=True, id_rp_excite_deg=30.0)            # roll proof impossible: isolate the yaw rule
    s.run(1.0)
    for i in range(200):
        s.att = (0.0, 0.0, -math.radians(90) * min(1.0, i / 100)); s.step()
    assert s.c.ident.state == "failed" and "yaw" in s.c.ident.why


def test_g3_identity_disagreement_after_proof_is_only_alerted():
    s = Sim(require_identity=True); s.att = (0.0, 0.0, 1.234); s.run(1.0); _hand_motion(s)
    assert s.c.ident.state == "confirmed"
    s.att = (math.radians(20), 0.0, 0.0); s.run(1.0)
    assert s.confirmed() and not s.lands()
    assert any(a[0] == "ALERT" and "identity" in a[1] for a in s.acts)


# ---------------- G4 / G10: box incl. height, tilt, one LAND per episode ----------------
def test_g10_height_limit_top_and_bottom():
    for z in (2.6, -0.1):
        s = Sim(); s.run(3.0)
        s.pos = (0.0, 0.0, z); s.step()
        assert len(s.lands()) == 1 and "box left" in s.lands()[0][1] and not s.confirmed()


def test_g4_xy_breach_on_the_first_pose_outside():
    s = Sim(); s.run(3.0)
    s.pos = (2.01, 0.0, 1.0); s.step()                 # one pose
    assert len(s.lands()) == 1


def test_g4_tilt_breach():
    s = Sim(); s.run(3.0)
    s.quat = quat_from_euler_zup(math.radians(61), 0, 0); s.step()
    assert len(s.lands()) == 1 and "tilt" in s.lands()[0][1]


def test_g4_one_land_per_episode_then_a_new_episode_after_disarm():
    s = Sim(recover_s=1.0); s.armed = True; s.run(2.0)
    s.pos = (3.0, 0.0, 1.0); s.run(0.5)                # many outside poses
    s.pos = (0.0, 0.0, 3.0); s.run(0.5)                # and above the top
    s.mocap_on = False; s.run(1.0); s.mocap_on = True  # and a stale spell
    assert len(s.lands()) == 1
    s.pos = (0.0, 0.0, 1.0); s.armed = False; s.run(1.5)
    assert s.confirmed()
    s.pos = (3.0, 0.0, 1.0); s.step()
    assert len(s.lands()) == 2


def test_g4_breach_before_any_confirmation_latches_without_land():
    s = Sim(); s.pos = (3.0, 0.0, 1.0); s.run(1.0)
    assert not s.lands() and not s.confirmed()


# ---------------- G7 / G8: dependency liveness ----------------
def test_g7_dependency_silence_lands():
    s = Sim(deps=("flow",)); s.beacons = {"flow": None}; s.run(3.0); assert s.confirmed()
    del s.beacons["flow"]
    s.run(0.9); assert s.confirmed()
    s.run(0.3)
    assert not s.confirmed() and len(s.lands()) == 1 and "flow" in s.lands()[0][1]


def test_g7_hung_dependency_detected_by_progress():
    s = Sim(deps=("flow",)); s.beacons = {"flow": 1}
    for i in range(300):
        s.beacons["flow"] = i; s.step()
    assert s.confirmed()
    s.run(1.9); assert s.confirmed()                    # beacons continue, counter frozen
    s.run(0.3)
    assert not s.confirmed() and "hung" in s.lands()[0][1]


def test_g7_dependency_never_seen_blocks_without_land():
    s = Sim(deps=("flow",)); s.run(3.0)
    assert not s.confirmed() and not s.lands()
    assert s.c.flags(s.t)[0]["bridge"] == 0 and s.c.flags(s.t)[0]["box"] == 1


def test_g8_dep_loss_stop_maps_to_land():
    s = Sim(deps=("flow",), dep_loss="stop"); s.beacons = {"flow": None}; s.run(3.0)
    del s.beacons["flow"]; s.run(1.5)
    assert len(s.lands()) == 1 and "mapped to LAND" in s.lands()[0][1]


# ---------------- watcher self-stall (B3b), sysid collision (G11), FC params / link (G5, G6) ----------------
def test_stall_latches_without_land_and_stays_withdrawn_while_armed():
    s = Sim(); s.armed = True; s.run(3.0); assert s.confirmed()
    s.t += 2.0                                         # the process was stopped for 2 s (SIGSTOP)
    acts = s.c.loop_start(s.t)
    assert any("stalled" in a[1] for a in acts) and not any(a[0] == "LAND" for a in acts)
    assert not s.confirmed()
    s.run(3.0)
    assert not s.confirmed() and not s.lands()


def test_sysid_collision_latches():
    s = Sim(); s.run(3.0)
    s.acts += s.c.on_sysid_collision(s.t, "HEARTBEAT from 211")
    assert not s.confirmed() and not s.lands()


def test_fc_params_and_link_gate_confirmation():
    s = Sim(); s.c.on_params(False, "MAV_GCS_SYSID=255"); s.run(3.0)
    assert not s.confirmed()
    s.c.on_params(True, "ok"); s.run(0.1)
    assert s.confirmed()
    s2 = Sim()
    s2.c.on_fc_heartbeat = lambda *a: None             # FC never heard
    s2.run(3.0)
    assert not s2.confirmed()


def test_flags_tokens_are_single_key_value():
    s = Sim(); s.run(3.0)
    f, _ = s.c.flags(s.t)
    assert set(f) >= {"box", "bridge"} and all(v in (0, 1) for v in f.values())


def test_g3_slow_fc_yaw_drift_does_not_fail_the_yaw_proof():
    s = Sim(require_identity=True); s.att = (0.0, 0.0, 1.234)
    for i in range(6000):                               # 60 s of FC yaw drift at 20 deg/min, mocap still
        s.att = (0.0, 0.0, 1.234 + math.radians(20) * i / 6000); s.step()
    assert s.c.ident.state == "unproven"
    s.att = (0.0, 0.0, 1.234 + math.radians(20))
    _hand_motion_from(s, s.att[2])
    assert s.c.ident.state == "confirmed", s.c.ident.why


def _hand_motion_from(s, fc_yaw0):
    for i in range(300):
        r = math.radians(10) * math.sin(math.pi * i / 300)
        s.att = (r, 0.0, fc_yaw0); s.quat = quat_from_euler_zup(r, 0.0, 0.0); s.step()
    for i in range(200):
        y = math.radians(90) * min(1.0, i / 100)
        s.att = (0.0, 0.0, fc_yaw0 - y); s.quat = quat_from_euler_zup(0.0, 0.0, y); s.step()
