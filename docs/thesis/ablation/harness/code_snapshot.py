"""Run-code snapshot (pre-registration §9 step 4): HEAD, git status of src/eval, sha256 of the run code."""
import hashlib, json, subprocess, sys, time
R = "/home/makerspace/thesis_ws"
F = ["src/estimators/fgo/fgo_replay.py", "src/estimators/fgo/fgo_core.py", "src/estimators/fgo/factors.py",
     "src/estimators/measurement_models.py", "src/estimators/imu_timing.py", "eval/three_way_eval.py",
     "eval/cruise_window.py", "docs/thesis/ablation/score_ablation.py", "src/estimators/fgo_cpp/tools/heavy.py"]
g = lambda *c: subprocess.run(["git", "-C", R, *c], capture_output=True, text=True).stdout.strip()
d = {"taken_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "head": g("rev-parse", "HEAD"),
     "status_src_eval_tracked": g("status", "--porcelain", "--untracked-files=no", "src", "eval"),
     "untracked_src_eval": g("status", "--porcelain", "src", "eval"),
     "sha256": {f: hashlib.sha256(open(f"{R}/{f}", "rb").read()).hexdigest() for f in F}}
json.dump(d, open(sys.argv[1], "w"), indent=1); print(json.dumps(d, indent=1))
