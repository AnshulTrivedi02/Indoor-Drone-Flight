#!/usr/bin/env python3
"""Mocap alignment (real-flight plan, tooling item 4; rung-1 item R8): TIME and FRAME alignment of motion-capture ground
truth against the flight-controller (FC) dataflash log and the Pi's logs, reusing the simulation's clock-map approach
(eval/input_timing.clock_offset / clock_map: least squares on frame-independent motion features, fitted in an early and
a late window, giving a LINEAR map offset + rate).

Clocks:
  * FC: dataflash TimeUS (us since boot).
  * Pi: ROS header time. The Pi <-> FC map comes from /imu/time_ref pairs (header Pi time, time_ref = HIGHRES_IMU.time_usec
    FC time): the D25 lower envelope (1st percentile of Pi - FC per 10 s window, outlier-robust) and a linear fit across
    the windows (rate). Same idea as the FGO node's live map.
  * Mocap: the mocap host's stamps. Mocap <-> FC is fitted from motion features both see, independent of frames:
      - angular speed |w| (DEFAULT, the only feature used unless asked): from mocap orientation (quaternion differences)
        against |FC gyro|;
      - vertical speed (optional cross-check): d(mocap z)/dt against d(RFND distance)/dt. Its latency is unknown
        (sensor + link), so it is never used for the result by default.

FC GYRO SOURCE (R8, 2026-10-10): `--gyro-src RISI` (DEFAULT) uses the LOG_REPLAY `RISI` records, the 400 Hz INS delta
angles that EKF3 itself consumes:
  * RISI has no TimeUS. Each RISI record takes the TimeUS of the PRECEDING `RFRH` frame header (one clock, as in the
    converter spec, plan sec. 4.3 item 1). Only instance `--imu-instance` (default 0, the lane EKF3 core 0 uses) is read.
  * rate = (DAX, DAY, DAZ) / DADT (FRD; only |w| is used, so the axis convention does not matter).
  * STAMPING RULE: a delta covers the DADT seconds that END at the frame stamp, so it is stamped at its centre,
    TimeUS(RFRH) - DADT/2 (SITL: DADT = 2.0 ms inside 2.5 ms frames, i.e. -1.0 ms). Recorded in the JSON.
  * NO group-delay shift: RISI deltas are accumulated from the RAW gyro, before apply_gyro_filters
    (AP_InertialSensor_Backend.cpp:364-371). The old IMU path (`--gyro-src IMU`, ~25 Hz logged, INS_GYRO_FILTER
    2-pole low-pass) keeps its sqrt(2)/(2 pi fc) group-delay shift (11.3 ms at 20 Hz).

TIME FIT:
  1. coarse: cross-correlation of the standardised |w| over the whole overlap on a 20 ms grid (`--coarse xcorr`,
     default; robust to an epoch-sized mocap clock), or the take-off climb match (`--coarse takeoff`, the old rule), or a
     user value (`--coarse-offset`).
  2. fine: in each fit window (default since 2026-10-11, `resolve_windows`: the pre-arm and the post-disarm SYNC WIGGLES,
     found as the last / first burst of FC |w| > 2 rad/s before arming / after disarming, +-2 s; defaults are computed
     only for windows not given; a log with no ARM record needs --early/--late/--init-seg; grid points outside either
     record are masked, never interpolated as held end values), the offset minimising the squared difference of the two STANDARDISED (zero-mean, unit-RMS within the
     window) features, i.e. maximising their normalised correlation. Both features pass through the identical pipeline
     (interpolate to a common grid, differentiate where needed, boxcar). Grid search coarse -> fine -> finer.
  3. linear map: offset(t_fc) = o1 + rate * (t_fc - t1), least squares over the window offsets (exact for two windows;
     residuals reported for three or more). Inverse: t_fc = (t_mocap - o1 + rate * t1) / (1 + rate).
     (Corrected 2026-10-10: the previous inverse carried an extra rate*o1/(1+rate) term, invisible at the self-test's
     3.5 s offset but ~0.1 ms per second of offset, i.e. hours of error for an epoch-stamped mocap clock.)

Frame (after time alignment): mocap positions -> the estimator's navigation frame by a 4-DoF fit (yaw + 3-D translation;
both frames are gravity-aligned) on an initial segment (default: from arming to arming + 30 s), i.e. aligned at the
start so that later drift is NOT absorbed. Also reported: a whole-flight 4-DoF fit (absorbs drift).
Writes JSON (clock map with per-window residuals, transforms) and a TUM of mocap truth on the FC clock, in the
estimator frame (ENU of the estimator's NED).

Mocap input: CSV `t_s, x, y, z, qx, qy, qz, qw` (metres; scalar-last quaternion; the mocap's world frame, z UP), as
written by realflight/mocap/export (or any whitespace-separated TUM with the same columns).
Usage (~/venv-ardupilot: numpy + scipy + pymavlink):
  python3 eval/mocap_align.py --bin FLIGHT.bin --mocap mocap.csv [--est XKF1|XUKO|XUKF|XFGO] [--gyro-src RISI|IMU]
                              [--pi-bag BAG] --out-dir DIR
  python3 eval/mocap_align.py --selftest TRIAL --out-dir DIR   (synthetic mocap from a simulated flight's 10 Hz SIM truth)
  Validation (synthetic + SITL): eval/mocap_align_validate.py"""
