#!/usr/bin/env python3
"""IMU gap rule for the replay estimators (UKF/FGO) — METHODOLOGY "RULE — IMU gaps and
the replay estimators" (user ruling, 2026-09-24).

A GAP is a step in `/imu/time_ref` sensor time (HIGHRES_IMU `time_usec`) larger than
GAP_MS. Normal steps are 2, 3, 5 and 6 ms: the 333 Hz stream is sampled off SITL's
400 Hz loop, so steps alternate while averaging 3.0005 ms. GAP_MS sits above every
normal step and below the smallest real dropout seen so far.

ARMING is the first dataflash `ARM` record with ArmState = 1. `time_usec` and dataflash
`TimeUS` are the same clock (both `AP_HAL::micros64()`: GCS_Common.cpp:2298 and the
logger), so gaps are placed against arming exactly, with no clock mapping.

Rule, per bag:
  no gap                      -> "ok"; the replay runs unchanged.
  gaps only before arming     -> "trim"; the replay starts at the first IMU sample after
                                 the last gap (`replay_start_s`, bag header clock).
  any gap after arming        -> "unusable"; UKF/FGO are not run and the bag is reported
                                 as unusable for the replay estimators.
The verdict is written to `<trial>/imu_gaps.json`, which the replays read (see
`imu_timing.replay_start`). Bags without /imu/time_ref (all dsn_*) get no file, and
their replays are unchanged.

Also reported (diagnostic): the stationary period that remains between replay start and
takeoff (GT horizontal speed and height), and receipt-vs-sensor timing (header stamp
minus a linear fit on sensor time).

Usage (venv-evo: rosbags + numpy; dataflash via ~/venv-ardupilot):
  python3 eval/imu_gap_check.py TRIAL [TRIAL...] [--write]
"""
import argparse, json, os, subprocess
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

TRIALS_DIR = os.path.expanduser("~/thesis_data/trials")
PY_AP = os.path.expanduser("~/venv-ardupilot/bin/python3")
GAP_MS = 10.0
_ARM = """
import sys
from pymavlink import mavutil
m = mavutil.mavlink_connection(sys.argv[1])
while True:
    x = m.recv_match(type="ARM")
    if x is None: break
    if x.ArmState == 1: print(x.TimeUS); break
"""
ts = get_typestore(Stores.ROS2_JAZZY)


def arm_time_us(trial):
    out = subprocess.run([PY_AP, "-c", _ARM, f"{TRIALS_DIR}/{trial}/ardupilot.bin"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return int(out)


def check(trial):
    hdr, sen, gt = [], [], []
    with Reader(f"{TRIALS_DIR}/{trial}/bag") as r:
        conns = [c for c in r.connections if c.topic in ("/imu/time_ref", "/ground_truth/pose")]
        for con, _, raw in r.messages(connections=conns):
            m = ts.deserialize_cdr(raw, con.msgtype)
            h = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if con.topic == "/imu/time_ref":
                hdr.append(h); sen.append(m.time_ref.sec * 1_000_000 + m.time_ref.nanosec // 1000)
            else:
                gt.append((h, m.pose.position.x, m.pose.position.y, m.pose.position.z))
    if not sen:
        return {"trial": trial, "verdict": "no_time_ref"}
    o = np.argsort(sen); sen = np.array(sen, np.int64)[o]; hdr = np.array(hdr)[o]
    gt = np.array(sorted(gt))
    arm = arm_time_us(trial)
    steps_ms = np.diff(sen) / 1e3
    u, c = np.unique(np.round(steps_ms, 1), return_counts=True)
    gi = np.where(steps_ms > GAP_MS)[0]
    gaps = [{"sensor_s": sen[i] / 1e6, "header_s": float(hdr[i]), "step_ms": float(steps_ms[i]),
             "before_arm": bool(sen[i + 1] < arm)} for i in gi]
    # arming on the bag header clock: linear fit of header against sensor time
    b, a = np.polyfit(sen / 1e6, hdr, 1)
    arm_hdr = a + b * arm / 1e6
    lat = hdr - (a + b * sen / 1e6)
    if not gaps:
        verdict, start = "ok", None
    elif all(g["before_arm"] for g in gaps):
        verdict, start = "trim", float(hdr[gi[-1] + 1])
    else:
        verdict, start = "unusable", None
    # takeoff: first GT height 5 cm above the resting height
    z0 = np.median(gt[gt[:, 0] < arm_hdr, 3])
    takeoff = float(gt[np.argmax(gt[:, 3] > z0 + 0.05), 0])
    t_from = start if start is not None else float(hdr[0])
    w = (gt[:, 0] >= t_from) & (gt[:, 0] <= takeoff - 0.5)
    v = np.hypot(np.gradient(gt[w, 1], gt[w, 0]), np.gradient(gt[w, 2], gt[w, 0]))
    return {
        "trial": trial, "verdict": verdict, "gap_ms": GAP_MS, "gaps": gaps,
        "replay_start_s": start, "arm_timeus_s": arm / 1e6, "arm_header_s": float(arm_hdr),
        "takeoff_header_s": takeoff, "imu_first_header_s": float(hdr[0]),
        "stationary_s": takeoff - t_from, "stationary_to_arm_s": float(arm_hdr - t_from),
        "stationary_gt_speed_max_mps": float(v.max()), "stationary_gt_z_span_m": float(np.ptp(gt[w, 3])),
        "step_counts_ms": {str(k): int(n) for k, n in zip(u, c)},
        "receipt_vs_sensor_ms": {"std": float(1e3 * lat.std()), "max_abs": float(1e3 * np.abs(lat).max()),
                                 "p99_abs": float(1e3 * np.percentile(np.abs(lat), 99))},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("trials", nargs="+")
    ap.add_argument("--write", action="store_true", help="write <trial>/imu_gaps.json")
    a = ap.parse_args()
    for t in a.trials:
        r = check(t)
        if a.write and r["verdict"] != "no_time_ref":
            json.dump(r, open(f"{TRIALS_DIR}/{t}/imu_gaps.json", "w"), indent=1)
        print(json.dumps(r))
