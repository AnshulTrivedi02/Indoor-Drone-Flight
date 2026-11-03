#!/usr/bin/env python3
"""FIGURE 4.1d (PROVISIONAL, internal id R6): offline standard-sensor drift, UNALIGNED, ALL 9 FLIGHTS (restyled copy of the
results-walkthrough page-01 figure fl_1A_unaligned_paths; walkthrough unchanged). Built ONLY from stored outputs (TUM files,
eval/results/*.json): no estimator run, no simulation, no bag read.

Scope and provenance: this is a NEW figures_thesis/ generator. It does NOT import or execute eval/figs_walkthrough_flights.py
(that module's top level reads bags via pymavlink/rosbags) - instead, as eval/figs_thesis_drift.py already does for
eval/figs_thesis.py, the three small, bag-free functions that build this exact figure's data (`to_NE`, `frame_ok`, `unaligned`)
and the `HEAD_TOL_DEG` constant are parsed out of eval/figs_walkthrough_flights.py with `ast` and exec'd in a private namespace -
never run as a script, never edited. The PLOTTED data therefore comes from literally the same code as the walkthrough's page 1.

Flights: the 9 textured-floor standard-sensor flights `dsn_tex_r1..r9` (Experiment 1A), the same n = 9 as fl_1A_unaligned_paths
and as Table 4.4 (T9, eval/figs_thesis.py). Per-flight cruise window from eval/results/{rerun_dsn_evo,dsn_extra_evo}.json.

FRAMES: identical convention to eval/figs_thesis_drift.py (R5) and index_drift.md - EKF3 TUMs are (N, E, D); UKF/FGO estimate
TUMs are the take-off-heading frame, x = North, y = West, so (N, E) = (x, -y); UKF/FGO truth TUMs are ENU (E, N, U). No
rotation, offset or scale fit is applied to any estimate (raw paths).

Frame-check tolerance (R6-1, see the handover): R5's own stop condition used HEAD_TOL_DEG = 2.0 deg, checked over ONE flight.
Extended to all 27 (estimator, flight) pairs, 4 fail at 2.0 deg (UKF r2/r6, FGO r2/r6: a genuine early-cruise heading error of
2.7-3.5 deg on those two flights, not a frame bug - take-off origin is exact (< 0.05 m) in all 27 cases, and an axis swap or
sign error in the relabel would show up as >= 90 deg, not 3 deg). eval/figs_walkthrough_flights.py already found exactly this
and widened its own gating tolerance to HEAD_TOL_DEG = 10.0 deg for the 9-flight case (its own comment explains why); this
script reuses that already-vetted 10 deg gate (ast-parsed from the same source, not re-derived) and reports the 2.0 deg count
alongside it for transparency, exactly as the walkthrough's own FRAME_NOTE does.

Outputs:
  docs/thesis/figures_thesis/R6_drift_9flights.{png,pdf}
  docs/thesis/figures_thesis/index_drift9.md     caption, inputs, frame check, cross-check table (index_drift.md is NOT touched)
  docs/thesis/figures_thesis/captions/R6.md       via thesis_style.write_caption() (verdict pointer appended separately by
                                                   eval/add_caption_verdict_pointers.py)

Usage: /home/makerspace/venv-evo/bin/python eval/figs_thesis_drift9.py"""
import ast, hashlib, json, math, os, subprocess, sys, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUTF = os.path.join(ROOT, "docs", "thesis", "figures_thesis"); INDEX = os.path.join(OUTF, "index_drift9.md")
SCRIPT = "eval/figs_thesis_drift9.py"
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

