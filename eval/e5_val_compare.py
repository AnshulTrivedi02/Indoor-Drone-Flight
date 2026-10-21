#!/usr/bin/env python3
"""E5 validation gates V-E5a/b/c (docs/thesis/tier1/e5_design.md §8.4; preregistration.md §4): compare one V-E5 run
(<in-root>/<trial>/lc_ukf_val_<task>/) DIRECTLY with the stored Experiment 2 UKF tracks
(~/thesis_data/trials/<trial>/room_ukf/{ukf_live.tum, ukf_rts.tum, stats.json}), never through another V-E5 run.
Live and RTS separately, per flight. PASS iff, for both tracks:
  1. rows match 1:1: the same number of rows and identical 6-dp timestamp strings (no interpolation);
  2. t_anchor and n_tag_fused equal the stored room_ukf/stats.json values;
  3. RMS horizontal position difference <= 1.0 mm over the rows inside the scored lap window
     (eval/results/expT/<trial>.json window_s; the same figure over all rows is reported beside it);
  4. max per-sample horizontal difference <= 2.0 mm over the same window;
  5. flow and range accept/reject counts equal to V-E5a's (lc_ukf_val_world/gate_log.npz, the count reference). A
     differing decision whose two test ratios both lie within 1e-9 (relative) of the gate (test ratio 1.0) is a
     ROUND-OFF flip, logged, and conditions 3 and 4 decide; any other difference is a FAIL. For V-E5a itself,
     condition 5 is "reference" (not judged).
Byte identity of the two TUM files is reported, never the gate. --delta-rmse also reads the ground truth from the bag
and reports, per track, the stored and new horizontal RMSE over the window and |dRMSE| (tag_score.py's err(): errors at
the track's own samples, ground truth interpolated; the §8 failure report; informational, never the gate). Reads only; writes only --json (a NEW file under
docs/thesis/tier1/ or ~/thesis_data/tier1/).
Usage (~/venv-evo): python3 eval/e5_val_compare.py TRIAL --task world|knownmap|augmented [--in-root DIR] [--json OUT]
                   [--delta-rmse]
Exit 0 = PASS, 1 = FAIL."""
import argparse, hashlib, json, os, sys
import numpy as np

RMS_TOL_M = 1.0e-3
MAX_TOL_M = 2.0e-3
FLIP_BAND = 1e-9


def read_tum(path):
    ts, xy = [], []
    for ln in open(path):
        f = ln.split()
        if not f:
            continue
        ts.append(f[0]); xy.append((float(f[1]), float(f[2])))
    return ts, np.array(xy, float).reshape(-1, 2)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def compare_track(ref_path, new_path, window):
    tr, xr = read_tum(ref_path); tn, xn = read_tum(new_path)
    out = {"ref": ref_path, "new": new_path, "rows_ref": len(tr), "rows_new": len(tn),
           "byte_identical": sha(ref_path) == sha(new_path)}
    out["rows_match"] = len(tr) == len(tn) and tr == tn
    if not out["rows_match"]:
        k = next((i for i, (a, b) in enumerate(zip(tr, tn)) if a != b), min(len(tr), len(tn)))
        out["first_row_mismatch"] = {"index": k, "ref": tr[k] if k < len(tr) else None, "new": tn[k] if k < len(tn) else None}
        out["pass"] = False
        return out
    d = np.hypot(*(xn - xr).T)
    t = np.array([float(s) for s in tr])
    w = (t >= window[0]) & (t <= window[1])
    out.update({"n_window": int(w.sum()), "rms_window_m": float(np.sqrt(np.mean(d[w] ** 2))) if w.any() else None,
                "max_window_m": float(d[w].max()) if w.any() else None,
                "rms_all_m": float(np.sqrt(np.mean(d ** 2))) if len(d) else None,
                "max_all_m": float(d.max()) if len(d) else None})
    out["pass"] = bool(w.any() and out["rms_window_m"] <= RMS_TOL_M and out["max_window_m"] <= MAX_TOL_M)
    return out


def read_gt(bag):
    """(t, x, y) of /ground_truth/pose from the bag (header stamps), as eval/tag_score.py."""
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY); G = []
    with Reader(bag) as rd:
        cs = {c.topic: c for c in rd.connections}
        for con, _, raw in rd.messages(connections=[cs["/ground_truth/pose"]]):
            m = ts.deserialize_cdr(raw, con.msgtype)
            G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y))
    return np.array(G)


def rmse_vs_gt(path, G, window):
    """tag_score.py err() (horizontal part) and its RMSE over the window."""
    ts, xy = read_tum(path); t = np.array([float(s) for s in ts])
    w = (t >= window[0]) & (t <= window[1])
    e = np.hypot(xy[w, 0] - np.interp(t[w], G[:, 0], G[:, 1]), xy[w, 1] - np.interp(t[w], G[:, 0], G[:, 2]))
    return float(np.sqrt(np.mean(e ** 2)))


