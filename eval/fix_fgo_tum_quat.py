#!/usr/bin/env python3
"""Ruling D10 (2026-09-30): repair the FGO TUM orientations written with fgo_replay.py's euler_to_quat
typo (w = cr*cp*cy + sr*sp*cy instead of ... + sr*sp*sy). x, y, z were written correctly, so the unit
quaternion's w is recovered as sign(w_written) * sqrt(1 - x^2 - y^2 - z^2) (exact up to the %.6f
rounding). Positions are untouched. The original is kept as <file>.typo; a file already repaired
(a .typo backup exists) is skipped.
Usage: python3 eval/fix_fgo_tum_quat.py FILE [...]"""
import os, sys
import numpy as np
n = 0
for p in sys.argv[1:]:
    if os.path.exists(p + ".typo"):
        continue
    a = np.loadtxt(p)
    x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    wn = np.sign(np.where(w == 0, 1, w)) * np.sqrt(np.clip(1 - x * x - y * y - z * z, 0, None))
    os.rename(p, p + ".typo")
    with open(p, "w") as f:
        for r, ww in zip(a, wn):
            f.write(f"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f} {r[3]:.6f} {r[4]:.6f} {r[5]:.6f} {r[6]:.6f} {ww:.6f}\n")
    n += 1
print(f"repaired {n} file(s)")
