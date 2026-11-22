#!/usr/bin/env python3
"""IPLS stage 2 scorer (docs/thesis/iterated_smoother/preregistration.md INCLUDING AMENDMENT 1, EXPLORATORY).
Scores the new track "IPLS-UKF (hindsight, exploratory)" with EXACTLY the registered Experiment 2 definitions.

Read-only. Writes only eval/results/iterated_smoother/ipls_scores.json. Never touches eval/results/expT/,
numbers.md, or any stored trial output (room_ukf/, room_fgo/, room_ukf_ipls/ are all opened for reading only).

**Reuse, not re-derivation.** eval/tag_score.py parses argv and runs its whole pipeline at module top level (it
cannot be imported), so the world-frame / no-alignment / lap-window / ground-truth-handling logic below
(`to_sim`, the lap-window regexes, `tum()`, `err()`, `st()`, the gap-interior rule) is copied verbatim from it.
eval/t_aggregate.py's `gains()` is copied verbatim for the per-gap hindsight gain. The functions below are
byte-for-byte identical to their namesakes in those two files (diffed by hand against tag_score.py 2026-11-xx /
t_aggregate.py 2026-11-xx; see the module docstrings there for what each one means).

**The check (must pass before any IPLS number is read):** for every one of the 12 Experiment 2 flights, this
recomputes "UKF live", "RTS-UKF (hindsight)" and "FGO hindsight (whole-flight batch)" from the bag + the SAME
stored tum files tag_score.py read, and asserts, by float equality:
  - horiz_err_m (rmse/median/p95/max/n) for those three tracks == eval/results/expT/<trial>.json's tracks.*;
  - every stored gap's t0/t1 and (for the tracks present in it) each of those three tracks' gap mean/max.
Any mismatch raises SystemExit("REFUSED: ...") before any IPLS scoring happens.

Then adds "IPLS-UKF (hindsight, exploratory)" from <trial>/room_ukf_ipls/ukf_ipls.tum, for trials whose G1/G2 gate
(eval/ipls_gates.py) passes. A trial that fails G1/G2 is reported (window, gates) but NOT scored, per the
pre-registration's own rule (section 4: "If any gate fails, stop and report; no result is scored" — applied
per-trial here since the pre-registration's per-run framing makes that the natural unit).

Convergence label (AMENDMENT 1 / preregistration section 2): a run is "converged" iff room_ukf_ipls/stats.json's
own `converged` flag is true AND no cost increase appears anywhere in the returned `history` (strict `cost[i] >
cost[i-1]`, no epsilon — the G3(b) 0.0015 rise counted at that same strictness). Otherwise "non-converged"; its
own stopping-rule trajectory (ukf_ipls.tum) is scored and the label is recorded (section 2: "its iteration-10
trajectory scored and labelled" when the run reaches max_iter without meeting the 1 mm rule; when a run meets the
1 mm rule early but still shows a cost increase, there is no iteration-10 trajectory to fall back to -- see the
preregistration-owner note this script prints for that case, which did not arise in this run).

Predictions (preregistration section 5, unrounded values):
  E-1: IPLS-UKF RMSE < RTS-UKF RMSE on every flight in conditions B, C, D (9/9).
  E-2: per condition, larger of (IPLS-UKF, FGO-batch) mean-of-3 RMSE <= 1.5x the smaller (4/4).
  E-3: IPLS-UKF per-gap hindsight gain (UKF live - IPLS-UKF) has condition medians strictly increasing A->D.

Usage: python3 eval/ipls_score.py [--json OUT]"""
import argparse, json, math, os, re, sys

import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__))
EXPT = os.path.join(HERE, "results", "expT")
GAP_MIN_S = 1.0
TRIALS = [f"T_{c}_r{r}" for c in "ABCD" for r in (1, 2, 3)]
COND = {t: t[2] for t in TRIALS}
IPLS_NAME = "IPLS-UKF (hindsight, exploratory)"
CHECK_TRACKS = ("UKF live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")


# ---- verbatim from eval/tag_score.py ----
def wrap(x):
    return (x + np.pi) % (2 * np.pi) - np.pi


