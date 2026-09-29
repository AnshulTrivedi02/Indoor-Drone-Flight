#!/usr/bin/env python3
"""PRE-REGISTERED confirmatory test and noise floor (METHODOLOGY "PRE-REGISTRATION — additional
dsn_tex repeats: the EKF3-vs-FGO ordering and the dsn noise floor"), written before the r4..r10
results were seen:
  d_i = evo(EKF3) - evo(FGO), evo -a (cruise), i = 4..10 (the 7 NEW flights only)
  "EKF3 lower" iff (a) d_i < 0 on >= 6 of 7 AND (b) the 95% t-interval (df 6) of mean d excludes 0
  "FGO lower" by the mirror rule; otherwise no ordering is claimed and mean d +- CI is reported
  Noise floor: SD per estimator (EKF3, FGO, UKF) and of d over ALL 10 re-flown flights, each with a
  chi-square 95% interval (df 9); UKF r4..r10 reported, with its instability rate (evo > 3x median).
Usage: python3 eval/dsn_paired_test.py OLD_EVO_JSON(r1-r3) NEW_EVO_JSON(r4-r10) [--json OUT]"""
import argparse, json, math
import numpy as np
from scipy import stats

ap = argparse.ArgumentParser(); ap.add_argument("old"); ap.add_argument("new"); ap.add_argument("--json"); a = ap.parse_args()


def load(p):
    d = json.load(open(p))["trials"]
    return {t: {k: v["ate_a_cruise"]["+0.00"] for k, v in d[t]["est"].items()} for t in d if t.startswith("dsn_tex_")}


old, new = load(a.old), load(a.new)
new_t = [f"dsn_tex_r{i}" for i in range(4, 11)]
all_t = [f"dsn_tex_r{i}" for i in range(1, 11)]
allv = {**old, **new}
est_key = lambda d, name: next(k for k in d if k.upper().startswith(name))
# A flight without a FGO value (IMU-gap rule: unusable for UKF/FGO) is counted as NOT supporting
# either ordering in (a), and is left out of (b) (METHODOLOGY, recorded before the results).
usable = [t for t in new_t if any(k.upper().startswith("FGO") for k in new[t])]
d = np.array([new[t][est_key(new[t], "EKF3")] - new[t][est_key(new[t], "FGO")] for t in usable])
n = len(d); mean, sd = d.mean(), d.std(ddof=1)
tq = stats.t.ppf(0.975, n - 1); ci = (mean - tq * sd / math.sqrt(n), mean + tq * sd / math.sqrt(n))
neg, pos = int((d < 0).sum()), int((d > 0).sum())
N7 = len(new_t)
sign_p = lambda k: float(sum(math.comb(N7, j) for j in range(k, N7 + 1)) / 2 ** N7)
if neg >= 6 and ci[1] < 0:
    verdict = "EKF3 lower (both (a) and (b) met)"
elif pos >= 6 and ci[0] > 0:
    verdict = "FGO lower (both (a) and (b) met)"
else:
    verdict = "no ordering claimed"
out = {"new_flights": new_t, "usable_for_FGO": usable, "d_m": d.round(4).tolist(), "n_neg": neg, "n_pos": pos,
       "sign_test_one_sided_p": {"EKF3_lower": sign_p(neg), "FGO_lower": sign_p(pos)},
       "mean_d_m": float(mean), "sd_d_m": float(sd), "t95_ci_m": [float(ci[0]), float(ci[1])], "verdict": verdict}


def sd_ci(x):
    x = np.asarray(x, float); df = len(x) - 1; s = x.std(ddof=1)
    return {"n": len(x), "mean": float(x.mean()), "sd": float(s),
            "sd_chi2_95": [float(s * math.sqrt(df / stats.chi2.ppf(0.975, df))), float(s * math.sqrt(df / stats.chi2.ppf(0.025, df)))]}


floor = {}
for name in ("EKF3", "FGO", "UKF"):
    vals = [allv[t][est_key(allv[t], name)] for t in all_t if any(k.upper().startswith(name) for k in allv[t])]
    floor[name] = sd_ci(vals); floor[name]["values"] = [round(v, 3) for v in vals]
has = lambda t, nm: any(k.upper().startswith(nm) for k in allv[t])
dall = [allv[t][est_key(allv[t], "EKF3")] - allv[t][est_key(allv[t], "FGO")] for t in all_t if has(t, "FGO")]
floor["d_EKF3_minus_FGO"] = sd_ci(dall)
ukf_t = [t for t in all_t if has(t, "UKF")]
ukf_all = np.array(floor["UKF"]["values"]); med = np.median(ukf_all)
floor["UKF"]["instability_rate"] = {"rule": "evo > 3x median", "median": float(med),
                                    "unstable": [t for t, v in zip(ukf_t, ukf_all) if v > 3 * med], "rate": float(np.mean(ukf_all > 3 * med))}
out["noise_floor_n10"] = floor
out["ukf_r4_r10"] = {t: (round(new[t][est_key(new[t], "UKF")], 3) if any(k.upper().startswith("UKF") for k in new[t]) else None) for t in new_t}
out["ekf3_r4_r10"] = {t: round(new[t][est_key(new[t], "EKF3")], 3) for t in new_t}
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
