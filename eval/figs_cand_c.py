#!/usr/bin/env python3
"""GROUP C candidate thesis figures (decision D124): Extension E2 (loop closure with fewer tags), Extension E3
(wrong tag IDs, including the tag maps) and Extension E5 (UKF with landmark states).

Source charts (NOT edited by this script): docs/thesis/summary/walkthrough/wt_15_E2_fewer_tags.png /
wt_16_E3_table.png / wt_16m_E3_maps.png / wt_A1_E3_verdicts.png / wt_A2_E3_maps_app.png / wt_18_E5_ukf_landmarks.png
(eval/figs_walkthrough_extra.py, eval/figs_walkthrough_flights.py) and docs/thesis/summary/summary_13_E2_fewer_tags.png /
summary_14_E3_wrong_ids.png / summary_15_E3_verdicts.png / summary_18_E5_ukf_landmarks.png (eval/figs_thesis_summary.py).

This script REPRODUCES the same data (same loaders: docs/thesis/tier1/scores/*.json, eval/results/expL/*.json,
sim/worlds/room_tags_map.json, and -- for the tag maps only -- /ground_truth/pose from the stored bags, cached by
eval/figs_cand_c_extract.py, run under heavy.py) and restyles it to the thesis candidate rules (D124): 160 mm
(TEXT_WIDTH_IN) wide, Okabe-Ito colours/markers, filled = live / open = hindsight, no titles, no verdict words, no
check counts, no badges or explanatory notes inside axes, no bold in axes, legends only where colour/style is not
otherwise identified, no overlapping plots, side-by-side panels only on a shared scale. Every number drawn (TXT) or
written into a caption/table is required to equal a passing check's computed/expected string (NUMTOK guard, as the
restyle generators already do; extended here to caption and table text too, see `guard()`).

Where a source chart is really a table (the E3 per-run outcome and the E3 registered verdicts), this script writes
a markdown table candidate instead of (E3 outcome) or in addition to (both) a chart -- see the brief, "E3 (wrong tag
IDs)". The E3 registered-verdicts table legitimately carries PASS/FAIL words in its own .md file (same genre as
Table A.4/A1-A3): only the words in the CAPTION are banned (D113), not in a table-candidate file.

STORED OUTPUTS ONLY. No flight, no estimator replay, no simulation. The only bag reads this candidate set needs
(ground truth for the E3 tag maps) are done by the separate eval/figs_cand_c_extract.py, run once under heavy.py,
with its cache deleted by this script once every candidate here is safely on disk.

Outputs: docs/thesis/figures_thesis/candidates/C0{1,2,5,6,7}.{png,pdf}, C0{3,4}_table.{png,pdf,md},
docs/thesis/figures_thesis/candidates/captions/C0{1..7}.md, docs/thesis/figures_thesis/candidates/index_c.md.
Usage: /home/makerspace/venv-evo/bin/python eval/figs_cand_c.py"""
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results")
T1D = os.path.join(ROOT, "docs", "thesis", "tier1")
OUTD = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "candidates")
CAPD = os.path.join(OUTD, "captions")
os.makedirs(OUTD, exist_ok=True)
os.makedirs(CAPD, exist_ok=True)
INDEX = os.path.join(OUTD, "index_c.md")
CACHE = os.path.expanduser("~/thesis_data/cand_c_cache")
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

L = lambda f: json.load(open(os.path.join(RES, f)))
LT = lambda f: json.load(open(os.path.join(T1D, "scores", f)))

