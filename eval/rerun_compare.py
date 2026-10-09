#!/usr/bin/env python3
"""Old vs new for every headline number of the consolidated re-run (user ruling 2026-09-29):
numbers.md sections 6-9, plus the Phase 4, Phase 5, 5b, scale-check and heading-share
headlines recorded after the numbers pack. Reads two results directories (OLD = the
pre-re-run snapshot, NEW = eval/results after the re-run) and writes a markdown report.

DIRECTION FLAGS (automatic, then reviewed by hand): a row is flagged when a comparison's
direction changes, i.e. for
  - orderings (which estimator is lower, textured vs blank, ...): the sign of the difference;
  - arm effects (heading arm minus baseline): the sign;
  - verdicts (pass/fail, consistent/inconsistent, fused/not fused): the boolean;
  - ratios against 1 (speed ratio, displacement ratio): the side of 1;
  - shares against 50% (heading-dominated or not).
Plain magnitudes (a number moving without a comparison changing) are listed, not flagged.

EXTENDED 2026-10-09 (final consolidated re-run, ruling "before launch"): the offline sections of T, O, L, H, the F
tests (F1, F2, F3, F3b, F3c) and 2(a) (F4) are compared too. Their extra flag kinds:
  - band verdicts (value <= a pre-registered band, e.g. P-H5 drift bands, P-T3/P-T4/H-O2/P-O3 ratio <= 1.5): the side of
    the band ("le:<band>");
  - count verdicts ("3/3", pass iff all) and the JSONs' own decision booleans: the verdict.
H, O and T "old" values: by default OLD/expH, OLD/expO, OLD/expT (the snapshot). With --prescore DIR (the pipeline's
same-scorer pre-score, ~/thesis_data/batches/final_rerun/prescore: s1_r*.json, s1far_r*.json, O_*.json, T_*.json) the
per-trial H/O/T files are read from DIR first, falling back to the snapshot. The H scorer renamed
`hold_windows_EKF3_flying` -> `hold_windows_vehicle` (140d1bf); both keys are accepted. T's aggregate (t_aggregate.json)
always comes from OLD/expT (the pre-score does not run t_aggregate; tag_score/t_aggregate are unchanged since the T JSONs
were written, verified by re-scoring byte-identically, docs/handovers/2026-10-09_final_rerun_repro.md).
V-L is reported as NOT re-scorable (ruling 6, 2026-10-09): its old value is listed, no new value is made.
Self-test: `--selftest` runs OLD = NEW = the given directory, requires every numeric delta = 0 and no flag, then mutates a
scratch copy (one verdict, one ordering, one band) and requires each to be flagged.
Usage: python3 eval/rerun_compare.py OLD_DIR NEW_DIR --md OUT.md [--json OUT.json] [--prescore DIR]
       python3 eval/rerun_compare.py --selftest RESULTS_DIR
"""
import argparse, copy, json, math, os, shutil, statistics as st, subprocess, sys, tempfile

WORLDS = ("tex", "trans", "blank")
ap = argparse.ArgumentParser(); ap.add_argument("old", nargs="?"); ap.add_argument("new", nargs="?")
ap.add_argument("--md"); ap.add_argument("--json"); ap.add_argument("--prescore")
ap.add_argument("--selftest", metavar="RESULTS_DIR"); a = ap.parse_args()
EXTRA_PREFIXES = ("T ", "O ", "L ", "H ", "F1", "F2", "F3", "2(a)", "file presence")


def selftest(res):
    """OLD = NEW (every delta 0, no flag), then three mutations of a scratch copy, each of which must be flagged."""
    me, tmp = os.path.abspath(__file__), tempfile.mkdtemp(prefix="rerun_compare_selftest_")
    run = lambda o, n, tag: json.load(open(subprocess.run(
        [sys.executable, me, o, n, "--md", f"{tmp}/{tag}.md", "--json", f"{tmp}/{tag}.json"], check=True,
        capture_output=True, text=True) and f"{tmp}/{tag}.json"))
    rows = run(res, res, "self")
    # The corridor sections map OLD names to NEW names (e.g. dsn_dejitter_baseline -> rerun_dsn_evo), so OLD = NEW is
    # not an identity there; the self-test covers the extended sections, whose OLD and NEW file names are the same.
    extra = [r for r in rows if r["section"].startswith(EXTRA_PREFIXES)]
    nonzero = [r for r in extra if (r["delta"] != "" and float(r["delta"]) != 0.0) or r.get("old_raw") != r.get("new_raw")]
    same = [r for r in extra if r["old"] != r["new"] and not r["new"].startswith("NOT re-scorable")]
    flagged = [r for r in extra if r["flag"]]
    print(f"self-compare: {len(rows)} rows, {len(extra)} in T/O/L/H/F/2(a): non-zero deltas {len(nonzero)}, "
          f"old != new {len(same)}, flags {len(flagged)}")
    for r in (nonzero + same + flagged)[:20]:
        print("   UNEXPECTED", r)
    ok = not nonzero and not same and not flagged and len(extra) > 0
    # mutations, on a scratch copy of only the files touched
    mut = f"{tmp}/mut"; shutil.copytree(res, mut)
    def edit(rel, fn):
        p = f"{mut}/{rel}"; d = json.load(open(p)); fn(d); json.dump(d, open(p, "w"), indent=1)
    edit("expT/t_aggregate.json", lambda d: d["H-T1 (FGO live -> whole-flight batch)"].__setitem__("PASS", not d["H-T1 (FGO live -> whole-flight batch)"]["PASS"]))
    def swap_o(d):   # ordering: FGO batch above RTS-UKF in O_r1
        t = d["tracks"]; t["FGO hindsight (whole-flight batch)"]["indoor_rmse_m"] = t["RTS-UKF (hindsight)"]["indoor_rmse_m"] * 3
    edit("expO/O_r1.json", swap_o)
    def band_h(d):   # P-H5: UKF 30 s drift beyond its 0.40 m band in s1_r1
        d["losses"][2]["UKF"]["drift_end_m"] = 0.55
    edit("expH/s1_r1.json", band_h)
    # a new-only H flight (s1far_r3b) that FAILS P-H5 must not change the both-sides counts (no flag)
    d3 = json.load(open(f"{mut}/expH/s1far_r1.json")); d3["losses"][2]["UKF"]["drift_end_m"] = 0.9
    json.dump(d3, open(f"{mut}/expH/s1far_r3b.json", "w"), indent=1)
    rows = run(res, mut, "mut")
    want = {"T H-T1 verdict": lambda r: r["section"].startswith("T verdicts") and r["quantity"].startswith("H-T1 PASS"),
            "O ordering FGO batch vs RTS-UKF O_r1": lambda r: r["section"].startswith("O (§16.2) orderings") and "O_r1" in r["quantity"] and "FGO batch − RTS-UKF" in r["quantity"],
            "H P-H5 UKF 30 s s1_r1": lambda r: r["section"].startswith("H (§17) P-H5") and r["quantity"].startswith("s1_r1 loss 3") and "UKF" in r["quantity"] and "as worded" in r["quantity"]}
    for k, f in want.items():
        hit = [r for r in rows if f(r)]
        good = bool(hit) and all(r["flag"] for r in hit)
        print(f"mutation '{k}': rows {len(hit)}, flagged {good}")
        ok = ok and good
    r3 = [r for r in rows if r["section"].startswith("H verdicts (new-only") and r["quantity"] == "P-H5 UKF"]
    good = bool(r3) and not r3[0]["flag"] and r3[0]["new"].startswith("3/4")
    print(f"new-only s1far_r3b: row {r3[0]['new'] if r3 else None}, unflagged {good}"); ok = ok and good
    # a missing new-side file must be flagged MISSING and make the run exit non-zero
    mis = f"{tmp}/mis"; shutil.copytree(res, mis); os.remove(f"{mis}/f4_test.json")
    pr = subprocess.run([sys.executable, me, res, mis, "--md", f"{tmp}/mis.md", "--json", f"{tmp}/mis.json"], capture_output=True, text=True)
    mrow = [r for r in json.load(open(f"{tmp}/mis.json")) if r["flag"] == "MISSING"]
    good = pr.returncode == 3 and len(mrow) == 1 and "f4_test.json" in mrow[0]["quantity"] and "WARNING" in pr.stderr
    print(f"missing f4_test.json on the new side: exit {pr.returncode}, MISSING rows {len(mrow)}, ok {good}"); ok = ok and good
    # every other flagged row must be a consequence of the three mutations (verdict counts derived from them)
    print("flagged rows in T/O/L/H/F/2(a) after mutation (each must follow from the three mutations):")
    for r in rows:
        if r["flag"] and r["section"].startswith(EXTRA_PREFIXES):
            print(f"   {r['section']} | {r['quantity']} | {r['old']} -> {r['new']}")
    shutil.rmtree(tmp)
    print("SELFTEST", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if a.selftest:
    selftest(a.selftest)
assert a.old and a.new and a.md, "usage: OLD_DIR NEW_DIR --md OUT.md (or --selftest RESULTS_DIR)"


def L(d, f):
    p = os.path.join(d, f)
    return json.load(open(p)) if os.path.exists(p) else None


def get(x, *ks):
    for k in ks:
        if x is None:
            return None
        x = x.get(k) if isinstance(x, dict) else None
    return x


rows = []   # (section, quantity, old, new, kind, flag_note)
RAW = {}    # row index -> (old, new) unformatted, for add() rows (written to the JSON as old_raw / new_raw)


def fmt(v, nd=3):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int, float)):
        return f"{v:.{nd}f}" if isinstance(v, float) else str(v)
    return str(v)


