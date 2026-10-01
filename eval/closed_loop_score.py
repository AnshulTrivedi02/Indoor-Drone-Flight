#!/usr/bin/env python3
"""Score a closed-loop flight against its PRE-REGISTERED criteria (METHODOLOGY "Part 2 — revised
pre-registration at the ruled 5.00 deg EKF3 yaw sigma" and "Part 2 — evaluation windows for every
band"). Windows exactly as recorded there:
  cruise   = the PINNED window (eval/cruise_window.cruise_bounds on GT), end-wall approach included
  (a)      = contact time from the pinned t0; PRIMARY: no contact before +100 s; any contact on the
             WEST wall (GT x <= -9.58) inside [+155, +215] s
  B1       = whole flight: completed mission (fly_trial "Trial flight complete" + landed), no
             watcher BREACH, |GT x| < 9.58 m throughout
  B2       = max |GT x| in cruise <= 6.0 m
  B3       = EKF3 yaw error (XKF1.Yaw - SIM.Yaw, dataflash) in cruise: p95 <= 1.0 deg, max <= 2.0 deg;
             y <= 140 m and y > 140 m reported as DIAGNOSTIC
  B4       = 1 s-smoothed |GT lateral speed| in cruise <= 0.25 m/s
  B5       = gyro rms (/imu/data_raw) roll <= 0.05, pitch <= 0.0108, yaw <= 0.02 rad/s over
             eval/rgs_profile.py's span (51-sample-smoothed GT forward speed > 0.3, trimmed 5 s)
The SITL dataflash clock is mapped to the bag's sim clock with the /imu/time_ref lower envelope
(as in eval/ground_test_check.py; offset ~ms, 162 ppm).
Usage (evo venv + pymavlink shim): python3 eval/closed_loop_score.py TRIAL --set a|b [--json OUT]"""
import argparse, json, os, sys
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--set", required=True, choices=["a", "b"])
# --est ukf (D17 V4, PRE-REGISTERED): B3 uses the UKF's current-time yaw (XUKO), the value the controller receives;
# EKF3's yaw error is then a DIAGNOSTIC, and S2 (XUKS horiz_pos_rel and healthy from arming to disarm) is added.
# --est fgo (D19, PRE-REGISTERED "B3 from XFGO, the scorer gets --est fgo"): B3 from the FGO backend's current-time
# yaw (XFGO); S2 = XFGO.OV (output valid) 100% from arming to disarm (the FGO has no horiz_pos_rel flag of its own).
ap.add_argument("--est", default="ekf3", choices=["ekf3", "ukf", "fgo"])
ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); C = os.path.expanduser(f"~/thesis_data/closed_loop/{a.trial}")
WALL = 9.58
ts = get_typestore(Stores.ROS2_JAZZY)
gt, imu, tref = [], [], []
with Reader(f"{D}/bag") as r:
    cs = [c for c in r.connections if c.topic in ("/ground_truth/pose", "/imu/data_raw", "/imu/time_ref")]
    for con, _, raw in r.messages(connections=cs):
        m = ts.deserialize_cdr(raw, con.msgtype); t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if con.topic == "/ground_truth/pose":
            gt.append((t, m.pose.position.x, m.pose.position.y, m.pose.position.z))
        elif con.topic == "/imu/data_raw":
            imu.append((t, m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z))
        else:
            tref.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, t))
gt, imu, tref = np.array(sorted(gt)), np.array(sorted(imu)), np.array(sorted(tref))
t, x, y = gt[:, 0], gt[:, 1], gt[:, 2]
c0, c1 = cruise_bounds(t, x, y)
w = (t >= c0) & (t <= c1)
out = {"trial": a.trial, "set": a.set, "cruise_s": [float(c0), float(c1)], "cruise_len_s": float(c1 - c0)}

# SITL -> sim clock (lower envelope of receipt - time_usec, 5 s bins)
sitl, recv = tref[:, 0], tref[:, 1]; dd = recv - sitl; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    q = (sitl >= lo) & (sitl < lo + 5)
    if q.sum() > 50:
        i = np.argmin(dd[q]); env.append((sitl[q][i], dd[q][i]))
