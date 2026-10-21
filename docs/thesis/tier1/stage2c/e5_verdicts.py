#!/usr/bin/env python3
"""Stage 2c: mechanical E5 verdicts (preregistration.md §4; extension experiment, pre-registered (2026-10-21; signed off
with amendments 2026-10-22)). Reads only:
  docs/thesis/tier1/scores/e5_T_A_r{1,2,3}.json          (l_score.py --prefix lc_ukf --suffix _t245)
  eval/results/expL/T_A_r{1,2,3}_t245.json               (stored Experiment 3 FGO, CURRENT)
  ~/thesis_data/tier1/T_A_r{r}/lc_ukf_{lc,nolc}_t245/stats.json   (§5.3 invariants)
Writes docs/thesis/tier1/scores/e5_verdicts.json (must be new). Every comparison is on unrounded json values.
Lap 1 = per_lap_rmse_m[0], lap 5 = per_lap_rmse_m[4]."""
import json, os, sys

R = "/home/makerspace/thesis_ws"
SC = f"{R}/docs/thesis/tier1/scores"
OUT = f"{SC}/e5_verdicts.json"
FL = ["T_A_r1", "T_A_r2", "T_A_r3"]
if os.path.exists(OUT):
    sys.exit(f"REFUSED: {OUT} exists")

src = lambda f, k: f"json:{os.path.relpath(f, R) if f.startswith(R) else f}:{k}"
res = {"label": "extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22)",
       "flights": {}, "criteria": {}}
for t in FL:
    fu, ff = f"{SC}/e5_{t}.json", f"{R}/eval/results/expL/{t}_t245.json"
    u, g = json.load(open(fu))["tracks"], json.load(open(ff))["tracks"]
    assert len(u["lc live"]["per_lap_rmse_m"]) == 5 and len(u["nolc live"]["per_lap_rmse_m"]) == 5
    v = {}
    for tr in ("lc live", "lc hindsight", "nolc live", "nolc hindsight"):
        v[f"ukf {tr} rmse_m"] = (u[tr]["rmse_m"], src(fu, f"tracks.{tr}.rmse_m"))
        v[f"ukf {tr} max_m"] = (u[tr]["max_m"], src(fu, f"tracks.{tr}.max_m"))
        for i in range(5):
            v[f"ukf {tr} lap{i+1}_m"] = (u[tr]["per_lap_rmse_m"][i], src(fu, f"tracks.{tr}.per_lap_rmse_m[{i}]"))
        v[f"fgo {tr} rmse_m"] = (g[tr]["rmse_m"], src(ff, f"tracks.{tr}.rmse_m"))
    val = lambda k: v[k][0]
    d = {"values": {k: {"value": a, "source": b} for k, (a, b) in v.items()}}
    d["ratio lc live lap5/lap1"] = val("ukf lc live lap5_m") / val("ukf lc live lap1_m")
    d["ratio nolc live lap5/lap1"] = val("ukf nolc live lap5_m") / val("ukf nolc live lap1_m")
    d["H-E5.1"] = d["ratio lc live lap5/lap1"] <= 1.5
    d["H-E5.2"] = val("ukf lc live rmse_m") < val("ukf nolc live rmse_m")
    d["H-E5.3"] = val("ukf lc hindsight rmse_m") < val("ukf nolc hindsight rmse_m")
    d["P-E5.4"] = val("ukf nolc live lap5_m") > 1.5 * val("ukf nolc live lap1_m")
    d["S-E5.5"] = val("ukf lc live rmse_m") > val("fgo lc live rmse_m")
    d["S-E5.6"] = val("ukf lc hindsight rmse_m") > val("fgo lc hindsight rmse_m")
    d["descriptive ratios UKF/FGO"] = {tr: val(f"ukf {tr} rmse_m") / val(f"fgo {tr} rmse_m")
                                       for tr in ("lc live", "lc hindsight", "nolc live", "nolc hindsight")}
    d["lc live / nolc live"] = val("ukf lc live rmse_m") / val("ukf nolc live rmse_m")
    d["lc hindsight / nolc hindsight"] = val("ukf lc hindsight rmse_m") / val("ukf nolc hindsight rmse_m")
    inv = {}
    for m in ("lc", "nolc"):
        sf = os.path.expanduser(f"~/thesis_data/tier1/{t}/lc_ukf_{m}_t245/stats.json")
        s = json.load(open(sf))
        inv[m] = {"stats": sf, "invariants": s.get("invariants"), "keys": sorted(s.keys())}
    d["invariants"] = inv
    res["flights"][t] = d

for c in ("H-E5.1", "H-E5.2", "H-E5.3", "P-E5.4", "S-E5.5", "S-E5.6"):
    n = sum(res["flights"][t][c] for t in FL)
    res["criteria"][c] = {"per_flight": {t: res["flights"][t][c] for t in FL}, "count": f"{n}/3",
                          "verdict": "PASS" if n == 3 else "FAIL"}
res["note"] = ("All 3 runs per criterion completed and passed their gates, so each verdict is PASS (3/3) or FAIL. "
               "S-E5.5/S-E5.6 are secondary (registered direction); S-E5.6 compares the UKF RTS with the FGO's "
               "Experiment 3 hindsight = iSAM2 full estimate after 5 extra updates (DEVIATION, M:10557), not an LM batch.")
json.dump(res, open(OUT, "w"), indent=1)
for t in FL:
    f = res["flights"][t]
    print(t, {k: f[k] for k in ("ratio lc live lap5/lap1", "ratio nolc live lap5/lap1", "H-E5.1", "H-E5.2", "H-E5.3",
                                 "P-E5.4", "S-E5.5", "S-E5.6")})
print({c: (r["count"], r["verdict"]) for c, r in res["criteria"].items()})
