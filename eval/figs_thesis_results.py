#!/usr/bin/env python3
"""RESULTS / DISCUSSION TABLES AND ONE FIGURE (2026-10-17). Built ONLY from stored results and documents: no simulation, no
estimator re-run, and no number in numbers.md, METHODOLOGY.md or the frozen pack is changed.

Outputs (new file names, prefix R; numbers are PROPOSED and provisional, see index_results.md):
  docs/thesis/tables/R1_hypothesis_scorecard.{md,tex,png(_pN)}     proposed Table 7.3
  docs/thesis/tables/R2_corrections_by_discovery.{md,tex,png(_pN)} proposed Table 7.4
  docs/thesis/figures_thesis/R3_trajectory_overlay.{png,pdf}       proposed Figure 4.2
  docs/thesis/tables/R4_information_vs_estimator.{md,tex,png(_pN)} proposed Table 7.5
  docs/thesis/figures_thesis/index_results.md                       captions, sources, cross-checks, gaps

Shared code: rd() (THE thesis rounding rule), the table helpers (tex, md, tex_selfcheck, table_page), the Okabe-Ito palette and
the plot style are taken from eval/figs_thesis.py WITHOUT executing that script (it runs everything at module level and would
regenerate files another agent is editing): the needed top-level nodes are parsed with ast and only those are executed. The
SHA-256 of rd()'s source text is printed in index_results.md.

Cross-checks are EXACT (ruling 2026-10-16): a displayed value is the stored full-precision value rounded once by rd() and must
equal the string typed from numbers.md character for character; the typed string must itself occur in the cited numbers.md
line (so a typing slip cannot pass). Quotes of pre-registrations are checked to occur, fragment by fragment and in order, in
the cited METHODOLOGY.md / tag_hold_design.md lines (markdown emphasis and code ticks removed).

Usage: /home/makerspace/venv-evo/bin/python eval/figs_thesis_results.py"""
import ast, hashlib, json, os, re, subprocess, sys, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUTF = os.path.join(ROOT, "docs", "thesis", "figures_thesis"); TAB = os.path.join(ROOT, "docs", "thesis", "tables")
INDEX = os.path.join(OUTF, "index_results.md"); SCRIPT = "eval/figs_thesis_results.py"
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

# ------------------------------------------------------------- shared code from figs_thesis.py, parsed, NOT executed as a script
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read(); _tree = ast.parse(_src)
_WANT_F = {"rd", "rng", "tex", "md", "tex_selfcheck", "table_page"}
_WANT_A = {"C", "MK", "TRUTH", "EST", "TEX_ESC", "TEX_UNI", "INK", "INK2", "GRID", "SURF", "WALL"}
_nodes, _rd_src = [], None
for n in _tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in _WANT_F:
        _nodes.append(n)
        if n.name == "rd":
            _rd_src = ast.get_source_segment(_src, n)
    elif isinstance(n, ast.Assign):
        names = {t.id for t in n.targets if isinstance(t, ast.Name)} | \
                {e.id for t in n.targets if isinstance(t, ast.Tuple) for e in t.elts if isinstance(e, ast.Name)}
        if names & _WANT_A:
            _nodes.append(n)
    elif isinstance(n, ast.Expr) and "rcParams.update" in (ast.get_source_segment(_src, n) or ""):
        _nodes.append(n)
