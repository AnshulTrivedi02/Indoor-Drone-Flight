#!/usr/bin/env python3
"""Run the FROZEN heading program on a recorded real video (real-flight plan, tooling item 3). Nothing here changes
the method or its frozen parameters (inlier 0.5 deg, S_MIN 200 px; eval/results/fwd_calibration.json "frozen").

Geometry. The frozen program assumes the simulated forward camera: 640x480 pinhole, fx = fy = 554.38, cx/cy = 320/240
(60 deg horizontal FOV), mono 8-bit. Each real frame is UNDISTORTED with calib.json (tools/real_camera/calibrate.py) and
RESAMPLED onto exactly that virtual camera (cv2.initUndistortRectifyMap with the frozen K as the new camera matrix), so
the measurement sees the geometry it was calibrated for. The printed coverage is the fraction of the virtual image
that real pixels fill (< 100% if the real lens is narrower than 60 deg: blank borders, fewer line segments).

Two test modes:
  * --truth SEGMENTS.csv (t_start_s,t_end_s,yaw_deg; yaw positive = nose LEFT, the heading program's sign): a camera
    rotated through known angles on a table (e.g. a turntable or a protractor-marked board). Reports, per segment,
    availability and the median heading; then, after removing ONE constant offset (median over segments), the residual
    bias, the robust noise (1.4826 x MAD) and the outlier share (> 3 deg). These are compared, as a DIAGNOSTIC only, with
    Phase 3's validation bars (availability 70 %, |bias| 0.5 deg, noise 1.0 deg, outliers 5 %).
  * no truth (e.g. a phone walked down a real corridor): availability, heading statistics and the frame-to-frame jump
    distribution; with --overlay, a video with the detected vanishing point and heading drawn on the resampled frames.
A real-camera VALIDATION (and any change to the frozen parameters) needs its own pre-registration; this is a test tool.

Usage (venv-fwd): python3 tools/real_camera/run_heading_video.py VIDEO [--calib calib.json] [--truth seg.csv]
          [--every-n 1] [--impl cpp|python] [--out run.csv] [--overlay out.mp4] [--start-s 0] [--end-s inf]"""
import argparse, csv, json, math, os, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src", "forward_camera"))
from heading_bridge_core import HeadingCore

FX_FROZEN, CX_FROZEN, CY_FROZEN, W, H = 554.3827056884766, 320.0, 240.0, 640, 480
K_FROZEN = np.array([[FX_FROZEN, 0, CX_FROZEN], [0, FX_FROZEN, CY_FROZEN], [0, 0, 1.0]])
BAR = {"avail_pct": 70.0, "bias_deg": 0.5, "noise_deg": 1.0, "outlier_pct": 5.0, "outlier_thr_deg": 3.0}

ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--calib"); ap.add_argument("--truth")
ap.add_argument("--every-n", type=int, default=1); ap.add_argument("--impl", default="cpp", choices=["cpp", "python"])
ap.add_argument("--out", default="heading_run.csv"); ap.add_argument("--overlay"); ap.add_argument("--start-s", type=float, default=0.0)
ap.add_argument("--end-s", type=float, default=math.inf); a = ap.parse_args()

fz = json.load(open(os.path.join(ROOT, "eval", "results", "fwd_calibration.json")))["frozen"]
core = HeadingCore(fz["inlier_deg"], fz["s_min"], 5.0, every_n=a.every_n, impl=a.impl)
cap = cv2.VideoCapture(a.video)
if not cap.isOpened():
    sys.exit(f"cannot open {a.video}")
src_w, src_h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

# undistort + resample map onto the frozen virtual camera
if a.calib:
    c = json.load(open(a.calib)); K = np.array(c["K"]); D = np.array(c["dist"])
    if tuple(c["image_size"]) != (src_w, src_h):
        s = src_w / c["image_size"][0]                       # same aspect assumed: scale the intrinsics
        K = K.copy(); K[:2] *= s
        print(f"note: calib image size {c['image_size']} != video {src_w}x{src_h}; intrinsics scaled by {s:.3f}")
    if c["model"] == "fisheye":
        m1, m2 = cv2.fisheye.initUndistortRectifyMap(K, D.reshape(4, 1), np.eye(3), K_FROZEN, (W, H), cv2.CV_32FC1)
    else:
        m1, m2 = cv2.initUndistortRectifyMap(K, D, None, K_FROZEN, (W, H), cv2.CV_32FC1)
else:
    print("WARNING: no --calib: assuming an UNDISTORTED pinhole with the frozen FOV, i.e. a plain resize; fine only for "
          "a synthetic or already-rectified video")
    m1 = m2 = None
cov = None
if m1 is not None:
    inside = (m1 >= 0) & (m1 <= src_w - 1) & (m2 >= 0) & (m2 <= src_h - 1); cov = float(100 * inside.mean())
    print(f"coverage of the frozen 640x480 view by real pixels: {cov:.1f} %" + ("" if cov > 99.5 else "  (narrower lens: blank borders)"))

