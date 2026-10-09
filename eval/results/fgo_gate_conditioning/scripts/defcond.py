"""cond(L) for the default C++ build (every 10th keyframe), compared with the emu build."""
import numpy as np
G = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/gatecond/out/"
W = 1127


def cl(f):
    a = np.fromfile(f).reshape(-1, W)[::10]
    out = []
    for r in a:
        L = r[2:902].reshape(30, 30); ev = np.linalg.eigvalsh(0.5 * (L + L.T)); out.append((r[0], ev[-1] / ev[0]))
    return np.array(out)


d = cl(G + "def.cond.f64"); e = cl(G + "emu.cond.f64")
n = min(len(d), len(e))
print("max |cond_def/cond_emu - 1|", np.max(np.abs(d[:n, 1] / e[:n, 1] - 1)))
for lo in range(0, 340, 60):
    s = (d[:, 0] >= lo) & (d[:, 0] < lo + 30)
    print(lo, f"{np.median(d[s, 1]):.2e}")
