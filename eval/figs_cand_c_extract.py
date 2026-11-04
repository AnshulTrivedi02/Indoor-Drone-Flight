#!/usr/bin/env python3
"""GROUP C (D124 candidates) -- bag extraction helper for the E3 tag-map candidates (C05/C06).

Reads ONLY /ground_truth/pose from three stored ROS2 bags (T_A_r1, T_A_r2, T_A_r3 -- the Experiment 3 flights
also reused by Extension E3), exactly as eval/figs_walkthrough_flights.py's ex_room() does (same topic, same bag
path, same (t, x, y) extraction; the dataflash/XKF1 half of ex_room() is NOT needed here and is not read, so this
script does not depend on pymavlink). Caches the result as .npz under ~/thesis_data/cand_c_cache so the plotting
script (eval/figs_cand_c.py) never touches a bag directly.

STORED OUTPUTS ONLY. Run under heavy.py, per the candidates brief:
  python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "cand-c E3 map bag extraction" -- \\
      /home/makerspace/venv-evo/bin/python eval/figs_cand_c_extract.py

Usage: /home/makerspace/venv-evo/bin/python eval/figs_cand_c_extract.py
"""
import os

import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

TD = os.path.expanduser("~/thesis_data/trials")
CACHE = os.path.expanduser("~/thesis_data/cand_c_cache")
os.makedirs(CACHE, exist_ok=True)

RUNS = ["T_A_r1", "T_A_r2", "T_A_r3"]


def ex_ground_truth(tr):
    """(t, x East, y North) of /ground_truth/pose, exactly as figs_walkthrough_flights.py's ex_room() reads it."""
    ts = get_typestore(Stores.ROS2_JAZZY)
    G = []
    bag = f"{TD}/{tr}/bag"
    with Reader(bag) as r:
        cs = {c.topic: c for c in r.connections}
        for con, _, raw in r.messages(connections=[cs["/ground_truth/pose"]]):
            m = ts.deserialize_cdr(raw, con.msgtype)
            G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y))
    return np.array(G)


def main():
    for tr in RUNS:
        p = os.path.join(CACHE, f"gt_{tr}.npz")
        if os.path.exists(p):
            print(f"cached: gt_{tr}.npz")
            continue
        G = ex_ground_truth(tr)
        np.savez(p, G=G)
        print(f"wrote gt_{tr}.npz ({len(G)} samples)")


if __name__ == "__main__":
    main()