# ------------------------------------------------------------- shared code from figs_thesis.py, parsed, NOT executed as a script
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read(); _tree = ast.parse(_src)
_WANT_F = {"rd"}
_WANT_A = {"C", "MK", "TRUTH", "EST", "INK", "INK2", "GRID", "SURF", "WALL"}
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
_ns = {"np": np}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
C, TRUTH, EST, INK, INK2 = (_ns[k] for k in ("C", "TRUTH", "EST", "INK", "INK2"))
RD_SHA = hashlib.sha256(_rd_src.encode()).hexdigest()
assert C == {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"} and TRUTH == "#999999", "palette changed in figs_thesis.py"

# ------------------------------------------------------------- shared code from figs_walkthrough_flights.py, parsed, NOT
# executed and NOT imported (its top level reads bags via pymavlink/rosbags; none of that is needed here). This is the SAME
# source the restyled figure must reproduce - `unaligned()` is the walkthrough's own function that builds fl_1A_unaligned_paths'
# per-flight path data, read directly from TUM files, exactly as it runs there.
FW = os.path.join(HERE, "figs_walkthrough_flights.py"); _wsrc = open(FW).read(); _wtree = ast.parse(_wsrc)
_WANT_WF = {"to_NE", "frame_ok", "unaligned"}
_WANT_WA = {"HEAD_TOL_DEG"}
_wnodes, _wfsrc = [], {}
for n in _wtree.body:
    if isinstance(n, ast.FunctionDef) and n.name in _WANT_WF:
        _wnodes.append(n); _wfsrc[n.name] = ast.get_source_segment(_wsrc, n)
    elif isinstance(n, ast.Assign):
        names = {t.id for t in n.targets if isinstance(t, ast.Name)}
        if names & _WANT_WA:
            _wnodes.append(n); _wfsrc["HEAD_TOL_DEG"] = ast.get_source_segment(_wsrc, n)
_wns = {"np": np, "math": math, "TD": TD}
exec(compile(ast.Module(body=_wnodes, type_ignores=[]), FW, "exec"), _wns)
w_unaligned, w_frame_ok, w_to_NE = _wns["unaligned"], _wns["frame_ok"], _wns["to_NE"]
HEAD_TOL_DEG = _wns["HEAD_TOL_DEG"]
assert HEAD_TOL_DEG == 10.0, f"walkthrough's own gating tolerance changed to {HEAD_TOL_DEG}; re-check R6-1 in the handover"
W_SHA = hashlib.sha256("".join(_wfsrc[k] for k in ("to_NE", "frame_ok", "unaligned", "HEAD_TOL_DEG")).encode()).hexdigest()

L = lambda f: json.load(open(os.path.join(RES, f)))
NUM = open(os.path.join(ROOT, "docs", "thesis", "numbers.md")).read().split("\n")
CLAUDEMD = open(os.path.join(ROOT, "CLAUDE.md")).read().split("\n")
CHK = []


def norm(s):
    return s.replace("**", "").replace("`", "").replace("\\|", "|")


def check(label, computed, expected, src, line_text=None):
    """EXACT string equality; if line_text is given, the expected string must also occur in that line."""
    inline = True if line_text is None else (norm(str(expected)) in norm(line_text))
    ok = str(computed) == str(expected) and inline
    CHK.append((label, str(computed), str(expected), src, ok))
    if not ok:
        print("   CHECK FAIL:", label, computed, expected, "" if inline else "NOT IN LINE")
    return ok


def cite(lines, path, line, phrase):
    """A cited rule line: the file as read at build time must contain `phrase` on line `line`."""
    got = phrase if phrase in lines[line - 1] else lines[line - 1].strip()[:90]
    check(f"rule text {path}:{line} contains the quoted phrase", got, phrase, f"{path}:{line} (read at build time)")
    return f"{path}:{line}"

# =============================================================================================== flights, windows (Experiment 1A)
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
A_FL = [f"dsn_tex_r{i}" for i in range(1, 10)]
SUB = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF": ("ukf", "ukf_traj.tum"), "FGO": ("fgo", "fgo_traj.tum")}
check("flights in the dataset (Experiment 1A, standard-sensor, textured floor)", str(len(A_FL)), "9",
      "docs/thesis/numbers.md:230", NUM[229])

# =============================================================================================== build data: walkthrough's OWN
# `unaligned()` (parsed above), called once per (estimator, flight) exactly as fl_1A_unaligned_paths does.
UN = {}; FR = []
for e in EST:
    sub, f = SUB[e]
    for tr in A_FL:
        win = ev[tr]["window_s"]
        diag, path = w_unaligned(e, tr, sub, f, win)
        ok, o_e, o_g, h_e, h_g = diag
        UN[(e, tr)] = path
        FR.append((tr, e, ok, o_e, o_g, h_e, h_g))

n_pass10 = sum(1 for r in FR if r[2])
print(f"frame check (walkthrough's own, HEAD_TOL_DEG={HEAD_TOL_DEG}): {n_pass10}/{len(FR)} PASS")
if n_pass10 != len(FR):
    sys.exit("FRAME CHECK FAILED (walkthrough's own 10 deg gate): " + str([r for r in FR if not r[2]]))
check("frame check (walkthrough's own rule and tolerance, ast-parsed from eval/figs_walkthrough_flights.py)",
      f"{n_pass10}/{len(FR)}", "27/27", "eval/figs_walkthrough_flights.py:frame_ok, HEAD_TOL_DEG=10.0 (this script's own parse)")

# R6-1 (see the handover): report the SAME computation at R5's own, tighter 2.0 deg tolerance, exactly as
# eval/figs_walkthrough_flights.py's own FRAME_NOTE does (that string is diagnostic there, not a gate; reproduced here as a
# real, regression-guarded check rather than a bare print).
HEAD_TOL_2 = 2.0
fail2 = [(tr, e, h_e - h_g) for tr, e, ok, o_e, o_g, h_e, h_g in FR if abs(h_e - h_g) >= HEAD_TOL_2]
n_pass2 = len(FR) - len(fail2)
FAIL2_NOTE = "; ".join(f"{tr} {e} {d:+.2f} deg" for tr, e, d in fail2)
print(f"at R5's {HEAD_TOL_2} deg tolerance: {n_pass2}/{len(FR)} pass; the others {FAIL2_NOTE}")
check(f"flights/estimators failing R5's own {HEAD_TOL_2} deg tolerance (not this figure's gate; see index_drift.md)",
      str(len(fail2)), "4", "this script, same formula as eval/figs_thesis_drift.py's FRAME CHECK; genuine early-cruise "
      "heading error on dsn_tex_r2/r6 (UKF, FGO), not a frame bug - all 27 take-off origins are < 0.05 m and the heading "
      "mismatch is 2.7-3.5 deg, far below the >= 90 deg an axis-swap or sign error would give")

# =============================================================================================== data-identity check: the
# DRAWN path's end point vs an INDEPENDENT recomputation straight from the TUM rows (not via `unaligned()`; a second, separate
# implementation of the same frame map and window crop).
END_INDEP = {}
for e in EST:
    sub, f = SUB[e]
    for tr in A_FL:
        win = ev[tr]["window_s"]
        a = np.loadtxt(f"{TD}/{tr}/{sub}/{f}"); g = np.loadtxt(f"{TD}/{tr}/{sub}/ground_truth.tum")
        if e == "EKF3":
            te, ne, ee = a[:, 0], a[:, 1], a[:, 2]
        else:
            te, ne, ee = a[:, 0], a[:, 1], -a[:, 2]
        tg = g[:, 0]
        k = (te >= tg[0]) & (te <= win[1])
        END_INDEP[(e, tr)] = (ne[k][-1], ee[k][-1])

# =============================================================================================== layout, palette, limits
STRETCH = 1.0
from thesis_style import TEXT_WIDTH_IN, write_caption
WALLC = "#bdbdbd"          # same medium-grey wall band as eval/figs_walkthrough_flights.py:258 (WALLC)
LW_FL = 0.9                # one thin line per flight, same weight as eval/figs_walkthrough_flights.py:231 (LW_FL)

mins = [UN[(e, tr)][2].min() for e in EST for tr in A_FL]
maxs = [UN[(e, tr)][2].max() for e in EST for tr in A_FL]
LIM1 = max(abs(min(mins)), abs(max(maxs)), 10.0) + 4.0           # same formula as figs_walkthrough_flights.py:524
YL0, YL1 = -3.0, 163.0                                           # same panel y-range as fl_1A_unaligned_paths

# Fixed margins, as absolute inches, converted to figure-fraction below: left/right are independent of figure height
# (width is fixed at TEXT_WIDTH_IN), top/bottom are not, so the figure HEIGHT is solved analytically (not iterated) from
# them so that the three already-equal, already-aligned panel boxes show a true 1:1 aspect by construction - the same
# layout-fix principle the restyle already applied to R3/R5 (figs_thesis_results.py / figs_thesis_drift.py), but solved in
# closed form here because gridspec's fixed-fraction wspace makes the per-panel box width independent of figure height.
# set_aspect(adjustable="box") is NOT used: it would shrink each panel independently and risks misaligning the three
# shared columns, exactly the bug that technique caused in the pre-fix R3/R5 (see the restyle handover).
LEFT_IN, RIGHT_IN, TOP_IN, BOTTOM_IN = 0.60, 0.10, 0.28, 0.48
WSPACE = 0.14
left_f, right_f = LEFT_IN / TEXT_WIDTH_IN, 1 - RIGHT_IN / TEXT_WIDTH_IN
PANEL_W = TEXT_WIDTH_IN * (right_f - left_f) / (3 + 2 * WSPACE)                 # one panel's box width, inches
PANEL_H = PANEL_W * (YL1 - YL0) / (2 * LIM1)                                    # box height for a true 1:1 aspect
FIGH = TOP_IN + BOTTOM_IN + PANEL_H
top_f, bottom_f = 1 - TOP_IN / FIGH, BOTTOM_IN / FIGH

fig = plt.figure(figsize=(TEXT_WIDTH_IN, FIGH))
gs = fig.add_gridspec(1, 3, wspace=WSPACE)
axs = [fig.add_subplot(gs[0, 0])]
axs += [fig.add_subplot(gs[0, i], sharex=axs[0], sharey=axs[0]) for i in range(1, 3)]
LINE_END = {}
for ax, e in zip(axs, EST):
    for s in (1, -1):
        ax.axvspan(10 * s, LIM1 * s, color=WALLC, lw=0, zorder=0.5)
    for s in (1, -1):
        cx = (10 + LIM1) / 2 * s
        t_ = ax.text(cx, 12.0, "wall", ha="center", va="center", fontsize=9.5, color=INK2, zorder=4)
        t_.set_path_effects([patheffects.withStroke(linewidth=2.5, foreground="#ffffff")])
    for tr in A_FL:
        t_rel, nE, eE, err, gt_ = UN[(e, tr)]
        tg, ng, eg = gt_
        w = tg <= ev[tr]["window_s"][1]
        ax.plot(eg[w], ng[w], color=TRUTH, lw=2.2, zorder=2, solid_capstyle="round")
    for tr in A_FL:
        t_rel, nE, eE, err, gt_ = UN[(e, tr)]
        ln = ax.plot(eE, nE, color=C[e], lw=LW_FL, zorder=3)[0]
        LINE_END[(e, tr)] = ln.get_xydata()[-1]           # (East, North), as DRAWN
    ax.plot(0, 0, marker="o", ms=5, color=INK, zorder=5)
    ax.set_xlabel("sideways, East (m)")
axs[0].set_xlim(-LIM1, LIM1); axs[0].set_ylim(YL0, YL1)
for ax, letter, e in zip(axs, "abc", EST):
    ax.set_title(f"({letter}) {e}", loc="left", color=C[e], fontsize=10.5)
axs[0].set_ylabel("along the corridor, North (m)")
for ax in axs[1:]:
    plt.setp(ax.get_yticklabels(), visible=False)
fig.subplots_adjust(left=left_f, right=right_f, top=top_f, bottom=bottom_f, wspace=WSPACE)
fig.canvas.draw()
bb0 = axs[0].get_window_extent().transformed(fig.dpi_scale_trans.inverted())
x0, x1 = axs[0].get_xlim()
st_meas = (bb0.height / (YL1 - YL0)) / (bb0.width / (x1 - x0))
assert abs(st_meas - 1.0) < 0.01, f"equal-scale analytic solve did not converge: FIGH={FIGH:.4f} st_meas={st_meas:.4f}"

check("equal scale (measured stretch) vs declared", rd(st_meas, 1), rd(STRETCH, 1), "panel geometry (axs[0] box, this script)")
check("x-axis symmetric about 0 (left and right limits, m)", f"{-axs[0].get_xlim()[0]:.6f}", f"{axs[0].get_xlim()[1]:.6f}",
      "LIM1 (same formula as figs_walkthrough_flights.py:524)")
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUTF, f"R6_drift_9flights.{ext}"), dpi=170 if ext == "png" else None)
plt.close(fig)

