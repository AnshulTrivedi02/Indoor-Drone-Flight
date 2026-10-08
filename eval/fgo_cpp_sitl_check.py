#!/usr/bin/env python3
"""SITL checks of the live FGO node (C++ fgo_cpp_node, or fgo_node.py), PRE-REGISTERED in docs/fgo_cpp_port.md
"Pre-registration 4" (committed before any C++-node SITL data existed).

  score TRIAL [--root DIR] [--scratch DIR] [--json OUT] [--replay-pair BIN_DIR] [--keep-scratch]
  decide --i J --ii J --iii J --a3 J [--json OUT]       (J = the score JSONs of flights (i), (ii), (iii) and a3)

score, per trial (read-only on the trial directory):
 config  void unless PARM AHRS_EKF_TYPE 10, AHRS_FGO_ENABLE 1, SERIAL3_PROTOCOL 2 (and, for the C++ node, the stats
         JSON echoes metadata.yaml's fgo_cpp line)
 a.      FC state age (dataflash XFGO 25 Hz: Age = now - t_valid, OV; XFGI per received state: arrival TimeUS, Tv)
         over W_a = [max(first ARM, first XFGI), min(first disarm after it, last XFGI)]: Age median/p95/p99/max,
         fraction Age > 250 ms, fraction OV = 0, longest OV = 0 span, arrival latency (TimeUS - Tv)
         median/p95/p99/max, largest gap between arrivals, Late count
 b.      the node's states (/fgo/pose in the bag; else fgo_node_stats.f64; fgo_node.py: fgo_node_stats.npz traj)
         against /ground_truth/pose. PRIMARY delta_att: the shift d in -200..+200 ms (0.5 ms grid) minimising the RMS
         of [roll_f(t_k) - roll_gt(t_k - d) - c_r, pitch_f(t_k) - pitch_gt(t_k - d) - c_p] (offsets fitted per d)
         over the airborne period (GT height > 0.5 m); d > 0 = states lag truth; on the grid edge = "not identified".
         Secondary (report only): roll/pitch RMS at d = 0; with the fixed spawn mapping (corridor x = world +Y,
         y = world -X, yaw + 90 deg; no alignment) over the airborne period and the cruise (longest run of GT
         horizontal speed > 0.3 m/s): horizontal error RMS/max/end, height RMS, yaw mean/RMS/max, relative
         horizontal error per metre over the cruise.
         --replay-pair BIN_DIR: the trial's own bag through BIN_DIR/fgo_cpp_live_replay in both imu_stamp modes
         (delay 0.10 s; the live node's t_armed_header as a HEARTBEAT row, else arm_source none), scored the same way.
 node    the C++ node's stats JSON (max_lateness_s, n_out_of_order, ...) and step / queue-lag percentiles.
decide applies Rule A (flight (i): max Age > 250 ms -> 0.10 s) and Rule B (R = max(5 ms, |d(iii) - d(a3)|); the
smaller |d| of (ii)/(iii) wins if they differ by >= R, else "indistinguishable at this resolution; keep time_ref").

A packed bag (bag_0.db3.zst) is decompressed to a COPY under --scratch (sha256 checked against PACKED.txt) and the copy
is removed at the end unless --keep-scratch. Run the whole `score` step through
src/estimators/fgo_cpp/tools/heavy.py (it decompresses and, with --replay-pair, runs replays; it does not call heavy.py
itself). Python: ~/venv-fgo (rosbags + pymavlink + numpy)."""
import argparse, glob, hashlib, json, math, os, shutil, subprocess, sys, tempfile
import numpy as np

AGE_MAX_MS = 250.0
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.environ.get("FGO_CPP_TOOLS", os.path.join(HERE, "..", "src", "estimators", "fgo_cpp", "tools"))
pct = lambda x, q: float(np.percentile(x, q)) if len(x) else None


# ---------------------------------------------------------------- helpers
def rp_from_R(R):            # R (n, 3, 3) body FLU -> nav (z up); ZYX Euler
    return np.arctan2(R[:, 2, 1], R[:, 2, 2]), -np.arcsin(np.clip(R[:, 2, 0], -1, 1)), np.arctan2(R[:, 1, 0], R[:, 0, 0])