import argparse, json, math, os, sys
import numpy as np
from scipy.signal import correlate, correlation_lags
from scipy.spatial.transform import Rotation as Rot
from pymavlink import mavutil


# ---------------------------------------------------------------------------------------------- FC log
def read_fc(path, est="XKF1", gyro_src="RISI", imu_instance=0):
    """Read the FC dataflash log. `gyro` is (t, gx, gy, gz) on the FC clock from RISI (see the module docstring for the
    stamping rule) or from IMU."""
    m = mavutil.mavlink_connection(path); G, R, A, E, S, S2, ARM, P = [], [], [], [], [], [], [], {}
    t_frame = None; dadt = []
    types = ["RFND", "ATT", est, "SIM", "SIM2", "ARM", "PARM"] + (["RFRH", "RISI"] if gyro_src == "RISI" else ["IMU"])
    while True:
        r = m.recv_match(type=types)
        if r is None:
            break
        ty = r.get_type()
        if ty == "RFRH":
            t_frame = r.TimeUS / 1e6; continue
        if ty == "RISI":
            if r.I == imu_instance and t_frame is not None and r.DADT > 0:
                G.append((t_frame - 0.5 * r.DADT, r.DAX / r.DADT, r.DAY / r.DADT, r.DAZ / r.DADT)); dadt.append(r.DADT)
            continue
        t = r.TimeUS / 1e6
        if ty == "IMU" and r.I == imu_instance: G.append((t, r.GyrX, r.GyrY, r.GyrZ))
        elif ty == "RFND" and r.Instance == 0: R.append((t, r.Dist))
        elif ty == "ATT": A.append((t, r.Roll, r.Pitch, r.Yaw))
        elif ty == est and (est != "XKF1" or r.C == 0): E.append((t, r.PN, r.PE, r.PD))
        elif ty == "SIM": S.append((t, r.Lat, r.Lng, r.Alt, r.Roll, r.Pitch, r.Yaw))
        elif ty == "SIM2": S2.append((t, r.PN, r.PE, r.PD))
        elif ty == "ARM": ARM.append((t, r.ArmState))
        elif ty == "PARM": P[r.Name] = r.Value
    if not G:
        raise SystemExit(f"no {gyro_src} gyro records (instance {imu_instance}) in {path}"
                         + (": is LOG_REPLAY set?" if gyro_src == "RISI" else ""))
    out = {k: np.array(v) for k, v in (("gyro", G), ("rfnd", R), ("att", A), ("est", E), ("sim", S), ("sim2", S2))}
    g = out["gyro"]; keep = np.r_[True, np.diff(g[:, 0]) > 0]       # monotonic stamps only
    out["gyro"] = g[keep]
    out |= {"arm": ARM, "params": P, "gyro_src": gyro_src, "imu_instance": imu_instance,
            "risi_dadt_median_s": float(np.median(dadt)) if dadt else None}
    return out


def load_mocap(path):
    """CSV (comma) or TUM (whitespace): t, x, y, z, qx, qy, qz, qw. Non-increasing stamps are dropped."""
    with open(path) as f:
        first = next(l for l in f if l.strip() and not l.startswith("#"))
    M = np.loadtxt(path, delimiter="," if "," in first else None, comments="#", ndmin=2)
    keep = np.r_[True, np.diff(M[:, 0]) > 0]
    M = M[keep]
    return {"t": M[:, 0], "p": M[:, 1:4], "q": M[:, 4:8]}


