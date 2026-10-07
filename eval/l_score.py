#!/usr/bin/env python3
"""Experiment L scorer (METHODOLOGY "Experiment L: pre-registration"). For one T flight: the keyframe FGO's live and
hindsight tracks for --mode lc and nolc (<trial>/lc_fgo_{lc,nolc}/), in tag 0's frame. Ground truth from the bag is
mapped into that frame with the known map (tag 0 at world (-3, -3), yaw 0 -> subtract (-3, -3)); the estimator never
sees the map. Lap window and laps from fly_trial.log 'LAP k LEG 0 START' / 'LAPS END' (SITL clock, mapped to the bag
clock by the /imu/time_ref lower envelope). Horizontal RMSE overall and per lap.
Usage (venv-tags): python3 eval/l_score.py TRIAL [--json OUT]"""
import argparse, json, os, re, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "tags")); import tag_measure as TM

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
tag0 = TM.load_map(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim", "worlds", "room_tags_map.json"))[0]
assert abs(tag0["yaw"]) < 1e-9, "the frame mapping below assumes tag 0 has yaw 0"
ts = get_typestore(Stores.ROS2_JAZZY); G, TR = [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs["/ground_truth/pose"], cs["/imu/time_ref"]]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
        else:
            G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x - tag0["p"][0], m.pose.position.y - tag0["p"][1]))
G, TR = np.array(G), np.array(TR)
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_bag = lambda x: x + (kk * x + c0)
laps, end = [], None
for ln in open(f"{D}/logs/fly_trial.log"):
    m_ = re.search(r"LAP (\d+) LEG 0 START t_sim=([\d.]+)", ln)
    if m_: laps.append(to_bag(float(m_[2])))
    m_ = re.search(r"LAPS END t_sim=([\d.]+)", ln)
    if m_: end = to_bag(float(m_[1]))
bounds = laps + [end]
out = {"trial": a.trial, "lap_bounds_s": bounds, "tracks": {}}
for mode in ("lc", "nolc"):
    for kind in ("live", "hindsight"):
        p = f"{D}/lc_fgo_{mode}/{kind}.tum"
        if not os.path.exists(p): continue
        x = np.loadtxt(p, ndmin=2)
        e = np.hypot(x[:, 1] - np.interp(x[:, 0], G[:, 0], G[:, 1]), x[:, 2] - np.interp(x[:, 0], G[:, 0], G[:, 2]))
        w = (x[:, 0] >= bounds[0]) & (x[:, 0] <= bounds[-1])
        per = [float(np.sqrt(np.mean(e[(x[:, 0] >= b0) & (x[:, 0] < b1)] ** 2))) for b0, b1 in zip(bounds[:-1], bounds[1:])]
        out["tracks"][f"{mode} {kind}"] = {"rmse_m": float(np.sqrt(np.mean(e[w] ** 2))), "max_m": float(e[w].max()), "per_lap_rmse_m": per}
        print(f"{mode:5s} {kind:9s} RMSE {out['tracks'][f'{mode} {kind}']['rmse_m']:.3f} max {e[w].max():.3f} | per lap "
              + " ".join(f"{v:.3f}" for v in per))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