def rpy_from_q(w, x, y, z):
    return (np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)), np.arcsin(np.clip(2 * (w * y - z * x), -1, 1)),
            np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def bag_dir_readable(D, scratch, notes):
    """The trial's bag directory, or a scratch copy of a packed one (sha256 checked). Returns (dir, scratch_copy|None)."""
    b = os.path.join(D, "bag")
    if glob.glob(os.path.join(b, "*.db3")):
        return b, None
    z = sorted(glob.glob(os.path.join(b, "*.db3.zst")))
    if not z:
        notes.append("no bag found"); return None, None
    dst = os.path.join(scratch, os.path.basename(D.rstrip("/")) + "_bag")
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(b, "metadata.yaml"), dst)
    out = os.path.join(dst, os.path.basename(z[0])[:-4])
    subprocess.run(["zstd", "-q", "-f", "-d", z[0], "-o", out], check=True)
    want = next((l.split()[1] for l in open(os.path.join(b, "PACKED.txt")) if l.startswith("sha256")), None)
    h = hashlib.sha256()
    with open(out, "rb") as f:
        for blk in iter(lambda: f.read(1 << 24), b""):
            h.update(blk)
    if want != h.hexdigest():
        raise SystemExit(f"sha256 mismatch on the scratch copy of {z[0]}")
    notes.append(f"packed bag decompressed to scratch copy {dst} (sha256 verified)")
    return dst, dst


def read_bag(bagdir):
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
    F, G = [], []
    with Reader(bagdir) as r:
        conns = {c.topic: c for c in r.connections}
        want = [t for t in ("/fgo/pose", "/ground_truth/pose") if t in conns]
        for con, _, raw in r.messages(connections=[conns[t] for t in want]):
            m = ts.deserialize_cdr(raw, con.msgtype); p, q = m.pose.position, m.pose.orientation
            (F if con.topic == "/fgo/pose" else G).append((st(m.header), p.x, p.y, p.z, q.w, q.x, q.y, q.z))
    conv = lambda A: (np.c_[A[:, :4], np.column_stack(rpy_from_q(A[:, 4], A[:, 5], A[:, 6], A[:, 7]))]
                      if len(A) else np.zeros((0, 7)))
    F = conv(np.array(sorted(F), float).reshape(-1, 8)); G = conv(np.array(sorted(G), float).reshape(-1, 8))
    return F, G          # rows: t, x, y, z, roll, pitch, yaw


# ---------------------------------------------------------------- check a
def check_a(D):
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(os.path.join(D, "ardupilot.bin"))
    P, ARM, O, I = {}, [], [], []
    while True:
        r = m.recv_match(type=["PARM", "ARM", "XFGO", "XFGI"])
        if r is None:
            break
        t = r.get_type(); ts = getattr(r, "TimeUS", 0) / 1e6
        if t == "PARM": P[r.Name] = r.Value
        elif t == "ARM": ARM.append((ts, r.ArmState))
        elif t == "XFGO": O.append((ts, r.OV, r.Age))
        elif t == "XFGI": I.append((ts, r.Tv / 1e3, r.V, r.Late))
    O, I = np.array(O, float).reshape(-1, 3), np.array(I, float).reshape(-1, 4)
    cfg = {k: P.get(k) for k in ("AHRS_EKF_TYPE", "AHRS_FGO_ENABLE", "SERIAL3_PROTOCOL")}
    res = {"params": cfg, "params_ok": cfg == {"AHRS_EKF_TYPE": 10.0, "AHRS_FGO_ENABLE": 1.0, "SERIAL3_PROTOCOL": 2.0}}
    arms = [t for t, s in ARM if s == 1]
    if not arms or not len(I) or not len(O):
        res["error"] = "no ARM, XFGI or XFGO"; return res
    t0 = max(arms[0], I[0, 0])
    dis = [t for t, s in ARM if s == 0 and t > t0]
    t1 = min(dis[0] if dis else np.inf, I[-1, 0])
    res["W_a_s"] = [t0, t1]
    w = (O[:, 0] >= t0) & (O[:, 0] <= t1)
    age = O[w, 2]
    inv = O[w, 1] == 0
    longest = 0.0
    if inv.any():
        tw = O[w, 0]; idx = np.flatnonzero(inv); br = np.flatnonzero(np.diff(idx) > 1)
        starts, ends = np.r_[idx[0], idx[br + 1]], np.r_[idx[br], idx[-1]]
        spans = [(float(tw[s]), float(tw[e])) for s, e in zip(starts, ends)]
        longest = max(e - s + 0.04 for s, e in spans)            # one XFGO period added per span
        res["invalid_spans_s_first20"] = [[round(s, 2), round(e, 2)] for s, e in spans[:20]]
    res["age_ms"] = {"n_xfgo": int(w.sum()), "median": pct(age, 50), "p95": pct(age, 95), "p99": pct(age, 99),
                     "max": float(age.max()) if len(age) else None,
                     "frac_over_250ms": float(np.mean(age > AGE_MAX_MS)) if len(age) else None,
                     "frac_output_invalid_OV0": float(np.mean(inv)) if len(inv) else None,
                     "longest_OV0_span_s": longest}
    wi = (I[:, 0] >= t0) & (I[:, 0] <= t1)
    lat = 1e3 * (I[wi, 0] - I[wi, 1]); gaps = 1e3 * np.diff(I[wi, 0])
    res["arrival"] = {"n_states": int(wi.sum()), "latency_ms_median": pct(lat, 50), "latency_ms_p95": pct(lat, 95),
                      "latency_ms_p99": pct(lat, 99), "latency_ms_max": float(lat.max()) if len(lat) else None,
                      "max_gap_between_states_ms": float(gaps.max()) if len(gaps) else None,
                      "frac_node_valid_flag0": float(np.mean(I[wi, 2] == 0)) if wi.any() else None,
                      "late_count_end": int(I[-1, 3])}
    return res