env = np.array(env); kk, cc = np.polyfit(env[:, 0], env[:, 1], 1)
to_sim = lambda s: s + kk * s + cc
out["clock_map"] = {"offset_ms_start": float(1e3 * (kk * env[0, 0] + cc)), "rate_ppm": float(1e6 * kk)}

# contact: first |x| >= WALL anywhere in the flight
hit = np.where(np.abs(x) >= WALL)[0]
contact = None if not len(hit) else {"t_rel_cruise_s": float(t[hit[0]] - c0), "x": float(x[hit[0]]), "y": float(y[hit[0]]),
                                     "wall": "west" if x[hit[0]] < 0 else "east"}
out["contact"] = contact
fly = open(f"{D}/logs/fly_trial.log").read() if os.path.exists(f"{D}/logs/fly_trial.log") else ""
breach = open(f"{C}/BREACH.txt").read().strip() if os.path.exists(f"{C}/BREACH.txt") else None
out["completed"] = "Trial flight complete" in fly and "landed" in fly
out["watcher_breach"] = breach

if a.set == "a":
    pa = {"no_contact_before_100s": contact is None or contact["t_rel_cruise_s"] >= 100,
          "contact_if_any_west_in_155_215": contact is None or (contact["wall"] == "west" and 155 <= contact["t_rel_cruise_s"] <= 215)}
    pa["pass"] = all(pa.values()); out["a_primary"] = pa
