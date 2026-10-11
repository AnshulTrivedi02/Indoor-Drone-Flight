"""Compare two yaw-cap gate logs (t, k, trace, fired) rows of float64: check count, fired keyframes, trace diffs,
and the smallest |trace - 0.04| margin (how close any decision came to flipping)."""
import sys
import numpy as np
a = np.fromfile(sys.argv[1]).reshape(-1, 4)
b = np.fromfile(sys.argv[2]).reshape(-1, 4)
print(f"checks {len(a)} / {len(b)}; fired {int(a[:, 3].sum())} / {int(b[:, 3].sum())}")
n = min(len(a), len(b))
same_t = bool(np.array_equal(a[:n, 0], b[:n, 0])) and len(a) == len(b)
fa = set(a[a[:, 3] == 1, 1].astype(int)); fb = set(b[b[:, 3] == 1, 1].astype(int))
print(f"check times identical: {same_t}; fired keyframe sets identical: {fa == fb} "
      f"(only first {len(fa - fb)}, only second {len(fb - fa)})")
dec = int(np.sum(a[:n, 3] != b[:n, 3]))
d = np.abs(a[:n, 2] - b[:n, 2]); rel = d / np.maximum(np.abs(a[:n, 2]), 1e-300)
if n:
    print(f"decision mismatches {dec}; max |d trace| {d.max():.3g} (rel {rel.max():.3g}); bit-identical traces "
          f"{int(np.sum(d == 0))}/{n}")
    m = np.abs(a[:n, 2] - 0.04)
    i = int(np.argmin(m))
    print(f"smallest |trace - 0.04| = {m[i]:.3g} at t {a[i, 0]:.3f} (trace {a[i, 2]:.6g}, fired {int(a[i, 3])}); "
          f"first fire t {a[a[:, 3] == 1, 0][0] if fa else None}")
