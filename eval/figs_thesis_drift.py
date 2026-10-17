#!/usr/bin/env python3
"""FIGURE 4.1c (PROVISIONAL, internal id R5): offline standard-sensor drift, UNALIGNED (trajectory option (c), user ruling
2026-10-17, METHODOLOGY item 2). Built ONLY from stored outputs: no estimator run, no simulation.

Outputs:
  docs/thesis/figures_thesis/R5_drift_unaligned.{png,pdf}
  docs/thesis/figures_thesis/index_drift.md      caption, inputs, frame check, cross-check table

Flight: the same rule as Figure 4.2 (R3) panel (a): of the 9 textured-floor flights of the standard-sensor dataset, the flight whose
mean cruise ATE over EKF3, UKF and FGO is the median (5th of 9). The rule is recomputed here and must give flight 3.

FRAMES (checked before plotting; the script stops if the check fails):
  truth   ekf3/ground_truth.tum is (N, E, D); ukf|fgo/ground_truth.tum is ENU (E, N, U); origin at take-off in both.
  EKF3    ekf3_traj.tum is (N, E, D), origin at take-off; no rotation applied.
  UKF/FGO {ukf,fgo}_traj.tum: the estimators start with yaw 0 (ukf_core.py:318; fgo_core.py:120 via fgo_replay.py:134), i.e. x along
          the take-off heading, z up. The drone spawns at yaw 90 deg ENU (sim/worlds/corridor_textured.sdf:218), i.e. heading North.
          So, by construction (not a fit), est x = North and est y = West: the fixed relabelling (N, E) = (x, -y), the same map as
          eval/phase5_analysis.py:12-14. No other rotation, offset or scale is applied to any estimate.
  Check: horizontal position at the first sample (take-off) ~0, and the direction of each mapped estimate's displacement over the
  first 5 m of true cruise travel within HEAD_TOL_DEG of truth's.

Rounding and palette: rd() and the Okabe-Ito colours parsed from eval/figs_thesis.py (not executed), as figs_thesis_results.py does.
Usage: /home/makerspace/venv-evo/bin/python eval/figs_thesis_drift.py"""
import ast, hashlib, json, math, os, re, subprocess, sys, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUTF = os.path.join(ROOT, "docs", "thesis", "figures_thesis"); INDEX = os.path.join(OUTF, "index_drift.md")
SCRIPT = "eval/figs_thesis_drift.py"
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
    elif isinstance(n, ast.Expr) and "rcParams.update" in (ast.get_source_segment(_src, n) or ""):
        _nodes.append(n)
