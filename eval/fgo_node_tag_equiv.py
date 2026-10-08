#!/usr/bin/env python3
"""Experiment H, S3 gate (docs/h_backends_tag_input.md sections 1.3-1.4, PRE-REGISTERED): the FGO node core with tag
fixes (FgoNodeCore(tags=True)) against the offline room_fgo_replay.py.

1. The offline reference: the UNMODIFIED room_fgo_replay.py (runpy, --no-batch) with FGO_OUT_ROOT -> scratch, so the
   stored <trial>/room_fgo/ is never written; its fgo_live.tum must be byte-identical to the stored one. Its module
   globals give the exact event stream (gap rule, whole-flight dejitter, stable sort) and the factor counts.
2. FN1-FN3: the node core driven with THAT stream (dejitter "none", gap "off", horizon 0.10 s), its keyframes from the
   re-anchor on written through room_fgo_replay.py's own TUM writer; compared row by row.
3. FN4 (+ report): the node on its CAUSAL inputs (bag receipt order, raw header stamps, causal dejitter, causal IMU-gap
   detection from /imu/time_ref, /tags/sent in arrival order), against the offline live track at the offline keyframe
   times, in tag-visible time (a sent fix within 0.2 s; 2 s after the anchor and after each re-acquisition excluded).
Also: keyframe step time before / after the anchor (the gate-only covariance recursion runs until the anchor).
Usage (~/venv-fgo): ROOM_TAG_SIGMA_POS=0.02 python3 eval/fgo_node_tag_equiv.py TRIAL SCRATCH_DIR [--json OUT] [--no-causal]"""
import argparse, contextlib, filecmp, glob, io, json, math, os, runpy, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "estimators")); sys.path.insert(0, os.path.join(ROOT, "src", "estimators", "fgo"))
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from fgo_node_core import FgoNodeCore

ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("scratch"); ap.add_argument("--json")
ap.add_argument("--no-causal", action="store_true"); a = ap.parse_args()
assert os.environ.get("ROOM_TAG_SIGMA_POS"), "set ROOM_TAG_SIGMA_POS (H: 0.02)"
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
stored = f"{D}/room_fgo/fgo_live.tum"
mt0 = {f: os.path.getmtime(os.path.join(D, "room_fgo", f)) for f in os.listdir(f"{D}/room_fgo")}
wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi
out = {"trial": a.trial, "tag_sigma_pos": float(os.environ["ROOM_TAG_SIGMA_POS"])}

# ---- 1. offline reference (reproduced into scratch) ----
os.environ["FGO_OUT_ROOT"] = os.path.join(a.scratch, "offline")
sys.argv = ["room_fgo_replay.py", a.trial, "--no-batch"]
t0 = time.perf_counter()
g = runpy.run_path(os.path.join(ROOT, "src", "estimators", "fgo", "room_fgo_replay.py"), run_name="__main__")
del os.environ["FGO_OUT_ROOT"]
repro = os.path.join(a.scratch, "offline", a.trial, "room_fgo", "fgo_live.tum")
mt1 = {f: os.path.getmtime(os.path.join(D, "room_fgo", f)) for f in os.listdir(f"{D}/room_fgo")}
assert mt0 == mt1, "stored room_fgo/ changed!"
fo = g["fgo"]
off = {"reproduced_byte_identical": filecmp.cmp(stored, repro, shallow=False), "t_anchor": g["t_anchor"],
       "n_tag": int(getattr(fo, "n_tag", 0)), "n_flow": int(fo.n_flow), "n_range": int(fo.n_range), "keyframe_failures": int(g["n_fail"]),
       "wall_s": time.perf_counter() - t0}
sn = np.array(g["step_ns"]) / 1e6
out["offline"] = off
ref = np.loadtxt(stored)
write_rows = g["write_rows"]; ev = g["ev"]; T_ARM = g["gp"].t_arm
SIG = float(os.environ["ROOM_TAG_SIGMA_POS"])


def yaw_of(q):
    x, y, z, w = q.T
    return np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def run_core(events, **kw):
    core = FgoNodeCore(window=0.25, lm_iters=2, t_arm=T_ARM, tags=True, tag_sigma_pos=SIG, **kw)
    buf = io.StringIO(); t0_ = time.perf_counter()
    with contextlib.redirect_stdout(buf):
        for e in events:
            core.push(*e)
        core.flush()
    core.n_fail = buf.getvalue().count("[warn] keyframe")
    core.wall_s = time.perf_counter() - t0_
    return core


