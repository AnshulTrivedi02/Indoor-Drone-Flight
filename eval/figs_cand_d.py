#!/usr/bin/env python3
"""CANDIDATE THESIS FIGURES, GROUP D (decision D124, 2026-11-04): Extension E4 (FGO window vs compute time / live error),
Extension E6 (map reuse) and the exploratory window/iteration ablation, restyled to thesis quality so the user can pick and
choose. Stored outputs only: no flight, no estimator replay, no simulation.

Scope (group D brief): every walkthrough/summary-page chart covering E4, E6 and the exploratory ablation that is NOT already
a figure in docs/thesis/figures_thesis/ (confirmed absent from index.md before this script was written). Source charts:
  - eval/figs_walkthrough_extra.py: ex_E4_tradeoff.png (two-panel, approved exception), ex_E4_err_compute.png
    (walkthrough page 17e), ex_E6_map_reuse.png (walkthrough page 20, three panels).
  - eval/figs_thesis_summary.py: page 16 (E4_step_time), page 17 (E4_accuracy), page 20 (E6_map_reuse, two panels - a
    SUBSET of the walkthrough's three; not a separate candidate, see below), page 19 (ablation), page 21
    (E4_error_vs_compute - same data/encoding as ex_E4_err_compute, ONE candidate covers both, see D01 below).

Data: loaders and expected strings are COPIED from eval/figs_walkthrough_extra.py and eval/figs_thesis_summary.py (same
stored score/result files, same selection), not invented. rd() is PARSED (not imported/run) from eval/figs_thesis.py, same
technique and SHA assertion as those two scripts, so the thesis rounding rule is identical.

Style (RS-1, D113, D124): 160 mm (6.30 in) wide, Okabe-Ito EKF3/UKF/FGO colours and markers from eval/thesis_style.py, no
in-figure titles, no verdict words/badges/check counts on the image, no bold in axes, linear axes only, side-by-side panels
only on a shared y-scale except the one user-approved E4 compute/accuracy two-panel exception (D04 below). Captions end with
a 'Verdicts: Table A.4, rows <ids>.' pointer (ids = the literal ID-column values of docs/thesis/tables/TA_verdicts.md).

Outputs: docs/thesis/figures_thesis/candidates/D0{1..8}.{png,pdf}, candidates/captions/D0{1..8}.md,
candidates/index_d.md. Usage: python3 eval/figs_cand_d.py   (numpy, matplotlib)."""
import ast, hashlib, json, os, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results"); T1D = os.path.join(ROOT, "docs", "thesis", "tier1")
ABD = os.path.join(ROOT, "docs", "thesis", "ablation")
OUTD = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "candidates")
CAPD = os.path.join(OUTD, "captions")
os.makedirs(OUTD, exist_ok=True); os.makedirs(CAPD, exist_ok=True)
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
L = lambda f: json.load(open(os.path.join(RES, f)))
LT = lambda f: json.load(open(os.path.join(T1D, "scores", f)))
TAPATH = os.path.join(ROOT, "docs", "thesis", "tables", "TA_verdicts.md")

# ------------------------------------------------------------------ rd(): the thesis rounding rule, PARSED (not run/imported) from
# figs_thesis.py, identical technique+SHA assertion to figs_walkthrough_extra.py / figs_thesis_summary.py.
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read()
_rd = next(n for n in ast.parse(_src).body if isinstance(n, ast.FunctionDef) and n.name == "rd")
RD_SHA = hashlib.sha256(ast.get_source_segment(_src, _rd).encode()).hexdigest()
_ns = {}; exec(compile(ast.Module(body=[_rd], type_ignores=[]), FT, "exec"), _ns); rd = _ns["rd"]
assert RD_SHA == "e7320d3b8f377157c0c6512b2c0b77c978ac309a7130d2729480b786e02589b3", "rd() changed in figs_thesis.py"


def rng(vals, n=2):
    return f"{rd(min(vals), n)}–{rd(max(vals), n)}"


# ------------------------------------------------------------------ style (eval/thesis_style.py, RS-1/D124)
sys.path.insert(0, HERE)
import thesis_style as TS
C, MK = TS.C, TS.MK
INK, INK2, GRID, SURF, TRUTH = TS.INK, TS.INK2, TS.GRID, TS.SURF, TS.TRUTH
plt.rcParams.update(TS.RCPARAMS)
FW = TS.TEXT_WIDTH_IN

# ------------------------------------------------------------------ bookkeeping: checks, text-number guard, per-figure save
CHK = []; TXT = []; ITEMS = []

# source display files the "shown" cross-check reads from (same role as figs_walkthrough_extra.py's DISPF): an
# expected string is not just hand-typed here, it must also occur verbatim in the file it is quoted from.
SHOWF = {"E4": os.path.join(T1D, "e4_results.md"), "E6": os.path.join(T1D, "e6_results.md"),
         "E6PR": os.path.join(T1D, "e6_preregistration.md"), "AB": os.path.join(ABD, "ablation_numbers.md"),
         "PR": os.path.join(T1D, "preregistration.md"), "PRA": os.path.join(ABD, "preregistration.md"),
         "T8": os.path.join(ROOT, "docs", "thesis", "tables", "T8_hindsight_ratio.md")}
_SHOWC = {}


def shown_text(k):
    return _SHOWC.setdefault(k, open(SHOWF[k], encoding="utf-8").read())


def check(fid, label, computed, expected, src, shown=()):
    """EXACT string equality; `shown`: [(file key, substring), ...] - each substring must ALSO occur verbatim in
    SHOWF[key], so the expected string is not just a hand-typed constant but is tied to the thesis source file it
    was copied from (same role as figs_walkthrough_extra.py's `shown=` parameter)."""
    c, e = str(computed), str(expected); ok = c == e
    for k, s_ in shown:
        f_ = s_ in shown_text(k); ok &= f_
        if not f_:
            print("   SHOWN FAIL:", fid, label, k, repr(s_))
    CHK.append(dict(fid=fid, label=label, computed=c, expected=e, src=src, ok=ok))
    if not ok:
        print("   CHECK FAIL:", fid, label, repr(c), repr(e), src)
    return c


def T(s):
    TXT.append(s); return s


import re
NUMTOK = re.compile(r"\d+(?:\.\d+)?")


