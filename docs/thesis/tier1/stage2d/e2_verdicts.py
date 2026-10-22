#!/usr/bin/env python3
"""Stage 2d: mechanical E2 verdicts (preregistration.md §1; extension experiment, pre-registered (2026-10-21; signed off
with amendments 2026-10-22)). Reads only:
  docs/thesis/tier1/scores/E2_T_{B,C,D}_r{1,2,3}.json           (l_score.py --in-root ~/thesis_data/tier1 --suffix _t245_tags...)
  eval/results/expL/T_A_r{1,2,3}_t245.json                       (stored Experiment 3 = condition A, CURRENT; P-E2.5 only)
  eval/results/expT/T_{B,C,D}_r{1,2,3}.json                      (stored Experiment 2 known-map FGO; DESCRIPTIVE ratios only)
  ~/thesis_data/tier1/T_<c>_r<i>/lc_fgo_{lc,nolc}_t245_tags.../stats.json   (invariants, keyframe failures, wall)
Writes docs/thesis/tier1/scores/E2_verdicts.json (must be new). Every comparison is on unrounded json values.
Lap 1 = per_lap_rmse_m[0], lap 5 = per_lap_rmse_m[4]."""
import json, os, sys

R = "/home/makerspace/thesis_ws"
SC = f"{R}/docs/thesis/tier1/scores"
OUT = f"{SC}/E2_verdicts.json"
IDS = {"B": [0, 1, 2, 3], "C": [0, 2], "D": [0]}
EXP_LM_NOLC = {"B": 21, "C": 11, "D": 6}      # §8: passes (tag 0: 6, each other tag: 5); reported, not a stop
if os.path.exists(OUT):
    sys.exit(f"REFUSED: {OUT} exists")
src = lambda f, k: f"json:{os.path.relpath(f, R) if f.startswith(R) else f}:{k}"
J = lambda p: json.load(open(p))
res = {"label": "extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22)",
       "flights": {}, "criteria": {}, "P-E2.5": {}, "known_map_descriptive": {}}

for c, ids in IDS.items():
    suf = "_t245_tags" + "-".join(map(str, ids))
    for r in (1, 2, 3):
        t = f"T_{c}_r{r}"
        fs, ft = f"{SC}/E2_{t}.json", f"{R}/eval/results/expT/{t}.json"
        s, e = J(fs)["tracks"], J(ft)["tracks"]
        v = {}
        for tr in ("lc live", "lc hindsight", "nolc live", "nolc hindsight"):
            assert len(s[tr]["per_lap_rmse_m"]) == 5, (t, tr)
            v[f"{tr} rmse_m"] = (s[tr]["rmse_m"], src(fs, f"tracks.{tr}.rmse_m"))
            v[f"{tr} max_m"] = (s[tr]["max_m"], src(fs, f"tracks.{tr}.max_m"))
            for i in range(5):
                v[f"{tr} lap{i+1}_m"] = (s[tr]["per_lap_rmse_m"][i], src(fs, f"tracks.{tr}.per_lap_rmse_m[{i}]"))
        v["expT FGO live rmse_m"] = (e["FGO live"]["horiz_err_m"]["rmse"], src(ft, "tracks.FGO live.horiz_err_m.rmse"))
        v["expT FGO batch rmse_m"] = (e["FGO hindsight (whole-flight batch)"]["horiz_err_m"]["rmse"],
                                     src(ft, "tracks.FGO hindsight (whole-flight batch).horiz_err_m.rmse"))
        val = lambda k: v[k][0]
        d = {"condition": c, "values": {k: {"value": a, "source": b} for k, (a, b) in v.items()}}
        d["ratio lc live lap5/lap1"] = val("lc live lap5_m") / val("lc live lap1_m")
        d["ratio nolc live lap5/lap1"] = val("nolc live lap5_m") / val("nolc live lap1_m")
        d["H-E2.1"] = val("lc live lap5_m") <= 1.5 * val("lc live lap1_m")
        d["H-E2.2"] = val("lc live rmse_m") < val("nolc live rmse_m")
        d["H-E2.3"] = val("lc hindsight rmse_m") < val("nolc hindsight rmse_m")
        d["P-E2.4"] = val("nolc live lap5_m") > 1.5 * val("nolc live lap1_m")
        d["lc live / nolc live"] = val("lc live rmse_m") / val("nolc live rmse_m")
        d["lc hindsight / nolc hindsight"] = val("lc hindsight rmse_m") / val("nolc hindsight rmse_m")
        d["lap1 lc live == lap1 nolc live"] = val("lc live lap1_m") == val("nolc live lap1_m")
        res["known_map_descriptive"][t] = {
            "E2 LC live / expT FGO live": val("lc live rmse_m") / val("expT FGO live rmse_m"),
            "E2 LC hindsight / expT FGO batch": val("lc hindsight rmse_m") / val("expT FGO batch rmse_m")}
        st, inv = {}, {}
        for m in ("lc", "nolc"):
            sf = os.path.expanduser(f"~/thesis_data/tier1/{t}/lc_fgo_{m}{suf}/stats.json")
            x = J(sf); x.pop("landmarks_final", None)
            st[m] = {"stats": sf, **{k: x.get(k) for k in ("t_anchor", "keyframes", "landmarks", "landmark_factors",
                     "raw_detections", "central", "keyframe_failures", "step_median_ms", "step_p99_ms", "wall_s")},
                     "tier1": x.get("tier1")}
        inv["t_anchor lc == nolc"] = st["lc"]["t_anchor"] == st["nolc"]["t_anchor"]
        inv["lc landmarks == n condition tags"] = st["lc"]["landmarks"] == len(ids)
        inv["nolc landmarks (expected per §8)"] = {"observed": st["nolc"]["landmarks"], "expected": EXP_LM_NOLC[c],
                                                   "equal": st["nolc"]["landmarks"] == EXP_LM_NOLC[c]}
        inv["tag_ids recorded == condition"] = all(st[m]["tier1"]["tag_ids"] == ids for m in ("lc", "nolc"))
        inv["n_filtered_out_by_tag_ids > 0 (lc, nolc)"] = [st[m]["tier1"]["n_filtered_out_by_tag_ids"] for m in ("lc", "nolc")]
        inv["raw_detections and central equal lc/nolc"] = (st["lc"]["raw_detections"] == st["nolc"]["raw_detections"]
                                                           and st["lc"]["central"] == st["nolc"]["central"])
        inv["src_dirty empty"] = all(st[m]["tier1"]["src_dirty"] == "" for m in ("lc", "nolc"))
        inv["commit"] = [st[m]["tier1"]["commit"] for m in ("lc", "nolc")]
        inv["keyframe_failures (lc, nolc)"] = [st[m]["keyframe_failures"] for m in ("lc", "nolc")]
        d["stats"] = st; d["invariants"] = inv
        res["flights"][t] = d

