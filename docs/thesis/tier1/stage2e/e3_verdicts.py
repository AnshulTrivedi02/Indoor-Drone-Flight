#!/usr/bin/env python3
"""Stage 2e: mechanical E3 verdicts (preregistration.md §2.1-§2.4; extension experiment, pre-registered (2026-10-21;
signed off with amendments 2026-10-22)). Reads only:
  docs/thesis/tier1/scores/E3a_T_A_r<i>_<p>_s<s>.json, E3b_T_A_r<i>_<p>_s<s>.json, E3b_T_A_r<i>_0.json   (l_score.py)
  eval/results/expL/T_A_r<i>_t245.json             (stored Experiment 3: clean LC and no-LC references, CURRENT)
  ~/thesis_data/trials/T_A_r<i>/lc_fgo_lc_t245/stats.json   (stored t_anchor and wall_s, frozen)
  ~/thesis_data/tier1/g0/T_A_r1/lc_fgo_lc_t245/stats.json   (G0-L (i): the serial clean wall_s for T_A_r1)
  ~/thesis_data/tier1/T_A_r<i>/lc_fgo_lc_t245<suffix>/stats.json   (covariates, invariants, mislabel counts, wall)
Writes docs/thesis/tier1/scores/E3_verdicts.json (must be new). Every comparison is on unrounded json values.
Lap 1 = per_lap_rmse_m[0], lap 5 = per_lap_rmse_m[4]. Verdict per criterion: NOT MET if a needed run failed its gate
(t_anchor != stored); else PASS iff every needed run satisfies the criterion.
USER RULING R2 (2026-10-22, terminology clarification, preregistration §2.3; applied before any E3 scoring): a DIVERGED
run (status FAILED-ESTIMATOR in stage2e/status/<job>.json: keyframe_failures > 0 or a non-finite .tum value) counts as
NOT SATISFYING every criterion that needs it (per-run False -> FAIL, never NOT MET). P-E3.6: a flight with any diverged
arm (a) run fails and its seed means are not computed. P-E3b.1 (literal): the run fails if its arm (b) run OR its matched
arm (a) run diverged. Each verdict carries "k of 3 runs diverged" per flight with divergence times (live excursion
onset = headline; first exception time; failure fraction, inflated because the harness does not recover after a throw).
Also reads stage2e/status/<job>.json and, for the 0% serial runtime pair (ruling R3), the extra timing-only arm (a) run
~/thesis_data/tier1/T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7/stats.json."""
import json, math, os, sys, statistics

R = "/home/makerspace/thesis_ws"
SC = f"{R}/docs/thesis/tier1/scores"
OUT = f"{SC}/E3_verdicts.json"
T1 = "/home/makerspace/thesis_data/tier1"
FL = [f"T_A_r{i}" for i in (1, 2, 3)]
RATES = ["0.01", "0.05"]
SEEDS = [0, 1, 2]
BASE = "_t245_tags0-1-2-3-4-5-6-7"
ROB = "_robcauchy2.385"
STS = "/home/makerspace/thesis_data/tier1/stage2e/status"
ONSET = "live_excursion_onset_t_s (|x| or |y| > 10 m, or non-finite; DESCRIPTIVE)"
if os.path.exists(OUT):
    sys.exit(f"REFUSED: {OUT} exists")
src = lambda f, k: f"json:{os.path.relpath(f, R) if f.startswith(R) else f}:{k}"
J = lambda p: json.load(open(p))
res = {"label": "extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22)",
       "references": {}, "runs": {}, "criteria_a": {}, "criteria_b": {}, "effective_rates": {}, "invariants": {},
       "runtime_descriptive": {}, "divergence": {},
       "rule": "user ruling R2 2026-10-22: a diverged (FAILED-ESTIMATOR) run counts as not satisfying any criterion that "
               "needs it (FAIL, never NOT MET); P-E3b.1 literal (fails if the arm (b) or the matched arm (a) run diverged)"}

