#!/usr/bin/env python3
"""RAW CORRIDOR ERRORS (Stage 1, raw-corridor branch; D106/D107). DESCRIPTIVE ONLY — nothing in this file
changes, supersedes or re-derives any registered (evo -a, aligned) verdict.

User ruling 2026-11-02 (verbatim intent, raw-corridor brief): for every offline Experiment 1 flight (D106
scope), compute the raw (world-frame, NOTHING fitted — no rotation, translation or scale alignment) 3D
position error over the registered cruise window, alongside the already-registered evo -a (cruise) value,
labelled DESCRIPTIVE. Read-only on every input: no estimator run, no replay, no simulation. Writes
eval/results/raw_corridor_errors.json (full precision + provenance) and
docs/thesis/raw_corridor/raw_corridor_numbers.md (rounded tables); numbers.md is untouched.

FRAME (identical convention to eval/figs_thesis_drift.py / Figure 4.1c, R5 — re-derived here, not imported,
because that script is scoped to one flight):
  EKF3 traj + truth   (N, E, D) -> (N, E, U) = (col1, col2, -col3)
  UKF/FGO truth        ENU (E, N, U)          -> (N, E, U) = (col2, col1, col3)
  UKF/FGO estimate      own frame, x = take-off heading (North), y = West, z = up (yaw0 = 0.0 by
                         construction: ukf_core.py init_state() x[6:9] roll0,pitch0,0.0; fgo_core.py
                         init(yaw0=0.0) default) -> (N, E, U) = (col1, -col2, col3)
No other rotation, offset or scale. Verified numerically against a known mid-cruise ground-truth row
(dsn_tex_r1, both families) before being used for the whole scope — see the handover.

GATE (stop condition, run before any value is reported for a cell): recompute evo -a (cruise) on the SAME
association (sync.associate_trajectories, t_max_diff 0.05, as eval/three_way_eval.py/evo_ape -a) in the
cell's OWN (un-relabelled) stored frame — the frame the registered number was computed in — and require
string equality after rd(.,6) against the stored ate_a_cruise. The raw-frame relabel above is an improper
rotation for UKF/FGO (a reflection, E = -y), so the Umeyama SE3 fit (restricted to proper rotations) is
run in the cell's OWN frame for the gate, never in the relabelled frame — mixing them would not reproduce
the stored number. The raw (unaligned) error below, by contrast, is a plain subtraction (no rotation
search at all), so the relabelled frame is exactly right there and chirality does not matter.

FRAME CHECK (stop condition per flight-cell): take-off |NE| (own first sample) < ORIG_TOL_M for both
estimate and truth, and the heading of the first 5 m of TRUE cruise travel (from the window start) agrees
with the estimate's own heading over the same truth-defined interval to within HEAD_TOL_DEG. Computed from
each cell's own FULL (uncropped) files, exactly as eval/figs_thesis_drift.py.

Usage: /home/makerspace/venv-evo/bin/python eval/raw_corridor_errors.py
"""
import ast, hashlib, json, math, os, sys
import numpy as np
from evo.core import sync, metrics
from evo.core.trajectory import PoseTrajectory3D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results")
TD = os.path.expanduser("~/thesis_data/trials")
OUT_JSON = os.path.join(RES, "raw_corridor_errors.json")

T_MAX_DIFF = 0.05
ORIG_TOL_M = 0.05
HEAD_TOL_DEG = 2.0

