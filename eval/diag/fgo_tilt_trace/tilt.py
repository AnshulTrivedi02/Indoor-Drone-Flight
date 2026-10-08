import sys, numpy as np
def q2rpy(q):
    x, y, z, w = q.T
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return np.stack([roll, pitch, yaw], 1)


def load(p):
    a = np.loadtxt(p); t = a[:, 0]
    rpy = q2rpy(a[:, 4:8])
    return t, a[:, 1:4], rpy


def err(est, gt):
    te, pe, re = est; tg, pg, rg = gt
    m = (te > tg[0]) & (te < tg[-1]); te = te[m]
    rgi = np.stack([np.interp(te, tg, np.unwrap(rg[:, i])) for i in range(3)], 1)
    pgi = np.stack([np.interp(te, tg, pg[:, i]) for i in range(3)], 1)
    return te, np.degrees(re[m][:, :2] - rgi[:, :2]), pgi, pe[m]


if __name__ == "__main__":
    est = load(sys.argv[1]); gt = load(sys.argv[2])
    t, e, pg, pe = err(est, gt)
    t0 = float(sys.argv[3]) if len(sys.argv) > 3 else t[0]; t1 = float(sys.argv[4]) if len(sys.argv) > 4 else t[-1]
    for a, b in [(t[0], t[-1]), (t0, t1)]:
        m = (t >= a) & (t <= b)
        rms = np.sqrt(np.mean(e[m,0]**2 + e[m,1]**2)); print(f"[{a:.1f},{b:.1f}] n={m.sum()} tiltRMS {rms:.3f} roll mean {e[m,0].mean():+.3f} sd {e[m,0].std():.3f}  pitch mean {e[m,1].mean():+.3f} sd {e[m,1].std():.3f}")
    if "-q" in sys.argv:
        sys.exit()
    for a in np.arange(t[0], t[-1], 5):
        m = (t >= a) & (t < a + 5)
        if m.sum() > 3:
            print(f"{a:6.1f} z={pg[m,2].mean():.2f} roll {e[m,0].mean():+.3f}/{e[m,0].std():.3f} pitch {e[m,1].mean():+.3f}/{e[m,1].std():.3f}")
