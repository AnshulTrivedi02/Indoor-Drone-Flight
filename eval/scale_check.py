#!/usr/bin/env python3
"""Distance-scale check (user ruling 2026-09-29; replaces "bounded check 5a").
Existing outputs only. Per bag, over the pinned cruise window (phase4 evo JSON):

  (A) flow sensor scale: measured forward flow (/optical_flow/measurement flow_y_rad,
      valid frames) against the flow PREDICTED from ground truth through the shared model
      measurement_models.h_flow_pose (GT attitude, GT velocity, GT base_link height,
      interval-averaged co-sampled gyro). Slope of meas vs pred (through the origin) and
      the median ratio. > 1 means the flow sensor over-reads.
  (B) estimator horizontal speed ratio: median over cruise of |v_est| / |v_gt|, with v from
      the time derivative of the stored positions, smoothed over 1 s. EKF3 from
      ekf3/ekf3_traj.tum vs ekf3/ground_truth.tum (both TimeUS clock, NED);
      UKF/FGO arms from <est>_<arm>/<est>_traj.tum vs the bag GT (sim clock).
      Also the displacement ratio from the Phase 4 evo JSON.
  (C) estimator height bias over cruise: estimated base_link height - GT height (UKF/FGO
      TUM z vs GT z; EKF3 -PD vs SIM height, relative to the start). The flow height each
      uses is height - 0.25 m (UKF/FGO h_cam) or lidar range - FLOW_POS_Z (EKF3).
A flow-following estimator's speed ratio is expected to be ~= flow scale x (its camera
height / true camera height). That relation is the consistency check reported here.

Usage (venv-evo: rosbags + numpy): python3 eval/scale_check.py [--json OUT]
"""
import argparse, glob, json, math, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src", "estimators"))
from measurement_models import h_flow_pose, CAM_OFFSET, FlowFrameGyroAverager
TD = os.path.expanduser("~/thesis_data/trials")
ARMS = {"fwdc": ("baseline", "heading"), "fwdplainc": ("baseline", "heading")}
ts = get_typestore(Stores.ROS2_JAZZY)
ts.register(get_types_from_msg(open(glob.glob(os.path.expanduser("~/thesis_ws/src/**/OpticalFlow.msg"), recursive=True)[0]).read(),
                               "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9


def quat_to_R(x, y, z, w):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def read_bag(trial):
    gt, fl, imu = [], [], []
    with Reader(f"{TD}/{trial}/bag") as r:
        cs = [c for c in r.connections if c.topic in ("/ground_truth/pose", "/optical_flow/measurement", "/imu/data_raw")]
        for con, _, raw in r.messages(connections=cs):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/ground_truth/pose":
                p, q = m.pose.position, m.pose.orientation
                gt.append((st(m.header), p.x, p.y, p.z, q.x, q.y, q.z, q.w))
            elif con.topic == "/optical_flow/measurement":
                if m.valid and m.inlier_ratio > 0:
                    fl.append((st(m.header), m.flow_x_rad, m.flow_y_rad))
            else:
                imu.append((st(m.header), m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z))
    return np.array(sorted(gt)), np.array(sorted(fl)), np.array(sorted(imu))


def smooth_speed(t, x, y, win_s=1.0):
    dt = np.median(np.diff(t)); k = max(1, int(round(win_s / dt)))
    ker = np.ones(k) / k
    xs, ys = np.convolve(x, ker, "same"), np.convolve(y, ker, "same")
    return np.hypot(np.gradient(xs, t), np.gradient(ys, t))


def flow_scale(gt, fl, imu, win):
    vx, vy = np.gradient(gt[:, 1], gt[:, 0]), np.gradient(gt[:, 2], gt[:, 0])
    vz = np.gradient(gt[:, 3], gt[:, 0])
    avg = FlowFrameGyroAverager(fl[0, 0] - 0.05)
    j = 0; meas, pred = [], []
    for t, fx, fy in fl:
        while j < len(imu) and imu[j, 0] <= t:
            avg.push(imu[j, 0], imu[j, 1:4]); j += 1
        om = avg.average(t, np.zeros(3))
        if not (win[0] <= t <= win[1]):
            continue
        i = np.searchsorted(gt[:, 0], t); i = min(max(i, 1), len(gt) - 1)
        R = quat_to_R(*gt[i, 4:8])
        v = np.array([np.interp(t, gt[:, 0], vx), np.interp(t, gt[:, 0], vy), np.interp(t, gt[:, 0], vz)])
        pr = h_flow_pose(R, v, np.interp(t, gt[:, 0], gt[:, 3]), om)
        meas.append((fx, fy)); pred.append(pr)
    meas, pred = np.array(meas), np.array(pred)
    ax = 1                                                   # forward motion -> flow_y
    slope = float((meas[:, ax] @ pred[:, ax]) / (pred[:, ax] @ pred[:, ax]))
    ok = np.abs(pred[:, ax]) > 0.05
    return {"flow_y_slope": slope, "flow_y_median_ratio": float(np.median(meas[ok, ax] / pred[ok, ax])),
            "n": int(len(meas)), "pred_flow_y_median": float(np.median(pred[:, ax]))}


def est_scale(t, x, y, z, gt, win, gtz_offset=0.0):
    w = (t >= win[0]) & (t <= win[1])
    s_est = smooth_speed(t, x, y)[w]
    g_s = np.interp(t[w], gt[:, 0], smooth_speed(gt[:, 0], gt[:, 1], gt[:, 2]))
    ok = g_s > 0.3
    dz = z[w] - (np.interp(t[w], gt[:, 0], gt[:, 3]) + gtz_offset)
    return {"speed_ratio_median": float(np.median(s_est[ok] / g_s[ok])), "height_bias_mean_m": float(dz.mean()),
            "true_height_mean_m": float(np.interp(t[w], gt[:, 0], gt[:, 3]).mean() + gtz_offset)}


def main(out):
    res = {}
    for ds, arms in ARMS.items():
        evo = json.load(open(os.path.join(RES, f"phase4_{ds}_evo.json")))["trials"]
        for w in ("tex", "trans", "blank"):
            for r in (1, 2, 3):
                t = f"{ds}_{w}_r{r}"; win = evo[t]["window_s"]
                gt, fl, imu = read_bag(t)
                row = {"flow": flow_scale(gt, fl, imu, win) if w != "blank" else None}
                e = np.loadtxt(f"{TD}/{t}/ekf3/ekf3_traj.tum"); eg = np.loadtxt(f"{TD}/{t}/ekf3/ground_truth.tum")
                egt = np.c_[eg[:, 0], eg[:, 1], eg[:, 2], eg[:, 3]]
                row["EKF3"] = est_scale(e[:, 0], e[:, 1], e[:, 2], e[:, 3], egt, win)
                row["EKF3"]["disp_ratio"] = evo[t]["est"]["EKF3"]["failure"]["disp_ratio"]
                for est in ("UKF", "FGO"):
                    for a in arms:
                        a_ = np.loadtxt(f"{TD}/{t}/{est.lower()}_{a}/{est.lower()}_traj.tum")
                        row[f"{est}_{a}"] = est_scale(a_[:, 0], a_[:, 1], a_[:, 2], a_[:, 3], gt[:, :4], win)
                        row[f"{est}_{a}"]["disp_ratio"] = evo[t]["est"][f"{est}_{a}"]["failure"]["disp_ratio"]
                res[t] = row
                print(t, "flow", None if row["flow"] is None else round(row["flow"]["flow_y_slope"], 4),
                      " ".join(f"{k}:{v['speed_ratio_median']:.3f}/dz{v['height_bias_mean_m']:+.3f}" for k, v in row.items() if k != "flow"), flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=os.path.join(RES, "scale_check.json"))
    main(ap.parse_args().json)
