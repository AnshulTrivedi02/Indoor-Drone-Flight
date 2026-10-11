"""POST-HOC DIAGNOSTIC (not a band): for a band-C comparison (export-driven C++ cpp_<p> vs native front end fe_<p>),
find the first yaw-cap gate decision mismatch and report |dp| / |dyaw| before and after it, and the gate traces there.
Usage: onset_c.py <dump dir> <prefix>"""
import sys
import numpy as np
D, p = sys.argv[1], sys.argv[2]
a = np.fromfile(f"{D}/cpp_{p}.kf.f64").reshape(-1, 40); b = np.fromfile(f"{D}/fe_{p}.kf.f64").reshape(-1, 40)
ga = np.fromfile(f"{D}/cpp_{p}.yawgate.f64").reshape(-1, 4); gb = np.fromfile(f"{D}/fe_{p}.yawgate.f64").reshape(-1, 4)
n = min(len(ga), len(gb))
mis = np.flatnonzero(ga[:n, 3] != gb[:n, 3])
dp = np.linalg.norm(a[:, 10:13] - b[:, 10:13], axis=1) * 1e3
yaw = lambda x: np.arctan2(x[:, 16], x[:, 13])
dyaw = np.degrees(np.abs((yaw(a) - yaw(b) + np.pi) % (2 * np.pi) - np.pi))
rel = np.abs(ga[:n, 2] - gb[:n, 2]) / np.abs(ga[:n, 2])
print(f"{p}: gate checks {n}; decision mismatches {len(mis)}")
if len(mis):
    i = mis[0]; k = int(ga[i, 1]); t = ga[i, 0]
    print(f"first mismatch at check {i}, keyframe {k}, t {t:.3f} s: trace cpp {ga[i, 2]:.9g} (fired {int(ga[i, 3])}) "
          f"fe {gb[i, 2]:.9g} (fired {int(gb[i, 3])}); rel trace diff there {rel[i]:.3g}; max rel before {rel[:i].max():.3g}")
    print(f"before it (rows < {k}): max |dp| {dp[:k].max():.4g} mm, max |dyaw| {dyaw[:k].max():.3g} deg")
    print(f"after it: max |dp| {dp[k:].max():.4g} mm, max |dyaw| {dyaw[k:].max():.3g} deg")
    print("mismatch times (s):", " ".join(f"{ga[j, 0]:.2f}" for j in mis))
print(f"whole run: max |dp| {dp.max():.4g} mm, max |dyaw| {dyaw.max():.3g} deg")
