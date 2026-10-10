"""End-to-end: mocap_watch.py as a real subprocess, a FakeFC (pymavlink, loopback), a fake mocap stream, and beacon
subprocesses. Each test names the bench test (docs/real_flights_plan.md 7.2.1) whose watcher-side behaviour it
exercises offline. The FC's reaction comes from FakeFC's MODEL of ArduCopter; the real FC side is proven on the bench.
"""
import math
import os
import signal
import threading
import time

import pytest

from realflight.watcher.tests.fakes import quat_from_euler_zup, wait_for, watch_ok_copy

SYS = 211


def confirmed(rig, timeout=8.0):
    ok = wait_for(lambda: watch_ok_copy(rig.hb_file())[0] and rig.fc.received("HEARTBEAT", src=SYS), timeout)
    assert ok, f"never confirmed: {open(rig.hb_file()).read() if os.path.exists(rig.hb_file()) else 'no file'}\n" \
               + rig.stoplog()[-2000:]


def file_flags(rig):
    f = open(rig.hb_file()).read().split()
    return dict(kv.split("=") for kv in f[1:])


def last_hb(rig):
    hb = rig.fc.received("HEARTBEAT", src=SYS)
    return hb[-1][0] if hb else None


# ---------------- B0 / G5 / G9 ----------------
def test_b0_all_up_confirms_file_and_mavlink_heartbeat(rig):
    rig.start(deps=("flow",))
    rig.beacon("flow")
    confirmed(rig)
    n0 = len(rig.fc.received("HEARTBEAT", src=SYS)); time.sleep(2.2)
    assert len(rig.fc.received("HEARTBEAT", src=SYS)) - n0 >= 2           # ~1 Hz tick
    f = file_flags(rig)
    assert f["box"] == f["bridge"] == f["pose"] == f["fc"] == "1" and f["host"]
    assert not rig.fc.lands()


def test_b1b_dependency_down_never_confirms_and_sends_no_heartbeat(rig):
    rig.start(deps=("flow",))
    time.sleep(3.0)
    ok, why = watch_ok_copy(rig.hb_file())
    assert not ok and "bridge=0" in why
    assert not rig.fc.received("HEARTBEAT", src=SYS) and not rig.fc.lands()


def test_b1_bad_fc_params_never_confirm(rig):
    from realflight.watcher.tests.fakes import GOOD_PARAMS
    rig.start(fc_kwargs={"params": dict(GOOD_PARAMS, MAV_GCS_SYSID=255)})
    time.sleep(3.0)
    assert not watch_ok_copy(rig.hb_file())[0] and file_flags(rig)["fc"] == "0"
    assert not rig.fc.received("HEARTBEAT", src=SYS)
    assert "MAV_GCS_SYSID=255" in rig.stoplog()


# ---------------- B2 / B3: watcher killed, hung ----------------
def test_b2_watcher_sigkill_stops_both_layers(rig):
    rig.start(fc_kwargs={"armed": True})
    confirmed(rig)
    t_kill = time.monotonic()
    rig.w.send_signal(signal.SIGKILL); rig.w.wait()
    assert last_hb(rig) <= t_kill + 0.05
    # FC layer (B2b): our FC model disarms within FS_GCS_TIMEOUT 3 s + the 3 Hz check
    ev = wait_for(lambda: [e for e in rig.fc.events if "GCS failsafe" in e[1]], 5)
    assert ev and ev[0][0] - t_kill <= 3.5 and not rig.fc.armed
    # flight-script layer (B2a): the file goes stale within 3 s + one tick
    assert wait_for(lambda: not watch_ok_copy(rig.hb_file())[0], 4.2)


