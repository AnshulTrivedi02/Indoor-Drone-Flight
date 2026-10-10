import sys, os, numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
ts = get_typestore(Stores.ROS2_JAZZY)
_msg = os.path.expanduser("~/thesis_ws/src/optical_flow_interfaces/msg/OpticalFlow.msg")
ts.register(get_types_from_msg(open(_msg).read(), "optical_flow_interfaces/msg/OpticalFlow"))
bag, out, tmax = sys.argv[1], sys.argv[2], float(sys.argv[3])
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
gt, fl, rg, att = [], [], [], []
want = {"/ground_truth/pose", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates"}
with Reader(bag) as r:
    conns = [c for c in r.connections if c.topic in want]
    t0 = None
    for con, t, raw in r.messages(connections=conns):
        if t0 is None:
            t0 = t
        if (t - t0) * 1e-9 > tmax:
            break
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/ground_truth/pose":
            p, q = m.pose.position, m.pose.orientation
            gt.append((st(m.header), p.x, p.y, p.z, q.w, q.x, q.y, q.z))
        elif con.topic == "/optical_flow/measurement":
            fl.append((st(m.header), m.flow_x_rad, m.flow_y_rad, m.feature_count, m.inlier_ratio, float(m.valid)))
        elif con.topic == "/downward_lidar/range":
            rg.append((st(m.header), m.range))
        else:
            att.append((st(m.header), m.vector.x, m.vector.y, m.vector.z))
np.savez(out, gt=np.array(gt), fl=np.array(fl), rg=np.array(rg), att=np.array(att))
print(len(gt), len(fl), len(rg), len(att))
