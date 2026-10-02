#!/usr/bin/env python3
"""Self-test of the real-camera calibration step (no real camera needed). Renders N synthetic chessboard views through a
KNOWN distorted pinhole camera (each output pixel is undistorted to a ray and intersected with the board plane), runs
tools/real_camera/calibrate.py on them, and checks the recovered intrinsics and distortion against the truth. Then checks
the resampling onto the frozen camera: a distorted view of a straight line must come out straight in the frozen 640x480
frame (max deviation from its fitted line, px).
Usage (venv-fwd): python3 tools/real_camera/selftest_calibration.py [--out-dir DIR]"""
import argparse, json, math, os, subprocess, sys
import cv2
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", default="/tmp/real_camera_selftest"); a = ap.parse_args()
os.makedirs(f"{a.out_dir}/views", exist_ok=True)
W, H = 1280, 720
K = np.array([[900.0, 0, 640.0], [0, 900.0, 360.0], [0, 0, 1]]); D = np.array([-0.25, 0.08, 0.0005, -0.0003, 0.0])
COLS, ROWS, SQ = 9, 6, 0.025                                  # inner corners, square size (m)
rng = np.random.default_rng(1)
# pixel grid -> normalised undistorted rays (once)
uv = np.stack(np.meshgrid(np.arange(W), np.arange(H)), -1).reshape(-1, 1, 2).astype(np.float64)
rays = cv2.undistortPoints(uv, K, D).reshape(-1, 2)            # x/z, y/z
rays = np.c_[rays, np.ones(len(rays))]
n_ok = 0
for i in range(30):
    rv = np.array([rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3)])
    R, _ = cv2.Rodrigues(rv); t = np.array([rng.uniform(-0.08, 0.08), rng.uniform(-0.05, 0.05), rng.uniform(0.35, 0.6)])
    n = R[:, 2]; d = n @ t                                     # plane: n.(X - t) = 0 in camera frame
    s = d / (rays @ n); P = rays * s[:, None]                  # intersection points
    loc = (P - t) @ R                                          # board coordinates (x, y, ~0)
    gx = np.floor(loc[:, 0] / SQ + 1); gy = np.floor(loc[:, 1] / SQ + 1)
    inside = (gx >= 0) & (gx < COLS + 1) & (gy >= 0) & (gy < ROWS + 1) & (s > 0)
    img = np.full(len(rays), 200, np.uint8)
    img[inside] = np.where(((gx + gy) % 2 == 0)[inside], 30, 225)
    cv2.imwrite(f"{a.out_dir}/views/v_{i:02d}.png", cv2.GaussianBlur(img.reshape(H, W), (3, 3), 0.6))
r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibrate.py"), f"{a.out_dir}/views",
                    "--cols", str(COLS), "--rows", str(ROWS), "--square-mm", str(SQ * 1000), "--out", f"{a.out_dir}/calib.json"],
                   capture_output=True, text=True)
print(r.stdout.strip()); c = json.load(open(f"{a.out_dir}/calib.json")); Ke = np.array(c["K"]); De = np.array(c["dist"])
res = {"n_views": c["n_views"], "rms_px": c["rms_px"], "fx_rel_err": abs(Ke[0, 0] / K[0, 0] - 1), "fy_rel_err": abs(Ke[1, 1] / K[1, 1] - 1),
       "cx_err_px": abs(Ke[0, 2] - K[0, 2]), "cy_err_px": abs(Ke[1, 2] - K[1, 2]), "k1_err": abs(De[0] - D[0]), "k2_err": abs(De[1] - D[1])}
# straightness after resampling onto the frozen camera: project a 3-D straight line through the TRUE camera, then map
F = np.array([[554.3827056884766, 0, 320.0], [0, 554.3827056884766, 240.0], [0, 0, 1]])
X = np.c_[np.linspace(-0.25, 0.25, 60), np.full(60, 0.12), np.full(60, 0.5)]
pd, _ = cv2.projectPoints(X, np.zeros(3), np.zeros(3), K, D)
pf = cv2.undistortPoints(pd, Ke, De, P=F).reshape(-1, 2)
inF = (pf[:, 0] >= 0) & (pf[:, 0] < 640) & (pf[:, 1] >= 0) & (pf[:, 1] < 480)
A = np.c_[pf[inF, 0], np.ones(inF.sum())]; coef, *_ = np.linalg.lstsq(A, pf[inF, 1], rcond=None)
res["line_max_dev_px_in_frozen_frame"] = float(np.abs(A @ coef - pf[inF, 1]).max())
dist_raw = np.abs(np.polyval(np.polyfit(pd.reshape(-1, 2)[:, 0], pd.reshape(-1, 2)[:, 1], 1), pd.reshape(-1, 2)[:, 0]) - pd.reshape(-1, 2)[:, 1]).max()
res["line_max_dev_px_raw_distorted"] = float(dist_raw)
res["pass"] = bool(res["rms_px"] < 0.5 and res["fx_rel_err"] < 0.01 and res["k1_err"] < 0.02 and res["line_max_dev_px_in_frozen_frame"] < 0.5)
print(json.dumps(res, indent=1))
