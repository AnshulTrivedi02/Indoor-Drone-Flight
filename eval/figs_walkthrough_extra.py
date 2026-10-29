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


def save(fid, fig, inputs):
    """Number guard: every number drawn on the figure (TXT) must occur in a passing check of this figure."""
    allowed = set()
    for c in CHK:
        if c["fig"] == fid and c["ok"]:
            allowed |= set(NUMTOK.findall(c["computed"])) | set(NUMTOK.findall(c["expected"]))
    stray = sorted({t for s in TXT for t in NUMTOK.findall(s.replace("EKF3", "EKF"))} - allowed)
    assert not stray, f"{fid}: number(s) {stray} drawn without a check"
    for s in TXT:
        assert "—" not in s, f"{fid}: em-dash in '{s}'"
    fig.canvas.draw(); r_ = fig.canvas.get_renderer(); W_, H_ = fig.bbox.width, fig.bbox.height
    for t_ in fig.findobj(matplotlib.text.Text):
        if t_.get_text() and t_.get_visible():
            b_ = t_.get_window_extent(renderer=r_)
            assert b_.x0 >= -1 and b_.x1 <= W_ + 1 and b_.y0 >= -1 and b_.y1 <= H_ + 1, f"{fid}: text runs off the figure: {t_.get_text()[:50]!r}"
    p = os.path.join(OUTD, f"ex_{fid}.png"); fig.savefig(p, dpi=DPI); plt.close(fig)
    FIGS[fid] = dict(file=os.path.relpath(p, ROOT), inputs=inputs, numbers=sorted(allowed & {t for s in TXT for t in NUMTOK.findall(s)}),
                     text=list(TXT))
    print(f"wrote ex_{fid}.png")


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
fig.subplots_adjust(left=0.1, right=0.99, top=0.84, bottom=0.2, wspace=0.12)
fig.suptitle(T("Experiment 5: holding next to a wall tag (left), drift while the tag is hidden (right)"), x=0.1, ha="left",
             fontsize=13.5, weight="bold", y=0.985)
save("5_hold_drift", fig, "eval/results/expH/{s1far_r1,s1far_r2,s1far_r3b,s1_r1..r3,s2v2_r1..r3,s3v2_r1..r3}.json, "
     "eval/results/expH/h_comparative_2026-10-11.json")

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
fig.subplots_adjust(left=0.08, right=0.985, top=0.80, bottom=0.25, wspace=0.28)
fig.suptitle(T("Extension E4: a longer FGO window costs far more compute and does not improve live accuracy"), x=0.08, ha="left",
             fontsize=13, weight="bold", y=0.975)
fig.text(0.08, 0.895, T("Filled squares: live (fixed-lag) estimates. NOT FITTED: room frame, no alignment. Both y-axes linear, from 0."),
         fontsize=11.5, color=INK2, va="top")
CAP = (f"A 5 s window costs {VRAT.replace('–', ' to ')} times the compute of the 0.25 s window (median step per flight) and does not "
       f"improve live accuracy: lower at 5 s on {sum(LOW.values())} of 12 flights (by at most {VDLO} m), higher on the other "
       f"{12 - sum(LOW.values())} (by at most {VDHI} m); H-E4.3 {VH43.split()[0]} (not met). From the 1 s window on, every flight is over "
       f"the {BUD} ms budget.")
import textwrap
fig.text(0.08, 0.035, T("\n".join(textwrap.wrap(CAP, 118))), fontsize=11.5, va="bottom", ha="left", color=INK, linespacing=1.25)
check("E4_tradeoff", "every flight over the budget at 1 s and above (after-anchor medians > 33 ms)", str(all(min(MED4[w]) > 33 for w in (1, 2, 5))),
      "True", "E4_verdicts.json", [("E4", "and 12/12 at each of 1, 2 and 5 s (> 33 ms)")])
check("E4_tradeoff", "registered id printed: H-E4.3", "H-E4.3", "H-E4.3", "pre-registration", [("PR", "| **H-E4.3** (directional accuracy, amendment 3) |")])
save("E4_tradeoff", fig, "docs/thesis/tier1/scores/E4_verdicts.json (P-E4.1 medians after the anchor, P-E4.2, H-E4.3); "
     "docs/thesis/tier1/scores/E4_<trial>_w<W>.json (cap 2) tracks 'FGO live' horiz_err_m.rmse")

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
