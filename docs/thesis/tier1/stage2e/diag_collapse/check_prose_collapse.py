#!/usr/bin/env python3
"""E3 map-collapse diagnosis: exact prose cross-check (the stage2e/check_prose.py approach). Every hand-written number in
e3_results.md §7, the METHODOLOGY entry and the handover is recomputed from its source (summary.json, recon_*.json, the
cf status/score jsons, stats.json, E3_verdicts.json, timing.tsv), rounded ONCE by rd(), and the exact string must appear
in the named document(s). Exit 1 on any missing string. Prints label | string | source."""
import json, sys
R = "/home/makerspace/thesis_ws"; T1 = "/home/makerspace/thesis_data/tier1"; O = f"{T1}/stage2e/diag_collapse"
J = lambda p: json.load(open(p)); S = J(f"{O}/summary.json"); V = J(f"{R}/docs/thesis/tier1/scores/E3_verdicts.json")
DOCS = {"doc": open(f"{R}/docs/thesis/tier1/e3_results.md").read().split("## 7. Map-collapse diagnosis")[1],
        "meth": open(f"{R}/METHODOLOGY.md").read().split("E3 map-collapse diagnosis (descriptive")[-1],
        "ho": open(f"{R}/docs/handovers/2026-10-23_e3_collapse_diag.md").read()}


def rd(x, nd, comma=False):
    """Round once."""
    return f"{x:,.{nd}f}" if comma else f"{x:.{nd}f}"


checks = []
def C(label, s, src, docs=("doc",)): checks.append((label, s, src, docs))
a, r3, cf, rb, rb2 = S["r1_1_s0"], S["r3_5_s0"], S["cf_ii"], S["r1_1_s0_rob"], S["r2_5_s1_rob"]
# 7.1 / 7.6 arithmetic
w1 = 0.5 * a["w_truth"]["wrong_w_median"] ** 2; sv = a["flow_sigma_v_m_s"]
C("median wrong cost", f"about {rd(round(w1, -2), 0, True)}", "0.5 * r1_1_s0 w_truth wrong_w_median^2 (to 100)", ("doc", "meth", "ho"))
C("wrong |w| truth (7.1)", f"about {rd(a['w_truth']['wrong_w_median'], 0)}σ", "summary r1_1_s0 w_truth.wrong_w_median", ("doc", "meth", "ho"))
C("h_cam", f"h_cam ≈ {rd(a['h_cam_median_m'], 4)} m", "summary r1_1_s0 h_cam_median_m")
C("sigma_v", f"{rd(sv, 4)} m/s", "0.25 * h_cam", ("doc", "meth", "ho"))
C("break-even T", f"longer than {rd(0.5 * 30 * 36 / (sv ** 2 * round(w1, -2)), 2)} s", "0.5*30*6^2/(sigma_v^2 * cost)", ("doc", "meth"))
C("cost 7.6", f"({rd(round(w1, -2), 0, True)})", "same")
# 7.2
for n, k in (("r1_1_s0", "19/19"), ("r3_5_s0", "94/94"), ("r2_5_s1_rob", "78/78")):
    d = J(f"{O}/{dict(r1_1_s0='recon_T_A_r1_0.01_s0', r3_5_s0='recon_T_A_r3_0.05_s0', r2_5_s1_rob='recon_T_A_r2_0.05_s1_rob')[n]}.json")
    assert d["events_match_logged"] and d["clock_rows_match"]
    C(f"events {n}", f"{d['n_events']}/{d['n_events']}", f"recon {n} n_events")