# ---- stored references (same flight) ----
ref = {}
for t in FL:
    f = f"{R}/eval/results/expL/{t}_t245.json"; x = J(f)["tracks"]
    sf = f"/home/makerspace/thesis_data/trials/{t}/lc_fgo_lc_t245/stats.json"; st = J(sf)
    ref[t] = {"clean lc live rmse_m": (x["lc live"]["rmse_m"], src(f, "tracks.lc live.rmse_m")),
              "clean lc hindsight rmse_m": (x["lc hindsight"]["rmse_m"], src(f, "tracks.lc hindsight.rmse_m")),
              "nolc live rmse_m": (x["nolc live"]["rmse_m"], src(f, "tracks.nolc live.rmse_m")),
              "nolc hindsight rmse_m": (x["nolc hindsight"]["rmse_m"], src(f, "tracks.nolc hindsight.rmse_m")),
              "clean lc live lap1_m": (x["lc live"]["per_lap_rmse_m"][0], src(f, "tracks.lc live.per_lap_rmse_m[0]")),
              "clean lc live lap5_m": (x["lc live"]["per_lap_rmse_m"][4], src(f, "tracks.lc live.per_lap_rmse_m[4]")),
              "t_anchor_s": (st["t_anchor"], src(sf, "t_anchor")),
              "stored clean wall_s (6 parallel)": (st["wall_s"], src(sf, "wall_s"))}
g0f = f"{T1}/g0/T_A_r1/lc_fgo_lc_t245/stats.json"
ref["T_A_r1"]["G0-L (i) wall_s (serial)"] = (J(g0f)["wall_s"], src(g0f, "wall_s"))
res["references"] = {t: {k: {"value": a, "source": b} for k, (a, b) in v.items()} for t, v in ref.items()}
rv = lambda t, k: ref[t][k][0]


