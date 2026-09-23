#!/usr/bin/env python3
"""Three-way evaluation — EKF3 / UKF / FGO on ONE pinned cruise window.

The single evaluation entry point for the comparison (Phase 0 onward; Phase 5 extends
it). Primary metric, per the 2026-09-23 ruling: **evo -a (cruise)** — every ATE this
prints is labelled that way (METHODOLOGY STANDING RULE).

CRUISE WINDOW (pinned; defined once per trial from ground truth, applied to all three):
  source     `<trial>/ukf/ground_truth.tum` — /ground_truth/pose from the bag (Gazebo
             truth, sim-time clock), ENU.
  speed      horizontal ground speed |d(x,y)/dt| (np.gradient), smoothed by a centred
             moving average of CRUISE_BOXCAR_S = 0.42 s (≈ the historical 25-sample
             boxcar at the ~59 Hz GT rate, but defined in time so it is rate-independent).
  criterion  smoothed speed > CRUISE_SPEED = 0.30 m/s; the window is the LARGEST
             contiguous run, [t0, t1] inclusive.
  applied    the same [t0, t1] (seconds) cropped out of every estimator's estimate AND
             reference TUM. EKF3's TUMs are on the dataflash TimeUS clock, taken to share
             the sim-time epoch; `--shifts` bounds the sensitivity to that assumption
             (METHODOLOGY, clock-sensitivity check).
  alignment  evo_ape -a (Umeyama SE3, no scale) fitted over the cropped cruise span only.

Sources, per trial (`~/thesis_data/trials/<trial>/`):
  EKF3  XKF1 (core 0, NED) vs SIM (lat/lng/alt -> local NED), both on TimeUS. Persisted
        as `ekf3/ekf3_traj.tum` + `ekf3/ground_truth.tum`.
  UKF   `ukf/ukf_traj.tum` vs `ukf/ground_truth.tum`  (ENU, sim-time)
  FGO   `fgo/fgo_traj.tum` vs `fgo/ground_truth.tum`  (ENU, sim-time)
  Extra estimator variants: `--est LABEL=subdir/traj.tum` (reference = subdir/ground_truth.tum).
Reference TUMs carry identity quaternions, so APE is the translation part.

FAILURE METRICS (transition/blank; METHODOLOGY "Three-way comparison" (2)), on the same
window, origin at t0: final displacement |d_est| / true travel |d_gt|, and divergence
onset = GT along-corridor distance at the first sample where | |d_est| - |d_gt| | > 15 m
and the median over the next 40 samples is also > 15 m (rule of plots/failure_analysis.py).

Usage (venv-ardupilot: numpy + pymavlink; evo is called from ~/venv-evo):
  python3 eval/three_way_eval.py [--shifts -0.5,-0.25,0,0.25,0.5] [--json OUT] TRIAL...
"""
import argparse, json, math, os, re, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from pymavlink import mavutil
from cruise_window import CRUISE_SPEED, CRUISE_BOXCAR_S, cruise_bounds

HOME = os.path.expanduser("~")
TRIALS_DIR = f"{HOME}/thesis_data/trials"
EVO_APE = f"{HOME}/venv-evo/bin/evo_ape"
T_MAX_DIFF = "0.05"
GT_SUB = "ukf"           # the bag-GT TUM that defines the window
DIVERGE_M = 15.0
DIVERGE_SUSTAIN = 40     # samples

ESTIMATORS = {           # label -> (subdir, estimate TUM); reference = subdir/ground_truth.tum
    "EKF3": ("ekf3", "ekf3_traj.tum"),
    "UKF":  ("ukf", "ukf_traj.tum"),
    "FGO":  ("fgo", "fgo_traj.tum"),
}


def write_tum(path, a):
    np.savetxt(path, a, fmt="%.6f")


def cruise_window(trial, speed=None):
    """Pinned cruise window [t0, t1] (s, sim-time) from the bag ground truth.

    `speed` overrides CRUISE_SPEED for the threshold-sensitivity check only."""
    g = np.loadtxt(f"{TRIALS_DIR}/{trial}/{GT_SUB}/ground_truth.tum")
    return cruise_bounds(g[:, 0], g[:, 1], g[:, 2], speed)


def ekf3_tums(trial):
    """Build and persist EKF3's est/ref TUMs from ardupilot.bin (idempotent)."""
    d = f"{TRIALS_DIR}/{trial}/ekf3"
    if os.path.exists(f"{d}/ekf3_traj.tum") and os.path.exists(f"{d}/ground_truth.tum"):
        return
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


def evo_ape_a(ref, est):
    out = subprocess.run([EVO_APE, "tum", ref, est, "--t_max_diff", T_MAX_DIFF,
                          "--no_warnings", "-a"], capture_output=True, text=True).stdout
    m = re.search(r"rmse\s+([\d.]+)", out)
    return float(m.group(1)) if m else float("nan")


def crop(a, t0, t1):
    return a[(a[:, 0] >= t0) & (a[:, 0] <= t1)]


