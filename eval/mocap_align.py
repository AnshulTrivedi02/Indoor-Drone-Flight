#!/usr/bin/env python3
"""Mocap alignment (real-flight plan, tooling item 4): TIME and FRAME alignment of motion-capture ground truth against
the flight-controller (FC) dataflash log and the Pi's logs, reusing the simulation's clock-map approach
(eval/input_timing.clock_offset / clock_map: least squares on frame-independent motion features, fitted in an early and
a late window, giving a LINEAR map offset + rate).

Clocks:
  * FC: dataflash TimeUS (us since boot).
  * Pi: ROS header time. The Pi <-> FC map comes from /imu/time_ref pairs (header Pi time, time_ref = HIGHRES_IMU.time_usec
    FC time): the D25 lower envelope (1st percentile of Pi - FC per 10 s window, outlier-robust) and a linear fit across
    the windows (rate). Same idea as the FGO node's live map.
  * Mocap: the mocap host's stamps (CSV). Mocap <-> FC is fitted from motion features both see, independent of frames:
      - vertical speed: d(mocap z)/dt against d(RFND distance)/dt (gravity-aligned z in both; small tilt);
      - angular speed |w|: from mocap orientation (quaternion differences) against |FC gyro| (IMU, any axes).
    Each feature is normalised by its RMS; the offset minimising their summed squared difference is found on a coarse then
    fine grid, in an early (take-off) and a late (landing) window -> offset(t) linear in t (rate in ppm).
Frame (after time alignment): mocap positions -> the estimator's navigation frame by a 4-DoF fit (yaw + 3-D translation;
both frames are gravity-aligned) on an initial segment (default: from arming to cruise start + 10 s), i.e. aligned at the
start so that later drift is NOT absorbed. Also reported: a whole-flight 4-DoF fit (absorbs drift), for evo -a style ATE. And the
mocap-body to vehicle-body rotation from a static period (mocap orientation against the FC's ATT roll/pitch/yaw).
Writes JSON (clock maps with residuals, transforms) and TUM files of mocap truth on the FC clock, in the estimator frame.

Mocap CSV columns: t_s, x, y, z, qx, qy, qz, qw (metres; scalar-last quaternion, the mocap's world frame, z UP).
Usage (venv-evo + pymavlink shim):
  python3 eval/mocap_align.py --bin FLIGHT.bin --mocap mocap.csv [--est XKF1|XUKO|XFGO] [--pi-bag BAG] [--out-dir DIR]
  python3 eval/mocap_align.py --selftest TRIAL   (synthetic mocap from a simulated flight's SIM truth)"""
import argparse, json, math, os, sys
import numpy as np
from scipy.spatial.transform import Rotation as Rot
from pymavlink import mavutil


# ---------------------------------------------------------------------------------------------- FC log
def read_fc(path, est="XKF1"):
    m = mavutil.mavlink_connection(path); G, R, A, E, S, ARM, P = [], [], [], [], [], [], {}
    while True:
        r = m.recv_match(type=["IMU", "RFND", "ATT", est, "SIM", "ARM", "PARM"])
        if r is None:
            break
        t = r.TimeUS / 1e6; ty = r.get_type()
        if ty == "IMU" and r.I == 0: G.append((t, r.GyrX, r.GyrY, r.GyrZ))
        elif ty == "RFND" and r.Instance == 0: R.append((t, r.Dist))
        elif ty == "ATT": A.append((t, r.Roll, r.Pitch, r.Yaw))
        elif ty == est and (est != "XKF1" or r.C == 0): E.append((t, r.PN, r.PE, r.PD))
        elif ty == "SIM": S.append((t, r.Lat, r.Lng, r.Alt, r.Roll, r.Pitch, r.Yaw))
        elif ty == "ARM": ARM.append((t, r.ArmState))
        elif ty == "PARM": P[r.Name] = r.Value
    return {k: np.array(v) for k, v in (("gyro", G), ("rfnd", R), ("att", A), ("est", E), ("sim", S))} | {"arm": ARM, "params": P}


# ---------------------------------------------------------------------------------------------- features
def ang_speed_mocap(t, q):
    r = Rot.from_quat(q); d = (r[:-1].inv() * r[1:]).as_rotvec()
    return 0.5 * (t[1:] + t[:-1]), np.linalg.norm(d, axis=1) / np.diff(t)


SMOOTH_S, GRID_S = 0.2, 0.01          # identical boxcar (s) on a common grid (s) for BOTH clocks' features


def boxcar(x):
    n = max(1, int(round(SMOOTH_S / GRID_S))); return np.convolve(x, np.ones(n) / n, "same")


