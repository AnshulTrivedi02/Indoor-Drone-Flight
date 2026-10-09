"""Onset of a Python-vs-C++ divergence: first |dp| > 1 um / 1 mm / 1 m, the first gate-decision mismatch, and the
max |dp| before that mismatch.  Usage: onset.py <ref prefix> <test prefix>"""
import sys
import numpy as np
a = np.fromfile(sys.argv[1] + ".kf.f64").reshape(-1, 40); b = np.fromfile(sys.argv[2] + ".kf.f64").reshape(-1, 40)
n = min(len(a), len(b)); a, b = a[:n], b[:n]
dp = np.linalg.norm(a[:, 10:13] - b[:, 10:13], axis=1); t = a[:, 0]
on = [f"{t[np.argmax(dp > th)]:.1f}" if (dp > th).any() else "never" for th in (1e-6, 1e-3, 1.0)]
ga = np.fromfile(sys.argv[1] + ".yawgate.f64").reshape(-1, 4); gb = np.fromfile(sys.argv[2] + ".yawgate.f64").reshape(-1, 4)
m = min(len(ga), len(gb)); mm = np.nonzero(ga[:m, 3] != gb[:m, 3])[0]
if len(mm):
    tm = ga[mm[0], 0]; pre = dp[t < tm]
    d = np.abs(ga[:mm[0], 2] - gb[:mm[0], 2]) / np.abs(ga[:mm[0], 2])
    print(f"first |dp|>1um/1mm/1m: {on[0]} / {on[1]} / {on[2]} s; first gate mismatch t {tm:.2f} s "
          f"(ref trace {ga[mm[0], 2]:.9g}, test {gb[mm[0], 2]:.9g}); max |dp| before it {1e3 * pre.max():.4g} mm; "
          f"max rel trace diff before it {d.max() if len(d) else 0:.3g}; mismatches {len(mm)}")
else:
    print(f"first |dp|>1um/1mm/1m: {on[0]} / {on[1]} / {on[2]} s; no gate mismatch")