C("rob correct est", f"median of {rd(rb['w_est']['correct_w_median'], 2)}σ", "summary r1_1_s0_rob w_est.correct_w_median")
tr = {rd(S[n]["w_truth"]["correct_w_median"], 2) for n in ("r1_1_s0", "r3_5_s0", "cf_ii", "r1_1_s0_rob", "r2_5_s1_rob")}
assert len(tr) == 1; C("truth correct all", f"at {tr.pop()}σ on every run", "summary *.w_truth.correct_w_median")
# 7.3
rc = J(f"{O}/recon_T_A_r1_0.01_s0.json"); fm = [f for f in rc["factors"] if f["mis"] and f["first"]]
C("first-sighting events", f"{rd(fm[0]['t'], 3)} s (4→3) and {rd(fm[1]['t'], 3)} s (4→6)", "recon r1 first-sighting factors (keyframe t)")
C("max before", f"at most {rd(a['max_err_before_first_1m'], 4)} m until {rd(a['first_live_err_over_1m_t'], 3)} s", "summary r1_1_s0", ("doc",))
C("step6", f"jumps to {rd(a['err_after_first_correct']['6'], 4)} m", "summary r1_1_s0 err_after_first_correct.6", ("doc", "ho"))
C("step3 t", f"Step 2, at {rd(a['first_correct_sighting_t']['3'], 3)} s", "summary r1_1_s0 first_correct_sighting_t.3")
C("step3 err", f"({rd(a['err_after_first_correct']['3'], 4)} m just after)", "summary r1_1_s0 err_after_first_correct.3")
C("t6", f"Step 1, at {rd(a['first_correct_sighting_t']['6'], 3)} s", "summary r1_1_s0 first_correct_sighting_t.6")
C("r3 onset", f"at {rd(r3['first_live_err_over_1m_t'], 3)} s, at a *non-first* wrong id ({r3['last_wrong_before_first_1m'][0]}→{r3['last_wrong_before_first_1m'][1]})",
  "summary r3_5_s0 first_live_err_over_1m_t / last_wrong_before_first_1m")
assert r3["last_wrong_before_first_1m"][2] is False
# 7.4 table
for lab, x in (("T_A_r1 1% s0, arm (a)", a), ("T_A_r3 5% s0, arm (a)", r3), ("cf (ii) T_A_r1 1% s0, 2 wrong only", cf)):
    e, t = x["w_est"], x["w_truth"]
    C(f"row {lab}", f"| {lab} | {x['n_wrong']} / {x['n_factors']} | {rd(t['tag_cost'], 0, True)} | {rd(e['tag_cost'], 0, True)} | {rd(100 * e['wrong_share'], 1)}% | "
      f"{rd(t['wrong_w_median'], 1)} → {rd(e['wrong_w_median'], 1)} | {rd(t['correct_w_median'], 2)} → {rd(e['correct_w_median'], 2)} | {rd(x['flow_proxy_cost'], 0, True)} | "
      f"{rd(x['spread_est_m'], 3)} / {rd(x['spread_truth_m'], 3)} | {rd(x['path_hindsight_m'], 1)} / {rd(x['path_truth_m'], 1)} |", f"summary {lab}")
