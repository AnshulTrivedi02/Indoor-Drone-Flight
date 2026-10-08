#!/usr/bin/env python3
"""Experiment H scorer, S1 (METHODOLOGY "Experiment H: pre-registration"). One flight:
  * frame W = the wall tag frame (N_W = world y - 4.998, E_W = world x); GT from the bag;
  * markers from fly_trial.log (HSEG i type START, OCCLUDER ON/OFF; SITL clock -> bag clock, /imu/time_ref envelope);
    the setpoint timeline is rebuilt from the profile JSON (HPROFILE path in metadata or --profile);
  * tracks: EKF3 (XKF1 core 0 PN/PE: EKF3's navigation frame IS W via ExtNav), UKF (room_ukf/ukf_live.tum) and FGO
    (room_fgo/fgo_live.tum), both in W written as ENU (x = E_W, y = N_W);
  * flying-estimator metrics (EKF3 in S1): hold error (GT distance from the hold target) per pre-loss hold window
    (the 60 s and 30 s holds, excluding 5 s after the change), lateral tracking error (GT E vs setpoint E during the
    lateral cycles), gyro activity (|gyro| high-passed at 1 Hz, RMS) in the hold windows;
  * per loss (OCCLUDER ON -> OFF) and per estimator: drift at the end (|estimate - GT| at OFF), re-lock time (OFF ->
    first fix sent after OFF; EKF3: first VISP after OFF), jump (largest position / yaw step in the 2 s after re-lock),
    lockout (after re-lock, |estimate - GT| > 3 sigma_pos sustained > 2 s while fixes arrive), EKF3 posTimeout share.
Usage (venv-tags): python3 eval/h_score.py TRIAL --profile batches/expH/s1_profile.json --sigma SIGMA [--json OUT]"""
import argparse, json, math, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--profile", required=True)
ap.add_argument("--sigma", type=float, required=True); ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); TAG = (0.0, 4.998)
wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi
ts = get_typestore(Stores.ROS2_JAZZY); G, TR, SENT, GY = [], [], [], []
with Reader(f"{D}/bag") as rd:
    cs = {c.topic: c for c in rd.connections}
    for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref", "/tags/sent", "/imu/data_raw") if x in cs]):
        m = ts.deserialize_cdr(raw, con.msgtype)
        if con.topic == "/imu/time_ref":
            TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)); continue
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if con.topic == "/ground_truth/pose":
            q = m.pose.orientation
            G.append((t, m.pose.position.y - TAG[1], m.pose.position.x - TAG[0], math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
        elif con.topic == "/tags/sent": SENT.append(t)
        else: GY.append((t, m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z))
G, TR, SENT, GY = np.array(G), np.array(TR), np.array(sorted(SENT)), np.array(GY)      # G: t, N_W, E_W, yaw_enu
sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1); to_bag = lambda x: x + (kk * x + c0)
seg_t, occ = {}, []
for ln in open(f"{D}/logs/fly_trial.log"):
    m_ = re.search(r"HSEG (\d+) (\w+) START t_sim=([\d.]+)", ln)
    if m_: seg_t[int(m_[1])] = to_bag(float(m_[3]))
    m_ = re.search(r"OCCLUDER (ON|OFF) t_sim=([\d.]+)", ln)
    if m_: occ.append((m_[1], to_bag(float(m_[2]))))
m_ = [ln for ln in open(f"{D}/logs/fly_trial.log") if "HPROFILE END" in ln]; t_end = to_bag(float(re.search(r"t_sim=([\d.]+)", m_[0])[1]))
P = json.load(open(a.profile))
# the hold point = the first move's target (S1: = the wait_fix point; from the far spawn, 2026-10-08 ruling 2, the first
# move is the ~2.4 m approach from the spawn, a DEVIATION excluded from scoring: no window below starts in it)
H = next(sg["to"] for sg in P if sg["type"] == "move"); START = P[0]["near"]
# setpoint timeline (N, E) from the profile and the segment start times
sp = []; cur = None
for i, sg in enumerate(P):
    if sg["type"] == "wait_fix": cur = list(START); continue
    if sg["type"] == "move":
        t0 = seg_t[i]; dd = math.hypot(sg["to"][0] - cur[0], sg["to"][1] - cur[1]); T = dd / sg["speed"]
        for tt in np.arange(0, T, 0.02): sp.append((t0 + tt, cur[0] + (sg["to"][0] - cur[0]) * tt / T, cur[1] + (sg["to"][1] - cur[1]) * tt / T))
        cur = list(sg["to"])
    elif sg["type"] == "hold":
        t0 = seg_t[i]; t1 = seg_t.get(i + 1, t_end)
        for tt in np.arange(t0, t1, 0.02): sp.append((tt, cur[0], cur[1]))
SP = np.array(sp)
# tracks
tracks = {}
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1, k4, visp = [], [], []
while True:
    r = mv.recv_match(type=["XKF1", "XKF4", "VISP"])
    if r is None: break
    if r.get_type() == "VISP": visp.append(to_bag(r.TimeUS / 1e6)); continue
    if r.C != 0: continue
    if r.get_type() == "XKF1": k1.append((to_bag(r.TimeUS / 1e6), r.PN, r.PE, math.radians(90.0 - r.Yaw)))
    else: k4.append((to_bag(r.TimeUS / 1e6), int(r.TS) & 1))
tracks["EKF3"] = np.array(k1); k4 = np.array(k4); visp = np.array(sorted(visp))
for n, p in (("UKF", "room_ukf/ukf_live.tum"), ("FGO", os.environ.get("DIAG_FGO_TUM", "room_fgo/fgo_live.tum"))):
    if os.path.exists(os.path.join(D, p)):
        x = np.loadtxt(os.path.join(D, p), ndmin=2); qx, qy, qz, qw = x[:, 4], x[:, 5], x[:, 6], x[:, 7]
        tracks[n] = np.c_[x[:, 0], x[:, 2], x[:, 1], np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy ** 2 + qz ** 2))]
