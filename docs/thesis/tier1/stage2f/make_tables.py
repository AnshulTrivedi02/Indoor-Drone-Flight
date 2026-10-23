#!/usr/bin/env python3
"""Stage 2f (E4): result tables for e4_results.md and numbers_tier1.md §E4, from scores/E4_verdicts.json and
stage2f/timing.tsv only. Each value is rounded ONCE with rd() (positions m 4 dp, step times ms 2 dp, wall s 1 dp,
fractions and ratios 2 dp). Writes stage2f/results_tables.md and stage2f/rows.md (numbers_tier1 rows)."""
import json, statistics as stt
R = "/home/makerspace/thesis_ws"; S = "/home/makerspace/thesis_data/tier1/stage2f"; T1 = "/home/makerspace/thesis_data/tier1"
V = json.load(open(f"{R}/docs/thesis/tier1/scores/E4_verdicts.json"))
FL = [f"T_{c}_r{r}" for c in "ABCD" for r in (1, 2, 3)]; WS = ["0.25", "0.5", "1", "2", "5"]
UNIT = {"m": 4, "ms": 2, "s": 1, "x": 2}
rd = lambda x, u: "—" if x is None else f"{x:.{UNIT[u]}f}"
job = lambda t, w, lm="": f"e4_{t}_w{w}{lm}"
RUN = V["runs"]
SRCV = "json:scores/E4_verdicts.json"
# driver wall times (stage2a for 0.25 s cap 2)
wall = {}
for ln in open(f"{S}/timing.tsv"):
    f = ln.rstrip("\n").split("\t")
    if len(f) >= 9 and f[8] == "completed":
        wall[f[0]] = float(f[3])
for ln in open(f"{T1}/stage2a/timing.tsv"):
    f = ln.rstrip("\n").split("\t")
    if f[0].startswith("ge4_"):
        wall[job(f[0][4:], "0.25")] = float(f[3])
L = []; P = L.append
P("### Run status and driver wall time (DIAGNOSTIC; 0.25 s cap 2 = Stage 2a G-E4 runs)\n")
P("| W (s) | cap | runs completed | status OK / FAILED-ESTIMATOR | driver wall min–max (s) | mean (s) |")
P("|---|---|---|---|---|---|")
for lm, fls in (("", FL), ("_lm10", ["T_A_r1", "T_D_r1"])):
    for w in WS:
        js = [job(t, w, lm) for t in fls]; done = [j for j in js if j in RUN]
        ok = sum(RUN[j]["status"] == "OK" for j in done); ws_ = [wall[j] for j in done if j in wall]
        P(f"| {w} | {10 if lm else 2} | {len(done)}/{len(js)} | {ok} / {len(done) - ok} | "
          f"{rd(min(ws_), 's')}–{rd(max(ws_), 's')} | {rd(stt.mean(ws_), 's')} |" if ws_ else f"| {w} | {10 if lm else 2} | 0/{len(js)} | — | — | — |")
P("\n### Per-step time after the anchor, median / p95 (ms; DIAGNOSTIC: workstation Python, 1 thread, nice 19, serial)\n")
P("| flight | " + " | ".join(f"W = {w} s" for w in WS) + " | strictly increasing (P-E4.1) |")
P("|---|" + "---|" * (len(WS) + 1))
for t in FL:
    c = [f"{rd(RUN[j]['step_median_ms_after_anchor'], 'ms')} / {rd(RUN[j]['step_p95_ms_after_anchor'], 'ms')}" if (j := job(t, w)) in RUN else "NOT RUN" for w in WS]
    s = V["P-E4.1"]["per_flight"][t]
    P(f"| {t} | " + " | ".join(c) + f" | {'yes' if s.get('strictly_increasing') else ('—' if s['satisfied'] is None else 'no')} |")
