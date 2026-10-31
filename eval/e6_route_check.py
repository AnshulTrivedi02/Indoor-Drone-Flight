#!/usr/bin/env python3
"""E6 route and tag-coverage check for a figure-of-eight flight (gate V-F, and the same report for every mapping
flight; docs/thesis/tier1/e6_preregistration.md §7). Reads only.
  * topics present: /tags/raw, /tags/sent, /imu/time_ref, /ground_truth/pose;
  * route: for each HPROFILE "move" segment (fly_trial.log 'HSEG i move START t_sim', SITL clock mapped to the bag clock
    by the /imu/time_ref lower envelope, as eval/l_score.py), ground truth at mid-segment must be within 0.5 m of the
    segment's line (cross-track; world x = LOCAL_NED E, world y = N);
  * coverage: central-third /tags/raw detections (lc_fgo_replay.py's rule) per tag id, per circuit of 8 segments;
    PASS needs >= 1 central detection of every one of the 8 tags in every circuit.
Usage: e6_route_check.py TRIAL PROFILE.json [--json OUT]"""
import argparse, json, math, os, re, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

FX, CX, CY = 554.3827056884766, 320.0, 240.0; R_VALID = (1.0 / 3.0) * math.hypot(CX, CY)
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("profile"); ap.add_argument("--json")
a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
segs = json.load(open(a.profile))
ts = get_typestore(Stores.ROS2_JAZZY); G, TR, raw = [], [], []; topics = {}
with Reader(f"{D}/bag") as rd:
    topics = {c.topic: c.msgcount for c in rd.connections}
    want = [c for c in rd.connections if c.topic in ("/ground_truth/pose", "/imu/time_ref", "/tags/raw")]
    for con, _, b in rd.messages(connections=want):
        m = ts.deserialize_cdr(b, con.msgtype); t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, t))
        elif con.topic == "/ground_truth/pose":
            G.append((t, m.pose.position.x, m.pose.position.y))
        else:
            u, v = FX * m.pose.position.x / m.pose.position.z + CX, FX * m.pose.position.y / m.pose.position.z + CY
            if math.hypot(u - CX, v - CY) <= R_VALID:
                raw.append((t, int(m.header.frame_id.split("_")[1])))
G, TR = np.array(G), np.array(TR)
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_bag = lambda x: x + (kk * x + c0)
st = {}; end = None; start = None
for ln in open(f"{D}/logs/fly_trial.log"):
    m_ = re.search(r"HSEG (\d+) move START t_sim=([\d.]+)", ln)
    if m_: st[int(m_[1])] = to_bag(float(m_[2]))
    m_ = re.search(r"HPROFILE END t_sim=([\d.]+)", ln)
    if m_: end = to_bag(float(m_[1]))
    m_ = re.search(r"HPROFILE: .* start N ([-\d.]+) E ([-\d.]+)", ln)
    if m_: start = (float(m_[2]), float(m_[1]))      # world (x, y) = (E, N)
res = {"trial": a.trial, "topics": {k: topics.get(k, 0) for k in ("/tags/raw", "/tags/sent", "/imu/time_ref", "/ground_truth/pose")},
       "segments": [], "circuits": []}
prev = start
for i, sg in enumerate(segs):
    to = (sg["to"][1], sg["to"][0])                   # world (x, y)
    T = math.hypot(to[0] - prev[0], to[1] - prev[1]) / sg["speed"]
    tm = st[i] + T / 2; gx, gy = np.interp(tm, G[:, 0], G[:, 1]), np.interp(tm, G[:, 0], G[:, 2])
    ux, uy = (to[0] - prev[0]) / (T * sg["speed"]), (to[1] - prev[1]) / (T * sg["speed"])
    xt = abs(-(gx - prev[0]) * uy + (gy - prev[1]) * ux)
    res["segments"].append({"i": i, "from": prev, "to": to, "t_start_bag": st[i], "cross_track_mid_m": float(xt), "ok": bool(xt <= 0.5)})
    prev = to
n_c = len(segs) // 8
for c in range(n_c):
    t0 = st[8 * c]; t1 = st[8 * c + 8] if 8 * c + 8 in st else (end if end is not None else G[-1, 0])
    cnt = {j: sum(1 for t, tid in raw if t0 <= t < t1 + 1.0 and tid == j) for j in range(8)}   # +1 s: the closing pass over tag 0
    res["circuits"].append({"circuit": c + 1, "t0": t0, "t1": t1, "central_detections": cnt, "ok": all(v >= 1 for v in cnt.values())})
res["total_central_per_tag"] = {j: sum(1 for _, tid in raw if tid == j) for j in range(8)}
res["pass"] = bool(all(v > 0 for v in res["topics"].values()) and all(s["ok"] for s in res["segments"]) and all(c["ok"] for c in res["circuits"]))
for s in res["segments"]:
    print(f"seg {s['i']:2d} {s['from']} -> {s['to']}: cross-track at mid {s['cross_track_mid_m']:.3f} m {'ok' if s['ok'] else 'FAIL'}")
for c in res["circuits"]:
    print(f"circuit {c['circuit']}: central detections per tag {c['central_detections']} {'ok' if c['ok'] else 'FAIL'}")
print("topics", res["topics"]); print("V-F/route check:", "PASS" if res["pass"] else "FAIL")
if a.json:
    if os.path.exists(a.json): sys.exit(f"refusing to overwrite {a.json}")
    json.dump(res, open(a.json, "w"), indent=1)
sys.exit(0 if res["pass"] else 1)
