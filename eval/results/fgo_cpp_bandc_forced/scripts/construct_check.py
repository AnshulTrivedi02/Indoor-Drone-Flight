"""Construction check for the forced-decision Band C (pre-registered 2026-10-11): a forced C++ gate log must have the
same checks, at the same keyframe indices k, with the same fired flags, as the Python log it was forced to.
Rows (t, k, trace, fired) float64. Usage: construct_check.py <python.yawgate.f64> <forced.yawgate.f64>"""
import sys
import numpy as np

a = np.fromfile(sys.argv[1]).reshape(-1, 4)
b = np.fromfile(sys.argv[2]).reshape(-1, 4)
same_n = len(a) == len(b)
same_k = same_n and np.array_equal(a[:, 1], b[:, 1])
same_f = same_n and np.array_equal(a[:, 3], b[:, 3])
n = min(len(a), len(b))
# how many forced decisions differ from what the C++ trace alone would have decided (the ties the switch overrides)
over = int(np.sum((b[:n, 2] > 0.04) != (b[:n, 3] == 1)))
print(f"checks python {len(a)} forced {len(b)}; k sequence identical: {same_k}; fired flags identical: {same_f} "
      f"(fired {int(a[:, 3].sum())} / {int(b[:, 3].sum())}); decisions overriding the C++ trace: {over}")
ok = same_n and same_k and same_f
print(f"CONSTRUCTION CHECK: {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
