#!/usr/bin/env python3
"""EXPLORATORY attribution ablation: build the result tables and verdicts from the score jsons (read-only analysis).

Inputs (read only):
  ~/thesis_data/ablation/scores/<rung>_<arm>.json   (score_ablation.py output; r6s_heading.json = stored Cauchy)
  ~/thesis_data/ablation/{timing.tsv,status.tsv}    (driver records)
  eval/results/phase4_<ds>_arms.json                 (stored UKF / EKF3 / thesis-FGO rows)
Outputs: ~/thesis_data/ablation/scores/ablation_results.json (every unrounded value used) and
         ~/thesis_data/ablation/tables.md (the tables, each value rounded ONCE).
Rules (docs/thesis/ablation/preregistration.md §6-§8; decisions_log D35, D36, D44): scored on unrounded values;
a FAILED-ESTIMATOR run (rc != 0, keyframe failure, non-finite, missing) counts against the prediction using it.
Usage: python3 docs/thesis/ablation/ablation_results.py
"""
import json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
A = os.path.expanduser("~/thesis_data/ablation")
BAGS = [f"{ds}_tex_r{r}" for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)]
FWDC = BAGS[:3]
LADDER = ["r1", "r2", "r3", "r4", "r5"]
NAMES = {"r0": "r0 0.25 s cap 2", "r1": "r1 1 kf cap 1", "r2": "r2 1 kf cap 2",
         "r3": "r3 1 kf cap 100 (convergence not confirmed)", "r4": "r4 1 s cap 2", "r5": "r5 2 s cap 2",
         "r6": "r6 Huber 0.25 s cap 2 (gate replaced)", "r7": "r7 Huber 1 kf cap 100 (gate replaced)",
         "r6s": "r6s stored Cauchy 2.385 0.25 s (gate replaced)"}
FOLDER = {"r0": "r0_w0.25_lm2", "r1": "r1_kf1_lm1", "r2": "r2_kf1_lm2", "r3": "r3_kf1_lm100", "r4": "r4_w1_lm2",
          "r5": "r5_w2_lm2", "r6": "r6_w0.25_lm2_huber", "r7": "r7_kf1_lm100_huber"}
ds = lambda t: t.split("_")[0]
m = lambda x: "—" if x is None else f"{x:.3f}".replace("-", "−")
r2 = lambda x: "—" if x is None else f"{x:.2f}".replace("-", "−")


def load():
    st = {d: json.load(open(f"{REPO}/eval/results/phase4_{d}_arms.json")) for d in ("fwdc", "fwdplainc")}
    sv = lambda t, k: st[ds(t)][t][k]["evo"]["ate_a_cruise"]["+0.00"]
    stored = {t: {"U_heading": sv(t, "UKF_heading"), "U_baseline": sv(t, "UKF_baseline"),
                  "F0_heading": sv(t, "FGO_heading"), "F0_baseline": sv(t, "FGO_baseline"),
                  "EKF3": st[ds(t)][t]["EKF3"]["ate_a_cruise"]["+0.00"]} for t in BAGS}
    sc = {}
    for f in os.listdir(f"{A}/scores"):
        mm = re.fullmatch(r"(r\ds?)_(heading|baseline)\.json", f)
        if mm:
            sc[(mm.group(1), mm.group(2))] = json.load(open(f"{A}/scores/{f}"))["trials"]
    # driver status: last line per job (the final attempt)
    status = {}
    if os.path.exists(f"{A}/status.tsv"):
        for ln in open(f"{A}/status.tsv"):
            p = ln.rstrip("\n").split("\t")
            if len(p) >= 8:
                status[p[0]] = {"rc": int(p[1][3:]), "kf_fail": int(p[2][8:]), "finite": p[3][7:], "rows": int(p[4][5:]),
                                "status": p[7]}
    timing = {}
    if os.path.exists(f"{A}/timing.tsv"):
        for ln in open(f"{A}/timing.tsv"):
            p = ln.rstrip("\n").split("\t")
            if len(p) == 9:
                timing[p[0]] = {"start": p[1], "end": p[2], "wall_s": None if p[3] == "-" else float(p[3]),
                                "rc": p[4], "try": p[5], "outcome": p[8]}
    return stored, sc, status, timing


