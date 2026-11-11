#!/usr/bin/env python3
"""Stage-1 DIAGNOSTIC (read-only): count how many of the flow/range factors the FGO
actually used in a stored run would have failed an EKF3-style gate, had one existed.

Design note: docs/thesis/diagnostics/fgo_gate_count.md (read that first). This script
is the instrumentation described there. It does NOT modify fgo_core.py, factors.py,
measurement_models.py or fgo_replay.py (all imported unmodified); it wraps fgo_core.FGO
in a subclass (GateCountFGO) whose keyframe() reads the pre-call state, computes the
would-be gate decisions, logs them, then calls the REAL unmodified keyframe() with the
SAME arguments. No estimator code changes. No thesis result changes.

Usage:
  eval/fgo_gate_count.py --selftest                 # pure-math unit tests (no gtsam needed)
  eval/fgo_gate_count.py --selftest-fgo             # tiny synthetic FGO non-perturbation check (needs ~/venv-fgo)
  eval/fgo_gate_count.py --byte-identity <trial>     # Section 6 proof: control vs instrumented vs stored
  eval/fgo_gate_count.py --run <trial> [--arm ARM]   # instrumented replay only, writes a gate-count summary

All runs that touch a real trial write ONLY under ~/thesis_data/diagnostics/fgo_gate_count/ --
never into a trial directory. This is enforced by assertion, not by convention.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import runpy
import shutil
import subprocess
import sys
import time

import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FGO_DIR = os.path.expanduser("~/thesis_ws/src/estimators/fgo")
ESTIMATORS_DIR = os.path.expanduser("~/thesis_ws/src/estimators")
DIAG_ROOT = os.path.expanduser("~/thesis_data/diagnostics/fgo_gate_count")

# ---------- gate constants, all cited in docs/thesis/diagnostics/fgo_gate_count.md ----------
FLOW_I_GATE = 300.0                       # EK3_FLOW_I_GATE, AP_NavEKF3.cpp:41,321
HGT_I_GATE = 500.0                        # EK3_HGT_I_GATE, not RNG_I_GATE (design doc Section 4), AP_NavEKF3.cpp:226
FLOW_GATE_C = (0.01 * FLOW_I_GATE) ** 2   # 9.0, per-axis NIS gate (chi-square(1), 3-sigma)
RANGE_GATE_C = (0.01 * HGT_I_GATE) ** 2   # 25.0, range/height NIS gate (chi-square(1), 5-sigma)
# chi-square(2) quantile at the SAME confidence level the per-axis chi-square(1) gate of 9 implies.
# p = P(|Z| < 3) = erf(3/sqrt(2)) (standard identity: Phi(x) = 0.5*(1+erf(x/sqrt(2)))), chi-square(2)'s CDF is the
# closed form 1 - exp(-x/2), so its quantile at p is x = -2*ln(1-p). Computed analytically, no scipy dependency.
_P_3SIGMA = math.erf(3.0 / math.sqrt(2.0))
JOINT_GATE_CHI2_2 = -2.0 * math.log(1.0 - _P_3SIGMA)   # ~11.8295
FLOW_MAX = 2.5                            # EK3_FLOW_MAX, AP_NavEKF3.cpp:312


# ======================================================================================
# 1. Pure NIS math (no gtsam). This is the part Section 9 of the brief asks to unit-test.
# ======================================================================================

def nis_joint(A, b, P, R_identity_dim=None):
    """testRatio numerator/denominator pair for a whitened factor's (A, b), per
    FGO_DESIGN.md Section 9.2's literal recipe: S = A P A^T + I (R already folded into
    A, b by the noise model's whitening), nis = b^T S^-1 b. Returns the SCALAR nis
    (divide by the relevant gate_c externally to get testRatio)."""
    A = np.asarray(A, float)
    b = np.asarray(b, float).reshape(-1)
    P = np.asarray(P, float)
    m = A.shape[0] if R_identity_dim is None else R_identity_dim
    S = A @ P @ A.T + np.eye(m)
    return float(b @ np.linalg.solve(S, b))


def nis_per_row(A, b, P):
    """Row-by-row (per-axis) scalar NIS, each row's own S_i = A_i P A_i^T + 1. This is
    the independent-axis assumption EKF3 itself makes (FGO_DESIGN.md Section 9.3: "Fuse X
    and Y axis measurements sequentially assuming observation errors are uncorrelated").
    Returns a list, one entry per row of A."""
    A = np.asarray(A, float)
    b = np.asarray(b, float).reshape(-1)
    P = np.asarray(P, float)
    out = []
    for i in range(A.shape[0]):
        Ai = A[i:i + 1, :]
        Si = float((Ai @ P @ Ai.T).item()) + 1.0
        out.append(float(b[i] ** 2 / Si))
    return out


def flow_max_onesided_reject(flow_x_rad, flow_y_rad):
    """EKF3's FLOW_MAX test, re-expressed in the FGO's own flow_xy = (flow_x_rad,
    flow_y_rad) convention, for the CURRENT (post-2236590, 2026-09-29) flow_bridge.py
    mapping, design doc Section 3.1/3.2. One-sided, signed, factor-level (rejects
    BOTH axes if EITHER raw axis trips it, design doc Section 3): reject if
    flow_x_rad <= -FLOW_MAX OR flow_y_rad <= -FLOW_MAX."""
    return (flow_x_rad <= -FLOW_MAX) or (flow_y_rad <= -FLOW_MAX)


def flow_max_twosided_reject(flow_x_rad, flow_y_rad):
    """The UKF's FLOW_MAX test (ukf_core.py ~293, unchanged): abs(flow) >= FLOW_MAX on
    either axis, factor-level."""
    return (abs(flow_x_rad) >= FLOW_MAX) or (abs(flow_y_rad) >= FLOW_MAX)


# ======================================================================================
# 2. Pure-math self-test. Runs with plain numpy; no gtsam, no bag, no thesis data.
# ======================================================================================

def _selftest():
    failures = []

    def check(name, cond):
        if not cond:
            failures.append(name)
        print(("ok  " if cond else "FAIL") + " " + name)

    # --- range: 1-DOF, hand-computed ---
    # H = [1], P = [[4.0]] (sigma^2 = 4 on the single state dof this factor touches),
    # residual b = 3.0 (already whitened by R: the noise model here is irrelevant to
    # the pure-math check, A/b are just given numbers).
    A = np.array([[1.0]]); b = np.array([3.0]); P = np.array([[4.0]])
    nis = nis_joint(A, b, P)
    expected = 3.0 ** 2 / (1.0 * 4.0 * 1.0 + 1.0)   # S = A P A^T + I = 4 + 1 = 5
    check("range: nis_joint matches hand calc (nis=9/5=1.8)", abs(nis - expected) < 1e-12)
    check("range: nis=1.8 does not trip gate_c=25", not (nis > RANGE_GATE_C))

    # a residual large enough to trip the range gate
    A2 = np.array([[1.0]]); b2 = np.array([12.0]); P2 = np.array([[1.0]])
    nis2 = nis_joint(A2, b2, P2)   # S = 1+1=2, nis = 144/2 = 72
    check("range: nis=72 trips gate_c=25", nis2 > RANGE_GATE_C)

    # --- flow: 2-DOF joint vs per-axis, a case where ONE axis alone is fine but the
    # pair fails the naive joint gate of 9 (demonstrating why 9 and 11.83 differ) ---
    A3 = np.eye(2); b3 = np.array([2.9, 2.9]); P3 = np.zeros((2, 2))   # S = I (P contributes 0 here)
    axis = nis_per_row(A3, b3, P3)
    joint = nis_joint(A3, b3, P3)
    check("flow: per-axis NIS = b_i^2 (S_i=1 here)", all(abs(a - 2.9 ** 2) < 1e-12 for a in axis))
    check("flow: neither axis alone trips gate_c=9 (8.41 < 9)", all(a <= FLOW_GATE_C for a in axis))
    check("flow: joint NIS trips both the naive joint gate of 9 and chi2(2)=11.83 (16.82 > both)",
          joint > FLOW_GATE_C and joint > JOINT_GATE_CHI2_2)
    # a case that trips naive-9 but NOT chi2(2)=11.83: this is the discriminating case the
    # brief's "report both" was for: b=(2.3,2.3) -> joint = 2*(2.3^2) = 10.58
    A4 = np.eye(2); b4 = np.array([2.3, 2.3]); P4 = np.zeros((2, 2))
    joint4 = nis_joint(A4, b4, P4)
    check(f"flow: joint NIS {joint4:.3f} trips naive-9 but not chi2(2)=11.83 (discriminates the two thresholds)",
          joint4 > FLOW_GATE_C and joint4 <= JOINT_GATE_CHI2_2)
    check("chi2(2) quantile at the 3-sigma-equivalent confidence is ~11.83",
          abs(JOINT_GATE_CHI2_2 - 11.8295) < 1e-3)

    # --- FLOW_MAX one-sided vs two-sided asymmetry (design doc Section 3.1) ---
    check("FLOW_MAX: +3.0 on X is NOT rejected one-sided (EKF3)", not flow_max_onesided_reject(3.0, 0.0))
    check("FLOW_MAX: +3.0 on X IS rejected two-sided (UKF)", flow_max_twosided_reject(3.0, 0.0))
    check("FLOW_MAX: -3.0 on X IS rejected one-sided (EKF3)", flow_max_onesided_reject(-3.0, 0.0))
    check("FLOW_MAX: -3.0 on X IS rejected two-sided (UKF)", flow_max_twosided_reject(-3.0, 0.0))
    check("FLOW_MAX: -3.0 on Y alone rejects the WHOLE factor one-sided (factor-level, not axis-level)",
          flow_max_onesided_reject(0.0, -3.0))
    check("FLOW_MAX: within bounds on both axes rejects neither way", not flow_max_onesided_reject(1.0, -1.0)
          and not flow_max_twosided_reject(1.0, -1.0))

    print(f"\n{len(failures)} failing check(s)" if failures else "\nall checks passed")
    return len(failures) == 0


# ======================================================================================
# 3. The instrumented FGO subclass. Imports gtsam/fgo_core lazily so Section 2 above can
#    run without the ~/venv-fgo interpreter.
# ======================================================================================

def _load_fgo_core():
    for p in (ESTIMATORS_DIR, FGO_DIR):
        if p not in sys.path:
            sys.path.insert(0, p)
    import fgo_core as _fc
    import factors as _F
    return _fc, _F


def make_gate_count_fgo_class():
    """Builds GateCountFGO against whatever fgo_core/factors are importable right now.
    A function, not a module-level class, so importing this module never requires gtsam
    (Section 2's pure-math selftest stays gtsam-free)."""
    fgo_core, F = _load_fgo_core()

    class GateCountFGO(fgo_core.FGO):
        """Read-only wrapper. See module docstring and design doc Section 2."""

        # Fixed offsets of X(k)/V(k)/B(k) WITHIN the 15-wide block this class itself builds
        # (Section 2.1 step 4). This is NOT the same thing as a factor's own declared key order,
        # which is read dynamically below via jf.keys(), exactly as fgo_core._info() does.
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.gate_log = []
            self.gate_errors = []

        def _rel_offsets(self, k):
            """(start, dim) pairs, consumed as arange(start, start+dim) below. dim is 6 for a
            Pose3 tangent, 3 for a Vector3, 6 for a ConstantBias tangent (6+3+6=15, matching P15)."""
            return {fgo_core.X(k): (0, 6), fgo_core.V(k): (6, 3), fgo_core.B(k): (9, 6)}

        def _subcov(self, P15, keys, rel):
            idx = np.concatenate([np.arange(rel[kk][0], rel[kk][0] + rel[kk][1]) for kk in keys])
            return P15[np.ix_(idx, idx)]

        def keyframe(self, t, flow=None, omega=None, rng=None, fwd=None, tag=None, gnss=None):
            if self.pim.deltaTij() <= 0:
                return super().keyframe(t, flow=flow, omega=omega, rng=rng, fwd=fwd, tag=tag, gnss=gnss)
            km1, k = self.k, self.k + 1
            entry = {"t": float(t), "k": int(k)}
            try:
                pred = self.pim.predict(fgo_core.NavState(self.prev_pose, self.prev_vel), self.prev_bias)
                Xk, Vk = pred.pose(), pred.velocity()
                g_imu = fgo_core.gtsam.NonlinearFactorGraph()
                g_imu.add(fgo_core.CombinedImuFactor(fgo_core.X(km1), fgo_core.V(km1), fgo_core.X(k),
                                                      fgo_core.V(k), fgo_core.B(km1), fgo_core.B(k), self.pim))
                vals = self._values(km1, k, Xk, Vk, self.prev_bias)
                P15 = np.linalg.inv(self._info(g_imu, vals, km1, k, prior=self.cov_gate))[15:30, 15:30]
                rel = self._rel_offsets(k)

                r_lo, r_hi = (0.05, 40.0) if self.geom is None else (self.geom["rng_min"], self.geom["rng_max"])
                if rng is not None and r_lo <= rng <= r_hi:
                    f = F.range_factor(self.range_noise, fgo_core.X(k), rng, self.geom)
                    jf = f.linearize(vals)
                    A, b = jf.jacobian()
                    Psub = self._subcov(P15, list(jf.keys()), rel)
                    nis = nis_joint(A, b, Psub)
                    entry["range"] = {"nis": nis, "reject_25": bool(nis > RANGE_GATE_C), "rng_meas": float(rng)}

                if flow is not None:
                    flow_xy, valid, inlier = flow
                    if valid and inlier > 0.0 and abs(flow_xy[0]) < 4.2 and abs(flow_xy[1]) < 4.2:
                        f = F.flow_factor(self.flow_noise, fgo_core.X(k), fgo_core.V(k), fgo_core.B(k),
                                          flow_xy, omega, self.geom)
                        jf = f.linearize(vals)
                        A, b = jf.jacobian()
                        Psub = self._subcov(P15, list(jf.keys()), rel)
                        axis_nis = nis_per_row(A, b, Psub)
                        joint = nis_joint(A, b, Psub)
                        fx, fy = float(flow_xy[0]), float(flow_xy[1])
                        entry["flow"] = {
                            "nis_axis": axis_nis,
                            "reject_axis_9": [bool(n > FLOW_GATE_C) for n in axis_nis],
                            "nis_joint": joint,
                            "reject_joint_9": bool(joint > FLOW_GATE_C),
                            "reject_joint_11_83": bool(joint > JOINT_GATE_CHI2_2),
                            "flow_xy": [fx, fy],
                            "flow_max_onesided_reject": bool(flow_max_onesided_reject(fx, fy)),
                            "flow_max_twosided_reject": bool(flow_max_twosided_reject(fx, fy)),
                        }
            except Exception as e:   # never let the diagnostic break the real replay
                entry["error"] = repr(e)
                self.gate_errors.append(entry)
            self.gate_log.append(entry)
            return super().keyframe(t, flow=flow, omega=omega, rng=rng, fwd=fwd, tag=tag, gnss=gnss)

    return GateCountFGO


# ======================================================================================
# 4. Tiny synthetic FGO non-perturbation check (needs gtsam). Feeds a handful of made-up
#    IMU/flow/range samples to a plain FGO and to GateCountFGO and compares the resulting
#    trajectories, WITHOUT touching any bag or any thesis_data trial.
# ======================================================================================

def _selftest_fgo():
    fgo_core, F = _load_fgo_core()
    GateCountFGO = make_gate_count_fgo_class()

    def build_and_run(cls):
        f = cls(window=1.0, kf_dt=1.0 / 30.0, lm_maxiter=2)
        f.init(np.array([0.0, 0.0, 9.81]), 2.0, 0.0)
        t = 0.0
        rng_state = np.random.RandomState(0)
        for step in range(40):
            t += 1.0 / 333.0
            acc = np.array([0.1, 0.0, 9.81]) + rng_state.normal(0, 0.001, 3)
            gyro = np.array([0.0, 0.0, 0.0]) + rng_state.normal(0, 0.0005, 3)
            f.integrate_imu(acc, gyro, 1.0 / 333.0)
            if step % 10 == 9:
                f.keyframe(t, flow=(np.array([0.3, 0.05]), True, 0.9), omega=gyro, rng=2.0)
        return f

    plain = build_and_run(fgo_core.FGO)
    inst = build_and_run(GateCountFGO)
    p_plain, v_plain = plain.last[1], plain.last[2]
    p_inst, v_inst = inst.last[1], inst.last[2]
    pos_ok = np.allclose(p_plain.translation(), p_inst.translation(), atol=0, rtol=0)
    rot_ok = np.allclose(p_plain.rotation().matrix(), p_inst.rotation().matrix(), atol=0, rtol=0)
    vel_ok = np.allclose(v_plain, v_inst, atol=0, rtol=0)
    n_flow_ok = plain.n_flow == inst.n_flow
    n_range_ok = plain.n_range == inst.n_range
    gate_ran = len(inst.gate_log) > 0 and not inst.gate_errors
    print(f"position bit-identical: {pos_ok}")
    print(f"rotation bit-identical: {rot_ok}")
    print(f"velocity bit-identical: {vel_ok}")
    print(f"n_flow matches: {n_flow_ok} ({plain.n_flow} vs {inst.n_flow})")
    print(f"n_range matches: {n_range_ok} ({plain.n_range} vs {inst.n_range})")
    print(f"gate hook ran without error on {len(inst.gate_log)} keyframe(s): {gate_ran}")
    if inst.gate_errors:
        print("gate_errors:", inst.gate_errors)
    ok = pos_ok and rot_ok and vel_ok and n_flow_ok and n_range_ok and gate_ran
    print("PASS" if ok else "FAIL")
    return ok


# ======================================================================================
# 5. Real-trial drivers. Monkeypatch fgo_core.FGO, then runpy the UNMODIFIED fgo_replay.py
#    in-process (same technique as docs/handovers/2026-10-09_fgo_gate_conditioning.md).
# ======================================================================================

def _ensure_bag_readable(trial, scratch_root):
    """Mirrors the project's established PACKED-bag convention (eval/fgo_cpp_sitl_check.py's
    bag_dir_readable, eval/figs_*.py): if the trial's bag is zstd-PACKED, decompress a
    sha256-verified scratch COPY under `scratch_root/<trial>/` (never touching the trial
    directory) and point FGO_BAG_ROOT at `scratch_root`. Returns None if the bag is already
    a plain (unpacked) directory, in which case no FGO_BAG_ROOT override is needed."""
    b = os.path.expanduser(f"~/thesis_data/trials/{trial}/bag")
    if glob.glob(os.path.join(b, "*.db3")):
        return None     # already readable as-is
    z = sorted(glob.glob(os.path.join(b, "*.db3.zst")))
    assert z, f"no bag (.db3 or .db3.zst) found for trial {trial} at {b}"
    dst = os.path.join(scratch_root, "bagcache", trial)
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(b, "metadata.yaml"), dst)
    out = os.path.join(dst, os.path.basename(z[0])[:-4])
    if not os.path.exists(out):
        subprocess.run(["zstd", "-q", "-f", "-d", z[0], "-o", out], check=True)
    want = next((l.split()[1] for l in open(os.path.join(b, "PACKED.txt")) if l.startswith("sha256")), None)
    h = hashlib.sha256()
    with open(out, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 24), b""):
            h.update(blk)
    assert want == h.hexdigest(), f"sha256 mismatch decompressing {z[0]} (scratch copy corrupt?)"
    return os.path.join(scratch_root, "bagcache")


