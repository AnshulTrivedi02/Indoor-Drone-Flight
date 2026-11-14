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
import matplotlib.ticker
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
    # RESTYLE (2026-11-02): repointed to the byte-identical pre-restyle copy - this is a separate reader document and
    # must not change; DNAME (below) is left as "figures_thesis/index.md" so the printed source name is unchanged.
    "IDX": "figures_thesis/working/index.md"}.items()}
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
        "FGO": ("cl_fgo_a_tex_r1_half_rp", [f"cl_fgo_b_tex_r{i}_half_rp" for i in (1, 2, 3)])}
agg = L("expT/t_aggregate.json"); TCOND = "ABCD"
TRK = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
OFL = ("O_r1", "O_r2", "O_r3b")
OI = {n: [L(f"expO/{t}.json")["tracks"][n]["indoor_rmse_m"] for t in OFL] for n in TRK}
LL = {(m, k): [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{m} {k}"] for r in (1, 2, 3)] for m in ("lc", "nolc") for k in ("live", "hindsight")}
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = ["s2v2_r1", "s2v2_r2", "s2v2_r3"]; S3V = ["s3v2_r1", "s3v2_r2", "s3v2_r3"]  # superseded, original priors - kept for Table A.2 historical reference only, not used below
S3RP = ["s3rp_r1", "s3rp_r2", "s3rp_r3"]  # corrected priors - matches Table 6.1 (T5) and figs_thesis.py
FLY = {"EKF3": (S1 + S1F, "EKF3"), "UKF": (S2V, "UKF_port"), "FGO": (S3RP, "FGO_flying")}
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
    assert TOP - h > meta["top"] + 0.03, f"{meta['id']}: table does not fit (h {h:.3f}, top {meta['top']:.3f}, lines {nl})"
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
CT = {}; EXP_CT = {"EKF3": "+242.1", "UKF": "+165.9", "FGO": "+166.7"}; NMC = {"EKF3": 470, "UKF": 471}
# FGO's current flight 1 (the corrected-priors re-fly, `cl_fgo_a_tex_r1_half_rp`, matching Table 4.3) is not itself a line
# of the frozen numbers.md (it is recorded in the writing pack's refly_priors/numbers_refly.md instead), so FGO is checked
# against Table 4.3 only, not NMC - unlike EKF3/UKF, whose single-flight figures are unchanged and still on those lines.
T4WORD = {"EKF3": "after window", "UKF": "PASS", "FGO": "PASS"}
WTXT = {"EKF3": ("[+155, +215]", 4948), "UKF": ("[+146, +218]", 7513), "FGO": ("[+145, +196]", 8995)}
VCT = {}
for e in EST:
    js = L(f"closed_loop_{HALF[e][0]}.json"); t = js["contact"]["t_rel_cruise_s"]; CT[e] = t
    inwin = WIN[e][0] <= t <= WIN[e][1] and js["contact"]["wall"] == "west" and t >= 100
    verdict = "PASS" if inwin else "MISS"
    VCT[e] = num(f"{e}: wall contact after cruise start (s) and verdict against its window", f"{rd(t, 1, sign=True)} {verdict}",
                 f"{EXP_CT[e]} {'MISS' if e == 'EKF3' else 'PASS'}", [("T4", f"{EXP_CT[e]} s ({T4WORD[e]})")],
                 [(NMC[e], EXP_CT[e])] if e in NMC else []).split(" ")[0]
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
      for e, x in zip(EST, ("0.33", "0.25", "0.32"))}
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
# Claims C1-C3 applied (user ruling 2026-10-24): the extension results are quoted from Table 7.1's footnote [k] (checked there exactly).
x_tags = disp("extension E2: loop closure also bounded with 4 and with 2 tags (H-E2.1 PASS 3/3 in each)", "with 4 tags and with 2 tags",
              [("T1", "with 4 tags and with 2 tags (E2), loop closure also bounded live drift")])
x_ids = disp("extension E3: wrong tag IDs in 1% of the eligible detections (H-E3.1 FAIL 0/9)", "1%",
             [("T1", "wrong IDs in 1% of the eligible detections (E3), the FGO as built lost its loop-closure advantage")])
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
     "re-solved with and without loop closure. Only the FGO has loop closure in the thesis (its EKF3 and UKF have no landmark states).",
     "in 3 of 3 flights: with loop closure the lap-5 error is at most 1.5 × the lap-1 error, and both the live and the hindsight "
     "errors are lower than without it; without it the lap-5 error exceeds 1.5 × lap 1.",
     f"All four PASS in 3 of 3 flights: with loop closure the error is lower and does not grow (lap 5 ÷ lap 1 = {v_lc}); without "
     f"it, it grows {v_nolc} times over five laps. Extension tests: also bounded {x_tags}, and for a UKF with the tags in its state; "
     f"with wrong IDs in {x_ids} of eligible detections the FGO lost this advantage.")
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
num("live errors similar (≤ 1.5× every flight): verdict", "PASS" if max(r42) <= 1.5 else "FAIL", "FAIL", [("T1", "H4.2 NOT MET")], [(559, "H-O2 FAIL")])
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
# corrected priors (expH/h_comparative_refly_priors.json), not the original-priors "re-flown" set in
# h_comparative_2026-10-11.json this used before - matches figs_thesis.py's own switch (see its line ~578).
_hc = L("expH/h_comparative_refly_priors.json")["new"]["sets"]["re-flown (S2v2 jitter-corrected UKF, S3rp corrected-prior FGO)"]
hE = [np.mean([w["mean_m"] for w in HJ(t)["hold_windows_vehicle"]]) for t in S1F]          # m (stored in m)
hU = [r["hold_mean_mm"] for r in _hc["UKF"]]; hF = [r["hold_mean_mm"] for r in _hc["FGO"]]
HV = {"EKF3": hE, "UKF": hU, "FGO": hF}; HK = {"EKF3": 3, "UKF": 0, "FGO": 0}      # HK: decimal shift to mm (EKF3 stored in m)
HVM = {e: [float(rd_si(v, 12, HK[e])) for v in HV[e]] for e in EST}                  # millimetres, for drawing only
# FGO's current value (7.3-8.3 mm, corrected priors) is not itself on numbers.md:675 - that frozen line keeps the
# original-priors figure (8.3-8.6 mm) as its own historical record, so FGO is checked against Table 7.1 (T1) only.
NMH = {"EKF3": 675, "UKF": 675}
VH = {e: num(f"{e}: mean hold error, range over 3 flights (mm)", rng_si(HV[e], 1, HK[e]), x,
             [("T1", f"hold {x} mm")], [(NMH[e], x)] if e in NMH else [])
      for e, x in zip(EST, ("7.8–7.9", "6.4–7.1", "7.3–8.3"))}
HWIN = {"EKF3 (first hold flights, near spawn)": S1, "EKF3 (far spawn, plotted)": S1F, "UKF": S2V, "FGO": S3RP}
for nm_, trs in HWIN.items():
    ws = [w for t in trs for w in HJ(t)["hold_windows_vehicle"]]
    ok_ = all(w["mean_m"] <= 0.05 and w["max_m"] <= 0.15 for w in ws)
    num(f"hold rule (every window mean ≤ 0.05 m and max ≤ 0.15 m), {nm_}", str(ok_), "True",
        [("T1", "hold 7.8–7.9 mm" if "far" in nm_ else "hold 6.4–7.1 mm" if nm_ == "UKF" else "hold 7.3–8.3 mm" if nm_ == "FGO" else "hold 7.8–7.9 mm")])
num("window max hold error range, EKF3 first hold flights / UKF (mm)",
    f"{rng_si([w['max_m'] for t in S1 for w in HJ(t)['hold_windows_vehicle']], 0, 3)} / {rng_si([w['max_m'] for t in S2V for w in HJ(t)['hold_windows_vehicle']], 0, 3)}",
    "16–25 / 17–21", [("R1", "max 16–25 mm (EKF3 flying)")], [(606, "16–25 mm"), (644, "6.1–7.4 / 17–21")])
disp("hold accuracy verdict as recorded: EKF3 first hold flights / FGO", "PASS / PASS", [("R1", "PASS: hold error mean 8 mm"), ("R1", "PASS: hold error mean 7.1–8.7 mm")],
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
      for e, x in zip(EST, ("31", "26", "28"))}
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
_f3 = [lo["FGO_flying"]["effective"]["drift_m"] for t in S3RP for lo in HJ(t)["losses"]]
_nu = sum(u > e for u, e in zip(_u2, _e1)); _nf = sum(f > e for f, e in zip(_f3, _e1))
num("directional prediction: matched losses with UKF / FGO drift strictly above flying EKF3 (effective, full precision); holds",
    f"{_nu} of {len(_e1)} / {_nf} of {len(_e1)}; {_nu == len(_e1) and _nf == len(_e1)}", "4 of 12 / 6 of 12; False",
    [("R1", "the final UKF port drifted more in 4 of 12 and the corrected-priors FGO node in 6 of 12")])
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

# =================================================================== EXTENSION EXPERIMENTS (pre-registered) + the exploratory ablation
# Added 2026-10-25 (user request, verbatim: "yes add the extension section, include the ablation page"). Appended after page 12 so
# every earlier page is drawn exactly as before. Sources: the STORED tier-1 score and verdict files (docs/thesis/tier1/scores/*.json),
# the stored Experiment 3 results (eval/results/expL/), the ablation's stored derived values (docs/thesis/ablation/ablation_results.json)
# and the ruled discussion paragraph (docs/thesis/discussion_material.md §1). Nothing is re-run. Every printed number is rounded once
# by rd() from the stored value and must equal, as a string, the value typed from the tier-1 / ablation result file it is shown in.
T1D = os.path.join(ROOT, "docs", "thesis", "tier1"); ABD = os.path.join(ROOT, "docs", "thesis", "ablation")
LT = lambda f: json.load(open(os.path.join(T1D, "scores", f)))
PRT = "docs/thesis/tier1/preregistration.md"; PRA = "docs/thesis/ablation/preregistration.md"
for k_, p_, n_ in (("E2", "tier1/e2_results.md", "E2 results (tier1/e2_results.md)"), ("E3", "tier1/e3_results.md", "E3 results (tier1/e3_results.md)"),
                   ("E4", "tier1/e4_results.md", "E4 results (tier1/e4_results.md)"), ("E5", "tier1/e5_results.md", "E5 results (tier1/e5_results.md)"),
                   ("PR", "tier1/preregistration.md", "tier-1 pre-registration (tier1/preregistration.md)"),
                   ("AB", "ablation/ablation_numbers.md", "ablation numbers (ablation/ablation_numbers.md, EXPLORATORY)"),
                   ("APR", "ablation/preregistration.md", "ablation pre-registration (ablation/preregistration.md)"),
                   ("DM", "discussion_material.md", "discussion material (discussion_material.md)")):
    DISP[k_] = os.path.join(ROOT, "docs", "thesis", p_); DNAME[k_] = n_


def rfind(path, phrase):
    """The one line of `path` that contains `phrase` (asserted unique), for a rule() check."""
    ls = [i + 1 for i, ln in enumerate(open(os.path.join(ROOT, path)).read().split("\n")) if phrase in ln]
    assert len(ls) == 1, f"{path}: '{phrase}' found on lines {ls}, expected exactly one"
    return ls[0]


def rulef(path, phrase, label):
    return rule(path, rfind(path, phrase), phrase, label)


def ids(*pairs):
    """Registered ids printed on a page (their digits must be covered): each id checked on its defining pre-registration line."""
    for path, phrase in pairs:
        rulef(path, phrase, f"registered id '{phrase}' defined in {os.path.basename(path)}")


def fl(t):
    return t.replace("T_A_", "8 tags, ").replace("T_B_", "4 tags, ").replace("T_C_", "2 tags, ").replace("T_D_", "1 tag, ").replace("r", "flight ")


TAGS = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
FLT = [f"T_{c}_r{i}" for c in TCOND for i in (1, 2, 3)]
EXT_FIRST = len(PAGES)                     # PAGES[EXT_FIRST:] are the extension pages (the contents page groups them)

