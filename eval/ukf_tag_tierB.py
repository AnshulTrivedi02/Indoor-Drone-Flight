#!/usr/bin/env python3
"""Experiment H, S2 gate, UKF tier B (docs/h_backends_tag_input.md section 1.2, PRE-REGISTERED): the port on
ArduPilot's own inputs, by Replay of the flight's dataflash log with UKF_EXTPOS=1 UKF_EXTYAW=1.

Reads: the ORIGINAL log's REPH messages (what EKF3 received), the Replay dump ukf_inputs.csv (T accepted fixes,
P queue processing, TP processed fixes, Y pseudo-yaw fusions), the Replay CSV ukf_shadow.csv (horizon state, 25 Hz),
the bag (/imu/time_ref for the SITL -> bag clock map as eval/h_score.py, /tags/sent, /ground_truth/pose), the
offline room_ukf/ukf_live.tum, and logs/fly_trial.log (OCCLUDER ON/OFF).
Checks UB1-UB4 (PASS/FAIL), the UB5 band (tag-visible difference from the offline UKF) and the UB6 prediction (the
port's own loss drift against GT, P-H5 UKF bands); reports the loss-time differences and the fix-time offsets.
Usage (~/venv-tags): python3 eval/ukf_tag_tierB.py TRIAL REPLAY_DIR [--json OUT]"""
import argparse, json, math, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("replay_dir"); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); R = a.replay_dir; TAG = (0.0, 4.998)
wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi
f32 = lambda v: float(np.float32(v))

# ---- original log: REPH in order ----
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); reph = []
while True:
    m = mv.recv_match(type=["REPH"])
    if m is None:
        break
    reph.append((m.PX, m.PY, m.Q1, m.Q2, m.Q3, m.Q4, m.PEr, m.AEr, m.TS, m.D))
reph = np.array(reph, float)

# ---- Replay dump ----
T, P5, TP, Y = [], [], [], []
for ln in open(f"{R}/ukf_inputs.csv"):
    c = ln.rstrip().split(",")
    if c[0] == "T":
        T.append([float(v) for v in c[1:]])            # now, ts, delay, evt, pn, pe, yaw, rp, ry
    elif c[0] == "P" and c[1] == "5":
        P5.append((int(c[2]), int(c[3])))              # event time, processing DAL time
    elif c[0] == "TP":
        TP.append([float(v) for v in c[1:]])           # evt, anchor, x0, x1, x8
    elif c[0] == "Y":
        Y.append(int(c[1]))
T, P5, TP, Y = np.array(T), np.array(P5), np.array(TP), np.array(Y)
out = {"trial": a.trial, "reph": int(len(reph)), "accepted_T": int(len(T)), "processed_P5": int(len(P5)), "processed_TP": int(len(TP))}

# ---- UB1: same input ----
acc, last = [], -10 ** 9
for i, r in enumerate(reph):                       # EKF3's writeExtNavData acceptance (pos finite, 20 ms rate limit)
    if not np.all(np.isfinite(r[[0, 1, 6]])):
        continue
    if (int(r[8]) - last) % 2 ** 32 < 20:
        continue
    last = int(r[8]); acc.append(i)
acc = np.array(acc)
ub1 = {"ekf3_rule_accepts": int(len(acc)), "same_count": bool(len(acc) == len(T))}
if len(acc) == len(T):
    A = reph[acc]
    q = A[:, 2:6]
    yaw321 = np.arctan2(2 * (q[:, 0] * q[:, 3] + q[:, 1] * q[:, 2]), 1 - 2 * (q[:, 2] ** 2 + q[:, 3] ** 2))
    evt_exp = np.maximum(T[:, 1] - T[:, 2] - 6, T[:, 0] - 60)
    rp_exp = np.array([f32(min(max(f32(e), f32(0.01)), f32(10.0))) ** 2 for e in A[:, 6]])
    r5 = f32(math.radians(5.0))
    ry_exp = np.array([max(max(f32(e), r5), 0.05) ** 2 for e in A[:, 7]])
    ub1.update({"ts_delay_match": bool(np.all(T[:, 1] == A[:, 8]) and np.all(T[:, 2] == A[:, 9])),
                "event_time_rule_exact": bool(np.all(T[:, 3] == evt_exp)),
                "event_time_clamped_share": float(np.mean(T[:, 0] - 60 > T[:, 1] - T[:, 2] - 6)),
                "pos_max_abs_diff": float(np.max(np.abs(T[:, 4:6] - A[:, 0:2]))),
                "yaw_max_abs_diff_rad": float(np.max(np.abs(wrap(T[:, 6] - yaw321)))),
                "rpos_max_rel_diff": float(np.max(np.abs(T[:, 7] / rp_exp - 1))),
                "ryaw_max_rel_diff": float(np.max(np.abs(T[:, 8] / ry_exp - 1)))})
    ub1["pass"] = bool(ub1["same_count"] and ub1["ts_delay_match"] and ub1["event_time_rule_exact"]
                       and ub1["pos_max_abs_diff"] <= 1e-6 and ub1["yaw_max_abs_diff_rad"] <= 1e-6
                       and ub1["rpos_max_rel_diff"] <= 1e-6 and ub1["ryaw_max_rel_diff"] <= 1e-6)