_ns = {"np": np, "plt": plt, "Line2D": Line2D, "textwrap": textwrap, "re": re, "TP_BUF": []}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), FT, "exec"), _ns)
rd, rng, tex, md, tex_selfcheck, table_page = (_ns[k] for k in ("rd", "rng", "tex", "md", "tex_selfcheck", "table_page"))
C, MK, TRUTH, EST, INK, INK2, GRID, WALL = (_ns[k] for k in ("C", "MK", "TRUTH", "EST", "INK", "INK2", "GRID", "WALL"))
RD_SHA = hashlib.sha256(_rd_src.encode()).hexdigest()
# characters these tables need that figs_thesis.py's TEX_UNI does not map (added to this script's copy only)
_ns["TEX_UNI"].update({"ψ": r"$\psi$", "ω": r"$\omega$", "δ": r"$\delta$", "ε": r"$\varepsilon$", "²": r"$^2$", "ⁱ": "i"})
assert C == {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"} and TRUTH == "#999999", "palette changed in figs_thesis.py"

L = lambda f: json.load(open(os.path.join(RES, f)))
NUM = open(os.path.join(ROOT, "docs", "thesis", "numbers.md")).read().split("\n")
MET = open(os.path.join(ROOT, "METHODOLOGY.md")).read().split("\n")
THD = open(os.path.join(ROOT, "docs", "tag_hold_design.md")).read().split("\n")
CORR = open(os.path.join(ROOT, "docs", "thesis", "final_results_pack_corrections.md")).read().split("\n")
CLM = open(os.path.join(ROOT, "docs", "thesis", "headline_claims_before_after.md")).read().split("\n")
DOCS = {"M": MET, "numbers.md": NUM, "tag_hold_design.md": THD, "corrections": CORR, "claims": CLM}
DOCNAME = {"M": "METHODOLOGY.md", "numbers.md": "docs/thesis/numbers.md", "tag_hold_design.md": "docs/tag_hold_design.md",
           "corrections": "docs/thesis/final_results_pack_corrections.md", "claims": "docs/thesis/headline_claims_before_after.md"}
U = lambda s: str(s).replace("-", "−")                     # unicode minus, as numbers.md prints it


def norm(s):
    s = s.replace("**", "").replace("`", "").replace("\\|", "|")
    return re.sub(r"\s+", " ", s)


def span(doc, a, b=None):
    return norm(" ".join(DOCS[doc][a - 1:(b or a)]))


CHK = []          # numeric cross-checks: (table, label, computed, expected, source, ok)
QCHK = []         # source checks: quotes and outcome strings found at the cited lines: (table, label, source, ok)


def check(tab, label, computed, expected, doc, ln):
    """EXACT: computed (stored value rounded once by rd) == typed expected string, AND the expected string occurs in the cited
    line(s) of the source document."""
    a, b = (ln, None) if isinstance(ln, int) else ln
    inline = norm(str(expected)) in span(doc, a, b)
    ok = (str(computed) == str(expected)) and inline
    CHK.append((tab, label, str(computed), str(expected), f"{DOCNAME[doc]}:{a}" + (f"-{b}" if b else ""), ok))
    if not ok:
        print("   CHECK FAIL:", tab, label, computed, expected, "in-line" if inline else "NOT IN LINE")
    return ok


def jcheck(tab, label, computed, expected, src):
    """EXACT, for a NEW value with no numbers.md / METHODOLOGY line (ruling 2026-10-18, item 6): the value recomputed from the
    stored result file (rounded once by rd()) must equal the typed string; the source is the result file, not a document line."""
    ok = str(computed) == str(expected)
    CHK.append((tab, label, str(computed), str(expected), src + " (new value; no document line)", ok))
    if not ok:
        print("   CHECK FAIL:", tab, label, computed, expected)
    return ok


def scheck(tab, label, computed, src_str, k, doc, ln):
    """EXACT, unit-shifted (units pass 2026-10-23): the displayed string (the stored value rounded once, by an exact decimal shift)
    must equal the source string shifted exactly by 10**k (si_str), AND the unshifted source string occurs in the cited line(s)."""
    from decimal import Decimal
    exp = re.sub(r"\d+(?:\.\d+)?", lambda m_: format(Decimal(m_.group(0)).scaleb(k), "f"), src_str)
    a, b = (ln, None) if isinstance(ln, int) else ln
    inline = norm(str(src_str)) in span(doc, a, b)
    ok = (str(computed) == exp) and inline
    CHK.append((tab, label + f" ({DOCNAME[doc]} '{src_str}' × 10^{k})", str(computed), exp, f"{DOCNAME[doc]}:{a}" + (f"-{b}" if b else ""), ok))
    if not ok:
        print("   CHECK FAIL:", tab, label, computed, exp, "in-line" if inline else "NOT IN LINE")
    return ok


def found(tab, label, frags, doc, a, b=None):
    """Each fragment occurs in the cited lines, in order."""
    s, pos, ok = span(doc, a, b), 0, True
    for f in frags:
        k = s.find(norm(f), pos)
        if k < 0:
            ok = False; print("   SOURCE FAIL:", tab, label, repr(f), f"{DOCNAME[doc]}:{a}-{b}"); break
        pos = k + len(norm(f))
    QCHK.append((tab, label, f"{DOCNAME[doc]}:{a}" + (f"-{b}" if b else ""), ok))
    return ok


def cite(doc, a, b=None):
    pre = {"M": "M", "numbers.md": "numbers.md", "tag_hold_design.md": "tag_hold_design.md", "corrections": "corrections",
           "claims": "claims"}[doc]
    return f"{pre}:{a}" + (f"-{b}" if b else "")


# ------------------------------------------------------------------------------------------------ table writer (3 outputs)
ITEMS = []


def save_tab(num, name, title, caption, header, rows, widths, inputs, notes=(), fs=7.6, bold=True):
    m_ = [f"# {num}. {title}", "", caption, "", "| " + " | ".join(md(h) for h in header) + " |", "|" + "---|" * len(header)]
    m_ += ["| " + " | ".join(md(c) for c in r) + " |" for r in rows]
    m_ += [""] + [f"*{md(n)}*\n" for n in notes] + [f"<!-- generated by {SCRIPT} (commit {COMMIT}); stored results only. Sources, "
                                                     f"cross-checks and gaps: docs/thesis/figures_thesis/index_results.md, {num} (PROPOSED). -->", ""]
    open(os.path.join(TAB, name + ".md"), "w").write("\n".join(m_))
    tw = sum(widths); spec = "".join(f"p{{\\dimexpr {rd(w / tw * 0.999, 3)}\\linewidth-2\\tabcolsep\\relax}}" for w in widths)
    t_ = [f"% {num} (PROPOSED; file {name}): generated by {SCRIPT} (commit {COMMIT}); stored results only. Sources and cross-checks: "
          "docs/thesis/figures_thesis/index_results.md.", "% Needs \\usepackage{booktabs} and longtable-free layout; not compiled here (no TeX).",
          r"\begin{table}[htbp]", r"\centering", r"\scriptsize", f"\\caption{{{tex(title)}. {tex(caption)}}}", f"\\label{{tab:{name}}}",
          f"\\begin{{tabular}}{{{spec}}}", r"\toprule", " & ".join((f"\\textbf{{{tex(h)}}}" if bold else tex(h)) for h in header) + r" \\", r"\midrule"]
    t_ += [" & ".join(tex(c) for c in r) + r" \\" for r in rows]
    t_ += [r"\bottomrule", r"\end{tabular}", r"\par\smallskip\raggedright"] + [f"\\textit{{Note.}} {tex(n)}\\par" for n in notes]
    t_ += [r"\end{table}", ""]
    txt = "\n".join(t_); tex_selfcheck(txt, len(header)); open(os.path.join(TAB, name + ".tex"), "w").write(txt)
    # table_page wraps a column at 0.95 x its width in characters: rescale so the page holds them at this font size
    pw = [w * 160 / tw for w in widths]
    figs = table_page(f"{num}. {title}", header, rows, pw, notes=notes, fs=fs, bold=bold); _ns["TP_BUF"].clear()
    pngs = []
    for k, f in enumerate(figs):
        base = os.path.join(TAB, name + (f"_p{k + 1}" if len(figs) > 1 else ""))
        f.savefig(base + ".png", dpi=150, bbox_inches="tight", pad_inches=0.25); plt.close(f); pngs.append(os.path.basename(base) + ".png")
    ITEMS.append(dict(num=num, name=name, kind="table", title=title, caption=caption, inputs=inputs, notes=notes,
                      files=[name + ".md", name + ".tex"] + pngs))
    print(f"wrote {name}: {len(rows)} rows, {len(pngs)} page(s)")


# =============================================================================================== R1 HYPOTHESIS SCORECARD
# Verdict categories (rule stated in the table note and index_results.md):
#   PASS            the record's verdict word is PASS, MET or TRUE (incl. "accepted as worded")
#   FAIL AS WORDED  a failure that the record itself labels "as worded" (methodology_definitions_draft.md, "As worded")
#   NOT MET         a test run whose decision rule was not met, recorded as FAIL, NOT met, FALSE or MISS, with no "as worded" label
#   WITHDRAWN       no longer made (methodology_definitions_draft.md, "Withdrawn"); V3 is listed, not restated
#   DESCRIPTIVE     no comparative test: a pre-registered comparison with no decision rule (C) or an exploratory analysis (X)
# ---- H5.5 S2/S3 directional prediction (ruling 2026-10-18, item 6), scored from STORED drift values only.
# Comparator: flying EKF3 = the EKF3-flying hold set (s1_r*.json, losses[*].EKF3); the EKF3 entries inside s2v2/s3v2 are shadows
# and are NOT used. Primary metric: the EFFECTIVE drift (last fix -> first returning fix, losses[*].<est>.effective.drift_m), the
# metric of the registered "3–31 mm" (M:10827-10828, "Values are the effective (post hoc) drifts"); the end-of-loss metric
# (drift_end_m) is also counted. Matching: same loss (5 / 15 / 30 s hover, ~7 s move; checked by duration class) and same repeat.
# "More" = strictly greater at full precision. Holds iff both estimators exceed flying EKF3 in every matched loss.
def _dcls(d):
    return 5 if d < 6.5 else (7 if d < 10 else (15 if d < 20 else 30))


def _h5d():
    H = lambda f: L(f"expH/{f}.json")["losses"]
    eff = lambda l, e: l[e]["effective"]["drift_m"] * 1e3
    end = lambda l, e: l[e]["drift_end_m"] * 1e3
    out = {"pairs": {}}
    for key, tag, est in (("ukf", "s2v2", "UKF_port"), ("fgo", "s3v2", "FGO_flying")):
        pr = []
        for r in (1, 2, 3):
            A, B = H(f"s1_r{r}"), H(f"{tag}_r{r}")
            assert len(A) == len(B) == 4
            for a, b in zip(A, B):
                assert _dcls(a["duration_s"]) == _dcls(b["duration_s"]), (tag, r, a["duration_s"], b["duration_s"])
                pr.append((r, _dcls(a["duration_s"]), eff(b, est), eff(a, "EKF3"), end(b, est), end(a, "EKF3")))
        out["pairs"][key] = pr
        out[f"n_{key}"] = f"{sum(p[2] > p[3] for p in pr)} of {len(pr)}"
        out[f"nend_{key}"] = f"{sum(p[4] > p[5] for p in pr)} of {len(pr)}"
        out[f"ndisp_{key}"] = f"{sum(float(rd(p[2], 0)) > float(rd(p[3], 0)) for p in pr)} of {len(pr)}"
        out[f"ties_{key}"] = [(p[0], p[1]) for p in pr if rd(p[2], 0) == rd(p[3], 0)]
        out[f"r_{key}"] = rng([p[2] for p in pr], 0)
        # the end-of-loss values as numbers.md §17.1 prints them: per loss r1 / r2 / r3, losses joined by '; '
        out[f"l_{key}"] = "; ".join(" / ".join(rd(p[4], 0) for p in pr if p[1] == c) for c in (5, 15, 30, 7))
    out["r_ekf"] = rng([p[3] for p in out["pairs"]["ukf"]], 0)
    out["holds"] = all(p[2] > p[3] for k in ("ukf", "fgo") for p in out["pairs"][k])
    return out


H5D = _h5d()
# Each row: label, name (vocabulary §5), part, prediction text, prediction source (doc, a, b), quote fragments,
#           outcome text, outcome source(s) [(doc, a, b, [fragments])], verdict, change note.

# CLAIMS UPDATE APPLIED (user ruling 2026-10-24, C2/C3/C1): extension-experiment verdicts quoted in the R1 and R4 notes, read from the
# tier-1 verdict jsons and checked exactly (jcheck: new values with no numbers.md line; numbers.md is content-frozen).
_T1S = os.path.join(ROOT, "docs", "thesis", "tier1", "scores")
_E2 = json.load(open(os.path.join(_T1S, "E2_verdicts.json")))["criteria"]["H-E2.1"]
_E3 = [v for k_, v in json.load(open(os.path.join(_T1S, "E3_verdicts.json")))["criteria_a"].items() if k_.startswith("H-E3.1")][0]
_E5 = json.load(open(os.path.join(_T1S, "e5_verdicts.json")))["criteria"]["H-E5.1"]
XE2 = "PASS 3/3 in each" if all(_E2[c]["verdict"] == "PASS" and _E2[c]["count"] == "3/3" for c in "BC") else "MISMATCH"
XE3 = f"{_E3['verdict']} {_E3['count']}; {_E3['divergence']['total']}"
XE5 = f"{_E5['verdict']} {_E5['count']}"
jcheck("R1", "extension E2: H-E2.1 with 4 tags (B) and with 2 tags (C)", XE2, "PASS 3/3 in each", "docs/thesis/tier1/scores/E2_verdicts.json (e2_results.md §1)")
jcheck("R1", "extension E3: H-E3.1 at 1% wrong ids; diverged runs", XE3, "FAIL 0/9; 6 of 9 runs diverged", "docs/thesis/tier1/scores/E3_verdicts.json (e3_results.md §1)")
for _t in ("R1", "R4"):     # the R1 note and the R4 note both quote H-E5.1
    jcheck(_t, "extension E5: H-E5.1 (UKF with tag landmark states, live drift bounded)", XE5, "PASS 3/3", "docs/thesis/tier1/scores/e5_verdicts.json (e5_results.md §1)")

R1 = [
 ("H1.1", "standard-sensor ordering, EKF3 vs FGO (confirmatory)", "",
  'Claim "EKF3 lower than the FGO on the textured floor" only if both hold: (a) d_i < 0 on at least 6 of 7 … (b) the 95% '
  't-interval (df 6) of mean d excludes 0 … Otherwise: no ordering is claimed', ("M", 5649, 5654),
  ['Claim "EKF3 lower than the FGO on the textured floor" only if both hold:', "(a) d_i < 0 on at least 6 of 7",
   "(b) the 95% t-interval (df 6) of mean d excludes 0.", "Otherwise: no ordering is claimed"],
  "no ordering claimed: d < 0 on 5/7, mean d −0.021 m, 95% CI [−0.989, +0.947] (flights 4–10)",
  [("numbers.md", 227, None, ["no ordering claimed", "d < 0 on 5/7", "mean d −0.021 m, 95% CI [−0.989, +0.947]"])],
  "NOT MET", "yes: the former verdict 'EKF3 lower' (6/7, CI [−1.16, −0.21]) used the mis-specified FGO noise model and is "
  "WITHDRAWN (claims row 2; corrections 14–15, first final re-run); the FGO initial-uncertainty correction (18) left the verdict unchanged"),
 ("H1.2", "heading-measurement validation", "heading and yaw rate, textured walls",
  "accuracy bar per bag over cruise: heading ψ: availability ≥ 70%, |bias| ≤ 0.5°, noise ≤ 1.0°, outlier rate ≤ 5% "
  "(|error| > 3°); yaw rate ω: ≥ 70%, ≤ 0.05 deg/s, ≤ 1.0 deg/s, ≤ 5%", ("M", 2727, 2730),
  ["heading ψ | ≥ 70% | ≤ 0.5° | ≤ 1.0° | ≤ 5% (|error| > 3°)", "yaw rate ω | ≥ 70% | ≤ 0.05 deg/s | ≤ 1.0 deg/s | ≤ 5%"],
  "heading valid on the textured-wall camera dataset 9/9; yaw rate validated only with textured walls",
  [("numbers.md", 330, None, ["fwdc 9/9"]), ("M", 2851, None, ["Yaw rate is validated only with textured walls."])],
  "PASS", "no (estimator-independent; not re-run; claims row 4)"),
 ("H1.2", "heading-measurement validation", "heading, plain walls over blank and transition floors",
  "(as above)", ("M", 2729, None), ["heading ψ | ≥ 70% | ≤ 0.5° | ≤ 1.0° | ≤ 5%"],
  "heading validated on plain walls on blank and transition floors (plain-wall camera dataset 6/9 overall)",
  [("M", 2843, 2845, ["Heading is validated", "plain walls on blank and transition floors."]), ("numbers.md", 330, None, ["fwdplainc 6/9"])],
  "PASS", "no"),
 ("H1.2", "heading-measurement validation", "heading, plain walls over the checkerboard floor; yaw rate, plain walls",
  "(as above)", ("M", 2729, 2730), ["heading ψ | ≥ 70% | ≤ 0.5° | ≤ 1.0° | ≤ 5%", "yaw rate ω"],
  "heading fails over the checkerboard floor (0/3; availability 60.5%, outliers 13.6%); yaw rate with plain walls not usable",
  [("numbers.md", 301, None, ["FAILED Phase 3 validation (0/3; availability 60.5%, outliers 13.6%"]),
   ("M", 2846, 2852, ["Heading fails on plain walls over a checkerboard floor.", "With plain walls, horizontal flow near the VP is not a usable measurement."])],
  "NOT MET", "no"),
 ("H1.3", "heading-fusion prediction", "(a) heading-driven share falls",
  "the heading-driven share falls", ("M", 1332, None), ["the heading-driven share falls"],
  "PASS in all 12 estimator × world × dataset cells (as recorded 2026-09-29; not re-scored after the final re-runs; the restated "
  "with-heading heading-driven cross-track is 0.063–0.068 m on the textured walls, numbers.md:263)",
  [("M", 3440, None, ['"The heading-driven share falls": PASS in all 12 estimator × world × dataset cells.']),
   ("numbers.md", 263, None, ["With heading: UKF 0.065 / 0.064 / 0.068; FGO 0.065 / 0.063 / 0.067"])],
  "PASS", "verdict not re-scored after the final re-runs (no restated verdict found in METHODOLOGY after line 12768); magnitudes restated, numbers.md:263"),
 ("H1.3", "heading-fusion prediction", "(b) residual roughly unchanged",
  "and the 26% residual stays roughly unchanged", ("M", 1332, 1333), ["and the 26% residual stays roughly unchanged"],
  "FAIL as worded in 10 of 12 cells (no numerical band for 'roughly'); as recorded 2026-09-29, not re-scored",
  [("M", 3447, 3448, ['"The residual stays roughly unchanged": FAIL as worded in 10 of 12 cells.', 'gave no numerical band for "roughly"'])],
  "FAIL AS WORDED", "verdict not re-scored after the final re-runs"),
 ("C1.a", "FGO vs UKF with heading", "(report, no decision rule)",
  "REPORT, no decision rule … FGO lower than UKF on all 3 fwdc textured bags; mixed on fwdplainc.", ("M", 7892, 7897),
  ["(REPORT, no decision rule)", "FGO lower than UKF on all 3 fwdc textured bags; mixed on fwdplainc."],
  "FGO lower on all 6 textured-floor bags: 3/3 textured walls (0.06 vs 0.13 m), 3/3 plain walls (0.09–0.22 vs 0.15–0.25 m; margin 0.03–0.06 m)",
  [("numbers.md", 299, None, ["FGO lower on all 6", "3/3 fwdc (0.06 vs 0.13 m) and 3/3 fwdplainc (0.09–0.22 vs 0.15–0.25 m; margin 0.03–0.06 m)"])],
  "DESCRIPTIVE", "yes: the first final re-run reversed it on plain walls (UKF lower 3/3; FGO 43 m, a model error); restored by "
  "correction 18 (claims row 7, HOLDS)"),
 ("H1.4", "robust-weighting test", "",
  '"robust FGO better than hard-gated UKF" iff, over the 6 bags, it has fewer lockout episodes in total AND a lower '
  "yaw-error max on ≥ 4 of 6", ("M", 7921, 7922),
  ['"robust FGO better than hard-gated UKF" iff, over the 6 bags, it has fewer lockout episodes in total AND a lower yaw-error max on ≥ 4 of 6.'],
  "NOT met (lockout tie): robust FGO lower yaw max on 6/6, but lockouts 3 = 3 (robust FGO vs hard-gated UKF)",
  [("numbers.md", 509, None, ["NOT met (lockout tie)", "robust lower yaw max on 6/6, but lockouts FGO_robust 3 = UKF_hard 3"])],
  "NOT MET", "reason changed: first recorded 'failed as worded' because the UKF had the lower worst-case yaw on 6/6 (M:8432); "
  "after the final re-runs the yaw part passes and the lockout tie fails it (ruling 8; claims row 27, HOLDS)"),
 ("X1.b", "robust vs hard-gated FGO, same bags", "(exploratory)",
  "F1 EXPLORATORY (not pre-registered): robust FGO against the hard-gated FGO, same bags, isolating the weighting (no prediction)",
  ("M", 8460, None), ["F1 EXPLORATORY (not pre-registered): robust FGO against the hard-gated FGO, same bags, isolating the weighting"],
  "tested on fresh flights by H1.7: 'F1's exploratory benefit over the hard-gated FGO still largely did not replicate (P1 and S2 "
  "FAIL); replicated: fewer wrong headings accepted (S1 5/6)'; the per-bag exploratory values (M:8464-8471) predate the final re-runs and are not restated",
  [("numbers.md", 501, None, ["F1's exploratory benefit over the hard-gated FGO still largely did not replicate (P1 and S2 FAIL); replicated: fewer wrong headings accepted (S1 5/6)"])],
  "DESCRIPTIVE", "the exploratory table is not restated (no numbers.md row)"),
 ("H1.5", "hindsight heading correction", "",
  '"hindsight correction" iff the batch FGO\'s hindsight OFF-interval yaw RMS is below both live arms\' on all 3 bags', ("M", 7940, 7941),
  ['"hindsight correction" iff the batch FGO\'s hindsight OFF-interval yaw RMS is below both live arms\' on all 3 bags.'],
  "MET: batch off-interval yaw RMS 0.063–0.066° against live 0.32–0.36° on all 3 bags",
  [("numbers.md", 510, None, ["MET", "batch off-interval yaw RMS 0.063–0.066° against live 0.32–0.36° on all 3 bags"])],
  "PASS", "yes: NOT met → MET in the first final re-run (ruling 4; claims row 28)"),
 ("H1.6", "large initial heading error", "",
  "\"the FGO's advantage grows with δ\" iff the FGO/UKF ratio of integrated error decreases monotonically with δ on ≥ 2 of 3 bags",
  ("M", 7962, 7963), ['"the FGO\'s advantage grows with δ" iff the FGO/UKF ratio of integrated error decreases monotonically with δ on ≥ 2 of 3 bags.'],
  "NOT met: ratio decreasing on 1/3 bags (2/3 needed); the FGO's Δ30 prior-induced lockout is gone",
  [("numbers.md", 511, None, ["NOT met", "the FGO's Δ30 prior-induced lockout is gone", "ratio decreasing on 1/3 bags (2/3 needed)"])],
  "NOT MET", "reason changed in the first final re-run (claims row 29, HOLDS); first recorded 'failed as worded' (M:8439)"),
 ("H1.6b", "nonlinearity test, redesigned", "(a) FGO converges at least as fast",
  '(a) "FGO converges at least as fast" iff FGO convergence ≤ UKF convergence at every δ on ≥ 2 of 3 bags', ("M", 8507, 8508),
  ['(a) "FGO converges at least as fast" iff FGO convergence ≤ UKF convergence at every δ on ≥ 2 of 3 bags'],
  "TRUE (unchanged)", [("numbers.md", 512, None, ["TRUE / FALSE (unchanged)"])], "PASS", "no (claims row 30)"),
 ("H1.6b", "nonlinearity test, redesigned", "(b) advantage grows with the error",
  "(b) \"the FGO's advantage grows with the error\" iff the FGO/UKF integrated-error ratio decreases monotonically with δ on ≥ 2 of 3 bags",
  ("M", 8509, 8510), ['(b) "the FGO\'s advantage grows with the error" iff the FGO/UKF integrated-error ratio decreases monotonically with δ on ≥ 2 of 3 bags.'],
  "FALSE (unchanged); the UKF still diverges numerically at every Δ", [("numbers.md", 512, None, ["TRUE / FALSE (unchanged); the UKF still diverges numerically at every Δ"])],
  "NOT MET", "no (claims row 30)"),
 ("H1.6c", "convergence speed in the UKF's valid range", "(a) FGO converges at least as fast",
  "(a) the FGO converges at least as fast iff FGO convergence ≤ UKF convergence at both δ on ≥ 2 of 3 bags", ("M", 8962, None),
  ["(a) the FGO converges at least as fast iff FGO convergence ≤ UKF convergence at both δ on ≥ 2 of 3 bags;"],
  "FALSE", [("numbers.md", 513, None, ["FALSE / TRUE"])], "NOT MET", "no"),
 ("H1.6c", "convergence speed in the UKF's valid range", "(b) advantage larger at 30°",
  "(b) the FGO's advantage is larger at 30° iff the FGO/UKF integrated-error ratio at 30° < at 10° on ≥ 2 of 3 bags", ("M", 8963, None),
  ["(b) the FGO's advantage is larger at 30° iff the FGO/UKF integrated-error ratio at 30° < at 10° on ≥ 2 of 3 bags."],
  "TRUE, accepted as worded and flagged FRAGILE: ratio decreasing on 2/3 bags (r3 rests on FGO integrals of 0.2–0.5 m·s)",
  [("numbers.md", 513, None, ["TRUE, accepted as worded and flagged FRAGILE", "Ratio decreasing on 2/3 bags"])],
  "PASS", "yes, twice: TRUE → FALSE in the first final re-run, FALSE → TRUE with correction 18 (restatement ruling 2; claims row 31)"),
 ("H1.7a", "robust-weighting replication: yaw maximum (primary)", "",
  "P1 (PRIMARY): the robust FGO's yaw maximum < the hard-gated FGO's on ≥ 10 of 12 flights … A P1 miss is a failure of the "
  "confirmation as worded", ("M", 9730, 9742),
  ["P1 (PRIMARY): the robust FGO's yaw maximum < the hard-gated FGO's on ≥ 10 of 12 flights.", "A P1 miss is a failure of the confirmation as worded."],
  "7/12 (≥ 10 needed): FAIL; 2 IMU-gap exclusions counted against",
  [("numbers.md", 497, None, ["7/12 (≥ 10 needed): FAIL", "(2 IMU-gap exclusions counted against)"])],
  "FAIL AS WORDED", "count only: 9/12 → 7/12 in the first final re-run, verdict unchanged (claims row 32)"),
 ("H1.7b", "replication: fewer wrong headings (secondary)", "",
  "S1 (secondary): on the plain-wall flights, the robust FGO accepts fewer wrong headings than the hard-gated FGO on ≥ 5 of 6",
  ("M", 9733, 9734), ["S1 (secondary): on the plain-wall flights, the robust FGO accepts fewer wrong headings than the hard-gated FGO on ≥ 5 of 6."],
  "5/6: PASS", [("numbers.md", 498, None, ["5/6: PASS"])], "PASS", "no (claims row 32)"),
 ("H1.7c", "replication: cross-track (secondary)", "",
  "S2 (secondary): the robust FGO's maximum cross-track ≤ the hard-gated FGO's on ≥ 8 of 12", ("M", 9737, None),
  ["S2 (secondary): the robust FGO's maximum cross-track ≤ the hard-gated FGO's on ≥ 8 of 12."],
  "5/12 (≥ 8 needed): FAIL", [("numbers.md", 499, None, ["5/12 (≥ 8 needed): FAIL"])], "NOT MET",
  "count only: 6/12 → 5/12 in the first final re-run, verdict unchanged"),
 ("H1.8", "closed loop without heading: contact prediction", "EKF3, real time (RTF 1.0)",
  "PRIMARY: no contact before +100 s; contact, if any, on the west wall inside [+155, +215] s", ("M", 4948, None),
  ["PRIMARY: no contact before +100 s; contact, if any, on the west wall inside [+155, +215] s."],
  "west-wall contact at cruise +186.2 s", [("numbers.md", 470, None, ["+186.2 (PASS, window [+155, +215])"])], "PASS", "no (flight; claims row 14)"),
 ("H1.8", "closed loop without heading: contact prediction", "EKF3, half real-time (RTF 0.5)",
  "(as above)", ("M", 4948, None), ["inside [+155, +215] s."],
  "contact at cruise +242.1 s: after the registered window (MISS)", [("numbers.md", 470, None, ["+242.1 (MISS, D21)"])], "NOT MET",
  "no (flight); no comparison across real-time factors is claimed"),
 ("H1.8", "closed loop without heading: contact prediction", "UKF (real time; half real-time, final UKF port)",
  "U3: contact on the WEST wall inside [+146, +218] s", ("M", 7513, None), ["U3: contact on the WEST wall inside [+146, +218] s."],
  "+163.0 s (real time); +165.9 s (half real-time, final UKF port); both west wall",
  [("numbers.md", 471, None, ["+163.0 (PASS, [+146, +218])", "+165.9 (PRIMARY PASS; west wall"])], "PASS",
  "value only: half real-time +198.0 s (earlier build) → +165.9 s (final UKF port; correction 17 flight pair); verdict unchanged"),
 ("H1.8", "closed loop without heading: contact prediction", "FGO (half real-time, final FGO node)",
  "U3: west-wall contact inside [+145, +196] s", ("M", 8995, None), ["U3: west-wall contact inside [+145, +196] s."],
  "+169.9 s west (U1, U2, U3 PASS; original priors)", [("numbers.md", 473, None, ["+169.9 west (U3 PASS, inside the registered [+145, +196]; U1/U2 PASS)"])],
  "PASS", "value only: +165.8 s (original) → +169.6 s (correction 14) → +169.9 s (correction 15); verdict unchanged"),
 ("H1.9", "closed loop with heading: criteria pass", "EKF3",
  "B1. Completes the full mission and lands with no wall contact (|x| < 9.58 m throughout) … B2. … cross-track ≤ 6.0 m … "
  "B3. … 95th percentile ≤ 1.0°, maximum ≤ 2.0° … B4. … ≤ 0.25 m/s … B5. No oscillation", ("M", 4951, 4966),
  ["B1. Completes the full mission and lands with no wall contact (|x| < 9.58 m throughout)", "B2. Maximum physical cross-track during cruise ≤ 6.0 m.",
   "B3. EKF3 yaw error during cruise: 95th percentile ≤ 1.0°, maximum ≤ 2.0°.", "B4. 1 s-smoothed |GT lateral speed| during cruise ≤ 0.25 m/s.", "B5. No oscillation"],
  "3/3 (Python heading node, real time), 3/3 (C++ node, real time), 3/3 (half real-time)", [("numbers.md", 477, None, ["3/3, 3/3 / 3/3"])],
  "PASS", "no (flight)"),
 ("H1.9", "closed loop with heading: criteria pass", "UKF (final UKF port, half real-time)",
  "(as above, + estimator-validity criterion: the estimator valid throughout)", ("M", 7361, 7362), ["S2 is the estimator valid throughout"],
  "3/3, all five criteria and estimator validity PASS", [("numbers.md", 478, None, ["3/3, ALL B criteria and S2 PASS"])], "PASS",
  "yes: the earlier-build half real-time set was 2/3 (flight 3 lateral speed 0.296 m/s); the re-flown final port 3/3 (correction 17 flight pair, 0.019 m/s)"),
 ("H1.9", "closed loop with heading: criteria pass", "FGO (final FGO node, half real-time)",
  "(as above)", ("M", 7361, 7362), ["S2 is the estimator valid throughout"],
  "3/3, all five criteria and estimator validity PASS (original priors); flight 3 lateral speed 0.246 m/s, 0.004 m/s inside",
  [("numbers.md", 480, None, ["3/3 / 3/3", "ALL B criteria and S2 PASS in both", "B4 0.246 m/s at cruise +0.5 s, inside the 0.25 m/s band by 4 mm/s"])],
  "PASS", "yes, before the final re-runs: the original FGO sets scored 2/3 until the oscillation-window scorer fix (correction 11, D28: 2/3 → 3/3)"),
 ("H2.1", "FGO hindsight gain grows with the gap (primary)", "",
  "H-T1 … the FGO's hindsight gain grows with the gap. PASS iff both: (i) the per-condition medians of Δ_FGO increase strictly "
  "A < B < C < D; (ii) Spearman ρ(gap length, Δ_FGO) over all gaps > 0 with p < 0.01", ("M", 10171, 10173),
  ["the FGO's hindsight gain grows with the gap. PASS iff both:", "(i) the per-condition medians of Δ_FGO increase strictly A < B < C < D;",
   "(ii) Spearman ρ(gap length, Δ_FGO) over all gaps > 0 with p < 0.01."],
  "PASS: median gain 0.010 / 0.011 / 0.023 / 0.052 m (A–D), strictly increasing; ρ = +0.30, p = 6e-6, n = 213 gaps",
  [("numbers.md", 533, 534, ["H-T1 (primary) PASS.", "0.010 / 0.011 / 0.023 / 0.052 m for A–D", "Spearman ρ = +0.30, p = 6e-6, n = 213 gaps."])],
  "PASS", "no (claims row 17)"),
 ("H2.2", "the same for the smoothed UKF", "",
  "P-T2 (prediction): the same holds for the RTS-UKF (Δ_UKF, same two criteria)", ("M", 10176, None),
  ["P-T2 (prediction): the same holds for the RTS-UKF (Δ_UKF, same two criteria)."],
  "FAIL: gain +0.020 / +0.032 / +0.037 / +0.029 m (not increasing; ρ +0.11, p 0.11)",
  [("numbers.md", 535, None, ["P-T2 FAIL.", "+0.020 / +0.032 / +0.037 / +0.029 m", "ρ +0.11, p 0.11"])], "NOT MET", "no (claims row 17)"),
 ("H2.3", "live errors similar", "",
  "P-T3 (prediction): live errors are similar. In every condition, the largest live horizontal RMSE among EKF3, UKF and FGO "
  "(mean over repeats) is ≤ 1.5 × the smallest", ("M", 10178, 10179),
  ["P-T3 (prediction): live errors are similar. In every condition, the largest live horizontal RMSE among EKF3, UKF and FGO (mean over repeats) is ≤ 1.5 × the smallest."],
  "FAIL: live max/min 1.97 / 2.36 / 1.42 / 1.57 (A–D; C inside the band)", [("numbers.md", 536, None, ["P-T3 FAIL.", "1.97 / 2.36 / 1.42 / 1.57 (C inside the band)"])],
  "NOT MET", "no (claims row 17); condition D wording changed to descriptive (claims row 18)"),
 ("H2.4", "FGO hindsight ≈ smoothed UKF", "",
  "P-T4 (prediction): FGO hindsight ≈ RTS-UKF. In every condition, the larger of their horizontal RMSEs (mean over repeats) is "
  "≤ 1.5 × the smaller", ("M", 10180, 10181),
  ["P-T4 (prediction): FGO hindsight ≈ RTS-UKF. In every condition, the larger of their horizontal RMSEs (mean over repeats) is ≤ 1.5 × the smaller."],
  "FAIL: FGO whole-flight batch vs smoothed UKF 1.31 / 2.14 / 2.06 / 3.89 (A–D)", [("numbers.md", 537, None, ["P-T4 FAIL.", "1.31 / 2.14 / 2.06 / 3.89"])],
  "NOT MET", "no (claims row 17)"),
 ("V3", "estimator validation check (Experiment 3)", "",
  "PASS iff its live ATE is within ±20% of the thesis FGO's live ATE on the same bag", ("M", 10490, None),
  ["PASS iff its live ATE is within ±20% of the thesis FGO's live ATE on the same bag"],
  "NOT re-scorable (labels never recorded); the old PASS (4.63 vs 4.59 m) was on the old FGO and is listed, not restated",
  [("numbers.md", 576, None, ["V-L: NOT re-scorable", "keyframe FGO 4.63 m vs thesis FGO 4.59 m", "is not restated"])],
  "WITHDRAWN", "yes: PASS (old FGO) → not re-scorable on the corrected FGO (ruling 6, 2026-10-09; claims row 24)"),
 ("H3.1", "loop closure bounds live drift (primary)", "",
  "H-L1 (PRIMARY): loop closure bounds live drift. For LC live, the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3 flights", ("M", 10501, 10502),
  ["H-L1 (PRIMARY): loop closure bounds live drift. For LC live, the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3 flights."],
  "PASS 3/3: with loop closure live lap 5 ÷ lap 1 0.16–0.43", [("numbers.md", 573, None, ["0.16–0.43"]), ("numbers.md", 577, None, ["H-L1 (primary), H-L2, H-L3 and P-L4: PASS 3/3"])],
  "PASS", "magnitudes only (correction 18); verdict unchanged (claims row 23)"),
 ("H3.2", "live error lower with loop closure", "",
  "H-L2: LC live overall RMSE < no-LC live overall RMSE in 3/3 flights", ("M", 10503, None), ["H-L2: LC live overall RMSE < no-LC live overall RMSE in 3/3 flights."],
  "PASS 3/3: live 0.049–0.076 m with, 0.263–0.361 m without loop closure",
  [("numbers.md", 573, 574, ["0.049–0.076 m", "0.263–0.361 m"]), ("numbers.md", 577, None, ["PASS 3/3"])], "PASS",
  "magnitudes only: without loop closure 0.281–0.362 → 0.263–0.361 m (correction 18; claims row 23)"),
 ("H3.3", "hindsight error lower with loop closure", "",
  "H-L3: LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights", ("M", 10504, None),
  ["H-L3: LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights."],
  "PASS 3/3: hindsight 0.017–0.027 m with, 0.221–0.266 m without loop closure",
  [("numbers.md", 573, 574, ["0.017–0.027 m", "0.221–0.266 m"]), ("numbers.md", 577, None, ["PASS 3/3"])], "PASS", "no (claims row 23)"),
 ("H3.4", "without loop closure, drift grows lap on lap", "",
  "P-L4 (prediction): no-LC live per-lap RMSE grows: lap 5 > 1.5 × lap 1 in 3/3 flights", ("M", 10505, None),
  ["P-L4 (prediction): no-LC live per-lap RMSE grows: lap 5 > 1.5 × lap 1 in 3/3 flights."],
  "PASS 3/3: without loop closure lap 5 ÷ lap 1 2.9–4.5", [("numbers.md", 574, None, ["2.9–4.5"]), ("numbers.md", 577, None, ["PASS 3/3"])],
  "PASS", "magnitudes only: lap ratio 3.0–5.0 → 2.9–4.5 (correction 18; claims row 23)"),
 ("H4.1", "FGO hindsight beats the filters' live tracks indoors (primary)", "",
  "H-O1 … FGO hindsight beats the filters' live tracks indoors. PASS iff in 3/3 flights the FGO-batch indoor RMSE is < both "
  "EKF3's and the UKF's live indoor RMSE", ("M", 10358, 10359),
  ["FGO hindsight beats the filters' live tracks indoors. PASS iff in 3/3 flights the FGO-batch indoor RMSE is < both EKF3's and the UKF's live indoor RMSE."],
  "PASS 3/3: FGO whole-flight batch 0.59 m against EKF3 live 1.42–1.43 m and UKF live 0.77–0.84 m",
  [("numbers.md", 558, None, ["H-O1 (primary) PASS 3/3."]), ("numbers.md", 552, 556, ["1.42–1.43 m", "0.77–0.84 m", "0.59 m"])],
  "PASS", "magnitude only: batch 0.33 → 0.59 m (≈93% correction 14, ≈7% correction 15, partial attribution); verdict unchanged (claims row 19)"),
 ("H4.2", "live indoor errors similar", "",
  "H-O2 … live indoor errors are similar. In every flight, the largest live indoor RMSE of EKF3, UKF and FGO is ≤ 1.5 × the smallest",
  ("M", 10360, 10361), ["live indoor errors are similar. In every flight, the largest live indoor RMSE of EKF3, UKF and FGO is ≤ 1.5 × the smallest."],
  "FAIL: live max ÷ min 1.71–1.84×", [("numbers.md", 559, None, ["H-O2 FAIL: the live ratio is 1.71–1.84×"])], "NOT MET",
  "ratio only: ~2.2× → 1.71–1.84× (first final re-run); verdict unchanged (claims row 19)"),
 ("H4.3", "FGO batch ≈ smoothed UKF", "",
  "P-O3 (prediction; the fair comparison): FGO batch and RTS-UKF indoor RMSE are within 1.5× of each other in every flight",
  ("M", 10362, 10363), ["P-O3 (prediction; the fair comparison): FGO batch and RTS-UKF indoor RMSE are within 1.5× of each other in every flight."],
  "PASS: FGO whole-flight batch ÷ smoothed UKF 1.01–1.02", [("numbers.md", 560, None, ["P-O3 PASS (was FAIL; flip accepted, ruling 5): batch FGO vs RTS-UKF ratio 1.01–1.02 (capped)"])],
  "PASS", "yes: FAIL → PASS in the first final re-run (ruling 5; claims row 20); 'FGO batch ~2× better' WITHDRAWN (claims row 21)"),
 ("H5.1", "hold accuracy (primary)", "",
  "H-H1 (primary, EKF3 flying): mean hold error ≤ 0.05 m and max ≤ 0.15 m in every pre-loss hold window, 3/3 flights.", ("M", 10687, 10688),
  ["H-H1 (primary, EKF3 flying): mean hold error ≤ 0.05 m and max ≤ 0.15 m in every pre-loss hold window, 3/3 flights."],
  "PASS: hold error mean 8 mm, max 16–25 mm (EKF3 flying); also PASS on the FGO-flying hold set (final FGO node)",
  [("numbers.md", 606, None, ["8 mm / 16–25 mm (H-H1 PASS)"]), ("numbers.md", 646, None, ["8.1–9.0 / 18–28 (H-H1 PASS)"])], "PASS", "no (flights; claims row 25)"),
 ("H5.2", "FGO holds tightest", "",
  ("H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.",
   "(design draft §e; no METHODOLOGY pre-registration line)"), ("tag_hold_design.md", 180, None), ["H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights."],
  "FAIL (0/3): UKF lowest 3/3 (6.4–7.1 mm); FGO highest in all three (8.3–8.6 against EKF3 7.8–7.9 mm)",
  [("numbers.md", 675, None, ["FAIL (0/3): UKF lowest 3/3 (6.4–7.1 mm); the FGO is now the HIGHEST in all three runs (8.3–8.6 against EKF3 7.8–7.9 mm)"])],
  "NOT MET", "wording only (tie → FGO highest) on the final-build sets; verdict identical to the original-build verdict"),
 ("H5.3", "smoothness similar", "",
  "P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators.", ("tag_hold_design.md", 183, None),
  ["P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators."],
  "FAIL (0/3): UKF 2.40–2.58×, FGO 2.10–2.37× EKF3's", [("numbers.md", 676, None, ["FAIL (0/3): UKF 2.40–2.58×, FGO 2.10–2.37× EKF3's"])],
  "NOT MET", "no: identical to the original-build verdict"),
 ("H5.4a", "after a 15 s loss, EKF3 jumps most", "",
  "After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights.",
  ("tag_hold_design.md", 185, 186), ["After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's in 3/3 flights."],
  "FAIL (0/3): EKF3 strictly the smallest (5 / 5 / 7 against UKF 20–30, FGO 7–30 mm)",
  [("numbers.md", 677, None, ["FAIL (0/3): EKF3 strictly the smallest in all three (5 / 5 / 7 against UKF 20–30, FGO 7–30 mm)"])],
  "NOT MET", "wording only (smallest or tied → strictly smallest); verdict identical"),
 ("H5.4b", "after a 5 s loss, jumps similar", "",
  "After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.", ("tag_hold_design.md", 187, None),
  ["After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other."],
  "FAIL (0/3): EKF3 4–5 against UKF 7–16, FGO 11–34 mm (max/min 3.2–7.7)",
  [("numbers.md", 678, None, ["FAIL (0/3): EKF3 4–5 against UKF 7–16, FGO 11–34 mm (max/min 3.2–7.7)"])], "NOT MET", "no: identical to the original-build verdict"),
 ("H5.5", "drift band", "",
  "P-H5 (drift during loss, per estimator): EKF3 and FGO: drift at the end of the 5 / 15 / 30 s hover losses ≤ 0.05 / 0.10 / 0.20 m. "
  "UKF: ≤ 2× those. Loss during the move (12 s): ≤ 0.15 m for EKF3 and FGO, 0.30 m for the UKF.", ("M", 10689, 10692),
  ["P-H5 (drift during loss, per estimator):", "EKF3 and FGO: drift at the end of the 5 / 15 / 30 s hover losses ≤ 0.05 / 0.10 / 0.20 m.",
   "UKF: ≤ 2× those.", "Loss during the move (12 s): ≤ 0.15 m for EKF3 and FGO, 0.30 m for the UKF."],
  "PASS: every loss inside its band (20/20 each estimator in S1; every band passes on the UKF- and FGO-flying hold sets)",
  [("numbers.md", 629, None, ["P-H5 PASS (20/20 each estimator"]), ("numbers.md", 644, None, ["every UKF band PASSES"]), ("numbers.md", 646, None, ["every FGO band PASSES"])],
  "PASS", "no (claims row 25); the S1 shadow drifts were restated (claims row 26)"),
 ("H5.5", "drift band", "S2/S3 directional prediction (UKF- and FGO-flying hold sets, final builds)",
  "Directional prediction: both flying estimators drift more than flying EKF3 did (3–31 mm).", ("M", 10971, None),
  ["Directional prediction: both flying estimators drift more than flying EKF3 did (3–31 mm)."],
  f"NOT borne out (the predicted outcome did not occur): per matched loss (same loss and repeat, flying EKF3 = the EKF3-flying hold set, near spawn), the final UKF port drifted more "
  f"in {H5D['n_ukf']} and the final FGO node in {H5D['n_fgo']} (strictly greater, full precision); ranges overlap (UKF {H5D['r_ukf']}, "
  f"FGO {H5D['r_fgo']}, flying EKF3 {H5D['r_ekf']} mm)",
  [("numbers.md", 644, None, [H5D["l_ukf"], "drifts 2–26 mm"]), ("numbers.md", 646, None, [H5D["l_fgo"]]),
   ("M", 10932, None, ["flying EKF3 drifted far less (3–31 mm)"])],
  "NOT MET", "new part (rulings 2026-10-18, item 6; labelled NOT MET by the second ruling of 2026-10-18; listed within H5.5's drift-prediction item, M:10959 and M:10971): scored from stored drift values only (eval/results/expH/s1_r*.json, "
  "s2v2_r*.json, s3v2_r*.json); judged NOT borne out on the superseded builds (M:12244-12245)"),
 ("H5.6", "re-lock time", "as pre-registered (EKF3-flying hold set)",
  "P-H6 (re-lock): EKF3: after the 5 s loss (no timeout), re-lock ≤ 0.2 s with a jump ≤ 0.05 m. After the 15 s and 30 s losses "
  "(posTimeout), the first fix resets position: re-lock ≤ 0.2 s with a jump equal to the accumulated drift (within 0.02 m of it). "
  "UKF and FGO: re-lock at the first fix (≤ 0.1 s), no reset; the largest single step ≤ the accumulated drift.", ("M", 10695, 10699),
  ["P-H6 (re-lock):", "EKF3: after the 5 s loss (no timeout), re-lock ≤ 0.2 s with a jump ≤ 0.05 m.",
   "After the 15 s and 30 s losses (posTimeout), the first fix resets position: re-lock ≤ 0.2 s with a jump equal to the accumulated drift (within 0.02 m of it).",
   "UKF and FGO: re-lock at the first fix (≤ 0.1 s), no reset; the largest single step ≤ the accumulated drift."],
  "re-lock 0.16–1.06 s for all three (occluder render lag): FAIL as worded", [("numbers.md", 617, None, ["0.16–1.06 s (occluder render lag; P-H6 FAIL as worded)"])],
  "FAIL AS WORDED", "no; the measurement-definition fault led to the redefinition (next row; correction 20)"),
 ("H5.6", "re-lock time", "redefined primary (UKF- and FGO-flying hold sets)",
  "Re-lock time, PRIMARY: from the first returning tag detection (the first /tags/raw wall-tag detection after the loss) to the "
  "first fix fused by the flying estimator. UKF port: the first ExtNav position update in its log after that detection. FGO: the first "
  "keyframe whose factors include that fix. Reason: the S1 finding that Gazebo's occluder rendering lags set_pose by 0.16–1.0 s, so "
  "cover-off timing measures the simulator. Band: ≤ 0.1 s for both (UKF: VISO_DELAY_MS 31 ms plus one step; FGO: ≤ one keyframe of "
  "33 ms plus the node latency).", ("M", 10948, 10955),
  ["Re-lock time, PRIMARY: from the first returning tag detection (the first /tags/raw wall-tag detection after the loss) to the first fix fused by the flying estimator.",
   "UKF port: the first ExtNav position update in its log after that detection.", "FGO: the first keyframe whose factors include that fix.",
   "Reason: the S1 finding that Gazebo's occluder rendering lags set_pose by 0.16–1.0 s, so cover-off timing measures the simulator.",
   "Band: ≤ 0.1 s for both (UKF: VISO_DELAY_MS 31 ms plus one step; FGO: ≤ one keyframe of 33 ms plus the node latency)."],
  "PASS: UKF −0.048…−0.015 s; FGO 0.002–0.032 s", [("numbers.md", 644, None, ["−0.048…−0.015 s, PASS"]), ("numbers.md", 646, None, ["0.002–0.032 s, PASS"])],
  "PASS", "a redefinition registered before the S2/S3 flights (correction 20), not a re-scoring of S1"),
 ("H5.6", "re-lock time", "jump criterion, kept as worded (UKF- and FGO-flying hold sets)",
  "Jump criterion: kept as worded (the largest single estimate step in the 2 s after re-lock ≤ the accumulated drift at re-lock; "
  "UKF/FGO converge without reset).", ("M", 10957, 10958),
  ["Jump criterion: kept as worded (the largest single estimate step in the 2 s after re-lock ≤ the accumulated drift at re-lock; UKF/FGO converge without reset)."],
  "fails as worded: final UKF port in most losses (steps 5–30 mm against drifts 2–26 mm); final FGO node in 4 of 12 losses. Why: "
  "the single-step correction at re-lock lands a few mm above the accumulated drift (numbers.md:644, 646)",
  [("numbers.md", 644, None, ["jump criterion AS WORDED fails in most losses (steps 5–30 mm against drifts 2–26 mm)"]),
   ("numbers.md", 646, None, ["jump AS WORDED fails in 4 of 12 losses"])],
  "FAIL AS WORDED", "part kept as worded (ruling 2026-10-18; added by ruling 2026-10-17, verbatim wording): the S2/S3 pre-registration "
  "kept this criterion as worded; its outcome is recorded (numbers.md §17.1) but was not scored as an H5.6 part before; no new analysis"),
 ("H5.7", "no lockout", "",
  "P-H7 (lockout): no estimator locks out the returning tag in any loss.", ("M", 10700, None),
  ["P-H7 (lockout): no estimator locks out the returning tag in any loss."],
  "PASS: no lockout in any loss", [("numbers.md", 629, None, ["No lockout in any loss (P-H7 PASS)."])], "PASS", "no (claims row 25)"),
]
CATS = ("PASS", "FAIL AS WORDED", "NOT MET", "WITHDRAWN", "DESCRIPTIVE")
rowsR1 = []
def vfound(tab, label, text, doc, a, b=None):
    """VERBATIM (ruling 2026-10-17, Experiment 5 wording): `text` occurs UNBROKEN in the cited lines, with list bullets, markdown
    emphasis and code ticks removed (no ellipsis, no paraphrase)."""
    src = norm(" ".join(re.sub(r"^\s*-\s+", "", ln) for ln in DOCS[doc][a - 1:(b or a)])).strip()
    ok = norm(text) in src
    if not ok:
        print("   VERBATIM FAIL:", tab, label, f"{DOCNAME[doc]}:{a}-{b}")
    QCHK.append((tab, label, f"{DOCNAME[doc]}:{a}" + (f"-{b}" if b else ""), ok))
    return ok


for lab, name, part, pred, (pd, pa, pb), pfr, out, osrc, verdict, chg in R1:
    assert verdict in CATS
    pq, pafter = pred if isinstance(pred, tuple) else (pred, "")
    found("R1", f"{lab} {part} prediction quote", pfr, pd, pa, pb)
    if lab.startswith("H5."):
        vfound("R1", f"{lab} {part} prediction quote, verbatim", pq, pd, pa, pb)
    for od, oa, ob, ofr in osrc:
        found("R1", f"{lab} {part} outcome", ofr, od, oa, ob)
    rowsR1.append([lab + (f" {part}" if part else ""), name, (f"{pq} [{cite(pd, pa, pb)}]" if pq.startswith("(as above") else
                   f"“{pq}”" + (f" {pafter}" if pafter else "") + f" [{cite(pd, pa, pb)}]"), out,
                   verdict, chg, "; ".join(cite(od, oa, ob) for od, oa, ob, _ in osrc)])
# the Experiment 5 notes' sources (two wordings of H5.1 and H5.5; the S2/S3 directional prediction)
vfound("R1", "note: design-draft H5.1 wording", "H-H1 (primary): every estimator holds within tag-fix accuracy. Mean hold error ≤ 0.05 m and max "
       "≤ 0.15 m in 3/3 flights per estimator.", "tag_hold_design.md", 176, 177)
vfound("R1", "note: design-draft H5.5 wording", "P-H5 (drift during loss, prediction): GT drift during the 15 s occlusion ≤ 0.3 m for every "
       "estimator.", "tag_hold_design.md", 188)
found("R1", "note: the design-draft H5.5 wording scored", ["P-H5 PASSES:", "every estimator drifted ≤ 30 mm over the 15 s loss (≤ 0.3 m)."], "M", 12243)
found("R1", "note: flying hold sets inside the H5.1 bounds", ["6.1–7.4 / 17–21"], "numbers.md", 644)
found("R1", "note: flying hold sets inside the H5.1 bounds (FGO)", ["8.1–9.0 / 18–28 (H-H1 PASS)"], "numbers.md", 646)
vfound("R1", "note: S2/S3 directional prediction", "Directional prediction: both flying estimators drift more than flying EKF3 did (3–31 mm).",
       "M", 10971, 10972)
found("R1", "note: directional prediction not borne out (superseded builds)", ["The S2/S3 directional prediction", "is NOT borne out:"], "M", 12244, 12245)
CNT = {c: sum(1 for r in R1 if r[8] == c) for c in CATS}
LABELS = sorted({r[0] for r in R1}, key=lambda s: (s[0] != "H", s))
# numeric cross-checks behind R1 (stored values, rounded once)
pt = L("dsn_paired_test.json")
from decimal import Decimal as _D
_b4 = L("closed_loop_cl_fgo_b_tex_r3_half_v3.json")["B"]["B4"]["max_abs_lat_speed_mps"]
scheck("R1", "H1.9 FGO flight 3: lateral-speed margin inside the 0.25 m/s band (m/s; exact 0.25 − stored max, rounded once)",
       rd(float(_D("0.25") - _D(str(_b4))), 3), "4", -3, "numbers.md", 480)
check("R1", "H1.1 mean d (m)", U(rd(pt["mean_d_m"], 3)), "−0.021", "numbers.md", 227)
check("R1", "H1.1 95% CI (m)", f"[{U(rd(pt['t95_ci_m'][0], 3))}, {rd(pt['t95_ci_m'][1], 3, sign=True)}]", "[−0.989, +0.947]", "numbers.md", 227)
ta = L("expT/t_aggregate.json"); TC = ta["conditions"]
check("R1", "H2.1 median FGO hindsight gain A–D (m)", " / ".join(rd(ta["H-T1 (FGO live -> whole-flight batch)"]["median_gain_m"][k], 3) for k in "ABCD"),
      "0.010 / 0.011 / 0.023 / 0.052", "numbers.md", 533)
LIVE = ("EKF3 live", "UKF live", "FGO live"); HIND = ("FGO hindsight (whole-flight batch)", "RTS-UKF (hindsight)")
mm = lambda d, ks: max(d[k] for k in ks) / min(d[k] for k in ks)
check("R1", "H2.3 live max/min A–D", " / ".join(rd(mm(TC[k]["mean_rmse_m"], LIVE), 2) for k in "ABCD"), "1.97 / 2.36 / 1.42 / 1.57", "numbers.md", 536)
check("R1", "H2.4 hindsight max/min A–D", " / ".join(rd(mm(TC[k]["mean_rmse_m"], HIND), 2) for k in "ABCD"), "1.31 / 2.14 / 2.06 / 3.89", "numbers.md", 537)
OFL = ("O_r1", "O_r2", "O_r3b"); OJ = {t: L(f"expO/{t}.json")["tracks"] for t in OFL}
o_live = [mm({k: OJ[t][k]["indoor_rmse_m"] for k in LIVE}, LIVE) for t in OFL]
check("R1", "H4.2 live max/min range", f"{rd(min(o_live), 2)}–{rd(max(o_live), 2)}×", "1.71–1.84×", "numbers.md", 559)
o_hind = [mm({k: OJ[t][k]["indoor_rmse_m"] for k in HIND}, HIND) for t in OFL]
check("R1", "H4.3 hindsight max/min range", f"{rd(min(o_hind), 2)}–{rd(max(o_hind), 2)}", "1.01–1.02", "numbers.md", 560)
# H5.5 S2/S3 directional prediction (ruling 2026-10-18, item 6): inputs against their document lines, new values against the json
found("R1", "note: H5.5 directional, the registered 3–31 mm is the effective drift", ["Values are the effective (post hoc) drifts"], "M", 10827, 10828)
found("R1", "note: H5.5 directional, pairing caveat", ["each estimator flew its own flights, so the pairing is by run index, not the same trajectory."], "M", 12249)
found("R1", "note: H5.5 directional, in the S2/S3 pre-registration", ["Experiment H S2/S3: pre-registration items fixed now (before any S2/S3 flight"], "M", 10946)
_HJ = "eval/results/expH/s1_r*.json, s2v2_r*.json, s3v2_r*.json"
check("R1", "H5.5 directional: final UKF port end-of-loss drift per loss, r1 / r2 / r3 (mm)", H5D["l_ukf"], "5 / 7 / 8; 19 / 7 / 26; 6 / 10 / 10; 26 / 4 / 5", "numbers.md", 644)
check("R1", "H5.5 directional: final FGO node end-of-loss drift per loss, r1 / r2 / r3 (mm)", H5D["l_fgo"], "13 / 20 / 17; 7 / 25 / 27; 22 / 15 / 9; 17 / 11 / 18", "numbers.md", 646)
check("R1", "H5.5 directional: flying EKF3 effective drift range, all 12 losses (mm)", H5D["r_ekf"], "3–31", "M", 10932)
check("R1", "H5.5 directional: final UKF port effective drift range, all 12 losses (mm)", H5D["r_ukf"], "2–26", "numbers.md", 644)
jcheck("R1", "H5.5 directional: final FGO node effective drift range, all 12 losses (mm)", H5D["r_fgo"], "7–27", _HJ)
jcheck("R1", "H5.5 directional: matched losses with the UKF / FGO drift strictly above flying EKF3 (effective, full precision)",
       f"{H5D['n_ukf']} / {H5D['n_fgo']}", "4 of 12 / 9 of 12", _HJ)
jcheck("R1", "H5.5 directional: same count, end-of-loss metric (drift_end_m)", f"{H5D['nend_ukf']} / {H5D['nend_fgo']}", "4 of 12 / 9 of 12", _HJ)
jcheck("R1", "H5.5 directional: same count, at the displayed mm precision (effective)", f"{H5D['ndisp_ukf']} / {H5D['ndisp_fgo']}", "3 of 12 / 9 of 12", _HJ)
jcheck("R1", "H5.5 directional: matched losses equal at the displayed mm precision (repeat, loss s), UKF / FGO", f"{H5D['ties_ukf']} / {H5D['ties_fgo']}", "[(2, 30)] / []", _HJ)
jcheck("R1", "H5.5 directional: prediction holds (both exceed flying EKF3 in every matched loss)", H5D["holds"], False, _HJ)
_cnt_txt = ", ".join(f"{c} {CNT[c]}" for c in CATS)
(lambda *a_, **k_: save_tab(*a_, bold=False, **k_))(  # Table 7.3: no bolding anywhere (ruling 2026-10-18)
    "Table 7.3", "R1_hypothesis_scorecard", "Hypothesis scorecard: every pre-registered hypothesis, comparison and check, with its restated verdict",
         f"Each row quotes the pre-registered prediction (with its source line), the outcome now (after the final re-runs and the rulings of "
         f"2026-10-16) and one of five verdicts. Counts per scored part ({len(R1)} parts, {len(LABELS)} labels): {_cnt_txt}.",
         ["label (part)", "name", "pre-registered prediction (quoted) [source]", "outcome now", "verdict", "changed through the corrections?", "outcome source"],
         rowsR1, [16, 16, 42, 38, 10, 34, 16],
         "METHODOLOGY.md and docs/tag_hold_design.md (predictions); docs/thesis/numbers.md (outcomes); docs/thesis/headline_claims_before_after.md "
         "(claims rows); eval/results/dsn_paired_test.json, expT/t_aggregate.json, expO/O_*.json (numeric cross-checks)",
         notes=["Verdicts (the rule used here; the record's own word decides): PASS = the record says PASS, MET or TRUE (including a verdict "
                "'accepted as worded'); FAIL AS WORDED = a failure the record itself labels 'as worded' (the literal verdict, kept although the "
                "wording is known to be faulty or unbanded; methodology draft, 'As worded'); NOT MET = a test that was run and whose rule was not "
                "met, recorded as FAIL, NOT met, FALSE or MISS without that label; WITHDRAWN = no longer made (methodology draft, 'Withdrawn'): V3 "
                "is not re-scorable, so its old PASS is listed and not restated; DESCRIPTIVE = no comparative test (C1.a is a pre-registered "
                "comparison with no decision rule; X1.b is exploratory).",
                "Labels with parts are scored per part (H1.2 by wall type and floor, H1.3 (a)/(b), H1.6b and H1.6c (a)/(b), H1.8 and H1.9 per flying "
                "estimator, H5.5 its bands and the S2/S3 directional prediction, H5.6 as pre-registered, as redefined and its jump criterion kept as worded), so the counts are per part, not per label.",
                "Experiment 5 (ruling 2026-10-17): every H5 prediction is quoted VERBATIM (no ellipsis; checked unbroken in the cited lines, "
                "markdown removed) and its verdict is judged against that wording. H5.1, H5.5, H5.6 (as pre-registered) and H5.7 are quoted from "
                "the S0/S1 pre-registration (M:10623, 'written before any H flight'); the H5.6 redefinition and its kept jump criterion from the "
                "S2/S3 pre-registration (M:10946, 'before any S2/S3 flight'). H5.2–H5.4b have no METHODOLOGY pre-registration line; their only "
                "pre-registration is the design draft (tag_hold_design.md §e), whose text is unchanged since commit c11fcf3 (2026-10-08 15:17), "
                "before the first Experiment 5 flight. Two wordings exist for H5.1 and H5.5: the design draft says 'H-H1 (primary): every estimator holds "
                "within tag-fix accuracy. Mean hold error ≤ 0.05 m and max ≤ 0.15 m in 3/3 flights per estimator.' (tag_hold_design.md:176-177) and 'P-H5 (drift during loss, prediction): GT drift during the 15 s "
                "occlusion ≤ 0.3 m for every estimator.' (tag_hold_design.md:188); the METHODOLOGY wording is the one scored. Both PASS under either wording "
                "(flying hold sets 6.1–7.4 / 17–21 mm UKF and 8.1–9.0 / 18–28 mm FGO, numbers.md:644, 646; the draft's P-H5 was scored PASS at "
                "M:12243).",
                "H5.5 S2/S3 directional prediction (ruling 2026-10-18): 'both flying estimators drift more than flying EKF3 did (3–31 mm)' "
                "(M:10971, in the S2/S3 pre-registration), scored as worded on the final builds (final UKF port H_s2v2_r*, final FGO node "
                "H_s3v2_r*) against flying EKF3 (the EKF3-flying hold set H_s1_r*, near spawn, the source of the registered 3–31 mm; the EKF3 shadows of the S2/S3 flights are not used), "
                "from stored drift values only. Primary: per matched loss (the same loss, 5 / 15 / 30 s hover or ~7 s move, and the same "
                "repeat: 12 per estimator), 'more' = strictly greater at full precision, on the effective drift (last fix to first "
                "returning fix), the metric of the registered 3–31 mm (M:10827-10828); it holds iff both estimators exceed flying EKF3 in "
                f"every matched loss. Result: UKF {H5D['n_ukf']}, FGO {H5D['n_fgo']}; the end-of-loss metric gives the same counts; at the "
                f"displayed mm precision UKF {H5D['ndisp_ukf']} (one UKF pair, repeat 2, 30 s loss, equal at that precision) and FGO "
                f"{H5D['ndisp_fgo']}. The ranges overlap (UKF {H5D['r_ukf']}, FGO {H5D['r_fgo']}, flying EKF3 {H5D['r_ekf']} mm). NOT borne "
                "out (the predicted outcome did not occur): labelled NOT MET. Caveat (M:12249): each estimator flew its own flights, so the pairing is by run index, "
                "not the same trajectory; it also crosses spawn points (the final-build UKF and FGO sets flew from the far spawn). The superseded builds were judged NOT borne out (M:12244-12245).",
                "H1.3 is shown as recorded on 2026-09-29 (M:3440-3448): no restated Phase 5 verdict exists after the final re-runs, only the restated "
                "decomposition magnitudes (numbers.md:263). The criteria families without hypothesis labels (dataset-quality bands, the 5S safety "
                "criteria) are not scored here: numbers.md §8 and Table A.2.",
                "'Changed through the corrections?' names the claims-table row (headline_claims_before_after.md) and the correction number "
                "(Table 7.4) where the sources link them. Corrections applied in one batch are applied jointly and not attributed individually "
                "(corrections file, attribution rule); a correction number after a change means 'in the batch that contained it', except where "
                "marked as a flight pair or a partial attribution.",
                "Experiment 3 scope (claims C2 and C3, user ruling 2026-10-24; the H3.1–H3.4 verdicts are unchanged): H3.1–H3.4 were scored "
                "with all 8 tags and correct tag IDs. Extension experiments (pre-registered 2026-10-21, signed off with amendments 2026-10-22; "
                "not thesis hypotheses, so not rows here): with 4 tags and with 2 tags, loop closure also bounded live drift (H-E2.1 "
                f"{XE2}); with wrong IDs in 1% of the eligible detections, the FGO as built lost its loop-closure advantage (H-E3.1 {XE3}); "
                f"a UKF with tag landmark states also bounded its live drift (H-E5.1 {XE5}). See limitations list item 3 and "
                "docs/thesis/tier1/claims_applied.md."])

# =============================================================================================== R2 CORRECTIONS BY DISCOVERY METHOD
# (n, short name, scope, corrections-file line, discovery category, how found (quoted fragment, checked), claims rows, hypotheses)
BASE = "none: before the claims table's 'before' state (07f9f56, 2026-10-09)"
FFR = "first final re-run (14–17 applied jointly)"
R2 = [
 (1, "UKF/FGO IMU dejitter (sensor-time reconstruction)", "DATA", 28, "fairness (input-equivalence) audit",
  "Fairness audit OI-2 (2026-09-24): an input asymmetry between the estimators.", BASE, "— (none stated in the sources)"),
 (2, "IMU-gap rule", "DATA", 29, "inspection of the recorded inputs", "Real dropouts found in fwd_* (M: \"IMU gap threshold\").", BASE,
  "H1.1: flight 10 unusable for the FGO and counted against both (numbers.md:227); H1.7a: 2 IMU-gap exclusions counted against (numbers.md:497)"),
 (3, "EKF3 flow sensor position FLOW_POS_Z 0.13 → 0.25", "CONFIG", 30, "offline cross-check against ground truth (distance scale)",
  "Distance-scale check (2026-09-29).", BASE, "— (none stated)"),
 (4, "UKF process dt = the accumulated IMU interval", "MODEL", 31, "offline cross-check against ground truth (distance scale)",
  "Distance-scale check (2026-09-29).", BASE, "— (none stated)"),
 (5, "lateral optical-flow sign", "MODEL / bridge", 32, "SITL flight exposing a defect",
  "Closed-loop smoke test (2026-09-29): the first data with large lateral velocity", BASE, "— (none stated)"),
 (6, "roll rate gains ×0.4447 (simulated vehicle)", "MODEL (vehicle)", 33, "diagnostic investigation of a measured effect",
  "EKF3 flow-derotation timing investigation (2026-09-29).", BASE, "— (none stated; all blank-floor data re-flown)"),
 (7, "time sync on; AHRS_EKF_TYPE explicit; replay logging", "CONFIG", 34, "source-code reading",
  "Part C source reading (SIM_JSON.cpp:410-413, 2026-09-29).", BASE, "— (none stated)"),
 (8, "heading share on the pinned cruise window", "ANALYSIS", 35, "analysis audit (window)", "Window audit (2026-09-29).", BASE, "— (none stated)"),
 (9, "ground-proximity flow rule for the UKF/FGO (D15)", "MODEL", 36, "port and offline equivalence or comparison work",
  "UKF port and offline comparison (2026-09-30). Every poor UKF flight began with a 5–17° heading jump at lift-off.", BASE,
  "C1.a is defined on the post-D15 arms (M:7892); the 'UKF poor in most textured flights' wording superseded (numbers.md:230)"),
 (10, "offline UKF IMU process noise as per-second densities (D27)", "MODEL", 37, "port and offline equivalence or comparison work",
  "UKF port equivalence work (2026-10-01).", BASE, "none: 'No verdict changes' (corrections:37)"),
 (11, "closed-loop scorer: oscillation-bound window (D28)", "SCORER", 38, "SITL flight failure (scoring localised)",
  "Localising the FGO r3 B5 failure (2026-10-02).", BASE, "H1.9 (FGO, original builds): 2/3 → 3/3 (numbers.md:479)"),
 (12, "six known-tag FGO runs lacked D15", "DATA / pipeline", 39, "port and offline equivalence or comparison work",
  "C++-port equivalence work (2026-10-08).", BASE, "H2.1–H2.4: re-run, 'no verdict changes' (corrections:39)"),
 (13, "UKF port float constants; C++ FGO clock seed", "PORT", 40, "port and offline equivalence or comparison work",
  "Port equivalence tests (2026-09-30; 2026-10-08).", BASE, "none: 'No offline result is affected' (corrections:40)"),
 (14, "FGO noise model: biasAccOmegaInt → 0", "MODEL", 41, "SITL flight exposing a defect (hold-flight trace)",
  "FGO hover-tilt trace (H safety tests, 2026-10-09).",
  f"{FFR}: 1a, 2 (WITHDRAWN: the old verdict used the mis-specified noise model, ruling 2), 3, 9, 11, 16, 18, 20, 21 (WITHDRAWN: "
  "largely an artefact of the noise model), 22 (partial attribution ≈93%), 24, 26, 28, 29, 33, 34; it also exposed the plain-wall "
  "divergence of row 8 (traced: 100% noise fix)",
  "H1.1 (verdict replaced: no ordering); H1.5 (NOT met → MET); H1.6 (reason changed); H1.6c (b) (TRUE → FALSE); H4.3 (FAIL → PASS); "
  "V3 (not re-scorable); C1.a (plain-wall reversal); H1.8 FGO (flight pair +165.8 → +169.6 s, verdict unchanged)"),
 (15, "FGO yaw cap variance-gated (as EKF3/UKF)", "MODEL", 42, "model audit", "Model audit (2026-10-09).",
  f"{FFR}: as 14 (the FGO rows); partial attribution of row 22 (≈7%, and the live track improves by 0.22–0.30 m)",
  "as 14; H1.8 FGO (flight pair +169.6 → +169.9 s); H5.2–H5.4b (ablation build → final FGO node: verdicts identical)"),
 (16, "offline UKF bias-corrected flow derotation", "MODEL", 43, "SITL flight exposing a defect (shadow-vs-flying gap)",
  "H S1 input-path diagnostic (2026-10-08): the shadow-vs-flying hover-drift gap.",
  f"{FFR}: 1a (UKF 3.91 → 3.59 m), 1b (values only, HOLDS), 6, 12, 13, 26 (the gap that exposed it closes), 33",
  "— (no hypothesis verdict stated as changed)"),
 (17, "UKF covariance jitter only on Cholesky failure", "MODEL (offline and port)", 44, "model audit", "Model audit (2026-10-09).",
  f"{FFR}: as 16 (the UKF rows); by elimination the 2.5 m flight-2 mismatch",
  "H1.8 UKF (flight pair +198.0 → +165.9 s, verdict unchanged); H1.9 UKF (half real-time set 2/3 → 3/3, flight pair)"),
 (18, "FGO initial σ: yaw 1e-3 rad → 1°, roll/pitch 2° → 5°", "MODEL", 45, "trace of a re-run divergence",
  "Plain-wall divergence trace (2026-10-10) of the first final re-run",
  "FGO-only re-run (a single-correction pair): 7 (C1.a restored, HOLDS), 8 (WITHDRAWN, traced), 31 (FALSE → TRUE, HOLDS); values in 1a, "
  "2 (verdict unchanged), 3, 5, 9, 11, 16, 23, 27, 32, 34",
  "C1.a (6/6 restored); H1.6c (b) (FALSE → TRUE, FRAGILE); H3.1–H3.4 (magnitudes only); flown FGO results kept the original priors"),
 (19, "FGO trajectory-writer quaternion typo (D10)", "SCORER (output writer)", None, "port and offline equivalence or comparison work",
  "Yaw representation. fgo_replay.py's TUM writer euler_to_quat has a w-component typo", BASE + "; 'No row of this file changes at its printed precision' (numbers.md:1014)",
  "— (FGO yaw values only, ≤ 0.17°; no evo value changed)"),
 (20, "re-lock time redefined from the first returning tag detection (P-H6)", "ANALYSIS (definition)", None,
  "SITL flight exposing a defect (scoring of the first hold flights)",
  "a measurement-definition fault found after scoring", BASE, "H5.6: S1 stays FAIL AS WORDED; the redefined primary PASSES on the final-build hold sets"),
]
SRC19 = ("M", 6592, 6600); SRC19b = ("M", 6805, 6830); SRC20 = ("M", 10798, None); SRC20b = ("M", 10948, 10952)
order = ["fairness (input-equivalence) audit", "inspection of the recorded inputs", "offline cross-check against ground truth (distance scale)",
         "analysis audit (window)", "source-code reading", "model audit", "port and offline equivalence or comparison work",
         "diagnostic investigation of a measured effect", "trace of a re-run divergence", "SITL flight exposing a defect",
         "SITL flight exposing a defect (hold-flight trace)", "SITL flight exposing a defect (shadow-vs-flying gap)",
         "SITL flight exposing a defect (scoring of the first hold flights)", "SITL flight failure (scoring localised)"]
grp = lambda c: "SITL flight (a defect exposed by a flown result)" if c.startswith("SITL") else c
rowsR2 = []
for n, nm, scope, ln, cat, how, cl, hy in sorted(R2, key=lambda r: (order.index(r[4]), r[0])):
    if ln:
        found("R2", f"correction {n} how found", [how], "corrections", ln)
        found("R2", f"correction {n} scope", [f"| {scope} |"], "corrections", ln)
        src = cite("corrections", ln)
    elif n == 19:
        found("R2", "correction 19 how found", [how], *SRC19); found("R2", "correction 19 result", ["No evo value changed, and no EKF3 or UKF number."], *SRC19b)
        found("R2", "correction 19 numbers.md", ["No row of this file changes at its printed precision."], "numbers.md", 1014)
        src = f"{cite(*SRC19)}; {cite(*SRC19b)}; numbers.md:1011-1014"
    else:
        found("R2", "correction 20 how found", [how], *SRC20); found("R2", "correction 20 redefinition", ["Re-lock time, PRIMARY: from the first returning tag detection"], *SRC20b)
        src = f"{cite(*SRC20)}; {cite(*SRC20b)}"
    rowsR2.append([grp(cat), str(n), nm, scope, how, cl, hy, src])
# claims-row status words used above: check against the claims table
for row, word in (("2", "WITHDRAWN"), ("8", "WITHDRAWN"), ("21", "WITHDRAWN"), ("7", "HOLDS"), ("31", "HOLDS"), ("20", "CHANGED"), ("28", "CHANGED"),
                  ("24", "CHANGED"), ("1b", "HOLDS"), ("26", "CHANGED"), ("22", "CHANGED")):
    ln = next(i + 1 for i, s in enumerate(CLM) if s.startswith(f"| {row} |"))
    found("R2", f"claims row {row} status {word}", [f"| {word} |"], "claims", ln)
save_tab("Table 7.4", "R2_corrections_by_discovery", "Corrections grouped by how they were found, with the headline claims and hypotheses each one changed",
         "The 18 corrections of the final results pack (corrections file) and two later ones it does not list (19, 20), grouped by the "
         "discovery route the sources record. 'Claims rows' are the rows of the headline-claims table (before vs after the final re-runs); "
         "rows are named for the re-run batch that changed them, which applied its corrections jointly.",
         ["discovered by", "no.", "correction", "scope", "how it was found (quoted)", "claims-table rows changed", "hypotheses (thesis labels) changed", "source"],
         rowsR2, [22, 5, 26, 10, 34, 44, 40, 16],
         "docs/thesis/final_results_pack_corrections.md (items 1–18); METHODOLOGY.md (items 19, 20); docs/thesis/headline_claims_before_after.md "
         "(claims rows); docs/thesis/numbers.md",
         notes=["Discovery routes are taken from the corrections file's 'how it was found' column (quoted), or from METHODOLOGY for 19 and 20. "
                "The SITL-flight group holds the defects that a flown result exposed: a closed-loop smoke flight (5), a scored closed-loop failure "
                "(11), hold flights (14, 16) and the scoring of the first hold flights (20). No correction was discovered by the attribution study "
                "itself (it attributed, it did not find); none is recorded as found by a reviewer's or the user's question.",
                "Corrections 1–13, 19 and 20 predate the claims table's 'before' state (commit 07f9f56, 2026-10-09 20:03): their effects are inside "
                "the 'before' column, so no claims row records them. 14–17 were applied jointly in the first final re-run and 18 alone in the "
                "FGO-only re-run; a claims row is listed against the batch that changed it, not attributed to one correction, except the directly "
                "traced plain-wall case (row 8, 18 and 14), the ruled O partial attribution (rows 21–22: ≈93% 14, ≈7% 15) and flight 2 of the "
                "standard-sensor dataset (17, by elimination).",
                "Included beyond the pack's 18: 19, the FGO trajectory-writer typo (D10), which changed stored FGO yaw values (≤ 0.17°) but no "
                "numbers.md row at its printed precision; and 20, the re-lock-time redefinition. Excluded (display or transcription fixes, no stored "
                "result changed): the single-rounding correction of numbers.md displays and the three transcription corrections (rulings "
                "2026-10-16; M:14229-14247); the 'final safety run' restatement (ruling 2026-10-16 item 5), which re-labels which stored run is final."])

# =============================================================================================== R3 TRAJECTORY OVERLAY (figure)
# THE SELECTION RULE (fixed here, in the caption text, before any path is loaded or plotted):
RULE = ("Flights chosen by a rule fixed before plotting: (a) of the 9 textured-floor flights of the standard-sensor dataset that all three "
        "estimators complete (flights 1–9; flight 10 is unusable for the UKF and FGO), the flight whose mean cruise ATE over EKF3, UKF and FGO "
        "is the median (5th of 9); (b) the flight of the textured-wall camera dataset (textured floor) with the same repeat index as (a) if it "
        "exists among its flights 1–3, otherwise the median of those three by the mean cruise ATE of the arms drawn solid.")
from evo.core import sync, metrics
from evo.core.trajectory import PoseTrajectory3D


def tum_traj(a):
    return PoseTrajectory3D(positions_xyz=a[:, 1:4], orientations_quat_wxyz=a[:, [7, 4, 5, 6]], timestamps=a[:, 0])


def aligned(trial, sub, f, win):
    """The cruise-ATE computation of eval/three_way_eval.py reproduced only to place the path: crop both TUMs to the stored window,
    associate (t_max_diff 0.05 s), then a yaw-only placement for drawing (see below). Returns (aligned est xyz, ref xyz, rmse)."""
    ref = np.loadtxt(f"{TD}/{trial}/{sub}/ground_truth.tum"); est = np.loadtxt(f"{TD}/{trial}/{sub}/{f}")
    c = lambda a: a[(a[:, 0] >= win[0]) & (a[:, 0] <= win[1])]
    r, e = sync.associate_trajectories(tum_traj(c(ref)), tum_traj(c(est)), 0.05)
    # Placement for DRAWING (ruling 2026-10-21): rotation about the vertical + shift only (yaw-only, no scale). The SE(3) fit of the
    # cruise ATE is degenerate about the near-straight corridor axis and can roll sideways drift into the vertical (METHODOLOGY
    # "FINDING (2026-10-21): the SE(3) cruise-ATE alignment is degenerate"); the yaw-only fit gives the same RMS to within millimetres.
    P, G = e.positions_xyz, r.positions_xyz
    mp, mg = P.mean(0), G.mean(0); a_, b_ = P - mp, G - mg
    th = np.arctan2((a_[:, 0] * b_[:, 1] - a_[:, 1] * b_[:, 0]).sum(), (a_[:, 0] * b_[:, 0] + a_[:, 1] * b_[:, 1]).sum())
    Rz = np.array([[np.cos(th), -np.sin(th), 0.0], [np.sin(th), np.cos(th), 0.0], [0.0, 0.0, 1.0]])
    Pa = (Rz @ a_.T).T + mg
    return Pa, G, float(np.sqrt((np.linalg.norm(Pa - G, axis=1) ** 2).mean()))


ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
DSNA = {i: {e: ev[f"dsn_tex_r{i}"]["est"][e]["ate_a_cruise"]["+0.00"] for e in EST} for i in range(1, 10)}
means = sorted((np.mean(list(DSNA[i].values())), i) for i in range(1, 10)); ra = means[4][1]
P4E = L("phase4_fwdc_evo.json")["trials"]
ARMB = {"EKF3": "EKF3", "UKF": "UKF_heading", "FGO": "FGO_heading"}
if ra in (1, 2, 3):
    rb = ra; rb_why = f"same repeat index as (a), flight {ra}"
else:
    mb = sorted((np.mean([P4E[f"fwdc_tex_r{i}"]["est"][ARMB[e]]["ate_a_cruise"]["+0.00"] for e in EST]), i) for i in (1, 2, 3)); rb = mb[1][1]
    rb_why = f"flight {ra} does not exist in the camera dataset; median of its flights 1–3"
TRA, TRB = f"dsn_tex_r{ra}", f"fwdc_tex_r{rb}"
print(f"R3 selection: (a) {TRA} (mean cruise ATE ranks {[i for _, i in means]}), (b) {TRB} ({rb_why})")
SUB = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF": ("ukf", "ukf_traj.tum"), "FGO": ("fgo", "fgo_traj.tum"),
       "UKF_baseline": ("ukf_baseline", "ukf_traj.tum"), "FGO_baseline": ("fgo_baseline", "fgo_traj.tum"),
       "UKF_heading": ("ukf_heading", "ukf_traj.tum"), "FGO_heading": ("fgo_heading", "fgo_traj.tum")}


