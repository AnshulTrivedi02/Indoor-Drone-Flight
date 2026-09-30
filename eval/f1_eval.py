#!/usr/bin/env python3
"""F1 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — offline tests F1, F2, F3"): robust weighting on bad headings.
  calibrate: cruise yaw-error RMS of each robust FGO variant on the calibration bags (p1c_fwdc_tex,
             p1c_fwdplainc_tex); rule = minimise the mean of the two, tie within 0.01 deg -> smaller k, then Huber.
  test:      fwdplainc_tex_r1..r3 (region: the whole cruise) and fwdc_tex_r1..r3 (region: GT y > 140 m);
             arms UKF hard-gated (ukf_heading), FGO hard-gated (fgo_heading), FGO robust (fgo_heading_<TAG>).
Frames: estimator yaw in the corridor frame (yaw 0 along the corridor, CCW +); truth psi = GT ENU yaw - 90 deg
(gt_eval_only.npz, as phase4_eval); estimator East = -y (corridor frame), GT East = x (ENU).
Wrong heading: |psi_meas - psi_true| > 3 deg; correct: <= 1 deg. Accepted: hard gate = passed (NIS <= 9, from the
arm's own log); robust = weight >= 0.5 at the solution (Huber w = min(1, k/|r|); Cauchy w = 1/(1 + (r/k)^2); r =
wrapped (psi_meas - yaw_est) / sigma). Lockout episode: >= 3 s of consecutive correct headings all rejected.
Usage (venv-fgo): python3 eval/f1_eval.py calibrate | test TAG [--json OUT]"""
import argparse, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "src", "estimators"))
from cruise_window import cruise_bounds
from measurement_models import forward_events, FWD_SIGMA, fwd_dataset
from scipy.spatial.transform import Rotation as Rot
TD = os.path.expanduser("~/thesis_data/trials")
VARIANTS = ["huber:1.0", "huber:1.345", "huber:2.0", "huber:3.0", "cauchy:1.0", "cauchy:2.385", "cauchy:3.0"]
tag_of = lambda v: "F1" + v.replace(":", "_").replace(".", "_")
wrap = lambda a: (a + np.pi) % (2 * np.pi) - np.pi


def traj(tr, sub, est):
    d = np.loadtxt(f"{TD}/{tr}/{sub}/{est}_traj.tum")
    return d[:, 0], d[:, 1], d[:, 2], np.unwrap(Rot.from_quat(d[:, 4:8]).as_euler("xyz")[:, 2])


def truth(tr):
    g = np.load(f"{TD}/{tr}/fwd_meas/gt_eval_only.npz")["g"]        # t, x(E), y(N), unwrapped ENU yaw
    return g


def region(tr, g):
    c0, c1 = cruise_bounds(g[:, 0], g[:, 1], g[:, 2])
    if tr.startswith("fwdc_"):
        return lambda t: (t >= c0) & (t <= c1) & (np.interp(t, g[:, 0], g[:, 2]) > 140.0)
    return lambda t: (t >= c0) & (t <= c1)


def yaw_err(tr, sub, est, g, sel):
    t, x, y, yaw = traj(tr, sub, est)
    w = sel(t)
    e = np.degrees(wrap(yaw[w] - (np.interp(t[w], g[:, 0], g[:, 3]) - np.pi / 2)))
    xt = -y[w] - np.interp(t[w], g[:, 0], g[:, 1])
    return {"yaw_rms_deg": float(np.sqrt(np.mean(e ** 2))), "yaw_max_deg": float(np.abs(e).max()),
            "xtrack_max_m": float(np.abs(xt).max())}


def headings(tr):
    ev = forward_events(tr, "heading")
    return np.array([(t, d[0]) for t, _, d in ev if d[0] is not None])


def accept_hard(tr, sub, est, H):
    """The arm's own gate decisions: UKF nis_psi (t, nis, accepted); FGO fwd_log (t_keyframe, kind, nis, ok) with
    each heading attached to the first keyframe at or after its capture time (< one 33.3 ms keyframe period)."""
    z = np.load(f"{TD}/{tr}/{sub}/timing_and_fwd.npz")
    if est == "ukf":
        L = z["nis_psi"]; tt, ok = L[:, 0], L[:, 2] > 0.5; tol_lo, tol_hi = -0.002, 0.002
    else:
        L = z["fwd_log"]; L = L[L[:, 1] == 0]; tt, ok = L[:, 0], L[:, 3] > 0.5; tol_lo, tol_hi = -1e-6, 0.0334
    acc = np.zeros(len(H), bool); matched = 0
    j = np.searchsorted(tt, H[:, 0] + tol_lo)
    for i, k in enumerate(j):
        if k < len(tt) and tt[k] - H[i, 0] <= tol_hi:
            acc[i] = ok[k]; matched += 1
    accept_hard.matched = matched
    return acc


