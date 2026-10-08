#!/usr/bin/env python3
"""Write a "message tape" for the live adapter's bag-replay harness (fgo_cpp_live_replay): the bag's messages in
RECEIPT (bag) order with their header stamps - what the ROS 2 node's callbacks receive, in that order.

Usage (~/venv-fgo): make_tape.py <bag_dir> <out.f64> [--imu-stamps-from-export] [--heading-from-export <prefix>]
                                 [--armed-at T]
  --imu-stamps-from-export  replace each IMU header stamp by the offline dejittered stamp (imu_timing.dejitter_imu on
                            the same bag-order stream, exactly as fgo_replay.py), for the equivalence row; otherwise
                            the raw receipt stamps are kept (the live case: the adapter stamps from /imu/time_ref)
  --heading-from-export P   forward-camera headings from the export P.raw.f64 (kind 4 rows: psi), written as the
                            heading bridge's sent message (NED yaw = -psi, quality 100, angErr 0) and inserted
                            before the first bag message stamped later than them (as a live arrival would be)
  --armed-at T              insert an "armed" row before the first bag message stamped later than T (HEARTBEAT case)
Rows (9 float64): kind, header t, payload; kinds as in fgo_live_replay.cpp."""
import argparse, glob, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from imu_timing import dejitter_imu

ap = argparse.ArgumentParser()
ap.add_argument("bag"); ap.add_argument("out")
ap.add_argument("--imu-stamps-from-export", action="store_true")
ap.add_argument("--heading-from-export")
ap.add_argument("--armed-at", type=float)
a = ap.parse_args()
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
NAN = float("nan")
rows = []
with Reader(a.bag) as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/imu/time_ref", "/optical_flow/measurement", "/downward_lidar/range",
            "/attitude/angular_rates", "/tags/sent"]
    for con, _, raw in r.messages(connections=[conns[w] for w in want if w in conns]):
        m = ts.deserialize_cdr(raw, con.msgtype); t = st(m.header)
        if con.topic == "/imu/data_raw":
            rows.append([0, t, m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z,
                         m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z, NAN])
        elif con.topic == "/imu/time_ref":
            rows.append([7, t, m.time_ref.sec + m.time_ref.nanosec * 1e-9] + [NAN] * 6)
        elif con.topic == "/optical_flow/measurement":
            rows.append([3, t, m.flow_x_rad, m.flow_y_rad, float(bool(m.valid)), float(m.inlier_ratio)] + [NAN] * 3)
        elif con.topic == "/downward_lidar/range":
            rows.append([2, t, float(m.range)] + [NAN] * 6)
        elif con.topic == "/attitude/angular_rates":
            rows.append([1, t, m.vector.x, m.vector.y, m.vector.z] + [NAN] * 4)
        else:
            q = m.pose.pose.orientation
            rows.append([5, t, m.pose.pose.position.x, m.pose.pose.position.y, 2 * np.arctan2(q.z, q.w)] + [NAN] * 4)
if a.imu_stamps_from_export:
    ev = [(row[1], "imu" if row[0] == 0 else "other", None) for row in rows if row[0] in (0, 1, 2, 3)]
    new, stats = dejitter_imu(ev)
    stamps = iter([e[0] for e in new if e[1] == "imu"])
    for row in rows:
        if row[0] == 0:
            row[1] = next(stamps)
    print(f"[tape] IMU stamps dejittered (offline): period {stats['period_ms']:.5f} ms")
ext = []
if a.heading_from_export:
    R = np.fromfile(a.heading_from_export + ".raw.f64").reshape(-1, 9)
    ext += [[4, f[1], -f[2], 100.0, 0.0] + [NAN] * 4 for f in R[R[:, 0] == 4] if np.isfinite(f[2])]
if a.armed_at is not None:
    ext.append([8, a.armed_at, 1.0] + [NAN] * 6)
ext.sort(key=lambda e: e[1])
out, j = [], 0
for row in rows:
    while j < len(ext) and ext[j][1] < row[1]:
        out.append(ext[j]); j += 1
    out.append(row)
out += ext[j:]
np.asarray(out, np.float64).tofile(a.out)
kinds = np.array([o[0] for o in out])
print(f"[tape] {len(out)} rows: " + ", ".join(f"{k}:{int((kinds == k).sum())}" for k in sorted(set(kinds.tolist()))))