# ---------------------------------------------------------------------------------------------- features
def ang_speed_mocap(t, q):
    keep = np.r_[True, np.diff(t) > 0]; t, q = t[keep], q[keep]
    r = Rot.from_quat(q); d = (r[:-1].inv() * r[1:]).as_rotvec()
    return 0.5 * (t[1:] + t[:-1]), np.linalg.norm(d, axis=1) / np.diff(t)


SMOOTH_S, GRID_S = 0.1, 0.005          # identical boxcar (s) on a common grid (s) for BOTH clocks' features
COARSE_GRID_S = 0.02
PARAB_HALF_S = 0.004   # half-width of the parabola fit for the final sub-sample offset


def boxcar(x, smooth=None, grid=None):
    n = max(1, int(round((smooth or SMOOTH_S) / (grid or GRID_S)))); return np.convolve(x, np.ones(n) / n, "same")


def clean_rfnd(rf):
    """Drop rangefinder short returns (the D23 artefact): samples below 60% of the 1 s rolling median."""
    t, d = rf[:, 0], rf[:, 1]; keep = np.ones(len(d), bool)
    for i in range(len(d)):
        w = (t >= t[i] - 0.5) & (t <= t[i] + 0.5)
        if d[i] < 0.6 * np.median(d[w]): keep[i] = False
    return rf[keep]


def gyro_group_delay_s(fc):
    """Low-frequency group delay of ArduPilot's 2-pole (Butterworth) gyro low-pass, INS_GYRO_FILTER Hz:
    sqrt(2) / (2 pi fc). The logged IMU gyro lags the true motion by this much (20 Hz -> 11.3 ms).
    ZERO for RISI: its deltas are integrated from the raw gyro, before the filters."""
    if fc.get("gyro_src", "IMU") == "RISI":
        return 0.0
    f = float(fc["params"].get("INS_GYRO_FILTER", 0) or 0)
    return math.sqrt(2) / (2 * math.pi * f) if f > 0 else 0.0


def fc_raw_curves(fc):
    """FC features on the FC clock. The IMU gyro is shifted EARLIER by the INS filter's group delay, so the fitted offset
    maps clocks rather than absorbing the filter lag (zero for RISI)."""
    g = fc["gyro"]; dg = gyro_group_delay_s(fc)
    c = {"w": (g[:, 0] - dg, np.linalg.norm(g[:, 1:4], axis=1)), "gaps": find_gaps(g[:, 0] - dg),
         "span": (float(g[0, 0] - dg), float(g[-1, 0] - dg))}
    if len(fc.get("rfnd", [])):
        rf = clean_rfnd(fc["rfnd"]); c["z"] = (rf[:, 0], rf[:, 1])
    return c


def mocap_raw_curves(mo):
    tw, w = ang_speed_mocap(mo["t"], mo["q"])
    return {"w": (tw, w), "z": (mo["t"], mo["p"][:, 2]), "gaps": find_gaps(mo["t"]), "span": (float(mo["t"][0]), float(mo["t"][-1]))}


GAP_FACTOR = 3.0      # a sample spacing > GAP_FACTOR x the median spacing is a dropout


def find_gaps(t):
    """Dropout intervals [(t_before, t_after)]: spacing > GAP_FACTOR x median. Interpolating across them would invent
    motion, so grid points inside them (dilated by the boxcar half-width) are excluded from the time fit."""
    d = np.diff(t); i = np.where(d > GAP_FACTOR * np.median(d))[0]
    return np.c_[t[i], t[i + 1]] if len(i) else np.zeros((0, 2))


def valid_mask(curves, grid, smooth=None):
    pad = 0.5 * (smooth or SMOOTH_S) + 2 * GRID_S; ok = np.ones(len(grid), bool)
    for a, b in curves.get("gaps", ()):
        ok &= ~((grid >= a - pad) & (grid <= b + pad))
    if "span" in curves:        # outside a record np.interp holds the end value: flat fake data, never fitted (2026-10-11)
        ok &= (grid >= curves["span"][0] + pad) & (grid <= curves["span"][1] - pad)
    return ok


