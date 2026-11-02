#!/usr/bin/env python3
"""RESULTS WALKTHROUGH, COMPOSITE FIGURES (2026-10-29): the two new figures of the restructured
docs/thesis/summary/results_walkthrough.pdf that no existing generator draws. Composed into the walkthrough by
eval/figs_results_walkthrough.py. CPU-light: stored result files only, no estimator run, no simulation, no bag read.

User request (verbatim, 2026-10-29, the parts this script implements):
  "Exp 5: merge hold error and hidden-tag drift into one two-panel figure."
  "TASK 2: Redesign the Extension E4 figures (longer FGO window) ... Build one two-panel figure:
   - Left panel: window length against median compute time per step (box = lowest to highest over 12 flights). Linear y-axis, no
     log scale. Draw the 33 ms budget line prominently. Label values directly on the boxes.
   - Right panel: absolute live horizontal RMSE per flight, with a line joining each flight's 0.25 s value to its 5 s value (12
     lines). Linear y-axis starting at zero so the flatness is not exaggerated. Use the same x positions as the left panel where
     possible.
   - X-axis: treat window length as equally spaced categorical positions (0.25, 0.5, 1, 2, 5 s) and add the caption note 'windows
     not to scale'.
   - If per-flight live error exists for the intermediate windows (0.5, 1, 2 s), include those points on the right panel. ...
   - Caption: state the trade-off plainly ..."
General rules: linear axes only, direct value labels, large fonts, consistent y-scales within a comparison, no em-dashes,
Australian English.

Figures (docs/thesis/summary/extra/):
  ex_5_hold_drift.png  Experiment 5: mean hold error (left) and worst drift while the tag was hidden (right), both in mm
                       (docs/thesis/units.md), ONE shared linear y-scale 0-60 mm (sharey, asserted), the 50 mm limit on each.
                       Same loaders and expected strings as eval/figs_thesis_summary.py pages 10 and 11 (COPIED, not imported:
                       importing would rewrite the summary outputs).
  ex_E4_tradeoff.png   E4: median step time per window (left, ms) and FGO live horizontal RMSE per flight at every window
                       (right, m, from 0), the windows at evenly spaced positions 0-4 on both panels. The two panels hold
                       different quantities side by side, as the user asked (stated in the index and the handover).

Checks (exact): every number printed on a figure is rounded ONCE by rd() (parsed from eval/figs_thesis.py, sha asserted) from the
stored value and must equal, as a string, the value typed from the thesis display it appears in (shown-in strings asserted in that
file), and where summary pages 10, 11, 16 or 17 print the same quantity, the computed string of that page's check row in
docs/thesis/summary/index_summary.md. Outputs: the PNGs, docs/thesis/summary/extra/index_extra.md, docs/thesis/summary/extra/checks.json.
Usage: python3 eval/figs_walkthrough_extra.py   (numpy, matplotlib)"""
import ast, hashlib, json, os, re, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results"); T1D = os.path.join(ROOT, "docs", "thesis", "tier1")
OUTD = os.path.join(ROOT, "docs", "thesis", "summary", "extra"); os.makedirs(OUTD, exist_ok=True)
INDEX = os.path.join(OUTD, "index_extra.md")
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
L = lambda f: json.load(open(os.path.join(RES, f)))
LT = lambda f: json.load(open(os.path.join(T1D, "scores", f)))

# ------------------------------------------------------------------ rd(): the thesis rounding rule, parsed (not run) from figs_thesis.py
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read()
_rd = next(n for n in ast.parse(_src).body if isinstance(n, ast.FunctionDef) and n.name == "rd")
RD_SHA = hashlib.sha256(ast.get_source_segment(_src, _rd).encode()).hexdigest()
_ns = {}; exec(compile(ast.Module(body=[_rd], type_ignores=[]), FT, "exec"), _ns); rd = _ns["rd"]
assert RD_SHA == "e7320d3b8f377157c0c6512b2c0b77c978ac309a7130d2729480b786e02589b3", "rd() changed in figs_thesis.py"


def rng(vals, n=2):
    return f"{rd(min(vals), n)}–{rd(max(vals), n)}"


def rd_si(v, n, k=0):
    """COPIED from eval/figs_thesis_summary.py: rd() of the stored value shifted exactly by 10**k (k = 3: stored m -> mm)."""
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(str(float(v))).scaleb(k).quantize(Decimal(1).scaleb(-int(n)), rounding=ROUND_HALF_UP)
    out = format(d, "f")
    return out[1:] if out.startswith("-") and d == 0 else out


def rng_si(vals, n, k=0):
    return f"{rd_si(min(vals), n, k)}–{rd_si(max(vals), n, k)}"


def si_str(s_, k):
    from decimal import Decimal
    return re.sub(r"\d+(?:\.\d+)?", lambda m_: format(Decimal(m_.group(0)).scaleb(k), "f"), s_)


