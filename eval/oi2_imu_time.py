#!/usr/bin/env python3
"""OI-2: rebuild a trial's bag with /imu/data_raw on SENSOR time instead of receipt time.

`imu_bridge.py` stamps each HIGHRES_IMU at receipt (ROS sim clock) and discards
`time_usec`, so the bags carry no per-sample sensor time. It is reconstructed here:

 1. Anchors: the dataflash logs `IMU` (instance 0) at 25 Hz, with values identical to
    what HIGHRES_IMU sent (float32 `get_accel()` / `get_gyro()`). Each dataflash sample
    is matched to its bag sample by value (bag FLU = (x, -y, -z) of FRD), giving
    (bag index i, sensor TimeUS) pairs.
 2. Clock: TimeUS -> bag sim clock with `input_timing.clock_map` (offset AND rate:
    SITL's TimeUS runs ~0.017-0.022% slow against Gazebo sim time, so a single offset
    would leave a ~50 ms drift across the flight; found while building this script).
 3. Model: t_sensor(i) = a + b*i, least squares over the anchors. HIGHRES_IMU is
    scheduled on SITL's 400 Hz loop, so true send times sit on a 2.5 ms grid; the
    linear model is therefore within about +-1.25 ms of true sensor time. The anchor
    residuals quantify this, and a dropped sample would show up as a step in them.
 4. Output: a clone trial `<trial>_oi2/` whose bag is identical except for the
    /imu/data_raw header stamps. `ardupilot.bin` and `metadata.yaml` are symlinked.
    The unchanged replay scripts then run on the clone. Estimators and the original
    trial are untouched.

Usage (venv-evo): python3 eval/oi2_imu_time.py TRIAL [TRIAL...]
"""
import os, subprocess, sys
import numpy as np
from rosbags.rosbag2 import Reader, Writer
from rosbags.typesys import Stores, get_typestore
import input_timing as IT

TRIALS_DIR = IT.TRIALS_DIR
ts = IT.ts

_IMU_DUMP = r"""
import sys, numpy as np
from pymavlink import mavutil
m = mavutil.mavlink_connection(sys.argv[1]); out = []
while True:
    x = m.recv_match(type='IMU')
    if x is None: break
    if getattr(x, 'I', 0) != 0: continue
    out.append((x.TimeUS / 1e6, x.AccX, x.AccY, x.AccZ, x.GyrX, x.GyrY, x.GyrZ))
np.save(sys.argv[2], np.array(out, dtype=np.float64))
"""


def f32(v):
    return np.float32(v).tobytes()


def build(trial):
    src = f"{TRIALS_DIR}/{trial}"
    p = f"{src}/ekf3/imu25.npy"
    if not os.path.exists(p):
        subprocess.run([IT.PY_AP, "-c", _IMU_DUMP, f"{src}/ardupilot.bin", p], check=True)
    df = np.load(p)
    imu, gt = [], []
    with Reader(f"{src}/bag") as r:
        conns = [c for c in r.connections if c.topic in ("/imu/data_raw", "/ground_truth/pose")]
        for con, _, raw in r.messages(connections=conns):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/imu/data_raw":
                a, g = m.linear_acceleration, m.angular_velocity
                imu.append((IT.stamp(m.header), a.x, a.y, a.z, g.x, g.y, g.z))
            else:
                gt.append((IT.stamp(m.header), m.pose.position.x, m.pose.position.y, m.pose.position.z))
    imu, gt = np.array(imu), np.array(sorted(gt))
    order = np.argsort(imu[:, 0], kind="stable")          # bag order == receipt order
    assert np.all(order == np.arange(len(imu)))
    to_sim, o1, o2, _, _ = IT.clock_map(IT.sim_truth(trial), gt)   # offset AND rate
    key = {}
    for i, row in enumerate(imu):
        key.setdefault((f32(row[1]), f32(-row[2]), f32(-row[3]), f32(row[4]), f32(-row[5]), f32(-row[6])), i)
    anc = [(key[k], float(to_sim(t))) for t, ax, ay, az, gx, gy, gz in df
           if (k := (f32(ax), f32(ay), f32(az), f32(gx), f32(gy), f32(gz))) in key]
    anc = np.array(anc)
    b, a = np.polyfit(anc[:, 0], anc[:, 1], 1)
    res = anc[:, 1] - (a + b * anc[:, 0])
    t_new = a + b * np.arange(len(imu))
    rec = imu[:, 0] - t_new                                  # receipt minus sensor time
    stats = {"anchors": len(anc), "anchor_pct": 100 * len(anc) / len(df), "period_ms": 1e3 * b,
             "fit_resid_std_ms": 1e3 * res.std(), "fit_resid_maxabs_ms": 1e3 * np.abs(res).max(),
             "receipt_minus_sensor_med_ms": 1e3 * np.median(rec), "p5": 1e3 * np.percentile(rec, 5),
             "p95": 1e3 * np.percentile(rec, 95),
             "rec_first30s_med_ms": 1e3 * np.median(rec[:10000]), "rec_last30s_med_ms": 1e3 * np.median(rec[-10000:])}
    # --- clone the bag with only the IMU header stamps replaced ---
    dst = f"{TRIALS_DIR}/{trial}_oi2"
    os.makedirs(dst, exist_ok=False)
    for f in ("ardupilot.bin", "metadata.yaml"):
        os.symlink(f"{src}/{f}", f"{dst}/{f}")
    k = 0
    with Reader(f"{src}/bag") as r, Writer(f"{dst}/bag", version=9) as w:
        wc = {c.id: w.add_connection(c.topic, c.msgtype, typestore=ts) for c in r.connections}
        for con, t, raw in r.messages():
            if con.topic == "/imu/data_raw":
                m = ts.deserialize_cdr(raw, con.msgtype)
                s = t_new[k]; k += 1
                m.header.stamp.sec = int(np.floor(s))
                m.header.stamp.nanosec = int(round((s - np.floor(s)) * 1e9)) % 1_000_000_000
                raw = ts.serialize_cdr(m, con.msgtype)
            w.write(wc[con.id], t, raw)
    assert k == len(imu)
    return stats


if __name__ == "__main__":
    for tr in sys.argv[1:]:
        s = build(tr)
        print(f"{tr}: anchors {s['anchors']} ({s['anchor_pct']:.1f}% of dataflash IMU), period {s['period_ms']:.5f} ms, "
              f"fit resid std {s['fit_resid_std_ms']:.3f} max {s['fit_resid_maxabs_ms']:.3f} ms; "
              f"receipt-sensor median {s['receipt_minus_sensor_med_ms']:.2f} [p5 {s['p5']:.2f}, p95 {s['p95']:.2f}] ms; "
              f"first/last 30 s median {s['rec_first30s_med_ms']:.2f}/{s['rec_last30s_med_ms']:.2f} ms")
