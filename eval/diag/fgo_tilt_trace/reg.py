"""Relation of the estimate's roll/pitch to GT roll/pitch: gain and lag (diagnostic)."""
import sys, numpy as np
sys.path.insert(0, ".")
from tilt import load
est = load(sys.argv[1]); gt = load(sys.argv[2]); a, b = float(sys.argv[3]), float(sys.argv[4])
te, _, re = est; tg, _, rg = gt
m = (te >= a) & (te <= b); te = te[m]; re = np.degrees(re[m])
for i, nm in enumerate(["roll", "pitch"]):
    best = None
    for lag in np.arange(-0.3, 0.301, 0.005):          # est(t) vs gt(t - lag)
        g = np.degrees(np.interp(te - lag, tg, rg[:, i]))
        x = g - g.mean(); y = re[:, i] - re[:, i].mean()
        k = (x @ y) / (x @ x); res = y - k * x
        if best is None or res.std() < best[2]:
            best = (lag, k, res.std(), np.corrcoef(x, y)[0, 1], g.std())
    g0 = np.degrees(np.interp(te, tg, rg[:, i]))
    e0 = re[:, i] - g0
    print(f"{nm}: gt sd {g0.std():.3f}  est sd {re[:,i].std():.3f}  err sd {e0.std():.3f} | best lag {best[0]*1e3:+.0f} ms gain {best[1]:.3f} "
          f"resid sd {best[2]:.3f} corr {best[3]:.3f}")