P("\n### Median step time over ALL keyframes (ms; DIAGNOSTIC; P-E4.2 second reading, D13)\n")
P("| flight | " + " | ".join(f"W = {w} s" for w in WS) + " |")
P("|---|" + "---|" * len(WS))
for t in FL:
    P(f"| {t} | " + " | ".join(rd(RUN[j]["step_median_ms"], "ms") if (j := job(t, w)) in RUN else "NOT RUN" for w in WS) + " |")
P("\n### FGO live horizontal RMSE in the lap window (m; world frame, no alignment) and the stored batch B_i\n")
P("| flight | " + " | ".join(f"W = {w} s" for w in WS) + " | stored batch B_i | L(5) < L(0.25) (H-E4.3; L(5) − L(0.25), unrounded) |")
P("|---|" + "---|" * (len(WS) + 2))
for t in FL:
    h = V["H-E4.3"]["per_flight"][t]
    P(f"| {t} | " + " | ".join(rd(RUN[j]["live"]["rmse"], "m") if (j := job(t, w)) in RUN else "NOT RUN" for w in WS)
      + f" | {rd(V['stored']['B_i (expT FGO batch rmse)'][t], 'm')} | {'yes' if h.get('lower_at_5') else ('—' if h['satisfied'] is None else 'no')} ({h['L5_m'] - h['L0.25_m']:+.7f} m) |")
P("\n### Fraction of the batch gain recovered (DESCRIPTIVE, no band)\n")
P("| W (s) | F(W) pooled, 12 flights | F A | F B | F C | F D | median f_i | f_i min–max | flights |")
P("|---|---|---|---|---|---|---|---|---|")
for w in WS[1:]:
    g = V["gain_fraction"]["cap2"][w]; fs = list(g["f_i"].values())
    P(f"| {w} | {rd(g['F_pooled'], 'x')} | " + " | ".join(rd(g["F_per_condition"][c], "x") for c in "ABCD")
      + f" | {rd(g['median_f_i'], 'x')} | {rd(min(fs), 'x')}–{rd(max(fs), 'x')} | {g['n_flights']} |" if fs else f"| {w} | — |")
gl = V["gain_fraction"]["lm10 rows (L_i(0.25) = cap-2 0.25 s run, D15)"]
P("\nLM-cap-10 rows (f_i, L_i(0.25) = the cap-2 0.25 s run): " + "; ".join(
    f"{t} " + ", ".join(f"W {w}: {rd(gl[f'{t} w{w}'], 'x')}" for w in WS) for t in ("T_A_r1", "T_D_r1")))
P("\n### LM cap 2 vs cap 10 (D12; flag iff any RMS reading > 0.029 m)\n")
P("| flight, W (s) | paired rows (unmatched) | horiz RMS / max, all (m) | 3D RMS / max, all (m) | horiz RMS, lap (m) | 3D RMS, lap (m) | live RMSE cap 2 / cap 10 (m) | Δ RMSE (m) | flag |")
P("|---|---|---|---|---|---|---|---|---|")
for t in ("T_A_r1", "T_D_r1"):
    for w in WS:
        c = V["convergence"]["per_run"][f"{t} w{w}"]
        if c is None:
            P(f"| {t}, {w} | NOT RUN | | | | | | | |"); continue
        P(f"| {t}, {w} | {c['rows_paired']} ({c['unmatched']}) | {rd(c['horiz_all']['rms_m'], 'm')} / {rd(c['horiz_all']['max_m'], 'm')} | "
          f"{rd(c['3d_all']['rms_m'], 'm')} / {rd(c['3d_all']['max_m'], 'm')} | {rd(c['horiz_lap']['rms_m'], 'm')} | {rd(c['3d_lap']['rms_m'], 'm')} | "
          f"{rd(c['live_rmse_cap2_m'], 'm')} / {rd(c['live_rmse_cap10_m'], 'm')} | {c['rmse_diff_cap10_minus_cap2_m']:+.4f} | "
          f"{'cap 2 NOT CONVERGED' if c['NOT_CONVERGED'] else 'converged'} |")