# data-identity check: the DRAWN line's end point vs the independent (non-`unaligned()`) TUM recomputation, 6 dp
for e in EST:
    for tr in A_FL:
        de, dn = LINE_END[(e, tr)]
        ine, iee = END_INDEP[(e, tr)][0], END_INDEP[(e, tr)][1]
        check(f"{tr} {e}: drawn path end point, North (m), 6 dp vs independent TUM recomputation", rd(dn, 6), rd(ine, 6),
              "independent recomputation from the TUM rows (this script, not via figs_walkthrough_flights.py:unaligned())")
        check(f"{tr} {e}: drawn path end point, East (m), 6 dp vs independent TUM recomputation", rd(de, 6), rd(iee, 6),
              "independent recomputation from the TUM rows (this script, not via figs_walkthrough_flights.py:unaligned())")

WSRC = cite(CLAUDEMD, "CLAUDE.md", 101, "5 m tall and 0.2 m thick at x = ±10 m")

# =============================================================================================== caption + index
CAP = ("Offline standard-sensor dataset (IMU, downward flow, downward LiDAR; no heading source), textured floor, Experiment "
       "1A, all 9 flights (dsn_tex_r1-r9). Passive estimators, truth flying. Each panel is one estimator; every one of its 9 "
       "flights is drawn, from take-off to the end of its own cruise window. Paths are raw: each estimate is drawn exactly as "
       "estimated, in its own navigation frame with its origin at take-off, with no fitted alignment (no rotation, "
       "translation or scale fit). EKF3 reports North/East directly. The UKF and FGO trajectories are expressed in the world "
       "frame by a fixed axis relabel from the known take-off heading (the vehicle spawns facing North, and both start with "
       "yaw 0 along it, so their x is North and their y is West: (North, East) = (x, −y)), the same convention as Figure "
       "4.1c and eval/phase5_analysis.py. The grey line is the true path (simulator); the black dot is take-off, at the "
       f"origin of every panel. The shaded bands beyond East = ±10 m ({WSRC}), labelled \"wall\", are the corridor walls. "
       f"East and North are drawn at equal scale ({rd(STRETCH, 1)}×); all three panels share the same x- and y-limits. "
       "Fitted and raw values: Table 4.4 (provisional).")
