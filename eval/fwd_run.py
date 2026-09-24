#!/usr/bin/env python3
"""Run the Phase 3 forward-camera measurements over every forward frame of one bag.

Pure measurement: reads /forward_camera/image only (no ground truth, no other sensor).
For every frame and every inlier tolerance in INLIER_GRID it stores the heading output
and its support; for every box size in BOX_GRID it stores the yaw rate and the number of
tracked corners (box centred on the previous frame's VP for the same tolerance). The
calibrated choice among these (METHODOLOGY, Phase 3) is applied at evaluation time.

Output: <trial>/fwd_meas/meas.npz

--frozen restricts both grids to the calibrated values in eval/results/fwd_calibration.json
(validation runs). Per frame it computes exactly the same numbers as the full grid for
those values: the same segments, the same per-frame seed, and each tolerance's VP chain
is independent of the others. Output: fwd_meas/meas_frozen.npz. --max-frames N is for
identity checks only.

Usage (venv-fwd: rosbags + OpenCV): python3 eval/fwd_run.py TRIAL [--frozen] [--max-frames N]
"""
import os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "forward_camera"))
import fwd_measure as F

INLIER_GRID = (0.5, 1.0, 1.5)
BOX_GRID = (40, 80, 160)
TD = os.path.expanduser("~/thesis_data/trials")
ts = get_typestore(Stores.ROS2_JAZZY)


def main(trial, frozen=False, max_frames=None, tag=None):
    global INLIER_GRID, BOX_GRID
    if frozen:
        import json
        c = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "fwd_calibration.json")))["frozen"]
        INLIER_GRID, BOX_GRID = (c["inlier_deg"],), (c["box_half_px"],)
    out_dir = f"{TD}/{trial}/fwd_meas"; os.makedirs(out_dir, exist_ok=True)
    ni, nb = len(INLIER_GRID), len(BOX_GRID)
    T, PSI, U, V, SUP, NIN, OM, NTR = [], [], [], [], [], [], [], []
    prev, prev_t, prev_vp = None, None, [None] * ni
    with Reader(f"{TD}/{trial}/bag") as r:
        conns = [c for c in r.connections if c.topic == "/forward_camera/image"]
        for k, (con, _, raw) in enumerate(r.messages(connections=conns)):
            if max_frames is not None and k >= max_frames:
                break
            m = ts.deserialize_cdr(raw, con.msgtype)
            assert m.encoding == "mono8"
            img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.step)[:, :m.width].copy()
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            segs = F.segments(img)
            psi, u, v, sup, nin = (np.full(ni, np.nan) for _ in range(5))
            om, ntr = np.full((ni, nb), np.nan), np.zeros((ni, nb))
            for i, thr in enumerate(INLIER_GRID):
                h = F.heading(img, seed=k, inlier_deg=thr, segs=segs)
                if h["psi_deg"] is not None:
                    psi[i], u[i], v[i], sup[i], nin[i] = h["psi_deg"], h["u"], h["v"], h["support"], h["n_inl"]
                if prev is not None and prev_vp[i] is not None and t > prev_t:
                    for j, b in enumerate(BOX_GRID):
                        w = F.yaw_rate(prev, img, prev_vp[i][0], prev_vp[i][1], t - prev_t, b)
                        if w["omega_dps"] is not None:
                            om[i, j], ntr[i, j] = w["omega_dps"], w["n_trk"]
                prev_vp[i] = None if h["psi_deg"] is None else (h["u"], h["v"])
            T.append(t); PSI.append(psi); U.append(u); V.append(v); SUP.append(sup); NIN.append(nin)
            OM.append(om); NTR.append(ntr)
            prev, prev_t = img, t
    name = tag or ("meas_frozen.npz" if frozen else "meas.npz")
    np.savez_compressed(f"{out_dir}/{name}", t=np.array(T), psi=np.array(PSI), u=np.array(U), v=np.array(V),
                        support=np.array(SUP), n_inl=np.array(NIN), omega=np.array(OM), n_trk=np.array(NTR),
                        inlier_grid=np.array(INLIER_GRID), box_grid=np.array(BOX_GRID))
    print(f"{trial}: {len(T)} frames -> {out_dir}/{name}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--frozen", action="store_true")
    ap.add_argument("--max-frames", type=int); ap.add_argument("--tag")
    a = ap.parse_args()
    main(a.trial, a.frozen, a.max_frames, a.tag)