# ------------------------------------------------------------------ style (Okabe-Ito, fixed per estimator; >= 11 pt everywhere)
C = {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"}
GREY = "#999999"; INK = "#111111"; INK2 = "#444444"; GRID = "#e6e6e6"
EST = ("EKF3", "UKF", "FGO")
TICK = {"EKF3": "EKF3\n(ArduPilot's\nstandard filter)", "UKF": "UKF\n(unscented\nKalman filter)", "FGO": "FGO\n(factor-graph\noptimiser)"}
plt.rcParams.update({"font.size": 13, "axes.titlesize": 14, "axes.labelsize": 13, "xtick.labelsize": 12.5, "ytick.labelsize": 12.5,
                     "legend.fontsize": 12, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
FW, FH, DPI = 10.9, 5.3, 200      # the walkthrough's plot box (in), drawn at 200 dpi so it is placed at about its own size

# ------------------------------------------------------------------ checks
DISPF = {"T1": "docs/thesis/tables/T1_scorecard.md", "T5": "docs/thesis/tables/T5_H_tag_loss_drift.md",
         "E4": "docs/thesis/tier1/e4_results.md", "PR": "docs/thesis/tier1/preregistration.md", "M": "METHODOLOGY.md",
         "T8": "docs/thesis/tables/T8_hindsight_ratio.md", "IS": "docs/thesis/summary/index_summary.md"}
_TX = {}
IDXS = open(os.path.join(ROOT, "docs", "thesis", "summary", "index_summary.md")).read()
CHK = []; FIGS = {}; TXT = []


def _text(k):
    return _TX.setdefault(k, open(os.path.join(ROOT, DISPF[k])).read())


def sumrow(page, label):
    """The computed string of summary page `page`'s check row whose label is exactly `label` (index_summary.md)."""
    sec = IDXS[IDXS.index(f"## Page {page}:"):]; sec = sec[:sec.find("\n## Page ", 5)]
    rows = [r for r in sec.split("\n") if r.startswith(f"| number | {label} |") or r.startswith(f"| display | {label} |")
            or r.startswith(f"| count | {label} |")]
    assert len(rows) == 1, f"summary page {page}: check row '{label}' found {len(rows)} times"
    assert rows[0].rstrip().endswith("| yes |"), f"summary page {page}: check row '{label}' did not pass"
    return re.findall(r"`([^`]*)`", rows[0])[0]


def check(fig, label, computed, expected, src, shown=(), summ=None):
    """EXACT string equality of the computed string with the expected one; every (display key, string) in `shown` must occur in that
    display file; summ = (summary page, check label): the summary page's check row must carry the same computed string."""
    c, e = str(computed), str(expected); ok = c == e; where = [src]
    for k, s_ in shown:
        f = s_ in _text(k); ok &= f; where.append(f"{DISPF[k]} shows '{s_}'" + ("" if f else " [NOT FOUND]"))
    if summ:
        sv = sumrow(*summ); f = sv == c; ok &= f
        where.append(f"index_summary.md page {summ[0]} row '{summ[1][:60]}' = '{sv}'" + ("" if f else " [DIFFERS]"))
    CHK.append(dict(fig=fig, label=label, computed=c, expected=e, where="; ".join(where), ok=ok))
    if not ok:
        print("   CHECK FAIL:", fig, label, repr(c), repr(e), where)
    return c


def T(s):
    TXT.append(s); return s


NUMTOK = re.compile(r"\d+(?:\.\d+)?")


def save(fid, fig, inputs, tag=None, key=False):
    """Number guard: every number drawn on the figure (TXT) must occur in a passing check of this figure. v3 (2026-10-31): tag = the
    raw / fitted tag drawn on the figure (None: the composer draws it), key = the figure carries the filled / open key; every axis
    linear (asserted); text measured at the saved dpi."""
    allowed = set()
    for c in CHK:
        if c["fig"] == fid and c["ok"]:
            allowed |= set(NUMTOK.findall(c["computed"])) | set(NUMTOK.findall(c["expected"]))
    stray = sorted({t for s in TXT for t in NUMTOK.findall(s.replace("EKF3", "EKF"))} - allowed)
    assert not stray, f"{fid}: number(s) {stray} drawn without a check"
    for s in TXT:
        assert "—" not in s, f"{fid}: em-dash in '{s}'"
    for a_ in fig.axes:
        assert a_.get_xscale() == "linear" and a_.get_yscale() == "linear", f"{fid}: a non-linear axis"
    fig.set_dpi(DPI); fig.canvas.draw(); r_ = fig.canvas.get_renderer(); W_, H_ = fig.bbox.width, fig.bbox.height
    ticks_ = {id(t) for a_ in fig.axes for t in a_.get_xticklabels() + a_.get_yticklabels()}
    for t_ in fig.findobj(matplotlib.text.Text):
        assert "—" not in t_.get_text(), f"{fid}: em-dash in figure text"
        if t_.get_text() and t_.get_visible() and id(t_) not in ticks_:
            b_ = t_.get_window_extent(renderer=r_)
            assert b_.x0 >= -1 and b_.x1 <= W_ + 1 and b_.y0 >= -1 and b_.y1 <= H_ + 1, f"{fid}: text runs off the figure: {t_.get_text()[:50]!r}"
    p = os.path.join(OUTD, f"ex_{fid}.png"); fig.savefig(p, dpi=DPI); plt.close(fig)
    FIGS[fid] = dict(file=os.path.relpath(p, ROOT), inputs=inputs, numbers=sorted(allowed & {t for s in TXT for t in NUMTOK.findall(s)}),
                     text=list(TXT), tag=tag, key=key)
    print(f"wrote ex_{fid}.png")


# =================================================================== v3 (2026-10-31): redrawn summary charts, self-explanatory
# User request 2026-10-31 ("SELF-EXPLANATORY PLOTS"; TASK 4, 5, 6): one-line finding title, direct labels instead of legends, the
# registered verdict printed on the data (each equal to the summary page's check row), the raw / fitted tag and, where filled and open
# marks are both used, the key "filled = live (during flight), open = hindsight (after landing)". Loaders and expected strings COPIED
# from eval/figs_thesis.py (F5, F7) and eval/figs_thesis_summary.py (pages 13, 14, 18); those scripts and their outputs are untouched.
DISPF.update({"FI": "docs/thesis/figures_thesis/index.md", "N": "docs/thesis/numbers.md", "E2": "docs/thesis/tier1/e2_results.md",
              "E3": "docs/thesis/tier1/e3_results.md", "E5": "docs/thesis/tier1/e5_results.md"})
KEY_LH = "filled = live (during flight), open = hindsight (after landing)"
SURF = "white"
MK = {"EKF3": "o", "UKF": "^", "FGO": "s"}


def title1(fig, text, x=0.01, y=0.985, fs=13.5):
    """One-line finding title, asserted to fit inside the figure on one line."""
    assert "\n" not in text
    T(text)
    while True:                         # shrink the font (not below 11 pt) until the one line fits, with a 3% margin
        t_ = fig.text(x, y, text, fontsize=fs, weight="bold", ha="left", va="top")
        fig.canvas.draw(); bb = t_.get_window_extent(renderer=fig.canvas.get_renderer())
        if bb.x1 <= fig.bbox.x1 * 0.97:
            return t_
        t_.remove(); fs -= 0.5
        assert fs >= 11, f"title does not fit on one line: {text}"


def corner(fig, tag, key=None, y=0.925):
    fig.text(0.99, y, T(tag), fontsize=11, ha="right", va="top", color=INK, bbox=dict(boxstyle="round,pad=0.3", fc="#f2f2f2", ec="#bbbbbb", lw=0.6))
    if key:
        fig.text(0.01, y, T(key), fontsize=11, ha="left", va="top", color=INK, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bbbbbb", lw=0.6))


def rbox(ax, x, vals, col, filled, w=0.3):
    """Box = lowest to highest of the flights (filled = live, open = hindsight); a minimum visible height."""
    lo, hi = min(vals), max(vals); yl = ax.get_ylim(); h = max(hi - lo, 0.012 * (yl[1] - yl[0]))
    ax.add_patch(Rectangle((x - w / 2, lo - (h - (hi - lo)) / 2), w, h, facecolor=col if filled else "white", edgecolor=col, lw=2.0, zorder=3))
    return lo - (h - (hi - lo)) / 2 + h


def mark(ax, x, y, text, **kw):
    """A verdict mark drawn next to the data (bold)."""
    kw.setdefault("fontsize", 11.5); kw.setdefault("weight", "bold"); kw.setdefault("ha", "left"); kw.setdefault("va", "center")
    return ax.text(x, y, T(text), **kw)


VERD = {"PASS": "PASS", "FAIL": "NOT MET"}     # check-row token -> the registered Result wording where the Result says NOT MET


# =================================================================== Experiment 5: hold error and drift while the tag is hidden
# Loaders COPIED from eval/figs_thesis_summary.py pages 10 and 11.
TXT = []
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = ["s2v2_r1", "s2v2_r2", "s2v2_r3"]; S3V = ["s3v2_r1", "s3v2_r2", "s3v2_r3"]
FLY = {"EKF3": (S1 + S1F, "EKF3"), "UKF": (S2V, "UKF_port"), "FGO": (S3V, "FGO_flying")}
BAND = {"EKF3": [50, 100, 200, 150], "FGO": [50, 100, 200, 150], "UKF": [100, 200, 400, 300]}
_hc = [v for k, v in L("expH/h_comparative_2026-10-11.json")["sets"].items() if k.startswith("re-flown")][0]
HV = {"EKF3": [np.mean([w["mean_m"] for w in HJ(t)["hold_windows_vehicle"]]) for t in S1F],
      "UKF": [r["hold_mean_mm"] for r in _hc["UKF"]], "FGO": [r["hold_mean_mm"] for r in _hc["FGO"]]}
HK = {"EKF3": 3, "UKF": 0, "FGO": 0}                     # exact decimal shift to mm (EKF3 stored in m)
VH = {e: check("5_hold_drift", f"{e}: mean hold error, range over 3 flights (mm)", rng_si(HV[e], 1, HK[e]), x,
               "eval/results/expH (hold_windows_vehicle; h_comparative_2026-10-11.json)", [("T1", f"hold {x} mm")],
               ("10", f"{e}: mean hold error, range over 3 flights (mm)"))
      for e, x in zip(EST, ("7.8–7.9", "6.4–7.1", "8.3–8.6"))}
HVM = {e: max(float(rd_si(v, 12, HK[e])) for v in HV[e]) for e in EST}          # mm, the highest flight, for drawing only
check("5_hold_drift", "flights per estimator", "/".join(str(len(HV[e])) for e in EST), "3/3/3", "S1 far r1-r3b, S2v2 r1-r3, S3v2 r1-r3",
      summ=("10", "flights per estimator"))
HLIM = check("5_hold_drift", "hold limit for the mean (mm) = the registered '≤ 0.05 m' (METHODOLOGY.md:10687) × 10^3, exact",
             si_str("0.05", 3), "50", "METHODOLOGY.md:10687", [("M", "mean hold error ≤ 0.05 m and max ≤ 0.15 m")])
worstm = {e: max(lo[FLY[e][1]]["effective"]["drift_m"] for t in FLY[e][0] for lo in HJ(t)["losses"]) for e in EST}
wli = {e: max(range(4), key=lambda li: max(lo[FLY[e][1]]["effective"]["drift_m"] for t in FLY[e][0] for lo in [HJ(t)["losses"][li]]))
       for e in EST}
VW = {e: check("5_hold_drift", f"{e}: worst drift over all tag losses (mm)", rd_si(worstm[e], 0, 3), x, "eval/results/expH losses[].effective.drift_m",
               [("T5", f"{x} / {BAND[e][wli[e]]}")], ("11", f"{e}: worst drift over all tag losses (mm)"))
      for e, x in zip(EST, ("31", "26", "27"))}
LK = {e: [bool(lo[FLY[e][1]]["lockout"]) for t in FLY[e][0] for lo in HJ(t)["losses"]] for e in EST}
VN = {e: check("5_hold_drift", f"{e}: losses with a lockout / losses", f"{sum(LK[e])} / {len(LK[e])}", x, "eval/results/expH losses[].lockout",
               [("T5", x)], ("11", f"{e}: losses with a lockout / losses"))
      for e, x in zip(EST, ("0 / 24", "0 / 12", "0 / 12"))}
DLIM = check("5_hold_drift", "tightest drift limit for EKF3 and the FGO (mm)", "50 / 200".split(" / ")[0], "50", "Table 6.1",
             [("T5", "EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm")])
check("5_hold_drift", "experiment number in the title", "5", "5", "summary page 10 title", [("IS", "## Page 10: Experiment 5:")])
YL5 = (0, 60)
assert max(HVM.values()) < YL5[1] and max(float(rd_si(worstm[e], 12, 3)) for e in EST) < YL5[1]
check("5_hold_drift", "y-axis: both panels, linear, mm, upper limit", "0 to 60", "0 to 60", "this script (sharey, asserted)")
check("5_hold_drift", "tag losses printed on the bars", " / ".join(VN[e].split(" / ")[1] for e in EST), "24 / 12 / 12", "Table 6.1 (lockout column)")

fig, (axl, axr) = plt.subplots(1, 2, figsize=(FW, FH), sharey=True)
for ax in (axl, axr):
    ax.set_xlim(-0.5, 2.5); ax.set_ylim(*YL5); ax.grid(axis="x", visible=False)
    ax.set_xticks(range(3)); ax.set_xticklabels([TICK[e] for e in EST], fontsize=11.5)
    ax.axhline(50, color=GREY, ls=(0, (6, 4)), lw=1.8, zorder=1)
for i, e in enumerate(EST):
    axl.bar(i, HVM[e], width=0.62, color=C[e], zorder=3)
    axl.text(i, HVM[e] + 1.2, T(f"{VH[e]} mm"), ha="center", va="bottom", fontsize=12.5, weight="bold")
    wmm = float(rd_si(worstm[e], 12, 3))
    axr.bar(i, wmm, width=0.62, color=C[e], zorder=3)
    axr.text(i, wmm + 1.2, T(f"{VW[e]} mm"), ha="center", va="bottom", fontsize=12.5, weight="bold")
    axr.text(i, 2.5, T(f"{VN[e].split(' / ')[1]}\ntag losses"), ha="center", va="bottom", fontsize=11, color="white", weight="bold")
axl.text(2.45, 50.6, T(f"limit for the mean: {HLIM} mm"), ha="right", va="bottom", fontsize=12, color="#555555")
axr.text(2.45, 50.6, T(f"tightest limit: {DLIM} mm"), ha="right", va="bottom", fontsize=12, color="#555555")
axl.set_ylabel("millimetres (mm), linear, the same\nscale in both panels")
axl.set_title(T("Holding still: mean hold error per flight\n(bar = highest of 3 flights; label = lowest–highest)"), loc="left", fontsize=13)
axr.set_title(T("Tag hidden: worst drift over all tag losses\n(bar = the worst loss)"), loc="left", fontsize=13)
# v3 (2026-10-31): the registered verdict on each bar (summary pages 10 and 11 check rows), one-line finding title, raw tag on the figure
VHV = check("5_hold_drift", "hold accuracy verdict as recorded: EKF3 first hold flights / FGO", "PASS / PASS", "PASS / PASS", "summary page 10",
            summ=("10", "hold accuracy verdict as recorded: EKF3 first hold flights / FGO"))
VDI = check("5_hold_drift", "every drift inside its limit (and 0 refusals: the lockout counts above)", "True", "True", "summary page 11",
            summ=("11", "every drift inside its limit"))
HMK = {"EKF3": f"{VHV.split(' / ')[0]}*", "UKF": "inside,\nno recorded\nverdict", "FGO": VHV.split(" / ")[1]}
for i, e in enumerate(EST):
    axl.text(i, 22, T(HMK[e]), ha="center", va="bottom", fontsize=11.5, weight="bold", linespacing=1.05)
    axr.text(i, max(float(rd_si(worstm[e], 12, 3)), 0) + 7.5, T("PASS" if VDI == "True" and VN[e].startswith("0 /") else "NOT MET"), ha="center",
             va="bottom", fontsize=11.5, weight="bold")
axl.text(-0.45, 57.5, T("* registered on EKF3's first hold flights"), fontsize=10.5, color=INK2, va="center")
fig.subplots_adjust(left=0.1, right=0.99, top=0.76, bottom=0.2, wspace=0.12)
title1(fig, f"All three estimators held the drone well inside the {HLIM} mm limits, at rest and with the tag hidden")
corner(fig, "raw: the drone's real position, nothing fitted")
save("5_hold_drift", fig, "eval/results/expH/{s1far_r1,s1far_r2,s1far_r3b,s1_r1..r3,s2v2_r1..r3,s3v2_r1..r3}.json, "
     "eval/results/expH/h_comparative_2026-10-11.json; verdicts index_summary.md pages 10 and 11", tag="raw: the drone's real position, nothing fitted")

# =================================================================== E4: the compute / accuracy trade-off of a longer FGO window
TXT = []
TCOND = "ABCD"; TAGS = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
FLT = [f"T_{c}_r{i}" for c in TCOND for i in (1, 2, 3)]
E4V = LT("E4_verdicts.json"); WS = [0.25, 0.5, 1, 2, 5]; WK = ["0.25", "0.5", "1", "2", "5"]
MED4 = {w: [E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][i] for t in FLT] for i, w in enumerate(WS)}
EXP4 = {0.25: "14.35–15.13", 0.5: "26.86–28.22", 1: "50.47–52.74", 2: "100.05–107.12", 5: "278.25–303.36"}
V4S = {w: check("E4_tradeoff", f"W = {w} s: median step time after the anchor, lowest–highest over 12 flights (ms)", rng(MED4[w], 2), EXP4[w],
                "E4_verdicts.json P-E4.1.per_flight.<t>.medians_after_anchor_ms", [("E4", x) for x in EXP4[w].split("–")],
                ("16", f"W = {w} s: median step time after the anchor, lowest–highest over 12 flights (ms)"))
       for w in WS}
check("E4_tradeoff", "windows (s)", " / ".join(WK), "0.25 / 0.5 / 1 / 2 / 5", "pre-registration", [("PR", "0.25 < 0.5 < 1 < 2 < 5 s")],
      ("16", "windows swept (s)"))
BUD = check("E4_tradeoff", "deployability budget (ms)", "33", "33", "pre-registration P-E4.2",
            [("PR", "the 33 ms deployability budget (M:707-721)")])
check("E4_tradeoff", "flights per window", "/".join(str(len(MED4[w])) for w in WS), "12/12/12/12/12", "E4_verdicts.json P-E4.1 per_flight",
      summ=("16", "flights per window"))
p41, p42 = E4V["P-E4.1"], E4V["P-E4.2"]
VP41 = check("E4_tradeoff", "P-E4.1 verdict and count", f"{p41['verdict']} {p41['count']}", "PASS 12/12", "E4_verdicts.json",
             [("E4", "**P-E4.1 PASS 12/12.**")], ("16", "P-E4.1 verdict and count"))
VP42 = check("E4_tradeoff", "P-E4.2 verdict and counts at 0.25 / 1 / 2 / 5 s", f"{p42['verdict']} " + " ".join(p42["counts"][k] for k in ("0.25", "1", "2", "5")),
             "PASS 12/12 12/12 12/12 12/12", "E4_verdicts.json", [("E4", "0.25 s: 12/12, 1 s: 12/12, 2 s: 12/12, 5 s: 12/12")],
             ("16", "P-E4.2 verdict and counts at 0.25 / 1 / 2 / 5 s"))
# "about 20 times" (user): the per-flight ratio of the 5 s median to the 0.25 s median (after the anchor), lowest-highest over the
# 12 flights, each end rounded ONCE to a whole number. Cross-check: the same range from e4_results.md's printed 2 dp medians.
RAT = [p41["per_flight"][t]["medians_after_anchor_ms"][4] / p41["per_flight"][t]["medians_after_anchor_ms"][0] for t in FLT]
_e4t = _text("E4"); _sec = _e4t[_e4t.index("### Per-step time after the anchor"):]; _sec = _sec[:_sec.index("\n### ", 5)]
RAT_T = []
for t in FLT:
    cells = [c.strip() for c in re.search(rf"^\| {t} \|(.+)$", _sec, re.M).group(1).split("|")]
    RAT_T.append(float(cells[4].split("/")[0]) / float(cells[0].split("/")[0]))
VRAT = check("E4_tradeoff", "5 s / 0.25 s median step time per flight, lowest–highest of 12 (×, whole numbers; json full precision)",
             f"{rd(min(RAT), 0)}–{rd(max(RAT), 0)}", f"{rd(min(RAT_T), 0)}–{rd(max(RAT_T), 0)}",
             "E4_verdicts.json vs the same ratio from e4_results.md's 2 dp table cells")
H43 = E4V["H-E4.3"]


def e4live(t, w):
    tr = LT(f"E4_{t}_w{w}.json")["tracks"]; ks = [k for k in tr if k.startswith("FGO live")]
    assert len(ks) == 1, f"E4_{t}_w{w}.json: FGO live tracks {ks}"
    return tr[ks[0]]["horiz_err_m"]["rmse"]


LW = {t: {w: e4live(t, w) for w in WK} for t in FLT}
check("E4_tradeoff", "score files (cap 2) equal E4_verdicts.json L0.25_m and L5_m on every flight",
      str(all(LW[t]["0.25"] == H43["per_flight"][t]["L0.25_m"] and LW[t]["5"] == H43["per_flight"][t]["L5_m"] for t in FLT)), "True",
      "scores/E4_<trial>_w<W>.json vs E4_verdicts.json", [("E4", "All values come from `scores/E4_verdicts.json`")],
      ("17", "score files (cap 2) equal E4_verdicts.json L0.25_m and L5_m on every flight"))
_E4ROW = {"T_A_r1": "0.0214 | 0.0214 | 0.0214 | 0.0214 | 0.0214", "T_A_r2": "0.0196 | 0.0196 | 0.0196 | 0.0196 | 0.0196",
          "T_A_r3": "0.0190 | 0.0190 | 0.0190 | 0.0190 | 0.0190", "T_B_r1": "0.0233 | 0.0230 | 0.0233 | 0.0232 | 0.0231",
          "T_B_r2": "0.0292 | 0.0292 | 0.0292 | 0.0292 | 0.0292", "T_B_r3": "0.0252 | 0.0252 | 0.0252 | 0.0252 | 0.0252",
          "T_C_r1": "0.0538 | 0.0546 | 0.0542 | 0.0540 | 0.0542", "T_C_r2": "0.0502 | 0.0501 | 0.0495 | 0.0497 | 0.0497",
          "T_C_r3": "0.0565 | 0.0564 | 0.0559 | 0.0561 | 0.0562", "T_D_r1": "0.0931 | 0.0901 | 0.0863 | 0.0890 | 0.0887",
          "T_D_r2": "0.0813 | 0.0814 | 0.0906 | 0.0803 | 0.0798", "T_D_r3": "0.0745 | 0.0743 | 0.0739 | 0.0738 | 0.0738"}
for t in FLT:
    check("E4_tradeoff", f"{t}: plotted live RMSE at W = 0.25 / 0.5 / 1 / 2 / 5 s (m, 4 dp)", " | ".join(rd(LW[t][w], 4) for w in WK), _E4ROW[t],
          f"scores/E4_{t}_w<W>.json tracks 'FGO live' horiz_err_m.rmse", [("E4", f"| {t} | {_E4ROW[t]} |")])
_E4R25 = {"A": "0.0190–0.0214", "B": "0.0233–0.0292", "C": "0.0502–0.0565", "D": "0.0745–0.0931"}
for c in TCOND:
    check("E4_tradeoff", f"{TAGS[c]}: live RMSE at W = 0.25 s, lowest–highest of 3 flights (m)", rng([LW[t]["0.25"] for t in FLT if t[2] == c], 4),
          _E4R25[c], "score files", [("E4", f" {x} |") for x in _E4R25[c].split("–")],
          ("17", f"{TAGS[c]}: live RMSE at W = 0.25 s, lowest–highest of 3 flights (m)"))
    check("E4_tradeoff", f"condition {c}: number of tags", TAGS[c], TAGS[c], "Table 5.2", [("T8", TAGS[c])])
D43 = {t: H43["per_flight"][t]["L5_m"] - H43["per_flight"][t]["L0.25_m"] for t in FLT}
LOW = {t: H43["per_flight"][t]["lower_at_5"] for t in FLT}
VH43 = check("E4_tradeoff", "H-E4.3 verdict and count", f"{H43['verdict']} {H43['count']}", "FAIL 7/12", "E4_verdicts.json",
             [("E4", "**H-E4.3 FAIL 7/12** (band ≥ 10/12)")], ("17", "H-E4.3 verdict and count"))
check("E4_tradeoff", "H-E4.3 flights lower at 5 s (recounted from the stored flags) / higher", f"{sum(LOW.values())} / {12 - sum(LOW.values())}",
      "7 / 5", "E4_verdicts.json H-E4.3.per_flight.<t>.lower_at_5", [("E4", "| **FAIL** | 7/12 |"), ("E4", "On the other five it was higher")])
check("E4_tradeoff", "difference sign agrees with the stored flag on every flight", str(all((D43[t] < 0) == LOW[t] for t in FLT)), "True",
      "E4_verdicts.json")
t_lo = min(FLT, key=lambda t: D43[t]); t_hi = max(FLT, key=lambda t: D43[t])
check("E4_tradeoff", "largest decrease at 5 s (5 s minus 0.25 s, m, 7 dp, unrounded in e4_results.md)", rd(D43[t_lo], 7, sign=True), "-0.0043321",
      f"E4_verdicts.json ({t_lo})", [("E4", "| yes (-0.0043321 m) |")])
check("E4_tradeoff", "largest increase at 5 s (5 s minus 0.25 s, m, 7 dp)", rd(D43[t_hi], 7, sign=True), "+0.0003395",
      f"E4_verdicts.json ({t_hi})", [("E4", "| no (+0.0003395 m) |")])
VDLO = check("E4_tradeoff", "largest decrease at 5 s, printed (m, 4 dp, rounded once)", rd(-D43[t_lo], 4), "0.0043", "E4_verdicts.json")
VDHI = check("E4_tradeoff", "largest increase at 5 s, printed (m, 4 dp, rounded once)", rd(D43[t_hi], 4), "0.0003", "E4_verdicts.json")
YL4 = (0, 0.10)
assert max(max(v.values()) for v in LW.values()) < YL4[1]
check("E4_tradeoff", "right panel y-axis: linear, from 0, upper limit (m)", "0 to 0.10", "0 to 0.10", "this script (asserted above every value)")
check("E4_tradeoff", "left panel y-axis: linear, from 0, upper limit (ms)", "0 to 350", "0 to 350", "this script")
check("E4_tradeoff", "figure counts printed: flights, lines", "12, 12", "12, 12", "E4 runs T_A-D r1-3")

fig, (axl, axr) = plt.subplots(1, 2, figsize=(FW, 5.7), gridspec_kw=dict(width_ratios=[1, 1]))
X = range(5)
# left: compute time
axl.set_xlim(-0.6, 5.0)
for i, w in enumerate(WS):
    lo, hi = min(MED4[w]), max(MED4[w]); hgt = max(hi - lo, 0.012 * 340)
    axl.add_patch(Rectangle((i - 0.2, lo - (hgt - (hi - lo)) / 2), 0.4, hgt, facecolor=C["FGO"], edgecolor=C["FGO"], lw=2.0, zorder=3))
axl.set_ylim(0, 350)
LBL = {0: (0, 44, "center", "bottom"), 1: (0.9, 84, "center", "bottom"), 2: (2.1, 64, "center", "bottom"), 3: (3, 116, "center", "bottom"),
       4: (3.62, 290.8, "right", "center")}
for i, w in enumerate(WS):
    tx, ty, ha, va = LBL[i]; lo, hi = min(MED4[w]), max(MED4[w])
    axl.text(tx, ty, T(V4S[w].replace("–", "–\n") + " ms"), ha=ha, va=va, fontsize=11.5, weight="bold", linespacing=1.05)
    if i < 2:
        axl.plot([i, i], [hi + 2, ty - 1], color="#777777", lw=1.0, zorder=2)
axl.axhline(33, color="#333333", lw=3.0, ls=(0, (6, 3)), zorder=2)
axl.text(4.95, 37, T(f"budget {BUD} ms\n(one camera frame)"), ha="right", va="bottom", fontsize=12, color="#333333", weight="bold")
axl.set_xticks(list(X)); axl.set_xticklabels([T(w) for w in WK]); axl.grid(axis="x", visible=False)
axl.set_ylabel("median compute time per step (ms)")
axl.set_title(T("Compute time: box = lowest to highest of 12 flights"), loc="left", fontsize=13)
# right: absolute live error, one line per flight across every window
axr.set_xlim(-0.6, 5.0); axr.set_ylim(*YL4)
for t in FLT:
    axr.plot(list(X), [LW[t][w] for w in WK], color=C["FGO"], lw=1.4, marker="s", ms=5.5, mfc=C["FGO"], mec=C["FGO"], zorder=3, alpha=0.9)
for c in TCOND:
    ys = [LW[t]["5"] for t in FLT if t[2] == c]
    yl = {"A": min(ys) - 0.0045, "B": max(ys) + 0.0045}.get(c, float(np.mean(ys)))
    axr.text(4.15, yl, T(TAGS[c]), ha="left", va="center", fontsize=12, color=INK2, weight="bold")
axr.set_xticks(list(X)); axr.set_xticklabels([T(w) for w in WK]); axr.grid(axis="x", visible=False)
axr.set_ylabel("FGO live horizontal error, RMSE (m)")
axr.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
axr.set_title(T("Live error: one line per flight (12 lines)"), loc="left", fontsize=13)
for ax in (axl, axr):
    ax.set_xlabel(T("FGO window (s), windows not to scale"))
check("E4_tradeoff", "registered ids printed: P-E4.1, P-E4.2", "P-E4.1 P-E4.2", "P-E4.1 P-E4.2", "pre-registration",
      [("PR", "P-E4.1"), ("PR", "P-E4.2")])
check("E4_tradeoff", "H-E4.3 band printed: at least 10 of 12 flights", "10 of 12", "10 of 12", "e4_results.md", [("E4", "**H-E4.3 FAIL 7/12** (band ≥ 10/12)")])
axl.text(-0.5, 250, T(f"P-E4.1 {VP41.split()[0]} ({VP41.split()[1].replace('/', ' of ')}):\nslower at every longer window"), fontsize=11.5, weight="bold", va="center")
axl.text(-0.5, 190, T(f"P-E4.2 {VP42.split()[0]}: within {BUD} ms\nat 0.25 s, over it from 1 s on"), fontsize=11.5, weight="bold", va="center")
axr.text(-0.5, 0.0445, T(f"H-E4.3 {VH43.split()[0]}: lower at 5 s on {sum(LOW.values())} of 12 flights"), fontsize=11, weight="bold", va="center")
axr.text(-0.5, 0.0375, T(f"(10 of 12 needed; largest change {VDLO} m)"), fontsize=10.5, va="center", color=INK2)
fig.subplots_adjust(left=0.08, right=0.985, top=0.80, bottom=0.14, wspace=0.28)
title1(fig, f"A 5 s FGO window took {VRAT.replace('–', ' to ')} times the compute of 0.25 s and did not improve live accuracy (H-E4.3 FAIL)")
corner(fig, "compute time measured; live error raw, nothing fitted", "filled = live (during flight)")
check("E4_tradeoff", "every flight over the budget at 1 s and above (after-anchor medians > 33 ms)", str(all(min(MED4[w]) > 33 for w in (1, 2, 5))),
      "True", "E4_verdicts.json", [("E4", "and 12/12 at each of 1, 2 and 5 s (> 33 ms)")])
check("E4_tradeoff", "registered id printed: H-E4.3", "H-E4.3", "H-E4.3", "pre-registration", [("PR", "| **H-E4.3** (directional accuracy, amendment 3) |")])
save("E4_tradeoff", fig, "docs/thesis/tier1/scores/E4_verdicts.json (P-E4.1 medians after the anchor, P-E4.2, H-E4.3); "
     "docs/thesis/tier1/scores/E4_<trial>_w<W>.json (cap 2) tracks 'FGO live' horiz_err_m.rmse", tag="compute time measured; live error raw, nothing fitted")

# ------------------------------------------------------------------- Experiment 2 (summary page 07; thesis F5 data)
TXT = []
TRK2 = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
TSTY2 = {"EKF3 live": ("EKF3", "live"), "UKF live": ("UKF", "live"), "FGO live": ("FGO", "live"), "RTS-UKF (hindsight)": ("UKF", "hind"),
         "FGO hindsight (whole-flight batch)": ("FGO", "hind")}
LAB2 = {"EKF3 live": "EKF3, live", "UKF live": "UKF, live", "FGO live": "FGO, live", "RTS-UKF (hindsight)": "UKF, re-solved after landing",
        "FGO hindsight (whole-flight batch)": "FGO, whole flight re-solved"}
agg = L("expT/t_aggregate.json")
MN2 = {n: [agg["conditions"][c]["mean_rmse_m"][n] for c in TCOND] for n in TRK2}
PER2 = {n: [[L(f"expT/T_{c}_r{r}.json")["tracks"][n]["horiz_err_m"]["rmse"] for r in (1, 2, 3)] for c in TCOND] for n in TRK2}
for c in TCOND:
    check("2_known_tags", f"{TAGS[c]}: live error EKF3 UKF FGO, mean of 3 flights (m)", " ".join(rd(agg["conditions"][c]["mean_rmse_m"][f"{e} live"], 3) for e in EST),
          {"A": "0.039 0.037 0.020", "B": "0.055 0.061 0.026", "C": "0.074 0.076 0.054", "D": "0.096 0.131 0.083"}[c], "expT/t_aggregate.json",
          summ=("07", f"{TAGS[c]}: live error EKF3 UKF FGO, mean of 3 flights (m)"))
    check("2_known_tags", f"{TAGS[c]}: the plotted mean equals the mean of the three plotted flights (6 dp, every track)",
          str(all(rd(float(np.mean(PER2[n][TCOND.index(c)])), 6) == rd(MN2[n][TCOND.index(c)], 6) for n in TRK2)), "True", "expT/T_<c>_r<r>.json vs t_aggregate.json")
GAP2 = " / ".join(rd(agg["conditions"][c]["gap_length_median_s"], 1) for c in TCOND)
check("2_known_tags", "median gap between fixes A–D (s), printed under the tag counts", GAP2, "4.3 / 10.1 / 22.0 / 46.3", "expT/t_aggregate.json",
      [("FI", "median gap between fixes 4.3 / 10.1 / 22.0 / 46.3 s")])
FB2 = rng_si([MN2["FGO hindsight (whole-flight batch)"][i] for i in range(4)], 2)
check("2_known_tags", "FGO whole-flight re-solve, mean over the 4 tag counts, lowest–highest (m, 2 dp), printed in the title", FB2, "0.01–0.03",
      "expT/t_aggregate.json", [("FI", "the FGO's hindsight batch stays at 0.01–0.03 m")])
V2P = check("2_known_tags", "primary (FGO hindsight gain grows as tags get fewer): verdict", "PASS" if agg["H-T1 (FGO live -> whole-flight batch)"]["PASS"] else "FAIL",
            "PASS", "expT/t_aggregate.json H-T1", summ=("07", "primary hypothesis (FGO hindsight gain grows as tags get fewer): verdict"))
V2L = check("2_known_tags", "live errors similar: verdict", "PASS" if agg["P-T3 live ratio max/min"]["PASS"] else "FAIL", "FAIL", "expT/t_aggregate.json P-T3",
            summ=("07", "live errors similar: verdict"))
C15 = [TAGS[c] for c in TCOND if agg["P-T3 live ratio max/min"]["by_condition"][c] <= 1.5]
V2C = check("2_known_tags", "conditions inside 1.5×", ", ".join(C15), "2 tags", "expT/t_aggregate.json P-T3 by_condition", summ=("07", "conditions inside 1.5×"))
check("2_known_tags", "the 1.5× limit and the counts printed", "1.5 / 8, 4, 2, 1 / 3", "1.5 / 8, 4, 2, 1 / 3", "summary page 07 pass rule; conditions A–D; 3 flights")
fig, ax = plt.subplots(figsize=(FW, 5.6))
xc = np.arange(4); offs = dict(zip(TRK2, np.linspace(-0.16, 0.16, 5)))
for n in TRK2:
    e_, kind = TSTY2[n]; x = xc + offs[n]
    ax.plot(x, MN2[n], color=C[e_], ls="-" if kind == "live" else "--", lw=1.6, marker=MK[e_], ms=7, mfc=C[e_] if kind == "live" else SURF,
            mec=C[e_], mew=1.4, zorder=3)
    for j in range(4):
        ax.scatter([x[j]] * 3, PER2[n][j], s=12, marker=MK[e_], color=C[e_] if kind == "live" else SURF, edgecolor=C[e_], lw=0.7, zorder=2, alpha=0.8)
YL2 = {"UKF live": 0.131, "RTS-UKF (hindsight)": 0.112, "EKF3 live": 0.096, "FGO live": 0.081, "FGO hindsight (whole-flight batch)": 0.028}
for n in TRK2:
    e_ = TSTY2[n][0]
    ax.text(3.27, MN2[n][3] if abs(MN2[n][3] - YL2[n]) < 0.006 else YL2[n], T(LAB2[n]), color=C[e_], fontsize=11.5, weight="bold", va="center", ha="left")
ax.set_xticks(xc); ax.set_xticklabels([T(f"{TAGS[c]}\n(fix every {g} s)") for c, g in zip(TCOND, GAP2.split(" / "))])
ax.set_xlabel("tags at known places in the room (median time between position fixes)")
ax.set_ylabel("average position error over 5 laps (m)")
ax.set_xlim(-0.4, 4.95); ax.set_ylim(0, 0.16); ax.grid(axis="x", visible=False)
G2 = check("2_known_tags", "H-T1: FGO hindsight gain per gap (median), A–D (m, 3 dp)", ", ".join(rd(agg["H-T1 (FGO live -> whole-flight batch)"]["median_gain_m"][c], 3) for c in TCOND),
           "0.010, 0.011, 0.023, 0.052", "expT/t_aggregate.json H-T1 median_gain_m", [("N", "0.010 / 0.011 / 0.023 / 0.052 m for A–D")])
mark(ax, -0.32, 0.152, f"Primary: the FGO's gain from re-solving ({G2} m) grows as tags get fewer: {V2P}", fontsize=11.5)
mark(ax, -0.32, 0.141, f"Predicted: live errors within 1.5× of each other: {VERD[V2L]} (only with {V2C})", fontsize=11.5)
ax.text(-0.32, 0.130, T("small marks: each of the 3 flights; large marks joined by lines: their mean"), fontsize=11, color=INK2, va="center")
fig.subplots_adjust(left=0.08, right=0.99, top=0.84, bottom=0.17)
title1(fig, f"With fewer tags every live error grows; the FGO re-solved after landing stays at {FB2.replace('–', ' to ')} m")
corner(fig, "raw, against the room's known tag map, nothing fitted", KEY_LH)
save("2_known_tags", fig, "eval/results/expT/T_{A,B,C,D}_r{1,2,3}.json (tracks.*.horiz_err_m.rmse), expT/t_aggregate.json", tag="raw, against the room's known tag map, nothing fitted",
     key=True)

# ------------------------------------------------------------------- Experiment 3 (summary page 08; thesis F7 data)
TXT = []
LL3 = {(m, k): [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{m} {k}"] for r in (1, 2, 3)] for m in ("lc", "nolc") for k in ("live", "hindsight")}
lc5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL3[("lc", "live")]]
nl5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL3[("nolc", "live")]]
V3a = check("3_loop_closure", "live, with loop closure: lap 5 ÷ lap 1 range", rng(lc5), "0.16–0.43", "expL", summ=("08", "live, with loop closure: lap 5 ÷ lap 1 range"))
V3b = check("3_loop_closure", "live, without loop closure: lap 5 ÷ lap 1 range", rng(nl5, 1), "2.9–4.5", "expL", summ=("08", "live, without loop closure: lap 5 ÷ lap 1 range"))
V3r = check("3_loop_closure", "the four rules: flights passing, of 3", "3/3 3/3 3/3 3/3", sumrow("08", "the four rules: flights passing, of 3"), "index_summary.md page 08")
check("3_loop_closure", "limit 1.5 (× lap 1), laps 1–5, flights 3, lap 1", "1.5 / 5 / 3 / 1", "1.5 / 5 / 3 / 1", "summary page 08 pass rule")
fig, axs = plt.subplots(1, 2, figsize=(FW, 5.4), sharey=True)
for ax, m, lab in ((axs[0], "lc", "with loop closure (tags recognised again)"), (axs[1], "nolc", "without loop closure")):
    for kind in ("live", "hindsight"):
        for tk in LL3[(m, kind)]:
            ax.plot(range(1, 6), tk["per_lap_rmse_m"], color=C["FGO"], ls="-" if kind == "live" else "--", marker="s", ms=6,
                    mfc=C["FGO"] if kind == "live" else SURF, mec=C["FGO"], lw=1.3, zorder=3)
    ax.set_title(T(f"FGO, {lab}: 3 flights"), loc="left", fontsize=12.5)
    ax.set_xticks(range(1, 6)); ax.set_xlabel("lap of the 6 m square"); ax.set_xlim(0.7, 5.3); ax.grid(axis="x", visible=False)
axs[0].set_ylabel("average position error per lap (m)"); axs[0].set_ylim(0, 0.6)
lv = [t["per_lap_rmse_m"][4] for t in LL3[("lc", "live")]]; hv = [t["per_lap_rmse_m"][4] for t in LL3[("lc", "hindsight")]]
axs[0].text(1.1, 0.168, T("FGO, live"), color=C["FGO"], fontsize=11.5, weight="bold", ha="left", va="center")
axs[0].annotate(T("FGO, whole flight re-solved"), (3.0, 0.02), xytext=(3.4, 0.11), color=C["FGO"], fontsize=11.5, weight="bold", ha="center",
                arrowprops=dict(arrowstyle="-", color=C["FGO"], lw=1.0))
nv = [t["per_lap_rmse_m"][4] for t in LL3[("nolc", "live")]]; nh = [t["per_lap_rmse_m"][4] for t in LL3[("nolc", "hindsight")]]
axs[1].text(5.2, max(nv) + 0.025, T("FGO, live"), color=C["FGO"], fontsize=11.5, weight="bold", ha="right")
axs[1].text(5.2, min(nh) - 0.04, T("FGO, whole flight re-solved"), color=C["FGO"], fontsize=11.5, weight="bold", ha="right")
mark(axs[0], 1.6, 0.42, f"PASS on 3 of 3 flights:\nlap 5 ÷ lap 1 = {V3a.replace('–', ' to ')}\n(limit 1.5), and below the\nright panel, live and re-solved")
mark(axs[1], 0.85, 0.56, f"PASS on 3 of 3 flights: grows {V3b.replace('–', ' to ')} times\nover five laps (predicted: more than 1.5)", fontsize=11)
fig.subplots_adjust(left=0.08, right=0.99, top=0.80, bottom=0.12, wspace=0.06)
title1(fig, f"Recognising tags seen before keeps the FGO's error flat; without it the error grows {V3b.replace('–', ' to ')} times over five laps")
corner(fig, "raw, measured from the start tag, nothing fitted", KEY_LH)
save("3_loop_closure", fig, "eval/results/expL/T_A_r{1,2,3}_t245.json (tracks.*.per_lap_rmse_m)", tag="raw, measured from the start tag, nothing fitted", key=True)

# ------------------------------------------------------------------- E2 (summary page 13): mean labels on the live AND hindsight boxes
TXT = []
E2V = LT("E2_verdicts.json")
LAP5 = {("A", k): [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"lc {k}"]["per_lap_rmse_m"][4] for r in (1, 2, 3)] for k in ("live", "hindsight")}
for c in "BCD":
    for k in ("live", "hindsight"):
        LAP5[(c, k)] = [LT(f"E2_T_{c}_r{r}.json")["tracks"][f"lc {k}"]["per_lap_rmse_m"][4] for r in (1, 2, 3)]
VM2 = {}
for c in TCOND:
    st = E2V["P-E2.5"]["means"][c]
    check("E2_fewer_tags", f"{TAGS[c]}: the mean's inputs are the plotted lap-5 live values (stored)", str([v["value"] for v in st["values"]] == LAP5[(c, "live")]),
          "True", "E2_verdicts.json P-E2.5.means", summ=("13", f"{TAGS[c]}: the mean's inputs are the plotted lap-5 live values (stored)"))
    VM2[(c, "live")] = check("E2_fewer_tags", f"{TAGS[c]}: mean over 3 flights of the live lap-5 error, with loop closure (m)", rd(float(np.mean(LAP5[(c, 'live')])), 4),
                             rd(st["mean_m"], 4), "E2_verdicts.json P-E2.5.means.<c>.mean_m",
                             summ=("13", f"{TAGS[c]}: mean over 3 flights of the live lap-5 error, with loop closure (m)"))
    # hindsight: no mean is stored or registered (user TASK 5: computed from the stored per-flight values, rounded once)
    VM2[(c, "hindsight")] = check("E2_fewer_tags", f"{TAGS[c]}: mean over 3 flights of the HINDSIGHT lap-5 error (m, 4 dp; computed here from the stored "
                                  "per-flight values, no mean test registered)", rd(float(np.mean(LAP5[(c, 'hindsight')])), 4),
                                  rd(sum(LAP5[(c, 'hindsight')]) / 3, 4), ("expL/T_A_r<r>_t245.json" if c == "A" else f"scores/E2_T_{c}_r<r>.json") +
                                  " tracks 'lc hindsight' per_lap_rmse_m[4]")
CR2 = E2V["criteria"]
V21 = check("E2_fewer_tags", "H-E2.1 per condition (B, C, D)", " ".join(CR2["H-E2.1"][c]["count"] for c in "BCD"), "3/3 3/3 3/3", "E2_verdicts.json",
            summ=("13", "H-E2.1 per condition (B, C, D)"))
V25 = check("E2_fewer_tags", "P-E2.5 verdict and its three ordering steps", f"{E2V['P-E2.5']['verdict']} {E2V['P-E2.5']['steps']['A<=B']} "
            f"{E2V['P-E2.5']['steps']['B<=C']} {E2V['P-E2.5']['steps']['C<=D']}", "FAIL False True True", "E2_verdicts.json",
            summ=("13", "P-E2.5 verdict and its three ordering steps"))
fig, ax = plt.subplots(figsize=(FW, 5.6))
ax.set_xlim(-0.6, 3.6); ax.set_ylim(0, 0.092)
for j, c in enumerate(TCOND):
    for k, kind in enumerate(("live", "hindsight")):
        x = j + (k - 0.5) * 0.4
        top_ = rbox(ax, x, LAP5[(c, kind)], C["FGO"], kind == "live", w=0.3)
        m_ = float(np.mean(LAP5[(c, kind)]))
        ax.plot([x - 0.19, x + 0.19], [m_, m_], color=INK, lw=2.0, zorder=5)
        ax.text(x, top_ + 0.0018, T(f"mean\n{VM2[(c, kind)]}"), ha="center", va="bottom", fontsize=10.5, linespacing=1.05)
        ax.text(x, -0.0035, T(kind), ha="center", va="top", fontsize=10.5, color=INK2)
    if c != "A":
        mark(ax, j, 0.0855, f"H-E2.1 PASS\n{CR2['H-E2.1'][c]['count'].replace('/', ' of ')} flights", ha="center", fontsize=10.5)
mark(ax, 0, 0.0855, "Experiment 3\nflights (8 tags)", ha="center", fontsize=10.5, weight="normal", color=INK2)
ax.set_xticks(range(4)); ax.set_xticklabels([T(TAGS[c]) for c in TCOND]); ax.tick_params(axis="x", pad=22)
ax.grid(axis="x", visible=False); ax.set_xlabel("tags in the room, each at an unknown place"); ax.set_ylabel("FGO error on the fifth lap (m)")
ax.text(3.55, 0.002, T(f"P-E2.5 (live mean does not fall as tags get fewer): {V25.split()[0]}, it fell from 8 to 4 tags"), fontsize=11,
        weight="bold", ha="right", va="bottom")
ax.text(3.55, 0.0075, T("box: lowest to highest of 3 flights; black line: mean (no mean test registered for hindsight)"), fontsize=10.5,
        color=INK2, ha="right", va="bottom")
fig.subplots_adjust(left=0.08, right=0.99, top=0.84, bottom=0.16)
title1(fig, "With 4, 2 and 1 tags the FGO's loop closure still bounded its error (H-E2.1 PASS); P-E2.5 FAIL")
corner(fig, "raw, measured from the start tag, nothing fitted", KEY_LH)
check("E2_fewer_tags", "counts printed (tags, flights, lap)", "8, 4, 2, 1 / 3 / 5", "8, 4, 2, 1 / 3 / 5", "summary page 13 metric")
check("E2_fewer_tags", "registered ids printed: H-E2.1, P-E2.5", "H-E2.1 P-E2.5", "H-E2.1 P-E2.5", "pre-registration", [("PR", "H-E2.1"), ("PR", "P-E2.5")])
save("E2_fewer_tags", fig, "docs/thesis/tier1/scores/E2_verdicts.json, E2_T_{B,C,D}_r{1,2,3}.json; eval/results/expL/T_A_r{1,2,3}_t245.json",
     tag="raw, measured from the start tag, nothing fitted", key=True)

# ------------------------------------------------------------------- E3 (summary page 14): the outcome table
TXT = []
E3V = LT("E3_verdicts.json"); RUNS3 = E3V["runs"]
GR3 = [("a", "0.01"), ("b", "0.01"), ("a", "0.05"), ("b", "0.05"), ("b", "0")]
LAB3 = {("a", "0.01"): "1% wrong IDs, FGO as built (plain)", ("b", "0.01"): "1% wrong IDs, robust FGO", ("a", "0.05"): "5% wrong IDs, FGO as built (plain)",
        ("b", "0.05"): "5% wrong IDs, robust FGO", ("b", "0"): "no wrong IDs, robust FGO"}
runs3 = lambda arm, rate: sorted(n for n, r in RUNS3.items() if r["arm"] == arm and r["rate"] == rate)
DIV3 = {n: bool(RUNS3[n]["run_status"]["diverged"]) for n in RUNS3}
LIVE3 = {n: RUNS3[n]["values"]["lc live rmse_m"]["value"] for n in RUNS3}
COLL3 = {n for n in RUNS3 if RUNS3[n]["arm"] == "a" and not DIV3[n]} | {"E3b_T_A_r2_0.05_s1"}      # as figs_thesis_summary.py (decision D49)
EXP3 = {("a", "0.01"): "3.7161–3.8960", ("a", "0.05"): "4.0395–4.2231", ("b", "0.01"): "0.0496–1.4769", ("b", "0.05"): "0.9776–4.1849", ("b", "0"): "0.0484–0.0760"}
ROW3 = {}
for a, r in GR3:
    ns = runs3(a, r); fin = [LIVE3[n] for n in ns if not DIV3[n]]
    ROW3[(a, r)] = dict(n=len(ns), div=sum(DIV3[n] for n in ns), coll=sum(n in COLL3 for n in ns),
                        rng=check("E3_table", f"arm ({a}) rate {r}: final live error of the finite runs, lowest–highest (m)", rng(fin, 4), EXP3[(a, r)],
                                  "E3_verdicts.json runs", summ=("14", f"arm ({a}) rate {r}: final live error of the finite runs, lowest–highest (m)")))
check("E3_table", "arm (a) 1%: runs diverged", f"{ROW3[('a', '0.01')]['div']} of {ROW3[('a', '0.01')]['n']}", "6 of 9", "E3_verdicts.json",
      summ=("14", "arm (a) 1%: runs diverged (status FAILED-ESTIMATOR)"))
check("E3_table", "arm (a) 5%: runs diverged", f"{ROW3[('a', '0.05')]['div']} of {ROW3[('a', '0.05')]['n']}", "0 of 9", "E3_verdicts.json",
      summ=("14", "arm (a) 5%: runs diverged"))
check("E3_table", "arm (b), every rate: runs diverged", f"{sum(ROW3[g]['div'] for g in GR3 if g[0] == 'b')} of {sum(ROW3[g]['n'] for g in GR3 if g[0] == 'b')}",
      "0 of 21", "E3_verdicts.json", summ=("14", "arm (b), every rate: runs diverged"))
check("E3_table", "arm (a) runs counted as collapsed (non-diverged)", sum(ROW3[g]["coll"] for g in GR3 if g[0] == "a"), "12", "E3 results §3",
      summ=("14", "arm (a) runs counted as collapsed (non-diverged)"))
check("E3_table", "arm (b) collapsed (DESCRIPTIVE): the one robust run E3 results §4 names", sum(ROW3[g]["coll"] for g in GR3 if g[0] == "b"), "1",
      "E3 results §4", [("E3", "**One robust run collapsed.** The exception is T_A_r2 5% s1")])
check("E3_table", "runs per rate and arm", "/".join(str(ROW3[g]["n"]) for g in GR3), "9/9/9/9/3", "E3_verdicts.json",
      summ=("14", "runs per rate and arm (3 flights × 3 seeds); robust controls at rate 0"))
REF3 = [E3V["references"][f"T_A_r{i}"]["nolc live rmse_m"]["value"] for i in (1, 2, 3)]
VREF = check("E3_table", "stored error without loop closure, the 3 flights, lowest–highest (m)", rng(REF3, 4), "0.2625–0.3608", "E3_verdicts.json references",
             summ=("14", "stored error without loop closure, the 3 flights, lowest–highest (m)"))
CA, CB = E3V["criteria_a"], E3V["criteria_b"]
kk_ = lambda d, p: next(k for k in d if k.startswith(p))
VH31 = check("E3_table", "H-E3.1 verdict and count", f"{CA[kk_(CA, 'H-E3.1')]['verdict']} {CA[kk_(CA, 'H-E3.1')]['count']}", "FAIL 0/9", "E3_verdicts.json",
             summ=("14", "H-E3.1 verdict and count"))
VB31 = check("E3_table", "P-E3b.1 at 1% and 5%: verdicts and counts", f"{CB[kk_(CB, 'P-E3b.1 0.01')]['verdict']} {CB[kk_(CB, 'P-E3b.1 0.01')]['count']} "
             f"{CB[kk_(CB, 'P-E3b.1 0.05')]['verdict']} {CB[kk_(CB, 'P-E3b.1 0.05')]['count']}", "PASS 9/9 PASS 9/9", "E3_verdicts.json",
             summ=("14", "P-E3b.1 at 1% and 5%: verdicts and counts"))
VB32 = check("E3_table", "P-E3b.2 verdict and count", f"{CB[kk_(CB, 'P-E3b.2')]['verdict']} {CB[kk_(CB, 'P-E3b.2')]['count']}", "PASS 3/3", "E3_verdicts.json",
             summ=("14", "P-E3b.2 verdict and count"))
check("E3_table", "1.10 (P-E3b.1 band) and the room's 8 tags", "1.10 / 8", "1.10 / 8", "summary page 14 pass rule")
check("E3_table", "wrong-ID rates (per cent of the eligible detections)", "1% / 5%", "1% / 5%", "E3_verdicts.json", summ=("14", "wrong-ID rates (per cent of the eligible detections)"))
check("E3_table", "registered ids printed: H-E3.1, P-E3b.1, P-E3b.2", "H-E3.1 P-E3b.1 P-E3b.2", "H-E3.1 P-E3b.1 P-E3b.2", "pre-registration",
      [("PR", "H-E3.1"), ("PR", "P-E3b.1"), ("PR", "P-E3b.2")])
fig = plt.figure(figsize=(FW, 5.2)); ax = fig.add_axes([0.01, 0.04, 0.98, 0.80]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
CX3 = [0.0, 0.33, 0.47, 0.71, 0.86]
HD3 = ["condition", "runs diverged", "error of the finished runs,\nlowest to highest (m)", "collapsed\n(descriptive)",
       "without loop\nclosure (m),\nfor reference"]
for x_, h_ in zip(CX3, HD3):
    ax.text(x_, 0.98, T(h_), fontsize=11.5, weight="bold", va="top", linespacing=1.1)
ax.add_patch(Rectangle((0, 0.785), 1, 0.006, color="#888888", lw=0))
for i, g in enumerate(GR3):
    y_ = 0.72 - 0.1 * i; R_ = ROW3[g]
    if i % 2 == 0:
        ax.add_patch(Rectangle((0, y_ - 0.05), 1, 0.1, color="#f4f4f4", lw=0, zorder=0))
    ax.text(CX3[0], y_, T(LAB3[g]), fontsize=12, va="center")
    ax.text(CX3[1], y_, T(f"{R_['div']} of {R_['n']}"), fontsize=12, va="center", weight="bold" if R_["div"] else "normal")
    ax.text(CX3[2], y_, T(R_["rng"].replace("–", " to ")), fontsize=12, va="center")
    ax.text(CX3[3], y_, T(f"{R_['coll']} of {R_['n']}"), fontsize=12, va="center")
    ax.text(CX3[4], y_, T(VREF.replace("–", " to ")), fontsize=11, va="center", color=INK2)
ax.text(0.0, 0.19, T(f"H-E3.1 (primary): at 1% wrong IDs, the FGO as built below its error without loop closure in 9 of 9 runs: "
                     f"{VH31.split()[0]}, {VH31.split()[1].replace('/', ' of ')}"), fontsize=11.5, weight="bold", va="center")
ax.text(0.0, 0.125, T(f"P-E3b.1: the robust FGO at most 1.10 × the plain FGO in the same run: {VB31.split()[0]}, "
                      f"{VB31.split()[1].replace('/', ' of ')} at 1% and {VB31.split()[3].replace('/', ' of ')} at 5%"), fontsize=11.5, weight="bold", va="center")
ax.text(0.0, 0.06, T(f"P-E3b.2: the robust FGO with no wrong IDs: {VB32.split()[0]}, {VB32.split()[1].replace('/', ' of ')}"), fontsize=11.5,
        weight="bold", va="center")
ax.text(0.0, 0.0, T("collapsed: the run finished with a wrong tag map (DESCRIPTIVE, not a registered measure; maps on the next page)"),
        fontsize=10.5, color=INK2, va="center")
title1(fig, "With 1% wrong tag IDs the FGO as built lost its loop-closure advantage (H-E3.1 FAIL); the robust FGO never diverged")
corner(fig, "raw, measured from the start tag, nothing fitted")
save("E3_table", fig, "docs/thesis/tier1/scores/E3_verdicts.json (runs, references, criteria)", tag="raw, measured from the start tag, nothing fitted")

# ------------------------------------------------------------------- E5 (summary page 18): direct box labels
TXT = []
E5V = LT("e5_verdicts.json")["flights"]; E5C = LT("e5_verdicts.json")["criteria"]
E5S = {r: LT(f"e5_T_A_r{r}.json")["tracks"] for r in (1, 2, 3)}
VAL5 = {}
for m in ("lc", "nolc"):
    for k in ("live", "hindsight"):
        VAL5[("UKF", m, k)] = [E5S[r][f"{m} {k}"]["rmse_m"] for r in (1, 2, 3)]
        VAL5[("FGO", m, k)] = [E5V[f"T_A_r{r}"]["values"][f"fgo {m} {k} rmse_m"]["value"] for r in (1, 2, 3)]
V5 = {}
for g in VAL5:
    lab_ = f"{g[0]} {'with' if g[1] == 'lc' else 'without'} loop closure, {g[2]}: lowest–highest over 3 flights (m)"
    V5[g] = check("E5_ukf_landmarks", lab_, rng(VAL5[g], 4), sumrow("18", lab_), "e5_verdicts.json / e5_T_A_r<r>.json", summ=("18", lab_))
VR5 = check("E5_ukf_landmarks", "H-E5.1: lap 5 ÷ lap 1, live with loop closure, lowest–highest", rng([E5V[f"T_A_r{r}"]["ratio lc live lap5/lap1"] for r in (1, 2, 3)], 2),
            "0.27–0.42", "e5_verdicts.json", summ=("18", "H-E5.1: lap 5 ÷ lap 1, live with loop closure, lowest–highest"))
VC5 = {h: check("E5_ukf_landmarks", f"{h}: verdict and count", f"{E5C[h]['verdict']} {E5C[h]['count']}", "PASS 3/3", "e5_verdicts.json", summ=("18", f"{h}: verdict and count"))
       for h in ("H-E5.1", "S-E5.5", "S-E5.6")}
check("E5_ukf_landmarks", "limit 1.5 and 3 flights", "1.5 / 3", "1.5 / 3", "summary page 18 pass rule")
check("E5_ukf_landmarks", "registered ids printed: H-E5.1, S-E5.5, S-E5.6; lap 5 / lap 1; 8 tags", "H-E5.1 S-E5.5 S-E5.6 / 5 / 1 / 8",
      "H-E5.1 S-E5.5 S-E5.6 / 5 / 1 / 8", "pre-registration", [("PR", "H-E5.1"), ("PR", "S-E5.5"), ("PR", "S-E5.6")])
fig, ax = plt.subplots(figsize=(FW, 5.6))
ax.set_xlim(-0.62, 1.92); ax.set_ylim(0, 1.82)
BL5 = {("UKF", "live"): "UKF\nlive", ("UKF", "hindsight"): "UKF\nhindsight", ("FGO", "live"): "FGO\nlive", ("FGO", "hindsight"): "FGO\nre-solved"}
for j, m in enumerate(("nolc", "lc")):
    for k, (e, kind) in enumerate((("UKF", "live"), ("UKF", "hindsight"), ("FGO", "live"), ("FGO", "hindsight"))):
        x = j * 1.3 + (k - 1.5) * 0.265
        top_ = rbox(ax, x, VAL5[(e, m, kind)], C[e], kind == "live", w=0.2)
        ax.text(x, top_ + 0.03, T(V5[(e, m, kind)].replace("–", " to\n") + " m"), ha="center", va="bottom", fontsize=10.5, linespacing=1.05)
        ax.text(x, -0.035, T(BL5[(e, kind)]), ha="center", va="top", fontsize=10.5, color=C[e], weight="bold", linespacing=1.0)
ax.set_xticks([0, 1.3]); ax.set_xticklabels([T("without loop closure"), T("with loop closure")]); ax.tick_params(axis="x", pad=38)
ax.grid(axis="x", visible=False); ax.set_ylabel("average position error over 5 laps (m)")
mark(ax, 0.62, 1.66, f"With loop closure the UKF's error did not grow:\nH-E5.1 {VC5['H-E5.1'].split()[0]} ({VC5['H-E5.1'].split()[1].replace('/', ' of ')}; "
     f"lap 5 ÷ lap 1 = {VR5.replace('–', ' to ')}, limit 1.5)", fontsize=11, va="top")
mark(ax, 0.62, 1.34, f"The UKF stayed above the FGO, live and hindsight:\nS-E5.5 {VC5['S-E5.5'].split()[0]}, S-E5.6 {VC5['S-E5.6'].split()[0]} "
     f"({VC5['S-E5.5'].split()[1].replace('/', ' of ')})", fontsize=11, va="top")
ax.text(0.62, 1.02, T("box: lowest to highest of 3 flights (8-tag room);\nthe FGO values are the stored Experiment 3 results"),
        fontsize=10.5, color=INK2, va="top")
fig.subplots_adjust(left=0.08, right=0.99, top=0.84, bottom=0.2)
title1(fig, "A UKF with landmark states also stopped its error growing with loop closure, but stayed above the FGO")
corner(fig, "raw, measured from the start tag, nothing fitted", KEY_LH)
save("E5_ukf_landmarks", fig, "docs/thesis/tier1/scores/e5_verdicts.json, e5_T_A_r{1,2,3}.json", tag="raw, measured from the start tag, nothing fitted", key=True)


# ------------------------------------------------------------------- E6 (summary page 20): map reuse (added 2026-11-02, user answer 5; D101-D104)
TXT = []
DISPF.update({"E6": "docs/thesis/tier1/e6_results.md", "E6PR": "docs/thesis/tier1/e6_preregistration.md"})
E6V = LT("e6_verdicts.json"); E6F = E6V["flights"]; E6T = ["T_A_r1", "T_A_r2", "T_A_r3"]; E6M = [E6V["pairs"][t] for t in E6T]
ARM6 = {"sv": "(i) surveyed", "fm": "(ii) FGO map", "um": "(iii) UKF map", "nm": "(iv) no map, LC online"}
EOR6 = ("FGO", "UKF")
LAP1_6 = {(e, a): [E6F[t][e][f"{ARM6[a]} | live"]["lap1_m"] for t in E6T] for e in EOR6 for a in ARM6}
ALL6 = {(e, a): [E6F[t][e][f"{ARM6[a]} | live"]["rmse_m"] for t in E6T] for e in EOR6 for a in ARM6}
check("E6_map_reuse", "verdict-file values equal the score files (lap 1 and overall, live, every arm, both estimators)",
      str(all(LAP1_6[(e, a)][i] == LT(f"e6_{t}.json")["tracks"][f"{ARM6[a]} | {e} live"]["per_lap_rmse_m"][0]
              and ALL6[(e, a)][i] == LT(f"e6_{t}.json")["tracks"][f"{ARM6[a]} | {e} live"]["rmse_m"] for e in EOR6 for a in ARM6 for i, t in enumerate(E6T))),
      "True", "scores/e6_verdicts.json vs scores/e6_T_A_r{1,2,3}.json",
      summ=("20", "verdict file values equal the score files (lap 1 and overall, live, every arm, both estimators)"))
V6L1 = {}
for e in EOR6:
    for a in ("fm", "nm"):
        lab_ = f"{e} estimator, {ARM6[a]}: lap-1 live RMSE, lowest–highest over 3 test flights (m)"
        V6L1[(e, a)] = check("E6_map_reuse", lab_, rng(LAP1_6[(e, a)], 4), sumrow("20", lab_), "e6_verdicts.json flights.<t>.<est>.'<arm> | live'.lap1_m",
                             [("E6", sumrow("20", lab_))], summ=("20", lab_))
RAT6 = {e: [ALL6[(e, "fm")][i] / ALL6[(e, "sv")][i] for i in range(3)] for e in EOR6}
V6R = {}
for e in EOR6:
    lab_ = f"{e} estimator: FGO map ÷ surveyed map, overall live RMSE, lowest–highest (×)"
    V6R[e] = check("E6_map_reuse", lab_, rng(RAT6[e], 2), sumrow("20", lab_), "e6_verdicts.json (rmse_m, arms ii / i)", [("E6", sumrow("20", lab_) + " times")],
                   summ=("20", lab_))
BND6 = {e: (E6V["p2_bands_m"][e]["lo"], E6V["p2_bands_m"][e]["hi"]) for e in EOR6}
for e in EOR6:
    lab_ = f"{e} estimator: surveyed-map band for P2 [min − R, max + R], 4 dp (m)"
    check("E6_map_reuse", lab_, f"{rd(BND6[e][0], 4)}–{rd(BND6[e][1], 4)}", sumrow("20", lab_), "e6_verdicts.json p2_bands_m", summ=("20", lab_))
CR6 = E6V["criteria"]
V6 = {k: check("E6_map_reuse", f"{k}: verdict and count", f"{CR6[k]['verdict']} {sum(CR6[k]['per_flight'])}/3", sumrow("20", f"{k}: verdict and count"),
               "e6_verdicts.json criteria", summ=("20", f"{k}: verdict and count"))
      for k in ("P1", "P2 (FGO)", "P2 (UKF)", "P3 (FGO)", "P3 (UKF)", "P4 (FGO)", "P4 (UKF)")}
SAME6 = check("E6_map_reuse", "DESCRIPTIVE: per-flight outcomes of P1, P3 (FGO) and P3 (UKF) identical on the 3 flights",
              str(CR6["P1"]["per_flight"] == CR6["P3 (FGO)"]["per_flight"] == CR6["P3 (UKF)"]["per_flight"]), "True", "e6_verdicts.json criteria.*.per_flight",
              summ=("20", "DESCRIPTIVE: per-flight outcomes of P1, P3 (FGO) and P3 (UKF) identical on the 3 flights"))
MAPD = [E6F[t]["map"]["ukf_map_pos_rms_m"] - E6F[t]["map"]["fgo_map_pos_rms_m"] for t in E6T]           # > 0: the FGO map is the better map
LIVD = {e: [ALL6[(e, "um")][i] - ALL6[(e, "fm")][i] for i in range(3)] for e in EOR6}               # > 0: lower live error on the FGO map
SGN6 = check("E6_map_reuse", "DESCRIPTIVE: sign of (live UKF map − live FGO map) equals the sign of (UKF-map RMS − FGO-map RMS), flights, per estimator",
             " ".join(f"{e} {sum((LIVD[e][i] > 0) == (MAPD[i] > 0) for i in range(3))}/3" for e in EOR6), "FGO 3/3 UKF 3/3", "e6_verdicts.json flights.<t>.map and rmse_m")
GAP1 = check("E6_map_reuse", "r1b: the two maps' position RMS differ by (m, 4 dp)", rd(abs(MAPD[0]), 4), "0.0007", "e6_verdicts.json flights.T_A_r1.map",
             [("E6", "0.0007 m of each other")])
check("E6_map_reuse", "counts printed: 3 flights, tag 0, lap 1, P1 to P4, 7 tags", "3 / 0 / 1 / 1 2 3 4 / 7", "3 / 0 / 1 / 1 2 3 4 / 7", "e6_preregistration.md",
      [("E6PR", "position RMS over the 7 tags (the P1 metric)"), ("E6PR", "(tag 0, §1.2)")])
check("E6_map_reuse", "mapping flights paired with the test flights", ", ".join(E6M), "E6M_fig8_r1b, E6M_fig8_r2, E6M_fig8_r3", "e6_verdicts.json pairs")
fig, axs = plt.subplots(1, 3, figsize=(FW, 6.0), gridspec_kw=dict(width_ratios=[1.15, 1.0, 1.15]))
ax1, ax2, ax3 = axs
SH6 = {"FGO": -0.17, "UKF": 0.17}
for j, e in enumerate(EOR6):
    xc_ = j * 1.3
    for i in range(3):
        xs = [xc_ - 0.22, xc_ + 0.22]; ys = [LAP1_6[(e, "fm")][i], LAP1_6[(e, "nm")][i]]
        ax1.plot(xs, ys, color=C[e], lw=0.9, alpha=0.7, zorder=2)
        ax1.plot(xs, ys, ls="", marker=MK[e], ms=8, color=C[e], zorder=3)
    ax1.text(xc_ - 0.32, max(LAP1_6[(e, "fm")]) + 0.004, T(V6L1[(e, "fm")].replace("–", " to\n")), ha="right", va="bottom", fontsize=10, linespacing=1.0)
    ax1.text(xc_ + 0.22, max(LAP1_6[(e, "nm")]) + 0.012, T(V6L1[(e, "nm")].replace("–", " to\n")), ha="center", va="bottom", fontsize=10, linespacing=1.0)
    ax1.text(xc_ - 0.22, -0.012, T("map"), ha="center", va="top", fontsize=10, color=INK2)
    ax1.text(xc_ + 0.22, -0.012, T("no map"), ha="center", va="top", fontsize=10, color=INK2)
    mark(ax1, xc_, 0.335, f"P4 {V6[f'P4 ({e})'].split()[0]}\n{V6[f'P4 ({e})'].split()[1].replace('/', ' of ')}", ha="center", fontsize=10.5, color=C[e])
ax1.set_xlim(-0.95, 1.75); ax1.set_ylim(0, 0.37); ax1.set_xticks([0, 1.3]); ax1.set_xticklabels([T(f"{e}\nestimator") for e in EOR6])
ax1.tick_params(axis="x", pad=18); ax1.grid(axis="x", visible=False); ax1.set_ylabel("live error, first lap (m)")
ax1.set_title(T("First lap: FGO map vs no map"), loc="left", fontsize=12)
for j, e in enumerate(EOR6):
    lo_, hi_ = BND6[e]
    ax2.add_patch(Rectangle((j - 0.32, lo_), 0.64, hi_ - lo_, facecolor=GREY, alpha=0.35, lw=0, zorder=1))
    ax2.plot([j] * 3, ALL6[(e, "fm")], ls="", marker=MK[e], ms=8, color=C[e], zorder=3)
    ax2.text(j, max(ALL6[(e, "fm")]) + 0.0012, T(f"{V6R[e].replace('–', ' to ')} ×\nsurveyed"), ha="center", va="bottom", fontsize=10, linespacing=1.0)
    mark(ax2, j, 0.0575, f"P2 {V6[f'P2 ({e})'].split()[0]}\n{V6[f'P2 ({e})'].split()[1].replace('/', ' of ')}\nin band", ha="center", fontsize=10.5, color=C[e], linespacing=1.0)
ax2.text(1.5, 0.0012, T("grey: surveyed-map band"), ha="right", va="bottom", fontsize=10, color=INK2)
ax2.set_xlim(-0.55, 1.55); ax2.set_ylim(0, 0.064); ax2.set_xticks([0, 1]); ax2.set_xticklabels([T(f"{e}\nestimator") for e in EOR6])
ax2.tick_params(axis="x", pad=18); ax2.grid(axis="x", visible=False); ax2.set_ylabel("live error, whole flight (m)")
ax2.set_title(T("Whole flight on the FGO map"), loc="left", fontsize=12)
ax3.axhline(0, color=GREY, lw=1.0, zorder=1); ax3.axvline(0, color=GREY, lw=1.0, zorder=1)
for e in EOR6:
    ax3.plot(MAPD, LIVD[e], ls="", marker=MK[e], ms=8, color=C[e], zorder=3)
ax3.set_xlim(-0.006, 0.024); ax3.set_ylim(-0.014, 0.03)
ax3.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.01)); ax3.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.01))
ax3.set_xlabel("map error difference (m)"); ax3.set_ylabel("live error difference (m)")
ax3.text(-0.0055, 0.0285, T(f"P1 {V6['P1'].split()[0]} {V6['P1'].split()[1].replace('/', ' of ')}\nP3 {V6['P3 (FGO)'].split()[0]} "
                            f"{V6['P3 (FGO)'].split()[1].replace('/', ' of ')} each"), fontsize=10.5, weight="bold", va="top")
