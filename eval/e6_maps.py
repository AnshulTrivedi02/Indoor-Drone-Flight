#!/usr/bin/env python3
"""E6 map production (tier-1 extension experiment "map once, fly again"; docs/thesis/tier1/e6_preregistration.md §3).

From ONE mapping flight's two loop-closure replays (both with --mode lc --t-max 245, gauge tag 0):
  (a) FGO map: the Experiment 3 keyframe FGO's hindsight landmark estimate, stats.json "landmarks_final"
      (lc_fgo_replay.py: iSAM2's full-graph estimate after 5 extra updates, the Experiment 3 hindsight; keyed by
      landmark index j in order of first sighting);
  (b) UKF map: the E5 landmark UKF's landmarks, stats.json "landmarks_in_state_final_filtered" (keyed by landmark
      index with the tag id). A static landmark (identity transition, zero process noise, never removed in LC) has
      its RTS-smoothed estimate equal to its filtered estimate at the final node, so this IS the RTS-smoothed map.
writes, in the WORLD frame, two map files in the room_tags_map.json layout (map_fgo.json, map_ukf.json) and
map_errors.json (each landmark against the surveyed map).

Frame: both replays express landmarks in tag 0's frame (tag 0 = the origin, held at it). World = tag-0 frame + tag 0's
surveyed pose (-3, -3, yaw 0): a fixed, registered translation (eval/l_score.py:28), no fit. Tag 0's entry in both maps
is therefore its surveyed pose, by construction; tag z (0.001 m), roll and pitch are the surveyed ones (the
flat-floor assumption of Experiment 3).
FGO landmark index -> tag id: recomputed from the flight's /tags/raw with lc_fgo_replay.py's own rules (central third,
time order, the first gauge-tag detection opens the graph, cut at anchor + t-max), and required to equal the landmark
UKF's recorded mapping (the same rule) for every index. The anchor time and landmark count of the two replays must
also agree (the E5 invariant, e5_design.md §5.3, checked here because the replays' own reference path does not exist
for a new flight).
Usage (venv-tags or venv-evo):
  e6_maps.py <mapping_trial> --fgo-dir DIR --ukf-dir DIR --out-dir ~/thesis_data/tier1/e6/maps/<mapping_trial>
  e6_maps.py <trial> --fgo-dir DIR --ukf-dir DIR --errors-only   (prints the errors, writes nothing; used for the
                                                                    stored T_A maps cited in the pre-registration)"""
import argparse, json, math, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.join(HERE, "..")
TRUE_MAP = os.path.join(REPO, "sim", "worlds", "room_tags_map.json")
FX, CX, CY = 554.3827056884766, 320.0, 240.0; R_VALID = (1.0 / 3.0) * math.hypot(CX, CY)   # lc_fgo_replay.py constants
wrap = lambda a_: (a_ + math.pi) % (2 * math.pi) - math.pi

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--fgo-dir", required=True)
ap.add_argument("--ukf-dir", required=True); ap.add_argument("--out-dir"); ap.add_argument("--errors-only", action="store_true")
ap.add_argument("--gauge-tag", type=int, default=0); ap.add_argument("--t-max", type=float, default=245.0)
a = ap.parse_args()
if not a.errors_only:
    _real = lambda p: os.path.realpath(os.path.expanduser(p))
    t1 = _real("~/thesis_data/tier1")
    if a.out_dir is None or not _real(a.out_dir).startswith(t1 + os.sep):
        sys.exit("[e6] REFUSED: --out-dir must be under ~/thesis_data/tier1")
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        sys.exit(f"[e6] REFUSED: {a.out_dir} exists and is not empty")

truth = json.load(open(TRUE_MAP)); T = {t["id"]: t for t in truth["tags"]}
t0 = T[a.gauge_tag]; assert abs(t0["yaw_deg"]) < 1e-12, "the tag-0 -> world translation assumes tag 0 has yaw 0"
fs = json.load(open(os.path.join(a.fgo_dir, "stats.json"))); us = json.load(open(os.path.join(a.ukf_dir, "stats.json")))
if fs.get("mode") != "lc" or us.get("mode") != "lc":
    sys.exit("[e6] both replays must be --mode lc")

# ---- FGO landmark index -> tag id from /tags/raw (lc_fgo_replay.py read loop + landmark_key in LC) ----
ts = get_typestore(Stores.ROS2_JAZZY); dets = []
with Reader(os.path.expanduser(f"~/thesis_data/trials/{a.trial}/bag")) as r:
    for con, _, raw in r.messages(connections=[c for c in r.connections if c.topic == "/tags/raw"]):
        m = ts.deserialize_cdr(raw, con.msgtype); tt = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        u, v = FX * m.pose.position.x / m.pose.position.z + CX, FX * m.pose.position.y / m.pose.position.z + CY
        if math.hypot(u - CX, v - CY) > R_VALID:
            continue
        dets.append((tt, int(m.header.frame_id.split("_")[1])))
dets.sort(key=lambda e: e[0])          # stable, as ev.sort in the replay
order = []; t_anch = None
for tt, tid in dets:
    if t_anch is None:
        if tid != a.gauge_tag:
            continue
        t_anch = tt
    if tt > t_anch + a.t_max:
        break
    if tid not in order:
        order.append(tid)
