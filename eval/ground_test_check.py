#!/usr/bin/env python3
"""Closed-loop Part 1 SITL ground test: criteria G1-G5 (METHODOLOGY "SITL ground test", fixed
before the test). Reads the trial's dataflash log (PARM, MSG, VISP, REPH, XKF1, XKF4, XKF5, ARM/EV),
the heading node CSV, and the bag's /imu/time_ref for the SITL<->Gazebo clock map.

Clock map (deviation, stated): the pre-registered G4(b) map is eval/input_timing.clock_map, which
fits the SITL/Gazebo offset from vehicle MOTION (SIM vs GT cross-correlation). A ground test has
no motion, so it cannot be used. Instead: /imu/time_ref pairs every HIGHRES_IMU time_usec (SITL
clock) with its ROS receipt stamp (Gazebo sim clock). recv - sitl = offset(t) + transport lag
(>= 0), so a linear fit to the lower envelope (per-5 s-bin minima) gives offset(t) as an UPPER
bound on the true offset by the minimum transport lag (loopback UDP, expected < 1 ms sim).
Usage (venv-ardupilot: numpy + pymavlink + rosbags): python3 eval/ground_test_check.py TRIAL [--json OUT]"""
import argparse, json, math, os
import numpy as np
from pymavlink import mavutil

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
P = ("EK3_SRC1_POSXY", "EK3_SRC1_YAW", "VISO_TYPE", "VISO_DELAY_MS", "VISO_YAW_M_NSE", "VISO_QUAL_MIN",
     "EK3_HGT_DELAY", "EK3_FLOW_DELAY", "AHRS_EKF_TYPE", "LOG_REPLAY", "EK3_SRC1_VELXY", "EK3_SRC1_POSZ")
par, msgs, visp, reph, x1, x4, x5, arm = {}, [], [], [], [], [], [], []
m = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
while True:
    r = m.recv_match(type=["PARM", "MSG", "VISP", "REPH", "XKF1", "XKF4", "XKF5", "ARM", "EV"])
    if r is None:
        break
    t = r.get_type()
    if t == "PARM":
        if r.Name in P:
            par[r.Name] = r.Value
    elif t == "MSG":
        msgs.append((r.TimeUS / 1e6, r.Message))
    elif t == "VISP":
        visp.append((r.TimeUS, r.RTimeUS, r.CTimeMS, r.PX, r.PY, r.Y, r.AErr, r.Ign, r.Q))
    elif t == "REPH":
        reph.append((r.TS, r.D, r.AEr, r.PX, r.PY))
    elif t in ("XKF1", "XKF4", "XKF5"):
        if r.C != 0:
            continue
        if t == "XKF1":
            x1.append((r.TimeUS / 1e6, r.PN, r.PE, r.Yaw))
        elif t == "XKF4":
            x4.append((r.TimeUS / 1e6, int(r.SS)))
        else:
            x5.append((r.TimeUS / 1e6, r.FIX, r.FIY))
    elif t == "ARM":
        arm.append((r.TimeUS / 1e6, int(r.ArmState)))
visp, reph, x1, x4, x5 = (np.array(v, dtype=float) if len(v) else np.zeros((0, 9)) for v in (visp, reph, x1, x4, x5))
out = {"params": par, "n": {"VISP": len(visp), "REPH": len(reph), "XKF5": len(x5)}}

# --- arming / disarm times ---
t_arm = next((t for t, s in arm if s == 1), None); t_dis = next((t for t, s in arm if s == 0 and t_arm and t > t_arm), None)
out["arm_s"], out["disarm_s"] = t_arm, t_dis

# --- G1: yaw-only ExtNav fusion ---
ek_msgs = [(round(t, 2), s) for t, s in msgs if "EKF3" in s or "ExtNav" in s or "VisOdom" in s or "yaw" in s.lower()]
pn_pe_max = float(np.abs(x1[:, 1:3]).max()) if len(x1) else None
g1 = {"ekf_msgs": ek_msgs[:20], "REPH_n": len(reph),
      "REPH_AEr_unique": sorted(set(np.round(reph[:, 2], 5).tolist())) if len(reph) else [],
      "XKF1_max_abs_PN_PE_m": pn_pe_max, "POSXY": par.get("EK3_SRC1_POSXY")}