def feats(curves, grid, use=("w", "vz"), smooth=None, step=None):
    """|w| and vertical speed on `grid`, computed IDENTICALLY for either clock: interpolate, differentiate, boxcar."""
    out = {}
    if "w" in use:
        out["w"] = boxcar(np.interp(grid, *curves["w"]), smooth, step)
    if "vz" in use:
        out["vz"] = boxcar(np.gradient(np.interp(grid, *curves["z"]), step or GRID_S), smooth, step)
    return out


def standardise(x):
    s = np.std(x)
    return (x - np.mean(x)) / (s if s > 1e-12 else 1.0)


def takeoff_time(t, vz, thr=0.2, hold=1.0):
    """First time vz stays above thr for hold seconds (the take-off climb)."""
    up = vz > thr; dt = np.median(np.diff(t)); n = max(1, int(hold / dt))
    run = np.convolve(up.astype(int), np.ones(n, int), "valid")
    i = np.argmax(run >= n)
    return float(t[i])


def coarse_xcorr(fc_c, mo_c):
    """Whole-overlap cross-correlation of the standardised |w| on a COARSE_GRID_S grid. Returns (offset mocap - FC,
    peak ratio = best / best outside +-1 s of it; > ~1.5 means unambiguous)."""
    g = COARSE_GRID_S
    tf = np.arange(fc_c["w"][0][0], fc_c["w"][0][-1], g); tm = np.arange(mo_c["w"][0][0], mo_c["w"][0][-1], g)
    a = standardise(boxcar(np.interp(tf, *fc_c["w"]), 0.2, g)); b = standardise(boxcar(np.interp(tm, *mo_c["w"]), 0.2, g))
    c = correlate(a, b, "full", method="fft"); lags = correlation_lags(len(a), len(b), "full")
    k = int(np.argmax(c)); d = tm[0] - tf[0] - lags[k] * g
    far = np.abs(lags - lags[k]) * g > 1.0
    return float(d), float(c[k] / max(c[far].max(), 1e-9))


def fit_offset(fc_c, mo_c, lo, hi, d0, half=2.0, use=("w",), rate=0.0):
    """offset d (mocap clock - FC clock) maximising the normalised correlation of the standardised features over FC
    time [lo, hi], searched within d0 +- half; 10 ms, then 0.5 ms grids, then a parabola fit over +-4 ms. Returns (d, cost,
    correlation at d, fraction of the window used); dropouts on either side are masked. cost = mean over features of mean((std(f_fc) - std(f_mo(t + d)))^2) = 2 (1 - corr)."""
    grid = np.arange(lo, hi, GRID_S); ff = feats(fc_c, grid, use); okf = valid_mask(fc_c, grid)
    gm = grid + rate * (grid - 0.5 * (lo + hi))       # the in-window drift (from a previous pass), so d is AT the centre
    def cost(d):
        fm = feats(mo_c, gm + d, use); ok = okf & valid_mask(mo_c, gm + d)
        return float(np.mean([np.mean((standardise(ff[k][ok]) - standardise(fm[k][ok])) ** 2) for k in use]))
    g1 = np.arange(d0 - half, d0 + half, 0.01); c0 = g1[np.argmin([cost(d) for d in g1])]
    g2 = np.arange(c0 - 0.02, c0 + 0.02, 0.0005); c1 = g2[np.argmin([cost(d) for d in g2])]
    # final: a least-squares parabola through the cost over c1 +- PARAB_HALF_S (0.25 ms steps). Taking the argmin of a
    # finer grid instead lets sub-ms noise bumps in the cost pick a local minimum (synthetic: up to 1.4 ms).
    g3 = c1 + np.arange(-PARAB_HALF_S, PARAB_HALF_S + 1e-9, 0.00025); cs = np.array([cost(d) for d in g3])
    a2, a1, _ = np.polyfit(g3 - c1, cs, 2)
    v = -a1 / (2 * a2) if a2 > 0 else np.inf
    best = float(c1 + v) if abs(v) <= PARAB_HALF_S else float(g3[np.argmin(cs)])
    cmin = float(cost(best))
    frac = float((okf & valid_mask(mo_c, gm + best)).mean())
    return best, cmin, 1.0 - cmin / 2.0, frac


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
    return pi_fc_map_pairs(np.array(sorted(P)))


