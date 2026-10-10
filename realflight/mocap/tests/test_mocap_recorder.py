"""Offline tests of the mocap recorder and export (localhost UDP on an ephemeral port; no hardware).
Run: ~/venv-ardupilot/bin/python3 -m pytest realflight/mocap/tests -q"""
import json, math, os, socket, threading, time

import numpy as np
import pytest

from realflight.mocap import export as EX
from realflight.mocap import recorder as RC
from realflight.mocap.source import PACKET, UdpPoseSource, decode, encode


def _q_yaw(deg):            # (w, x, y, z) about z
    h = math.radians(deg) / 2
    return (math.cos(h), 0.0, 0.0, math.sin(h))


def test_packet_roundtrip_and_malformed():
    b = encode(42, 123.456, 3, "drone", 1, (1.0, 2.0, 3.0), (1.0, 0.0, 0.0, 0.0))
    assert len(b) == PACKET.size == 93
    s = decode(b, 5.0, 6.0)
    assert (s.frame_no, s.t_mocap, s.body_id, s.body_name, s.tracked, s.pos) == (42, 123.456, 3, "drone", 1, (1.0, 2.0, 3.0))
    assert decode(b[:-1], 0.0) is None
    assert decode(b"XXXX" + b[4:], 0.0) is None


class _Live:
    """A recorder running in a thread on an ephemeral UDP port; always closed by the test's finally."""

    def __init__(self, tmp_path, **kw):
        self.src = UdpPoseSource("127.0.0.1", 0)
        self.rec = RC.Recorder(str(tmp_path / "r.csv"), str(tmp_path / "r.meta.json"), {"test": True}, **kw)
        self.stop = False
        self.th = threading.Thread(target=RC.run, args=(self.src, self.rec, 20.0, lambda: self.stop), daemon=True)
        self.th.start()
        self.tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, b):
        self.tx.sendto(b, ("127.0.0.1", self.src.port)); time.sleep(0.0005)

    def finish(self):
        time.sleep(0.3); self.stop = True; self.th.join(5.0)
        assert not self.th.is_alive()
        self.rec.close(self.src.bad); self.src.close(); self.tx.close()
        return json.load(open(self.rec.meta_path))


def test_live_udp_counts_dupes_dropouts_malformed(tmp_path):
    L = _Live(tmp_path, body_id=1)
    try:
        sent = 0
        for k in range(300):
            if 100 <= k < 130:
                continue                                                  # a 30-frame dropout
            tr = 0 if 200 <= k < 210 else 1
            L.send(encode(k, 1000.0 + k * 0.01, 1, "drone", tr, (0.01 * k, 0.0, 1.0), _q_yaw(k * 0.1))); sent += 1
            if k == 10:
                L.send(encode(10, 1000.10, 1, "drone", 1, (0.1, 0.0, 1.0), _q_yaw(1.0)))       # duplicate
            if k == 60:
                L.send(encode(55, 1000.55, 1, "drone", 1, (0.55, 0.0, 1.0), _q_yaw(5.5)))      # out of order
                L.send(b"garbage"); L.send(b"XXXX" + bytes(89))                                  # 2 malformed
                L.send(encode(5, 0.0, 7, "other", 1, (0, 0, 0), (1, 0, 0, 0)))                  # another body
    finally:
        meta = L.finish()
    b = meta["bodies"]["1:drone"]
    assert meta["status"] == "complete"
    assert b["written"] == sent == 270
    assert b["duplicates_or_out_of_order"] == 2
    assert meta["malformed"] == 2 and meta["other_body_ignored"] == 1
    assert b["missing_frames"] == 30 and b["n_frame_gaps"] == 1
    assert b["n_time_gaps"] == 1 and abs(b["longest_time_gap_s"] - 0.31) < 1e-6
    assert b["not_tracked_rows"] == 10
    assert abs(b["rate_hz"] - 100.0) < 1e-6
    rows = open(tmp_path / "r.csv").read().splitlines()
    assert rows[0].split(",") == RC.COLUMNS and len(rows) == 271


def test_silence_detected(tmp_path):
    L = _Live(tmp_path, silence_s=0.2)
    try:
        for k in range(20):
            L.send(encode(k, k * 0.01, 1, "drone", -1, (0, 0, 1), (1, 0, 0, 0)))
        time.sleep(0.4)
        for k in range(20, 40):
            L.send(encode(k, k * 0.01, 1, "drone", -1, (0, 0, 1), (1, 0, 0, 0)))
    finally:
        meta = L.finish()
    assert len(meta["silences"]) == 1 and meta["silences"][0]["length_s"] >= 0.2


