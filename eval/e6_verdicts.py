#!/usr/bin/env python3
"""E6 verdicts (docs/thesis/tier1/e6_preregistration.md §5, as worded; written in Stage 1 before any test run, D82).

Inputs (read only): docs/thesis/tier1/scores/e6_T_A_r{1,2,3}.json (eval/e6_score.py), the map errors
~/thesis_data/tier1/e6/maps/<mapping trial>/map_errors.json (eval/e6_maps.py), and the stored Experiment 2 scores
eval/results/expT/T_A_r{1,2,3}.json (the P2 band). Pairing (D74): mapping flight E6M_fig8_rk -> test flight T_A_rk
(override with --pair, e.g. after a re-flight: --pair 1=E6M_fig8_r1b).
Rules (§5): every criterion on 3/3; strict comparisons on unrounded values; PASS iff all three hold, FAIL iff all three
are present and any fails; NOT RUN if an input is missing (a crash or a gate failure is recorded by hand as NOT MET,
preregistration.md §0.5). P2-P4 per test estimator (UKF, FGO) separately. Descriptive values have no verdict.
Usage: e6_verdicts.py --json docs/thesis/tier1/scores/e6_verdicts.json  (a NEW file)"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.join(HERE, "..")
ap = argparse.ArgumentParser(); ap.add_argument("--json", required=True); ap.add_argument("--pair", action="append", default=[])
a = ap.parse_args()
if os.path.exists(a.json):
    sys.exit(f"[e6] REFUSED: {a.json} exists")
PAIR = {k: f"E6M_fig8_r{k}" for k in (1, 2, 3)}
for p in a.pair:
    k, m = p.split("="); PAIR[int(k)] = m
SC = os.path.join(REPO, "docs", "thesis", "tier1", "scores"); MAPS = os.path.expanduser("~/thesis_data/tier1/e6/maps")


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


def verdict(vals):
    if any(v is None for v in vals):
        return "NOT RUN"
    return "PASS" if all(vals) else "FAIL"


out = {"pairs": {f"T_A_r{k}": PAIR[k] for k in PAIR}, "criteria": {}, "flights": {}}
# ---- P2 bands from the stored arm (i) live repeats (json:expT, unrounded) ----
band = {}
for est, trk in (("FGO", "FGO live"), ("UKF", "UKF live")):
    v = [json.load(open(os.path.join(REPO, "eval", "results", "expT", f"T_A_r{k}.json")))["tracks"][trk]["horiz_err_m"]["rmse"] for k in (1, 2, 3)]
    R = max(v) - min(v); band[est] = {"stored": v, "R": R, "lo": min(v) - R, "hi": max(v) + R}
out["p2_bands_m"] = band
# ---- P1 ----
p1 = []
for k in (1, 2, 3):
    me = load(os.path.join(MAPS, PAIR[k], "map_errors.json"))
    f = None if me is None else me["errors"]["fgo"]["pos_rms_m"]; u = None if me is None else me["errors"]["ukf"]["pos_rms_m"]
    out["flights"].setdefault(f"T_A_r{k}", {})["map"] = {"mapping_trial": PAIR[k], "fgo_map_pos_rms_m": f, "ukf_map_pos_rms_m": u,
                                                         "ukf_over_fgo": None if me is None else u / f}
    p1.append(None if me is None else f < u)
out["criteria"]["P1"] = {"criterion": "FGO-map position RMS < UKF-map position RMS, 3/3 mapping flights", "per_flight": p1,
                         "verdict": verdict(p1)}
# ---- P2-P4 per estimator ----
A_I, A_II, A_III, A_IV = "(i) surveyed", "(ii) FGO map", "(iii) UKF map", "(iv) no map, LC online"
for est in ("FGO", "UKF"):
    p2, p3, p4 = [], [], []
    for k in (1, 2, 3):
        s = load(os.path.join(SC, f"e6_T_A_r{k}.json")); fl = out["flights"].setdefault(f"T_A_r{k}", {}); d = {}
        g = lambda arm, kind: (None if s is None else s["tracks"].get(f"{arm} | {est} {kind}"))
        ok = lambda t: t is not None and "rmse_m" in t
        i_l, ii_l, iii_l, iv_l = g(A_I, "live"), g(A_II, "live"), g(A_III, "live"), g(A_IV, "live")
        if s is not None and s.get("fgo_map_name") not in (None, f"fgomap_{PAIR[k]}"):
            sys.exit(f"[e6] T_A_r{k}: scored map name {s.get('fgo_map_name')} does not match the pairing {PAIR[k]}")
        p2.append(band[est]["lo"] <= ii_l["rmse_m"] <= band[est]["hi"] if ok(ii_l) else None)
        p3.append(ii_l["rmse_m"] < iii_l["rmse_m"] if ok(ii_l) and ok(iii_l) else None)
        p4.append(ii_l["per_lap_rmse_m"][0] < iv_l["per_lap_rmse_m"][0] if ok(ii_l) and ok(iv_l) else None)
        for arm in (A_I, A_II, A_III, A_IV):
            for kind in ("live", "hindsight"):
                t = g(arm, kind)
                if ok(t):
                    d[f"{arm} | {kind}"] = {"rmse_m": t["rmse_m"], "max_m": t["max_m"], "lap1_m": t["per_lap_rmse_m"][0],
                                            "lap5_m": t["per_lap_rmse_m"][-1], "lap5_over_lap1": t["lap5_over_lap1"]}
        if ok(ii_l):
            d["descriptive"] = {"FGO map / surveyed, live": ii_l["rmse_m"] / i_l["rmse_m"] if ok(i_l) else None,
                                "FGO map / UKF map, live": ii_l["rmse_m"] / iii_l["rmse_m"] if ok(iii_l) else None,
                                "P4-overall: FGO map live / no map live (overall window)": ii_l["rmse_m"] / iv_l["rmse_m"] if ok(iv_l) else None,
                                "P4-overall direction (FGO map lower)": ii_l["rmse_m"] < iv_l["rmse_m"] if ok(iv_l) else None}
        fl[est] = d
    out["criteria"][f"P2 ({est})"] = {"criterion": f"{est} live RMSE on the FGO map within the surveyed band "
                                      f"[{band[est]['lo']:.6f}, {band[est]['hi']:.6f}] m, 3/3", "per_flight": p2, "verdict": verdict(p2)}
    out["criteria"][f"P3 ({est})"] = {"criterion": f"{est} live RMSE, FGO map < UKF map, 3/3", "per_flight": p3, "verdict": verdict(p3)}
    out["criteria"][f"P4 ({est})"] = {"criterion": f"{est} lap-1 live RMSE, FGO map < no map (iv), 3/3", "per_flight": p4, "verdict": verdict(p4)}
for c, v in out["criteria"].items():
    print(f"{c:10s} {v['verdict']:8s} {v['per_flight']}")
json.dump(out, open(a.json, "w"), indent=1)
