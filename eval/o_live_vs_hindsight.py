#!/usr/bin/env python3
"""Experiment 4 (O) live against hindsight, read-only, from the STORED tracks only (no replay, flight or simulation).
Ground truth, the SITL->bag clock map, the route markers and the error definition are taken verbatim from
eval/o_score.py (horizontal error, world frame, no alignment); the script first checks that it reproduces the stored
indoor_rmse_m / indoor_max_m / err_at_return_m of eval/results/expO/<trial>.json exactly (float equality) and stops
otherwise. Per trial it then reports:
  1. per live track (UKF, FGO) against its own hindsight track (RTS-UKF, FGO whole-flight batch): the first live sample
     in [GNSS OFF, GNSS ON] whose error exceeds the hindsight error at that instant (hindsight POSITION linearly
     interpolated to the live sample time, then its error against ground truth), the number of below/above changes, the
     last below->above change, and the time-weighted fraction of the indoor section with live below hindsight
     (each live sample holds until the next one; the section is clipped to [OFF, ON]);
  2. per live track (EKF3, UKF, FGO): the minimum error on the return leg [OUTBACK BACK START, GNSS ON], with its time;
  3. per hindsight track: the peak error in [OFF, ON], with its time;
  5. per live track: the along-track / cross-track split of the error vector (estimate minus truth) at the far end
     (OUTBACK BACK START), at the return-leg minimum and at GNSS ON (nearest sample, as o_score's err_at_return_m).
     Along-track axis u = unit vector from the true position at OUTBACK OUT START to the true position at OUTBACK BACK
     START (the outward leg); along = e.u (positive = estimate further out than truth); cross = e.n, n = u rotated +90 deg
     (positive = estimate to the left of the outward direction).
  Also: the GNSS samples (gnss.npz) before GNSS OFF from the re-anchor on, and after GNSS ON (item 4 support).
Usage (venv-tags, under heavy.py): python3 eval/o_live_vs_hindsight.py [--json OUT]"""
import argparse, json, os, re
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIALS = ("O_r1", "O_r2", "O_r3b")
PAIRS = (("UKF live", "RTS-UKF (hindsight)"), ("FGO live", "FGO hindsight (whole-flight batch)"))
FILES = {"UKF live": "room_ukf/ukf_live.tum", "RTS-UKF (hindsight)": "room_ukf/ukf_rts.tum",
         "FGO live": "room_fgo/fgo_live.tum", "FGO hindsight (whole-flight batch)": "room_fgo/fgo_batch.tum"}
