#!/usr/bin/env python3
"""Onboard camera frames for the world documentation (docs/thesis/world_images/onboard/), from EXISTING bags only.

Read-only with respect to stored data: each packed bag (bag/bag_0.db3.zst) is decompressed to a SCRATCH copy (with its
metadata.yaml), read with rosbags, and the copy is deleted afterwards. Nothing under ~/thesis_data is written.

Forward camera (/forward_camera/image, mono8 640x480): the frame nearest each requested ground-truth y is taken (y from
the trial's fwd_meas/gt_eval_only.npz, written by eval/fwd_eval.py), and the FROZEN Phase 3 vanishing point for that
same frame is drawn from fwd_meas/meas_frozen.npz (row k = the k-th forward image; matched by header stamp `t`).
Nothing is recomputed. A VP counts as a heading measurement when support >= s_min (eval/results/fwd_calibration.json
"frozen"); below that, the point is drawn hollow and labelled "no measurement" (support < s_min) or absent (NaN).

Downward camera (/downward_camera/image, rgb8 640x480): the only stored bags with it are room_tags flights; frames are
chosen by ground truth (/ground_truth/pose in the same bag): "hover" = airborne (z > 1 m) and horizontal speed
< 0.05 m/s; "cruise" = horizontal speed within 0.05 m/s of the commanded 0.5 m/s.

Run with ~/venv-fwd/bin/python (rosbags, numpy, Pillow, opencv):
  python sim/tools/onboard_frames.py --out docs/thesis/world_images/onboard --scratch <dir>
"""
import argparse, json, os, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rosbags.highlevel import AnyReader
from pathlib import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRIALS = os.path.expanduser("~/thesis_data/trials")
FWD = [("fwdc_tex_r1", [40.0, 150.0]), ("fwdplainc_tex_r1", [40.0, 150.0]), ("fwdc_trans_r1", [80.0]),
       ("fwdplainc_blank_r1", [40.0]), ("fwdc_blank_r1", [40.0])]
DOWN = [("tagchar_h20", ["hover", "cruise"]), ("tagchar_h30", ["cruise"])]
VP_OK, VP_NO = (230, 159, 0), (86, 180, 233)   # Okabe-Ito orange #E69F00 = valid heading, sky blue #56B4E9 = none
# (the estimator colours #0072B2 / #009E73 / #D55E00 are reserved for EKF3 / UKF / FGO in the thesis figures)
FONT = ImageFont.load_default()


def unpack(trial, scratch):
    src = os.path.join(TRIALS, trial, "bag")
    dst = os.path.join(scratch, trial + "_bag"); shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
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


def forward(trial, ys, scratch, out, s_min):
    meas = np.load(os.path.join(TRIALS, trial, "fwd_meas", "meas_frozen.npz"))
    g = np.load(os.path.join(TRIALS, trial, "fwd_meas", "gt_eval_only.npz"))["g"]
    want = {}
    for y in ys:
        i = int(np.argmin(np.abs(g[:, 2] - y)))
        k = int(np.argmin(np.abs(meas["t"] - g[i, 0])))
        want[k] = (y, g[i])
    bag = unpack(trial, scratch); rows = []
    try:
        with AnyReader([Path(bag)]) as r:
            con = [c for c in r.connections if c.topic == "/forward_camera/image"]
            for k, (c, _, raw) in enumerate(r.messages(connections=con)):
                if k not in want:
                    continue
                m = r.deserialize(raw, c.msgtype); t = stamp(m)
                assert abs(t - meas["t"][k]) < 1e-6, (trial, k, t, meas["t"][k])   # same frame as the frozen row
                y, gi = want[k]
                u, v, sup, psi = (float(meas[n][k, 0]) for n in ("u", "v", "support", "psi"))
                im = Image.fromarray(img(m)).convert("RGB"); d = ImageDraw.Draw(im)
                valid = np.isfinite(u) and sup >= s_min
                if np.isfinite(u) and np.isfinite(v):
                    col = VP_OK if valid else VP_NO
                    r0 = 9
                    d.ellipse([u - r0 - 2, v - r0 - 2, u + r0 + 2, v + r0 + 2], outline=(0, 0, 0), width=1)
                    d.ellipse([u - r0, v - r0, u + r0, v + r0], outline=col, width=3, fill=col if valid else None)
                    d.line([u - 22, v, u + 22, v], fill=col, width=2); d.line([u, v - 22, u, v + 22], fill=col, width=2)
                lab = ("VP (frozen Phase 3): u %.1f v %.1f px, support %.0f, heading %+.2f deg" % (u, v, sup, psi)
                       if valid else "frozen Phase 3: NO heading measurement (%s)"
                       % ("support %.0f < %d" % (sup, s_min) if np.isfinite(sup) and np.isfinite(u) else "no VP"))
                d.rectangle([0, 0, 640, 30], fill=(255, 255, 255))
                d.text((6, 3), "%s  t %.2f s  GT y %.1f m" % (trial, t, gi[2]), fill=(0, 0, 0), font=FONT)
                d.text((6, 16), lab, fill=(150, 100, 0) if valid else (20, 110, 170), font=FONT)
                f = "%s__fwd_y%03d.png" % (trial, round(y)); im.save(os.path.join(out, f))
                rows.append(dict(file=f, trial=trial, camera="forward", frame_index=k, t=t, gt_x=float(gi[1]),
                                 gt_y=float(gi[2]), vp_u=u, vp_v=v, support=sup, heading_deg=psi, valid=bool(valid)))
                if len(rows) == len(want):
                    break
    finally:
        shutil.rmtree(bag, ignore_errors=True)
    return rows


