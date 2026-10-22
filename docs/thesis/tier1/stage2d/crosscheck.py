#!/usr/bin/env python3
"""Stage 2d exact cross-check (numbers_tier1.md provenance rules): every value entered in numbers_tier1.md §E2 and in
e2_results.md, rounded ONCE from its stored json value, with its source. Reads only; prints markdown rows.
Positions 4 dp in m; ratios 2 dp; wall times 1 dp (s)."""
import json, os

R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"
J = lambda p: json.load(open(p))
IDS = {"B": "0-1-2-3", "C": "0-2", "D": "0"}
V = J(f"{SC}/E2_verdicts.json")

print("## E2 per flight (json:scores/E2_<trial>.json, tracks.<track>)")
for c in IDS:
    for r in (1, 2, 3):
        t = f"T_{c}_r{r}"; d = J(f"{SC}/E2_{t}.json")["tracks"]
        for tr in ("lc live", "lc hindsight", "nolc live", "nolc hindsight"):
            x = d[tr]; laps = " / ".join(f"{v:.4f}" for v in x["per_lap_rmse_m"])
            print(f"| {t} {tr} | RMSE {x['rmse_m']:.4f} | max {x['max_m']:.4f} | laps 1-5 {laps} | "
                  f"lap5/lap1 {x['per_lap_rmse_m'][4]/x['per_lap_rmse_m'][0]:.2f} | json:scores/E2_{t}.json:tracks.{tr} |")

print("\n## Per-flight ratios and checks (json:scores/E2_verdicts.json:flights.<t>)")
for t, f in V["flights"].items():
    km = V["known_map_descriptive"][t]
    print(f"| {t} | lc live lap5/lap1 {f['ratio lc live lap5/lap1']:.2f} | nolc live lap5/lap1 {f['ratio nolc live lap5/lap1']:.2f} | "
          f"lc/nolc live {f['lc live / nolc live']:.2f} hindsight {f['lc hindsight / nolc hindsight']:.2f} | "
          f"H-E2.1 {f['H-E2.1']} H-E2.2 {f['H-E2.2']} H-E2.3 {f['H-E2.3']} P-E2.4 {f['P-E2.4']} | "
          f"lap1 lc==nolc {f['lap1 lc live == lap1 nolc live']} | "
          f"expT FGO live {f['values']['expT FGO live rmse_m']['value']:.4f} batch {f['values']['expT FGO batch rmse_m']['value']:.4f} | "
          f"E2/known-map live {km['E2 LC live / expT FGO live']:.2f} hindsight {km['E2 LC hindsight / expT FGO batch']:.2f} |")
    s = f["stats"]
    for m in ("lc", "nolc"):
        x = s[m]
        print(f"|   {t} {m} stats | t_anchor {x['t_anchor']} | landmarks {x['landmarks']} | landmark_factors {x['landmark_factors']} | "
              f"raw {x['raw_detections']} central {x['central']} filtered {x['tier1']['n_filtered_out_by_tag_ids']} | "
              f"keyframes {x['keyframes']} kf_failures {x['keyframe_failures']} | wall_s {x['wall_s']:.1f} | step median {x['step_median_ms']:.2f} ms |")
    print(f"|   {t} invariants | {json.dumps(f['invariants'])} |")

print("\n## Verdicts")
for k, cs in V["criteria"].items():
    for c, x in cs.items():
        print(f"| {k} {c} | {x['count']} | {x['verdict']} | {x['per_flight']} | json:scores/E2_verdicts.json:criteria.{k}.{c} |")
p = V["P-E2.5"]
print(f"| P-E2.5 | means A {p['means']['A']['mean_m']:.4f} B {p['means']['B']['mean_m']:.4f} C {p['means']['C']['mean_m']:.4f} "
      f"D {p['means']['D']['mean_m']:.4f} | steps {p['steps']} | {p['verdict']} | json:scores/E2_verdicts.json:P-E2.5 |")
