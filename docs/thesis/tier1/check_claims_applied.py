#!/usr/bin/env python3
"""Read-only check of the claims application (user ruling 2026-10-24: "C1-C5: accepted as proposed"; Q2; Q3; the D17 cell).

Three parts:
  1. WORDING: each replaced old string is absent from its file and each new string is present (generated outputs and the
     hand-written files).
  2. NUMBERS: every number in the new wording of the files that NO generator writes (limitations.md, the two methodology
     fact sheets, claims_applied.md) is recomputed from the stored tier-1 verdict jsons and rounded ONCE (half away from
     zero, through the shortest decimal form, as rd() in eval/figs_thesis.py), and the resulting string must occur in the
     file. The generated outputs (T1, F7 caption, summary page 08, R1/R4 notes) carry their own exact checks in the
     generators.
  3. FROZEN: numbers.md above '## Errata' unchanged (tools/check_numbers_frozen.py).

Usage: python3 docs/thesis/tier1/check_claims_applied.py [--root DIR]   (exit 0 = all pass)"""
import argparse, json, os, subprocess, sys
from decimal import Decimal, ROUND_HALF_UP

ap = argparse.ArgumentParser(); ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
ROOT = ap.parse_args().root
T1 = os.path.join(ROOT, "docs", "thesis", "tier1"); SC = os.path.join(T1, "scores")
J = lambda f: json.load(open(os.path.join(SC, f)))
R = lambda p: open(os.path.join(ROOT, p)).read()
RES = []


def rd(v, n):
    out = str(Decimal(str(float(v))).quantize(Decimal(1).scaleb(-int(n)), rounding=ROUND_HALF_UP))
    return out[1:] if out.startswith("-") and Decimal(out) == 0 else out


def ok(kind, label, cond, detail=""):
    RES.append((kind, label, bool(cond), detail))


def has(path, s, label, kind="new wording present"):
    ok(kind, f"{label}: {path}", s in R(path), s[:100])


def lacks(path, s, label):
    ok("old wording absent", f"{label}: {path}", s not in R(path), s[:100])


# ------------------------------------------------------------------------------------------------ 1. wording
T1MD = "docs/thesis/tables/T1_scorecard.md"; IDX = "docs/thesis/figures_thesis/index.md"; SUM = "docs/thesis/summary/index_summary.md"
F33 = "docs/thesis/methodology_factsheets/3.3_estimators.md"; F35 = "docs/thesis/methodology_factsheets/3.5_experiments.md"
LIM = "docs/thesis/limitations.md"; R4 = "docs/thesis/tables/R4_information_vs_estimator.md"; R1 = "docs/thesis/tables/R1_hypothesis_scorecard.md"
WALK = "docs/thesis/summary/index_walkthrough.md"
for p, s, lab in ((T1MD, "N/A: FGO capability only (the filters have no loop closure)", "C1 T1 EKF3 cell"),
                  (T1MD, "N/A: no loop-closure equivalent (FGO capability only)", "C1 T1 UKF cell"),
                  (T1MD, "Experiment 3, FGO only: H3.1–H3.4", "C1 T1 statuses note"),
                  (T1MD, "Experiment 3, one estimator [h];", "C1 T1 by-row note"),
                  (IDX, "This is an FGO capability, not an FGO-against-filter result (the filters have no loop-closure equivalent)", "C1 F7 caption"),
                  (SUM, "Only the FGO can do this, so there is no comparison between estimators.", "C1 summary page 08"),
                  (WALK, "Only the FGO can do this, so there is no comparison between estimators.", "C1 walkthrough verbatim rows"),
                  (R4, "Experiment 3 (loop closure) has one estimator and no spread", "C1 R4 note"),
                  (F35, "An FGO capability test, not FGO vs filter (M:10456-10457).", "C1 fact sheet 3.5"),
                  (F33, "It is the largest window that met the 33 ms deployability budget", "C4/Q2 fact sheet 3.3")):
    lacks(p, s, lab)
