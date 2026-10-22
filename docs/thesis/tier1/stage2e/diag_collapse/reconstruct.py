#!/usr/bin/env python3
"""E3 map-collapse diagnosis (DESCRIPTIVE, 2026-10-23, after scoring). READ-ONLY on all run outputs; no gtsam solve.

Reconstructs, for one E3 run, the exact list of tag landmark factors lc_fgo_replay.py built, by replaying its event logic
(same bag read, central-third rule, tag filter, Mislabeller stream, gap rule, dejitter, keyframe clock, landmark
creation order) WITHOUT any optimisation. Checks:
  * the regenerated mislabel events equal stats.json:tier1.mislabel.events_t_true_new exactly (Part 1a spot-check);
  * the factor count equals stats.json:landmark_factors and the reconstructed keyframe clock equals the hindsight.tum
    times (row for row). (That a mislabelled detection keeps its TRUE geometry holds here BY CONSTRUCTION, as in the
    replay, where p_tb is computed before and independently of the Mislabeller; it is not checked independently.)
  * landmark creation order -> landmarks_final index map.
Then evaluates every tag factor's whitened residual (same noise as the replay: 0.05 m, 0.05 m, 5 deg; diagonal, no
kernel for arm (a)) at (i) the run's final estimate (hindsight.tum + landmarks_final) and (ii) the TRUTH (ground-truth
pose in tag 0's frame, as l_score.py, + the true tag map for the REPORTED id).
Usage (venv-fgo): reconstruct.py TRIAL RATE SEED [--keep T1,T2] [--run-dir DIR] --out JSON"""
import sys, os, glob, math, json, argparse
import numpy as np
R = "/home/makerspace/thesis_ws"
sys.path.insert(0, f"{R}/src/estimators"); sys.path.insert(0, f"{R}/src/estimators/fgo"); sys.path.insert(0, f"{R}/src/tags")
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from gtsam import Rot3
from measurement_models import TAG_SIGMA_POS, TAG_SIGMA_YAW
from imu_timing import dejitter_imu, apply_gap_rule
import tag_measure as TM
import tier1_paths as T1

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("rate", type=float); ap.add_argument("seed", type=int)
ap.add_argument("--keep", default=None); ap.add_argument("--run-dir", default=None); ap.add_argument("--out", required=True)
a = ap.parse_args()
KEEP = None if a.keep is None else [float(x) for x in a.keep.split(",")]
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
RUN = a.run_dir or os.path.expanduser(f"~/thesis_data/tier1/{a.trial}/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis{a.rate:g}_s{a.seed}")
ST = json.load(open(f"{RUN}/stats.json"))
FX, CX, CY = 554.3827056884766, 320.0, 240.0; R_VALID = (1.0 / 3.0) * math.hypot(CX, CY)
ts = get_typestore(Stores.ROS2_JAZZY)
msgp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(msgp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
ORIGIN = {"p": np.zeros(3), "yaw": 0.0}
TAG_IDS = tuple(range(8)); MIS = T1.Mislabeller(a.rate, a.seed, TAG_IDS, 0)
ev = []; G = []
with Reader(f"{D}/bag") as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates", "/tags/raw",
            "/ground_truth/pose"]
    for con, _, raw in r.messages(connections=[conns[w] for w in want if w in conns]):
        m = ts.deserialize_cdr(raw, con.msgtype); tt = stamp(m.header)
        if con.topic == "/ground_truth/pose":
            q = m.pose.orientation
            G.append((tt, m.pose.position.x, m.pose.position.y, Rot3.Quaternion(q.w, q.x, q.y, q.z).yaw())); continue
        if con.topic == "/imu/data_raw":
            ev.append((tt, "imu", None))
        elif con.topic == "/tags/raw":
            t_ct = np.array([m.pose.position.x, m.pose.position.y, m.pose.position.z]); q = m.pose.orientation
            R_ct = Rot3.Quaternion(q.w, q.x, q.y, q.z).matrix()
            u, v = FX * t_ct[0] / t_ct[2] + CX, FX * t_ct[1] / t_ct[2] + CY
            if math.hypot(u - CX, v - CY) > R_VALID:
                continue
            p_tb, R_tb = TM.vehicle_pose(ORIGIN, R_ct, t_ct)
            tid_true = int(m.header.frame_id.split("_")[1])
            tid, mis = MIS(tt, tid_true)
            if mis and KEEP is not None and any(abs(tt - x) < 1e-6 for x in KEEP):
                tid, mis = tid_true, False
            ev.append((tt, "tagrel", (tid, float(p_tb[0]), float(p_tb[1]), TM.yaw_of(R_tb), tid_true, mis)))
        else:
            ev.append((tt, "other", None))