def _assert_safe_out_root(out_root):
    out_root = os.path.expanduser(out_root)
    assert out_root.startswith(DIAG_ROOT), (
        f"refusing to write outside {DIAG_ROOT}: {out_root} (never write into a trial directory)")
    os.makedirs(out_root, exist_ok=True)
    return out_root


def _run_fgo_replay(trial, out_root, instrumented, arm=None, window=1.0, lm_iters=2, extra_env=None):
    """Runs fgo_replay.py in-process via runpy, with argv/env set for `trial`, into
    `out_root` (must be under DIAG_ROOT). If instrumented, fgo_core.FGO is monkeypatched
    to GateCountFGO BEFORE fgo_replay.py's `from fgo_core import FGO` executes. Returns
    the module globals dict (so the caller can pull out `fgo`, `gate_log`, etc.)."""
    out_root = _assert_safe_out_root(out_root)
    for p in (ESTIMATORS_DIR, FGO_DIR):
        if p not in sys.path:
            sys.path.insert(0, p)
    fgo_core, _F = _load_fgo_core()
    if instrumented:
        fgo_core.FGO = make_gate_count_fgo_class()
    else:
        import importlib
        importlib.reload(fgo_core)   # restore the real FGO if a prior instrumented run patched it in-process

    env_backup = dict(os.environ)
    argv_backup = list(sys.argv)
    try:
        os.environ["FGO_OUT_ROOT"] = out_root
        bag_root = _ensure_bag_readable(trial, DIAG_ROOT)
        if bag_root:
            os.environ["FGO_BAG_ROOT"] = bag_root
        if extra_env:
            os.environ.update(extra_env)
        sys.argv = ["fgo_replay.py", trial, str(window), str(lm_iters)] + ([arm] if arm else [])
        script = os.path.join(FGO_DIR, "fgo_replay.py")
        g = runpy.run_path(script, run_name="__main__")
    finally:
        os.environ.clear(); os.environ.update(env_backup)
        sys.argv = argv_backup
    return g