ratio = a["w_truth"]["tag_cost"] / (a["w_est"]["tag_cost"] + a["flow_proxy_cost"])
assert 9.5 <= ratio < 10.5, ratio
C("about 10x", f"about 10× lower than the tag cost alone at the true layout (T_A_r1 1% s0: {rd(a['w_est']['tag_cost'], 0, True)} + {rd(a['flow_proxy_cost'], 0, True)} against {rd(a['w_truth']['tag_cost'], 0, True)})", "summary r1_1_s0")
C("residual fall", f"from about {rd(a['w_truth']['wrong_w_median'], 0)}σ to about {rd(a['w_est']['wrong_w_median'], 0)}σ", "summary r1_1_s0")
C("correct rise", f"rise only to about {rd(a['w_est']['correct_w_median'], 0)}σ", "summary r1_1_s0")
C("path", f"{rd(a['path_hindsight_m'], 1)} m against {rd(a['path_truth_m'], 1)} m true", "summary r1_1_s0")
C("flow w", f"about {rd(a['flow_proxy_w_median'], 0)}σ of one flow factor", "summary r1_1_s0 flow_proxy_w_median")
C("top3", f"carry {rd(100 * a['w_est']['top3_wrong_share_of_wrong'], 1)}% of the wrong", "summary r1_1_s0 w_est.top3_wrong_share_of_wrong")
C("19 wrong share", f"The {a['n_wrong']} wrong factors ({rd(100 * a['n_wrong'] / a['n_factors'], 1)}% of the factors) together carry {rd(100 * a['w_est']['wrong_share'], 1)}%", "summary r1_1_s0")
C("rob spread", f"(spread {rd(rb['spread_est_m'], 3)} m)", "summary r1_1_s0_rob")
C("rob wrong", f"stay at about {rd(rb['w_est']['wrong_w_median'], 0)}σ", "summary r1_1_s0_rob w_est.wrong_w_median")
C("rob2 cauchy", f"at the estimate ({rd(rb2['w_est']['cauchy_tag_cost'], 0, True)}) is *higher* than at the truth ({rd(rb2['w_truth']['cauchy_tag_cost'], 0, True)})", "summary r2_5_s1_rob cauchy", ("doc",))
assert rb2["w_est"]["cauchy_tag_cost"] > rb2["w_truth"]["cauchy_tag_cost"]
C("rob2 flow", f"extra flow cost of {rd(rb2['flow_proxy_cost'], 0, True)}", "summary r2_5_s1_rob flow_proxy_cost")
C("rob2 path", f"({rd(rb2['path_hindsight_m'], 1)} m against {rd(rb2['path_truth_m'], 1)} m)", "summary r2_5_s1_rob")
C("rob2 nfirst", f"Its {['', 'one', 'two', 'three', 'four', 'five'][len(rb2['first_sighting_mislabelled_tids'])]} first-sighting mislabels", "summary r2_5_s1_rob")
fs5 = [J(f"{T1}/{t}/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.05_s{s}/stats.json")["tier1"]["landmarks_first_sighting_mislabelled"] for t in ("T_A_r1", "T_A_r2", "T_A_r3") for s in (0, 1, 2)]
assert sum(f >= len(rb2["first_sighting_mislabelled_tids"]) for f in fs5) > 1, fs5   # 'not unique among the 5% runs'
# 7.5 table
st0 = J(f"{T1}/T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s0/stats.json")
C("orig row", f"| original (scored) | — | {a['n_wrong']} | 3, 6 | OK | {rd(a['lc_live_rmse_m'], 4)} | {rd(a['lc_hindsight_rmse_m'], 4)} | {rd(a['spread_est_m'], 3)} | {rd(st0['wall_s'], 1)} |", "summary + scores E3a + stats.json")
tim = {l.split("\t")[0]: l.split("\t") for l in open(f"{O}/timing.tsv") if "\t" in l}
si = S["cf_i"]["status"]; ONS = "live_excursion_onset_t_s (|x| or |y| > 10 m, or non-finite; DESCRIPTIVE)"
assert si["status"] == "FAILED-ESTIMATOR" and si["prefix_check"]["prefix_identical"]
wi = J(f"{si['run_dir']}/stats.json")["wall_s"]
C("cf_i row", f"| cf (i) | 36.169, 36.928 | 17 | none | **FAILED-ESTIMATOR**: onset {rd(si[ONS], 3)} s, first exception {rd(si['first_failure_t_s'], 3)} s, failure fraction {rd(si['failure_fraction'], 2)} | diverged | diverged | diverged | {rd(wi, 1)} |",
  "status/cf_i.json + stats.json:wall_s")
C("cf_i onset", f"onset {rd(si[ONS], 3)} s", "status/cf_i.json", ("doc", "meth", "ho"))
sii = S["cf_ii"]["status"]; assert sii["status"] == "OK" and sii["prefix_check"]["prefix_identical"]
C("cf_ii row", f"| cf (ii) | the other 17 | {cf['n_wrong']} | 3, 6 | OK | {rd(cf['lc_live_rmse_m'], 4)} | {rd(cf['lc_hindsight_rmse_m'], 4)} | {rd(cf['spread_est_m'], 3)} | {rd(J(f"{sii['run_dir']}/stats.json")['wall_s'], 1)} |", "summary cf_ii + stats.json:wall_s")
for s in (1, 2):
    x = S[f"cf2_s{s}"]; keep = {1: "49.402, 60.358", 2: "54.253, 55.870"}[s]; assert x["keyframe_failures"] == 0 and x["first_sighting_mislabelled"] == 0
    C(f"cf2_s{s} row", f"| cf2_s{s} (earlier diagnosis, seed {s}) | {keep} | {x['n_wrong_remaining']} | none | OK | {rd(x['lc_live_rmse_m'], 4)} | {rd(x['lc_hindsight_rmse_m'], 4)} | {rd(x['spread_est_m'], 3)} | {rd(x['wall_s'], 1)} |", f"summary cf2_s{s}")
