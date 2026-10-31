#!/usr/bin/env python3
"""E6 scorer (tier-1 extension experiment "map once, fly again"; docs/thesis/tier1/e6_preregistration.md §4).

One test flight (T_A_r1/r2/r3), every E6 arm in ONE frame (the world frame) with ONE scorer, no alignment:
  (i)   surveyed map  : the stored Experiment 2 tracks ~/thesis_data/trials/<t>/room_ukf/{ukf_live,ukf_rts}.tum and
                        room_fgo/{fgo_live,fgo_batch}.tum (world frame), read only;
  (ii)  FGO map       : ~/thesis_data/tier1/<t>/room_{ukf,fgo}_e6_<fgo-map name>/ (world frame);
  (iii) UKF map       : ~/thesis_data/tier1/<t>/room_{ukf,fgo}_e6_<ukf-map name>/ (world frame);
  (iv)  no map (loop closure online): the stored Experiment 3 FGO ~/thesis_data/trials/<t>/lc_fgo_lc_t245/ and the E5
                        landmark UKF ~/thesis_data/tier1/<t>/lc_ukf_lc_t245/ (both in tag 0's frame), read only.
Frame: tag 0's frame -> world by ADDING tag 0's surveyed position (-3, -3); tag 0's yaw is 0 (asserted), so this is a
translation only: the registered transform eval/l_score.py:28 applies to ground truth (it subtracts (-3, -3) from GT;
adding it to the estimate gives the same error to round-off). No fit to any estimate.
Window and metrics: copied from eval/l_score.py (lap window from fly_trial.log 'LAP k LEG 0 START' / 'LAPS END' on the
SITL clock, mapped to the bag clock by the /imu/time_ref lower envelope; horizontal error at the track's own samples;
RMSE and max over the window, per-lap RMSE laps 1-5, lap-5 / lap-1). eval/tag_score.py uses the same window.
Usage (venv-tags or venv-evo):
  e6_score.py <trial> --fgo-map-name N1 --ukf-map-name N2 --json docs/thesis/tier1/scores/e6_<trial>.json
  e6_score.py <trial> --stored-only --json ...   (arms (i) and (iv) only: the scorer gate S-E6, which compares them
                                                   with the stored scores; §7)
--json must be a NEW file under docs/thesis/tier1/ or ~/thesis_data/tier1/."""
import argparse, json, os, re, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(REPO, "src", "tags")); import tag_measure as TM

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json", required=True)
ap.add_argument("--fgo-map-name"); ap.add_argument("--ukf-map-name"); ap.add_argument("--stored-only", action="store_true")
a = ap.parse_args()
_real = lambda p: os.path.realpath(os.path.expanduser(p))
_under = lambda p, r: _real(p) == _real(r) or _real(p).startswith(_real(r) + os.sep)
if not (_under(a.json, "~/thesis_data/tier1") or _under(a.json, os.path.join(REPO, "docs", "thesis", "tier1"))) or os.path.exists(a.json):
    sys.exit(f"[e6] REFUSED: --json must be a NEW file under ~/thesis_data/tier1 or docs/thesis/tier1/ (got {a.json!r})")
if not a.stored_only and (a.fgo_map_name is None or a.ukf_map_name is None):
    sys.exit("[e6] REFUSED: --fgo-map-name and --ukf-map-name are required unless --stored-only")
TR_ = os.path.expanduser("~/thesis_data/trials"); T1_ = os.path.expanduser("~/thesis_data/tier1")
D = os.path.join(TR_, a.trial)
tag0 = TM.load_map(os.path.join(REPO, "sim", "worlds", "room_tags_map.json"))[0]
assert abs(tag0["yaw"]) < 1e-9, "the tag-0 -> world mapping below assumes tag 0 has yaw 0"
OFF = np.array([tag0["p"][0], tag0["p"][1]])

# ---- ground truth (world), /imu/time_ref, lap bounds: eval/l_score.py:29-55 with the world frame kept ----
ts = get_typestore(Stores.ROS2_JAZZY); G, TR = [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs["/ground_truth/pose"], cs["/imu/time_ref"]]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
        else:
            G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y))
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

ARMS = [("(i) surveyed", "FGO", "live", f"{D}/room_fgo/fgo_live.tum", "world"),
        ("(i) surveyed", "FGO", "hindsight", f"{D}/room_fgo/fgo_batch.tum", "world"),
        ("(i) surveyed", "UKF", "live", f"{D}/room_ukf/ukf_live.tum", "world"),
        ("(i) surveyed", "UKF", "hindsight", f"{D}/room_ukf/ukf_rts.tum", "world"),
        ("(iv) no map, LC online", "FGO", "live", f"{D}/lc_fgo_lc_t245/live.tum", "tag0"),
        ("(iv) no map, LC online", "FGO", "hindsight", f"{D}/lc_fgo_lc_t245/hindsight.tum", "tag0"),
        ("(iv) no map, LC online", "UKF", "live", f"{T1_}/{a.trial}/lc_ukf_lc_t245/live.tum", "tag0"),
        ("(iv) no map, LC online", "UKF", "hindsight", f"{T1_}/{a.trial}/lc_ukf_lc_t245/hindsight.tum", "tag0")]
