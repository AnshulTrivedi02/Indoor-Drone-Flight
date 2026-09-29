#!/usr/bin/env python3
"""Offline test of the live heading bridge (closed-loop Part 1) on a recorded fwdc bag.

Drives src/forward_camera/heading_bridge_core.HeadingCore — the code the ROS node runs — over
every /forward_camera/image frame of a bag, in stream order (k = frame index), and checks:
  1. MATCH: psi and support equal Phase 3's stored meas_frozen.npz for every frame (the node
     would send exactly the Phase 3 heading), and validity (support >= S_MIN) likewise.
  2. TIMING: per-frame processing time (single-threaded, cv2.setNumThreads(1)); the every-Nth
     choice N = ceil(p95 / frame interval at the lowest dataset RTF), and the processing part
     of the latency.
  3. FRAME CONVENTION (test only; truth is never used by the node): with the offset set from
     the first N_OFFSET valid on-ground headings against the dataflash SIM yaw (NED), the
     yaw the node would send, offset - psi, is compared with SIM yaw over the cruise; the
     opposite sign is reported alongside to show the check discriminates.
  4. GROUND VALIDITY: fraction of valid headings before take-off (the offset is set there).
Usage (the Phase 3 stack: system OpenCV 4.6 via ~/venv-fwd, pymavlink via the shim):
  PYTHONPATH=~/.cache/thesis_pyshim nice -n 19 ~/venv-fwd/bin/python eval/heading_bridge_offline.py TRIAL_DIR [--json OUT]
"""
import argparse, json, math, os, sys, time
import numpy as np
import cv2
cv2.setNumThreads(1)
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src", "forward_camera"))
from heading_bridge_core import HeadingCore, N_OFFSET, wrap

ap = argparse.ArgumentParser(); ap.add_argument("trial_dir"); ap.add_argument("--json"); ap.add_argument("--max-frames", type=int)
ap.add_argument("--rtf-min", type=float, default=0.72, help="lowest forward-camera dataset RTF (ceiling datasets 0.72-0.77)")
a = ap.parse_args()
fz = json.load(open(os.path.join(HERE, "results", "fwd_calibration.json")))["frozen"]
core = HeadingCore(fz["inlier_deg"], fz["s_min"], 0.148, every_n=1)
ref = np.load(f"{a.trial_dir}/fwd_meas/meas_frozen.npz")
rpsi, rsup, rt = ref["psi"][:, 0], ref["support"][:, 0], ref["t"]
ts = get_typestore(Stores.ROS2_JAZZY)

T, PSI, SUP, VAL, DT = [], [], [], [], []
with Reader(f"{a.trial_dir}/bag") as r:
    conns = [c for c in r.connections if c.topic == "/forward_camera/image"]
    for k, (con, _, raw) in enumerate(r.messages(connections=conns)):
        if a.max_frames and k >= a.max_frames:
            break
        m = ts.deserialize_cdr(raw, con.msgtype)
        img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.step)[:, :m.width].copy()
        psi, sup, valid, dt = core.measure(k, img)
        T.append(m.header.stamp.sec + m.header.stamp.nanosec * 1e-9); PSI.append(np.nan if psi is None else psi)
        SUP.append(sup if psi is not None else np.nan); VAL.append(valid); DT.append(dt)
        if k % 1000 == 0:
            print(f"frame {k}", flush=True)
T, PSI, SUP, VAL, DT = map(np.array, (T, PSI, SUP, VAL, DT))
n = len(T)
out = {"trial": os.path.basename(a.trial_dir), "frames": int(n)}

# 1. match
same_t = np.array_equal(T, rt[:n])
both_nan = np.isnan(PSI) & np.isnan(rpsi[:n])
psi_eq = both_nan | (PSI == rpsi[:n])
sup_eq = (np.isnan(SUP) & np.isnan(rsup[:n])) | (SUP == rsup[:n])
rvalid = np.isfinite(rpsi[:n]) & (np.nan_to_num(rsup[:n]) >= fz["s_min"])
out["match"] = {"stamps_identical": bool(same_t), "psi_identical_frames": int(psi_eq.sum()), "support_identical_frames": int(sup_eq.sum()),
                "valid_identical_frames": int((VAL == rvalid).sum()), "max_abs_psi_diff_deg": float(np.nanmax(np.abs(PSI - rpsi[:n])) if np.any(np.isfinite(PSI - rpsi[:n])) else 0.0),
                "valid_frames": int(VAL.sum()), "pass": bool(same_t and psi_eq.all() and sup_eq.all() and (VAL == rvalid).all())}

# 2. timing
ms = 1e3 * DT; interval_wall_ms = 1e3 / 30.30303 / a.rtf_min
p = lambda q: float(np.percentile(ms, q))
N = max(1, math.ceil(p(95) / interval_wall_ms))
out["timing_ms"] = {"min": float(ms.min()), "p5": p(5), "median": p(50), "p95": p(95), "p99": p(99), "max": float(ms.max()),
                    "frame_interval_wall_ms_at_rtf_min": interval_wall_ms, "every_n": N,
                    "note": "single-threaded, niced, measured WHILE the re-fly batch runs (concurrent load): an upper bound"}

# 3/4. frame convention and ground validity, against dataflash SIM truth (TEST ONLY)
try:
    from pymavlink import mavutil
    mlog = mavutil.mavlink_connection(f"{a.trial_dir}/ardupilot.bin"); s = []
    while True:
        x = mlog.recv_match(type=["SIM"])
        if x is None:
            break
        s.append((x.TimeUS / 1e6, x.Yaw, x.Alt))
    s = np.array(s)
    # map bag sim time to TimeUS: dataflash SIM vs bag GT z is not needed at 10 ms accuracy for a
    # yaw comparison over minutes; use the offset between the first GT-free proxy: SIM Alt rise vs
    # frame index is unavailable, so align by the METHODOLOGY clock map's early offset (-7 ms) = ~0.
    yaw_sim = np.unwrap(np.radians(s[:, 1])); alt = s[:, 2] - s[0, 2]
    tk = T + 0.0
    ysim = np.interp(tk, s[:, 0], yaw_sim); ak = np.interp(tk, s[:, 0], alt)
    ground = ak < 0.1
    out["ground_validity"] = {"frames_on_ground": int(ground.sum()), "valid_on_ground": int((VAL & ground).sum()),
                              "valid_pct_on_ground": float(100 * (VAL & ground).sum() / max(ground.sum(), 1))}
    idx = np.where(VAL & ground)[0][:N_OFFSET]
    res = {}
    for sign in (+1, -1):
        off = math.atan2(np.mean(np.sin(ysim[idx] + sign * np.radians(PSI[idx]))), np.mean(np.cos(ysim[idx] + sign * np.radians(PSI[idx]))))
        air = VAL & (ak > 1.5)
        e = np.degrees(np.array([wrap(off - sign * math.radians(p_) - y) for p_, y in zip(PSI[air], ysim[air])]))
        res["node convention (offset - psi)" if sign == 1 else "opposite sign (offset + psi)"] = {
            "offset_deg": math.degrees(off), "airborne_valid": int(air.sum()), "err_mean_deg": float(e.mean()),
            "err_sd_deg": float(e.std()), "err_abs_p95_deg": float(np.percentile(np.abs(e), 95))}
    out["frame_convention_vs_SIM_truth_TEST_ONLY"] = res
except Exception as ex:
    out["frame_convention_error"] = repr(ex)

print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