C("prefix rows", f"{si['prefix_check']['prefix_rows_before_first_kept_keyframe']} rows for cf (i), {sii['prefix_check']['prefix_rows_before_first_kept_keyframe']} rows for cf (ii)", "status/cf_*.json prefix_check")
clean = V["runs"]["E3a_T_A_r1_0.01_s0"]["values"]["lc live rmse_m"]["value"] / V["runs"]["E3a_T_A_r1_0.01_s0"]["lc live / stored clean lc live"]
C("cf_ii x clean", f"LC live is {rd(cf['lc_live_rmse_m'], 4)} m ({rd(cf['lc_live_rmse_m'] / clean, 0)}× clean)", "summary cf_ii / stored clean LC live (E3_verdicts ratio-implied)", ("doc",))
C("cf_ii spread", f"spread {rd(cf['spread_est_m'], 3)} m against {rd(cf['spread_truth_m'], 3)} m", "summary cf_ii", ("doc",))
C("cf2 spreads", f"spread {rd(S['cf2_s1']['spread_est_m'], 3)} and {rd(S['cf2_s2']['spread_est_m'], 3)} m", "summary cf2_*", ("doc", "meth", "ho"))
C("cf2_s1 max", f"live max of {rd(S['cf2_s1']['lc_live_max_m'], 4)} m", "summary cf2_s1 lc_live_max_m")
# 7.7 machine time
C("time cf_i", f"| cf (i) | {tim['cf_i'][2]} s |", "timing.tsv"); C("time cf_ii", f"| cf (ii) | {tim['cf_ii'][2]} s |", "timing.tsv")
C("ho times", f"{tim['cf_i'][2]} s + {tim['cf_ii'][2]} s", "timing.tsv", ("ho",))
# METHODOLOGY / handover headline numbers
nda = [V["runs"][f"E3a_{t}_{p}_s{q}"] for t in ("T_A_r1", "T_A_r2", "T_A_r3") for p in ("0.01", "0.05") for q in (0, 1, 2)]
xs = [r["lc live / stored clean lc live"] for r in nda if not r["run_status"]["diverged"]]; assert len(xs) == 12
C("meth 51-85", f"{rd(min(xs), 0)}–{rd(max(xs), 0)}× clean", "E3_verdicts.json:runs.E3a_*.lc live / stored clean lc live (non-diverged)", ("meth",))
fs = [f for f in rc["factors"] if f["mis"] and f["first"]]
C("meth 22.4", f"({rd(a['first_correct_sighting_t']['6'], 3)} s), {rd(a['first_correct_sighting_t']['6'] - fs[1]['t'], 1)} s after the mislabel", "summary - recon", ("meth",))
C("cf_ii x clean meth/ho", f"({rd(cf['lc_live_rmse_m'] / clean, 0)}× clean)", "summary cf_ii / clean", ("doc", "meth", "ho"))
C("truth spread meth/ho", f"against {rd(cf['spread_truth_m'], 3)} m", "summary spread_truth_m", ("doc", "meth", "ho"))
C("ho first-sighting", f"({rd(fm[0]['t'], 3)} / {rd(fm[1]['t'], 3)} s)", "recon r1 first-sighting factors", ("ho",))
C("ho 59.332", f"first correct sighting ({rd(a['first_correct_sighting_t']['6'], 3)} s)", "summary r1_1_s0", ("ho",))
C("ho 43.914", f"non-first wrong id ({rd(r3['first_live_err_over_1m_t'], 3)} s)", "summary r3_5_s0", ("ho",))
import glob
gv = J(sorted(glob.glob(f"{R}/docs/thesis/tier1/frozen_manifest_20261022T002851_verify_e3collapse_*.json"))[-1]); assert gv["verdict"] == "IDENTICAL"
C("guard files", f"IDENTICAL, {gv['n_files_checked']:,}", "guard verify report n_files_checked", ("ho",))
C("meth cf_ii live", f"{rd(cf['lc_live_rmse_m'], 4)} m", "summary cf_ii", ("meth", "ho"))
C("meth r1 costs", f"{rd(a['w_est']['tag_cost'], 0, True)} + {rd(a['flow_proxy_cost'], 0, True)} against {rd(a['w_truth']['tag_cost'], 0, True)}", "summary r1_1_s0", ("meth", "ho"))
bad = 0
for label, s, src, docs in checks:
    ok = all(s in DOCS[d] for d in docs); bad += not ok
    print(f"{'OK ' if ok else 'MISSING'} | {label} | {s} | {src} | {','.join(docs)}")
print(f"{len(checks)} checks, {bad} missing"); sys.exit(1 if bad else 0)
