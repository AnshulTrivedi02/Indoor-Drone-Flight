#!/usr/bin/env python3
"""Rung-1 scorer (real-flight plan item R9): the three estimators, all on the FC clock, against mocap, on ONE window
that is defined BY RULE in a pre-registration file written before flying.

Inputs (TUM: t x y z qx qy qz qw; all on the FC clock; z UP, gravity-aligned; any origin and heading):
  --mocap   mocap truth on the FC clock: eval/mocap_align.py's `mocap_fc_clock_est_frame.tum`.
  --est LABEL=PATH.tum           an estimator trajectory (e.g. the FGO from the dataflash converter), ENU.
  --est-bin LABEL=RECORD --bin LOG.bin
                                 an estimator read from a dataflash log (the Replay output): XKF1 (core 0) for EKF3,
                                 XUKO (the UKF's current-time output, the counterpart of XKF1) or XUKF (its fused state
                                 at the delayed horizon) for the UKF port, XFGO if present. NED -> ENU; written as TUM
                                 (identity quaternions) to --work-dir and scored from there.
  --prereg  the pre-registration JSON (window rule, metric settings). Its sha256 goes into the output.

WINDOW (computed from mocap ONLY, applied identically to every estimator):
  rule "airborne" (rung-1 default): height h = z - ground level (median z over the first `ground_ref_s` seconds of
      mocap); airborne = h > `airborne_height_m`; the LONGEST airborne run of at least `hold_s` is the flight;
      window = [take-off + `start_after_takeoff_s`, landing - `end_before_landing_s`]; refused if shorter than
      `min_duration_s`.
  rule "speed": three_way_eval's pinned cruise rule (largest run of smoothed horizontal speed > `speed_mps`).
  rule "fixed": `t0_s`, `t1_s` given (regression tests only; never for results).

METRICS per estimator, on the window (estimator samples inside it; mocap interpolated at their stamps):
  evo_ape_a_se3        evo_ape -a (Umeyama SE(3), no scale), RMSE, t_max_diff from the prereg; the SAME call as
                       three_way_eval (the simulation's STANDING metric, "evo -a (cruise)").
  ate_4dof             yaw + translation fit over the window (both frames gravity-aligned), RMSE 3-D / horizontal /
                       vertical. The plan's "evo -a (4-DoF)": evo has no yaw-only alignment, so it is computed here.
  drift_start_aligned  4-DoF fit on the first `drift_init_segment_s` of the window ONLY, then the error over the whole
                       window: RMSE, max, final, and final horizontal error / mocap path length (% of distance).
  coverage             samples, longest gap, fraction of the window within `max_gap_s` of a sample.
  The pre-registration names the PRIMARY metric; all are reported and labelled.

Usage (~/venv-ardupilot; evo_ape is called from ~/venv-evo):
  python3 eval/real_score.py --prereg PREREG.json --mocap MOCAP.tum --bin REPLAY.bin --est-bin EKF3=XKF1 \\
      --est-bin UKF=XUKO --est FGO=fgo_fc.tum --work-dir DIR --out score.json
"""
import argparse, hashlib, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
from three_way_eval import evo_ape_a, crop, write_tum      # identical evo call and TUM format to the simulation metric

