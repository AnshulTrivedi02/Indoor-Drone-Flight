"""Extract /ground_truth/pose (with orientation) and /imu/time_ref pairs from an unpacked scratch bag."""
import sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

bag, out = sys.argv[1], sys.argv[2]
ts = get_typestore(Stores.ROS2_JAZZY)
st = lambda s: s.sec + s.nanosec * 1e-9
G, P = [], []
with Reader(bag) as r:
    cs = [c for c in r.connections if c.topic in ("/ground_truth/pose", "/imu/time_ref")]
    for c, _, raw in r.messages(connections=cs):
        m = ts.deserialize_cdr(raw, c.msgtype)
        if c.topic == "/ground_truth/pose":
            p, q = m.pose.position, m.pose.orientation
            G.append((st(m.header.stamp), p.x, p.y, p.z, q.x, q.y, q.z, q.w))
        else:
            P.append((st(m.header.stamp), st(m.time_ref)))
np.savetxt(f"{out}_gt.tum", np.array(G), fmt="%.9f")
np.savetxt(f"{out}_timeref.txt", np.array(P), fmt="%.9f")
print(len(G), len(P))