# ------------------------------------------------------------------- E2, fewer tags
fig, meta = new_page("13", "E2_fewer_tags", "Extension E2: loop closure with fewer tags",
                     "Whether the FGO (factor-graph optimiser) still keeps its error small by recognising tags it has seen before "
                     "when the room has fewer tags (8, 4, 2 or 1), each at an unknown place.")
E2V = LT("E2_verdicts.json")
LAP5 = {("A", k): [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"lc {k}"]["per_lap_rmse_m"][4] for r in (1, 2, 3)] for k in ("live", "hindsight")}
for c in "BCD":
    for k in ("live", "hindsight"):
        LAP5[(c, k)] = [LT(f"E2_T_{c}_r{r}.json")["tracks"][f"lc {k}"]["per_lap_rmse_m"][4] for r in (1, 2, 3)]
for c in TCOND:
    disp(f"condition {c}: number of tags", TAGS[c], [("T8", TAGS[c])])
EXP2 = {"A": "0.0317", "B": "0.0238", "C": "0.0492", "D": "0.0687"}
V2 = {}
for c in TCOND:
    st = E2V["P-E2.5"]["means"][c]
    num(f"{TAGS[c]}: the mean's inputs are the plotted lap-5 live values (stored)", str([v["value"] for v in st["values"]] == LAP5[(c, "live")]), "True",
        [("E2", "per_lap_rmse_m[4]")])
    V2[c] = num(f"{TAGS[c]}: mean over 3 flights of the live lap-5 error, with loop closure (m)", rd(float(np.mean(LAP5[(c, 'live')])), 4), EXP2[c],
                [("E2", f"{c} = {EXP2[c]}")])
    num(f"{TAGS[c]}: the mean equals the stored P-E2.5 mean", rd(st["mean_m"], 4), EXP2[c], [("E2", "P-E2.5.means")])
CR2 = E2V["criteria"]
CNT2 = {}
for h in ("H-E2.1", "H-E2.2", "H-E2.3", "P-E2.4"):
    n_ = sum(sum(CR2[h][c]["per_flight"].values()) for c in "BCD"); vv = {CR2[h][c]["verdict"] for c in "BCD"}
    CNT2[h] = num(f"{h}: flights passing over B, C and D, and the verdict in every condition", f"{n_} of 9 {'/'.join(sorted(vv))}", "9 of 9 PASS",
                  [("E2", f"| {'**H-E2.1 (PRIMARY)**' if h == 'H-E2.1' else h}"), ("E2", "**PASS** 3/3 | **PASS** 3/3 | **PASS** 3/3")]).split(" PASS")[0]
num("H-E2.1 per condition (B, C, D)", " ".join(CR2["H-E2.1"][c]["count"] for c in "BCD"), "3/3 3/3 3/3", [("E2", "PASS in B, C and D (9/9)")])
v25 = num("P-E2.5 verdict and its three ordering steps", f"{E2V['P-E2.5']['verdict']} {E2V['P-E2.5']['steps']['A<=B']} {E2V['P-E2.5']['steps']['B<=C']} {E2V['P-E2.5']['steps']['C<=D']}",
          "FAIL False True True", [("E2", "**P-E2.5 (graded, one check): FAIL.**"), ("E2", "A ≤ B False, B ≤ C True, C ≤ D True")]).split()[0]
ids((PRT, "| **H-E2.1 (PRIMARY)** |"), (PRT, "| H-E2.2 |"), (PRT, "| H-E2.3 |"), (PRT, "| P-E2.4 |"), (PRT, "| P-E2.5 (graded) |"))
rulef(PRT, "| LC live lap-5 RMSE ≤ 1.5 × lap-1 RMSE | ≤ 1.5, 3/3 flights |", "H-E2.1 rule: lap 5 ≤ 1.5 × lap 1 in 3 of 3 flights per tag count")
rulef(PRT, "PASS iff all three steps are non-decreasing", "P-E2.5 rule: the mean lap-5 live error does not decrease as tags get fewer")
disp("condition D: one tag, the start (origin) tag, so it is the known-map case", "known-map, one-tag", [("E2", "the **known-map, one-tag** case")])
counted("flights per tag count", "/".join(str(len(LAP5[(c, 'live')])) for c in TCOND), "3/3/3/3", "expL T_A_r1-r3 (8 tags, stored Experiment 3) + E2_T_<c>_r1-r3")
ax = AX(0.09, 0.60, 0.125)
ax.set_xlim(-0.6, 3.6); ax.set_ylim(0, 0.085)
for j, c in enumerate(TCOND):
    for k, kind in enumerate(("live", "hindsight")):
        x = j + (k - 0.5) * 0.36
        top_ = rbox(ax, x, LAP5[(c, kind)], C["FGO"], kind == "live", w=0.3)
    mx = j - 0.18; m_ = float(np.mean(LAP5[(c, "live")]))
    ax.plot([mx - 0.2, mx + 0.2], [m_, m_], color=INK, lw=2.0, zorder=5)
    label_val(ax, mx, max(LAP5[(c, "live")]) + 0.0025, f"mean\n{V2[c]} m", ha="center", va="bottom", fontsize=12, linespacing=1.1)
ax.set_xticks(range(4)); ax.set_xticklabels([T(TAGS[c]) + ("\n(Experiment 3)" if c == "A" else "") for c in TCOND])
ax.grid(axis="x", visible=False); ax.set_xlabel("Tags in the room, each at an unknown place"); ax.set_ylabel("Error on the fifth lap (m)")
lg = AX(0.71, 0.28, 0.125); lg.axis("off")
lg.legend(handles=[Patch(facecolor=C["FGO"], edgecolor=C["FGO"], lw=2, label="FGO live estimate,\nwith loop closure"),
                   Patch(facecolor="white", edgecolor=C["FGO"], lw=2, label="FGO hindsight (whole\nflight re-solved after\nlanding), with loop closure"),
                   Line2D([], [], color=INK, lw=2.0, label="black line: mean of the\nlive values (P-E2.5)")],
          frameon=False, loc="center left", labelspacing=1.3, title="box = lowest to highest\nof the 3 flights", title_fontsize=12)
foot(fig, meta,
     "error on the fifth lap (root-mean-square, horizontal) of the FGO with loop closure, lowest–highest over 3 flights per tag count, "
     "metres, in the frame of the start tag; the 8-tag flights are the stored Experiment 3 flights.",
     "primary H-E2.1: with 4, 2 and 1 tags, the lap-5 live error is at most 1.5 × the lap-1 error in 3 of 3 flights; H-E2.2, H-E2.3 "
     "and P-E2.4 as in Experiment 3; P-E2.5: the mean lap-5 live error does not decrease as tags get fewer.",
     f"H-E2.1 PASS ({CNT2['H-E2.1']} flights); H-E2.2, H-E2.3 and P-E2.4 PASS ({CNT2['H-E2.2']} each). P-E2.5 {v25}: the mean fell from "
     f"8 tags ({V2['A']} m) to 4 tags ({V2['B']} m) before rising. With 1 tag the only tag is the start tag, so that case is the "
     "known-map, one-tag case.")
finish(fig, meta)

# ------------------------------------------------------------------- E3, wrong tag ids: outcome per run
fig, meta = new_page("14", "E3_wrong_ids", "Extension E3: wrong tag IDs (outcome of every run)",
                     "What happens to the FGO's loop closure when a few tag sightings carry the wrong tag ID, as built (plain) and with "
                     "a robust weighting of the tag measurements.")
E3V = LT("E3_verdicts.json"); RUNS3 = E3V["runs"]
ST3 = {nm_: r["run_status"]["status"] for nm_, r in RUNS3.items()}
GR3 = [("a", "0.01"), ("b", "0.01"), ("a", "0.05"), ("b", "0.05"), ("b", "0")]
def runs3(arm, rate):
    return sorted(n for n, r in RUNS3.items() if r["arm"] == arm and r["rate"] == rate)
LIVE3 = {n: RUNS3[n]["values"]["lc live rmse_m"]["value"] for n in RUNS3}
DIV3 = {n: bool(RUNS3[n]["run_status"]["diverged"]) for n in RUNS3}
assert all(DIV3[n] == (ST3[n] != "OK") for n in RUNS3), "E3: status and divergence disagree"  # a diverged run's RMSE may be finite (pre-divergence segment); it is never plotted
print("E3 statuses", sorted(set(ST3.values())))
num("arm (a) 1%: runs diverged (status FAILED-ESTIMATOR)", f"{sum(DIV3[n] for n in runs3('a', '0.01'))} of {len(runs3('a', '0.01'))}", "6 of 9",
    [("E3", "1%: 6 of 9 runs diverged")])
num("arm (a) 5%: runs diverged", f"{sum(DIV3[n] for n in runs3('a', '0.05'))} of {len(runs3('a', '0.05'))}", "0 of 9", [("E3", "at 5%: 0 of 9 runs diverged")])
num("arm (b), every rate: runs diverged", f"{sum(DIV3[n] for a, r in GR3 if a == 'b' for n in runs3(a, r))} of {sum(len(runs3(a, r)) for a, r in GR3 if a == 'b')}",
    "0 of 21", [("E3", "**Arm (b) (robust): 0 of 21 runs diverged.**")])
# 'collapsed' (DESCRIPTIVE): exactly the runs e3_results.md groups as collapsed -- every non-diverged arm (a) run (§3) and the one
# robust run it names (§4, T_A_r2 5% s1). No per-run flag is stored, so no threshold is invented (decision D49).
COLL3 = {n for n in RUNS3 if RUNS3[n]["arm"] == "a" and not DIV3[n]} | {"E3b_T_A_r2_0.05_s1"}
disp("collapsed (DESCRIPTIVE), arm (a): every non-diverged run, as grouped in E3 results §3", "All 12 non-diverged runs finish with LC live 3.7161–4.2231 m",
     [("E3", "All 12 non-diverged runs finish with LC live 3.7161–4.2231 m"), ("E3", "the non-robust solution's landmark map collapses")])
disp("collapsed (DESCRIPTIVE), arm (b): the one robust run E3 results §4 names", "One robust run collapsed",
     [("E3", "**One robust run collapsed.** The exception is T_A_r2 5% s1")])
counted("arm (a) runs counted as collapsed (non-diverged)", sum(1 for n in COLL3 if RUNS3[n]["arm"] == "a"), 12, "E3 results §3 'All 12 non-diverged runs'")
G3 = {}
EXP3 = {("a", "0.01"): "3.7161–3.8960", ("a", "0.05"): "4.0395–4.2231", ("b", "0.01"): "0.0496–1.4769", ("b", "0.05"): "0.9776–4.1849", ("b", "0"): "0.0484–0.0760"}
for a, r in GR3:
    fin = [LIVE3[n] for n in runs3(a, r) if not DIV3[n]]
    G3[(a, r)] = dict(div=sum(DIV3[n] for n in runs3(a, r)), coll=sum(n in COLL3 for n in runs3(a, r)), n=len(runs3(a, r)),
                      rng=num(f"arm ({a}) rate {r}: final live error of the finite runs, lowest–highest (m)", rng(fin, 4), EXP3[(a, r)],
                              [("E3", x) for x in EXP3[(a, r)].split("–")]))
REF3 = [E3V["references"][f"T_A_r{i}"]["nolc live rmse_m"]["value"] for i in (1, 2, 3)]
vref = num("stored error without loop closure, the 3 flights, lowest–highest (m)", rng(REF3, 4), "0.2625–0.3608", [("E3", "| 0.2625 | 0.2451 |"), ("E3", "| 0.3608 | 0.2657 |")])
disp("the room of E3: all 8 tags (condition A)", "8 tags", [("T8", "8 tags")])
CA, CB = E3V["criteria_a"], E3V["criteria_b"]
kk = lambda d, p: next(k for k in d if k.startswith(p))
h31 = CA[kk(CA, "H-E3.1")]
VH31 = num("H-E3.1 verdict and count", f"{h31['verdict']} {h31['count']}", "FAIL 0/9", [("E3", "| **H-E3.1 (PRIMARY)** 1%: LC live < the same flight's stored no-LC live | **FAIL** | 0/9")])
b1a, b1b, b2 = CB[kk(CB, "P-E3b.1 0.01")], CB[kk(CB, "P-E3b.1 0.05")], CB[kk(CB, "P-E3b.2")]
VB31 = num("P-E3b.1 at 1% and 5%: verdicts and counts", f"{b1a['verdict']} {b1a['count']} {b1b['verdict']} {b1b['count']}", "PASS 9/9 PASS 9/9",
           [("E3", "| P-E3b.1 1%: robust LC live ≤ 1.10 × arm (a), per run (+10%: judgement, not derived from data) | **PASS** | 9/9"),
            ("E3", "| P-E3b.1 5% (same band) | **PASS** | 9/9")])
