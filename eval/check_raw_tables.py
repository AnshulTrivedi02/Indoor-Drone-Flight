#!/usr/bin/env python3
"""Exact cross-check for the raw (DESCRIPTIVE) columns/rows added to docs/thesis/tables/{T1_scorecard,T2_accuracy_heading,
T9_1A_fitted_vs_raw}.md and docs/thesis/tables/R4_information_vs_estimator.md (raw-tables stage 2, 2026-11-02; D106/D107/D111,
user ruling "option 1 on fitted results"). stdlib + json only (ast, hashlib, json, os, re, sys, decimal - no third-party
imports), per the brief.

This checker is INDEPENDENT of eval/figs_thesis.py and eval/figs_thesis_results.py: every raw/median/range value is
recomputed here straight from eval/results/raw_corridor_errors.json (never imported from, or compared against, those
generators' own in-memory strings), using rd() parsed (not executed as a module) from eval/figs_thesis.py, exactly as
docs/thesis/raw_corridor/check_raw_corridor.py already does for the numbers file these tables draw from.

Checks:
  1. rd()'s source SHA-256 matches the one recorded in eval/results/raw_corridor_errors.json (same rounding rule
     everywhere; that json's own SHA matches docs/thesis/raw_corridor/raw_corridor_numbers.md's, per that file's own
     check_raw_corridor.py).
  2. Every raw cell printed in T1/T2/T9/R4 equals rd(json value, 2) (or rd(median/range, 2)), compared as a WHOLE cell
     (markdown row split on unescaped '|', matched by row label/estimator - not a substring search, so a value that
     happens to be a substring of a different, unrelated number cannot pass).
  3. Every aligned (registered) cell these same checks touch is INDEPENDENTLY recomputed from the registered result
     files (rerun_dsn_evo.json, dsn_extra_evo.json, phase4_fwdc_evo.json) and compared the same way - catching an
     aligned/raw column swap, not just a wrong raw number.
  4. T9's two numbers.md citations (the fitted medians at :236, the UKF fitted range at :232) are checked against the
     ACTUAL numbers.md file content at those line numbers, not merely typed into a note.
  5. A negative control: an independently perturbed value is asserted to make a cell-equality check FAIL, proving the
     comparison is not vacuously true (e.g. from a typo making an "expected" string equal to itself only trivially).

Exit 0 iff every check passes (negative control's own failure is REQUIRED, not counted as a check failure).
"""
import ast, hashlib, json, os, re, sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results")
TAB = os.path.join(ROOT, "docs", "thesis", "tables")
NUMBERS_MD = os.path.join(ROOT, "docs", "thesis", "numbers.md")

