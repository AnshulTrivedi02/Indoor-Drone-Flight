#!/usr/bin/env python3
"""Compare the Python and C++ numerics-probe outputs line by line (bit identity, max abs / rel difference).
Usage: compare_probe.py <probe_py.txt> <probe_cpp.txt>"""
import sys
import numpy as np

a = [l for l in open(sys.argv[1]).read().split("\n") if l]
b = [l for l in open(sys.argv[2]).read().split("\n") if l]
assert len(a) == len(b), (len(a), len(b))
for x, y in zip(a, b):
    nx, *vx = x.split(); ny, *vy = y.split()
    assert nx == ny, (nx, ny)
    vx = np.array(vx, float); vy = np.array(vy, float)
    d = np.abs(vx - vy); nz = vx != 0
    rel = (d[nz] / np.abs(vx[nz])).max() if nz.any() else 0.0
    print(f"{nx:9s} n={len(vx):3d} bit-identical={str(np.array_equal(vx, vy)):5s} max|d|={d.max():.3e} max rel={rel:.3e}")
