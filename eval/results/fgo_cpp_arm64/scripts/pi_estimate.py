"""Item 2f: ESTIMATED Raspberry Pi per-keyframe FGO step time (NOT a measurement).
x86 step times: the 2d scratch-build replays (d18/dump/cpp_*.step_ns.i64, i7-8700, single thread, nice 19, generic
x86-64), plus the L1/L2 live-adapter figures (d18/logs/L{1,2}.log). Scale: Geekbench 6 single-core ratios already
cited in docs/fgo_cpp_port.md (i7-8700 ~1527; Pi 5 ~764-787 -> 1.9-2.0x; Pi 4 ~293-340 -> 4.5-5.2x)."""
import numpy as np
D = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/d18/dump"
RATIO = {"Pi 5 (A76)": (1.9, 2.0), "Pi 4 (A72)": (4.5, 5.2)}
BUDGET = 33.3
rows = []
for p in ["dsn_tex_r1_baseline", "fwdc_tex_r1_heading", "T_A_r1", "O_r1"]:
    s = np.fromfile(f"{D}/cpp_{p}.step_ns.i64", np.int64) / 1e6
    rows.append((f"replay {p}", np.median(s), np.percentile(s, 99), s.max()))
rows.append(("live L1 dsn_tex (2d log)", 0.532, 0.912, 2.968))
rows.append(("live L2 fwdc heading (2d log)", 0.960, 1.685, 3.105))
rows.append(("worst single spike seen (fgo_cpp_port.md)", float("nan"), float("nan"), 12.9))
print(f"{'x86 run':44s} {'med':>6s} {'p99':>6s} {'max':>6s} | " + " | ".join(f"{k}: med / p99 / max" for k in RATIO))
for name, med, p99, mx in rows:
    cells = []
    for lo, hi in RATIO.values():
        f = lambda v: "  -  " if np.isnan(v) else f"{v*lo:.1f}-{v*hi:.1f}"
        cells.append(f"{f(med)} / {f(p99)} / {f(mx)}")
    print(f"{name:44s} {med:6.3f} {p99:6.3f} {mx:6.2f} | " + " | ".join(cells))
print(f"budget per keyframe (30 Hz): {BUDGET:.1f} ms. ESTIMATES ONLY; +-40% load variation on the x86 medians (fgo_cpp_port.md).")
