#!/usr/bin/env python3
"""GROUP C candidate figure C08 (E6 mapping flights, figure-of-eight route) -- bag extraction helper.

Reads ONLY /ground_truth/pose (t, x East, y North, z Up; world/Gazebo ENU frame -- the same frame as the commanded
route in docs/thesis/tier1/scores/e6_route_E6M_fig8_<r>.json and the tag maps in docs/thesis/tier1/e6/maps/, per
eval/e6_maps.py's own frame statement: "world (Gazebo ENU) = tag-0 frame + (-3, -3), yaw 0") from the three E6
mapping-flight bags (E6M_fig8_r1b, E6M_fig8_r2, E6M_fig8_r3). Caches the result as .npz under
~/thesis_data/cand_e6route_cache so the plotting script (eval/figs_cand_e6route.py) never touches a bag directly.
No trimming to "airborne" is done here -- the full (t, x, y, z) series is cached, and the plotting script decides
the takeoff/landing window from z (so that decision stays visible and checkable in the script that draws the figure,
not hidden in this extraction step).

STORED OUTPUTS ONLY. Run under heavy.py, per the candidates brief:
  python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "cand-e6route bag extraction" -- \\
      /home/makerspace/venv-evo/bin/python eval/figs_cand_e6route_extract.py

Usage: /home/makerspace/venv-evo/bin/python eval/figs_cand_e6route_extract.py
"""
import os

import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

TD = os.path.expanduser("~/thesis_data/trials")
CACHE = os.path.expanduser("~/thesis_data/cand_e6route_cache")
os.makedirs(CACHE, exist_ok=True)

RUNS = ["E6M_fig8_r1b", "E6M_fig8_r2", "E6M_fig8_r3"]


def ex_ground_truth(tr):
    """(t, x East, y North, z Up) of /ground_truth/pose, full flight, no trimming."""
    ts = get_typestore(Stores.ROS2_JAZZY)
    G = []
    bag = f"{TD}/{tr}/bag"
    with Reader(bag) as r:
        cs = {c.topic: c for c in r.connections}
        for con, _, raw in r.messages(connections=[cs["/ground_truth/pose"]]):
            m = ts.deserialize_cdr(raw, con.msgtype)
            G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y,
                       m.pose.position.z))
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