g1["pass"] = bool(len(reph) > 0 and g1["REPH_AEr_unique"] == [0.05] and pn_pe_max is not None and pn_pe_max < 5.0
                  and par.get("EK3_SRC1_POSXY") == 0 and any("yaw aligned" in s.lower() or "external nav" in s.lower() for _, s in ek_msgs))
out["G1"] = g1

# --- node CSV ---
import csv
rows = list(csv.DictReader(open(f"{D}/logs/heading_bridge.csv")))
sent = [r for r in rows if r["sent"] == "1"]
off_rows = [r for r in rows if r["offset_rad"] != ""]
first_off = next((float(r["t_capture"]) for r in off_rows), None)
out["node"] = {"rows": len(rows), "sent": len(sent), "offset_rad": float(off_rows[-1]["offset_rad"]) if off_rows else None,
               "offset_locked_at_capture_s": first_off,
               "armed_flag_at_first_offset": int(off_rows[0]["armed"]) if off_rows else None}

# --- G2 / G3 ---
arm_fail = [(round(t, 2), s) for t, s in msgs if "PreArm" in s or "Arm:" in s]
out["G2"] = {"armed": t_arm is not None, "prearm_or_arm_failures": arm_fail[:10],
             "offset_locked_before_arm": bool(off_rows and int(off_rows[0]["armed"]) == 0)}
out["G2"]["pass"] = bool(out["G2"]["armed"] and out["G2"]["offset_locked_before_arm"]
                         and not any("Vis" in s or "EKF" in s for _, s in arm_fail))
origin_msgs = [(round(t, 2), s) for t, s in msgs if "origin" in s.lower()]
out["G3"] = {"origin_msgs": origin_msgs, "pass": bool(g1["pass"] and out["G2"]["pass"])}

# --- clock map from /imu/time_ref (see docstring) ---
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ts = get_typestore(Stores.ROS2_JAZZY); pr = []
with Reader(f"{D}/bag") as rd:
    cs = [c for c in rd.connections if c.topic == "/imu/time_ref"]
    for con, _, raw in rd.messages(connections=cs):
        mm = ts.deserialize_cdr(raw, con.msgtype)
        pr.append((mm.time_ref.sec + mm.time_ref.nanosec * 1e-9, mm.header.stamp.sec + mm.header.stamp.nanosec * 1e-9))
pr = np.array(pr); sitl, recv = pr[:, 0], pr[:, 1]; d = recv - sitl
bins = np.arange(sitl.min(), sitl.max() + 5, 5.0); env = []
for lo in bins[:-1]:
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); k, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_sim = lambda t_sitl: t_sitl + (k * t_sitl + c0)
out["clock_map"] = {"source": "/imu/time_ref lower envelope", "offset_s_at_start": float(k * env[0, 0] + c0),
                    "rate_ppm": float(k * 1e6), "envelope_resid_ms_max": float(1e3 * np.abs(env[:, 1] - (k * env[:, 0] + c0)).max()),
                    "n_bins": len(env)}

# --- G4: latency (a) node, (b) VISP ---
lat_a = np.array([1e3 * (float(r["t_sim_sent"]) - float(r["t_capture"])) for r in sent])
# (b) receipt on the SITL clock mapped to sim, minus capture (RTimeUS is the capture time we sent, sim clock)
lat_b = 1e3 * (to_sim(visp[:, 0] / 1e6) - visp[:, 1] / 1e6) if len(visp) else np.array([])
def st(x):
    return None if not len(x) else {"min": float(x.min()), "p5": float(np.percentile(x, 5)), "median": float(np.median(x)),
                                     "p95": float(np.percentile(x, 95)), "max": float(x.max()), "n": int(len(x))}