VB32 = num("P-E3b.2 verdict and count", f"{b2['verdict']} {b2['count']}", "PASS 3/3", [("E3", "| **PASS** | 3/3 | 0 of 1 per flight")])
num("P-E3b.1 at 1%: runs SATISFIED, flagged (matched arm (a) run diverged)", len(b1a["satisfied, flagged"]), 6, [("E3", "**6 runs are SATISFIED, flagged**")])
ids((PRT, "| **H-E3.1 (PRIMARY)** |"), (PRT, "| P-E3b.1 (\"no worse\", amendment 4) |"), (PRT, "| P-E3b.2 |"))
rulef(PRT, "at 1%: LC live overall < the same flight's stored no-LC live overall | 9/9 runs", "H-E3.1 rule: at 1% wrong IDs, below the stored error without loop closure, 9 of 9 runs")
rulef(PRT, "robust LC live overall ≤ **1.10 ×** arm (a) LC live overall of the same flight, rate and seed", "P-E3b.1 rule: robust ≤ 1.10 × as built, per run")
disp("wrong-ID rates (per cent of the eligible detections)", "1% / 5%", [("E3", "(T_A, 1% / 5%, seeds 0–2)")])
counted("runs per rate and arm (3 flights × 3 seeds); robust controls at rate 0", "/".join(str(G3[g]["n"]) for g in GR3), "9/9/9/9/3", "E3_verdicts.json runs")
ax = AX(0.09, 0.62, 0.145)
YD = 4.98
ax.set_xlim(-0.6, 4.6); ax.set_ylim(0, 5.62)
ax.axhspan(min(REF3), max(REF3), color="#dddddd", lw=0, zorder=1)
T(f"grey band: stored error\nwithout loop closure,\n{vref} m")
ax.annotate(f"grey band: stored error\nwithout loop closure,\n{vref} m", xy=(2.0, max(REF3) + 0.02), xytext=(2.0, 1.0), ha="center", va="bottom",
            fontsize=11.5, color="#555555", arrowprops=dict(arrowstyle="->", color="#777777", lw=1.2))
ax.axhspan(4.7, 5.62, color="#f4f4f4", lw=0, zorder=0); ax.axhline(4.7, color=GREY, lw=0.8)
label_val(ax, 4.55, 5.56, "diverged (the estimator failed: no finite error)", fontsize=11.5, color="#555555", va="top", ha="right")
for j, (a, r) in enumerate(GR3):
    ns = runs3(a, r); fins = [n for n in ns if not DIV3[n]]; divs = [n for n in ns if DIV3[n]]
    xs = np.linspace(j - 0.22, j + 0.22, len(ns))
    for x_, n in zip(xs, ns):
        if DIV3[n]:
            ax.plot(x_, YD, marker="x", color=C["FGO"], ms=11, mew=2.4, ls="none", zorder=4)
        else:
            ax.plot(x_, LIVE3[n], marker="s" if a == "a" else "D", color=C["FGO"], ms=9 if a == "a" else 8, ls="none", zorder=4,
                    mec="white" if n in COLL3 else C["FGO"], mew=0.8)
    g = G3[(a, r)]
    lab = f"{g['rng']} m"
    label_val(ax, j, 2.75, lab.replace("–", "–\n"), ha="center", va="bottom", fontsize=11.5, linespacing=1.05)
    T(f"{g['div']} of {g['n']} diverged"); T(f"{g['coll']} of {g['n']} collapsed*")
XT3 = ["1% wrong IDs\nFGO as built", "1% wrong IDs\nrobust FGO", "5% wrong IDs\nFGO as built", "5% wrong IDs\nrobust FGO", "no wrong IDs\nrobust FGO"]
ax.set_xticks(range(5)); ax.set_xticklabels([T(s_) + f"\n{G3[g]['div']} diverged\n{G3[g]['coll']} collapsed*" for s_, g in zip(XT3, GR3)], fontsize=11)
ax.set_yticks([0, 1, 2, 3, 4]); ax.grid(axis="x", visible=False)
ax.set_ylabel("Live position error over five laps (m)")
lg = AX(0.73, 0.26, 0.03); lg.axis("off")
lg.legend(handles=[Line2D([], [], ls="none", marker="s", color=C["FGO"], ms=10, label="FGO as built (plain)"),
                   Line2D([], [], ls="none", marker="D", color=C["FGO"], ms=9, label="robust FGO (robust\nweighting of tags)"),
                   Line2D([], [], ls="none", marker="x", color=C["FGO"], ms=11, mew=2.4, label="diverged run")],
          frameon=False, loc="upper left", labelspacing=0.6, title="one mark per run", title_fontsize=12, borderaxespad=0.0)
lg.text(0.0, -0.02, wrap("Numbers: lowest–highest error of the finished runs.", 33) + "\n" +
        wrap("* collapsed (DESCRIPTIVE, not a registered measure): the run finished with a wrong tag map. Plain runs: "
             "map shrunk, consistent with a least-squares compromise. Robust run: map folded (a wrong basin).", 33), fontsize=11, va="bottom", color=INK2, linespacing=1.2, transform=lg.transAxes)
foot(fig, meta,
     "live horizontal position error of the FGO with loop closure over five laps (root-mean-square), metres, start-tag frame, 8-tag "
     "room; one mark per run (3 flights × 3 seeds; control: 3 flights).",
     "primary H-E3.1: at 1% wrong IDs, the error is below the same flight's stored error without loop closure (grey band) in 9 of 9 "
     "runs (a diverged run counts as not met); P-E3b.1: the robust FGO is at most 1.10 × the plain FGO in the same run.",
     f"H-E3.1 {VH31.replace('0/9', '(0 of 9)')}: 6 of 9 plain runs diverged and the other 3 ended far above the grey band. The robust FGO "
     f"never diverged: P-E3b.1 {VB31.split()[0]} (9 of 9 at 1% and at 5%), P-E3b.2 {VB32.split()[0]} (3 of 3, no wrong IDs). All registered "
     "E3 verdicts are listed on their own page.")
finish(fig, meta)

# ------------------------------------------------------------------- E3, every registered verdict
fig, meta = new_page("15", "E3_verdicts", "Extension E3: wrong tag IDs (every registered verdict)",
                     "The registered tests of Extension E3, each with its count over the runs (3 flights × 3 seeds at each wrong-ID rate).")
T("3 flights × 3 seeds")
ROWS3 = [("H-E3.1 (primary)", "1%: live error below the stored no-loop-closure error", CA, "H-E3.1", "| **H-E3.1 (PRIMARY)** |", "FAIL", "0/9"),
         ("H-E3.2", "1%: the same for the hindsight error", CA, "H-E3.2", "| H-E3.2 |", "FAIL", "0/9"),
         ("H-E3.3", "1%: lap-5 live error at most 1.5 × lap 1", CA, "H-E3.3", "| H-E3.3 |", "FAIL", "3/9"),
         ("P-E3.4", "1%: live error at most 2 × the clean live error", CA, "P-E3.4", "| P-E3.4 |", "FAIL", "0/9"),
         ("P-E3.5a", "5%: as H-E3.1", CA, "P-E3.5a", "| P-E3.5 |", "FAIL", "0/9"),
         ("P-E3.5b", "5%: as H-E3.2", CA, "P-E3.5b", None, "FAIL", "0/9"),
         ("P-E3.5c", "5%: as H-E3.3", CA, "P-E3.5c", None, "PASS", "9/9"),
         ("P-E3.6", "per flight: error does not fall as the rate rises", CA, "P-E3.6", "| P-E3.6 (dose–response) |", "FAIL", "0/3"),
         ("P-E3b.1 (robust)", "1% and 5%: robust error at most 1.10 × the plain FGO's", (CB, CB), ("P-E3b.1 0.01", "P-E3b.1 0.05"), None, "PASS", "9/9"),
         ("P-E3b.2 (robust)", "no wrong IDs: robust within ±10% of the clean error", CB, "P-E3b.2", None, "PASS", "3/3")]
TR3 = []
for idn, what, crit, key, defn, ev, ec in ROWS3:
    vs_ = []
    for cr_, k_ in (zip(crit, key) if isinstance(key, tuple) else [(crit, key)]):
        c_ = cr_[kk(cr_, k_)]
        vs_.append(num(f"{k_}: verdict and count", f"{c_['verdict']} {c_['count']}", f"{ev} {ec}", [("E3", f"**{ev}** | {ec}")]).split())
    if defn:
        ids((PRT, defn))
    TR3.append([idn, what, " and ".join(v_[1].replace("/", " of ") for v_ in vs_), vs_[0][0]])
for ph, lab in (("at 1%: LC live lap-5 ≤ 1.5 × lap-1", "H-E3.3 rule: lap 5 ≤ 1.5 × lap 1"),
                ("at 1%: LC live overall ≤ 2 × the same flight's clean LC live", "P-E3.4 rule: ≤ 2 × clean"),
                ("rate-0 control: robust LC live overall within ±10% of the stored clean LC live", "P-E3b.2 rule: within ±10% of clean")):
    rulef(PRT, ph, lab)
disp("P-E3.5 is registered as the H-E3.1, H-E3.2 and H-E3.3 criteria at 5%", "at 5%: the H-E3.1, H-E3.2 and H-E3.3 criteria",
     [("PR", "at 5%: the H-E3.1, H-E3.2 and H-E3.3 criteria")])
disp("P-E3b.1 is registered at 1% and at 5%", "at 1% and at 5%", [("PR", "at 1% and at 5%, **per run**")])
rulef(PRT, "robust LC live overall ≤ **1.10 ×** arm (a) LC live overall of the same flight, rate and seed", "P-E3b.1 rule: robust ≤ 1.10 × as built, per run")
num("P-E3b.1 at 1%: runs SATISFIED, flagged (matched arm (a) run diverged)", len(b1a["satisfied, flagged"]), 6, [("E3", "**6 runs are SATISFIED, flagged**")])
table(fig, meta, ["registered test", "what it checks", "runs passing", "verdict"],
      TR3, [19, 51, 17, 13], fs=11)
foot(fig, meta,
     "pass or fail of each test, counted over the runs (flights for P-E3.6); 1% / 5% = share of tag sightings given a wrong ID.",
     "each test as registered before the runs; a diverged run counts as not met.",
     f"Primary H-E3.1 FAIL; of the plain FGO's tests only P-E3.5c passed. The robust FGO's tests passed (6 of its 1% passes are flagged: "
     "the matching plain run diverged, so no ratio exists).")
finish(fig, meta)

# ------------------------------------------------------------------- E4, step time against the window
fig, meta = new_page("16", "E4_step_time", "Extension E4: a longer FGO window, compute time",
                     "How the FGO's compute time per step grows when its window of recent measurements is made longer, against the "
                     "33 ms available per camera frame.")
E4V = LT("E4_verdicts.json"); WS = [0.25, 0.5, 1, 2, 5]
MED4 = {w: [E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][i] for t in FLT] for i, w in enumerate(WS)}
EXP4 = {0.25: "14.35–15.13", 0.5: "26.86–28.22", 1: "50.47–52.74", 2: "100.05–107.12", 5: "278.25–303.36"}
V4S = {w: num(f"W = {w} s: median step time after the anchor, lowest–highest over 12 flights (ms)", rng(MED4[w], 2), EXP4[w],
              [("E4", x) for x in EXP4[w].split("–")]) for w in WS}
p41, p42 = E4V["P-E4.1"], E4V["P-E4.2"]
VP41 = num("P-E4.1 verdict and count", f"{p41['verdict']} {p41['count']}", "PASS 12/12", [("E4", "**P-E4.1 PASS 12/12.**")])
VP42 = num("P-E4.2 verdict and counts at 0.25 / 1 / 2 / 5 s", f"{p42['verdict']} " + " ".join(p42["counts"][k] for k in ("0.25", "1", "2", "5")),
           "PASS 12/12 12/12 12/12 12/12", [("E4", "0.25 s: 12/12, 1 s: 12/12, 2 s: 12/12, 5 s: 12/12")])
