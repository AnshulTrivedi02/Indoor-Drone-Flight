#!/usr/bin/env python3
"""Stage 2e exact cross-check (numbers_tier1.md provenance rules). Recomputes, INDEPENDENTLY of e3_verdicts.py, every
value and verdict from the per-run score jsons, the per-run stats.json files and the stored references. Asserts that each
equals the value in scores/E3_verdicts.json, then prints each one rounded once with its source.
Positions 4 dp (m), ratios 2 dp, rates % 2 dp. Exit 1 on any mismatch.
Ruling R2 (2026-10-22): the run status (diverged iff stats.json keyframe_failures > 0 or any non-finite value in
live.tum / hindsight.tum) is re-derived HERE from the run outputs, independently of run_status.py, and a diverged run
counts as not satisfying every criterion that needs it (P-E3b.1 literal: also when the matched arm (a) run diverged;
P-E3.6: a flight with any diverged arm (a) run fails). NaN compares equal to NaN in the value checks."""
import json, math, sys
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"; T1 = "/home/makerspace/thesis_data/tier1"
J = lambda p: json.load(open(p)); V = J(f"{SC}/E3_verdicts.json")
FL = ["T_A_r1", "T_A_r2", "T_A_r3"]; RATES = ["0.01", "0.05"]; SEEDS = [0, 1, 2]
BASE = "_t245_tags0-1-2-3-4-5-6-7"; ROB = "_robcauchy2.385"
bad = []
def eq(a, b, what):
    same = a == b or (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b))
    if not same: bad.append((what, a, b))


def diverged(rdir, st):
    if st["keyframe_failures"] > 0:
        return True
    for f in ("live.tum", "hindsight.tum"):
        for ln in open(f"{rdir}/{f}"):
            if any(not math.isfinite(float(x)) for x in ln.split()):
                return True
    return False

ref = {}
for t in FL:
    x = J(f"{R}/eval/results/expL/{t}_t245.json")["tracks"]
    ref[t] = dict(cl=x["lc live"]["rmse_m"], ch=x["lc hindsight"]["rmse_m"], nl=x["nolc live"]["rmse_m"],
                  nh=x["nolc hindsight"]["rmse_m"], ta=J(f"/home/makerspace/thesis_data/trials/{t}/lc_fgo_lc_t245/stats.json")["t_anchor"])
runs = {}
for arm in "ab":
    for t in FL:
        keys = ([("0", None)] if arm == "b" else []) + [(p, s) for p in RATES for s in SEEDS]
        for p, s in keys:
            n = f"E3{arm}_{t}_0" if p == "0" else f"E3{arm}_{t}_{p}_s{s}"
            suf = BASE + ("" if p == "0" else f"_mis{p}_s{s}") + (ROB if arm == "b" else "")
            sc = J(f"{SC}/{n}.json")
            assert sc["tier1"]["suffix"] == suf, (n, sc["tier1"])
            rdir = f"{T1}/{t}/lc_fgo_lc{suf}"; st = J(f"{rdir}/stats.json")
            L, H = sc["tracks"]["lc live"], sc["tracks"]["lc hindsight"]
            runs[n] = dict(t=t, p=p, s=s, arm=arm, live=L["rmse_m"], hind=H["rmse_m"], l1=L["per_lap_rmse_m"][0],
                           l5=L["per_lap_rmse_m"][4], mx=L["max_m"], st=st, div=diverged(rdir, st))
            eq(V["runs"][n]["run_status"]["diverged"], runs[n]["div"], n + " diverged")
            d = V["runs"][n]["values"]
            eq(d["lc live rmse_m"]["value"], L["rmse_m"], n + " live"); eq(d["lc hindsight rmse_m"]["value"], H["rmse_m"], n + " hind")
            eq(d["lc live lap1_m"]["value"], L["per_lap_rmse_m"][0], n + " l1"); eq(d["lc live lap5_m"]["value"], L["per_lap_rmse_m"][4], n + " l5")
            if not runs[n]["div"]:
                eq(V["runs"][n]["ratio lc live lap5/lap1"], L["per_lap_rmse_m"][4] / L["per_lap_rmse_m"][0], n + " ratio")
            eq(V["runs"][n]["gate t_anchor == stored"], st["t_anchor"] == ref[t]["ta"], n + " gate")
            m = st["tier1"]["mislabel"]
            if m is not None:
                vm = V["runs"][n]["covariates"]["mislabel"]
                eq(vm["n_mislabelled"], m["n_mislabelled"], n + " nmis"); eq(vm["n_calls"], m["n_calls"], n + " ncalls")
                eq(vm["effective_overall_rate"], m["n_mislabelled"] / m["n_calls"], n + " eff")
                eq(vm["rate_among_eligible"], m["n_mislabelled"] / m["n_eligible_non_gauge"], n + " elig")
                assert all(e[1] != 0 and e[2] != 0 and e[1] != e[2] for e in m["events_t_true_new"]), n

