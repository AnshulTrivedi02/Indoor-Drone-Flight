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
  --prereg  the pre-registration JSON. Its sha256 goes into the output. It is read STRICTLY (load_prereg): every key
            below is required, unknown keys are refused, and nothing is filled in from defaults, so the scored
            definitions are exactly the file's. The rung-1 draft is docs/rung1_preregistration_draft.json.
  --mocap-align-json  mocap_align.py's JSON for this flight; required when the prereg has a `clock_map` section, whose
            rule it is checked against (default windows used, the same sync-wiggle thresholds).

PRE-REGISTRATION SCHEMA (2026-10-11):
  window             {"rule": "airborne" | "speed" | "fixed", + that rule's keys (below)}
  metrics            {"primary": "evo_ape_a_se3" | "ate_4dof", "t_max_diff_s": 0.05 (the only value: evo is called
                      exactly as three_way_eval), "max_gap_s", "max_mocap_interp_gap_s"}
  drift              {"segment_rule": "motion_onset_path" | "window_start_time", + that rule's keys (below)}
  estimator_records  {LABEL: "XKF1" | "XUKO" | "XUKF" | "XFGO" | "TUM"}: every scored label must be listed, and a
                      --est-bin LABEL=RECORD must name exactly this record (a TUM input needs "TUM")
  clock_map          optional {"rule": "disarmed_wiggles", "w_thr_rad_s", "pad_s", "merge_s", "min_burst_s"}
  name, status, notes, rationale   free text (kept in the output)

WINDOW (computed from mocap ONLY, applied identically to every estimator):
  rule "airborne" (rung-1 default): height h = z - ground level (the `ground_percentile` percentile of mocap z over
      the WHOLE record: the vehicle rests at both ends, while the record may START with it held up for the sync
      wiggle); airborne = h > `airborne_height_m`; the LONGEST airborne run of at least `hold_s` is the flight;
      window = [take-off + `start_after_takeoff_s`, landing - `end_before_landing_s`]; refused if shorter than
      `min_duration_s`.
  rule "speed": three_way_eval's pinned cruise rule (largest run of smoothed horizontal speed > `speed_mps`).
  rule "fixed": `t0_s`, `t1_s` given (regression tests only; never for results).

METRICS per estimator, on the window (estimator samples inside it; mocap interpolated at their stamps, but ONLY where
the two bracketing mocap samples are <= `max_mocap_interp_gap_s` apart: across a mocap dropout the truth would be
invented, so those estimator samples are dropped from the in-house metrics and counted; evo is given the full set):
  evo_ape_a_se3        evo_ape -a (Umeyama SE(3), no scale), RMSE, t_max_diff from the prereg; the SAME call as
                       three_way_eval (the simulation's STANDING metric, "evo -a (cruise)").
  ate_4dof             yaw + translation fit over the window (both frames gravity-aligned), RMSE 3-D / horizontal /
                       vertical. The plan's "evo -a (4-DoF)": evo has no yaw-only alignment, so it is computed here.
  drift_start_aligned  4-DoF fit on an INITIAL SEGMENT ONLY, then the error over the whole window: RMSE, max, final,
                       and final horizontal error / mocap path length (% of distance). The segment (prereg `drift`):
                         motion_onset_path (rung 1): from the motion onset (the first time in the window the mocap
                           horizontal speed, boxcar `onset_smooth_s`, stays above `onset_speed_mps` for `onset_hold_s`)
                           until the mocap has travelled `init_path_m` horizontally: on the first leg, never in the
                           hover (fixes the draft's defect 1: [t_to + 25 s, t_to + 30 s] was inside the hover);
                         window_start_time: the first `init_segment_s` of the window (regression/tests).
                       The yaw of that fit is only defined if the segment MOVES horizontally: the metric is refused
                       when the segment's horizontal extent (largest distance from its first point) is below
                       `min_extent_m`.
  coverage             samples, longest gap, fraction of the window within `max_gap_s` of a sample.
  The pre-registration names the PRIMARY metric (output `primary`); all are reported and labelled.

Usage (~/venv-ardupilot; evo_ape is called from ~/venv-evo):
  python3 eval/real_score.py --prereg PREREG.json --mocap MOCAP.tum --bin REPLAY.bin --est-bin EKF3=XKF1 \\
      --est-bin UKF=XUKO --est FGO=fgo_fc.tum --work-dir DIR --out score.json
"""
import argparse, hashlib, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
from three_way_eval import evo_ape_a, crop, write_tum, T_MAX_DIFF   # identical evo call, TUM format, t_max_diff

DEFAULT_PREREG = {      # a COMPLETE, valid pre-registration for the tests; main() never fills anything in from it
    "window": {"rule": "airborne", "ground_percentile": 5.0, "airborne_height_m": 0.30, "hold_s": 1.0,
               "start_after_takeoff_s": 25.0, "end_before_landing_s": 5.0, "min_duration_s": 20.0},
    "metrics": {"primary": "evo_ape_a_se3", "t_max_diff_s": 0.05, "max_gap_s": 0.5, "max_mocap_interp_gap_s": 0.05},
    "drift": {"segment_rule": "motion_onset_path", "onset_speed_mps": 0.15, "onset_smooth_s": 1.0, "onset_hold_s": 1.0,
              "init_path_m": 2.0, "min_extent_m": 1.0},
    "estimator_records": {"EKF3": "XKF1", "UKF": "XUKO", "FGO": "TUM"},
}

WINDOW_KEYS = {"airborne": {"ground_percentile", "airborne_height_m", "hold_s", "start_after_takeoff_s",
                            "end_before_landing_s", "min_duration_s"},
               "speed": {"speed_mps"}, "fixed": {"t0_s", "t1_s"}}
DRIFT_KEYS = {"motion_onset_path": {"onset_speed_mps", "onset_smooth_s", "onset_hold_s", "init_path_m", "min_extent_m"},
              "window_start_time": {"init_segment_s", "min_extent_m"}}
METRIC_KEYS = {"primary", "t_max_diff_s", "max_gap_s", "max_mocap_interp_gap_s"}
PRIMARY = ("evo_ape_a_se3", "ate_4dof")
RECORDS = ("XKF1", "XUKO", "XUKF", "XFGO", "TUM")
CLOCK_KEYS = {"rule", "w_thr_rad_s", "pad_s", "merge_s", "min_burst_s"}
TOP_KEYS = {"window", "metrics", "drift", "estimator_records"}
TOP_OPTIONAL = {"clock_map", "name", "status", "notes", "rationale"}


def _exact(d, need, where):
    if not isinstance(d, dict):
        raise SystemExit(f"prereg {where}: must be an object")
    miss, extra = sorted(need - set(d)), sorted(set(d) - need)
    if miss or extra:
        raise SystemExit(f"prereg {where}: missing keys {miss}, unknown keys {extra}")


def load_prereg(src):
    """The pre-registration, validated STRICTLY (see the module docstring). src: a path or a dict. Nothing is defaulted."""
    pre = json.load(open(src)) if isinstance(src, str) else src
    miss, extra = sorted(TOP_KEYS - set(pre)), sorted(set(pre) - TOP_KEYS - TOP_OPTIONAL)
    if miss or extra:
        raise SystemExit(f"prereg: missing sections {miss}, unknown sections {extra}")
    w = pre["window"]
    if not isinstance(w, dict) or w.get("rule") not in WINDOW_KEYS:
        raise SystemExit(f"prereg window.rule must be one of {sorted(WINDOW_KEYS)}")
    _exact(w, WINDOW_KEYS[w["rule"]] | {"rule"}, "window")
    m = pre["metrics"]; _exact(m, METRIC_KEYS, "metrics")
    if m["primary"] not in PRIMARY:
        raise SystemExit(f"prereg metrics.primary must be one of {PRIMARY}")
    if float(m["t_max_diff_s"]) != float(T_MAX_DIFF):
        raise SystemExit(f"prereg metrics.t_max_diff_s must be {T_MAX_DIFF} (evo is called exactly as three_way_eval)")
    d = pre["drift"]
    if not isinstance(d, dict) or d.get("segment_rule") not in DRIFT_KEYS:
        raise SystemExit(f"prereg drift.segment_rule must be one of {sorted(DRIFT_KEYS)}")
    _exact(d, DRIFT_KEYS[d["segment_rule"]] | {"segment_rule"}, "drift")
    er = pre["estimator_records"]
    if not isinstance(er, dict) or not er or any(v not in RECORDS for v in er.values()):
        raise SystemExit(f"prereg estimator_records: {{LABEL: one of {RECORDS}}}")
    if "clock_map" in pre:
        _exact(pre["clock_map"], CLOCK_KEYS, "clock_map")
        if pre["clock_map"]["rule"] != "disarmed_wiggles":
            raise SystemExit("prereg clock_map.rule must be 'disarmed_wiggles'")
    return pre


def check_clock_map(cm, align):
    """The flight's mocap_align JSON against the prereg clock_map: default windows, the same wiggle-burst rule."""
    src = align.get("window_sources") or {}
    bad = [k for k in ("early", "late") if not str(src.get(k, "")).startswith("default")]
    if bad:
        raise SystemExit(f"mocap_align windows {bad} were not the pre-registered default (window_sources {src})")
    rule = align.get("sync_window_rule") or {}
    want = {k: cm[k] for k in ("w_thr_rad_s", "pad_s", "merge_s", "min_burst_s")}
    if any(abs(float(rule.get(k, float("nan"))) - float(v)) > 1e-9 for k, v in want.items()):
        raise SystemExit(f"mocap_align sync_window_rule {rule} differs from the prereg clock_map {want}")
    return {"window_sources": src, "sync_window_rule": rule}


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
    g = float(np.percentile(z, w["ground_percentile"]))
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


def drift_segment(mo, t0, t1, d):
    """(s0, s1, None) on the FC clock: the drift metric's initial segment, from MOCAP only; or (.., .., reason)."""
    if d["segment_rule"] == "window_start_time":
        return t0, t0 + d["init_segment_s"], None
    w = (mo[:, 0] >= t0) & (mo[:, 0] <= t1); t, xy = mo[w, 0], mo[w, 1:3]
    if len(t) < 10:
        return None, None, "fewer than 10 mocap samples in the window"
    sp = np.hypot(np.gradient(xy[:, 0], t), np.gradient(xy[:, 1], t))
    n = max(1, int(round(d["onset_smooth_s"] / float(np.median(np.diff(t))))))
    sp = np.convolve(sp, np.ones(n) / n, "same")
    hi = sp > d["onset_speed_mps"]; k = None; i = 0
    while i < len(t):
        if hi[i]:
            j = i
            while j < len(t) and hi[j]:
                j += 1
            if t[j - 1] - t[i] >= d["onset_hold_s"]:
                k = i
                break
            i = j
        else:
            i += 1
    if k is None:
        return None, None, (f"no motion onset (speed > {d['onset_speed_mps']} m/s for {d['onset_hold_s']} s) "
                            f"in the window")
    path = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(xy[k:], axis=0), axis=1))]
    m = np.where(path >= d["init_path_m"])[0]
    if not len(m):
        return float(t[k]), None, f"the mocap travels only {path[-1]:.2f} m after the onset (< init_path_m)"
    return float(t[k]), float(t[k + m[0]]), None


def drift_metric(gt, pe, te, mo, t0, t1, d):
    s0, s1, why = drift_segment(mo, t0, t1, d)
    if why:
        return {"error": why, "segment_rule": d["segment_rule"]}
    s = (te >= s0) & (te <= s1)
    if s.sum() < 5:
        return {"error": "fewer than 5 samples in the initial segment", "segment_fc_s": [s0, s1]}
    ext = float(np.max(np.linalg.norm(gt[s, :2] - gt[s][0, :2], axis=1)))
    if ext < d["min_extent_m"]:
        return {"error": f"initial segment moves only {ext:.3f} m horizontally (< min_extent_m = {d['min_extent_m']}): "
                         f"yaw undefined", "init_segment_extent_h_m": ext, "segment_fc_s": [s0, s1]}
    yaw0, R0, tr0 = fit_4dof(gt[s], pe[s]); r0 = pe - ((R0 @ gt.T).T + tr0)
    path = float(np.sum(np.linalg.norm(np.diff(gt[:, :2], axis=0), axis=1)))
    fh = float(np.linalg.norm(r0[-1, :2]))
    return {**err_stats(r0), "final_m": float(np.linalg.norm(r0[-1])), "final_h_m": fh, "mocap_path_length_h_m": path,
            "final_h_pct_of_path": 100.0 * fh / path if path > 0 else None, "segment_rule": d["segment_rule"],
            "segment_fc_s": [s0, s1], "init_segment_extent_h_m": ext, "yaw_deg": math.degrees(yaw0)}


def score_one(mo, est, t0, t1, m, tmp, label, drift=None):
    drift = DEFAULT_PREREG["drift"] if drift is None else drift
    e = crop(est, t0, t1)
    e = e[(e[:, 0] >= mo[0, 0]) & (e[:, 0] <= mo[-1, 0])]
    if len(e) < 10:
        return {"error": f"only {len(e)} estimator samples inside the window"}
    # evo -a (SE(3)), the standing simulation metric: reference = mocap cropped to the same window. evo associates by
    # nearest stamp within t_max_diff (no interpolation), so it is given the full cropped estimate, as three_way_eval.
    rc, ec = f"{tmp}/{label}_ref.tum", f"{tmp}/{label}_est.tum"
    write_tum(rc, crop(mo, t0, t1)); write_tum(ec, e)
    out = {"n": int(len(e)), "evo_ape_a_se3": {"rmse_m": evo_ape_a(rc, ec), "t_max_diff_s": m["t_max_diff_s"]}}
    # in-house metrics: interpolate mocap only where it is bracketed closely (no truth invented across a dropout)
    j = np.searchsorted(mo[:, 0], e[:, 0]).clip(1, len(mo) - 1)
    ok = (mo[j, 0] - mo[j - 1, 0]) <= m["max_mocap_interp_gap_s"]
    ok |= np.isin(e[:, 0], mo[:, 0])                                   # exact stamp matches are always fine
    out["n_in_house"] = int(ok.sum()); out["n_dropped_mocap_gap"] = int((~ok).sum())
    e = e[ok]
    if len(e) < 10:
        out["error"] = f"only {len(e)} estimator samples with bracketing mocap"
        return out
    gt = np.c_[[np.interp(e[:, 0], mo[:, 0], mo[:, k]) for k in (1, 2, 3)]].T
    pe = e[:, 1:4]
    # 4-DoF over the window (mocap -> estimator frame)
    yaw, Rz, tr = fit_4dof(gt, pe); res = pe - ((Rz @ gt.T).T + tr)
    out["ate_4dof"] = {**err_stats(res), "yaw_deg": math.degrees(yaw)}
    # start-aligned drift
    out["drift_start_aligned"] = drift_metric(gt, pe, e[:, 0], mo, t0, t1, drift)
    # coverage
    st = np.r_[t0, e[:, 0], t1]; gaps = np.diff(st)
    out["coverage"] = {"longest_gap_s": float(gaps.max()),
                       "fraction_within_max_gap": float(1.0 - np.sum(gaps[gaps > m["max_gap_s"]]) / (t1 - t0)),
                       "first_s": float(e[0, 0]), "last_s": float(e[-1, 0])}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prereg", required=True); ap.add_argument("--mocap", required=True)
    ap.add_argument("--mocap-align-json", help="mocap_align.py's JSON (required if the prereg has clock_map)")
    ap.add_argument("--est", action="append", default=[], help="LABEL=PATH.tum (FC clock, ENU)")
    ap.add_argument("--est-bin", action="append", default=[], help="LABEL=RECORD from --bin (XKF1, XUKO, XUKF, XFGO)")
    ap.add_argument("--bin"); ap.add_argument("--work-dir", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv); os.makedirs(a.work_dir, exist_ok=True)
    pre = load_prereg(a.prereg); er = pre["estimator_records"]
    clock = None
    if "clock_map" in pre:
        if not a.mocap_align_json:
            raise SystemExit("the prereg has clock_map: give --mocap-align-json")
        clock = check_clock_map(pre["clock_map"], json.load(open(a.mocap_align_json)))
    mo = load_tum(a.mocap)
    t0, t1, winfo = window_from_rule(mo, pre["window"])
    ests = {}
    for s in a.est:
        lab, p = s.split("=", 1)
        if er.get(lab) != "TUM":
            raise SystemExit(f"--est {lab}: the prereg's estimator_records has {lab} = {er.get(lab)!r}, not 'TUM'")
        ests[lab] = {"source": os.path.abspath(p), "sha256": sha256(p), "traj": load_tum(p), "record": "TUM"}
    if a.est_bin:
        if not a.bin:
            raise SystemExit("--est-bin needs --bin")
        pairs = [s.split("=", 1) for s in a.est_bin]
        for lab, rec in pairs:
            if er.get(lab) != rec:
                raise SystemExit(f"--est-bin {lab}={rec}: the prereg's estimator_records has {lab} = {er.get(lab)!r}")
        tr = bin_trajs(a.bin, sorted({r for _, r in pairs}))
        for lab, rec in pairs:
            if not len(tr[rec]):
                raise SystemExit(f"no {rec} records in {a.bin}")
            p = f"{a.work_dir}/{lab}_{rec}.tum"; write_tum(p, ned_tum(tr[rec]))
            ests[lab] = {"source": f"{os.path.abspath(a.bin)}:{rec}", "sha256": sha256(a.bin), "traj": load_tum(p),
                         "record": rec}
    prim = pre["metrics"]["primary"]
    out = {"prereg": {"path": os.path.abspath(a.prereg), "sha256": sha256(a.prereg), "resolved": pre},
           "mocap": {"path": os.path.abspath(a.mocap), "sha256": sha256(a.mocap), "n": int(len(mo))},
           "clock_map_check": clock, "window_s": [t0, t1], "window_info": winfo, "primary_metric": prim,
           "primary": {}, "estimators": {}}
    for lab, d in ests.items():
        r = score_one(mo, d["traj"], t0, t1, pre["metrics"], a.work_dir, lab, pre["drift"])
        out["estimators"][lab] = {"source": d["source"], "record": d["record"], "sha256": d["sha256"], **r}
        out["primary"][lab] = r[prim]["rmse_m"] if prim in r else None
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"window [{t0:.2f}, {t1:.2f}] s ({winfo['rule']}), primary metric {prim}")
    print(f"{'est':8}{'evo -a':>10}{'4DoF':>10}{'drift fin':>11}{'drift %':>9}{'n':>7}")
    for lab, r in out["estimators"].items():
        if "error" in r:
            print(f"{lab:8} {r['error']}"); continue
        d = r["drift_start_aligned"]
        print(f"{lab:8}{r['evo_ape_a_se3']['rmse_m']:10.3f}{r['ate_4dof']['rmse_m']:10.3f}"
              f"{d.get('final_m', float('nan')):11.3f}{(d.get('final_h_pct_of_path') or float('nan')):9.2f}{r['n']:7d}")
    print(f"[out] {a.out}")
    return out


if __name__ == "__main__":
    main()