if not a.stored_only:
    for arm, nm in (("(ii) FGO map", a.fgo_map_name), ("(iii) UKF map", a.ukf_map_name)):
        ARMS += [(arm, "FGO", "live", f"{T1_}/{a.trial}/room_fgo_e6_{nm}/fgo_live.tum", "world"),
                 (arm, "FGO", "hindsight", f"{T1_}/{a.trial}/room_fgo_e6_{nm}/fgo_batch.tum", "world"),
                 (arm, "UKF", "live", f"{T1_}/{a.trial}/room_ukf_e6_{nm}/ukf_live.tum", "world"),
                 (arm, "UKF", "hindsight", f"{T1_}/{a.trial}/room_ukf_e6_{nm}/ukf_rts.tum", "world")]

out = {"trial": a.trial, "frame": "world (Gazebo ENU); tag-0-frame tracks + tag 0's surveyed position (-3, -3), yaw 0",
       "lap_bounds_s": bounds, "fgo_map_name": a.fgo_map_name, "ukf_map_name": a.ukf_map_name, "tracks": {}}
for arm, est, kind, p, frame in ARMS:
    key = f"{arm} | {est} {kind}"
    if not os.path.exists(p):
        out["tracks"][key] = {"missing": p}; print(f"{key:45s} MISSING {p}"); continue
    x = np.loadtxt(p, ndmin=2)
    xy = x[:, 1:3] + (OFF if frame == "tag0" else 0.0)
    e = np.hypot(xy[:, 0] - np.interp(x[:, 0], G[:, 0], G[:, 1]), xy[:, 1] - np.interp(x[:, 0], G[:, 0], G[:, 2]))
    w = (x[:, 0] >= bounds[0]) & (x[:, 0] <= bounds[-1])
    per = [float(np.sqrt(np.mean(e[(x[:, 0] >= b0) & (x[:, 0] < b1)] ** 2))) for b0, b1 in zip(bounds[:-1], bounds[1:])]
    r = {"path": p, "frame_in": frame, "rmse_m": float(np.sqrt(np.mean(e[w] ** 2))), "max_m": float(e[w].max()),
         "n": int(w.sum()), "per_lap_rmse_m": per, "lap5_over_lap1": per[-1] / per[0] if len(per) == 5 else None}
    out["tracks"][key] = r
    print(f"{key:45s} RMSE {r['rmse_m']:.4f} max {r['max_m']:.4f} | per lap " + " ".join(f"{v:.4f}" for v in per))

# ---- S-E6: the stored arms must reproduce the stored scores (eval/results/expT, expL; tier-1 E5 scores) ----
chk = []
eT = json.load(open(os.path.join(REPO, "eval", "results", "expT", f"{a.trial}.json")))["tracks"]
eL = json.load(open(os.path.join(REPO, "eval", "results", "expL", f"{a.trial}_t245.json")))
e5 = json.load(open(os.path.join(REPO, "docs", "thesis", "tier1", "scores", f"e5_{a.trial}.json")))
for key, ref, src in (("(i) surveyed | FGO live", eT["FGO live"]["horiz_err_m"]["rmse"], "expT FGO live"),
                      ("(i) surveyed | FGO hindsight", eT["FGO hindsight (whole-flight batch)"]["horiz_err_m"]["rmse"], "expT FGO batch"),
                      ("(i) surveyed | UKF live", eT["UKF live"]["horiz_err_m"]["rmse"], "expT UKF live"),
                      ("(i) surveyed | UKF hindsight", eT["RTS-UKF (hindsight)"]["horiz_err_m"]["rmse"], "expT RTS-UKF")):
    chk.append({"track": key, "stored": ref, "source": f"eval/results/expT/{a.trial}.json {src} rmse",
                "e6": out["tracks"][key].get("rmse_m"), "abs_diff": abs(out["tracks"][key].get("rmse_m", np.nan) - ref)})
for est, src, js in (("FGO", f"eval/results/expL/{a.trial}_t245.json", eL), ("UKF", f"docs/thesis/tier1/scores/e5_{a.trial}.json", e5)):
    for kind in ("live", "hindsight"):
        key = f"(iv) no map, LC online | {est} {kind}"; ref = js["tracks"][f"lc {kind}"]
        diffs = [abs(out["tracks"][key]["rmse_m"] - ref["rmse_m"]), abs(out["tracks"][key]["max_m"] - ref["max_m"])] + \
                [abs(u - v) for u, v in zip(out["tracks"][key]["per_lap_rmse_m"], ref["per_lap_rmse_m"])]
        chk.append({"track": key, "stored": ref["rmse_m"], "source": f"{src} lc {kind} (rmse, max, per-lap)",
                    "e6": out["tracks"][key]["rmse_m"], "abs_diff": max(diffs)})
    if js["lap_bounds_s"] != bounds:
        chk.append({"track": f"lap bounds vs {src}", "abs_diff": float(np.max(np.abs(np.array(js["lap_bounds_s"]) - np.array(bounds))))})
tw = json.load(open(os.path.join(REPO, "eval", "results", "expT", f"{a.trial}.json")))["window_s"]
chk.append({"track": "window vs expT window_s", "abs_diff": max(abs(tw[0] - bounds[0]), abs(tw[1] - bounds[-1]))})
TOL = 1e-9
out["scorer_gate_S_E6"] = {"tolerance_m": TOL, "checks": chk, "pass": all(c["abs_diff"] <= TOL for c in chk)}
print(f"S-E6 scorer gate: {'PASS' if out['scorer_gate_S_E6']['pass'] else 'FAIL'} "
      f"(max |diff| {max(c['abs_diff'] for c in chk):.3g} m over {len(chk)} checks, tolerance {TOL:g} m)")
json.dump(out, open(a.json, "w"), indent=1)
sys.exit(0 if out["scorer_gate_S_E6"]["pass"] else 4)
