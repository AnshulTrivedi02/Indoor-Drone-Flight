"""R9 end-to-end test on a SITL log, ground truth standing in for mocap, aligned with the EXISTING clock tool
(eval/input_timing.clock_offset: SIM truth vs /ground_truth/pose velocity profiles, early and late window -> offset and
rate), not with mocap_align (R8 is on hold).

Run with ~/venv-evo (rosbags for input_timing; the SIM dump and the scorer run in ~/venv-ardupilot as subprocesses):
  ~/venv-evo/bin/python3 eval/results/r1_scorer/e2e_cl_ukf_clockmap.py TRIAL GT.tum SCRATCH_DIR OUT.json
GT.tum = /ground_truth/pose (t x y z qx qy qz qw, sim clock), extracted from a SCRATCH copy of the packed bag
(eval/results/r1_mocap_sync/extract_gt_timeref.py). The trial directory is only read: the SIM dump goes to SCRATCH_DIR
(input_timing.sim_truth would write ekf3/sim_enu.npy into the trial, so it is NOT called).

Deviation from input_timing.clock_map: its windows (TimeUS 0-70 s and > 290 s) are sized for the 300 s corridor
flights; this flight is ~236 s long, so the late window here is TimeUS > 170 s. The early window is unchanged."""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, EVAL)
import input_timing as IT

trial, gt_path, scratch, out = sys.argv[1:5]
os.makedirs(scratch, exist_ok=True)
binp = os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin")
sim_npy = f"{scratch}/{trial}_sim_enu.npy"
if not os.path.exists(sim_npy):
    subprocess.run([IT.PY_AP, "-c", IT._SIM_DUMP, binp, sim_npy], check=True)
sim = np.load(sim_npy)                                   # TimeUS s, E, N, U
gt = np.loadtxt(gt_path); gt = gt[np.r_[True, np.diff(gt[:, 0]) > 0]]
EARLY, LATE = IT.EARLY_WIN, (170.0, 1e9)
fits = []
for lo, hi in (EARLY, LATE):
    w = sim[(sim[:, 0] >= lo) & (sim[:, 0] <= hi)]
    o, c = IT.clock_offset(w, gt[:, :4])
    fits.append((float(np.mean(w[:, 0])), o, c))
(t1, o1, _), (t2, o2, _) = fits
s = (o2 - o1) / (t2 - t1)                                # offset(t) = TimeUS - sim = o1 + s (t - t1)
to_fc = lambda ts: (ts + o1 - s * t1) / (1 - s)
mo = gt.copy(); mo[:, 0] = to_fc(gt[:, 0])
mo_path = f"{scratch}/{trial}_gt_fc_clock.tum"; np.savetxt(mo_path, mo, fmt="%.6f")
fgo = np.loadtxt(os.path.expanduser(f"~/thesis_data/trials/{trial}/fgo/fgo_traj.tum")); fgo[:, 0] = to_fc(fgo[:, 0])
fgo_path = f"{scratch}/{trial}_fgo_fc_clock.tum"; np.savetxt(fgo_path, fgo, fmt="%.6f")
clock = {"tool": "input_timing.clock_offset (SIM vs GT velocity)", "windows_timeus_s": [list(EARLY), list(LATE)],
         "timeus_minus_sim_early_ms": 1e3 * o1, "timeus_minus_sim_late_ms": 1e3 * o2, "rate_ppm": 1e6 * s,
         "fit_costs": [fits[0][2], fits[1][2]]}
print(json.dumps(clock, indent=1))
# 2026-10-11: the example prereg was replaced by the strict draft (no clock_map check here: GT clock map, not R8).
# Re-running needs a prereg without clock_map and with UKF_fused: "XUKF" in estimator_records.
subprocess.run([IT.PY_AP, os.path.join(EVAL, "real_score.py"), "--prereg", os.path.join(EVAL, "..", "docs", "rung1_preregistration_draft.json"),
                "--mocap", mo_path, "--bin", binp, "--est-bin", "EKF3=XKF1", "--est-bin", "UKF=XUKO",
                "--est-bin", "UKF_fused=XUKF", "--est", f"FGO={fgo_path}", "--work-dir", f"{scratch}/rs_{trial}",
                "--out", out], check=True)
r = json.load(open(out)); r["test_clock_alignment"] = clock
json.dump(r, open(out, "w"), indent=1)
