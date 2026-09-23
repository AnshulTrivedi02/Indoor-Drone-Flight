#!/usr/bin/env python3
"""Three-way evo `-a` evaluation — EKF3 / UKF / FGO on one declared window.

The single evaluation entry point for the comparison (Phase 0 onward; Phase 5 extends
it). Every ATE it prints is **evo `-a`** (SE3-aligned, METHODOLOGY STANDING RULE),
labelled with the window it was computed on.

Sources, per trial (`~/thesis_data/trials/<trial>/`):
  EKF3  XKF1 (core 0, NED) vs SIM (lat/lng/alt -> local NED), both on the dataflash
        TimeUS clock. Written to disk as `ekf3/ekf3_traj.tum` + `ekf3/ground_truth.tum`
        (previously rebuilt ad hoc and never persisted).
  UKF   `ukf/ukf_traj.tum` vs `ukf/ground_truth.tum`  (ENU, bag sim-time clock)
  FGO   `fgo/fgo_traj.tum` vs `fgo/ground_truth.tum`  (ENU, bag sim-time clock)
Ground-truth TUMs carry identity quaternions, so evo's default translation-part APE
is what is measured. evo `-a` is frame-agnostic (Umeyama), so NED vs ENU is immaterial.

Windows:
  full    each estimator's whole trajectory file (what `rerun_batch.py` used)
  cruise  GT ground speed > 0.30 m/s after a 25-sample boxcar, largest contiguous run
          — the same rule as ukf_replay.py / fgo_replay.py apparatus metrics — computed
          from each estimator's own reference TUM on its own clock.
Note `-a` re-solves the alignment on whatever span it is given, so a cruise number is
not a sub-average of the full one.

Usage (venv-ardupilot: numpy + pymavlink; evo is called from ~/venv-evo):
  python3 eval/three_way_eval.py [--window full|cruise|both] [--json OUT] TRIAL...
  python3 eval/three_way_eval.py --window both dsn_tex_r1 dsn_tex_r2 dsn_tex_r3
"""
import argparse, json, math, os, re, subprocess, tempfile
import numpy as np
from pymavlink import mavutil

HOME = os.path.expanduser("~")
TRIALS_DIR = f"{HOME}/thesis_data/trials"
EVO_APE = f"{HOME}/venv-evo/bin/evo_ape"
T_MAX_DIFF = "0.05"
CRUISE_SPEED = 0.30     # m/s
CRUISE_BOXCAR = 25      # samples

# label -> (subdir, estimate TUM, reference TUM). EKF3's TUMs are built by ekf3_tums().
ESTIMATORS = {
    "EKF3": ("ekf3", "ekf3_traj.tum", "ground_truth.tum"),
    "UKF":  ("ukf", "ukf_traj.tum", "ground_truth.tum"),
    "FGO":  ("fgo", "fgo_traj.tum", "ground_truth.tum"),
}


def write_tum(path, a):
    np.savetxt(path, a, fmt="%.6f")


def cruise_bounds(t, x, y):
    """Largest contiguous run of boxcar-smoothed GT ground speed > CRUISE_SPEED."""
    sp = np.convolve(np.hypot(np.gradient(x), np.gradient(y)) / np.gradient(t),
                     np.ones(CRUISE_BOXCAR) / CRUISE_BOXCAR, mode="same")
    cr = sp > CRUISE_SPEED
    bi = bj = i = 0
    while i < len(cr):
        if cr[i]:
            j = i
            while j < len(cr) and cr[j]:
                j += 1
            if j - i > bj - bi:
                bi, bj = i, j
            i = j
        else:
            i += 1
    return t[bi], t[bj - 1]


def evo_ape_a(ref, est):
    out = subprocess.run([EVO_APE, "tum", ref, est, "--t_max_diff", T_MAX_DIFF,
                          "--no_warnings", "-a"], capture_output=True, text=True).stdout
    m = re.search(r"rmse\s+([\d.]+)", out)
    return float(m.group(1)) if m else float("nan")


