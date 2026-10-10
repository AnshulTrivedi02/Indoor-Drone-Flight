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
