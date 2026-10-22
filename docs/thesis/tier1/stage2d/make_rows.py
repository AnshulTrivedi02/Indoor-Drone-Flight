#!/usr/bin/env python3
"""Stage 2d: generate numbers_tier1.md §E2 rows from the stored jsons (values rounded once; same rounding as crosscheck.py)."""
import json
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"
J = lambda p: json.load(open(p)); V = J(f"{SC}/E2_verdicts.json")
for c in "BCD":
    for r in (1, 2, 3):
        t = f"T_{c}_r{r}"; d = J(f"{SC}/E2_{t}.json")["tracks"]; s = f"json:scores/E2_{t}.json"
        for tr, lab in (("lc live", "LC live"), ("lc hindsight", "LC hindsight"), ("nolc live", "no-LC live"), ("nolc hindsight", "no-LC hindsight")):
            x = d[tr]
            print(f"| {t} {lab} overall RMSE | {x['rmse_m']:.4f} | m | CURRENT | `{s}:tracks.{tr}.rmse_m` |")
            print(f"| {t} {lab} lap 1 / lap 5 RMSE | {x['per_lap_rmse_m'][0]:.4f} / {x['per_lap_rmse_m'][4]:.4f} | m | CURRENT | `{s}:tracks.{tr}.per_lap_rmse_m[0]`, `[4]` |")
        f = V["flights"][t]; k = V["known_map_descriptive"][t]; vs = "json:scores/E2_verdicts.json"
        print(f"| {t} LC live lap-5 / lap-1 | {f['ratio lc live lap5/lap1']:.2f} | ratio | CURRENT | `{vs}:flights.{t}.ratio lc live lap5/lap1` |")
        print(f"| {t} no-LC live lap-5 / lap-1 | {f['ratio nolc live lap5/lap1']:.2f} | ratio | CURRENT | `{vs}:flights.{t}.ratio nolc live lap5/lap1` |")
        print(f"| {t} E2 LC ÷ Experiment 2 FGO, live / hindsight (inputs and solvers differ) | {k['E2 LC live / expT FGO live']:.2f} / {k['E2 LC hindsight / expT FGO batch']:.2f} | ratio | DESCRIPTIVE | `{vs}:known_map_descriptive.{t}` |")
p = V["P-E2.5"]
print(f"| P-E2.5 mean LC live lap-5 RMSE, A / B / C / D | {p['means']['A']['mean_m']:.4f} / {p['means']['B']['mean_m']:.4f} / {p['means']['C']['mean_m']:.4f} / {p['means']['D']['mean_m']:.4f} | m | CURRENT | `json:scores/E2_verdicts.json:P-E2.5.means.<c>.mean_m` (A from `eval/results/expL/T_A_r<i>_t245.json:tracks.lc live.per_lap_rmse_m[4]`) |")
print()
print("| criterion | B | C | D | source |\n|---|---|---|---|---|")
names = {"H-E2.1": "**H-E2.1 (PRIMARY)**: LC live lap-5 ≤ 1.5 × lap-1", "H-E2.2": "H-E2.2: LC live < no-LC live (overall)",
         "H-E2.3": "H-E2.3: LC hindsight < no-LC hindsight (overall)", "P-E2.4": "P-E2.4: no-LC live lap-5 > 1.5 × lap-1"}
for k, n in names.items():
    cs = V["criteria"][k]
    print(f"| {n} | **{cs['B']['verdict']}** {cs['B']['count']} | **{cs['C']['verdict']}** {cs['C']['count']} | **{cs['D']['verdict']}** {cs['D']['count']} | `json:scores/E2_verdicts.json:criteria.{k}` |")
st = p["steps"]
print(f"| P-E2.5 (graded, one check): mean LC live lap-5 non-decreasing A → B → C → D | **{p['verdict']}** (A ≤ B {st['A<=B']}, B ≤ C {st['B<=C']}, C ≤ D {st['C<=D']}) | | | `json:scores/E2_verdicts.json:P-E2.5` |")
