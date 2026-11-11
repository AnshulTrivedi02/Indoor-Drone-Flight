#!/usr/bin/env python3
"""DIAGNOSTIC aggregator for the FGO gate-count stage 2 run sets (docs/thesis/diagnostics/
fgo_gate_count.md, D134, D137). Reads every per-run summary JSON written by
`eval/fgo_gate_count.py --run ...` under ~/thesis_data/diagnostics/fgo_gate_count/, and writes
two files under eval/results/fgo_gate_count/ (never a trial directory):

  per_run.json  -- one record per run, as written by fgo_gate_count.py (passed through, plus a
                   few derived percentages), for set 1A (15 dsn_* runs, arm=null) and set 1B
                   (54 trial x arm runs).
  per_set.json  -- set 1A grouped by floor condition (textured/blank/transition, summed over
                   repeats); set 1B grouped by (wall_type, floor, arm) -- 2 x 3 x 3 = 18 groups,
                   each summing exactly the 3 repeats r1/r2/r3.

No estimator code is touched; this script only reads the diagnostic's own output JSONs.
"""
import glob
import json
import os
import re

DIAG_ROOT = os.path.expanduser("~/thesis_data/diagnostics/fgo_gate_count")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "fgo_gate_count")

SET_1A = {"dsn_blank_r1", "dsn_blank_r2", "dsn_blank_r3",
          "dsn_tex_r1", "dsn_tex_r2", "dsn_tex_r3", "dsn_tex_r4", "dsn_tex_r5",
          "dsn_tex_r6", "dsn_tex_r7", "dsn_tex_r8", "dsn_tex_r9",
          "dsn_trans_r1", "dsn_trans_r2", "dsn_trans_r3"}
SET_1B_TRIALS = {"fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3",
                  "fwdc_trans_r1", "fwdc_trans_r2", "fwdc_trans_r3",
                  "fwdc_blank_r1", "fwdc_blank_r2", "fwdc_blank_r3",
                  "fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3",
                  "fwdplainc_trans_r1", "fwdplainc_trans_r2", "fwdplainc_trans_r3",
                  "fwdplainc_blank_r1", "fwdplainc_blank_r2", "fwdplainc_blank_r3"}
ARMS = ("baseline", "heading", "heading_yawrate")


def _floor_of(trial):
    for f in ("blank", "trans", "tex"):
        if f in trial:
            return {"tex": "textured", "trans": "transition", "blank": "blank"}[f]
    raise ValueError(trial)


def _wall_of(trial):
    return "fwdc" if trial.startswith("fwdc_") else "fwdplainc"


def _pct(n, d):
    # Full precision, no intermediate rounding: a pre-round here (e.g. round(,4)) can move a value
    # across the eventual 2dp rounding boundary used downstream (rd()), a real double-rounding bug
    # found and fixed during stage 2 (e.g. 10/1770*100 = 0.564971...%, which must round to 0.56%, not
    # 0.57%; round(,4) first gives 0.5650, which THEN rounds to 0.57%). rd() (eval/figs_thesis.py) is
    # the single rounding step; this function must not add a second one.
    return None if d == 0 else 100.0 * n / d


def load_runs():
    """Loads every *_gate_summary.json under DIAG_ROOT, classifies into set 1A / 1B / other."""
    runs = []
    for p in sorted(glob.glob(os.path.join(DIAG_ROOT, "*_gate_summary.json"))):
        with open(p) as fh:
            d = json.load(fh)
        trial = d["trial"]
        arm = d.get("arm")
        if trial in SET_1A and arm is None:
            d["_set"] = "1A"
        elif trial in SET_1B_TRIALS and arm in ARMS:
            d["_set"] = "1B"
            d["_wall"] = _wall_of(trial)
            d["_floor"] = _floor_of(trial)
        else:
            d["_set"] = "other"   # not part of the registered run set (D137); kept, not summarised
        d["_path"] = p
        flow_n = d["flow"]["n"]; range_n = d["range"]["n"]
        d["_pct"] = {
            "flow_reject_axis0_pct": _pct(d["flow"]["reject_axis_9"][0], flow_n),
            "flow_reject_axis1_pct": _pct(d["flow"]["reject_axis_9"][1], flow_n),
            "flow_reject_joint9_pct": _pct(d["flow"]["reject_joint_9"], flow_n),
            "flow_reject_joint11_83_pct": _pct(d["flow"]["reject_joint_11_83"], flow_n),
            "flow_max_onesided_pct": _pct(d["flow"]["flow_max_onesided_reject"], flow_n),
            "flow_max_twosided_pct": _pct(d["flow"]["flow_max_twosided_reject"], flow_n),
            "range_reject25_pct": _pct(d["range"]["reject_25"], range_n),
        }
        runs.append(d)
    return runs