def load_run(arm, t, rate, seed):
    if rate == "0":
        name, suf, sfile = f"E3{arm}_{t}_0", BASE + ROB, f"{SC}/E3{arm}_{t}_0.json"
    else:
        suf = BASE + f"_mis{rate}_s{seed}" + (ROB if arm == "b" else "")
        name, sfile = f"E3{arm}_{t}_{rate}_s{seed}", f"{SC}/E3{arm}_{t}_{rate}_s{seed}.json"
    s = J(sfile)["tracks"]
    v = {}
    for tr in ("lc live", "lc hindsight"):
        assert len(s[tr]["per_lap_rmse_m"]) == 5, (name, tr)
        v[f"{tr} rmse_m"] = (s[tr]["rmse_m"], src(sfile, f"tracks.{tr}.rmse_m"))
        v[f"{tr} max_m"] = (s[tr]["max_m"], src(sfile, f"tracks.{tr}.max_m"))
        for i in range(5):
            v[f"{tr} lap{i+1}_m"] = (s[tr]["per_lap_rmse_m"][i], src(sfile, f"tracks.{tr}.per_lap_rmse_m[{i}]"))
    stf = f"{T1}/{t}/lc_fgo_lc{suf}/stats.json"
    x = J(stf); x.pop("landmarks_final", None)
    t1 = x["tier1"]; mis = t1["mislabel"]
    cov = {k: x.get(k) for k in ("t_anchor", "keyframes", "landmarks", "landmark_factors", "raw_detections", "central",
                                 "keyframe_failures", "step_median_ms", "step_p99_ms", "wall_s", "hindsight_polish_s")}
    cov["stats"] = stf
    cov["landmarks_first_sighting_mislabelled"] = t1["landmarks_first_sighting_mislabelled"]
    cov["tag_robust"] = t1["tag_robust"]; cov["commit"] = t1["commit"]; cov["src_dirty"] = t1["src_dirty"]
    cov["tag_ids"] = t1["tag_ids"]; cov["argv"] = t1["argv"]
    ta = x["t_anchor"]
    if mis is not None:
        ev = mis["events_t_true_new"]
        cov["mislabel"] = {k: mis[k] for k in ("rate", "seed", "valid_ids", "gauge", "n_calls", "n_eligible_non_gauge",
                                               "n_mislabelled")}
        cov["mislabel"]["rate_among_eligible"] = mis["n_mislabelled"] / mis["n_eligible_non_gauge"]
        cov["mislabel"]["effective_overall_rate"] = mis["n_mislabelled"] / mis["n_calls"]
        cov["mislabel"]["n_injected_in_[t_anchor,t_anchor+245] (DESCRIPTIVE)"] = sum(
            1 for e in ev if ta is not None and ta <= e[0] <= ta + 245.0)
        cov["mislabel"]["gauge never true id or replacement"] = all(e[1] != 0 and e[2] != 0 for e in ev)
        cov["mislabel"]["replacement != true and in 1..7"] = all(e[2] != e[1] and 1 <= e[2] <= 7 for e in ev)
        cov["mislabel"]["n_events == n_mislabelled"] = len(ev) == mis["n_mislabelled"]
        events = [tuple(e) for e in ev]
    else:
        cov["mislabel"] = None; events = []
    gate = ta == rv(t, "t_anchor_s")
    job = "e" + name[1:]
    stj = f"{STS}/{job}.json"; sj = J(stj)
    assert sj["run_dir"] == f"{T1}/{t}/lc_fgo_lc{suf}", (name, sj["run_dir"])
    assert sj["keyframe_failures"] == x["keyframe_failures"], (name, "status json stale")
    stat = {"status": sj["status"], "diverged": sj["status"] == "FAILED-ESTIMATOR", "source": stj,
            "keyframe_failures": sj["keyframe_failures"], "keyframes_ok": sj["keyframes_ok"],
            "failure_fraction (inflated: no recovery after a throw)": sj["failure_fraction"],
            "first_exception_t_s": sj["first_failure_t_s"],
            "live divergence onset t_s (headline; |x| or |y| > 10 m or non-finite)": sj[ONSET],
            "exception_counts_in_log": sj["exception_counts_in_log"], "nonfinite": sj["nonfinite"]}
    return {"name": name, "arm": arm, "flight": t, "rate": rate, "seed": seed, "score": sfile,
            "values": {k: {"value": a, "source": b} for k, (a, b) in v.items()}, "covariates": cov,
            "gate t_anchor == stored": gate, "run_status": stat}, events


runs, events = {}, {}
for arm in ("a", "b"):
    for t in FL:
        keys = [("0", None)] if arm == "b" else []
        keys += [(p, s) for p in RATES for s in SEEDS]
        for p, s in keys:
            d, ev = load_run(arm, t, p, s)
            runs[d["name"]] = d; events[(arm, t, p, s)] = ev
res["runs"] = runs
val = lambda n, k: runs[n]["values"][k]["value"]
ra = lambda t, p, s: f"E3a_{t}_{p}_s{s}"
rb = lambda t, p, s: f"E3b_{t}_{p}_s{s}"


div = lambda n: runs[n]["run_status"]["diverged"]


def div_summary(names):
    """'k of 3 runs diverged' per flight (and in total) over the runs a criterion needs, with divergence times."""
    out = {}
    for t in FL:
        nt = [n for n in names if runs[n]["flight"] == t]
        d = [n for n in nt if div(n)]
        arms = sorted({runs[n]["arm"] for n in nt})
        txt = "; ".join(f"arm ({am}): {sum(1 for n in nt if runs[n]['arm'] == am and div(n))} of "
                        f"{sum(1 for n in nt if runs[n]['arm'] == am)} runs diverged" for am in arms) if len(arms) > 1 \
            else f"{len(d)} of {len(nt)} runs diverged"
        out[t] = {"text": txt,
                  "diverged": {n: {"live divergence onset t_s (headline)": runs[n]["run_status"][
                      "live divergence onset t_s (headline; |x| or |y| > 10 m or non-finite)"],
                      "first_exception_t_s": runs[n]["run_status"]["first_exception_t_s"],
                      "failure_fraction (inflated)": runs[n]["run_status"]["failure_fraction (inflated: no recovery after a throw)"]}
                      for n in d}}
    k = sum(1 for n in names if div(n))
    out["total"] = f"{k} of {len(names)} runs diverged"
    return out


