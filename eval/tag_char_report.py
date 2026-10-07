#!/usr/bin/env python3
"""Tag module characterisation (experiments T/L; reported BEFORE any estimator uses tags). Per trial (recorded with
downward images): for every frame, each mapped tag's 4 corners are projected into the image with the GROUND-TRUTH body
pose (tag_measure's frozen frames), giving which tags are fully visible. Then:
  * detection rate: fully-visible tags that were detected (correct id), by height;
  * wrong ids / detections of tags not visible (false positives);
  * detection range: the ground distance from the camera nadir to the tag centre at detection (max, p95);
  * pose error of the vehicle pose from each detection against GT: horizontal position, height, yaw, tilt;
    by height and by the tag's radial position in the image (centre / middle / edge thirds of the half-diagonal);
  * processing time per frame (detection + pose), single thread.
Usage (venv-tags): python3 eval/tag_char_report.py TRIAL... [--json OUT]"""
import argparse, json, math, os, sys, time
import cv2
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "tags")); import tag_measure as T
ap = argparse.ArgumentParser(); ap.add_argument("trials", nargs="+"); ap.add_argument("--json")
ap.add_argument("--map", default=os.path.join(ROOT, "sim", "worlds", "room_tags_map.json")); a = ap.parse_args()
tm = T.load_map(a.map); FX, CX, CY = 554.3827056884766, 320.0, 240.0
K = np.array([[FX, 0, CX], [0, FX, CY], [0, 0, 1]]); D = T.TagDetector(FX, FX, CX, CY)
half = T.TAG_SIZE_M / 2; ts = get_typestore(Stores.ROS2_JAZZY); out = {}
M = T.CONVENTIONS[T.TEXTURE_CONVENTION]


def corners_world(i):
    R_wt = T.rz(tm[i]["yaw"]) @ M
    return [tm[i]["p"] + R_wt @ np.array([sx * half, sy * half, 0.0]) for sx, sy in ((-1, 1), (1, 1), (1, -1), (-1, -1))]


def project(pw, p_wb, R_wb):
    R_wc = R_wb @ T.R_BODY_CAM; p_wc = p_wb + R_wb @ T.T_BODY_CAM_POS
    pc = R_wc.T @ (pw - p_wc)
    if pc[2] <= 0: return None
    u = K @ (pc / pc[2]); return u[:2]


for tr in a.trials:
    G, I = [], []
    with Reader(os.path.expanduser(f"~/thesis_data/trials/{tr}/bag")) as r:
        cs = {c.topic: c for c in r.connections}
        for c, _, raw in r.messages(connections=[cs["/ground_truth/pose"], cs["/downward_camera/image"]]):
            m = ts.deserialize_cdr(raw, c.msgtype); t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if c.topic == "/ground_truth/pose":
                q = m.pose.orientation; G.append((t, m.pose.position.x, m.pose.position.y, m.pose.position.z, q.x, q.y, q.z, q.w))
            else:
                I.append((t, np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, 3)))
    G = np.array(G); rows = []; n_vis = n_det_vis = n_false = n_wrong = 0; proc = []
    for t, img in I:
        j = np.argmin(np.abs(G[:, 0] - t)); p_wb = G[j, 1:4]; R_wb = Rot.from_quat(G[j, 4:8]).as_matrix()
        if p_wb[2] < 1.0:
            continue
        vis = set()
        for i in tm:
            uv = [project(c, p_wb, R_wb) for c in corners_world(i)]
            if all(u is not None and 0 <= u[0] < 640 and 0 <= u[1] < 480 for u in uv):
                vis.add(i)
        t0 = time.perf_counter(); dets = D.detect(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)); proc.append(time.perf_counter() - t0)
        got = {d[0] for d in dets}
        n_vis += len(vis); n_det_vis += len(vis & got); n_false += len(got - vis)
        for (i, R, tt, cn, cc, dm, hm) in dets:
            if i not in tm:
                n_wrong += 1; continue
            pe, Re = T.vehicle_pose(tm[i], R, tt)
            dyaw = math.degrees((T.yaw_of(Re) - T.yaw_of(R_wb) + math.pi) % (2 * math.pi) - math.pi)
            tilt_err = math.degrees(np.arccos(np.clip(((Re @ np.array([0, 0, 1])) @ (R_wb @ np.array([0, 0, 1]))), -1, 1)))
            rad = math.hypot(cc[0] - CX, cc[1] - CY) / math.hypot(CX, CY)
            nadir = p_wb + R_wb @ T.T_BODY_CAM_POS
            rows.append({"h": float(p_wb[2]), "rad": rad, "ground_dist": float(np.hypot(*(tm[i]["p"][:2] - nadir[:2]))),
                         "dxy": float(np.hypot(*(pe[:2] - p_wb[:2]))), "dz": float(pe[2] - p_wb[2]), "dyaw": dyaw, "dtilt": tilt_err,
                         "margin": dm, "side_px": float(np.mean(np.linalg.norm(np.roll(cn, -1, 0) - cn, axis=1)))})
    R_ = {k: np.array([x[k] for x in rows]) for k in (rows[0] if rows else {})}
    def st(x): return {"median": float(np.median(x)), "p95": float(np.percentile(x, 95)), "max": float(np.max(np.abs(x)))} if len(x) else None
    by_rad = {}
    for lo, hi, nm in ((0, 1 / 3, "centre"), (1 / 3, 2 / 3, "middle"), (2 / 3, 1.01, "edge")):
        w = (R_["rad"] >= lo) & (R_["rad"] < hi) if rows else []
        if rows and w.any():
            by_rad[nm] = {"n": int(w.sum()), "dxy_m": st(R_["dxy"][w]), "abs_dyaw_deg": st(np.abs(R_["dyaw"][w]))}
    out[tr] = {"height_m_median": float(np.median(R_["h"])) if rows else None, "frames": len(I), "detections": len(rows),
               "visible_tag_frames": n_vis, "detection_rate_visible": (n_det_vis / n_vis) if n_vis else None,
               "detections_not_visible": n_false, "unknown_ids": n_wrong,
               "ground_dist_m": st(R_["ground_dist"]) if rows else None, "tag_side_px": st(R_["side_px"]) if rows else None,
               "dxy_m": st(R_["dxy"]) if rows else None, "dz_m": st(R_["dz"]) if rows else None,
               "abs_dyaw_deg": st(np.abs(R_["dyaw"])) if rows else None, "dtilt_deg": st(R_["dtilt"]) if rows else None,
               "by_image_radius": by_rad, "proc_ms": {"median": 1e3 * float(np.median(proc)), "p99": 1e3 * float(np.percentile(proc, 99))} if proc else None}
    o = out[tr]
    print(f"{tr}: h {o['height_m_median']:.2f} m | detected {o['detections']} | rate (visible) {o['detection_rate_visible']:.3f} | "
          f"false {o['detections_not_visible']} unknown {o['unknown_ids']} | ground dist max {o['ground_dist_m']['max']:.2f} m | "
          f"dxy median {o['dxy_m']['median']*1e3:.1f} p95 {o['dxy_m']['p95']*1e3:.1f} mm | |dyaw| median {o['abs_dyaw_deg']['median']:.3f} p95 "
          f"{o['abs_dyaw_deg']['p95']:.3f} deg | dz median {o['dz_m']['median']*1e3:.1f} mm | proc {o['proc_ms']['median']:.1f} ms")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