ts = get_typestore(Stores.ROS2_JAZZY)
out = {}
for trial in TRIALS:
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    stored = json.load(open(f"{REPO}/eval/results/expO/{trial}.json"))
    # ---- verbatim from eval/o_score.py: ground truth, clock map, markers, EKF3 track ----
    G, TR = [], []
    with Reader(f"{D}/bag") as rd:
        cs = {c.topic: c for c in rd.connections}
        for con, _, raw in rd.messages(connections=[cs["/ground_truth/pose"], cs["/imu/time_ref"]]):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/imu/time_ref":
                TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
            else:
                G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y))
    G, TR = np.array(G), np.array(TR)
    sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        w = (sitl >= lo) & (sitl < lo + 5)
        if w.sum() > 50:
            i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
    env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
    to_bag = lambda x: x + (kk * x + c0)
    mk = {}
    for ln in open(f"{D}/logs/fly_trial.log"):
        for key in ("GNSS OFF", "GNSS ON", "OUTBACK ALIGN START", "OUTBACK OUT START", "OUTBACK BACK START", "OUTBACK END"):
            m_ = re.search(key + r" (?:START )?t_sim=([\d.]+)", ln) if "START" not in key else re.search(key + r" t_sim=([\d.]+)", ln)
            if m_ and key not in mk: mk[key] = to_bag(float(m_[1]))
    g = np.load(f"{D}/gnss.npz"); oE, oN = g["ekf3_origin_EN"]
    mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1 = []
    while True:
        r = mv.recv_match(type=["XKF1"])
        if r is None: break
        if r.C != 0: continue
        k1.append((to_bag(r.TimeUS / 1e6), r.PE + oE, r.PN + oN))
    tracks = {"EKF3 live": np.array(k1)}
    for n_, p in FILES.items():
        tracks[n_] = np.loadtxt(f"{D}/{p}", ndmin=2)[:, :3]
    # ---- checks against the stored scores ----
    assert {k: float(v) for k, v in mk.items()} == stored["markers_bag_s"], (trial, "markers differ")
    T_OFF, T_ON, T_FAR, T_OUT = mk["GNSS OFF"], mk["GNSS ON"], mk["OUTBACK BACK START"], mk["OUTBACK OUT START"]
    gx = lambda t: np.interp(t, G[:, 0], G[:, 1]); gy = lambda t: np.interp(t, G[:, 0], G[:, 2])
    def evec(T):
        return np.stack([T[:, 1] - gx(T[:, 0]), T[:, 2] - gy(T[:, 0])], 1)
    for n_, T in tracks.items():
        e = np.hypot(*evec(T).T); w = (T[:, 0] >= T_OFF) & (T[:, 0] <= T_ON); s = stored["tracks"][n_]
        i_on = np.argmin(np.abs(T[:, 0] - T_ON))
        assert float(np.sqrt(np.mean(e[w] ** 2))) == s["indoor_rmse_m"], (trial, n_, "rmse")
        assert float(e[w].max()) == s["indoor_max_m"], (trial, n_, "max")
        assert float(e[i_on]) == s["err_at_return_m"], (trial, n_, "at return")
    R = {"markers_bag_s": stored["markers_bag_s"], "indoor_s": stored["indoor_s"], "checks_vs_stored": "PASS (markers; indoor_rmse_m, indoor_max_m, err_at_return_m for all 6 tracks, float equality)"}
    # ---- 1. live vs own hindsight ----
    R["item1"] = {}
    for live, hind in PAIRS:
        L, H = tracks[live], tracks[hind]
        w = (L[:, 0] >= T_OFF) & (L[:, 0] <= T_ON); tl = L[w, 0]
        el = np.hypot(*evec(L[w]).T)
        hx = np.interp(tl, H[:, 0], H[:, 1]); hy = np.interp(tl, H[:, 0], H[:, 2])
        eh = np.hypot(hx - gx(tl), hy - gy(tl))
        above = el > eh
        ch = np.flatnonzero(np.diff(above.astype(int)) != 0) + 1
        up = [int(i) for i in ch if above[i]]
        t_end = np.append(tl[1:], T_ON); dt = t_end - tl
        frac_below = float(dt[~above].sum() / (T_ON - T_OFF))
        i1 = int(np.argmax(above)) if above.any() else None
        R["item1"][live] = {"hindsight": hind, "n_live_samples_indoor": int(w.sum()),
                            "first_above_t_since_off_s": float(tl[i1] - T_OFF) if i1 is not None else None,
                            "first_above_live_err_m": float(el[i1]) if i1 is not None else None,
                            "first_above_hind_err_m": float(eh[i1]) if i1 is not None else None,
                            "live_above_at_first_indoor_sample": bool(above[0]),
                            "n_changes": int(len(ch)),
                            "last_below_to_above_t_since_off_s": float(tl[up[-1]] - T_OFF) if up else None,
                            "frac_indoor_live_below": frac_below}
    # ---- 2. return-leg minimum of each live error; 5. along/cross split ----
    vo = np.array([gx(T_OUT), gy(T_OUT)]); vf = np.array([gx(T_FAR), gy(T_FAR)])
    u = (vf - vo) / np.linalg.norm(vf - vo); nrm = np.array([-u[1], u[0]])
    R["axis"] = {"u_EN": u.tolist(), "n_EN": nrm.tolist(), "true_out_start_EN": vo.tolist(), "true_far_end_EN": vf.tolist(),
                 "outward_leg_length_m": float(np.linalg.norm(vf - vo))}
    R["item2"], R["item5"] = {}, {}
    for live in ("EKF3 live", "UKF live", "FGO live"):
        T = tracks[live]; E = evec(T); e = np.hypot(*E.T)
        w = np.flatnonzero((T[:, 0] >= T_FAR) & (T[:, 0] <= T_ON)); im = int(w[np.argmin(e[w])])
        R["item2"][live] = {"min_err_m": float(e[im]), "t_since_off_s": float(T[im, 0] - T_OFF), "t_bag_s": float(T[im, 0]),
                            "t_since_far_end_s": float(T[im, 0] - T_FAR)}
        R["item5"][live] = {}
        for lab, i in (("far_end", int(np.argmin(np.abs(T[:, 0] - T_FAR)))), ("return_leg_min", im),
                       ("gnss_on", int(np.argmin(np.abs(T[:, 0] - T_ON))))):
            R["item5"][live][lab] = {"t_since_off_s": float(T[i, 0] - T_OFF), "err_m": float(e[i]),
                                     "along_m": float(E[i] @ u), "cross_m": float(E[i] @ nrm)}
    # ---- 3. hindsight peaks ----
    R["item3"] = {}
    for _, hind in PAIRS:
        T = tracks[hind]; e = np.hypot(*evec(T).T); w = np.flatnonzero((T[:, 0] >= T_OFF) & (T[:, 0] <= T_ON))
        ip = int(w[np.argmax(e[w])])
        assert float(e[ip]) == stored["tracks"][hind]["indoor_max_m"]
        R["item3"][hind] = {"peak_err_m": float(e[ip]), "t_since_off_s": float(T[ip, 0] - T_OFF), "t_bag_s": float(T[ip, 0])}
    # ---- 4. GNSS samples available to the replays ----
    tg = g["t"]
    R["item4_gnss_samples"] = {"n_total": int(len(tg)), "t_first": float(tg.min()), "t_last": float(tg.max()),
                               "n_before_off": int((tg < T_OFF).sum()), "n_after_on": int((tg > T_ON).sum()),
                               "n_in_indoor": int(((tg >= T_OFF) & (tg <= T_ON)).sum()),
                               "last_before_off": float(tg[tg < T_OFF].max()), "first_after_on": float(tg[tg > T_ON].min()),
                               "hindsight_track_span": {h: [float(tracks[h][0, 0]), float(tracks[h][-1, 0])] for _, h in PAIRS}}
    out[trial] = R
    print(trial, json.dumps(R, indent=1))
if a.json:
    os.makedirs(os.path.dirname(a.json), exist_ok=True); json.dump(out, open(a.json, "w"), indent=1)