def save_fig(fid, fig, title, caption_body, inputs, rows):
    """Writes D0x.png/.pdf, the caption (candidates/captions/<fid>.md) and records the index row. `rows`: list of
    TA_verdicts.md ID-column strings this candidate's content covers (empty -> 'none (descriptive)'), optionally
    prefixed 'Extension E4 '/'Extension E6 ' for reader disambiguation (stripped before the ID-column check)."""
    # number guard: every number drawn on THIS figure (via T()), AND every number in the caption text, must occur in
    # one of THIS figure's own passing checks (the brief: "every number on a figure or in a caption must be in an
    # exact cross-check").
    allowed = set()
    for c in CHK:
        if c["fid"] == fid and c["ok"]:
            allowed |= set(NUMTOK.findall(c["computed"])) | set(NUMTOK.findall(c["expected"]))
    stray = sorted({t for s in TXT for t in NUMTOK.findall(s.replace("EKF3", "EKF"))} - allowed)
    assert not stray, f"{fid}: number(s) {stray} drawn on the figure without a passing check"
    cap_stray = sorted(set(NUMTOK.findall(caption_body)) - allowed)
    assert not cap_stray, f"{fid}: number(s) {cap_stray} in the caption without a passing check"
    for s in TXT:
        assert "—" not in s, f"{fid}: em-dash in '{s}'"
    assert "—" not in caption_body, f"{fid}: em-dash in the caption"
    for a_ in fig.axes:
        assert a_.get_xscale() == "linear" and a_.get_yscale() == "linear", f"{fid}: a non-linear axis"
    for t_ in fig.findobj(matplotlib.text.Text):
        tt = t_.get_text()
        for bad in ("PASS", "FAIL", "NOT MET", "MISS", " MET", "Verdict"):
            assert bad not in tt, f"{fid}: verdict word {bad!r} drawn on the figure: {tt!r}"
    BANNED = re.compile(r"\b(pass(?:es|ed|ing)?|fail(?:s|ed|ing)?|not\s+met|met|miss(?:es|ed|ing)?|verdicts?)\b", re.IGNORECASE)
    hits = sorted(set(w.group(0) for w in BANNED.finditer(caption_body)))
    assert not hits, f"{fid}: banned verdict word(s) {hits} in the caption body (D113)"
    verdict = (f"Verdicts: Table A.4, rows {'; '.join(rows)}." if rows else "Verdicts: Table A.4, none (descriptive).")
    cap = caption_body.strip() + "\n\n" + verdict
    open(os.path.join(CAPD, f"{fid}.md"), "w").write(f"{title}.\n\n{cap}\n")
    base = os.path.join(OUTD, fid)
    try:
        fig.tight_layout()
    except Exception:
        pass
    fig.savefig(base + ".png", dpi=200); fig.savefig(base + ".pdf"); plt.close(fig)
    myc = [c for c in CHK if c["fid"] == fid]
    ok = all(c["ok"] for c in myc)
    ITEMS.append(dict(id=fid, title=title, inputs=inputs, rows=rows, nchk=len(myc), nok=sum(c["ok"] for c in myc), ok=ok))
    print(f"wrote {base}.png/.pdf  checks {sum(c['ok'] for c in myc)}/{len(myc)}")


# ------------------------------------------------------------------ TA_verdicts.md ID-column values (for the row-id sanity check)
TA_IDS = set()
for _ln in open(TAPATH, encoding="utf-8"):
    if not _ln.startswith("|"):
        continue
    _parts = _ln.split("|")
    if len(_parts) < 3 or _parts[1].strip() in ("Experiment", "---"):
        continue
    TA_IDS.add(_parts[2].strip())


def assert_rows(fid, rows):
    for r in rows:
        bare = r.split(" ", 2)[-1] if r.startswith(("Extension ", "Experiment ")) else r
        assert bare in TA_IDS, f"{fid}: row id {r!r} (bare {bare!r}) not a literal TA_verdicts.md ID-column value"


# =================================================================== shared E4 data (COPIED loaders: figs_walkthrough_extra.py /
# figs_thesis_summary.py "E4, step time against the window" / "E4, live error against the window" sections)
TCOND = "ABCD"; TAGS = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
FLT = [f"T_{c}_r{i}" for c in TCOND for i in (1, 2, 3)]
E4V = LT("E4_verdicts.json"); WS = [0.25, 0.5, 1, 2, 5]; WK = ["0.25", "0.5", "1", "2", "5"]
MED4 = {w: [E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][i] for t in FLT] for i, w in enumerate(WS)}
EXP4 = {0.25: "14.35–15.13", 0.5: "26.86–28.22", 1: "50.47–52.74", 2: "100.05–107.12", 5: "278.25–303.36"}


def e4live(t, w):
    tr = LT(f"E4_{t}_w{w}.json")["tracks"]; ks = [k for k in tr if k.startswith("FGO live")]
    assert len(ks) == 1
    return tr[ks[0]]["horiz_err_m"]["rmse"]


LW = {t: {w: e4live(t, w) for w in WK} for t in FLT}
H43 = E4V["H-E4.3"]
D43 = {t: H43["per_flight"][t]["L5_m"] - H43["per_flight"][t]["L0.25_m"] for t in FLT}
LOW = {t: H43["per_flight"][t]["lower_at_5"] for t in FLT}
RAT = [E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][4] / E4V["P-E4.1"]["per_flight"][t]["medians_after_anchor_ms"][0] for t in FLT]


def halves(key, s):
    """[(key, half) for half in a '<lo>–<hi>' range string] - the 'shown' form used by figs_walkthrough_extra.py's
    V4S checks (each half of the range verified present in the thesis results file, not the joined string)."""
    return [(key, h) for h in s.split("–")]


BUDGET_PHRASE = "the 33 ms deployability budget (M:707-721)"
WINDOWS_PHRASE = "0.25 < 0.5 < 1 < 2 < 5 s"

# =================================================================== D01: E4, live error against compute time, ONE axis
# (walkthrough page 17e / ex_E4_err_compute.png; same encoding as summary page 21 E4_error_vs_compute - ONE candidate covers
# both source pages, since they draw the same data the same way).
TXT = []; fid = "D01"
check(fid, "extension label", "E4", "E4", "pre-registration")
for w in WS:
    check(fid, f"W = {w} s: median step time after the anchor, lowest-highest over 12 flights (ms)", rng(MED4[w], 2), EXP4[w],
          "E4_verdicts.json P-E4.1.per_flight.<t>.medians_after_anchor_ms", shown=halves("E4", EXP4[w]))
VRAT = check(fid, "5 s / 0.25 s median step time per flight, lowest-highest of 12 (x, whole numbers)", f"{rd(min(RAT), 0)}–{rd(max(RAT), 0)}",
             "19–20", "E4_verdicts.json")
_DW = [LW[t][w] - LW[t]["0.25"] for t in FLT for w in WK[1:]]
VMX = check(fid, "largest |change in live RMSE from the 0.25 s value| over every longer window and flight, strictly under 0.01 m",
            str(max(abs(v) for v in _DW) < 0.01), "True", "score files (cap 2)")
VH43N = check(fid, "flights with lower live error at W = 5 s than at W = 0.25 s, of 12", f"{sum(LOW.values())}/12", "7/12",
              "E4_verdicts.json H-E4.3.per_flight.<t>.lower_at_5")
