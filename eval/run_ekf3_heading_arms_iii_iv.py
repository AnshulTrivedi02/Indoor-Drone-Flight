#!/usr/bin/env python3
"""Run arms (iii) UKF and (iv) FGO heading at sigma_psi=5 deg on all 18 Phase-4 bags
(docs/thesis/ekf3_heading_replay/preregistration.md, D139 order step 6).

4-way parallel (standing decision rule 6: this is a non-timing experiment), wrapped as ONE
heavy.py step for the WHOLE batch (per the brief: "up to 4 in parallel per the standing rule,
through heavy.py"). Uses the additive FWD_SIGMA_PSI_DEG env var (proven byte-identical on the
default/unset path against the stored fwdc_blank_r1 heading arm for both estimators --
eval/results/ekf3_heading_replay/gates.json "sigma_option_byte_identity_proof" -- before this
script was ever run with it set).

Writes to UKF_OUT_ROOT/FGO_OUT_ROOT = ~/thesis_data/ekf3_heading_replay/{ukf,fgo}/, never into
~/thesis_data/trials/. Reads bags from UKF_BAG_ROOT/FGO_BAG_ROOT = a pre-decompressed,
sha256-verified copy under ~/thesis_data/ekf3_heading_replay/bag_root/ (packed bags cannot be
read directly by rosbags' Reader).

Usage: python3 src/estimators/fgo_cpp/tools/heavy.py "<desc>" -- \
         python3 eval/run_ekf3_heading_arms_iii_iv.py
"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BAG_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/bag_root")
UKF_OUT_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/ukf")
FGO_OUT_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/fgo")
LOG_DIR = os.path.expanduser("~/thesis_data/ekf3_heading_replay/arms_iii_iv_logs")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(UKF_OUT_ROOT, exist_ok=True)
os.makedirs(FGO_OUT_ROOT, exist_ok=True)

BAGS = [f"{p}_{r}" for p in ("fwdc_tex", "fwdc_trans", "fwdc_blank",
                              "fwdplainc_tex", "fwdplainc_trans", "fwdplainc_blank")
        for r in ("r1", "r2", "r3")]

JOBS_LOG = os.path.join(LOG_DIR, "jobs.log")


def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}  {msg}"
    print(line, flush=True)
    with open(JOBS_LOG, "a") as f:
        f.write(line + "\n")


def run_one(name, cmd, env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    log(f"START    {name}")
    t0 = time.time()
    log_path = os.path.join(LOG_DIR, f"{name}.log")
    with open(log_path, "w") as lf:
        r = subprocess.run(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT)
    wall = time.time() - t0
    status = "DONE" if r.returncode == 0 else "FAILED"
    log(f"{status}     {name}  wall={wall:.0f}s  rc={r.returncode}")
    return name, r.returncode, wall


def main():
    commit = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    jobs = []
    for bag in BAGS:
        jobs.append((f"ukf__{bag}__heading5", [
            os.path.expanduser("~/venv-evo/bin/python"), os.path.join(REPO, "src/estimators/ukf_replay.py"),
            bag, "heading"
        ], {"UKF_OUT_ROOT": UKF_OUT_ROOT, "UKF_BAG_ROOT": BAG_ROOT, "FWD_SIGMA_PSI_DEG": "5"}))
        jobs.append((f"fgo__{bag}__heading5", [
            os.path.expanduser("~/venv-fgo/bin/python"), os.path.join(REPO, "src/estimators/fgo/fgo_replay.py"),
            bag, "0.25", "2", "heading"
        ], {"FGO_OUT_ROOT": FGO_OUT_ROOT, "FGO_BAG_ROOT": BAG_ROOT, "FWD_SIGMA_PSI_DEG": "5"}))

    log(f"BEGIN    jobs=run_ekf3_heading_arms_iii_iv n_jobs={len(jobs)} parallel=4 commit={commit}")
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(run_one, name, cmd, env_extra): name for name, cmd, env_extra in jobs}
        for fut in as_completed(futs):
            results.append(fut.result())
    n_fail = sum(1 for _, rc, _ in results if rc != 0)
    log(f"END      n_jobs={len(jobs)} n_fail={n_fail}")
    summary_path = os.path.join(LOG_DIR, "summary.json")
    json.dump({"n_jobs": len(jobs), "n_fail": n_fail, "commit": commit,
               "results": [{"name": n, "rc": rc, "wall_s": w} for n, rc, w in results]},
              open(summary_path, "w"), indent=1)
    print(f"[out] {summary_path}")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
