#!/usr/bin/env python3
"""Build the three-panel forward-camera comparison figure (docs/thesis/world_images/thesis/forward_camera_panel.png)
from the three raw frames already extracted by thesis_frames.py (no bag reading here; this step only arranges
existing image files). All three are taken at the same position along the corridor (ground truth y about 40 m)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.image import imread

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
import sys
sys.path.insert(0, os.path.join(REPO, "eval"))
import thesis_style as ts

OUT = os.path.join(REPO, "docs", "thesis", "world_images", "thesis")
CAP = os.path.join(OUT, "captions")

PANELS = [("forward_line_walls_raw.png", "line-textured walls"),
          ("forward_plain_walls_checker_raw.png", "plain walls, checkerboard floor"),
          ("forward_plain_walls_blank_raw.png", "plain walls, blank floor")]

plt.rcParams.update(ts.RCPARAMS)
plt.rcParams.update({"axes.grid": False})


def main():
    frames = json.load(open(os.path.join(OUT, "frames.json")))
    by_raw = {r["raw"]: r for r in frames if "raw" in r}
    fig, axes = plt.subplots(1, 3, figsize=(ts.TEXT_WIDTH_IN, ts.TEXT_WIDTH_IN / 3 * 480 / 640 + 0.35))
    gt_ys = []
    for ax, (fname, label), lab in zip(axes, PANELS, "abc"):
        a = imread(os.path.join(OUT, fname))
        ax.imshow(a, cmap="gray", vmin=0, vmax=1 if a.dtype != "uint8" else 255, interpolation="none")
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_xlabel("(%s) %s" % (lab, label), fontsize=9)
        gt_ys.append(by_raw[fname]["gt_y"])
    fig.tight_layout()
    f = os.path.join(OUT, "forward_camera_panel.png")
    fig.savefig(f, dpi=200)
    fig.savefig(f[:-4] + ".pdf")
    plt.close(fig)
    with open(os.path.join(CAP, "forward_camera_panel.md"), "w") as fh:
        fh.write(
            "Forward camera at the same point about %.0f m along the corridor, as recorded with no overlay: "
            "(a) line-textured walls, (b) plain walls over the checkerboard floor, (c) plain walls over the blank floor.\n" % gt_ys[0])
    print(f)


if __name__ == "__main__":
    main()
