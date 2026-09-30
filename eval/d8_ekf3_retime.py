#!/usr/bin/env python3
"""D8 DIAGNOSTIC (ruling 2026-09-30; never replaces the dataset results): EKF3's own cost from fusing
our flow at a misdated time. EKF3 stamps flow at arrival - EK3_FLOW_DELAY - flowTimeDeltaAvg/2 (100/2,
hard-coded) - 6 ms (AP_NavEKF3_Measurements.cpp:232-236), which puts our 30 Hz flow 31-44 ms BEFORE
capture. The diagnostic Replay (~/ardupilot_diag: flowTimeDeltaAvg_ms = 0) with EK3_FLOW_DELAY =
round(capture->EKF3 latency - 6) re-times each flow to its capture time.
Per trial: stock-EKF3 Replay (baseline; must reproduce the dataset's EKF3 score) and re-timed Replay,
each scored exactly as eval/three_way_eval.py scores EKF3 (XKF1 core 0 vs SIM, pinned cruise window,
evo -a). Usage (venv-evo + pymavlink shim): python3 eval/d8_ekf3_retime.py TRIAL OUTDIR"""
import glob, json, math, os, subprocess, sys
import numpy as np
from pymavlink import mavutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import three_way_eval as T

trial, outdir = sys.argv[1], sys.argv[2]
TD = os.path.expanduser(f"~/thesis_data/trials/{trial}")
_it = {}
for _f in ("input_timing_dsn_extra.json", "input_timing_rerun_all.json"):   # the dsn_extra bags (r4-r10) have their own file
    _it.update(json.load(open(os.path.join(HERE, "results", _f))))
lat = _it[trial]["flow_to_ekf3"]["lat_median_ms"]            # None on blank: no flow frame was fused, nothing to re-time
fd = None if lat is None else max(0, int(round(lat - 6)))
# ONE diagnostic Replay binary (EKF3 only, no shadow UKF): stock flow timing when D8_FLOW_DT_AVG_MS is unset
# (the baseline, which must reproduce the dataset's EKF3 score), re-timed with it = 0 plus EK3_FLOW_DELAY
EXE = os.path.expanduser("~/ardupilot_diag/build/sitl/tool/Replay")
REPLAY = {"baseline": ({}, []),
          "retimed": ({"D8_FLOW_DT_AVG_MS": "0"}, [] if fd is None else ["--parm", f"EK3_FLOW_DELAY={fd}"])}


def replay(name):
    d = os.path.join(outdir, trial, name); os.makedirs(d, exist_ok=True)
    env_extra, extra = REPLAY[name]
    env = {k: v for k, v in os.environ.items() if k != "D8_FLOW_DT_AVG_MS"}; env.update(env_extra)
    r = subprocess.run(["timeout", "1500", "nice", "-n", "10", EXE, *extra, f"{TD}/ardupilot.bin"], cwd=d, env=env,
                       stdout=open(f"{d}/replay.log", "w"), stderr=subprocess.STDOUT)
    if r.returncode != 0 or "PANIC" in open(f"{d}/replay.log").read():
        raise SystemExit(f"{trial} {name}: Replay failed (rc {r.returncode}); see {d}/replay.log")
    logs = sorted(glob.glob(f"{d}/logs/*.BIN"), key=os.path.getmtime)
    return logs[-1]


def score(binpath, sim):
    m = mavutil.mavlink_connection(binpath); xk = []
    while True:
        x = m.recv_match(type=["XKF1"])
        if x is None:
            break
        if getattr(x, "C", 0) == 100:          # Replay logs the REPLAYED EKF3 as core 100 (+100); cores 0/1 are the input log's
            xk.append((x.TimeUS / 1e6, x.PN, x.PE, x.PD))
    xk = np.array(xk)
    t0, t1 = T.cruise_window(trial)
    ref = T.crop(sim, t0, t1); est = T.crop(np.c_[xk[:, 0], xk[:, 1:4], np.tile([0., 0., 0., 1.], (len(xk), 1))], t0, t1)
    d = os.path.join(outdir, trial); rp, ep = f"{d}/_ref.tum", f"{d}/_est.tum"
    T.write_tum(rp, ref); T.write_tum(ep, est)
    return T.evo_ape_a(rp, ep)


T.ekf3_tums(trial)                                     # the dataset's own SIM-based reference (idempotent)
sim = np.loadtxt(f"{TD}/ekf3/ground_truth.tum")
res = {"trial": trial, "latency_median_ms": lat, "EK3_FLOW_DELAY_retimed": fd,
       "dataset_ekf3_evo": None}
for n in ("baseline", "retimed"):
    res[n] = score(replay(n), sim)
ds = {**json.load(open(os.path.join(HERE, "results", "rerun_dsn_evo.json")))["trials"]}
for f in ("dsn_extra_evo", "rerun_fwdc_evo", "rerun_fwdplainc_evo"):
    p = os.path.join(HERE, "results", f + ".json")
    if os.path.exists(p):
        ds.update(json.load(open(p))["trials"])
if trial in ds:
    res["dataset_ekf3_evo"] = ds[trial]["est"]["EKF3"]["ate_a_cruise"]["+0.00"]
res["cost_m"] = None if (res["retimed"] is None or res["baseline"] is None) else res["baseline"] - res["retimed"]
json.dump(res, open(os.path.join(outdir, trial, "d8.json"), "w"), indent=1)
print(json.dumps(res))
