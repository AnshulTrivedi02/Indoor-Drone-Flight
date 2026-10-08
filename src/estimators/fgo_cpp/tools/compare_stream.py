#!/usr/bin/env python3
"""Compare the native front end's processed stream with the Python export (docs/fgo_cpp_port.md, band C diagnostics).

Usage: compare_stream.py <python_prefix> <frontend_out_prefix>
Reports: event count and kind order, max |dt| of the dejittered IMU stamps (C++ closed form vs numpy.polyfit),
non-IMU stamps and payloads bit-identical, and the interval-averaged gyro (flow omega, forward gyro-z) bit identity."""
import json, sys
import numpy as np

py_p, fe_p = sys.argv[1:3]
P = np.fromfile(py_p + ".events.f64").reshape(-1, 9)
C = np.fromfile(fe_p + ".events.f64").reshape(-1, 9)
print(f"events: python {len(P)}  front end {len(C)}")
n = min(len(P), len(C))
kinds_same = np.array_equal(P[:n, 0], C[:n, 0])
print(f"kind sequence identical: {kinds_same}")
imu = P[:n, 0] == 0
dt = np.abs(P[:n, 1] - C[:n, 1])
print(f"IMU stamps: max |dt| {dt[imu].max():.3e} s, bit-identical {np.mean(dt[imu] == 0) * 100:.1f}% of samples")
print(f"non-IMU stamps bit-identical: {np.array_equal(P[:n][~imu, 1], C[:n][~imu, 1])}")
pay = lambda X: np.nan_to_num(X[:, 2:6], nan=-12345.0)
print(f"payloads (cols 2-5) bit-identical: {np.array_equal(pay(P[:n]), pay(C[:n]))}")
avg = np.fromfile(fe_p + ".avg.f64").reshape(-1, 5)
for kind, nm, cols in [(3, "flow omega", slice(6, 9)), (4, "forward gyro-z", slice(4, 5))]:
    pr = P[(P[:, 0] == kind) & ~np.isnan(P[:, cols.start])]
    cr = avg[avg[:, 0] == kind]
    if len(pr) == 0 and len(cr) == 0:
        continue
    m = min(len(pr), len(cr))
    a = pr[:m, cols]; b = cr[:m, 2:2 + (cols.stop - cols.start)]
    print(f"{nm}: python {len(pr)}  front end {len(cr)}  stamps identical {np.array_equal(pr[:m, 1], cr[:m, 1])}  "
          f"bit-identical {np.array_equal(a, b)}  max |diff| {np.abs(a - b).max():.3e}")
fe = json.load(open(fe_p + ".frontend.json"))
print("front end:", json.dumps(fe))
