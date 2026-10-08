"""Tag-fix error vs GT (rigid 2D fit W<-world), its spectrum, and its relation to the FGO roll/pitch error."""
import sys, numpy as np
sys.path.insert(0, ".")
from tilt import load, err, q2rpy
Z = np.load(sys.argv[1]); fgo_tum, gt_tum = sys.argv[2], sys.argv[3]; a, b = float(sys.argv[4]), float(sys.argv[5])
tag = Z["tag"]; gt = Z["gt"]
tg = gt[:, 0]
gx = np.interp(tag[:, 0], tg, gt[:, 1]); gy = np.interp(tag[:, 0], tg, gt[:, 2])
m = (tag[:, 0] >= a) & (tag[:, 0] <= b)
# rigid fit: tag = R(th) [gx,gy] + c
P = np.c_[gx[m], gy[m]]; Q = tag[m, 1:3]
Pc, Qc = P - P.mean(0), Q - Q.mean(0)
U, S, Vt = np.linalg.svd(Pc.T @ Qc); Rm = (U @ Vt).T
c = Q.mean(0) - Rm @ P.mean(0)
print("W<-world rotation deg", np.degrees(np.arctan2(Rm[1, 0], Rm[0, 0])), "offset", c)
pred = (Rm @ np.c_[gx, gy].T).T + c
e = tag[:, 1:3] - pred
dtag = np.diff(tag[m, 0])
print(f"tag rate {1/np.median(dtag):.1f} Hz, gaps>0.1s: {(dtag>0.1).sum()}")
print("tag err E/N mean", e[m].mean(0), "sd", e[m].std(0))
# GT yaw for body-lateral direction
yaw_gt = q2rpy(gt[:, 4:8])[:, 2]
# spectrum of tag error (resampled 25 Hz)
tt = np.arange(a, b, 0.04)
for i, nm in enumerate(["E", "N"]):
    x = np.interp(tt, tag[m, 0], e[m, i]); x -= x.mean()
    f = np.fft.rfftfreq(len(x), 0.04); Pw = np.abs(np.fft.rfft(x)) ** 2; tot = Pw[1:].sum()
    bands = [(0, 0.1), (0.1, 0.5), (0.5, 2), (2, 5), (5, 12.6)]
    print(f"tag err {nm}:", " ".join(f"{lo}-{hi}Hz:{Pw[(f>=lo)&(f<hi)].sum()/tot*100:.0f}%" for lo, hi in bands))
# correlation of the FGO roll/pitch error with tag error (and its 2nd derivative) at FGO times
est = load(fgo_tum); g2 = load(gt_tum)
t, ee, pg, pe = err(est, g2)
mm = (t >= a) & (t <= b); t = t[mm]; ee = ee[mm]
eE = np.interp(t, tag[m, 0], e[m, 0]); eN = np.interp(t, tag[m, 0], e[m, 1])
for i, nm in enumerate(["roll", "pitch"]):
    for lab, s in [("tagE", eE), ("tagN", eN)]:
        best = max(((np.corrcoef(np.roll(s, L), ee[:, i])[0, 1], L) for L in range(-15, 16)), key=lambda z: abs(z[0]))
        print(f"{nm} err vs {lab}: corr {np.corrcoef(s, ee[:, i])[0,1]:+.2f}, best {best[0]:+.2f} at lag {best[1]} kf")
# FGO position error vs GT in W frame
pgw = (Rm @ pg[mm, :2].T).T + c
pe_ = pe[mm, :2] - pgw
print("FGO pos err E/N sd mm", pe_.std(0) * 1e3, "mean", pe_.mean(0) * 1e3)