BUD = check(fid, "deployability budget (ms)", "33", "33", "pre-registration P-E4.2", shown=[("PR", BUDGET_PHRASE)])
assert VMX == "True"
check(fid, "bound quoted in the caption (m)", "0.01", "0.01", "this script (asserted above)")
check(fid, "repeats per condition", "3", "3", "E4 runs T_<c>_r1-r3")
for c in TCOND:
    check(fid, f"condition {c}: number of tags", TAGS[c], TAGS[c], "Table 5.2", shown=[("T8", TAGS[c])])
check(fid, "windows swept (s)", " / ".join(WK), "0.25 / 0.5 / 1 / 2 / 5", "pre-registration", shown=[("PR", WINDOWS_PHRASE)])

fig, ax = plt.subplots(figsize=(FW, 3.9))
XL, YL = (0, 370), (0, 0.10)
ax.set_xlim(*XL); ax.set_ylim(*YL)
assert max(max(MED4[w]) for w in WS) < XL[1] and max(max(v.values()) for v in LW.values()) < YL[1]
for t in FLT:
    ax.plot([MED4[w][FLT.index(t)] for w in WS], [LW[t][w] for w in WK], color=C["FGO"], lw=1.2, marker=MK["FGO"], ms=5,
            mfc=C["FGO"], mec=C["FGO"], zorder=3, alpha=0.85)
