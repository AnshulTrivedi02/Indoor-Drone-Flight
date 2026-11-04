#!/usr/bin/env python3
"""CANDIDATE THESIS FIGURES, GROUP B (decision D124): bag-only extraction, run ONCE under heavy.py.

Pre-populates ~/thesis_data/cand_b_cache/*.npz from bag reads only (no estimator run, no simulation). The main
generator (eval/figs_cand_b.py) reads these cached arrays and never opens a bag itself.

Needed for:
  - Experiment 3 (loop closure): ground truth /ground_truth/pose of T_A_r1, T_A_r2, T_A_r3, for the true-laps
    candidate and the FGO estimated-trajectory candidates (both already stored as .tum files, no bag needed for
    those). Cached RAW (world frame): the tag-0 shift is applied by the generator, not here, so the raw array is
    reusable for both the raw-world-frame truth figure and the tag-0-frame trajectory figures.
  - Experiment 4 (outdoor-indoor): ground truth AND /imu/time_ref of O_r1, O_r2, O_r3b (the SITL-to-bag clock map
    needs both), for the all-flights error-against-time candidates (the EKF3 XKF1 curve is read from the stored,
    already-local, ardupilot.bin dataflash file directly by the generator - not a bag, no cache entry needed here).

COPIED (not imported) from eval/figs_walkthrough_flights.py's _bag_open()/ex_room(): same bag-open/packed-bag
handling, same message fields read, same cache-key naming ("room_<trial>") so the generator's own identically-named
cached()/ex_room() transparently finds these entries and never re-opens a bag.

Usage: /home/makerspace/venv-evo/bin/python eval/figs_cand_b_extract.py"""
import math, os, shutil, subprocess, sys, tempfile
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

TD = os.path.expanduser("~/thesis_data/trials")
CACHE = os.path.expanduser("~/thesis_data/cand_b_cache")
os.makedirs(CACHE, exist_ok=True)
tempfile.tempdir = CACHE

T_FL = [f"T_A_r{i}" for i in (1, 2, 3)]
O_FL = ["O_r1", "O_r2", "O_r3b"]


def _bag_open(tr):
    bag = f"{TD}/{tr}/bag"
    if not os.path.exists(f"{bag}/bag_0.db3") and os.path.exists(f"{bag}/bag_0.db3.zst"):
        tmp = tempfile.mkdtemp(prefix="cand_b_bag_")
        shutil.copy(f"{bag}/metadata.yaml", tmp)
        subprocess.run(["zstd", "-q", "-d", f"{bag}/bag_0.db3.zst", "-o", f"{tmp}/bag_0.db3"], check=True)
        return tmp, tmp
    return bag, None


def extract_room(tr, need_time_ref):
    ts = get_typestore(Stores.ROS2_JAZZY)
    G, TR = [], []
    bag, tmp = _bag_open(tr)
    try:
        with Reader(bag) as r:
            cs = {c.topic: c for c in r.connections}
            topics = ["/ground_truth/pose"] + (["/imu/time_ref"] if need_time_ref else [])
            for con, _, raw in r.messages(connections=[cs[x] for x in topics if x in cs]):
                m = ts.deserialize_cdr(raw, con.msgtype)
                if con.topic == "/imu/time_ref":
                    TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
                    continue
                q = m.pose.orientation
                G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y,
                          math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    return dict(G=np.array(G), TR=np.array(TR))


def extract_xkf1(tr):
    """EKF3's own logged position (dataflash ardupilot.bin, core 0), not a bag - cached anyway for consistency (every
    flight-data read in this candidate set goes through the same heavy.py-protected extraction step)."""
    mv = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); k1 = []
    while True:
        r = mv.recv_match(type=["XKF1"])
        if r is None:
            break
        if r.C == 0:
            k1.append((r.TimeUS / 1e6, r.PE, r.PN))
    return dict(K1=np.array(k1))


def main():
    for tr in T_FL:
        p = os.path.join(CACHE, f"room_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: {tr}"); continue
        d = extract_room(tr, need_time_ref=False)
        np.savez(p, **d)
        print(f"ok {tr}: {len(d['G'])} ground-truth samples")
    for tr in O_FL:
        p = os.path.join(CACHE, f"room_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: {tr}"); continue
        d = extract_room(tr, need_time_ref=True)
        np.savez(p, **d)
        print(f"ok {tr}: {len(d['G'])} ground-truth samples, {len(d['TR'])} time_ref samples")
    for tr in O_FL:
        p = os.path.join(CACHE, f"xkf1_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: xkf1 {tr}"); continue
        d = extract_xkf1(tr)
        np.savez(p, **d)
        print(f"ok xkf1 {tr}: {len(d['K1'])} XKF1 samples")


if __name__ == "__main__":
    main()
