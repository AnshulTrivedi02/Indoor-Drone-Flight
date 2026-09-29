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
Usage: python3 eval/rerun_compare.py OLD_DIR NEW_DIR --md OUT.md [--json OUT.json]
"""
import argparse, json, math, os, statistics as st

WORLDS = ("tex", "trans", "blank")
ap = argparse.ArgumentParser(); ap.add_argument("old"); ap.add_argument("new")
ap.add_argument("--md", required=True); ap.add_argument("--json"); a = ap.parse_args()


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
    delta = (new - old) if isinstance(old, (int, float)) and isinstance(new, (int, float)) and not isinstance(old, bool) else None
    rows.append((sec, q, fmt(old, nd), fmt(new, nd), fmt(delta, nd) if delta is not None else "", flag))


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

# ---------- write ----------
out = ["# Consolidated re-run — old vs new (auto-generated by eval/rerun_compare.py)", "",
       f"OLD = `{O}` (pre-re-run snapshot), NEW = `{N}`. `DIRECTION` marks a changed comparison "
       "(ordering sign, arm-effect sign, verdict, side of 1 / 50% / NEES 3); see the script docstring.", ""]
sec = None
for s, q, o, n, d, f in rows:
    if s != sec:
        out += ["", f"### {s}", "", "| quantity | old | new | Δ | flag |", "|---|---|---|---|---|"]; sec = s
    out.append(f"| {q} | {o} | {n} | {d} | {f} |")
nflag = sum(1 for r in rows if r[5])
out.insert(3, f"**Rows: {len(rows)}; direction flags: {nflag}.**")
open(a.md, "w").write("\n".join(out) + "\n")
if a.json:
    json.dump([dict(zip(("section", "quantity", "old", "new", "delta", "flag"), r)) for r in rows], open(a.json, "w"), indent=1)
print(f"{len(rows)} rows, {nflag} direction flags -> {a.md}")
