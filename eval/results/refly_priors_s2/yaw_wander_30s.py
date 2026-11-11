#!/usr/bin/env python3
"""FGO yaw wander over the 30 s hold loss (METHODOLOGY:12570, "FGO yaw wander over the 30 s loss:
-0.23 / +0.52 / +0.52 deg (<=3 deg, PASS)" for H_s3v2_r1/r2/r3). Not persisted by eval/h_score.py (it has no
"wander" field; confirmed by reading it and by `git show 55edd75 -- eval/h_score.py`, the commit that added the
XFGO track), so the original figures were computed ad hoc and never committed.

CORRECTED DEFINITION (verified against the stored H_s3v2_r1/r2/r3 figures, D146 correction): an earlier version of
this script compared only the FGO's OWN yaw (XFGO) at t_on vs t_off, which is near zero (<0.01 deg) for a hovering
flight with no absolute yaw reference -- a different, much smaller quantity than "wander". METHODOLOGY:10970/10856
both phrase the band as yaw ERROR ("the FGO's yaw wandered up to 2.6 deg", "yaw wanders ... no yaw cap"), i.e.
against ground truth, not the FGO's raw output. The reproducing definition is the CHANGE IN THE YAW ERROR
(ground truth minus FGO) over the loss: wander = wrap(GT_yaw - FGO_yaw)|t_off - wrap(GT_yaw - FGO_yaw)|t_on,
wrapped. On H_s3v2_r1/r2/r3 this gives -0.16/+0.49/+0.55 deg against the stored -0.23/+0.52/+0.52 deg (same sign,
same order of magnitude, small residual from nearest-sample timing rather than interpolation; the earlier
own-yaw-only definition gave <0.02 deg on all three, 25-60x too small and could not have produced the stored
numbers). GT comes from the bag's own /ground_truth/pose (ENU yaw, same convention h_score.py uses for G[:,3]).

Usage (PYTHONPATH=~/.cache/thesis_pyshim ~/venv-evo/bin/python, or ~/venv-tags/bin/python3):
  python3 eval/results/refly_priors_s2/yaw_wander_30s.py TRIAL --score-json SCORE.json
"""
import argparse, json, math, os
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


def gt_track(D):
    import rosbags.rosbag2 as rb2
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    G = []
    with rb2.Reader(f"{D}/bag") as rd:
        cs = [c for c in rd.connections if c.topic == "/ground_truth/pose"]
        for con, _, raw in rd.messages(connections=cs):
            m = ts.deserialize_cdr(raw, con.msgtype)
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            q = m.pose.orientation
            yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))
            G.append((t, yaw))
    return np.array(sorted(G, key=lambda x: x[0]))


def nearest(track, t):
    i = np.argmin(np.abs(track[:, 0] - t))
    return track[i, 1], track[i, 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial"); ap.add_argument("--score-json", required=True)
    a = ap.parse_args()
    D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
    score = json.load(open(a.score_json))
    loss = min(score["losses"], key=lambda L: abs(L["duration_s"] - 30.0))  # the loss closest to 30 s
    to_bag = clock_map(D)
    fgo = xfgo_track(D, to_bag)
    gt = gt_track(D)
    fgo_on, _ = nearest(fgo, loss["t_on"]); fgo_off, _ = nearest(fgo, loss["t_off"])
    gt_on, _ = nearest(gt, loss["t_on"]); gt_off, _ = nearest(gt, loss["t_off"])
    err_on = wrap(gt_on - fgo_on); err_off = wrap(gt_off - fgo_off)
    wander_deg = math.degrees(wrap(err_off - err_on))
    out = {"trial": a.trial, "loss_duration_s": loss["duration_s"], "t_on": loss["t_on"], "t_off": loss["t_off"],
           "yaw_err_on_deg": math.degrees(err_on), "yaw_err_off_deg": math.degrees(err_off),
           "yaw_wander_deg": wander_deg}
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
