"""Step-time summary (median / p95 / p99 / max, ms) for the yaw-cap-gate stage: Python replays, the C++ replay and the
C++ live adapter, with the binit0 (pre-gate) runs alongside where they exist."""
import os
import numpy as np
S = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad"


def summ(name, ms):
    if ms is None or len(ms) == 0:
        print(f"{name:52s} (missing)"); return
    print(f"{name:52s} n {len(ms):6d}  median {np.median(ms):7.3f}  p95 {np.percentile(ms, 95):7.3f}  "
          f"p99 {np.percentile(ms, 99):7.3f}  max {np.max(ms):8.3f}  >33ms {100 * np.mean(ms > 33.0):5.2f}%")


def py(root, trial, arm):
    f = f"{root}/out/{trial}/fgo_{arm}/timing_and_fwd.npz"
    return np.load(f)["t_keyframe_ns"] / 1e6 if os.path.exists(f) else None


def cpp(root, p):
    f = f"{root}/dump/cpp_{p}.step_ns.i64"
    return np.fromfile(f, np.int64) / 1e6 if os.path.exists(f) else None


def live(root, row):
    f = f"{root}/dump/{row}.live.f64"
    return np.fromfile(f).reshape(-1, 6)[:, 4] / 1e6 if os.path.exists(f) else None


for tag, root in (("gate", f"{S}/yawgate"), ("binit0", f"{S}/binit0")):
    for trial, arm in (("dsn_tex_r1", "baseline"), ("dsn_trans_r1", "baseline"), ("dsn_blank_r1", "baseline"),
                       ("fwdc_tex_r1", "heading")):
        summ(f"[{tag}] Python {trial} {arm}", py(root, trial, arm))
    for p in ("dsn_tex_r1_baseline", "fwdc_tex_r1_heading", "dsn_trans_r1_baseline", "dsn_blank_r1_baseline"):
        summ(f"[{tag}] C++ replay {p}", cpp(root, p))
    for row in ("L1", "L2"):
        summ(f"[{tag}] C++ live adapter {row}", live(root, row))
