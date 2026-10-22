#!/usr/bin/env python3
"""Stage 2e: exact cross-check of the hand-written numbers in docs/thesis/tier1/e3_results.md (and the final handover).
Each value is recomputed from its source (scores/*.json, E3_verdicts.json, run stats.json, status jsons), rounded ONCE
(positions 4 dp m, ratios 2 dp, times as printed: event/onset 3 dp s, wall 1 dp s, step 1 dp ms), and the exact
string must appear in the document. Exit 1 on any missing string. Prints label | string | source."""
import json, sys
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"; T1 = "/home/makerspace/thesis_data/tier1"
S = f"{T1}/stage2e"; B = "_t245_tags0-1-2-3-4-5-6-7"; ROB = "_robcauchy2.385"
J = lambda p: json.load(open(p)); V = J(f"{SC}/E3_verdicts.json")
DOC = open(f"{R}/docs/thesis/tier1/e3_results.md").read()
HO = open(f"{R}/docs/handovers/2026-10-23_tier1_stage2e_final.md").read()
FL = ["T_A_r1", "T_A_r2", "T_A_r3"]; RT = ["0.01", "0.05"]; SD = [0, 1, 2]
f4 = lambda x: f"{x:.4f}"; f2 = lambda x: f"{x:.2f}"; f1 = lambda x: f"{x:.1f}"; f3 = lambda x: f"{x:.3f}"
rng = lambda xs, f: f"{f(min(xs))}–{f(max(xs))}"
checks = []   # (label, string, source, docs)
def C(label, s, src, docs=("doc",)): checks.append((label, s, src, docs))
run = lambda n: V["runs"][n]; val = lambda n, k: run(n)["values"][k]["value"]
st = lambda t, p, s, arm="a": J(f"{T1}/{t}/lc_fgo_lc{B}_mis{p}_s{s}{ROB if arm == 'b' else ''}/stats.json")
# §1 divergence table
ONS = "live divergence onset t_s (headline; |x| or |y| > 10 m or non-finite)"
FF = "failure_fraction (inflated: no recovery after a throw)"
for t in FL:
    for s in (1, 2):
        n = f"E3a_{t}_0.01_s{s}"; rs = run(n)["run_status"]
        C(f"{n} onset/exception", f"| {f3(rs[ONS])} | {f3(rs['first_exception_t_s'])} |", f"E3_verdicts.json:runs.{n}.run_status", ("doc", "ho"))
        C(f"{n} fraction", f"| {f3(rs['first_exception_t_s'])} | {rs[FF]:.4f} |", "same")
        ev = st(t, "0.01", s)["tier1"]["mislabel"]["events_t_true_new"]
        for e in [e for e in ev if 40 < e[0] < rs[ONS]][-2:]:
            C(f"{n} event", f"{f3(e[0])} ({e[1]}→{e[2]}", f"{t} stats.json:tier1.mislabel.events_t_true_new")
# §3 arm (a) non-diverged ranges
nd = [f"E3a_{t}_{p}_s{s}" for t in FL for p in RT for s in SD if not run(f"E3a_{t}_{p}_s{s}")["run_status"]["diverged"]]
C("n non-diverged arm a", f"All {len(nd)} non-diverged runs", "E3_verdicts.json:runs.*.run_status.diverged")
C("arm a live range", rng([val(n, "lc live rmse_m") for n in nd], f4) + " m", "scores E3a lc live rmse_m", ("doc", "ho"))
C("arm a hind range", rng([val(n, "lc hindsight rmse_m") for n in nd], f4) + " m", "scores E3a lc hindsight rmse_m")
C("live/clean", rng([run(n)["lc live / stored clean lc live"] for n in nd], f2) + "×", "E3_verdicts.json:runs.*.lc live / stored clean lc live", ("doc", "ho"))
C("live/nolc", rng([run(n)["lc live / stored nolc live"] for n in nd], f2) + "×", "E3_verdicts.json:runs.*.lc live / stored nolc live")
lm = st("T_A_r1", "0.01", 0)["landmarks_final"]; xs = [lm[str(i)][0] for i in range(1, 8)]; ys = [lm[str(i)][1] for i in range(1, 8)]
C("r1 1% s0 map", f"x {rng(xs, f4)} m, y {rng(ys, f4)} m", "T_A_r1 1% s0 stats.json:landmarks_final[1..7]")
lm = st("T_A_r3", "0.05", 0)["landmarks_final"]; xs = [lm[str(i)][0] for i in range(1, 8)]; ys = [lm[str(i)][1] for i in range(1, 8)]
C("r3 5% s0 map", f"x {rng(xs, f4)} m, y {rng(ys, f4)} m", "T_A_r3 5% s0 stats.json:landmarks_final[1..7]")
# §4 arm (b)
b1 = [f"E3b_{t}_0.01_s{s}" for t in FL for s in SD]; b5 = [f"E3b_{t}_0.05_s{s}" for t in FL for s in SD if not (t == "T_A_r2" and s == 1)]
C("b hind 1%", rng([val(n, "lc hindsight rmse_m") for n in b1], f4) + " m at 1%", "scores E3b lc hindsight rmse_m")
C("b hind 5% ex r2 s1", rng([val(n, "lc hindsight rmse_m") for n in b5], f4) + " m at 5%", "same")
C("b lap1 max", f"lap 1 up to {f4(max(val(n, 'lc live lap1_m') for n in b1 + b5))} m", "scores E3b per_lap_rmse_m[0]")
C("b lap5 range", "lap 5 (" + rng([val(n, "lc live lap5_m") for n in b1 + b5], f4) + " m)", "scores E3b per_lap_rmse_m[4]")
n = "E3b_T_A_r2_0.05_s1"
C("b r2 5% s1", f"robust LC live {f4(val(n, 'lc live rmse_m'))} m and hindsight {f4(val(n, 'lc hindsight rmse_m'))} m", f"scores/{n}.json", ("doc", "ho"))
C("b r2 5% s1 ratio", f"ratio {f2(run(n)['b live / a live'])} ≤ 1.10", f"E3_verdicts.json:runs.{n}.b live / a live")
C("P-E3b.2 range", rng([run(f"E3b_{t}_0")["lc live / stored clean lc live"] for t in FL], f2) + " × the stored clean LC live", "E3_verdicts.json:runs.E3b_*_0")
# effective rates
for p in RT:
    e = V["effective_rates"][f"a {p}"]; pr = e["per_run"]
    C(f"rates {p}", f"| {e['sum_n_mislabelled']} | {sum(v['n_eligible_non_gauge'] for v in pr.values()):,} | {sum(v['n_calls'] for v in pr.values()):,} | "
      f"{100*e['pooled_rate_among_eligible']:.2f} | {100*e['pooled_effective_overall_rate']:.2f} |", f"E3_verdicts.json:effective_rates.a {p}")
    C(f"rates {p} ho", f"{100*e['pooled_rate_among_eligible']:.2f}% among eligible, {100*e['pooled_effective_overall_rate']:.2f}% overall", "same", ("ho",))