def _sum_group(rows):
    flow_n = sum(r["flow"]["n"] for r in rows)
    range_n = sum(r["range"]["n"] for r in rows)
    ax0 = sum(r["flow"]["reject_axis_9"][0] for r in rows)
    ax1 = sum(r["flow"]["reject_axis_9"][1] for r in rows)
    j9 = sum(r["flow"]["reject_joint_9"] for r in rows)
    j1183 = sum(r["flow"]["reject_joint_11_83"] for r in rows)
    fm1 = sum(r["flow"]["flow_max_onesided_reject"] for r in rows)
    fm2 = sum(r["flow"]["flow_max_twosided_reject"] for r in rows)
    rg25 = sum(r["range"]["reject_25"] for r in rows)
    near9_0 = sum(r["flow"]["near_gate9_axis0"] for r in rows)
    near9_1 = sum(r["flow"]["near_gate9_axis1"] for r in rows)
    nearj9 = sum(r["flow"]["near_gate_joint9"] for r in rows)
    nearj1183 = sum(r["flow"]["near_gate_joint11_83"] for r in rows)
    nearrg25 = sum(r["range"]["near_gate25"] for r in rows)
    gp = sum((r.get("n_flow_gp_replaced") or 0) for r in rows)
    return {
        "n_runs": len(rows), "n_flow_factors": flow_n, "n_range_factors": range_n,
        "reject_axis_9": [ax0, ax1], "reject_joint_9": j9, "reject_joint_11_83": j1183,
        "flow_max_onesided_reject": fm1, "flow_max_twosided_reject": fm2, "range_reject_25": rg25,
        "pct": {
            "flow_reject_axis0_pct": _pct(ax0, flow_n), "flow_reject_axis1_pct": _pct(ax1, flow_n),
            "flow_reject_joint9_pct": _pct(j9, flow_n), "flow_reject_joint11_83_pct": _pct(j1183, flow_n),
            "flow_max_onesided_pct": _pct(fm1, flow_n), "flow_max_twosided_pct": _pct(fm2, flow_n),
            "range_reject25_pct": _pct(rg25, range_n),
        },
        "near_threshold": {"flow_axis0_near9": near9_0, "flow_axis1_near9": near9_1,
                           "flow_joint_near9": nearj9, "flow_joint_near11_83": nearj1183,
                           "range_near25": nearrg25},
        "n_flow_gp_replaced": gp,
        "trials": sorted({r["trial"] for r in rows}),
        "all_byte_identical_to_stored": all(r.get("instrumented_vs_stored_byte_identical") is True for r in rows),
        "n_byte_identity_checked": sum(1 for r in rows if r.get("instrumented_vs_stored_byte_identical") is not None),
    }


def build_per_set(runs):
    sets = {}
    a1 = [r for r in runs if r["_set"] == "1A"]
    for floor in ("textured", "blank", "transition"):
        rows = [r for r in a1 if _floor_of(r["trial"]) == floor]
        if rows:
            sets[f"1A_{floor}"] = _sum_group(rows)
    if a1:
        sets["1A_all"] = _sum_group(a1)

    b1 = [r for r in runs if r["_set"] == "1B"]
    for wall in ("fwdc", "fwdplainc"):
        for floor in ("textured", "blank", "transition"):
            for arm in ARMS:
                rows = [r for r in b1 if r["_wall"] == wall and r["_floor"] == floor and r["arm"] == arm]
                if rows:
                    sets[f"1B_{wall}_{floor}_{arm}"] = _sum_group(rows)
    if b1:
        sets["1B_all"] = _sum_group(b1)
    return sets


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    runs = load_runs()
    with open(os.path.join(OUT_DIR, "per_run.json"), "w") as fh:
        json.dump(runs, fh, indent=2)
    sets = build_per_set(runs)
    with open(os.path.join(OUT_DIR, "per_set.json"), "w") as fh:
        json.dump(sets, fh, indent=2)
    n1a = sum(1 for r in runs if r["_set"] == "1A")
    n1b = sum(1 for r in runs if r["_set"] == "1B")
    nother = sum(1 for r in runs if r["_set"] == "other")
    print(f"loaded {len(runs)} run summaries: set 1A={n1a}/15, set 1B={n1b}/54, other(excluded)={nother}")
    print(f"wrote {OUT_DIR}/per_run.json and {OUT_DIR}/per_set.json")
    bad = [r["trial"] + (f"_{r['arm']}" if r.get("arm") else "") for r in runs
          if r.get("instrumented_vs_stored_byte_identical") is False]
    if bad:
        print(f"STOP-WORTHY: {len(bad)} run(s) NOT byte-identical to stored: {bad}")


if __name__ == "__main__":
    main()