def pi_fc_map_pairs(P, win=10.0):
    """P = (header/Pi time, FC time) pairs. Lower envelope (1st percentile of Pi - FC per `win` s) + linear fit."""
    off = P[:, 0] - P[:, 1]; t0 = P[0, 1]
    pts = []
    for a in np.arange(P[0, 1], P[-1, 1], win):
        w = (P[:, 1] >= a) & (P[:, 1] < a + win)
        if w.sum() > 100:
            pts.append((float(np.median(P[w, 1])), float(np.percentile(off[w], 1))))
    pts = np.array(pts); k, c = np.polyfit(pts[:, 0] - t0, pts[:, 1], 1)
    resid = pts[:, 1] - (k * (pts[:, 0] - t0) + c)
    return {"pi_minus_fc_at_start_s": float(c), "rate_ppm": float(k * 1e6), "window_resid_max_ms": float(1e3 * np.abs(resid).max()),
            "n_windows": int(len(pts)), "t0_fc_s": float(t0)}


# ---------------------------------------------------------------------------------------------- main alignment
def clock_fit(fc, mo, windows, use=("w",), coarse="xcorr", coarse_offset=None):
    """Fit the linear clock map mocap <- FC over the given FC-clock windows. Returns (result dict, to_fc)."""
    fc_c, mo_c = fc_raw_curves(fc), mocap_raw_curves(mo)
    info = {}
    if coarse_offset is not None:
        d0 = float(coarse_offset); info["coarse"] = {"rule": "given", "offset_s": d0}
    elif coarse == "takeoff":
        gf = np.arange(fc_c["z"][0][0], fc_c["z"][0][-1], GRID_S); gm = np.arange(mo["t"][0], mo["t"][-1], GRID_S)
        d0 = takeoff_time(gm, feats(mo_c, gm, ("vz",))["vz"]) - takeoff_time(gf, feats(fc_c, gf, ("vz",))["vz"])
        info["coarse"] = {"rule": "takeoff", "offset_s": d0}
    else:
        d0, pr = coarse_xcorr(fc_c, mo_c); info["coarse"] = {"rule": "xcorr", "offset_s": d0, "peak_ratio": pr}
    # pass 1 without drift; pass 2 (and 3) re-fit each window with the drift found, so each offset belongs to its
    # window CENTRE rather than to wherever the motion energy sits inside the window (a 150 ppm drift over a 25 s
    # window otherwise biases each offset by up to ~2 ms).
    rate, prev, starts = 0.0, d0, None
    for it in range(3):
        fits = []
        for j, (lo, hi) in enumerate(windows):
            if starts is None:
                o, c, rho, frac = fit_offset(fc_c, mo_c, lo, hi, prev, use=use); prev = o
            else:
                o, c, rho, frac = fit_offset(fc_c, mo_c, lo, hi, starts[j], half=0.05, use=use, rate=rate)
            fits.append({"window_fc_s": [lo, hi], "t_centre_fc_s": 0.5 * (lo + hi), "mocap_minus_fc_s": o, "cost": c,
                         "corr": rho, "valid_fraction": frac})
        tc = np.array([f["t_centre_fc_s"] for f in fits]); oc = np.array([f["mocap_minus_fc_s"] for f in fits])
        t1 = float(tc[0])
        if len(fits) >= 2:
            rate, o1 = np.polyfit(tc - t1, oc, 1)
        else:
            rate, o1 = 0.0, float(oc[0])
        starts = list(oc)
        if len(fits) < 2:
            break
    for f in fits:
        f["resid_ms"] = 1e3 * (f["mocap_minus_fc_s"] - (o1 + rate * (f["t_centre_fc_s"] - t1)))
    o1, rate = float(o1), float(rate)
    to_fc = lambda tm: (tm - o1 + rate * t1) / (1.0 + rate)        # inverse of tm = tf + o1 + rate (tf - t1)
    res = {"gyro_src": fc.get("gyro_src", "IMU"), "imu_instance": fc.get("imu_instance", 0),
           "risi_stamp_rule": "TimeUS(preceding RFRH) - DADT/2" if fc.get("gyro_src") == "RISI" else None,
           "risi_dadt_median_s": fc.get("risi_dadt_median_s"),
           "gyro_filter_delay_ms_compensated": 1e3 * gyro_group_delay_s(fc), "features": list(use),
           "smooth_s": SMOOTH_S, "grid_s": GRID_S, **info, "windows": fits,
           "map": {"form": "t_mocap = t_fc + o1 + rate (t_fc - t1)", "o1_s": o1, "t1_fc_s": t1, "rate_ppm": rate * 1e6},
           # kept for compatibility with the earlier JSON
           "mocap_minus_fc_early_s": fits[0]["mocap_minus_fc_s"], "mocap_minus_fc_late_s": fits[-1]["mocap_minus_fc_s"],
           "rate_ppm": rate * 1e6}
    return res, to_fc