def NE(key, xyz):
    """(North, East) of an aligned path: aligned paths are in their ground-truth file's frame (EKF3: N, E, D; UKF/FGO: ENU)."""
    return (xyz[:, 0], xyz[:, 1]) if key == "EKF3" else (xyz[:, 1], xyz[:, 0])


PANELS = [("a", TRA, ev[TRA]["window_s"], [("EKF3", "EKF3", "--"), ("UKF", "UKF", "--"), ("FGO", "FGO", "--")], ev[TRA]["est"]),
          ("b", TRB, P4E[TRB]["window_s"], [("EKF3", "EKF3", "--"), ("UKF_baseline", "UKF", "--"), ("FGO_baseline", "FGO", "--"),
                                             ("UKF_heading", "UKF", "-"), ("FGO_heading", "FGO", "-")], P4E[TRB]["est"])]
PATHS = {}
for pid, tr, win, arms, est in PANELS:
    for key, e, ls in arms:
        xyz, ref, rmse = aligned(tr, *SUB[key], win)
        st = est[key]["ate_a_cruise"]["+0.00"]
        CHK.append(("R3", f"({pid}) {tr} {key}: plotted path's yaw-only RMSE {rd(rmse, 6)} within 0.005 m of the stored cruise ATE {rd(st, 6)} (data identity)",
                    str(abs(rmse - st) < 0.005), "True",
                    f"{'rerun_dsn_evo.json / dsn_extra_evo.json' if pid == 'a' else 'phase4_fwdc_evo.json'}:{tr}.est.{key}.ate_a_cruise", abs(rmse - st) < 0.005))
        PATHS[(pid, key)] = (NE(key, xyz), NE(key, ref), e, ls, st)
