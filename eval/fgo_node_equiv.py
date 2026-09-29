#!/usr/bin/env python3
"""FGO node validation (ruling D7; METHODOLOGY "FGO track ... PRE-REGISTERED").
  --mode step2 : the node core (src/estimators/fgo/fgo_node_core.py) is driven with the offline
                 replay's OWN event stream (the same bag reading, IMU-gap trim, whole-flight dejitter
                 and stable stamp sort as fgo_replay.py), dejitter="none", gap="off". Bands FE1-FE4.
  --mode step3 : the node on its CAUSAL inputs, one difference at a time (a REPORT):
                   i   causal dejitter (raw receipt stamps, running fit), stamp order
                   ii  arrival (bag receipt) order through the horizon queue, offline stamps
                   i+ii both;  iii (+ causal gap detection from /imu/time_ref, instead of the trim)
Compared with the offline FGO's <trial>/fgo/fgo_traj.tum (window 0.25 s, LM 2) over the pinned
cruise window; also the keyframe step time. Deterministic mode: the bag is read as fast as possible.
Usage (~/venv-fgo): python3 eval/fgo_node_equiv.py TRIAL --mode step2|step3 [--json OUT]"""
import argparse, glob, json, math, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "src", "estimators")); sys.path.insert(0, os.path.join(ROOT, "src", "estimators", "fgo"))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from imu_timing import dejitter_imu, apply_gap_rule
from fgo_node_core import FgoNodeCore
from cruise_window import cruise_bounds

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--mode", required=True, choices=["step2", "step3"])
ap.add_argument("--json"); a = ap.parse_args()
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
ts = get_typestore(Stores.ROS2_JAZZY)
ts.register(get_types_from_msg(open(glob.glob(os.path.join(ROOT, "**/OpticalFlow.msg"), recursive=True)[0]).read(),
                               "optical_flow_interfaces/msg/OpticalFlow"))
st = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9

# read the bag ONCE, in bag (receipt) order, keeping the receipt time
raw = []          # (receipt_t, header_t, kind, payload)
with Reader(f"{D}/bag") as r:
    conns = {c.topic: c for c in r.connections}
    want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates", "/imu/time_ref"]
    for con, t_ns, rawb in r.messages(connections=[conns[w] for w in want if w in conns]):
        m = ts.deserialize_cdr(rawb, con.msgtype)
        if con.topic == "/imu/time_ref":
            raw.append((t_ns * 1e-9, st(m.header), "tref", m.time_ref.sec + m.time_ref.nanosec * 1e-9)); continue
        tt = st(m.header)
        if con.topic == "/imu/data_raw":
            p = (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]),
                 np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])); k = "imu"
        elif con.topic == "/downward_lidar/range":
            p = float(m.range); k = "rng"
        elif con.topic == "/optical_flow/measurement":
            p = (np.array([m.flow_x_rad, m.flow_y_rad]), bool(m.valid), float(m.inlier_ratio)); k = "flow"
        else:
            p = np.array([m.vector.x, m.vector.y, m.vector.z]); k = "att"
        raw.append((t_ns * 1e-9, tt, k, p))

# the OFFLINE stream, exactly as fgo_replay.py builds it (header stamps, bag order, trim, dejitter, stable sort)
off = [(h, k, p) for (_, h, k, p) in raw if k != "tref"]
off = apply_gap_rule(off, a.trial)
off, dj = dejitter_imu(off)
off.sort(key=lambda e: e[0])
dj_map = {}      # bag position of each IMU sample -> offline dejittered stamp (for variant ii)

ref = np.loadtxt(f"{D}/fgo/fgo_traj.tum"); gt = np.loadtxt(f"{D}/fgo/ground_truth.tum")
c0, c1 = cruise_bounds(gt[:, 0], gt[:, 1], gt[:, 2])
m_off = dict(l.strip().split("=") for l in open(f"{D}/fgo/metrics.txt"))


def yaw_of(q):
    x, y, z, w = q.T
    return np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def validity(core):
    v = np.array(core.valid_log, dtype=float).reshape(-1, 2)
    if not len(v):
        return None
    w = (v[:, 0] >= c0) & (v[:, 0] <= c1)
    ch = np.where(np.diff(v[:, 1]) != 0)[0]
    return {"valid_pct_cruise": float(100 * v[w, 1].mean()),
            "changes_rel_cruise_s": [(round(float(v[i + 1, 0] - c0), 2), int(v[i + 1, 1])) for i in ch[:10]]}


