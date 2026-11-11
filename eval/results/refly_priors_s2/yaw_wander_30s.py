#!/usr/bin/env python3
"""FGO yaw wander over the 30 s hold loss (METHODOLOGY:12570, "FGO yaw wander over the 30 s loss:
-0.23 / +0.52 / +0.52 deg (<=3 deg, PASS)" for H_s3v2_r1/r2/r3). Not persisted by eval/h_score.py (it has no
"wander" field; confirmed by reading it and by `git show 55edd75 -- eval/h_score.py`, the commit that added the
XFGO track). Re-derives it here with the SAME clock map and XFGO track h_score.py itself builds (TimeUS -> bag
clock via to_bag, from /imu/time_ref and fly_trial.log's HSEG markers; OV==1 filter; yaw = radians(90 - Yaw)),
reading the loss's own t_on/t_off from the ALREADY-SCORED h_score.py json (same clock, same units) rather than
re-detecting OCCLUDER markers independently.

Definition (matching the METHODOLOGY numbers, verified below): the signed wrapped yaw change over the one loss
whose duration is closest to 30 s (yaw at t_off minus yaw at t_on, nearest XFGO OV==1 samples), in degrees.

Usage (PYTHONPATH=~/.cache/thesis_pyshim ~/venv-evo/bin/python):
  python3 eval/results/refly_priors_s2/yaw_wander_30s.py TRIAL --score-json SCORE.json
"""
import argparse, json, math, os, re
import numpy as np
from pymavlink import mavutil

wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi


def clock_map(D):
    import rosbags.rosbag2 as rb2
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    TR = []
    with rb2.Reader(f"{D}/bag") as rd:
        cs = [c for c in rd.connections if c.topic == "/imu/time_ref"]
        for con, _, raw in rd.messages(connections=cs):
            m = ts.deserialize_cdr(raw, con.msgtype)
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, t))
    TR = np.array(sorted(TR))
    sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        w = (sitl >= lo) & (sitl < lo + 5)
        if w.sum() > 50:
            i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
    env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
    return lambda x: x + (kk * x + c0)


def xfgo_track(D, to_bag):
    mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); xfgo = []
    while True:
        r = mv.recv_match(type=["XFGO"])
        if r is None: break
        if r.OV == 1:
            xfgo.append((to_bag(r.TimeUS / 1e6), math.radians(90.0 - r.Yaw)))
    return np.array(sorted(xfgo, key=lambda x: x[0]))


def nearest_yaw(track, t):
    i = np.argmin(np.abs(track[:, 0] - t))
    return track[i, 1], track[i, 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial"); ap.add_argument("--score-json", required=True)
    a = ap.parse_args()
    D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
    score = json.load(open(a.score_json))
    losses = score["losses"]
    # the loss whose duration is closest to 30 s
    loss = min(losses, key=lambda L: abs(L["duration_s"] - 30.0))
    to_bag = clock_map(D)
    track = xfgo_track(D, to_bag)
    y_on, t_on_used = nearest_yaw(track, loss["t_on"])
    y_off, t_off_used = nearest_yaw(track, loss["t_off"])
    wander_deg = math.degrees(wrap(y_off - y_on))
    out = {"trial": a.trial, "loss_duration_s": loss["duration_s"], "t_on": loss["t_on"], "t_off": loss["t_off"],
           "t_on_used": float(t_on_used), "t_off_used": float(t_off_used),
           "yaw_on_deg": math.degrees(y_on), "yaw_off_deg": math.degrees(y_off),
           "yaw_wander_deg": wander_deg}
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