_ns = {"np": np, "plt": plt, "Line2D": Line2D, "textwrap": textwrap, "re": re}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
C, TRUTH, EST, INK, INK2, GRID = (_ns[k] for k in ("C", "TRUTH", "EST", "INK", "INK2", "GRID"))
RD_SHA = hashlib.sha256(_rd_src.encode()).hexdigest()
assert C == {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"} and TRUTH == "#999999", "palette changed in figs_thesis.py"

L = lambda f: json.load(open(os.path.join(RES, f)))
NUM = open(os.path.join(ROOT, "docs", "thesis", "numbers.md")).read().split("\n")
CHK = []


def norm(s):
    return s.replace("**", "").replace("`", "").replace("\\|", "|")


def check(label, computed, expected, src, line_text=None):
    """EXACT string equality; if line_text is given, the expected string must also occur in that numbers.md line."""
    inline = True if line_text is None else (norm(str(expected)) in norm(line_text))
    ok = str(computed) == str(expected) and inline
    CHK.append((label, str(computed), str(expected), src, ok))
    if not ok:
        print("   CHECK FAIL:", label, computed, expected, "" if inline else "NOT IN LINE")
    return ok


# =============================================================================================== flight choice (R3 rule)
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
DSNA = {i: {e: ev[f"dsn_tex_r{i}"]["est"][e]["ate_a_cruise"]["+0.00"] for e in EST} for i in range(1, 10)}
means = sorted((np.mean(list(DSNA[i].values())), i) for i in range(1, 10)); ra = means[4][1]
assert ra == 3, f"R3 rule now selects flight {ra}, not 3: stop and re-read the brief"
TR = f"dsn_tex_r{ra}"; WIN = ev[TR]["window_s"]
print(f"R5 flight: {TR} (median of 9 by mean cruise ATE; order {[i for _, i in means]}); cruise window {WIN}")

# =============================================================================================== load, map frames
SUB = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF": ("ukf", "ukf_traj.tum"), "FGO": ("fgo", "fgo_traj.tum")}
ld = lambda sub, f: np.loadtxt(f"{TD}/{TR}/{sub}/{f}")


def to_NE(key, a, truth):
    """(t, North, East) with NO alignment. EKF3 and its truth file: (N, E, D). UKF/FGO truth files: ENU (E, N, U).
    UKF/FGO estimates: own frame, x = take-off heading (North), y = left (West) -> (N, E) = (x, -y)."""
    if key == "EKF3":
        return a[:, 0], a[:, 1], a[:, 2]
    if truth:
        return a[:, 0], a[:, 2], a[:, 1]
    return a[:, 0], a[:, 1], -a[:, 2]


DATA = {}
for key, (sub, f) in SUB.items():
    DATA[key] = (to_NE(key, ld(sub, f), False), to_NE(key, ld(sub, "ground_truth.tum"), True))

# ---------------------------------------------------------------------------- FRAME CHECK (stop condition)
HEAD_TOL_DEG = 2.0; ORIG_TOL_M = 0.05
FRAME = []
for key, ((te, ne, ee), (tg, ng, eg)) in DATA.items():
    o_est = math.hypot(ne[0], ee[0]); o_gt = math.hypot(ng[0], eg[0])
    # first 5 m of true cruise travel: from the window start to where truth has gone 5 m further North
    i0 = np.searchsorted(tg, WIN[0]); j0 = i0 + np.argmax(ng[i0:] - ng[i0] >= 5.0)
    ta, tb = tg[i0], tg[j0]
    dN_g, dE_g = ng[j0] - ng[i0], eg[j0] - eg[i0]
    dN_e = np.interp(tb, te, ne) - np.interp(ta, te, ne); dE_e = np.interp(tb, te, ee) - np.interp(ta, te, ee)
    h_g = math.degrees(math.atan2(dE_g, dN_g)); h_e = math.degrees(math.atan2(dE_e, dN_e))
    ok = o_est < ORIG_TOL_M and o_gt < ORIG_TOL_M and abs(h_e - h_g) < HEAD_TOL_DEG
    FRAME.append((key, o_est, o_gt, ta, tb, h_e, h_g, ok))
    print(f"frame {key}: take-off |NE| est {o_est:.4f} m, truth {o_gt:.4f} m; first-5 m heading est {h_e:+.3f} deg vs truth "
          f"{h_g:+.3f} deg (t {ta:.2f}-{tb:.2f} s): {'PASS' if ok else 'FAIL'}")
if not all(r[-1] for r in FRAME):
    sys.exit("FRAME CHECK FAILED: an estimate is not in truth's frame; not plotting (stop condition of the brief)")

# truth timebases: the EKF3 and UKF/FGO truth files must describe the same truth (spot check at 5 times inside the window)
for t in np.linspace(WIN[0] + 5, WIN[1] - 5, 5):
    a = DATA["EKF3"][1]; b = DATA["UKF"][1]
    d = math.hypot(np.interp(t, a[0], a[1]) - np.interp(t, b[0], b[1]), np.interp(t, a[0], a[2]) - np.interp(t, b[0], b[2]))
    assert d < 0.05, f"truth files disagree by {d:.3f} m at t {t:.1f}"

# =============================================================================================== data-identity check (cruise ATE)
from evo.core import sync, metrics
from evo.core.trajectory import PoseTrajectory3D


def tum_traj(a):
    return PoseTrajectory3D(positions_xyz=a[:, 1:4], orientations_quat_wxyz=a[:, [7, 4, 5, 6]], timestamps=a[:, 0])


def cruise_ate(sub, f, win):
    """Copied from eval/figs_thesis_results.py aligned() (= eval/three_way_eval.py): crop to the stored window, associate
    (0.05 s), Umeyama SE(3) without scale, translation RMSE. Used ONLY as a data-identity check; NOTHING plotted is aligned."""
    ref = ld(sub, "ground_truth.tum"); est = ld(sub, f)
    c = lambda a: a[(a[:, 0] >= win[0]) & (a[:, 0] <= win[1])]
    r, e = sync.associate_trajectories(tum_traj(c(ref)), tum_traj(c(est)), 0.05)
    e.align(r, correct_scale=False)
    m = metrics.APE(metrics.PoseRelation.translation_part); m.process_data((r, e))
    return m.get_statistic(metrics.StatisticsType.rmse)


NUMLN = {"EKF3": (221, ["4.03", "3.86", "4.10"]), "FGO": (223, ["4.05", "1.80", "4.48"]), "UKF": (225, ["3.98", "1.61", "5.17"])}
for key, (sub, f) in SUB.items():
    st = ev[TR]["est"][key]["ate_a_cruise"]["+0.00"]
    check(f"{TR} {key}: recomputed cruise ATE (evo -a, stored window) vs stored, 6 dp", rd(cruise_ate(sub, f, WIN), 6), rd(st, 6),
          f"rerun_dsn_evo.json:{TR}.est.{key}.ate_a_cruise")
    ln, vals = NUMLN[key]
    check(f"{TR} {key}: displayed cruise ATE (m), legend", rd(st, 2), vals[ra - 1], f"docs/thesis/numbers.md:{ln}", NUM[ln - 1])
check("flights in the dataset (caption 'of 9')", str(len(DSNA)), "9", "rerun_dsn_evo.json + dsn_extra_evo.json: dsn_tex_r1..r9")
check("flight shown (R3 rule)", str(ra), "3", "R3 rule (eval/figs_thesis_results.py), recomputed")

# =============================================================================================== errors vs true distance travelled
LBL = {"EKF3": "EKF3 (no heading)", "UKF": "UKF (no heading)", "FGO": "FGO (no heading)"}
ERR = {}
for key, ((te, ne, ee), (tg, ng, eg)) in DATA.items():
    k = (te >= tg[0]) & (te <= WIN[1])                      # from take-off (first truth sample) to the end of the stored cruise window
    gN = np.interp(te[k], tg, ng); gE = np.interp(te[k], tg, eg)
    ERR[key] = (gN, ne[k] - gN, ee[k] - gE, ne[k], ee[k])
TP = DATA["UKF"][1]; kt = TP[0] <= WIN[1]

STRETCH = 1.0
fig = plt.figure(figsize=(15.5, 13.2))
gs = fig.add_gridspec(3, 1, height_ratios=[1.45, 1.0, 1.0], hspace=0.36)
ax0 = fig.add_subplot(gs[0]); ax1 = fig.add_subplot(gs[1]); ax2 = fig.add_subplot(gs[2], sharex=ax1, sharey=ax1)
# --- top: paths
ax0.plot(TP[1][kt], TP[2][kt], color=TRUTH, lw=3.2, solid_capstyle="round", zorder=2, label="truth (simulator)")
for key in EST:
    gN, aE, cE, nE, eE = ERR[key]
    ax0.plot(nE, eE, color=C[key], lw=1.3, ls=(0, (5, 3)), zorder=3,
             label=f"{LBL[key]}; cruise ATE after alignment (Figure 4.2) {rd(ev[TR]['est'][key]['ate_a_cruise']['+0.00'], 2)} m")
emax = max(ERR[k][4].max() for k in EST); emin = min(ERR[k][4].min() for k in EST)
YL0, YL1 = min(emin, 0) - 4.0, emax + 4.0
ax0.set_xlim(-2, 162); ax0.set_ylim(YL0, YL1); ax0.set_aspect(STRETCH, adjustable="box"); ax0.grid(True, color=GRID, lw=0.6)
ax0.set_xlabel("North, along the corridor (m)"); ax0.set_ylabel("East (m)")
ax0.set_title(f"(a) top-down paths from take-off, UNALIGNED: each estimate in its own navigation frame (standard-sensor dataset, "
              f"textured floor, flight {ra})", loc="left", fontsize=10.5)
ax0.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), fontsize=8.2, frameon=True, framealpha=0.95, edgecolor=GRID)
fig.canvas.draw()
bb = ax0.get_window_extent().transformed(fig.dpi_scale_trans.inverted()); x0, x1 = ax0.get_xlim(); y0, y1 = ax0.get_ylim()
st_meas = (bb.height / (y1 - y0)) / (bb.width / (x1 - x0))
check("lateral stretch printed on panel (a) vs drawn axes geometry", rd(st_meas, 1), rd(STRETCH, 1), "set_aspect() of panel (a)")
ax0.text(161, YL0 + 1.0, f"East axis stretched {rd(STRETCH, 1)}× relative to North (equal scale)", ha="right", va="bottom", fontsize=8.4, color=INK2)
# --- bottom: errors, same y-limits (shared y)
for ax, idx, ttl, yl in ((ax1, 1, "(b) along-track error: estimated North − true North", "along-track error (m)"),
                         (ax2, 2, "(c) sideways (cross-track) error: estimated East − true East", "sideways error (m)")):
    ax.axhline(0, color=TRUTH, lw=1.6, zorder=1)
    for key in EST:
        ax.plot(ERR[key][0], ERR[key][idx], color=C[key], lw=1.3, ls=(0, (5, 3)), label=LBL[key])
    ax.set_ylabel(yl); ax.set_title(ttl, loc="left", fontsize=10.5); ax.grid(True, color=GRID, lw=0.6)