# displayed cruise ATEs against numbers.md (2 dp; numbers.md prints flights 1-3 only)
if ra <= 3:
    check("R3", f"(a) flight {ra} EKF3 cruise ATE (m)", rd(DSNA[ra]["EKF3"], 2), ["4.03", "3.86", "4.10"][ra - 1], "numbers.md", 221)
    check("R3", f"(a) flight {ra} FGO cruise ATE (m)", rd(DSNA[ra]["FGO"], 2), ["4.05", "1.80", "4.48"][ra - 1], "numbers.md", 223)
    check("R3", f"(a) flight {ra} UKF cruise ATE (m)", rd(DSNA[ra]["UKF"], 2), ["3.98", "1.61", "5.17"][ra - 1], "numbers.md", 225)
for key, ln, vals in (("EKF3", 269, ["4.09", "3.60", "4.08"]), ("FGO_baseline", 270, ["4.47", "2.26", "4.54"]), ("UKF_baseline", 271, ["4.96", "1.78", "4.96"]),
                      ("UKF_heading", 291, ["0.13", "0.13", "0.14"]), ("FGO_heading", 292, ["0.06", "0.06", "0.06"])):
    check("R3", f"(b) flight {rb} {key} cruise ATE (m)", rd(P4E[TRB]["est"][key]["ate_a_cruise"]["+0.00"], 2), vals[rb - 1], "numbers.md", ln)

