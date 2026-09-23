#!/usr/bin/env python3
"""Generate the forward-camera wall textures (deterministic, seeded).

Side walls (`corridor_wall_lined`), one image per 10 m x 5 m segment, 1 cm/px:
  - HORIZONTAL black lines every 0.5 m (z = 0.5 ... 4.5 m), 8 cm thick, on a white base. They run
    parallel to the corridor axis, so in the forward camera they converge on the
    corridor vanishing point. This is the heading-from-structure cue.
  - NON-PERIODIC vertical structure: vertical bars of random width (3-20 cm), random
    grey level (darker than the base), random height and random spacing (mean ~0.4 m). This gives horizontal
    optical flow a 2-D texture to track (stripes alone suffer the aperture problem),
    and avoids a regular bar spacing that could alias the LK tracker or RANSAC.
  - Three variants (seeds 0, 1, 2) cycle along the wall, so the pattern repeats
    only every 30 m.
End wall (`corridor_end_wall`), 20 m x 5 m: non-periodic random rectangles plus the
same horizontal lines, a far-field target at the end of the corridor.

Usage: python3 sim/tools/make_wall_textures.py   (needs numpy + Pillow; venv-evo)
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(os.path.dirname(HERE), "models")
PX_PER_M = 100
BASE, LINE = 250, 0           # grey levels (v2: max contrast; v1 160/25 rendered too faint, METHODOLOGY)
LINE_Z = np.arange(0.5, 5.0, 0.5)
LINE_W_M = 0.08


def horizontal_lines(img):
    h = img.shape[0]
    for z in LINE_Z:
        r = int(round(h - z * PX_PER_M))           # image row 0 is the TOP of the wall
        w = int(LINE_W_M * PX_PER_M) // 2
        img[max(r - w, 0):r + w, :] = LINE


def side_wall(seed, length_m=10.0, height_m=5.0):
    rng = np.random.default_rng(seed)
    W, H = int(length_m * PX_PER_M), int(height_m * PX_PER_M)
    img = np.full((H, W), BASE, np.uint8)
    x = rng.uniform(0, 0.3) * PX_PER_M
    while x < W:
        bw = int(rng.uniform(0.03, 0.20) * PX_PER_M)
        top = int(rng.uniform(0.0, 0.6) * H)
        bot = int(rng.uniform(top + 0.3 * H, H))
        img[top:bot, int(x):int(x) + bw] = int(rng.uniform(0, 150))
        x += bw + rng.exponential(0.4) * PX_PER_M
    horizontal_lines(img)
    return img


def end_wall(seed=10, width_m=20.0, height_m=5.0):
    rng = np.random.default_rng(seed)
    W, H = int(width_m * PX_PER_M), int(height_m * PX_PER_M)
    img = np.full((H, W), BASE, np.uint8)
    for _ in range(140):
        w, h = int(rng.uniform(0.2, 1.5) * PX_PER_M), int(rng.uniform(0.2, 1.5) * PX_PER_M)
        x0, y0 = int(rng.uniform(0, W - w)), int(rng.uniform(0, H - h))
        img[y0:y0 + h, x0:x0 + w] = int(rng.uniform(30, 240))
    horizontal_lines(img)
    return img


def save(img, model, name):
    d = os.path.join(MODELS, model, "materials", "textures")
    os.makedirs(d, exist_ok=True)
    Image.fromarray(img).convert("RGB").save(os.path.join(d, name), optimize=True)


if __name__ == "__main__":
    for s in range(3):
        save(side_wall(s), "corridor_wall_lined", f"wall_{s}.png")
    save(end_wall(), "corridor_end_wall", "end_wall.png")
    print("written under", MODELS)