ax3.text(0.0235, -0.0135, T(f"DESCRIPTIVE, 3 flights: same sign\non {SGN6.split()[1].replace('/', ' of ')} for both\nestimators; on r1b the maps\n"
                           f"differ by {GAP1} m"), fontsize=9.5, color=INK2, ha="right", va="bottom", linespacing=1.05)
ax3.set_title(T("UKF map minus FGO map"), loc="left", fontsize=12)
ax3.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
ax3.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
fig.text(0.01, 0.015, T("Limitations: simulation only; n = 3 flights; perfect tag IDs; tag 0 anchors the frame; maps used as exact (no map "
                        "uncertainty carried); same world and day;\nP4 compares with other loop-closure estimators. The mapping flights flew a "
                        "different route (out of sample), so the same-route caveat does not apply."), fontsize=9.5, color=INK2, va="bottom",
         linespacing=1.15)
fig.subplots_adjust(left=0.07, right=0.985, top=0.80, bottom=0.25, wspace=0.42)
title1(fig, "Flying live, a map from an earlier flight beat no map on the first lap (P4 PASS) but did not match the survey (P2 FAIL)")
corner(fig, "raw, world frame, nothing fitted; live tracks", "filled = live (during flight)")
save("E6_map_reuse", fig, "docs/thesis/tier1/scores/e6_verdicts.json (flights, criteria, p2_bands_m, pairs), e6_T_A_r{1,2,3}.json",
     tag="raw, world frame, nothing fitted; live tracks", key=True)

