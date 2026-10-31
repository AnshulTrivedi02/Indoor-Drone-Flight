#!/usr/bin/env python3
"""Render docs/thesis/tier1/e6_results.md from the template e6/e6_results_template.md, filling every number from the
score jsons / stats.json / guard reports, each rounded ONCE by rd() (e6_tables.py). Writes only e6_results.md."""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e6_tables as T

R = T.R; T1D = os.path.join(R, "docs", "thesis", "tier1")
rd = T.rd; A = T.ARMS


def rng(vals, nd=4, unit=" m"):
    return f"{rd(min(vals), nd)}–{rd(max(vals), nd)}{unit}"


def F(arm, est, kind, lap1=False):
    return [T.tr(k, arm, est, kind)["per_lap_rmse_m"][0] if lap1 else T.tr(k, arm, est, kind)["rmse_m"] for k in (1, 2, 3)]


def values():
    V = T.V; m = [V["flights"][f"T_A_r{k}"]["map"] for k in (1, 2, 3)]
    b = V["p2_bands_m"]["UKF"]; ukf_r1 = T.tr(1, A[1], "UKF", "live")["rmse_m"]
    ratio = lambda est, a1, a2: [T.tr(k, a1, est, "live")["rmse_m"] / T.tr(k, a2, est, "live")["rmse_m"] for k in (1, 2, 3)]
    bs = [json.load(open(p))["batch_s"] for p in sorted(glob.glob(os.path.expanduser("~/thesis_data/tier1/T_A_r*/room_fgo_e6_*/stats.json")))]
    assert len(bs) == 6
    v = {
        "p1_r1b": f"{rd(m[0]['fgo_map_pos_rms_m'])} m against {rd(m[0]['ukf_map_pos_rms_m'])} m",
        "p2_ukf_r1": f"{rd(ukf_r1)} m against an upper edge of {rd(b['hi'])} m",
        "p4o_fgo": rng(ratio("FGO", A[1], A[3]), 2, ""), "p4o_ukf": rng(ratio("UKF", A[1], A[3]), 2, ""),
        "l1_fgo_map": rng(F(A[1], "FGO", "live", True)), "l1_fgo_iv": rng(F(A[3], "FGO", "live", True)),
        "l1_ukf_map": rng(F(A[1], "UKF", "live", True)), "l1_ukf_iv": rng(F(A[3], "UKF", "live", True)),
        "map_fgo": rng([x["fgo_map_pos_rms_m"] for x in m]), "map_ukf": rng([x["ukf_map_pos_rms_m"] for x in m]),
        "r_fgo": rng(ratio("FGO", A[1], A[0]), 2, ""), "r_ukf": rng(ratio("UKF", A[1], A[0]), 2, ""),
        "hs_fgo_map": rng(F(A[1], "FGO", "hindsight")), "hs_fgo_i": rng(F(A[0], "FGO", "hindsight")),
        "r1b_diff": f"{rd(abs(m[0]['fgo_map_pos_rms_m'] - m[0]['ukf_map_pos_rms_m']))} m",
        "batch": rng(bs, 1, " s"),
        "hs_fgo_iv": rng(F(A[3], "FGO", "hindsight")), "hs_fgo_maps": rng(F(A[1], "FGO", "hindsight") + F(A[2], "FGO", "hindsight")),
        "n_hs_fgo": sum(T.tr(k, A[3], "FGO", "hindsight")["rmse_m"] < min(T.tr(k, A[1], "FGO", "hindsight")["rmse_m"], T.tr(k, A[2], "FGO", "hindsight")["rmse_m"]) for k in (1, 2, 3)),
        "hs_ukf_iv": rng(F(A[3], "UKF", "hindsight")), "hs_ukf_fmap": rng(F(A[1], "UKF", "hindsight")), "ukf_i": rng(F(A[0], "UKF", "live")),
    }
    return v


def guard_rows():
    rows = []
    for lab, pat in (("before Stage 2", "stage2_pre"), ("after 2a (UKF replays)", "stage2a_post"),
                     ("after 2b (FGO replays)", "stage2b_post"), ("after scoring and verdicts", "stage2c_scoring_post"),
                     ("after the results write-up", "stage2d_docs_post"),
                     ("after the final cross-check revision", "stage2e_final_post")):
        p = sorted(glob.glob(os.path.join(T1D, f"frozen_manifest_20261022T002851_verify_e6_{pat}_*.json")))
        if not p:
            continue
        g = json.load(open(p[-1]))
        rows.append(f"| {lab} ({g['verified_local'][:16].replace('T', ' ')} AEDT) | **{g['verdict']}**, {g['n_files_checked']:,} files | `{os.path.basename(p[-1])}` |")
    return "\n".join(rows)


if __name__ == "__main__":
    t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e6_results_template.md")).read()
    d = {k: "\n".join(f()) for k, f in T.TABLES.items()}; d.update(values()); d["guard"] = guard_rows()
    open(os.path.join(T1D, "e6_results.md"), "w").write(t.format(**d))
    print("wrote e6_results.md")
