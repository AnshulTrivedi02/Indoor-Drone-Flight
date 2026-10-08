"""Is the tag-fix error coupled to the TRUE attitude (roll/pitch) of the vehicle? Regress tag err on GT roll/pitch."""
import sys, numpy as np
sys.path.insert(0, ".")
from tilt import q2rpy
Z = np.load(sys.argv[1]); a, b = float(sys.argv[2]), float(sys.argv[3])
tag = Z["tag"]; gt = Z["gt"]; tg = gt[:, 0]
gx = np.interp(tag[:, 0], tg, gt[:, 1]); gy = np.interp(tag[:, 0], tg, gt[:, 2])
m = (tag[:, 0] >= a) & (tag[:, 0] <= b)
P = np.c_[gx[m], gy[m]]; Q = tag[m, 1:3]
Pc, Qc = P - P.mean(0), Q - Q.mean(0)
U, S, Vt = np.linalg.svd(Pc.T @ Qc); Rm = (U @ Vt).T; c = Q.mean(0) - Rm @ P.mean(0)
e = tag[m, 1:3] - ((Rm @ P.T).T + c)
rpy = q2rpy(gt[:, 4:8])
rg = np.interp(tag[m, 0], tg, rpy[:, 0]); pg = np.interp(tag[m, 0], tg, rpy[:, 1])
for lag in [0.0, 0.033, 0.066, 0.1, 0.15]:
    rg = np.interp(tag[m, 0] - lag, tg, rpy[:, 0]); pg = np.interp(tag[m, 0] - lag, tg, rpy[:, 1])
    A = np.c_[rg - rg.mean(), pg - pg.mean()]
    for i, nm in enumerate(["E", "N"]):
        k, *_ = np.linalg.lstsq(A, e[:, i] - e[:, i].mean(), rcond=None)
        r = e[:, i] - e[:, i].mean() - A @ k
        print(f"lag {lag*1e3:4.0f} ms tag err {nm}: = {k[0]:+.3f} m/rad*roll {k[1]:+.3f} m/rad*pitch; "
              f"R2 {1 - r.var()/e[:, i].var():.2f}  (sd {e[:, i].std()*1e3:.1f} mm)")
# also against GT lateral velocity (latency signature)
vx = np.gradient(gt[:, 1], tg); vy = np.gradient(gt[:, 2], tg)
for lag in [0.0, 0.05, 0.1]:
    V = np.c_[np.interp(tag[m, 0], tg, vx), np.interp(tag[m, 0], tg, vy)]
    V = (Rm @ V.T).T
    for i, nm in enumerate(["E", "N"]):
        k = np.polyfit(V[:, i], e[:, i], 1)[0]
        print(f"tag err {nm} vs GT vel {nm}: slope {k*1e3:+.1f} ms (corr {np.corrcoef(V[:, i], e[:, i])[0,1]:+.2f})")
    break