def verdict(names, test, needs=lambda n: [n]):
    """Per run: None if any needed run failed its gate (-> NOT MET, §0.5); False if any needed run diverged
    (ruling R2: not satisfying, -> FAIL); else the criterion. The test is never evaluated on a diverged run."""
    per, why = {}, {}
    for n in names:
        nd = needs(n)
        if not all(runs[m]["gate t_anchor == stored"] for m in nd):
            per[n] = None; why[n] = "gate failed (t_anchor != stored)"
        elif any(div(m) for m in nd):
            per[n] = False; why[n] = "diverged: " + ", ".join(m for m in nd if div(m))
        else:
            per[n] = bool(test(n))
    if any(v is None for v in per.values()):
        vd = "NOT MET"
    else:
        vd = "PASS" if all(per.values()) else "FAIL"
    allneed = sorted({m for n in names for m in needs(n)})
    return {"per_run": per, "count": f"{sum(1 for v in per.values() if v)}/{len(per)}", "verdict": vd,
            "not satisfied because": why, "divergence": div_summary(allneed)}


r1 = [ra(t, "0.01", s) for t in FL for s in SEEDS]
r5 = [ra(t, "0.05", s) for t in FL for s in SEEDS]
fl = lambda n: runs[n]["flight"]
H1 = lambda n: val(n, "lc live rmse_m") < rv(fl(n), "nolc live rmse_m")
H2 = lambda n: val(n, "lc hindsight rmse_m") < rv(fl(n), "nolc hindsight rmse_m")
H3 = lambda n: val(n, "lc live lap5_m") <= 1.5 * val(n, "lc live lap1_m")
ca = res["criteria_a"]
ca["H-E3.1 (PRIMARY) 1%: LC live < stored no-LC live"] = verdict(r1, H1)
ca["H-E3.2 1%: LC hindsight < stored no-LC hindsight"] = verdict(r1, H2)
ca["H-E3.3 1%: LC live lap5 <= 1.5 x lap1"] = verdict(r1, H3)
ca["P-E3.4 1%: LC live <= 2 x stored clean LC live (x2: judgement, not derived from data)"] = verdict(
    r1, lambda n: val(n, "lc live rmse_m") <= 2.0 * rv(fl(n), "clean lc live rmse_m"))
ca["P-E3.5a 5%: H-E3.1 criterion"] = verdict(r5, H1)
ca["P-E3.5b 5%: H-E3.2 criterion"] = verdict(r5, H2)
ca["P-E3.5c 5%: H-E3.3 criterion"] = verdict(r5, H3)
# P-E3.6: per flight, seed-mean LC live: clean <= 1% <= 5%
p6 = {}
for t in FL:
    m1 = m5 = None
    if not any(div(ra(t, p, s)) for p in RATES for s in SEEDS):
        m1 = statistics.fmean(val(ra(t, "0.01", s), "lc live rmse_m") for s in SEEDS)
        m5 = statistics.fmean(val(ra(t, "0.05", s), "lc live rmse_m") for s in SEEDS)
    c = rv(t, "clean lc live rmse_m")
    need6 = [ra(t, p, s) for p in RATES for s in SEEDS]
    gates = all(runs[n]["gate t_anchor == stored"] for n in need6)
    dv = [n for n in need6 if div(n)]
    if not gates:
        p6[t] = {"clean": c, "seed-mean 1%": None, "seed-mean 5%": None, "pass": None, "why": "gate failed"}
    elif dv:   # ruling R2: not satisfying; seed means not computed from truncated / non-finite RMSEs
        p6[t] = {"clean": c, "seed-mean 1%": None, "seed-mean 5%": None, "pass": False, "why": "diverged: " + ", ".join(dv)}
    else:
        p6[t] = {"clean": c, "seed-mean 1%": m1, "seed-mean 5%": m5, "clean<=1%": c <= m1, "1%<=5%": m1 <= m5,
                 "pass": c <= m1 and m1 <= m5}