disp("windows swept (s)", "0.25 / 0.5 / 1 / 2 / 5", [("PR", "0.25 < 0.5 < 1 < 2 < 5 s")])
_p05 = p42["per_window"]["0.5"]["per_flight"]
V05 = num("W = 0.5 s (DESCRIPTIVE): flights with both medians ≤ 33 ms", f"{sum(v['median_all_ms'] <= 33 and v['median_after_anchor_ms'] <= 33 for v in _p05.values())} of {len(_p05)}",
          "12 of 12", [("E4", "0.5 s (DESCRIPTIVE, on the budget): 12/12 ≤ 33 ms")])
ids((PRT, "| P-E4.1 |"), (PRT, "| P-E4.2 |"))
rulef(PRT, "the 33 ms deployability budget (M:707-721): the median is ≤ 33 ms at W = 0.25 s and > 33 ms at W ≥ 1 s", "P-E4.2 rule: 33 ms budget")
counted("flights per window", "/".join(str(len(MED4[w])) for w in WS), "12/12/12/12/12", "E4_verdicts.json P-E4.1 per_flight, T_A-D r1-3")
def tagdisp():
    for c in TCOND:
        disp(f"condition {c}: number of tags", TAGS[c], [("T8", TAGS[c])])
    counted("flights per tag count", "/".join(str(sum(t[2] == c for t in FLT)) for c in TCOND), "3/3/3/3", "E4 runs: T_<c>_r1-r3 for c = A-D")
tagdisp()
ax = AX(0.10, 0.60, 0.10)
ax.set_xlim(0, 5.6); ax.set_ylim(0, 340)
for w in WS:
    rbox(ax, w, MED4[w], C["FGO"], True, w=0.14, minh=0.012)
ax.axhline(33, color=GREY, ls=(0, (6, 4)), lw=1.6, zorder=1)
label_val(ax, 5.55, 30, "budget 33 ms (one camera frame)", ha="right", va="top", fontsize=12.5, color="#555555")
for w, (tx, ty, ha, arrow) in {0.25: (1.5, 6, "left", True), 0.5: (1.5, 42, "left", True), 1: (1.5, 68, "left", True),
                               2: (2.12, 104, "left", False), 5: (4.88, 290, "right", False)}.items():
    T(f"{V4S[w]} ms")
    if arrow:
        ax.annotate(f"{V4S[w]} ms", xy=(w + 0.08, float(np.mean(MED4[w]))), xytext=(tx, ty), ha=ha, va="bottom", fontsize=12,
                    arrowprops=dict(arrowstyle="-", color="#777777", lw=1.0, shrinkA=2, shrinkB=2))
    else:
        ax.text(tx, ty, f"{V4S[w]} ms", ha=ha, va="center", fontsize=12)
ax.set_xticks(WS); ax.set_xticklabels([T(f"{w:g}") for w in WS])
_tl = ax.get_xticklabels(); _tl[0].set_ha("right"); _tl[1].set_ha("left")
ax.set_xlabel("FGO window of recent measurements (s)"); ax.set_ylabel("Median compute time per step (ms)")
lg = AX(0.73, 0.25, 0.10); lg.axis("off")
lg.legend(handles=[Patch(facecolor=C["FGO"], label="FGO live, median step\ntime per flight")], frameon=False, loc="upper left",
          title="box = lowest to highest\nof the 12 flights", title_fontsize=12)
lg.text(0, 0.35, wrap("Measured on a workstation in Python (one thread), not on the flight controller.", 26), fontsize=11.5, va="top",
        color=INK2, linespacing=1.25, transform=lg.transAxes)
foot(fig, meta,
     "median compute time per FGO step after the first tag fix, lowest–highest over 12 flights (8, 4, 2 and 1 tags, 3 each), "
     "milliseconds; a diagnostic workstation measurement.",
     "P-E4.1: the median rises with every longer window on 12 of 12 flights; P-E4.2: at most 33 ms at 0.25 s and more than 33 ms at "
     "1, 2 and 5 s, on 12 of 12 flights at each.",
     f"P-E4.1 {VP41.split()[0]} (12 of 12). P-E4.2 {VP42.split()[0]} (12 of 12 at each window). The 0.5 s window, registered as "
     f"descriptive only, was also within 33 ms on {V05} flights.")
for w in WS:
    T(f"{w:g}")
finish(fig, meta)

# ------------------------------------------------------------------- E4, live error against the window (2026-10-27)
# User request (verbatim): "can you reproduce the plot in the summary pdf with the fgo window vs error, it is hard to tell how
# increasing the window affects error increase/decrease". Replaces the L(5) - L(0.25) per-flight plot (D51) by the change from the
# 0.25 s value at every window, one panel per tag count on one shared y-scale (decisions D57-D60). Source: the stored cap-2 score
# files scores/E4_<trial>_w<W>.json, track "FGO live", horiz_err_m.rmse (the _lm10 files are not read).
fig, meta = new_page("17", "E4_accuracy", "Extension E4: a longer FGO window, live error",
                     "How the FGO's live position error changes when its window of recent measurements is made longer (0.25 s up "
                     "to 5 s), on the same flights, for each number of tags in the room.")
H43 = E4V["H-E4.3"]
D43 = [H43["per_flight"][t]["L5_m"] - H43["per_flight"][t]["L0.25_m"] for t in FLT]
LOW = [H43["per_flight"][t]["lower_at_5"] for t in FLT]
WK = ["0.25", "0.5", "1", "2", "5"]


def e4live(t, w):
    tr = LT(f"E4_{t}_w{w}.json")["tracks"]; ks = [k for k in tr if k.startswith("FGO live")]
    assert len(ks) == 1, f"E4_{t}_w{w}.json: FGO live tracks {ks}"
    return tr[ks[0]]["horiz_err_m"]["rmse"]


LW = {t: {w: e4live(t, w) for w in WK} for t in FLT}
DW = {t: {w: LW[t][w] - LW[t]["0.25"] for w in WK} for t in FLT}
tagdisp()
disp("windows swept (s)", "0.25 / 0.5 / 1 / 2 / 5", [("PR", "0.25 < 0.5 < 1 < 2 < 5 s")])
num("score files (cap 2) equal E4_verdicts.json L0.25_m and L5_m on every flight",
    str(all(LW[t]["0.25"] == H43["per_flight"][t]["L0.25_m"] and LW[t]["5"] == H43["per_flight"][t]["L5_m"] for t in FLT)), "True",
    [("E4", "All values come from `scores/E4_verdicts.json`")])
_E4ROW = {"T_A_r1": "0.0214 | 0.0214 | 0.0214 | 0.0214 | 0.0214", "T_A_r2": "0.0196 | 0.0196 | 0.0196 | 0.0196 | 0.0196",
          "T_A_r3": "0.0190 | 0.0190 | 0.0190 | 0.0190 | 0.0190", "T_B_r1": "0.0233 | 0.0230 | 0.0233 | 0.0232 | 0.0231",
          "T_B_r2": "0.0292 | 0.0292 | 0.0292 | 0.0292 | 0.0292", "T_B_r3": "0.0252 | 0.0252 | 0.0252 | 0.0252 | 0.0252",
          "T_C_r1": "0.0538 | 0.0546 | 0.0542 | 0.0540 | 0.0542", "T_C_r2": "0.0502 | 0.0501 | 0.0495 | 0.0497 | 0.0497",
          "T_C_r3": "0.0565 | 0.0564 | 0.0559 | 0.0561 | 0.0562", "T_D_r1": "0.0931 | 0.0901 | 0.0863 | 0.0890 | 0.0887",
          "T_D_r2": "0.0813 | 0.0814 | 0.0906 | 0.0803 | 0.0798", "T_D_r3": "0.0745 | 0.0743 | 0.0739 | 0.0738 | 0.0738"}
for t in FLT:
    num(f"{fl(t)}: plotted live RMSE at W = 0.25 / 0.5 / 1 / 2 / 5 s (m, 4 dp; the plot shows each minus the 0.25 s value)",
        " | ".join(rd(LW[t][w], 4) for w in WK), _E4ROW[t], [("E4", f"| {t} | {_E4ROW[t]} |")])
_E4R25 = {"A": "0.0190–0.0214", "B": "0.0233–0.0292", "C": "0.0502–0.0565", "D": "0.0745–0.0931"}
V25 = {c: num(f"{TAGS[c]}: live RMSE at W = 0.25 s, lowest–highest of 3 flights (m)",
              rng([LW[t]["0.25"] for t in FLT if t[2] == c], 4), _E4R25[c], [("E4", f" {x} |") for x in _E4R25[c].split("–")])
       for c in TCOND}
VH43 = num("H-E4.3 verdict and count", f"{H43['verdict']} {H43['count']}", "FAIL 7/12", [("E4", "**H-E4.3 FAIL 7/12** (band ≥ 10/12)")])
num("H-E4.3 flights lower at 5 s (recounted from the stored per-flight flags)", f"{sum(LOW)}/12", "7/12", [("E4", "| **FAIL** | 7/12 |")])
num("difference sign agrees with the stored flag on every flight", str(all((d < 0) == l for d, l in zip(D43, LOW))), "True", [("E4", "L(5) − L(0.25), unrounded")])
conv = E4V["convergence"]
nflag = sum(bool(v.get("NOT_CONVERGED")) for v in conv["per_run"].values())
VCV = num("LM cap 2 vs cap 10: runs flagged not converged", f"{nflag} of {len(conv['per_run'])}", "0 of 10", [("E4", "so no flag is raised")])
ids((PRT, "| **H-E4.3** (directional accuracy, amendment 3) |"))
rulef(PRT, "| **≥ 10/12 flights** |", "H-E4.3 rule: lower at 5 s on at least 10 of 12 flights")
disp("windows compared (s)", "5 s / 0.25 s", [("E4", "live RMSE at 5 s < at 0.25 s")])


# Result sentence (descriptive, D59): bounds on |change from the 0.25 s value| over every longer window and every flight of a panel
# group, from the stored jsons (no result file prints them). "under X" = the largest value rounded ONCE upwards (ROUND_CEILING) at
# the printed precision, with largest < X asserted; "up to about X" = the largest rounded once by rd(); directions = both signs present.
def ceil_s(v, n):
    from decimal import Decimal, ROUND_CEILING
    return format(Decimal(str(float(v))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_CEILING), "f")


def chg(cs):
    return [DW[t][w] for t in FLT if t[2] in cs for w in WK[1:]]


MAB, MC, MD = (max(abs(v) for v in chg(cs)) for cs in ("AB", "C", "D"))
VBAB = num("8 or 4 tags: largest |change from 0.25 s| over every window and flight, rounded up once (m)", ceil_s(MAB, 4), "0.0003", [])
num("8 or 4 tags: largest |change| is strictly under the printed bound ('under')", str(MAB < float(VBAB)), "True", [])
VBC = num("2 tags: largest |change from 0.25 s| over every window and flight, rounded up once (m)", ceil_s(MC, 3), "0.001", [])
num("2 tags: largest |change| is strictly under the printed bound ('under')", str(MC < float(VBC)), "True", [])
num("2 tags: changes of both signs ('either way')", str(min(chg("C")) < 0 < max(chg("C"))), "True", [])
VBD = num("1 tag: largest |change from 0.25 s| over every window and flight, rounded once (m; 'up to about')", rd(MD, 3), "0.009", [])
num("1 tag: changes of both signs ('not in one direction')", str(min(chg("D")) < 0 < max(chg("D"))), "True", [])
num("1 tag: the largest |change| exceeds the 2-tag bound ('larger')", str(MD > float(VBC)), "True", [])
num("1 tag, flight 2, W = 1 s: change from 0.25 s (m, the largest; rounded once, 7 dp; not printed)", rd(DW["T_D_r2"]["1"], 7, sign=True),
    "+0.0093144", [])
