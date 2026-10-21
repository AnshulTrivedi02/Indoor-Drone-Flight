#!/usr/bin/env python3
"""Stage 2c exact cross-check (numbers_tier1.md provenance rules): every value entered in numbers_tier1.md §Gates (V-E5)
and §E5, and in e5_results.md, rounded ONCE from its stored json value, with its source. Reads only; prints markdown rows.
Positions 4 dp in m (V-E5 differences in um, 3 dp, from the same m values); ratios 2 dp."""
import json, glob, os

R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"
rel = lambda p: os.path.relpath(p, f"{R}/docs/thesis/tier1/scores") if p.startswith(SC) else os.path.relpath(p, R)
J = lambda p: json.load(open(p))

print("## V-E5 gates (per gate: pass count, worst-case figures over 12 flights x {live, rts})")
for g, task in (("ve5a", "world"), ("ve5b", "knownmap"), ("ve5c", "augmented")):
    fs = sorted(glob.glob(f"{SC}/{g}_T_*.json")); P = [J(f) for f in fs]
    worst = lambda key: max((p[k][key], os.path.basename(f), k) for f, p in zip(fs, P) for k in ("live", "rts"))
    rmsw, maxw, rmsa = worst("rms_window_m"), worst("max_window_m"), worst("rms_all_m")
    dr = max((p[k]["rmse_vs_gt_m"]["abs_delta"], os.path.basename(f), k) for f, p in zip(fs, P) for k in ("live", "rts"))
    flips = sum(p["gates"].get("n_flips", 0) or 0 for p in P)
    print(f"| {g} ({task}) | PASS {sum(p['PASS'] for p in P)}/{len(P)}; rows match {sum(p['live']['rows_match'] and p['rts']['rows_match'] for p in P)}/12; "
          f"t_anchor and n_tag_fused equal {sum(p['anchor_tagcount']['pass'] for p in P)}/12; "
          f"byte-identical live {sum(p['live']['byte_identical'] for p in P)}/12, rts {sum(p['rts']['byte_identical'] for p in P)}/12; "
          f"worst RMS (window) {rmsw[0]*1e6:.3f} um [{rmsw[1]}:{rmsw[2]}.rms_window_m]; "
          f"worst max (window) {maxw[0]*1e6:.3f} um [{maxw[1]}:{maxw[2]}.max_window_m]; "
          f"worst RMS (all rows) {rmsa[0]*1e6:.3f} um [{rmsa[1]}:{rmsa[2]}.rms_all_m]; "
          f"worst |dRMSE| vs GT {dr[0]*1e6:.3f} um [{dr[1]}:{dr[2]}.rmse_vs_gt_m.abs_delta]; "
          f"gate decision flips {flips} (gates.n_flips) |")

print("\n## E5 per flight (json:scores/e5_<trial>.json, tracks.<track>)")
for t in ("T_A_r1", "T_A_r2", "T_A_r3"):
    f = f"{SC}/e5_{t}.json"; d = J(f)["tracks"]
    for tr in ("lc live", "lc hindsight", "nolc live", "nolc hindsight"):
        x = d[tr]; laps = " / ".join(f"{v:.4f}" for v in x["per_lap_rmse_m"])
        print(f"| {t} {tr} | RMSE {x['rmse_m']:.4f} | max {x['max_m']:.4f} | laps 1-5 {laps} | "
              f"lap5/lap1 {x['per_lap_rmse_m'][4]/x['per_lap_rmse_m'][0]:.2f} | json:{rel(f)}:tracks.{tr} |")

print("\n## Verdicts (json:scores/e5_verdicts.json)")
v = J(f"{SC}/e5_verdicts.json")
for c, r in v["criteria"].items():
    print(f"| {c} | {r['count']} | {r['verdict']} | per flight {r['per_flight']} | json:e5_verdicts.json:criteria.{c} |")
for t, fd in v["flights"].items():
    print(f"| {t} | lc live lap5/lap1 {fd['ratio lc live lap5/lap1']:.2f} | nolc live lap5/lap1 {fd['ratio nolc live lap5/lap1']:.2f} | "
          f"UKF/FGO lc live {fd['descriptive ratios UKF/FGO']['lc live']:.2f}, lc hindsight {fd['descriptive ratios UKF/FGO']['lc hindsight']:.2f}, "
          f"nolc live {fd['descriptive ratios UKF/FGO']['nolc live']:.2f}, nolc hindsight {fd['descriptive ratios UKF/FGO']['nolc hindsight']:.2f} | "
          f"lc/nolc live {fd['lc live / nolc live']:.2f}, hindsight {fd['lc hindsight / nolc hindsight']:.2f} | "
          f"FGO lc live {fd['values']['fgo lc live rmse_m']['value']:.4f}, lc hindsight {fd['values']['fgo lc hindsight rmse_m']['value']:.4f} |")
    for m in ("lc", "nolc"):
        i = fd["invariants"][m]["invariants"]
        print(f"|   {t} {m} invariants | t_anchor e5 {i['t_anchor']['e5']} fgo {i['t_anchor']['fgo']} | landmarks e5 {i['landmarks']['e5']} fgo {i['landmarks']['fgo']} | "
              f"tag meas used {i['tag_measurements_used_vs_landmark_factors (reported, not a stop)']} | pass {i['pass']} |")