def clean_rfnd(rf):
    """Drop rangefinder short returns (the D23 artefact): samples below 60% of the 1 s rolling median."""
    t, d = rf[:, 0], rf[:, 1]; keep = np.ones(len(d), bool)
    for i in range(len(d)):
        w = (t >= t[i] - 0.5) & (t <= t[i] + 0.5)
        if d[i] < 0.6 * np.median(d[w]): keep[i] = False
    return rf[keep]


def gyro_group_delay_s(fc):
    """Low-frequency group delay of ArduPilot's 2-pole (Butterworth) gyro low-pass, INS_GYRO_FILTER Hz:
    sqrt(2) / (2 pi fc). The logged IMU gyro lags the true motion by this much (20 Hz -> 11.3 ms)."""
    f = float(fc["params"].get("INS_GYRO_FILTER", 0) or 0)
    return math.sqrt(2) / (2 * math.pi * f) if f > 0 else 0.0


def fc_raw_curves(fc):
    """FC features on the FC clock. The gyro is shifted EARLIER by the INS filter's group delay, so the fitted offset
    maps clocks rather than absorbing the filter lag. The rangefinder path's latency is NOT known (sensor + link), so vz
    is an optional cross-check only (self-test: vz alone biased the offset by about -40 ms)."""
    g = fc["gyro"]; rf = clean_rfnd(fc["rfnd"]); dg = gyro_group_delay_s(fc)
    return {"w": (g[:, 0] - dg, np.linalg.norm(g[:, 1:4], axis=1)), "z": (rf[:, 0], rf[:, 1])}


def mocap_raw_curves(mo):
    tw, w = ang_speed_mocap(mo["t"], mo["q"])
    return {"w": (tw, w), "z": (mo["t"], mo["p"][:, 2])}


def feats(curves, grid):
    """|w| and vertical speed on `grid`, computed IDENTICALLY for either clock: interpolate, differentiate, boxcar."""
    w = boxcar(np.interp(grid, *curves["w"]))
    vz = boxcar(np.gradient(np.interp(grid, *curves["z"]), GRID_S))
    return {"w": w, "vz": vz}


def takeoff_time(t, vz, thr=0.2, hold=1.0):
    """First time vz stays above thr for hold seconds (the take-off climb)."""
    up = vz > thr; dt = np.median(np.diff(t)); n = max(1, int(hold / dt))
    run = np.convolve(up.astype(int), np.ones(n, int), "valid")
    i = np.argmax(run >= n)
    return float(t[i])


def fit_offset(fc_c, mo_c, lo, hi, d0, half=2.0, use=("w",)):
    """offset d (mocap clock - FC clock) minimising sum over features of ((f_fc(t) - f_mo(t + d)) / rms)^2 for t in
    [lo, hi], searched within d0 +- half (d0 from the take-off match); coarse, then two finer passes."""
    grid = np.arange(lo, hi, GRID_S); ff = feats(fc_c, grid); sc = {k: np.sqrt(np.mean(v ** 2)) + 1e-9 for k, v in ff.items()}
    def cost(d):
        fm = feats(mo_c, grid + d); return sum(np.mean(((ff[k] - fm[k]) / sc[k]) ** 2) for k in use)
    g1 = np.arange(d0 - half, d0 + half, 0.01); c0 = g1[np.argmin([cost(d) for d in g1])]
    g2 = np.arange(c0 - 0.02, c0 + 0.02, 0.0005); c1 = g2[np.argmin([cost(d) for d in g2])]
    g3 = np.arange(c1 - 0.001, c1 + 0.001, 0.00005); cs = np.array([cost(d) for d in g3])
    return float(g3[np.argmin(cs)]), float(cs.min())


# ---------------------------------------------------------------------------------------------- frames
def fit_4dof(src, dst):
    """yaw + translation mapping src -> dst (both gravity-aligned, z up)."""
    cs, cd = src.mean(0), dst.mean(0); a, b = src[:, :2] - cs[:2], dst[:, :2] - cd[:2]
    yaw = math.atan2(np.sum(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]), np.sum(a[:, 0] * b[:, 0] + a[:, 1] * b[:, 1]))
    Rz = Rot.from_euler("z", yaw).as_matrix(); t = cd - Rz @ cs
    return yaw, t, Rz


def fit_se3(src, dst):
    cs, cd = src.mean(0), dst.mean(0); U, _, Vt = np.linalg.svd((src - cs).T @ (dst - cd))
    Dm = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]); R = Vt.T @ Dm @ U.T
    return R, cd - R @ cs


def ned_to_enu(p):
    return np.c_[p[:, 1], p[:, 0], -p[:, 2]]