num("1 tag, flight 1, W = 1 s: change from 0.25 s (m; rounded once, 7 dp; not printed)", rd(DW["T_D_r1"]["1"], 7, sign=True),
    "-0.0067342", [])

# four panels, one per tag count, on ONE shared y-scale (sharey); the windows at evenly spaced positions, not to scale (D57); one line
# per flight, filled markers (live), flights told apart by marker and nudged sideways so equal values stay visible (D58)
YLIM = (-0.0080, 0.0110)
assert YLIM[0] < min(min(DW[t].values()) for t in FLT) and max(max(DW[t].values()) for t in FLT) < YLIM[1]
FMK = {"1": "s", "2": "o", "3": "^"}; DODGE = {"1": -0.12, "2": 0.0, "3": 0.12}
PX = [0.115 + i * 0.215 for i in range(4)]; PW = 0.19
axs = [AX(PX[i], PW, 0.135) for i in range(4)]
for i, (ax, c) in enumerate(zip(axs, TCOND)):
    if i:
        ax.sharey(axs[0])
    ax.set_ylim(*YLIM); ax.set_xlim(-0.45, 4.45)
    ax.axhline(0, color=INK2, lw=1.2, zorder=2)
    for t in FLT:
        if t[2] == c:
            r = t[-1]
            ax.plot([k + DODGE[r] for k in range(5)], [DW[t][w] for w in WK], color=C["FGO"], lw=1.5, marker=FMK[r], ms=7.5,
                    mfc=C["FGO"], mec=C["FGO"], zorder=4)
    ax.set_xticks(range(5)); ax.set_xticklabels([T(w) for w in WK], fontsize=11.5)
    ax.grid(axis="x", visible=False)
    ax.set_title(T(TAGS[c]) + "\n" + T(f"at 0.25 s: {V25[c]} m"), fontsize=12, pad=6)
    if i:
        ax.tick_params(labelleft=False)
axs[0].set_yticks([-0.006, -0.003, 0, 0.003, 0.006, 0.009])
axs[0].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.3f}".replace("-", "−") if abs(v) > 1e-12 else "0"))
axs[0].set_ylabel("Change in live error from\nits 0.25 s value (m)")
label_val(axs[0], -0.35, -0.0075, "below 0 = more accurate", fontsize=11, color="#555555", va="bottom")
axs[0].legend(handles=[Line2D([], [], color=C["FGO"], lw=1.5, marker=FMK[r], ms=7.5, label=T(f"flight {r}")) for r in "123"],
              frameon=False, loc="upper left", fontsize=11, title="FGO live", title_fontsize=11, borderaxespad=0.3)
foot(fig, meta,
     "change in the live horizontal position error over the laps (root-mean-square, room frame, nothing fitted) from its value with "
     "the 0.25 s window, per flight and window, metres. The windows are evenly spaced, not to scale.",
     "H-E4.3: the error is lower with the 5 s window on at least 10 of 12 flights (a count fixed in advance).",
     f"H-E4.3 {VH43.split()[0]}: lower at 5 s on {VH43.split()[1].replace('/', ' of ')} flights. The check that two solver iterations are "
     f"enough raised no flag ({VCV} runs). With 8 or 4 tags the window changes the live error by under {VBAB} m; with 2 tags by under "
     f"{VBC} m either way; with 1 tag the changes are larger (up to about {VBD} m) and not in one direction.")
_b = axs[0].get_position().y0
fig.text(PX[0] + (PX[3] + PW - PX[0]) / 2, _b - 0.045, T("FGO window of recent measurements (s), evenly spaced, not to scale"),
         ha="center", va="top", fontsize=13)
finish(fig, meta)

# ------------------------------------------------------------------- E4, live error against compute time (2026-11-02, D110)
# User request 2026-11-02 ("a live error vs compute time plot"), scoped to E4 only and DESCRIPTIVE (no new verdict): the same stored
# values as pages 16 and 17 on one axis, x = each flight's median step time after the anchor at each window (E4_verdicts.json
# P-E4.1), y = the same flight's live RMSE at that window (the cap-2 score files read for page 17). Page id 21, printed after 17.
fig, meta = new_page("21", "E4_error_vs_compute", "Extension E4: live error against compute time",
                     "Whether paying for a longer FGO window in compute time buys a lower live position error, on the same 12 "
                     "flights (DESCRIPTIVE, not a registered measure).")
tagdisp()
disp("windows swept (s)", "0.25 / 0.5 / 1 / 2 / 5", [("PR", "0.25 < 0.5 < 1 < 2 < 5 s")])
for w in WS:
    num(f"W = {w} s: median step time after the anchor, lowest–highest over 12 flights (ms)", rng(MED4[w], 2), EXP4[w],
        [("E4", x) for x in EXP4[w].split("–")])
num("points pair one flight's step time with the same flight's live error at the same window",
    str(all(MED4[w][j] == E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][i] for i, w in enumerate(WS) for j, t in enumerate(FLT))),
    "True", [])
_r21 = [E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][4] / E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][0] for t in FLT]
VR21 = num("5 s / 0.25 s median step time per flight, lowest–highest of 12 (×, whole numbers)", f"{rd(min(_r21), 0)}–{rd(max(_r21), 0)}",
           "19–20", [])
_mx21 = max(abs(v) for t in FLT for w, v in DW[t].items() if w != "0.25")
num("largest |change in live RMSE from the 0.25 s value| over every longer window and flight is under 0.01 m", str(_mx21 < 0.01), "True", [])
disp("bound printed (m)", "0.01", [])
num("H-E4.3 verdict and count", f"{H43['verdict']} {H43['count']}", "FAIL 7/12", [("E4", "**H-E4.3 FAIL 7/12** (band ≥ 10/12)")])
disp("H-E4.3 band: at least 10 of 12 flights", "10 of 12", [("E4", "(band ≥ 10/12)")])
disp("deployability budget (ms)", "33", [("PR", "the 33 ms deployability budget (M:707-721)")])
ids((PRT, "| **H-E4.3** (directional accuracy, amendment 3) |"))
counted("flights, points per flight", f"{len(FLT)}, {len(WK)}", "12, 5", "E4 runs T_A-D r1-3 × 5 windows")
ax = AX(0.10, 0.70, 0.10)
ax.set_xlim(0, 370); ax.set_ylim(0, 0.10)
assert max(max(MED4[w]) for w in WS) < 320 and max(max(v.values()) for v in LW.values()) < 0.10
for j, t in enumerate(FLT):
    ax.plot([MED4[w][j] for w in WS], [LW[t][w] for w in WK], color=C["FGO"], lw=1.4, marker="s", ms=6, mfc=C["FGO"], mec=C["FGO"], zorder=3)