fgo_tid = {j: tid for j, tid in enumerate(order)}
ukf_tid = {int(k): int(v["tag"]) for k, v in us["landmarks_in_state_final_filtered"].items()}
inv = {"t_anchor": {"fgo": fs["t_anchor"], "ukf": us["t_anchor"], "from_tags_raw": t_anch,
                    "ok": fs["t_anchor"] == us["t_anchor"] == t_anch},
       "landmarks": {"fgo": fs["landmarks"], "ukf": us["landmarks"], "from_tags_raw": len(order),
                     "ok": fs["landmarks"] == us["landmarks"] == len(order) == len(fs["landmarks_final"])},
       "index_to_tag": {"fgo_from_tags_raw": {str(k): v for k, v in fgo_tid.items()}, "ukf_recorded": {str(k): v for k, v in ukf_tid.items()},
                        "ok": all(fgo_tid.get(k) == v for k, v in ukf_tid.items()) and fgo_tid.get(0) == a.gauge_tag
                              and set(fgo_tid.values()) == set(T)},
       "fgo_gauge_at_origin_max_abs": float(max(abs(x) for x in fs["landmarks_final"]["0"]))}
inv["pass"] = inv["t_anchor"]["ok"] and inv["landmarks"]["ok"] and inv["index_to_tag"]["ok"]
if not inv["pass"]:
    print(json.dumps(inv, indent=1)); sys.exit("[e6] map invariants FAILED (no map written)")

# ---- world-frame maps ----
lm = {"fgo": {fgo_tid[int(j)]: v for j, v in fs["landmarks_final"].items() if int(j) != 0},
      "ukf": {int(v["tag"]): v["pose"] for v in us["landmarks_in_state_final_filtered"].values()}}
res = {"trial": a.trial, "invariants": inv, "frame": "world (Gazebo ENU) = tag-0 frame + (-3, -3), yaw 0 (registered, no fit)",
       "maps": {}, "errors": {}}
for src in ("fgo", "ukf"):
    tags = []
    for tid in sorted(T):
        t = dict(T[tid])
        if tid != a.gauge_tag:
            L = lm[src][tid]
            t.update({"x": L[0] + t0["x"], "y": L[1] + t0["y"], "yaw_rad": float(wrap(L[2])), "yaw_deg": math.degrees(wrap(L[2]))})
        else:
            t["yaw_rad"] = math.radians(t["yaw_deg"])
        tags.append(t)
    mp = {"tags": tags, "frame": truth["frame"],
          "source": {"e6_map": src, "mapping_trial": a.trial, "replay_dir": a.fgo_dir if src == "fgo" else a.ukf_dir,
                     "key": "landmarks_final" if src == "fgo" else "landmarks_in_state_final_filtered (= RTS at the final node)",
                     "gauge": f"tag {a.gauge_tag} = surveyed pose (frame definition)", "z_roll_pitch": "surveyed (flat floor)"}}
    res["maps"][src] = mp
    per = {}
    for t in tags:
        if t["id"] == a.gauge_tag:
            continue
        tr = T[t["id"]]
        per[str(t["id"])] = {"pos_err_m": math.hypot(t["x"] - tr["x"], t["y"] - tr["y"]), "dx_m": t["x"] - tr["x"],
                             "dy_m": t["y"] - tr["y"], "yaw_err_deg": math.degrees(wrap(t["yaw_rad"] - math.radians(tr["yaw_deg"])))}
    pe = np.array([p["pos_err_m"] for p in per.values()]); ye = np.array([abs(p["yaw_err_deg"]) for p in per.values()])
    res["errors"][src] = {"per_tag": per, "n_tags": int(len(pe)), "pos_rms_m": float(np.sqrt(np.mean(pe ** 2))),
                          "pos_max_m": float(pe.max()), "pos_mean_m": float(pe.mean()),
                          "yaw_rms_deg": float(np.sqrt(np.mean(ye ** 2))), "yaw_max_abs_deg": float(ye.max())}
    print(f"{a.trial} {src.upper()} map: position RMS {res['errors'][src]['pos_rms_m']:.4f} m, max {pe.max():.4f} m; "
          f"yaw RMS {res['errors'][src]['yaw_rms_deg']:.3f} deg, max {ye.max():.3f} deg (7 non-gauge tags)")
res["errors"]["fgo_over_ukf_pos_rms"] = res["errors"]["fgo"]["pos_rms_m"] / res["errors"]["ukf"]["pos_rms_m"]
if a.errors_only:
    print(json.dumps({k: res["errors"][k] for k in ("fgo", "ukf")}, indent=1)); sys.exit(0)
os.makedirs(a.out_dir, exist_ok=True)
for src in ("fgo", "ukf"):
    json.dump(res["maps"][src], open(os.path.join(a.out_dir, f"map_{src}.json"), "w"), indent=1)
json.dump({k: v for k, v in res.items() if k != "maps"}, open(os.path.join(a.out_dir, "map_errors.json"), "w"), indent=1)
print(f"wrote {a.out_dir}/map_fgo.json, map_ukf.json, map_errors.json")
