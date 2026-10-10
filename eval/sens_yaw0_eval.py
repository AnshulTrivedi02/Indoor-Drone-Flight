#!/usr/bin/env python3
"""Labelled SENSITIVITY CHECK (user ruling 2026-10-10, METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma",
item 1): the UKF and the FGO with a 0.1 rad initial yaw sigma (EKF3's CovarianceInit value) instead of the shared 1 deg,
on the six fwdplainc tex/trans bags and two textured bags (dsn_tex_r1, fwdc_tex_r1). NOT a thesis result: it reports
whether any conclusion changes.

Inputs:
  main  = the corrected pass's own outputs in the trial directories (<trial>/{ukf,fgo}[_<arm>]/), initial yaw sigma 1 deg;
  sens  = <SENS_OUT>/<trial>/{ukf,fgo}[_<arm>]_iy0.1/ (INIT_YAW_SIGMA_RAD=0.1; written by the pipeline's sens_yaw0 stage).
Metrics (as eval/diag/plainwall_trace/a4.py): evo -a (cruise) with three_way_eval's own write_tum / crop / evo_ape_a and the
pinned window (dsn: <results>/rerun_dsn_evo.json; forward sets: <results>/phase4_<ds>_arms.json); for the forward sets also
the yaw error against fwd_meas/gt_eval_only.npz (phase4_eval's definition), the fused-heading count, and the gyro-z bias
mean from metrics.txt.

Usage (venv-ardupilot, as three_way_eval):  sens_yaw0_eval.py <SENS_OUT> --json <out.json> [--results eval/results]
"""
import argparse, json, math, os, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import three_way_eval as T

TD = os.path.expanduser("~/thesis_data/trials")
PLAIN = [f"fwdplainc_{w}_r{r}" for w in ("tex", "trans") for r in (1, 2, 3)]
RUNS = [(t, a) for t in PLAIN + ["fwdc_tex_r1"] for a in ("baseline", "heading")] + [("dsn_tex_r1", None)]
TAG = "_iy0.1"


def tumyaw(a):
    x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    return np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def window(trial, res):
    if trial.startswith("dsn_"):
        return json.load(open(f"{res}/rerun_dsn_evo.json"))["trials"][trial]["window_s"]
    ds = "fwdplainc" if trial.startswith("fwdplainc") else "fwdc"
    return json.load(open(f"{res}/phase4_{ds}_arms.json"))[trial]["window_s"]


def metrics(trial, d, est_f, win, tmp):
    if not os.path.exists(f"{d}/{est_f}"):
        return {"missing": d}
    t0, t1 = win
    ref, est = np.loadtxt(f"{d}/ground_truth.tum"), np.loadtxt(f"{d}/{est_f}")
    rc, ec = f"{tmp}/r.tum", f"{tmp}/e.tum"
    T.write_tum(rc, T.crop(ref, t0, t1)); T.write_tum(ec, T.crop(est, t0, t1))
    out = {"evo_a_cruise": T.evo_ape_a(rc, ec)}
    g_p = f"{TD}/{trial}/fwd_meas/gt_eval_only.npz"
    if os.path.exists(g_p):
        g = np.load(g_p)["g"]
        w = (est[:, 0] >= t0) & (est[:, 0] <= t1)
        err = np.degrees(tumyaw(est)[w] - (np.interp(est[w, 0], g[:, 0], g[:, 3]) - math.pi / 2))
        if np.abs(err).max() < 170:
            err = (err + 180) % 360 - 180
        out.update(yaw_rms_deg=float(np.sqrt(np.mean(err ** 2))), yaw_max_deg=float(np.abs(err).max()))
    if os.path.exists(f"{d}/metrics.txt"):
        m = {k.strip(): v.strip() for k, v in (l.split("=", 1) for l in open(f"{d}/metrics.txt") if "=" in l)}
        for k in ("bgz_mean", "true_bias_mean"):
            try:
                out[k + "_dpm"] = float(m[k])
            except (KeyError, ValueError):
                pass
    if os.path.exists(f"{d}/fwd_stats.json"):
        c = json.load(open(f"{d}/fwd_stats.json")).get("counts", {})
        out.update(psi_fused=c.get("psi_fused"), psi_valid=c.get("psi_valid"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sens_out"); ap.add_argument("--json", required=True); ap.add_argument("--results", default=f"{HERE}/results")
    a = ap.parse_args()
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for trial, arm in RUNS:
            win = window(trial, a.results)
            for est in ("UKF", "FGO"):
                sub = est.lower() + ("" if arm is None else f"_{arm}")
                main_m = metrics(trial, f"{TD}/{trial}/{sub}", f"{est.lower()}_traj.tum", win, tmp)
                sens_m = metrics(trial, f"{a.sens_out}/{trial}/{sub}{TAG}", f"{est.lower()}_traj.tum", win, tmp)
                rows.append({"trial": trial, "arm": arm or "plain", "est": est, "init_yaw_sigma_1deg": main_m,
                             "init_yaw_sigma_0p1rad": sens_m})
                f = lambda m, k, fmt: (fmt % m[k]) if isinstance(m.get(k), (int, float)) else "-"
                print(f"{trial:20} {arm or 'plain':9} {est}  evo {f(main_m, 'evo_a_cruise', '%8.2f')} -> "
                      f"{f(sens_m, 'evo_a_cruise', '%8.2f')} m   yaw max {f(main_m, 'yaw_max_deg', '%7.2f')} -> "
                      f"{f(sens_m, 'yaw_max_deg', '%7.2f')} deg   fused {main_m.get('psi_fused', '-')} -> {sens_m.get('psi_fused', '-')}")
    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    json.dump({"label": "SENSITIVITY CHECK (not a thesis result): initial yaw sigma 0.1 rad (EKF3) vs 1 deg (shared)",
               "ruling": "METHODOLOGY RULINGS (user, 2026-10-10): FGO initial yaw sigma, item 1", "rows": rows},
              open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
