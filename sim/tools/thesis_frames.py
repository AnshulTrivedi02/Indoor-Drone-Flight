#!/usr/bin/env python3
"""Onboard camera frames for the thesis reader-facing figure set (docs/thesis/world_images/thesis/), read-only from
EXISTING stored bags. Replaces the overlaid frames in docs/thesis/world_images/onboard/ with two kinds of output per
requested frame: a RAW frame straight off the image topic (no text, no drawn marker at all) and, for the forward
camera only, a SEPARATE vanishing-point variant that draws only the marker (no text either).

The vanishing-point marker is the already-computed, frozen Phase 3 heading measurement for that exact frame
(fwd_meas/meas_frozen.npz, row k = the k-th forward image; matched by header stamp), read back here, not
recomputed - this script performs no estimation of its own.

Read-only with respect to stored data: each packed bag (bag/bag_0.db3.zst) is decompressed to a SCRATCH copy, read
with rosbags, and the copy is deleted afterwards. Nothing under ~/thesis_data is written. No world file, trial data
or result is touched.

One trial per invocation (run via heavy.py, one at a time, per the bag-reading rule):
  ~/venv-fwd/bin/python3 sim/tools/thesis_frames.py forward <trial> <y_m> --out DIR --scratch DIR
  ~/venv-fwd/bin/python3 sim/tools/thesis_frames.py downward <trial> <kind> --out DIR --scratch DIR
"""
import argparse, json, os, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw
from rosbags.highlevel import AnyReader
from pathlib import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRIALS = os.path.expanduser("~/thesis_data/trials")
VP_OK, VP_NO = (230, 159, 0), (86, 180, 233)   # Okabe-Ito orange = valid heading, sky blue = no measurement


def unpack(trial, scratch):
    src = os.path.join(TRIALS, trial, "bag")
    dst = os.path.join(scratch, trial + "_bag")
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    shutil.copyfile(os.path.join(src, "metadata.yaml"), os.path.join(dst, "metadata.yaml"))
    if os.path.exists(os.path.join(src, "bag_0.db3.zst")):
        subprocess.run(["zstd", "-d", "-q", os.path.join(src, "bag_0.db3.zst"), "-o", os.path.join(dst, "bag_0.db3")],
                       check=True)
    else:
        shutil.copyfile(os.path.join(src, "bag_0.db3"), os.path.join(dst, "bag_0.db3"))
    return dst


def img(msg):
    ch = {"mono8": 1, "rgb8": 3, "bgr8": 3}[msg.encoding]
    a = np.frombuffer(bytes(msg.data), np.uint8).reshape(msg.height, msg.step)[:, :msg.width * ch]
    a = a.reshape(msg.height, msg.width, ch) if ch > 1 else a
    return a[..., ::-1] if msg.encoding == "bgr8" else a


def stamp(msg):
    return msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9


