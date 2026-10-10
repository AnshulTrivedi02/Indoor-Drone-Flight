"""G1 (mocap input + frames) and G7 (networked liveness, sidecars) unit tests. Loopback sockets on ephemeral ports."""
import json
import math
import signal
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np
import pytest

from realflight.watcher import mocap
from realflight.watcher.frames import FrameConverter, euler_frd, tilt_deg
from realflight.watcher.liveness import LivenessBeacon, LivenessMonitor, UdpLivenessSocket
from realflight.watcher.sidecars import ProcSidecar, TopicRateCore, proc_state
from realflight.watcher.tests.fakes import quat_from_euler_zup, wait_for


# ---------------- G1: frames ----------------
def test_g1_euler_signs_match_the_fc_frd_convention():
    conv = FrameConverter("z")
    _, R = conv.convert((0, 0, 0), quat_from_euler_zup(math.radians(10), 0, 0))       # right side down
    assert math.degrees(euler_frd(R)[0]) == pytest.approx(10, abs=1e-6)
    _, R = conv.convert((0, 0, 0), quat_from_euler_zup(0, math.radians(-10), 0))      # FLU pitch -10 = nose up
    assert math.degrees(euler_frd(R)[1]) == pytest.approx(10, abs=1e-6)
    _, R = conv.convert((0, 0, 0), quat_from_euler_zup(0, 0, math.radians(30)))       # CCW from above
    assert math.degrees(euler_frd(R)[2]) == pytest.approx(-30, abs=1e-6)              # FRD yaw is CW-positive
    _, R = conv.convert((0, 0, 0), quat_from_euler_zup(math.radians(61), 0, 0))
    assert tilt_deg(R) == pytest.approx(61, abs=1e-6)


def test_g1_y_up_conversion():
    conv = FrameConverter("y")
    p, R = conv.convert((1.0, 2.0, 3.0), (1, 0, 0, 0))     # y-up: height is mocap y
    assert np.allclose(p, (1.0, -3.0, 2.0))
    assert np.allclose(R, np.eye(3))
    # a y-up body rolled 10 deg about its forward (x) axis reads 10 deg roll after conversion
    c, s = math.cos(math.radians(5)), math.sin(math.radians(5))
    _, R = conv.convert((0, 0, 0), (c, s, 0, 0))
    assert math.degrees(euler_frd(R)[0]) == pytest.approx(10, abs=1e-6)


# ---------------- G1: packet codec and UDP adapter ----------------
def test_g1_packet_roundtrip_and_malformed():
    b = mocap.encode(7, 123.5, 3, "quad", 1, (1, 2, 3), (1, 0, 0, 0))
    assert len(b) == mocap.PACKET.size == 93
    s = mocap.decode(b, 10.0)
    assert (s.frame_no, s.t_mocap, s.body_id, s.body_name, s.tracked, s.pos, s.quat) == \
        (7, 123.5, 3, "quad", 1, (1.0, 2.0, 3.0), (1.0, 0.0, 0.0, 0.0))
    assert mocap.decode(b[:-1], 0) is None and mocap.decode(b"XXXX" + b[4:], 0) is None


def test_g1_udp_pose_source_receives_and_counts_bad_packets():
    src = mocap.UdpPoseSource("127.0.0.1", 0)
    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for i in range(5):
            tx.sendto(mocap.encode(i, time.time(), 1, "quad", 1, (0, 0, i), (1, 0, 0, 0)), ("127.0.0.1", src.port))
        tx.sendto(b"garbage", ("127.0.0.1", src.port))
        got = []
        wait_for(lambda: got.extend(src.poll()) or len(got) == 5, 2)
        assert [g.frame_no for g in got] == list(range(5)) and src.bad == 1
    finally:
        tx.close(); src.close()


def test_g1_pose_stamped_adapter_has_no_tracked_flag():
    msg = SimpleNamespace(header=SimpleNamespace(stamp=SimpleNamespace(sec=5, nanosec=500000000)),
                          pose=SimpleNamespace(position=SimpleNamespace(x=1, y=2, z=3),
                                               orientation=SimpleNamespace(w=1, x=0, y=0, z=0)))
    s = mocap.pose_stamped_to_sample(msg, "quad", 9, 1.0)
    assert s.tracked == -1 and s.t_mocap == 5.5 and s.pos == (1, 2, 3) and s.body_name == "quad"


# ---------------- G7: liveness ----------------
def test_g7_monitor_silence_progress_and_unknown():
    m = LivenessMonitor(["a", "b"], 1.0, 2.0)
    m.feed(json.dumps({"n": "a", "prog": 1}).encode(), 0.0)
    m.feed(json.dumps({"n": "zzz"}).encode(), 0.0)
    m.feed(b"not json", 0.0)
    st = m.status(0.5)
    assert st["a"][0] and not st["b"][0] and m.unknown == {"zzz": 1} and m.bad == 1
    for t in (0.5, 1.0, 1.5, 2.0, 2.5):                  # beacons keep coming, counter stuck at 1
        m.feed(json.dumps({"n": "a", "prog": 1}).encode(), t)
    assert "hung" in m.status(2.5)["a"][1]
    assert "silent" in m.status(4.0)["a"][1]


def test_g7_beacon_over_udp():
    sock = UdpLivenessSocket("127.0.0.1", 0)
    b = LivenessBeacon("flow", ("127.0.0.1", sock.port))
    try:
        b.beat(42)
        data = wait_for(lambda: sock.drain(), 2)
        m = json.loads(data[0])
        assert m["n"] == "flow" and m["prog"] == 42 and m["seq"] == 1
    finally:
        b.close(); sock.close()


def test_g7_proc_sidecar_detects_death_and_sigstop():
    sock = UdpLivenessSocket("127.0.0.1", 0)
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    sc = ProcSidecar("dep", ("127.0.0.1", sock.port), pid=p.pid)
    try:
        assert sc.step() and proc_state(p.pid) in "RS"
        p.send_signal(signal.SIGSTOP)
        assert wait_for(lambda: proc_state(p.pid) == "T", 2)
        assert not sc.step()                              # stopped (hung) -> no beacon
        p.send_signal(signal.SIGCONT)
        assert wait_for(lambda: sc.step(), 2)
        p.kill(); p.wait()
        assert not sc.step()                              # dead -> no beacon
    finally:
        try:
            p.send_signal(signal.SIGCONT); p.kill(); p.wait(2)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass
        sc.beacon.close(); sock.close()


def test_g7_topic_sidecar_core_reports_message_count():
    sock = UdpLivenessSocket("127.0.0.1", 0)
    core = TopicRateCore("flow_tracker", ("127.0.0.1", sock.port))
    try:
        for _ in range(3):
            core.on_msg()
        core.step()
        data = wait_for(lambda: sock.drain(), 2)
        assert json.loads(data[0])["prog"] == 3
    finally:
        core.beacon.close(); sock.close()
