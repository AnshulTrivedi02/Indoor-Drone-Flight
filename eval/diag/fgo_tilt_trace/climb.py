"""Tag fixes around take-off: count, error vs GT (W frame from h_score: N_W = y - 4.998, E_W = x), per 1 s bin."""
import sys, numpy as np
Z = np.load(sys.argv[1]); a, b = float(sys.argv[2]), float(sys.argv[3])
tag, gt = Z["tag"], Z["gt"]; tg = gt[:, 0]
E = np.interp(tag[:, 0], tg, gt[:, 1]); N = np.interp(tag[:, 0], tg, gt[:, 2]) - 4.998; zz = np.interp(tag[:, 0], tg, gt[:, 3])
eE, eN = tag[:, 1] - E, tag[:, 2] - N
rng = np.hypot(E, N)
for lo in np.arange(a, b, 1.0):
    m = (tag[:, 0] >= lo) & (tag[:, 0] < lo + 1)
    zi = np.interp(lo + 0.5, tg, gt[:, 3])
    if m.sum():
        print(f"{lo:5.1f} z {zi:.2f} n {m.sum():3d} range {rng[m].mean():.2f}  errE {eE[m].mean()*1e3:+6.1f}/{eE[m].std()*1e3:5.1f} mm  errN {eN[m].mean()*1e3:+6.1f}/{eN[m].std()*1e3:5.1f} mm")
    else:
        print(f"{lo:5.1f} z {zi:.2f} n   0")