def test_b3b_watcher_sigstop_withdraws_and_never_lands_or_resumes_while_armed(rig):
    rig.start(fc_kwargs={"armed": True, "failsafe_model": False})
    confirmed(rig)
    rig.w.send_signal(signal.SIGSTOP); t_stop = time.monotonic()
    time.sleep(2.0)
    rig.w.send_signal(signal.SIGCONT); t_cont = time.monotonic()
    time.sleep(3.0)
    assert not rig.fc.received("HEARTBEAT", src=SYS, since=t_stop + 0.05), "heartbeat resumed after SIGCONT"
    assert not rig.fc.lands(), "a LAND/mode command was sent after SIGCONT"
    assert not watch_ok_copy(rig.hb_file())[0] and file_flags(rig)["latch"] == "1"
    assert "stalled" in rig.stoplog()
    # the episode clears only once the FC reports disarmed and all checks hold for recover_s
    rig.fc.armed = False
    assert wait_for(lambda: rig.fc.received("HEARTBEAT", src=SYS, since=t_cont + 3.0), 4)


def test_sigterm_exits_fail_closed(rig):
    rig.start()
    confirmed(rig)
    rig.w.send_signal(signal.SIGTERM); rig.w.wait(5); t = time.monotonic()
    assert file_flags(rig)["box"] == "0"
    time.sleep(1.5)
    assert not rig.fc.received("HEARTBEAT", src=SYS, since=t)


# ---------------- B4: box breach (height, G10) -> one LAND (G4) ----------------
@pytest.mark.parametrize("pos", [(0.0, 0.0, 2.6), (2.2, 0.0, 1.0)])
def test_b4_box_breach_sends_one_land_and_withdraws(rig, pos):
    rig.start(fc_kwargs={"armed": True, "failsafe_model": False})
    confirmed(rig)
    rig.feeder.pos = pos; t0 = time.monotonic()
    lands = wait_for(lambda: rig.fc.lands(), 2)
    assert lands and lands[0][0] - t0 <= 0.3, f"LAND latency {lands and lands[0][0] - t0}"
    time.sleep(2.0)
    assert len(rig.fc.lands()) == 1 and rig.fc.mode == 9
    assert not rig.fc.received("HEARTBEAT", src=SYS, since=lands[0][0] + 0.05)
    assert file_flags(rig)["box"] == "0"
    assert os.path.exists(os.path.join(rig.out, "BREACH.txt"))


def test_b4c_tilt_breach(rig):
    rig.start(fc_kwargs={"armed": True, "failsafe_model": False})
    confirmed(rig)
    rig.feeder.quat = quat_from_euler_zup(math.radians(65), 0, 0)
    assert wait_for(lambda: rig.fc.lands(), 2) and "tilt" in rig.stoplog()


# ---------------- B5: mocap stopped / untracked (G2) ----------------
def test_b5a_mocap_stream_stopped_lands_within_stale_limit(rig):
    rig.start(fc_kwargs={"armed": True, "failsafe_model": False})
    confirmed(rig)
    rig.feeder.paused = True; t0 = time.monotonic()
    lands = wait_for(lambda: rig.fc.lands(), 2)
    assert lands and 0.4 <= lands[0][0] - t0 <= 0.7, lands and lands[0][0] - t0
    assert "stale" in rig.stoplog()
    time.sleep(1.5)
    assert not rig.fc.received("HEARTBEAT", src=SYS, since=lands[0][0] + 0.05) and len(rig.fc.lands()) == 1


def test_b5b_untracked_flag_lands(rig):
    rig.start(fc_kwargs={"armed": True, "failsafe_model": False})
    confirmed(rig)
    rig.feeder.tracked = 0; t0 = time.monotonic()
    lands = wait_for(lambda: rig.fc.lands(), 2)
    assert lands and lands[0][0] - t0 <= 0.3 and "NOT TRACKED" in rig.stoplog()


def test_b5c_restored_stream_reconfirms_only_when_disarmed_after_recover_s(rig):
    rig.start(fc_kwargs={"armed": False}, recover_s=2.0)
    confirmed(rig)
    rig.feeder.paused = True
    wait_for(lambda: rig.fc.lands(), 2)
    time.sleep(0.5)
    rig.feeder.paused = False; t_back = time.monotonic()
    t_conf = wait_for(lambda: watch_ok_copy(rig.hb_file())[0] and time.monotonic(), 6)
    assert t_conf and t_conf - t_back >= 2.0
    assert len(rig.fc.lands()) == 1