ax.axvline(33, color=INK2, lw=1.8, ls=(0, (6, 3)), zorder=2)
ax.text(37, YL[1] * 0.97, T(f"{BUD} ms budget"), ha="left", va="top", fontsize=10, color=INK2)
ax.set_xlabel("FGO median compute time per step (ms)")
ax.set_ylabel("FGO live horizontal error, RMSE (m)")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
save_fig(fid, fig,
         "Extension E4: FGO live error against compute time, one axis",
         "Extension E4 (FGO window length sweep), tag-room replays of Experiment 2's 12 flights (conditions A-D: 8, 4, 2, 1 tags, "
         "3 repeats each). FGO live only (no other estimator), raw (room-frame, no alignment) horizontal RMSE over the 5 laps, "
         f"against the FGO's own median compute time per step after the first tag fix (a workstation diagnostic, Python, one "
         f"thread, not the flight controller). One line per flight (12), one point per window (0.25, 0.5, 1, 2, 5 s), joined in "
         f"window order (median step time increases strictly with window length on every flight, {EXP4[0.25]} ms at 0.25 s to "
         f"{EXP4[5]} ms at 5 s, a {VRAT}-times rise). Dashed vertical line: the {BUD} ms deployability budget (one camera frame). "
         f"No window moved a flight's live error by 0.01 m or more; the live error was lower at the 5 s window than at the "
         f"0.25 s window on {VH43N} flights.",
         "docs/thesis/tier1/scores/E4_verdicts.json (P-E4.1 medians after the anchor, H-E4.3); "
         "docs/thesis/tier1/scores/E4_<trial>_w<W>.json (cap 2) tracks 'FGO live' horiz_err_m.rmse",
         ["Extension E4 P-E4.1", "Extension E4 P-E4.2", "Extension E4 H-E4.3"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== D02: E4, window against compute time (box; summary page 16)
TXT = []; fid = "D02"
check(fid, "extension label", "E4", "E4", "pre-registration")
for w in WS:
    check(fid, f"W = {w} s: median step time after the anchor, lowest-highest over 12 flights (ms)", rng(MED4[w], 2), EXP4[w],
          "E4_verdicts.json P-E4.1.per_flight.<t>.medians_after_anchor_ms", shown=halves("E4", EXP4[w]))
BUD2 = check(fid, "deployability budget (ms)", "33", "33", "pre-registration P-E4.2", shown=[("PR", BUDGET_PHRASE)])
VP41 = check(fid, "P-E4.1: flights with a strictly increasing step-time median over every window, of 12", str(E4V["P-E4.1"]["count"]),
             "12/12", "E4_verdicts.json P-E4.1")
check(fid, "windows swept (s)", " / ".join(WK), "0.25 / 0.5 / 1 / 2 / 5", "pre-registration", shown=[("PR", WINDOWS_PHRASE)])
check(fid, "repeats per condition", "3", "3", "E4 runs T_<c>_r1-r3")
for c in TCOND:
    check(fid, f"condition {c}: number of tags", TAGS[c], TAGS[c], "Table 5.2", shown=[("T8", TAGS[c])])

fig, ax = plt.subplots(figsize=(FW, 3.9))
ax.set_xlim(-0.6, 5.9); ax.set_ylim(0, 340)
for i, w in enumerate(WS):
    lo, hi = min(MED4[w]), max(MED4[w]); hgt = max(hi - lo, 0.012 * 340)
    ax.add_patch(Rectangle((i - 0.18, lo - (hgt - (hi - lo)) / 2), 0.36, hgt, facecolor=C["FGO"], edgecolor=C["FGO"], lw=1.6, zorder=3))
for i, w in enumerate(WS):
    hi = max(MED4[w])
    ax.text(i, hi + 14, T(EXP4[w].replace("–", "–\n") + " ms"), ha="center", va="bottom", fontsize=9.5, linespacing=1.05)
ax.axhline(33, color=INK2, lw=1.6, ls=(0, (6, 4)), zorder=1)
ax.text(5.75, 37, T(f"{BUD2} ms budget"), ha="right", va="bottom", fontsize=10, color=INK2)
ax.set_xticks(list(range(5))); ax.set_xticklabels([T(w) for w in WK])
ax.set_xlabel("FGO window of recent measurements (s), evenly spaced, not to scale")
ax.set_ylabel("Median compute time per step (ms)")
save_fig(fid, fig,
         "Extension E4: FGO window length against compute time",
         "Extension E4, the same 12 flights as the live-error-against-compute-time figure (conditions A-D: 8, 4, 2, 1 tags, 3 "
         "repeats each), FGO live only. Each box "
         "spans the lowest to the highest of the 12 flights' median compute time per step after the first tag fix, at each of "
         "5 window lengths (0.25, 0.5, 1, 2, 5 s; a diagnostic workstation measurement, Python, one thread, not the flight "
         f"controller). The windows are evenly spaced on the axis, not to scale. Dashed line: the {BUD2} ms deployability "
         f"budget (one camera frame). The median step time increases strictly with window length on {VP41} flights.",
         "docs/thesis/tier1/scores/E4_verdicts.json P-E4.1 medians_after_anchor_ms",
         ["Extension E4 P-E4.1", "Extension E4 P-E4.2"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== D03: E4, window against live error, change from 0.25 s, one
# panel per tag count, shared y-scale (summary page 17)
TXT = []; fid = "D03"
check(fid, "extension label", "E4", "E4", "pre-registration")
DW = {t: {w: LW[t][w] - LW[t]["0.25"] for w in WK} for t in FLT}
check(fid, "repeats per condition (flights per panel)", "3", "3", "E4 runs T_<c>_r1-r3")
for c in TCOND:
    check(fid, f"condition {c}: number of tags", TAGS[c], TAGS[c], "Table 5.2", shown=[("T8", TAGS[c])])
_E4R25 = {"A": "0.0190–0.0214", "B": "0.0233–0.0292", "C": "0.0502–0.0565", "D": "0.0745–0.0931"}
V25 = {c: check(fid, f"{TAGS[c]}: live RMSE at W = 0.25 s, lowest-highest of 3 flights (m)", rng([LW[t]["0.25"] for t in FLT if t[2] == c], 4),
               _E4R25[c], "score files", shown=halves("E4", _E4R25[c])) for c in TCOND}


def chg(cs):
    return [DW[t][w] for t in FLT if t[2] in cs for w in WK[1:]]


from decimal import Decimal, ROUND_CEILING


def ceil_s(v, n):
    return format(Decimal(str(float(v))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_CEILING), "f")


MAB, MC, MD = (max(abs(v) for v in chg(cs)) for cs in ("AB", "C", "D"))
VBAB = check(fid, "8 or 4 tags: largest |change from 0.25 s| over every window and flight, rounded up once (m)", ceil_s(MAB, 4), "0.0003", "score files")
VBC = check(fid, "2 tags: largest |change from 0.25 s| over every window and flight, rounded up once (m)", ceil_s(MC, 3), "0.001", "score files")
VBD = check(fid, "1 tag: largest |change from 0.25 s| over every window and flight, rounded once (m)", rd(MD, 3), "0.009", "score files")
VH43N2 = check(fid, "flights with lower live error at W = 5 s than at W = 0.25 s, of 12", f"{sum(LOW.values())}/12", "7/12", "E4_verdicts.json")
check(fid, "windows swept (s)", " / ".join(WK), "0.25 / 0.5 / 1 / 2 / 5", "pre-registration", shown=[("PR", WINDOWS_PHRASE)])

YLIM = (-0.0080, 0.0110)
assert YLIM[0] < min(min(DW[t].values()) for t in FLT) and max(max(DW[t].values()) for t in FLT) < YLIM[1]
DODGE = {"1": -0.12, "2": 0.0, "3": 0.12}
fig, axs = plt.subplots(1, 4, figsize=(FW, 3.7), sharey=True)
for i, (ax, c) in enumerate(zip(axs, TCOND)):
    ax.set_ylim(*YLIM); ax.set_xlim(-0.45, 4.45)
    ax.axhline(0, color=INK2, lw=1.0, zorder=2)
    for t in FLT:
        if t[2] == c:
            r = t[-1]
            ax.plot([k + DODGE[r] for k in range(5)], [DW[t][w] for w in WK], color=C["FGO"], lw=1.2, marker=MK["FGO"], ms=5.5,
                    mfc=C["FGO"], mec=C["FGO"], zorder=4)
    ax.set_xticks(range(5)); ax.set_xticklabels([T(w) for w in WK], fontsize=9, rotation=90)
    ax.set_title(T(f"({'abcd'[i]}) {TAGS[c]}"), loc="left", fontsize=9.5)
    if i:
        ax.tick_params(labelleft=False)
axs[0].set_ylabel("Change in live error from\nits 0.25 s value (m)")
axs[0].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.3f}".replace("-", "−") if abs(v) > 1e-12 else "0"))
fig.text(0.5, 0.015, T("FGO window of recent measurements (s), evenly spaced, not to scale"), ha="center", fontsize=10)
save_fig(fid, fig,
         "Extension E4: FGO window length against live error, by tag count",
         "Extension E4, the same 12 flights and metric as the window-against-compute-time figure (FGO live, raw room-frame "
         "horizontal RMSE over the 5 laps), shown "
         "as the change from each flight's own 0.25 s value as the window lengthens; one panel per tag count, (a)-(d), one shared "
         "linear y-scale. One line per flight (3 per panel, nudged sideways so equal values stay visible); windows evenly spaced, "
         f"not to scale. At 0.25 s the live RMSE is {V25['A']} m (8 tags), {V25['B']} m (4 tags), {V25['C']} m (2 tags) and "
         f"{V25['D']} m (1 tag). With 8 or 4 tags the window changes the live error by under {VBAB} m; with 2 tags by under "
         f"{VBC} m; with 1 tag the changes are larger, up to about {VBD} m. The live error was lower at the 5 s window than at "
         f"the 0.25 s window on {VH43N2} flights.",
         "docs/thesis/tier1/scores/E4_<trial>_w<W>.json (cap 2) tracks 'FGO live' horiz_err_m.rmse; E4_verdicts.json H-E4.3",
         ["Extension E4 H-E4.3"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== D04: E4 two-panel compute/accuracy trade-off (walkthrough
# page 17, ex_E4_tradeoff.png - a USER-APPROVED two-panel exception, different y-scales (D124 brief)).
TXT = []; fid = "D04"
check(fid, "extension label", "E4", "E4", "pre-registration")
for w in WS:
    check(fid, f"W = {w} s: median step time after the anchor, lowest-highest over 12 flights (ms) [D04]", rng(MED4[w], 2), EXP4[w],
          "E4_verdicts.json P-E4.1.per_flight.<t>.medians_after_anchor_ms", shown=halves("E4", EXP4[w]))
BUD4 = check(fid, "deployability budget (ms) [D04]", "33", "33", "pre-registration P-E4.2", shown=[("PR", BUDGET_PHRASE)])
VP41b = check(fid, "P-E4.1: flights with a strictly increasing step-time median over every window, of 12 [D04]", str(E4V["P-E4.1"]["count"]),
              "12/12", "E4_verdicts.json P-E4.1")
VH43N3 = check(fid, "flights with lower live error at W = 5 s than at W = 0.25 s, of 12 [D04]", f"{sum(LOW.values())}/12", "7/12", "E4_verdicts.json")
check(fid, "windows swept (s) [D04]", " / ".join(WK), "0.25 / 0.5 / 1 / 2 / 5", "pre-registration", shown=[("PR", WINDOWS_PHRASE)])

fig, (axl, axr) = plt.subplots(1, 2, figsize=(FW, 3.9))
axl.set_xlim(-0.6, 5.0); axl.set_ylim(0, 350)
for i, w in enumerate(WS):
    lo, hi = min(MED4[w]), max(MED4[w]); hgt = max(hi - lo, 0.012 * 340)
    axl.add_patch(Rectangle((i - 0.18, lo - (hgt - (hi - lo)) / 2), 0.36, hgt, facecolor=C["FGO"], edgecolor=C["FGO"], lw=1.6, zorder=3))
axl.axhline(33, color=INK2, lw=1.6, ls=(0, (6, 4)), zorder=1)
axl.text(4.95, 40, T(f"{BUD4} ms budget"), ha="right", va="bottom", fontsize=9.5, color=INK2)
axl.set_xticks(list(range(5))); axl.set_xticklabels([T(w) for w in WK])
axl.set_xlabel("FGO window (s), not to scale"); axl.set_ylabel("Median compute time per step (ms)")
axl.set_title(T("(a) compute time"), loc="left", fontsize=10.5)
axr.set_xlim(-0.6, 5.0); axr.set_ylim(0, 0.10)
for t in FLT:
    axr.plot(list(range(5)), [LW[t][w] for w in WK], color=C["FGO"], lw=1.1, marker=MK["FGO"], ms=4.8, mfc=C["FGO"], mec=C["FGO"],
             zorder=3, alpha=0.85)
axr.set_xticks(list(range(5))); axr.set_xticklabels([T(w) for w in WK])
axr.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
axr.set_xlabel("FGO window (s), not to scale"); axr.set_ylabel("FGO live horizontal error, RMSE (m)")
axr.set_title(T("(b) live error"), loc="left", fontsize=10.5)
save_fig(fid, fig,
         "Extension E4: compute time and live error against window length (two panels, different y-scales)",
         "Extension E4, the same 12 flights as the other E4 figures (FGO live, raw room-frame horizontal RMSE over the 5 laps). "
         "Two panels on "
         "different y-scales: compute time in ms (a), live error in m (b). (a) median compute time per step after the first tag "
         "fix (workstation diagnostic), box = lowest to highest of the 12 flights, at each window; dashed line: the 33 ms "
         "deployability budget. (b) absolute live error, one line per flight (12), one point per window, joined in window order. "
         f"Both panels share the same x positions (0.25, 0.5, 1, 2, 5 s, evenly spaced, not to scale). The median step time "
         f"increases strictly with window length on {VP41b} flights; the live error was lower at the 5 s window than at the "
         f"0.25 s window on {VH43N3} flights.",
         "docs/thesis/tier1/scores/E4_verdicts.json (P-E4.1 medians after the anchor, H-E4.3); "
         "docs/thesis/tier1/scores/E4_<trial>_w<W>.json (cap 2) tracks 'FGO live' horiz_err_m.rmse",
         ["Extension E4 P-E4.1", "Extension E4 P-E4.2", "Extension E4 H-E4.3"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== shared E6 data (COPIED loaders: figs_walkthrough_extra.py
# "E6 (summary page 20): map reuse" section)
E6V = LT("e6_verdicts.json"); E6F = E6V["flights"]; E6T = ["T_A_r1", "T_A_r2", "T_A_r3"]
ARM6 = {"sv": "(i) surveyed", "fm": "(ii) FGO map", "um": "(iii) UKF map", "nm": "(iv) no map, LC online"}
EOR6 = ("FGO", "UKF")
LAP1_6 = {(e, a): [E6F[t][e][f"{ARM6[a]} | live"]["lap1_m"] for t in E6T] for e in EOR6 for a in ARM6}
ALL6 = {(e, a): [E6F[t][e][f"{ARM6[a]} | live"]["rmse_m"] for t in E6T] for e in EOR6 for a in ARM6}
CR6 = E6V["criteria"]
EXP6_L1 = {("FGO", "fm"): "0.0303–0.0510", ("FGO", "nm"): "0.0818–0.1608", ("UKF", "fm"): "0.0389–0.0471",
           ("UKF", "nm"): "0.1560–0.2565"}
RAT6 = {e: [ALL6[(e, "fm")][i] / ALL6[(e, "sv")][i] for i in range(3)] for e in EOR6}
EXP6_R = {"FGO": "1.52–2.14", "UKF": "0.98–1.26"}
BND6 = {e: (E6V["p2_bands_m"][e]["lo"], E6V["p2_bands_m"][e]["hi"]) for e in EOR6}
EXP6_B = {"FGO": "0.0167–0.0237", "UKF": "0.0330–0.0408"}

# =================================================================== D05: E6, first lap: FGO map vs no map
TXT = []; fid = "D05"
check(fid, "extension label", "E6", "E6", "pre-registration")
check(fid, "room condition: number of tags", "8 tags", "8 tags", "Table 5.2", shown=[("T8", "8 tags")])
check(fid, "lap number referenced in the caption (first lap)", "1", "1", "this script (lap1_m)")
V6L1 = {g: check(fid, f"{g[0]} estimator, {ARM6[g[1]]}: lap-1 live RMSE, lowest-highest over 3 test flights (m)", rng(LAP1_6[g], 4), x,
               "e6_verdicts.json flights.<t>.<est>.'<arm> | live'.lap1_m", shown=[("E6", x)]) for g, x in EXP6_L1.items()}
VP4 = {e: check(fid, f"P4 ({e}): flights where the FGO-map lap-1 error is lower than the no-map lap-1 error, of 3", f"{sum(CR6[f'P4 ({e})']['per_flight'])}/3",
              "3/3", "e6_verdicts.json criteria") for e in EOR6}

fig, ax = plt.subplots(figsize=(FW, 3.6))
ax.set_xlim(-0.95, 1.75); ax.set_ylim(0, 0.37)
for j, e in enumerate(EOR6):
    xc = j * 1.3
    for i in range(3):
        xs = [xc - 0.22, xc + 0.22]; ys = [LAP1_6[(e, "fm")][i], LAP1_6[(e, "nm")][i]]
        ax.plot(xs, ys, color=C[e], lw=0.9, alpha=0.7, zorder=2)
        ax.plot(xs, ys, ls="", marker=MK[e], ms=7, color=C[e], zorder=3)
    ax.text(xc - 0.22, -0.018, T("map"), ha="center", va="top", fontsize=9, color=INK2)
    ax.text(xc + 0.22, -0.018, T("no map"), ha="center", va="top", fontsize=9, color=INK2)
ax.set_xticks([0, 1.3]); ax.set_xticklabels([f"{e}" for e in EOR6]); ax.tick_params(axis="x", pad=16)
ax.set_ylabel("Live error, first lap (m)")
ax.legend(handles=[Line2D([], [], ls="-", marker=MK[e], color=C[e], ms=7, label=e) for e in EOR6], frameon=False, loc="upper left")
save_fig(fid, fig,
         "Extension E6: first-lap live error, a reused FGO map against no map",
         "Extension E6 (map reuse), the tag-room test flights (3 repeats, 8-tag room), replayed through both the FGO and the "
         "UKF, live tracks, first lap only, raw (world-frame, no alignment) horizontal RMSE. Each point is one of the 3 test "
         "flights, joined map-to-no-map; colour = the estimator (both are tested against a tag map built in hindsight from an "
         "earlier, out-of-sample mapping flight). 'map' = the FGO-built map used as if exact; 'no map' = loop closure "
         f"re-identifying tags online, no prior map. Lap-1 live RMSE on the FGO map: {V6L1[('FGO','fm')]} m (FGO), "
         f"{V6L1[('UKF','fm')]} m (UKF); with no map: {V6L1[('FGO','nm')]} m (FGO), {V6L1[('UKF','nm')]} m (UKF). The FGO-map "
         f"lap-1 error was lower than the no-map lap-1 error on {VP4['FGO']} flights (FGO) and {VP4['UKF']} flights (UKF).",
         "docs/thesis/tier1/scores/e6_verdicts.json (flights, criteria), e6_T_A_r{1,2,3}.json",
         ["Extension E6 P4 (FGO)", "Extension E6 P4 (UKF)"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== D06: E6, whole flight on the FGO map against the surveyed band
TXT = []; fid = "D06"
check(fid, "extension label", "E6", "E6", "pre-registration")
check(fid, "laps per flight", "5", "5", "tag-room flight design (5 laps)")
V6R = {e: check(fid, f"{e} estimator: FGO map / surveyed map, overall live RMSE, lowest-highest (x)", rng(RAT6[e], 2), x,
               "e6_verdicts.json (rmse_m, arms ii / i)", shown=[("E6", x)]) for e, x in EXP6_R.items()}
V6B = {e: check(fid, f"{e} estimator: surveyed-map band for P2 [min - R, max + R] (m)", f"{rd(BND6[e][0], 4)}–{rd(BND6[e][1], 4)}", x,
               "e6_verdicts.json p2_bands_m") for e, x in EXP6_B.items()}
VP2 = {e: check(fid, f"P2 ({e}): flights where the FGO-map whole-flight error lies inside the surveyed-map band, of 3", f"{sum(CR6[f'P2 ({e})']['per_flight'])}/3",
              x, "e6_verdicts.json criteria") for e, x in (("FGO", "0/3"), ("UKF", "2/3"))}
BAND_PHRASE = "the band extends the observed repeat interval by one range on each side"
check(fid, "band derivation quoted verbatim from the pre-registration", BAND_PHRASE, BAND_PHRASE, "e6_preregistration.md:208",
      shown=[("E6PR", BAND_PHRASE)])

fig, ax = plt.subplots(figsize=(FW, 3.6))
ax.set_xlim(-0.55, 1.55); ax.set_ylim(0, 0.064)
for j, e in enumerate(EOR6):
    lo, hi = BND6[e]
    ax.add_patch(Rectangle((j - 0.32, lo), 0.64, hi - lo, facecolor=TRUTH, alpha=0.35, lw=0, zorder=1))
    ys = ALL6[(e, "fm")]
    ax.plot([j] * 3, ys, ls="", marker=MK[e], ms=7, color=C[e], zorder=3)
ax.set_xticks([0, 1]); ax.set_xticklabels([f"{e}" for e in EOR6]); ax.tick_params(axis="x", pad=8)
ax.set_ylabel("Live error, whole flight (m)")
ax.legend(handles=[Line2D([], [], ls="", marker=MK[e], color=C[e], ms=7, label=f"{e}, FGO map, live") for e in EOR6] +
                  [Rectangle((0, 0), 1, 1, facecolor=TRUTH, alpha=0.35, lw=0, label="surveyed-map band")],
          frameon=False, loc="upper left")
save_fig(fid, fig,
         "Extension E6: whole-flight live error on a reused FGO map against the surveyed-map band",
         "Extension E6, the same 3 test flights as the first-lap figure, live tracks, whole flight (5 laps), raw (world-frame, "
         "no alignment) "
         "horizontal RMSE, estimated using the map built in hindsight from an earlier mapping flight ('FGO map'). Grey band: "
         "the same estimator's live error range on the surveyed (ground-truth) tag positions; the band extends that observed "
         f"repeat interval by one range on each side (the pre-registered P2 band). FGO-map / surveyed-map ratio, "
         f"lowest-highest over 3 flights: {V6R['FGO']} x (FGO), {V6R['UKF']} x (UKF); bands {V6B['FGO']} m (FGO), "
         f"{V6B['UKF']} m (UKF). The FGO-map whole-flight error fell inside the surveyed-map band on {VP2['FGO']} flights "
         f"(FGO) and {VP2['UKF']} flights (UKF).",
         "docs/thesis/tier1/scores/e6_verdicts.json (flights, criteria, p2_bands_m), e6_T_A_r{1,2,3}.json",
         ["Extension E6 P2 (FGO)", "Extension E6 P2 (UKF)"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== D07: E6, map-error difference against live-error difference
TXT = []; fid = "D07"
check(fid, "extension label", "E6", "E6", "pre-registration")
MAPD = [E6F[t]["map"]["ukf_map_pos_rms_m"] - E6F[t]["map"]["fgo_map_pos_rms_m"] for t in E6T]
LIVD = {e: [ALL6[(e, "um")][i] - ALL6[(e, "fm")][i] for i in range(3)] for e in EOR6}
check(fid, "flight id referenced in the caption (r1b)", "1", "1", "e6_verdicts.json pairs (E6M_fig8_r1b -> T_A_r1)")
GAP1 = check(fid, "r1b: the two maps' position RMS differ by (m)", rd(abs(MAPD[0]), 4), "0.0007", "e6_verdicts.json flights.T_A_r1.map")
SGN6 = check(fid, "sign of (live UKF map - live FGO map) equals the sign of (UKF-map RMS - FGO-map RMS), flights, per estimator",
             " ".join(f"{e} {sum((LIVD[e][i] > 0) == (MAPD[i] > 0) for i in range(3))}/3" for e in EOR6), "FGO 3/3 UKF 3/3",
             "e6_verdicts.json flights.<t>.map and rmse_m")
P1N = check(fid, "P1: mapping flights where the FGO map had the lower landmark position RMS, of 3", f"{sum(CR6['P1']['per_flight'])}/3", "2/3",
            "e6_verdicts.json criteria")
P3N = {e: check(fid, f"P3 ({e}): test flights where the live error was lower on the FGO map than the UKF map, of 3", f"{sum(CR6[f'P3 ({e})']['per_flight'])}/3",
              "2/3", "e6_verdicts.json criteria") for e in EOR6}

fig, ax = plt.subplots(figsize=(FW, 3.8))
ax.set_xlim(-0.006, 0.024); ax.set_ylim(-0.014, 0.03)
ax.axhline(0, color=INK2, lw=0.9, zorder=1); ax.axvline(0, color=INK2, lw=0.9, zorder=1)
for e in EOR6:
    ax.plot(MAPD, LIVD[e], ls="", marker=MK[e], ms=7, color=C[e], zorder=3)
ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.01)); ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.01))
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}"))
ax.set_xlabel("Map error difference (m), UKF map minus FGO map")
ax.set_ylabel("Live error difference (m),\nUKF map minus FGO map")
ax.legend(handles=[Line2D([], [], ls="", marker=MK[e], color=C[e], ms=7, label=e) for e in EOR6], frameon=False, loc="upper left")
save_fig(fid, fig,
         "Extension E6: map-error difference against live-error difference",
         "Extension E6, the same 3 mapping flights and paired test flights as the other two E6 figures. x: the hindsight "
         "landmark position RMS of "
         "the UKF-built map minus the FGO-built map (one value per mapping flight, both estimators share it). y: the matched test "
         "flight's live horizontal RMSE on the UKF map minus the live RMSE on the FGO map, world frame, no alignment, computed "
         "separately for the FGO and the UKF (so two points per mapping flight, one per estimator). A point above and right of "
         "the origin means the map with the lower landmark error also gave the lower live error. DESCRIPTIVE: on r1b the two "
         f"maps' position RMS differ by {GAP1} m; the sign of the live-error difference matched the sign of the map-error "
         "difference on 3 of 3 mapping flights for each estimator. The FGO map had the lower landmark position RMS on "
         f"{P1N} mapping flights; its live error was lower than the UKF map's on {P3N['FGO']} flights (FGO) and "
         f"{P3N['UKF']} flights (UKF).",
         "docs/thesis/tier1/scores/e6_verdicts.json (flights.<t>.map, flights.<t>.<est>.'<arm> | live'.rmse_m, criteria)",
         ["Extension E6 P1", "Extension E6 P3 (FGO)", "Extension E6 P3 (UKF)"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== D08: ablation (EXPLORATORY), fitted cruise error per rung
# against the stored UKF band (summary/walkthrough page 19)
TXT = []; fid = "D08"
ABR = json.load(open(os.path.join(ABD, "ablation_results.json")))
FW3 = ["fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3"]; RUNG = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]
check(fid, "number of rungs swept", "8", "8", "ablation/preregistration.md (r0-r7)")
check(fid, "P2 pass threshold on R(r3)", "0.5", "0.5", "ablation/preregistration.md:221", shown=[("PRA", "R_i(r3) ≥ 0.5")])
AV = {(g, b): ABR["runs"][f"{g}.{b}.heading"]["ate_a_cruise_m"] for g in RUNG for b in FW3}
UK = [ABR["stored"][b]["U_heading"] for b in FW3]
VUK = check(fid, "stored UKF with heading, the 3 line-textured bags, lowest-highest (m)", rng(UK, 3), "0.127–0.137",
            "ablation_results.json stored", shown=[("AB", "0.127"), ("AB", "0.137")])
VFA = check(fid, "FGO, all plotted rungs, lowest-highest (m)", rng(list(AV.values()), 3), "0.044–0.065",
            "ablation_results.json runs", shown=[("AB", "0.044"), ("AB", "0.065")])
R3v = [ABR["R"][f"r3.{b}"] for b in FW3]
VR3 = check(fid, "retention R(r3) on the 3 line-textured bags, lowest-highest", f"{rd(min(R3v), 2)}-{rd(max(R3v), 2)}", "0.97-1.01",
            "ablation_results.json R", shown=[("AB", "1.01, 0.97, 0.98")])
P2A, P3A = ABR["P2"], ABR["P3"]
VN2 = check(fid, "P2 (with heading): line-textured bags where R(r3) is at least 0.5 (half the FGO-UKF gap), of 3",
            f"{P2A['n_pass']}/3", "3/3", "ablation_results.json P2")
# P3 is reported over 6 bags (3 fwdc + 3 fwdplainc); only the 3 line-textured (fwdc) bags are plotted here, so the
# in-caption count is recomputed from the SAME stored per-bag flags, filtered to the plotted bags only (not the
# 4/6, 2/6 headline counts, which include the plain-wall bags this figure does not draw).
N_R6 = sum(P3A["bags"][b]["r6_within"] for b in FW3); N_R7 = sum(P3A["bags"][b]["r7_within"] for b in FW3)
VN3 = check(fid, "P3 (descriptive): line-textured bags where r6 stays within its control band of r0, of 3", f"{N_R6}/3", "3/3",
            "ablation_results.json P3.bags.<fwdc_tex_*>.r6_within")
VN3b = check(fid, "P3 (descriptive): line-textured bags where r7 stays within its control band of r3, of 3", f"{N_R7}/3", "1/3",
             "ablation_results.json P3.bags.<fwdc_tex_*>.r7_within")
HUBER = check(fid, "robust weighting: Huber parameter", "1.345", "1.345", "ablation/preregistration.md", shown=[("PRA", "Huber 1.345")])

RL = {"r0": "r0\n0.25s\ncap2", "r1": "r1\n1 kf\ncap1", "r2": "r2\n1 kf\ncap2", "r3": "r3\n1 kf\ncap100", "r4": "r4\n1s\ncap2",
      "r5": "r5\n2s\ncap2", "r6": "r6\n0.25s\nrobust", "r7": "r7\n1 kf\nrobust"}
for g, ph in (("r0", "| `r0_w0.25_lm2` | 0.25 | 2 |"), ("r1", "| `r1_kf1_lm1` | 0.01 | 1 |"), ("r2", "| `r2_kf1_lm2` | 0.01 | 2 |"),
              ("r3", "| `r3_kf1_lm100` | 0.01 | 100 |"), ("r4", "| `r4_w1_lm2` | 1 | 2 |"), ("r5", "| `r5_w2_lm2` | 2 | 2 |"),
              ("r6", "| `r6_w0.25_lm2_huber` | 0.25 | 2 |"), ("r7", "| `r7_kf1_lm100_huber` | 0.01 | 100 |")):
    check(fid, f"rung {g}: window (s) and iteration cap (verbatim from the pre-registration table)", ph, ph,
          "ablation/preregistration.md", shown=[("PRA", ph)])
fig, ax = plt.subplots(figsize=(FW, 3.9))
ax.set_xlim(-0.6, 7.6); ax.set_ylim(0, 0.16)
ax.axhspan(min(UK), max(UK), color=C["UKF"], alpha=0.20, lw=0, zorder=1)
for u in UK:
    ax.axhline(u, color=C["UKF"], lw=1.3, ls=(0, (5, 3)), zorder=2)
for j, g in enumerate(RUNG):
    for k, b in enumerate(FW3):
        ax.plot(j + (k - 1) * 0.18, AV[(g, b)], marker="D" if g in ("r6", "r7") else MK["FGO"], color=C["FGO"],
                ms=7 if g in ("r6", "r7") else 7.5, ls="none", zorder=4)
ax.set_xticks(range(8)); ax.set_xticklabels([T(RL[g]) for g in RUNG], fontsize=9)
ax.set_ylabel("Fitted cruise error (m)")
ax.legend(handles=[Line2D([], [], ls="none", marker=MK["FGO"], color=C["FGO"], ms=7, label="FGO, Gaussian weighting"),
                   Line2D([], [], ls="none", marker="D", color=C["FGO"], ms=6.5, label="FGO, robust weighting"),
                   Rectangle((0, 0), 1, 1, facecolor=C["UKF"], alpha=0.20, label="UKF with heading (stored)")],
          frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.42), fontsize=9)
save_fig(fid, fig,
         "Ablation (EXPLORATORY): FGO window and iteration count against the stored UKF band",
         "EXPLORATORY: not a thesis hypothesis test; the FGO's own pre-registration for this ablation is signed off separately "
         "(docs/thesis/ablation/preregistration.md). Fitted cruise ATE (evo -a, a best-fit SE(3) alignment over the cruise "
         "window, not a raw error), 3 line-textured-wall flights (fwdc_tex_r1-r3), the FGO replayed with the camera heading, "
         "for 8 rungs of window length and LM iteration cap: r0 = the thesis FGO (0.25 s window, iteration cap 2); r1-r3 = a "
         "one-keyframe window (0.01 s) at iteration caps 1, 2 and 100 (cap 100: convergence not confirmed, iterations not "
         "logged); r4 = 1 s window, cap 2; r5 = 2 s window, cap 2; r6 = 0.25 s window with robust (Huber "
         f"{HUBER}) weighting in place of the heading gate; r7 = one-keyframe window, cap 100, robust weighting. Square "
         f"markers: Gaussian weighting (r0-r5); diamond markers: robust weighting (r6, r7). Shaded band: the stored UKF with "
         f"the camera heading on the same 3 flights ({VUK} m). The FGO's fitted error over all plotted rungs is {VFA} m. "
         f"Collapsing the window to one keyframe (r3, iteration cap 100) gave a retention R(r3) of {VR3} against the FGO-UKF "
         f"gap on the 3 bags, at least 0.5 on {VN2} of them. Against r0 (Gaussian), r6 (robust) stayed within its control band "
         f"on {VN3} bags; against r3, r7 stayed within its control band on {VN3b} bags.",
         "docs/thesis/ablation/ablation_results.json (runs, stored, R, P3)",
         ["P2 (with heading)", "P3 (descriptive)"])
assert_rows(fid, ITEMS[-1]["rows"])

# =================================================================== index
n_tot = len(CHK); n_ok = sum(c["ok"] for c in CHK)
lines = ["# Candidate thesis figures, group D: index",
         "",
         f"*Generated by `eval/figs_cand_d.py` at commit `{COMMIT}`. Stored results only: nothing re-run, no flight, no "
         "estimator replay, no simulation. Scope: Extension E4 (FGO window vs compute time / live error) and Extension E6 (map "
         "reuse), plus the exploratory window/iteration ablation. Decision D124.*",
         "",
         f"**Cross-checks: {n_ok}/{n_tot} EXACT** (the stored full-precision value, rounded once by `rd()` parsed from "
         "`eval/figs_thesis.py`, equals the expected string character for character; no tolerance).",
         "",
         "| id | proposed title | source chart(s) | data files | checks | verdict pointer |",
         "|---|---|---|---|---|---|"]
TITLES = {
    "D01": "FGO live error against compute time, one axis",
    "D02": "FGO window length against compute time",
    "D03": "FGO window length against live error, by tag count",
    "D04": "FGO compute time and live error against window length (two panels)",
    "D05": "Map reuse: first-lap live error, map against no map",
    "D06": "Map reuse: whole-flight live error against the surveyed-map band",
    "D07": "Map reuse: map-error difference against live-error difference",
    "D08": "Ablation (EXPLORATORY): FGO window/iteration count against the stored UKF band",
}
SRC = {
    "D01": "walkthrough `extra/ex_E4_err_compute.png` (page 17e); summary page 21 `E4_error_vs_compute` (same data/encoding, one candidate covers both)",
    "D02": "summary page 16 `E4_step_time`",
    "D03": "summary page 17 `E4_accuracy`",
    "D04": "walkthrough `extra/ex_E4_tradeoff.png` (page 17; user-approved two-panel exception)",
    "D05": "walkthrough `extra/ex_E6_map_reuse.png` (page 20) panel (a); summary page 20 `E6_map_reuse` left panel",
    "D06": "walkthrough `extra/ex_E6_map_reuse.png` (page 20) panel (b); summary page 20 `E6_map_reuse` right panel",
    "D07": "walkthrough `extra/ex_E6_map_reuse.png` (page 20) panel (c) (no summary-page equivalent)",
    "D08": "summary page 19 `ablation`; walkthrough page 19 (embeds the same summary-page chart, one candidate covers both)",
}
for it in ITEMS:
    fid = it["id"]
    lines.append(f"| {fid} | {TITLES[fid]} | {SRC[fid]} | {it['inputs']} | {it['nok']}/{it['nchk']} | "
                 f"{'rows ' + '; '.join(it['rows']) + '.' if it['rows'] else 'none (descriptive).'} |")
lines += ["",
          "## Notes",
          "",
          "- D01 and D04's right panel, and D03, all derive from the same underlying per-flight live-RMSE-by-window values "
          "(`scores/E4_<trial>_w<W>.json`), but encode them three different ways (D01: x = compute time, one line per flight; "
          "D04(b): x = window category, absolute value; D03: x = window category, change from the 0.25 s value, split by tag "
          "count) - kept as three candidates because each answers a different reading of the brief (compute-vs-error; the "
          "approved two-panel trade-off; the per-condition directional test), not because any one shows new data.",
          "- D02 and D04's left panel are the same box-plot content (step time per window); D04 is kept as its own candidate "
          "only because the brief names the two-panel compute/accuracy figure as a user-approved exception in its own right.",
          "- D05-D07 are the three panels of one source chart (`ex_E6_map_reuse.png`), split per the brief's 'separate plots, "
          "each with its own caption' instruction; the summary page 20 version only has the D05/D06 panels (a 2-panel subset), "
          "not a fourth candidate.",
          "- D08 is the only ablation chart in either source document; its walkthrough page is a full-page embed of the summary "
          "page's own figure, so one candidate covers both.",
          "- D08's pointer is `P2 (with heading); P3 (descriptive)`, not P1: the chart plots the WITH-HEADING arm of every rung "
          "(`ABR['runs'][...].heading`), and P1 (the no-heading control) is scored on a different, unplotted dataset - its "
          "n_within counts would not describe this figure's own data. P3's in-caption counts (r6 vs r0, r7 vs r3, 'within its "
          "control band') are recomputed from the same stored per-bag flags P3 uses, filtered to the 3 line-textured bags this "
          "figure actually draws, not the headline 4/6 and 2/6 counts (which also cover 3 unplotted plain-wall bags).",
          "- every number in a caption is cross-checked, not only numbers drawn on the plotted image (the save_fig() number "
          "guard scans both); several of the file-provenance ('shown') checks tie a quoted range or threshold back to its "
          "exact source sentence (docs/thesis/tier1/e4_results.md, e6_results.md, e6_preregistration.md:208, "
          "docs/thesis/ablation/ablation_numbers.md, preregistration.md), the same role as the upstream scripts' `shown=` "
          "parameter.", ""]
open(os.path.join(OUTD, "index_d.md"), "w").write("\n".join(lines))
print(f"\nTOTAL checks: {n_ok}/{n_tot}")
assert n_ok == n_tot, "not all checks passed"