def accept_robust(tr, sub, H, variant):
    t, x, y, yaw = traj(tr, sub, "fgo")
    kind, k = variant.split(":"); k = float(k)
    sig = FWD_SIGMA[fwd_dataset(tr)]["psi"]
    r = wrap(H[:, 1] - np.interp(H[:, 0], t, yaw)) / sig
    w = np.minimum(1.0, k / np.maximum(np.abs(r), 1e-12)) if kind == "huber" else 1.0 / (1.0 + (r / k) ** 2)
    return w >= 0.5


def counts(H, acc, g, sel):
    m = sel(H[:, 0]); psi_true = np.interp(H[:, 0], g[:, 0], g[:, 3]) - np.pi / 2
    err = np.degrees(np.abs(wrap(H[:, 1] - psi_true)))
    wrong, correct = m & (err > 3.0), m & (err <= 1.0)
    rej_c = correct & ~acc
    # lockout: >= 3 s of consecutive CORRECT headings (in time order within the region) all rejected
    ci = np.where(correct)[0]; lock = 0; start = None
    for a_, i in enumerate(ci):
        if rej_c[i]:
            if start is None:
                start = H[i, 0]
            if H[i, 0] - start >= 3.0 and (a_ + 1 == len(ci) or not rej_c[ci[a_ + 1]]):
                lock += 1
        else:
            start = None
    return {"n_in_region": int(m.sum()), "wrong": int(wrong.sum()), "wrong_accepted": int((wrong & acc).sum()),
            "correct": int(correct.sum()), "correct_rejected": int(rej_c.sum()), "lockout_episodes": int(lock)}


ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["calibrate", "test"]); ap.add_argument("tag", nargs="?")
ap.add_argument("--json"); a = ap.parse_args(); out = {}
if a.mode == "calibrate":
    for v in VARIANTS:
        rms = []
        for tr in ("p1c_fwdc_tex", "p1c_fwdplainc_tex"):
            g = truth(tr); c0, c1 = cruise_bounds(g[:, 0], g[:, 1], g[:, 2])
            rms.append(yaw_err(tr, f"fgo_heading_{tag_of(v)}", "fgo", g, lambda t: (t >= c0) & (t <= c1))["yaw_rms_deg"])
        out[v] = {"yaw_rms_deg": rms, "mean": float(np.mean(rms))}
        print(v, [round(x, 3) for x in rms], round(float(np.mean(rms)), 3))
    best = min(out.values(), key=lambda d: d["mean"])["mean"]
    tied = [v for v in VARIANTS if out[v]["mean"] <= best + 0.01]
    tied.sort(key=lambda v: (float(v.split(":")[1]), 0 if v.startswith("huber") else 1))
    out["chosen"] = tied[0]; print("CHOSEN", tied[0], "(tied within 0.01 deg:", tied, ")")
else:
    v = a.tag
    for tr in ("fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3", "fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3"):
        g = truth(tr); sel = region(tr, g); H = headings(tr); r = {}
        for name, sub, est in (("UKF_hard", "ukf_heading", "ukf"), ("FGO_hard", "fgo_heading", "fgo"), ("FGO_robust", f"fgo_heading_{tag_of(v)}", "fgo")):
            acc = accept_robust(tr, sub, H, v) if name == "FGO_robust" else accept_hard(tr, sub, est, H)
            r[name] = {**yaw_err(tr, sub, est, g, sel), **counts(H, acc, g, sel)}
        out[tr] = r
        print(tr, json.dumps({k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in d.items()} for k, d in r.items()}))
    arms = ("UKF_hard", "FGO_robust")
    lock = {k: sum(out[t][k]["lockout_episodes"] for t in out) for k in arms}
    better_max = sum(out[t]["FGO_robust"]["yaw_max_deg"] < out[t]["UKF_hard"]["yaw_max_deg"] for t in out)
    out["decision"] = {"lockout_total": lock, "robust_lower_yaw_max_on": better_max,
                       "robust_FGO_better": bool(lock["FGO_robust"] < lock["UKF_hard"] and better_max >= 4)}
    print("DECISION", json.dumps(out["decision"]))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
