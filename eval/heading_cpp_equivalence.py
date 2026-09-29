#!/usr/bin/env python3
"""Equivalence test of the C++ heading port (src/forward_camera/cpp/libheading.so) against the
frozen Phase 3 Python output, with the bands PRE-REGISTERED in METHODOLOGY ("C++ port of the
heading node's per-frame computation — equivalence bands PRE-REGISTERED"), C1-C4:
  C1 VP existence and validity identical on every frame (boundary cases listed, else FAIL)
  C2 |d psi| <= 1e-6 deg     C3 |d support| <= 1e-6 px     C4 quality identical
Reference: <trial>/fwd_meas/meas_frozen.npz (Phase 3; the Python node reproduced it on all
10,203 fwdc_tex_r1 frames, eval/results/heading_bridge_offline_fwdc_tex_r1.json). Every frame of
the bag in stream order, seed = k. Also records per-frame time: C++ (in-library) and Python
(fwd_measure.heading, single-threaded) on a subsample of the same frames.
Usage (Phase 3 stack): nice -n 19 ~/venv-fwd/bin/python eval/heading_cpp_equivalence.py TRIAL_DIR [--json OUT] [--py-sample N]"""
import argparse, ctypes, json, math, os, sys, time
import numpy as np
import cv2
cv2.setNumThreads(1)
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "forward_camera"))
import fwd_measure as F

ap = argparse.ArgumentParser(); ap.add_argument("trial_dir"); ap.add_argument("--json")
ap.add_argument("--py-sample", type=int, default=500, help="frames (evenly spaced) also timed in Python")
a = ap.parse_args()
fz = json.load(open(os.path.join(HERE, "results", "fwd_calibration.json")))["frozen"]
INL, SMIN = float(fz["inlier_deg"]), float(fz["s_min"])
lib = ctypes.CDLL(os.path.join(ROOT, "src", "forward_camera", "cpp", "libheading.so"))
lib.hc_heading.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
                           ctypes.c_double, ctypes.c_double, ctypes.c_void_p, ctypes.c_void_p]
ref = np.load(f"{a.trial_dir}/fwd_meas/meas_frozen.npz")
rpsi, rsup, rt = ref["psi"][:, 0], ref["support"][:, 0], ref["t"]

ts = get_typestore(Stores.ROS2_JAZZY)
rows, cpp_t, py_t = [], [], []
dout, iout = np.zeros(6), np.zeros(6, dtype=np.int32)
with Reader(f"{a.trial_dir}/bag") as r:
    conns = [c for c in r.connections if c.topic == "/forward_camera/image"]
    n_total = sum(c.msgcount for c in conns)
    py_every = max(1, n_total // max(1, a.py_sample))
    for k, (con, _, raw) in enumerate(r.messages(connections=conns)):
        m = ts.deserialize_cdr(raw, con.msgtype)
        img = np.ascontiguousarray(np.frombuffer(m.data, np.uint8).reshape(m.height, m.step)[:, :m.width])
        lib.hc_heading(img.ctypes.data, m.width, m.height, img.strides[0], k, INL, SMIN, dout.ctypes.data, iout.ctypes.data)
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        rows.append((t, dout[0] if iout[0] else np.nan, dout[3] if iout[0] else 0.0, int(iout[0]), int(iout[4]), int(iout[5])))
        cpp_t.append(1e3 * dout[5])
        if k % py_every == 0:
            t0 = time.perf_counter(); F.heading(img, seed=k, inlier_deg=INL); py_t.append(1e3 * (time.perf_counter() - t0))
R = np.array(rows)
n = min(len(R), len(rpsi))
stamps_ok = bool(np.allclose(R[:n, 0], rt[:n], atol=1e-6)) and len(R) == len(rpsi)
c_has = R[:n, 3] == 1; r_has = np.isfinite(rpsi[:n])
r_valid = r_has & (rsup[:n] >= SMIN); c_valid = R[:n, 4] == 1
r_q = np.where(r_has, np.minimum(100, np.floor(50.0 * np.where(r_has, rsup[:n], 0) / SMIN)), -1).astype(int)
both = c_has & r_has
dpsi = np.abs(R[:n, 1] - rpsi[:n])[both]; dsup = np.abs(R[:n, 2] - rsup[:n])[both]
mis_exist = np.where(c_has != r_has)[0]; mis_valid = np.where(c_valid != r_valid)[0]; mis_q = np.where(R[:n, 5].astype(int) != r_q)[0]
# boundary cases (C1/C4): only a support within 1e-6 px of S_MIN / a quality step can excuse a mismatch
def boundary(i):
    return bool(r_has[i] and abs(rsup[i] - SMIN) <= 1e-6) or bool(r_has[i] and abs((50.0 * rsup[i] / SMIN) - round(50.0 * rsup[i] / SMIN)) * SMIN / 50.0 <= 1e-6)
out = {"trial": os.path.basename(a.trial_dir.rstrip("/")), "frames": int(n), "stamps_identical": stamps_ok,
       "C1": {"vp_existence_mismatch": mis_exist.tolist()[:50], "validity_mismatch": mis_valid.tolist()[:50],
              "unexplained": [int(i) for i in np.union1d(mis_exist, mis_valid) if not boundary(i)][:50]},
       "C2": {"max_abs_dpsi_deg": float(dpsi.max()) if len(dpsi) else 0.0, "n_exact": int((dpsi == 0).sum()), "n_both": int(both.sum())},
       "C3": {"max_abs_dsupport_px": float(dsup.max()) if len(dsup) else 0.0, "n_exact": int((dsup == 0).sum())},
       "C4": {"quality_mismatch": mis_q.tolist()[:50], "unexplained": [int(i) for i in mis_q if not boundary(i)][:50]},
       "timing_ms": {"cpp": {q: float(np.percentile(cpp_t, p)) for q, p in (("min", 0), ("median", 50), ("p95", 95), ("p99", 99), ("max", 100))},
                     "python_sample": {q: float(np.percentile(py_t, p)) for q, p in (("min", 0), ("median", 50), ("p95", 95), ("max", 100))},
                     "python_n": len(py_t), "note": "single-threaded; nice 19"}}
out["C1"]["pass"] = stamps_ok and not out["C1"]["unexplained"]
out["C2"]["pass"] = out["C2"]["max_abs_dpsi_deg"] <= 1e-6
out["C3"]["pass"] = out["C3"]["max_abs_dsupport_px"] <= 1e-6
out["C4"]["pass"] = not out["C4"]["unexplained"]
out["pass"] = all(out[c]["pass"] for c in ("C1", "C2", "C3", "C4"))
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