def test_export_y_up_frozen_untracked(tmp_path):
    raw = tmp_path / "raw.csv"
    with open(raw, "w") as f:
        f.write(",".join(RC.COLUMNS) + "\n")
        th = math.radians(30) / 2                          # 30 deg about the y-up world's UP axis (y)
        qy = (math.cos(th), 0.0, math.sin(th), 0.0)
        for k in range(200):
            t = 50.0 + k * 0.01
            tracked = -1
            p, q = (1.0 + 0.001 * k, 2.0, 3.0), qy
            if 100 <= k < 160:                             # frozen: bit-identical repeats for 0.6 s
                p = (1.0 + 0.001 * 100, 2.0, 3.0)
            f.write(f"{k},{t:.9f},{t + 7:.9f},{t + 1.7e9:.6f},1,drone,{tracked},{p[0]:.6f},{p[1]:.6f},{p[2]:.6f},"
                    f"{q[0]:.9f},{q[1]:.9f},{q[2]:.9f},{q[3]:.9f}\n")
        f.write(f"200,52.0,59.0,0,1,drone,0,9,9,9,1,0,0,0\n")      # NOT tracked: dropped
    out = tmp_path / "mocap.csv"
    s = EX.export(EX.load_raw(str(raw)), str(out), up="y")
    assert s["dropped_frozen"] == 59 and s["dropped_not_tracked"] == 1 and s["written"] == 141
    M = np.loadtxt(out, delimiter=",", comments="#")
    assert np.allclose(M[0, 1:4], [1.0, -3.0, 2.0])          # (x, y, z) y-up -> (x, -z, y)
    # orientation: 30 deg about up -> 30 deg yaw about z; scalar-last
    qx, qy_, qz, qw = M[0, 4:8]
    assert abs(qx) < 1e-9 and abs(qy_) < 1e-9 and abs(math.degrees(2 * math.atan2(qz, qw)) - 30.0) < 1e-6
    # the time column is t_mocap by default
    assert abs(M[0, 0] - 50.0) < 1e-9


def test_export_readable_by_mocap_align(tmp_path):
    ma = pytest.importorskip("scipy")      # mocap_align needs scipy + pymavlink (venv-ardupilot)
    import importlib.util, sys
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("mocap_align", os.path.join(here, "..", "..", "..", "eval", "mocap_align.py"))
    try:
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    except ImportError:
        pytest.skip("pymavlink not available")
    raw = tmp_path / "raw.csv"
    with open(raw, "w") as f:
        f.write(",".join(RC.COLUMNS) + "\n")
        for k in range(50):
            q = _q_yaw(k)
            f.write(f"{k},{k * 0.01:.9f},0,0,1,d,1,{k:.6f},0,1,{q[0]:.9f},{q[1]:.9f},{q[2]:.9f},{q[3]:.9f}\n")
    EX.export(EX.load_raw(str(raw)), str(tmp_path / "m.csv"), up="z")
    mo = mod.load_mocap(str(tmp_path / "m.csv"))
    assert mo["p"].shape == (50, 3) and np.allclose(mo["q"][5], [0, 0, math.sin(math.radians(5) / 2), math.cos(math.radians(5) / 2)])


# ---------------- restarts (2026-10-11 fix: a frame-counter reset used to drop the rest of the flight) ----------------
def _smp(k, t, frame=None, rx=None):
    from realflight.mocap.source import MocapSample
    return MocapSample(frame_no=k if frame is None else frame, t_mocap=t, t_rx=(t if rx is None else rx), body_id=1,
                       body_name="drone", tracked=1, pos=(0.01 * k, 0.0, 1.0), quat=_q_yaw(0.0), t_rx_wall=0.0)


def _rec(tmp_path, name="r"):
    return RC.Recorder(str(tmp_path / f"{name}.csv"), str(tmp_path / f"{name}.meta.json"), {"test": True}, body_id=1)