# ---------------------------------------------------------------------------------------------- Pi <-> FC
def pi_fc_map(bag):
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY); P = []
    with Reader(bag) as r:
        for c, _, raw in r.messages(connections=[c for c in r.connections if c.topic == "/imu/time_ref"]):
            m = ts.deserialize_cdr(raw, c.msgtype)
            P.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.time_ref.sec + m.time_ref.nanosec * 1e-9))
    P = np.array(sorted(P)); off = P[:, 0] - P[:, 1]; t0 = P[0, 1]
    pts = []
    for a in np.arange(P[0, 1], P[-1, 1], 10.0):
        w = (P[:, 1] >= a) & (P[:, 1] < a + 10.0)
        if w.sum() > 100:
            pts.append((float(np.median(P[w, 1])), float(np.percentile(off[w], 1))))
    pts = np.array(pts); k, c = np.polyfit(pts[:, 0] - t0, pts[:, 1], 1)
    resid = pts[:, 1] - (k * (pts[:, 0] - t0) + c)
    return {"pi_minus_fc_at_start_s": float(c), "rate_ppm": float(k * 1e6), "window_resid_max_ms": float(1e3 * np.abs(resid).max()),
            "n_windows": int(len(pts)), "t0_fc_s": float(t0)}


# ---------------------------------------------------------------------------------------------- main alignment
def align(fc, mo, early, late, init_seg, use=("w",)):
    fc_c, mo_c = fc_raw_curves(fc), mocap_raw_curves(mo)
    gf = np.arange(fc["gyro"][0, 0], fc["gyro"][-1, 0], GRID_S); gm = np.arange(mo["t"][0], mo["t"][-1], GRID_S)
    d0 = takeoff_time(gm, feats(mo_c, gm)["vz"]) - takeoff_time(gf, feats(fc_c, gf)["vz"])   # coarse: the take-off climb
    o1, c1 = fit_offset(fc_c, mo_c, *early, d0, use=use); o2, c2 = fit_offset(fc_c, mo_c, *late, o1, use=use)
    t1, t2 = 0.5 * sum(early), 0.5 * sum(late)
    rate = (o2 - o1) / (t2 - t1)
    to_fc = lambda tm: tm - (o1 + rate * (tm - o1 - t1)) / (1 + rate)       # invert tm = tf + o1 + rate (tf - t1)
    res = {"clock": {"gyro_filter_delay_ms_compensated": 1e3 * gyro_group_delay_s(fc), "features": list(use), "coarse_takeoff_match_s": d0, "mocap_minus_fc_early_s": o1, "mocap_minus_fc_late_s": o2, "rate_ppm": rate * 1e6,
                     "fit_cost_early": c1, "fit_cost_late": c2, "windows_fc_s": [list(early), list(late)]}}
    tfc = to_fc(mo["t"]); est = fc["est"]
    p_est = ned_to_enu(est[:, 1:4])
    sel = (est[:, 0] >= init_seg[0]) & (est[:, 0] <= init_seg[1]) & (est[:, 0] >= tfc[0]) & (est[:, 0] <= tfc[-1])
    pm = np.c_[[np.interp(est[sel, 0], tfc, mo["p"][:, k]) for k in range(3)]].T
    yaw, t4, Rz = fit_4dof(pm, p_est[sel])
    res["frame_4dof_initial"] = {"yaw_deg": math.degrees(yaw), "t_m": t4.tolist(), "segment_fc_s": list(init_seg), "n": int(sel.sum())}
    allw = (est[:, 0] >= tfc[0]) & (est[:, 0] <= tfc[-1])
    pma = np.c_[[np.interp(est[allw, 0], tfc, mo["p"][:, k]) for k in range(3)]].T
    yaw_w, t_w, _ = fit_4dof(pma, p_est[allw])      # 4-DoF (not SE(3)): a straight flight leaves roll/pitch about its axis unobservable
    res["frame_4dof_whole_flight"] = {"yaw_deg": math.degrees(yaw_w), "t_m": t_w.tolist(),
                                      "note": "absorbs drift: use for evo -a style ATE only; drift metrics use the initial-segment fit"}
    mo_in_est = (Rz @ mo["p"].T).T + t4
    return res, tfc, mo_in_est, to_fc


