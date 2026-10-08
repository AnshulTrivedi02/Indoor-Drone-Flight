"""Model audit (2026-10-09), DIAGNOSTIC: extract the shared 10 s IMU window and the sensor arrival stamps.

Reads an UNPACKED copy of a trial bag (scratch), dejitters /imu/data_raw exactly as the replays do
(src/estimators/imu_timing.dejitter_imu, after the IMU-gap rule), and writes <out>.npz with:
  t, acc, gyro   -- the dejittered 333 Hz FLU samples inside [T0, T0 + 10 s]
  t_flow, t_rng  -- every flow / range header stamp of the flight (arrival-rate audit, item 2)
  gt_t, gt_xyz   -- ground truth (window sanity only)
Usage (~/venv-fgo): python3 imu_window.py BAGDIR TRIAL T0 OUT"""
import sys, os
import numpy as np
from rosbags.highlevel import AnyReader
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "estimators"))
from imu_timing import dejitter_imu, apply_gap_rule

bagdir, trial, T0, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
DUR = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
ev, gt, tf, tr = [], [], [], []
with AnyReader([Path(bagdir)]) as r:
    cons = [c for c in r.connections if c.topic in ("/imu/data_raw", "/optical_flow/measurement",
                                                     "/downward_lidar/range", "/ground_truth/pose")]
    for con, _, raw in r.messages(connections=cons):
        if con.topic == "/optical_flow/measurement":
            # custom type not registered in this reader; the header stamp is the first CDR field after the 4-byte header
            sec = int.from_bytes(raw[4:8], "little", signed=True); ns = int.from_bytes(raw[8:12], "little")
            tf.append(sec + 1e-9 * ns); continue
        m = r.deserialize(raw, con.msgtype)
        tt = m.header.stamp.sec + 1e-9 * m.header.stamp.nanosec
        if con.topic == "/imu/data_raw":
            ev.append((tt, "imu", (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]),
                                   np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z]))))
        elif con.topic == "/downward_lidar/range":
            tr.append(tt)
        else:
            gt.append((tt, m.pose.position.x, m.pose.position.y, m.pose.position.z))
ev = apply_gap_rule(ev, trial)
ev, st = dejitter_imu(ev)
print("dejitter", st)
w = [(t, d) for t, k, d in ev if k == "imu" and T0 <= t <= T0 + DUR + 1e-9]
t = np.array([a for a, _ in w]); acc = np.array([d[0] for _, d in w]); gyro = np.array([d[1] for _, d in w])
gt = np.array(sorted(gt))
sel = (gt[:, 0] >= T0) & (gt[:, 0] <= T0 + DUR)
v = np.diff(gt[sel, 1:3], axis=0) / np.maximum(np.diff(gt[sel, 0]), 1e-6)[:, None]
print(f"window {t[0]:.3f}..{t[-1]:.3f} s, n={len(t)}, mean acc {acc.mean(0).round(3)}, gyro rms {np.sqrt((gyro**2).mean(0)).round(4)}, "
      f"GT net horiz speed {np.linalg.norm(gt[sel,1:3][-1]-gt[sel,1:3][0])/(gt[sel,0][-1]-gt[sel,0][0]):.3f} m/s, z {gt[sel,3].mean():.3f} m")
np.savez(out, t=t, acc=acc, gyro=gyro, t_flow=np.array(sorted(tf)), t_rng=np.array(sorted(tr)), gt_t=gt[:, 0], gt_xyz=gt[:, 1:],
         period_ms=st["period_ms"])