C("H-E3.1 effective 1%", f"effective overall rate {100*V['effective_rates']['a 0.01']['pooled_effective_overall_rate']:.2f}%", "same")
# §5 runtime
c = V["runtime_descriptive"]["0"]
C("pair", f"**{f2(c['T_A_r2']['ratio'])}** ({f1(c['T_A_r2']['b wall_s'])} / {f1(c['T_A_r2']['ref wall_s'])} s)", "E3_verdicts.json:runtime_descriptive.0.T_A_r2")
C("pair ho", f"`wall_s` {f1(c['T_A_r2']['ref wall_s'])} s", "same", ("ho",))
C("pair step", f"{f1(c['T_A_r2']['a step_median_ms'])} / {f1(c['T_A_r2']['b step_median_ms'])} ms", "same")
for p in RT:
    r = V["runtime_descriptive"][p]
    C(f"rt {p}", f"{f2(r['median'])} ({f2(r['min'])}–{f2(r['max'])})", f"E3_verdicts.json:runtime_descriptive.{p}")
for t in ("T_A_r1", "T_A_r3"):
    C(f"ctl {t}", f"{f2(c[t]['ratio'])} ({f1(c[t]['b wall_s'])} / {f1(c[t]['ref wall_s'])} s)", f"E3_verdicts.json:runtime_descriptive.0.{t}")
a1p, a1s = st("T_A_r2", "0.01", 0)["wall_s"], st("T_A_r1", "0.01", 0)["wall_s"]
C("1% slowdown", f"{f1(a1p)} s, against {f1(a1s)} s for the serial T_A_r1 1% s0, a factor of {f2(a1p / a1s)}", "stats.json:wall_s")
C("1% throughput", f"about {f2(4 * a1s / a1p)}× throughput", "4 × serial / parallel wall")
w5p = [st(t, "0.05", s)["wall_s"] for t in ("T_A_r2", "T_A_r3") for s in SD]; w5s = [st("T_A_r1", "0.05", s)["wall_s"] for s in SD]
C("5% walls", f"{rng(w5p, f1)} s in the batch, against {rng(w5s, f1)} s serial", "stats.json:wall_s")
C("5% slowdown", f"a factor of {f2(min(w5p) / max(w5s))}–{f2(max(w5p) / min(w5s))}", "min/max ratio of the above", ("doc", "ho"))
sm_s = [st("T_A_r1", p, s)["step_median_ms"] for p, s in [("0.01", 0)] + [("0.05", s) for s in SD]]
sm_p = [st(t, p, s)["step_median_ms"] for t in ("T_A_r2", "T_A_r3") for p in RT for s in SD if st(t, p, s)["keyframe_failures"] == 0]
C("step medians", f"step median rose from {rng(sm_s, f1)} ms (serial) to {rng(sm_p, f1)} ms", "stats.json:step_median_ms")
bad = 0
for label, s, src, docs in checks:
    ok = all(s in (DOC if d == "doc" else HO) for d in docs)
    bad += not ok
    print(f"{'OK ' if ok else 'MISSING'} | {label} | {s} | {src} | {','.join(docs)}")
print("MISSING:", bad); sys.exit(1 if bad else 0)