else:
    B = {}
    B["B1"] = {"completed": out["completed"], "no_breach": breach is None, "max_abs_x_flight": float(np.abs(x).max())}
    B["B1"]["pass"] = bool(out["completed"] and breach is None and np.abs(x).max() < WALL)
    B["B2"] = {"max_abs_x_cruise_m": float(np.abs(x[w]).max())}; B["B2"]["pass"] = B["B2"]["max_abs_x_cruise_m"] <= 6.0
    # B3: yaw error from the dataflash (the flying estimator's yaw; --est)
    mm = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); ser = {"ekf3": [], "ukf": [], "fgo": []}; sim, st, arm, fov = [], [], [], []
    while True:
        rr = mm.recv_match(type=["XKF1", "SIM", "XUKO", "XUKS", "ARM", "XFGO"])
        if rr is None:
            break
        ty = rr.get_type()
        if ty == "SIM":
            sim.append((rr.TimeUS / 1e6, rr.Yaw))
        elif ty == "XKF1" and rr.C == 0:
            ser["ekf3"].append((rr.TimeUS / 1e6, rr.Yaw))
        elif ty == "XUKO":
            ser["ukf"].append((rr.TimeUS / 1e6, rr.Yaw))
        elif ty == "XFGO":
            ser["fgo"].append((rr.TimeUS / 1e6, rr.Yaw)); fov.append((rr.TimeUS / 1e6, int(rr.OV)))
        elif ty == "XUKS":
            st.append((rr.TimeUS / 1e6, (int(rr.SS) >> 3) & 1, int(rr.H)))
        elif ty == "ARM":
            arm.append((rr.TimeUS / 1e6, rr.ArmState))
    sim = np.array(sim)

    def b3(ek):
        ek = np.array(ek)
        te = to_sim(ek[:, 0]); simy = np.interp(ek[:, 0], sim[:, 0], np.unwrap(np.radians(sim[:, 1])))
        err = np.degrees((np.radians(ek[:, 1]) - simy + np.pi) % (2 * np.pi) - np.pi)
        we = (te >= c0) & (te <= c1); ye = np.interp(te, t, y)
        ae = np.abs(err[we])
        r = {"p95_deg": float(np.percentile(ae, 95)), "max_deg": float(ae.max()), "mean_deg": float(err[we].mean()),
             "diag_y_le_140": {"p95": float(np.percentile(np.abs(err[we & (ye <= 140)]), 95)), "max": float(np.abs(err[we & (ye <= 140)]).max())},
             "diag_y_gt_140": ({"p95": float(np.percentile(np.abs(err[we & (ye > 140)]), 95)), "max": float(np.abs(err[we & (ye > 140)]).max())}
                               if (we & (ye > 140)).any() else None)}
        r["pass"] = r["p95_deg"] <= 1.0 and r["max_deg"] <= 2.0
        return r
    B["B3"] = b3(ser[a.est]); B["B3"]["estimator"] = a.est
    for other in [e for e in ("ekf3", "ukf", "fgo") if e != a.est and len(ser[e])]:
        out.setdefault("diag_B3_other_estimator", {})[other] = b3(ser[other])
    if a.est == "ukf":
        st = np.array(st); arms = [tt for tt, s_ in arm if s_ == 1]; dis = [tt for tt, s_ in arm if s_ == 0 and arms and tt > arms[0]]
        ws = (st[:, 0] >= arms[0]) & (st[:, 0] <= (dis[0] if dis else st[-1, 0]))
        out["S2"] = {"horiz_pos_rel_pct": float(100 * st[ws, 1].mean()), "healthy_pct": float(100 * st[ws, 2].mean())}
        out["S2"]["pass"] = out["S2"]["horiz_pos_rel_pct"] == 100.0 and out["S2"]["healthy_pct"] == 100.0
    if a.est == "fgo":
        fv = np.array(fov); arms = [tt for tt, s_ in arm if s_ == 1]; dis = [tt for tt, s_ in arm if s_ == 0 and arms and tt > arms[0]]
        ws = (fv[:, 0] >= arms[0]) & (fv[:, 0] <= (dis[0] if dis else fv[-1, 0]))
        out["S2"] = {"fgo_output_valid_pct": float(100 * fv[ws, 1].mean())}
        out["S2"]["pass"] = out["S2"]["fgo_output_valid_pct"] == 100.0
    # "1 s-smoothed": a 1 s TIME window. GT stamps are irregular (occasional samples 1 ms apart), so
    # x is resampled on a uniform 100 Hz grid, boxcar-smoothed over 1 s (100 samples), then
    # differentiated. (The first version used a sample-count boxcar + np.gradient on the raw stamps,
    # which a 1 ms stamp gap amplified ~16x: 0.333 m/s on cl_b_tex_r1 against 0.033 m/s. METHODOLOGY.)
    tg = np.arange(c0, c1, 0.01); xg = np.interp(tg, t, x)
    xs = np.convolve(xg, np.ones(100) / 100, "valid"); tv = tg[50:50 + len(xs)]
    vx = np.gradient(xs, 0.01)
    B["B4"] = {"max_abs_lat_speed_mps": float(np.abs(vx).max()), "rms_mps": float(np.sqrt(np.mean(vx ** 2))),
               "t_rel_cruise_of_max_s": float(tv[np.argmax(np.abs(vx))] - c0)}
    B["B4"]["pass"] = B["B4"]["max_abs_lat_speed_mps"] <= 0.25
    vy = np.convolve(np.gradient(y, t), np.ones(51) / 51, "same"); tc = t[vy > 0.3]; r0, r1 = tc[0], tc[-1]
    sel = (imu[:, 0] > r0 + 5) & (imu[:, 0] < r1 - 5)
    g = {nm: float(imu[sel, ax].std()) for ax, nm in ((1, "roll"), (2, "pitch"), (3, "yaw"))}
    B["B5"] = {"gyro_rms": g, "pass": g["roll"] <= 0.05 and g["pitch"] <= 0.0108 and g["yaw"] <= 0.02}
    B["pass"] = all(B[b]["pass"] for b in ("B1", "B2", "B3", "B4", "B5"))
    out["B"] = B
    # DIAGNOSTIC: heading acceptance in cruise (VISP rows vs node-sent quality >= 50)
    import csv
    hb = f"{D}/logs/heading_bridge.csv"
    if os.path.exists(hb):
        rows = [q for q in csv.DictReader(open(hb)) if q["sent"] == "1" and c0 <= float(q["t_capture"]) <= c1]
        mm = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); vis = 0; ign = 0
        while True:
            rr = mm.recv_match(type=["VISP"])
            if rr is None:
                break
            if c0 <= rr.RTimeUS / 1e6 <= c1:
                vis += 1; ign += int(rr.Ign)
        out["diag_heading"] = {"sent_cruise": len(rows), "sent_q_ge_50": sum(int(q["quality"]) >= 50 for q in rows),
                               "VISP_cruise": vis, "VISP_ignored": ign}
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