gi = lambda t, c: np.interp(t, G[:, 0], G[:, c])
out = {"trial": a.trial, "sigma_pos": a.sigma}
# flying estimator (EKF3): hold windows = segment 2 (60 s) and the 30 s hold after the lateral cycles
holds = [(i, sg) for i, sg in enumerate(P) if sg["type"] == "hold" and sg["s"] >= 30]
pre_loss = [h for h in holds if seg_t[h[0]] < occ[0][1]]
hw = []
for i, sg in pre_loss:
    t0, t1 = seg_t[i] + 5, seg_t[i] + sg["s"]; w = (G[:, 0] >= t0) & (G[:, 0] <= t1)
    e = np.hypot(G[w, 1] - H[0], G[w, 2] - H[1])
    gw = (GY[:, 0] >= t0) & (GY[:, 0] <= t1); g = GY[gw, 1:]
    k = max(1, int(round(1.0 / np.median(np.diff(GY[:, 0])))))
    hp = g - np.vstack([np.convolve(g[:, j], np.ones(k) / k, "same") for j in range(3)]).T
    hw.append({"t0": float(t0), "t1": float(t1), "mean_m": float(e.mean()), "max_m": float(e.max()), "gyro_hp_rms_rad_s": float(np.sqrt(np.mean(np.sum(hp ** 2, 1))))})