def compare(core, name):
    tr = np.array(core.traj)
    n = min(len(tr), len(ref))
    same_t = bool(len(tr) == len(ref) and np.allclose(tr[:, 0], ref[:, 0], atol=1e-6))
    # compare at the offline keyframe times (interpolate the node when grids differ)
    # identical keyframe grid -> compare ROW BY ROW (interpolating at the reference file's %.6f-rounded
    # stamps adds speed x 5e-7 s, ~1e-4 m in a blank runaway: an artefact found on dsn_blank_r1)
    if same_t:
        px = tr[:, 1:4]
    else:
        px = np.c_[[np.interp(ref[:, 0], tr[:, 0], tr[:, i]) for i in (1, 2, 3)]].T
    yw = np.unwrap(tr[:, 6]) if same_t else np.interp(ref[:, 0], tr[:, 0], np.unwrap(tr[:, 6]))
    # "as written": the node's attitude through fgo_replay.py's OWN TUM writer (its euler_to_quat has a
    # w-component typo, sr*sp*cy for sr*sp*sy, giving a non-unit quaternion) and %.6f rounding, so both
    # sides are compared in the same representation (FE2)
    r_, p_, y_ = tr[:, 4], tr[:, 5], tr[:, 6]
    cr, sr, cp, sp, cy, sy = np.cos(r_/2), np.sin(r_/2), np.cos(p_/2), np.sin(p_/2), np.cos(y_/2), np.sin(y_/2)
    qw = np.round(np.c_[sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*cy], 6)
    yw_written = np.unwrap(yaw_of(qw)) if same_t else np.interp(ref[:, 0], tr[:, 0], np.unwrap(yaw_of(qw)))
    # FE4: gyro-z bias against the offline bgz_series.txt (|b| deg/min per keyframe in its apparatus window)
    bz = np.loadtxt(f"{D}/fgo/bgz_series.txt")
    fe4 = float(np.max(np.abs(np.interp(bz[:, 0], tr[:, 0], np.abs(np.degrees(tr[:, 7]) * 60)) - bz[:, 1]))) if same_t else None
    w = (ref[:, 0] >= c0) & (ref[:, 0] <= c1)
    dp = np.linalg.norm(px - ref[:, 1:4], axis=1)[w]
    dy_rpy = np.degrees(np.abs((yw - yaw_of(ref[:, 4:8]) + math.pi) % (2 * math.pi) - math.pi))[w]
    dy = np.degrees(np.abs((yw_written - yaw_of(ref[:, 4:8]) + math.pi) % (2 * math.pi) - math.pi))[w]
    bgz = np.degrees(tr[:, 7]) * 60
    sm = np.array(core.step_ns) / 1e6
    return {"variant": name, "keyframes": len(tr), "keyframes_offline": int(m_off["n_kf"]), "same_keyframe_times": same_t,
            "n_flow": core.fgo.n_flow, "n_flow_offline": int(m_off["n_flow"]), "n_range": core.fgo.n_range, "n_range_offline": int(m_off["n_range"]),
            "dpos_m": {"max": float(dp.max()), "rms": float(np.sqrt(np.mean(dp ** 2))), "end": float(dp[-1])},
            "dyaw_deg": {"max": float(dy.max()), "end": float(dy[-1])},
            "dyaw_deg_node_rpy_vs_offline_quat": {"max": float(dy_rpy.max())},
            "step_ms": {"median": float(np.median(sm)), "p95": float(np.percentile(sm, 95)), "p99": float(np.percentile(sm, 99))},
            "reinits": core.reinits, "valid_end": core.valid, "dbgz_deg_per_min_max": fe4,
            "validity": validity(core)}


def run(events, name, **kw):
    core = FgoNodeCore(window=0.25, lm_iters=2, **kw)
    t0 = time.perf_counter()
    for e in events:
        core.push(*e)
    core.flush()
    res = compare(core, name); res["wall_s"] = time.perf_counter() - t0
    if os.environ.get("SAVE_TRAJ"):
        np.save(os.environ["SAVE_TRAJ"] + f"_{name}.npy", np.array(core.traj))
    print(name, json.dumps(res), flush=True)
    return res


out = {"trial": a.trial, "mode": a.mode, "window_s": [float(c0), float(c1)], "offline_dejitter": dj}
if a.mode == "step2":
    r2 = run(off, "step2_offline_stream", dejitter="none", gap="off", horizon_s=0.10)
    r2["FE1"] = r2["dpos_m"]["max"] <= 1e-6
    r2["FE2"] = r2["dyaw_deg"]["max"] <= 1e-6
    r2["FE4"] = r2["dbgz_deg_per_min_max"] is not None and r2["dbgz_deg_per_min_max"] <= 1e-9
    r2["FE3"] = (r2["keyframes"] == r2["keyframes_offline"] and r2["n_flow"] == r2["n_flow_offline"] and r2["n_range"] == r2["n_range_offline"])
    out["step2"] = r2; out["pass"] = bool(r2["FE1"] and r2["FE2"] and r2["FE3"] and r2["FE4"])
else:
    trim = json.load(open(f"{D}/imu_gaps.json")) if os.path.exists(f"{D}/imu_gaps.json") else {"verdict": "ok"}
    t_trim = trim.get("replay_start_s") if trim["verdict"] == "trim" else None
    keep = (lambda h: True) if t_trim is None else (lambda h: h >= t_trim)
    # offline dejittered stamps for each IMU sample, in bag order (for variant ii)
    imu_off = iter([e[0] for e in off if e[1] == "imu"])
    arrival = []           # (stamp, kind, payload) in bag order: IMU with offline stamps, others with header stamps
    for (_, h, k, p) in raw:
        if k == "tref" or not keep(h):
            continue
        arrival.append((next(imu_off) if k == "imu" else h, k, p))
    raw_stamp = sorted([(h, k, p) for (_, h, k, p) in raw if k != "tref" and keep(h)], key=lambda e: e[0])
    raw_arrival = [(h, k, p) for (_, h, k, p) in raw if k != "tref" and keep(h)]
    all_arrival_tref = [(h if k != "tref" else h, k, p) for (_, h, k, p) in raw]
    out["step3"] = [
        run(raw_stamp, "i_causal_dejitter", dejitter="causal", gap="off", horizon_s=0.10),
        run(arrival, "ii_arrival_order", dejitter="none", gap="off", horizon_s=0.10),
        run(raw_arrival, "i+ii", dejitter="causal", gap="off", horizon_s=0.10),
        run(all_arrival_tref, "i+ii+iii_causal_gap", dejitter="causal", gap="causal", horizon_s=0.10),
    ]
print(json.dumps({k: v for k, v in out.items() if k not in ("step3",)}, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
