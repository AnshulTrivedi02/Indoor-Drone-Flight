#!/usr/bin/env python3
"""Per-keyframe equivalence of a C++ FGO run against a reference run (docs/fgo_cpp_port.md).

Usage: compare_kf.py <ref_prefix> <test_prefix> [ref_timing_npz] [--rows anchored]
Both prefixes have <p>.kf.f64 in the fgo_export layout (KF_COLS from <ref>.init.json, 31 for the first, baseline-only
exports). Pre-registered band: identical keyframe count; per keyframe |dp| <= 1 mm and |dyaw| <= 0.01 deg.
Also: per-keyframe decision flags, the first keyframe whose position differs by > 1e-9 m, velocity / bias
differences, the whole-flight batch (<p>.batch.f64) if both have one, and step timing."""
import json, os, sys
import numpy as np

ref, test = sys.argv[1], sys.argv[2]
extra = [a for a in sys.argv[3:] if not a.startswith("--")]
info = json.load(open(ref + ".init.json"))
NC = info.get("kf_cols", 31)
py = np.fromfile(ref + ".kf.f64", np.float64).reshape(-1, NC)
cp = np.fromfile(test + ".kf.f64", np.float64).reshape(-1, 40)[:, :NC]
print(f"keyframe rows: ref {len(py)}  test {len(cp)}  -> count {'IDENTICAL' if len(py) == len(cp) else 'DIFFERENT'}")
n = min(len(py), len(cp)); py, cp = py[:n], cp[:n]
eq = lambda a, b: (a == b) | (np.isnan(a) & np.isnan(b))
print(f"t_kf identical: {np.array_equal(py[:, 0], cp[:, 0])}   t_lat identical: {np.array_equal(py[:, 1], cp[:, 1])}")
flags = [(2, "k_before"), (3, "k_after"), (4, "flow replaced"), (5, "flow factor"), (6, "range factor")]
if NC >= 40:
    flags += [(32, "heading accepted"), (34, "yaw-rate accepted"), (35, "tag factor"), (36, "gnss factor"),
              (37, "anchored"), (38, "keyframe failed")]
for j, nm in flags:
    bad = np.flatnonzero(~eq(py[:, j], cp[:, j]))
    tot = int(np.nansum(py[:, j])) if j >= 4 else None
    print(f"{nm:18s} mismatches: {len(bad)}" + (f" (first at row {bad[0]}, t {py[bad[0], 0]:.3f})" if len(bad) else "")
          + (f"   [ref total {tot}]" if tot is not None else ""))
fu = np.flatnonzero(~eq(py[:, 7:9], cp[:, 7:9]).all(axis=1))
print(f"flow-used xy not bit-identical: {len(fu)} rows; max |diff| {np.nanmax(np.abs(py[:, 7:9] - cp[:, 7:9])) if n else 0:.3e}")
if NC >= 40:
    for j, nm in [(31, "heading NIS"), (33, "yaw-rate NIS")]:
        m = ~np.isnan(py[:, j])
        if m.any():
            print(f"{nm}: {m.sum()} frames, max |diff| {np.nanmax(np.abs(py[m, j] - cp[m, j])):.3e}, "
                  f"min |NIS - 9| over frames {np.nanmin(np.abs(py[m, j] - 9.0)):.3e}")
sel = np.ones(n, bool)
if "--rows" in sys.argv and NC >= 40:          # e.g. room runs: only anchored keyframes are the trajectory
    sel = (py[:, 37] == 1) & (cp[:, 37] == 1)
    print(f"rows compared: {sel.sum()} anchored of {n}")
P, C = py[sel], cp[sel]
dp = np.linalg.norm(P[:, 10:13] - C[:, 10:13], axis=1)
yaw = lambda a: np.arctan2(a[:, 16], a[:, 13])           # R row-major: R10 at 16, R00 at 13
dyaw = np.degrees(np.abs((yaw(P) - yaw(C) + np.pi) % (2 * np.pi) - np.pi))
dv = np.linalg.norm(P[:, 22:25] - C[:, 22:25], axis=1)
dba = np.linalg.norm(P[:, 25:28] - C[:, 25:28], axis=1); dbg = np.linalg.norm(P[:, 28:31] - C[:, 28:31], axis=1)
first = np.flatnonzero(dp > 1e-9)
print(f"first row with |dp| > 1e-9 m: {first[0] if len(first) else None}"
      + (f" (t {P[first[0], 0]:.4f}, |dp| {dp[first[0]]:.3e})" if len(first) else ""))
for nm, x, unit in [("position", dp * 1e3, "mm"), ("yaw", dyaw, "deg"), ("velocity", dv * 1e3, "mm/s"),
                    ("accel bias", dba, "m/s^2"), ("gyro bias", dbg, "rad/s")]:
    print(f"{nm:10s} max {x.max():.3e}  p99 {np.percentile(x, 99):.3e}  median {np.median(x):.3e} {unit}")
ok = len(py) == len(cp) and dp.max() <= 1e-3 and dyaw.max() <= 0.01
print(f"PRE-REGISTERED BAND (same count, |dp|<=1 mm, |dyaw|<=0.01 deg): {'PASS' if ok else 'FAIL'}")
print(f"bit-identical per-keyframe state: {np.array_equal(P[:, 10:31], C[:, 10:31])}")
if os.path.exists(ref + ".batch.f64") and os.path.exists(test + ".batch.f64"):
    bp = np.fromfile(ref + ".batch.f64").reshape(-1, 14); bc = np.fromfile(test + ".batch.f64").reshape(-1, 14)
    print(f"[batch] keys ref {len(bp)} test {len(bc)}  key ids identical: {len(bp) == len(bc) and np.array_equal(bp[:, :2], bc[:, :2])}")
    m = min(len(bp), len(bc))
    bdp = np.linalg.norm(bp[:m, 2:5] - bc[:m, 2:5], axis=1)
    byaw = lambda a: np.arctan2(a[:, 8], a[:, 5])
    bdy = np.degrees(np.abs((byaw(bp[:m]) - byaw(bc[:m]) + np.pi) % (2 * np.pi) - np.pi))
    bok = len(bp) == len(bc) and bdp.max() <= 1e-3 and bdy.max() <= 0.01
    print(f"[batch] position max {bdp.max()*1e3:.3e} p99 {np.percentile(bdp, 99)*1e3:.3e} mm; yaw max {bdy.max():.3e} "
          f"p99 {np.percentile(bdy, 99):.3e} deg -> BAND {'PASS' if bok else 'FAIL'}")
if os.path.exists(test + ".step_ns.i64"):
    c_ns = np.fromfile(test + ".step_ns.i64", np.int64) / 1e6
    print(f"[timing test] median {np.median(c_ns):.3f} ms  p99 {np.percentile(c_ns, 99):.3f} ms  max {c_ns.max():.3f} ms  n {len(c_ns)}")
if extra:
    p_ns = np.load(extra[0])["t_keyframe_ns"] / 1e6
    print(f"[timing ref]  median {np.median(p_ns):.3f} ms  p99 {np.percentile(p_ns, 99):.3f} ms  n {len(p_ns)}")
