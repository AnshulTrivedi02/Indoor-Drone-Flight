#!/usr/bin/env python3
"""Stage 2f (E4): verdicts, gain fractions and the LM-cap convergence check, from finished runs only (read-only on run
outputs; writes docs/thesis/tier1/scores/E4_verdicts.json). Pre-registration §3; decisions D12-D15.
Inputs per run: ~/thesis_data/tier1/<trial>/room_fgo_w<W>[_lm10]/{stats.json, fgo_live.tum}, stage2f/status/<job>.json,
scores/E4_<trial>_w<W>[_lm10].json (tag_score.py), and the stored eval/results/expT/<trial>.json (batch B_i).
Usage: e4_verdicts.py [--out FILE]   (default docs/thesis/tier1/scores/E4_verdicts.json; refuses to overwrite)"""
import json, math, os, statistics as stt, sys
import numpy as np
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"; T1 = "/home/makerspace/thesis_data/tier1"
S = f"{T1}/stage2f"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else f"{SC}/E4_verdicts.json"
if os.path.exists(OUT):
    sys.exit(f"refusing to overwrite {OUT}")
FL = [f"T_{c}_r{r}" for c in "ABCD" for r in (1, 2, 3)]
WS = [0.25, 0.5, 1.0, 2.0, 5.0]; CONV = ["T_A_r1", "T_D_r1"]; BUDGET = 33.0; RMS_ACC = 0.029
J = lambda p: json.load(open(p))
g = lambda w: f"{w:g}"
LIVE, BATCH = "FGO live", "FGO hindsight (whole-flight batch)"


def run(t, w, lm=False):
    """dict for one run, or None if it did not complete (no stats.json / no status / no score)."""
    suf = "_lm10" if lm else ""
    d = f"{T1}/{t}/room_fgo_w{g(w)}{suf}"; job = f"e4_{t}_w{g(w)}{suf}"
    sp, stp, scp = f"{d}/stats.json", f"{S}/status/{job}.json", f"{SC}/E4_{t}_w{g(w)}{suf}.json"
    if not (os.path.exists(sp) and os.path.exists(stp) and os.path.exists(scp)):
        return None
    st, ss, sc = J(sp), J(stp), J(scp)
    assert st["window_s"] == w and st["lm_iters"] == (10 if lm else 2), (job, st["window_s"], st["lm_iters"])
    assert sc["tier1"]["fgo_dir"] == d, (job, sc["tier1"]["fgo_dir"])
    return {"job": job, "dir": d, "status": ss["status"], "keyframe_failures": st["keyframe_failures"],
            "first_failure_t_s": ss["first_failure_t_s"],
            "excursion_onset_t_s": ss["live_excursion_onset_t_s (|x| or |y| > 10 m, or non-finite; DESCRIPTIVE)"],
            "commit": st["tier1"]["commit"], "src_dirty": st["tier1"]["src_dirty"],
            "step_median_ms": st["step_median_ms"], "step_p95_ms": st["tier1"]["step_p95_ms"],
            "step_median_ms_after_anchor": st["tier1"]["step_median_ms_after_anchor"],
            "step_p95_ms_after_anchor": st["tier1"]["step_p95_ms_after_anchor"], "n_steps": st["tier1"]["n_steps"],
            "t_anchor": st["t_anchor"], "n_tag_factors": st["n_tag_factors"],
            "live": sc["tracks"][LIVE]["horiz_err_m"], "live_yaw_deg": sc["tracks"][LIVE]["yaw_err_deg"],
            "lap_window_s": sc["window_s"]}


runs = {(t, w, lm): run(t, w, lm) for t in FL for w in WS for lm in (False,)}
runs.update({(t, w, True): run(t, w, True) for t in CONV for w in WS})
B = {t: J(f"{R}/eval/results/expT/{t}.json")["tracks"][BATCH]["horiz_err_m"]["rmse"] for t in FL}
L025_stored = {t: J(f"{R}/eval/results/expT/{t}.json")["tracks"][LIVE]["horiz_err_m"]["rmse"] for t in FL}
ok = lambda r: r is not None and r["status"] == "OK"


def verdict(n_ok, n_need, missing, failed_runs, k_pass):
    """§0.5: NOT RUN if a needed run is missing (not finished); FAILED-ESTIMATOR runs count as not satisfying (D14)."""
    if missing:
        return "NOT RUN"
    return "PASS" if n_ok >= k_pass else "FAIL"


out = {"label": "extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22)",
       "runs": {r["job"]: r for r in runs.values() if r is not None},
       "missing_runs": [f"e4_{t}_w{g(w)}{'_lm10' if lm else ''}" for (t, w, lm), r in runs.items() if r is None],
       "stored": {"B_i (expT FGO batch rmse)": B, "L_i(0.25) stored (expT FGO live rmse)": L025_stored}}