def compare_gates(ref_npz, new_npz):
    """§8.4 condition 5. Returns a dict with 'pass' and every flip."""
    a, b = np.load(ref_npz), np.load(new_npz)
    out = {"ref": ref_npz, "new": new_npz}
    names = {0: "flow_x", 1: "flow_y", 2: "range"}
    out["counts_ref"] = {names[c]: int(a["accepted"][a["code"] == c].sum()) for c in names}
    out["counts_new"] = {names[c]: int(b["accepted"][b["code"] == c].sum()) for c in names}
    out["counts_equal"] = out["counts_ref"] == out["counts_new"] and len(a["t"]) == len(b["t"])
    aligned = len(a["t"]) == len(b["t"]) and np.array_equal(a["t"], b["t"]) and np.array_equal(a["code"], b["code"])
    out["decisions_aligned"] = bool(aligned)
    if not aligned:                                    # a different set of gated decisions: not a round-off flip
        out["pass"] = False; out["reason"] = "gated decision sequences differ (time or axis): not classifiable as round-off"
        return out
    diff = np.nonzero(a["accepted"] != b["accepted"])[0]
    flips = []
    for i in diff:
        ra, rb = float(a["test"][i]), float(b["test"][i])
        flips.append({"t": float(a["t"][i]), "axis": names[int(a["code"][i])], "test_ref": ra, "test_new": rb,
                      "roundoff": abs(ra - 1.0) <= FLIP_BAND and abs(rb - 1.0) <= FLIP_BAND})
    out["flips"] = flips
    out["n_flips"] = len(flips); out["n_roundoff_flips"] = sum(f["roundoff"] for f in flips)
    out["pass"] = all(f["roundoff"] for f in flips)
    return out


def judge(trial, task, in_root, trials_root, expt_dir, gt=None):
    new_dir = os.path.join(in_root, trial, f"lc_ukf_val_{task}")
    ref_dir = os.path.join(trials_root, trial, "room_ukf")
    window = json.load(open(os.path.join(expt_dir, f"{trial}.json")))["window_s"]
    rs, ns = json.load(open(f"{ref_dir}/stats.json")), json.load(open(f"{new_dir}/stats.json"))
    res = {"trial": trial, "task": task, "window_s": window, "tolerance": {"rms_m": RMS_TOL_M, "max_m": MAX_TOL_M,
           "flip_band": FLIP_BAND}}
    res["anchor_tagcount"] = {"t_anchor": [rs["t_anchor"], ns["t_anchor"]], "n_tag_fused": [rs["n_tag_fused"], ns["n_tag_fused"]],
                              "pass": rs["t_anchor"] == ns["t_anchor"] and rs["n_tag_fused"] == ns["n_tag_fused"]}
    res["live"] = compare_track(f"{ref_dir}/ukf_live.tum", f"{new_dir}/ukf_live.tum", window)
    res["rts"] = compare_track(f"{ref_dir}/ukf_rts.tum", f"{new_dir}/ukf_rts.tum", window)
    if task == "world":
        res["gates"] = {"pass": True, "note": "V-E5a is the count reference (§8.4 condition 5)"}
    else:
        res["gates"] = compare_gates(os.path.join(in_root, trial, "lc_ukf_val_world", "gate_log.npz"), f"{new_dir}/gate_log.npz")
    if gt is not None:
        for k, f in (("live", "ukf_live.tum"), ("rts", "ukf_rts.tum")):
            a_, b_ = rmse_vs_gt(f"{ref_dir}/{f}", gt, window), rmse_vs_gt(f"{new_dir}/{f}", gt, window)
            res[k]["rmse_vs_gt_m"] = {"stored": a_, "new": b_, "abs_delta": abs(b_ - a_)}
    res["PASS"] = bool(res["anchor_tagcount"]["pass"] and res["live"]["pass"] and res["rts"]["pass"] and res["gates"]["pass"])
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("trial")
    ap.add_argument("--task", choices=["world", "knownmap", "augmented"], required=True)
    ap.add_argument("--in-root", default=os.path.expanduser("~/thesis_data/tier1"))
    ap.add_argument("--json", default=None)
    ap.add_argument("--delta-rmse", action="store_true", help="also report |dRMSE| against ground truth (reads the bag)")
    a = ap.parse_args()
    real = lambda p: os.path.realpath(os.path.expanduser(p))
    under = lambda p, r: real(p) == real(r) or real(p).startswith(real(r) + os.sep)
    here = os.path.dirname(os.path.abspath(__file__))
    t1d, t1docs = "~/thesis_data/tier1", os.path.join(here, "..", "docs", "thesis", "tier1")
    if not under(a.in_root, t1d):
        sys.exit(f"[tier1] REFUSED: --in-root {a.in_root!r} is not under {t1d}")
    if a.json is not None and (not (under(a.json, t1d) or under(a.json, t1docs)) or os.path.exists(a.json)):
        sys.exit(f"[tier1] REFUSED: --json must be a NEW file under {t1d} or docs/thesis/tier1/ (got {a.json!r})")
    trials = os.path.expanduser("~/thesis_data/trials")
    gt = read_gt(os.path.join(trials, a.trial, "bag")) if a.delta_rmse else None
    res = judge(a.trial, a.task, os.path.expanduser(a.in_root), trials, os.path.join(here, "results", "expT"), gt)
    for k in ("live", "rts"):
        r = res[k]
        print(f"{a.trial} {a.task:9s} {k:4s} rows {r['rows_new']}/{r['rows_ref']} match={r['rows_match']} "
              f"byte_identical={r['byte_identical']} rms_win={r.get('rms_window_m')} max_win={r.get('max_window_m')} "
              f"rms_all={r.get('rms_all_m')} dRMSE={r.get('rmse_vs_gt_m')} -> {'PASS' if r['pass'] else 'FAIL'}")
    print(f"anchor/tag count {res['anchor_tagcount']}  gates pass={res['gates']['pass']}  ==> {'PASS' if res['PASS'] else 'FAIL'}")
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    sys.exit(0 if res["PASS"] else 1)


if __name__ == "__main__":
    main()