def step_split(core):
    st = np.array(core.step_ns) / 1e6; tk = np.array([r[0] for r in core.traj])
    res = {}
    for lab, m in (("before_anchor", tk < (core.t_anchor or np.inf)), ("after_anchor", tk >= (core.t_anchor or np.inf))):
        if m.any():
            res[lab] = {"median_ms": float(np.median(st[m])), "p95_ms": float(np.percentile(st[m], 95)),
                        "p99_ms": float(np.percentile(st[m], 99)), "max_ms": float(st[m].max()), "n": int(m.sum())}
    return res


# ---- 2. FN1-FN3: the node core on the offline stream ----
c2 = run_core([(t, k, d) for t, k, d in ev], dejitter="none", gap="off", horizon_s=0.10)
rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r, an in zip(c2.traj, c2.anchor_log) if an[0]]
node_tum = os.path.join(a.scratch, "node_step2_fgo_live.tum"); write_rows(node_tum, rows)
nt = np.loadtxt(node_tum)
same_t = len(nt) == len(ref) and np.array_equal(nt[:, 0], ref[:, 0])
fn = {"node_rows": int(len(nt)), "offline_rows": int(len(ref)), "byte_identical": filecmp.cmp(node_tum, stored, shallow=False)}
if same_t:
    dp = np.linalg.norm(nt[:, 1:4] - ref[:, 1:4], axis=1); dy = np.degrees(np.abs(wrap(yaw_of(nt[:, 4:8]) - yaw_of(ref[:, 4:8]))))
    fn["FN1_max_m"] = float(dp.max()); fn["FN2_max_deg"] = float(dy.max())
fn["FN3"] = {"same_keyframe_times": bool(same_t), "t_anchor_node": c2.t_anchor, "t_anchor_offline": off["t_anchor"],
             "n_tag": [int(getattr(c2.fgo, "n_tag", 0)), off["n_tag"]], "n_flow": [int(c2.fgo.n_flow), off["n_flow"]],
             "n_range": [int(c2.fgo.n_range), off["n_range"]], "keyframe_failures_node": int(c2.n_fail)}
f3 = fn["FN3"]
f3["pass"] = bool(same_t and c2.t_anchor == off["t_anchor"] and f3["n_tag"][0] == f3["n_tag"][1] and f3["n_flow"][0] == f3["n_flow"][1]
                  and f3["n_range"][0] == f3["n_range"][1] and c2.n_fail == 0 and off["keyframe_failures"] == 0)
fn["FN1_pass"] = bool(same_t and fn["FN1_max_m"] <= 1e-6)
fn["FN2_pass"] = bool(same_t and fn["FN2_max_deg"] <= 1e-6)
fn["pass"] = bool(fn["FN1_pass"] and fn["FN2_pass"] and f3["pass"] and off["reproduced_byte_identical"])
fn["step_ms"] = step_split(c2); fn["step_ms_offline_replay_all"] = {"median_ms": float(np.median(sn)), "p95_ms": float(np.percentile(sn, 95))}
out["FN1_FN3"] = fn
print(json.dumps({"offline": off, "FN1_FN3": fn}, indent=1), flush=True)