# ------------------------------------------------------------------------------------- rd(), parsed (not hand-copied)
FT = os.path.join(ROOT, "eval", "figs_thesis.py")
_src = open(FT).read()
_tree = ast.parse(_src)
_rd_node = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd")
_rd_src = ast.get_source_segment(_src, _rd_node)
_ns = {}
exec(compile(ast.Module(body=[_rd_node], type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
RD_SHA = hashlib.sha256(_rd_src.encode()).hexdigest()

n_ok = n_fail = 0


def check(label, ok, extra=""):
    global n_ok, n_fail
    if ok:
        n_ok += 1
    else:
        n_fail += 1
        print(f"FAIL: {label} {extra}")
    return ok


def rng(vals, n=2):
    return f"{rd(min(vals), n)}–{rd(max(vals), n)}"


def med(vals):
    import statistics
    return float(statistics.median(vals))


# ------------------------------------------------------------------------------------- load the raw json (one source of truth)
RAWJ = json.load(open(os.path.join(RES, "raw_corridor_errors.json")))
check("rd() SHA-256 matches raw_corridor_errors.json's own recorded SHA (same rounding rule everywhere)",
      RD_SHA == RAWJ["rd_sha256"], f"{RD_SHA} vs {RAWJ['rd_sha256']}")
RAWIDX = {}
for c in RAWJ["cells"]:
    k = (c["trial"], c["estimator"], c["arm"])
    assert k not in RAWIDX, f"duplicate cell {k}"
    RAWIDX[k] = c


def raw3d(trial, est, arm="baseline"):
    c = RAWIDX[(trial, est, arm)]
    assert "raw" in c, f"no raw value for {trial}/{est}/{arm}"
    return c["raw"]["rms_3d_m"], c["raw"]["end_3d_m"]


def stored_ate(trial, est, arm="baseline"):
    return RAWIDX[(trial, est, arm)]["stored_ate_a_cruise"]


EST = ("EKF3", "UKF", "FGO")

# ------------------------------------------------------------------------------------- registered (aligned) result files
def L(f):
    return json.load(open(os.path.join(RES, f)))


DSN_SRC = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
DSN = {e: [(i, DSN_SRC[f"dsn_tex_r{i}"]["est"][e]["ate_a_cruise"]["+0.00"]) for i in range(1, 10)
           if e in DSN_SRC[f"dsn_tex_r{i}"]["est"]] for e in EST}
MED = {e: med([v for _, v in DSN[e]]) for e in EST}
_T1A_TR = [f"dsn_tex_r{i}" for i in range(1, 10)]

P4_FWDC = L("phase4_fwdc_evo.json")["trials"]
P4_FWDPC = L("phase4_fwdplainc_evo.json")["trials"]
_T2_FWDC_TR = [f"fwdc_tex_r{r}" for r in (1, 2, 3)]
_T2_FWDPC_TR = [f"fwdplainc_tex_r{r}" for r in (1, 2, 3)]


def p4_val(ds, r, key):
    d = P4_FWDC if ds == "fwdc" else P4_FWDPC
    return d[f"{ds}_tex_r{r}"]["est"][key]["ate_a_cruise"]["+0.00"]


BK = {"EKF3": "EKF3", "UKF": "UKF_baseline", "FGO": "FGO_baseline"}

# ------------------------------------------------------------------------------------- markdown row splitting (positional,
# never substring): each data row is "| c0 | c1 | ... | cN |"; split on unescaped '|' only.
_SPLIT = re.compile(r"(?<!\\)\|")


def md_rows(path):
    rows = []
    for line in open(path, encoding="utf-8").read().split("\n"):
        line = line.strip()
        if not line.startswith("|") or set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        if re.fullmatch(r"\|[-:\s|]+\|", line):
            continue
        cells = [c.strip() for c in _SPLIT.split(line)][1:-1]
        rows.append(cells)
    return rows


def cell_eq(got, expect, label):
    return check(label, got == expect, f"got {got!r} expected {expect!r}")


_T1B_TR = [f"{ds}_tex_r{r}" for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)]
NUM_LINES = open(NUMBERS_MD, encoding="utf-8").read().split("\n")


def _rl(ds, est, arm, key):
    return " / ".join(rd(raw3d(f"{ds}_tex_r{r}", est, arm)[0 if key == "rms" else 1], 2) for r in (1, 2, 3))


# =================================================================================== T1_scorecard.md
def check_t1(path, record=check):
    c = record
    T1 = md_rows(path)
    t1_1a_raw = next(r for r in T1 if r and r[0].startswith("Experiment 1A: raw world-frame error"))
    t1_1b_raw = next(r for r in T1 if r and r[0].startswith("Experiment 1B: raw world-frame error"))
    for j, e in enumerate(EST, start=1):
        exp_rms = [raw3d(t, e, "baseline")[0] for t in _T1A_TR]; exp_end = [raw3d(t, e, "baseline")[1] for t in _T1A_TR]
        expect = f"RMS {rd(med(exp_rms), 2)}; end {rd(med(exp_end), 2)}"
        c(f"T1 1A raw row, {e}", t1_1a_raw[j] == expect, f"got {t1_1a_raw[j]!r} expected {expect!r}")
    c("T1 1B raw row, EKF3", t1_1b_raw[1] == "no offline heading arm", t1_1b_raw[1])
    for j, e in ((2, "UKF"), (3, "FGO")):
        exp_rms = [raw3d(t, e, "heading")[0] for t in _T1B_TR]; exp_end = [raw3d(t, e, "heading")[1] for t in _T1B_TR]
        expect = f"RMS {rng(exp_rms, 2)}; end {rng(exp_end, 2)}"
        c(f"T1 1B raw row, {e}", t1_1b_raw[j] == expect, f"got {t1_1b_raw[j]!r} expected {expect!r}")
    # aligned (registered) cells, independently recomputed from the same rows (catch a row-mismatch, not just a wrong
    # raw number): T1's 1A cell is "median <x> m (<note>)"; use startswith, not `in`, so a value appearing only inside
    # the free-text note cannot pass.
    t1_1a_aligned = next(r for r in T1 if r and r[0].startswith("Experiment 1A: standard sensors"))
    for j, e in enumerate(EST, start=1):
        c(f"T1 1A aligned cell, {e}", t1_1a_aligned[j].startswith(f"median {rd(MED[e], 2)} m ("), t1_1a_aligned[j])
    # T1's 1B aligned cell for UKF/FGO is "<range> m (...)" over the same 6 heading bags
    t1_1b_aligned = next(r for r in T1 if r and r[0].startswith("Experiment 1B: with the camera heading"))
    for j, e in ((2, "UKF"), (3, "FGO")):
        aligned_range = rng([p4_val(ds, r, f"{e}_heading") for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)], 2)
        c(f"T1 1B aligned cell (6-bag range), {e}", t1_1b_aligned[j].startswith(f"{aligned_range} m"), t1_1b_aligned[j])


# =================================================================================== T2_accuracy_heading.md
def check_t2(path, record=check):
    c = record
    T2 = md_rows(path)
    t2_rows = {r[0]: r for r in T2 if r and r[0] in EST}
    c("T2: 3 estimator rows found", len(t2_rows) == 3, list(t2_rows))
    for e in EST:
        row = t2_rows[e]
        # columns (0-indexed): 0 estimator, 1 aligned-9f, 2 raw-9f, 3 aligned-fwdc, 4 raw-fwdc, 5 aligned-fwdplainc,
        # 6 raw-fwdplainc, 7 aligned-fwdc-heading, 8 raw-fwdc-heading, 9 aligned-fwdplainc-heading, 10 raw-fwdplainc-heading, 11 decomposition
        rms9 = [raw3d(t, e, "baseline")[0] for t in _T1A_TR]; end9 = [raw3d(t, e, "baseline")[1] for t in _T1A_TR]
        expect9 = f"RMS {rd(med(rms9), 2)} ({rng(rms9, 2)}); end {rd(med(end9), 2)} ({rng(end9, 2)})"
        c(f"T2 col2 (9 flights) raw, {e}", row[2] == expect9, f"got {row[2]!r} expected {expect9!r}")
        v = [v for _, v in DSN[e]]
        exp1 = f"{rd(MED[e], 2)} ({rng(v, 2)})"
        c(f"T2 col1 (9 flights) aligned, {e}", row[1] == exp1, f"got {row[1]!r} expected {exp1!r}")

        for ds, tr_list, acol, rcol in (("fwdc", _T2_FWDC_TR, 3, 4), ("fwdplainc", _T2_FWDPC_TR, 5, 6)):
            rms = [raw3d(t, e, "baseline")[0] for t in tr_list]; end = [raw3d(t, e, "baseline")[1] for t in tr_list]
            expect = "RMS " + " / ".join(rd(x, 2) for x in rms) + "; end " + " / ".join(rd(x, 2) for x in end)
            c(f"T2 {ds} raw, {e}", row[rcol] == expect, f"got {row[rcol]!r} expected {expect!r}")
            aligned = " / ".join(rd(p4_val(ds, r, BK[e]), 2) for r in (1, 2, 3))
            got_aligned = row[acol].rstrip(" *")
            c(f"T2 {ds} aligned, {e}", got_aligned == aligned, f"got {got_aligned!r} expected {aligned!r}")

        for ds, tr_list, acol, rcol in (("fwdc", _T2_FWDC_TR, 7, 8), ("fwdplainc", _T2_FWDPC_TR, 9, 10)):
            if e == "EKF3":
                c(f"T2 {ds} with-heading raw, EKF3", row[rcol] == "n/a", row[rcol])
                c(f"T2 {ds} with-heading aligned, EKF3", "no offline heading arm" in row[acol], row[acol])
                continue
            rms = [raw3d(t, e, "heading")[0] for t in tr_list]; end = [raw3d(t, e, "heading")[1] for t in tr_list]
            expect = "RMS " + " / ".join(rd(x, 2) for x in rms) + "; end " + " / ".join(rd(x, 2) for x in end)
            c(f"T2 {ds} with-heading raw, {e}", row[rcol] == expect, f"got {row[rcol]!r} expected {expect!r}")
            aligned = " / ".join(rd(p4_val(ds, r, f"{e}_heading"), 2) for r in (1, 2, 3))
            got_aligned = row[acol].rstrip(" *")
            c(f"T2 {ds} with-heading aligned, {e}", got_aligned == aligned, f"got {got_aligned!r} expected {aligned!r}")


# =================================================================================== T9_1A_fitted_vs_raw.md
def check_t9(path, record=check):
    c = record
    T9 = md_rows(path)
    t9_rows = {r[0]: r for r in T9 if r and r[0] in EST}
    c("T9: 3 estimator rows found", len(t9_rows) == 3, list(t9_rows))
    for e in EST:
        row = t9_rows[e]
        v = [v for _, v in DSN[e]]
        rms = [raw3d(t, e, "baseline")[0] for t in _T1A_TR]; end = [raw3d(t, e, "baseline")[1] for t in _T1A_TR]
        c(f"T9 n, {e}", row[1] == "9", row[1])
        c(f"T9 fitted median, {e}", row[2] == rd(MED[e], 2), f"got {row[2]!r} expected {rd(MED[e], 2)!r}")
        c(f"T9 fitted range, {e}", row[3] == rng(v, 2), f"got {row[3]!r} expected {rng(v, 2)!r}")
        c(f"T9 raw RMS median, {e}", row[4] == rd(med(rms), 2), f"got {row[4]!r} expected {rd(med(rms), 2)!r}")
        c(f"T9 raw RMS range, {e}", row[5] == rng(rms, 2), f"got {row[5]!r} expected {rng(rms, 2)!r}")
        c(f"T9 raw end median, {e}", row[6] == rd(med(end), 2), f"got {row[6]!r} expected {rd(med(end), 2)!r}")
        c(f"T9 raw end range, {e}", row[7] == rng(end, 2), f"got {row[7]!r} expected {rng(end, 2)!r}")
    # T9's numbers.md citations: check against the ACTUAL file content at the cited lines, as separate tokens (no
    # ordering chain is reproduced in this checker's own labels or in any table text). numbers.md:230 (the D15
    # claim-wording row, CURRENT) prints "... median 5.13; above EKF3 4.10 and FGO 4.46 by median ..." - UKF's own
    # value is quoted via the word "median" (the sentence is already about the UKF), EKF3/FGO via their own names.
    c("numbers.md:230 contains 'EKF3 4.10' (fitted median token)", "EKF3 4.10" in NUM_LINES[229], NUM_LINES[229][:200])
    c("numbers.md:230 contains 'FGO 4.46' (fitted median token)", "FGO 4.46" in NUM_LINES[229], NUM_LINES[229][:200])
    c("numbers.md:230 contains 'median 5.13' (UKF fitted median token)", "median 5.13" in NUM_LINES[229], NUM_LINES[229][:200])
    c("numbers.md:232 contains the UKF fitted range '1.17–5.85'", "1.17–5.85" in NUM_LINES[231], NUM_LINES[231][:200])


# =================================================================================== R4_information_vs_estimator.md
def check_r4(path, record=check):
    c = record
    R4 = md_rows(path)
    r4_1a = next(r for r in R4 if r and r[0].startswith("Experiment 1A"))
    r4_1b = next(r for r in R4 if r and r[0].startswith("Experiment 1B"))
    exp_1a_raw = "RAW (DESCRIPTIVE), medians: " + "; ".join(
        f"{e} RMS {rd(med([raw3d(t, e, 'baseline')[0] for t in _T1A_TR]), 2)}, end "
        f"{rd(med([raw3d(t, e, 'baseline')[1] for t in _T1A_TR]), 2)}" for e in EST)
    c("R4 1A raw column", r4_1a[3] == exp_1a_raw, f"got {r4_1a[3]!r} expected {exp_1a_raw!r}")
    exp_1a_aligned = f"EKF3 {rd(MED['EKF3'], 2)}, UKF {rd(MED['UKF'], 2)}, FGO {rd(MED['FGO'], 2)} (medians)"
    c("R4 1A aligned column (independent recompute)", r4_1a[2] == exp_1a_aligned, f"got {r4_1a[2]!r} expected {exp_1a_aligned!r}")

    exp_1b_raw = ("RAW (DESCRIPTIVE), RMS; end:\nwith heading: UKF " + _rl("fwdc", "UKF", "heading", "rms") + "; "
                  + _rl("fwdc", "UKF", "heading", "end") + ", FGO " + _rl("fwdc", "FGO", "heading", "rms") + "; "
                  + _rl("fwdc", "FGO", "heading", "end") + "\nwithout: EKF3 " + _rl("fwdc", "EKF3", "baseline", "rms")
                  + "; " + _rl("fwdc", "EKF3", "baseline", "end") + ", UKF " + _rl("fwdc", "UKF", "baseline", "rms")
                  + "; " + _rl("fwdc", "UKF", "baseline", "end") + ", FGO " + _rl("fwdc", "FGO", "baseline", "rms")
                  + "; " + _rl("fwdc", "FGO", "baseline", "end"))
    # the .md renders "\n" as "<br>" (eval/figs_thesis.py's md()); normalise before comparing
    got_1b_raw = r4_1b[3].replace("<br>", "\n")
    c("R4 1B raw column", got_1b_raw == exp_1b_raw, f"got {got_1b_raw!r} expected {exp_1b_raw!r}")
    # R4's 1B ALIGNED cell is a literal string in the generator (pre-existing, not introduced by this stage); recompute
    # it independently from phase4_fwdc_evo.json to confirm the literal is correct, not just unchanged.
    exp_1b_aligned = ("with heading: UKF " + " / ".join(rd(p4_val("fwdc", r, "UKF_heading"), 2) for r in (1, 2, 3))
                      + ", FGO " + " / ".join(rd(p4_val("fwdc", r, "FGO_heading"), 2) for r in (1, 2, 3))
                      + "; without: EKF3 " + " / ".join(rd(p4_val("fwdc", r, "EKF3"), 2) for r in (1, 2, 3))
                      + ", UKF " + " / ".join(rd(p4_val("fwdc", r, "UKF_baseline"), 2) for r in (1, 2, 3))
                      + ", FGO " + " / ".join(rd(p4_val("fwdc", r, "FGO_baseline"), 2) for r in (1, 2, 3)))
    c("R4 1B aligned column (independent recompute from phase4_fwdc_evo.json)", r4_1b[2] == exp_1b_aligned,
      f"got {r4_1b[2]!r} expected {exp_1b_aligned!r}")
    # every other row's new column must be exactly "-" (out of raw-corridor scope, not withheld)
    for row in R4:
        if row is r4_1a or row is r4_1b or not row or row[0] == "condition":
            continue
        if len(row) >= 4 and row[0]:
            c(f"R4 row {row[0][:40]!r}: raw column is '-' (out of scope)", row[3] == "-", row[3])


check_t1(os.path.join(TAB, "T1_scorecard.md"))
check_t2(os.path.join(TAB, "T2_accuracy_heading.md"))
check_t9(os.path.join(TAB, "T9_1A_fitted_vs_raw.md"))
check_r4(os.path.join(TAB, "R4_information_vs_estimator.md"))

# =================================================================================== negative control (REQUIRED to fail)
# Corrupt EKF3's RAW RMS median cell (column 4 - the raw comparison itself, not the pre-existing fitted value) in a
# scratch COPY of T9 and run check_t9 on it through the exact same parse/recompute path as the real check above (not a
# bare string-equality demo). A private `collector` is passed as `record` so this never touches the real n_ok/n_fail
# totals; the scratch file is deleted afterwards either way.
import shutil, tempfile
_t9_path = os.path.join(TAB, "T9_1A_fitted_vs_raw.md")
_scratch_dir = tempfile.mkdtemp(prefix="check_raw_tables_negctrl_")
_scratch = os.path.join(_scratch_dir, "T9_corrupted.md")
_orig_lines = open(_t9_path, encoding="utf-8").read().split("\n")
_idx = next(i for i, l in enumerate(_orig_lines) if l.strip().startswith("| EKF3 | 9 |"))
_parts = [p.strip() for p in _orig_lines[_idx].strip().strip("|").split("|")]
assert len(_parts) == 8, _parts   # estimator, n, fitted median, fitted range, raw RMS median, raw RMS range, raw end median, raw end range
_orig_raw_rms_median = _parts[4]
_corrupted_val = f"{float(_orig_raw_rms_median) + 1.0:.2f}"
_parts[4] = _corrupted_val
_orig_lines[_idx] = "| " + " | ".join(_parts) + " |"
open(_scratch, "w", encoding="utf-8").write("\n".join(_orig_lines))

_ctrl_fails = []
_collect = lambda label, ok, extra="": (_ctrl_fails.append(label) if not ok else None) or ok
check_t9(_scratch, record=_collect)
shutil.rmtree(_scratch_dir)
if not any(lbl == "T9 raw RMS median, EKF3" for lbl in _ctrl_fails):
    print(f"NEGATIVE CONTROL DID NOT FAIL on the corrupted raw RMS median cell (fails seen: {_ctrl_fails}) - the raw "
          "comparison is not discriminating. Aborting.")
    sys.exit(2)
print(f"Negative control: corrupting EKF3's T9 raw RMS median ({_orig_raw_rms_median} -> {_corrupted_val}) caused "
      f"{len(_ctrl_fails)} check(s) to fail, including the targeted one, as required (not counted in the total below).")

print(f"\n{n_ok}/{n_ok + n_fail} checks OK (rd() SHA256 {RD_SHA[:16]}...)")
sys.exit(0 if n_fail == 0 else 1)
