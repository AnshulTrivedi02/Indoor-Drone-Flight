#!/usr/bin/env python3
"""CANDIDATE THESIS FIGURES, GROUP E (extension-experiment and Experiment 4/5 PATH candidates): bag/dataflash-only
extraction, run ONCE under heavy.py.

Pre-populates ~/thesis_data/cand_e_cache/*.npz from bag reads and local dataflash (ardupilot.bin) reads only - no
estimator run, no replay, no simulation. The main generator (eval/figs_cand_e.py) reads these cached arrays and
never opens a bag or dataflash file itself.

COPIED (not imported) patterns:
  - _bag_open()/extract_room() ground-truth read: from eval/figs_cand_b_extract.py's own extract_room() (itself
    copied from eval/figs_walkthrough_flights.py's _bag_open()/ex_room()). Cached RAW (world frame): any tag-0 or
    wall-tag frame shift is applied by the generator, not here.
  - extract_xkf1(): same as eval/figs_cand_b_extract.py's extract_xkf1(), generalised to any trial, core 0 only.
  - extract_xuko()/extract_xfgo(): COPIED from eval/h_score.py's own dataflash read (XUKO: the flying UKF port's
    current-time output, NED W frame; XFGO: the flying FGO node's output, kept only where OV == 1, "output valid").

Needed for:
  - E2 (fewer tags, loop closure): ground truth of T_B_r1, T_C_r1, T_D_r1 (T_A_r1 ground truth is Experiment 3's,
    listed below; the FGO tracks themselves are already stored .tum files under ~/thesis_data/tier1/).
  - E3 (wrong tag IDs) and the window sweep (E4 tier-1 extension): ground truth of T_A_r1 (shared by both; the FGO
    tracks are already stored .tum files).
  - E5 (UKF landmark states vs FGO): ground truth of T_A_r1 (shared with the above; both estimators' tracks are
    already stored .tum files).
  - Experiment 4 (outdoor-indoor): ground truth AND /imu/time_ref of O_r1 (for the SITL-to-bag clock map), plus its
    XKF1 dataflash (EKF3's own track; UKF/FGO tracks are already stored .tum files, no read needed for those).
  - Experiment 5 (tag hold): ground truth AND /imu/time_ref of H_s1far_r1, H_s2v2_r1, H_s3v2_r1, plus each one's own
    flying-estimator dataflash message (XKF1 core 0 for EKF3, XUKO for the UKF port, XFGO (OV==1) for the FGO node).

Usage: /home/makerspace/venv-fgo/bin/python eval/figs_cand_e_extract.py"""
import math, os, shutil, subprocess, sys, tempfile
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

TD = os.path.expanduser("~/thesis_data/trials")
CACHE = os.path.expanduser("~/thesis_data/cand_e_cache")
os.makedirs(CACHE, exist_ok=True)
tempfile.tempdir = CACHE

ROOM_ONLY = ["T_B_r1", "T_C_r1", "T_D_r1", "T_A_r1"]          # ground truth only, no time_ref/dataflash needed
ROOM_WITH_TR = ["O_r1", "H_s1far_r1", "H_s2v2_r1", "H_s3rp_r2"]  # ground truth + /imu/time_ref (dataflash clock map)
# H_s3rp_r2 (corrected priors, the CURRENT FGO-flying hold set) replaces H_s3v2_r1 (superseded original priors):
# H_s3rp_r1 has no stored bag, but H_s3rp_r2 and H_s3rp_r3 do.
XKF1_TRIALS = ["O_r1", "H_s1far_r1"]
XUKO_TRIALS = ["H_s2v2_r1"]
XFGO_TRIALS = ["H_s3rp_r2"]


def _bag_open(tr):
    bag = f"{TD}/{tr}/bag"
    if not os.path.exists(f"{bag}/bag_0.db3") and os.path.exists(f"{bag}/bag_0.db3.zst"):
        tmp = tempfile.mkdtemp(prefix="cand_e_bag_")
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
    """EKF3's own logged position (dataflash ardupilot.bin, core 0), not a bag."""
    mv = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); k1 = []
    while True:
        r = mv.recv_match(type=["XKF1"])
        if r is None:
            break
        if r.C == 0:
            k1.append((r.TimeUS / 1e6, r.PN, r.PE, math.radians(90.0 - r.Yaw)))
    return dict(K1=np.array(k1))


def extract_xuko(tr):
    """The flying UKF port's own current-time output (dataflash XUKO, NED W frame), COPIED from eval/h_score.py."""
    mv = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); xuko = []
    while True:
        r = mv.recv_match(type=["XUKO"])
        if r is None:
            break
        xuko.append((r.TimeUS / 1e6, r.PN, r.PE, math.radians(90.0 - r.Yaw)))
    return dict(K1=np.array(xuko))


def extract_xfgo(tr):
    """The flying FGO node's own output, kept only where OV == 1 ('output valid'), COPIED from eval/h_score.py."""
    mv = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); xfgo = []
    while True:
        r = mv.recv_match(type=["XFGO"])
        if r is None:
            break
        if r.OV == 1:
            xfgo.append((r.TimeUS / 1e6, r.PN, r.PE, math.radians(90.0 - r.Yaw)))
    return dict(K1=np.array(xfgo))


def main():
    for tr in ROOM_ONLY:
        p = os.path.join(CACHE, f"room_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: {tr}"); continue
        d = extract_room(tr, need_time_ref=False)
        np.savez(p, **d)
        print(f"ok {tr}: {len(d['G'])} ground-truth samples")
    for tr in ROOM_WITH_TR:
        p = os.path.join(CACHE, f"room_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: {tr}"); continue
        d = extract_room(tr, need_time_ref=True)
        np.savez(p, **d)
        print(f"ok {tr}: {len(d['G'])} ground-truth samples, {len(d['TR'])} time_ref samples")
    for tr in XKF1_TRIALS:
        p = os.path.join(CACHE, f"xkf1_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: xkf1 {tr}"); continue
        d = extract_xkf1(tr)
        np.savez(p, **d)
        print(f"ok xkf1 {tr}: {len(d['K1'])} XKF1 samples")
    for tr in XUKO_TRIALS:
        p = os.path.join(CACHE, f"xuko_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: xuko {tr}"); continue
        d = extract_xuko(tr)
        np.savez(p, **d)
        print(f"ok xuko {tr}: {len(d['K1'])} XUKO samples")
    for tr in XFGO_TRIALS:
        p = os.path.join(CACHE, f"xfgo_{tr}.npz")
        if os.path.exists(p):
            print(f"cached already: xfgo {tr}"); continue
        d = extract_xfgo(tr)
        np.savez(p, **d)
        print(f"ok xfgo {tr}: {len(d['K1'])} XFGO samples")


if __name__ == "__main__":
    main()