# ---- 3. FN4: causal inputs ----
if not a.no_causal:
    ts = get_typestore(Stores.ROS2_JAZZY)
    ts.register(get_types_from_msg(open(glob.glob(os.path.join(ROOT, "**/OpticalFlow.msg"), recursive=True)[0]).read(),
                                   "optical_flow_interfaces/msg/OpticalFlow"))
    st_ = lambda h: h.stamp.sec + h.stamp.nanosec * 1e-9
    raw, SENT = [], []
    with Reader(f"{D}/bag") as r:
        conns = {c.topic: c for c in r.connections}
        want = ["/imu/data_raw", "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates", "/imu/time_ref", "/tags/sent"]
        for con, t_ns, rawb in r.messages(connections=[conns[w] for w in want if w in conns]):
            m = ts.deserialize_cdr(rawb, con.msgtype); h = st_(m.header)
            if con.topic == "/imu/time_ref":
                raw.append((h, "tref", m.time_ref.sec + m.time_ref.nanosec * 1e-9)); continue
            if con.topic == "/imu/data_raw":
                p = (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]),
                     np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])); k = "imu"
            elif con.topic == "/downward_lidar/range":
                p = float(m.range); k = "rng"
            elif con.topic == "/optical_flow/measurement":
                p = (np.array([m.flow_x_rad, m.flow_y_rad]), bool(m.valid), float(m.inlier_ratio)); k = "flow"
            elif con.topic == "/tags/sent":
                q = m.pose.pose.orientation; p = (m.pose.pose.position.x, m.pose.pose.position.y, 2 * math.atan2(q.z, q.w)); k = "tag"
                SENT.append(h)
            else:
                p = np.array([m.vector.x, m.vector.y, m.vector.z]); k = "att"
            raw.append((h, k, p))
    SENT = np.array(sorted(SENT))
    c3 = run_core(raw, dejitter="causal", gap="causal", horizon_s=0.10)
    tr = np.array([r[:7] for r, an in zip(c3.traj, c3.anchor_log) if an[0]])
    w = (ref[:, 0] >= tr[0, 0]) & (ref[:, 0] <= tr[-1, 0]); R_ = ref[w]
    pN, pE = np.interp(R_[:, 0], tr[:, 0], tr[:, 2]), np.interp(R_[:, 0], tr[:, 0], tr[:, 1])
    py = np.interp(R_[:, 0], tr[:, 0], np.unwrap(tr[:, 6]))
    dh = np.hypot(pN - R_[:, 2], pE - R_[:, 1]); dy = np.degrees(np.abs(wrap(py - yaw_of(R_[:, 4:8]))))
    j = np.searchsorted(SENT, R_[:, 0], side="right") - 1
    vis = (j >= 0) & (R_[:, 0] - SENT[np.clip(j, 0, None)] <= 0.2)
    reacq = [SENT[0]] + [SENT[k] for k in range(1, len(SENT)) if SENT[k] - SENT[k - 1] > 1.0]
    for t_ in reacq:
        vis &= ~((R_[:, 0] >= t_) & (R_[:, 0] < t_ + 2.0))
    gaps = [(SENT[k - 1], SENT[k]) for k in range(1, len(SENT)) if SENT[k] - SENT[k - 1] > 1.0]
    losses = []
    for tl, tf in gaps:                       # the difference just before the returning fix (report)
        i = np.searchsorted(R_[:, 0], tf) - 1
        losses.append({"t_last_fix": float(tl), "t_first_fix": float(tf), "loss_s": float(tf - tl),
                       "horiz_diff_m": float(dh[i]), "yaw_diff_deg": float(dy[i])})
    n_tag_c = int(getattr(c3.fgo, "n_tag", 0))
    fn4 = {"t_anchor_node": c3.t_anchor, "t_anchor_offline": off["t_anchor"], "n_tag": [n_tag_c, off["n_tag"]],
           "reinits": int(c3.reinits), "valid_end": bool(c3.valid), "keyframe_failures": int(c3.n_fail),
           "samples_visible": int(vis.sum()), "samples": int(len(R_)),
           "horiz_m": {"p50": float(np.median(dh[vis])), "p95": float(np.percentile(dh[vis], 95)), "max": float(dh[vis].max())},
           "yaw_deg": {"p50": float(np.median(dy[vis])), "p95": float(np.percentile(dy[vis], 95)), "max": float(dy[vis].max())},
           "whole_after_anchor": {"horiz_max_m": float(dh.max()), "yaw_max_deg": float(dy.max())},
           "losses": losses, "step_ms": step_split(c3),
           "band": "visible: horizontal p95 <= 0.02 m, max <= 0.15 m; yaw p95 <= 0.2 deg, max <= 0.5 deg; same anchor fix; tag factors within 1%"}
    fn4["pass"] = bool(fn4["horiz_m"]["p95"] <= 0.02 and fn4["horiz_m"]["max"] <= 0.15 and fn4["yaw_deg"]["p95"] <= 0.2
                       and fn4["yaw_deg"]["max"] <= 0.5 and c3.t_anchor == off["t_anchor"] and abs(n_tag_c - off["n_tag"]) <= 0.01 * off["n_tag"])
    out["FN4"] = fn4
    print(json.dumps({"FN4": fn4}, indent=1), flush=True)
if a.json:
    json.dump(out, open(a.json, "w"), indent=1, default=float)