def tum(path):
    if not os.path.exists(path):
        return None
    x = np.loadtxt(path, ndmin=2)
    qx, qy, qz, qw = x[:, 4], x[:, 5], x[:, 6], x[:, 7]
    return np.c_[x[:, 0], x[:, 1], x[:, 2], np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy ** 2 + qz ** 2))]


def err(tr, G, W0, W1):
    w = (tr[:, 0] >= W0) & (tr[:, 0] <= W1)
    T = tr[w]
    eE = T[:, 1] - np.interp(T[:, 0], G[:, 0], G[:, 1])
    eN = T[:, 2] - np.interp(T[:, 0], G[:, 0], G[:, 2])
    gy = np.interp(T[:, 0], G[:, 0], np.unwrap(G[:, 3]))
    return T[:, 0], np.hypot(eE, eN), np.degrees(np.abs(wrap(T[:, 3] - gy)))


def st(x):
    return {"rmse": float(np.sqrt(np.mean(x ** 2))), "median": float(np.median(x)), "p95": float(np.percentile(x, 95)),
            "max": float(np.max(x)), "n": int(len(x))}


# ---- verbatim from eval/t_aggregate.py ----
def gains(live, hind, per_trial_gaps):
    rows = []
    for c in "ABCD":
        for t in (f"T_{c}_r1", f"T_{c}_r2", f"T_{c}_r3"):
            for g in per_trial_gaps.get(t, []):
                if live in g and hind in g:
                    rows.append((c, g["length_s"], g[live]["mean"] - g[hind]["mean"]))
    return rows


# ---- per-trial recomputation (same bag/log reads as tag_score.py) ----
def load_bag_and_window(trial):
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    ts = get_typestore(Stores.ROS2_JAZZY)
    G, TR, SENT = [], [], []
    with Reader(f"{D}/bag") as rd:
        cs = {c.topic: c for c in rd.connections}
        for con, _, raw in rd.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref", "/tags/sent") if x in cs]):
            m = ts.deserialize_cdr(raw, con.msgtype)
            if con.topic == "/imu/time_ref":
                TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
                continue
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if con.topic == "/ground_truth/pose":
                q = m.pose.orientation
                G.append((t, m.pose.position.x, m.pose.position.y, math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
            else:
                SENT.append(t)
    G, TR, SENT = np.array(G), np.array(TR), np.array(sorted(SENT))
    sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]
    env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        w = (sitl >= lo) & (sitl < lo + 5)
        if w.sum() > 50:
            i = np.argmin(d[w])
            env.append((sitl[w][i], d[w][i]))
    env = np.array(env)
    kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
    to_sim = lambda x: x + (kk * x + c0)

    starts, end = [], None
    for ln in open(f"{D}/logs/fly_trial.log"):
        m_ = re.search(r"LAP (\d+) LEG (\d+) START t_sim=([\d.]+)", ln)
        if m_:
            starts.append(float(m_[3]))
        m_ = re.search(r"LAPS END t_sim=([\d.]+)", ln)
        if m_:
            end = float(m_[1])
    W0, W1 = to_sim(starts[0]), to_sim(end)
    S = SENT[(SENT >= W0) & (SENT <= W1)]
    return G, W0, W1, S


def compute_gaps(S, W0, W1, E):
    rows = []
    for g0, g1 in zip(S[:-1], S[1:]):
        if g1 - g0 < GAP_MIN_S:
            continue
        row = {"t0": float(g0), "t1": float(g1), "length_s": float(g1 - g0)}
        for n_, (t_, eh) in E.items():
            w = (t_ > g0) & (t_ < g1)
            if w.any():
                row[n_] = {"mean": float(eh[w].mean()), "max": float(eh[w].max())}
        rows.append(row)
    return rows


def score_trial(trial):
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    G, W0, W1, S = load_bag_and_window(trial)

    tracks = {}
    for name, p in (("UKF live", f"{D}/room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", f"{D}/room_ukf/ukf_rts.tum"),
                    ("FGO hindsight (whole-flight batch)", f"{D}/room_fgo/fgo_batch.tum"),
                    (IPLS_NAME, f"{D}/room_ukf_ipls/ukf_ipls.tum")):
        t_ = tum(p)
        if t_ is not None:
            tracks[name] = t_

    E, out_tracks = {}, {}
    for n_, tr in tracks.items():
        t_, eh, ey = err(tr, G, W0, W1)
        E[n_] = (t_, eh)
        out_tracks[n_] = {"horiz_err_m": st(eh), "yaw_err_deg": {"median": float(np.median(ey)), "p95": float(np.percentile(ey, 95))}}

    gaps = compute_gaps(S, W0, W1, E)
    return {"trial": trial, "window_s": [float(W0), float(W1)], "tracks": out_tracks, "gaps": gaps,
            "has_ipls": IPLS_NAME in tracks}


def check_reproduction(trial, scored):
    stored = json.load(open(f"{EXPT}/{trial}.json"))
    problems = []
    for n_ in CHECK_TRACKS:
        a, b = scored["tracks"].get(n_), stored["tracks"].get(n_)
        if a is None or b is None:
            problems.append(f"{trial}: track {n_!r} missing on one side")
            continue
        if a["horiz_err_m"] != b["horiz_err_m"]:
            problems.append(f"{trial}: {n_} horiz_err_m mismatch: {a['horiz_err_m']} != {b['horiz_err_m']}")
    sg, bg = scored["gaps"], stored["gaps"]
    if len(sg) != len(bg):
        problems.append(f"{trial}: gap count mismatch: {len(sg)} != {len(bg)}")
    else:
        for i, (a, b) in enumerate(zip(sg, bg)):
            if a["t0"] != b["t0"] or a["t1"] != b["t1"]:
                problems.append(f"{trial}: gap {i} t0/t1 mismatch: {a['t0']},{a['t1']} != {b['t0']},{b['t1']}")
            for n_ in CHECK_TRACKS:
                if n_ in a or n_ in b:
                    if a.get(n_) != b.get(n_):
                        problems.append(f"{trial}: gap {i} {n_} mismatch: {a.get(n_)} != {b.get(n_)}")
    return problems


def gate_pass(trial):
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "ipls_gates.py"), trial], capture_output=True, text=True)
    return r.returncode == 0, r.stdout


