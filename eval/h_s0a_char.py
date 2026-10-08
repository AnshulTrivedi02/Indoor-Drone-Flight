#!/usr/bin/env python3
"""Experiment H, S0a: wall-tag characterisation from the FORWARD camera (pre-registered rules, METHODOLOGY
"Experiment H: pre-registration"). Reads the S0a trial bag (full forward stream + GT).
  1. Texture convention: for each candidate in tag_measure.CONVENTIONS, the vehicle pose from every wall-tag (id 10)
     detection against GT -> median position / |yaw| error. FROZEN if exactly one candidate has median < 0.05 m and
     < 1 deg (else: stop and report).
  2. With the frozen convention, per detection: horizontal error in W (= world xy minus the tag), range, image radius of
     the tag centre. Validity rule: the largest r_valid (10 px steps) with p95 horizontal error <= 0.05 m over the
     detections at range 1.0-2.0 m (camera-to-tag distance).
  3. sigma_pos = p95 horizontal error of the VALID detections at 1.5 m (1.35-1.65 m), rounded UP to 0.01 m.
  4. Lateral amplitude: the image radius of the tag centre when the vehicle is at W (-1.5, +-A) at the tag's height,
     from the camera geometry; the largest A in 0.1 m steps (<= 0.5) with radius <= r_valid.
  5. Detection rate (tag fully in view by GT projection), wrong ids, time per frame.
Usage (venv-tags): python3 eval/h_s0a_char.py TRIAL [--json OUT]"""
import argparse, json, math, os, sys, time
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "src", "tags"))
import tag_measure as T
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--json"); a = ap.parse_args()
FX, CX, CY = 554.3827056884766, 320.0, 240.0; K = np.array([[FX, 0, CX], [0, FX, CY], [0, 0, 1]])
WALL_ID, WALL_P, WALL_RPY = 10, np.array([0.0, 4.998, 1.5]), (math.pi / 2, 0.0, 0.0)
D = os.path.expanduser(f"~/thesis_data/trials/{a.trial}")
ts = get_typestore(Stores.ROS2_JAZZY); G, I = [], []
with Reader(f"{D}/bag") as r:
    cs = {c.topic: c for c in r.connections}
    for c, _, raw in r.messages(connections=[cs["/ground_truth/pose"], cs["/forward_camera/image"]]):
        m = ts.deserialize_cdr(raw, c.msgtype); t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if c.topic == "/ground_truth/pose":
            q = m.pose.orientation; G.append((t, m.pose.position.x, m.pose.position.y, m.pose.position.z, q.x, q.y, q.z, q.w))
        else:
            I.append((t, np.frombuffer(m.data, np.uint8).reshape(m.height, m.step)[:, :m.width].copy()))