def cmd_run(args):
    g = _run_fgo_replay(args.trial, args.out_root, instrumented=True, arm=args.arm,
                        window=args.window, lm_iters=args.lm_iters)
    fgo = g.get("fgo")
    assert fgo is not None and hasattr(fgo, "gate_log"), "instrumented run did not produce a gate_log"
    n_flow_checked = sum(1 for e in fgo.gate_log if "flow" in e)
    n_range_checked = sum(1 for e in fgo.gate_log if "range" in e)
    assert n_flow_checked == fgo.n_flow, (n_flow_checked, fgo.n_flow)
    assert n_range_checked == fgo.n_range, (n_range_checked, fgo.n_range)
    summary = _summarise(fgo.gate_log)
    summary["trial"] = args.trial
    summary["n_flow_factors"] = fgo.n_flow
    summary["n_range_factors"] = fgo.n_range
    summary["n_gate_errors"] = len(fgo.gate_errors)
    out_path = os.path.join(_assert_safe_out_root(args.out_root), f"{args.trial}_gate_summary.json")
    with open(out_path, "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"wrote {out_path}")


def _summarise(gate_log):
    flow_entries = [e["flow"] for e in gate_log if "flow" in e]
    range_entries = [e["range"] for e in gate_log if "range" in e]
    near = lambda v, g, tol=0.001: abs(v - g) <= tol * g   # "within +/-0.1% of the threshold" (design doc Section 7b)
    s = {
        "flow": {
            "n": len(flow_entries),
            "reject_axis_9": [sum(e["reject_axis_9"][i] for e in flow_entries) for i in range(2)] if flow_entries else [0, 0],
            "reject_joint_9": sum(e["reject_joint_9"] for e in flow_entries),
            "reject_joint_11_83": sum(e["reject_joint_11_83"] for e in flow_entries),
            "flow_max_onesided_reject": sum(e["flow_max_onesided_reject"] for e in flow_entries),
            "flow_max_twosided_reject": sum(e["flow_max_twosided_reject"] for e in flow_entries),
            "near_gate9_axis0": sum(near(e["nis_axis"][0], FLOW_GATE_C) for e in flow_entries),
            "near_gate9_axis1": sum(near(e["nis_axis"][1], FLOW_GATE_C) for e in flow_entries),
            "near_gate_joint9": sum(near(e["nis_joint"], FLOW_GATE_C) for e in flow_entries),
            "near_gate_joint11_83": sum(near(e["nis_joint"], JOINT_GATE_CHI2_2) for e in flow_entries),
        },
        "range": {
            "n": len(range_entries),
            "reject_25": sum(e["reject_25"] for e in range_entries),
            "near_gate25": sum(near(e["nis"], RANGE_GATE_C) for e in range_entries),
        },
    }
    return s


def cmd_byte_identity(args):
    trial = args.trial
    arm = args.arm
    scratch = _assert_safe_out_root(os.path.join(args.out_root, "byte_identity"))
    control_dir = os.path.join(scratch, "control")
    inst_dir = os.path.join(scratch, "instrumented")
    os.makedirs(control_dir, exist_ok=True); os.makedirs(inst_dir, exist_ok=True)
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

    t0 = time.time()
    g_ctrl = _run_fgo_replay(trial, control_dir, instrumented=False, arm=arm,
                             window=args.window, lm_iters=args.lm_iters)
    t1 = time.time()
    g_inst = _run_fgo_replay(trial, inst_dir, instrumented=True, arm=arm,
                             window=args.window, lm_iters=args.lm_iters)
    t2 = time.time()
    print(f"control run: {t1 - t0:.1f} s wall clock")
    print(f"instrumented run: {t2 - t1:.1f} s wall clock")

    # The hook-ran check (not an accuracy check): if the wrapper errored on every
    # keyframe, or never saw a flow/range factor, non-perturbation would be TRIVIALLY
    # true and would prove nothing. Assert the hook actually exercised both factor
    # types, on the full set the real FGO added, with zero internal errors.
    fgo_inst = g_inst.get("fgo")
    assert fgo_inst is not None and hasattr(fgo_inst, "gate_log"), "instrumented run produced no gate_log"
    n_flow_checked = sum(1 for e in fgo_inst.gate_log if "flow" in e)
    n_range_checked = sum(1 for e in fgo_inst.gate_log if "range" in e)
    hook_ok = (len(fgo_inst.gate_errors) == 0
               and n_flow_checked == fgo_inst.n_flow
               and n_range_checked == fgo_inst.n_range
               and fgo_inst.n_flow > 0 and fgo_inst.n_range > 0)
    print(f"hook ran cleanly: {hook_ok} (gate_errors={len(fgo_inst.gate_errors)}, "
          f"flow checked {n_flow_checked}/{fgo_inst.n_flow}, range checked {n_range_checked}/{fgo_inst.n_range})")

    sub = "" if arm is None else f"_{arm}"
    ctrl_tum = os.path.join(control_dir, trial, f"fgo{sub}", "fgo_traj.tum")
    inst_tum = os.path.join(inst_dir, trial, f"fgo{sub}", "fgo_traj.tum")
    stored_tum = os.path.expanduser(f"~/thesis_data/trials/{trial}/fgo{sub}/fgo_traj.tum")

    def cmp_files(a, b):
        if not (os.path.exists(a) and os.path.exists(b)):
            return None
        with open(a, "rb") as fa, open(b, "rb") as fb:
            return fa.read() == fb.read()

    ctrl_vs_inst = cmp_files(ctrl_tum, inst_tum)
    ctrl_vs_stored = cmp_files(ctrl_tum, stored_tum)
    result = {
        "trial": trial,
        "arm": arm,
        "control_tum": ctrl_tum,
        "instrumented_tum": inst_tum,
        "stored_tum": stored_tum,
        "control_vs_instrumented_byte_identical": ctrl_vs_inst,
        "control_vs_stored_byte_identical": ctrl_vs_stored,
        "hook_ran_cleanly": hook_ok,
        "n_flow_factors": fgo_inst.n_flow,
        "n_range_factors": fgo_inst.n_range,
        "control_wall_s": round(t1 - t0, 1),
        "instrumented_wall_s": round(t2 - t1, 1),
    }
    print(json.dumps(result, indent=2))
    if not hook_ok:
        print("STOP: the gate hook did not run cleanly on every factor the FGO actually added. "
              "A PASS below this line would not mean what it claims to mean.")
    elif ctrl_vs_inst is not True:
        print("STOP: instrumentation perturbs the estimate (control != instrumented). "
              "Per the brief, do not proceed to stage 2 until this is fixed.")
    elif ctrl_vs_stored is not True:
        print("NOTE: control != stored. This is a PROVENANCE finding (current code differs from "
              "whatever produced the stored file), not an instrumentation finding. The "
              "instrumentation itself is proven non-perturbing by the control-vs-instrumented match.")
    else:
        print("PASS: hook ran on every factor added, and control == instrumented == stored.")
    out_path = os.path.join(scratch, f"{trial}{sub}_byte_identity.json")
    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"wrote {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--selftest-fgo", action="store_true")
    ap.add_argument("--byte-identity", metavar="TRIAL")
    ap.add_argument("--run", metavar="TRIAL")
    ap.add_argument("--arm", default=None)
    ap.add_argument("--window", type=float, default=0.25)   # production default: eval/run_set_eval.sh's
    # "fgo_replay.py $t 0.25" (rerun_dsn, the stage that wrote the stored dsn_*/fgo/ outputs this
    # diagnostic compares against), not fgo_replay.py's own 1.0 s fallback, which is a scaffold
    # default never used by any production run (CLAUDE.md's FGO section: "window 0.25 s, a declared
    # config choice").
    ap.add_argument("--lm-iters", type=int, default=2)
    ap.add_argument("--out-root", default=DIAG_ROOT)
    args = ap.parse_args()

    if args.selftest:
        ok = _selftest()
        sys.exit(0 if ok else 1)
    if args.selftest_fgo:
        ok = _selftest_fgo()
        sys.exit(0 if ok else 1)
    if args.byte_identity:
        args.trial = args.byte_identity
        cmd_byte_identity(args)
        return
    if args.run:
        args.trial = args.run
        cmd_run(args)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
