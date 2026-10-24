"""Per-job status line (pre-registration §9 'per job'): rc, keyframe failures, finiteness, rows, step median/p95."""
import os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rungs import *
j, rc, log = sys.argv[1], int(sys.argv[2]), sys.argv[3]
r, t, arm, d = parse(j)
txt = open(log).read() if os.path.exists(log) else ""
kff = len(re.findall(r"^\[warn\] keyframe at", txt, re.M))
tp = os.path.join(d, "fgo_traj.tum")
fin, n = "-", 0
if os.path.exists(tp):
    x = np.loadtxt(tp); n = len(x); fin = bool(np.all(np.isfinite(x)))
med = p95 = float("nan")
zp = os.path.join(d, "timing_and_fwd.npz")
if os.path.exists(zp):
    s = np.load(zp)["t_keyframe_ns"] / 1e6; med, p95 = np.median(s), np.percentile(s, 95)
status = "OK" if (rc == 0 and kff == 0 and fin is True) else "FAILED-ESTIMATOR"
print(f"{j}\trc={rc}\tkf_fail={kff}\tfinite={fin}\trows={n}\tstep_med_ms={med:.3f}\tstep_p95_ms={p95:.3f}\t{status}")
