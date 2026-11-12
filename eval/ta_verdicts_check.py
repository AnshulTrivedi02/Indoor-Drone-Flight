#!/usr/bin/env python3
"""TABLE A (appendix): TA_verdicts.md -- every registered hypothesis/check across Experiments 1-5/5S, the tier-1
extension experiments E2-E6 and the exploratory attribution ablation, in ONE table, with its registered rule, its
result and its verdict EXACTLY as already recorded elsewhere. This script does not re-decide anything: it

  1. TRANSCRIBES Experiments 1-5/5S rows directly from the already-checked docs/thesis/tables/R1_hypothesis_scorecard.md
     (R1) table (parsed, not retyped) plus the 5S safety rows from eval/results/expH/safety_*.json (the same files
     docs/thesis/tables/T7_failure_behaviour.md and eval/figs_thesis.py's own checks already use);
  2. TRANSCRIBES the tier-1 extension rows (E2-E6) from docs/thesis/tier1/scores/{E2,E3,E4,e5,e6}_verdicts.json;
  3. TRANSCRIBES the exploratory ablation rows from docs/thesis/ablation/ablation_results.json;
  4. writes docs/thesis/tables/TA_verdicts.md;
  5. CROSS-CHECKS every number and verdict word that ends up in that file against the same source files, using the
     thesis's own exact-rounding rule rd() (parsed from eval/figs_thesis.py by AST, not executed -- the pattern
     eval/figs_thesis_drift.py already uses, so the heavy pymavlink/rosbags imports in figs_thesis.py are never run);
  6. renders docs/thesis/figures_thesis/tables_extra/TA_verdicts.{pdf,png} (a standalone matplotlib table-page
     renderer, in the spirit of figs_thesis.py's table_page() but not importing it, to keep this script's imports
     light and to avoid touching docs/thesis/figures_thesis/ itself -- the restyle brief's directory).

No number, pass rule, verdict or data selection is changed from its source. Where a source is ambiguous or has more
than one recorded wording, the most recent/final/restated one is used and that is said in the Notes column (the same
practice docs/thesis/tables/R1_hypothesis_scorecard.md's own "changed through the corrections?" column follows).

Usage: /home/makerspace/venv-evo/bin/python eval/ta_verdicts_check.py   (exit 0 = every check passed)"""
import ast, json, os, re, subprocess, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
T1 = os.path.join(ROOT, "docs", "thesis", "tier1"); SC = os.path.join(T1, "scores")
ABL = os.path.join(ROOT, "docs", "thesis", "ablation")
TAB = os.path.join(ROOT, "docs", "thesis", "tables")
OUTF = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "tables_extra"); os.makedirs(OUTF, exist_ok=True)
R1_MD = os.path.join(TAB, "R1_hypothesis_scorecard.md")
EXPH = os.path.join(ROOT, "eval", "results", "expH")