def ekf3_tums(trial):
    """Build and persist EKF3's est/ref TUMs from ardupilot.bin (idempotent)."""
    d = f"{TRIALS_DIR}/{trial}/ekf3"
    os.makedirs(d, exist_ok=True)
    m = mavutil.mavlink_connection(f"{TRIALS_DIR}/{trial}/ardupilot.bin")
    xk, sim = [], []
    while True:
        x = m.recv_match(type=["XKF1", "SIM"])
        if x is None:
            break
        if x.get_type() == "XKF1":
            if getattr(x, "C", 0) != 0:
                continue
            xk.append((x.TimeUS / 1e6, x.PN, x.PE, x.PD))
        else:
            sim.append((x.TimeUS / 1e6, x.Lat, x.Lng, x.Alt))
    xk, sim = np.array(xk), np.array(sim)
    lat, lng = sim[:, 1].copy(), sim[:, 2].copy()
    if np.abs(lat).max() > 1000:            # degE7
        lat /= 1e7
        lng /= 1e7
    R = 6378137.0
    gN = np.radians(lat - lat[0]) * R
    gE = np.radians(lng - lng[0]) * R * math.cos(math.radians(lat.mean()))
    gD = -(sim[:, 3] - sim[0, 3])
    qI = lambda n: np.tile([0., 0., 0., 1.], (n, 1))
    write_tum(f"{d}/ground_truth.tum", np.c_[sim[:, 0], gN, gE, gD, qI(len(sim))])
    write_tum(f"{d}/ekf3_traj.tum", np.c_[xk[:, 0], xk[:, 1:4], qI(len(xk))])


def evaluate(trial, window, tmp):
    res = {}
    for name, (sub, est_f, ref_f) in ESTIMATORS.items():
        d = f"{TRIALS_DIR}/{trial}/{sub}"
        ref_p, est_p = f"{d}/{ref_f}", f"{d}/{est_f}"
        if not (os.path.exists(ref_p) and os.path.exists(est_p)):
            res[name] = {"ate_a": float("nan"), "missing": True}
            continue
        if window == "full":
            res[name] = {"ate_a": evo_ape_a(ref_p, est_p)}
            continue
        ref, est = np.loadtxt(ref_p), np.loadtxt(est_p)
        t0, t1 = cruise_bounds(ref[:, 0], ref[:, 1], ref[:, 2])
        rc, ec = f"{tmp}/{trial}_{name}_ref.tum", f"{tmp}/{trial}_{name}_est.tum"
        write_tum(rc, ref[(ref[:, 0] >= t0) & (ref[:, 0] <= t1)])
        write_tum(ec, est[(est[:, 0] >= t0) & (est[:, 0] <= t1)])
        res[name] = {"ate_a": evo_ape_a(rc, ec), "window_s": [float(t0), float(t1)]}
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("trials", nargs="+")
    ap.add_argument("--window", choices=["full", "cruise", "both"], default="both")
    ap.add_argument("--json", help="write results here")
    a = ap.parse_args()
    windows = ["full", "cruise"] if a.window == "both" else [a.window]
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for tr in a.trials:
            ekf3_tums(tr)
            out[tr] = {w: evaluate(tr, w, tmp) for w in windows}
            print(f"{tr:16}" + "  ".join(
                f"[{w}] " + " ".join(f"{n} {out[tr][w][n]['ate_a']:.2f}" for n in ESTIMATORS)
                for w in windows), flush=True)
    for w in windows:
        print(f"\n=== evo -a RMSE (m), window = {w} ===")
        print(f"{'trial':16}" + "".join(f"{n:>9}" for n in ESTIMATORS))
        for tr in a.trials:
            print(f"{tr:16}" + "".join(f"{out[tr][w][n]['ate_a']:9.2f}" for n in ESTIMATORS))
        print(f"{'mean':16}" + "".join(
            f"{np.nanmean([out[t][w][n]['ate_a'] for t in a.trials]):9.2f}" for n in ESTIMATORS))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print(f"\n[out] {a.json}")


if __name__ == "__main__":
    main()