for p, s, lab in ((T1MD, "UKF with landmark states (extension E5): bounded; ~2x FGO error [k]", "D17 cell (user wording)"),
                  (T1MD, "N/A: no landmark states (the thesis EKF3 as configured has no loop closure; EKF3 with landmark states not tested)", "C1 EKF3 cell"),
                  (T1MD, "UKF ÷ FGO live overall RMSE with loop closure 1.76–2.08× (LC live, descriptive)", "D17 footnote range"),
                  (T1MD, "an extension variant, not the UKF used elsewhere in this table", "D17 footnote"),
                  (T1MD, "H3.1–H3.4 PASS 3/3; 8 tags, correct tag IDs [k]", "C2/C3 FGO cell"),
                  ("docs/thesis/tables/T1_scorecard.tex", r"\textasciitilde{}2x FGO error", "D17 cell in TeX"),
                  (IDX, "The thesis's EKF3 and UKF, as configured, have no landmark states", "C1 F7 caption"),
                  (IDX, "H-E3.1 FAIL 0/9; 6 of 9 runs diverged", "C2 F7 caption"),
                  (IDX, "H-E2.1 PASS 3/3 in each", "C3 F7 caption"),
                  (IDX, "Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 2.9 to 4.5 times over five laps", "F7 title (user answer 3, 2026-11-02, D99; was '3–4×')"),
                  (SUM, "Only the FGO has loop closure in the thesis (its EKF3 and UKF have no landmark states).", "C1 summary page 08"),
                  (SUM, "with 4 tags and with 2 tags", "C3 summary page 08"),
                  (R4, "has one thesis estimator and no spread", "C1 R4 note"),
                  (R1, "Experiment 3 scope (claims C2 and C3", "C2/C3 R1 note"),
                  (F33, "In the corridor configuration, 0.25 s was the largest window within the 33 ms budget; on the tag-room flights 0.5 s also fitted (27–28 ms)", "Q2 (house en dash)"),
                  (F33, "No general claim is made about the largest window", "Q2 'no general claim'"),
                  (F33, "No convergence flag was raised", "C5"),
                  (F35, "the thesis's EKF3 and UKF, as configured, have no landmark states", "C1 fact sheet"),
                  (F35, "The result assumes correct re-identification (claim C2)", "C2 fact sheet"),
                  (F35, "Tag count (claim C3)", "C3 fact sheet"),
                  (LIM, "| 3 | The FGO as configured (plain least squares, tag readings ungated) is not robust to wrong tag IDs: at 1% wrong IDs, 6 of 9 "
                        "runs diverged and the remaining 3 ended 51-75x the clean error (H-E3.1 FAIL, 0/9). A robust-weighted variant avoided divergence "
                        "in all 21 runs, though one collapsed. The landmark UKF (E5) was not tested with wrong IDs. |", "Q3 verbatim, range per Q4")):
    has(p, s, lab)

# ------------------------------------------------------------------------------------------------ 2. numbers (single rounding)
E3 = J("E3_verdicts.json"); E4 = J("E4_verdicts.json"); E5 = J("e5_verdicts.json"); E2 = J("E2_verdicts.json")
h31 = [v for k, v in E3["criteria_a"].items() if k.startswith("H-E3.1")][0]
ok("number", "Q3 '0/9' and FAIL = H-E3.1", f"{h31['verdict']} {h31['count']}" == "FAIL 0/9" and "(H-E3.1 FAIL, 0/9)" in R(LIM))
ok("number", "Q3 '6 of 9 runs diverged' = H-E3.1 divergence total", h31["divergence"]["total"] == "6 of 9 runs diverged" and "6 of 9 runs diverged" in R(LIM))
ok("number", "Q3 'all 21 runs' (robust arm, 0 diverged)", E3["divergence"]["arm b"]["total"] == "0 of 21 runs diverged" and "all 21 runs" in R(LIM))
# the plain-FGO (arm a) runs that did not diverge: LC live ÷ the same flight's clean LC live
st = E3["divergence"]["per_run_status"]
rat = {n: r["values"]["lc live rmse_m"]["value"] / E3["references"][r["flight"]]["clean lc live rmse_m"]["value"]
       for n, r in E3["runs"].items() if r["arm"] == "a" and not st[n]["diverged"]}
r1 = [v for n, v in rat.items() if E3["runs"][n]["rate"] == "0.01"]
ok("number", "Q3 'the remaining 3' = 1% plain runs that did not diverge", len(r1) == 3 and len(rat) == 12, f"{len(r1)} at 1%, {len(rat)} at 1% and 5%")
ok("number", "Q3/Q4 '51-75x' = the 3 non-diverged 1% plain runs, integers", f"{rd(min(r1), 0)}-{rd(max(r1), 0)}" == "51-75" and "51-75x" in R(LIM))
ok("number", "Q4: the mis-scoped '51-85x' no longer appears in the item 3 claim text", "51-85x" not in R(LIM).split("| 3 | ",1)[1].split(" | ",1)[0])   # the claim cell only; the provenance cell records the Q4 correction
ok("number", "all 12 non-diverged plain runs, integers = 51-85 (the range the scope note keeps)", f"{rd(min(rat.values()), 0)}-{rd(max(rat.values()), 0)}" == "51-85")
ok("number", "scope note 51.26–85.49× (12 runs, 2 dp)", f"{rd(min(rat.values()), 2)}–{rd(max(rat.values()), 2)}×" in R(LIM))
ok("number", "scope note 51.26–75.23× (the 3 at 1%, 2 dp)", f"{rd(min(r1), 2)}–{rd(max(r1), 2)}×" in R(LIM))
coll = E3["runs"]["E3b_T_A_r2_0.05_s1"]["values"]["lc live rmse_m"]["value"]
ok("number", "Q3 'one collapsed' = robust T_A_r2 5% s1 (live 4.1849 m, the only robust run above 2 m)",
   rd(coll, 4) == "4.1849" and sum(r["values"]["lc live rmse_m"]["value"] > 2 for n, r in E3["runs"].items() if r["arm"] == "b") == 1
   and "T_A_r2 5% s1" in R(LIM))