DEFAULT_PREREG = {
    "window": {"rule": "airborne", "ground_ref_s": 3.0, "airborne_height_m": 0.30, "hold_s": 1.0,
               "start_after_takeoff_s": 25.0, "end_before_landing_s": 5.0, "min_duration_s": 20.0},
    "metrics": {"primary": "evo_ape_a_se3", "t_max_diff_s": 0.05, "drift_init_segment_s": 10.0, "max_gap_s": 0.5},
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_tum(path):
    a = np.loadtxt(path, ndmin=2)
    a = a[np.argsort(a[:, 0], kind="stable")]
    return a[np.r_[True, np.diff(a[:, 0]) > 0]]


# ---------------------------------------------------------------------------------------------- inputs
def bin_trajs(path, records):
    """{record: (N, 4) [t, PN, PE, PD]} from a dataflash log; XKF1 core 0 only."""
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(path); out = {r: [] for r in records}
    while True:
        x = m.recv_match(type=list(records))
        if x is None:
            break
        ty = x.get_type()
        if ty == "XKF1" and getattr(x, "C", 0) != 0:
            continue
        out[ty].append((x.TimeUS / 1e6, x.PN, x.PE, x.PD))
    return {k: np.array(v) for k, v in out.items()}


def ned_tum(a):
    """[t, PN, PE, PD] -> TUM ENU with identity quaternions (APE here is the translation part)."""
    return np.c_[a[:, 0], a[:, 2], a[:, 1], -a[:, 3], np.tile([0.0, 0.0, 0.0, 1.0], (len(a), 1))]


# ---------------------------------------------------------------------------------------------- window
def longest_run(mask):
    best, i, n = (0, 0), 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    return best


def window_from_rule(mo, w):
    t, z = mo[:, 0], mo[:, 3]
    if w["rule"] == "fixed":
        return float(w["t0_s"]), float(w["t1_s"]), {"rule": "fixed"}
    if w["rule"] == "speed":
        t0, t1 = cruise_bounds(t, mo[:, 1], mo[:, 2], w.get("speed_mps"))
        return t0, t1, {"rule": "speed", "speed_mps": w.get("speed_mps")}
    if w["rule"] != "airborne":
        raise SystemExit(f"unknown window rule {w['rule']}")
    g = float(np.median(z[t <= t[0] + w["ground_ref_s"]]))
    i, j = longest_run(z - g > w["airborne_height_m"])
    if j == i or t[j - 1] - t[i] < w["hold_s"]:
        raise SystemExit("no airborne segment in the mocap record")
    tk, tl = float(t[i]), float(t[j - 1])
    t0, t1 = tk + w["start_after_takeoff_s"], tl - w["end_before_landing_s"]
    info = {"rule": "airborne", "ground_level_m": g, "takeoff_s": tk, "landing_s": tl}
    if t1 - t0 < w["min_duration_s"]:
        raise SystemExit(f"window [{t0:.2f}, {t1:.2f}] shorter than min_duration_s = {w['min_duration_s']}")
    return t0, t1, info


# ---------------------------------------------------------------------------------------------- metrics
def fit_4dof(src, dst):
    """yaw + translation with dst ~= Rz src + t (both z up)."""
    cs, cd = src.mean(0), dst.mean(0); a, b = src[:, :2] - cs[:2], dst[:, :2] - cd[:2]
    yaw = math.atan2(np.sum(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]), np.sum(a[:, 0] * b[:, 0] + a[:, 1] * b[:, 1]))
    c, s = math.cos(yaw), math.sin(yaw); Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return yaw, Rz, cd - Rz @ cs


def err_stats(e):
    n3, nh = np.linalg.norm(e, axis=1), np.linalg.norm(e[:, :2], axis=1)
    return {"rmse_m": float(np.sqrt(np.mean(n3 ** 2))), "rmse_h_m": float(np.sqrt(np.mean(nh ** 2))),
            "rmse_v_m": float(np.sqrt(np.mean(e[:, 2] ** 2))), "max_m": float(n3.max())}


def score_one(mo, est, t0, t1, m, tmp, label):
    e = crop(est, t0, t1)
    e = e[(e[:, 0] >= mo[0, 0]) & (e[:, 0] <= mo[-1, 0])]
    if len(e) < 10:
        return {"error": f"only {len(e)} estimator samples inside the window"}
    gt = np.c_[[np.interp(e[:, 0], mo[:, 0], mo[:, k]) for k in (1, 2, 3)]].T
    pe = e[:, 1:4]
    # evo -a (SE(3)), the standing simulation metric: reference = mocap cropped to the same window
    rc, ec = f"{tmp}/{label}_ref.tum", f"{tmp}/{label}_est.tum"
    write_tum(rc, crop(mo, t0, t1)); write_tum(ec, e)
    out = {"n": int(len(e)), "evo_ape_a_se3": {"rmse_m": evo_ape_a(rc, ec), "t_max_diff_s": m["t_max_diff_s"]}}
    # 4-DoF over the window (mocap -> estimator frame)
    yaw, Rz, tr = fit_4dof(gt, pe); res = pe - ((Rz @ gt.T).T + tr)
    out["ate_4dof"] = {**err_stats(res), "yaw_deg": math.degrees(yaw)}
    # start-aligned drift
    s = e[:, 0] <= t0 + m["drift_init_segment_s"]
    if s.sum() >= 5:
        yaw0, R0, tr0 = fit_4dof(gt[s], pe[s]); r0 = pe - ((R0 @ gt.T).T + tr0)
        path = float(np.sum(np.linalg.norm(np.diff(gt[:, :2], axis=0), axis=1)))
        fh = float(np.linalg.norm(r0[-1, :2]))
        out["drift_start_aligned"] = {**err_stats(r0), "final_m": float(np.linalg.norm(r0[-1])), "final_h_m": fh,
                                      "mocap_path_length_h_m": path,
                                      "final_h_pct_of_path": 100.0 * fh / path if path > 0 else None,
                                      "init_segment_s": m["drift_init_segment_s"], "yaw_deg": math.degrees(yaw0)}
    else:
        out["drift_start_aligned"] = {"error": "fewer than 5 samples in the initial segment"}
    # coverage
    st = np.r_[t0, e[:, 0], t1]; gaps = np.diff(st)
    out["coverage"] = {"longest_gap_s": float(gaps.max()),
                       "fraction_within_max_gap": float(1.0 - np.sum(gaps[gaps > m["max_gap_s"]]) / (t1 - t0)),
                       "first_s": float(e[0, 0]), "last_s": float(e[-1, 0])}
    return out


def merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prereg", required=True); ap.add_argument("--mocap", required=True)
    ap.add_argument("--est", action="append", default=[], help="LABEL=PATH.tum (FC clock, ENU)")
    ap.add_argument("--est-bin", action="append", default=[], help="LABEL=RECORD from --bin (XKF1, XUKO, XUKF, XFGO)")
    ap.add_argument("--bin"); ap.add_argument("--work-dir", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); os.makedirs(a.work_dir, exist_ok=True)
    pre = merge(DEFAULT_PREREG, json.load(open(a.prereg)))
    mo = load_tum(a.mocap)
    t0, t1, winfo = window_from_rule(mo, pre["window"])
    ests = {}
    for s in a.est:
        lab, p = s.split("=", 1); ests[lab] = {"source": os.path.abspath(p), "sha256": sha256(p), "traj": load_tum(p)}
    if a.est_bin:
        if not a.bin:
            raise SystemExit("--est-bin needs --bin")
        pairs = [s.split("=", 1) for s in a.est_bin]
        tr = bin_trajs(a.bin, sorted({r for _, r in pairs}))
        for lab, rec in pairs:
            if not len(tr[rec]):
                raise SystemExit(f"no {rec} records in {a.bin}")
            p = f"{a.work_dir}/{lab}_{rec}.tum"; write_tum(p, ned_tum(tr[rec]))
            ests[lab] = {"source": f"{os.path.abspath(a.bin)}:{rec}", "sha256": sha256(a.bin), "traj": load_tum(p)}
    out = {"prereg": {"path": os.path.abspath(a.prereg), "sha256": sha256(a.prereg), "resolved": pre},
           "mocap": {"path": os.path.abspath(a.mocap), "sha256": sha256(a.mocap), "n": int(len(mo))},
           "window_s": [t0, t1], "window_info": winfo, "primary_metric": pre["metrics"]["primary"], "estimators": {}}
    for lab, d in ests.items():
        r = score_one(mo, d["traj"], t0, t1, pre["metrics"], a.work_dir, lab)
        out["estimators"][lab] = {"source": d["source"], "sha256": d["sha256"], **r}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"window [{t0:.2f}, {t1:.2f}] s ({winfo['rule']}), primary metric {out['primary_metric']}")
    print(f"{'est':8}{'evo -a':>10}{'4DoF':>10}{'drift fin':>11}{'drift %':>9}{'n':>7}")
    for lab, r in out["estimators"].items():
        if "error" in r:
            print(f"{lab:8} {r['error']}"); continue
        d = r["drift_start_aligned"]
        print(f"{lab:8}{r['evo_ape_a_se3']['rmse_m']:10.3f}{r['ate_4dof']['rmse_m']:10.3f}"
              f"{d.get('final_m', float('nan')):11.3f}{(d.get('final_h_pct_of_path') or float('nan')):9.2f}{r['n']:7d}")
    print(f"[out] {a.out}")


if __name__ == "__main__":
    main()