lo = min(min(ERR[k][1].min(), ERR[k][2].min()) for k in EST); hi = max(max(ERR[k][1].max(), ERR[k][2].max()) for k in EST)
pad = 0.06 * (hi - lo); ax1.set_ylim(lo - pad, hi + pad); ax1.set_xlim(-2, 162)
assert ax1.get_ylim() == ax2.get_ylim()
ax2.set_xlabel("true distance travelled along the corridor, North (m)")
ax1.legend(loc="upper left", fontsize=8.2, frameon=True, framealpha=0.95, edgecolor=GRID, ncol=3)
ax1.text(0.995, 0.96, "same y-scale in (b) and (c)", transform=ax1.transAxes, ha="right", va="top", fontsize=8.4, color=INK2)
fig.suptitle("Without a heading source, all three estimates drift sideways: the unaligned paths and their errors along the corridor",
             x=0.01, ha="left", fontsize=12.5, weight="bold", y=0.93)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUTF, f"R5_drift_unaligned.{ext}"), dpi=170 if ext == "png" else None, bbox_inches="tight")
plt.close(fig)

# =============================================================================================== caption + index
CAP = (f"Offline standard-sensor dataset (IMU, downward flow, downward LiDAR; no heading source), textured floor, flight {ra}, chosen by "
       "the same rule as Figure 4.2(a), fixed before plotting: of the 9 textured-floor flights that all three estimators complete, the "
       "flight whose mean cruise ATE over EKF3, UKF and FGO is the median (5th of 9). n = 1 flight shown (of 9). Passive estimators, "
       "truth flying. (a) Top-down paths from take-off to the end of the cruise window, truth grey. Unlike Figure 4.2, the paths are "
       "NOT aligned: each estimate is drawn as estimated, in its own navigation frame with its origin at take-off, so the sideways "
       "drift caused by heading error, which the SE(3) alignment of the cruise ATE (and of Figure 4.2) removes, is shown; it reaches "
       "tens of metres by the end of the cruise. No fitted alignment is applied to any estimate. EKF3 reports North/East directly. The "
       "UKF and FGO trajectories are expressed in the world frame by a fixed axis relabel from the known take-off heading (the vehicle "
       "spawns facing North, and both start with yaw 0 along it, so their x is North and their y is West: (North, East) = (x, −y)), "
       "the same convention as eval/phase5_analysis.py. The "
       f"East axis is stretched {rd(STRETCH, 1)}× relative to North (equal scale: the drift is large enough not to need stretching); the legend gives each estimator's stored cruise ATE (after "
       "alignment, as in Figure 4.2) for reference. (b) Along-track error (estimated North − true North) and (c) sideways error "
       "(estimated East − true East) against the true distance travelled along the corridor, from take-off to the end of the cruise "
       "window (the stop and landing are not drawn). Truth is interpolated to each estimator's own timestamps. (b) and (c) share one "
       "y-scale. The along-track error is not a pure scale error: a heading error also shortens the North component of the "
       "estimated travel. Dashed: no heading source (all three). No log axes.")