# ---------------------------------------------------------------- check b
def fit_delta(F, G, half=True):
    """F, G rows (t, x, y, z, roll, pitch, yaw). Airborne = GT height > 0.5 m at t_k."""
    tk = F[:, 0]
    ok = (tk >= G[0, 0] + 0.25) & (tk <= G[-1, 0] - 0.25) & (np.interp(tk, G[:, 0], G[:, 3]) > 0.5)
    if ok.sum() < 100:
        return {"error": "fewer than 100 airborne states"}
    t = tk[ok]; rf, pf = F[ok, 4], F[ok, 5]
    grid = np.arange(-0.200, 0.2000001, 0.0005)
    rms = np.empty(len(grid))
    for i, d in enumerate(grid):
        er = rf - np.interp(t - d, G[:, 0], G[:, 4]); ep = pf - np.interp(t - d, G[:, 0], G[:, 5])
        er -= er.mean(); ep -= ep.mean()
        rms[i] = math.sqrt(np.mean(np.r_[er, ep] ** 2))
    i = int(np.argmin(rms)); i0 = int(np.argmin(np.abs(grid)))
    er0 = rf - np.interp(t, G[:, 0], G[:, 4]); ep0 = pf - np.interp(t, G[:, 0], G[:, 5])
    out = {"delta_att_ms": None if i in (0, len(grid) - 1) else round(1e3 * grid[i], 1),
           "identified": i not in (0, len(grid) - 1), "grid_argmin_ms": round(1e3 * grid[i], 1),
           "rms_at_delta_deg": math.degrees(rms[i]), "rms_at_0_deg": math.degrees(rms[i0]),
           "offsets_deg_at_0": [math.degrees(er0.mean()), math.degrees(ep0.mean())],
           "n_states": int(ok.sum()), "t_s": [float(t[0]), float(t[-1])]}
    # diagnostics (report only, added after the pre-registration; they change no rule): curve depth at +-20 ms
    # and the same fit on each half of the airborne states (how well the minimum is located)
    j20 = [int(np.argmin(np.abs(grid - grid[i] - s))) for s in (-0.020, 0.020)]
    out["diag_rms_rise_at_pm20ms_deg"] = [math.degrees(rms[j] - rms[i]) for j in j20]
    if half:
        h = len(t) // 2
        out["diag_delta_halves_ms"] = [fit_delta(F[np.flatnonzero(ok)[s]], G, half=False).get("grid_argmin_ms")
                                       for s in (slice(0, h), slice(h, None))]
    return out


