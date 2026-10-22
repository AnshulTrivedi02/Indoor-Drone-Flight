#!/usr/bin/env python3
"""Stage 2e: numbers_tier1.md §E3 rows (-> rows.md) and e3_results.md tables (-> results_tables.md), generated from
scores/E3_verdicts.json only. Values rounded once: positions 4 dp (m), ratios 2 dp, rates in % to 2 dp, wall and
event times 1 dp / 3 dp (s).
Ruling R2 (2026-10-22): a diverged (FAILED-ESTIMATOR) run's RMSE values are not printed as numbers (they are inf/NaN or
cover only the pre-divergence segment); the cell reads "diverged". Its divergence onset (headline), first exception
time and failure fraction (inflated: no recovery after a throw) are printed instead."""
import json, math
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"; S = "/home/makerspace/thesis_data/tier1/stage2e"
J = lambda p: json.load(open(p)); V = J(f"{SC}/E3_verdicts.json")
FL = ["T_A_r1", "T_A_r2", "T_A_r3"]; RATES = ["0.01", "0.05"]; SEEDS = [0, 1, 2]
VS = "json:scores/E3_verdicts.json"
pct = lambda p: {"0.01": "1%", "0.05": "5%", "0": "0"}[p]
RS = lambda n: V["runs"][n]["run_status"]
DV = lambda n: RS(n)["diverged"]
ONS = "live divergence onset t_s (headline; |x| or |y| > 10 m or non-finite)"
FF = "failure_fraction (inflated: no recovery after a throw)"
NM = lambda n: V["runs"][n]["ratios not meaningful (a needed run diverged)"]


def v(n, k, f=".4f"):
    if DV(n):
        return "diverged"
    x = V["runs"][n]["values"][k]["value"]
    assert x is not None and math.isfinite(x), (n, k, x)
    return format(x, f)


def r2(n, k):
    if (NM(n) if k.startswith("b ") else DV(n)):   # (b)/(a) ratios need both runs finite; the others only this run
        return "—"
    return format(V["runs"][n][k], ".2f")


def tm(x, f=".3f"):
    return "—" if x is None else format(x, f)


rows = []; P = rows.append


def run_rows(n, lab):
    s = f"json:scores/{n}.json"
    if DV(n):
        st = RS(n)
        P(f"| {lab} run status | **FAILED-ESTIMATOR (diverged)**: live divergence onset {tm(st[ONS])} s; first exception {tm(st['first_exception_t_s'])} s; "
          f"failure fraction {st[FF]:.4f} ({st['keyframe_failures']} / {st['keyframe_failures'] + st['keyframes_ok']}; inflated: no recovery after a throw) | s / ratio | CURRENT | "
          f"`{VS}:runs.{n}.run_status` (from `tier1:stage2e/status/e{n[1:]}.json`) |")
        return
    P(f"| {lab} LC live / hindsight overall RMSE | {v(n,'lc live rmse_m')} / {v(n,'lc hindsight rmse_m')} | m | CURRENT | `{s}:tracks.lc live.rmse_m`, `tracks.lc hindsight.rmse_m` |")
    P(f"| {lab} LC live lap 1 / lap 5 RMSE | {v(n,'lc live lap1_m')} / {v(n,'lc live lap5_m')} | m | CURRENT | `{s}:tracks.lc live.per_lap_rmse_m[0]`, `[4]` |")
    P(f"| {lab} LC live lap-5 / lap-1 | {r2(n, 'ratio lc live lap5/lap1')} | ratio | CURRENT | `{VS}:runs.{n}.ratio lc live lap5/lap1` |")


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
K6 = "P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight"
p6 = V["criteria_a"][K6]["per_flight"]
for t in FL:
    if p6[t]["seed-mean 1%"] is None:
        P(f"| {t} P-E3.6 | not satisfied ({p6[t]['why']}); seed means not computed | — | CURRENT | `{VS}:criteria_a.{K6}.per_flight.{t}` |")
    else:
        P(f"| {t} P-E3.6 LC live: stored clean / seed-mean 1% / seed-mean 5% | {p6[t]['clean']:.4f} / {p6[t]['seed-mean 1%']:.4f} / {p6[t]['seed-mean 5%']:.4f} | m | CURRENT | `{VS}:criteria_a.{K6}.per_flight.{t}` |")
P("")


