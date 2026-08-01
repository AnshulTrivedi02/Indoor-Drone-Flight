#!/usr/bin/env python3
"""Item 4/5 data: flow residual = measured flow - flow predicted from GROUND-TRUTH
velocity + attitude through the shared h_flow_pose. Also GT body velocity and GT
roll/pitch, for the tilt-correlation (item 5). Saves an .npz for the plotter.

A persistent non-zero mean in the LATERAL (x) channel with zero GT lateral motion is
a pipeline bias (e.g. residual camera tilt), not an estimator error. Read-only,
existing bag. Usage: diag_flow_residual.py <trial>   (run in venv-evo)."""
import sys, os, glob, math
import numpy as np
sys.path.insert(0, os.path.expanduser("~/thesis_ws/src/estimators"))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from measurement_models import h_flow_pose

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
BAG = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/bag")
OUT = os.path.expanduser(f"~/thesis_ws/plots/_diag_{TRIAL}_flowresid.npz")
ts = get_typestore(Stores.ROS2_JAZZY)
mp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(mp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec*1e-9

def q2R(w, x, y, z):
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                     [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])
def q2rpy(w, x, y, z):
    roll = math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    pitch = math.asin(max(-1, min(1, 2*(w*y-z*x))))
    yaw = math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return roll, pitch, yaw

gt = []; flow = []; att = []
with Reader(BAG) as r:
    c = {x.topic: x for x in r.connections}
    for con, t, raw in r.messages(connections=[c[k] for k in
            ["/ground_truth/pose", "/optical_flow/measurement", "/attitude/angular_rates"] if k in c]):
        m = ts.deserialize_cdr(raw, con.msgtype); tt = stamp(m.header)
        if con.topic == "/ground_truth/pose":
            p = m.pose.position; q = m.pose.orientation
            gt.append((tt, p.x, p.y, p.z, q.w, q.x, q.y, q.z))
        elif con.topic == "/optical_flow/measurement":
            flow.append((tt, m.flow_x_rad, m.flow_y_rad, bool(m.valid), float(m.inlier_ratio)))
        elif con.topic == "/attitude/angular_rates":
            att.append((tt, m.vector.x, m.vector.y, m.vector.z))
gt = np.array(sorted(gt)); att = np.array(sorted(att))
# GT velocity (ENU) by finite diff
gvE = np.gradient(gt[:, 1], gt[:, 0]); gvN = np.gradient(gt[:, 2], gt[:, 0]); gvU = np.gradient(gt[:, 3], gt[:, 0])
geul = np.array([q2rpy(*gt[i, 4:8]) for i in range(len(gt))])

t0 = gt[0, 0]
rows = []
for f in sorted(flow):
    tt, fx, fy, valid, inlier = f
    if not valid:
        continue
    # interpolate GT state to flow time
    R = q2R(*[np.interp(tt, gt[:, 0], gt[:, k]) for k in (4, 5, 6, 7)])
    v = np.array([np.interp(tt, gt[:, 0], gvE), np.interp(tt, gt[:, 0], gvN), np.interp(tt, gt[:, 0], gvU)])
    z = np.interp(tt, gt[:, 0], gt[:, 3])
    om = np.array([np.interp(tt, att[:, 0], att[:, k]) for k in (1, 2, 3)])
    pred = h_flow_pose(R, v, z, om)                    # GT-predicted raw flow
    v_body = R.T @ v                                   # GT body velocity (FLU) for reference
    roll = np.interp(tt, gt[:, 0], np.unwrap(geul[:, 0])); pitch = np.interp(tt, gt[:, 0], np.unwrap(geul[:, 1]))
    rows.append((tt-t0, pred[0]-fx, pred[1]-fy, v_body[0], v_body[1], roll, pitch, inlier, om[0], om[1]))
rows = np.array(rows)
np.savez(OUT, t=rows[:, 0], resid_x=rows[:, 1], resid_y=rows[:, 2],
         vbody_x=rows[:, 3], vbody_y=rows[:, 4], gt_roll=rows[:, 5], gt_pitch=rows[:, 6], inlier=rows[:, 7],
         rollspeed=rows[:, 8], pitchspeed=rows[:, 9])
# cruise stats
w = (rows[:, 0] > 40) & (rows[:, 0] < rows[-1, 0]-10)
print(f"{TRIAL}: flow residual (pred-meas), cruise mean +/- std:")
print(f"  x (lateral) = {rows[w,1].mean():+.4f} +/- {rows[w,1].std():.4f} rad/s")
print(f"  y (forward) = {rows[w,2].mean():+.4f} +/- {rows[w,2].std():.4f} rad/s")
print(f"  GT roll cruise mean = {math.degrees(rows[w,5].mean()):+.3f} deg   pitch = {math.degrees(rows[w,6].mean()):+.3f} deg")
cc_ang = np.corrcoef(rows[w, 5], rows[w, 1])[0, 1]
cc_rate = np.corrcoef(rows[w, 8], rows[w, 1])[0, 1]
print(f"  corr(lateral residual, roll ANGLE)={cc_ang:+.3f}   corr(lateral residual, roll RATE)={cc_rate:+.3f}")
print(f"saved {OUT}")