else:
    ub1["pass"] = False
out["UB1"] = ub1
# ---- UB2: queue ----
srt = np.sort(T[:, 3].astype(int))
ub2 = {"each_processed_once": bool(len(P5) == len(T) and np.array_equal(np.sort(P5[:, 0]), srt)),
       "time_ordered": bool(np.all(np.diff(P5[:, 0]) >= 0)),
       "min_horizon_minus_event_ms": int(np.min((P5[:, 1] - 60) - P5[:, 0]))}
ub2["pass"] = bool(ub2["each_processed_once"] and ub2["time_ordered"] and ub2["min_horizon_minus_event_ms"] >= 0)
out["UB2"] = ub2
# ---- UB3: anchor ----
ia = np.where(TP[:, 1] == 1)[0]
first = TP[0]
Tfirst = T[np.argsort(T[:, 3], kind="stable")][0]
ub3 = {"n_anchor_rows": int(len(ia)), "anchor_is_first_processed": bool(len(ia) == 1 and ia[0] == 0),
       "anchor_event_time_ms": int(first[0]),
       "state_eq_fix_max_abs": float(max(abs(first[2] - Tfirst[4]), abs(first[3] - Tfirst[5]), abs(wrap(first[4] - Tfirst[6])))),
       "pseudo_yaw_before_anchor": int((Y < first[0]).sum()), "pseudo_yaw_after_anchor": int((Y > first[0]).sum())}
ub3["pass"] = bool(ub3["anchor_is_first_processed"] and ub3["state_eq_fix_max_abs"] <= 1e-6 and ub3["pseudo_yaw_after_anchor"] == 0)
out["UB3"] = ub3
out["UB4"] = {"processed_eq_accepted": bool(len(TP) == len(T)), "pass": bool(len(TP) == len(T))}

# ---- clock map and bag ----
ts = get_typestore(Stores.ROS2_JAZZY); TR, SENT, G = [], [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/imu/time_ref", "/tags/sent", "/ground_truth/pose")]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        th = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, th))
        elif con.topic == "/tags/sent":
            SENT.append(th)
        else:
            q = m.pose.orientation
            G.append((th, m.pose.position.y - TAG[1], m.pose.position.x - TAG[0], math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
TR, SENT, G = np.array(TR), np.array(SENT), np.array(sorted(G))
sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):          # lower envelope per 5 s, linear fit (as eval/h_score.py)
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1); to_bag = lambda x: x + (kk * x + c0)
out["clock_map"] = {"rate_ppm": float(kk * 1e6), "offset_s": float(c0)}
# fix-time offsets: the port's event time (bag clock) minus the fix's capture stamp (REPH <-> /tags/sent 1:1 in order)
if len(SENT) == len(reph) and len(acc) == len(T):
    off = (to_bag(T[:, 3] / 1e3) - SENT[acc]) * 1e3
    out["fix_time_offset_ms"] = {"median": float(np.median(off)), "p5": float(np.percentile(off, 5)), "p95": float(np.percentile(off, 95)),
                                 "min": float(off.min()), "max": float(off.max())}

# ---- tracks ----
cv = np.genfromtxt(f"{R}/ukf_shadow.csv", delimiter=",", names=True)
port = np.c_[to_bag(cv["TimeUS"] / 1e6), cv["PN"], cv["PE"], wrap(np.radians(cv["Yaw"]))]     # t, N, E, yaw NED
x = np.loadtxt(f"{D}/room_ukf/ukf_live.tum")
qx, qy, qz, qw = x[:, 4], x[:, 5], x[:, 6], x[:, 7]
off_t = np.c_[x[:, 0], x[:, 2], x[:, 1], wrap(np.pi / 2 - np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy ** 2 + qz ** 2)))]
t_anchor_bag = float(off_t[0, 0])
w = (port[:, 0] >= max(t_anchor_bag, off_t[0, 0])) & (port[:, 0] <= off_t[-1, 0])
P_ = port[w]
oN, oE = np.interp(P_[:, 0], off_t[:, 0], off_t[:, 1]), np.interp(P_[:, 0], off_t[:, 0], off_t[:, 2])
oY = np.interp(P_[:, 0], off_t[:, 0], np.unwrap(off_t[:, 3]))
dh = np.hypot(P_[:, 1] - oN, P_[:, 2] - oE); dy = np.degrees(np.abs(wrap(P_[:, 3] - oY)))
# tag-visible: a sent fix within the previous 0.2 s; exclude 2 s after the anchor and after each re-acquisition (gap > 1 s)
j = np.searchsorted(SENT, P_[:, 0], side="right") - 1
vis = (j >= 0) & (P_[:, 0] - SENT[np.clip(j, 0, None)] <= 0.2)
reacq = [SENT[0]] + [SENT[k] for k in range(1, len(SENT)) if SENT[k] - SENT[k - 1] > 1.0]
for tr_ in reacq:
    vis &= ~((P_[:, 0] >= tr_) & (P_[:, 0] < tr_ + 2.0))