TITLE = "Without a heading source, every one of the 9 flights drifts sideways off the true path"
n_ok = sum(1 for c in CHK if c[-1])
W = [f"# Figure 4.1d (provisional): offline standard-sensor drift, unaligned, all 9 flights (internal id R6)\n",
     f"Generated by `{SCRIPT}` at commit `{COMMIT}` (outputs from the working tree at that commit). Stored outputs only: no "
     "estimator run, no simulation, no bag read. **Provisional label; nothing else is renumbered.** A restyled copy of the "
     "results-walkthrough page-01 figure `fl_1A_unaligned_paths` (`eval/figs_walkthrough_flights.py`, `docs/thesis/summary/"
     "flights/`), which is itself unchanged.\n",
     f"**Cross-checks:** {n_ok}/{len(CHK)} EXACT (string equality after one rounding by `rd()`). **Frame check:** "
     f"{n_pass10}/{len(FR)} PASS at the walkthrough's own {HEAD_TOL_DEG:g} deg gate (see R6-1 in the handover for the {HEAD_TOL_2:g} "
     f"deg figure, {n_pass2}/{len(FR)}).\n",
     f"**Rounding:** `rd()` parsed from `eval/figs_thesis.py` (not executed); SHA-256 of its source `{RD_SHA}`. `to_NE`/"
     f"`frame_ok`/`unaligned`/`HEAD_TOL_DEG` parsed from `eval/figs_walkthrough_flights.py` (not executed, not imported); "
     f"SHA-256 of their concatenated source `{W_SHA}`. Palette: Okabe–Ito, EKF3 {C['EKF3']}, UKF {C['UKF']}, FGO {C['FGO']}, "
     f"truth {TRUTH}.\n",
     "## Figure\n", "| file | title |", "|---|---|", f"| `figures_thesis/R6_drift_9flights.{{png,pdf}}` | {TITLE} |\n",
     "## Caption\n", CAP + "\n",
     "## Inputs\n",
     "- `~/thesis_data/trials/dsn_tex_r1..r9/ekf3/{ekf3_traj,ground_truth}.tum` (N, E, D)",
     "- `~/thesis_data/trials/dsn_tex_r1..r9/ukf/{ukf_traj,ground_truth}.tum`, `~/thesis_data/trials/dsn_tex_r1..r9/fgo/"
     "{fgo_traj,ground_truth}.tum` (estimate: own frame, x = take-off heading; truth: ENU)",
     "- cruise windows: `eval/results/rerun_dsn_evo.json`, `eval/results/dsn_extra_evo.json`\n",
     "## Frame check (walkthrough's own rule, ast-parsed; stop condition of this script)\n",
     "Spawn yaw 90° ENU = heading North (`sim/worlds/corridor_textured.sdf:218`); UKF yaw0 = 0 (`src/estimators/"
     "ukf_core.py:318`); FGO yaw0 = 0 (`src/estimators/fgo/fgo_core.py:120`, `fgo_replay.py:134`). Map for the UKF/FGO: "
     "(N, E) = (x, −y). Pass (walkthrough's own gate, `frame_ok()`): take-off |NE| < 0.05 m and heading of the first 5 m of "
     f"true cruise travel within {HEAD_TOL_DEG:g}° of truth. R5's own, tighter {HEAD_TOL_2:g}° tolerance over all 27 pairs is "
     "reported for transparency, not used as a gate here (see R6-1 in the handover).\n",
     "| trial | estimator | take-off \\|NE\\| est (m) | take-off \\|NE\\| truth (m) | est heading (°, from North) | truth heading (°) | "
     f"result ({HEAD_TOL_DEG:g}°) | result ({HEAD_TOL_2:g}°) |",
     "|---|---|---|---|---|---|---|---|"]
