"""Dump bag topics needed for the tilt trace into an npz (diagnostic)."""
import sys, os, glob, numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
trial = sys.argv[1]; out = sys.argv[2]
D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/src/optical_flow_interfaces/msg/OpticalFlow.msg"))[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
R = {k: [] for k in ["imu", "flow", "rng", "tag", "gt", "att"]}
with Reader(f"{D}/bag") as r:
    conns = {c.topic: c for c in r.connections}
    print(sorted(conns))
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/tags/sent", "/ground_truth/pose",
            "/attitude/angular_rates"]
    for con, _, raw in r.messages(connections=[conns[w] for w in want if w in conns]):
        m = ts.deserialize_cdr(raw, con.msgtype); t = st(m.header)
        if con.topic == "/imu/data_raw":
            a, g = m.linear_acceleration, m.angular_velocity
            R["imu"].append((t, a.x, a.y, a.z, g.x, g.y, g.z))
        elif con.topic == "/optical_flow/measurement":
            R["flow"].append((t, m.flow_x_rad, m.flow_y_rad, float(m.valid), m.inlier_ratio, m.feature_count))
        elif con.topic == "/downward_lidar/range":
            R["rng"].append((t, m.range))
        elif con.topic == "/tags/sent":
            p = m.pose.pose.position; q = m.pose.pose.orientation
            R["tag"].append((t, p.x, p.y, 2 * np.arctan2(q.z, q.w)))
        elif con.topic == "/ground_truth/pose":
            p = m.pose.position; q = m.pose.orientation
            R["gt"].append((t, p.x, p.y, p.z, q.x, q.y, q.z, q.w))
        else:
            v = m.vector; R["att"].append((t, v.x, v.y, v.z))
np.savez(out, **{k: np.array(v) for k, v in R.items()})
print({k: len(v) for k, v in R.items()})