G = np.array(G); det = T.TagDetector(FX, FX, CX, CY)
rows = []; n_vis = n_det_vis = n_wrong = 0; proc = []; samples = []
half = T.TAG_SIZE_M / 2
for t, img in I:
    j = np.argmin(np.abs(G[:, 0] - t)); p_wb = G[j, 1:4]; R_wb = Rot.from_quat(G[j, 4:8]).as_matrix()
    if p_wb[2] < 0.8:
        continue
    R_wc = R_wb @ T.R_BODY_CAM_FWD; p_wc = p_wb + R_wb @ T.T_BODY_CAM_FWD_POS
    # visibility of the 4 tag corners (any convention: the square's corners are convention-independent)
    Rm = T.wall_tag_R_wt(WALL_RPY, "u+x_v-y")
    cw = [WALL_P + Rm @ np.array([sx * half, sy * half, 0.0]) for sx, sy in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    vis = True
    for c3 in cw:
        pc = R_wc.T @ (c3 - p_wc)
        if pc[2] <= 0: vis = False; break
        u = K @ (pc / pc[2])
        if not (0 <= u[0] < 640 and 0 <= u[1] < 480): vis = False; break
    t0 = time.perf_counter(); dets = det.detect(img); proc.append(time.perf_counter() - t0)
    got = {d[0] for d in dets}
    n_vis += vis; n_det_vis += vis and (WALL_ID in got); n_wrong += len(got - {WALL_ID})
    for (i, R, tt, cn, cc, dm, hm) in dets:
        if i != WALL_ID: continue
        samples.append((R, tt, p_wb.copy(), T.yaw_of(R_wb)))
        rows.append({"R": R, "t": tt, "p": p_wb.copy(), "yaw": T.yaw_of(R_wb), "rad": math.hypot(cc[0] - CX, cc[1] - CY),
                     "range": float(np.linalg.norm(tt)), "margin": dm})
conv = T.find_convention_full(samples, WALL_RPY, WALL_P)
ok = [k for k, (pe, ye) in conv.items() if pe < 0.05 and ye < 1.0]
out = {"trial": a.trial, "frames": len(I), "detections": len(rows), "visible_frames": int(n_vis),
       "detection_rate_visible": n_det_vis / max(n_vis, 1), "wrong_ids": int(n_wrong),
       "proc_ms": {"median": 1e3 * float(np.median(proc)), "p99": 1e3 * float(np.percentile(proc, 99))},
       "conventions": conv, "frozen_convention": ok[0] if len(ok) == 1 else None}
print(json.dumps({k: v for k, v in out.items() if k != "conventions"}, indent=1)); print("conventions:", conv)
if len(ok) != 1:
    print("STOP: convention not unique / not found"); json.dump(out, open(a.json, "w"), indent=1) if a.json else None; sys.exit(2)
R_wt = T.wall_tag_R_wt(WALL_RPY, ok[0])
for r_ in rows:
    p, Rw = T.vehicle_pose_full(R_wt, WALL_P, r_["R"], r_["t"])
    r_["dxy"] = float(np.hypot(p[0] - r_["p"][0], p[1] - r_["p"][1])); r_["dz"] = float(p[2] - r_["p"][2])
    r_["dyaw"] = float(np.degrees(abs((T.yaw_of(Rw) - r_["yaw"] + math.pi) % (2 * math.pi) - math.pi)))
R_ = {k: np.array([x[k] for x in rows]) for k in ("rad", "range", "dxy", "dz", "dyaw")}
band = (R_["range"] >= 1.0) & (R_["range"] <= 2.0); r_valid = None; tab = []
for rv in range(10, 410, 10):
    w = band & (R_["rad"] <= rv)
    if w.sum() < 20: continue
    p95 = float(np.percentile(R_["dxy"][w], 95)); tab.append((rv, int(w.sum()), p95))
    if p95 <= 0.05: r_valid = rv
w15 = (R_["range"] >= 1.35) & (R_["range"] <= 1.65) & (R_["rad"] <= (r_valid or 0))
sigma = math.ceil(100 * float(np.percentile(R_["dxy"][w15], 95))) / 100 if w15.sum() else None
amp = None
for A in (0.5, 0.4, 0.3, 0.2, 0.1):          # tag-centre image radius from W (-1.5, A), camera at the tag's height
    u = FX * (-A) / (1.5 - T.T_BODY_CAM_FWD_POS[0]) + CX
    if r_valid and abs(u - CX) <= r_valid: amp = A; break
by_range = {}
for lo, hi in ((0.9, 1.25), (1.25, 1.75), (1.75, 2.25), (2.25, 2.8)):
    w = (R_["range"] >= lo) & (R_["range"] < hi)
    if w.any():
        by_range[f"{lo}-{hi} m"] = {"n": int(w.sum()), "dxy_p50": float(np.median(R_["dxy"][w])), "dxy_p95": float(np.percentile(R_["dxy"][w], 95)),
                                     "dyaw_p95": float(np.percentile(R_["dyaw"][w], 95)), "dz_p95": float(np.percentile(np.abs(R_["dz"][w]), 95))}
out.update({"r_valid_px": r_valid, "radius_table_1.0-2.0m": tab, "sigma_pos_m": sigma, "lateral_amplitude_m": amp, "by_range": by_range})
print("r_valid", r_valid, "sigma_pos", sigma, "amplitude", amp); print(json.dumps(by_range, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