# ------------------------------------------------------------------- 1C additional no-heading flights (appendix; user answer 2; D97, D98)
# DESCRIPTIVE, no verdict. The registered 1C verdicts are computed from HALF (figs_thesis.py, figs_thesis_summary.py; the flights script
# parses figs_thesis.py's HALF): these five flights are not in it, which is asserted here, so they cannot change a registered number.
TXT = []
XTR = [("cl_a_tex", "EKF3", "EKF3, full speed (real time)"),
       ("cl_ukf_a_tex", "UKF", "UKF, old build (before the jitter\ncorrection), full speed"),
       ("cl_ukf_a_tex_half", "UKF", "UKF, old build (before the jitter\ncorrection), half real time"),
       ("cl_fgo_a_tex_half", "FGO", "FGO, original build (before the noise\ncorrection), half real time"),
       ("cl_fgo_a_tex_half_v2", "FGO", "FGO, noise fix only, yaw cap ungated\n(ABLATION), half real time")]
REGH = {}
for src_ in ("figs_thesis.py", "figs_thesis_summary.py"):
    s_ = open(os.path.join(HERE, src_)).read()
    nd_ = next(n for n in ast.parse(s_).body if isinstance(n, ast.Assign) and any(isinstance(t_, ast.Name) and t_.id == "HALF" for t_ in n.targets))
    REGH[src_] = eval(compile(ast.Expression(nd_.value), src_, "eval"))