def align(fc, mo, early, late, init_seg, use=("w",), coarse="xcorr", coarse_offset=None, extra_windows=()):
    windows = [tuple(early)] + [tuple(w) for w in extra_windows] + [tuple(late)]
    clk, to_fc = clock_fit(fc, mo, windows, use, coarse, coarse_offset)
    res = {"clock": clk}
    tfc = to_fc(mo["t"]); est = fc["est"]
    if len(est):
        p_est = ned_to_enu(est[:, 1:4])
        sel = (est[:, 0] >= init_seg[0]) & (est[:, 0] <= init_seg[1]) & (est[:, 0] >= tfc[0]) & (est[:, 0] <= tfc[-1])
        pm = np.c_[[np.interp(est[sel, 0], tfc, mo["p"][:, k]) for k in range(3)]].T
        yaw, t4, Rz = fit_4dof(pm, p_est[sel])
        res["frame_4dof_initial"] = {"yaw_deg": math.degrees(yaw), "t_m": t4.tolist(), "segment_fc_s": list(init_seg), "n": int(sel.sum())}
        allw = (est[:, 0] >= tfc[0]) & (est[:, 0] <= tfc[-1])
        pma = np.c_[[np.interp(est[allw, 0], tfc, mo["p"][:, k]) for k in range(3)]].T
        yaw_w, t_w, _ = fit_4dof(pma, p_est[allw])  # 4-DoF (not SE(3)): a straight flight leaves roll/pitch about its axis unobservable
        res["frame_4dof_whole_flight"] = {"yaw_deg": math.degrees(yaw_w), "t_m": t_w.tolist(),
                                          "note": "absorbs drift: use for evo -a style ATE only; drift metrics use the initial-segment fit"}
    else:
        Rz, t4 = np.eye(3), np.zeros(3)
        res["frame_4dof_initial"] = {"yaw_deg": 0.0, "t_m": [0.0, 0.0, 0.0], "note": "no estimator records: frame left as mocap"}
    mo_in_est = (Rz @ mo["p"].T).T + t4
    return res, tfc, mo_in_est, to_fc


SYNC_W_THR = 2.0        # rad/s: a sync wiggle (flight cards D6: RISI rates > 2 rad/s while disarmed)
SYNC_MERGE_S = 1.0      # samples above the threshold closer than this belong to one burst
SYNC_MIN_S = 1.0        # a burst shorter than this is not a wiggle (a set-down knock)
SYNC_PAD_S = 2.0        # the fit window extends the burst by this much on each side


def sync_bursts(fc, thr=SYNC_W_THR, merge_s=SYNC_MERGE_S, min_s=SYNC_MIN_S):
    """Bursts of FC |w| (0.1 s boxcar on the gyro samples) above thr, as [(start, end)] on the FC clock."""
    g = fc["gyro"]; t = g[:, 0]; w = np.linalg.norm(g[:, 1:4], axis=1)
    n = max(1, int(round(0.1 / max(float(np.median(np.diff(t))), 1e-4)))); ws = np.convolve(w, np.ones(n) / n, "same")
    hi = t[ws > thr]
    if not len(hi):
        return []
    cut = np.where(np.diff(hi) > merge_s)[0]
    starts, ends = np.r_[hi[0], hi[cut + 1]], np.r_[hi[cut], hi[-1]]
    return [(float(a), float(b)) for a, b in zip(starts, ends) if b - a >= min_s]