def secondary(F, G, frame="corridor"):
    if frame == "corridor":                         # nav (x fwd, y left) -> world ENU: x_w = -y_n, y_w = x_n
        Wx, Wy, Wyaw = -F[:, 2], F[:, 1], F[:, 6] + math.pi / 2
    else:
        Wx, Wy, Wyaw = F[:, 1], F[:, 2], F[:, 6]
    tk = F[:, 0]; ok = (tk >= G[0, 0]) & (tk <= G[-1, 0])
    gx, gy, gz = (np.interp(tk, G[:, 0], G[:, j]) for j in (1, 2, 3))
    gyaw = np.interp(tk, G[:, 0], np.unwrap(G[:, 6]))
    groll, gpitch = (np.interp(tk, G[:, 0], G[:, j]) for j in (4, 5))
    eh = np.hypot(Wx - gx, Wy - gy); ez = F[:, 3] - gz
    ey = np.degrees(wrap(Wyaw - gyaw)); er = np.degrees(F[:, 4] - groll); ep = np.degrees(F[:, 5] - gpitch)
    sp = np.hypot(np.gradient(gx), np.gradient(gy)) / np.maximum(np.gradient(tk), 1e-6)
    sp = np.convolve(sp, np.ones(25) / 25, mode="same")
    cr = ok & (sp > 0.3); bi = bj = 0; i = 0
    while i < len(cr):
        if cr[i]:
            j = i
            while j < len(cr) and cr[j]: j += 1
            if j - i > bj - bi: bi, bj = i, j
            i = j
        else:
            i += 1
    ix = np.arange(len(tk)); res = {}
    for nm, wv in {"airborne": ok & (gz > 0.5), "cruise": (ix >= bi) & (ix < bj)}.items():
        if not wv.any():
            continue
        d = {"t_s": [float(tk[wv][0]), float(tk[wv][-1])], "n": int(wv.sum()),
             "roll_rms_deg": float(np.sqrt(np.mean(er[wv] ** 2))), "pitch_rms_deg": float(np.sqrt(np.mean(ep[wv] ** 2))),
             "horiz_rms_m": float(np.sqrt(np.mean(eh[wv] ** 2))), "horiz_max_m": float(eh[wv].max()),
             "horiz_end_m": float(eh[wv][-1]), "height_rms_m": float(np.sqrt(np.mean(ez[wv] ** 2))),
             "yaw_mean_deg": float(ey[wv].mean()), "yaw_rms_deg": float(np.sqrt(np.mean(ey[wv] ** 2))),
             "yaw_max_abs_deg": float(np.abs(ey[wv]).max())}
        if nm == "cruise":
            k0, k1 = np.flatnonzero(wv)[[0, -1]]
            travel = float(np.hypot(gx[k1] - gx[k0], gy[k1] - gy[k0]))
            dE = float(np.hypot((Wx[k1] - Wx[k0]) - (gx[k1] - gx[k0]), (Wy[k1] - Wy[k0]) - (gy[k1] - gy[k0])))
            d.update({"travel_m": travel, "relative_horiz_err_end_m": dE, "relative_err_per_m": dE / travel if travel > 0 else None})
        res[nm] = d
    return res


def kf_states(prefix):
    K = np.fromfile(prefix + ".kf.f64").reshape(-1, 40)
    R = K[:, 13:22].reshape(-1, 3, 3); r, p, y = rp_from_R(R)
    return np.c_[K[:, 1], K[:, 10:13], r, p, y]


def replay_pair(bagdir, D, bindir, scratch):
    out = {}
    js = os.path.join(D, "fgo_node_stats.json")
    t_arm = json.load(open(js)).get("t_armed_header", -1.0) if os.path.exists(js) else -1.0
    base = os.path.join(scratch, os.path.basename(D.rstrip("/")) + "_replay")
    os.makedirs(base, exist_ok=True)
    tape = base + "/raw.tape"
    cmd = [os.path.expanduser("~/venv-fgo/bin/python"), os.path.join(TOOLS, "make_tape.py"), bagdir, tape]
    if t_arm is not None and t_arm >= 0:
        cmd += ["--armed-at", repr(float(t_arm))]
    subprocess.run(cmd, check=True)
    cfg = base + "/live.init.json"
    json.dump({"mode": "corridor", "window": 0.25, "kf_dt": 1.0 / 30.0, "lm_iters": 2, "t_arm": None,
               "fwd_sigma_psi": None}, open(cfg, "w"))
    out["arming"] = f"HEARTBEAT row at t_armed_header {t_arm}" if t_arm is not None and t_arm >= 0 else "arm_source none (no t_armed_header)"
    for mode in ("time_ref", "causal"):
        pre = f"{base}/R_{mode}"
        subprocess.run([os.path.join(bindir, "fgo_cpp_live_replay"), tape, cfg, pre, "--imu-stamp", mode, "--delay", "0.10",
                        "--arm-source", "heartbeat" if t_arm is not None and t_arm >= 0 else "none"],
                       check=True, stdout=subprocess.DEVNULL)
        out[mode] = {"states": pre + ".kf.f64"}
    return out