ub5 = {"samples_visible": int(vis.sum()), "samples_total": int(len(P_)),
       "horiz_m": {"p50": float(np.median(dh[vis])), "p95": float(np.percentile(dh[vis], 95)), "max": float(dh[vis].max())},
       "yaw_deg": {"p50": float(np.median(dy[vis])), "p95": float(np.percentile(dy[vis], 95)), "max": float(dy[vis].max())},
       "band": "horizontal p95 <= 0.02 m, max <= 0.05 m; yaw p95 <= 1.0 deg, max <= 2.0 deg"}
ub5["pass"] = bool(ub5["horiz_m"]["p95"] <= 0.02 and ub5["horiz_m"]["max"] <= 0.05 and ub5["yaw_deg"]["p95"] <= 1.0 and ub5["yaw_deg"]["max"] <= 2.0)
out["UB5"] = ub5
out["diag_whole_after_anchor"] = {"horiz_max_m": float(dh.max()), "yaw_max_deg": float(dy.max())}

# ---- losses: differences (report) and the UB6 prediction (port drift vs GT) ----
occ = []
for ln in open(f"{D}/logs/fly_trial.log"):
    m_ = re.search(r"OCCLUDER (ON|OFF) t_sim=([\d.]+)", ln)
    if m_:
        occ.append((m_[1], to_bag(float(m_[2]))))
gi = lambda t, c: np.interp(t, G[:, 0], G[:, c])
bands = [0.10, 0.20, 0.40, 0.30]       # P-H5 UKF: hover 5 / 15 / 30 s, during the move
L = []
for k_, ((s1, ton), (s2, toff)) in enumerate(zip(occ[0::2], occ[1::2])):
    row = {"t_on": float(ton), "t_off": float(toff), "band_m": bands[k_] if k_ < 4 else None}
    k_first = int(np.searchsorted(SENT, toff, side="right")) if (SENT > toff).any() else None
    # effective: the port's state BEFORE it fused the returning fix. The port fuses each fix at its EVENT time (EKF3's
    # clamp, ~25 ms before capture) on the horizon timeline, so the cut is that fix's event time (its T row, REPH and
    # /tags/sent 1:1), not its capture stamp (corrected 2026-10-08, before hand-off: the capture cut could include the fix)
    t_eff = float(to_bag(T[k_first, 3] / 1e3)) if (k_first is not None and len(acc) == len(T) and len(SENT) == len(reph)) else None
    for lab, tq in (("as_worded", toff), ("effective", t_eff)):
        if tq is None:
            continue
        ib = np.searchsorted(port[:, 0], tq, side="left") - 1     # the last port sample strictly before tq
        tp = port[ib, 0]
        drift = math.hypot(port[ib, 1] - gi(tp, 1), port[ib, 2] - gi(tp, 2))
        on, oe = np.interp(tp, off_t[:, 0], off_t[:, 1]), np.interp(tp, off_t[:, 0], off_t[:, 2])
        row[lab] = {"t": float(tp), "port_drift_m": float(drift), "offline_drift_m": float(math.hypot(on - gi(tp, 1), oe - gi(tp, 2))),
                    "port_minus_offline_m": float(math.hypot(port[ib, 1] - on, port[ib, 2] - oe))}
    if k_ < 4:
        row["UB6_within_band"] = bool(all(row[l]["port_drift_m"] <= bands[k_] for l in ("as_worded", "effective") if l in row))
    L.append(row)
out["losses"] = L
out["UB6_prediction_holds"] = bool(all(r.get("UB6_within_band", True) for r in L))
out["pass_UB1_UB5"] = bool(all(out[k]["pass"] for k in ("UB1", "UB2", "UB3", "UB4", "UB5")))
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
