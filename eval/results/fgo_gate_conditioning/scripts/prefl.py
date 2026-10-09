"""Pre-flip relative gate-trace difference, Python vs C++ (emu and default builds), from the existing unforced gate logs.
Light: reads 2k-row logs only."""
import numpy as np
D = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate2/dump/"
for b in ["tex", "trans", "blank"]:
    for other in ["emu_", "cpp_"]:
        a = np.fromfile(D + f"dsn_{b}_r1_baseline.yawgate.f64").reshape(-1, 4)
        c = np.fromfile(D + f"{other}dsn_{b}_r1_baseline.yawgate.f64").reshape(-1, 4)
        n = min(len(a), len(c)); a = a[:n]; c = c[:n]
        ok = (a[:, 1] == c[:, 1]) & (a[:, 0] == c[:, 0])
        mm = np.where((a[:, 3] != c[:, 3]) | ~ok)[0]; i1 = mm[0] if len(mm) else n
        a = a[:i1]; c = c[:i1]
        rel = np.abs(a[:, 2] - c[:, 2]) / np.abs(a[:, 2]); t = a[:, 0]
        m = (rel > 0) & (t > 5)
        sl, ic = np.polyfit(np.log10(t[m]), np.log10(rel[m]), 1)
        sl2, ic2 = np.polyfit(t[m], np.log10(rel[m]), 1)
        q = []
        for lo in np.arange(0, t.max(), 30):
            s = (t >= lo) & (t < lo + 30)
            if s.any():
                q.append(f"{lo:.0f}:{np.median(rel[s]):.1e}/{rel[s].max():.1e}")
        print(f"{other}{b}: pre-flip rows {i1} (t<{t.max():.1f}); zero-diff {np.sum(rel == 0)}; "
              f"loglog slope {sl:.2f}; semilog {sl2 * 100:.2f} dec/100 s")
        print("   30 s bins median/max:", " ".join(q))