fig, axs = plt.subplots(2, 1, figsize=(15.5, 10.2))
lat = max(np.abs(PATHS[k][0][1]).max() for k in PATHS) * 1.08; lat = max(lat, 2.0)
TT = {"a": f"(a) standard sensors, no heading: standard-sensor dataset, textured floor, flight {ra}",
      "b": f"(b) with the camera heading (offline heading arms): textured-wall camera dataset, textured floor, flight {rb}"}
LBL = {"EKF3": "EKF3 (no heading)", "UKF": "UKF (no heading)", "FGO": "FGO (no heading)", "UKF_baseline": "UKF, no heading",
       "FGO_baseline": "FGO, no heading", "UKF_heading": "UKF, with heading", "FGO_heading": "FGO, with heading"}
for ax, (pid, tr, win, arms, est) in zip(axs, PANELS):
    (gN, gE) = PATHS[(pid, arms[0][0])][1]
    ax.plot(gN, gE, color=TRUTH, lw=3.2, solid_capstyle="round", zorder=2, label="truth (simulator)")
    for key, e, ls in arms:
        (n_, e_), _, col, ls_, st = PATHS[(pid, key)]
        lab = LBL[key] if not (pid == "b" and key == "EKF3") else "EKF3, no heading (no offline heading arm)"
        ax.plot(n_, e_, color=C[e], lw=1.5 if ls == "-" else 1.2, ls=ls if ls == "-" else (0, (5, 3)), zorder=4 if ls == "-" else 3,
                label=f"{lab}: cruise ATE {rd(st, 2)} m")
    ax.set_xlim(-2, 162); ax.set_ylim(-lat, lat); ax.set_aspect(3.0, adjustable="box")
    ax.set_xlabel("along the corridor, North (m)"); ax.set_ylabel("East (m)  [lateral axis stretched]")
    ax.set_title(TT[pid], loc="left", fontsize=10.5)
    ax.legend(loc="upper left", fontsize=8.2, frameon=True, framealpha=0.95, edgecolor=GRID, ncol=2)
