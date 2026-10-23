#!/usr/bin/env python3
"""READER SUMMARY PAGES (2026-10-18): one plain-language page per experiment, separate from the detailed thesis tables.

User request (verbatim): "can you just generate the plots with the essential information only, it is hard to parse any
meaning from the tables and plots due to lots of extra stuff, just give the comparison numbers, the experiment, and simply
state the metrics which were used to identify if the flight passed or failed". Added: "make sure everything is easy to
understand and simple, it should be easy to understand for someone looking at it for the first time".

Plotting and tabulating only. NO number is recomputed from raw data and nothing is re-run: every printed number is computed
from the SAME stored result files that eval/figs_thesis.py reads (eval/results/**), rounded ONCE by the thesis rounding rule
rd() (parsed from eval/figs_thesis.py, which is not run or imported, because it runs at module level), and must equal, EXACTLY
as a string, the value typed here from the current thesis tables and figures. Each expected string must also be found in the
thesis display file it is quoted from (docs/thesis/tables/*.md, docs/thesis/figures_thesis/index*.md), and, where numbers.md
carries it, in the cited numbers.md line (the Errata lines E4-E6 for the blank floor). Every pass bound printed on a page is
read from its METHODOLOGY line at build time. A guard then scans every page's text: any number not covered by a check stops
the build.

The pages carry no provenance; all of it is in docs/thesis/summary/index_summary.md.

Outputs: docs/thesis/summary/summary_NN_<short>.png, summary_plots.pdf (contents page, a "how to read" page, then the pages in
experiment order), index_summary.md.
Usage: python3 eval/figs_thesis_summary.py   (numpy + matplotlib only)."""
import ast, hashlib, json, math, os, re, subprocess, sys, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results")
OUT = os.path.join(ROOT, "docs", "thesis", "summary"); os.makedirs(OUT, exist_ok=True)
PDF = os.path.join(OUT, "summary_plots.pdf"); INDEX = os.path.join(OUT, "index_summary.md")
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
L = lambda f: json.load(open(os.path.join(RES, f)))

# ------------------------------------------------------------------ rd(): the thesis rounding rule, parsed (not run) from figs_thesis.py
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read()
_rd = next(n for n in ast.parse(_src).body if isinstance(n, ast.FunctionDef) and n.name == "rd")
RD_SRC = ast.get_source_segment(_src, _rd); RD_SHA = hashlib.sha256(RD_SRC.encode()).hexdigest()
_ns = {}; exec(compile(ast.Module(body=[_rd], type_ignores=[]), FT, "exec"), _ns); rd = _ns["rd"]
assert RD_SHA == "e7320d3b8f377157c0c6512b2c0b77c978ac309a7130d2729480b786e02589b3", "rd() changed in figs_thesis.py"


def rng(vals, n=2):
    return f"{rd(min(vals), n)}–{rd(max(vals), n)}"


# ------------------------------------------------------------------ SI display (2026-10-22, user request: "make sure all the plots
# and the results walkthrough are all in si units, not cm, mm etc"). Lengths in metres, times in seconds (angles stay in degrees).
# Units pass (2026-10-23, user ruling: one unit per quantity, the same in a table as in its figure; SI prefixes allowed): the
# Experiment 5 hold quantities (hold error, tag-loss drift, drift limits) are in mm, as in Tables 6.1 and 7.1 (docs/thesis/units.md).
# A value is converted by an EXACT decimal shift of its stored full-precision form and rounded ONCE at the printed precision (rd_si);
# the expected thesis string is converted by the same exact decimal shift of the string (si_str), the factor stated in the check
# label. The thesis tables keep their own units, so the "shown in" checks still look for the native string there.
def rd_si(v, n, k=0):
    """rd() of the stored value v shifted exactly by 10**k (k = -3: stored mm -> m; k = 0: stored in m). n may be negative (n = -3:
    nearest 1000 m)."""
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(str(float(v))).scaleb(k).quantize(Decimal(1).scaleb(-int(n)), rounding=ROUND_HALF_UP)
    out = format(d, "f")
    return out[1:] if out.startswith("-") and d == 0 else out


def rng_si(vals, n, k=0):
    return f"{rd_si(min(vals), n, k)}–{rd_si(max(vals), n, k)}"


def si_str(s_, k):
    """Every number in the thesis string s_ shifted exactly by 10**k as a decimal ('7.8–7.9' mm, k = -3 -> '0.0078–0.0079' m)."""
    from decimal import Decimal
    return re.sub(r"\d+(?:\.\d+)?", lambda m_: format(Decimal(m_.group(0)).scaleb(k), "f"), s_)


NNBSP = "\u202f"     # narrow no-break space: the SI digit-group separator


def grp(s_):
    """SI digit grouping (narrow no-break space every three digits) of every whole number of five or more digits."""
    return re.sub(r"(?<![\d.])\d{5,}(?![\d.])", lambda m_: f"{int(m_.group(0)):,}".replace(",", NNBSP), s_)