# G-E4 consistency: the E4 0.25 s live RMSE equals the stored one
out["L025_equals_stored"] = {t: (runs[(t, 0.25, False)] is not None and runs[(t, 0.25, False)]["live"]["rmse"] == L025_stored[t]) for t in FL}

# ---- P-E4.1: after-anchor median strictly increasing with W, 12/12 ----
p1 = {}
for t in FL:
    rr = [runs[(t, w, False)] for w in WS]
    if any(r is None for r in rr):
        p1[t] = {"satisfied": None, "reason": "run missing"}; continue
    m = [r["step_median_ms_after_anchor"] for r in rr]
    p1[t] = {"medians_after_anchor_ms": m, "strictly_increasing": all(a < b for a, b in zip(m, m[1:])),
             "all_runs_ok": all(ok(r) for r in rr)}
    p1[t]["satisfied"] = p1[t]["strictly_increasing"] and p1[t]["all_runs_ok"]
miss1 = [t for t in FL if p1[t]["satisfied"] is None]
n1 = sum(1 for t in FL if p1[t]["satisfied"])
out["P-E4.1"] = {"criterion": "median step time (after the anchor) increases strictly with W: 0.25 < 0.5 < 1 < 2 < 5 s, 12/12 flights",
                 "per_flight": p1, "count": f"{n1}/12", "verdict": verdict(n1, 12, miss1, None, 12)}

# ---- P-E4.2: <= 33 ms at 0.25 s and > 33 ms at W >= 1 s, 12/12 at each; both median readings (D13); 0.5 s descriptive ----
p2 = {}; miss2 = []
for w in WS:
    rows = {}
    for t in FL:
        r = runs[(t, w, False)]
        if r is None:
            rows[t] = None; (miss2.append(f"{t} w{g(w)}") if w != 0.5 else None); continue
        a, b = r["step_median_ms"], r["step_median_ms_after_anchor"]
        sat = (a <= BUDGET and b <= BUDGET) if w == 0.25 else (a > BUDGET and b > BUDGET)
        rows[t] = {"median_all_ms": a, "median_after_anchor_ms": b, "satisfied": bool(sat and ok(r)),
                   "readings_disagree": (a <= BUDGET) != (b <= BUDGET), "run_ok": ok(r)}
    n = sum(1 for v in rows.values() if v and v["satisfied"])
    p2[g(w)] = {"per_flight": rows, "count": f"{n}/12", "role": "DESCRIPTIVE (on the budget)" if w == 0.5 else
                ("<= 33 ms" if w == 0.25 else "> 33 ms")}
need = [g(w) for w in WS if w != 0.5]
allpass = all(p2[k]["count"] == "12/12" for k in need)
out["P-E4.2"] = {"criterion": "median <= 33 ms at W = 0.25 s and > 33 ms at W >= 1 s, 12/12 at each (both median readings, D13)",
                 "per_window": p2, "verdict": "NOT RUN" if miss2 else ("PASS" if allpass else "FAIL"),
                 "counts": {k: p2[k]["count"] for k in need}}

# ---- convergence (cap 2 vs cap 10), D12 ----
def load_tum(p):
    rows = {}
    for ln in open(p):
        f = ln.split(); rows[f[0]] = np.array([float(x) for x in f[1:4]])
    return rows


conv = {}
for t in CONV:
    for w in WS:
        a, b = runs[(t, w, False)], runs[(t, w, True)]
        if a is None or b is None:
            conv[f"{t} w{g(w)}"] = None; continue
        A, Bt = load_tum(f"{a['dir']}/fgo_live.tum"), load_tum(f"{b['dir']}/fgo_live.tum")
        ks = sorted(set(A) & set(Bt), key=float)
        w0, w1 = a["lap_window_s"]
        d = np.array([A[k] - Bt[k] for k in ks]); tt = np.array([float(k) for k in ks]); inw = (tt >= w0) & (tt <= w1)
        h, d3 = np.hypot(d[:, 0], d[:, 1]), np.linalg.norm(d, axis=1)
        rd = {"rows_cap2": len(A), "rows_cap10": len(Bt), "rows_paired": len(ks), "unmatched": len(A) + len(Bt) - 2 * len(ks)}
        for nm, x, msk in (("horiz_all", h, slice(None)), ("3d_all", d3, slice(None)), ("horiz_lap", h, inw), ("3d_lap", d3, inw)):
            rd[nm] = {"max_m": float(np.max(x[msk])), "rms_m": float(np.sqrt(np.mean(x[msk] ** 2)))}
        rd["max_rms_reading_m"] = max(rd[k]["rms_m"] for k in ("horiz_all", "3d_all", "horiz_lap", "3d_lap"))
        rd["NOT_CONVERGED"] = rd["max_rms_reading_m"] > RMS_ACC
        rd["live_rmse_cap2_m"], rd["live_rmse_cap10_m"] = a["live"]["rmse"], b["live"]["rmse"]
        rd["rmse_diff_cap10_minus_cap2_m"] = b["live"]["rmse"] - a["live"]["rmse"]
        rd["cap10_status"] = b["status"]
        conv[f"{t} w{g(w)}"] = rd
