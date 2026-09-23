#!/usr/bin/env python3
"""Extract sample frames from a trial bag's image topic at chosen ground-truth y positions.

For each requested y (m, along the corridor), saves the recorded frame whose stamp is
closest to the moment ground truth crosses that y, plus a contact sheet of all of them.

Usage (venv-evo: rosbags + numpy + Pillow):
  python3 eval/extract_frames.py TRIAL OUT_DIR [--topic /forward_camera/image] [--y 10,40,80,120,150]
"""
import argparse, os
import numpy as np
from PIL import Image, ImageDraw
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

TRIALS_DIR = os.path.expanduser("~/thesis_data/trials")
ts = get_typestore(Stores.ROS2_JAZZY)


def stamp(h):
    return h.stamp.sec + h.stamp.nanosec * 1e-9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial")
    ap.add_argument("out")
    ap.add_argument("--topic", default="/forward_camera/image")
    ap.add_argument("--y", default="10,40,80,120,150")
    a = ap.parse_args()
    ys = [float(v) for v in a.y.split(",")]
    os.makedirs(a.out, exist_ok=True)
    bag = f"{TRIALS_DIR}/{a.trial}/bag"
    gt = []
    with Reader(bag) as r:
        c = [x for x in r.connections if x.topic == "/ground_truth/pose"]
        for con, _, raw in r.messages(connections=c):
            m = ts.deserialize_cdr(raw, con.msgtype)
            gt.append((stamp(m.header), m.pose.position.y))
    gt = np.array(sorted(gt))
    # first crossing of each y after takeoff (GT y is monotonic during cruise)
    targets = {y: gt[np.argmax(gt[:, 1] >= y), 0] for y in ys if gt[:, 1].max() >= y}
    best = {y: (np.inf, None) for y in targets}
    with Reader(bag) as r:
        c = [x for x in r.connections if x.topic == a.topic]
        for con, t, raw in r.messages(connections=c):
            m = ts.deserialize_cdr(raw, con.msgtype)
            st = stamp(m.header)
            for y, tt in targets.items():
                if abs(st - tt) < best[y][0]:
                    ch = 1 if m.encoding == "mono8" else 3
                    img = np.frombuffer(bytes(m.data), np.uint8).reshape(m.height, m.step)[:, :m.width * ch]
                    best[y] = (abs(st - tt), img.reshape(m.height, m.width, ch) if ch > 1 else img.copy(), st)
    tiles = []
    for y, (dt, img, st) in best.items():
        im = Image.fromarray(img)
        im.save(os.path.join(a.out, f"{a.trial}_y{int(y):03d}.png"))
        t = im.convert("L").resize((320, 240))
        ImageDraw.Draw(t).text((5, 5), f"{a.trial}  y={y:.0f} m  t={st:.2f} s", fill=255)
        tiles.append(t)
        print(f"y={y:6.1f} m  frame t={st:.3f} s  (|dt| {dt*1e3:.1f} ms)")
    sheet = Image.new("L", (320 * len(tiles), 240))
    for i, t in enumerate(tiles):
        sheet.paste(t, (320 * i, 0))
    sheet.save(os.path.join(a.out, f"{a.trial}_sheet.png"))


if __name__ == "__main__":
    main()