def crit_table(C, key):
    P("| criterion | verdict | count | divergence (k of 3 runs diverged, per flight) | source |\n|---|---|---|---|---|")
    for k, x in C.items():
        d = x["divergence"]
        lab = k
        if x.get("satisfied, flagged"):
            lab = k + " [satisfied, flagged ((a) diverged, (b) OK; no ratio): " + ", ".join(x["satisfied, flagged"]) + "]"
        dt = "; ".join(f"{t}: {d[t]['text']}" for t in FL) + f" (total {d['total']})"
        P(f"| {lab} | **{x['verdict']}** | {x['count']} | {dt} | `{VS}:{key}.{k}` |")


crit_table(V["criteria_a"], "criteria_a")
K1 = {p: next(k for k in V["criteria_b"] if k.startswith(f"P-E3b.1 {p}:")) for p in RATES}
P("\n### Arm (b): robust tag factors, Cauchy k = 2.385 (ESTIMATOR VARIANT)\n")
P("| quantity | value | unit | status | source |\n|---|---|---|---|---|")
for t in FL:
    n = f"E3b_{t}_0"; run_rows(n, f"{t} robust rate 0 (control)")
    if not DV(n):
        P(f"| {t} robust rate 0: LC live ÷ stored clean LC live | {r2(n, 'lc live / stored clean lc live')} | ratio | CURRENT | `{VS}:runs.{n}.lc live / stored clean lc live` |")
    for p in RATES:
        for sd in SEEDS:
            n = f"E3b_{t}_{p}_s{sd}"; lab = f"{t} robust {pct(p)} s{sd}"
            run_rows(n, lab)
            a_ = f"E3a_{t}_{p}_s{sd}"
            if not DV(n) and DV(a_):
                P(f"| {lab} P-E3b.1 | (a) diverged at {tm(RS(a_)[ONS])} s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not finite | — | CURRENT | `{VS}:criteria_b.{K1[p]}.satisfied, flagged.{n}` |")
            elif not DV(n):
                P(f"| {lab} LC live ÷ arm (a) LC live | {r2(n, 'b live / a live')} | ratio | CURRENT | `{VS}:runs.{n}.b live / a live` |")
c2 = V["runtime_descriptive"]["0"]["T_A_r2"]
P(f"| **runtime, serial 0% pair on T_A_r2 (headline): arm (b) ÷ arm (a) wall** | {c2['ratio']:.2f} ({c2['b wall_s']:.1f} / {c2['ref wall_s']:.1f} s) | ratio | DESCRIPTIVE (DIAGNOSTIC timing) | `{VS}:runtime_descriptive.0.T_A_r2` |")
for p in RATES:
    rt = V["runtime_descriptive"][p]
    if rt["median"] is None:
        P(f"| runtime (b)/(a), {pct(p)} | no pair without a diverged run | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE | `{VS}:runtime_descriptive.{p}` |")
    else:
        P(f"| runtime (b)/(a), {pct(p)}: median (min–max) of {rt['n_pairs_neither_diverged']} pairs without a diverged run | {rt['median']:.2f} ({rt['min']:.2f}–{rt['max']:.2f}) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE (parallel batch) | `{VS}:runtime_descriptive.{p}` |")
for t in ("T_A_r1", "T_A_r3"):
    c = V["runtime_descriptive"]["0"][t]
    lab = "÷ G0-L (i) (serial; arm (b) in the parallel batch)" if t == "T_A_r1" else "÷ stored clean wall (6 parallel; arm (b) in the parallel batch)"
    P(f"| {t} runtime rate-0 control {lab} | {c['ratio']:.2f} ({c['b wall_s']:.1f} / {c['ref wall_s']:.1f} s) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE | `{VS}:runtime_descriptive.0.{t}` |")
P("")
crit_table(V["criteria_b"], "criteria_b")
open(f"{S}/rows.md", "w").write("\n".join(rows) + "\n")

# ---------------- e3_results.md tables ----------------
T = []; Q = T.append


def stcell(n):
    if not DV(n):
        return "OK"
    st = RS(n)
    return f"**diverged**: onset {tm(st[ONS])} s, 1st exception {tm(st['first_exception_t_s'])} s, fail fraction {st[FF]:.2f}"