ax.axvline(33, color=GREY, ls=(0, (6, 4)), lw=1.6, zorder=1)
label_val(ax, 37, 0.043, "budget 33 ms (one camera frame)", ha="left", va="center", fontsize=12, color="#555555")
for w, ha in zip(WS, ("right", "left", "center", "center", "center")):
    ax.text(float(np.mean(MED4[w])) + {"right": 3, "left": -3}.get(ha, 0), 0.003, T(f"{w:g} s"), ha=ha, va="bottom", fontsize=11.5,
            color=INK2, zorder=5, bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none") if w == 0.5 else None)
for c in TCOND:
    ys = [LW[t]["5"] for t in FLT if t[2] == c]
    yl = {"A": min(ys) - 0.0045, "B": max(ys) + 0.0045}.get(c, float(np.mean(ys)))
    ax.text(max(MED4[5]) + 10, yl, T(TAGS[c]), ha="left", va="center", fontsize=12.5, color=INK2, weight="bold")
ax.set_xlabel("FGO median compute time per step (ms); labels at the bottom = the window")
ax.set_ylabel("FGO live horizontal error, RMSE (m)")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
lg = AX(0.83, 0.15, 0.10); lg.axis("off")
lg.text(0, 0.98, wrap("One line per flight (12), one point per window, joined in window order. Compute measured on a workstation in "
                      "Python; no other estimator is drawn.", 20), fontsize=11, va="top", color=INK2, linespacing=1.25, transform=lg.transAxes)
foot(fig, meta,
     "each flight's live horizontal position error over the laps (root-mean-square, room frame, nothing fitted, metres) against its "
     "median compute time per FGO step after the first tag fix (milliseconds, a diagnostic workstation measurement), at each window.",
     "none: DESCRIPTIVE, not a registered measure. The registered E4 tests are on the two previous pages.",
     f"From 0.25 s to 5 s the compute per step rose {VR21.replace('–', ' to ')} times on every flight, while no longer window changed "
     f"a flight's live error by 0.01 m or more (H-E4.3 FAIL: lower at 5 s on 7 of 12 flights, 10 of 12 needed).")
finish(fig, meta)

# ------------------------------------------------------------------- E5, UKF with landmark states
fig, meta = new_page("18", "E5_ukf_landmarks", "Extension E5: a UKF with landmark states",
                     "Whether a UKF with landmark states (extension E5), not the UKF used elsewhere, keeps its error small by "
                     "recognising tags seen before, with the FGO for reference.")
E5V = LT("e5_verdicts.json")["flights"]; E5C = LT("e5_verdicts.json")["criteria"]
E5S = {r: LT(f"e5_T_A_r{r}.json")["tracks"] for r in (1, 2, 3)}
VAL5 = {}
for m in ("lc", "nolc"):
    for k in ("live", "hindsight"):
        VAL5[("UKF", m, k)] = [E5S[r][f"{m} {k}"]["rmse_m"] for r in (1, 2, 3)]
        VAL5[("FGO", m, k)] = [E5V[f"T_A_r{r}"]["values"][f"fgo {m} {k} rmse_m"]["value"] for r in (1, 2, 3)]
        num(f"FGO {m} {k}: the reference equals the stored Experiment 3 value", str(VAL5[("FGO", m, k)] == [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{m} {k}"]["rmse_m"] for r in (1, 2, 3)]),
            "True", [("E5", "eval/results/expL/T_A_r<i>_t245.json")])
EXP5 = {("UKF", "lc", "live"): "0.0911–0.1335", ("UKF", "lc", "hindsight"): "0.0445–0.0552", ("UKF", "nolc", "live"): "0.8738–1.4112",
        ("UKF", "nolc", "hindsight"): "0.9162–1.3349", ("FGO", "lc", "live"): "0.0494–0.0760", ("FGO", "lc", "hindsight"): "0.0172–0.0270",
        ("FGO", "nolc", "live"): "0.2625–0.3608", ("FGO", "nolc", "hindsight"): "0.2210–0.2657"}
SH5 = {"UKF": "E5", "FGO": "E3"}
V5 = {g: num(f"{g[0]} {'with' if g[1] == 'lc' else 'without'} loop closure, {g[2]}: lowest–highest over 3 flights (m)", rng(VAL5[g], 4), x,
             [(SH5[g[0]] if not (g[0] == "FGO" and g[1] == "lc" and g[2] == "live") else "E5", y) for y in x.split("–")]) for g, x in EXP5.items()}
r51e = [E5V[f"T_A_r{r}"]["ratio lc live lap5/lap1"] for r in (1, 2, 3)]
VR5 = num("H-E5.1: lap 5 ÷ lap 1, live with loop closure, lowest–highest", rng(r51e, 2), "0.27–0.42", [("E5", "ratio 0.27 / 0.42 / 0.30")])
VC5 = {h: num(f"{h}: verdict and count", f"{E5C[h]['verdict']} {E5C[h]['count']}", "PASS 3/3",
              [("E5", f"| 3/3 | **PASS**")]) for h in ("H-E5.1", "H-E5.2", "H-E5.3", "P-E5.4", "S-E5.5", "S-E5.6")}
disp("S-E5.6: the FGO side is the iSAM2 hindsight (its whole graph after 5 extra updates), not an LM batch",
     "iSAM2's full-graph estimate after 5 extra updates", [("E5", "iSAM2's full-graph estimate after 5")])
ids((PRT, "| **H-E5.1 (PRIMARY)** |"), (PRT, "| H-E5.2 |"), (PRT, "| H-E5.3 |"), (PRT, "| P-E5.4 |"), (PRT, "| S-E5.5 (live) |"), (PRT, "| S-E5.6 (hindsight) |"))
disp("extension label", "E5", [("PR", "**E5 primary:**")])
rulef(PRT, "with re-identification (LC), the landmark UKF's live lap-5 RMSE ≤ 1.5 × its live lap-1 RMSE, per flight", "H-E5.1 rule: lap 5 ≤ 1.5 × lap 1")
counted("flights", len(r51e), 3, "e5_T_A_r1-r3 (8-tag room)")
disp("the room of E5: all 8 tags (condition A)", "8 tags", [("T8", "8 tags")])
ax = AX(0.09, 0.64, 0.10)
ax.set_xlim(-0.62, 1.92); ax.set_ylim(0, 1.75)
for j, m in enumerate(("nolc", "lc")):
    for k, (e, kind) in enumerate((("UKF", "live"), ("UKF", "hindsight"), ("FGO", "live"), ("FGO", "hindsight"))):
        x = j * 1.3 + (k - 1.5) * 0.265
        top_ = rbox(ax, x, VAL5[(e, m, kind)], C[e], kind == "live", w=0.2)
        label_val(ax, x, top_ + 0.03, V5[(e, m, kind)].replace("–", "–\n") + " m", ha="center", va="bottom", fontsize=10.5, linespacing=1.05)
ax.set_xticks([0, 1.3]); ax.set_xticklabels(["without loop closure", "with loop closure"])
ax.grid(axis="x", visible=False); ax.set_ylabel("Average horizontal position error (m)")
lg = AX(0.75, 0.24, 0.10); lg.axis("off")
lg.legend(handles=[Patch(facecolor=C["UKF"], edgecolor=C["UKF"], lw=2, label="UKF with landmark\nstates (E5), live"),
                   Patch(facecolor="white", edgecolor=C["UKF"], lw=2, label="the same, hindsight\n(smoothed after\nlanding)"),
                   Patch(facecolor=C["FGO"], edgecolor=C["FGO"], lw=2, label="FGO live (stored\nExperiment 3)"),
                   Patch(facecolor="white", edgecolor=C["FGO"], lw=2, label="FGO hindsight\n(stored, iSAM2)")],
          frameon=False, loc="center left", labelspacing=1.2, title="box = lowest to highest\nof the 3 flights", title_fontsize=12)
T("UKF with landmark\nstates (E5), live")
foot(fig, meta,
     "average horizontal position error over five laps (root-mean-square), lowest–highest over 3 flights (8-tag room), metres, in the "
     "frame of the start tag; the FGO values are the stored Experiment 3 results.",
     "primary H-E5.1: with loop closure the UKF's lap-5 live error is at most 1.5 × its lap-1 error in 3 of 3 flights; H-E5.2, H-E5.3 "
     "and P-E5.4 as in Experiment 3; secondary S-E5.5 and S-E5.6: the UKF's live and hindsight errors are above the FGO's.",
     f"H-E5.1 PASS (3 of 3; lap 5 ÷ lap 1 = {VR5}); H-E5.2, H-E5.3 and P-E5.4 PASS (3 of 3). S-E5.5 and S-E5.6 PASS (3 of 3): the UKF's "
     "errors were higher than the FGO's. S-E5.6 compares with the FGO's iSAM2 hindsight (its whole graph after 5 extra updates), not an "
     "LM batch.")
finish(fig, meta)

# ------------------------------------------------------------------- E6, map reuse (added 2026-11-02, user answer 5; decisions D101-D104)
# Stored E6 score and verdict files only (docs/thesis/tier1/scores/e6_T_A_r{1,2,3}.json, e6_verdicts.json). Placed after E5 and before
# the exploratory ablation (page id 20; the ablation keeps id 19 so no existing page, file or check row is renumbered). The Metric and
# Pass rule lines are fragments of the E6 pre-registration, word for word (markdown bold removed), each checked against its line; the
# Result line is the verdicts as worded, computed from e6_verdicts.json and checked against e6_results.md §3.
for k_, p_, n_ in (("E6", "tier1/e6_results.md", "E6 results (tier1/e6_results.md)"),
                   ("E6PR", "tier1/e6_preregistration.md", "E6 pre-registration (tier1/e6_preregistration.md)")):
    DISP[k_] = os.path.join(ROOT, "docs", "thesis", p_); DNAME[k_] = n_
E6PRP = "docs/thesis/tier1/e6_preregistration.md"


def rule_plain(path, phrase, label):
    """rule() on the one line of `path` that contains `phrase` once markdown bold (**) is removed (asserted unique)."""
    ls = [i + 1 for i, ln in enumerate(open(os.path.join(ROOT, path)).read().split("\n")) if phrase in ln.replace("**", "")]
    assert len(ls) == 1, f"{path}: '{phrase}' found on lines {ls}, expected exactly one"
    ok = True
    CHK.append(dict(page=PAGE, kind="rule", label=label, computed=phrase, expected=phrase, where=f"{os.path.basename(path)}:{ls[0]} (bold removed)", ok=ok))
    return phrase


fig, meta = new_page("20", "E6_map_reuse", "Extension E6: reusing a tag map from an earlier flight",
                     "Whether a tag map estimated in hindsight from one earlier flight, then used as if exact, can replace surveying the "
                     "tags: the live error on that map against the surveyed map and against no map.")
E6V = LT("e6_verdicts.json"); E6F = E6V["flights"]; E6T = ["T_A_r1", "T_A_r2", "T_A_r3"]
E6S = {t: LT(f"e6_{t}.json")["tracks"] for t in E6T}
ARM6 = {"sv": "(i) surveyed", "fm": "(ii) FGO map", "um": "(iii) UKF map", "nm": "(iv) no map, LC online"}
LAP1_6 = {(e, a): [E6F[t][e][f"{ARM6[a]} | live"]["lap1_m"] for t in E6T] for e in ("FGO", "UKF") for a in ARM6}
ALL6 = {(e, a): [E6F[t][e][f"{ARM6[a]} | live"]["rmse_m"] for t in E6T] for e in ("FGO", "UKF") for a in ARM6}
num("verdict file values equal the score files (lap 1 and overall, live, every arm, both estimators)",
    str(all(LAP1_6[(e, a)][i] == E6S[t][f"{ARM6[a]} | {e} live"]["per_lap_rmse_m"][0] and ALL6[(e, a)][i] == E6S[t][f"{ARM6[a]} | {e} live"]["rmse_m"]
            for e in ("FGO", "UKF") for a in ARM6 for i, t in enumerate(E6T))), "True", [("E6", "json:scores/e6_T_A_r{1,2,3}.json")])
EXP6 = {("FGO", "fm"): "0.0303–0.0510", ("FGO", "nm"): "0.0818–0.1608", ("UKF", "fm"): "0.0389–0.0471", ("UKF", "nm"): "0.1560–0.2565"}
V6L1 = {g: num(f"{g[0]} estimator, {ARM6[g[1]]}: lap-1 live RMSE, lowest–highest over 3 test flights (m)", rng(LAP1_6[g], 4), x, [("E6", x)])
        for g, x in EXP6.items()}
RAT6 = {e: [ALL6[(e, "fm")][i] / ALL6[(e, "sv")][i] for i in range(3)] for e in ("FGO", "UKF")}
num("FGO map ÷ surveyed (live) recomputed equals the stored descriptive ratio, both estimators (12 dp)",
    str(all(rd(RAT6[e][i], 12) == rd(E6F[t][e]["descriptive"]["FGO map / surveyed, live"], 12) for e in ("FGO", "UKF") for i, t in enumerate(E6T))), "True",
    [("E6", "FGO map ÷ surveyed (live)")])
V6R = {e: num(f"{e} estimator: FGO map ÷ surveyed map, overall live RMSE, lowest–highest (×)", rng(RAT6[e], 2), x, [("E6", f"{x} times")])
       for e, x in (("FGO", "1.52–2.14"), ("UKF", "0.98–1.26"))}
BND6 = {e: (E6V["p2_bands_m"][e]["lo"], E6V["p2_bands_m"][e]["hi"]) for e in ("FGO", "UKF")}
V6B = {e: num(f"{e} estimator: surveyed-map band for P2 [min − R, max + R], 4 dp (m)", f"{rd(BND6[e][0], 4)}–{rd(BND6[e][1], 4)}", x, [("E6PR", f"({x})")])
       for e, x in (("FGO", "0.0167–0.0237"), ("UKF", "0.0330–0.0408"))}
CR6 = E6V["criteria"]
V6 = {k: num(f"{k}: verdict and count", f"{CR6[k]['verdict']} {sum(CR6[k]['per_flight'])}/3", x, [("E6", y)])
      for k, x, y in (("P1", "FAIL 2/3", "| P1 |"), ("P2 (FGO)", "FAIL 0/3", "| P2 (FGO) |"), ("P2 (UKF)", "FAIL 2/3", "| P2 (UKF) |"),
                      ("P3 (FGO)", "FAIL 2/3", "| P3 (FGO) |"), ("P3 (UKF)", "FAIL 2/3", "| P3 (UKF) |"), ("P4 (FGO)", "PASS 3/3", "| P4 (FGO) |"),
                      ("P4 (UKF)", "PASS 3/3", "| P4 (UKF) |"))}
SAME6 = num("DESCRIPTIVE: per-flight outcomes of P1, P3 (FGO) and P3 (UKF) identical on the 3 flights", str(CR6["P1"]["per_flight"] == CR6["P3 (FGO)"]["per_flight"] == CR6["P3 (UKF)"]["per_flight"]),
            "True", [("E6", "P1, P3 (FGO) and P3 (UKF) are identical (no, yes, yes)")])
RES6 = (f"P1 {V6['P1'].split()[0]} {V6['P1'].split()[1]}; P2 {V6['P2 (FGO)'].split()[0]} (FGO {V6['P2 (FGO)'].split()[1]}, UKF {V6['P2 (UKF)'].split()[1]}); "
        f"P3 {V6['P3 (FGO)'].split()[0]} {V6['P3 (FGO)'].split()[1]} each; P4 {V6['P4 (FGO)'].split()[0]} {V6['P4 (FGO)'].split()[1]} each "
        "(live tracks; hindsight carries no verdict).")
assert V6["P3 (FGO)"] == V6["P3 (UKF)"] and V6["P4 (FGO)"] == V6["P4 (UKF)"] and V6["P2 (FGO)"].split()[0] == V6["P2 (UKF)"].split()[0]
rule_plain(E6PRP, "Hindsight tracks carry no verdict (descriptive, §6).", "hindsight carries no verdict")
MET6 = "; ".join(rule_plain(E6PRP, f_, f"metric fragment {i + 1}") for i, f_ in enumerate((
    "per track: horizontal RMSE over the window, max, per-lap RMSE laps 1–5, lap-5 / lap-1",
    "One scorer, one frame (world), no alignment",
    "position RMS over the 7 tags (the P1 metric)")))
RFR6 = [("P1", "PASS iff FGO-map position RMS < UKF-map position RMS on 3/3 mapping flights (strict, unrounded)"),
        ("P2", "PASS iff, on 3/3 test flights, the live RMSE on the FGO map lies inside the surveyed-map band [min − R, max + R] of the same estimator"),
        ("P3", "PASS iff live RMSE (FGO map) < live RMSE (UKF map) on 3/3 test flights (paired: same flight, same estimator; strict, unrounded)"),
        ("P4", "PASS iff lap-1 live RMSE (FGO map) < lap-1 live RMSE (arm (iv)) on 3/3 test flights")]
RULE6 = " ".join(f"{k}: {rule_plain(E6PRP, f_, f'{k} pass rule (fragment)')}." for k, f_ in RFR6) + " " + \
        rule_plain(E6PRP, "P2–P4 are judged separately for each test estimator (UKF and FGO), 3/3 each.", "P2-P4 per estimator")
ids((E6PRP, "| **P1** |"), (E6PRP, "| **P2** |"), (E6PRP, "| **P3** |"), (E6PRP, "| **P4** |"))
disp("tag 0 registers the frame", "tag 0", [("E6", "(tag 0, pre-registration §1.2)")])
disp("mapping flights: a different route, out of sample", "out-of-sample figures of eight on a different route", [("E6", "out-of-sample figures of eight on a different route")])
counted("test flights / mapping flights / non-gauge tags", "3 / 3 / 7", "3 / 3 / 7", "e6_verdicts.json pairs; 7 non-gauge tags (e6_results.md §2)")
rule_plain(E6PRP, "the FGO estimator is compared with the stored Experiment 3 FGO, the UKF with the stored E5 landmark UKF", "P4 confound: arm (iv) uses other estimators")
# chart: left = lap 1 (P4), right = whole flight (P2); one box per arm per estimator, filled = live
EOR = ("FGO", "UKF")
axa = AX(0.075, 0.30, 0.10); axb = AX(0.435, 0.22, 0.10)
axa.set_xlim(-0.6, 1.6); axa.set_ylim(0, 0.30); axb.set_xlim(-0.6, 1.6); axb.set_ylim(0, 0.06)
for j, e in enumerate(EOR):
    for k, (a, lab) in enumerate((("fm", "FGO map"), ("nm", "no map"))):
        x = j + (k - 0.5) * 0.46
        top_ = rbox(axa, x, LAP1_6[(e, a)], C[e], True, w=0.36)
        label_val(axa, x, top_ + 0.006, V6L1[(e, a)].replace("–", "–\n") + " m", ha="center", va="bottom", fontsize=10.5, linespacing=1.05)
        label_val(axa, x, -0.012, lab, ha="center", va="top", fontsize=10.5, color=INK2)
    lo_, hi_ = BND6[e]
    axb.add_patch(Rectangle((j - 0.3, lo_), 0.6, hi_ - lo_, facecolor=GREY, alpha=0.35, lw=0, zorder=1))
    top_ = rbox(axb, j, ALL6[(e, "fm")], C[e], True, w=0.3)
    _rl = V6R[e].replace("–", "–\n")
    label_val(axb, j, top_ + 0.0015, f"{_rl} ×\nsurveyed", ha="center", va="bottom", fontsize=10.5, linespacing=1.05)
    label_val(axb, j, -0.0024, "FGO map", ha="center", va="top", fontsize=10.5, color=INK2)
for ax_, t_ in ((axa, "First lap (P4)"), (axb, "Whole flight (P2)")):
    ax_.set_xticks([0, 1]); ax_.set_xticklabels([T(f"{e}\nestimator") for e in EOR]); ax_.tick_params(axis="x", pad=20)
    ax_.grid(axis="x", visible=False); ax_.set_title(T(t_), loc="left", fontsize=13)
axa.set_ylabel("live error (m)"); axb.set_ylabel("live error (m)")
label_val(axb, 1.55, 0.0035, "grey: surveyed-map band", ha="right", va="bottom", fontsize=10.5, color="#555555")
tx = AX(0.69, 0.30, 0.07); tx.axis("off")
NOTE6 = ("Box: lowest to highest of the 3 test flights, live. Descriptive (3 flights): P1, P3 (FGO) and P3 (UKF) gave the same per-flight outcome (no, yes, yes): the map with the lower "
         "map error gave the lower live error, so map quality, not estimator, decided P3. Limitations: simulation; n = 3; perfect tag "
         "IDs; tag 0 anchors the frame; maps used as exact; same world and day; P4 compares with other loop-closure estimators. The "
         "mapping flights flew a different route (out of sample).")
tx.text(0, 1, wrap(T(NOTE6), 37), fontsize=10.5, va="top", ha="left", linespacing=1.18, transform=tx.transAxes)
foot(fig, meta, MET6 + ".", RULE6, RES6)
finish(fig, meta)

# ------------------------------------------------------------------- Ablation (EXPLORATORY)
fig, meta = new_page("19", "ablation", "Ablation (EXPLORATORY): the FGO's window and iterations",
                     "Whether the FGO's lower error than the UKF with the camera heading comes from its window, retained history or "
                     "iteration count. Exploratory: not a thesis hypothesis; it has its own signed-off pre-registration.")
ABR = json.load(open(os.path.join(ABD, "ablation_results.json")))
FW3 = ["fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3"]; RUNG = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]
AV = {(g, b): ABR["runs"][f"{g}.{b}.heading"]["ate_a_cruise_m"] for g in RUNG for b in FW3}
UK = [ABR["stored"][b]["U_heading"] for b in FW3]
num("r0 equals the stored thesis FGO on the 3 bags (identity gate)", str([AV[("r0", b)] for b in FW3] == [ABR["stored"][b]["F0_heading"] for b in FW3]), "True",
    [("AB", "**Identity gate (r0, 0.25 s, cap 2): PASS.**")])
num("every plotted run is status OK", str(all(ABR["runs"][f"{g}.{b}.heading"]["status"] == "OK" for g in RUNG for b in FW3)), "True", [("AB", "84/84 OK")])
VUK = num("stored UKF with heading, the 3 line-textured bags, lowest–highest (m)", rng(UK, 3), "0.127–0.137", [("AB", "0.127"), ("AB", "0.137")])
VFA = num("FGO, all plotted rungs, lowest–highest (m)", rng(list(AV.values()), 3), "0.044–0.065", [("AB", "0.044"), ("AB", "0.065")])
P1, P2, P3 = ABR["P1"], ABR["P2"], ABR["P3"]
VP1 = num("P1 verdict (needs every rung 6/6) and the r1-r5 counts", f"{'FAIL' if any(P1[r]['verdict'] == 'FAIL' for r in ('r1', 'r2', 'r3', 'r4', 'r5')) else 'PASS'} "
          + " ".join(f"{P1[r]['n_within']}/6" for r in ("r1", "r2", "r3", "r4", "r5")), "FAIL 5/6 5/6 5/6 6/6 6/6", [("AB", "| P1 overall | FAIL |")]).split()[0]
VP2 = num("P2 verdict and count", f"{P2['verdict']} {P2['n_pass']}/3", "PASS 3/3", [("AB", "| P2 | PASS | 3/3 |")])
VP3 = num("P3 verdict", P3["verdict"], "FAIL", [("AB", "| P3 | FAIL | r6 4/6, r7 2/6 |")])
disp("P3 is confounded with removing the heading gate", "Confounded with gate removal", [("AB", "Confounded with gate removal")])
# the Result line is the ruled discussion paragraph, extracted at build time and asserted verbatim (decision D52)
_dm = open(DISP["DM"]).read().split("\n")
_i = next(i for i, l_ in enumerate(_dm) if l_.startswith("> An exploratory ablation"))
_par = []
while _i < len(_dm) and _dm[_i].startswith(">"):
    _par.append(_dm[_i][1:].strip()); _i += 1
PARA = " ".join(_par)
disp("Result = the ruled discussion paragraph, verbatim (discussion_material.md §1)", PARA, [("DM", p_) for p_ in _par])
R3 = [ABR["R"][f"r3.{b}"] for b in FW3]
num("paragraph 'retention 0.97-1.01': R(r3) on the 3 line-textured bags, lowest-highest (ASCII hyphen, as written)", f"{rd(min(R3), 2)}-{rd(max(R3), 2)}", "0.97-1.01",
    [("DM", "retention 0.97-1.01"), ("AB", "R(r3) on `fwdc`: 1.01, 0.97, 0.98")])
d4 = [abs(P1[r]["bags"]["fwdplainc_tex_r3"]["delta_m"]) for r in ("r1", "r2", "r3")]
num("paragraph 'about 0.4 m': |Δ| on fwdplainc_tex_r3 at r1-r3, each rounded to 1 dp", " ".join(rd(x, 1) for x in d4), "0.4 0.4 0.4", [("DM", "(by about 0.4 m)")])
d13 = max(abs(P1[r]["bags"]["fwdc_tex_r2"]["delta_m"]) for r in ("r1", "r2", "r3", "r4", "r5"))
num("paragraph 'up to 1.3 m': largest |Δ| on fwdc_tex_r2 over r1-r5", rd(d13, 1), "1.3", [("DM", "by up to 1.3 m on another")])
RL = {"r0": "0.25 s\ncap 2\n(thesis)", "r1": "one\nkeyframe\ncap 1", "r2": "one\nkeyframe\ncap 2", "r3": "one\nkeyframe\ncap 100", "r4": "1 s\ncap 2",
      "r5": "2 s\ncap 2", "r6": "0.25 s\nrobust", "r7": "one\nkeyframe\nrobust"}
for g, ph in (("r0", "| `r0_w0.25_lm2` | 0.25 | 2 |"), ("r1", "| `r1_kf1_lm1` | 0.01 | 1 |"), ("r2", "| `r2_kf1_lm2` | 0.01 | 2 |"),
              ("r3", "| `r3_kf1_lm100` | 0.01 | 100 |"), ("r4", "| `r4_w1_lm2` | 1 | 2 |"), ("r5", "| `r5_w2_lm2` | 2 | 2 |"),
              ("r6", "| `r6_w0.25_lm2_huber` | 0.25 | 2 |"), ("r7", "| `r7_kf1_lm100_huber` | 0.01 | 100 |")):
    rulef(PRA, ph, f"rung {g}: window (s) and iteration cap")
rulef(PRA, "Pass iff R_i(r3) ≥ 0.5 on all 3 `fwdc` bags.", "P2 rule: r3 keeps at least half the gap on each of the 3 line-textured bags")
ids((PRA, "**P1 (control, no heading).**"), (PRA, "**P2 (with heading): the one-keyframe converged FGO (r3: cap 100"),
    (PRA, "**P3 (descriptive): robust weighting replacing the heading gate (Huber 1.345)"))
counted("line-textured with-heading bags", len(FW3), 3, "ablation_results.json runs <rung>.fwdc_tex_r1-r3.heading")
ax = AX(0.095, 0.61, 0.135)
ax.set_xlim(-0.6, 7.6); ax.set_ylim(0, 0.16)
ax.axhspan(min(UK), max(UK), color=C["UKF"], alpha=0.22, lw=0, zorder=1)
for u in UK:
    ax.axhline(u, color=C["UKF"], lw=1.6, ls=(0, (5, 3)), zorder=2)
label_val(ax, 7.55, max(UK) + 0.003, f"UKF with the heading (stored): {VUK} m", ha="right", va="bottom", fontsize=12, color=C["UKF"])
for j, g in enumerate(RUNG):
    for k, b in enumerate(FW3):
        ax.plot(j + (k - 1) * 0.2, AV[(g, b)], marker="D" if g in ("r6", "r7") else "s", color=C["FGO"], ms=8 if g in ("r6", "r7") else 8.5,
                ls="none", zorder=4)
label_val(ax, 3.5, 0.025, f"FGO, all rungs: {VFA} m", ha="center", va="top", fontsize=12, color=C["FGO"])
ax.set_xticks(range(8)); ax.set_xticklabels([T(f"{g}\n{RL[g]}") for g in RUNG], fontsize=10.5)
ax.grid(axis="x", visible=False); ax.set_ylabel("Fitted cruise error (m)")
lg = AX(0.73, 0.25, 0.03); lg.axis("off")
lg.legend(handles=[Line2D([], [], ls="none", marker="s", color=C["FGO"], ms=10, label="FGO, Gaussian\n(one mark per flight)"),
                   Line2D([], [], ls="none", marker="D", color=C["FGO"], ms=9, label="FGO, robust weighting\nreplacing the heading\ngate"),
                   Patch(facecolor=C["UKF"], alpha=0.35, label="UKF (stored), the\nsame 3 flights")],
          frameon=False, loc="upper left", labelspacing=0.8, borderaxespad=0.0)
VT = f"Verdicts (exploratory): P1 {VP1}; P2 {VP2.replace('/', ' of ').replace('PASS ', 'PASS, ')}; P3 {VP3} (confounded with removing the heading gate)."
lg.text(0, 0.0, wrap(T(VT), 29), fontsize=11.5, va="bottom", weight="bold", linespacing=1.2, transform=lg.transAxes)
foot(fig, meta,
     "fitted cruise position error of the FGO with the camera heading, 3 painted-line-wall flights, metres; r0 = the thesis FGO.",
     "own pre-registration: P2 passes if r3 (a one-keyframe window) keeps at least half of the FGO's advantage over the UKF on each "
     "flight; P1 and P3 compare rungs with r0 against a noise band.",
     PARA)
finish(fig, meta)
for p in PAGES[EXT_FIRST:]:
    print(f"   extension page {p['id']}: footer top {p['top']!r}")

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

# ------------------------------------------------------------------ the section page opening the extension experiments (2026-10-25)
PAGE = "ext"; TXT = []
SEC_TITLE = "Extension experiments (pre-registered)"
figx = plt.figure(figsize=(PAGE_W, PAGE_H))
figx.text(0.045, 0.62, SEC_TITLE, fontsize=26, weight="bold", va="bottom")
x_e = disp("the four extension experiments", "E2–E5", [("PR", "# Extension experiments E2–E5: pre-registration")])
disp("offline replays only, no new flights", "replays of recordings that already exist", [("PR", "Offline only: replays of recordings that already exist")])
disp("the ablation is exploratory, not a thesis hypothesis test", "This is not a thesis hypothesis test", [("APR", "**EXPLORATORY.** This is not a thesis hypothesis test.")])
x_e6 = disp("E6, pre-registered separately", "E6", [("E6PR", "# E6: map reuse")])
disp("E6 flew new mapping flights (figures of eight) and replays the recorded tag-room flights", "out-of-sample figures of eight",
     [("E6", "out-of-sample figures of eight on a different route")])
SEC_PARAS = [f"These four experiments ({x_e}) were added after the main experiments. Each one, with its pass rules, was written down "
             "and signed off before it was run. They replay flights already recorded in the room with tags: nothing was flown again.",
             f"{x_e6} (map reuse) was pre-registered later, on its own, before any of its runs. It flew three new mapping flights "
             "(figures of eight, a different route) and then replays the recorded tag-room flights on the maps they produced.",
             "The last page is an ablation, and it is EXPLORATORY: it is not a thesis hypothesis. It has its own pre-registration, signed "
             "off before it was run, and it replays the corridor flights recorded with the forward camera.",
             "Verdicts are printed with the words recorded for them: PASS = the registered rule was met; FAIL = the registered rule was "
             "tested and not met. DESCRIPTIVE = shown, not tested."]
yy_ = 0.56
for s_ in SEC_PARAS:
    t_ = wrap(T(s_), 96); figx.text(0.045, yy_, t_, fontsize=14, va="top", linespacing=1.3, color=INK2 if s_ is SEC_PARAS[-1] else INK)
    yy_ -= 0.0325 * (t_.count("\n") + 1) + 0.025
assert yy_ > 0.05, "section page overflows"
_allowed = set()
for c in CHK:
    if c["page"] == PAGE and c["ok"]:
        _allowed |= set(NUMTOK.findall(c["computed"])) | set(NUMTOK.findall(c["expected"]))
_stray = sorted({t for s_ in TXT for t in NUMTOK.findall(s_)} - _allowed)
assert not _stray, f"section page: number(s) {_stray} printed without a check"
figx.savefig(os.path.join(OUT, "summary_ext_section.png"), dpi=150)

figc = plt.figure(figsize=(PAGE_W, PAGE_H))
figc.text(0.045, 0.945, "Experiment summary pages: contents", fontsize=21, weight="bold", va="top")
figc.text(0.045, 0.88, "One page per experiment, in experiment order. The detailed thesis tables are unchanged and separate.",
          fontsize=14, va="top", color=INK2)
# rows: how-to, the main pages, the section page, the extension pages (re-laid out 2026-10-25 to fit them: step 0.0355, 12.5 pt)
rows_c = [("", "How to read these pages", False)] + [(str(i + 1), p["title"], False) for i, p in enumerate(PAGES[:EXT_FIRST])] + \
         [("", SEC_TITLE, True)] + [(str(i + 1), p["title"], False) for i, p in enumerate(PAGES) if i >= EXT_FIRST]
CSTEP = 0.034   # 0.0355 until 2026-11-02; one more row (page 21, D110)
for i, (n, t, hd) in enumerate(rows_c):
    yc = 0.80 - i * CSTEP - (0.008 if i > EXT_FIRST else 0)
    figc.text(0.07, yc, n, fontsize=12.5, va="top", ha="right", color=INK2)
    figc.text(0.09 if not hd else 0.045, yc, t, fontsize=12.5 if not hd else 13.5, va="top", weight="bold" if hd else "normal")
    figc.text(0.95, yc, f"page {i + 2}", fontsize=12, va="top", ha="right", color=INK2)
assert 0.80 - (len(rows_c) - 1) * CSTEP - 0.008 > 0.04, "contents page overflows"
figc.savefig(os.path.join(OUT, "summary_00_contents.png"), dpi=150)
with PdfPages(PDF) as pdf:
    for f in [figc, fig0] + [p["fig"] for p in PAGES[:EXT_FIRST]] + [figx] + [p["fig"] for p in PAGES[EXT_FIRST:]]:
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
      "**Combined PDF:** `summary_plots.pdf` = contents page, 'How to read these pages', then the pages below in experiment order; pages 13–20 "
      "follow a section page `summary_ext_section.png` headed 'Extension experiments (pre-registered)' (added 2026-10-25; page 19 is the "
      "EXPLORATORY ablation, under the same heading but labelled as exploratory, and is printed last; page 20, E6, added 2026-11-02, is printed between 18 and 19). The contents page is also saved as `summary_00_contents.png`. "
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
       "09": "H4.1 primary PASS 3/3, H4.2 NOT MET, H4.3 PASS (Table 5.1, Table 7.3); EKF3's 4.10 m return jump (Table 7.2) not shown",
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
HYP.update({
    "13": "EXTENSION EXPERIMENT, PRE-REGISTERED (tier1/preregistration.md §1). H-E2.1 (primary) PASS 3/3 in B, C and D; H-E2.2, H-E2.3, P-E2.4 "
          "PASS 3/3 in each; P-E2.5 FAIL (A ≤ B false). Sources: scores/E2_T_<c>_r<i>.json (lap-5 live and hindsight, per_lap_rmse_m[4]), "
          "scores/E2_verdicts.json (criteria, P-E2.5 means), eval/results/expL/T_A_r<i>_t245.json for the 8-tag (A) values (as P-E2.5 uses "
          "them). Hindsight lap-5 values are plotted, not printed (no display file shows them). Condition D is degenerate (known map, one tag). "
          "Known-map ratios (DESCRIPTIVE), invariants and wall times not shown",
    "14": "EXTENSION EXPERIMENT, PRE-REGISTERED (§2). Per-run outcome from scores/E3_verdicts.json:runs (run_status.diverged; lc live rmse_m "
          "of the finished runs). 'Collapsed' is DESCRIPTIVE (decision D49): exactly the runs e3_results.md groups as collapsed (every "
          "non-diverged arm (a) run, §3; the robust T_A_r2 5% s1, §4); no per-run collapse flag is stored and no threshold is invented. The plain runs' maps ended shrunk (consistent with a least-squares compromise, §3/§7.4); the robust run's map ended folded, read in §7.4 as a wrong basin, not a cheaper compromise. The "
          "grey band is the stored no-LC live RMSE of T_A_r1-r3 (E3_verdicts.json:references). Diverged runs are drawn in a separate band "
          "with no y value. The map-collapse figure (tier1/figs/e3_collapse_maps.png) is placed in the results walkthrough, not here",
    "15": "EXTENSION EXPERIMENT, PRE-REGISTERED (§2). All registered E3 verdicts from E3_verdicts.json:criteria_a / criteria_b, recorded words "
          "(PASS / FAIL). P-E3b.1's 6 'SATISFIED, flagged' runs (user ruling 2026-10-23) are stated. Runtime ratios (DESCRIPTIVE) not shown",
    "16": "EXTENSION EXPERIMENT, PRE-REGISTERED (§3). P-E4.1 PASS 12/12, P-E4.2 PASS (12/12 at 0.25, 1, 2, 5 s; 0.5 s descriptive, 12/12 ≤ 33 ms). "
          "Values: E4_verdicts.json:P-E4.1.per_flight.<t>.medians_after_anchor_ms (DIAGNOSTIC workstation timing). Linear axes; the x axis is "
          "the window in s to scale. All-keyframe medians and p95 not shown",
    "17": "EXTENSION EXPERIMENT, PRE-REGISTERED (§3). H-E4.3 FAIL 7/12 (band ≥ 10/12). Plotted: the change from the 0.25 s value, scores/E4_<trial>_w<W>.json tracks 'FGO live' horiz_err_m.rmse minus the same at W = 0.25 s, cap-2 runs only (the _lm10 files are not read); the w0.25 and w5 values asserted equal to E4_verdicts.json:H-E4.3.per_flight.<t>.L0.25_m / L5_m on 12/12, and every plotted value at 4 dp equal to its e4_results.md table cell. One panel per tag count on one shared y-scale; windows evenly spaced, not to scale (D57); flights nudged sideways by ±0.12 of a window step (D58). panel-title ranges at 4 dp as e4_results.md prints them (D59); the Result's three bounds are from the stored jsons only (D60). LM cap check (D12): 0 of 10 runs flagged; the RMS readings are not printed. Gain fractions (DESCRIPTIVE) not shown. Replaces the L(5) − L(0.25) plot of D51 (2026-10-27)",
    "21": "EXTENSION EXPERIMENT E4, DESCRIPTIVE page added 2026-11-02 (user request; D110): no registered measure and no new verdict. Plotted: x = E4_verdicts.json:P-E4.1.per_flight.<t>.medians_after_anchor_ms (DIAGNOSTIC workstation timing), y = the cap-2 score files read for page 17 (tracks 'FGO live' horiz_err_m.rmse), each point one flight at one window, joined in window order; linear axes from 0. H-E4.3 is quoted as on page 17. Printed after page 17.",
    "18": "EXTENSION EXPERIMENT, PRE-REGISTERED (§4). The UKF here is the UKF WITH LANDMARK STATES (E5), not the UKF used in the other "
          "experiments. H-E5.1 (primary), H-E5.2, H-E5.3, P-E5.4 PASS 3/3; S-E5.5, S-E5.6 (secondary, registered direction) PASS 3/3. S-E5.6's FGO "
          "side is the Experiment 3 iSAM2 hindsight (whole graph after 5 extra updates), not an LM batch, as e5_results.md states. Values: "
          "scores/e5_T_A_r<i>.json and e5_verdicts.json (FGO values asserted equal to eval/results/expL). Validation gates V-E5a/b/c not shown",
    "20": "EXTENSION EXPERIMENT E6, PRE-REGISTERED (2026-10-31; tier1/e6_preregistration.md), added to the summary 2026-11-02 (user answer 5). "
          "Placed after E5 and before the ablation; id 20 so no existing page is renumbered. Values: scores/e6_T_A_r{1,2,3}.json and "
          "e6_verdicts.json (lap-1 and overall live RMSE, world frame, no alignment; the P2 bands p2_bands_m). Metric and Pass rule are "
          "pre-registration fragments, word for word with markdown bold removed (each a rule row); the Result is the verdicts as worded "
          "(P2-P4 per estimator, no pooling). Live tracks only: the hindsight tracks carry no verdict, and in hindsight the FGO's own "
          "online map (arm iv) beat both fixed-map batches on 3/3 flights (e6_results.md §4, not shown). The 'map quality, not estimator, "
          "decided P3' note is DESCRIPTIVE over 3 flights (per-flight P1 = P3 (FGO) = P3 (UKF) = no, yes, yes; on r1b the two maps differ by "
          "0.0007 m). 'FGO map' names the map's source, 'FGO estimator' the estimator that flies on it",
    "19": "EXPLORATORY ABLATION: not a thesis hypothesis; its own pre-registration (ablation/preregistration.md, signed off 2026-10-24). Values: "
          "docs/thesis/ablation/ablation_results.json runs.<rung>.fwdc_tex_r1-r3.heading.ate_a_cruise_m (evo -a (cruise)) and stored.<bag>.U_heading. "
          "Verdicts P1 FAIL, P2 PASS 3/3, P3 FAIL (confounded with gate removal). The Result line is the ruled discussion paragraph "
          "(discussion_material.md §1), extracted at build time and asserted verbatim; its three numbers are re-derived from "
          "ablation_results.json. Plain-wall bags, control rows, the retention ladder R, r6s (stored Cauchy) and step times not plotted "
          "(decision D53). D46 ('tables only') is superseded by the user's request of 2026-10-25"})
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