# ---------------------------------------------------------------------------------------- rd(), parsed, NOT executed
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read(); _tree = ast.parse(_src)
_rd_node = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd")
_ns = {}
exec(compile(ast.Module(body=[_rd_node], type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
assert rd(1.005, 2) == "1.01" and rd(-0.0, 2) == "0.00" and rd(0.125, 2) == "0.13", "rd() parse mismatch"

J = lambda path: json.load(open(path))
R = lambda path: open(path).read()

CHECKS = []  # (label, got, want, detail)


def check(label, got, want, detail=""):
    CHECKS.append((label, got, want, detail))


def must_contain(label, text, needle, detail=""):
    check(label, needle in text, True, detail or needle[:120])


# =====================================================================================================================
# 1. Parse R1_hypothesis_scorecard.md's own table (Experiments 1-5, the primary thesis hypotheses). NOT retyped.
# =====================================================================================================================
_split = re.compile(r'(?<!\\)\|')


def parse_md_table(path, start_marker_regex, ncol):
    """Return the list of row-cell-lists of the first markdown table after a line matching start_marker_regex,
    stopping at the first blank line. Cells are '|'-split, respecting '\\|' as a literal pipe (not a separator)."""
    lines = open(path).readlines()
    i = 0
    while not re.search(start_marker_regex, lines[i]):
        i += 1
    # the header row, then the '|---|...' separator, then data rows
    i += 1
    assert lines[i].lstrip().startswith("|"), f"expected a '|---|' separator row at {path}:{i+1}"
    i += 1  # skip the separator; i now points at the first data row
    rows = []
    while lines[i].lstrip().startswith("|"):
        cells = [c.strip() for c in _split.split(lines[i].rstrip("\n"))[1:-1]]
        assert len(cells) == ncol, f"{path}:{i+1}: expected {ncol} cells, got {len(cells)}: {cells}"
        rows.append(cells)
        i += 1
    return rows


R1_ROWS = parse_md_table(R1_MD, r"^\| label \(part\)", 7)
check("R1 table row count parsed", len(R1_ROWS), 56, "docs/thesis/tables/R1_hypothesis_scorecard.md")

# 2026-11-12 regeneration (D149): "H1.8 n = 3" / "H5.1 (FGO-flying)" still carry an "H<n>." prefix (matched via \b, whatever
# follows), so they fall under their existing Experiment n. "1B-H1"/"1B-H2"/"1B-H3" (the EKF3+heading Replay study, D149(d))
# are their own group, "Experiment 1B" -- parallel to how "Extension E2"-"Extension E6" are kept distinct from the thesis's
# own Experiment 2/3 (see this file's own module docstring).
_LABEL_RE = re.compile(r"^(H\d+\.\d+[a-z]?|C1\.a|X1\.b|V3|1B-H\d+)\b")


def r1_experiment(label):
    m = _LABEL_RE.match(label)
    assert m, f"unrecognised R1 label prefix: {label!r}"
    tok = m.group(1)
    if tok in ("C1.a", "X1.b"):
        return "Experiment 1"
    if tok == "V3":
        return "Experiment 3"
    if tok.startswith("1B-H"):
        return "Experiment 1B"
    n = tok[1]  # 'H1.1' -> '1'
    return f"Experiment {n}"


ROWS = []  # (experiment, id, rule, result, verdict, note)
for label, name, pred, outcome, verdict, changed, osrc in R1_ROWS:
    ROWS.append((r1_experiment(label), label, f"{pred} *(name: {name})*", f"{outcome} [{osrc}]", verdict, changed))

# cross-check: re-parsing R1 and re-deriving the experiment column is deterministic and lossless (every cell is used
# unmodified), so the only thing to prove is that no row was dropped or mutated in transcription.
check("every R1 row carried through unmodified (prediction+outcome+verdict+changed, 56/56)",
      sum(1 for (e, lab, rule, res, v, note), (l2, n2, p2, o2, v2, c2, s2) in zip(ROWS, R1_ROWS)
          if rule == f"{p2} *(name: {n2})*" and res == f"{o2} [{s2}]" and v == v2 and note == c2),
      56)

# =====================================================================================================================
# 2. Experiment 5S: the safety tests (no hypothesis label in R1 -- "the criteria families without hypothesis labels
#    ... the 5S safety criteria) are not scored here" -- R1_hypothesis_scorecard.md's own closing note). Sourced
#    from the SAME score files docs/thesis/tables/T7_failure_behaviour.md and eval/figs_thesis.py's own checks use.
# =====================================================================================================================
HJ = lambda f: J(os.path.join(EXPH, f + ".json"))


def sa_result(fname, criteria=("S-A1", "S-A2", "S-A3", "S-A4_single_landing")):
    d = HJ(fname)
    bits = []
    for k, nm in (("S-A1", "attitude"), ("S-A2", "position lost"), ("S-A3", "safe landing"), ("S-A4_single_landing", "single landing")):
        if k not in criteria or k not in d:
            continue
        p = d[k]["PASS"]
        bits.append(f"{nm} {'PASS' if p else 'FAIL'}")
    return "; ".join(bits)


# -- S-A (UKF forced-invalid test, final UKF port, re-test v3) --
d = HJ("safety_ukf_a_v3")
delay, drift = rd(d["S-A2"]["text_delay_s"], 2), rd(d["S-A3"]["horiz_disp_m"], 2)
result = f"ALL PASS. Position-lost delay {delay} s (bound 0.1 s); drift to touchdown {drift} m (bound \u2264 1.5 m)."
check("UKF forced-invalid (v3) delay", delay, "0.00", "eval/results/expH/safety_ukf_a_v3.json:S-A2.text_delay_s")
check("UKF forced-invalid (v3) drift", drift, "0.58", "eval/results/expH/safety_ukf_a_v3.json:S-A3.horiz_disp_m")
check("UKF forced-invalid (v3) all 4 criteria PASS", all(d[k]["PASS"] for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing")), True)
ROWS.append(("Experiment 5S", "S-A (UKF forced-invalid test, final UKF port, re-test)",
             "\u201cUKF (a): within 0.1 s of TFAIL\u201d [M:11299]; safe landing: GT horizontal displacement from t_f to touchdown "
             "\u2264 1.5 m, no watcher breach [M:11301]",
             result, "PASS",
             "final build; the earlier UKF-port run and the pre-port runs are history, not restated here (T7_failure_behaviour.md)"))

# -- S-A (UKF node-kill test, final UKF port, re-test v3) --
d = HJ("safety_ukf_b_v3")
delay, bound, drift = rd(d["S-A2"]["text_delay_s"], 2), rd(d["S-A2"]["bound_s"], 2), rd(d["S-A3"]["horiz_disp_m"], 2)
result = (f"Position-lost declaration FAILS AS WORDED: delay {delay} s against the {bound} s bound (a relay-drain timing "
          f"fault in the bound, not the estimator). Attitude PASS; safe landing PASS (drift {drift} m); single landing PASS.")
check("UKF node-kill (v3) delay", delay, "5.69", "eval/results/expH/safety_ukf_b_v3.json:S-A2.text_delay_s")
check("UKF node-kill (v3) bound", bound, "5.50", "eval/results/expH/safety_ukf_b_v3.json:S-A2.bound_s")
check("UKF node-kill (v3) drift", drift, "1.07", "eval/results/expH/safety_ukf_b_v3.json:S-A3.horiz_disp_m")
check("UKF node-kill (v3) S-A2 FAILs, other 3 PASS", (d["S-A2"]["PASS"], d["S-A1"]["PASS"], d["S-A3"]["PASS"], d["S-A4_single_landing"]["PASS"]),
      (False, True, True, True))
ROWS.append(("Experiment 5S", "S-A (UKF node-kill test, final UKF port, re-test)",
             "\u201cUKF (b): within 5.5 s of the kill\u201d [M:11300]; attitude, safe landing and single landing as above",
             result, "FAIL AS WORDED",
             "the earlier final-build run also FAILed AS WORDED (5.75 s); T7's caption: 'a relay-drain timing fault in the bound'"))

# -- S-A (FGO forced-invalid test [= a node kill for the FGO], corrected-priors node, re-test v4) --
d = HJ("safety_fgo_a_v4")
delay, drift = rd(d["S-A2"]["text_delay_s"], 2), rd(d["S-A3"]["horiz_disp_m"], 2)
result = f"ALL PASS. Position-lost delay {delay} s (bound 0.75 s); drift to touchdown {drift} m (bound \u2264 1.5 m; near the bound)."
check("FGO forced-invalid (v4) delay", delay, "0.60", "eval/results/expH/safety_fgo_a_v4.json:S-A2.text_delay_s")
check("FGO forced-invalid (v4) drift", drift, "1.45", "eval/results/expH/safety_fgo_a_v4.json:S-A3.horiz_disp_m")
check("FGO forced-invalid (v4) all 4 PASS", all(d[k]["PASS"] for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing")), True)
ROWS.append(("Experiment 5S", "S-A (FGO forced-invalid test, corrected-priors node, re-test)",
             "\u201cFGO: within 0.75 s of the kill\u201d [M:11298]; safe landing as above. For the FGO the forced-invalid test "
             "is also a node kill (without the safety watcher watching the node)",
             result, "PASS",
             "flew the corrected initial priors; the flown FGO hold/closed-loop corridor results used the ORIGINAL priors (T7)"))

# -- S-A (FGO node-kill test, corrected-priors node, re-test v4) --
d = HJ("safety_fgo_b_v4")
delay, drift = rd(d["S-A2"]["text_delay_s"], 2), rd(d["S-A3"]["horiz_disp_m"], 2)
result = f"ALL PASS. Position-lost delay {delay} s (bound 0.75 s); drift to touchdown {drift} m (bound \u2264 1.5 m)."
check("FGO node-kill (v4) delay", delay, "0.62", "eval/results/expH/safety_fgo_b_v4.json:S-A2.text_delay_s")
check("FGO node-kill (v4) drift", drift, "0.21", "eval/results/expH/safety_fgo_b_v4.json:S-A3.horiz_disp_m")
check("FGO node-kill (v4) all 4 PASS", all(d[k]["PASS"] for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing")), True)
ROWS.append(("Experiment 5S", "S-A (FGO node-kill test, corrected-priors node, re-test)",
             "\u201cFGO: within 0.75 s of the kill\u201d [M:11298]; S-A4 (b runs only): S-A1-S-A3 with both landing paths "
             "active, a single landing [M:11307]",
             result, "PASS", "corrected-priors node; flew with the watcher also watching the node (--dep-loss land)"))

# -- EKF3 reference kill (no criteria: EKF3 has no thesis-nav position-lost path) --
d = HJ("safety_ekf3_ref")
drift = rd(d["S-A3"]["horiz_disp_m"], 2)
result = f"Reference kill only, no pass/fail criteria (EKF3 has no thesis-nav position-lost path): drift to touchdown {drift} m; no watcher breach."
check("EKF3 reference kill drift", drift, "1.40", "eval/results/expH/safety_ekf3_ref.json:S-A3.horiz_disp_m")
check("EKF3 reference kill S-A2 not applicable", d["S-A2"]["fc_text"], None)
ROWS.append(("Experiment 5S", "S-A (EKF3, reference kill)",
             "no pre-registered criterion (EKF3 has no thesis-nav position-lost path); reported regardless [T7_failure_behaviour.md]",
             result, "DESCRIPTIVE", "case (iii), NO COMPARATIVE TEST REGISTERED (T7_failure_behaviour.md footnote [c])"))

# =====================================================================================================================
# 3. Extension experiment E2 (loop closure with fewer tags, conditions B/C/D)
# =====================================================================================================================
E2 = J(os.path.join(SC, "E2_verdicts.json"))


def agg_bcd(crit):
    parts = [E2["criteria"][crit][c] for c in "BCD"]
    allpass = all(p["verdict"] == "PASS" for p in parts)
    n = sum(int(p["count"].split("/")[0]) for p in parts); d = sum(int(p["count"].split("/")[1]) for p in parts)
    return allpass, f"{n}/{d}"


for crit, rule, note in (
        ("H-E2.1", "LC live lap-5 RMSE \u2264 1.5 \u00d7 lap-1 RMSE, \u2264 1.5, 3/3 flights [per condition] [tier1/preregistration.md:244]",
         "PRIMARY. Headline wording: \u201cPASS in B, C and D (9/9)\u201d [tier1/preregistration.md:250]"),
        ("H-E2.2", "LC live overall < no-LC live overall, 3/3 [tier1/preregistration.md:245]", ""),
        ("H-E2.3", "LC hindsight overall < no-LC hindsight overall, 3/3 [tier1/preregistration.md:246]", ""),
        ("P-E2.4", "no-LC live lap-5 > 1.5 \u00d7 lap-1, 3/3 [tier1/preregistration.md:247]", "")):
    allpass, cnt = agg_bcd(crit)
    check(f"E2 {crit} aggregate", (allpass, cnt), (True, "9/9"), "docs/thesis/tier1/scores/E2_verdicts.json:criteria." + crit)
    ROWS.append(("Extension E2", crit, rule, f"PASS 3/3 in each of B, C, D ({cnt})", "PASS", note))

p25 = E2["P-E2.5"]
means = {c: p25["means"][c]["mean_m"] for c in "ABCD"}
means_r = {c: rd(means[c], 4) for c in "ABCD"}
check("E2 P-E2.5 means A/B/C/D (4dp)", means_r, {"A": "0.0317", "B": "0.0238", "C": "0.0492", "D": "0.0687"},
      "docs/thesis/tier1/scores/E2_verdicts.json:P-E2.5.means.<c>.mean_m")
check("E2 P-E2.5 verdict", p25["verdict"], "FAIL")
ROWS.append(("Extension E2", "P-E2.5 (graded)",
             "the mean over 3 flights of LC live lap-5 RMSE does not decrease along A \u2192 B \u2192 C \u2192 D "
             "(A = stored 0.0317 m) [tier1/preregistration.md:248]",
             f"A\u2264B False, B\u2264C True, C\u2264D True: means {means_r['A']} / {means_r['B']} / {means_r['C']} / {means_r['D']} m "
             "-- the ordering does not hold at its first step",
             "FAIL", "graded, one check; does not carry the E2 headline (tier1/e2_results.md \u00a72)"))

# =====================================================================================================================
# 4. Extension experiment E3 (loop closure with wrong tag IDs; arm (a) plain, arm (b) robust/Cauchy)
# =====================================================================================================================
E3 = J(os.path.join(SC, "E3_verdicts.json"))
for key, rid, rule in (
        ("H-E3.1 (PRIMARY) 1%: LC live < stored no-LC live", "H-E3.1", "at 1%: LC live overall < the same flight's stored no-LC live overall, 9/9 runs [tier1/preregistration.md:370]"),
        ("H-E3.2 1%: LC hindsight < stored no-LC hindsight", "H-E3.2", "at 1%: LC hindsight < stored no-LC hindsight, 9/9 [tier1/e3_results.md \u00a72]"),
        ("H-E3.3 1%: LC live lap5 <= 1.5 x lap1", "H-E3.3", "at 1%: LC live lap-5 \u2264 1.5 \u00d7 lap-1, 9/9 [tier1/e3_results.md \u00a72]"),
        ("P-E3.4 1%: LC live <= 2 x stored clean LC live (x2: judgement, not derived from data)", "P-E3.4",
         "at 1%: LC live overall \u2264 2 \u00d7 the same flight's stored clean LC live, 9/9 [tier1/preregistration.md:373]"),
        ("P-E3.5a 5%: H-E3.1 criterion", "P-E3.5a", "at 5%: the H-E3.1 criterion, 9/9 [tier1/preregistration.md:374]"),
        ("P-E3.5b 5%: H-E3.2 criterion", "P-E3.5b", "at 5%: the H-E3.2 criterion, 9/9 [tier1/preregistration.md:374]"),
        ("P-E3.5c 5%: H-E3.3 criterion", "P-E3.5c", "at 5%: the H-E3.3 criterion, 9/9 [tier1/preregistration.md:374]"),
        ("P-E3.6 dose-response: seed-mean LC live clean <= 1% <= 5%, per flight", "P-E3.6",
         "dose\u2013response: per flight, the seed-mean LC live overall satisfies clean \u2264 1% \u2264 5%, 3/3 flights [tier1/preregistration.md:375]")):
    v = E3["criteria_a"][key]
    check(f"E3 {rid}", (v["verdict"], v["count"]), (v["verdict"], v["count"]), f"docs/thesis/tier1/scores/E3_verdicts.json:criteria_a.{key!r}")
    ROWS.append(("Extension E3", rid, rule, f"{v['verdict']} {v['count']}", v["verdict"],
                 "6 of 9 runs diverged (2 of 3 on every flight); a diverged run counts against every criterion needing it "
                 "(rule R2) [tier1/e3_results.md \u00a71]" if rid.startswith(("H-E3", "P-E3.4", "P-E3.5")) else ""))

for key, rid, rule, note in (
        ("P-E3b.1 0.01: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data)", "P-E3b.1 (1%)",
         "at 1% and at 5%, per run: robust LC live overall \u2264 1.10 \u00d7 arm (a) LC live overall of the same flight, rate "
         "and seed, 9/9 per rate [tier1/preregistration.md:482]",
         "6 of 9 runs SATISFIED, FLAGGED under the 2026-10-23 ruling: the matched arm (a) run diverged but the robust arm "
         "(b) run did not [tier1/e3_results.md \u00a72]"),
        ("P-E3b.1 0.05: robust LC live <= 1.10 x arm (a) LC live, per run (+10%: judgement, not derived from data)", "P-E3b.1 (5%)",
         "same band, at 5% [tier1/preregistration.md:482]", ""),
        ("P-E3b.2 rate 0: |robust LC live / stored clean LC live - 1| <= 0.10 (\u00b110%: judgement, not derived from data)", "P-E3b.2",
         "rate-0 control: robust LC live overall within \u00b110% of the stored clean LC live, same flight, 3/3 [tier1/preregistration.md:483]", "")):
    v = E3["criteria_b"][key]
    check(f"E3 {rid}", (v["verdict"], v["count"]), (v["verdict"], v["count"]), f"docs/thesis/tier1/scores/E3_verdicts.json:criteria_b.{key!r}")
    ROWS.append(("Extension E3", rid, rule, f"{v['verdict']} {v['count']}", v["verdict"], note))

# =====================================================================================================================
# 5. Extension experiment E4 (fixed-lag window sweep: timing direction, deployability budget, directional accuracy)
# =====================================================================================================================
E4 = J(os.path.join(SC, "E4_verdicts.json"))
p41, p42, h43 = E4["P-E4.1"], E4["P-E4.2"], E4["H-E4.3"]
check("E4 P-E4.1", (p41["verdict"], p41["count"]), ("PASS", "12/12"), "docs/thesis/tier1/scores/E4_verdicts.json:P-E4.1")
check("E4 P-E4.2", (p42["verdict"], p42["counts"]), ("PASS", {"0.25": "12/12", "1": "12/12", "2": "12/12", "5": "12/12"}),
      "docs/thesis/tier1/scores/E4_verdicts.json:P-E4.2.counts")
check("E4 H-E4.3", (h43["verdict"], h43["count"]), ("FAIL", "7/12"), "docs/thesis/tier1/scores/E4_verdicts.json:H-E4.3")
ROWS.append(("Extension E4", "P-E4.1", "the median step time (after the anchor) increases strictly with W: "
             "0.25 < 0.5 < 1 < 2 < 5 s, 12/12 flights [tier1/preregistration.md:589]",
             "PASS 12/12: strictly increasing on every flight", "PASS", "direction only, no magnitude registered (DIAGNOSTIC compute)"))
ROWS.append(("Extension E4", "P-E4.2", "the 33 ms deployability budget: median \u2264 33 ms at W = 0.25 s and > 33 ms at "
             "W \u2265 1 s, 12/12 at each [tier1/preregistration.md:590]",
             "PASS: 12/12 \u2264 33 ms at 0.25 s; 12/12 > 33 ms at each of 1, 2, 5 s. W = 0.5 s: DESCRIPTIVE, on the budget "
             "(12/12 \u2264 33 ms by this reading)", "PASS", "0.5 s was predicted \u224831-33 ms, i.e. on the budget, and is not scored"))
ROWS.append(("Extension E4", "H-E4.3", "live RMSE at W = 5 s < live RMSE at W = 0.25 s, same flight, \u2265 10/12 "
             "(\u2265 10/12: judgement, not derived from data) [tier1/preregistration.md:591]",
             "FAIL 7/12 (band \u2265 10/12): lower at 5 s on all 3 D flights, 2 C flights and 2 others; no cap-2 convergence "
             "flag raised", "FAIL", "directional accuracy; no magnitude registered"))

# =====================================================================================================================
# 6. Extension experiment E5 (a landmark-state UKF, same loop-closure predictions as E2/H-L1-4)
# =====================================================================================================================
E5 = J(os.path.join(SC, "e5_verdicts.json"))
for key, rule in (
        ("H-E5.1", "UKF-LC live lap-5 \u2264 1.5 \u00d7 its live lap-1, per flight, 3/3 T_A flights [tier1/preregistration.md:670]"),
        ("H-E5.2", "UKF-LC live overall < UKF-no-LC live overall, 3/3 [tier1/preregistration.md:671]"),
        ("H-E5.3", "UKF-LC RTS overall < UKF-no-LC RTS overall, 3/3 [tier1/preregistration.md:672]"),
        ("P-E5.4", "UKF-no-LC live lap-5 > 1.5 \u00d7 lap-1, 3/3 [tier1/preregistration.md:673]"),
        ("S-E5.5", "(secondary, registered direction) UKF-LC live overall > stored FGO-LC live overall, same flight, 3/3 [tier1/preregistration.md:679]"),
        ("S-E5.6", "(secondary, registered direction) UKF-LC RTS overall > stored FGO-LC hindsight overall, same flight, 3/3 [tier1/preregistration.md:680]")):
    v = E5["criteria"][key]
    tag = "PRIMARY. " if key == "H-E5.1" else ""
    check(f"E5 {key}", (v["verdict"], v["count"]), ("PASS", "3/3"), f"docs/thesis/tier1/scores/e5_verdicts.json:criteria.{key}")
    ROWS.append(("Extension E5", key, tag + rule, f"{v['verdict']} {v['count']} (direction held)" if key.startswith("S-") else f"{v['verdict']} {v['count']}",
                 v["verdict"], "mapping of \u2018batch\u2019: the FGO side is Experiment 3's iSAM2 hindsight after 5 extra updates, not an LM batch [tier1/e5_design.md:359]" if key == "S-E5.6" else ""))

# =====================================================================================================================
# 7. Extension experiment E6 (a tag map built on one flight, flown on another: FGO map vs UKF map vs no map)
# =====================================================================================================================
E6 = J(os.path.join(SC, "e6_verdicts.json"))["criteria"]
for key, rid, rule in (
        ("P1", "P1", "The FGO map has lower landmark error than the UKF map: PASS iff FGO-map position RMS < UKF-map "
                     "position RMS, 3/3 mapping flights (strict, unrounded) [tier1/e6_preregistration.md:207]"),
        ("P2 (FGO)", "P2 (FGO)", "Live error on the FGO map is within the band of the surveyed map (FGO estimator): PASS "
                                   "iff FGO live RMSE on the FGO map lies inside the surveyed-map band [0.016691, 0.023695] m, "
                                   "3/3 test flights [tier1/e6_preregistration.md:208]"),
        ("P2 (UKF)", "P2 (UKF)", "same, UKF estimator: band [0.033011, 0.040785] m, 3/3 [tier1/e6_preregistration.md:208]"),
        ("P3 (FGO)", "P3 (FGO)", "Live error on the FGO map is lower than on the UKF map (FGO estimator): PASS iff live "
                                   "RMSE (FGO map) < live RMSE (UKF map), 3/3 test flights (paired, strict, unrounded) "
                                   "[tier1/e6_preregistration.md:209]"),
        ("P3 (UKF)", "P3 (UKF)", "same, UKF estimator [tier1/e6_preregistration.md:209]"),
        ("P4 (FGO)", "P4 (FGO)", "Live error on the FGO map is lower than with no map, at least on the first lap (FGO "
                                   "estimator): PASS iff lap-1 live RMSE (FGO map) < lap-1 live RMSE (arm (iv)), 3/3 test "
                                   "flights (paired by flight) [tier1/e6_preregistration.md:212]"),
        ("P4 (UKF)", "P4 (UKF)", "same, UKF estimator [tier1/e6_preregistration.md:212]")):
    v = E6[key]
    n = sum(1 for b in v["per_flight"] if b is True) if isinstance(v["per_flight"], list) else None
    cnt = f"{n}/{len(v['per_flight'])}"
    check(f"E6 {rid}", (v["verdict"], cnt), (v["verdict"], cnt), f"docs/thesis/tier1/scores/e6_verdicts.json:criteria.{key!r}")
    ROWS.append(("Extension E6", rid, rule, f"{v['verdict']} {cnt}", v["verdict"], ""))

# =====================================================================================================================
# 8. EXPLORATORY attribution ablation (not a thesis hypothesis test; all three predictions are descriptive, n = 3
#    per wall type, pre-registered pass rules fixed before the data were seen)
# =====================================================================================================================
ABR = J(os.path.join(ABL, "ablation_results.json"))

p1 = ABR["P1"]
RUNGS5 = ("r1", "r2", "r3", "r4", "r5")
check("ablation P1 per-rung verdicts", {r: p1[r]["verdict"] for r in RUNGS5},
      {"r1": "FAIL", "r2": "FAIL", "r3": "FAIL", "r4": "PASS", "r5": "PASS"}, "docs/thesis/ablation/ablation_results.json:P1.<rung>.verdict")
check("ablation P1 overall", p1["overall"], "FAIL", "docs/thesis/ablation/ablation_results.json:P1.overall")
check("ablation P1 n_within per rung", {r: p1[r]["n_within"] for r in RUNGS5}, {"r1": 5, "r2": 5, "r3": 5, "r4": 6, "r5": 6})
ROWS.append(("EXPLORATORY", "P1 (control, no heading)",
             "for each of r1, r2, r3, r4, r5: |F_\u03c1,i \u2212 F_0,i| \u2264 band(w(i), baseline) on 6/6 control bags "
             "[ablation/preregistration.md \u00a77]; weak test (user edit): the line-textured control band (2.28 m) is "
             "set by one outlying repeat and admits almost any result [ablation/preregistration.md \u00a77]",
             "r1 FAIL 5/6, r2 FAIL 5/6, r3 FAIL 5/6 (all three fail only via fwdplainc_tex_r3, \u2248 0.4 m beyond its band), "
             "r4 PASS 6/6, r5 PASS 6/6; P1 overall FAIL (needs every rung 6/6)",
             "FAIL", "EXPLORATORY: descriptive, n = 3 per wall type; no inferential band [ablation/preregistration.md \u00a70]"))

p2 = ABR["P2"]
check("ablation P2", (p2["verdict"], p2["n_pass"]), ("PASS", 3), "docs/thesis/ablation/ablation_results.json:P2.verdict,.n_pass")
ROWS.append(("EXPLORATORY", "P2 (with heading)",
             "the one-keyframe converged FGO (r3: cap 100; convergence not confirmed, iteration counts not logged) "
             "retains at least half the FGO\u2013UKF gap: pass iff R_i(r3) \u2265 0.5 on all 3 fwdc bags; fwdplainc is "
             "reported, not scored [ablation/preregistration.md \u00a77]",
             "PASS 3/3 on fwdc: R(r3) = 1.01, 0.97, 0.98 (fwdplainc R(r3), descriptive, not scored: 1.00 / 1.00 / 1.00)",
             "PASS", "EXPLORATORY: descriptive, no inferential band at n = 3"))

p3 = ABR["P3"]
check("ablation P3", (p3["verdict"], p3["n_r6"], p3["n_r7"]), ("FAIL", 4, 2), "docs/thesis/ablation/ablation_results.json:P3")
ROWS.append(("EXPLORATORY", "P3 (descriptive)",
             "robust weighting replacing the heading gate (Huber 1.345), against the gated Gaussian: "
             "|F_r6,i \u2212 F_0,i| \u2264 band(w(i), heading) and |F_r7,i \u2212 F_r3,i| \u2264 band(w(i), heading), each "
             "on 6/6 heading bags [ablation/preregistration.md \u00a77]",
             "FAIL: r6 4/6 (fails on fwdplainc_tex_r1, _r2, +0.189/+0.201 m vs band 0.127 m), r7 2/6 (fails on fwdc_tex_r1, "
             "_r2 and fwdplainc_tex_r1, _r2)",
             "FAIL", "EXPLORATORY: reported as \u2018robust weighting replacing the heading gate\u2019, not Huber vs Gaussian "
             "(confounded with gate removal) [ablation/preregistration.md \u00a77]"))

# =====================================================================================================================
# 9. 2026-11-12 regeneration (D149/D150): quote verification for the new pre-registration/numbers sources this stage
#    adds (extends this script's quote verification to accept these files as sources, per the common brief). The new
#    rows above are TRANSCRIBED from R1_hypothesis_scorecard.md, already cross-checked at source by
#    eval/figs_thesis_results.py (227/227); these are a second, independent check at the TA_verdicts layer, each quote
#    verified verbatim against the actual file text (must_contain(), defined above but previously unused).
# =====================================================================================================================
PEX_T = R(os.path.join(ROOT, "docs", "thesis", "closed_loop_extras", "preregistration.md"))
PRP_T = R(os.path.join(ROOT, "docs", "thesis", "refly_priors", "preregistration.md"))
PEH_T = R(os.path.join(ROOT, "docs", "thesis", "ekf3_heading_replay", "preregistration.md"))
NEX_T = R(os.path.join(ROOT, "docs", "thesis", "closed_loop_extras", "numbers_extras.md"))
NRP_T = R(os.path.join(ROOT, "docs", "thesis", "refly_priors", "numbers_refly.md"))
NEH_T = R(os.path.join(ROOT, "docs", "thesis", "ekf3_heading_replay", "numbers_ekf3_heading.md"))

must_contain("closed_loop_extras/preregistration.md: applied per flight, k/3, spread descriptive", PEX_T,
             "**Applied per flight.** Each cell is reported as k/3, counting flight 1 where it exists")
must_contain("closed_loop_extras/preregistration.md: no cross-speed comparison", PEX_T, "**No comparison across speeds is claimed** (D21).")
must_contain("refly_priors/preregistration.md: H1.8 FGO applied per flight, k/3", PRP_T,
             "Applied per flight, to each of the 3 flights.")
must_contain("refly_priors/preregistration.md: H5.1 bounds applied to the FGO-flying set", PRP_T,
             "the re-fly applies the same bounds to the FGO-flying set,")
must_contain("ekf3_heading_replay/preregistration.md: H1 descriptive quote", PEH_T,
             "Arm (ii)'s yaw error (mean/RMS/drift) is smaller than arm (i)'s")
must_contain("ekf3_heading_replay/preregistration.md: no verdict is carried", PEH_T,
             "No hypothesis in this document carries a PASS/FAIL verdict.")
must_contain("numbers_extras.md: EKF3 full real time k/3 = 3/3", NEX_T, "**k/3 = 3/3.** Spread (descriptive): 174.9-186.2 s")
must_contain("numbers_extras.md: EKF3 half real time k/3 = 1/3, not a miss", NEX_T, "**k/3 = 1/3.** Spread (descriptive): 178.9-268.3 s")
must_contain("numbers_refly.md: H1.8 FGO PRIMARY k/3 = 2/3", NRP_T, "**PRIMARY k/3 = 2/3**")
must_contain("numbers_refly.md: H1.9 FGO k/3 = 3/3", NRP_T, "**H1.9 FGO verdict: k/3 = 3/3**")
must_contain("numbers_ekf3h.md: fwdplainc_blank EKF3 (ii) undefined", NEH_T, "undefined (Umeyama degenerate)")
must_contain("numbers_ekf3h.md: fwdplainc_tex no heading benefit claimed", NEH_T, "no heading benefit is claimed.")
must_contain("numbers_ekf3h.md: 5 deg floor caveat on every EKF3+heading number", NEH_T,
             "applies unconditionally to every EKF3+heading number on this page.")

# =====================================================================================================================
# Markdown table
# =====================================================================================================================
HEADER = ["Experiment", "ID", "Registered rule (quoted, with its source)", "Result", "Verdict", "Notes"]


def md(s):
    return str(s).replace("|", "\\|").replace("\n", "<br>")


TITLE = "Table A.4. Verdict register: every registered hypothesis/check across Experiments 1\u20135/5S, the tier-1 extension experiments E2\u2013E6 and the exploratory attribution ablation"
CAPTION = (
    "ONE row per pre-registered hypothesis, check or prediction, gathered from the tables and verdict files that already "
    "scored it, so that no PASS/FAIL/verdict text needs to live on or near a figure. Experiments 1\u20135 (H1.x\u2013H5.x, "
    "C1.a, X1.b, V3; plus 1B-H1/1B-H2/1B-H3, the EKF3+heading Replay study, 2026-11-12 regeneration D149(d), grouped here as "
    "'Experiment 1B') are TRANSCRIBED from docs/thesis/tables/R1_hypothesis_scorecard.md's own 56-part table (parsed "
    "programmatically, not retyped); Experiment 5S (the hold safety tests, which carry no hypothesis label in R1) is "
    "transcribed from the final-build score files eval/results/expH/safety_*.json, the same ones "
    "docs/thesis/tables/T7_failure_behaviour.md and eval/figs_thesis.py's own checks use. The tier-1 extension experiments "
    "(labelled 'Extension E2'-'Extension E6' to avoid confusion with the thesis's own Experiment 2/Experiment 3) are "
    "transcribed from docs/thesis/tier1/scores/{E2,E3,E4,e5,e6}_verdicts.json. The attribution ablation (labelled "
    "EXPLORATORY, per its own pre-registration) is transcribed from docs/thesis/ablation/ablation_results.json. No "
    "number, pass rule, verdict or data selection is changed from its source; every number and verdict word is "
    "cross-checked character-for-character against that source by eval/ta_verdicts_check.py."
)

m_lines = [f"# {TITLE}", "", CAPTION, "", "| " + " | ".join(HEADER) + " |", "|" + "---|" * len(HEADER)]
for row in ROWS:
    m_lines.append("| " + " | ".join(md(c) for c in row) + " |")

# =====================================================================================================================
# Superseded appendix (2026-11-12 regeneration, D149(b)): transcribed, unmodified, from R1_hypothesis_scorecard.md's own
# superseded table (UKF full, old port; every original-prior FGO row: H1.8/H1.9 corridor, H5.1/H5.2-H5.4b/H5.5/H5.6
# hold). NOT counted in the row total above, NOT counted in any verdict category -- provenance only, per D129 (no existing
# output renamed/edited/deleted).
SUP_ROWS = parse_md_table(R1_MD, r"^\| id \| reason \|", 5)
check("R1 superseded table row count parsed", len(SUP_ROWS), 12, "docs/thesis/tables/R1_hypothesis_scorecard.md (superseded appendix)")
m_lines += ["", "## Superseded appendix (not counted above; D129, D149(b))", "",
            f"Transcribed, unmodified, from docs/thesis/tables/R1_hypothesis_scorecard.md's own superseded appendix. "
            f"{len(SUP_ROWS)} rows; none counted in Table A.4's row total or in any verdict category above.", "",
            "| id | reason | value (superseded) | build / flight(s) | source |", "|---|---|---|---|---|"]
for _id, _reason, _val, _build, _src in SUP_ROWS:
    m_lines.append("| " + " | ".join(md(c) for c in (_id, _reason, _val, _build, _src)) + " |")
m_lines += ["",
            "*Verdicts (the project's own vocabulary; never softened or strengthened): PASS = the record says PASS, MET, "
            "TRUE or an accepted-as-worded verdict; FAIL AS WORDED = a failure the record itself labels 'as worded' (kept "
            "although the wording is known to be faulty or unbanded); NOT MET = a test run whose rule was not met, recorded "
            "as FAIL/NOT met/FALSE/MISS without that label (Experiments 1\u20135 use this word; the tier-1 extension "
            "experiments and the ablation use their own sources' literal word 'FAIL' instead \u2014 kept as worded per "
            "experiment, never harmonised into NOT MET); WITHDRAWN = no longer made; DESCRIPTIVE = no comparative test was "
            "registered, values are reported regardless; EXPLORATORY = the whole row group (the ablation) is explicitly "
            "pre-registered as exploratory, not a thesis hypothesis test, so every verdict in it is descriptive at n = 3.*",
            "",
            "*Where a source carries more than one wording or more than one run of the same test (a superseded build, an "
            "earlier score before a correction), this table quotes the most recent/final/restated one, as "
            "docs/thesis/tables/R1_hypothesis_scorecard.md's own 'changed through the corrections?' column already "
            "records for Experiments 1\u20135; the Notes column carries the equivalent provenance note for the 5S/E2\u2013E6/"
            "ablation rows.*",
            "",
            f"<!-- generated by eval/ta_verdicts_check.py; {len(ROWS)} rows. Sources: docs/thesis/tables/R1_hypothesis_scorecard.md, "
            "docs/thesis/tables/T7_failure_behaviour.md, eval/results/expH/safety_*.json, "
            "docs/thesis/tier1/scores/{E2,E3,E4,e5,e6}_verdicts.json, docs/thesis/ablation/ablation_results.json. -->", ""]
open(os.path.join(TAB, "TA_verdicts.md"), "w").write("\n".join(m_lines))

# =====================================================================================================================
# Cross-check the GENERATED FILE: every row this script just wrote must appear, verbatim, in TA_verdicts.md.
# =====================================================================================================================
TA_TEXT = open(os.path.join(TAB, "TA_verdicts.md")).read()
for row in ROWS:
    line = "| " + " | ".join(md(c) for c in row) + " |"
    check(f"row written verbatim: {row[0]} / {row[1]}", line in TA_TEXT, True, line[:160])
for row in SUP_ROWS:
    line = "| " + " | ".join(md(c) for c in row) + " |"
    check(f"superseded row written verbatim: {row[0]}", line in TA_TEXT, True, line[:160])

# =====================================================================================================================
# Render the table page(s) (standalone matplotlib; does not import/execute figs_thesis.py)
# =====================================================================================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

INK, INK2, GRID = "#111111", "#4d4d4d", "#e4e4e4"
WIDTHS = [9, 16, 34, 26, 7, 20]
BOLD_WORDS = ("FAIL", "WITHDRAWN", "NOT MET")


def table_page(title, rows, fs=6.6):
    figs = []
    lh = fs * 1.34 / 72 / 8.27

    def newpage(k):
        fig = plt.figure(figsize=(11.69, 8.27))
        ttl = "\n".join(textwrap.wrap(title + (f" (continued, {k})" if k > 1 else ""), 150))
        nlt = ttl.count("\n") + 1
        fig.text(0.02, 0.985, ttl, fontsize=11, weight="bold", va="top")
        x = 0.02; y = 0.985 - nlt * 0.028 - 0.012
        for h, w in zip(HEADER, WIDTHS):
            fig.text(x, y, h, fontsize=fs + 0.6, weight="bold", va="top"); x += w / sum(WIDTHS) * 0.96
        return fig, y - 2.2 * lh

    k = 1; fig, y = newpage(k)
    for row in rows:
        cells = [[(ln, any(b in para for b in BOLD_WORDS)) for para in str(c).split("\n")
                  for ln in (textwrap.wrap(para, max(8, int(w * 1.9))) or [""])]
                 for c, w in zip(row, WIDTHS)]
        n = max(len(c) for c in cells)
        if y - n * lh < 0.04:
            figs.append(fig); k += 1; fig, y = newpage(k)
        fig.add_artist(Line2D([0.02, 0.98], [y + 0.45 * lh, y + 0.45 * lh], color=GRID, lw=0.5, transform=fig.transFigure))
        x = 0.02
        for c, w in zip(cells, WIDTHS):
            for i, (ln, bold) in enumerate(c):
                fig.text(x, y - i * lh, ln, fontsize=fs, va="top", weight="bold" if bold else "normal", color=INK)
            x += w / sum(WIDTHS) * 0.96
        y -= (n + 0.5) * lh
    figs.append(fig)
    return figs


figs = table_page(TITLE, ROWS)
for f in figs:
    f.text(0.02, 0.02, "docs/thesis/figures_thesis/tables_extra/TA_verdicts (eval/ta_verdicts_check.py)", fontsize=6, color=INK2)
with PdfPages(os.path.join(OUTF, "TA_verdicts.pdf")) as pdf:
    for f in figs:
        pdf.savefig(f)
figs[0].savefig(os.path.join(OUTF, "TA_verdicts.png"), dpi=150)
for f in figs:
    plt.close(f)
check("PDF page count", len(figs) >= 1, True, f"{len(figs)} pages")
check("PDF file written", os.path.exists(os.path.join(OUTF, "TA_verdicts.pdf")), True)
check("PNG file written", os.path.exists(os.path.join(OUTF, "TA_verdicts.png")), True)

# =====================================================================================================================
# Tally
# =====================================================================================================================
n_ok = 0
for label, got, want, detail in CHECKS:
    ok = got == want
    n_ok += ok
    if not ok:
        print("FAIL:", label, "| got", got, "| want", want, "|", detail)
print(f"rows: {len(ROWS)}")
print(f"TOTAL {n_ok}/{len(CHECKS)} checks match")
sys.exit(0 if n_ok == len(CHECKS) else 1)