def downward(trial, kinds, scratch, out):
    bag = unpack(trial, scratch); rows = []
    try:
        with AnyReader([Path(bag)]) as r:
            gc = [c for c in r.connections if c.topic == "/ground_truth/pose"]
            G = np.array([(stamp(m), m.pose.position.x, m.pose.position.y, m.pose.position.z)
                          for m in (r.deserialize(raw, c.msgtype) for c, _, raw in r.messages(connections=gc))])
            dt = np.gradient(G[:, 0]); sp = np.hypot(np.gradient(G[:, 1]) / dt, np.gradient(G[:, 2]) / dt)
            sp = np.convolve(sp, np.ones(25) / 25, mode="same")
            pick = {}
            for kind in kinds:
                ok = (G[:, 3] > 1.0) & ((sp < 0.05) if kind == "hover" else (np.abs(sp - 0.5) < 0.05))
                idx = np.nonzero(ok)[0]
                pick[kind] = G[idx[len(idx) // 2], 0]                       # middle of the qualifying period
            ic = [c for c in r.connections if c.topic == "/downward_camera/image"]
            best = {k: (1e9, None, None) for k in pick}
            for c, _, raw in r.messages(connections=ic):
                m = r.deserialize(raw, c.msgtype); t = stamp(m)
                for k, tk in pick.items():
                    if abs(t - tk) < best[k][0]:
                        best[k] = (abs(t - tk), t, img(m))
            for k, (_, t, a) in best.items():
                j = int(np.argmin(np.abs(G[:, 0] - t)))
                im = Image.fromarray(a).convert("RGB"); d = ImageDraw.Draw(im)
                d.rectangle([0, 0, 640, 18], fill=(255, 255, 255))
                d.text((6, 3), "%s downward, %s  t %.2f s  GT (%.2f, %.2f, z %.2f) m  speed %.2f m/s"
                       % (trial, k, t, G[j, 1], G[j, 2], G[j, 3], sp[j]), fill=(0, 0, 0), font=FONT)
                f = "%s__down_%s.png" % (trial, k); im.save(os.path.join(out, f))
                rows.append(dict(file=f, trial=trial, camera="downward", kind=k, t=t, gt_x=G[j, 1], gt_y=G[j, 2],
                                 gt_z=G[j, 3], speed=float(sp[j])))
    finally:
        shutil.rmtree(bag, ignore_errors=True)
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--scratch", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); os.makedirs(a.scratch, exist_ok=True)
    s_min = json.load(open(os.path.join(REPO, "eval", "results", "fwd_calibration.json")))["frozen"]["s_min"]
    rows = []
    for t, k in DOWN:
        rows += downward(t, k, a.scratch, a.out); print(t, "done")
    for t, ys in FWD:
        rows += forward(t, ys, a.scratch, a.out, s_min); print(t, "done")
    json.dump(dict(s_min=s_min, frames=rows), open(os.path.join(a.out, "frames.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