out["convergence"] = {"threshold_rms_m": RMS_ACC, "rule": "D12: flag iff any of the four RMS readings > 0.029 m", "per_run": conv}

# ---- H-E4.3: L(5) < L(0.25), >= 10/12 ----
h3 = {}
for t in FL:
    a, b = runs[(t, 0.25, False)], runs[(t, 5.0, False)]
    if a is None or b is None:
        h3[t] = {"satisfied": None}; continue
    h3[t] = {"L0.25_m": a["live"]["rmse"], "L5_m": b["live"]["rmse"], "lower_at_5": b["live"]["rmse"] < a["live"]["rmse"],
             "runs_ok": ok(a) and ok(b)}
    h3[t]["satisfied"] = h3[t]["lower_at_5"] and h3[t]["runs_ok"]
miss3 = [t for t in FL if h3[t]["satisfied"] is None]
n3 = sum(1 for t in FL if h3[t]["satisfied"])
qual = [k for k in ("T_A_r1 w5", "T_D_r1 w5") if conv.get(k) and conv[k]["NOT_CONVERGED"]]
out["H-E4.3"] = {"criterion": "live RMSE at W = 5 s < live RMSE at W = 0.25 s, same flight, >= 10/12 (>= 10/12: judgement, not derived from data)",
                 "per_flight": h3, "count": f"{n3}/12", "verdict": verdict(n3, 12, miss3, None, 10),
                 "qualifier": ("cap 2 not converged at 5 s (" + ", ".join(qual) + ")") if qual else None}

# ---- gain fraction (DESCRIPTIVE) ----
gf = {}
for w in WS[1:]:
    f = {}; num = {}; den = {}
    for t in FL:
        a, b = runs[(t, 0.25, False)], runs[(t, w, False)]
        if a is None or b is None or not ok(b):
            continue
        num[t] = a["live"]["rmse"] - b["live"]["rmse"]; den[t] = a["live"]["rmse"] - B[t]; f[t] = num[t] / den[t]
    pooled = (sum(num.values()) / sum(den.values())) if num else None
    per_c = {c: (sum(num[t] for t in num if t[2] == c) / sum(den[t] for t in den if t[2] == c))
             if all(f"T_{c}_r{r}" in num for r in (1, 2, 3)) else None for c in "ABCD"}
    gf[g(w)] = {"f_i": f, "F_pooled": pooled, "F_per_condition": per_c, "median_f_i": stt.median(f.values()) if f else None,
                "n_flights": len(f), "excluded (missing or FAILED-ESTIMATOR)": [t for t in FL if t not in f]}
gflm = {}
for t in CONV:
    for w in WS:
        a, b = runs[(t, 0.25, False)], runs[(t, w, True)]
        if a is None or b is None or not ok(b):
            gflm[f"{t} w{g(w)}"] = None; continue
        gflm[f"{t} w{g(w)}"] = (a["live"]["rmse"] - b["live"]["rmse"]) / (a["live"]["rmse"] - B[t])
out["gain_fraction"] = {"definition": "f_i(W) = (L_i(0.25) - L_i(W)) / (L_i(0.25) - B_i); F(W) pooled sums; DESCRIPTIVE",
                        "cap2": gf, "lm10 rows (L_i(0.25) = cap-2 0.25 s run, D15)": gflm}
# ---- timing summary (DIAGNOSTIC) ----
tim = {}
for w in WS:
    rr = [runs[(t, w, False)] for t in FL if runs[(t, w, False)] is not None]
    if rr:
        tim[g(w)] = {k: [min(r[k] for r in rr), max(r[k] for r in rr)] for k in
                     ("step_median_ms", "step_median_ms_after_anchor", "step_p95_ms", "step_p95_ms_after_anchor")}
        tim[g(w)]["n"] = len(rr)
out["timing_ranges_ms (DIAGNOSTIC)"] = tim
out["commits"] = sorted({r["commit"] for r in out["runs"].values() if not r["job"].endswith("_w0.25")})
out["src_dirty_nonempty"] = [r["job"] for r in out["runs"].values() if r["src_dirty"]]
json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps({k: out[k]["verdict"] for k in ("P-E4.1", "P-E4.2", "H-E4.3")}),
      out["P-E4.1"]["count"], out["P-E4.2"]["counts"], out["H-E4.3"]["count"], out["H-E4.3"]["qualifier"])
print("missing:", len(out["missing_runs"]))