pv = [v["pass"] for v in p6.values()]
ca["P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight"] = {
    "per_flight": p6, "count": f"{sum(1 for v in pv if v)}/3",
    "verdict": "NOT MET" if None in pv else ("PASS" if all(pv) else "FAIL"),
    "divergence": div_summary([ra(t, p, s) for t in FL for p in RATES for s in SEEDS])}

# descriptive per-run ratios
for n, d in runs.items():
    t = d["flight"]
    d["ratios not meaningful (a needed run diverged)"] = div(n) or (d["arm"] == "b" and d["rate"] != "0"
                                                                   and div(ra(t, d["rate"], d["seed"])))
    d["ratio lc live lap5/lap1"] = val(n, "lc live lap5_m") / val(n, "lc live lap1_m")
    d["lc live / stored clean lc live"] = val(n, "lc live rmse_m") / rv(t, "clean lc live rmse_m")
    d["lc live / stored nolc live"] = val(n, "lc live rmse_m") / rv(t, "nolc live rmse_m")
    d["lc hindsight / stored nolc hindsight"] = val(n, "lc hindsight rmse_m") / rv(t, "nolc hindsight rmse_m")
    d["lc hindsight / stored clean lc hindsight"] = val(n, "lc hindsight rmse_m") / rv(t, "clean lc hindsight rmse_m")
    if d["arm"] == "b" and d["rate"] != "0":
        a_ = ra(t, d["rate"], d["seed"])
        d["b live / a live"] = val(n, "lc live rmse_m") / val(a_, "lc live rmse_m")
        d["b hindsight / a hindsight (DESCRIPTIVE)"] = val(n, "lc hindsight rmse_m") / val(a_, "lc hindsight rmse_m")

# ---- arm (b) ----
cb = res["criteria_b"]
for p in RATES:
    names = [rb(t, p, s) for t in FL for s in SEEDS]
    # an arm (b) criterion also needs its matched arm (a) run (gate; and, literally per ruling R2, not diverged)
    v = verdict(names, lambda n: val(n, "lc live rmse_m") <= 1.10 * val(ra(fl(n), runs[n]["rate"], runs[n]["seed"]),
                                                                          "lc live rmse_m"),
                needs=lambda n: [n, ra(fl(n), runs[n]["rate"], runs[n]["seed"])])
    cb[f"P-E3b.1 {p}: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data)"] = v
cb["P-E3b.2 rate 0: |robust LC live / stored clean LC live - 1| <= 0.10 (±10%: judgement, not derived from data)"] = verdict(
    [f"E3b_{t}_0" for t in FL], lambda n: abs(val(n, "lc live rmse_m") / rv(fl(n), "clean lc live rmse_m") - 1.0) <= 0.10)

# ---- effective rates (arm a; arm b uses the identical stream, checked below) ----
for arm in ("a", "b"):
    for p in RATES:
        names = [f"E3{arm}_{t}_{p}_s{s}" for t in FL for s in SEEDS]
        M = [runs[n]["covariates"]["mislabel"] for n in names]
        res["effective_rates"][f"{arm} {p}"] = {
            "per_run": {n: {k: m[k] for k in ("n_mislabelled", "n_eligible_non_gauge", "n_calls", "rate_among_eligible",
                                              "effective_overall_rate",
                                              "n_injected_in_[t_anchor,t_anchor+245] (DESCRIPTIVE)")}
                        for n, m in zip(names, M)},
            "pooled_rate_among_eligible": sum(m["n_mislabelled"] for m in M) / sum(m["n_eligible_non_gauge"] for m in M),
            "pooled_effective_overall_rate": sum(m["n_mislabelled"] for m in M) / sum(m["n_calls"] for m in M),
            "sum_n_mislabelled": sum(m["n_mislabelled"] for m in M)}