def default_windows(fc, pad=SYNC_PAD_S, init_len=30.0, thr=SYNC_W_THR):
    """The rung-1 default fit windows (2026-10-11; flight cards D6/D8, pre-registration sec. 8):
      early = the LAST |w| burst ending before the first arming, +-pad (the pre-arm, disarmed sync wiggle);
      late  = the FIRST |w| burst starting after the last disarming, +-pad (the post-disarm sync wiggle);
      init  = (arm, arm + init_len) (the initial frame-fit segment).
    Each is None when it cannot be found. NO ARM record (a disarmed hand-carry log): SystemExit asking for explicit
    windows. (The old arm-anchored rule, kept as legacy_windows for SITL logs without wiggles, started the early window
    AT arming and so missed the pre-arm wiggle.)"""
    arms = [t for t, st in fc["arm"] if st == 1]
    if not arms:
        raise SystemExit("mocap_align: the log has no ARM record (ArmState 1), e.g. a disarmed hand-carry log. Give the "
                         "windows explicitly on the FC clock (s): --early T0 T1 and --late T0 T1 (the two sync-wiggle "
                         "periods) and --init-seg T0 T1 (the initial frame-fit segment).")
    arm = arms[0]; dis = [t for t, st in fc["arm"] if st == 0 and t > arm]; disarm = dis[-1] if dis else None
    b = sync_bursts(fc, thr)
    pre = [x for x in b if x[1] <= arm]; post = [x for x in b if disarm is not None and x[0] >= disarm]
    early = (pre[-1][0] - pad, pre[-1][1] + pad) if pre else None
    late = (post[0][0] - pad, post[0][1] + pad) if post else None
    return early, late, (arm, arm + init_len)


def resolve_windows(fc, early=None, late=None, init=None):
    """Defaults ONLY for the missing arguments (an explicit window is never replaced, and a log with no ARM record
    works when all three are given). Returns (early, late, init, sources)."""
    src = {"early": "given", "late": "given", "init_seg": "given"}
    if early is not None and late is not None and init is not None:
        return tuple(early), tuple(late), tuple(init), src
    e0, l0, i0 = default_windows(fc)
    missing = []
    if early is None:
        early, src["early"] = e0, "default: last |w| burst before arming"
        if e0 is None: missing.append("--early (no |w| burst > %.1f rad/s before arming)" % SYNC_W_THR)
    if late is None:
        late, src["late"] = l0, "default: first |w| burst after disarming"
        if l0 is None: missing.append("--late (no disarm record, or no |w| burst > %.1f rad/s after it)" % SYNC_W_THR)
    if init is None:
        init, src["init_seg"] = i0, "default: arm to arm + 30 s"
    if missing:
        raise SystemExit("mocap_align: cannot find the default window(s); give them explicitly: " + "; ".join(missing))
    return tuple(early), tuple(late), tuple(init), src


def legacy_windows(fc, early_len=25.0, late_before=20.0, late_after=8.0, min_dist=0.5):
    """The pre-2026-10-11 arm-anchored windows, for SITL logs WITHOUT sync wiggles (selftest, mocap_align_validate's
    SITL check; their stored results in eval/results/r1_mocap_sync/ used this rule). Not for real flights."""
    arms = [t for t, st in fc["arm"] if st == 1]
    rf = fc.get("rfnd", np.zeros((0, 2)))
    hi = np.where(rf[:, 1] > min_dist)[0] if len(rf) else []
    if not arms or not len(hi):
        raise SystemExit("legacy_windows needs an ARM record and a rangefinder reading above %.2f m" % min_dist)
    arm = arms[0]; land = rf[hi[-1], 0]
    return (arm, arm + early_len), (land - late_before, land + late_after), (arm, arm + 30.0)