vw = None
if a.overlay:
    vw = cv2.VideoWriter(a.overlay, cv2.VideoWriter_fourcc(*"mp4v"), fps / a.every_n, (W, H))
rows = []; k = 0
while True:
    ok, fr = cap.read()
    if not ok:
        break
    t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
    if t < a.start_s:
        k += 1; continue
    if t > a.end_s:
        break
    if not core.selected(k):
        k += 1; continue
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY) if fr.ndim == 3 else fr
    img = cv2.remap(g, m1, m2, cv2.INTER_LINEAR) if m1 is not None else cv2.resize(g, (W, H), interpolation=cv2.INTER_AREA)
    psi, sup, valid, dt = core.measure(k, img)
    q = core.quality(psi, sup)
    rows.append((k, t, psi, sup, int(valid), q, dt * 1e3))
    if vw is not None:
        o = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if psi is not None and a.impl == "cpp":
            pu, pv = core._dout[1], core._dout[2]
            cv2.circle(o, (int(round(pu)), int(round(pv))), 8, (0, 0, 255) if valid else (0, 165, 255), 2)
        txt = "no VP" if psi is None else f"psi {psi:+.2f} deg  support {sup:.0f}  {'VALID' if valid else 'invalid'}"
        cv2.putText(o, f"t {t:7.2f}s  {txt}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)
        vw.write(o)
    k += 1
if vw is not None:
    vw.release()
with open(a.out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["k", "t_s", "psi_deg", "support", "valid", "quality", "proc_ms"])
    for r in rows:
        w.writerow([r[0], f"{r[1]:.4f}", "" if r[2] is None else repr(float(r[2])), repr(float(r[3])), r[4], r[5], f"{r[6]:.2f}"])

R = np.array([(r[1], np.nan if r[2] is None else r[2], r[4], r[6]) for r in rows]) if rows else np.zeros((0, 4))
summ = {"video": a.video, "frames_processed": len(rows), "coverage_pct": cov, "impl": a.impl,
        "avail_pct": float(100 * R[:, 2].mean()) if len(R) else None,
        "proc_ms_median": float(np.median(R[:, 3])) if len(R) else None, "proc_ms_p99": float(np.percentile(R[:, 3], 99)) if len(R) else None}
v = R[R[:, 2] == 1] if len(R) else R
if len(v) > 1:
    jumps = np.abs(np.diff(v[:, 1]))
    summ.update({"psi_median_deg": float(np.median(v[:, 1])), "psi_p5_p95_deg": [float(np.percentile(v[:, 1], 5)), float(np.percentile(v[:, 1], 95))],
                 "frame_jump_median_deg": float(np.median(jumps)), "frame_jump_p99_deg": float(np.percentile(jumps, 99))})
if a.truth:
    segs = [(float(r[0]), float(r[1]), float(r[2])) for r in csv.reader(open(a.truth)) if r and not r[0].startswith("#")]
    per = []
    for t0, t1, y in segs:
        w_ = (R[:, 0] >= t0) & (R[:, 0] <= t1); vv = w_ & (R[:, 2] == 1)
        per.append({"t": [t0, t1], "truth_deg": y, "n": int(w_.sum()), "avail_pct": float(100 * vv.sum() / max(w_.sum(), 1)),
                    "psi_median_deg": float(np.median(R[vv, 1])) if vv.any() else None, "_vals": R[vv, 1] - y})
    off = float(np.median([p["psi_median_deg"] - p["truth_deg"] for p in per if p["psi_median_deg"] is not None]))
    res = np.concatenate([p["_vals"] - off for p in per]) if per else np.zeros(0)
    seg_bias = [p["psi_median_deg"] - p["truth_deg"] - off for p in per if p["psi_median_deg"] is not None]
    noise = float(1.4826 * np.median(np.abs(res - np.median(res)))) if len(res) else None
    outl = float(100 * np.mean(np.abs(res) > BAR["outlier_thr_deg"])) if len(res) else None
    avail = float(np.mean([p["avail_pct"] for p in per]))
    summ["table_test"] = {"segments": [{k_: v_ for k_, v_ in p.items() if k_ != "_vals"} for p in per], "constant_offset_deg": off,
                          "max_abs_segment_bias_deg": float(np.max(np.abs(seg_bias))) if seg_bias else None, "noise_deg": noise,
                          "outlier_pct": outl, "avail_pct_mean": avail,
                          "diagnostic_vs_phase3_bars": {"avail": avail >= BAR["avail_pct"],
                                                        "bias": bool(seg_bias) and max(abs(b) for b in seg_bias) <= BAR["bias_deg"],
                                                        "noise": noise is not None and noise <= BAR["noise_deg"],
                                                        "outliers": outl is not None and outl <= BAR["outlier_pct"]}}
json.dump(summ, open(os.path.splitext(a.out)[0] + "_summary.json", "w"), indent=1, default=str)
print(json.dumps(summ, indent=1, default=str)[:2500])
