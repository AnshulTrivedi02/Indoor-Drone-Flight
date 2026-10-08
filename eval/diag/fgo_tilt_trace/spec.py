import sys, numpy as np
sys.path.insert(0, ".")
from tilt import load, err
est = load(sys.argv[1]); gt = load(sys.argv[2]); a, b = float(sys.argv[3]), float(sys.argv[4])
t, e, pg, pe = err(est, gt)
m = (t >= a) & (t <= b); t = t[m]; e = e[m]
print("dt median", np.median(np.diff(t)), "n", len(t))
for i, nm in enumerate(["roll", "pitch"]):
    x = e[:, i] - e[:, i].mean()
    f = np.fft.rfftfreq(len(x), np.median(np.diff(t))); P = np.abs(np.fft.rfft(x)) ** 2
    bands = [(0, 0.1), (0.1, 0.5), (0.5, 2), (2, 5), (5, 10), (10, 15.1)]
    tot = P[1:].sum()
    print(nm, " ".join(f"{lo}-{hi}Hz:{P[(f>=lo)&(f<hi)].sum()/tot*100:.0f}%" for lo, hi in bands))
    top = np.argsort(P)[-6:][::-1]; print("  peaks", [(round(f[j], 3), round(P[j] / tot * 100, 1)) for j in top])
    # lag-1 autocorrelation
    print("  ac lag1", np.corrcoef(x[:-1], x[1:])[0, 1], "lag2", np.corrcoef(x[:-2], x[2:])[0, 1])
# also: est roll itself vs gt roll sd
re = est[2]; mm = (est[0] >= a) & (est[0] <= b)
rg = gt[2]; mg = (gt[0] >= a) & (gt[0] <= b)
print("est roll sd deg", np.degrees(re[mm, 0]).std(), "gt roll sd deg", np.degrees(rg[mg, 0]).std())
print("est pitch sd deg", np.degrees(re[mm, 1]).std(), "gt pitch sd deg", np.degrees(rg[mg, 1]).std())
np.savetxt(sys.argv[5] if len(sys.argv) > 5 else "err.txt", np.c_[t, e])
