"""Regression: real_score (strict prereg, fixed window = three_way_eval's pinned cruise window) against three_way_eval's
own evo -a call on dsn_tex_r1, UKF and FGO, on the CURRENT stored outputs (read only)."""
import copy, json, os, sys, tempfile
import numpy as np
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")      # the scripts directory
# Run: ~/venv-ardupilot/bin/python <this> OUT.json   (writes evo scratch to a temporary directory only)
sys.path.insert(0, W)
import real_score as RS
import three_way_eval as TW

T = os.path.expanduser("~/thesis_data/trials/dsn_tex_r1")
t0, t1 = TW.cruise_window("dsn_tex_r1")
out = {"trial": "dsn_tex_r1", "three_way_window_s": [t0, t1]}
g = np.loadtxt(f"{T}/ukf/ground_truth.tum")
with tempfile.TemporaryDirectory() as d:
    pre = copy.deepcopy(RS.DEFAULT_PREREG); pre["window"] = {"rule": "speed", "speed_mps": None}
    pre["estimator_records"] = {"UKF": "TUM", "FGO": "TUM"}
    json.dump(pre, open(f"{d}/speed.json", "w"))
    r = RS.main(["--prereg", f"{d}/speed.json", "--mocap", f"{T}/ukf/ground_truth.tum", "--work-dir", f"{d}/w0",
                 "--out", f"{d}/s.json"])
    out["speed_rule_window_s"] = r["window_s"]
    for lab, sub, f in (("UKF", "ukf", "ukf_traj.tum"), ("FGO", "fgo", "fgo_traj.tum")):
        ref, est = np.loadtxt(f"{T}/{sub}/ground_truth.tum"), np.loadtxt(f"{T}/{sub}/{f}")
        rc, ec = f"{d}/{lab}_r.tum", f"{d}/{lab}_e.tum"
        TW.write_tum(rc, TW.crop(ref, t0, t1)); TW.write_tum(ec, TW.crop(est, t0, t1))
        tw = TW.evo_ape_a(rc, ec)
        pre = copy.deepcopy(RS.DEFAULT_PREREG); pre["window"] = {"rule": "fixed", "t0_s": t0, "t1_s": t1}
        pre["estimator_records"] = {lab: "TUM"}
        json.dump(pre, open(f"{d}/{lab}.json", "w"))
        s = RS.main(["--prereg", f"{d}/{lab}.json", "--mocap", f"{T}/{sub}/ground_truth.tum", "--est", f"{lab}={T}/{sub}/{f}",
                     "--work-dir", f"{d}/w{lab}", "--out", f"{d}/{lab}_out.json"])
        out[lab] = {"three_way_evo_a": tw, "real_score_evo_a": s["estimators"][lab]["evo_ape_a_se3"]["rmse_m"],
                    "identical": tw == s["estimators"][lab]["evo_ape_a_se3"]["rmse_m"]}
print(json.dumps(out, indent=1))
json.dump(out, open(sys.argv[1], "w"), indent=1)