def selftest(trial, out_dir, use=("w",)):
    """Synthetic mocap from SIM truth with a KNOWN clock offset/rate and frame; recover them."""
    path = os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin"); fc = read_fc(path, "XKF1"); s = fc["sim"]
    lat, lng = s[:, 1], s[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    U = s[:, 3] - s[0, 3]
    TRUE = {"offset_s": 3.4567, "rate_ppm": 80.0, "yaw_deg": 37.0, "t_m": [1.234, -2.345, 0.111]}
    Rf = Rot.from_euler("z", -TRUE["yaw_deg"], degrees=True).as_matrix()     # mocap = Rf (enu - t): inverse of the fit target
    p_enu = np.c_[E, N, U]; p_mo = (Rf @ (p_enu - np.array(TRUE["t_m"])).T).T
    rng = np.random.default_rng(0); p_mo += rng.normal(0, 0.0005, p_mo.shape)
    # body attitude: SIM roll/pitch/yaw (NED) -> a quaternion; the frame-independent |w| is all that is used for time
    q = Rot.from_euler("ZYX", np.c_[np.radians(s[:, 6]), np.radians(s[:, 5]), np.radians(s[:, 4])]).as_quat()
    t_mo = s[:, 0] + TRUE["offset_s"] + TRUE["rate_ppm"] * 1e-6 * (s[:, 0] - s[0, 0])
    mo = {"t": t_mo, "p": p_mo, "q": q}          # SIM is logged at only 10 Hz: this limits the self-test's time resolution
    arm = [t for t, st in fc["arm"] if st == 1][0]; land = fc["rfnd"][np.where(fc["rfnd"][:, 1] > 1.0)[0][-1], 0]
    res, tfc, mo_in_est, _ = align(fc, mo, (arm, arm + 25.0), (land - 20.0, land + 8.0), (arm, arm + 30.0), use=use)
    res["features_used"] = list(use)
    # recovered offset at the early window centre vs truth there
    t_e = 0.5 * (2 * arm + 25.0)
    true_off_e = TRUE["offset_s"] + TRUE["rate_ppm"] * 1e-6 * (t_e - s[0, 0])
    res["selftest"] = {"truth": TRUE, "offset_err_ms_early": 1e3 * (res["clock"]["mocap_minus_fc_early_s"] - true_off_e),
                       "rate_err_ppm": res["clock"]["rate_ppm"] - TRUE["rate_ppm"],
                       "yaw_err_deg": res["frame_4dof_initial"]["yaw_deg"] - TRUE["yaw_deg"]}
    est = fc["est"]; pe = ned_to_enu(est[:, 1:4]); w = (est[:, 0] >= arm) & (est[:, 0] <= arm + 30.0)
    pmi = np.c_[[np.interp(est[w, 0], tfc, mo_in_est[:, k]) for k in range(3)]].T
    res["selftest"]["initial_segment_pos_resid_rms_m"] = float(np.sqrt(np.mean(np.sum((pmi - pe[w]) ** 2, axis=1))))
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--bin"); ap.add_argument("--mocap"); ap.add_argument("--est", default="XKF1")
    ap.add_argument("--pi-bag"); ap.add_argument("--out-dir", default="mocap_align_out"); ap.add_argument("--selftest"); ap.add_argument("--features", default="w", help="w (|gyro|, default), vz (rangefinder vertical speed; latency unknown), or w,vz")
    ap.add_argument("--early", type=float, nargs=2); ap.add_argument("--late", type=float, nargs=2); ap.add_argument("--init-seg", type=float, nargs=2)
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    if a.selftest:
        res = selftest(a.selftest, a.out_dir, use=tuple(a.features.split(",")))
    else:
        fc = read_fc(a.bin, a.est); M = np.loadtxt(a.mocap, delimiter=",", comments="#")
        mo = {"t": M[:, 0], "p": M[:, 1:4], "q": M[:, 4:8]}
        arm = [t for t, st in fc["arm"] if st == 1][0]; land = fc["rfnd"][np.where(fc["rfnd"][:, 1] > 0.5)[0][-1], 0]
        early = tuple(a.early) if a.early else (arm, arm + 25.0); late = tuple(a.late) if a.late else (land - 20.0, land + 8.0)
        init = tuple(a.init_seg) if a.init_seg else (arm, arm + 30.0)
        res, tfc, mo_in_est, _ = align(fc, mo, early, late, init, use=tuple(a.features.split(",")))
        q = Rot.from_quat(mo["q"]); q4 = (Rot.from_euler("z", res["frame_4dof_initial"]["yaw_deg"], degrees=True) * q).as_quat()
        np.savetxt(f"{a.out_dir}/mocap_fc_clock_est_frame.tum", np.c_[tfc, mo_in_est, q4], fmt="%.6f")
        if a.pi_bag:
            res["pi_fc_clock"] = pi_fc_map(a.pi_bag)
    json.dump(res, open(f"{a.out_dir}/mocap_align.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