for c in IDS:
    fl = [f"T_{c}_r{r}" for r in (1, 2, 3)]
    for k in ("H-E2.1", "H-E2.2", "H-E2.3", "P-E2.4"):
        n = sum(res["flights"][t][k] for t in fl)
        res["criteria"].setdefault(k, {})[c] = {"per_flight": {t: res["flights"][t][k] for t in fl}, "count": f"{n}/3",
                                               "verdict": "PASS" if n == 3 else "FAIL"}

# P-E2.5: mean over 3 flights of LC live lap-5 RMSE, A (stored expL) -> B -> C -> D, non-decreasing at every step
means = {}
for c in ("A", "B", "C", "D"):
    vals = []
    for r in (1, 2, 3):
        f = f"{R}/eval/results/expL/T_A_r{r}_t245.json" if c == "A" else f"{SC}/E2_T_{c}_r{r}.json"
        vals.append((J(f)["tracks"]["lc live"]["per_lap_rmse_m"][4], src(f, "tracks.lc live.per_lap_rmse_m[4]")))
    means[c] = {"mean_m": sum(a for a, _ in vals) / 3, "values": [{"value": a, "source": b} for a, b in vals]}
steps = {f"{a}<={b}": means[a]["mean_m"] <= means[b]["mean_m"] for a, b in (("A", "B"), ("B", "C"), ("C", "D"))}
res["P-E2.5"] = {"means": means, "steps": steps, "verdict": "PASS" if all(steps.values()) else "FAIL"}
res["note"] = ("All 18 runs completed (see stats); each per-condition verdict is PASS (3/3) or FAIL. H-E2.1 PASS iff "
               "lap5 <= 1.5 x lap1; P-E2.4 PASS iff lap5 > 1.5 x lap1. Known-map ratios are DESCRIPTIVE (inputs and "
               "solvers differ). Condition D is degenerate (preregistration §1).")
json.dump(res, open(OUT, "w"), indent=1)
for t, f in res["flights"].items():
    print(t, {k: f[k] for k in ("ratio lc live lap5/lap1", "ratio nolc live lap5/lap1", "H-E2.1", "H-E2.2", "H-E2.3", "P-E2.4")})
    print("   inv", f["invariants"])
print({k: {c: (x["count"], x["verdict"]) for c, x in v.items()} for k, v in res["criteria"].items()})
print("P-E2.5", {c: m["mean_m"] for c, m in means.items()}, steps, res["P-E2.5"]["verdict"])
