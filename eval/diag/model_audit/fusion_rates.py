"""Model audit (2026-10-09), DIAGNOSTIC: effective fusion RATE of flow and range per estimator (item 2).

EKF3 (source, pinned 7bac20cbcc):
  flow  writeOptFlowMeas returns early when (imuSampleTime_ms - flowMeaTime_ms) < sensorIntervalMin_ms = 50
        (AP_NavEKF3_Measurements.cpp:178, AP_NavEKF3.h:516). Simulated here on the dataflash OF record times (the
        AP_OpticalFlow update that calls writeOptFlowMeas), quantised to whole ms as imuSampleTime_ms.
  range readRangeFinder samples when (imuSampleTime_ms - lastRngMeasTime_ms) > 50 (Measurements.cpp:32); it runs once
        per 12.5 ms prediction (UpdateFilter -> SelectVelPosFusion -> readRangeFinder, PosVelFusion.cpp:1267), so a
        sample every 62.5 ms (5 predictions), each the median of the last 3 samples, fused once.
UKF offline / FGO: every bag flow and range message (ukf_replay.py one update per message; the FGO one factor per
keyframe at 30 Hz). UKF port: every writeOptFlowMeas fan-out, and range sampled every update() (the D18 30 Hz rule).
Usage (~/venv-ardupilot): python3 fusion_rates.py ARDUPILOT.BIN WINDOW.npz T_CRUISE0 T_CRUISE1   (bag clock, s)"""
import sys
import numpy as np
from pymavlink import DFReader

binf, win, c0, c1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
w = np.load(win)
tf, tr = w["t_flow"], w["t_rng"]
f = DFReader.DFReader_binary(binf)
of = []
while True:
    m = f.recv_match(type=["OF"])
    if m is None:
        break
    of.append(m.TimeUS * 1e-6)
of = np.array(of)
# the dataflash clock is ~0 offset from the bag clock to within ~60 ms (CLAUDE.md); the window is long, so use it as is
sel = (of >= c0) & (of <= c1)
ms = np.floor(of[sel] * 1000.0).astype(np.int64)
acc, last = 0, -10**9
for t in ms:
    if t - last >= 50:
        acc += 1; last = t
dur = c1 - c0
bf = ((tf >= c0) & (tf <= c1)).sum(); br = ((tr >= c0) & (tr <= c1)).sum()
# EKF3 range: one sample per 5 predictions of 12.5 ms
ekf_rng = dur / 0.0625
out = {"window_s": [c0, c1],
       "flow_arrivals_bag_hz": bf / dur, "flow_OF_records_hz": sel.sum() / dur,
       "ekf3_flow_accepted_hz": acc / dur, "ekf3_flow_accept_fraction": acc / max(sel.sum(), 1),
       "range_arrivals_bag_hz": br / dur, "ekf3_range_fused_hz_derived": ekf_rng / dur,
       "OF_interval_ms_median": float(np.median(np.diff(of[sel])) * 1e3)}
for k, v in out.items():
    print(f"{k}: {v}")
import json
json.dump(out, open(win.replace(".npz", "_rates.json"), "w"), indent=1)