# ---------------- B9: dependency loss (G7, G8) ----------------
@pytest.mark.parametrize("how,dep_loss", [("SIGSTOP", "land"), ("SIGKILL", "land"), ("SIGSTOP", "stop")])
def test_b9_dependency_loss_lands(rig, how, dep_loss):
    rig.start(deps=("flow",), extra=["--dep-loss", dep_loss], fc_kwargs={"armed": True, "failsafe_model": False})
    b = rig.beacon("flow")
    confirmed(rig)
    b.send_signal(getattr(signal, how)); t0 = time.monotonic()
    lands = wait_for(lambda: rig.fc.lands(), 3)
    assert lands and lands[0][0] - t0 <= 1.5, lands and lands[0][0] - t0
    assert file_flags(rig)["bridge"] == "0"
    if dep_loss == "stop":
        assert "mapped to LAND" in rig.stoplog()


def test_b9_hung_dependency_beacon_alive_but_no_progress(rig):
    rig.start(deps=("flow",), fc_kwargs={"armed": True, "failsafe_model": False})
    import subprocess, sys
    from realflight.watcher.tests.conftest import ROOT
    code = ("import sys,time; sys.path.insert(0,%r)\nfrom realflight.watcher.liveness import LivenessBeacon\n"
            "b=LivenessBeacon('flow',('127.0.0.1',%d)); t0=time.time(); i=0\n"
            "while True:\n i += 1 if time.time()-t0 < 4 else 0\n b.beat(i); time.sleep(0.1)\n") % (ROOT, rig.live_port)
    rig.procs.append(subprocess.Popen([sys.executable, "-c", code]))
    confirmed(rig)
    lands = wait_for(lambda: rig.fc.lands(), 8)
    assert lands and "hung" in rig.stoplog()


# ---------------- B6: wrong body (G3) ----------------
def test_b6_wrong_body_name_never_confirms(rig):
    rig.start(body_name="quad", feeder_body="other_object")
    time.sleep(3.0)
    assert not watch_ok_copy(rig.hb_file())[0] and not rig.fc.received("HEARTBEAT", src=SYS)
    rig.w.send_signal(signal.SIGTERM); rig.w.wait(5)
    assert "other_object" in open(os.path.join(rig.out, "mocap_watch_summary.txt")).read()


def _hand_motion(rig, move_mocap):
    """B6: hand roll 10 deg, then hand yaw 90 deg. The FC ATTITUDE follows the vehicle; the mocap follows only if
    the configured body IS the vehicle."""
    off = 0.7
    for i in range(300):
        r = math.radians(10) * math.sin(math.pi * i / 300)
        rig.fc.att = (r, 0.0, off)
        if move_mocap:
            rig.feeder.quat = quat_from_euler_zup(r, 0.0, 0.0)
        time.sleep(0.01)
    for i in range(200):
        y = math.radians(90) * min(1.0, i / 100)
        rig.fc.att = (0.0, 0.0, off - y)
        if move_mocap:
            rig.feeder.quat = quat_from_euler_zup(0.0, 0.0, y)
        time.sleep(0.01)


@pytest.mark.parametrize("right_body", [True, False])
def test_b6_identity_by_hand_motion(rig, right_body):
    rig.start(identity="require")
    rig.fc.att = (0.0, 0.0, 0.7)
    time.sleep(2.0)
    assert not watch_ok_copy(rig.hb_file())[0] and file_flags(rig)["id"] == "0"     # unproven at rest
    _hand_motion(rig, move_mocap=right_body)
    time.sleep(1.0)
    ok = watch_ok_copy(rig.hb_file())[0]
    rig.w.send_signal(signal.SIGTERM); rig.w.wait(5)
    summ = open(os.path.join(rig.out, "mocap_watch_summary.txt")).read()
    if right_body:
        assert ok and "identity=confirmed" in summ, summ
    else:
        assert not ok and "identity=failed" in summ and not rig.fc.received("HEARTBEAT", src=SYS), summ
    assert not rig.fc.lands()
