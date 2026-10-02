#!/usr/bin/env python3
"""Real-camera lens calibration (real-flight plan, tooling item 3). Chessboard views from a video or an image folder ->
intrinsics + distortion (OpenCV pinhole model with k1, k2, p1, p2, k3; or --fisheye). Writes calib.json, which
run_heading_video.py uses to resample real frames onto the FROZEN simulated forward camera (640x480, fx = 554.38,
cx/cy = 320/240, i.e. a 60 deg horizontal FOV pinhole), so the frozen heading program runs unchanged.

Capture advice: print a chessboard (e.g. 9x6 inner corners, 25 mm squares) flat on rigid board; record 20-40 s
moving it to fill the corners and edges of the image at several tilts; keep it sharp (good light, no motion blur).
A reprojection RMS below ~0.5 px is good; above ~1 px, recapture.

Usage (venv-fwd: OpenCV): python3 tools/real_camera/calibrate.py INPUT (video file or image folder)
          --cols 9 --rows 6 --square-mm 25 [--every-n 10] [--max-views 60] [--fisheye] [--out calib.json]"""
import argparse, glob, json, math, os, sys
import cv2
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--cols", type=int, required=True)
ap.add_argument("--rows", type=int, required=True); ap.add_argument("--square-mm", type=float, required=True)
ap.add_argument("--every-n", type=int, default=10); ap.add_argument("--max-views", type=int, default=60)
ap.add_argument("--fisheye", action="store_true"); ap.add_argument("--out", default="calib.json"); a = ap.parse_args()


def frames():
    if os.path.isdir(a.input):
        for p in sorted(glob.glob(os.path.join(a.input, "*"))):
            im = cv2.imread(p)
            if im is not None:
                yield p, im
    else:
        cap = cv2.VideoCapture(a.input); k = 0
        while True:
            ok, im = cap.read()
            if not ok:
                break
            if k % a.every_n == 0:
                yield f"frame{k}", im
            k += 1


pattern = (a.cols, a.rows)
objp = np.zeros((a.cols * a.rows, 1, 3), np.float64)
objp[:, 0, :2] = np.mgrid[0:a.cols, 0:a.rows].T.reshape(-1, 2) * a.square_mm / 1000.0
obj, img, size, used = [], [], None, []
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
for name, im in frames():
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) if im.ndim == 3 else im
    size = g.shape[::-1]
    ok, c = cv2.findChessboardCorners(g, pattern, cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE)
    if not ok:
        continue
    c = cv2.cornerSubPix(g, c, (11, 11), (-1, -1), crit)
    obj.append(objp.copy()); img.append(c.astype(np.float64)); used.append(name)
    if len(obj) >= a.max_views:
        break
if len(obj) < 10:
    sys.exit(f"only {len(obj)} chessboard views found (need >= 10): recapture, or check --cols/--rows (INNER corners)")
if a.fisheye:
    K, D = np.zeros((3, 3)), np.zeros((4, 1))
    rms, K, D, _, _ = cv2.fisheye.calibrate([o.reshape(-1, 1, 3) for o in obj], [i.reshape(-1, 1, 2) for i in img], size, K, D,
                                            flags=cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC | cv2.fisheye.CALIB_FIX_SKEW, criteria=crit)
else:
    rms, K, D, _, _ = cv2.calibrateCamera([o.astype(np.float32) for o in obj], [i.astype(np.float32) for i in img], size, None, None)
fov_h = 2 * math.degrees(math.atan(size[0] / 2 / K[0, 0])); fov_v = 2 * math.degrees(math.atan(size[1] / 2 / K[1, 1]))
out = {"model": "fisheye" if a.fisheye else "pinhole", "image_size": list(size), "K": K.tolist(), "dist": D.ravel().tolist(),
       "rms_px": float(rms), "n_views": len(obj), "fov_h_deg_approx": fov_h, "fov_v_deg_approx": fov_v,
       "pattern": {"cols": a.cols, "rows": a.rows, "square_mm": a.square_mm}, "input": os.path.abspath(a.input)}
json.dump(out, open(a.out, "w"), indent=1)
print(json.dumps({k: out[k] for k in ("model", "image_size", "rms_px", "n_views", "fov_h_deg_approx", "fov_v_deg_approx")}))
print("FROZEN camera needs a horizontal FOV >= 60 deg (else the resampled image has blank borders):",
      "OK" if fov_h >= 60 else f"NARROWER ({fov_h:.1f} deg)")
print(f"wrote {a.out}")