fig.canvas.draw()
bb = axs[0].get_window_extent().transformed(fig.dpi_scale_trans.inverted()); x0, x1 = axs[0].get_xlim(); y0, y1 = axs[0].get_ylim()
STRETCH = (bb.height / (y1 - y0)) / (bb.width / (x1 - x0))
for ax in axs:
    ax.text(161, -lat * 0.93, f"lateral axis stretched {rd(STRETCH, 1)}×; same axes in both panels", ha="right", va="bottom", fontsize=8.4, color=INK2)
fig.suptitle("True and estimated paths, top-down: with the camera heading the UKF and FGO paths lie on the true path",
             x=0.01, ha="left", fontsize=12.5, weight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.97))
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUTF, f"R3_trajectory_overlay.{ext}"), dpi=170 if ext == "png" else None, bbox_inches="tight")
plt.close(fig)
CAP3 = (f"{RULE} Chosen: (a) flight {ra} (cross-estimator mean cruise ATEs, ascending, by flight: "
        + ", ".join(f"{i}: {rd(m, 2)}" for m, i in means) + f" m); (b) flight {rb} ({rb_why}). Top-down, cruise window only, truth grey. Each "
        "estimated path is drawn after a best-fit rotation about the vertical and a shift (no scale), fitted over the stored cruise window "
        "against its own ground-truth file. This gives the same average error as the standard 3D alignment used for the cruise ATE (the RMSE "
        "of every plotted path is within 0.005 m of its stored cruise ATE; cross-checks), but cannot roll the path about the corridor axis: "
        "the 3D fit is free to do so on a straight path and can turn sideways drift into up-and-down error that is invisible from above. "
        "The legend gives the stored cruise ATE. The alignment removes a constant heading offset, so the "
        "metres-scale sideways drift of the unaligned estimates (Table 4.1, heading-error decomposition) is not shown; an error along "
        "the corridor (for example EKF3's distance-scale error) lies along the path and barely shows top-down. Dashed: no heading "
        "source; solid: with the camera heading (offline heading arms, UKF and FGO only; EKF3 has no offline heading arm and is shown as the "
        f"no-heading baseline). The lateral (East) axis is stretched {rd(STRETCH, 1)}× relative to the along-corridor axis, the same in both "
        "panels; no log axes. Passive estimators, truth flying (Experiment 1A/1B offline).")