# ----------------------------------------------------------------------------------------------- rd(), parsed (not hand-copied)
FT = os.path.join(HERE, "figs_thesis.py")
_src = open(FT).read()
_tree = ast.parse(_src)
_rd_node = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd")
_rd_src = ast.get_source_segment(_src, _rd_node)
_ns = {}
exec(compile(ast.Module(body=[_rd_node], type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
RD_SHA = hashlib.sha256(_rd_src.encode()).hexdigest()


# ----------------------------------------------------------------------------------------------- frame mapping
def to_NEU(family, a, is_truth):
    """(t, N, E, U), no alignment. See module docstring FRAME section."""
    t = a[:, 0]
    if family == "EKF3":
        return t, a[:, 1], a[:, 2], -a[:, 3]
    if is_truth:
        return t, a[:, 2], a[:, 1], a[:, 3]
    return t, a[:, 1], -a[:, 2], a[:, 3]


def crop(a, t0, t1):
    return a[(a[:, 0] >= t0) & (a[:, 0] <= t1)]


def tum_traj_raw(a):
    """Own (un-relabelled) frame, exactly eval/three_way_eval.py's tum_traj (used for the GATE only)."""
    return PoseTrajectory3D(positions_xyz=a[:, 1:4], orientations_quat_wxyz=a[:, [7, 4, 5, 6]], timestamps=a[:, 0])


def tum_traj_NEU(family, a, is_truth):
    """(N, E, U) relabelled frame, identity orientation (orientation unused by translation-only metrics).
    Timestamps are untouched by the relabel, so association against this gives the SAME matched pairs
    (by index) as association against the raw frame."""
    t, N, E, U = to_NEU(family, a, is_truth)
    pos = np.c_[N, E, U]
    q = np.tile([1.0, 0.0, 0.0, 0.0], (len(t), 1))
    return PoseTrajectory3D(positions_xyz=pos, orientations_quat_wxyz=q, timestamps=t)


def cruise_ate(ref_raw, est_raw, t0, t1):
    """GATE metric: evo -a (cruise) in the cell's own stored frame. Mirrors
    eval/three_way_eval.py::evaluate()+evo_ape_a() / eval/figs_thesis_drift.py::cruise_ate()."""
    r, e = sync.associate_trajectories(tum_traj_raw(crop(ref_raw, t0, t1)), tum_traj_raw(crop(est_raw, t0, t1)),
                                        T_MAX_DIFF)
    e.align(r, correct_scale=False)
    m = metrics.APE(metrics.PoseRelation.translation_part)
    m.process_data((r, e))
    return m.get_statistic(metrics.StatisticsType.rmse), len(r.timestamps)


def raw_errors(family, ref_raw, est_raw, t0, t1):
    """DESCRIPTIVE metric: raw (nothing fitted) 3D + horizontal error in the common (N, E, U) world frame,
    on the SAME association as the gate (same t0, t1, same t_max_diff)."""
    r, e = sync.associate_trajectories(tum_traj_NEU(family, crop(ref_raw, t0, t1), True),
                                        tum_traj_NEU(family, crop(est_raw, t0, t1), False), T_MAX_DIFF)
    err = e.positions_xyz - r.positions_xyz          # (n, 3) = (dN, dE, dU), nothing fitted
    n = len(err)
    rms3 = float(np.sqrt(np.mean(np.sum(err ** 2, axis=1))))
    end3 = float(np.linalg.norm(err[-1]))
    rmsh = float(np.sqrt(np.mean(err[:, 0] ** 2 + err[:, 1] ** 2)))
    endh = float(math.hypot(err[-1, 0], err[-1, 1]))
    return {"n_matched": n, "rms_3d_m": rms3, "end_3d_m": end3, "rms_h_m": rmsh, "end_h_m": endh,
            "window_s": [t0, t1], "t_last_matched_s": float(r.timestamps[-1])}


def frame_check(family, ref_full, est_full, t0):
    """Exactly eval/figs_thesis_drift.py's per-estimator frame check, on the cell's own FULL files."""
    tg, ng, eg, _ = to_NEU(family, ref_full, True)
    te, ne, ee, _ = to_NEU(family, est_full, False)
    o_est = math.hypot(ne[0], ee[0])
    o_gt = math.hypot(ng[0], eg[0])
    i0 = np.searchsorted(tg, t0)
    if i0 >= len(tg):
        return {"ok": False, "reason": "window start beyond truth file", "o_est": o_est, "o_gt": o_gt}
    rel = ng[i0:] - ng[i0]
    if not np.any(rel >= 5.0):
        return {"ok": False, "reason": "truth never travels 5 m after window start", "o_est": o_est, "o_gt": o_gt}
    j0 = i0 + int(np.argmax(rel >= 5.0))
    ta, tb = float(tg[i0]), float(tg[j0])
    dN_g, dE_g = ng[j0] - ng[i0], eg[j0] - eg[i0]
    dN_e = np.interp(tb, te, ne) - np.interp(ta, te, ne)
    dE_e = np.interp(tb, te, ee) - np.interp(ta, te, ee)
    h_g = math.degrees(math.atan2(dE_g, dN_g))
    h_e = math.degrees(math.atan2(dE_e, dN_e))
    ok = o_est < ORIG_TOL_M and o_gt < ORIG_TOL_M and abs(h_e - h_g) < HEAD_TOL_DEG
    return {"ok": bool(ok), "o_est": o_est, "o_gt": o_gt, "t_a": ta, "t_b": tb, "heading_est_deg": h_e,
            "heading_truth_deg": h_g}


# ----------------------------------------------------------------------------------------------- scope (from stored JSONs, not directory listings)
def load(name):
    return json.load(open(os.path.join(RES, name)))


DSN_SUB = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF": ("ukf", "ukf_traj.tum"), "FGO": ("fgo", "fgo_traj.tum")}


def dsn_cells():
    out = []
    for src_name in ("rerun_dsn_evo.json", "dsn_extra_evo.json"):
        d = load(src_name)
        for trial, t in d["trials"].items():
            if "tex" in trial:
                dataset = "dsn_tex"
            elif "blank" in trial:
                dataset = "dsn_blank"
            elif "trans" in trial:
                dataset = "dsn_trans"
            else:
                raise ValueError(trial)
            win = t["window_s"]
            for est, ed in t["est"].items():
                sub, traj_f = DSN_SUB[est]
                out.append({
                    "dataset": dataset, "trial": trial, "estimator": est, "arm": "baseline", "family": est,
                    "sub": sub, "traj_file": traj_f, "window_s": win,
                    "stored_ate_a_cruise": ed["ate_a_cruise"]["+0.00"],
                    "source": f"{src_name}:trials.{trial}.est.{est}.ate_a_cruise",
                })
    return out


def phase4_cells(dataset, arms_file):
    out = []
    d = load(arms_file)
    for trial, t in d.items():
        win = t["window_s"]
        for key, kd in t.items():
            if key == "window_s":
                continue
            est = "EKF3" if key == "EKF3" else key.split("_", 1)[0]
            arm = "baseline" if key == "EKF3" else key.split("_", 1)[1]
            sub = "ekf3" if key == "EKF3" else key.lower()
            traj_f = {"EKF3": "ekf3_traj.tum", "UKF": "ukf_traj.tum", "FGO": "fgo_traj.tum"}[est]
            ate = kd["ate_a_cruise"]["+0.00"] if "ate_a_cruise" in kd else kd["evo"]["ate_a_cruise"]["+0.00"]
            out.append({
                "dataset": dataset, "trial": trial, "estimator": est, "arm": arm, "family": est,
                "sub": sub, "traj_file": traj_f, "window_s": win, "stored_ate_a_cruise": ate,
                "source": f"{arms_file}:{trial}.{key}.ate_a_cruise",
            })
    return out


def build_scope():
    cells = dsn_cells()
    cells += phase4_cells("fwdc", "phase4_fwdc_arms.json")
    cells += phase4_cells("fwdplainc", "phase4_fwdplainc_arms.json")
    return cells


# ----------------------------------------------------------------------------------------------- main
def main():
    cells = build_scope()
    print(f"scope: {len(cells)} cells")
    results = []
    n_gate_ok = n_frame_ok = 0
    for c in cells:
        tdir = os.path.join(TD, c["trial"], c["sub"])
        traj_path = os.path.join(tdir, c["traj_file"])
        truth_path = os.path.join(tdir, "ground_truth.tum")
        rec = dict(c)
        rec["traj_path"] = traj_path
        rec["truth_path"] = truth_path
        if not (os.path.exists(traj_path) and os.path.exists(truth_path)):
            rec["stop"] = "missing input file"
            results.append(rec)
            print(f"STOP {c['trial']}/{c['sub']}: missing input file")
            continue
        est_full = np.loadtxt(traj_path)
        ref_full = np.loadtxt(truth_path)
        t0, t1 = c["window_s"]

        # --- GATE
        try:
            recomputed, n_gate = cruise_ate(ref_full, est_full, t0, t1)
        except Exception as ex:
            rec["stop"] = f"gate exception: {ex}"
            results.append(rec)
            print(f"STOP {c['trial']}/{c['sub']}: gate exception {ex}")
            continue
        stored = c["stored_ate_a_cruise"]
        gate_ok = rd(recomputed, 6) == rd(stored, 6)
        rec["gate"] = {"recomputed_ate_a_cruise": recomputed, "stored_ate_a_cruise": stored,
                       "n_matched": n_gate, "ok": gate_ok}
        if gate_ok:
            n_gate_ok += 1
        else:
            rec["stop"] = f"GATE FAIL: recomputed {recomputed!r} vs stored {stored!r}"
            results.append(rec)
            print(f"STOP {c['trial']}/{c['sub']}: GATE FAIL recomputed={recomputed} stored={stored}")
            continue

        # --- FRAME CHECK
        fc = frame_check(c["family"], ref_full, est_full, t0)
        rec["frame_check"] = fc
        if fc["ok"]:
            n_frame_ok += 1
        else:
            rec["stop"] = "frame check failed (see frame_check for the measured heading/origin)"
            results.append(rec)
            print(f"STOP {c['trial']}/{c['sub']}: FRAME CHECK FAIL {fc}")
            continue

        # --- RAW (descriptive) errors
        rec["raw"] = raw_errors(c["family"], ref_full, est_full, t0, t1)
        results.append(rec)

    n_ok = sum(1 for r in results if "stop" not in r)
    n_stop = sum(1 for r in results if "stop" in r)
    print(f"done: {len(results)} cells, {n_ok} OK, {n_stop} STOP, gate OK {n_gate_ok}, frame OK {n_frame_ok}")

    out = {
        "generated_by": "eval/raw_corridor_errors.py",
        "frame_note": "see module docstring FRAME section",
        "t_max_diff_s": T_MAX_DIFF, "orig_tol_m": ORIG_TOL_M, "head_tol_deg": HEAD_TOL_DEG,
        "rd_sha256": RD_SHA,
        "n_cells": len(results), "n_ok": n_ok, "n_stop": n_stop,
        "n_gate_ok": n_gate_ok, "n_frame_ok": n_frame_ok,
        "cells": results,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(out, open(OUT_JSON, "w"), indent=1)
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