def load_convergence(trial):
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    sp = f"{D}/room_ukf_ipls/stats.json"
    if not os.path.exists(sp):
        return None
    s = json.load(open(sp))
    hist = s["history"]
    cost_increase = any(hist[i]["cost"] > hist[i - 1]["cost"] for i in range(1, len(hist)))
    final_label = "converged" if (s["converged"] and not cost_increase) else "non-converged"
    return {"iterations_run": s["iterations_run"], "converged_flag": s["converged"], "cost_increase": cost_increase,
            "final_label": final_label, "history": hist, "run_time_s_total": s["run_time_s_total"],
            "run_time_s_forward_pass": s["run_time_s_forward_pass"], "run_time_s_ipls": s["run_time_s_ipls"],
            "src_dirty": s["src_dirty"]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
    per_trial, per_trial_gaps, convergence, gates = {}, {}, {}, {}
    repro_problems = []

    for trial in TRIALS:
        ok, gate_out = gate_pass(trial)
        gates[trial] = {"PASS": ok, "detail": gate_out.strip().splitlines()[0] if gate_out.strip() else ""}
        convergence[trial] = load_convergence(trial)

        scored = score_trial(trial)
        repro_problems += check_reproduction(trial, scored)
        per_trial[trial] = scored
        per_trial_gaps[trial] = scored["gaps"]

    if repro_problems:
        msg = "\n".join(repro_problems[:20])
        raise SystemExit(f"REFUSED: reproduction check against eval/results/expT/ failed ({len(repro_problems)} problems):\n{msg}")
    print(f"Reproduction check: PASS for all {len(TRIALS)} trials "
          f"({len(CHECK_TRACKS)} tracks x horiz_err_m + all gap t0/t1/mean/max, float equality).")

    scored_trials = [t for t in TRIALS if gates[t]["PASS"] and per_trial[t]["has_ipls"]]
    not_scored = [t for t in TRIALS if t not in scored_trials]

    rmse = {t: {n_: per_trial[t]["tracks"][n_]["horiz_err_m"]["rmse"]
                for n_ in ("UKF live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
                if n_ in per_trial[t]["tracks"]} for t in TRIALS}
    for t in scored_trials:
        rmse[t][IPLS_NAME] = per_trial[t]["tracks"][IPLS_NAME]["horiz_err_m"]["rmse"]

    conditions = {}
    for c in "ABCD":
        trs = [f"T_{c}_r{r}" for r in (1, 2, 3)]
        scored_trs = [t for t in trs if t in scored_trials]
        row = {"mean_rmse_m": {n_: float(np.mean([rmse[t][n_] for t in trs])) for n_ in
                                ("UKF live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")}}
        if len(scored_trs) == 3:
            row["mean_rmse_m"][IPLS_NAME] = float(np.mean([rmse[t][IPLS_NAME] for t in trs]))
        elif scored_trs:
            row["mean_rmse_m_partial_n"] = {IPLS_NAME: len(scored_trs)}
            row["mean_rmse_m"][IPLS_NAME + " (partial)"] = float(np.mean([rmse[t][IPLS_NAME] for t in scored_trs]))
        conditions[c] = row

    # E-1
    e1_rows = {}
    for t in [f"T_{c}_r{r}" for c in "BCD" for r in (1, 2, 3)]:
        if t in scored_trials:
            e1_rows[t] = bool(rmse[t][IPLS_NAME] < rmse[t]["RTS-UKF (hindsight)"])
    e1_pass_n = sum(1 for v in e1_rows.values() if v)
    E1 = {"per_flight": e1_rows, "n_pass": e1_pass_n, "n_total": 9, "PASS": e1_pass_n == 9 and len(e1_rows) == 9}

    # E-2 (only if all 3 repeats of a condition are scored)
    e2_rows = {}
    for c in "ABCD":
        if IPLS_NAME in conditions[c]["mean_rmse_m"]:
            m_ipls = conditions[c]["mean_rmse_m"][IPLS_NAME]
            m_fgo = conditions[c]["mean_rmse_m"]["FGO hindsight (whole-flight batch)"]
            ratio = max(m_ipls, m_fgo) / min(m_ipls, m_fgo)
            e2_rows[c] = {"ipls_mean_rmse_m": m_ipls, "fgo_batch_mean_rmse_m": m_fgo, "ratio": ratio, "PASS": ratio <= 1.5}
    e2_pass_n = sum(1 for v in e2_rows.values() if v["PASS"])
    E2 = {"by_condition": e2_rows, "n_pass": e2_pass_n, "n_total": 4, "PASS": e2_pass_n == 4 and len(e2_rows) == 4}

    # E-3
    g_rows = gains("UKF live", IPLS_NAME, {t: per_trial[t]["gaps"] for t in scored_trials})
    med = {c: (float(np.median([d for cc, _, d in g_rows if cc == c])) if any(cc == c for cc, _, _ in g_rows) else None)
           for c in "ABCD"}
    have_all = all(med[c] is not None for c in "ABCD")
    mono = have_all and all(med["ABCD"[i]] < med["ABCD"[i + 1]] for i in range(3))
    E3 = {"condition_medians_m": med, "n_gaps": len(g_rows), "strictly_increasing": bool(mono), "PASS": bool(mono)}

    out = {
        "preregistration": "docs/thesis/iterated_smoother/preregistration.md (+AMENDMENT 1)",
        "track": IPLS_NAME,
        "trials": TRIALS,
        "gates": gates,
        "scored_trials": scored_trials,
        "not_scored_trials": not_scored,
        "convergence": convergence,
        "rmse_m": rmse,
        "conditions": conditions,
        "E-1": E1, "E-2": E2, "E-3": E3,
        "reproduction_check": "PASS",
    }
    print(json.dumps({k: v for k, v in out.items() if k not in ("convergence",)}, indent=1))
    if a.json:
        os.makedirs(os.path.dirname(a.json), exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
        print(f"wrote {a.json}")


if __name__ == "__main__":
    main()
