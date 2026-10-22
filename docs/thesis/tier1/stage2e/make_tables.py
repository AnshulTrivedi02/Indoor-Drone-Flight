#!/usr/bin/env python3
"""Stage 2e: numbers_tier1.md §E3 rows (-> rows.md) and e3_results.md tables (-> results_tables.md), generated from
scores/E3_verdicts.json and the per-run score jsons only. Values rounded once: positions 4 dp (m), ratios 2 dp,
rates in % to 2 dp, wall times 1 dp (s)."""
import json
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"; S = "/home/makerspace/thesis_data/tier1/stage2e"
J = lambda p: json.load(open(p)); V = J(f"{SC}/E3_verdicts.json")
FL = ["T_A_r1", "T_A_r2", "T_A_r3"]; RATES = ["0.01", "0.05"]; SEEDS = [0, 1, 2]
VS = "json:scores/E3_verdicts.json"
pct = lambda p: {"0.01": "1%", "0.05": "5%", "0": "0"}[p]
v = lambda n, k: V["runs"][n]["values"][k]["value"]
rows = []; P = rows.append


def run_rows(n, lab):
    s = f"json:scores/{n}.json"
    P(f"| {lab} LC live / hindsight overall RMSE | {v(n,'lc live rmse_m'):.4f} / {v(n,'lc hindsight rmse_m'):.4f} | m | CURRENT | `{s}:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |")
    P(f"| {lab} LC live lap 1 / lap 5 RMSE | {v(n,'lc live lap1_m'):.4f} / {v(n,'lc live lap5_m'):.4f} | m | CURRENT | `{s}:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |")
    P(f"| {lab} LC live lap-5 / lap-1 | {V['runs'][n]['ratio lc live lap5/lap1']:.2f} | ratio | CURRENT | `{VS}:runs.{n}.ratio lc live lap5/lap1` |")


P("### Arm (a): FGO as-is (PRIMARY)\n")
P("| quantity | value | unit | status | source |\n|---|---|---|---|---|")
for t in FL:
    for p in RATES:
        for sd in SEEDS:
            n = f"E3a_{t}_{p}_s{sd}"; lab = f"{t} {pct(p)} s{sd}"
            run_rows(n, lab)
            m = V["runs"][n]["covariates"]["mislabel"]
            P(f"| {lab} injected / eligible non-gauge / all central calls (whole bag) | {m['n_mislabelled']} / {m['n_eligible_non_gauge']} / {m['n_calls']} | count | CURRENT | `tier1:{t}/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis{p}_s{sd}/stats.json:tier1.mislabel` (copied to `{VS}:runs.{n}.covariates.mislabel`) |")
            P(f"| {lab} rate among eligible / effective overall rate | {100*m['rate_among_eligible']:.2f} / {100*m['effective_overall_rate']:.2f} | % | CURRENT | `{VS}:runs.{n}.covariates.mislabel.rate_among_eligible`, `.effective_overall_rate` |")
for p in RATES:
    e = V["effective_rates"][f"a {p}"]
    P(f"| pooled {pct(p)} (9 runs): rate among eligible / effective overall rate | {100*e['pooled_rate_among_eligible']:.2f} / {100*e['pooled_effective_overall_rate']:.2f} | % | CURRENT | `{VS}:effective_rates.a {p}.pooled_rate_among_eligible`, `.pooled_effective_overall_rate` |")
p6 = V["criteria_a"]["P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight"]["per_flight"]
for t in FL:
    P(f"| {t} P-E3.6 LC live: stored clean / seed-mean 1% / seed-mean 5% | {p6[t]['clean']:.4f} / {p6[t]['seed-mean 1%']:.4f} / {p6[t]['seed-mean 5%']:.4f} | m | CURRENT | `{VS}:criteria_a.P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight.per_flight.{t}` |")
P("")
P("| criterion | verdict | count | source |\n|---|---|---|---|")
for k, x in V["criteria_a"].items():
    P(f"| {k} | **{x['verdict']}** | {x['count']} | `{VS}:criteria_a.{k}` |")
P("\n### Arm (b): robust tag factors, Cauchy k = 2.385 (ESTIMATOR VARIANT)\n")
P("| quantity | value | unit | status | source |\n|---|---|---|---|---|")
for t in FL:
    n = f"E3b_{t}_0"; run_rows(n, f"{t} robust rate 0 (control)")
    P(f"| {t} robust rate 0: LC live ÷ stored clean LC live | {V['runs'][n]['lc live / stored clean lc live']:.2f} | ratio | CURRENT | `{VS}:runs.{n}.lc live / stored clean lc live` |")
    for p in RATES:
        for sd in SEEDS:
            n = f"E3b_{t}_{p}_s{sd}"; lab = f"{t} robust {pct(p)} s{sd}"
            run_rows(n, lab)
            P(f"| {lab} LC live ÷ arm (a) LC live | {V['runs'][n]['b live / a live']:.2f} | ratio | CURRENT | `{VS}:runs.{n}.b live / a live` |")
for p in RATES:
    rt = V["runtime_descriptive"][p]
    P(f"| runtime (b)/(a), {pct(p)}: median (min–max) of 9 | {rt['median']:.2f} ({rt['min']:.2f}–{rt['max']:.2f}) | ratio | DESCRIPTIVE | `{VS}:runtime_descriptive.{p}` |")