def main():
    stored, sc, status, timing = load()

    def F(rung, t, arm):
        """(value or None, ok flag, status string)."""
        r = sc.get((rung, arm), {}).get(t)
        if rung == "r6s":
            ok = r is not None and r.get("status") == "OK"
            return (r["ate_a_cruise_m"] if r and "ate_a_cruise_m" in r else None), ok, (r or {}).get("status", "MISSING")
        j = f"{rung}__{t}__{arm}"
        s = status.get(j, {}).get("status", "NOT RUN")
        ok = r is not None and r.get("status") == "OK" and s == "OK" and timing.get(j, {}).get("outcome") == "completed"
        return (r["ate_a_cruise_m"] if r and "ate_a_cruise_m" in r else None), ok, (s if r else "MISSING")

    band = {(d, a): max(stored[f"{d}_tex_r{i}"][f"F0_{a}"] for i in (1, 2, 3)) - min(stored[f"{d}_tex_r{i}"][f"F0_{a}"] for i in (1, 2, 3))
            for d in ("fwdc", "fwdplainc") for a in ("heading", "baseline")}
    out = {"label": "EXPLORATORY", "band": {f"{d}.{a}": v for (d, a), v in band.items()}, "stored": stored,
           "runs": {}, "R": {}, "P1": {}, "P2": {}, "P3": {}, "interp": {}}
    for rung in ["r0"] + LADDER + ["r6", "r7", "r6s"]:
        for arm in ("heading", "baseline"):
            if rung in ("r6", "r7", "r6s") and arm == "baseline":
                continue
            for t in BAGS:
                v, ok, s = F(rung, t, arm)
                r = sc.get((rung, arm), {}).get(t, {})
                out["runs"][f"{rung}.{t}.{arm}"] = {"ate_a_cruise_m": v, "ok": ok, "status": s,
                                                    "step_ms": r.get("step_ms"), "fwd_counts": r.get("fwd_counts"),
                                                    "wall_s": timing.get(f"{rung}__{t}__{arm}", {}).get("wall_s")}
    run = lambda rung, t, arm: out["runs"][f"{rung}.{t}.{arm}"]
    # r0 equality with stored (gate part 2, re-checked here)
    out["r0_equal_stored"] = sum(run("r0", t, a)["ate_a_cruise_m"] == stored[t][f"F0_{a}"] for t in BAGS for a in ("heading", "baseline"))
    # R per bag
    for t in BAGS:
        gap = stored[t]["U_heading"] - stored[t]["F0_heading"]
        for rung in ["r0"] + LADDER + ["r6", "r7", "r6s"]:
            v = run(rung, t, "heading")["ate_a_cruise_m"]
            out["R"][f"{rung}.{t}"] = None if v is None else (stored[t]["U_heading"] - v) / gap
        out["R"][f"gap.{t}"] = gap
        out["R"][f"bandgap.{t}"] = band[(ds(t), "heading")] / gap
    # P1
    for rung in LADDER:
        rows = {}
        for t in BAGS:
            x = run(rung, t, "baseline"); d = None if x["ate_a_cruise_m"] is None else x["ate_a_cruise_m"] - stored[t]["F0_baseline"]
            within = x["ok"] and d is not None and abs(d) <= band[(ds(t), "baseline")]
            u = stored[t]["U_baseline"]
            flip = None if d is None else ((u - x["ate_a_cruise_m"]) > 0) != ((u - stored[t]["F0_baseline"]) > 0)
            rows[t] = {"delta_m": d, "within": within, "ok": x["ok"], "sign_flip": flip}
        n = sum(r["within"] for r in rows.values())
        out["P1"][rung] = {"bags": rows, "n_within": n, "verdict": "PASS" if n == 6 else "FAIL"}
    out["P1"]["overall"] = "PASS" if all(out["P1"][r]["verdict"] == "PASS" for r in LADDER) else "FAIL"
    # P2
    p2 = {t: {"R": out["R"][f"r3.{t}"], "ok": run("r3", t, "heading")["ok"]} for t in FWDC}
    for t in FWDC:
        p2[t]["pass"] = p2[t]["ok"] and p2[t]["R"] is not None and p2[t]["R"] >= 0.5
    n2 = sum(p2[t]["pass"] for t in FWDC)
    out["P2"] = {"bags": p2, "n_pass": n2, "verdict": "PASS" if n2 == 3 else "FAIL",
                 "fwdplainc_R_r3_descriptive": {t: out["R"][f"r3.{t}"] for t in BAGS[3:]}}
    # P3
    p3 = {}
    for t in BAGS:
        a, b, c = run("r6", t, "heading"), run("r0", t, "heading"), run("r7", t, "heading")
        d3 = run("r3", t, "heading")
        d6 = None if a["ate_a_cruise_m"] is None else a["ate_a_cruise_m"] - b["ate_a_cruise_m"]
        d7 = None if (c["ate_a_cruise_m"] is None or d3["ate_a_cruise_m"] is None) else c["ate_a_cruise_m"] - d3["ate_a_cruise_m"]
        bd = band[(ds(t), "heading")]
        p3[t] = {"d_r6_r0": d6, "r6_within": a["ok"] and d6 is not None and abs(d6) <= bd,
                 "d_r7_r3": d7, "r7_within": c["ok"] and d3["ok"] and d7 is not None and abs(d7) <= bd}
    n6, n7 = sum(p3[t]["r6_within"] for t in BAGS), sum(p3[t]["r7_within"] for t in BAGS)
    out["P3"] = {"bags": p3, "n_r6": n6, "n_r7": n7, "verdict": "PASS" if n6 == 6 and n7 == 6 else "FAIL"}
    # interpretation-table tests (fwdc, heading; D36, D44)
    it = {}
    for t in FWDC:
        bg = out["R"][f"bandgap.{t}"]; R = {k: out["R"][f"{k}.{t}"] for k in LADDER}
        it[t] = {"bandgap": bg, "thr": 1 - bg,
                 "r3_persists": R["r3"] is not None and R["r3"] >= 1 - bg,
                 "r4_within2": R["r4"] is not None and abs(R["r4"] - 1) <= bg,
                 "r5_within2": R["r5"] is not None and abs(R["r5"] - 1) <= bg,
                 "r4_ge1": R["r4"] is not None and R["r4"] >= 1 - bg, "r5_ge1": R["r5"] is not None and R["r5"] >= 1 - bg}
        bd = band[("fwdc", "heading")]
        fv = {k: run(k, t, "heading")["ate_a_cruise_m"] for k in ("r1", "r2", "r3")}
        it[t]["iter_pairs_gt_band"] = {f"{a}-{b}": (None if fv[a] is None or fv[b] is None else abs(fv[a] - fv[b]) > bd)
                                       for a, b in (("r1", "r2"), ("r1", "r3"), ("r2", "r3"))}
        it[t]["iter_pair_diff_m"] = {f"{a}-{b}": (None if fv[a] is None or fv[b] is None else fv[a] - fv[b])
                                     for a, b in (("r1", "r2"), ("r1", "r3"), ("r2", "r3"))}
    out["interp"] = it
    json.dump(out, open(f"{A}/scores/ablation_results.json", "w"), indent=1)

    # ---------- tables (rounded once) ----------
    L = []
    L.append("## T1. With heading: FGO evo -a (cruise), m (EXPLORATORY)\n")
    L.append("| bag | r0 | r1 | r2 | r3 | r4 | r5 | UKF (stored) | EKF3 (stored) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for t in BAGS:
        L.append(f"| {t} | " + " | ".join(m(run(k, t, "heading")["ate_a_cruise_m"]) for k in ["r0"] + LADDER)
                 + f" | {m(stored[t]['U_heading'])} | {m(stored[t]['EKF3'])} |")
    L.append("\n## T2. Gap retention R_i = (U_i − F_ρ,i) / (U_i − F_0,i) (EXPLORATORY; DESCRIPTIVE)\n")
    L.append("| bag | gap (m) | 1 − band/gap | R(r1) | R(r2) | R(r3) | R(r4) | R(r5) | R(r6) | R(r7) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for t in BAGS:
        L.append(f"| {t} | {m(out['R'][f'gap.{t}'])} | {r2(1 - out['R'][f'bandgap.{t}'])} | "
                 + " | ".join(r2(out["R"][f"{k}.{t}"]) for k in LADDER + ["r6", "r7"]) + " |")
    L.append("\n## T3. Control (no heading): FGO evo -a (cruise), m, and paired Δ = F_ρ − F_0, m (EXPLORATORY)\n")
    L.append("| bag | r0 | r1 (Δ) | r2 (Δ) | r3 (Δ) | r4 (Δ) | r5 (Δ) | band | UKF (stored) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for t in BAGS:
        cells = [f"{m(run(k, t, 'baseline')['ate_a_cruise_m'])} ({m(out['P1'][k]['bags'][t]['delta_m'])})" for k in LADDER]
        L.append(f"| {t} | {m(run('r0', t, 'baseline')['ate_a_cruise_m'])} | " + " | ".join(cells)
                 + f" | {m(band[(ds(t), 'baseline')])} | {m(stored[t]['U_baseline'])} |")
    L.append("\n## T4. Robust weighting replacing the heading gate: evo -a (cruise), m (EXPLORATORY; DESCRIPTIVE)\n")
    L.append("| bag | r0 | r6 Huber 0.25 s | r6 − r0 | r3 | r7 Huber 1 kf | r7 − r3 | r6s stored Cauchy | band (heading) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for t in BAGS:
        L.append(f"| {t} | {m(run('r0', t, 'heading')['ate_a_cruise_m'])} | {m(run('r6', t, 'heading')['ate_a_cruise_m'])} | "
                 f"{m(p3[t]['d_r6_r0'])} | {m(run('r3', t, 'heading')['ate_a_cruise_m'])} | {m(run('r7', t, 'heading')['ate_a_cruise_m'])} | "
                 f"{m(p3[t]['d_r7_r3'])} | {m(run('r6s', t, 'heading')['ate_a_cruise_m'])} | {m(band[(ds(t), 'heading')])} |")
    L.append("\n## T5. Compute per step, median / p95, ms (EXPLORATORY; DIAGNOSTIC: workstation Python, serial, 1 thread, nice 19)\n")
    L.append("| bag, arm | " + " | ".join(["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]) + " |")
    L.append("|---|" + "---|" * 8)
    for arm in ("heading", "baseline"):
        for t in BAGS:
            cells = []
            for k in ["r0"] + LADDER + ["r6", "r7"]:
                if k in ("r6", "r7") and arm == "baseline":
                    cells.append("—"); continue
                s = run(k, t, arm)["step_ms"]
                cells.append("—" if not s else f"{s['median']:.1f} / {s['p95']:.1f}")
            L.append(f"| {t}, {arm} | " + " | ".join(cells) + " |")
    L.append("\n## T6. Headings fused / valid, and run status (EXPLORATORY; DESCRIPTIVE)\n")
    L.append("| bag | " + " | ".join(["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]) + " |")
    L.append("|---|" + "---|" * 8)
    for t in BAGS:
        cells = []
        for k in ["r0"] + LADDER + ["r6", "r7"]:
            c = run(k, t, "heading")["fwd_counts"]
            cells.append("—" if not c else f"{c['psi_fused']} / {c['psi_valid']}")
        L.append(f"| {t} | " + " | ".join(cells) + " |")
    open(f"{A}/tables.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nr0 equal stored:", out["r0_equal_stored"], "/12")
    print("P1:", {k: (out["P1"][k]["n_within"], out["P1"][k]["verdict"]) for k in LADDER}, out["P1"]["overall"])
    print("P2:", n2, "/3", out["P2"]["verdict"]); print("P3:", n6, n7, out["P3"]["verdict"])
    print("interp:", json.dumps(it, indent=1))
    bad = [k for k, v in out["runs"].items() if not v["ok"]]
    print("not-ok runs:", bad)


if __name__ == "__main__":
    main()
