"""Piecewise log-log growth exponent of the pre-flip relative gate-trace difference (unforced logs)."""
import numpy as np
D = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate2/dump/"
for b in ["tex", "trans"]:
    for o in ["emu_", "cpp_"]:
        a = np.fromfile(D + f"dsn_{b}_r1_baseline.yawgate.f64").reshape(-1, 4)
        c = np.fromfile(D + f"{o}dsn_{b}_r1_baseline.yawgate.f64").reshape(-1, 4)
        n = min(len(a), len(c)); a, c = a[:n], c[:n]
        i1 = np.where(a[:, 3] != c[:, 3])[0][0]; a, c = a[:i1], c[:i1]
        t = a[:, 0]; r = np.abs(a[:, 2] - c[:, 2]) / a[:, 2]
        out = []
        for lo, hi in [(5, 60), (60, 150), (150, t.max())]:
            m = (t >= lo) & (t <= hi) & (r > 0)
            out.append(f"{lo}-{hi:.0f}s exp {np.polyfit(np.log10(t[m]), np.log10(r[m]), 1)[0]:.2f}")
        print(o, b, "; ".join(out))
