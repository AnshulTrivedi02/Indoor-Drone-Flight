#!/usr/bin/env python3
"""Score arms (i)-(iv) of the EKF3 heading Replay stage 2 (preregistration section 6: exactly
the Phase 4 metrics -- evo -a (cruise), transition/blank failure metrics, yaw error).

Re-roots eval/three_way_eval.py's failure_metrics()/evo_ape_a()/crop() directly (never calls its
evaluate()/main(), which hardcode trials/ paths) and eval/phase4_eval.py's tum_yaw() for the
UKF/FGO yaw-error formula, applied unchanged to EKF3's Replayed XKF1 via the SAME sign conversion
established and verified against the SAME bag's stored UKF_baseline/FGO_baseline yaw-error sign
(see "validate" subcommand).

EKF3 corridor-ENU psi: XKF1.Yaw is ArduPilot's NED yaw (nose-right positive, 0=North); the
standard NED<->ENU relation for the SAME physical heading is yaw_ENU = 90 - yaw_NED, and
phase4_eval.py's own psi_true = GT_ENU_yaw - 90, so psi_est_ekf3 = (90 - XKF1.Yaw) - 90 =
-XKF1.Yaw. VERIFIED empirically (not just derived): arm (i)'s own end-of-cruise error on
fwdc_tex_r1 using this formula is -42.6 deg, matching UKF_baseline's -48.2 deg and FGO_baseline's
-44.2 deg on the SAME bag in both sign and rough magnitude (all three see the same SITL gyro
bias) -- the OPPOSITE sign (not negating XKF1.Yaw) gives +42.6 deg, which would disagree with
both.

Usage:
  eval/ekf3_heading_score.py validate        # reproduce ONE stored 0.148deg arm exactly; must pass before scoring
  eval/ekf3_heading_score.py score [--json OUT]
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import three_way_eval as T  # noqa: E402
import phase4_eval as P4  # noqa: E402

TD = os.path.expanduser("~/thesis_data/trials")
EKF_ARMS_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/arms")
UKF5_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/ukf")
FGO5_ROOT = os.path.expanduser("~/thesis_data/ekf3_heading_replay/fgo")
RESULTS = os.path.join(HERE, "results", "ekf3_heading_replay")
os.makedirs(RESULTS, exist_ok=True)

BAGS = [f"{p}_{w}_r{r}" for p in ("fwdc", "fwdplainc") for w in ("tex", "trans", "blank") for r in (1, 2, 3)]


def wrap180(a):
    return (a + 180) % 360 - 180


def yaw_error_from_series(t, yaw_rad, g, t0, t1):
    """EXACTLY phase4_eval.per_arm()'s formula, generalised to take a (t, yaw_rad) series
    directly instead of reading a TUM file -- so it can be reused for EKF3's XKF1.Yaw-derived
    series with no code duplication of the error/slope/wrap logic."""
    w = (t >= t0) & (t <= t1)
    err = np.degrees(yaw_rad[w] - (np.interp(t[w], g[:, 0], g[:, 3]) - math.pi / 2))
    err = wrap180(err) if np.abs(err).max() < 170 else err
    slope = np.polyfit((t[w] - t[w][0]) / 60.0, err, 1)[0]
    return {"yaw_err_mean_deg": float(err.mean()), "yaw_err_rms_deg": float(np.sqrt(np.mean(err ** 2))),
            "yaw_err_end_deg": float(err[-1]), "yaw_err_drift_dpm": float(slope)}


def ekf3_yaw_series(bin_path, core=100):
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(bin_path)
    out = []
    while True:
        x = m.recv_match(type=["XKF1"])
        if x is None:
            break
        if int(getattr(x, "C", -1)) == core:
            out.append((x.TimeUS / 1e6, -math.radians(x.Yaw)))   # psi_est_ekf3 = -yaw_NED, see module docstring
    a = np.array(out)
    return a[:, 0], np.unwrap(a[:, 1])


def latest_replayed_bin(outdir):
    import glob
    logs = sorted(glob.glob(os.path.join(outdir, "logs", "*.BIN")), key=os.path.getmtime)
    if not logs:
        raise SystemExit(f"no replayed .BIN in {outdir}")
    return logs[-1]


def ekf3_arm_metrics(bag, arm):
    """arm in ('baseline','heading') -- arm (i)/(ii)."""
    outdir = os.path.join(EKF_ARMS_ROOT, bag, arm)
    manifest = json.load(open(os.path.join(outdir, "manifest.json")))
    bin_path = latest_replayed_bin(outdir)
    t, yaw = ekf3_yaw_series(bin_path)
    t0, t1 = T.cruise_window(bag)
    g = np.load(f"{TD}/{bag}/fwd_meas/gt_eval_only.npz")["g"]
    yawerr = yaw_error_from_series(t, yaw, g, t0, t1)
    # failure metrics: EKF3's own ref/est TUMs, already written by ekf3_tums()+score_arm_i_or_ii's crop/write_tum
    ref = np.loadtxt(f"{TD}/{bag}/ekf3/ground_truth.tum")
    est_rows = []
    m2 = __import__("pymavlink.mavutil", fromlist=["mavutil"]).mavlink_connection(bin_path)
    while True:
        x = m2.recv_match(type=["XKF1"])
        if x is None:
            break
        if int(getattr(x, "C", -1)) == 100:
            est_rows.append((x.TimeUS / 1e6, x.PN, x.PE, x.PD))
    est = np.array(est_rows)
    est_full = np.c_[est[:, 0], est[:, 1:4], np.tile([0., 0., 0., 1.], (len(est), 1))]
    failure = T.failure_metrics(ref, est_full, t0, t1)
    return {"evo_a_cruise": manifest.get("result_evo_a_cruise"), "failure": failure, **yawerr,
            "n_records_injected": manifest.get("n_records_injected")}


def nis_psi_summary(d, est_label):
    """EXACTLY phase4_eval.per_arm()'s own NIS extraction (UKF: nis_psi[:,1] from
    timing_and_fwd.npz; FGO: fwd_log[fwd_log[:,1]==0, 2]), then phase4_eval.nis_summ()."""
    z = np.load(os.path.join(d, "timing_and_fwd.npz"))
    if est_label == "UKF":
        n = z["nis_psi"][:, 1] if len(z["nis_psi"]) else np.array([])
    else:
        fl = z["fwd_log"]
        n = fl[fl[:, 1] == 0, 2] if len(fl) else np.array([])
    return P4.nis_summ(n)


def estimator_arm_metrics(bag, est_label, outdir_sub_glob_root, traj_name, sigma_deg=5):
    """arm (iii)/(iv): UKF/FGO at sigma=sigma_deg, from <root>/<bag>/<sub>/."""
    import glob
    cands = glob.glob(os.path.join(outdir_sub_glob_root, bag, f"*_fwdsig{sigma_deg}"))
    if len(cands) != 1:
        raise SystemExit(f"{bag}: expected exactly one *_fwdsig{sigma_deg} dir under "
                          f"{outdir_sub_glob_root}/{bag}, found {cands}")
    d = cands[0]
    t, yaw = P4.tum_yaw(os.path.join(d, traj_name))
    t0, t1 = T.cruise_window(bag)
    g = np.load(f"{TD}/{bag}/fwd_meas/gt_eval_only.npz")["g"]
    yawerr = yaw_error_from_series(t, yaw, g, t0, t1)
    ref = np.loadtxt(os.path.join(d, "ground_truth.tum"))
    est = np.loadtxt(os.path.join(d, traj_name))
    failure = T.failure_metrics(ref, est, t0, t1)
    rp, ep = os.path.join(RESULTS, f"_tmp_{bag}_{est_label}_ref.tum"), os.path.join(RESULTS, f"_tmp_{bag}_{est_label}_est.tum")
    T.write_tum(rp, T.crop(ref, t0, t1))
    T.write_tum(ep, T.crop(est, t0, t1))
    evo = T.evo_ape_a(rp, ep)
    os.remove(rp)
    os.remove(ep)
    fs = json.load(open(os.path.join(d, "fwd_stats.json")))
    nis = nis_psi_summary(d, est_label)
    return {"evo_a_cruise": evo, "failure": failure, **yawerr, "sigma_psi_rad": fs["sigma"]["psi"],
            "psi_valid": fs["counts"]["psi_valid"], "psi_fused": fs["counts"]["psi_fused"], "nis_psi": nis}


def _validate_one(bag, est_label, sub, traj_name):
    t0, t1 = T.cruise_window(bag)
    g = np.load(f"{TD}/{bag}/fwd_meas/gt_eval_only.npz")["g"]
    d = f"{TD}/{bag}/{sub}"
    t, yaw = P4.tum_yaw(f"{d}/{traj_name}")
    mine = yaw_error_from_series(t, yaw, g, t0, t1)
    stored = json.load(open(os.path.join(HERE, "results", "phase4_fwdc_arms.json")))[bag][f"{est_label}_heading"]
    print(f"--- {est_label} yaw error -- mine vs stored ---")
    ok = True
    for k in ("yaw_err_mean_deg", "yaw_err_rms_deg", "yaw_err_end_deg", "yaw_err_drift_dpm"):
        same = abs(mine[k] - stored[k]) < 1e-9
        ok &= same
        print(f"  {k:20} mine={mine[k]!r:28} stored={stored[k]!r:28} {'OK' if same else 'MISMATCH'}")
    ref = np.loadtxt(f"{d}/ground_truth.tum")
    est = np.loadtxt(f"{d}/{traj_name}")
    failure = T.failure_metrics(ref, est, t0, t1)
    stored_evo = json.load(open(os.path.join(HERE, "results", "phase4_fwdc_evo.json")))["trials"][bag]["est"][f"{est_label}_heading"]
    print(f"--- {est_label} failure metrics -- mine vs stored ---")
    for k in ("disp_ratio", "onset_gt_dist", "final_disp", "true_travel"):
        same = (failure[k] is None and stored_evo["failure"][k] is None) or \
               (failure[k] is not None and stored_evo["failure"][k] is not None and abs(failure[k] - stored_evo["failure"][k]) < 1e-6)
        ok &= same
        print(f"  {k:16} mine={failure[k]!r:24} stored={stored_evo['failure'][k]!r:24} {'OK' if same else 'MISMATCH'}")
    rp, ep = os.path.join(RESULTS, f"_validate_{est_label}_ref.tum"), os.path.join(RESULTS, f"_validate_{est_label}_est.tum")
    T.write_tum(rp, T.crop(ref, t0, t1))
    T.write_tum(ep, T.crop(est, t0, t1))
    evo = T.evo_ape_a(rp, ep)
    os.remove(rp)
    os.remove(ep)
    same = abs(evo - stored_evo["ate_a_cruise"]["+0.00"]) < 1e-3
    ok &= same
    print(f"{est_label} evo -a (cruise): mine={evo} stored={stored_evo['ate_a_cruise']['+0.00']} {'OK' if same else 'MISMATCH'}")
    nis = nis_psi_summary(d, est_label)
    stored_nis = json.load(open(os.path.join(HERE, "results", f"phase4_fwdc_arms.json")))[bag][f"{est_label}_heading"]["nis_psi"]
    same = set(nis) == set(stored_nis) and all(
        (nis[k] == stored_nis[k]) if not isinstance(nis[k], float) else abs(nis[k] - stored_nis[k]) < 1e-9
        for k in nis)
    ok &= same
    print(f"{est_label} nis_psi: mine={nis} stored={stored_nis} {'OK' if same else 'MISMATCH'}")
    return ok


def cmd_validate(a):
    """Reproduce ONE stored 0.148deg arm PER ESTIMATOR (UKF_heading and FGO_heading, both on
    fwdc_tex_r1) via this script's OWN re-rooted logic, and compare against the stored
    phase4_fwdc_evo.json / phase4_fwdc_arms.json numbers exactly. Must PASS before trusting this
    script for the 5deg arms."""
    bag = "fwdc_tex_r1"
    ok = _validate_one(bag, "UKF", "ukf_heading", "ukf_traj.tum")
    ok &= _validate_one(bag, "FGO", "fgo_heading", "fgo_traj.tum")
    print("\nWRAPPER VALIDATION:", "PASS" if ok else "FAIL")
    if not ok:
        sys.exit(1)


def cmd_score(a):
    out = {}
    for bag in BAGS:
        print(f"=== {bag} ===", flush=True)
        row = {}
        row["EKF3_baseline_arm_i"] = ekf3_arm_metrics(bag, "baseline")
        row["EKF3_heading_arm_ii"] = ekf3_arm_metrics(bag, "heading")
        row["UKF_heading5_arm_iii"] = estimator_arm_metrics(bag, "UKF", UKF5_ROOT, "ukf_traj.tum")
        row["FGO_heading5_arm_iv"] = estimator_arm_metrics(bag, "FGO", FGO5_ROOT, "fgo_traj.tum")
        out[bag] = row
        print(json.dumps(row, indent=1), flush=True)
    path = a.json or os.path.join(RESULTS, "scored.json")
    json.dump(out, open(path, "w"), indent=1)
    print(f"[out] {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    v = sp.add_parser("validate"); v.set_defaults(func=cmd_validate)
    s = sp.add_parser("score"); s.add_argument("--json"); s.set_defaults(func=cmd_score)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