def test_forwarder_restart_large_jump_keeps_writing(tmp_path):
    rec = _rec(tmp_path)
    rec.accept([_smp(k, 1000.0 + 0.01 * k) for k in range(200)])
    seg2 = [_smp(200 + j, 1002.0 + 0.01 * j, frame=j) for j in range(100)]    # counter back to 0, mocap clock continues
    seg2.insert(51, _smp(250, 1002.50, frame=50))                             # a duplicate INSIDE segment 2
    rec.accept(seg2)
    rec.close()
    meta = json.load(open(tmp_path / "r.meta.json")); b = meta["bodies"]["1:drone"]
    assert b["written"] == 300 and b["duplicates_or_out_of_order"] == 1
    assert b["segments"] == 2 and len(b["restarts"]) == 1
    ev = b["restarts"][0]
    assert ev["kind"] == "frame_counter_reset" and ev["last_frame_before"] == 199 and ev["first_frame_after"] == 0
    assert abs(ev["last_t_mocap_before"] - 1001.99) < 1e-9 and abs(ev["first_t_mocap_after"] - 1002.0) < 1e-9
    assert b["n_clock_faults"] == 0 and b["n_time_gaps"] == 0 and b["n_frame_gaps"] == 0     # no spurious faults
    raw = EX.load_raw(str(tmp_path / "r.csv"))
    assert (raw["segment"] == 0).sum() == 200 and (raw["segment"] == 1).sum() == 100
    s = EX.export(raw, str(tmp_path / "m.csv"), up="z")                       # continuous mocap clock: allowed
    assert s["written"] == 300 and s["segments_in_log"] == [0, 1]


def test_restart_small_jump_held_run_is_written(tmp_path):
    rec = _rec(tmp_path)
    rec.accept([_smp(k, 10.0 + 0.01 * k) for k in range(50)])
    rec.accept([_smp(50 + j, 10.5 + 0.01 * j, frame=40 + j) for j in range(30)])   # counter back by 9 only
    rec.accept([_smp(5, 10.05)])                                                   # a late stray: still a duplicate
    rec.close()
    b = json.load(open(tmp_path / "r.meta.json"))["bodies"]["1:drone"]
    assert b["written"] == 80 and b["segments"] == 2 and b["duplicates_or_out_of_order"] == 1
    rows = open(tmp_path / "r.csv").read().splitlines()[1:]
    assert [int(r.split(",")[0]) for r in rows[50:53]] == [40, 41, 42]         # the held frames were not lost
    assert int(rows[50].split(",")[-1]) == 1


def test_short_backward_run_stays_duplicates(tmp_path):
    rec = _rec(tmp_path)
    rec.accept([_smp(k, 0.01 * k) for k in range(50)])
    rec.accept([_smp(k, 0.01 * k) for k in range(45, 50)])                     # 5 re-sent frames: not a restart
    rec.accept([_smp(k, 0.01 * k) for k in range(50, 60)])
    rec.close()
    b = json.load(open(tmp_path / "r.meta.json"))["bodies"]["1:drone"]
    assert b["written"] == 60 and b["duplicates_or_out_of_order"] == 5 and b["segments"] == 1


def test_mocap_clock_reset_export_refused_unless_segment_named(tmp_path):
    rec = _rec(tmp_path)
    rec.accept([_smp(k, 500.0 + 0.01 * k) for k in range(200)])
    rec.accept([_smp(k, 0.01 * (k - 200), frame=k - 200) for k in range(200, 300)])   # Motive restart: frames AND clock
    rec.close()
    b = json.load(open(tmp_path / "r.meta.json"))["bodies"]["1:drone"]
    assert b["written"] == 300 and b["segments"] == 2
    raw = EX.load_raw(str(tmp_path / "r.csv"))
    with pytest.raises(SystemExit) as e:
        EX.export(raw, str(tmp_path / "m.csv"), up="z")
    assert "--segment" in str(e.value)
    s = EX.export(raw, str(tmp_path / "m1.csv"), up="z", segment=1)
    assert s["written"] == 100 and s["segment_exported"] == 1
    s0 = EX.export(raw, str(tmp_path / "m0.csv"), up="z", segment=0)
    assert s0["written"] == 200


def test_clock_reset_with_increasing_frames_is_a_segment(tmp_path):
    rec = _rec(tmp_path)
    rec.accept([_smp(k, 100.0 + 0.01 * k) for k in range(100)])
    rec.accept([_smp(k, 0.01 * k) for k in range(100, 150)])                   # frames go on, the clock jumps back
    rec.close()
    b = json.load(open(tmp_path / "r.meta.json"))["bodies"]["1:drone"]
    assert b["written"] == 150 and b["n_clock_faults"] == 1 and b["segments"] == 2
    assert b["restarts"][0]["kind"] == "mocap_clock_reset"