def cnt(names, f, needs=lambda n: [n]):   # ruling R2: a needed diverged run -> not satisfied (f never evaluated)
    return sum(1 for n in names if not any(runs[m]["div"] for m in needs(n)) and f(runs[n]))
r1 = [f"E3a_{t}_0.01_s{s}" for t in FL for s in SEEDS]; r5 = [f"E3a_{t}_0.05_s{s}" for t in FL for s in SEEDS]
my = {"H-E3.1": cnt(r1, lambda r: r["live"] < ref[r["t"]]["nl"]), "H-E3.2": cnt(r1, lambda r: r["hind"] < ref[r["t"]]["nh"]),
      "H-E3.3": cnt(r1, lambda r: r["l5"] <= 1.5 * r["l1"]), "P-E3.4": cnt(r1, lambda r: r["live"] <= 2 * ref[r["t"]]["cl"]),
      "P-E3.5a": cnt(r5, lambda r: r["live"] < ref[r["t"]]["nl"]), "P-E3.5b": cnt(r5, lambda r: r["hind"] < ref[r["t"]]["nh"]),
      "P-E3.5c": cnt(r5, lambda r: r["l5"] <= 1.5 * r["l1"])}
m6 = 0
for t in FL:
    dv = [f"E3a_{t}_{p}_s{s}" for p in RATES for s in SEEDS if runs[f"E3a_{t}_{p}_s{s}"]["div"]]
    if dv:
        print(f"| P-E3.6 {t} | not satisfied: diverged {dv} |"); continue
    a1 = sum(runs[f"E3a_{t}_0.01_s{s}"]["live"] for s in SEEDS) / 3; a5 = sum(runs[f"E3a_{t}_0.05_s{s}"]["live"] for s in SEEDS) / 3
    m6 += ref[t]["cl"] <= a1 <= a5
    print(f"| P-E3.6 {t} | clean {ref[t]['cl']:.4f} | 1% mean {a1:.4f} | 5% mean {a5:.4f} |")
my["P-E3.6"] = m6
for p in RATES:
    my[f"P-E3b.1 {p}"] = cnt([f"E3b_{t}_{p}_s{s}" for t in FL for s in SEEDS],
                             lambda r: r["live"] <= 1.10 * runs[f"E3a_{r['t']}_{r['p']}_s{r['s']}"]["live"],
                             needs=lambda n: [n, "E3a" + n[3:]])
my["P-E3b.2"] = cnt([f"E3b_{t}_0" for t in FL], lambda r: abs(r["live"] / ref[r["t"]]["cl"] - 1) <= 0.10)
vc = {**V["criteria_a"], **V["criteria_b"]}
for k, c in my.items():
    vk = [x for x in vc if x.split(" ")[0] == k.split(" ")[0] and (len(k.split(" ")) == 1 or k.split(" ")[1] in x)]
    assert len(vk) == 1, (k, vk)
    den = int(vc[vk[0]]["count"].split("/")[1])
    eq(vc[vk[0]]["count"], f"{c}/{den}", k + " count")
    print(f"| {k} | {c}/{den} | {'PASS' if c == den else 'FAIL'} | verdicts.json: {vc[vk[0]]['verdict']} {vc[vk[0]]['count']} |")
    eq(vc[vk[0]]["verdict"], "PASS" if c == den else "FAIL", k + " verdict")
for p in RATES:
    M = [runs[f"E3a_{t}_{p}_s{s}"]["st"]["tier1"]["mislabel"] for t in FL for s in SEEDS]
    pe = sum(m["n_mislabelled"] for m in M) / sum(m["n_eligible_non_gauge"] for m in M)
    po = sum(m["n_mislabelled"] for m in M) / sum(m["n_calls"] for m in M)
    eq(V["effective_rates"][f"a {p}"]["pooled_rate_among_eligible"], pe, "pooled e " + p)
    eq(V["effective_rates"][f"a {p}"]["pooled_effective_overall_rate"], po, "pooled o " + p)
    print(f"| pooled {p} | eligible {100*pe:.2f} % | overall {100*po:.2f} % | n {sum(m['n_mislabelled'] for m in M)} |")
for n, r in runs.items():
    print(f"| {n} | live {r['live']:.4f} | hind {r['hind']:.4f} | lap1 {r['l1']:.4f} lap5 {r['l5']:.4f} | {r['l5']/r['l1']:.2f} | "
          f"t_anchor {r['st']['t_anchor']} | lm {r['st']['landmarks']} | kf_fail {r['st']['keyframe_failures']} | wall {r['st']['wall_s']:.1f} |")
for arm in "ab":
    for t in FL:
        for p in RATES:
            k = sum(runs[f"E3{arm}_{t}_{p}_s{s}"]["div"] for s in SEEDS)
            print(f"| arm ({arm}) {t} {p} | {k} of 3 runs diverged |")
print("MISMATCHES:", bad if bad else "none")
sys.exit(1 if bad else 0)