def selftest(trial, out_dir, use=("w",), gyro_src="RISI"):
    """Synthetic mocap from SIM truth (10 Hz) with a KNOWN clock offset/rate and frame; recover them."""
    path = os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin"); fc = read_fc(path, "XKF1", gyro_src); s = fc["sim"]
    lat, lng = s[:, 1], s[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    U = s[:, 3] - s[0, 3]
    TRUE = {"offset_s": 3.4567, "rate_ppm": 80.0, "yaw_deg": 37.0, "t_m": [1.234, -2.345, 0.111]}
    Rf = Rot.from_euler("z", -TRUE["yaw_deg"], degrees=True).as_matrix()     # mocap = Rf (enu - t): inverse of the fit target
    p_enu = np.c_[E, N, U]; p_mo = (Rf @ (p_enu - np.array(TRUE["t_m"])).T).T
    rng = np.random.default_rng(0); p_mo += rng.normal(0, 0.0005, p_mo.shape)
    q = Rot.from_euler("ZYX", np.c_[np.radians(s[:, 6]), np.radians(s[:, 5]), np.radians(s[:, 4])]).as_quat()
    t_mo = s[:, 0] + TRUE["offset_s"] + TRUE["rate_ppm"] * 1e-6 * (s[:, 0] - s[0, 0])
    mo = {"t": t_mo, "p": p_mo, "q": q}          # SIM is logged at only 10 Hz: this limits the self-test's time resolution
    early, late, init = legacy_windows(fc, min_dist=1.0)       # SITL log: no sync wiggles
    res, tfc, mo_in_est, _ = align(fc, mo, early, late, init, use=use)
    res["features_used"] = list(use)
    t_e = 0.5 * (early[0] + early[1])
    true_off_e = TRUE["offset_s"] + TRUE["rate_ppm"] * 1e-6 * (t_e - s[0, 0])
    res["selftest"] = {"truth": TRUE, "offset_err_ms_early": 1e3 * (res["clock"]["mocap_minus_fc_early_s"] - true_off_e),
                       "rate_err_ppm": res["clock"]["rate_ppm"] - TRUE["rate_ppm"],
                       "yaw_err_deg": res["frame_4dof_initial"]["yaw_deg"] - TRUE["yaw_deg"]}
    est = fc["est"]; pe = ned_to_enu(est[:, 1:4]); w = (est[:, 0] >= init[0]) & (est[:, 0] <= init[1])
    pmi = np.c_[[np.interp(est[w, 0], tfc, mo_in_est[:, k]) for k in range(3)]].T
    res["selftest"]["initial_segment_pos_resid_rms_m"] = float(np.sqrt(np.mean(np.sum((pmi - pe[w]) ** 2, axis=1))))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--bin"); ap.add_argument("--mocap"); ap.add_argument("--est", default="XKF1")
    ap.add_argument("--gyro-src", default="RISI", choices=["RISI", "IMU"]); ap.add_argument("--imu-instance", type=int, default=0)
    ap.add_argument("--pi-bag"); ap.add_argument("--out-dir", required=True); ap.add_argument("--selftest")
    ap.add_argument("--features", default="w", help="w (|gyro|, default), vz (rangefinder vertical speed; latency unknown), or w,vz")
    ap.add_argument("--coarse", default="xcorr", choices=["xcorr", "takeoff"]); ap.add_argument("--coarse-offset", type=float)
    ap.add_argument("--early", type=float, nargs=2); ap.add_argument("--late", type=float, nargs=2); ap.add_argument("--init-seg", type=float, nargs=2)
    a = ap.parse_args(argv); os.makedirs(a.out_dir, exist_ok=True)
    use = tuple(a.features.split(","))
    if a.selftest:
        res = selftest(a.selftest, a.out_dir, use=use, gyro_src=a.gyro_src)
    else:
        fc = read_fc(a.bin, a.est, a.gyro_src, a.imu_instance); mo = load_mocap(a.mocap)
        early, late, init, wsrc = resolve_windows(fc, a.early, a.late, a.init_seg)
        res, tfc, mo_in_est, _ = align(fc, mo, early, late, init, use=use, coarse=a.coarse, coarse_offset=a.coarse_offset)
        res["window_sources"] = wsrc
        q = Rot.from_quat(mo["q"]); q4 = (Rot.from_euler("z", res["frame_4dof_initial"]["yaw_deg"], degrees=True) * q).as_quat()
        np.savetxt(f"{a.out_dir}/mocap_fc_clock_est_frame.tum", np.c_[tfc, mo_in_est, q4], fmt="%.6f")
        res["inputs"] = {"bin": os.path.abspath(a.bin), "mocap": os.path.abspath(a.mocap), "est": a.est}
        if a.pi_bag:
            res["pi_fc_clock"] = pi_fc_map(a.pi_bag)
    json.dump(res, open(f"{a.out_dir}/mocap_align.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