def score(a):
    D = os.path.join(a.root, a.trial); notes = []
    out = {"trial": a.trial, "notes": notes}
    meta = open(os.path.join(D, "metadata.yaml")).read() if os.path.exists(os.path.join(D, "metadata.yaml")) else ""
    out["meta"] = [l for l in meta.splitlines() if l.startswith(("fgo_node", "fgo_cpp", "world", "extra_parm"))]
    impl = "cpp" if any(l.startswith("fgo_node_impl: cpp") for l in out["meta"]) else "python"
    out["impl"] = impl
    js = os.path.join(D, "fgo_node_stats.json")
    out["node_stats"] = json.load(open(js)) if os.path.exists(js) else None
    out["a"] = check_a(D)
    # config check (Pre-registration 4)
    cfg_ok = bool(out["a"].get("params_ok"))
    if impl == "cpp":
        fl = next((l for l in out["meta"] if l.startswith("fgo_cpp:")), "")
        s = (out["node_stats"] or {}).get("config", "")
        try:
            dly = float(fl.split("reorder_delay_s:")[1].split(",")[0]); stp = fl.split("imu_stamp:")[1].split(",")[0].strip()
            echo = (f"reorder_delay_s={dly:.6f}" in s) and (f"imu_stamp={stp} " in s)
        except (IndexError, ValueError):
            echo, dly, stp = False, None, None
        out["config_echo_ok"] = echo; cfg_ok = cfg_ok and echo
        out["config"] = {"reorder_delay_s": dly if echo else None, "imu_stamp": stp if echo else None}
    else:
        out["config"] = {"reorder_delay_s": 0.10, "imu_stamp": "causal (fgo_node.py)"}
    out["config_ok"] = cfg_ok
    if not cfg_ok:
        notes.append("CONFIG CHECK FAILED: the flight is VOID under Pre-registration 4 (scores below are not admissible)")
    # b
    scratch = a.scratch or tempfile.mkdtemp(prefix="fgo_cpp_sitl_check_")
    bagdir, copy = bag_dir_readable(D, scratch, notes)
    F, G = read_bag(bagdir) if bagdir else (np.zeros((0, 7)), np.zeros((0, 7)))
    src = "/fgo/pose (bag)"
    if not len(F) and os.path.exists(os.path.join(D, "fgo_node_stats.f64")):
        S = np.fromfile(os.path.join(D, "fgo_node_stats.f64")).reshape(-1, 10)
        F = np.c_[S[:, 0], S[:, 6:9], np.full(len(S), np.nan), np.full(len(S), np.nan), S[:, 9]]
        src = "fgo_node_stats.f64 (no roll/pitch: delta_att not available)"
    if not len(F) and os.path.exists(os.path.join(D, "fgo_node_stats.npz")):
        T = np.load(os.path.join(D, "fgo_node_stats.npz"), allow_pickle=True)["traj"]   # t, x, y, z, roll, pitch, yaw, bgz
        F = T[:, :7].astype(float); src = "fgo_node_stats.npz traj (fgo_node.py)"
    out["b_source"] = src
    if len(F) and len(G):
        out["b_primary"] = fit_delta(F, G) if np.isfinite(F[:, 4]).all() else {"error": "no roll/pitch in the source"}
        out["b_secondary"] = secondary(F, G)
        if a.replay_pair and bagdir:
            rp = replay_pair(bagdir, D, a.replay_pair, scratch)
            for mode in ("time_ref", "causal"):
                Fr = kf_states(rp[mode]["states"][:-len(".kf.f64")])
                rp[mode].update({"b_primary": fit_delta(Fr, G), "b_secondary": secondary(Fr, G), "n_kf": len(Fr)})
            out["b_replay_pair"] = rp
    else:
        notes.append("no node states or no ground truth: check b not scored")
    if out["node_stats"] is not None and os.path.exists(os.path.join(D, "fgo_node_stats.f64")):
        S = np.fromfile(os.path.join(D, "fgo_node_stats.f64")).reshape(-1, 10)
        out["node_timing"] = {"step_ms_median": pct(S[:, 4] / 1e6, 50), "step_ms_p99": pct(S[:, 4] / 1e6, 99),
                              "queue_lag_ms_median": pct(1e3 * S[:, 5], 50), "queue_lag_ms_p99": pct(1e3 * S[:, 5], 99),
                              "queue_lag_ms_max": float(1e3 * S[:, 5].max())}
    if copy and not a.keep_scratch:
        shutil.rmtree(copy, ignore_errors=True)
    return out


