#!/usr/bin/env python3
"""D15: old (eval/results_pre_d15) vs new (eval/results) for every numbers.md row the rule can move."""
import json, os, numpy as np
O, N = "eval/results_pre_d15", "eval/results"
L = lambda d, f: json.load(open(os.path.join(d, f)))
f2 = lambda v: "—" if v is None else f"{v:.2f}"
def ate(d, f, t, e):
    try: return d_[f][t]["est"][e]["ate_a_cruise"]["+0.00"] if (d_ := {f: L(d, f)["trials"]}) else None
    except KeyError: return None
print("== 6.4 forward-camera sets, textured evo -a (cruise)")
for f in ("rerun_fwdc_evo.json", "rerun_fwdplainc_evo.json", "rerun_p1c_evo.json"):
    tr = L(N, f)["trials"]
    for t in sorted(k for k in tr if "tex" in k):
        print(f"  {t:22s}", "  ".join(f"{e} {f2(ate(O,f,t,e))}->{f2(ate(N,f,t,e))}" for e in ("EKF3", "UKF", "FGO")))
print("== 6.6 Phase 4 arms, evo -a (cruise), textured, and yaw rms")
for ds in ("fwdc", "fwdplainc"):
    fe = f"phase4_{ds}_evo.json"; fa = f"phase4_{ds}_arms.json"
    tr = L(N, fe)["trials"]; ao, an = L(O, fa), L(N, fa)
    for t in sorted(k for k in tr if "tex" in k):
        ests = [e for e in tr[t]["est"] if e != "EKF3"]
        print(f"  {t:18s}", "  ".join(f"{e} {f2(ate(O,fe,t,e))}->{f2(ate(N,fe,t,e))}" for e in ests))
        print(f"  {'':18s} yaw rms:", "  ".join(f"{e} {ao[t][e]['yaw_err_rms_deg']:.2f}->{an[t][e]['yaw_err_rms_deg']:.2f}" for e in an[t] if isinstance(an[t][e], dict) and "yaw_err_rms_deg" in an[t][e]))
print("== 6.5 scale check (textured fwdc)")
so, sn = L(O, "scale_check.json"), L(N, "scale_check.json")
for t in sorted(k for k in sn if "tex" in k and k.startswith("fwdc")):
    print(f"  {t}", "  ".join(f"{e} spd {so[t][e]['speed_ratio_median']:.3f}->{sn[t][e]['speed_ratio_median']:.3f} along {so[t][e]['along_ratio_median']:.3f}->{sn[t][e]['along_ratio_median']:.3f}" for e in sn[t] if e not in ("flow",) and "speed_ratio_median" in sn[t][e]))
print("== 5b NEES (position mean), textured")
co, cn = L(O, "phase5b_consistency.json")["consistency"], L(N, "phase5b_consistency.json")["consistency"]
t0 = next(iter(cn)); print("  keys:", list(cn[t0]["UKF_heading"])[:12])
print("== 8 scores")
for s in ("rerun_p1c_score.json", "rerun_fwdc_score.json", "rerun_fwdplainc_score.json", "dsn_extra_score.json", "rerun_dsn_score.json"):
    if not os.path.exists(os.path.join(N, s)): print("  missing", s); continue
    for d, tag in ((O, "old"), (N, "new")):
        x = L(d, s); p = sum(v["primary"] == "PASS" for v in x["trials"].values())
        fails = {t: v["primary_fails"] for t, v in x["trials"].items() if v["primary"] != "PASS"}
        print(f"  {s} {tag}: {p}/{len(x['trials'])} pass; {fails}")
print("== 6.2 blank behaviour (+10/+30/+60 s |err|, blank)")
for d, tag in ((O, "old"), (N, "new")):
    b = L(d, "blank_behaviour.json"); out = {}
    for t, v in b.items():
        for arm in ("ukf", "fgo", "ukf_baseline", "fgo_baseline", "ukf_heading", "fgo_heading"):
            if arm in v and isinstance(v[arm], dict):
                k = arm.split("_")[0] + ("_heading" if arm.endswith("heading") else "") + ("|blank" if "blank" in t else "|trans")
                for h in ("+10s", "+30s", "+60s"):
                    if h in v[arm] and v[arm][h]: out.setdefault((k, h), []).append(np.hypot(v[arm][h]["along_m"], v[arm][h]["cross_m"]))
    print(" ", tag, {f"{k[0]} {k[1]}": f"{min(x):.1f}-{max(x):.1f} (n={len(x)})" for k, x in sorted(out.items())})