out["G4"] = {"a_node_sent_minus_capture_ms": st(lat_a), "b_visp_receipt_minus_capture_ms": st(lat_b)}
if len(lat_a) and len(lat_b):
    agree = abs(lat_a.min() - lat_b.min()) <= 5.0
    rec = int(round(lat_b.min()))
    horizon = max(par.get("EK3_HGT_DELAY", 60), par.get("EK3_FLOW_DELAY", 10))
    out["G4"].update({"min_agree_within_5ms": bool(agree), "VISO_DELAY_MS_recommended": rec,
                      "horizon_other_sensors_ms": horizon, "pass": bool(agree and rec <= horizon)})

# --- G5 (RE-WORDED before run 2; METHODOLOGY "Rulings ... G5 re-worded BEFORE run 2") ---
if len(reph) and len(visp):
    dl = float(par.get("VISO_DELAY_MS"))
    hz = max(par.get("EK3_HGT_DELAY", 60), par.get("EK3_FLOW_DELAY", 10), dl)
    n = min(len(reph), len(visp))
    g51 = {"REPH_D_unique": sorted(set(reph[:, 1].astype(int).tolist())), "VISO_DELAY_MS": dl, "horizon_ms": hz,
           "XKF5_rows_while_ExtNav": int(((x5[:, 0] >= visp[0, 0] / 1e6) & (x5[:, 0] <= visp[-1, 0] / 1e6)).sum()) if len(x5) else 0,
           "count_match": len(reph) == len(visp)}
    g51["pass"] = bool(g51["REPH_D_unique"] == [int(dl)] and hz >= dl and g51["XKF5_rows_while_ExtNav"] > 0)
    # effective fusion time (SITL ms): MAX(TS - D - 6, receipt - horizon)  [AP_NavEKF3_Measurements.cpp:1101-1105]
    ts_ms, recv_ms = reph[:n, 0], visp[:n, 0] / 1e3
    fuse = np.maximum(ts_ms - reph[:n, 1] - 6.0, recv_ms - hz)
    cap_sitl_ms = 1e3 * (visp[:n, 1] / 1e6 - c0) / (1 + k)
    r = fuse - cap_sitl_ms
    p95 = float(np.percentile(r, 95))
    g52 = {"residual_ms": st(r), "clamped_to_horizon_pct": float(100 * np.mean(ts_ms - reph[:n, 1] - 6.0 < recv_ms - hz)),
           "misalign_deg_at_0.93dps_p95": p95 * 1e-3 * 0.93, "misalign_deg_at_GT_p99_0.09dps_p95": p95 * 1e-3 * 0.09}
    g52["pass"] = bool(g52["misalign_deg_at_0.93dps_p95"] <= 0.25)
    # G5.3 latency stability: sent - capture per processed frame, armed period (arm + 5 s .. disarm)
    tc = np.array([float(r_["t_capture"]) for r_ in sent]); la = np.array([1e3 * (float(r_["t_sim_sent"]) - float(r_["t_capture"])) for r_ in sent])
    ks = np.array([int(r_["k"]) for r_ in rows])
    # arm/disarm are on the SITL clock; capture is on the sim clock (offset ~ms, negligible for a 330 s window)
    lo = (t_arm or 0) + 5; hi = t_dis or tc.max()
    w = (tc >= lo) & (tc <= hi)
    slope = float(np.polyfit(tc[w], la[w], 1)[0]) if w.sum() > 10 else None
    blocks = [float(np.median(la[w & (tc >= b0) & (tc < b0 + 30)])) for b0 in np.arange(lo, hi, 30) if (w & (tc >= b0) & (tc < b0 + 30)).sum() > 5]
    dk = np.diff(ks); step = int(np.median(dk)); drops = int(((dk - step) // step)[dk > step].sum())
    g53 = {"armed_window_s": [lo, hi], "slope_ms_per_s": slope, "block30_medians_ms": [round(x, 1) for x in blocks],
           "dropped_selected": drops, "processed": int(len(ks)), "drop_pct": 100 * drops / (drops + len(ks))}
    g53["pass"] = bool(slope is not None and abs(slope) <= 0.1 and blocks and max(blocks) <= 200 and g53["drop_pct"] <= 5)
    out["G5"] = {"G5.1": g51, "G5.2": g52, "G5.3": g53, "pass": bool(g51["pass"] and g52["pass"] and g53["pass"])}
print(json.dumps(out, indent=1, default=str))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1, default=str)