check("1C_extra", "registered 1C set (HALF) identical in figs_thesis.py and figs_thesis_summary.py", str(REGH["figs_thesis.py"] == REGH["figs_thesis_summary.py"]),
      "True", "ast of HALF in both scripts")
REGT = {t for v in REGH["figs_thesis.py"].values() for t in [v[0]] + list(v[1])}
check("1C_extra", "none of the five additional flights is in the registered set (HALF)", str(not ({t for t, _, _ in XTR} & REGT)), "True", "HALF")
ALLA = sorted(f[len("closed_loop_"):-5] for f in os.listdir(RES) if f.startswith("closed_loop_") and "_a_tex" in f and f.endswith(".json"))
check("1C_extra", "every stored no-heading flight is either registered or one of the five", str(sorted(ALLA) == sorted([t for t, _, _ in XTR] + [v[0] for v in REGH["figs_thesis.py"].values()])),
      "True", "eval/results/closed_loop_*_a_tex*.json")
CT_EXP = {"cl_a_tex": "186.2", "cl_ukf_a_tex": "163.0", "cl_ukf_a_tex_half": "198.0", "cl_fgo_a_tex_half": "165.8", "cl_fgo_a_tex_half_v2": "169.6"}
CTX = {}
for t, e, _ in XTR:
    j_ = L(f"closed_loop_{t}.json")["contact"]
    v_ = j_["t_rel_cruise_s"] if "t_rel_cruise_s" in j_ else j_["cruise_plus_s"]
    CTX[t] = (v_, check("1C_extra", f"{t}: wall contact, s after cruise start (DESCRIPTIVE)", rd(v_, 1), CT_EXP[t], f"eval/results/closed_loop_{t}.json contact",
                         [("N", f"+{CT_EXP[t]}")]))
    check("1C_extra", f"{t}: west wall", L(f"closed_loop_{t}.json")["contact"]["wall"], "west", f"closed_loop_{t}.json contact.wall")
