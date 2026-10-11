"""Item 2f: x86 C++ vs arm64 C++ per keyframe, split at the first yaw-cap gate decision mismatch (a threshold tie
at 0.04 is not an architecture difference in itself: report |dp| before it separately). Also the step-time ratio
(emulated arm64 / x86; RELATIVE ONLY, qemu wall time is not representative).
Usage: onset_arm.py <x86 prefix> <arm prefix>"""
import sys
import numpy as np
x, r = sys.argv[1], sys.argv[2]
a = np.fromfile(f"{x}.kf.f64").reshape(-1, 40); b = np.fromfile(f"{r}.kf.f64").reshape(-1, 40)
n = min(len(a), len(b)); a, b = a[:n], b[:n]
ga = np.fromfile(f"{x}.yawgate.f64").reshape(-1, 4); gb = np.fromfile(f"{r}.yawgate.f64").reshape(-1, 4)
m = min(len(ga), len(gb))
mis = np.flatnonzero(ga[:m, 3] != gb[:m, 3])
ok = np.isfinite(a[:, 10]) & np.isfinite(b[:, 10])
dp = np.where(ok, np.linalg.norm(a[:, 10:13] - b[:, 10:13], axis=1) * 1e3, 0.0)
yaw = lambda q: np.arctan2(q[:, 16], q[:, 13])
dyaw = np.where(ok, np.degrees(np.abs((yaw(a) - yaw(b) + np.pi) % (2 * np.pi) - np.pi)), 0.0)
first = int(np.argmax(dp > 0)) if np.any(dp > 0) else None
print(f"rows {n}; first row with |dp| > 0: {first}" + (f" (t {a[first, 0]:.3f} s)" if first is not None else ""))
print(f"gate checks {m}; decision mismatches {len(mis)}")
if len(mis):
    i = mis[0]; k = int(ga[i, 1])
    rel = np.abs(ga[:m, 2] - gb[:m, 2]) / np.abs(ga[:m, 2])
    print(f"first mismatch: check {i}, keyframe {k}, t {ga[i, 0]:.3f} s, trace x86 {ga[i, 2]:.9g} (fired {int(ga[i, 3])})"
          f" arm {gb[i, 2]:.9g} (fired {int(gb[i, 3])}); max rel trace diff before it {rel[:i].max() if i else 0:.3g}")
    print(f"BEFORE it: max |dp| {dp[:k].max():.4g} mm, p99 {np.percentile(dp[:k], 99):.4g} mm, max |dyaw| {dyaw[:k].max():.3g} deg")
    print(f"after it: max |dp| {dp[k:].max():.4g} mm, max |dyaw| {dyaw[k:].max():.3g} deg")
    print("mismatch times (s):", " ".join(f"{ga[j, 0]:.2f}" for j in mis))
print(f"WHOLE run: max |dp| {dp.max():.4g} mm, p99 {np.percentile(dp, 99):.4g} mm, max |dyaw| {dyaw.max():.3g} deg")
try:
    sx = np.fromfile(f"{x}.step_ns.i64", np.int64) / 1e6; sr = np.fromfile(f"{r}.step_ns.i64", np.int64) / 1e6
    q = lambda s: (np.median(s), np.percentile(s, 99), s.max())
    print("step ms x86 (2d run) median/p99/max %.3f / %.3f / %.3f" % q(sx))
    print("step ms arm64 UNDER QEMU median/p99/max %.3f / %.3f / %.3f" % q(sr))
    print("emulation slowdown (relative only) median %.1fx, p99 %.1fx" % (np.median(sr) / np.median(sx),
          np.percentile(sr, 99) / np.percentile(sx, 99)))
except FileNotFoundError:
    pass