# ------------------------------------------------------------------ style (Okabe-Ito, fixed per estimator; >= 11 pt everywhere)
C = {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"}
MK = {"EKF3": "o", "UKF": "^", "FGO": "s"}
GREY = "#999999"; INK = "#111111"; INK2 = "#444444"; GRID = "#e6e6e6"
EST = ("EKF3", "UKF", "FGO")
NAME = {"EKF3": "EKF3 (ArduPilot's standard filter)", "UKF": "UKF (unscented Kalman filter)", "FGO": "FGO (factor-graph optimiser)"}
TICK = {"EKF3": "EKF3\n(ArduPilot's\nstandard filter)", "UKF": "UKF\n(unscented\nKalman filter)", "FGO": "FGO\n(factor-graph\noptimiser)"}
plt.rcParams.update({"font.size": 13, "axes.titlesize": 14, "axes.labelsize": 13, "xtick.labelsize": 12, "ytick.labelsize": 12,
                     "legend.fontsize": 12, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
PAGE_W, PAGE_H = 11.69, 8.27          # A4 landscape

# ------------------------------------------------------------------ cross-checks
DISP = {k: os.path.join(ROOT, "docs", "thesis", p) for k, p in {
    "T1": "tables/T1_scorecard.md", "T2": "tables/T2_accuracy_heading.md", "T3": "tables/T3_blank_floor.md",
    "T4": "tables/T4_closed_loop.md", "T5": "tables/T5_H_tag_loss_drift.md", "T6": "tables/T6_O_indoor_rmse.md",
    "T7": "tables/T7_failure_behaviour.md", "T8": "tables/T8_hindsight_ratio.md", "R1": "tables/R1_hypothesis_scorecard.md",
    "IDX": "figures_thesis/index.md"}.items()}
DNAME = {"T1": "Table 7.1 (T1_scorecard.md)", "T2": "Table 4.1 (T2_accuracy_heading.md)", "T3": "Table 4.2 (T3_blank_floor.md)",
         "T4": "Table 4.3 (T4_closed_loop.md)", "T5": "Table 6.1 (T5_H_tag_loss_drift.md)", "T6": "Table 5.1 (T6_O_indoor_rmse.md)",
         "T7": "Table 7.2 (T7_failure_behaviour.md)", "T8": "Table 5.2 (T8_hindsight_ratio.md)", "R1": "Table 7.3 (R1_hypothesis_scorecard.md)",
         "IDX": "figures_thesis/index.md (check rows of Figures 5.1, 5.2 and Table A.2)"}
_TXT = {}; _LINES = {}
NM = "docs/thesis/numbers.md"; M_ = "METHODOLOGY.md"


def _text(k):
    return _TXT.setdefault(k, open(DISP[k]).read())


def _line(path, n):
    return _LINES.setdefault(path, open(os.path.join(ROOT, path)).read().split("\n"))[n - 1]


CHK = []          # every check: page, kind, label, computed, expected, where, ok
PAGE = None       # the page currently being built


def num(label, computed, expected, shown, nm=()):
    """A printed number. computed = stored value rounded once by rd(); expected = the string typed from the thesis display.
    shown = [(display key, string that must occur in that display file)]; nm = [(numbers.md line, string that must occur in
    it)]. All must hold. Returns the computed string (the only string the page may print)."""
    c, e = str(computed), str(expected)
    ok = c == e
    where = []
    for k, s in shown:
        f = s in _text(k); ok &= f
        where.append(f"{DNAME[k]} shows '{s}'" + ("" if f else " [NOT FOUND]"))
    for ln, s in nm:
        f = s in _line(NM, ln); ok &= f
        where.append(f"numbers.md:{ln} has '{s}'" + ("" if f else " [NOT FOUND]"))
    CHK.append(dict(page=PAGE, kind="number", label=label, computed=c, expected=e, where="; ".join(where), ok=ok))
    if not ok:
        print("   CHECK FAIL:", PAGE, label, repr(c), repr(e), where)
    return c


def disp(label, expected, shown, nm=()):
    """A DISPLAY-ONLY string printed on a page (a label, a fixed word or a unit conversion of a bound): it is not computed from
    a stored value, so it only has to occur in the thesis display file (and the cited numbers.md line). Counted separately."""
    e = str(expected); ok = True; where = []
    for k, s_ in shown:
        f = s_ in _text(k); ok &= f
        where.append(f"{DNAME[k]} shows '{s_}'" + ("" if f else " [NOT FOUND]"))
    for ln, s_ in nm:
        f = s_ in _line(NM, ln); ok &= f
        where.append(f"numbers.md:{ln} has '{s_}'" + ("" if f else " [NOT FOUND]"))
    CHK.append(dict(page=PAGE, kind="display", label=label, computed=e, expected=e, where="; ".join(where), ok=ok))
    if not ok:
        print("   DISPLAY FAIL:", PAGE, label, where)
    return e


def rule(path, line, phrase, label):
    """A pass bound or rule wording printed on a page: line `line` of `path` must contain `phrase` (read at build time)."""
    ok = phrase in _line(path, line)
    CHK.append(dict(page=PAGE, kind="rule", label=label, computed=phrase if ok else _line(path, line).strip()[:90], expected=phrase,
                    where=f"{os.path.basename(path)}:{line}", ok=ok))
    if not ok:
        print("   RULE FAIL:", PAGE, path, line, phrase)
    return phrase


def counted(label, computed, expected, why):
    """A count printed on a page that is a property of the stored data set (flights, bags, losses), not a result value."""
    c, e = str(computed), str(expected); ok = c == e
    CHK.append(dict(page=PAGE, kind="count", label=label, computed=c, expected=e, where=why, ok=ok))
    if not ok:
        print("   COUNT FAIL:", PAGE, label, c, e)
    return c


# ------------------------------------------------------------------ data (the loaders of eval/figs_thesis.py, copied)
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
pt = L("dsn_paired_test.json")
DSN = {}
for est in EST:
    DSN[est] = [(i, ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"]["+0.00"]) for i in range(1, 10)
                if est in ev[f"dsn_tex_r{i}"]["est"] and ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"].get("+0.00") is not None]
CAMB = [(ds, r) for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)]
P4 = {}
for ds, r in CAMB:
    e_ = L(f"phase4_{ds}_evo.json")["trials"][f"{ds}_tex_r{r}"]["est"]
    P4[(ds, r)] = {k: e_[k]["ate_a_cruise"]["+0.00"] for k in ("EKF3", "UKF_baseline", "FGO_baseline", "UKF_heading", "FGO_heading")}
bb = L("blank_behaviour.json")
BLANK = {}
for est, keys in (("UKF", ("ukf", "ukf_baseline")), ("FGO", ("fgo", "fgo_baseline"))):
    rows = []
    for trn, v in bb.items():
        if "blank" not in trn or trn.startswith("ds_"):
            continue
        a = next((v[k] for k in keys if k in v), None)
        if a is None:
            continue
        rows.append([math.hypot(a[t]["along_m"], a[t]["cross_m"]) for t in ("+10s", "+30s", "+60s", "end")])
    BLANK[est] = np.array(rows)
EK_INV = [v["EKF3_invalid_period"]["duration_in_cruise_s"] for k, v in bb.items() if "blank" in k and "EKF3_invalid_period" in v]
VAL = L("fwd_validation.json")["aggregate"]
WIN = {"EKF3": (155, 215), "UKF": (146, 218), "FGO": (145, 196)}
HALF = {"EKF3": ("cl_a_tex_half", [f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)]),
        "UKF": ("cl_ukf_a_tex_half_v2", [f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)]),
        "FGO": ("cl_fgo_a_tex_half_v3", [f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)])}
agg = L("expT/t_aggregate.json"); TCOND = "ABCD"
TRK = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
OFL = ("O_r1", "O_r2", "O_r3b")
OI = {n: [L(f"expO/{t}.json")["tracks"][n]["indoor_rmse_m"] for t in OFL] for n in TRK}
LL = {(m, k): [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{m} {k}"] for r in (1, 2, 3)] for m in ("lc", "nolc") for k in ("live", "hindsight")}
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = ["s2v2_r1", "s2v2_r2", "s2v2_r3"]; S3V = ["s3v2_r1", "s3v2_r2", "s3v2_r3"]
FLY = {"EKF3": (S1 + S1F, "EKF3"), "UKF": (S2V, "UKF_port"), "FGO": (S3V, "FGO_flying")}
BAND = {"EKF3": [50, 100, 200, 150], "FGO": [50, 100, 200, 150], "UKF": [100, 200, 400, 300]}


def drifts(trs, key):
    out = [[], [], [], []]
    for t in trs:
        for i, lo in enumerate(HJ(t)["losses"]):
            out[i].append(float(rd_si(lo[key]["effective"]["drift_m"], 12, 3)))      # mm by an exact decimal shift (units pass)
    return out


# ------------------------------------------------------------------ page machinery
PAGES = []          # dict(id, file, title, what, metric, rule, result, fig)
TXT = []            # every string drawn on the current page (scanned by the number guard)


def wrap(s, w):
    return "\n".join(textwrap.wrap(s, w, break_long_words=False, break_on_hyphens=False))


def T(s):
    TXT.append(s); return s


TOP = 0.755          # top of the chart / table area (figure fraction)
AXL = []            # (axes, left, width, pad) placed once the footer height is known


def AX(left, width, pad):
    """A chart or legend axes whose bottom is set by foot(): bottom = top of the footer + pad, top = TOP."""
    ax = FIG.add_axes([left, 0.4, width, 0.3]); AXL.append((ax, left, width, pad)); return ax


def new_page(pid, short, title, what):
    global PAGE, TXT, FIG, AXL
    PAGE = pid; TXT = []; AXL = []
    fig = FIG = plt.figure(figsize=(PAGE_W, PAGE_H))
    fig.text(0.045, 0.945, title, fontsize=19, weight="bold", va="top", ha="left")
    fig.text(0.045, 0.885, wrap("What this tests: " + T(what), 100), fontsize=14, va="top", ha="left", color=INK2, style="italic")
    return fig, dict(id=pid, short=short, title=title, what=what)


def foot(fig, meta, metric, rule_s, result):
    """The three lines under the chart: Metric, Pass rule, Result (labels bold), laid out from the bottom of the page up; then
    every chart axes of the page is placed between the footer and TOP."""
    LH, GAP, WR = 0.0285, 0.016, 94
    blocks = [(lab, wrap(T(body), WR)) for lab, body in (("Metric:", metric), ("Pass rule:", rule_s), ("Result:", result))]
    h = sum(LH * (w.count("\n") + 1) + GAP for _, w in blocks)
    y = top = 0.035 + h
    fig.add_artist(Line2D([0.045, 0.955], [top + 0.012, top + 0.012], color=GRID, lw=1.2, transform=fig.transFigure))
    for lab, w in blocks:
        fig.text(0.045, y, lab, fontsize=13.5, weight="bold", va="top", ha="left")
        fig.text(0.155, y, w, fontsize=13.5, va="top", ha="left", linespacing=1.25)
        y -= LH * (w.count("\n") + 1) + GAP
    meta.update(metric=metric, rule=rule_s, result=result, top=top)
    for ax, l, wd, pad in AXL:
        b = top + pad
        assert TOP - b > 0.18, f"{meta['id']}: chart area too small ({TOP - b:.2f})"
        ax.set_position([l, b, wd, TOP - b])
    return top


NUMTOK = re.compile(r"\d+(?:\.\d+)?")


def finish(fig, meta):
    """Number guard: every number in the page text (title excluded: it carries only the experiment number) must occur in a
    computed check string or a cited rule phrase of THIS page. Then save the PNG."""
    if "deferred" in meta:
        meta.pop("deferred")()
    allowed = set()
    for c in CHK:
        if c["page"] == PAGE and c["ok"]:
            allowed |= set(NUMTOK.findall(c["computed"])) | set(NUMTOK.findall(c["expected"]))
    stray = sorted({t for s in TXT for t in NUMTOK.findall(s.replace("EKF3", "EKF"))} - allowed)
    assert not stray, f"page {PAGE}: number(s) {stray} printed without a check: " + " || ".join(s for s in TXT if set(NUMTOK.findall(s)) & set(stray))
    fn = f"summary_{meta['id']}_{meta['short']}.png"
    fig.savefig(os.path.join(OUT, fn), dpi=150)
    meta.update(file=fn, fig=fig); PAGES.append(meta)
    print(f"wrote {fn}")


def legend_est(ax, ests=EST, extra=(), **kw):
    h = [Line2D([], [], ls="none", marker=MK[e], color=C[e], ms=10, label=NAME[e].replace(" (", "\n(")) for e in ests] + list(extra)
    return ax.legend(handles=h, frameon=False, **kw)


def table(fig, meta, header, rows, widths, fs=13.5):
    """A minimal ruled table drawn as text, from TOP down with a fixed line height. Drawn once the footer is placed (deferred to
    finish() if foot() has not run yet)."""
    if "top" not in meta:
        meta["deferred"] = lambda: table(fig, meta, header, rows, widths, fs)
        return None
    tot = sum(widths); xs = [sum(widths[:i]) / tot for i in range(len(widths) + 1)]
    wraps = [max(8, int(wd / tot * 90 * 13.5 / fs * (0.86 if j == 0 else 1.0))) for j, wd in enumerate(widths)]
    allr = [header] + rows
    nl = [max((wrap(str(c), wraps[j]).count("\n") + 1) for j, c in enumerate(r)) for r in allr]
    LH = fs * 1.3 / 72 / PAGE_H
    h = LH * (sum(nl) + 0.8 * len(allr))
    assert TOP - h > meta["top"] + 0.03, f"{meta['id']}: table does not fit"
    ax = fig.add_axes([0.045, TOP - h, 0.91, h]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, h)
    y = h
    for i, r in enumerate(allr):
        hh = LH * (nl[i] + 0.8)
        if i == 0:
            ax.add_patch(Rectangle((0, y - hh), 1, hh, color="#f2f2f2", lw=0))
        for j, c in enumerate(r):
            T(str(c))
            ax.text(xs[j] + 0.006, y - LH * 0.4, wrap(str(c), wraps[j]), fontsize=fs, va="top", ha="left", linespacing=1.15,
                    weight="bold" if (i == 0 or j == 0) else "normal")
        y -= hh
        ax.plot([0, 1], [y, y], color=GREY if i < len(allr) - 1 else INK2, lw=0.8 if i < len(allr) - 1 else 1.2)
    ax.plot([0, 1], [h, h], color=INK2, lw=1.2)
    return ax


def label_val(ax, x, y, s, **kw):
    T(s)
    kw.setdefault("fontsize", 13); kw.setdefault("ha", "left"); kw.setdefault("va", "center")
    return ax.text(x, y, s, **kw)


def rbox(ax, x, vals, color, live, w=0.34, minh=0.012):
    """One mark per estimator per condition when the value is a range over flights: a box from the lowest to the highest
    flight (at least a thin bar), filled = live, open (white with a coloured edge) = hindsight."""
    lo_, hi_ = min(vals), max(vals); span = ax.get_ylim()[1] - ax.get_ylim()[0]
    hgt = max(hi_ - lo_, minh * span)
    ax.add_patch(Rectangle((x - w / 2, lo_ - (hgt - (hi_ - lo_)) / 2), w, hgt, facecolor=color if live else "white", edgecolor=color,
                           lw=2.2, zorder=3))
    return lo_ - (hgt - (hi_ - lo_)) / 2 + hgt


def bound(ax, y, s, x=None, **kw):
    """A pass bound: grey dashed line labelled with its value."""
    ax.axhline(y, color=GREY, ls=(0, (6, 4)), lw=1.6, zorder=1)
    T(s)
    ax.text(ax.get_xlim()[1] if x is None else x, y, s, color="#555555", fontsize=12.5, ha="right", va="bottom", **kw)


# =================================================================== 1A, textured floor
fig, meta = new_page("01", "1A_textured", "Experiment 1A: position error with standard sensors, checkerboard floor",
                     "How accurately three position estimators track a drone along a long indoor corridor with no GPS, using only "
                     "motion sensors, a downward camera and a height sensor.")
med = {e: float(np.median([v for _, v in DSN[e]])) for e in EST}
lo = {e: min(v for _, v in DSN[e]) for e in EST}; hi = {e: max(v for _, v in DSN[e]) for e in EST}
EXP1A = {"EKF3": "4.10 (3.11–4.12)", "UKF": "5.13 (1.17–5.85)", "FGO": "4.46 (1.27–4.61)"}
NM1A = {"EKF3": (), "UKF": ((232, "5.13 / 1.17–5.85"),), "FGO": ((236, "FGO 4.46"),)}
V1A = {e: num(f"median (range) of flights 1–9, {e} (m)", f"{rd(med[e], 2)} ({rd(lo[e], 2)}–{rd(hi[e], 2)})", EXP1A[e],
              [("T2", EXP1A[e])], NM1A[e] + ((236, f"{e} {rd(med[e], 2)}"),)) for e in EST}
n9 = counted("flights per estimator (textured floor, flights 1–9)", "/".join(str(len(DSN[e])) for e in EST), "9/9/9", "rerun_dsn_evo.json + dsn_extra_evo.json, one cruise ATE per flight; Table 4.1 header '9 flights'")
nf, nneg = len(pt["new_flights"]), pt["n_neg"]
v_neg = num("confirmatory test: flights with EKF3 lower, of all", f"{nneg} of {nf}", "5 of 7", [("T1", "EKF3 lower on 5 of 7")], [(227, "d < 0 on 5/7")])
v_ci = num("confirmatory test: 95% interval of the mean difference EKF3 − FGO (m)",
           f"{rd(pt['t95_ci_m'][0], 3, sign=True)} to {rd(pt['t95_ci_m'][1], 3, sign=True)}", "-0.989 to +0.947",
           [("T1", "95% CI -0.989 to +0.947 m")], [(227, "95% CI [−0.989, +0.947]")])
num("confirmatory test verdict", pt["verdict"], "no ordering claimed", [("T1", "no ordering is claimed")], [(227, "no ordering claimed")])
rule(M_, 5650, "at least 6 of 7", "H1.1 rule (a): EKF3 lower on at least 6 of 7 flights")
rule(M_, 5652, "the 95% t-interval (df 6) of mean `d` excludes 0", "H1.1 rule (b): 95% interval excludes 0")
rule(M_, 5653, "by the mirror rule", "H1.1: the same rule the other way")
ax = AX(0.10, 0.56, 0.135)
for i, e in enumerate(EST):
    ax.plot([i, i], [lo[e], hi[e]], color=C[e], lw=2.2, solid_capstyle="round")
    ax.plot(i, med[e], marker=MK[e], color=C[e], ms=15, ls="none", zorder=4)
    m_, r_ = V1A[e].split(" ", 1)
    label_val(ax, i + 0.09, med[e], f"median {m_} m")
    label_val(ax, i + 0.09, lo[e] + 0.05, f"range {r_.strip('()')}", fontsize=12, color=INK2, va="bottom")
ax.set_xlim(-0.4, 2.85); ax.set_ylim(0, 6.5); ax.set_xticks(range(3)); ax.set_xticklabels([TICK[e] for e in EST])
ax.set_ylabel("Average position error over the cruise (m)"); ax.grid(axis="x", visible=False)
lg = AX(0.70, 0.28, 0.135); lg.axis("off")
legend_est(lg, extra=[Line2D([], [], color=INK2, lw=2.2, label="vertical line: range over\nthe 9 flights")], loc="center left")
foot(fig, meta,
     f"average position error over the straight cruise (after a best-fit alignment), median of {n9.split('/')[0]} flights per estimator, metres "
     "(the vertical lines show the range over the flights).",
     f"EKF3 and the FGO were ranked only if one was lower on at least 6 of 7 further flights AND the 95% confidence interval of "
     "the difference excluded zero (the same rule either way); no ranking rule was registered for the UKF.",
     f"NOT MET: on the further flights EKF3 was lower on {v_neg} and the interval ({v_ci.replace('-', '−')} m) includes zero, so no estimator is "
     "ranked above another.")
finish(fig, meta)

# =================================================================== 1A, blank floor
fig, meta = new_page("02", "1A_blank", "Experiment 1 (1A and 1B): blank floor, nothing for the camera to track",
                     "What each estimator does when the downward camera sees a plain floor and its motion measurements are lost.")
nU = counted("blank-floor flights replayed by the UKF / FGO", f"{len(BLANK['UKF'])}/{len(BLANK['FGO'])}", "11/11", "blank_behaviour.json; Table 4.2 'flights' column")
nE = counted("blank-floor flights, EKF3", len(EK_INV), 14, "blank_behaviour.json EKF3_invalid_period; Table 4.2 'flights' column")
num("blank floor: number of flights shown, UKF / FGO / EKF3", f"{nU.split('/')[0]} / {nU.split('/')[1]} / {nE}", "11 / 11 / 14",
    [("T3", "| UKF | 11 |"), ("T3", "| FGO | 11 |"), ("T3", "| EKF3 | 14 |")])
VB = {}
for e, exp in (("UKF", ("0.7–1.8 (median 1.1)", "15.3–26.8 (median 19.4)", "29–40")), ("FGO", ("0.7–1.8 (median 1.1)", "16.6–27.7 (median 20.4)", "23–41"))):
    ln = 1448 if e == "UKF" else 1455
    VB[(e, 10)] = num(f"{e} error 10 s after flow loss: range (median), m", f"{rng(BLANK[e][:, 0], 1)} (median {rd(np.median(BLANK[e][:, 0]), 1)})",
                      exp[0], [("T3", exp[0])], [(ln, exp[0].split(" ")[0])])
    VB[(e, 30)] = num(f"{e} error 30 s after flow loss: range (median), m", f"{rng(BLANK[e][:, 1], 1)} (median {rd(np.median(BLANK[e][:, 1]), 1)})",
                      exp[1], [("T3", exp[1])], [(ln, exp[1].split(" ")[0])])
    VB[(e, "end")] = num(f"{e} error at the end of the cruise (m, to the nearest 1000 m; numbers.md km × 10^3, digits grouped, as Table 4.2)",
                         grp(rng_si(BLANK[e][:, 3], -3)), grp(si_str(exp[2], 3)), [("T3", grp(si_str(exp[2], 3)) + " †")], [(1462, "29–40 / 23–41")])
disp("time points after flow loss used on this page (s)", "10 / 30", [("T3", "+10 s (m)"), ("T3", "+30 s (m)")])
vinv = num("EKF3: flagged its position invalid for (s of cruise)", rng(EK_INV, 0), "301–310", [("T3", "invalid (for 301–310 s of cruise)")], [(245, "blank from take-off (all 14), for 301–310 s")])
rule(M_, 5551, "**Not accuracy comparisons** (ruling)", "blank floor: ruled not an accuracy comparison (no pass rule)")
med_ = lambda s: s.split("median ")[1].rstrip(")")
table(fig, meta,
      ["estimator", "error 10 s after the camera lost the floor", "error 30 s after", "error at the end of the cruise"],
      [[NAME["EKF3"] + f", {nE} flights", "marks its own position as invalid from take-off for the whole cruise (no error to score)", "", ""],
       [NAME["UKF"] + f", {nU.split('/')[0]} flights", f"{med_(VB[('UKF', 10)])} m (median)", f"{med_(VB[('UKF', 30)])} m (median)", f"{VB[('UKF', 'end')]} m (runaway)"],
       [NAME["FGO"] + f", {nU.split('/')[1]} flights", f"{med_(VB[('FGO', 10)])} m (median)", f"{med_(VB[('FGO', 30)])} m (median)", f"{VB[('FGO', 'end')]} m (runaway)"]],
      [30, 30, 18, 22])
foot(fig, meta,
     "distance between the estimated and the true position after the camera stops giving motion measurements, metres (rounded to "
     "thousands of metres at the end); EKF3 instead reports whether it considers its own position valid.",
     "none registered: a descriptive comparison (this floor tests behaviour when the camera fails, not accuracy).",
     "None of the three kept a usable position: EKF3 declared its position invalid, and the UKF and FGO errors grew without limit "
     "to tens of thousands of metres by the end of the flight.")
finish(fig, meta)

# =================================================================== 1B, heading measurement check
fig, meta = new_page("03", "1B_heading_check", "Experiment 1B: checking the forward camera's heading measurement",
                     "Whether a forward-looking camera can measure the drone's heading (the direction it faces) from the "
                     "corridor's walls, before any estimator uses it.")
vT = num("heading check, line-textured walls: flights passing", VAL["psi/fwdc/all"]["n_pass"], "9/9", [("R1", "textured-wall camera dataset 9/9")], [(330, "`fwdc` 9/9")])
vP = num("heading check, plain walls: flights passing", VAL["psi/fwdplainc/all"]["n_pass"], "6/9", [("R1", "plain-wall camera dataset 6/9 overall")], [(330, "`fwdplainc` 6/9")])
vPC = num("heading check, plain walls over the checkerboard floor: flights passing", VAL["psi/fwdplainc/tex"]["n_pass"], "0/3", [("R1", "checkerboard floor (0/3")])
num("heading check, plain walls over the blank and transition floors: verdict", "PASS" if all(VAL[f"psi/fwdplainc/{f}"]["n_pass"] == "3/3" for f in ("blank", "trans")) else "FAIL",
    "PASS", [("R1", "heading validated on plain walls on blank and transition floors")])
for ph, lab in (("≥ 70%", "availability"), ("≤ 0.5°", "bias"), ("≤ 1.0°", "noise"), ("≤ 5% (\\|error\\| > 3°)", "outlier rate")):
    rule(M_, 2729, ph, f"heading accuracy bar: {lab}")
of = lambda s: s.replace("/", " of ")
table(fig, meta,
      ["camera view", "flights where the heading passed", "result"],
      [["walls with painted lines", of(vT), "PASS on every floor"],
       ["plain walls", of(vP), f"PASS over the blank and the half-and-half (part checkerboard, part blank) floors; NOT MET over the checkerboard floor ({of(vPC)})"]],
      [26, 26, 48])
foot(fig, meta,
     "the camera's heading compared with the simulator's true heading over each flight's cruise; each flight passes or fails.",
     "per flight, a heading must be available for at least 70% of the cruise, with a mean error of at most 0.5°, noise of at most "
     "1.0°, and at most 5% of readings more than 3° wrong.",
     f"PASS with painted-line walls ({of(vT)} flights). With plain walls it passed on {of(vP)} flights: it failed on all flights over "
     "the checkerboard floor.")
finish(fig, meta)

# =================================================================== 1B, offline accuracy with and without the heading
fig, meta = new_page("04", "1B_accuracy", "Experiment 1B: position error with and without the camera heading",
                     "Whether adding the forward camera's heading to the estimators reduces the position error, using the same "
                     "recorded flights with and without it.")
FW = [b for b in CAMB if b[0] == "fwdc"]
nb = counted("painted-line-wall recorded flights (bags), checkerboard floor", len(FW), 3, "phase4_fwdc_evo.json fwdc_tex_r1-r3; Table 4.1 'textured walls, flights 1 / 2 / 3'")
V4 = {}
for e, k, exp, ln in (("EKF3", "EKF3", "3.60–4.09", 269), ("UKF", "UKF_baseline", "1.78–4.96", 271), ("FGO", "FGO_baseline", "2.26–4.54", 270),
                      ("UKF", "UKF_heading", "0.13–0.14", 291), ("FGO", "FGO_heading", "0.06–0.06", 292)):
    vals = [P4[b][k] for b in FW]
    v = num(f"{k}, painted-line walls, range over flights 1–3 (m)", rng(vals, 2), exp,
            [("T2", f"| {e} |"), ("T2", " / ".join(rd(x, 2) for x in vals))], [(ln, " / ".join(rd(x, 2) for x in vals))])
    lo_, hi_ = v.split("–")
    V4[(e, "yes" if "heading" in k else "no")] = lo_ if lo_ == hi_ else v
disp("EKF3 has no offline heading input", "no offline heading arm", [("T2", "no offline heading arm")])
disp("plain walls on the checkerboard floor: heading check result", "0/3", [("R1", "checkerboard floor (0/3")], [(301, "0/3")])
disp("plain walls on the checkerboard floor: no heading benefit claimed", "NO heading benefit is claimed", [("T2", "no heading benefit is claimed")],
     [(301, "NO heading benefit is claimed")])
rule(M_, 7892, "REPORT, no decision rule", "FGO vs UKF with heading: registered to be reported, with no decision rule")
NOBEN = "no benefit claimed (the heading failed its check here)"
table(fig, meta,
      ["estimator", f"painted-line walls: without the heading ({nb} flights)", f"painted-line walls: with the heading ({nb} flights)",
       "plain walls, with the heading"],
      [[NAME["EKF3"], f"{V4[('EKF3', 'no')]} m", "not tested (no input for it)", "not tested"],
       [NAME["UKF"], f"{V4[('UKF', 'no')]} m", f"{V4[('UKF', 'yes')]} m", NOBEN],
       [NAME["FGO"], f"{V4[('FGO', 'no')]} m", f"{V4[('FGO', 'yes')]} m", NOBEN]],
      [28, 24, 24, 24], fs=13)
foot(fig, meta,
     f"average position error over the straight cruise (after a best-fit alignment), lowest–highest over the {nb} recorded "
     "flights with painted-line walls on the checkerboard floor, the same flights processed with and without the heading, metres.",
     "none registered: a descriptive comparison (the UKF-versus-FGO comparison was registered to be reported, with no decision rule).",
     f"With painted-line walls the UKF and FGO errors were {V4[('UKF', 'yes')].split('–')[-1]} m or less with the camera heading, "
     "against metres without it; the two are not ranked. With plain walls on this floor the heading failed its check (see the "
     "previous page), so no benefit is claimed there.")
finish(fig, meta)

# =================================================================== 1C, closed loop without the heading
fig, meta = new_page("05", "1C_no_heading", "Experiment 1C: an estimator flies the drone, without the camera heading",
                     "With each estimator steering the drone and no heading measurement, does the drone drift into the wall at the "
                     "time predicted beforehand?")
CT = {}; EXP_CT = {"EKF3": "+242.1", "UKF": "+165.9", "FGO": "+169.9"}; NMC = {"EKF3": 470, "UKF": 471, "FGO": 473}
WTXT = {"EKF3": ("[+155, +215]", 4948), "UKF": ("[+146, +218]", 7513), "FGO": ("[+145, +196]", 8995)}
VCT = {}
for e in EST:
    js = L(f"closed_loop_{HALF[e][0]}.json"); t = js["contact"]["t_rel_cruise_s"]; CT[e] = t
    inwin = WIN[e][0] <= t <= WIN[e][1] and js["contact"]["wall"] == "west" and t >= 100
    verdict = "PASS" if inwin else "MISS"
    VCT[e] = num(f"{e}: wall contact after cruise start (s) and verdict against its window", f"{rd(t, 1, sign=True)} {verdict}",
                 f"{EXP_CT[e]} {'MISS' if e == 'EKF3' else 'PASS'}", [("T4", f"{EXP_CT[e]} s; window {WTXT[e][0]} s: {'MISS' if e == 'EKF3' else 'PASS'}")],
                 [(NMC[e], EXP_CT[e])]).split(" ")[0]
    rule(M_, WTXT[e][1], f"{WTXT[e][0]} s", f"{e} predicted contact window")
    num(f"{e}: stored pass flag agrees", str(js["a_primary"]["pass"] == (e != "EKF3")), "True", [("T4", "window")])
rule(M_, 4948, "no contact before +100 s", "no wall contact before 100 s after cruise start")
ax = AX(0.25, 0.71, 0.10)
for i, e in enumerate(EST[::-1]):
    w0, w1 = WIN[e]
    ax.add_patch(Rectangle((w0, i - 0.28), w1 - w0, 0.56, color="#e3e3e3", lw=0, zorder=1))
    for w in (w0, w1):
        ax.plot([w, w], [i - 0.28, i + 0.28], color=GREY, ls=(0, (4, 3)), lw=1.6, zorder=2)
    label_val(ax, w0, i - 0.31, f"{w0} s", ha="center", va="top", fontsize=11.5, color="#555555")
    label_val(ax, w1, i - 0.31, f"{w1} s", ha="center", va="top", fontsize=11.5, color="#555555")
    ax.plot(CT[e], i, marker=MK[e], color=C[e], ms=15, ls="none", zorder=4)
    label_val(ax, CT[e], i + 0.33, f"wall at {VCT[e]} s", ha="center", va="bottom", fontsize=13, weight="bold", color=C[e])
ax.axvline(100, color=GREY, ls=(0, (6, 4)), lw=1.6)
label_val(ax, 102, 2.62, "100 s: no contact allowed before this", fontsize=12, color="#555555", va="bottom")
ax.set_xlim(90, 262); ax.set_ylim(-1.15, 2.95); ax.set_yticks(range(3)); ax.set_yticklabels([NAME[e].replace(" (", "\n(") for e in EST[::-1]])
ax.set_xlabel("Time from the start of the cruise until the drone touched the wall (s)"); ax.grid(axis="y", visible=False)
ax.legend(handles=[Patch(color="#e3e3e3", label="window predicted before the flight (grey dashed edges)")], frameon=False, loc="lower right", fontsize=12)
foot(fig, meta,
     "time from the start of the cruise until the drone touched the west wall, seconds; one flight per estimator (the simulator ran "
     "at half real time; the flight speed was unchanged).",
     "PASS if the drone reached the wall inside the window predicted for that estimator (grey) and not before 100 s; here a pass "
     "means the drift was understood, not that the flight succeeded.",
     "Without a heading every estimator drifted into the wall. UKF and FGO PASS (inside their windows); EKF3 NOT MET (it reached "
     "the wall later than its window).")
finish(fig, meta)

# =================================================================== 1C, closed loop with the heading
fig, meta = new_page("06", "1C_with_heading", "Experiment 1C: an estimator flies the drone, with the camera heading",
                     "With each estimator steering the drone and the camera heading added, does every flight complete the corridor "
                     "safely and straight?")
B2h = {e: [L(f"closed_loop_{t}.json")["B"]["B2"]["max_abs_x_cruise_m"] for t in HALF[e][1]] for e in EST}
passh = {e: sum(L(f"closed_loop_{t}.json")["B"]["pass"] and L(f"closed_loop_{t}.json").get("S2", {}).get("pass", True) for t in HALF[e][1]) for e in EST}
VX = {e: num(f"{e}: largest sideways distance over its 3 flights (m)", rd(max(B2h[e]), 2), x, [("T1", f"max cross-track ≤ {x} m")])
      for e, x in zip(EST, ("0.33", "0.25", "0.39"))}
VP = {e: num(f"{e}: flights passing all five checks", f"{passh[e]}/{len(HALF[e][1])}", "3/3", [("T4", "3/3 PASS")], [(477 if e == "EKF3" else 478 if e == "UKF" else 480, "3/3")]) for e in EST}
rule(M_, 4951, "lands with no wall contact", "check 1: complete the mission with no wall contact")
rule(M_, 4953, "**≤ 6.0 m**", "check 2: sideways distance at most 6.0 m")
rule(M_, 4958, "**95th percentile ≤ 1.0°, maximum ≤ 2.0°**", "check 3: heading error 95th percentile ≤ 1.0°, max ≤ 2.0°")
rule(M_, 4963, "**≤ 0.25 m/s**", "check 4: sideways speed at most 0.25 m/s")
rule(M_, 4966, "No oscillation", "check 5: no oscillation")
ax = AX(0.11, 0.55, 0.135)
for i, e in enumerate(EST):
    v = max(B2h[e])
    ax.bar(i, v, width=0.55, color=C[e], zorder=3)
    label_val(ax, i, v + 0.12, f"{VX[e]} m", ha="center", va="bottom", weight="bold")
    label_val(ax, i, 1.35, f"{VP[e].replace('/', ' of ')}\nflights\npassed", ha="center", va="bottom", fontsize=12.5, color=INK2)
ax.set_xlim(-0.5, 2.5); ax.set_ylim(0, 6.8)
bound(ax, 6.0, "limit 6.0 m", x=2.45)
ax.set_xticks(range(3)); ax.set_xticklabels([TICK[e] for e in EST]); ax.grid(axis="x", visible=False)
ax.set_ylabel("Largest sideways distance from the\ncorridor centre line (m)")
lg = AX(0.69, 0.29, 0.135); lg.axis("off")
lg.text(0, 0.95, wrap("The five checks for each flight:", 30), fontsize=13, weight="bold", va="top")
T("• finish the corridor without touching a wall"); T("• stay within 6.0 m of the centre line")
T("• heading error within 1.0° (95% of the time), 2.0° at most"); T("• sideways speed at most 0.25 m/s"); T("• no oscillation")
lg.text(0, 0.80, "\n".join(["• finish the corridor without\n    touching a wall", "• stay within 6.0 m of the\n    centre line",
                            "• heading error within 1.0°\n    (95% of the time), 2.0° at most", "• sideways speed at most\n    0.25 m/s",
                            "• no oscillation"]), fontsize=12.5, va="top", linespacing=1.35)
foot(fig, meta,
     "pass or fail of five checks in each flight, 3 flights per estimator (each estimator flew its own flights); the bars show the "
     "largest sideways distance from the centre line in any of them, metres (simulator at half real time, flight speed unchanged).",
     "each flight must pass all five checks listed on the right, and the estimator must report a valid position throughout.",
     "All three PASS: every flight (3 of 3 for each estimator) passed all five checks; the estimators are not ranked against each other.")
finish(fig, meta)

# =================================================================== 2, known tags
fig, meta = new_page("07", "2_known_tags", "Experiment 2: occasional position fixes from tags at known places",
                     "How well each estimator tracks the drone in a room when printed tags at known places give occasional position "
                     "fixes, as the number of tags is reduced.")
TL = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
for c in TCOND:
    disp(f"condition {c}: number of tags", TL[c], [("T8", TL[c])])
VT = {}
EXP_T = {"A": "0.039 0.037 0.020", "B": "0.055 0.061 0.026", "C": "0.074 0.076 0.054", "D": "0.096 0.131 0.083"}
NMT = {"A": 526, "B": 527, "C": 528, "D": 529}
for c in TCOND:
    mr = agg["conditions"][c]["mean_rmse_m"]
    s = num(f"{TL[c]}: live error EKF3 UKF FGO, mean of 3 flights (m)", " ".join(rd(mr[f"{e} live"], 3) for e in EST), EXP_T[c],
            [("IDX", EXP_T[c])], [(NMT[c], f"{x} m") for x in EXP_T[c].split()])
    for e, x in zip(EST, s.split()):
        VT[(c, e)] = x
disp("flights per condition", "3 / 3 / 3 / 3", [("IDX", "3 / 3 / 3 / 3")])
num("primary hypothesis (FGO hindsight gain grows as tags get fewer): verdict", "PASS" if agg["H-T1 (FGO live -> whole-flight batch)"]["PASS"] else "FAIL", "PASS", [("R1", "PASS: median gain")])
num("live errors similar: verdict", "PASS" if agg["P-T3 live ratio max/min"]["PASS"] else "FAIL", "FAIL", [("R1", "FAIL: live max/min 1.97 / 2.36")])
inside = [c for c in TCOND if agg["P-T3 live ratio max/min"]["by_condition"][c] <= 1.5]
num("conditions inside 1.5×", "/".join(TL[c] for c in inside), "2 tags", [("T1", "C inside the band")])
rule(M_, 10179, "is ≤ 1.5 × the smallest", "live errors similar: largest ≤ 1.5 × smallest, every condition")
rule(M_, 10171, "the FGO's hindsight gain grows with the gap", "primary: the FGO's hindsight gain grows with the gap between fixes")
ax = AX(0.09, 0.60, 0.10)
wd = 0.26
for j, c in enumerate(TCOND):
    for k, e in enumerate(EST):
        x = j + (k - 1) * wd; v = agg["conditions"][c]["mean_rmse_m"][f"{e} live"]
        ax.bar(x, v, width=wd * 0.92, color=C[e], zorder=3)
        label_val(ax, x, v + 0.002, VT[(c, e)], ha="center", va="bottom", fontsize=11.5)
ax.set_xticks(range(4)); ax.set_xticklabels([TL[c] for c in TCOND]); ax.set_ylim(0, 0.145); ax.grid(axis="x", visible=False)
ax.set_xlabel("Tags placed in the room (fewer tags = longer gaps between fixes)"); ax.set_ylabel("Average horizontal position error (m)")
lg = AX(0.71, 0.28, 0.10); lg.axis("off")
legend_est(lg, loc="center left")
foot(fig, meta,
     "average horizontal position error of each estimator's live estimate (root-mean-square over five laps), mean of 3 flights per "
     "tag count, metres.",
     "primary: the FGO's gain from re-solving the whole flight afterwards (hindsight) grows as tags get fewer; also predicted: live "
     "errors similar, the largest at most 1.5 × the smallest for every tag count.",
     "Primary PASS. 'Live errors similar' NOT MET (only the 2-tag case was within 1.5 ×), so the live errors are not ranked.")
finish(fig, meta)

# =================================================================== 3, loop closure
fig, meta = new_page("08", "3_loop_closure", "Experiment 3: recognising tags seen before (loop closure)",
                     "Whether the FGO (factor-graph optimiser) keeps its error small by recognising tags at unknown places when it "
                     "passes them again on later laps.")
EXP_L = {("nolc", "live"): "0.263–0.361", ("lc", "live"): "0.049–0.076", ("nolc", "hindsight"): "0.221–0.266", ("lc", "hindsight"): "0.017–0.027"}
NML = {"lc": 573, "nolc": 574}
VL = {k: num(f"{'with' if k[0] == 'lc' else 'without'} loop closure, {k[1]}: error range over 3 flights (m)", rng([t["rmse_m"] for t in LL[k]], 3), x,
             [("R1", x), ("IDX", x)], [(NML[k[0]], x)]) for k, x in EXP_L.items()}
r51 = lambda m: [t["per_lap_rmse_m"][-1] / t["per_lap_rmse_m"][0] for t in LL[(m, "live")]]
v_lc = num("live, with loop closure: lap 5 ÷ lap 1 range", rng(r51("lc"), 2), "0.16–0.43", [("IDX", "0.16–0.43")], [(573, "0.16–0.43")])
v_nolc = num("live, without loop closure: lap 5 ÷ lap 1 range", rng(r51("nolc"), 1), "2.9–4.5", [("IDX", "2.9–4.5")], [(574, "2.9–4.5")])
p = [sum(r <= 1.5 for r in r51("lc")), sum(a["rmse_m"] < b["rmse_m"] for a, b in zip(LL[("lc", "live")], LL[("nolc", "live")])),
     sum(a["rmse_m"] < b["rmse_m"] for a, b in zip(LL[("lc", "hindsight")], LL[("nolc", "hindsight")])), sum(r > 1.5 for r in r51("nolc"))]
num("the four rules: flights passing, of 3", " ".join(f"{x}/3" for x in p), "3/3 3/3 3/3 3/3", [("IDX", "3/3 3/3 3/3 3/3")], [(577, "PASS 3/3")])
rule(M_, 10501, "the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3", "with loop closure: lap 5 ≤ 1.5 × lap 1 in 3 of 3")
rule(M_, 10503, "LC live overall RMSE < no-LC live overall RMSE in 3/3 flights", "live lower with loop closure, 3 of 3")
rule(M_, 10504, "LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights", "hindsight lower with loop closure, 3 of 3")
rule(M_, 10505, "lap 5 > 1.5 × lap 1 in 3/3 flights", "without loop closure: lap 5 > 1.5 × lap 1 in 3 of 3")
ax = AX(0.09, 0.60, 0.06)
ax.set_xlim(-0.6, 1.6); ax.set_ylim(0, 0.42)
for j, m in enumerate(("nolc", "lc")):
    for k, kind in enumerate(("live", "hindsight")):
        vals = [t["rmse_m"] for t in LL[(m, kind)]]; x = j + (k - 0.5) * 0.46
        top_ = rbox(ax, x, vals, C["FGO"], kind == "live")
        label_val(ax, x, top_ + 0.006, VL[(m, kind)] + " m", ha="center", va="bottom", fontsize=12.5)
ax.set_xticks([0, 1]); ax.set_xticklabels(["without loop closure", "with loop closure"])
ax.grid(axis="x", visible=False); ax.set_ylabel("Average horizontal position error (m)")
lg = AX(0.71, 0.28, 0.06); lg.axis("off")
lg.legend(handles=[Patch(facecolor=C["FGO"], edgecolor=C["FGO"], lw=2, label="FGO live estimate\n(during the flight)"),
                   Patch(facecolor="white", edgecolor=C["FGO"], lw=2, label="FGO hindsight\n(whole flight re-solved\nafter landing)")],
          frameon=False, loc="center left", labelspacing=1.4, title="box = lowest to highest\nof the 3 flights", title_fontsize=12)
foot(fig, meta,
     "average horizontal position error over five laps (root-mean-square), lowest–highest over 3 flights, metres; the same flights "
     "re-solved with and without loop closure. Only the FGO can do this, so there is no comparison between estimators.",
     "in 3 of 3 flights: with loop closure the lap-5 error is at most 1.5 × the lap-1 error, and both the live and the hindsight "
     "errors are lower than without it; without it the lap-5 error exceeds 1.5 × lap 1.",
     f"All four PASS in 3 of 3 flights: with loop closure the error is lower and does not grow (lap 5 ÷ lap 1 = {v_lc}); without "
     f"it, it grows {v_nolc} times over five laps.")
finish(fig, meta)

# =================================================================== 4, outdoor-indoor
fig, meta = new_page("09", "4_outdoor_indoor", "Experiment 4: flying from outdoors (with GPS) to indoors (without)",
                     "How far each estimator drifts during about two minutes indoors after GPS is lost, and whether re-solving "
                     "the flight afterwards helps.")
EXP_O = {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89", "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}
NMO = {"EKF3 live": 552, "UKF live": 553, "FGO live": 554, "RTS-UKF (hindsight)": 555, "FGO hindsight (whole-flight batch)": 556}
VO = {}
for n in TRK:
    VO[n] = num(f"{n}: indoor error range over 3 flights (m)", rng(OI[n], 2), EXP_O[n], [("T6", f"| {EXP_O[n]} |")],
                [(NMO[n], EXP_O[n] if n != "FGO hindsight (whole-flight batch)" else "0.59 m")])
VO["FGO hindsight (whole-flight batch)"] = VO["FGO hindsight (whole-flight batch)"].split("–")[0] if len(set(VO["FGO hindsight (whole-flight batch)"].split("–"))) == 1 else VO["FGO hindsight (whole-flight batch)"]
num("FGO whole-flight batch printed as a single value (all 3 flights round to it)", VO["FGO hindsight (whole-flight batch)"], "0.59", [("T1", "batch 0.59")])
h41 = sum(OI[TRK[4]][i] < OI["EKF3 live"][i] and OI[TRK[4]][i] < OI["UKF live"][i] for i in range(3))
num("primary: FGO hindsight below EKF3 and UKF live, flights of 3", f"{h41}/3", "3/3", [("R1", "PASS 3/3: FGO whole-flight batch 0.59 m")], [(558, "PASS 3/3")])
r42 = [max(OI[f"{e} live"][i] for e in EST) / min(OI[f"{e} live"][i] for e in EST) for i in range(3)]
num("live errors similar (≤ 1.5× every flight): verdict", "PASS" if max(r42) <= 1.5 else "FAIL", "FAIL", [("T1", "H4.2 FAILS")], [(559, "H-O2 FAIL")])
r43 = [max(OI[TRK[3]][i], OI[TRK[4]][i]) / min(OI[TRK[3]][i], OI[TRK[4]][i]) for i in range(3)]
num("two hindsight errors within 1.5× (every flight): verdict", "PASS" if max(r43) <= 1.5 else "FAIL", "PASS", [("T1", "H4.3 PASS")], [(560, "P-O3 PASS")])
rule(M_, 10358, "PASS iff in 3/3", "primary rule: in 3 of 3 flights")
rule(M_, 10359, "flights the FGO-batch indoor RMSE is < both EKF3's and the UKF's live indoor RMSE", "primary rule: FGO hindsight below both filters' live errors")
rule(M_, 10361, "indoor RMSE of EKF3, UKF and FGO is ≤ 1.5 × the smallest", "live similar: largest ≤ 1.5 × smallest")
rule(M_, 10362, "within 1.5× of each other in every", "hindsight pair within 1.5×")
ax = AX(0.09, 0.60, 0.11)
ax.set_xlim(-0.5, 4.5); ax.set_ylim(0, 1.75)
XO = [("EKF3 live", "EKF3", True), ("UKF live", "UKF", True), ("FGO live", "FGO", True), ("RTS-UKF (hindsight)", "UKF", False),
      ("FGO hindsight (whole-flight batch)", "FGO", False)]
for i, (n, e, live) in enumerate(XO):
    top_ = rbox(ax, i, OI[n], C[e], live, w=0.5)
    label_val(ax, i, top_ + 0.03, VO[n] + " m", ha="center", va="bottom", fontsize=12.5)
ax.set_xticks(range(5)); ax.set_xticklabels(["EKF3\nlive", "UKF\nlive", "FGO\nlive", "UKF\nhindsight\n(smoothed)", "FGO\nhindsight\n(whole flight)"])
ax.grid(axis="x", visible=False); ax.set_ylabel("Horizontal position error indoors (m)")
lg = AX(0.71, 0.28, 0.11); lg.axis("off")
lg.legend(handles=[Patch(facecolor=C[e], label=NAME[e].replace(" (", "\n(")) for e in EST] +
                  [Patch(facecolor=INK2, label="filled: live estimate\n(during the flight)"),
                   Patch(facecolor="white", edgecolor=INK2, lw=2, label="open: hindsight (flight\nre-solved after landing)")],
          frameon=False, loc="center left", labelspacing=0.9, title="box = lowest to highest\nof the 3 flights", title_fontsize=12)
foot(fig, meta,
     "horizontal position error indoors without GPS (root-mean-square), lowest–highest over 3 flights, metres.",
     "primary: the FGO's hindsight error must be below both filters' live errors in 3 of 3 flights; also predicted: the three live "
     "errors within 1.5 × of each other, and the two hindsight errors within 1.5 × of each other.",
     "Primary PASS: the FGO hindsight error was lower than the EKF3 and UKF live errors in 3 of 3 flights. Hindsight errors similar: "
     "PASS. Live errors similar: NOT MET (the live errors are not ranked).")
finish(fig, meta)

# =================================================================== 5, hold accuracy
fig, meta = new_page("10", "5_hold", "Experiment 5: holding the drone still next to a wall tag",
                     "Whether each estimator, flying the drone, can hold it in place next to a printed tag on the wall that a "
                     "camera sees.")
_hc = [v for k, v in L("expH/h_comparative_2026-10-11.json")["sets"].items() if k.startswith("re-flown")][0]
hE = [np.mean([w["mean_m"] for w in HJ(t)["hold_windows_vehicle"]]) for t in S1F]          # m (stored in m)
hU = [r["hold_mean_mm"] for r in _hc["UKF"]]; hF = [r["hold_mean_mm"] for r in _hc["FGO"]]
HV = {"EKF3": hE, "UKF": hU, "FGO": hF}; HK = {"EKF3": 3, "UKF": 0, "FGO": 0}      # HK: decimal shift to mm (EKF3 stored in m)
HVM = {e: [float(rd_si(v, 12, HK[e])) for v in HV[e]] for e in EST}                  # millimetres, for drawing only
VH = {e: num(f"{e}: mean hold error, range over 3 flights (mm)", rng_si(HV[e], 1, HK[e]), x,
             [("T1", f"hold {x} mm")], [(675, x)])
      for e, x in zip(EST, ("7.8–7.9", "6.4–7.1", "8.3–8.6"))}
HWIN = {"EKF3 (first hold flights, near spawn)": S1, "EKF3 (far spawn, plotted)": S1F, "UKF": S2V, "FGO": S3V}
for nm_, trs in HWIN.items():
    ws = [w for t in trs for w in HJ(t)["hold_windows_vehicle"]]
    ok_ = all(w["mean_m"] <= 0.05 and w["max_m"] <= 0.15 for w in ws)
    num(f"hold rule (every window mean ≤ 0.05 m and max ≤ 0.15 m), {nm_}", str(ok_), "True",
        [("T1", "hold 7.8–7.9 mm" if "far" in nm_ else "hold 6.4–7.1 mm" if nm_ == "UKF" else "hold 8.3–8.6 mm" if nm_ == "FGO" else "hold 7.8–7.9 mm")])
num("window max hold error range, EKF3 first hold flights / UKF (mm)",
    f"{rng_si([w['max_m'] for t in S1 for w in HJ(t)['hold_windows_vehicle']], 0, 3)} / {rng_si([w['max_m'] for t in S2V for w in HJ(t)['hold_windows_vehicle']], 0, 3)}",
    "16–25 / 17–21", [("R1", "max 16–25 mm (EKF3 flying)")], [(606, "16–25 mm"), (644, "6.1–7.4 / 17–21")])
disp("hold accuracy verdict as recorded: EKF3 first hold flights / FGO", "PASS / PASS", [("R1", "PASS: hold error mean 8 mm"), ("R1", "also PASS on the FGO-flying hold set")],
     [(606, "H-H1 PASS"), (646, "H-H1 PASS")])
num("comparative predictions (FGO tightest and the other three): verdict", "; ".join(_hc["criteria"][k].split()[0] for k in ("H-H2", "P-H3", "H-H4 (15 s)", "H-H4 (5 s)")),
    "FAIL; FAIL; FAIL; FAIL", [("T1", "comparatives FAIL")], [(675, "**FAIL** (0/3)")])
rule(M_, 10687, "mean hold error ≤ 0.05 m and max ≤ 0.15 m", "hold accuracy: mean ≤ 0.05 m and max ≤ 0.15 m")
rule(M_, 10687, "every pre-loss hold window, 3/3", "hold accuracy: in 3 of 3 flights")
counted("flights per estimator", "/".join(str(len(HV[e])) for e in EST), "3/3/3", "S1 far r1-r3b, S2v2 r1-r3, S3v2 r1-r3 (Table 7.1 [i] '3 flights per estimator')")
HLIM = disp("hold limits, mean / largest (mm) = the registered '≤ 0.05 m' / '≤ 0.15 m' (METHODOLOGY.md:10687) × 10^3, exact", si_str("0.05 / 0.15", 3), [])
ax = AX(0.11, 0.80, 0.135)
for i, e in enumerate(EST):
    v = HVM[e]
    ax.bar(i, max(v), width=0.55, color=C[e], zorder=3)
    label_val(ax, i, max(v) + 1.0, f"{VH[e]} mm", ha="center", va="bottom", weight="bold")
ax.set_xlim(-0.5, 2.5); ax.set_ylim(0, 58)
bound(ax, 50, f"limit for the mean: {HLIM.split(' / ')[0]} mm", x=2.45)
ax.set_xticks(range(3)); ax.set_xticklabels([TICK[e] for e in EST]); ax.grid(axis="x", visible=False)
ax.set_ylabel("Mean hold error per flight (mm)")
foot(fig, meta,
     "distance between where the drone was held and where it should be, mean per flight, lowest–highest over 3 flights per "
     "estimator (each estimator flew its own flights), millimetres; each bar shows the highest flight.",
     f"mean hold error at most {HLIM.split(' / ')[0]} mm and largest at most {HLIM.split(' / ')[1]} mm in every hold, in 3 of 3 flights.",
     "All three held far inside both limits in every hold. The registered test passed on EKF3's first hold flights and on the "
     "FGO's; the UKF's flights have no recorded verdict but are inside. The four predicted differences between the estimators, "
     "such as the FGO holding tightest: NOT MET.")
finish(fig, meta)

# =================================================================== 5, drift while the tag is hidden
fig, meta = new_page("11", "5_tag_loss", "Experiment 5: drift while the wall tag is hidden",
                     "How far the drone drifts while the tag is hidden for a few seconds, and whether each estimator picks the tag "
                     "up again.")
DR = {(e, li): drifts(FLY[e][0], FLY[e][1])[li] for e in EST for li in range(4)}
worst = {e: max(max(DR[(e, li)]) for li in range(4)) for e in EST}
wli = {e: max(range(4), key=lambda li: max(DR[(e, li)])) for e in EST}
worstm = {e: max(lo[FLY[e][1]]["effective"]["drift_m"] for t in FLY[e][0] for lo in HJ(t)["losses"]) for e in EST}   # m, as stored
VW = {e: num(f"{e}: worst drift over all tag losses (mm)", rd_si(worstm[e], 0, 3), x, [("T5", f"{x} / {BAND[e][wli[e]]}")])
      for e, x in zip(EST, ("31", "26", "27"))}
LK = {e: [bool(lo[FLY[e][1]]["lockout"]) for t in FLY[e][0] for lo in HJ(t)["losses"]] for e in EST}
VN = {e: num(f"{e}: losses with a lockout / losses", f"{sum(LK[e])} / {len(LK[e])}", x, [("T5", x)]) for e, x in zip(EST, ("0 / 24", "0 / 12", "0 / 12"))}
inband = all(v <= BAND[e][li] for (e, li), d in DR.items() for v in d)
num("every drift inside its limit", str(inband), "True", [("T5", "every loss inside its band")], [(629, "P-H5 PASS")])
disp("tightest and loosest limit for EKF3 and the FGO (mm)", "50 / 200", [("T5", "EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm")])
disp("the UKF's limits are twice the others'", "UKF ≤ 100 / 200 / 400 / 300 mm", [("T5", "UKF ≤ 100 / 200 / 400 / 300 mm")])
rule(M_, 10690, "≤ 0.05 / 0.10 / 0.20 m", "drift limits, EKF3 and FGO hover losses")
rule(M_, 10691, "≤ 2× those", "UKF limits twice those")
rule(M_, 10700, "no estimator locks out the returning tag in any loss", "no lockout")
_e1 = [lo["EKF3"]["effective"]["drift_m"] for t in S1 for lo in HJ(t)["losses"]]
_u2 = [lo["UKF_port"]["effective"]["drift_m"] for t in S2V for lo in HJ(t)["losses"]]
_f3 = [lo["FGO_flying"]["effective"]["drift_m"] for t in S3V for lo in HJ(t)["losses"]]
_nu = sum(u > e for u, e in zip(_u2, _e1)); _nf = sum(f > e for f, e in zip(_f3, _e1))
num("directional prediction: matched losses with UKF / FGO drift strictly above flying EKF3 (effective, full precision); holds",
    f"{_nu} of {len(_e1)} / {_nf} of {len(_e1)}; {_nu == len(_e1) and _nf == len(_e1)}", "4 of 12 / 9 of 12; False",
    [("R1", "the final UKF port drifted more in 4 of 12 and the final FGO node in 9 of 12")])
disp("directional prediction verdict", "NOT MET", [("R1", "NOT borne out (the predicted o")])
ax = AX(0.11, 0.80, 0.135)
for i, e in enumerate(EST):
    wmm = float(rd_si(worstm[e], 12, 3))                                              # mm, exact shift, for drawing only
    ax.bar(i, wmm, width=0.55, color=C[e], zorder=3)
    label_val(ax, i, wmm + 1.0, f"{VW[e]} mm", ha="center", va="bottom", weight="bold")
    nl = VN[e].split(" / ")[1]
    label_val(ax, i, 3, f"{nl}\ntag losses", ha="center", va="bottom", fontsize=12, color="white", weight="bold")
ax.set_xlim(-0.5, 2.5); ax.set_ylim(0, 60)
bound(ax, 50, "tightest limit: 50 mm", x=2.45)
ax.set_xticks(range(3)); ax.set_xticklabels([TICK[e] for e in EST]); ax.grid(axis="x", visible=False)
ax.set_ylabel("Worst drift while the tag was hidden (mm)")
foot(fig, meta,
     "how far the drone moved between the last tag sighting before a loss and the first one after it, worst case over all tag losses (hidden for a few seconds "
     "to half a minute, hovering or moving), millimetres.",
     "every loss must stay inside its own limit (50 to 200 mm for EKF3 and the FGO, depending on the loss; twice that for the UKF), "
     "and no estimator may refuse the tag when it returns.",
     f"All three PASS: every tag loss stayed inside its limit and the tag was always picked up again ({VN['EKF3'].split(' / ')[0]} "
     "refusals). The predicted extra drift of the UKF and FGO over EKF3: NOT MET.")
finish(fig, meta)

# =================================================================== 5S, safety tests
fig, meta = new_page("12", "5S_safety", "Experiment 5S: safety tests (the estimator fails in flight)",
                     "When the flying estimator fails mid-flight, does the drone notice, switch to a safe landing and come down "
                     "gently?")
SF = {"ua": "safety_ukf_a_v3", "ub": "safety_ukf_b_v3", "fa": "safety_fgo_a_v4", "fb": "safety_fgo_b_v4"}
J = {k: HJ(f) for k, f in SF.items()}
BND = {"ua": 0.1, "ub": 5.5, "fa": 0.75, "fb": 0.75}
rule(M_, 11298, "FGO: within **0.75 s** of the kill", "FGO: position lost declared within 0.75 s")
rule(M_, 11299, "UKF (a): within **0.1 s** of TFAIL", "UKF forced failure: within 0.1 s")
rule(M_, 11300, "UKF (b): within **5.5 s** of the kill", "UKF inputs cut: within 5.5 s")
rule(M_, 11295, "≤ **3°**", "attitude: roll/pitch within 3°"); rule(M_, 11295, "≤ **5°**", "attitude: yaw within 5°")
rule(M_, 11304, "≤ **1.5 m**", "safe landing: drift to touchdown at most 1.5 m")
DT = {}
for k, exp, sh in (("ua", "0.00", ("IDX", "0.00 ≤ 0.1: True")), ("ub", "5.69", ("T7", "5.69 s, bound 5.50 s")), ("fa", "0.60", ("IDX", "0.60 s / 1.45 m")), ("fb", "0.62", ("IDX", "0.62 s / 0.21 m"))):
    DT[k] = num(f"{SF[k]}: time to declare 'position lost' (s)", rd(J[k]["S-A2"]["text_delay_s"], 2), exp, [sh], [(490, exp)] if k != "ua" else [(490, "trigger 0.00 s")])
BT = {k: disp(f"{SF[k]}: limit as displayed (s)", x, [sh]) for k, x, sh in
      (("ua", "0.10", ("IDX", "0.00 ≤ 0.1")), ("ub", "5.50", ("T7", "bound 5.50 s")), ("fa", "0.75", ("IDX", "FGO: within **0.75 s**")), ("fb", "0.75", ("IDX", "FGO: within **0.75 s**")))}
PF = lambda b: "PASS" if b else "FAIL"
VS = {}
for k, exp in (("ua", "PASS PASS PASS"), ("ub", "PASS FAIL PASS"), ("fa", "PASS PASS PASS"), ("fb", "PASS PASS PASS")):
    VS[k] = num(f"{SF[k]}: attitude / position lost / safe landing", " ".join(PF(J[k][c]["PASS"]) for c in ("S-A1", "S-A2", "S-A3")), exp,
                [("T7", "final UKF port, re-test (FINAL): ALL PASS" if k == "ua" else "final UKF port, re-test (FINAL): position lost FAIL as worded (5.69 s" if k == "ub"
                  else "corrected-priors node, re-test (FINAL): ALL PASS")]).split()
for k in ("ub",):
    num(f"{SF[k]}: single landing (input-cut runs only)", PF(J[k]["S-A4_single_landing"]["PASS"]), "PASS", [("T7", "position lost FAIL as worded (5.69 s, bound 5.50 s)")])
num("FGO second test (watcher watching): single landing", PF(J["fb"]["S-A4_single_landing"]["PASS"]), "PASS", [("T7", "corrected-priors node, re-test (FINAL): ALL PASS, 0.21 m")])
rule(M_, 11307, "S-A4 (b runs only)", "single landing checked for the second kind of test only")
cell = lambda k, i: VS[k][i]
table(fig, meta,
      ["what was done in flight", "attitude correct", "'position lost' declared in time", "landed safely", "overall"],
      [["UKF (unscented Kalman filter): forced to report its output invalid", cell("ua", 0), f"{cell('ua', 1)} ({DT['ua']}\u00a0s; limit {BT['ua']}\u00a0s)", cell("ua", 2), "PASS"],
       ["UKF: all its position inputs cut off", cell("ub", 0), f"{cell('ub', 1)} ({DT['ub']}\u00a0s; limit {BT['ub']}\u00a0s)", cell("ub", 2), "FAIL (as worded)"],
       ["FGO (factor-graph optimiser): program stopped", cell("fa", 0), f"{cell('fa', 1)} ({DT['fa']}\u00a0s; limit {BT['fa']}\u00a0s)", cell("fa", 2), "PASS"],
       ["FGO: program stopped, safety monitor watching it", cell("fb", 0), f"{cell('fb', 1)} ({DT['fb']}\u00a0s; limit {BT['fb']}\u00a0s)", cell("fb", 2), "PASS"]],
      [38, 12, 26, 12, 12], fs=12.5)
foot(fig, meta,
     "pass or fail of each safety check in the final run of each test (one flight per test); the time from the failure until the "
     "drone reported 'position lost' and began to land, seconds.",
     "attitude within 3° (roll and pitch) and 5° (heading); 'position lost' declared within the limit shown; landing within 1.5 m of "
     "where the failure happened, with no safety breach (and a single landing when two landing triggers exist).",
     "The FGO passed both tests. The UKF passed the forced-invalid test but failed the inputs-cut test as worded: it declared "
     f"'position lost' after {DT['ub']} s against a {BT['ub']} s limit. EKF3 (ArduPilot's standard filter) has no such failure path, "
     "so it was not tested.")
finish(fig, meta)

# =================================================================== how to read + contents, PDF and index
PAGE = "00"; TXT = []
fig0 = plt.figure(figsize=(PAGE_W, PAGE_H))
fig0.text(0.045, 0.945, "How to read these pages", fontsize=21, weight="bold", va="top")
HL = 0.0295                                             # line height at 13.5 pt (figure fraction)
y = [0.875]


def para(s, x=0.045, w=104, fs=13, gap=0.01, **kw):
    t = wrap(s, w); fig0.text(x, y[0], t, fontsize=fs, va="top", linespacing=1.3, **kw)
    y[0] -= HL * (t.count("\n") + 1) * fs / 13.5 + gap


para("This thesis compares three ways of estimating where a drone is, indoors and without GPS, in a computer simulation "
     "(the simulator knows the true position, so every error can be measured). Each page shows one experiment: what it tests, "
     "one chart or one small table, and three lines underneath.", gap=0.02)
para("The three estimators (the same colour and shape on every page)", fs=15, weight="bold", gap=0.01)
DESC = {"EKF3": "ArduPilot's standard extended Kalman filter: the baseline that comes with the autopilot.",
        "UKF": "an unscented Kalman filter written for this thesis, using the same sensors.",
        "FGO": "a factor-graph optimiser: it re-solves a short window of recent measurements together, and can re-solve a whole flight."}
for e in EST:
    fig0.text(0.06, y[0] + 0.004, {"EKF3": "●", "UKF": "▲", "FGO": "■"}[e], color=C[e], fontsize=18, va="top")
    fig0.text(0.09, y[0], f"{e}:", color=C[e], fontsize=13.5, weight="bold", va="top")
    para(DESC[e], x=0.155, w=92, gap=0.006)
y[0] -= 0.012
para("Marks, boxes and lines", fs=15, weight="bold", gap=0.01)
for s_ in ("Filled mark or box = live: the estimate available during the flight. Open (white) = hindsight: the whole flight "
           "re-solved after landing.",
           "A box spans the lowest to the highest value over the flights; a single value is printed when they round to the same number.",
           "Grey dashed line or grey band = a pass limit written down before the flights were flown.",
           "The cruise is the long straight part of each flight; the checkerboard floor is the textured floor the downward camera tracks."):
    para("•  " + s_, x=0.06, w=102, gap=0.006)
y[0] -= 0.012
para("The three lines under each chart", fs=15, weight="bold", gap=0.01)
for s_ in ("Metric: what was measured, and its unit.   Pass rule: the rule fixed before the flights, in one sentence.",
           "Result: PASS = the rule was met. NOT MET = the rule was tested and not met. FAIL (as worded) = the rule, read exactly "
           "as it was written, was not met.",
           "'None registered' = no pass rule was set, so the numbers are only shown. Words such as 'lower' are used only where a "
           "rule fixed in advance was met."):
    para("•  " + s_, x=0.06, w=102, gap=0.006)
print("how-to bottom", round(y[0], 3)); assert y[0] > 0.0, "how-to page overflows"
fig0.savefig(os.path.join(OUT, "summary_00_how_to_read.png"), dpi=150)

figc = plt.figure(figsize=(PAGE_W, PAGE_H))
figc.text(0.045, 0.945, "Experiment summary pages: contents", fontsize=21, weight="bold", va="top")
figc.text(0.045, 0.88, "One page per experiment, in experiment order. The detailed thesis tables are unchanged and separate.",
          fontsize=14, va="top", color=INK2)
rows_c = [("", "How to read these pages")] + [(str(i + 1), p["title"]) for i, p in enumerate(PAGES)]
for i, (n, t) in enumerate(rows_c):
    figc.text(0.07, 0.80 - i * 0.052, n, fontsize=14, va="top", ha="right", color=INK2)
    figc.text(0.09, 0.80 - i * 0.052, t, fontsize=14, va="top")
    figc.text(0.95, 0.80 - i * 0.052, f"page {i + 2}", fontsize=13, va="top", ha="right", color=INK2)
with PdfPages(PDF) as pdf:
    for f in [figc, fig0] + [p["fig"] for p in PAGES]:
        pdf.savefig(f)
plt.close("all")

ok = all(c["ok"] for c in CHK)
nn = sum(c["kind"] == "number" for c in CHK); nr = sum(c["kind"] == "rule" for c in CHK); nc = sum(c["kind"] == "count" for c in CHK)
nd = sum(c["kind"] == "display" for c in CHK)
good = lambda k: sum(c["ok"] for c in CHK if c["kind"] == k)
md = ["# Experiment summary pages: index and provenance", "",
      f"*Generated by `eval/figs_thesis_summary.py` at commit `{COMMIT}`. Stored results only: nothing re-run or recomputed from raw data. "
      "The detailed thesis tables and figures (`docs/thesis/tables/`, `docs/thesis/figures_thesis/`) are unchanged. This file holds ALL "
      "provenance; the pages carry none.*", "",
      f"**Cross-checks: {good('number')}/{nn} data-derived numbers EXACT, {good('display')}/{nd} display-only strings found, "
      f"{good('rule')}/{nr} rule lines found, {good('count')}/{nc} counts.** "
      "A display-only check is a label, a fixed verdict word or a unit conversion of a bound that is not computed from a stored "
      "value; it only has to occur in the thesis display file (and the cited numbers.md line). "
      "A number check is EXACT when (1) the stored full-precision value rounded once by `rd()` (parsed from `eval/figs_thesis.py`, "
      f"source SHA-256 `{RD_SHA}`, the same as in `index_results.md`) equals the expected string typed from the thesis display, character "
      "for character; (2) the expected string (or the cited fragment) occurs in that display file; and (3) where a numbers.md line is "
      "cited, the fragment occurs in that line (the blank-floor rows cite the Errata lines E4–E6, 1448/1455/1462, which override the "
      "frozen rows). A rule check reads the cited METHODOLOGY (or table) line at build time and requires the quoted phrase. A number "
      "guard then scans every page's text and stops the build if any number on a page is not covered by one of that page's checks.", "",
      "**Combined PDF:** `summary_plots.pdf` = contents page, 'How to read these pages', then the pages below in experiment order. "
      "Palette fixed per estimator (Okabe–Ito): EKF3 #0072B2, UKF #009E73, FGO #D55E00, references/limits grey #999999; filled = live, "
      "open = hindsight; no log axes; one chart or one table per page; fonts ≥ 11 pt.", "",
      "**Terms on the pages, mapped to the thesis vocabulary:** standard sensors = the standard-sensor dataset (`dsn`); painted-line walls = "
      "the textured-wall camera dataset (`fwdc`); plain walls = the plain-wall camera dataset (`fwdplainc`); checkerboard floor = the textured "
      "floor; half-and-half floor = the transition floor; 'average position error over the cruise' = cruise ATE (`evo -a (cruise)`); "
      "'re-solved after landing' = hindsight (FGO whole-flight batch, smoothed UKF); 'an estimator flies the drone' = closed loop; "
      "'half real time' = RTF 0.5 (the simulator ran at half real time; the commanded speed was unchanged at 0.5 m/s).", ""]
HYP = {"01": "H1.1 (confirmatory EKF3 − FGO test, flights 4–10; Table 7.1 [a]); UKF medians descriptive (Table 7.1 [b])",
       "02": "no hypothesis: blank floor ruled 'Not accuracy comparisons' (M:5551); Table 4.2, Table 7.1 [d]. Pools 1A and 1B blank flights as Table 4.2 does",
       "03": "H1.2 heading-measurement validation (3 parts in Table 7.3); yaw-rate validation not shown",
       "04": "C1.a (registered comparison without a decision rule, Table 7.1 [c]); EKF3 has no offline heading arm (by ruling). Values are the 3 "
             "textured-wall bags only (Table 4.1). The 3 plain-wall bags on the checkerboard floor are NOT given numbers: the heading failed "
             "validation there (H1.2, 0/3) and no heading benefit is claimed (numbers.md:301, restatement ruling 4; the Table 7.5 note omits them "
             "for the same reason). Table 7.1's 6-bag ranges (0.13–0.25 / 0.06–0.22 m) are therefore not used on this page",
       "05": "H1.8 contact prediction at half real-time (RTF 0.5): EKF3 NOT MET (D21), final UKF port PASS, final FGO node PASS (Table 4.3, Table 7.3). "
             "EKF3 at real time (+186.2 s, PASS) not shown",
       "06": "H1.9 the five closed-loop criteria B1–B5 + estimator validity S2 (Table 4.3, Table 7.1 [j]); builds: EKF3, final UKF port, final FGO node "
             "(original priors). Heading-error p95/max and lateral-speed values (Table 4.3) are not printed",
       "07": "H2.1 primary PASS, H2.3 FAIL as worded (Figure 5.1, Table 7.3); H2.2 and H2.4 (both FAIL) not shown",
       "08": "H3.1–H3.4 PASS 3/3 (Figure 5.2, Table 7.3); V3 (not re-scorable) not shown",
       "09": "H4.1 primary PASS 3/3, H4.2 FAIL as worded, H4.3 PASS (Table 5.1, Table 7.3); EKF3's 4.10 m return jump (Table 7.2) not shown",
       "10": "H5.1 (recorded PASS for EKF3 flying, S1 near spawn, mean 8 mm, max 16–25 mm, numbers.md:606; and for the final FGO node, "
             "numbers.md:646; the UKF set has no recorded verdict, its windows are inside both bounds: max 17–21 mm, numbers.md:644; the rule "
             "is re-checked here on every stored hold window of S1, S1 far, S2v2 and S3v2). Values = Table 7.1: EKF3 = the EKF3-flying hold set at the FAR spawn (S1 far, the "
             "comparatives' EKF3 side), UKF/FGO = run means of the comparative table (numbers.md:675); the per-window UKF range 6.1–7.4 mm "
             "(numbers.md:644) is not used. Comparatives H5.2, H5.3, H5.4a, H5.4b FAIL as worded",
       "11": "H5.5 drift bands PASS, H5.7 no lockout PASS, H5.5 S2/S3 directional prediction NOT MET (Table 6.1, Table 7.3). EKF3 = near + far spawn "
             "(6 flights, 24 losses) as Table 6.1; drift = the EFFECTIVE metric (last fix → first returning fix). H5.6 (re-lock time) not shown",
       "12": "5S safety criteria S-A1–S-A4, final run of each test (Table 7.2, Table A.2): UKF (a) `H_safety_ukf_a_v3`, UKF (b) `H_safety_ukf_b_v3` "
             "(final UKF port re-tests), FGO (a)/(b) `H_safety_fgo_a_v4`/`_b_v4` (the corrected-priors node: a DIFFERENT build from the final FGO node "
             "flown in Experiments 1C and 5). The UKF (a) score file records a 0.75 s bound; the page shows the registered 0.1 s (as Table A.2). "
             "Landing drifts (0.58 / 1.07 / 1.45 / 0.21 m) not printed; earlier runs not shown"}
for p in PAGES:
    md += [f"## Page {p['id']}: {p['title']}", "", f"- **File:** `{p['file']}`", f"- **What this tests:** {p['what']}",
           f"- **Metric:** {p['metric']}", f"- **Pass rule:** {p['rule']}", f"- **Result:** {p['result']}",
           f"- **Thesis labels and notes:** {HYP[p['id']]}", "",
           "| kind | check | computed | expected | where it is shown / cited | match |", "|---|---|---|---|---|---|"]
    for c in CHK:
        if c["page"] == p["id"]:
            md.append(f"| {c['kind']} | {c['label']} | `{c['computed']}` | `{c['expected']}` | {c['where'].replace('|', '¦')} | {'yes' if c['ok'] else '**NO**'} |")
    md.append("")
md += ["## Left out, and why", "",
       "- **Experiment 1A, transition floor:** no current thesis table or figure displays a transition-floor value (only the "
       "experiment matrix names it), so there is no displayed number to cross-check; not computed from the result files.",
       "- **Experiment 1B sub-studies H1.3–H1.7 (heading-fusion prediction, robust weighting, hindsight heading correction, large initial "
       "heading error and its redesigns, the robust-weighting replication):** each needs its own jargon and has mixed verdicts; they are "
       "in Table 7.3 and are left out of this reader summary.",
       "- **Dataset-quality bands, the yaw-rate validation, the H5.6 re-lock time, V3, X1.b, compute cost and the build ablations:** "
       "not essential to the pass/fail story; in Tables 7.3, A.1–A.3.", ""]
open(INDEX, "w").write("\n".join(md))
print(f"checks: data-derived numbers {good('number')}/{nn}, display-only {good('display')}/{nd}, rules {good('rule')}/{nr}, counts {good('count')}/{nc}; wrote {PDF}, {INDEX}")
sys.exit(0 if ok else 1)