Q("TABLE_A")
Q("| flight | rate | seed | status | LC live | LC hindsight | LC live max | LC live lap 1 → lap 5 | lap5/lap1 | live ÷ clean | live ÷ no-LC | hindsight ÷ no-LC | injected (whole bag) | in [t_a, t_a+245] | eligible rate (%) | effective overall rate (%) | first-sighting mislabelled | kf failures | wall (s) |")
Q("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in FL:
    for p in RATES:
        for sd in SEEDS:
            n = f"E3a_{t}_{p}_s{sd}"; d = V["runs"][n]; c = d["covariates"]; m = c["mislabel"]
            Q(f"| {t} | {pct(p)} | {sd} | {stcell(n)} | {v(n,'lc live rmse_m')} | {v(n,'lc hindsight rmse_m')} | {v(n,'lc live max_m')} | "
              f"{v(n,'lc live lap1_m')} → {v(n,'lc live lap5_m')} | {r2(n,'ratio lc live lap5/lap1')} | {r2(n,'lc live / stored clean lc live')} | "
              f"{r2(n,'lc live / stored nolc live')} | {r2(n,'lc hindsight / stored nolc hindsight')} | {m['n_mislabelled']} | "
              f"{m['n_injected_in_[t_anchor,t_anchor+245] (DESCRIPTIVE)']} | {100*m['rate_among_eligible']:.2f} | {100*m['effective_overall_rate']:.2f} | "
              f"{c['landmarks_first_sighting_mislabelled']} | {c['keyframe_failures']} | {c['wall_s']:.1f} |")
Q("TABLE_REF")
Q("| flight | clean LC live | clean LC hindsight | no-LC live | no-LC hindsight | clean LC live lap 1 → lap 5 | t_anchor (s) |\n|---|---|---|---|---|---|---|")
for t in FL:
    r = V["references"][t]; g = lambda k: r[k]["value"]
    Q(f"| {t} | {g('clean lc live rmse_m'):.4f} | {g('clean lc hindsight rmse_m'):.4f} | {g('nolc live rmse_m'):.4f} | {g('nolc hindsight rmse_m'):.4f} | "
      f"{g('clean lc live lap1_m'):.4f} → {g('clean lc live lap5_m'):.4f} | {g('t_anchor_s')} |")
Q("TABLE_B")
Q("| flight | rate | seed | status | robust LC live | robust LC hindsight | lap 1 → lap 5 | lap5/lap1 | arm (a) LC live | (b) ÷ (a) live | (b) ÷ (a) hindsight | ÷ clean | kf failures | wall (s) | (b)/(a) wall | polish (s) b / a |")
Q("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in FL:
    n = f"E3b_{t}_0"; d = V["runs"][n]; c = d["covariates"]; rc = V["runtime_descriptive"]["0"][t]
    lab = " (serial pair, headline)" if t == "T_A_r2" else " (not like for like)"
    Q(f"| {t} | 0 (control) | — | {stcell(n)} | {v(n,'lc live rmse_m')} | {v(n,'lc hindsight rmse_m')} | {v(n,'lc live lap1_m')} → {v(n,'lc live lap5_m')} | "
      f"{r2(n,'ratio lc live lap5/lap1')} | (clean {V['references'][t]['clean lc live rmse_m']['value']:.4f}) | — | — | {r2(n,'lc live / stored clean lc live')} | "
      f"{c['keyframe_failures']} | {c['wall_s']:.1f} | {rc['ratio']:.2f}{lab} | {c['hindsight_polish_s']:.1f} / — |")
    for p in RATES:
        for sd in SEEDS:
            n = f"E3b_{t}_{p}_s{sd}"; a = f"E3a_{t}_{p}_s{sd}"; d = V["runs"][n]; c = d["covariates"]
            rr = V["runtime_descriptive"][p]["per_run"][n]
            wr = "—" if rr["diverged (a or b): wall not comparable"] else f"{rr['ratio']:.2f}"
            Q(f"| {t} | {pct(p)} | {sd} | {stcell(n)} | {v(n,'lc live rmse_m')} | {v(n,'lc hindsight rmse_m')} | {v(n,'lc live lap1_m')} → {v(n,'lc live lap5_m')} | "
              f"{r2(n,'ratio lc live lap5/lap1')} | {v(a,'lc live rmse_m')} | {r2(n,'b live / a live')} | {r2(n,'b hindsight / a hindsight (DESCRIPTIVE)')} | "
              f"{r2(n,'lc live / stored clean lc live')} | {c['keyframe_failures']} | {c['wall_s']:.1f} | {wr} | {rr['b hindsight_polish_s']:.1f} / {rr['a hindsight_polish_s']:.1f} |")
open(f"{S}/results_tables.md", "w").write("\n".join(T) + "\n")
print(f"rows.md {len(rows)} lines; results_tables.md {len(T)} lines")