def forward(trial, y, scratch, out, s_min):
    meas = np.load(os.path.join(TRIALS, trial, "fwd_meas", "meas_frozen.npz"))
    g = np.load(os.path.join(TRIALS, trial, "fwd_meas", "gt_eval_only.npz"))["g"]
    i = int(np.argmin(np.abs(g[:, 2] - y)))
    k = int(np.argmin(np.abs(meas["t"] - g[i, 0])))
    bag = unpack(trial, scratch)
    row = None
    try:
        with AnyReader([Path(bag)]) as r:
            con = [c for c in r.connections if c.topic == "/forward_camera/image"]
            for kk, (c, _, raw) in enumerate(r.messages(connections=con)):
                if kk != k:
                    continue
                m = r.deserialize(raw, c.msgtype)
                t = stamp(m)
                assert abs(t - meas["t"][k]) < 1e-6, (trial, k, t, meas["t"][k])
                a = img(m)
                u, v, sup, psi = (float(meas[n][k, 0]) for n in ("u", "v", "support", "psi"))
                raw_name = "%s_fwd_raw.png" % trial
                Image.fromarray(a).save(os.path.join(out, raw_name))
                valid = np.isfinite(u) and sup >= s_min
                vp_im = Image.fromarray(a).convert("RGB")
                d = ImageDraw.Draw(vp_im)
                if np.isfinite(u) and np.isfinite(v):
                    col = VP_OK if valid else VP_NO
                    r0 = 9
                    d.ellipse([u - r0 - 2, v - r0 - 2, u + r0 + 2, v + r0 + 2], outline=(0, 0, 0), width=1)
                    d.ellipse([u - r0, v - r0, u + r0, v + r0], outline=col, width=3, fill=col if valid else None)
                    d.line([u - 22, v, u + 22, v], fill=col, width=2)
                    d.line([u, v - 22, u, v + 22], fill=col, width=2)
                vp_name = "%s_fwd_vp.png" % trial
                vp_im.save(os.path.join(out, vp_name))
                row = dict(trial=trial, raw=raw_name, vp=vp_name, requested_y=y, gt_y=float(g[i, 2]),
                           gt_x=float(g[i, 1]), frame_index=k, t=t, vp_u=u, vp_v=v, support=sup,
                           heading_deg=psi, valid=bool(valid))
                break
    finally:
        shutil.rmtree(bag, ignore_errors=True)
    return row


def downward(trial, kind, scratch, out):
    bag = unpack(trial, scratch)
    row = None
    try:
        with AnyReader([Path(bag)]) as r:
            gc = [c for c in r.connections if c.topic == "/ground_truth/pose"]
            G = np.array([(stamp(m), m.pose.position.x, m.pose.position.y, m.pose.position.z)
                          for m in (r.deserialize(raw, c.msgtype) for c, _, raw in r.messages(connections=gc))])
            dt = np.gradient(G[:, 0])
            sp = np.hypot(np.gradient(G[:, 1]) / dt, np.gradient(G[:, 2]) / dt)
            sp = np.convolve(sp, np.ones(25) / 25, mode="same")
            ok = (G[:, 3] > 1.0) & ((sp < 0.05) if kind == "hover" else (np.abs(sp - 0.5) < 0.05))
            idx = np.nonzero(ok)[0]
            t_want = G[idx[len(idx) // 2], 0]
            ic = [c for c in r.connections if c.topic == "/downward_camera/image"]
            best = (1e9, None, None)
            for c, _, raw in r.messages(connections=ic):
                m = r.deserialize(raw, c.msgtype)
                t = stamp(m)
                if abs(t - t_want) < best[0]:
                    best = (abs(t - t_want), t, img(m))
            _, t, a = best
            j = int(np.argmin(np.abs(G[:, 0] - t)))
            name = "%s_down_%s_raw.png" % (trial, kind)
            Image.fromarray(a).save(os.path.join(out, name))
            row = dict(trial=trial, kind=kind, file=name, t=t, gt_x=float(G[j, 1]), gt_y=float(G[j, 2]),
                       gt_z=float(G[j, 3]), speed=float(sp[j]))
    finally:
        shutil.rmtree(bag, ignore_errors=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["forward", "downward"])
    ap.add_argument("trial")
    ap.add_argument("param")  # y (m) for forward, kind (hover/cruise) for downward
    ap.add_argument("--out", required=True)
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.scratch, exist_ok=True)
    result_path = os.path.join(a.out, "_extract_%s_%s.json" % (a.mode, a.trial))
    if a.mode == "forward":
        s_min = json.load(open(os.path.join(REPO, "eval", "results", "fwd_calibration.json")))["frozen"]["s_min"]
        row = forward(a.trial, float(a.param), a.scratch, a.out, s_min)
    else:
        row = downward(a.trial, a.param, a.scratch, a.out)
    json.dump(row, open(result_path, "w"), indent=1, default=float)
    print(json.dumps(row, indent=1, default=float))


if __name__ == "__main__":
    main()