def failure_metrics(ref, est, t0, t1):
    """Displacement ratio + divergence onset on [t0, t1], origin at t0 (horizontal)."""
    e = crop(est, t0, t1)
    t = e[:, 0]
    gx, gy = np.interp(t, ref[:, 0], ref[:, 1]), np.interp(t, ref[:, 0], ref[:, 2])
    d_est = np.hypot(e[:, 1] - e[0, 1], e[:, 2] - e[0, 2])
    d_gt = np.hypot(gx - gx[0], gy - gy[0])
    dev = np.abs(d_est - d_gt)
    onset = None
    for k in range(len(dev)):
        if dev[k] > DIVERGE_M and np.median(dev[k:k + DIVERGE_SUSTAIN]) > DIVERGE_M:
            onset = float(d_gt[k])
            break
    return {"final_disp": float(d_est[-1]), "true_travel": float(d_gt[-1]),
            "disp_ratio": float(d_est[-1] / d_gt[-1]), "onset_gt_dist": onset}


def evaluate(trial, shifts, tmp, estimators, pool, speed=None):
    ekf3_tums(trial)
    t0, t1 = cruise_window(trial, speed)
    res = {"window_s": [t0, t1], "est": {}}
    jobs = {}
    for name, (sub, est_f) in estimators.items():
        d = f"{TRIALS_DIR}/{trial}/{sub}"
        if not os.path.exists(f"{d}/{est_f}"):
            continue
        ref, est = np.loadtxt(f"{d}/ground_truth.tum"), np.loadtxt(f"{d}/{est_f}")
        res["est"][name] = {"failure": failure_metrics(ref, est, t0, t1), "ate_a_cruise": {}}
        for s in shifts:
            rc = f"{tmp}/{trial}_{name}_{s:+.2f}_ref.tum"
            ec = f"{tmp}/{trial}_{name}_{s:+.2f}_est.tum"
            write_tum(rc, crop(ref, t0 + s, t1 + s))
            write_tum(ec, crop(est, t0 + s, t1 + s))
            jobs[(name, s)] = pool.submit(evo_ape_a, rc, ec)
    for (name, s), f in jobs.items():
        res["est"][name]["ate_a_cruise"][f"{s:+.2f}"] = f.result()
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("trials", nargs="+")
    ap.add_argument("--shifts", default="0",
                    help="comma list of whole-window time shifts (s) for clock sensitivity")
    ap.add_argument("--est", action="append", default=[],
                    help="extra estimator LABEL=subdir/traj.tum")
    ap.add_argument("--only", help="comma list of estimator labels to evaluate")
    ap.add_argument("--cruise-speed", type=float, default=None,
                    help=f"threshold-sensitivity override (default {CRUISE_SPEED} m/s; not for results)")
    ap.add_argument("--json", help="write results here")
    a = ap.parse_args()
    shifts = [float(s) for s in a.shifts.split(",")]
    if 0.0 not in shifts:
        shifts.insert(0, 0.0)
    ests = dict(ESTIMATORS)
    for e in a.est:
        lab, path = e.split("=")
        sub, f = path.split("/")
        ests[lab] = (sub, f)
    if a.only:
        ests = {k: v for k, v in ests.items() if k in a.only.split(",")}
    out = {}
    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(8) as pool:
        for tr in a.trials:
            out[tr] = evaluate(tr, shifts, tmp, ests, pool, a.cruise_speed)
            r = out[tr]
            print(f"{tr:18} cruise [{r['window_s'][0]:.2f}, {r['window_s'][1]:.2f}] s  " +
                  "  ".join(f"{n} {v['ate_a_cruise']['+0.00']:.2f}" for n, v in r["est"].items()),
                  flush=True)
    names = [n for n in ests if any(n in out[t]["est"] for t in a.trials)]
    val = lambda t, n, k: out[t]["est"][n]["ate_a_cruise"][k] if n in out[t]["est"] else float("nan")
    print("\n=== evo -a (cruise) RMSE, m ===")
    print(f"{'trial':18}" + "".join(f"{n:>10}" for n in names))
    for tr in a.trials:
        print(f"{tr:18}" + "".join(f"{val(tr, n, '+0.00'):10.2f}" for n in names))
    if len(shifts) > 1:
        print("\n=== clock sensitivity: max |Δ evo -a (cruise)| over shifts, m ===")
        print(f"{'trial':18}" + "".join(f"{n:>10}" for n in names))
        for tr in a.trials:
            print(f"{tr:18}" + "".join(
                f"{max(abs(val(tr, n, f'{s:+.2f}') - val(tr, n, '+0.00')) for s in shifts):10.3f}"
                for n in names))
    print("\n=== failure metrics (cruise): disp_ratio / onset GT distance (m) ===")
    for tr in a.trials:
        print(f"{tr:18}" + "  ".join(
            f"{n} {out[tr]['est'][n]['failure']['disp_ratio']:.2f}/"
            f"{out[tr]['est'][n]['failure']['onset_gt_dist'] or float('nan'):.0f}"
            for n in names if n in out[tr]["est"]))
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump({"window_def": {"source": f"{GT_SUB}/ground_truth.tum",
                                  "speed_mps": a.cruise_speed or CRUISE_SPEED, "boxcar_s": CRUISE_BOXCAR_S,
                                  "rule": "largest contiguous run", "metric": "evo -a (cruise)"},
                   "trials": out}, open(a.json, "w"), indent=1)
        print(f"\n[out] {a.json}")


if __name__ == "__main__":
    main()