P("\n### Verdicts\n")
P("| criterion | verdict | count |")
P("|---|---|---|")
P(f"| P-E4.1: median step (after the anchor) strictly increasing 0.25 < 0.5 < 1 < 2 < 5 s, 12/12 | **{V['P-E4.1']['verdict']}** | {V['P-E4.1']['count']} |")
c2 = V["P-E4.2"]["counts"]
P(f"| P-E4.2: median ≤ 33 ms at 0.25 s and > 33 ms at W ≥ 1 s, 12/12 at each (both readings, D13) | **{V['P-E4.2']['verdict']}** | "
  + ", ".join(f"{w} s: {c2[w]}" for w in ("0.25", "1", "2", "5")) + f"; 0.5 s (DESCRIPTIVE, on the budget): {sum(1 for v in V['P-E4.2']['per_window']['0.5']['per_flight'].values() if v['median_all_ms'] <= 33 and v['median_after_anchor_ms'] <= 33)}/12 ≤ 33 ms |")
q = V["H-E4.3"]["qualifier"]
P(f"| **H-E4.3**: live RMSE at 5 s < at 0.25 s, ≥ 10/12 (≥ 10/12: judgement, not derived from data) | **{V['H-E4.3']['verdict']}**{' (' + q + ')' if q else ''} | {V['H-E4.3']['count']} |")
open(f"{S}/results_tables.md", "w").write("\n".join(L) + "\n")
# numbers_tier1 rows
N = []; A = N.append
for t in FL:
    for w in WS:
        j = job(t, w)
        if j in RUN:
            A(f"| {t} FGO live RMSE, W = {w} s | {rd(RUN[j]['live']['rmse'], 'm')} | m | CURRENT | `json:scores/E4_{t}_w{w}.json:tracks.FGO live.horiz_err_m.rmse` |")
for t in FL:
    for w in WS:
        j = job(t, w)
        if j in RUN:
            A(f"| {t} step median after anchor / all keyframes, W = {w} s | {rd(RUN[j]['step_median_ms_after_anchor'], 'ms')} / {rd(RUN[j]['step_median_ms'], 'ms')} | ms | DIAGNOSTIC | `tier1:{t}/room_fgo_w{w}/stats.json` keys `tier1.step_median_ms_after_anchor`, `step_median_ms` |")
for w in WS[1:]:
    g = V["gain_fraction"]["cap2"][w]
    A(f"| F({w} s) pooled / median f_i | {rd(g['F_pooled'], 'x')} / {rd(g['median_f_i'], 'x')} | fraction | DESCRIPTIVE | `{SRCV}:gain_fraction.cap2.{w}.F_pooled`, `.median_f_i` |")
for t in ("T_A_r1", "T_D_r1"):
    for w in WS:
        c = V["convergence"]["per_run"][f"{t} w{w}"]
        if c:
            A(f"| {t} cap 2 vs cap 10, W = {w} s: max RMS reading / flag | {rd(c['max_rms_reading_m'], 'm')} / {'NOT CONVERGED' if c['NOT_CONVERGED'] else 'converged'} | m | DESCRIPTIVE | `{SRCV}:convergence.per_run.{t} w{w}.max_rms_reading_m` |")
A(f"| P-E4.1 | {V['P-E4.1']['verdict']} ({V['P-E4.1']['count']}) | — | CURRENT | `{SRCV}:P-E4.1.verdict` |")
A(f"| P-E4.2 | {V['P-E4.2']['verdict']} (" + ", ".join(f"{w} s {c2[w]}" for w in ("0.25", "1", "2", "5")) + f") | — | CURRENT | `{SRCV}:P-E4.2.verdict` |")
A(f"| H-E4.3 | {V['H-E4.3']['verdict']} ({V['H-E4.3']['count']}){'; ' + q if q else ''} | — | CURRENT | `{SRCV}:H-E4.3.verdict` |")
open(f"{S}/rows.md", "w").write("\n".join(N) + "\n")
print(open(f"{S}/results_tables.md").read())