check("1C_extra", "additional flights counted", str(len(XTR)), "5", "this list")
fig, ax = plt.subplots(figsize=(FW, 5.0))
for i, (t, e, lab) in enumerate(XTR):
    y_ = len(XTR) - 1 - i
    ax.plot(CTX[t][0], y_, ls="", marker=MK[e], ms=11, color=C[e], zorder=3)
    ax.text(CTX[t][0] + 2.5, y_, T(f"+{CTX[t][1]} s"), va="center", fontsize=11.5, weight="bold")
    ax.text(102, y_, T(lab), va="center", ha="left", fontsize=10.5, color=C[e], linespacing=1.05)
ax.set_xlim(100, 215); ax.set_ylim(-0.6, len(XTR) - 0.4); ax.set_yticks([]); ax.grid(axis="y", visible=False)
ax.spines["left"].set_visible(False)
ax.set_xlabel("wall contact, time after the start of the cruise (s)")
fig.text(0.01, 0.02, T("Each flight was flown once (n = 1), on the textured corridor with no camera heading. No pass window and no verdict are "
                       "drawn: the registered\nExperiment 1C verdicts use only the pre-registered flights, and the full-speed and half-real-time "
                       "flights are not compared."), fontsize=10, color=INK2, va="bottom", linespacing=1.15)
fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.25)
title1(fig, "Five more no-heading flights: each also reached the west wall (descriptive; not scored here)")
corner(fig, "additional flights, not part of the pre-registered set")
check("1C_extra", "n = 1", "1", "1", "numbers.md §15 ('n = 1 per no-heading cell')", [("N", "n = 1 per no-heading cell")])
save("1C_extra", fig, "eval/results/closed_loop_{cl_a_tex, cl_ukf_a_tex, cl_ukf_a_tex_half, cl_fgo_a_tex_half, cl_fgo_a_tex_half_v2}.json (contact); "
     "HALF from eval/figs_thesis.py and eval/figs_thesis_summary.py (ast)", tag="additional flights, not part of the pre-registered set")


# =================================================================== index
n_ok = sum(c["ok"] for c in CHK)
W = ["# Results walkthrough, composite figures: index and provenance", "",
     f"*Generated by `eval/figs_walkthrough_extra.py` at commit `{COMMIT}`. Stored result files only; nothing re-run. rd() parsed from "
     f"`eval/figs_thesis.py` (source sha256 `{RD_SHA}`).*", "",
     f"**Checks:** {n_ok}/{len(CHK)} EXACT (string equality; shown-in strings found in the cited display file; where summary pages 10, 11, "
     "16 or 17 print the same quantity, the computed string of that page's check row in `index_summary.md` is equal). Every number drawn "
     "on a figure occurs in a passing check of that figure (number guard), and no figure text has an em-dash.", "",
     "**Layout notes.** `ex_5_hold_drift.png`: the two panels share ONE linear y-scale (0 to 60 mm, `sharey`), the unit of "
     "docs/thesis/units.md for both quantities. `ex_E4_tradeoff.png`: the two panels hold different quantities (ms, m) side by side "
     "because the user asked for exactly this two-panel figure; each axis is linear from 0, and the windows sit at evenly spaced "
     "positions 0 to 4 on both panels (not to scale, stated on the figure).", "",
     "## Figures", "", "| figure | file | sha256 | inputs | numbers drawn |", "|---|---|---|---|---|"]
for k, f in FIGS.items():
    W.append(f"| {k} | `{f['file']}` | `{hashlib.sha256(open(os.path.join(ROOT, f['file']), 'rb').read()).hexdigest()}` | {f['inputs']} | "
             f"{', '.join(f['numbers'])} |")
W += ["", "## Checks", "", "| figure | check | computed | expected | where | result |", "|---|---|---|---|---|---|"]
W += [f"| {c['fig']} | {c['label'].replace('|', '¦')} | `{c['computed'].replace('|', '¦')}` | `{c['expected'].replace('|', '¦')}` | "
      f"{c['where'].replace('|', '¦')} | {'OK' if c['ok'] else 'FAIL'} |" for c in CHK]
open(INDEX, "w").write("\n".join(W) + "\n")
json.dump(dict(figs=FIGS, checks=CHK), open(os.path.join(OUTD, "checks.json"), "w"), indent=1)
print(f"checks {n_ok}/{len(CHK)}; wrote {INDEX}")
sys.exit(0 if n_ok == len(CHK) else 1)