def decide(a):
    J = {k: json.load(open(getattr(a, k))) for k in ("i", "ii", "iii", "a3")}
    out = {"inputs": {k: getattr(a, k) for k in J}, "void": [k for k, j in J.items() if not j.get("config_ok")]}
    exp = {"i": (0.20, "time_ref"), "ii": (0.10, "time_ref"), "iii": (0.10, "causal")}
    for k, (dly, stp) in exp.items():
        c = J[k].get("config", {})
        if c.get("reorder_delay_s") is None or abs(c["reorder_delay_s"] - dly) > 1e-9 or c.get("imu_stamp") != stp:
            out["void"].append(f"{k}: configuration {c} is not the pre-registered ({dly}, {stp})")
    mx = J["i"]["a"].get("age_ms", {}).get("max")
    out["rule_A"] = {"flight_i_max_age_ms": mx,
                     "verdict": None if mx is None else ("adopt 0.10 s (max Age > 250 ms)" if mx > AGE_MAX_MS else "keep 0.20 s"),
                     "flight_ii_max_age_ms": J["ii"]["a"].get("age_ms", {}).get("max"),
                     "reason_figures_i": J["i"]["a"].get("age_ms"), "figures_ii": J["ii"]["a"].get("age_ms")}
    m2 = out["rule_A"]["flight_ii_max_age_ms"]
    if m2 is not None and m2 > AGE_MAX_MS:
        out["rule_A"]["note"] = "neither delay keeps the age within the 250 ms budget at all times (to the main session)"
    out["rule_A"]["cost_of_0.10"] = {k: {f: (J[k].get("node_stats") or {}).get(f) for f in ("max_lateness_s", "n_out_of_order")}
                                     for k in ("ii", "iii")}
    d = {k: J[k].get("b_primary", {}).get("delta_att_ms") for k in ("ii", "iii", "a3")}
    out["rule_B"] = {"delta_att_ms": d}
    if None in d.values():
        out["rule_B"]["verdict"] = "indistinguishable at this resolution; keep time_ref (a delta_att not identified)"
    else:
        R = max(5.0, abs(d["iii"] - d["a3"])); diff = abs(abs(d["ii"]) - abs(d["iii"]))
        out["rule_B"].update({"resolution_R_ms": R, "abs_difference_ms": diff})
        out["rule_B"]["verdict"] = ("indistinguishable at this resolution; keep time_ref" if diff < R else
                                    ("time_ref (FC clock) more accurate" if abs(d["ii"]) < abs(d["iii"]) else
                                     "causal (Python node timing) more accurate"))
    rp = J["ii"].get("b_replay_pair")
    if rp:
        out["rule_B"]["replay_pair_ii_report"] = {m: rp[m]["b_primary"].get("delta_att_ms") for m in ("time_ref", "causal")}
    if out["void"]:
        out["NOTE"] = "VOID flights present: verdicts above are not admissible until those flights are re-flown"
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score"); s.add_argument("trial"); s.add_argument("--root", default=os.path.expanduser("~/thesis_data/trials"))
    s.add_argument("--scratch"); s.add_argument("--json"); s.add_argument("--replay-pair", metavar="BIN_DIR")
    s.add_argument("--keep-scratch", action="store_true")
    d = sub.add_parser("decide")
    for k in ("i", "ii", "iii", "a3"):
        d.add_argument(f"--{k}", required=True)
    d.add_argument("--json")
    a = ap.parse_args()
    res = score(a) if a.cmd == "score" else decide(a)
    print(json.dumps(res, indent=1, default=str))
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1, default=str)
