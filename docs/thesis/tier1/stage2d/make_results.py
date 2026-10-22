#!/usr/bin/env python3
"""Stage 2d: tables for e2_results.md, from the stored jsons only (rounded once)."""
import json
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"
J = lambda p: json.load(open(p)); V = J(f"{SC}/E2_verdicts.json")
print("| flight | LC live | LC hindsight | no-LC live | no-LC hindsight | LC live max | no-LC live max | LC live lap 1 → lap 5 | LC live lap5/lap1 | no-LC live lap 1 → lap 5 | no-LC live lap5/lap1 |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for c in "BCD":
    for r in (1, 2, 3):
        t = f"T_{c}_r{r}"; d = J(f"{SC}/E2_{t}.json")["tracks"]; f = V["flights"][t]
        L, N = d["lc live"], d["nolc live"]
        print(f"| {t} | {L['rmse_m']:.4f} | {d['lc hindsight']['rmse_m']:.4f} | {N['rmse_m']:.4f} | {d['nolc hindsight']['rmse_m']:.4f} | "
              f"{L['max_m']:.4f} | {N['max_m']:.4f} | {L['per_lap_rmse_m'][0]:.4f} → {L['per_lap_rmse_m'][4]:.4f} | {f['ratio lc live lap5/lap1']:.2f} | "
              f"{N['per_lap_rmse_m'][0]:.4f} → {N['per_lap_rmse_m'][4]:.4f} | {f['ratio nolc live lap5/lap1']:.2f} |")
print()
print("| flight | LC live / no-LC live | LC hindsight / no-LC hindsight |\n|---|---|---|")
for t, f in V["flights"].items():
    print(f"| {t} | {f['lc live / nolc live']:.2f} | {f['lc hindsight / nolc hindsight']:.2f} |")
print()
print("| flight | E2 LC live | Exp. 2 FGO live | ratio | E2 LC hindsight | Exp. 2 FGO batch | ratio |\n|---|---|---|---|---|---|---|")
for t, f in V["flights"].items():
    v = f["values"]; k = V["known_map_descriptive"][t]
    print(f"| {t} | {v['lc live rmse_m']['value']:.4f} | {v['expT FGO live rmse_m']['value']:.4f} | {k['E2 LC live / expT FGO live']:.2f} | "
          f"{v['lc hindsight rmse_m']['value']:.4f} | {v['expT FGO batch rmse_m']['value']:.4f} | {k['E2 LC hindsight / expT FGO batch']:.2f} |")
print()
print("| flight | t_anchor (s) | landmarks LC / no-LC | landmark factors | central / filtered out | keyframe failures LC, no-LC | wall LC / no-LC (s, stats.json) |\n|---|---|---|---|---|---|---|")
for t, f in V["flights"].items():
    a, b = f["stats"]["lc"], f["stats"]["nolc"]
    print(f"| {t} | {a['t_anchor']} | {a['landmarks']} / {b['landmarks']} | {a['landmark_factors']} | {a['central']} / {a['tier1']['n_filtered_out_by_tag_ids']} | "
          f"{a['keyframe_failures']}, {b['keyframe_failures']} | {a['wall_s']:.1f} / {b['wall_s']:.1f} |")