# ---- invariants ----
inv = res["invariants"]
allr = list(runs.values())
inv["t_anchor == stored (all runs)"] = {"count": f"{sum(r['gate t_anchor == stored'] for r in allr)}/{len(allr)}",
                                        "failing": [r["name"] for r in allr if not r["gate t_anchor == stored"]]}
inv["landmarks == 8 (all runs)"] = {"count": f"{sum(r['covariates']['landmarks'] == 8 for r in allr)}/{len(allr)}",
                                    "failing": [r["name"] for r in allr if r["covariates"]["landmarks"] != 8]}
mr = [r for r in allr if r["covariates"]["mislabel"] is not None]
for k in ("gauge never true id or replacement", "replacement != true and in 1..7", "n_events == n_mislabelled"):
    inv[k] = {"count": f"{sum(r['covariates']['mislabel'][k] for r in mr)}/{len(mr)}",
              "failing": [r["name"] for r in mr if not r["covariates"]["mislabel"][k]]}
inv["controls have no mislabel"] = all(runs[f"E3b_{t}_0"]["covariates"]["mislabel"] is None for t in FL)
nest = {}
for arm in ("a", "b"):
    for t in FL:
        for s in SEEDS:
            e1, e5 = set(events[(arm, t, "0.01", s)]), set(events[(arm, t, "0.05", s)])
            nest[f"{arm} {t} s{s}"] = e1 <= e5
inv["1% events nested in 5% events (same t, true, new)"] = {"count": f"{sum(nest.values())}/{len(nest)}", "per": nest}
same = {f"{t} {p} s{s}": events[("a", t, p, s)] == events[("b", t, p, s)] for t in FL for p in RATES for s in SEEDS}
inv["arm (b) events == arm (a) events (same flight, rate, seed)"] = {"count": f"{sum(same.values())}/{len(same)}"}
inv["robust flag: arm a None, arm b cauchy:2.385"] = all(
    (r["covariates"]["tag_robust"] is None) == (r["arm"] == "a") and (r["arm"] == "a" or r["covariates"]["tag_robust"] == "cauchy:2.385")
    for r in allr)
inv["src_dirty empty (all runs)"] = all(r["covariates"]["src_dirty"] == "" for r in allr)
inv["commits"] = sorted({r["covariates"]["commit"] for r in allr})
inv["tag_ids == 0..7 (all runs)"] = all(r["covariates"]["tag_ids"] == list(range(8)) for r in allr)
inv["keyframe_failures (all runs)"] = {r["name"]: r["covariates"]["keyframe_failures"] for r in allr}
inv["landmarks_first_sighting_mislabelled (all runs)"] = {r["name"]: r["covariates"]["landmarks_first_sighting_mislabelled"]
                                                          for r in allr}
inv["landmark_factors (all runs)"] = {r["name"]: r["covariates"]["landmark_factors"] for r in allr}

# ---- runtime ratio (b)/(a): DESCRIPTIVE ONLY ----
rt = {}
for p in RATES:
    per = {}
    for t in FL:
        for s in SEEDS:
            a_, b_ = runs[ra(t, p, s)]["covariates"], runs[rb(t, p, s)]["covariates"]
            dd = div(ra(t, p, s)) or div(rb(t, p, s))
            per[rb(t, p, s)] = {"b wall_s": b_["wall_s"], "a wall_s": a_["wall_s"], "ratio": b_["wall_s"] / a_["wall_s"],
                                "b hindsight_polish_s": b_["hindsight_polish_s"], "a hindsight_polish_s": a_["hindsight_polish_s"],
                                "diverged (a or b): wall not comparable": dd,
                                "label": "NOT LIKE FOR LIKE: " + ("arm (a) serial, arm (b) in the width<=4 parallel batch"
                                         if t == "T_A_r1" else "both in the width<=4 parallel batch, varying co-load")}
    rs = [v["ratio"] for v in per.values() if not v["diverged (a or b): wall not comparable"]]
    rt[p] = {"per_run": per, "n_pairs_neither_diverged": len(rs),
             "median": statistics.median(rs) if rs else None, "min": min(rs) if rs else None, "max": max(rs) if rs else None,
             "label": "DESCRIPTIVE, NOT LIKE FOR LIKE (parallel batch); median/min/max over pairs where neither run diverged"}
