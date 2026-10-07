#!/usr/bin/env python3
"""Experiment T: pooled verdicts over the 12 flights (METHODOLOGY "Experiment T: pre-registration"). Reads
eval/results/expT/<trial>.json (eval/tag_score.py --json) for T_{A,B,C,D}_r{1,2,3}.
  H-T1 (primary): per-gap FGO hindsight gain d = mean live err - mean whole-flight-batch err; PASS iff the condition
        medians rise strictly A < B < C < D AND Spearman rho(gap length, d) > 0 with p < 0.01 over all gaps.
  P-T2: the same two criteria for the UKF (live -> RTS).
  P-T3: per condition, max/min of the live horizontal RMSE (EKF3, UKF, FGO; mean over repeats) <= 1.5.
  P-T4: per condition, max/min of (FGO batch, RTS-UKF) horizontal RMSE (mean over repeats) <= 1.5.
Usage: python3 eval/t_aggregate.py [--json OUT]"""
import argparse, json, os
import numpy as np
from scipy.stats import spearmanr

ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "expT")
C = "ABCD"; LIVE = ["EKF3 live", "UKF live", "FGO live"]; HB = "FGO hindsight (whole-flight batch)"; RU = "RTS-UKF (hindsight)"
S = {c: [json.load(open(f"{R}/T_{c}_r{r}.json")) for r in (1, 2, 3)] for c in C}
out = {"conditions": {}}


def gains(live, hind):
    rows = []
    for c in C:
        for s in S[c]:
            for g in s["gaps"]:
                if live in g and hind in g:
                    rows.append((c, g["length_s"], g[live]["mean"] - g[hind]["mean"]))
    return rows


def verdict(rows):
    med = {c: float(np.median([d for cc, _, d in rows if cc == c])) for c in C}
    mono = all(med[C[i]] < med[C[i + 1]] for i in range(3))
    rho, p = spearmanr([L for _, L, _ in rows], [d for _, _, d in rows])
    return {"median_gain_m": med, "strictly_increasing": mono, "spearman_rho": float(rho), "p": float(p), "n_gaps": len(rows),
            "PASS": bool(mono and rho > 0 and p < 0.01)}


out["H-T1 (FGO live -> whole-flight batch)"] = verdict(gains("FGO live", HB))
out["P-T2 (UKF live -> RTS)"] = verdict(gains("UKF live", RU))
p3, p4 = {}, {}
for c in C:
    m = {n: float(np.mean([s["tracks"][n]["horiz_err_m"]["rmse"] for s in S[c]])) for n in LIVE + [HB, RU]}
    out["conditions"][c] = {"mean_rmse_m": m, "gap_length_median_s": float(np.median([g["length_s"] for s in S[c] for g in s["gaps"]])),
                            "ekf3_horiz_pos_abs_in_gaps": float(np.mean([g["ekf3_horiz_pos_abs_frac"] for s in S[c] for g in s["gaps"]
                                                                         if g.get("ekf3_horiz_pos_abs_frac") is not None]))}
    l = [m[n] for n in LIVE]; p3[c] = max(l) / min(l); p4[c] = max(m[HB], m[RU]) / min(m[HB], m[RU])
out["P-T3 live ratio max/min"] = {"by_condition": p3, "PASS": all(v <= 1.5 for v in p3.values())}
out["P-T4 hindsight ratio max/min"] = {"by_condition": p4, "PASS": all(v <= 1.5 for v in p4.values())}
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