# --- Part 1a: the regenerated injection stream must equal the logged one exactly
logged = [tuple(e) for e in ST["tier1"]["mislabel"]["events_t_true_new"]]
regen = [(float(t), int(i), int(n)) for t, i, n in MIS.events]
assert regen == [(float(t), int(i), int(n)) for t, i, n in logged], "regenerated mislabel events differ from stats.json"
ev = apply_gap_rule(ev, a.trial); ev, _ = dejitter_imu(ev); ev.sort(key=lambda e: e[0])
t_imu0 = next(t for t, k, _ in ev if k == "imu"); t_init = t_imu0 + 0.5
t_kf_next = t_init + 1.0 / 30.0; t_anchor = None; k = None; t_last = None; key_t = []; pend = []; factors = []
lm_key = {}; first = {}
for tt, kind, d in ev:
    if t_anchor is not None and tt > t_anchor + 245.0:
        break
    if tt < t_init:
        continue
    if kind == "tagrel":
        if t_anchor is None:
            if d[0] == 0:
                t_anchor = tt; k = 0; key_t.append((0, t_last)); pend = [d]
        else:
            pend.append(d)
    elif kind == "imu":
        while tt >= t_kf_next:
            if t_anchor is None:
                t_last = t_kf_next                         # fgo.keyframe sets t_last (the anchor row's time)
            else:
                k += 1; key_t.append((k, t_kf_next))
                for dd in pend:
                    tid = dd[0]; new = tid not in lm_key
                    if new: lm_key[tid] = len(lm_key); first[tid] = dd[5]
                    factors.append({"k": k, "t": t_kf_next, "tid": tid, "tid_true": dd[4], "mis": bool(dd[5]),
                                    "first": bool(new), "j": lm_key[tid], "meas": [dd[1], dd[2], dd[3]]})
            pend = []; t_kf_next += 1.0 / 30.0
assert abs(t_anchor - ST["t_anchor"]) < 1e-6, (t_anchor, ST["t_anchor"])
assert len(factors) == ST["landmark_factors"], (len(factors), ST["landmark_factors"])
H = np.loadtxt(f"{RUN}/hindsight.tum", ndmin=2)
assert len(H) == len(key_t) and np.allclose(H[:, 0], [t for _, t in key_t], atol=2e-6), "keyframe clock mismatch"
yawq = lambda q: Rot3.Quaternion(q[3], q[0], q[1], q[2]).yaw()
HY = np.array([yawq(r[4:8]) for r in H])
LM = {int(j): np.array(v) for j, v in ST["landmarks_final"].items()}
MAP = {t["id"]: np.array([t["x"] + 3.0, t["y"] + 3.0, math.radians(t["yaw_deg"])]) for t in
       json.load(open(f"{R}/sim/worlds/room_tags_map.json"))["tags"]}
G = np.array(G); wrap = lambda x: (x + math.pi) % (2 * math.pi) - math.pi
gt_at = lambda t: (np.interp(t, G[:, 0], G[:, 1]) + 3.0, np.interp(t, G[:, 0], G[:, 2]) + 3.0,
                   math.atan2(np.interp(t, G[:, 0], np.sin(G[:, 3])), np.interp(t, G[:, 0], np.cos(G[:, 3]))))
SIG = np.array([TAG_SIGMA_POS, TAG_SIGMA_POS, TAG_SIGMA_YAW])


def resid(x, y, yaw, lm, meas):
    c, s = math.cos(lm[2]), math.sin(lm[2]); dx, dy = x - lm[0], y - lm[1]
    e = np.array([c * dx + s * dy - meas[0], -s * dx + c * dy - meas[1], wrap(yaw - lm[2] - meas[2])])
    return e / SIG


for f in factors:
    h = H[f["k"]]; f["w_est"] = resid(h[1], h[2], HY[f["k"]], LM[f["j"]], f["meas"]).tolist()
    gx, gy, gyaw = gt_at(f["t"]); f["w_truth"] = resid(gx, gy, gyaw, MAP[f["tid"]], f["meas"]).tolist()
j2tid = {j: tid for tid, j in lm_key.items()}
out = {"run": RUN, "trial": a.trial, "rate": a.rate, "seed": a.seed, "keep": KEEP, "t_anchor": t_anchor,
       "events_match_logged": True, "n_events": len(regen), "clock_rows_match": True,
       "j_to_tid": j2tid, "first_sighting_mislabelled_tids": [t for t, m in first.items() if m],
       "landmarks_final_by_tid": {str(j2tid[j]): LM[j].tolist() for j in LM}, "true_map_tag0_frame": {str(i): v.tolist() for i, v in MAP.items()},
       "factors": factors}
json.dump(out, open(a.out, "w"))
print(f"OK {RUN}: {len(factors)} factors, {sum(f['mis'] for f in factors)} wrong, events match ({len(regen)}), clock match, "
      f"first-sighting mislabelled tids {out['first_sighting_mislabelled_tids']}")