ctl = {}
PA = f"{T1}/T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7/stats.json"   # extra timing-only arm (a) 0% run (ruling R3)
pa = J(PA); assert pa["tier1"]["mislabel"] is None and pa["tier1"]["tag_robust"] is None and pa["keyframe_failures"] == 0
for t in FL:
    b_ = runs[f"E3b_{t}_0"]["covariates"]
    if t == "T_A_r2":
        ctl[t] = {"b wall_s": b_["wall_s"], "reference": "fresh serial arm (a) 0% run e3a_T_A_r2_0 (ruling R3): HEADLINE, like for like",
                  "ref wall_s": pa["wall_s"], "ref source": src(PA, "wall_s"), "ratio": b_["wall_s"] / pa["wall_s"],
                  "b hindsight_polish_s": b_["hindsight_polish_s"], "a hindsight_polish_s": pa["hindsight_polish_s"],
                  "a step_median_ms": pa["step_median_ms"], "b step_median_ms": b_["step_median_ms"]}
    elif t == "T_A_r1":
        ctl[t] = {"b wall_s": b_["wall_s"], "reference": "G0-L (i) wall_s (serial); arm (b) ran in the parallel batch: NOT LIKE FOR LIKE",
                  "ref wall_s": rv(t, "G0-L (i) wall_s (serial)"), "ratio": b_["wall_s"] / rv(t, "G0-L (i) wall_s (serial)"),
                  "b hindsight_polish_s": b_["hindsight_polish_s"]}
    else:
        ctl[t] = {"b wall_s": b_["wall_s"], "reference": "stored clean wall_s (6 parallel): NOT LIKE FOR LIKE",
                  "ref wall_s": rv(t, "stored clean wall_s (6 parallel)"),
                  "ratio": b_["wall_s"] / rv(t, "stored clean wall_s (6 parallel)"),
                  "b hindsight_polish_s": b_["hindsight_polish_s"]}
rt["0"] = ctl
res["runtime_descriptive"] = rt
res["divergence"] = {"arm a": div_summary([ra(t, p, s) for t in FL for p in RATES for s in SEEDS]),
                     "arm b": div_summary([n for n in runs if runs[n]["arm"] == "b"]),
                     "per_run_status": {n: r["run_status"] for n, r in runs.items()}}

json.dump(res, open(OUT, "w"), indent=1)
for k, v in list(ca.items()) + list(cb.items()):
    print(f"{v['verdict']:8s} {v['count']:5s} {k}")
for k, v in res["effective_rates"].items():
    print("rates", k, round(v["pooled_rate_among_eligible"], 5), round(v["pooled_effective_overall_rate"], 5), v["sum_n_mislabelled"])
for k, v in inv.items():
    if not isinstance(v, dict) or "count" in v:
        print("inv", k, v if not isinstance(v, dict) else (v["count"], v.get("failing")))
print("runtime", {p: (v["median"], v["min"], v["max"], v["n_pairs_neither_diverged"]) for p, v in rt.items() if p != "0"},
      {t: round(v["ratio"], 3) for t, v in ctl.items()})
for k, v in list(ca.items()) + list(cb.items()):
    print("diverged", k[:12], v["divergence"]["total"], {t: v["divergence"][t]["text"] for t in FL})