ITEMS.append(dict(num="Figure 4.2", name="R3_trajectory_overlay", kind="figure",
                  title="True and estimated paths, top-down: with the camera heading the UKF and FGO paths lie on the true path", caption=CAP3,
                  inputs=f"~/thesis_data/trials/{TRA}/{{ekf3,ukf,fgo}}/*.tum; ~/thesis_data/trials/{TRB}/{{ekf3,ukf_baseline,fgo_baseline,ukf_heading,"
                         "fgo_heading}/*.tum; windows and cruise ATEs: eval/results/rerun_dsn_evo.json, dsn_extra_evo.json, phase4_fwdc_evo.json",
                  notes=(), files=["R3_trajectory_overlay.png", "R3_trajectory_overlay.pdf"]))
print(f"wrote R3_trajectory_overlay (stretch {rd(STRETCH, 2)})")

# =============================================================================================== R4 INFORMATION vs ESTIMATOR
sp = lambda vals: (max(vals) - min(vals), max(vals) / min(vals))
rowsR4 = []
# --- 1A: standard sensors, textured floor, flights 1-9
med = {e: float(np.median([DSNA[i][e] for i in range(1, 10)])) for e in EST}
for e, s in (("EKF3", "EKF3 4.10"), ("UKF", "UKF 5.13"), ("FGO", "FGO 4.46")):
    check("R4", f"1A median {e} (m)", f"{e} {rd(med[e], 2)}", s, "numbers.md", 236)
check("R4", "1A UKF flights 1–9 range (m)", f"{rd(min(DSNA[i]['UKF'] for i in range(1, 10)), 2)}–{rd(max(DSNA[i]['UKF'] for i in range(1, 10)), 2)}", "1.17–5.85", "numbers.md", 232)
d1, r1 = sp(list(med.values())); pf = [sp(list(DSNA[i].values()))[1] for i in range(1, 10)]
dsc = L("rerun_ds_evo.json")["trials"]; DSV = [dsc[f"ds_tex_r{i}"]["est"]["EKF3"]["ate_a_cruise"]["+0.00"] for i in (1, 2, 3)]
check("R4", "compass reference EKF3 flights 1–3 (m)", " / ".join(rd(v, 2) for v in DSV), "0.66 / 0.69 / 0.07", "numbers.md", 237)
check("R4", "standard-sensor EKF3 flights 1–3 (m)", " / ".join(rd(DSNA[i]["EKF3"], 2) for i in (1, 2, 3)), "4.03 / 3.86 / 4.10", "numbers.md", 221)
ek3 = [DSNA[i]["EKF3"] for i in (1, 2, 3)]
rowsR4.append(["Experiment 1A: standard sensors, textured floor", "cruise ATE (m); n = 9 flights (median per estimator)",
               f"EKF3 {rd(med['EKF3'], 2)}, UKF {rd(med['UKF'], 2)}, FGO {rd(med['FGO'], 2)} (medians)",
               f"{rd(d1, 2)} m; {rd(r1, 2)}× (medians); per flight {rd(min(pf), 2)}–{rd(max(pf), 2)}×",
               "a compass heading, EKF3 only (compass reference dataset, flights 1–3; different flights, same world)",
               f"EKF3 mean {rd(np.mean(ek3), 2)} → {rd(np.mean(DSV), 2)} m; {rd(np.mean(ek3) / np.mean(DSV), 1)}× (means of 3; descriptive)",
               "rerun_dsn_evo.json, dsn_extra_evo.json, rerun_ds_evo.json; numbers.md:221, 232, 236, 237"])
# --- 1B: textured-wall camera dataset, textured floor, flights 1-3 (same bags)
F = {r: P4E[f"fwdc_tex_r{r}"]["est"] for r in (1, 2, 3)}; g = lambda r, k: F[r][k]["ate_a_cruise"]["+0.00"]
for key, ln, vals in (("EKF3", 269, "4.09 / 3.60 / 4.08"), ("FGO_baseline", 270, "4.47 / 2.26 / 4.54"), ("UKF_baseline", 271, "4.96 / 1.78 / 4.96"),
                      ("UKF_heading", 291, "0.13 / 0.13 / 0.14"), ("FGO_heading", 292, "0.06 / 0.06 / 0.06")):
    check("R4", f"1B {key} flights 1/2/3 (m)", " / ".join(rd(g(r, key), 2) for r in (1, 2, 3)), vals, "numbers.md", ln)
spw = [sp([g(r, "UKF_heading"), g(r, "FGO_heading")]) for r in (1, 2, 3)]
spn = [sp([g(r, "EKF3"), g(r, "UKF_baseline"), g(r, "FGO_baseline")]) for r in (1, 2, 3)]
eu = [g(r, "UKF_baseline") / g(r, "UKF_heading") for r in (1, 2, 3)]; ef = [g(r, "FGO_baseline") / g(r, "FGO_heading") for r in (1, 2, 3)]
du = [g(r, "UKF_baseline") - g(r, "UKF_heading") for r in (1, 2, 3)]; df = [g(r, "FGO_baseline") - g(r, "FGO_heading") for r in (1, 2, 3)]
rowsR4.append(["Experiment 1B: with the camera heading, textured walls, textured floor", "cruise ATE (m); n = 3 flights (the same bags with and without the heading)",
               "with heading: UKF 0.13 / 0.13 / 0.14, FGO 0.06 / 0.06 / 0.06; without: EKF3 4.09 / 3.60 / 4.08, UKF 4.96 / 1.78 / 4.96, FGO 4.47 / 2.26 / 4.54",
               f"with heading (UKF, FGO; 2 estimators): {rng([s[0] for s in spw], 2)} m; {rng([s[1] for s in spw], 2)}×. Without (3 estimators): "
               f"{rng([s[0] for s in spn], 2)} m; {rng([s[1] for s in spn], 2)}×",
               "the camera heading (offline heading arm; UKF and FGO only)",
               f"UKF {rng(du, 2)} m lower, {rng(eu, 0)}×; FGO {rng(df, 2)} m lower, {rng(ef, 0)}× (per flight, without ÷ with)",
               "phase4_fwdc_evo.json; numbers.md:269-271, 291-292"])
# --- blank floor (non-† times only)
bb = L("blank_behaviour.json")
BL = [k for k in bb if "blank" in k and not k.startswith("ds_")]
hyp = lambda a, t: float(np.hypot(a[t]["along_m"], a[t]["cross_m"]))
BASEK = lambda k, e: next(bb[k][x] for x in (e.lower(), e.lower() + "_baseline") if x in bb[k])   # as figs_thesis.py's T3
B10 = {e: [hyp(BASEK(k, e), "+10s") for k in BL] for e in ("UKF", "FGO")}
B30 = {e: [hyp(BASEK(k, e), "+30s") for k in BL] for e in ("UKF", "FGO")}
check("R4", "blank n flights", str(len(BL)), "11", "numbers.md", 248)
check("R4", "blank UKF +10 / +30 s ranges (m)", f"{rng(B10['UKF'], 1)} / {rng(B30['UKF'], 1)}", "0.7–1.8 / 15.3–26.8", "numbers.md", 1448)
check("R4", "blank FGO +10 / +30 s ranges (m)", f"{rng(B10['FGO'], 1)} / {rng(B30['FGO'], 1)}", "0.7–1.8 / 16.6–27.7", "numbers.md", 1455)
r30 = [B30["FGO"][i] / B30["UKF"][i] for i in range(len(BL))]
HB = [k for k in BL if "ukf_heading" in bb[k] and bb[k]["ukf_heading"]]
h30 = {e: [hyp(bb[k][f"{e.lower()}_heading"], "+30s") / hyp(BASEK(k, e), "+30s") for k in HB] for e in ("UKF", "FGO")}
rowsR4.append(["Blank floor (no flow aiding; 1A and 1B flights pooled)", f"position error at +30 s after flow loss (m); n = {len(BL)} flights "
               f"(the heading contrast: n = {len(HB)})",
               f"EKF3: invalid (no scored error); UKF {rng(B30['UKF'], 1)}, FGO {rng(B30['FGO'], 1)} (no heading)",
               f"UKF and FGO only (EKF3 flags its position invalid): FGO ÷ UKF per flight {rng(r30, 2)}",
               "the camera heading (same bags, UKF and FGO heading arms)",
               f"with ÷ without, per flight: UKF {rng(h30['UKF'], 2)}, FGO {rng(h30['FGO'], 2)} (the heading holds yaw, not position)",
               "blank_behaviour.json (+30s along/cross); numbers.md:248-249"])
# --- Experiment 2 known tags (live; hindsight)
for k, ln in zip("ABCD", (526, 527, 528, 529)):
    for e, j in zip(LIVE, (1, 2, 3)):
        v = rd(TC[k]["mean_rmse_m"][e], 3)
        check("R4", f"T {k} {e} (m)", f"{v} m", f"{v} m", "numbers.md", ln)
liveA = [TC["A"]["mean_rmse_m"][e] for e in LIVE]; liveD = [TC["D"]["mean_rmse_m"][e] for e in LIVE]
spT = [mm(TC[k]["mean_rmse_m"], LIVE) for k in "ABCD"]; spH = [mm(TC[k]["mean_rmse_m"], HIND) for k in "ABCD"]
tagL = [TC["D"]["mean_rmse_m"][e] / TC["A"]["mean_rmse_m"][e] for e in LIVE]; tagH = [TC["D"]["mean_rmse_m"][e] / TC["A"]["mean_rmse_m"][e] for e in HIND]
rowsR4.append(["Experiment 2: known tags, live", "horizontal RMSE (m); n = 3 flights per condition (mean); 4 conditions",      # m (units pass 2026-10-23; was cm)
               "1 tag: EKF3 " + rd(TC['D']['mean_rmse_m']['EKF3 live'], 3) + ", UKF " + rd(TC['D']['mean_rmse_m']['UKF live'], 3)
               + ", FGO " + rd(TC['D']['mean_rmse_m']['FGO live'], 3) + "; 8 tags: EKF3 " + rd(liveA[0], 3) + ", UKF " + rd(liveA[1], 3)
               + ", FGO " + rd(liveA[2], 3),
               f"max ÷ min {rd(min(spT), 2)}–{rd(max(spT), 2)}× over A–D (H2.3)",
               "more tags: 8 tags (condition A) against 1 tag (D)",
               "1 tag ÷ 8 tags: " + ", ".join(f"{e.split()[0]} {rd(x, 2)}×" for e, x in zip(LIVE, tagL)),
               "expT/t_aggregate.json; numbers.md:526-529, 536"])
rowsR4.append(["Experiment 2: known tags, hindsight", "horizontal RMSE (m); n = 3 flights per condition (mean)",
               "1 tag: FGO batch " + rd(TC['D']['mean_rmse_m'][HIND[0]], 3) + ", smoothed UKF " + rd(TC['D']['mean_rmse_m'][HIND[1]], 3)
               + "; 8 tags: " + rd(TC['A']['mean_rmse_m'][HIND[0]], 3) + ", " + rd(TC['A']['mean_rmse_m'][HIND[1]], 3),
               f"max ÷ min {rd(min(spH), 2)}–{rd(max(spH), 2)}× over A–D (H2.4)", "more tags: 8 tags (A) against 1 tag (D)",
               f"1 tag ÷ 8 tags: FGO batch {rd(tagH[0], 2)}×, smoothed UKF {rd(tagH[1], 2)}×", "expT/t_aggregate.json; numbers.md:526-529, 537"])
