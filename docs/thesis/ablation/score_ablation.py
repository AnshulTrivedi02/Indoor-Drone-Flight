#!/usr/bin/env python3
"""EXPLORATORY attribution ablation: read-only scorer (analysis code, NOT estimator code).

Scores FGO/UKF trajectories written under any output root with the SAME metric as the thesis: evo -a (cruise), the
pinned cruise window of eval/three_way_eval.py. It imports three_way_eval's own functions (cruise_window, crop,
evo_ape_a); it never calls ekf3_tums() (that one can write into a trial directory) and writes nothing under
~/thesis_data/trials. The cruise window comes from the STORED ~/thesis_data/trials/<trial>/ukf/ground_truth.tum
(three_way_eval.GT_SUB), exactly as for the stored results; the reference is <root>/<trial>/<sub>/ground_truth.tum,
as three_way_eval.evaluate() does for every estimator.

Also reads, per run, the per-keyframe step times (timing_and_fwd.npz, t_keyframe_ns; fgo_replay.py) and the
forward-camera counts (fwd_stats.json), when present.

Usage (venv-ardupilot: three_way_eval imports pymavlink; evo_ape is called from ~/venv-evo):
  ~/venv-ardupilot/bin/python docs/thesis/ablation/score_ablation.py --root DIR --sub fgo_heading [--est fgo_traj.tum]
      [--json OUT] TRIAL...
  ~/venv-ardupilot/bin/python docs/thesis/ablation/score_ablation.py --gate [--json OUT]
--gate: scorer identity gate on the STORED outputs (root = ~/thesis_data/trials): every value must equal the stored
  eval/results/phase4_<ds>_arms.json value (key <trial>.<EST>_<arm>.evo.ate_a_cruise."+0.00") exactly. Exit 1 if not.
"""
import argparse, json, os, sys, tempfile
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO, "eval"))
import three_way_eval as T   # noqa: E402  (cruise_window, crop, evo_ape_a, write_tum, TRIALS_DIR)

BAGS = [f"{ds}_tex_r{r}" for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)]


def score_one(root, trial, sub, est_f, tmp):
    d = os.path.join(root, trial, sub)
    ep, rp = os.path.join(d, est_f), os.path.join(d, "ground_truth.tum")
    if not os.path.exists(ep):
        return {"status": "MISSING", "path": ep}
    t0, t1 = T.cruise_window(trial)
    ref, est = np.loadtxt(rp), np.loadtxt(ep)
    fin = bool(np.all(np.isfinite(est)))
    rc, ec = os.path.join(tmp, f"{trial}_{sub}_ref.tum"), os.path.join(tmp, f"{trial}_{sub}_est.tum")
    T.write_tum(rc, T.crop(ref, t0, t1)); T.write_tum(ec, T.crop(est, t0, t1))
    out = {"status": "OK" if fin else "NONFINITE", "window_s": [t0, t1], "ate_a_cruise_m": T.evo_ape_a(rc, ec)}
    tp = os.path.join(d, "timing_and_fwd.npz")
    z = np.load(tp) if os.path.exists(tp) else None
    if z is not None and "t_keyframe_ns" in z.files:      # FGO only (the UKF npz has other keys)
        s = z["t_keyframe_ns"] / 1e6
        out["step_ms"] = {"n": int(len(s)), "median": float(np.median(s)), "p95": float(np.percentile(s, 95)),
                          "max": float(s.max()), "sum_s": float(s.sum() / 1e3)}
    fp = os.path.join(d, "fwd_stats.json")
    if os.path.exists(fp):
        out["fwd_counts"] = json.load(open(fp)).get("counts")
    return out


def gate(js):
    cases = [("fgo_heading", "fgo_traj.tum", "FGO_heading"), ("fgo_baseline", "fgo_traj.tum", "FGO_baseline"),
             ("ukf_heading", "ukf_traj.tum", "UKF_heading"), ("ukf_baseline", "ukf_traj.tum", "UKF_baseline")]
    stored = {ds: json.load(open(os.path.join(REPO, "eval", "results", f"phase4_{ds}_arms.json")))
              for ds in ("fwdc", "fwdplainc")}
    res, bad = {}, 0
    with tempfile.TemporaryDirectory() as tmp:
        for t in BAGS:
            for sub, f, key in cases:
                r = score_one(T.TRIALS_DIR, t, sub, f, tmp)
                ref = stored[t.split("_")[0]][t][key]["evo"]["ate_a_cruise"]["+0.00"]
                ok = r.get("ate_a_cruise_m") == ref
                bad += not ok
                res[f"{t}.{key}"] = {"scored": r.get("ate_a_cruise_m"), "stored": ref, "equal": ok}
                print(f"{t:18} {key:13} scored {r.get('ate_a_cruise_m')}  stored {ref}  {'EQUAL' if ok else 'DIFFERENT'}")
    print(f"[gate] {len(res) - bad}/{len(res)} equal")
    if js:
        json.dump({"gate": "score_ablation identity on stored outputs", "n": len(res), "n_equal": len(res) - bad,
                   "cases": res}, open(js, "w"), indent=1)
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("trials", nargs="*")
    ap.add_argument("--root"); ap.add_argument("--sub"); ap.add_argument("--est", default="fgo_traj.tum")
    ap.add_argument("--json"); ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()
    if a.gate:
        sys.exit(gate(a.json))
    root = os.path.expanduser(a.root)
    assert os.path.realpath(root) != os.path.realpath(T.TRIALS_DIR) or a.sub, "give --sub"
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for t in a.trials or BAGS:
            out[t] = score_one(root, t, a.sub, a.est, tmp)
            print(t, json.dumps(out[t]))
    if a.json:
        json.dump({"label": "EXPLORATORY", "metric": "evo -a (cruise), three_way_eval pinned window",
                   "root": root, "sub": a.sub, "est": a.est, "trials": out}, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