# ------------------------------------------------------------------ rd(): the thesis rounding rule, parsed (not run) from figs_thesis.py
FT = os.path.join(HERE, "figs_thesis.py")
_src = open(FT).read()
_rd = next(n for n in ast.parse(_src).body if isinstance(n, ast.FunctionDef) and n.name == "rd")
RD_SHA = hashlib.sha256(ast.get_source_segment(_src, _rd).encode()).hexdigest()
_ns = {}
exec(compile(ast.Module(body=[_rd], type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
assert RD_SHA == "e7320d3b8f377157c0c6512b2c0b77c978ac309a7130d2729480b786e02589b3", "rd() changed in figs_thesis.py"


def rng(vals, n=2):
    return f"{rd(min(vals), n)}–{rd(max(vals), n)}"


# ------------------------------------------------------------------ style: constants only from eval/thesis_style.py (NOT write_caption,
# which targets figures_thesis/captions/, the reader-facing directory -- this script writes its own captions to candidates/captions/).
sys.path.insert(0, HERE)
import thesis_style as TS

C, MK, TRUTH = TS.C, TS.MK, TS.TRUTH
INK, INK2, GRID, SURF = TS.INK, TS.INK2, TS.GRID, TS.SURF
EST = TS.EST
FW = TS.TEXT_WIDTH_IN           # 6.30 in = 160 mm (RS-1)
plt.rcParams.update(TS.RCPARAMS)
KEY_LH = "filled = live (during flight), open = hindsight (after landing)"

# ------------------------------------------------------------------ checks
DISPF = {"E2": "docs/thesis/tier1/e2_results.md", "E3": "docs/thesis/tier1/e3_results.md", "E5": "docs/thesis/tier1/e5_results.md",
         "PR": "docs/thesis/tier1/preregistration.md", "NT": "docs/thesis/tier1/numbers_tier1.md", "E5D": "docs/thesis/tier1/e5_design.md",
         "DL": "docs/thesis/tier1/decisions_log.md"}
_TX = {}


def _text(k):
    return _TX.setdefault(k, open(os.path.join(ROOT, DISPF[k])).read())


CHK = []
FIGS = {}
TXT = []


def check(fid, label, computed, expected, src, shown=()):
    """EXACT string equality of the computed string with the expected one; every (display key, string) in `shown` must occur in
    that display file (as in eval/figs_walkthrough_extra.py's check())."""
    c, e = str(computed), str(expected)
    ok = c == e
    where = [src]
    for k, s_ in shown:
        f = s_ in _text(k)
        ok &= f
        where.append(f"{DISPF[k]} shows '{s_}'" + ("" if f else " [NOT FOUND]"))
    CHK.append(dict(fig=fid, label=label, computed=c, expected=e, where="; ".join(where), ok=ok))
    if not ok:
        print("   CHECK FAIL:", fid, label, repr(c), repr(e), where)
    return c


def T(s):
    TXT.append(s)
    return s


NUMTOK = re.compile(r"\d+(?:\.\d+)?")
# Registered-id and candidate-id strings carry "fake numbers" that are identifiers, not claims (e.g. the 3.5 inside P-E3.5a, the
# 02 inside C02) -- stripped before the NUMTOK scan, the same fix the restyle generators apply to "EKF3" (-> "EKF") so its 3 is not
# mistaken for a claimed value. Genuine claim numbers (e.g. the 1.5 in "<= 1.5 x lap-1") are NOT matched by this pattern and are
# still required to come from a passing check().
ID_RE = re.compile(r"\b[HPS]-E\d+b?\.\d+[a-z]?\b")
CAND_RE = re.compile(r"\bC0\d")      # no trailing \b: also strips "C03" out of "C03_table.md" (underscore is a \w char)


def _strip(s):
    return CAND_RE.sub("CAND", ID_RE.sub("ID", s)).replace("EKF3", "EKF")


def allowed_for(fid):
    a = set()
    for c in CHK:
        if c["fig"] == fid and c["ok"]:
            a |= set(NUMTOK.findall(_strip(c["computed"]))) | set(NUMTOK.findall(_strip(c["expected"])))
    return a


def guard(fid, text):
    """Every number in `text` (a caption body or a table's cell text, run after the figure/table is built) must be grounded in
    a passing check() of this candidate id -- the same discipline the restyle generators apply to drawn figure text (NUMTOK),
    extended here to caption and table text, since this generator moves many numbers OFF the chart and into those two places."""
    allowed = allowed_for(fid)
    stray = sorted({t for t in NUMTOK.findall(_strip(text))} - allowed)
    assert not stray, f"{fid}: number(s) {stray} written without a passing check"


def save(fid, fig, inputs, key=False, pool=None):
    """Figure candidates: PDF + PNG, 160 mm wide, number guard (TXT), no em-dash, linear axes only, nothing off-canvas.
    `pool`: the check() fid to draw the allowed-number pool from, if different from the saved file's own id (C02's data-identity
    checks are shared with table candidate C03 under the pool id "C0203")."""
    allowed = allowed_for(pool or fid)
    stray = sorted({t for s in TXT for t in NUMTOK.findall(_strip(s))} - allowed)
    assert not stray, f"{fid}: number(s) {stray} drawn without a check"
    for s in TXT:
        assert "—" not in s, f"{fid}: em-dash in '{s}'"
    for a_ in fig.axes:
        assert a_.get_xscale() == "linear" and a_.get_yscale() == "linear", f"{fid}: a non-linear axis"
        for t_ in a_.texts + [a_.xaxis.label, a_.yaxis.label]:
            assert t_.get_fontweight() not in ("bold", "heavy"), f"{fid}: bold text in axes: {t_.get_text()!r}"
    fig.canvas.draw()
    r_ = fig.canvas.get_renderer()
    W_, H_ = fig.bbox.width, fig.bbox.height
    ticks_ = {id(t) for a_ in fig.axes for t in a_.get_xticklabels() + a_.get_yticklabels()}
    for t_ in fig.findobj(matplotlib.text.Text):
        assert "—" not in t_.get_text(), f"{fid}: em-dash in figure text"
        if t_.get_text() and t_.get_visible():
            assert t_.get_fontsize() >= 9.0, f"{fid}: text below the 9 pt floor ({t_.get_fontsize()} pt): {t_.get_text()[:50]!r}"
        if t_.get_text() and t_.get_visible() and id(t_) not in ticks_:
            b_ = t_.get_window_extent(renderer=r_)
            assert b_.x0 >= -1 and b_.x1 <= W_ + 1 and b_.y0 >= -1 and b_.y1 <= H_ + 1, f"{fid}: text runs off the figure: {t_.get_text()[:50]!r}"
    p_png = os.path.join(OUTD, f"{fid}.png")
    p_pdf = os.path.join(OUTD, f"{fid}.pdf")
    fig.savefig(p_png, dpi=200)
    fig.savefig(p_pdf)
    plt.close(fig)
    FIGS[fid] = dict(files=[os.path.relpath(p_png, ROOT), os.path.relpath(p_pdf, ROOT)], inputs=inputs,
                      numbers=sorted(allowed & {t for s in TXT for t in NUMTOK.findall(s)}), key=key)
    print(f"wrote {fid}.png/.pdf")


def write_caption(fid, text):
    p = os.path.join(CAPD, f"{fid}.md")
    with open(p, "w") as f:
        f.write(text.strip() + "\n")
    return p


def pointer_line(ids):
    if not ids:
        return "Verdicts: Table A.4, none (descriptive)."
    return "Verdicts: Table A.4, rows " + "; ".join(ids) + "."


# =================================================================== C01: Extension E2, loop closure with fewer tags
# Source: eval/figs_walkthrough_extra.py "E2_fewer_tags" (walkthrough extra page 15) and eval/figs_thesis_summary.py
# summary page 13 -- the SAME data (LAP5, E2_verdicts.json means/criteria), so ONE candidate covers both source charts.
TXT = []
TCOND = "ABCD"
TAGS = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
E2V = LT("E2_verdicts.json")
LAP5 = {("A", k): [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"lc {k}"]["per_lap_rmse_m"][4] for r in (1, 2, 3)] for k in ("live", "hindsight")}
for c in "BCD":
    for k in ("live", "hindsight"):
        LAP5[(c, k)] = [LT(f"E2_T_{c}_r{r}.json")["tracks"][f"lc {k}"]["per_lap_rmse_m"][4] for r in (1, 2, 3)]
# independent second pipeline for the hindsight means (no registered test exists, so rd(mean) vs rd(sum/3) from the SAME values
# would be circular on its own): eval/figs_walkthrough_extra.py computes the identical quantity from the identical stored values
# by a separately-written generator; its own passing check row is read here, read-only, as the second source.
_WX = {c["label"]: c for c in json.load(open(os.path.join(ROOT, "docs", "thesis", "summary", "extra", "checks.json")))["checks"]
       if c["fig"] == "E2_fewer_tags" and c["ok"]}
VM2 = {}
for c in TCOND:
    st = E2V["P-E2.5"]["means"][c]
    check("C01", f"{TAGS[c]}: the mean's inputs are the plotted lap-5 live values (stored)",
          str([v["value"] for v in st["values"]] == LAP5[(c, "live")]), "True", "E2_verdicts.json P-E2.5.means")
    VM2[(c, "live")] = check("C01", f"{TAGS[c]}: mean over 3 flights of the live lap-5 error, with loop closure (m)",
                              rd(float(np.mean(LAP5[(c, "live")])), 4), rd(st["mean_m"], 4), "E2_verdicts.json P-E2.5.means.<c>.mean_m")
    wx_lab = f"{TAGS[c]}: mean over 3 flights of the HINDSIGHT lap-5 error (m, 4 dp; computed here from the stored per-flight " \
             "values, no mean test registered)"
    VM2[(c, "hindsight")] = check("C01", f"{TAGS[c]}: mean over 3 flights of the hindsight lap-5 error (m, 4 dp; computed from the "
                                  "stored per-flight values, no mean test registered), cross-checked against the independent "
                                  "eval/figs_walkthrough_extra.py pipeline", rd(float(np.mean(LAP5[(c, "hindsight")])), 4),
                                  _WX[wx_lab]["computed"],
                                  ("expL/T_A_r<r>_t245.json" if c == "A" else f"scores/E2_T_{c}_r<r>.json") + " tracks 'lc hindsight' "
                                  "per_lap_rmse_m[4]; cross-checked against docs/thesis/summary/extra/checks.json (read-only)")
check("C01", "tag counts printed (x-axis categories, condition A = Experiment 3)", "8, 4, 2, 1 / 3", "8, 4, 2, 1 / 3",
      "tier1/e2_results.md condition definitions (B = 0,1,2,3; C = 0,2; D = 0)")
check("C01", "room geometry printed in the caption (laps, square side m)", "5 / 6", "5 / 6",
      "docs/thesis/tier1/preregistration.md ('5 laps of a 6 m square')", [("PR", "6 m square")])

fig, ax = plt.subplots(figsize=(FW, 4.0))
ax.set_xlim(-0.6, 3.6)
ax.set_ylim(0, 0.092)


def rbox(ax_, x, vals, col, filled, w=0.3):
    lo, hi = min(vals), max(vals)
    yl = ax_.get_ylim()
    h = max(hi - lo, 0.012 * (yl[1] - yl[0]))
    ax_.add_patch(Rectangle((x - w / 2, lo - (h - (hi - lo)) / 2), w, h, facecolor=col if filled else SURF, edgecolor=col, lw=1.4, zorder=3))
    return lo - (h - (hi - lo)) / 2 + h


for j, c in enumerate(TCOND):
    for k, kind in enumerate(("live", "hindsight")):
        x = j + (k - 0.5) * 0.4
        top_ = rbox(ax, x, LAP5[(c, kind)], C["FGO"], kind == "live", w=0.3)
        m_ = float(np.mean(LAP5[(c, kind)]))
        ax.plot([x - 0.19, x + 0.19], [m_, m_], color=INK, lw=1.6, zorder=5)
        ax.text(x, top_ + 0.0018, T(VM2[(c, kind)]), ha="center", va="bottom", fontsize=9, linespacing=1.0)
xtl = [T(TAGS[c]) + ("\n(Experiment 3)" if c == "A" else "") for c in TCOND]
ax.set_xticks(range(4))
ax.set_xticklabels(xtl)
ax.grid(axis="x", visible=False)
ax.set_xlabel("tags in the room, each at an unknown place")
ax.set_ylabel("FGO error on the fifth lap (m)")
leg = ax.legend(handles=[Patch(facecolor=C["FGO"], edgecolor=C["FGO"], lw=1.4, label="live, with loop closure"),
                         Patch(facecolor=SURF, edgecolor=C["FGO"], lw=1.4, label="hindsight, with loop closure"),
                         Line2D([], [], color=INK, lw=1.6, label="mean of the 3 flights")],
                frameon=False, loc="upper left", fontsize=9.0, labelspacing=0.5)
fig.tight_layout()
save("C01", fig, "docs/thesis/tier1/scores/E2_verdicts.json, E2_T_{B,C,D}_r{1,2,3}.json; eval/results/expL/T_A_r{1,2,3}_t245.json", key=True)

C01_CAP = (
    f"Extension E2 (loop closure with fewer tags; tag room, 5 laps of a 6 m square, open loop on simulator truth; the condition with "
    "8 tags re-uses the Experiment 3 flights): raw, measured from the start tag, nothing fitted. The FGO's horizontal position error "
    "on the fifth lap, root-mean-square, in the frame of "
    "the start tag, box = lowest to highest over 3 flights, solid/filled = live (with loop closure), open = hindsight (after "
    f"landing, with loop closure); black line = the mean of the 3 flights in that box (live or hindsight). The mean lap-5 live "
    "error over 3 flights is "
    f"{VM2[('A','live')]} m at 8 tags, {VM2[('B','live')]} m at 4 tags, {VM2[('C','live')]} m at 2 tags and {VM2[('D','live')]} m at "
    f"1 tag; the corresponding hindsight means (no mean test is registered for hindsight) are {VM2[('A','hindsight')]}, "
    f"{VM2[('B','hindsight')]}, {VM2[('C','hindsight')]} and {VM2[('D','hindsight')]} m. With 1 tag, that tag is the start tag, so that "
    "condition is the known-map, one-tag case."
)
guard("C01", C01_CAP)
write_caption("C01", C01_CAP + "\n\n" + pointer_line(["H-E2.1", "P-E2.5 (graded)"]))

# =================================================================== C02 / C03: Extension E3, the outcome of every run
# Source: eval/figs_walkthrough_extra.py "E3_table" (really a table, drawn with ax.text; walkthrough extra/ex_E3_table.png) and
# eval/figs_thesis_summary.py summary page 14 (a genuine scatter chart). Same underlying data (E3_verdicts.json runs/references):
# C02 is the thesis-quality CHART (one mark per run, restyled from summary page 14 -- every E3 run is LIVE, so every mark is filled,
# no open/hindsight marks here); C03 is the markdown TABLE candidate of the same data, closer to the walkthrough's own table layout.
TXT = []
E3V = LT("E3_verdicts.json")
RUNS3 = E3V["runs"]
GR3 = [("a", "0.01"), ("b", "0.01"), ("a", "0.05"), ("b", "0.05"), ("b", "0")]
LAB3 = {("a", "0.01"): "1% wrong IDs\nFGO as built", ("b", "0.01"): "1% wrong IDs\nrobust FGO", ("a", "0.05"): "5% wrong IDs\nFGO as built",
        ("b", "0.05"): "5% wrong IDs\nrobust FGO", ("b", "0"): "no wrong IDs\nrobust FGO"}
LAB3T = {("a", "0.01"): "1% wrong IDs, FGO as built (plain)", ("b", "0.01"): "1% wrong IDs, robust FGO",
         ("a", "0.05"): "5% wrong IDs, FGO as built (plain)", ("b", "0.05"): "5% wrong IDs, robust FGO", ("b", "0"): "no wrong IDs, robust FGO"}
runs3 = lambda arm, rate: sorted(n for n, r in RUNS3.items() if r["arm"] == arm and r["rate"] == rate)
DIV3 = {n: bool(RUNS3[n]["run_status"]["diverged"]) for n in RUNS3}
LIVE3 = {n: RUNS3[n]["values"]["lc live rmse_m"]["value"] for n in RUNS3}
COLL3 = {n for n in RUNS3 if RUNS3[n]["arm"] == "a" and not DIV3[n]} | {"E3b_T_A_r2_0.05_s1"}      # as figs_thesis_summary.py (decision D49)
EXP3 = {("a", "0.01"): "3.7161–3.8960", ("a", "0.05"): "4.0395–4.2231", ("b", "0.01"): "0.0496–1.4769",
        ("b", "0.05"): "0.9776–4.1849", ("b", "0"): "0.0484–0.0760"}
ROW3 = {}
for a, r in GR3:
    ns = runs3(a, r)
    fin = [LIVE3[n] for n in ns if not DIV3[n]]
    ROW3[(a, r)] = dict(n=len(ns), div=sum(DIV3[n] for n in ns), coll=sum(n in COLL3 for n in ns),
                        rng=check("C0203", f"arm ({a}) rate {r}: final live error of the finite runs, lowest–highest (m)",
                                  rng(fin, 4), EXP3[(a, r)], "E3_verdicts.json runs"))
check("C0203", "arm (a) 1%: runs diverged", f"{ROW3[('a', '0.01')]['div']} of {ROW3[('a', '0.01')]['n']}", "6 of 9", "E3_verdicts.json")
check("C0203", "arm (a) 5%: runs diverged", f"{ROW3[('a', '0.05')]['div']} of {ROW3[('a', '0.05')]['n']}", "0 of 9", "E3_verdicts.json")
check("C0203", "arm (b), every rate: runs diverged",
      f"{sum(ROW3[g]['div'] for g in GR3 if g[0] == 'b')} of {sum(ROW3[g]['n'] for g in GR3 if g[0] == 'b')}", "0 of 21", "E3_verdicts.json")
check("C0203", "arm (a) runs counted as collapsed (non-diverged)", sum(ROW3[g]["coll"] for g in GR3 if g[0] == "a"), "12", "E3 results §3")
check("C0203", "arm (b) collapsed (descriptive): the one robust run E3 results §4 names", sum(ROW3[g]["coll"] for g in GR3 if g[0] == "b"),
      "1", "E3 results §4", [("E3", "**One robust run collapsed.** The exception is T_A_r2 5% s1")])
check("C0203", "runs per rate and arm", "/".join(str(ROW3[g]["n"]) for g in GR3), "9/9/9/9/3", "E3_verdicts.json")
check("C0203", "D49 cited in the C03 caption: no per-run collapse flag is stored", "49", "49", "decisions_log.md",
      [("DL", "D49 | 2026-10-25 | E3 per-run outcome \"collapsed\": no per-run collapse flag is stored")])
REF3 = [E3V["references"][f"T_A_r{i}"]["nolc live rmse_m"]["value"] for i in (1, 2, 3)]
VREF = check("C0203", "stored error without loop closure, the 3 flights, lowest–highest (m)", rng(REF3, 4), "0.2625–0.3608",
             "E3_verdicts.json references")
check("C0203", "wrong-ID rates (per cent of the eligible detections)", "1% / 5%", "1% / 5%", "E3_verdicts.json")
check("C0203", "room tag count (caption)", "8", "8", "preregistration.md", [("PR", "The 8 tags sit on a 6 m square")])

# ---- C02: chart, filled FGO squares (every run is live), a categorical "diverged" tick for runs with no finite error.
# Legend placed BELOW the axes (not on top of the data) -- the "diverged" band and the 5% groups leave no clean empty region
# inside the axes for a legend, and the brief bans drawing one plot/element over another.
fig, ax = plt.subplots(figsize=(FW, 4.3))
YDIV = 5.2
ax.set_xlim(-0.6, 4.6)
ax.set_ylim(0, 5.7)
ax.axhspan(min(REF3), max(REF3), color="#dddddd", lw=0, zorder=1)
for j, (a, r) in enumerate(GR3):
    ns = runs3(a, r)
    live_ns = [n for n in ns if not DIV3[n]]
    div_ns = [n for n in ns if DIV3[n]]
    # Live and diverged runs get their own independent, deterministic horizontal spread -- not a shared
    # linspace over all runs in the group -- so a group with few diverged runs (e.g. 6 of 9 here) doesn't
    # inherit cramped spacing from sharing index slots with the live runs. The diverged span (+-0.4) is
    # slightly wider than the live span (+-0.32) since "x" markers need more clearance than squares to stay
    # visually separate at this marker size, while staying inside the 1.0-unit column pitch so neighbouring
    # columns (e.g. "5% wrong IDs, FGO as built" at j+1) never overlap.
    live_xs = np.linspace(j - 0.32, j + 0.32, len(live_ns)) if len(live_ns) > 1 else [j]
    for x_, n in zip(live_xs, live_ns):
        ax.plot(x_, LIVE3[n], marker=MK["FGO"], color=C["FGO"], ms=6, ls="none", zorder=4)
    div_xs = np.linspace(j - 0.4, j + 0.4, len(div_ns)) if len(div_ns) > 1 else [j]
    for x_, n in zip(div_xs, div_ns):
        ax.plot(x_, YDIV, marker="x", color=C["FGO"], ms=8, mew=1.8, ls="none", zorder=4)
ax.set_xticks(range(5))
ax.set_xticklabels([T(LAB3[g]) for g in GR3], fontsize=9.0)
ax.set_yticks([0, 1, 2, 3, 4, YDIV])
ax.set_yticklabels(["0", "1", "2", "3", "4", "diverged"])
ax.grid(axis="x", visible=False)
ax.set_ylabel("live position error over five laps (m)")
leg = fig.legend(handles=[Line2D([], [], ls="none", marker=MK["FGO"], color=C["FGO"], ms=6, label="finished run (filled: live)"),
                          Line2D([], [], ls="none", marker="x", color=C["FGO"], ms=8, mew=1.8, label="diverged run"),
                          Patch(facecolor="#dddddd", edgecolor="none", label="stored error without\nloop closure, 3 flights")],
                 frameon=False, loc="lower center", ncol=3, fontsize=9.0, bbox_to_anchor=(0.5, 0.0), columnspacing=1.4)
fig.tight_layout(rect=(0, 0.1, 1, 1))
save("C02", fig, "docs/thesis/tier1/scores/E3_verdicts.json (runs, references)", pool="C0203")

C0203_CAP = (
    "Extension E3 (wrong tag IDs; 8-tag room, 5 laps, the FGO with loop closure): raw, measured from the start tag, nothing fitted. "
    "Outcome of every run, 3 flights (T_A_r1-r3) times 3 "
    "seeds at each wrong-ID rate (1% and 5%; control at rate 0: 3 flights, no seed sweep). One mark per run: live horizontal position "
    "error over five laps, root-mean-square, start-tag frame, metres; the estimator diverged on some runs (the FGO's keyframe graph "
    "threw repeated exceptions), marked separately rather than plotted, regardless of whether the stored error value is finite. Grey band: "
    f"the stored error without loop closure on the same 3 flights, {VREF} m. At 1% wrong IDs the FGO as built (plain) diverged in "
    f"{ROW3[('a','0.01')]['div']} of {ROW3[('a','0.01')]['n']} runs and the finished runs ended at {ROW3[('a','0.01')]['rng']} m; "
    f"at 5% it diverged in {ROW3[('a','0.05')]['div']} of {ROW3[('a','0.05')]['n']} and finished at "
    f"{ROW3[('a','0.05')]['rng']} m. The robust FGO never diverged at either rate ({ROW3[('b','0.01')]['rng']} m at 1%, "
    f"{ROW3[('b','0.05')]['rng']} m at 5%) and with no wrong IDs finished at {ROW3[('b','0')]['rng']} m."
)
guard("C0203", C0203_CAP)
write_caption("C02", C0203_CAP + "\n\n" + pointer_line(["H-E3.1", "P-E3b.1 (1%)", "P-E3b.1 (5%)", "P-E3b.2"]))

# ---- C03: markdown table candidate of the same run-outcome data, closer to the source table's own layout
C03_ROWS = []
for g in GR3:
    C03_ROWS.append([LAB3T[g], f"{ROW3[g]['div']} of {ROW3[g]['n']}", ROW3[g]["rng"].replace("–", " to "),
                      f"{ROW3[g]['coll']} of {ROW3[g]['n']}", VREF.replace("–", " to ")])
C03_MD = "\n".join([
    "# C03. Extension E3: outcome of every run (table candidate)",
    "",
    "| condition | runs diverged | error of the finished runs, lowest to highest (m) | collapsed (descriptive) | without loop closure (m), for reference |",
    "|---|---|---|---|---|",
] + ["| " + " | ".join(row) + " |" for row in C03_ROWS] + [
    "",
    "collapsed (descriptive, not a registered measure): the run finished with a wrong tag map (plain runs: map shrunk, consistent with "
    "a least-squares compromise; the one robust run: map folded, a wrong basin). Source: docs/thesis/tier1/scores/E3_verdicts.json "
    "(runs, references). Same data as candidate C02.",
])
guard("C0203", C03_MD)
with open(os.path.join(OUTD, "C03_table.md"), "w") as f:
    f.write(C03_MD + "\n")
print("wrote C03_table.md")
C03_CAP = ("Extension E3 (wrong tag IDs): raw, measured from the start tag, nothing fitted. The outcome of every run as a table, "
           "one row per condition (1% and 5% wrong IDs, FGO as built and robust, plus a no-wrong-ID robust control), from the same "
           "docs/thesis/tier1/scores/E3_verdicts.json runs and references that candidate C02's chart plots as one mark per run. "
           "Columns: "
           "runs diverged (the estimator's keyframe graph threw repeated exceptions; not plotted regardless of whether the stored "
           "value is finite), the live error of the finished runs (root-mean-square over five laps, start-tag frame, "
           "lowest to highest, metres), the runs counted as collapsed (descriptive, not a registered measure, since no per-run "
           "collapse flag is stored: every non-diverged plain-arm run plus the one robust run named in "
           "docs/thesis/tier1/e3_results.md, as decisions_log.md D49 records) and the stored error without loop closure on the same "
           "3 flights, for reference. n per row is 9 runs for the 1% and 5% rows (both arms) and 3 for the no-wrong-ID control; see "
           "C03_table.md.")
guard("C0203", C03_CAP)
write_caption("C03", C03_CAP + "\n\n" + pointer_line(["H-E3.1", "P-E3b.1 (1%)", "P-E3b.1 (5%)", "P-E3b.2"]))

# =================================================================== C04: Extension E3, every registered verdict (table candidate ONLY)
# Source: eval/figs_thesis_summary.py summary page 15 (= walkthrough page A1), a table drawn as a figure. "Verdicts belong in
# tables, not on figures" (brief): this candidate is a markdown table, not a chart, and its own .md file legitimately carries the
# PASS/FAIL words (same genre as Table A.4 and A1-A3) -- only this candidate's CAPTION file stays banned-word-clean, per D113.
TXT = []
CA, CB = E3V["criteria_a"], E3V["criteria_b"]
kk_ = lambda d, p: next(k for k in d if k.startswith(p))
ROWS3 = [("H-E3.1 (primary)", "1%: live error below the stored no-loop-closure error", CA, "H-E3.1", "FAIL", "0/9"),
         ("H-E3.2", "1%: the same for the hindsight error", CA, "H-E3.2", "FAIL", "0/9"),
         ("H-E3.3", "1%: lap-5 live error at most 1.5 × lap 1", CA, "H-E3.3", "FAIL", "3/9"),
         ("P-E3.4", "1%: live error at most 2 × the clean live error", CA, "P-E3.4", "FAIL", "0/9"),
         ("P-E3.5a", "5%: as H-E3.1", CA, "P-E3.5a", "FAIL", "0/9"),
         ("P-E3.5b", "5%: as H-E3.2", CA, "P-E3.5b", "FAIL", "0/9"),
         ("P-E3.5c", "5%: as H-E3.3", CA, "P-E3.5c", "PASS", "9/9"),
         ("P-E3.6", "per flight: error does not fall as the rate rises", CA, "P-E3.6", "FAIL", "0/3"),
         ("P-E3b.1 (1%, robust)", "1%: robust error at most 1.10 × the plain FGO's", CB, "P-E3b.1 0.01", "PASS", "9/9"),
         ("P-E3b.1 (5%, robust)", "5%: robust error at most 1.10 × the plain FGO's", CB, "P-E3b.1 0.05", "PASS", "9/9"),
         ("P-E3b.2 (robust)", "no wrong IDs: robust within ±10% of the clean error", CB, "P-E3b.2", "PASS", "3/3")]
b1a = CB[kk_(CB, "P-E3b.1 0.01")]
NFLAG = check("C04", "P-E3b.1 at 1%: runs SATISFIED, flagged (matched arm (a) run diverged, so no ratio exists)",
              len(b1a["satisfied, flagged"]), 6, "E3_verdicts.json criteria_b", [("E3", "**6 runs are SATISFIED, flagged**")])
NOTE = {"P-E3b.1 (1%, robust)": f"{NFLAG} of 9 are SATISFIED, flagged: the matched arm (a) run diverged, so no ratio exists"}
C04_ROWS = []
for idn, what, crit, key, ev, ec in ROWS3:
    c_ = crit[kk_(crit, key)]
    got = check("C04", f"{key}: verdict and count", f"{c_['verdict']} {c_['count']}", f"{ev} {ec}", "E3_verdicts.json criteria")
    C04_ROWS.append([idn, what, ec.replace("/", " of "), ev, NOTE.get(idn, "")])
# every id string printed in the "registered test" column is itself registered with the preregistration doc, so composite
# "fake numbers" inside an id (e.g. the 3.5 inside P-E3.5a) are grounded the same way the restyle generators ground "H-E2.1 P-E2.5".
IDSTR = "H-E3.1 H-E3.2 H-E3.3 P-E3.4 P-E3.5a P-E3.5b P-E3.5c P-E3.6 P-E3b.1 P-E3b.2"
check("C04", "registered ids printed", IDSTR, IDSTR, "pre-registration", [("PR", "H-E3.1")])
check("C04", "wrong-ID rates (per cent of the eligible detections)", "1% / 5%", "1% / 5%", "E3_verdicts.json")
check("C04", "H-E3.3 / P-E3.5c band: lap-5 live <= 1.5 x lap-1", "1.5", "1.5", "docs/thesis/tier1/e3_results.md",
      [("E3", "≤ 1.5 × lap-1")])
check("C04", "P-E3.4 band: live <= 2 x the clean live error", "2", "2", "docs/thesis/tier1/e3_results.md",
      [("E3", "≤ 2 × stored clean LC live")])
check("C04", "P-E3b.1 band: robust <= 1.10 x the plain FGO, same run", "1.10", "1.10", "docs/thesis/tier1/e3_results.md",
      [("E3", "≤ 1.10 × arm (a)")])
check("C04", "P-E3b.2 band: within ±10% of the stored clean error", "10", "10", "docs/thesis/tier1/e3_results.md",
      [("E3", "within ±10% of stored clean LC live")])
C04_MD = "\n".join([
    "# C04. Extension E3: every registered verdict (table candidate)",
    "",
    "| registered test | what it checks | runs passing | verdict | note |",
    "|---|---|---|---|---|",
] + ["| " + " | ".join(row) + " |" for row in C04_ROWS] + [
    "",
    "Pass or fail of each test, counted over the runs (flights for P-E3.6, raw per-flight means, nothing fitted); 1% / 5% = share of "
    "tag sightings given a wrong ID; a diverged run counts as not met. Source: docs/thesis/tier1/scores/E3_verdicts.json "
    "(criteria_a, criteria_b). Primary: H-E3.1. This table reproduces the same rows as the Extension E3 section of the appendix "
    "verdict register (docs/thesis/tables/TA_verdicts.md).",
])
guard("C04", C04_MD)
with open(os.path.join(OUTD, "C04_table.md"), "w") as f:
    f.write(C04_MD + "\n")
print("wrote C04_table.md")
C04_CAP = ("Extension E3 (wrong tag IDs): raw per-run counts against each registered band, nothing fitted. Every registered test, "
           "its count over the runs (3 flights × 3 seeds at each wrong-ID "
           "rate; the robust control at rate 0 is 3 flights, no seed sweep), reproduced as a table from docs/thesis/tier1/scores/"
           "E3_verdicts.json; see C04_table.md.")
guard("C04", C04_CAP)
write_caption("C04", C04_CAP + "\n\n" + pointer_line(["H-E3.1", "H-E3.2", "H-E3.3", "P-E3.4", "P-E3.5a", "P-E3.5b", "P-E3.5c", "P-E3.6",
                                                       "P-E3b.1 (1%)", "P-E3b.1 (5%)", "P-E3b.2"]))

# =================================================================== C05 / C06: Extension E3, tag maps
# Source: eval/figs_walkthrough_flights.py "E3_maps"/"E3_maps_app" (flights/fl_E3_maps.png, flights/fl_E3_maps_app.png; walkthrough
# wt_16m_E3_maps.png, wt_A2_E3_maps_app.png). Ground truth (/ground_truth/pose of T_A_r1, T_A_r2, T_A_r3) is read ONLY by
# eval/figs_cand_c_extract.py, run once under heavy.py; this script reads only its cache (deleted at the very end of this run).
TXT = []
TD = os.path.expanduser("~/thesis_data/trials")
T1DD = os.path.expanduser("~/thesis_data/tier1")
T1S = os.path.join(T1D, "scores")
TMAP = json.load(open(os.path.join(ROOT, "sim", "worlds", "room_tags_map.json")))["tags"]
_t0 = next(t for t in TMAP if t["id"] == 0)
TRUEMAP = {t["id"]: (t["x"] - _t0["x"], t["y"] - _t0["y"]) for t in TMAP}
B3_ = "lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7"
E3M = [("T_A_r1", os.path.join(TD, "T_A_r1", "lc_fgo_lc_t245"), os.path.join(RES, "expL", "T_A_r1_t245.json"),
        "no wrong IDs, FGO as built\n(Experiment 3, flight 1)"),
       ("T_A_r1", os.path.join(T1DD, "T_A_r1", f"{B3_}_mis0.01_s0"), os.path.join(T1S, "E3a_T_A_r1_0.01_s0.json"),
        "1% wrong IDs, FGO as built\n(flight 1, seed 0)"),
       ("T_A_r3", os.path.join(T1DD, "T_A_r3", f"{B3_}_mis0.05_s0"), os.path.join(T1S, "E3a_T_A_r3_0.05_s0.json"),
        "5% wrong IDs, FGO as built\n(flight 3, seed 0)"),
       ("T_A_r2", os.path.join(T1DD, "T_A_r2", f"{B3_}_mis0.05_s1_robcauchy2.385"), os.path.join(T1S, "E3b_T_A_r2_0.05_s1.json"),
        "5% wrong IDs, robust FGO\n(flight 2, seed 1)")]


def ground_truth(tr):
    """Read-only from the eval/figs_cand_c_extract.py cache (populated under heavy.py). NOT a bag read."""
    z = np.load(os.path.join(CACHE, f"gt_{tr}.npz"))
    return z["G"]


def e3_maps(fid, runs, width):
    fig, axs = plt.subplots(1, len(runs), figsize=(width, width / len(runs) + 0.9), sharex=True, sharey=True)
    axs = np.atleast_1d(axs)
    for i, (ax, (tr, rd_, sc, lab)) in enumerate(zip(axs, runs)):
        G = ground_truth(tr)
        Gx, Gy = G[:, 1] - _t0["x"], G[:, 2] - _t0["y"]
        H = np.loadtxt(f"{rd_}/hindsight.tum", ndmin=2)
        S = json.load(open(sc))
        lb = S["lap_bounds_s"]
        e_ = np.hypot(H[:, 1] - np.interp(H[:, 0], G[:, 0], Gx), H[:, 2] - np.interp(H[:, 0], G[:, 0], Gy))
        wl = (H[:, 0] >= lb[0]) & (H[:, 0] <= lb[-1])
        check(fid, f"{os.path.basename(rd_)} ({tr}): plotted hindsight track, RMSE over the stored lap window vs the stored "
              "'lc hindsight' rmse_m (6 dp)", rd(float(np.sqrt(np.mean(e_[wl] ** 2))), 6), rd(S["tracks"]["lc hindsight"]["rmse_m"], 6),
              os.path.relpath(sc, ROOT))
        wg = (G[:, 0] >= H[0, 0]) & (G[:, 0] <= H[-1, 0])
        ax.plot(Gx[wg], Gy[wg], color=TRUTH, lw=1.3, zorder=2)
        ax.plot(H[:, 1], H[:, 2], color=C["FGO"], lw=0.7, ls=(0, (4, 2)), alpha=0.9, zorder=3)
        for tid, (x_, y_) in TRUEMAP.items():
            ax.plot(x_, y_, marker="D", ms=5.5, color=TRUTH, zorder=4)
        lm = json.load(open(f"{rd_}/stats.json"))["landmarks_final"]
        for v in lm.values():
            ax.plot(v[0], v[1], marker=MK["FGO"], ms=6, mfc=SURF, mec=C["FGO"], mew=1.3, ls="", zorder=5)
        check(fid, f"{os.path.basename(rd_)}: final landmarks drawn = true tags", f"{len(lm)} / {len(TRUEMAP)}", "8 / 8",
              "stats.json landmarks_final; room_tags_map.json")
        ax.set_title(T(f"({'ab'[i]})"), loc="left", fontsize=9.0)      # panel label only (a)/(b); the run description is in the caption
        ax.set_aspect(1.0, adjustable="box")
        ax.set_xlabel("from the start tag, x (m)")
    axs[0].set_ylabel("from the start tag, y (m)")
    axs[0].set_xlim(-1.5, 7.5)
    axs[0].set_ylim(-1.5, 7.5)
    leg = fig.legend(handles=[Line2D([], [], color=TRUTH, lw=1.3, label="true track"),
                              Line2D([], [], color=TRUTH, ls="none", marker="D", ms=5.5, label="true tag"),
                              Line2D([], [], color=C["FGO"], lw=0.7, ls=(0, (4, 2)), label="FGO hindsight track"),
                              Line2D([], [], ls="none", marker=MK["FGO"], mfc=SURF, mec=C["FGO"], mew=1.3, ms=6, label="FGO final tag map")],
                     loc="lower center", ncol=4, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    return fig


fig = e3_maps("C05", E3M[:2], FW)
check("C05", "runs shown: the clean reference + one collapse example (T_A_r1 1% s0, FGO as built)", "2", "2", "user answer 4 (2026-11-02), D100")
check("C05", "panel labels printed (experiment no. / flight no., seed no.)", "3, 1 / 1, 0", "3, 1 / 1, 0",
      "E3M run selection (this script): Experiment 3 flight 1 (reference); flight 1 seed 0 (1% collapse)")
save("C05", fig, "eval/figs_cand_c_extract.py cache (bag /ground_truth/pose of T_A_r1, tag 0 frame); hindsight.tum and stats.json "
     "landmarks_final of the two runs; sim/worlds/room_tags_map.json; scores: eval/results/expL/T_A_r1_t245.json, "
     "docs/thesis/tier1/scores/E3a_T_A_r1_0.01_s0.json")
fig = e3_maps("C06", E3M[2:], FW)
check("C06", "runs shown: the other two maps of the 2026-10-31 walkthrough (moved to the appendix)", "2", "2", "user answer 4 (2026-11-02), D100")
check("C06", "panel labels printed (wrong-ID rate %, flight no., seed no., x2)", "5, 3, 0 / 5, 2, 1", "5, 3, 0 / 5, 2, 1",
      "E3M run selection (this script): 5% flight 3 seed 0 (plain); 5% flight 2 seed 1 (robust collapse)")
save("C06", fig, "eval/figs_cand_c_extract.py cache (bag /ground_truth/pose of T_A_r2, T_A_r3, tag 0 frame); hindsight.tum and "
     "stats.json landmarks_final of the two runs; sim/worlds/room_tags_map.json; scores: docs/thesis/tier1/scores/"
     "E3a_T_A_r3_0.05_s0.json, E3b_T_A_r2_0.05_s1.json")

C05_CAP = ("Extension E3 (wrong tag IDs), main example: raw, from the start tag, nothing fitted. Grey = true track and the 8 true "
           "tags; orange = the "
           "FGO's hindsight track (after landing) and its final tag map, equal scale, identical limits in both panels. (a) No "
           "wrong IDs (Experiment 3, flight 1), the final map matches the room. (b) 1% wrong IDs, FGO as built (flight 1, seed 0), "
           "the final map is shrunk inward from the true square.")
guard("C05", C05_CAP)
write_caption("C05", C05_CAP + "\n\n" + pointer_line([]))
C06_CAP = ("Extension E3 (wrong tag IDs), appendix: raw, from the start tag, nothing fitted. Two more wrong-ID runs, same drawing "
           "and equal scale as candidate C05. (a) 5% "
           "wrong IDs, FGO as built (flight 3, seed 0), the final map shrunk, as in C05 panel (b). (b) 5% wrong IDs, "
           "robust FGO (flight 2, seed 1), the one robust run that collapsed: the final map folded into a different arrangement from "
           "the true square rather than merely shrinking.")
guard("C06", C06_CAP)
write_caption("C06", C06_CAP + "\n\n" + pointer_line([]))

# =================================================================== C07: Extension E5, UKF with landmark states
# Source: eval/figs_walkthrough_extra.py "E5_ukf_landmarks" (walkthrough extra/ex_E5_ukf_landmarks.png) and
# eval/figs_thesis_summary.py summary page 18. Same data (e5_verdicts.json, e5_T_A_r{1,2,3}.json): one candidate.
TXT = []
E5V = LT("e5_verdicts.json")["flights"]
E5C = LT("e5_verdicts.json")["criteria"]
E5S = {r: LT(f"e5_T_A_r{r}.json")["tracks"] for r in (1, 2, 3)}
VAL5 = {}
for m in ("lc", "nolc"):
    for k in ("live", "hindsight"):
        VAL5[("UKF", m, k)] = [E5S[r][f"{m} {k}"]["rmse_m"] for r in (1, 2, 3)]
        VAL5[("FGO", m, k)] = [E5V[f"T_A_r{r}"]["values"][f"fgo {m} {k} rmse_m"]["value"] for r in (1, 2, 3)]
EXP5 = {("UKF", "lc", "live"): "0.0911–0.1335", ("FGO", "lc", "live"): "0.0494–0.0760",
        ("UKF", "lc", "hindsight"): "0.0445–0.0552", ("FGO", "lc", "hindsight"): "0.0172–0.0270",
        ("UKF", "nolc", "live"): "0.8738–1.4112", ("FGO", "nolc", "live"): "0.2625–0.3608",
        ("UKF", "nolc", "hindsight"): "0.9162–1.3349", ("FGO", "nolc", "hindsight"): "0.2210–0.2657"}
# FGO's e5_verdicts.json reference values, cross-checked against the SAME-flight Experiment 3 scores (eval/results/expL/*.json) --
# a second, independent loader for the same numbers (e5_verdicts.json carries these only as a copied reference, per its own design).
for r in (1, 2, 3):
    exp_ = L(f"expL/T_A_r{r}_t245.json")["tracks"]
    for m in ("lc", "nolc"):
        for k in ("live", "hindsight"):
            got_ = E5V[f"T_A_r{r}"]["values"][f"fgo {m} {k} rmse_m"]["value"]
            check("C07", f"T_A_r{r} fgo {m} {k} rmse_m: e5_verdicts.json reference equals the Experiment 3 score (6 dp)",
                  rd(got_, 6), rd(exp_[f"{m} {k}"]["rmse_m"], 6), f"eval/results/expL/T_A_r{r}_t245.json")
V5 = {}
for g in VAL5:
    lab_ = f"{g[0]} {'with' if g[1] == 'lc' else 'without'} loop closure, {g[2]}: lowest–highest over 3 flights (m)"
    shown = [("NT", rd(min(VAL5[g]), 4)), ("NT", rd(max(VAL5[g]), 4))] if g[0] == "UKF" else []
    V5[g] = check("C07", lab_, rng(VAL5[g], 4), EXP5[g], "e5_verdicts.json / e5_T_A_r<r>.json", shown)
VR5 = check("C07", "H-E5.1: lap 5 ÷ lap 1, live with loop closure, lowest–highest",
            rng([E5V[f"T_A_r{r}"]["ratio lc live lap5/lap1"] for r in (1, 2, 3)], 2), "0.27–0.42", "e5_verdicts.json",
            [("NT", "0.27"), ("NT", "0.42")])
check("C07", "room geometry and flight count printed in the caption (tags, laps, flights, lap 1)", "8 / 5 / 3 / 1", "8 / 5 / 3 / 1",
      "preregistration.md", [("PR", "The 8 tags sit on a 6 m square")])
check("C07", "FGO hindsight mapping cited in the caption (iSAM2 + 5 extra updates, not an LM batch; source line)", "2 / 5 / 247",
      "2 / 5 / 247", "e5_design.md", [("E5D", "the FGO uses iSAM2's full-graph estimate after 5 extra updates")])

fig, ax = plt.subplots(figsize=(FW, 3.9))
ax.set_xlim(-0.62, 1.92)
ax.set_ylim(0, 1.72)
BL5 = {("UKF", "live"): "UKF\nlive", ("UKF", "hindsight"): "UKF\nhindsight", ("FGO", "live"): "FGO\nlive", ("FGO", "hindsight"): "FGO\nhindsight"}
for j, m in enumerate(("nolc", "lc")):
    for k, (e, kind) in enumerate((("UKF", "live"), ("UKF", "hindsight"), ("FGO", "live"), ("FGO", "hindsight"))):
        x = j * 1.3 + (k - 1.5) * 0.265
        top_ = rbox(ax, x, VAL5[(e, m, kind)], C[e], kind == "live", w=0.2)
ax.set_xticks([0, 1.3])
ax.set_xticklabels([T("without loop closure"), T("with loop closure")])
ax.tick_params(axis="x", pad=8)
ax.grid(axis="x", visible=False)
ax.set_ylabel("horizontal RMSE over 5 laps (m)")
leg = ax.legend(handles=[Patch(facecolor=C["UKF"], edgecolor=C["UKF"], lw=1.4, label="UKF live"),
                         Patch(facecolor=SURF, edgecolor=C["UKF"], lw=1.4, label="UKF hindsight"),
                         Patch(facecolor=C["FGO"], edgecolor=C["FGO"], lw=1.4, label="FGO live"),
                         Patch(facecolor=SURF, edgecolor=C["FGO"], lw=1.4, label="FGO hindsight")],
                frameon=False, loc="upper left", fontsize=9.0, ncol=2, labelspacing=0.5, columnspacing=1.0)
fig.tight_layout()
save("C07", fig, "docs/thesis/tier1/scores/e5_verdicts.json, e5_T_A_r{1,2,3}.json", key=True)

C07_CAP = ("Extension E5 (a UKF variant carrying each AprilTag as a landmark state, 8-tag room, 5 laps, same flights as Experiment 3): "
           "raw, measured from the start tag, nothing fitted. "
           "Horizontal RMSE over the 5 laps, start-tag frame, box = lowest to highest over 3 flights, solid/filled = live, open = "
           "hindsight (UKF: RTS-smoothed; FGO: the stored Experiment 3 values, its own hindsight after landing, iSAM2's "
           "full-graph estimate after 5 extra updates, not a whole-flight LM batch, see docs/thesis/tier1/e5_design.md:247). "
           "Without loop closure "
           f"(each tag seen once), UKF live {V5[('UKF','nolc','live')]} m, UKF hindsight {V5[('UKF','nolc','hindsight')]} m, FGO live "
           f"{V5[('FGO','nolc','live')]} m, FGO hindsight {V5[('FGO','nolc','hindsight')]} m. With loop closure (re-identifying tags "
           f"seen before), UKF live {V5[('UKF','lc','live')]} m, UKF hindsight {V5[('UKF','lc','hindsight')]} m, FGO live "
           f"{V5[('FGO','lc','live')]} m, FGO hindsight {V5[('FGO','lc','hindsight')]} m. With loop closure the UKF's lap 5 ÷ lap "
           f"1 live ratio is {VR5}.")
guard("C07", C07_CAP)
write_caption("C07", C07_CAP + "\n\n" + pointer_line(["H-E5.1", "S-E5.5", "S-E5.6"]))

# =================================================================== index
N_OK = sum(1 for c in CHK if c["ok"])
N_TOT = len(CHK)
print(f"figs_cand_c: {N_OK}/{N_TOT} checks ok")
assert N_OK == N_TOT, "a check failed -- see CHECK FAIL lines above"

IDX = [
    "# Group C candidate thesis figures (decision D124): Extension E2, Extension E3 (including the tag maps) and Extension E5",
    "",
    f"Built by eval/figs_cand_c.py at commit `{COMMIT}`, run with /home/makerspace/venv-evo/bin/python. The E3 tag maps (C05, C06) "
    "also need eval/figs_cand_c_extract.py, run once under heavy.py to cache /ground_truth/pose from the stored bags to "
    "~/thesis_data/cand_c_cache (deleted once this script finishes). Stored outputs only throughout: no flight, estimator replay or "
    "simulation. Rules: 160 mm (6.30 in) wide, Okabe-Ito EKF3/UKF/FGO + grey truth, filled = live / open = hindsight, no titles, no "
    "verdict words, no badges or explanatory notes inside axes, no bold in axes, side-by-side panels only on a shared scale, every "
    "number in an exact cross-check (parsed rd(), SHA-pinned).",
    "",
    f"**Checks: {N_OK}/{N_TOT} (exact string equality).**",
    "",
    "| id | proposed title | source chart(s) | data files | checks | verdict pointer |",
    "|---|---|---|---|---|---|",
    "| C01 | Loop closure with fewer tags: the FGO's error on lap 5 | walkthrough extra/ex_E2_fewer_tags.png (p15); summary page 13 "
    "(same data, one candidate) | tier1/scores/E2_verdicts.json, E2_T_{B,C,D}_r{1,2,3}.json; eval/results/expL/T_A_r{1,2,3}_t245.json | "
    f"{sum(1 for c in CHK if c['fig'] == 'C01')}/{sum(1 for c in CHK if c['fig'] == 'C01')} | H-E2.1; P-E2.5 (graded) |",
    "| C02 | Wrong tag IDs: outcome of every run (chart) | walkthrough extra/ex_E3_table.png (p16, really a table -> see C03); "
    "summary page 14 (chart; same underlying data) | tier1/scores/E3_verdicts.json | "
    f"{sum(1 for c in CHK if c['fig'] == 'C0203')}/{sum(1 for c in CHK if c['fig'] == 'C0203')} (shared with C03) | "
    "H-E3.1; P-E3b.1 (1%); P-E3b.1 (5%); P-E3b.2 |",
    "| C03 | Wrong tag IDs: outcome of every run (table) | walkthrough extra/ex_E3_table.png (p16) | tier1/scores/E3_verdicts.json | "
    "shared with C02 | H-E3.1; P-E3b.1 (1%); P-E3b.1 (5%); P-E3b.2 |",
    "| C04 | Wrong tag IDs: every registered verdict (table) | summary page 15 = walkthrough page A1 (table drawn as a figure) | "
    f"tier1/scores/E3_verdicts.json | {sum(1 for c in CHK if c['fig'] == 'C04')}/{sum(1 for c in CHK if c['fig'] == 'C04')} | "
    "H-E3.1; H-E3.2; H-E3.3; P-E3.4; P-E3.5a; P-E3.5b; P-E3.5c; P-E3.6; P-E3b.1 (1%); P-E3b.1 (5%); P-E3b.2 |",
    "| C05 | Wrong tag IDs: tag maps, clean reference + main collapse example | flights/fl_E3_maps.png (walkthrough wt_16m_E3_maps.png) "
    f"| bags T_A_r1 (ground truth); tier1 run dirs; tier1/scores/E3a_T_A_r1_0.01_s0.json | "
    f"{sum(1 for c in CHK if c['fig'] == 'C05')}/{sum(1 for c in CHK if c['fig'] == 'C05')} | none (descriptive: one run per panel, "
    "not the 9-run H-E3.1 population) |",
    "| C06 | Wrong tag IDs: tag maps, appendix (two more runs) | flights/fl_E3_maps_app.png (walkthrough wt_A2_E3_maps_app.png) | "
    f"bags T_A_r2, T_A_r3 (ground truth); tier1 run dirs; tier1/scores/E3a_T_A_r3_0.05_s0.json, E3b_T_A_r2_0.05_s1.json | "
    f"{sum(1 for c in CHK if c['fig'] == 'C06')}/{sum(1 for c in CHK if c['fig'] == 'C06')} | none (descriptive, as C05) |",
    "| C07 | A UKF with landmark states against the FGO | walkthrough extra/ex_E5_ukf_landmarks.png (p18); summary page 18 (same "
    f"data) | tier1/scores/e5_verdicts.json, e5_T_A_r{{1,2,3}}.json | "
    f"{sum(1 for c in CHK if c['fig'] == 'C07')}/{sum(1 for c in CHK if c['fig'] == 'C07')} | H-E5.1; S-E5.5; S-E5.6 |",
    "",
    "Notes for the coordinator:",
    "- C02 and C03 share one dataset (the per-run outcome of Extension E3); C02 is the chart, C03 the table candidate, as the brief "
    "asks for both.",
    "- C04 reproduces the same rows as Table A.4's Extension E3 section (already in docs/thesis/figures_thesis/ as part of TA_verdicts), "
    "but is built anyway because the brief names \"the registered verdicts (summary page 15 / walkthrough A1)\" as its own candidate; "
    "flagged in case the coordinator judges it redundant with Table A.4.",
    "- C03 and C04 are markdown table candidates, not charts (per the brief, \"verdicts belong in tables, not on figures\"): "
    "C03_table.md and C04_table.md sit beside this index; C04_table.md legitimately carries PASS/FAIL words (same convention as "
    "Table A.4/A1-A3), but its caption file (captions/C04.md) stays banned-word-clean per D113, describing the table rather than "
    "restating its verdicts.",
    "- C05/C06 need the cache from eval/figs_cand_c_extract.py (run once under heavy.py, deleted at the end of this run); "
    "regenerating these two candidates from scratch means re-running that extraction step first.",
]
with open(INDEX, "w") as f:
    f.write("\n".join(IDX) + "\n")
print("wrote index_c.md")

# ------------------------------------------------------------------ delete the bag-extraction cache (brief: "deleting it at the end")
if os.path.isdir(CACHE):
    shutil.rmtree(CACHE)
    print(f"removed {CACHE}")