w05 = [r["step_median_ms_after_anchor"] for n, r in E4["runs"].items() if n.endswith("_w0.5")]
ok("number", "Q2 '27–28 ms' = 12 E4 W = 0.5 s medians after the anchor, integers", len(w05) == 12 and f"{rd(min(w05), 0)}–{rd(max(w05), 0)} ms" == "27–28 ms" and "(27–28 ms)" in R(F33))
ok("number", "C4 P-E4.1 PASS 12/12", f"{E4['P-E4.1']['verdict']} {E4['P-E4.1']['count']}" == "PASS 12/12" and "P-E4.1 PASS 12/12" in R(F33))
ok("number", "C4 P-E4.2 PASS (12/12 at 0.25, 1, 2, 5 s)", E4["P-E4.2"]["verdict"] == "PASS" and set(E4["P-E4.2"]["counts"].values()) == {"12/12"} and "(P-E4.2 PASS)" in R(F33))
ok("number", "C4 H-E4.3 FAIL 7/12", f"{E4['H-E4.3']['verdict']} {E4['H-E4.3']['count']}" == "FAIL 7/12" and "H-E4.3 FAIL 7/12" in R(F33))
cv = E4["convergence"]["per_run"]
ok("number", "C5 largest RMS reading 0.0009 m, threshold 0.029 m, no flag, 10 cap-10 runs",
   rd(max(r["max_rms_reading_m"] for r in cv.values()), 4) == "0.0009" and E4["convergence"]["threshold_rms_m"] == 0.029
   and not any(r["NOT_CONVERGED"] for r in cv.values()) and len(cv) == 10 and "0.0009 m, against the 0.029 m threshold" in R(F33))
e5r = [E5["flights"][f]["descriptive ratios UKF/FGO"]["lc live"] for f in ("T_A_r1", "T_A_r2", "T_A_r3")]
ok("number", "C1 UKF ÷ FGO live 1.76–2.08 (fact sheet 3.5)", f"{rd(min(e5r), 2)}–{rd(max(e5r), 2)}" == "1.76–2.08" and "UKF ÷ FGO live 1.76–2.08, descriptive" in R(F35))
ok("number", "D17 '~2x' = each ratio rounded once to an integer is 2", [rd(r, 0) for r in e5r] == ["2", "2", "2"])
ok("number", "C1 H-E5.1 / S-E5.5 PASS 3/3", all(f"{E5['criteria'][k]['verdict']} {E5['criteria'][k]['count']}" == "PASS 3/3" for k in ("H-E5.1", "S-E5.5"))
   and "H-E5.1 PASS 3/3" in R(F35) and "S-E5.5 PASS 3/3" in R(F35))
b1 = [v for k, v in E3["criteria_b"].items() if k.startswith("P-E3b.1 0.01")][0]; b5 = [v for k, v in E3["criteria_b"].items() if k.startswith("P-E3b.1 0.05")][0]
ok("number", "C2 P-E3b.1 PASS 9/9 at 1% and 9/9 at 5%; 0 of 21 (fact sheet 3.5)", (b1["verdict"], b1["count"], b5["verdict"], b5["count"]) == ("PASS", "9/9", "PASS", "9/9")
   and "P-E3b.1 PASS 9/9 at 1% and 9/9 at 5%" in R(F35) and "diverged on 0 of 21 runs" in R(F35) and "6 of 9 runs diverged" in R(F35))
ok("number", "C3 H-E2.1 PASS 3/3 in B and C (fact sheet 3.5)", all(E2["criteria"]["H-E2.1"][c]["verdict"] == "PASS" and E2["criteria"]["H-E2.1"][c]["count"] == "3/3" for c in "BC")
   and "H-E2.1 PASS 3/3 in each" in R(F35))
CA = "docs/thesis/tier1/claims_applied.md"
if os.path.exists(os.path.join(ROOT, CA)):
    ca = R(CA)
    for s in ("1.76–2.08", "51.26–85.49", "51.26–75.23", "26.86–28.22", "6 of 9", "0 of 21"):
        ok("number", f"claims_applied.md carries '{s}'", s in ca)

# ------------------------------------------------------------------------------------------------ 3. frozen
fr = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_numbers_frozen.py")], capture_output=True, text=True)
ok("frozen", "numbers.md above '## Errata' unchanged", fr.returncode == 0, fr.stdout.strip()[:80])

kinds = {}
for k, lab, g, d in RES:
    kinds.setdefault(k, [0, 0]); kinds[k][0] += g; kinds[k][1] += 1
    if not g:
        print("FAIL:", k, "|", lab, "|", d)
for k, (a, b) in kinds.items():
    print(f"{k}: {a}/{b}")
n_ok = sum(r[2] for r in RES)
print(f"TOTAL {n_ok}/{len(RES)}")
sys.exit(0 if n_ok == len(RES) else 1)
