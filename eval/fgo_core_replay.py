#!/usr/bin/env python3
"""Offline twin of the LIVE FGO node, for FG1 on shadow runs WITH heading (declared before fgo_shadow_half_b).
fgo_replay.py's heading arm reads the offline forward measurements (fwd_meas/), not the heading values the node
actually received (the heading bridge's sent ODOMETRY yaw, /forward_camera/heading_sent, which is not recorded in
the bag). This replay feeds the node core (fgo_node_core.FgoNodeCore) exactly as fgo_node.py does:
  - core settings as the node: window 0.25 s, LM 2, horizon 0.10 s, dejitter "causal", gap "causal", t_arm None,
    heading sigma 5 deg (fwd_sigma psi), chi-square gate 9;
  - every bag message (IMU, flow, range, attitude rates, /imu/time_ref) in bag RECEIPT order with its header stamp;
  - the sent headings from logs/heading_bridge.csv (rows with sent = 1), inserted at their send time t_sim_sent
    with stamp t_capture and psi = -yaw_ap, gated as fgo_node._hdg: quality >= 50 and >= 20 ms apart.
Writes <trial>/<out>/fgo_traj.tum (corridor frame, x y z + quaternion from roll/pitch/yaw) and ground_truth.tum
(from /ground_truth/pose), so eval/fgo_gate_check.py can use it as the FG1 reference.
Usage (~/venv-fgo): python3 eval/fgo_core_replay.py TRIAL [--no-heading] [--out fgo_core]"""
import argparse, csv, glob, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "estimators")); sys.path.insert(0, os.path.join(ROOT, "src", "estimators", "fgo"))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from fgo_node_core import FgoNodeCore
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--no-heading", action="store_true")
ap.add_argument("--out", default="fgo_core")
ap.add_argument("--save-npz", action="store_true", help="also save the heading gate log (fwd_log) and traj (D26)"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); OUT = f"{D}/{a.out}"; os.makedirs(OUT, exist_ok=True)
ts = get_typestore(Stores.ROS2_JAZZY)
ts.register(get_types_from_msg(open(glob.glob(os.path.join(ROOT, "**/OpticalFlow.msg"), recursive=True)[0]).read(),
                               "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
ev, gt = [], []                       # ev: (receipt_t, header_t, kind, payload)
with Reader(f"{D}/bag") as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates", "/imu/time_ref", "/ground_truth/pose"]
    for con, t_ns, rawb in r.messages(connections=[conns[w] for w in want if w in conns]):
        m = ts.deserialize_cdr(rawb, con.msgtype); tr = t_ns * 1e-9
        if con.topic == "/ground_truth/pose":
            p, q = m.pose.position, m.pose.orientation; gt.append((st(m.header), p.x, p.y, p.z, q.x, q.y, q.z, q.w)); continue
        if con.topic == "/imu/time_ref":
            ev.append((tr, st(m.header), "tref", m.time_ref.sec + m.time_ref.nanosec * 1e-9)); continue
        if con.topic == "/imu/data_raw":
            p = (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]),
                 np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])); k = "imu"
        elif con.topic == "/downward_lidar/range":
            p = float(m.range); k = "rng"
        elif con.topic == "/optical_flow/measurement":
            p = (np.array([m.flow_x_rad, m.flow_y_rad]), bool(m.valid), float(m.inlier_ratio)); k = "flow"
        else:
            p = np.array([m.vector.x, m.vector.y, m.vector.z]); k = "att"
        ev.append((tr, st(m.header), k, p))
n_hdg = 0
if not a.no_heading:
    last = None
    for row in csv.DictReader(open(f"{D}/logs/heading_bridge.csv")):
        if row["sent"] != "1" or int(row["quality"]) < 50:
            continue
        tc = float(row["t_capture"])
        if last is not None and tc - last < 0.020:
            continue
        last = tc; n_hdg += 1
        ev.append((float(row["t_sim_sent"]), tc, "fwd", (-float(row["yaw_ap_rad"]), None)))
ev.sort(key=lambda e: e[0])           # receipt order (stable: bag order kept for equal receipt times)
core = FgoNodeCore(window=0.25, lm_iters=2, fwd_sigma=(None if a.no_heading else {"psi": math.radians(5.0), "omega": None}),
                   fwd_gate=9.0, horizon_s=0.10, dejitter="causal", gap="causal")
for _, h, k, p in ev:
    core.push(h, k, p)
core.flush()
tr = np.array(core.traj)
r_, p_, y_ = tr[:, 4], tr[:, 5], tr[:, 6]
cr, sr, cp, sp, cy, sy = np.cos(r_/2), np.sin(r_/2), np.cos(p_/2), np.sin(p_/2), np.cos(y_/2), np.sin(y_/2)
q = np.c_[sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy]
np.savetxt(f"{OUT}/fgo_traj.tum", np.c_[tr[:, 0:4], q], fmt="%.6f")
np.savetxt(f"{OUT}/ground_truth.tum", np.array(gt), fmt="%.6f")
fl = getattr(core.fgo, "fwd_log", [])
acc = int(sum(1 for x in fl if x[1] == 0 and x[3])); n0 = int(sum(1 for x in fl if x[1] == 0))
print(f"[core replay] {a.trial}: {len(tr)} keyframes, headings pushed {n_hdg}, fused {acc}/{n0}, valid_end {core.valid}, reinits {core.reinits}")
if a.save_npz:
    np.savez(f"{OUT}/core_replay.npz", traj=tr, fwd_log=np.array([(x[0], x[1], x[2], float(x[3]), x[4]) for x in fl]).reshape(-1, 5))
print(f"[out] {OUT}/fgo_traj.tum")
