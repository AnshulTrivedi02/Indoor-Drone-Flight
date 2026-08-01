#!/usr/bin/env python3
"""Decisive fairness check: does EKF3 or the UKF derotate the lateral flow correctly?
Correlate each estimator's OWN flow-X innovation with roll rate over cruise (each uses
its own state + gyro, so no ground-truth differentiation is involved). If an estimator
derotates correctly its innovation is uncorrelated with roll rate.

Result (dsn_tex_r1): EKF3 corr ~+0.03 (correct); UKF corr ~+0.71 (roll-rate-coupled,
wrong sign in h_flow's flow_x_rot). So EKF3 has the correct derotation and the UKF/FGO
(shared h_flow) do not -> fixing h_flow's sign makes UKF/FGO MATCH EKF3, removing a
real asymmetry. Run EKF3 part in venv-ardupilot, UKF part in venv-evo.
"""
import sys, os, glob
import numpy as np

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
mode = sys.argv[2] if len(sys.argv) > 2 else "ekf3"

if mode == "ekf3":
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/ardupilot.bin"))
    ft, fx, gt, gx = [], [], [], []
    while True:
        x = m.recv_match(type=['XKF5', 'IMU'])
        if x is None: break
        if x.get_type() == 'XKF5' and getattr(x, 'C', 0) == 0: ft.append(x.TimeUS/1e6); fx.append(x.FIX/1000.0)
        elif x.get_type() == 'IMU' and getattr(x, 'I', 0) == 0: gt.append(x.TimeUS/1e6); gx.append(x.GyrX)
    ft = np.array(ft); fx = np.array(fx); gxi = np.interp(ft, gt, gx)
    w = (ft > ft[0]+40) & (ft < ft[-1]-10)
    print(f"EKF3 {TRIAL}: flow-X innov (FIX) vs roll rate  corr={np.corrcoef(gxi[w],fx[w])[0,1]:+.3f} "
          f"slope={np.polyfit(gxi[w],fx[w],1)[0]:+.3f}  (correct derotation => ~0)")
else:
    sys.path.insert(0, os.path.expanduser("~/thesis_ws/src/estimators"))
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore, get_types_from_msg
    import ukf_core as U
    from measurement_models import h_flow
    np.seterr(all='ignore')
    ts = get_typestore(Stores.ROS2_JAZZY)
    mp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
    ts.register(get_types_from_msg(open(mp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
    stamp = lambda h: h.stamp.sec + h.stamp.nanosec*1e-9
    ev = []
    with Reader(os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/bag")) as r:
        c = {x.topic: x for x in r.connections}
        for con, t, raw in r.messages(connections=[c[k] for k in
                ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates"] if k in c]):
            m = ts.deserialize_cdr(raw, con.msgtype); tt = stamp(m.header)
            if con.topic == "/imu/data_raw": ev.append((tt, "imu", (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]), np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z]))))
            elif con.topic == "/downward_lidar/range": ev.append((tt, "rng", float(m.range)))
            elif con.topic == "/optical_flow/measurement": ev.append((tt, "flow", (np.array([m.flow_x_rad, m.flow_y_rad]), bool(m.valid), float(m.inlier_ratio))))
            elif con.topic == "/attitude/angular_rates": ev.append((tt, "att", np.array([m.vector.x, m.vector.y, m.vector.z])))
    ev.sort(key=lambda e: e[0])
    p = U.make_params(); t0 = next(t for t, k, _ in ev if k == "imu")
    al = [d[0] for t, k, d in ev if k == "imu" and t <= t0+0.5]; fr = next(d for t, k, d in ev if k == "rng" and p['RNG_MIN'] <= d <= p['RNG_MAX'])
    x, P = U.init_state(np.mean(al, axis=0), fr); ti = t0+0.5
    om = np.zeros(3); tp = ti; ty = ti; da = np.zeros(3); dv = np.zeros(3); ad = 0.0; rows = []
    for t, kind, d in ev:
        if t < ti:
            if kind == "att": om = d
            continue
        if kind == "att": om = d
        elif kind == "imu":
            dti = t-tp; tp = t
            if dti <= 0 or dti > 0.2: continue
            da += d[1]*dti; dv += d[0]*dti; ad += dti
            if ad >= p['dt']:
                x, P = U.predict(x, P, da, dv, p)
                if t-ty >= p['YAW_DT']: x, P, _ = U.update_yaw_pseudo(x, P, p); ty = t
                da = np.zeros(3); dv = np.zeros(3); ad = 0.0
        elif kind == "rng": x, P, _ = U.update_range(x, P, d, p)
        elif kind == "flow":
            fxy, v, inl = d
            if v and inl > 0 and abs(fxy[0]) < p['FLOW_MAX'] and abs(fxy[1]) < p['FLOW_MAX']:
                sig, Wm, Wc = U._sigma_points(x, P, p)
                rows.append((t, fxy[0]-Wm@np.array([h_flow(s, om)[0] for s in sig]), om[0]))
            x, P, _ = U.update_flow(x, P, fxy, om, v, inl, p)
    rows = np.array(rows); w = (rows[:, 0] > rows[0, 0]+40) & (rows[:, 0] < rows[-1, 0]-10)
    print(f"UKF  {TRIAL}: flow-X innov vs roll rate  corr={np.corrcoef(rows[w,2],rows[w,1])[0,1]:+.3f} "
          f"slope={np.polyfit(rows[w,2],rows[w,1],1)[0]:+.3f}  (correct derotation => ~0)")