def add(sec, q, old, new, kind="mag", ref=None, nd=3):
    """kind: mag (magnitude only) | sign (flag if sign differs) | side:<ref> | bool"""
    flag = ""
    if old is not None and new is not None:
        if kind == "sign" and (old > 0) != (new > 0) and old != 0 and new != 0:
            flag = "DIRECTION"
        elif kind.startswith("side:"):
            r = float(kind.split(":")[1])
            if (old - r) * (new - r) < 0:
                flag = "DIRECTION"
        elif kind == "bool" and bool(old) != bool(new):
            flag = "DIRECTION"
        elif kind.startswith("le:"):          # band verdict: value <= band
            r = float(kind.split(":")[1])
            if (old <= r) != (new <= r):
                flag = "VERDICT"
    delta = (new - old) if isinstance(old, (int, float)) and isinstance(new, (int, float)) and not isinstance(old, bool) else None
    rows.append((sec, q, fmt(old, nd), fmt(new, nd), fmt(delta, nd) if delta is not None else "", flag))
    RAW[len(rows) - 1] = (old, new)


def mean(v):
    v = [x for x in v if x is not None]
    return st.mean(v) if v else None


def rng(v):
    v = [x for x in v if x is not None]
    return (max(v) - min(v)) if v else None


O, N = a.old, a.new
# ---------- 6.1 textured dsn baseline ----------
for tag, of, nf in (("dsn", "dsn_dejitter_baseline.json", "rerun_dsn_evo.json"),):
    od, nd_ = get(L(O, of), "trials"), get(L(N, nf), "trials") or get(L(N, of), "trials")
    for est in ("EKF3", "FGO", "UKF"):
        ov = [get(od, f"dsn_tex_r{r}", "est", est, "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
        nv = [get(nd_, f"dsn_tex_r{r}", "est", est, "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
        for r in range(3):
            add("6.1 dsn textured evo -a (cruise), m", f"{est} r{r+1}", ov[r], nv[r])
        add("6.1 dsn textured evo -a (cruise), m", f"{est} mean", mean(ov), mean(nv))
        add("6.1 dsn textured evo -a (cruise), m", f"{est} range", rng(ov), rng(nv))
    for x, y in (("EKF3", "FGO"), ("UKF", "EKF3"), ("UKF", "FGO")):
        o = [get(od, f"dsn_tex_r{r}", "est", e, "ate_a_cruise", "+0.00") for e in (x, y) for r in (1, 2, 3)]
        n = [get(nd_, f"dsn_tex_r{r}", "est", e, "ate_a_cruise", "+0.00") for e in (x, y) for r in (1, 2, 3)]
        add("6.1 dsn textured evo -a (cruise), m", f"ordering: mean {x} − mean {y}",
            mean(o[:3]) - mean(o[3:]) if None not in o else None, mean(n[:3]) - mean(n[3:]) if None not in n else None, "sign")
    # 6.2 failure metrics, all estimators
    for w in ("trans", "blank"):
        for est in ("EKF3", "FGO", "UKF"):
            for m, k in (("displacement ratio", "disp_ratio"), ("onset (GT y, m)", "onset_gt_dist")):
                ov = [get(od, f"dsn_{w}_r{r}", "est", est, "failure", k) for r in (1, 2, 3)]
                nv = [get(nd_, f"dsn_{w}_r{r}", "est", est, "failure", k) for r in (1, 2, 3)]
                add(f"6.2 dsn {w} failure metrics", f"{est} {m}, mean of 3", mean(ov), mean(nv),
                    "side:1" if k == "disp_ratio" else "mag", nd=2 if k == "disp_ratio" else 1)
    for w in WORLDS:
        for est in ("EKF3", "FGO", "UKF"):
            ov = [get(od, f"dsn_{w}_r{r}", "est", est, "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            nv = [get(nd_, f"dsn_{w}_r{r}", "est", est, "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            if w != "tex":
                add(f"6.2 dsn {w} failure metrics", f"{est} evo -a (cruise), mean of 3", mean(ov), mean(nv), nd=2)

# ---------- 6.3 heading share ----------
oh, nh = L(O, "heading_share_restated.json"), L(N, "heading_share_restated.json")
for t in ("dsn_tex_r3", "dsn_tex_r1", "dsn_tex_r2"):
    add("6.3 EKF3 lateral drift, heading share (pinned cruise window)", f"{t} share", get(oh, t, "share"), get(nh, t, "share"), "side:0.5")
    add("6.3 EKF3 lateral drift, heading share (pinned cruise window)", f"{t} errV mean (m/s)", get(oh, t, "errV_mean"), get(nh, t, "errV_mean"), "sign")
    add("6.3 EKF3 lateral drift, heading share (pinned cruise window)", f"{t} cross-track err (m)", get(oh, t, "xtrack_err_m"), get(nh, t, "xtrack_err_m"), nd=1)
    add("6.3 EKF3 lateral drift, heading share (pinned cruise window)", f"{t} residual (m/s)", get(oh, t, "resid_mean"), get(nh, t, "resid_mean"), "sign")

# ---------- 6.4 forward-camera sets and p1c ----------
for ds, of, nf in (("fwdc", "fwdc_evo.json", "rerun_fwdc_evo.json"), ("fwdplainc", "fwdplainc_evo.json", "rerun_fwdplainc_evo.json")):
    od, nd_ = get(L(O, of), "trials"), get(L(N, nf), "trials")
    for est in ("EKF3", "FGO", "UKF"):
        ov = [get(od, f"{ds}_tex_r{r}", "est", est, "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
        nv = [get(nd_, f"{ds}_tex_r{r}", "est", est, "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
        add(f"6.4 {ds} textured evo -a (cruise), m", f"{est} mean of 3", mean(ov), mean(nv), nd=2)
        add(f"6.4 {ds} textured evo -a (cruise), m", f"{est} r1/r2/r3", "/".join(fmt(x, 2) for x in ov), "/".join(fmt(x, 2) for x in nv))
        for w in ("trans", "blank"):
            for m, k in (("ratio", "disp_ratio"), ("onset", "onset_gt_dist")):
                ov = [get(od, f"{ds}_{w}_r{r}", "est", est, "failure", k) for r in (1, 2, 3)]
                nv = [get(nd_, f"{ds}_{w}_r{r}", "est", est, "failure", k) for r in (1, 2, 3)]
                add(f"6.4 {ds} {w} failure metrics", f"{est} {m}, mean of 3", mean(ov), mean(nv),
                    "side:1" if k == "disp_ratio" else "mag", nd=2 if k == "disp_ratio" else 1)
op, np_ = get(L(O, "p1c_evo.json"), "trials"), get(L(N, "rerun_p1c_evo.json"), "trials")
for t in ("p1c_fwdc_tex", "p1c_fwdplainc_tex"):
    for est in ("EKF3", "FGO", "UKF"):
        add("6.4 p1c check flights, textured evo -a (cruise), m", f"{t} {est}", get(op, t, "est", est, "ate_a_cruise", "+0.00"),
            get(np_, t, "est", est, "ate_a_cruise", "+0.00"), nd=2)

# ---------- ds compass-active reference (EKF3 only) ----------
nds = get(L(N, "rerun_ds_evo.json"), "trials")
for w in WORLDS:
    nv = [get(nds, f"ds_{w}_r{r}", "est", "EKF3", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
    add("6.3 ds (compass-active) EKF3 evo -a (cruise), m — old values used a different (apparatus) metric", f"{w} mean of 3", None, mean(nv), nd=2)
    if w != "tex":
        nv = [get(nds, f"ds_{w}_r{r}", "est", "EKF3", "failure", "disp_ratio") for r in (1, 2, 3)]
        add("6.3 ds (compass-active) EKF3 evo -a (cruise), m — old values used a different (apparatus) metric", f"{w} displacement ratio, mean of 3", None, mean(nv), nd=2)

# ---------- 6.5 scale check ----------
os_, ns = L(O, "scale_check.json"), L(N, "scale_check.json")
for key, lab in (("EKF3", "EKF3"), ("FGO_baseline", "FGO baseline"), ("FGO_heading", "FGO heading"),
                 ("UKF_baseline", "UKF baseline"), ("UKF_heading", "UKF heading")):
    for ds in ("fwdc", "fwdplainc"):
        ov = [get(os_, f"{ds}_tex_r{r}", key, "speed_ratio_median") for r in (1, 2, 3)]
        nv = [get(ns, f"{ds}_tex_r{r}", key, "speed_ratio_median") for r in (1, 2, 3)]
        add("6.5 distance scale (textured, speed ratio)", f"{lab} {ds} mean of 3", mean(ov), mean(nv), "side:1")
for ds in ("fwdc", "fwdplainc"):
    ov = [get(os_, f"{ds}_tex_r{r}", "flow", "flow_y_slope") for r in (1, 2, 3)]
    nv = [get(ns, f"{ds}_tex_r{r}", "flow", "flow_y_slope") for r in (1, 2, 3)]
    add("6.5 distance scale (textured, speed ratio)", f"flow sensor scale {ds} mean of 3", mean(ov), mean(nv), "side:1")

# ---------- 7 bands ----------
ob = {"EKF3": {"tex": {"ate": [1.26, 8.13]}, "trans": {"ratio": [0.51, 0.63], "onset": [96, 108]}, "blank": {"ratio": [0.12, 0.27], "onset": [13, 24]}},
      "FGO": {"tex": {"ate": [4.17, 5.14]}, "trans": {"ratio": [0.67, 0.78], "onset": [90, 101]}, "blank": {"ratio": [1.45, 1.60], "onset": [28, 42]}}}
nb = L(N, "rerun_p4_bands.json")
for est in ("EKF3", "FGO"):
    for w in WORLDS:
        for k in (("ate",) if w == "tex" else ("ratio", "onset")):
            rows.append(("7 P4 bands (recomputed from the re-flown dsn, same formula)", f"{est} {w} {k}",
                         str(ob[est][w][k]), str(get(nb, est, w, k)), "", ""))
ofq, nfq = L(O, "flow_quality_dsn.json"), L(N, "flow_quality_dsn.json")
for w in WORLDS:
    for k in ("inlier_mean", "flow_y_raw_mean", "features_mean"):
        add("7 P3 references (dsn n=3 mean)", f"{w} {k}", mean([get(ofq, f"dsn_{w}_r{r}", k) for r in (1, 2, 3)]),
            mean([get(nfq, f"dsn_{w}_r{r}", k) for r in (1, 2, 3)]), nd=4)

# ---------- 8 pass counts ----------
for ds, of, nf in (("fwdc", "fwdc_score.json", "rerun_fwdc_score.json"), ("fwdplainc", "fwdplainc_score.json", "rerun_fwdplainc_score.json"),
                   ("p1c", "p1c_score.json", "rerun_p1c_score.json")):
    o, n = get(L(O, of), "trials"), get(L(N, nf), "trials")
    cnt = lambda x: None if x is None else f"{sum(v['primary'] == 'PASS' for v in x.values())}/{len(x)}"
    rows.append(("8 dataset primary pass counts", f"{ds} primary PASS", cnt(o), cnt(n), "", ""))
    if o and n:
        for t in sorted(set(o) & set(n)):
            if (o[t]["primary"] == "PASS") != (n[t]["primary"] == "PASS"):
                rows.append(("8 dataset primary pass counts", f"{t} verdict", f"{o[t]['primary']} {o[t]['primary_fails']}",
                             f"{n[t]['primary']} {n[t]['primary_fails']}", "", "DIRECTION"))

# ---------- 9 Phase 3 validation ----------
ov, nv = L(O, "fwd_validation.json"), L(N, "fwd_validation.json")
for m in ("psi", "omega"):
    for ds in ("fwdc", "fwdplainc"):
        for w in WORLDS:
            k = f"{m}/{ds}/{w}"
            for f in ("avail_pct", "bias", "noise_sd", "robust_sigma", "outlier_pct"):
                add(f"9 Phase 3 validation ({m})", f"{ds} {w} {f}", get(ov, "aggregate", k, f), get(nv, "aggregate", k, f), nd=3)
            op_, np2 = get(ov, "aggregate", k, "n_pass"), get(nv, "aggregate", k, "n_pass")
            maj = lambda s: None if s is None else (lambda a_, b_: 2 * int(a_) >= int(b_))(*s.split("/"))
            flag = "DIRECTION" if (op_ and np2 and maj(op_) != maj(np2)) else ""
            rows.append((f"9 Phase 3 validation ({m})", f"{ds} {w} bags passing all bars", str(op_), str(np2), "", flag))
pv = L(N, "fwd_validation_p1c.json")
for m in ("psi", "omega"):
    for ds in ("fwdc", "fwdplainc"):
        k = f"{m}/{ds}/all"
        add("9 Phase 3 second validation on re-flown p1c (frozen parameters; old = calibration set)", f"{m} {ds} avail / outlier %",
            None, None)
        rows[-1] = rows[-1][:3] + (f"{fmt(get(pv, 'aggregate', k, 'avail_pct'), 1)} / {fmt(get(pv, 'aggregate', k, 'outlier_pct'), 2)}",) + rows[-1][4:]

# ---------- Phase 4 ----------
for ds, arms in (("fwdc", ("baseline", "heading", "heading_yawrate")), ("fwdplainc", ("baseline", "heading"))):
    oa, na = L(O, f"phase4_{ds}_arms.json"), L(N, f"phase4_{ds}_arms.json")
    for w in WORLDS:
        for est in ("UKF", "FGO"):
            for arm in arms:
                ov_ = [get(oa, f"{ds}_{w}_r{r}", f"{est}_{arm}", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
                nv_ = [get(na, f"{ds}_{w}_r{r}", f"{est}_{arm}", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
                add(f"P4 {ds} {w}: evo -a (cruise), mean of 3, m", f"{est}_{arm}", mean(ov_), mean(nv_), nd=2)
                oy = [get(oa, f"{ds}_{w}_r{r}", f"{est}_{arm}", "yaw_err_rms_deg") for r in (1, 2, 3)]
                ny = [get(na, f"{ds}_{w}_r{r}", f"{est}_{arm}", "yaw_err_rms_deg") for r in (1, 2, 3)]
                add(f"P4 {ds} {w}: yaw error rms, mean of 3, deg", f"{est}_{arm}", mean(oy), mean(ny), nd=2)
            # arm effect: heading minus baseline (evo); flagged if the sign flips
            ob_ = [get(oa, f"{ds}_{w}_r{r}", f"{est}_baseline", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            oh_ = [get(oa, f"{ds}_{w}_r{r}", f"{est}_heading", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            nb_ = [get(na, f"{ds}_{w}_r{r}", f"{est}_baseline", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            nh_ = [get(na, f"{ds}_{w}_r{r}", f"{est}_heading", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            add(f"P4 {ds} {w}: heading arm effect (heading − baseline evo, mean), m", est,
                None if None in ob_ + oh_ else mean(oh_) - mean(ob_), None if None in nb_ + nh_ else mean(nh_) - mean(nb_), "sign", nd=2)
        oe = [get(oa, f"{ds}_{w}_r{r}", "EKF3", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
        ne = [get(na, f"{ds}_{w}_r{r}", "EKF3", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
        add(f"P4 {ds} {w}: evo -a (cruise), mean of 3, m", "EKF3 (reference)", mean(oe), mean(ne), nd=2)
        # heading-arm ordering vs EKF3
        for est in ("UKF", "FGO"):
            oh_ = [get(oa, f"{ds}_{w}_r{r}", f"{est}_heading", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            nh_ = [get(na, f"{ds}_{w}_r{r}", f"{est}_heading", "evo", "ate_a_cruise", "+0.00") for r in (1, 2, 3)]
            add(f"P4 {ds} {w}: ordering {est}_heading − EKF3 (evo mean), m", est,
                None if None in oh_ + oe else mean(oh_) - mean(oe), None if None in nh_ + ne else mean(nh_) - mean(ne), "sign", nd=2)

# ---------- Phase 5 ----------
o5, n5 = L(O, "phase5_analysis.json"), L(N, "phase5_analysis.json")
for ds, arms in (("fwdc", ("baseline", "heading", "heading_yawrate")), ("fwdplainc", ("baseline", "heading"))):
    for w in WORLDS:
        for lab in ["EKF3"] + [f"{e}_{a}" for e in ("UKF", "FGO") for a in arms]:
            os5 = [get(o5, "decomposition", f"{ds}_{w}_r{r}", lab, "share") for r in (1, 2, 3)]
            ns5 = [get(n5, "decomposition", f"{ds}_{w}_r{r}", lab, "share") for r in (1, 2, 3)]
            add(f"P5 {ds} {w}: heading share of lateral velocity error, mean of 3", lab, mean(os5), mean(ns5), "side:0.5", nd=2)
    for est in ("UKF", "FGO"):
        for arm in arms[1:]:
            of_ = sum((get(o5, "endwall", f"{ds}_{w}_r{r}/{est}_{arm}", "fused") or 0) for w in WORLDS for r in (1, 2, 3)) if o5 else None
            nf_ = sum((get(n5, "endwall", f"{ds}_{w}_r{r}/{est}_{arm}", "fused") or 0) for w in WORLDS for r in (1, 2, 3)) if n5 else None
            owr = sum((get(o5, "endwall", f"{ds}_{w}_r{r}/{est}_{arm}", "wrong_gt_3deg") or 0) for w in WORLDS for r in (1, 2, 3)) if o5 else None
            nwr = sum((get(n5, "endwall", f"{ds}_{w}_r{r}/{est}_{arm}", "wrong_gt_3deg") or 0) for w in WORLDS for r in (1, 2, 3)) if n5 else None
            rows.append((f"P5 end wall (GT y > 140 m): wrong (> 3°) valid headings fused / wrong", f"{ds} {est}_{arm}",
                         f"{of_} / {owr}", f"{nf_} / {nwr}", "", "DIRECTION" if (of_ and not nf_) or (nf_ and not of_) else ""))
for est in ("UKF", "FGO"):
    oa_ = [get(o5, "plain_checker", f"fwdplainc_tex_r{r}/{est}", "accept_pct") for r in (1, 2, 3)]
    na_ = [get(n5, "plain_checker", f"fwdplainc_tex_r{r}/{est}", "accept_pct") for r in (1, 2, 3)]
    add("P5 plain walls over checker floor: gate acceptance %, mean of 3", est, mean(oa_), mean(na_), nd=1)

# ---------- Phase 5b ----------
o6, n6 = L(O, "phase5b_consistency.json"), L(N, "phase5b_consistency.json")
for ds in ("fwdc", "fwdplainc"):
    for w in WORLDS:
        for lab in ("EKF3", "UKF_baseline", "UKF_heading", "FGO_baseline", "FGO_heading"):
            on = [get(o6, "consistency", f"{ds}_{w}_r{r}", lab, "mean_nees") for r in (1, 2, 3)]
            nn = [get(n6, "consistency", f"{ds}_{w}_r{r}", lab, "mean_nees") for r in (1, 2, 3)]
            add(f"P5b {ds} {w}: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3)", lab, mean(on), mean(nn), "side:3", nd=2)
            op5 = [get(o6, "consistency", f"{ds}_{w}_r{r}", lab, "pct_outside_3sigma") for r in (1, 2, 3)]
            np5 = [get(n6, "consistency", f"{ds}_{w}_r{r}", lab, "pct_outside_3sigma") for r in (1, 2, 3)]
            add(f"P5b {ds} {w}: % outside ±3σ, mean of 3", lab, mean(op5), mean(np5), nd=1)
for grp in ("endwall_S", "checker_S"):
    for k in ("fwdc/UKF", "fwdc/FGO", "fwdplainc/UKF", "fwdplainc/FGO"):
        add(f"P5b {grp}: median √S (deg)", k, get(o6, grp, k, "all", "median_sqrtS_deg"), get(n6, grp, k, "all", "median_sqrtS_deg"), nd=3)
        add(f"P5b {grp}: yaw-prediction NEES mean", k, get(o6, grp, k, "all", "yaw_pred_nees_mean"), get(n6, grp, k, "all", "yaw_pred_nees_mean"), "side:3", nd=2)

# ====================================================================================================================
# EXTENDED SECTIONS (2026-10-09): T, O, L, H, F1-F3c, 2(a). Headline list: docs/handovers/2026-10-09_final_rerun_pipeline.md §5.
# ====================================================================================================================
PS = a.prescore


def LX(d, sub, f, pre=False):
    """Per-trial H/O/T file: the same-scorer pre-score first (old side only, --prescore), then <d>/<sub>/<f>."""
    if pre and PS and os.path.exists(os.path.join(PS, f)):
        return L(PS, f)
    return L(os.path.join(d, sub), f)


def cnt_row(sec, q, ov, nv):
    """A count verdict: lists of per-flight booleans -> 'k/n', PASS iff all; flagged if PASS changes."""
    c = lambda v: None if v is None or None in v else f"{sum(bool(x) for x in v)}/{len(v)}"
    p = lambda v: None if v is None or None in v else all(v)
    po, pn = p(ov), p(nv)
    fl = "VERDICT" if po is not None and pn is not None and po != pn else ""
    rows.append((sec, q, f"{c(ov)} ({'PASS' if po else 'FAIL'})" if po is not None else "—",
                 f"{c(nv)} ({'PASS' if pn else 'FAIL'})" if pn is not None else "—", "", fl))


def lt(x, y):
    return None if x is None or y is None else x < y


def ratio(x, y):
    return None if x is None or y is None or y == 0 else x / y


# ---------- T (§16.1): t_aggregate.json ----------
TA = "T (§16.1)"
ot, nt = L(os.path.join(O, "expT"), "t_aggregate.json"), L(os.path.join(N, "expT"), "t_aggregate.json")
TRK = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
for c in "ABCD":
    for k in TRK:
        add(f"{TA} mean horizontal RMSE by condition, m", f"{c} {k}", get(ot, "conditions", c, "mean_rmse_m", k),
            get(nt, "conditions", c, "mean_rmse_m", k), nd=4)
    om, nm = (get(x, "conditions", c, "mean_rmse_m") for x in (ot, nt))
    for x, y in (("FGO hindsight (whole-flight batch)", "RTS-UKF (hindsight)"), ("FGO live", "UKF live"),
                 ("UKF live", "EKF3 live"), ("FGO live", "EKF3 live")):
        add(f"{TA} orderings (mean RMSE difference), m", f"{c}: {x} − {y}",
            None if not om or om.get(x) is None or om.get(y) is None else om[x] - om[y],
            None if not nm or nm.get(x) is None or nm.get(y) is None else nm[x] - nm[y], "sign", nd=4)
for hk, lab in (("H-T1 (FGO live -> whole-flight batch)", "H-T1"), ("P-T2 (UKF live -> RTS)", "P-T2")):
    for c in "ABCD":
        add(f"{TA} {lab} hindsight gain (median), m", c, get(ot, hk, "median_gain_m", c), get(nt, hk, "median_gain_m", c), "sign", nd=4)
    add(f"{TA} {lab} hindsight gain (median), m", "Spearman rho", get(ot, hk, "spearman_rho"), get(nt, hk, "spearman_rho"), "sign")
    add(f"{TA} {lab} hindsight gain (median), m", "p", get(ot, hk, "p"), get(nt, hk, "p"), "le:0.01", nd=6)
    add(f"T verdicts", f"{lab} medians strictly increasing", get(ot, hk, "strictly_increasing"), get(nt, hk, "strictly_increasing"), "bool")
    add(f"T verdicts", f"{lab} PASS", get(ot, hk, "PASS"), get(nt, hk, "PASS"), "bool")
for hk, lab in (("P-T3 live ratio max/min", "P-T3"), ("P-T4 hindsight ratio max/min", "P-T4")):
    for c in "ABCD":
        add(f"{TA} {lab} max/min ratio (band ≤ 1.5)", c, get(ot, hk, "by_condition", c), get(nt, hk, "by_condition", c), "le:1.5")
    add(f"T verdicts", f"{lab} PASS", get(ot, hk, "PASS"), get(nt, hk, "PASS"), "bool")

# ---------- O (§16.2): expO/O_r1, O_r2, O_r3b ----------
OA, OTR = "O (§16.2)", ("O_r1", "O_r2", "O_r3b")
OK_ = {"EKF3": "EKF3 live", "UKF": "UKF live", "FGO": "FGO live", "RTS": "RTS-UKF (hindsight)",
       "RTSfree": "RTS-UKF (hindsight, cap-free forward pass)", "batch": "FGO hindsight (whole-flight batch)"}
oo = {t: LX(O, "expO", f"{t}.json", pre=True) for t in OTR}
no = {t: LX(N, "expO", f"{t}.json") for t in OTR}
oi = lambda d, k: get(d, "tracks", OK_[k], "indoor_rmse_m")
for t in OTR:
    for k in OK_:
        for m in ("indoor_rmse_m", "err_at_return_m", "max_step_after_return_m"):
            add(f"{OA} per flight, m", f"{t} {OK_[k]} {m}", get(oo[t], "tracks", OK_[k], m), get(no[t], "tracks", OK_[k], m), nd=3)
    for x, y in (("batch", "EKF3"), ("batch", "UKF"), ("batch", "RTS"), ("FGO", "UKF"), ("UKF", "EKF3")):
        add(f"{OA} orderings (indoor RMSE difference), m", f"{t}: {OK_[x] if x != 'batch' else 'FGO batch'} − {OK_[y]}".replace(
            "RTS-UKF (hindsight)", "RTS-UKF"), None if oi(oo[t], x) is None or oi(oo[t], y) is None else oi(oo[t], x) - oi(oo[t], y),
            None if oi(no[t], x) is None or oi(no[t], y) is None else oi(no[t], x) - oi(no[t], y), "sign")
    live = lambda d: [oi(d, k) for k in ("EKF3", "UKF", "FGO")]
    h2 = lambda d: None if None in live(d) else max(live(d)) / min(live(d))
    add(f"{OA} H-O2 live max/min ratio (band ≤ 1.5)", t, h2(oo[t]), h2(no[t]), "le:1.5")
    p3 = lambda d, r: None if oi(d, "batch") is None or oi(d, r) is None else max(oi(d, "batch"), oi(d, r)) / min(oi(d, "batch"), oi(d, r))
    add(f"{OA} P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5)", f"{t} (capped)", p3(oo[t], "RTS"), p3(no[t], "RTS"), "le:1.5")
    add(f"{OA} P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5)", f"{t} (cap-free)", p3(oo[t], "RTSfree"), p3(no[t], "RTSfree"), "le:1.5")
h1 = lambda d: None if None in (oi(d, "batch"), oi(d, "EKF3"), oi(d, "UKF")) else oi(d, "batch") < min(oi(d, "EKF3"), oi(d, "UKF"))
cnt_row("O verdicts", "H-O1 FGO batch < EKF3 and UKF live, flights", [h1(oo[t]) for t in OTR], [h1(no[t]) for t in OTR])
cnt_row("O verdicts", "H-O2 live max/min ≤ 1.5, flights", [None if h2(oo[t]) is None else h2(oo[t]) <= 1.5 for t in OTR],
        [None if h2(no[t]) is None else h2(no[t]) <= 1.5 for t in OTR])
cnt_row("O verdicts", "P-O3 batch vs RTS-UKF ≤ 1.5 (capped), flights", [None if p3(oo[t], "RTS") is None else p3(oo[t], "RTS") <= 1.5 for t in OTR],
        [None if p3(no[t], "RTS") is None else p3(no[t], "RTS") <= 1.5 for t in OTR])
cnt_row("O verdicts", "P-O3 batch vs RTS-UKF ≤ 1.5 (cap-free), flights", [None if p3(oo[t], "RTSfree") is None else p3(oo[t], "RTSfree") <= 1.5 for t in OTR],
        [None if p3(no[t], "RTSfree") is None else p3(no[t], "RTSfree") <= 1.5 for t in OTR])

# ---------- L (§16.3): expL/T_A_r*_t245.json; V-L not re-scorable ----------
LA, LTR = "L (§16.3)", ("T_A_r1", "T_A_r2", "T_A_r3")
ol = {t: L(os.path.join(O, "expL"), f"{t}_t245.json") for t in LTR}
nl = {t: L(os.path.join(N, "expL"), f"{t}_t245.json") for t in LTR}
lap = lambda d, k: (lambda v: None if not v else v[-1] / v[0])(get(d, "tracks", k, "per_lap_rmse_m"))
lr = lambda d, k: get(d, "tracks", k, "rmse_m")
for t in LTR:
    for k in ("lc live", "lc hindsight", "nolc live", "nolc hindsight"):
        add(f"{LA} per flight RMSE, m", f"{t} {k}", lr(ol[t], k), lr(nl[t], k), nd=4)
    add(f"{LA} H-L1 lc live lap5/lap1 (band ≤ 1.5)", t, lap(ol[t], "lc live"), lap(nl[t], "lc live"), "le:1.5")
    add(f"{LA} P-L4 nolc live lap5/lap1 (> 1.5 predicted)", t, lap(ol[t], "nolc live"), lap(nl[t], "nolc live"), "le:1.5")
    for k in ("live", "hindsight"):
        add(f"{LA} orderings (lc − nolc RMSE), m", f"{t} {k}", None if None in (lr(ol[t], f"lc {k}"), lr(ol[t], f"nolc {k}")) else lr(ol[t], f"lc {k}") - lr(ol[t], f"nolc {k}"),
            None if None in (lr(nl[t], f"lc {k}"), lr(nl[t], f"nolc {k}")) else lr(nl[t], f"lc {k}") - lr(nl[t], f"nolc {k}"), "sign", nd=4)
le = lambda x, b: None if x is None else x <= b
cnt_row("L verdicts", "H-L1 lc live lap5/lap1 ≤ 1.5, flights", [le(lap(ol[t], "lc live"), 1.5) for t in LTR], [le(lap(nl[t], "lc live"), 1.5) for t in LTR])
cnt_row("L verdicts", "H-L2 lc live < nolc live, flights", [lt(lr(ol[t], "lc live"), lr(ol[t], "nolc live")) for t in LTR],
        [lt(lr(nl[t], "lc live"), lr(nl[t], "nolc live")) for t in LTR])
cnt_row("L verdicts", "H-L3 lc hindsight < nolc hindsight, flights", [lt(lr(ol[t], "lc hindsight"), lr(ol[t], "nolc hindsight")) for t in LTR],
        [lt(lr(nl[t], "lc hindsight"), lr(nl[t], "nolc hindsight")) for t in LTR])
cnt_row("L verdicts", "P-L4 nolc live lap5 > 1.5 × lap1, flights", [None if lap(ol[t], "nolc live") is None else lap(ol[t], "nolc live") > 1.5 for t in LTR],
        [None if lap(nl[t], "nolc live") is None else lap(nl[t], "nolc live") > 1.5 for t in LTR])
ovl = get(L(O, "vl_dsn_tex_r1.json"), "trials", "dsn_tex_r1", "est")
for k in ("KF_FGO_notags", "FGO_thesis"):
    rows.append((f"{LA} V-L (dsn_tex_r1 evo -a cruise, m)", k, fmt(get(ovl, k, "ate_a_cruise", "+0.00")),
                 "NOT re-scorable (ruling 6, 2026-10-09: labels never recorded)", "", ""))

# ---------- H (§17): expH/s1_r1..3, s1far_r1, r2 (+ r3b, new only) ----------
HA = "H (§17)"
HTR = ("s1_r1", "s1_r2", "s1_r3", "s1far_r1", "s1far_r2", "s1far_r3b")
LOSS = ("5 s", "15 s", "30 s", "move")
BAND = {"EKF3": (0.05, 0.10, 0.20, 0.15), "FGO": (0.05, 0.10, 0.20, 0.15), "UKF": (0.10, 0.20, 0.40, 0.30)}
oh = {t: LX(O, "expH", f"{t}.json", pre=True) for t in HTR}
nh = {t: LX(N, "expH", f"{t}.json") for t in HTR}
hold = lambda d: get(d, "hold_windows_vehicle") or get(d, "hold_windows_EKF3_flying")   # key renamed in 140d1bf
p5o, p5n, p7o, p7n = {e: [] for e in BAND}, {e: [] for e in BAND}, {e: [] for e in BAND}, {e: [] for e in BAND}
h_newonly = {e: ([], []) for e in BAND}
LOSS_DUR = ((3, 8), (12, 18), (26, 34), (5, 10))   # expected loss durations (s) by index: 5 s, 15 s, 30 s, the ~7 s move
for t in HTR:
    if oh[t] is None and nh[t] is None:
        continue
    for i in range(2):
        add(f"{HA} H-H1 hold (EKF3 flying), m", f"{t} window {i+1} mean", get((hold(oh[t]) or [None, None])[i] if hold(oh[t]) else None, "mean_m"),
            get((hold(nh[t]) or [None, None])[i] if hold(nh[t]) else None, "mean_m"), "le:0.05", nd=4)
    for li, lab in enumerate(LOSS):
        ol_ = (get(oh[t], "losses") or [None] * 4)[li] if get(oh[t], "losses") else None
        nl_ = (get(nh[t], "losses") or [None] * 4)[li] if get(nh[t], "losses") else None
        for side, l_ in (("old", ol_), ("new", nl_)):
            du = get(l_, "duration_s")
            if du is not None and not (LOSS_DUR[li][0] <= du <= LOSS_DUR[li][1]):
                rows.append(("H loss order check", f"{t} {side} loss {li+1} expected {lab}", "", f"duration {du:.1f} s", "", "LOSS ORDER"))
        for e in ("EKF3", "UKF", "FGO"):
            b = BAND[e][li]
            add(f"{HA} P-H5 drift at end of loss (band {e} {'/'.join(str(x) for x in BAND[e])} m)", f"{t} loss {li+1} ({lab}) {e} as worded",
                get(ol_, e, "drift_end_m"), get(nl_, e, "drift_end_m"), f"le:{b}", nd=4)
            add(f"{HA} P-H5 drift at end of loss (band {e} {'/'.join(str(x) for x in BAND[e])} m)", f"{t} loss {li+1} ({lab}) {e} effective",
                get(ol_, e, "effective", "drift_m"), get(nl_, e, "effective", "drift_m"), f"le:{b}", nd=4)
            if e != "EKF3":
                add(f"{HA} re-lock from the first returning fix, s", f"{t} loss {li+1} ({lab}) {e}",
                    get(ol_, e, "effective", "relock_after_first_fix_s"), get(nl_, e, "effective", "relock_after_first_fix_s"), nd=3)
                add(f"{HA} jump at re-lock, m", f"{t} loss {li+1} ({lab}) {e}", get(ol_, e, "jump_pos_m"), get(nl_, e, "jump_pos_m"), nd=4)
            dO, dN = get(ol_, e, "drift_end_m"), get(nl_, e, "drift_end_m")
            if oh[t] is not None and nh[t] is not None:   # verdict counts: flights on BOTH sides only (r3b is new-only)
                p5o[e].append(None if dO is None else dO <= b); p7o[e].append(None if ol_ is None else not get(ol_, e, "lockout"))
                p5n[e].append(None if dN is None else dN <= b); p7n[e].append(None if nl_ is None else not get(nl_, e, "lockout"))
            elif nh[t] is not None:
                h_newonly[e][0].append(None if dN is None else dN <= b); h_newonly[e][1].append(None if nl_ is None else not get(nl_, e, "lockout"))
        for x, y in (("FGO", "UKF"), ("UKF", "EKF3"), ("FGO", "EKF3")):
            g = lambda d, e: get(d, e, "drift_end_m")
            add(f"{HA} orderings (drift at end of loss, difference), m", f"{t} loss {li+1} ({lab}) {x} − {y}",
                None if None in (g(ol_, x), g(ol_, y)) else g(ol_, x) - g(ol_, y),
                None if None in (g(nl_, x), g(nl_, y)) else g(nl_, x) - g(nl_, y), "sign", nd=4)
for e in BAND:
    cnt_row("H verdicts", f"P-H5 (as worded, all losses of the flights scored on both sides) {e}", p5o[e] or None, p5n[e] or None)
    cnt_row("H verdicts", f"P-H7 no lockout (flights on both sides) {e}", p7o[e] or None, p7n[e] or None)
    if h_newonly[e][0]:   # new-only flights (s1far_r3b): reported, never compared
        cnt_row("H verdicts (new-only flights, e.g. s1far_r3b; no old value)", f"P-H5 {e}", None, h_newonly[e][0])
        cnt_row("H verdicts (new-only flights, e.g. s1far_r3b; no old value)", f"P-H7 {e}", None, h_newonly[e][1])

# ---------- F tests (METHODOLOGY verdicts) ----------
FF = ("fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3")
f1o, f1n = L(O, "f1_test.json"), L(N, "f1_test.json")
F1T = ("fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3") + FF
for arm in ("UKF_hard", "FGO_hard", "FGO_robust"):
    for m in ("yaw_max_deg", "yaw_rms_deg", "xtrack_max_m", "wrong_accepted", "correct_rejected", "lockout_episodes"):
        add("F1 (test, k = 2.385): mean over the 6 flights", f"{arm} {m}", mean([get(f1o, t, arm, m) for t in F1T]),
            mean([get(f1n, t, arm, m) for t in F1T]), nd=3)
for t in F1T:
    add("F1 orderings: FGO_robust − FGO_hard yaw max, deg", t,
        None if None in (get(f1o, t, "FGO_robust", "yaw_max_deg"), get(f1o, t, "FGO_hard", "yaw_max_deg")) else get(f1o, t, "FGO_robust", "yaw_max_deg") - get(f1o, t, "FGO_hard", "yaw_max_deg"),
        None if None in (get(f1n, t, "FGO_robust", "yaw_max_deg"), get(f1n, t, "FGO_hard", "yaw_max_deg")) else get(f1n, t, "FGO_robust", "yaw_max_deg") - get(f1n, t, "FGO_hard", "yaw_max_deg"), "sign")
add("F1 verdict", "robust_lower_yaw_max_on (flights)", get(f1o, "decision", "robust_lower_yaw_max_on"), get(f1n, "decision", "robust_lower_yaw_max_on"))
for k in ("UKF_hard", "FGO_robust"):
    add("F1 verdict", f"lockout_total {k}", get(f1o, "decision", "lockout_total", k), get(f1n, "decision", "lockout_total", k))
add("F1 verdict", "robust_FGO_better (F1 met)", get(f1o, "decision", "robust_FGO_better"), get(f1n, "decision", "robust_FGO_better"), "bool")
f2o, f2n = L(O, "f2_test.json"), L(N, "f2_test.json")
for t in FF:
    for arm in ("UKF_live", "FGO_live", "FGO_batch_hindsight"):
        for m in ("off_yaw_rms_deg", "off_xtrack_rms_m", "on_yaw_rms_deg"):
            add("F2 per flight", f"{t} {arm} {m}", get(f2o, t, arm, m), get(f2n, t, arm, m))
    g2 = lambda d, x, y: None if None in (get(d, t, x, "off_xtrack_rms_m"), get(d, t, y, "off_xtrack_rms_m")) else get(d, t, x, "off_xtrack_rms_m") - get(d, t, y, "off_xtrack_rms_m")
    add("F2 orderings (off-region cross-track RMS difference), m", f"{t} FGO batch − FGO live", g2(f2o, "FGO_batch_hindsight", "FGO_live"), g2(f2n, "FGO_batch_hindsight", "FGO_live"), "sign")
    add("F2 orderings (off-region cross-track RMS difference), m", f"{t} FGO live − UKF live", g2(f2o, "FGO_live", "UKF_live"), g2(f2n, "FGO_live", "UKF_live"), "sign")
add("F2 verdict", "hindsight_correction (F2 met)", get(f2o, "decision", "hindsight_correction"), get(f2n, "decision", "hindsight_correction"), "bool")
for tag, f, dk in (("F3", "f3_test.json", ("fgo_advantage_grows",)), ("F3b", "f3b_test.json", ("a_fgo_at_least_as_fast", "b_advantage_grows")),
                   ("F3c", "f3c_test.json", ("a_fgo_at_least_as_fast", "b_advantage_grows"))):
    fo, fn = L(O, f), L(N, f)
    deltas = [k.split("_d")[1] for k in (get(fo, FF[0]) or get(fn, FF[0]) or {}) if k.startswith("UKF_d")]
    for t in FF:
        for d_ in deltas:
            for e in ("UKF", "FGO"):
                for m in ("convergence_s", "xtrack_peak_m", "xtrack_int_60s_ms"):
                    add(f"{tag} per flight", f"{t} {e} Δ{d_} {m}", get(fo, t, f"{e}_d{d_}", m), get(fn, t, f"{e}_d{d_}", m))
            gi = lambda d: None if None in (get(d, t, f"FGO_d{d_}", "xtrack_int_60s_ms"), get(d, t, f"UKF_d{d_}", "xtrack_int_60s_ms")) else get(d, t, f"FGO_d{d_}", "xtrack_int_60s_ms") - get(d, t, f"UKF_d{d_}", "xtrack_int_60s_ms")
            add(f"{tag} orderings (FGO − UKF cross-track integral), m·s", f"{t} Δ{d_}", gi(fo), gi(fn), "sign")
        for rk in ("fgo_over_ukf_int_ratio", "ratio"):
            rov, rnv = get(fo, t, rk), get(fn, t, rk)
            if rov is not None or rnv is not None:
                rows.append((f"{tag} per flight", f"{t} {rk}", str(rov), str(rnv), "", ""))
        for bk in ("ratio_decreasing", "fgo_le_ukf_all_deltas"):
            if get(fo, t, bk) is not None or get(fn, t, bk) is not None:
                add(f"{tag} per flight", f"{t} {bk}", get(fo, t, bk), get(fn, t, bk), "bool")
    for k in dk:
        add(f"{tag} verdict", k, get(fo, "decision", k), get(fn, "decision", k), "bool")

# ---------- 2(a) (F4, §15.1): f4_test.json ----------
f4o, f4n = L(O, "f4_test.json"), L(N, "f4_test.json")
F4T = sorted(set(k for k in (f4o or {}) if k != "decision") | set(k for k in (f4n or {}) if k != "decision"))
for arm in ("UKF_hard", "FGO_hard", "FGO_robust"):
    for m in ("yaw_max_deg", "yaw_rms_deg", "xtrack_max_m", "wrong_accepted", "lockout_episodes"):
        add("2(a) (F4) mean over the usable flights", f"{arm} {m}", mean([get(f4o, t, arm, m) for t in F4T]), mean([get(f4n, t, arm, m) for t in F4T]))
for t in F4T:
    for m in ("yaw_max_deg", "xtrack_max_m"):
        g4 = lambda d: None if None in (get(d, t, "FGO_robust", m), get(d, t, "FGO_hard", m)) else get(d, t, "FGO_robust", m) - get(d, t, "FGO_hard", m)
        add(f"2(a) (F4) orderings: FGO_robust − FGO_hard", f"{t} {m}", g4(f4o), g4(f4n), "sign")
dd = ("n_flights", "n_plain", "P1_robust_lower_yaw_max_than_hard_on", "S1_robust_fewer_wrong_accepted_plain_on", "S2_robust_xtrack_max_le_hard_on")
for k in dd:
    add("2(a) (F4) verdicts", k, get(f4o, "decision", k), get(f4n, "decision", k))
for k in ("P1_pass", "S1_pass", "S2_pass"):
    add("2(a) (F4) verdicts", k, get(f4o, "decision", k), get(f4n, "decision", k), "bool")
for k in ("yaw_max_deg", "yaw_rms_deg", "xtrack_max_m"):
    add("2(a) (F4) verdicts", f"reference: robust lower than UKF on ({k})", get(f4o, "decision", "reference_robust_lower_than_UKF_on", k),
        get(f4n, "decision", "reference_robust_lower_than_UKF_on", k))
for k in ("UKF_hard", "FGO_hard", "FGO_robust"):
    add("2(a) (F4) verdicts", f"lockout_total {k}", get(f4o, "decision", "lockout_total", k), get(f4n, "decision", "lockout_total", k))

# ---------- file presence guard for the extended sections (a missing output must never read as "no change") ----------
EXT_FILES = ([("expT", "t_aggregate.json", False)] + [("expO", f"{t}.json", True) for t in OTR]
             + [("expL", f"{t}_t245.json", False) for t in LTR] + [("expH", f"{t}.json", True) for t in HTR]
             + [("", f, False) for f in ("f1_test.json", "f2_test.json", "f3_test.json", "f3b_test.json", "f3c_test.json", "f4_test.json")])
NEW_ONLY_OK = {"s1far_r3b.json"}
n_missing = 0
for sub, f, pre in EXT_FILES:
    o_ok = (pre and PS and os.path.exists(os.path.join(PS, f))) or os.path.exists(os.path.join(O, sub, f))
    n_ok = os.path.exists(os.path.join(N, sub, f))
    if o_ok and n_ok:
        continue
    if not o_ok and not n_ok and f in NEW_ONLY_OK:
        continue
    if f in NEW_ONLY_OK and n_ok:
        rows.append(("file presence (extended sections)", f"{sub}/{f}", "absent (expected: new flight)", "present", "", ""))
        continue
    n_missing += 1
    rows.append(("file presence (extended sections)", f"{sub}/{f}", "present" if o_ok else "MISSING", "present" if n_ok else "MISSING", "", "MISSING"))
    print(f"WARNING: {sub}/{f} missing on the {'new' if o_ok else 'old'} side" + ("" if o_ok or n_ok else " (and the old)"), file=sys.stderr)

# ---------- write ----------
out = ["# Consolidated re-run — old vs new (auto-generated by eval/rerun_compare.py)", "",
       f"OLD = `{O}` (pre-re-run snapshot), NEW = `{N}`. `DIRECTION` marks a changed comparison "
       "(ordering sign, arm-effect sign, verdict, side of 1 / 50% / NEES 3); see the script docstring.", ""]
sec = None
_order = {}
for r in rows:
    _order.setdefault(r[0], len(_order))
for s, q, o, n, d, f in sorted(rows, key=lambda r: _order[r[0]]):   # stable: one table per section (verdict rows interleave)
    if s != sec:
        out += ["", f"### {s}", "", "| quantity | old | new | Δ | flag |", "|---|---|---|---|---|"]; sec = s
    out.append(f"| {q} | {o} | {n} | {d} | {f} |")
nflag = sum(1 for r in rows if r[5])
out.insert(3, f"**Rows: {len(rows)}; direction flags: {nflag}.**")
open(a.md, "w").write("\n".join(out) + "\n")
if a.json:
    json.dump([dict(zip(("section", "quantity", "old", "new", "delta", "flag"), r),
                    **({"old_raw": RAW[i][0], "new_raw": RAW[i][1]} if i in RAW else {})) for i, r in enumerate(rows)],
              open(a.json, "w"), indent=1)
print(f"{len(rows)} rows, {nflag} direction flags -> {a.md}")
if n_missing:
    print(f"ERROR: {n_missing} extended-section file(s) missing on one side (rows flagged MISSING)", file=sys.stderr)
    sys.exit(3)