# --- Experiment 4 outdoor-indoor
for e, s in (("EKF3 live", "1.42–1.43 m"), ("UKF live", "0.77–0.84 m"), ("FGO live", "0.83–0.89 m")):
    check("R4", f"O {e} indoor RMSE range", rng([OJ[t][e]["indoor_rmse_m"] for t in OFL], 2) + " m", s, "numbers.md", (552, 554))
ind = {e: [OJ[t][e]["indoor_rmse_m"] for t in OFL] for e in LIVE}; ret = {e: [OJ[t][e]["err_10s_after_return_m"] for t in OFL] for e in LIVE}
gi = {e: [ind[e][i] / ret[e][i] for i in range(3)] for e in LIVE}
rowsR4.append(["Experiment 4: outdoor–indoor, live", "indoor horizontal RMSE (m), GNSS off for 123 s; n = 3 flights",
               "EKF3 " + rng(ind['EKF3 live'], 2) + ", UKF " + rng(ind['UKF live'], 2) + ", FGO " + rng(ind['FGO live'], 2),
               f"max ÷ min {rd(min(o_live), 2)}–{rd(max(o_live), 2)}× (H4.2)",
               "GNSS: indoor RMSE (GNSS off) against the error 10 s after GNSS returns (GNSS on); different statistics (an RMSE against a single "
               "time point), not like-for-like",
               "error 10 s after return: " + ", ".join(f"{e.split()[0]} {rng(ret[e], 3)} m" for e in LIVE)
               + "; indoor ÷ that: " + ", ".join(f"{e.split()[0]} {rng(gi[e], 0)}×" for e in LIVE),
               "expO/O_r1, O_r2, O_r3b.json (indoor_rmse_m; err_10s_after_return_m has no numbers.md cell); numbers.md:552-554, 559"])
rowsR4.append(["Experiment 4: outdoor–indoor, hindsight", "indoor horizontal RMSE (m); n = 3 flights",
               "FGO batch " + rng([OJ[t][HIND[0]]['indoor_rmse_m'] for t in OFL], 2) + ", smoothed UKF " + rng([OJ[t][HIND[1]]['indoor_rmse_m'] for t in OFL], 2),
               f"max ÷ min {rd(min(o_hind), 2)}–{rd(max(o_hind), 2)}× (H4.3)", "hindsight (whole-flight smoothing) against live, same flights",
               "live ÷ hindsight, best live vs best hindsight per flight: " + rng([min(OJ[t][e]['indoor_rmse_m'] for e in LIVE) / min(OJ[t][e]['indoor_rmse_m'] for e in HIND) for t in OFL], 2) + "×",
               "expO/O_*.json; numbers.md:552-556, 560"])
# --- Experiment 5 tag hold
HC = L("expH/h_comparative_2026-10-11.json"); HE = HC["EKF3 (S1 far, flying)"]
HS = {("re" if k.startswith("re-flown") else "old"): v for k, v in HC["sets"].items()}
hold = {"EKF3": [x["hold_mean_mm"] for x in HE], "UKF": [x["hold_mean_mm"] for x in HS["re"]["UKF"]], "FGO": [x["hold_mean_mm"] for x in HS["re"]["FGO"]]}
for i, (ln, exp_) in enumerate(((667, "7.8 / 6.4 / 8.3"), (668, "7.9 / 7.1 / 8.3"), (669, "7.8 / 6.7 / 8.6"))):
    check("R4", f"H run {i + 1} hold mean EKF3/UKF/FGO (mm)", f"{rd(hold['EKF3'][i], 1)} / {rd(hold['UKF'][i], 1)} / {rd(hold['FGO'][i], 1)}",
          exp_, "numbers.md", ln)
FLYF = {"EKF3": (["s1far_r1", "s1far_r2", "s1far_r3b"], "EKF3"), "UKF": (["s2v2_r1", "s2v2_r2", "s2v2_r3"], "UKF_port"),
        "FGO": (["s3v2_r1", "s3v2_r2", "s3v2_r3"], "FGO_flying")}
d30 = {e: [L(f"expH/{f}.json")["losses"][2][k]["drift_end_m"] * 1000 for f in FLYF[e][0]] for e, (_, k) in FLYF.items()}
assert all(abs(L(f"expH/{f}.json")["losses"][2]["duration_s"] - 30) < 2 for e in FLYF for f in FLYF[e][0])
for e, f, ln, idx in (("EKF3", "s1far_r1", 621, 0), ("EKF3", "s1far_r2", 622, 1), ("EKF3", "s1far_r3b", 623, 2)):
    exp_ = {621: "15 / 10 / 3 / 7", 622: "19 / 12 / 26 / 23", 623: "12 / 17 / 11 / 16"}[ln]
    got = " / ".join(rd(L(f"expH/{f}.json")["losses"][j]["EKF3"]["drift_end_m"] * 1000, 0) for j in range(4))
    check("R4", f"H {f} EKF3 end-of-loss drift 5/15/30/move (mm)", got, exp_, "numbers.md", ln)
check("R4", "H UKF-flying hold set 30 s end-of-loss drift r1/r2/r3 (mm)", " / ".join(rd(x, 0) for x in d30["UKF"]), "6 / 10 / 10", "numbers.md", 644)
check("R4", "H FGO-flying hold set 30 s end-of-loss drift r1/r2/r3 (mm)", " / ".join(rd(x, 0) for x in d30["FGO"]), "22 / 15 / 9", "numbers.md", 646)
spHold = [sp([hold[e][i] for e in EST]) for i in range(3)]
rowsR4.append(["Experiment 5: tag hold (each estimator flying)", "mean hold error (mm), tag visible; n = 3 flights per estimator (paired by run index, not trajectory)",
               "EKF3 " + rng(hold['EKF3'], 1) + ", UKF " + rng(hold['UKF'], 1) + ", FGO " + rng(hold['FGO'], 1),
               f"{rng([s[0] for s in spHold], 1)} mm; {rng([s[1] for s in spHold], 2)}× per run",
               "the tag: visible (hold error) against hidden for 30 s (drift at the end of the loss); different statistics, not like-for-like",
               "30 s loss drift: " + ", ".join(f"{e} {rng(d30[e], 0)} mm" for e in EST) + "; ÷ the same run's hold error: "
               + ", ".join(f"{e} {rng([d30[e][i] / hold[e][i] for i in range(3)], 1)}×" for e in EST),
               "expH/h_comparative_2026-10-11.json; expH/s1far_r*.json, s2v2_r*.json, s3v2_r*.json; numbers.md:621-623, 644, 646, 667-669"])
save_tab("Table 7.5", "R4_information_vs_estimator", "Spread between estimators against the effect of adding information, per condition",
         "For each condition: the primary metric of each estimator, the best–worst spread across the estimators (max − min and max ÷ min), and "
         "the change when information is added (a heading, more tags, GNSS, or the tag itself). Spreads and ratios are computed here from the "
         "stored full-precision values and rounded once; their inputs are cross-checked against numbers.md. The numbers are reported without "
         "a conclusion beyond them.",
         ["condition", "metric; n", "estimator values", "spread across estimators", "information added (contrast)", "effect of the information", "source"],
         rowsR4, [22, 26, 40, 30, 32, 40, 30],
         "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json, rerun_ds_evo.json, phase4_fwdc_evo.json, blank_behaviour.json, expT/t_aggregate.json, "
         "expO/O_*.json, expH/h_comparative_2026-10-11.json, expH/s1far_r*.json, s2v2_r*.json, s3v2_r*.json",
         notes=["Spread = max − min and max ÷ min of the stated metric over the estimators that have a value in that condition (2 in Experiment 1B "
                "with heading and on the blank floor; 3 elsewhere). 'Per flight' ranges are the range over flights of the per-flight spread or ratio. "
                "Ratios use the stored full-precision values, not the displayed ones.",
                "Experiment 1A's information contrast (a compass, EKF3 only) compares different flights of the same world and is descriptive. Experiment "
                "1B's contrast is paired (the same bags with and without the heading arm); EKF3 has no offline heading arm (by ruling). The plain-wall "
                "camera dataset is omitted: on its checkerboard floor the heading failed validation (H1.2), so no heading benefit is claimed there "
                "(restatement ruling 4).",
                "Blank floor: the +60 s and end-of-cruise values are runaway magnitudes (†, not reproducible across builds), so no ratio is formed from "
                "them; +30 s is used. Experiments 4 and 5 compare different statistics across the information contrast (stated in the row), so those "
                "ratios are indicative only. Experiment 3 (loop closure) has one thesis estimator and no spread: the thesis EKF3 and UKF, as "
                "configured, have no landmark states; a UKF with tag landmark states (extension experiment E5, not in this table) also bounded "
                f"its live drift (H-E5.1 {XE5}). Experiment 1C (closed loop) passes 3/3 for "
                "every estimator with the heading (Table 4.3), so it has no spread in its primary metric."])

# =============================================================================================== index_results.md
nC = len(CHK); nCok = sum(c[5] for c in CHK); nQ = len(QCHK); nQok = sum(q[3] for q in QCHK)
W = []
W.append("# Results and discussion tables and figure: index (PROPOSED numbering)\n")
W.append(f"*Generated by `{SCRIPT}` at commit `{COMMIT}`. Stored results and documents only: no simulation, no estimator re-run, and "
         "nothing in numbers.md, METHODOLOGY.md, the frozen pack or the in-use thesis files was edited. Not yet in the combined PDF "
         "(integration comes later).*\n")
W.append(f"**Rounding:** every number goes through `rd()` from `eval/figs_thesis.py`, loaded by parsing that file (it is not run). SHA-256 of "
         f"`rd()`'s source: `{RD_SHA}`. Palette: the fixed Okabe–Ito colours of figs_thesis.py (EKF3 {C['EKF3']}, UKF {C['UKF']}, FGO {C['FGO']}, "
         f"truth {TRUTH}), asserted equal at run time.\n")
W.append(f"**Cross-checks:** {nCok}/{nC} numeric checks EXACT (display = stored value rounded once = the string typed from numbers.md, and that "
         f"string occurs in the cited numbers.md line; for Figure 4.2, the plotted path's RMSE = the stored cruise ATE to 6 dp); {nQok}/{nQ} source "
         "checks (every quoted pre-registration and every outcome string found, in order, at its cited lines).\n")
W.append("## Proposed numbers (provisional; the chapter plan is the user's)\n")
W.append("| proposed number | file | content | why this number |\n|---|---|---|---|")
W.append("| **Table 7.3** | `tables/R1_hypothesis_scorecard.*` | hypothesis scorecard | Chapter 7 = synthesis (vocabulary §6); after Tables 7.1–7.2 |")
W.append("| **Table 7.4** | `tables/R2_corrections_by_discovery.*` | corrections by discovery route | synthesis / threats to validity; could move to the appendix (A.4) |")
W.append("| **Figure 4.2** | `figures_thesis/R3_trajectory_overlay.*` | true vs estimated paths, Experiment 1A and 1B | Chapter 4 = Experiment 1; after Figure 4.1 |")
W.append("| **Table 7.5** | `tables/R4_information_vs_estimator.*` | estimator spread vs information effect | synthesis |\n")
W.append("None of these numbers is used in `figs_thesis.py`'s TNUM (4.1, 5.1–5.3, 6.1, 7.1, 7.2, 4.1–4.3, A.1–A.3) and none is in Chapter 3.\n")
for it in ITEMS:
    W.append(f"## {it['num']} ({it['kind']}; file `{it['name']}`): {it['title']}\n")
    W.append(f"**Caption.** {it['caption']}\n")
    for n in it["notes"]:
        W.append(f"*Note.* {n}\n")
    W.append(f"**Inputs.** {it['inputs']}\n")
    W.append("**Files.** " + ", ".join(f"`{f}`" for f in it["files"]) + "\n")
W.append("## Verdict counts (Table 7.3)\n")
W.append(f"{len(R1)} scored parts over {len(LABELS)} labels ({', '.join(LABELS)}): " + "; ".join(f"**{c}** {CNT[c]}" for c in CATS) + ".\n")
W.append("## Figure 4.2 selection\n")
W.append(f"Rule (fixed in the code and the caption before any path was loaded): {RULE}\n")
W.append(f"Result: (a) `{TRA}`; (b) `{TRB}` ({rb_why}). Cross-estimator mean cruise ATE by flight, ascending: "
         + ", ".join(f"flight {i} {rd(m, 3)} m" for m, i in means) + ".\n")
W.append("## Numeric cross-checks (exact)\n")
W.append("| table | check | computed | expected | source | result |\n|---|---|---|---|---|---|")
for t, lab, c_, e_, s_, ok in CHK:
    W.append(f"| {t} | {md(lab)} | {md(c_)} | {md(e_)} | {md(s_)} | {'OK' if ok else '**MISMATCH**'} |")
W.append("\n## Source checks (quotes and outcome strings at the cited lines)\n")
W.append("| table | item | cited lines | result |\n|---|---|---|---|")
for t, lab, s_, ok in QCHK:
    W.append(f"| {t} | {md(lab)} | {s_} | {'found' if ok else '**NOT FOUND**'} |")
W.append("\n## Gaps: what cannot be built from existing sources (listed, not inferred)\n")
for gtxt in [
    "**H1.3 restated verdict.** No Phase 5 verdict was re-scored after the final re-runs; Table 7.3 shows the 2026-09-29 verdict (M:3440-3448) "
    "beside the restated magnitudes (numbers.md:263).",
    "**X1.b values.** The exploratory robust-vs-hard-gated FGO table (M:8464-8471) predates the final re-runs and has no restated numbers.md row; "
    "only its replication (H1.7) is restated.",
    "**V3.** Not re-scorable (its labels were never recorded; ruling 6, 2026-10-09). It fits none of the five categories exactly; it is counted "
    "as WITHDRAWN ('listed, not restated').",
    "**H5.2–H5.4b pre-registration.** Only the design draft (`docs/tag_hold_design.md` §e) states them; there is no METHODOLOGY pre-registration line.",
    "**Correction-to-claim attribution.** Corrections applied in one batch (14–17; and 18 alone) are not attributed to individual claims rows "
    "except the three ruled exceptions; corrections 1–13, 19 and 20 predate the claims table, so no claims row records their effect.",
    "**Experiment 4 'with GNSS' accuracy.** No stored outdoor RMSE exists; the error 10 s after GNSS returns (`err_10s_after_return_m`, no "
    "numbers.md cell) is the only with-GNSS value, a single time point, not like-for-like with the indoor RMSE.",
    "**Experiment 5 information contrast.** Hold error (tag visible) and end-of-loss drift (tag hidden) are different statistics; no like-for-like "
    "'without the tag' hold error exists.",
    "**Blank floor.** Only the non-runaway +10 s and +30 s errors can carry a ratio; the +60 s and end-of-cruise values are † runaway magnitudes.",
    "**Figure 4.2 unaligned drift.** The paths are drawn after a yaw-only alignment that reproduces the stored cruise ATE to within 0.005 m (ruling 2026-10-21); the unaligned "
    "metres-scale sideways drift is the heading-error decomposition of Table 4.1, not redrawn here.",
]:
    W.append(f"- {gtxt}")
W.append("")
open(INDEX, "w").write("\n".join(W))
print(f"wrote {INDEX}: numeric checks {nCok}/{nC}, source checks {nQok}/{nQ}; verdicts {CNT}")
