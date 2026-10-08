#!/usr/bin/env python3
"""Per-keyframe equivalence of the C++ FGO port against the Python FGO (docs/fgo_cpp_port.md).

Usage: compare_kf.py <python_dump_prefix> <cpp_out_prefix> [python_timing_npz]
Pre-registered band (written before the first comparison): per keyframe |dp| <= 1 mm, |dyaw| <= 0.01 deg,
identical keyframe count. Also reports flag agreement (keyframe created, flow replaced / flow factor /
range factor added), the first keyframe whose position differs by more than 1e-9 m, and velocity / bias
differences. Timing: per-keyframe step time of each implementation (same timed region)."""
import sys
import numpy as np

NC = 31
py = np.fromfile(sys.argv[1] + ".kf.f64", np.float64).reshape(-1, NC)
cp = np.fromfile(sys.argv[2] + ".kf.f64", np.float64).reshape(-1, NC)
print(f"keyframe rows: python {len(py)}  c++ {len(cp)}  -> count {'IDENTICAL' if len(py) == len(cp) else 'DIFFERENT'}")
n = min(len(py), len(cp))
py, cp = py[:n], cp[:n]
print(f"t_kf identical: {np.array_equal(py[:, 0], cp[:, 0])}   t_lat identical: {np.array_equal(py[:, 1], cp[:, 1])}")
names = ["k_before", "k_after", "replaced", "flow_factor", "range_factor"]
for j, nm in zip(range(2, 7), names):
    bad = np.flatnonzero(py[:, j] != cp[:, j])
    print(f"{nm:13s} mismatches: {len(bad)}" + (f" (first at row {bad[0]})" if len(bad) else ""))
fu = np.flatnonzero(~((py[:, 7:9] == cp[:, 7:9]) | (np.isnan(py[:, 7:9]) & np.isnan(cp[:, 7:9]))).all(axis=1))
print(f"flow-used xy not bit-identical: {len(fu)} rows; max |diff| {np.nanmax(np.abs(py[:, 7:9] - cp[:, 7:9])) if n else 0:.3e}")
dp = np.linalg.norm(py[:, 10:13] - cp[:, 10:13], axis=1)
yaw = lambda a: np.arctan2(a[:, 16], a[:, 13])           # R row-major: R10 at 13+3, R00 at 13
dyaw = np.degrees(np.abs((yaw(py) - yaw(cp) + np.pi) % (2 * np.pi) - np.pi))
dv = np.linalg.norm(py[:, 22:25] - cp[:, 22:25], axis=1)
dba = np.linalg.norm(py[:, 25:28] - cp[:, 25:28], axis=1)
dbg = np.linalg.norm(py[:, 28:31] - cp[:, 28:31], axis=1)
first = np.flatnonzero(dp > 1e-9)
print(f"first row with |dp| > 1e-9 m: {first[0] if len(first) else None}"
      + (f" (t {py[first[0], 0]:.4f}, |dp| {dp[first[0]]:.3e})" if len(first) else ""))
for nm, x, unit in [("position", dp * 1e3, "mm"), ("yaw", dyaw, "deg"), ("velocity", dv * 1e3, "mm/s"),
                    ("accel bias", dba, "m/s^2"), ("gyro bias", dbg, "rad/s")]:
    print(f"{nm:10s} max {x.max():.3e}  p99 {np.percentile(x, 99):.3e}  median {np.median(x):.3e} {unit}")
ok = len(py) == len(cp) and dp.max() <= 1e-3 and dyaw.max() <= 0.01
print(f"PRE-REGISTERED BAND (|dp|<=1 mm, |dyaw|<=0.01 deg, same count): {'PASS' if ok else 'FAIL'}")
c_ns = np.fromfile(sys.argv[2] + ".step_ns.i64", np.int64) / 1e6
print(f"[timing c++]    median {np.median(c_ns):.3f} ms  p99 {np.percentile(c_ns, 99):.3f} ms  max {c_ns.max():.3f} ms  n {len(c_ns)}")
if len(sys.argv) > 3:
    p_ns = np.load(sys.argv[3])["t_keyframe_ns"] / 1e6
    print(f"[timing python] median {np.median(p_ns):.3f} ms  p99 {np.percentile(p_ns, 99):.3f} ms  max {p_ns.max():.3f} ms  n {len(p_ns)}")
    print(f"[timing] median speed-up {np.median(p_ns) / np.median(c_ns):.1f}x")