for t in FL:
    c = V["runtime_descriptive"]["0"][t]
    lab = "÷ G0-L (i), serial" if t == "T_A_r1" else "÷ stored clean wall, NOT LIKE FOR LIKE (6 parallel)"
    P(f"| {t} runtime rate-0 control {lab} | {c['ratio']:.2f} ({c['b wall_s']:.1f} / {c['ref wall_s']:.1f} s) | ratio | DESCRIPTIVE | `{VS}:runtime_descriptive.0.{t}` |")
P("")
P("| criterion | verdict | count | source |\n|---|---|---|---|")
for k, x in V["criteria_b"].items():
    P(f"| {k} | **{x['verdict']}** | {x['count']} | `{VS}:criteria_b.{k}` |")
open(f"{S}/rows.md", "w").write("\n".join(rows) + "\n")

# ---------------- e3_results.md tables ----------------
T = []; Q = T.append
Q("TABLE_A")
Q("| flight | rate | seed | LC live | LC hindsight | LC live max | LC live lap 1 → lap 5 | lap5/lap1 | live ÷ clean | live ÷ no-LC | hindsight ÷ no-LC | injected (whole bag) | in [t_a, t_a+245] | eligible rate (%) | effective overall rate (%) | first-sighting mislabelled | kf failures | wall (s) |")
Q("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in FL:
    for p in RATES:
        for sd in SEEDS:
            n = f"E3a_{t}_{p}_s{sd}"; d = V["runs"][n]; c = d["covariates"]; m = c["mislabel"]
            Q(f"| {t} | {pct(p)} | {sd} | {v(n,'lc live rmse_m'):.4f} | {v(n,'lc hindsight rmse_m'):.4f} | {v(n,'lc live max_m'):.4f} | "
              f"{v(n,'lc live lap1_m'):.4f} → {v(n,'lc live lap5_m'):.4f} | {d['ratio lc live lap5/lap1']:.2f} | {d['lc live / stored clean lc live']:.2f} | "
              f"{d['lc live / stored nolc live']:.2f} | {d['lc hindsight / stored nolc hindsight']:.2f} | {m['n_mislabelled']} | "
              f"{m['n_injected_in_[t_anchor,t_anchor+245] (DESCRIPTIVE)']} | {100*m['rate_among_eligible']:.2f} | {100*m['effective_overall_rate']:.2f} | "
              f"{c['landmarks_first_sighting_mislabelled']} | {c['keyframe_failures']} | {c['wall_s']:.1f} |")
Q("TABLE_REF")
Q("| flight | clean LC live | clean LC hindsight | no-LC live | no-LC hindsight | clean LC live lap 1 → lap 5 | t_anchor (s) |\n|---|---|---|---|---|---|---|")
for t in FL:
    r = V["references"][t]; g = lambda k: r[k]["value"]
    Q(f"| {t} | {g('clean lc live rmse_m'):.4f} | {g('clean lc hindsight rmse_m'):.4f} | {g('nolc live rmse_m'):.4f} | {g('nolc hindsight rmse_m'):.4f} | "
      f"{g('clean lc live lap1_m'):.4f} → {g('clean lc live lap5_m'):.4f} | {g('t_anchor_s')} |")
Q("TABLE_B")
Q("| flight | rate | seed | robust LC live | robust LC hindsight | lap 1 → lap 5 | lap5/lap1 | arm (a) LC live | (b) ÷ (a) live | (b) ÷ (a) hindsight | ÷ clean | kf failures | wall (s) | (b)/(a) wall | polish (s) b / a |")
Q("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in FL:
    n = f"E3b_{t}_0"; d = V["runs"][n]; c = d["covariates"]; rc = V["runtime_descriptive"]["0"][t]
    Q(f"| {t} | 0 (control) | — | {v(n,'lc live rmse_m'):.4f} | {v(n,'lc hindsight rmse_m'):.4f} | {v(n,'lc live lap1_m'):.4f} → {v(n,'lc live lap5_m'):.4f} | "
      f"{d['ratio lc live lap5/lap1']:.2f} | (clean {V['references'][t]['clean lc live rmse_m']['value']:.4f}) | — | — | {d['lc live / stored clean lc live']:.2f} | "
      f"{c['keyframe_failures']} | {c['wall_s']:.1f} | {rc['ratio']:.2f}{'' if t == 'T_A_r1' else ' (not like for like)'} | {c['hindsight_polish_s']:.1f} / — |")
    for p in RATES:
        for sd in SEEDS:
            n = f"E3b_{t}_{p}_s{sd}"; a = f"E3a_{t}_{p}_s{sd}"; d = V["runs"][n]; c = d["covariates"]
            rr = V["runtime_descriptive"][p]["per_run"][n]
            Q(f"| {t} | {pct(p)} | {sd} | {v(n,'lc live rmse_m'):.4f} | {v(n,'lc hindsight rmse_m'):.4f} | {v(n,'lc live lap1_m'):.4f} → {v(n,'lc live lap5_m'):.4f} | "
              f"{d['ratio lc live lap5/lap1']:.2f} | {v(a,'lc live rmse_m'):.4f} | {d['b live / a live']:.2f} | {d['b hindsight / a hindsight (DESCRIPTIVE)']:.2f} | "
              f"{d['lc live / stored clean lc live']:.2f} | {c['keyframe_failures']} | {c['wall_s']:.1f} | {rr['ratio']:.2f} | {rr['b hindsight_polish_s']:.1f} / {rr['a hindsight_polish_s']:.1f} |")
open(f"{S}/results_tables.md", "w").write("\n".join(T) + "\n")
print(f"rows.md {len(rows)} lines; results_tables.md {len(T)} lines")