for tr, e, ok, o_e, o_g, h_e, h_g in FR:
    ok2 = abs(h_e - h_g) < HEAD_TOL_2
    W.append(f"| {tr} | {e} | {o_e:.4f} | {o_g:.4f} | {h_e:+.3f} | {h_g:+.3f} | {'PASS' if ok else 'FAIL'} | {'PASS' if ok2 else 'FAIL'} |")
W += ["", "## Cross-checks\n", "| check | computed | expected | source | result |", "|---|---|---|---|---|"]
for lab, a, b, s, ok in CHK:
    W.append(f"| {lab} | {a} | {b} | {s} | {'OK' if ok else 'FAIL'} |")
W += ["", "## Notes\n",
      "- RESTYLE: a new generator, built for this restyled figure; `docs/thesis/summary/flights/fl_1A_unaligned_paths.png` and "
      "its own `index_flights.md` entry (`eval/figs_walkthrough_flights.py`) are NOT touched, NOT re-run, and NOT re-checked "
      "by this script - they remain exactly as that generator last wrote them.",
      "- Removed from the walkthrough source figure, per the thesis restyle rules (RS; D113): the score box (per-estimator "
      "median cruise ATE), the ranking-rule box, the one-line finding title/headline, and the raw/fitted corner tag. The "
      "median cruise ATEs and the ranking-rule result are in Table 4.4 (provisional) and Table A.4 respectively, not drawn "
      "here.",
      "- R6-1 (handover): the walkthrough's own gating tolerance (10°, not R5's single-flight 2.0°) is reused unchanged - see "
      "the module docstring and the Frame check section above for the full reasoning (a genuine, small early-cruise heading "
      "error on 2 of 9 flights for the UKF/FGO, not a frame bug).",
      "- R6-2 (handover): the caption's verdict pointer (appended by `eval/add_caption_verdict_pointers.py`) names H1.1, the "
      "registered confirmatory EKF3-vs-FGO ranking test for the standard-sensor (no-heading) dataset. H1.1's own registered "
      "sample is flights 4-10 (a different, paired population, `numbers.md` §6.1) - NOT the same 9 flights shown here (1-9, "
      "the same population as Table 4.4's medians). This figure is the panorama of which H1.1's sample is a subset; it is "
      "not itself H1.1 evidence. Table 4.4 (T9, `eval/figs_thesis.py`) states the same distinction in its own notes.",
      "- Line weight, wall-band colour and the end-point frame-check formula are the same as "
      "`eval/figs_walkthrough_flights.py`'s own `fl_1A_unaligned_paths`; only the drawn elements differ (restyle rules)."]
open(INDEX, "w").write("\n".join(W) + "\n")
write_caption("R6", f"{TITLE}.\n\n{CAP}")
print(f"cross-checks {n_ok}/{len(CHK)}; frame {n_pass10}/{len(FR)} (10 deg), {n_pass2}/{len(FR)} (2 deg); "
      "wrote R6_drift_9flights + index_drift9.md")
