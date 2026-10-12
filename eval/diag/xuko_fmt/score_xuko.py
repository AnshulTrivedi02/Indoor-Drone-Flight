#!/usr/bin/env python3
"""XUKO verification (b), 2026-10-12: the rung-1 scorer (eval/real_score.py) on a Replay output log of a SITL flight,
with the SITL truth standing in for mocap. A PLUMBING test, not a result.

  score_xuko.py <replay output .BIN> <work dir> <out.json>

* "mocap" = the log's own SIM2 position (PN/PE/PD, on the FC clock TimeUS, so no clock map is needed) and SIM yaw,
  decimated to 100 Hz, written as TUM (ENU, z up).
* The pre-registration = the SIGNED-OFF docs/rung1_preregistration.json with ONLY the `clock_map` section removed (no
  mocap_align on SITL truth; the section is optional in the schema). Its sha256 and the one change are recorded.
* Scored from the log: EKF3=XKF1@100, EKF3_onboard=XKF1@0, UKF=XUKO, UKF_horizon=XUKF (the registered records).
Run with ~/venv-ardupilot (evo is called by real_score as in three_way_eval).
"""
import copy, hashlib, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, EVAL)
from df_reader import read_records  # noqa: E402
import real_score as RS  # noqa: E402

binp, work, out = sys.argv[1:4]
os.makedirs(work, exist_ok=True)
recs, info = read_records(binp, ["SIM2", "SIM"])
s2 = recs["SIM2"]; s1 = recs["SIM"]
t2 = np.array([r["TimeUS"] for r in s2]) / 1e6
keep = np.r_[True, np.diff(np.floor(t2 * 100)) > 0]                       # 100 Hz
t = t2[keep]
pn = np.array([r["PN"] for r in s2])[keep]; pe = np.array([r["PE"] for r in s2])[keep]
pd = np.array([r["PD"] for r in s2])[keep]
t1 = np.array([r["TimeUS"] for r in s1]) / 1e6
yaw_ned = np.unwrap(np.radians([r["Yaw"] for r in s1]))
yaw_enu = math.pi / 2 - np.interp(t, t1, yaw_ned)
q = np.c_[np.zeros_like(t), np.zeros_like(t), np.sin(yaw_enu / 2), np.cos(yaw_enu / 2)]
mo = np.c_[t, pe, pn, -pd, q]
mo_path = os.path.join(work, "sim_truth_fc_clock.tum"); np.savetxt(mo_path, mo, fmt="%.6f")

src = os.path.join(EVAL, "..", "docs", "rung1_preregistration.json")
raw = open(src, "rb").read(); pre = json.loads(raw); pre2 = copy.deepcopy(pre); del pre2["clock_map"]
pre_path = os.path.join(work, "prereg_no_clockmap.json"); json.dump(pre2, open(pre_path, "w"), indent=1)
r = RS.main(["--prereg", pre_path, "--mocap", mo_path, "--bin", binp,
             "--est-bin", "EKF3=XKF1@100", "--est-bin", "EKF3_onboard=XKF1@0", "--est-bin", "UKF=XUKO",
             "--est-bin", "UKF_horizon=XUKF", "--work-dir", os.path.join(work, "rs"), "--out", out])
r["xuko_test"] = {"truth": "SIM2 PN/PE/PD + SIM Yaw from the same log, FC clock, 100 Hz",
                  "prereg_source": "docs/rung1_preregistration.json", "prereg_source_sha256": hashlib.sha256(raw).hexdigest(),
                  "prereg_change": "clock_map section removed (SITL truth is on the FC clock); nothing else"}
json.dump(r, open(out, "w"), indent=1, default=str)
print(json.dumps({k: {m: (v.get("evo_ape_a_se3", {}) or {}).get("rmse_m") for m, v in [("evo", v)]}
                  for k, v in r["estimators"].items()}, indent=1, default=str))