out["hold_windows_EKF3_flying"] = hw
lat_i = [i for i, sg in enumerate(P) if sg["type"] == "move" and abs(sg["to"][1]) > 0 and seg_t[i] < occ[0][1]]
t0, t1 = seg_t[lat_i[0]], seg_t[lat_i[-1] + 3] if lat_i[-1] + 3 in seg_t else seg_t[lat_i[-1]] + 20
w = (G[:, 0] >= t0) & (G[:, 0] <= t1); eE = G[w, 2] - np.interp(G[w, 0], SP[:, 0], SP[:, 2]); eN = G[w, 1] - np.interp(G[w, 0], SP[:, 0], SP[:, 1])
out["lateral_tracking_EKF3_flying"] = {"rmse_m": float(np.sqrt(np.mean(eE ** 2 + eN ** 2))), "max_m": float(np.hypot(eE, eN).max())}
# losses
L = []
for (s1, ton), (s2, toff) in zip(occ[0::2], occ[1::2]):
    assert s1 == "ON" and s2 == "OFF"
    row = {"t_on": float(ton), "t_off": float(toff), "duration_s": float(toff - ton)}
    w4 = (k4[:, 0] > ton) & (k4[:, 0] < toff); row["EKF3_posTimeout_share"] = float(k4[w4, 1].mean()) if w4.any() else None
    for n, X in tracks.items():
        i_off = np.argmin(np.abs(X[:, 0] - toff))
        drift = float(math.hypot(X[i_off, 1] - gi(X[i_off, 0], 1), X[i_off, 2] - gi(X[i_off, 0], 2)))
        src = visp if n == "EKF3" else SENT
        nxt = src[src > toff]; t_rl = float(nxt[0]) if len(nxt) else None
        r = {"drift_end_m": drift, "relock_s": (t_rl - toff) if t_rl else None}
        if t_rl:
            w = (X[:, 0] >= t_rl - 0.05) & (X[:, 0] <= t_rl + 2.0); Y = X[w]
            st = np.hypot(np.diff(Y[:, 1]), np.diff(Y[:, 2])); sy = np.degrees(np.abs(wrap(np.diff(Y[:, 3]))))
            r["jump_pos_m"] = float(st.max()) if len(st) else None; r["jump_yaw_deg"] = float(sy.max()) if len(sy) else None
            w2 = (X[:, 0] > t_rl + 0.5) & (X[:, 0] < t_rl + 6)
            err = np.hypot(X[w2, 1] - gi(X[w2, 0], 1), X[w2, 2] - gi(X[w2, 0], 2))
            bad = err > 3 * a.sigma; run = 0; mx = 0
            dt = np.median(np.diff(X[:, 0])) if len(X) > 2 else 0.01
            for b in bad:
                run = run + 1 if b else 0; mx = max(mx, run)
            r["lockout"] = bool(mx * dt > 2.0); r["err_after_relock_max_m"] = float(err.max()) if len(err) else None
        # EFFECTIVE loss (POST HOC, 2026-10-08): the occluder's rendering lags set_pose by 0.16-1.0 s, so fixes go on
        # after ON and resume late after OFF. The real loss = the gap in SENT fixes around OFF:
        # t_last = last fix before OFF, t_first = first fix after OFF. Drift at t_first (just before fusing it);
        # estimator re-lock = first fused fix (EKF3: VISP receipt; UKF/FGO: the fix itself) - t_first; jump after t_first.
        prev = SENT[SENT < toff]; nxt2 = SENT[SENT > toff]
        if len(prev) and len(nxt2):
            tl, tf = float(prev[-1]), float(nxt2[0])
            i_b = np.searchsorted(X[:, 0], tf) - 1
            d_eff = float(math.hypot(X[i_b, 1] - gi(X[i_b, 0], 1), X[i_b, 2] - gi(X[i_b, 0], 2)))
            fus = (visp[visp >= tf - 1e-6][0] if n == "EKF3" and (visp >= tf - 1e-6).any() else tf)
            w = (X[:, 0] >= tf - 0.05) & (X[:, 0] <= tf + 2.0); Y = X[w]
            st = np.hypot(np.diff(Y[:, 1]), np.diff(Y[:, 2])); sy = np.degrees(np.abs(wrap(np.diff(Y[:, 3]))))
            r["effective"] = {"t_last_fix": tl, "t_first_fix": tf, "loss_s": tf - tl, "drift_m": d_eff,
                              "relock_after_first_fix_s": float(fus - tf),
                              "jump_pos_m": float(st.max()) if len(st) else None, "jump_yaw_deg": float(sy.max()) if len(sy) else None}
        row[n] = r
    L.append(row)
out["losses"] = L
print(json.dumps(out, indent=1))
if a.json: json.dump(out, open(a.json, "w"), indent=1)