TITLE = "Without a heading source, all three estimates drift sideways: the unaligned paths and their errors along the corridor"
n_ok = sum(1 for c in CHK if c[-1])
W = [f"# Figure 4.1c (provisional): offline standard-sensor drift, unaligned (internal id R5)\n",
     f"Generated by `{SCRIPT}` at commit `{COMMIT}` (outputs from the working tree at that commit). Stored outputs only: no estimator "
     "run, no simulation. **Provisional label; nothing else is renumbered.**\n",
     f"**Cross-checks:** {n_ok}/{len(CHK)} EXACT (string equality after one rounding by `rd()`; numbers.md strings must also occur in "
     f"the cited line). **Frame check:** {sum(1 for r in FRAME if r[-1])}/{len(FRAME)} PASS.\n",
     f"**Rounding:** `rd()` parsed from `eval/figs_thesis.py` (not executed); SHA-256 of its source `{RD_SHA}`. Palette: Okabe–Ito, "
     f"EKF3 {C['EKF3']}, UKF {C['UKF']}, FGO {C['FGO']}, truth {TRUTH}.\n",
     "## Figure\n", "| file | title |", "|---|---|", f"| `figures_thesis/R5_drift_unaligned.{{png,pdf}}` | {TITLE} |\n",
     "## Caption\n", CAP + "\n",
     "## Inputs\n",
     f"- `~/thesis_data/trials/{TR}/ekf3/{{ekf3_traj,ground_truth}}.tum` (N, E, D)",
     f"- `~/thesis_data/trials/{TR}/ukf/{{ukf_traj,ground_truth}}.tum`, `~/thesis_data/trials/{TR}/fgo/{{fgo_traj,ground_truth}}.tum` "
     "(estimate: own frame, x = take-off heading; truth: ENU)",
     "- cruise windows and cruise ATEs: `eval/results/rerun_dsn_evo.json`, `eval/results/dsn_extra_evo.json`; displayed ATEs: "
     "`docs/thesis/numbers.md:221,223,225`\n",
     "## Frame check (stop condition of the brief)\n",
     "Spawn yaw 90° ENU = heading North (`sim/worlds/corridor_textured.sdf:218`); UKF yaw0 = 0 (`src/estimators/ukf_core.py:318`); "
     "FGO yaw0 = 0 (`src/estimators/fgo/fgo_core.py:120`, `fgo_replay.py:134`). Map for the UKF/FGO: (N, E) = (x, −y), as "
     f"`eval/phase5_analysis.py:12-14`. Pass: take-off |NE| < {ORIG_TOL_M} m and heading of the first 5 m of true cruise travel within "
     f"{HEAD_TOL_DEG}° of truth.\n",
     "| estimator | take-off \\|NE\\| est (m) | take-off \\|NE\\| truth (m) | interval (s) | est heading (°, from North) | truth heading (°) | result |",
     "|---|---|---|---|---|---|---|"]
