"""Onset of the Python-vs-C++ divergence: first keyframe time where |dp| exceeds 1 um, 1 mm, 1 m."""
import sys
import numpy as np
D = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/binit0/dump/"
for p in sys.argv[1:]:
    ref, test = (p.split(":") + ["cpp_" + p])[:2]
    a = np.fromfile(D + ref + ".kf.f64").reshape(-1, 40); b = np.fromfile(D + test + ".kf.f64").reshape(-1, 40)
    n = min(len(a), len(b)); a, b = a[:n], b[:n]
    dp = np.linalg.norm(a[:, 10:13] - b[:, 10:13], axis=1)
    out = [f"{p} ({test}):"]
    for thr, nm in [(1e-6, "1 um"), (1e-3, "1 mm"), (1.0, "1 m")]:
        i = np.flatnonzero(dp > thr)
        out.append(f"> {nm} at t {a[i[0], 0]:.2f} s" if len(i) else f"> {nm} never")
    print("  ".join(out), f"  n_kf {n}, t span {a[0,0]:.1f}-{a[-1,0]:.1f}")