for key, o_e, o_g, ta, tb, he, hg, ok in FRAME:
    W.append(f"| {key} | {o_e:.4f} | {o_g:.4f} | {ta:.2f}–{tb:.2f} | {he:+.3f} | {hg:+.3f} | {'PASS' if ok else 'FAIL'} |")
W += ["", "Diagnostic values above are for the check only and are not printed on the figure.\n",
      "## Cross-checks\n", "| check | computed | expected | source | result |", "|---|---|---|---|---|"]
for lab, a, b, s, ok in CHK:
    W.append(f"| {lab} | {a} | {b} | {s} | {'OK' if ok else 'FAIL'} |")
W += ["", "## Notes\n",
      "- Numbers on the figure: the flight number, the three displayed cruise ATEs, the stretch factor; numbers in the caption: "
      "the flight number, 9, 5th, n = 1, the stretch factor. All are in the table above (\"5th of 9\" follows from 9 by the median rule).",
      "- The unaligned end-of-cruise errors are deliberately not printed: they have no stored source row in numbers.md.",
      "- Finding (not a blocker): `ukf_replay.py:239-289` (and the FGO's `metrics.txt`) read the UKF/FGO TUM column 1 as East, but it is "
      "along the take-off heading (North); the stored `metrics.txt` fields `along_pN`, `cross_track`, `ate_apparatus` for these "
      "estimators are therefore axis-swapped and are not used here."]
open(INDEX, "w").write("\n".join(W) + "\n")
print(f"cross-checks {n_ok}/{len(CHK)}; frame {sum(1 for r in FRAME if r[-1])}/{len(FRAME)}; wrote R5_drift_unaligned + index_drift.md")
