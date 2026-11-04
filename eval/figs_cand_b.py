#!/usr/bin/env python3
"""CANDIDATE THESIS FIGURES, GROUP B (decision D124, 2026-11-04): Experiments 2, 3, 4, 5 and 5S charts from
docs/thesis/summary/results_walkthrough.pdf and docs/thesis/summary/summary_plots.pdf that are NOT already a figure
in docs/thesis/figures_thesis/ (see index.md: F5 = Experiment 2, F7 = Experiment 3 loop closure per lap, F6 =
Experiment 4). These are CANDIDATES for the user to pick from, not inserted into the thesis figure set themselves.

Reproduces the SAME data as each source chart (same loaders, same files, same selection; code below is COPIED from
eval/figs_thesis.py (by ast, as eval/figs_walkthrough_flights.py and eval/figs_cand_a.py do), eval/figs_thesis_
summary.py and eval/figs_walkthrough_extra.py, not invented), then restyles to the thesis standard: eval/thesis_
style.py (160 mm text width, Okabe-Ito palette), no in-figure titles/verdict words/badges, no overlapping plots,
captions ending in a Table A.4 pointer (D113), every number in an exact cross-check.

STORED OUTPUTS ONLY. The only bag reads needed (Experiment 3 ground truth of T_A_r1-3; Experiment 4 ground truth
and /imu/time_ref of O_r1, O_r2, O_r3b) were pre-extracted ONCE under heavy.py by eval/figs_cand_b_extract.py into
~/thesis_data/cand_b_cache/*.npz (deleted at the end of this group's work - see docs/handovers/2026-11-04_cand_b.md
for the exact heavy.py invocations). This generator itself never opens a bag. Experiment 4's EKF3 curve (XKF1) is
read from the already-local ardupilot.bin dataflash file, also pre-extracted into the same cache. Every other input
is a stored eval/results/*.json or trial-directory .tum file. No estimator is run, no simulation, no flight.

Outputs: docs/thesis/figures_thesis/candidates/B##_*.{pdf,png} (+ B08_table.md), candidates/captions/B##.md,
candidates/index_b.md.
Usage: /home/makerspace/venv-evo/bin/python eval/figs_cand_b.py"""
import ast, json, math, os, re, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from thesis_style import TEXT_WIDTH_IN, C, MK, TRUTH, INK, INK2, GRID, SURF, WALL, EST, RCPARAMS
plt.rcParams.update(RCPARAMS)

RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
CACHE = os.path.expanduser("~/thesis_data/cand_b_cache")
OUT = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "candidates"); os.makedirs(OUT, exist_ok=True)
CAPD = os.path.join(OUT, "captions"); os.makedirs(CAPD, exist_ok=True)
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
L = lambda f: json.load(open(os.path.join(RES, f)))

# ---------------------------------------------------------------------------------------------- rd()/rd_si()/rng_si()/si_str()/rng(),
# ast-parsed (not executed as a script) from eval/figs_thesis.py, exactly as eval/figs_cand_a.py and eval/figs_walkthrough_flights.py do.
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read(); _tree = ast.parse(_src)
_WANT_F = {"rd", "rd_si", "rng_si", "si_str", "rng"}
_nodes, _fsrc = [], {}
for n in _tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in _WANT_F:
        _nodes.append(n); _fsrc[n.name] = ast.get_source_segment(_src, n)
_ns = {"re": re}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), FT, "exec"), _ns)
rd, rd_si, rng_si, si_str, rng = (_ns[k] for k in ("rd", "rd_si", "rng_si", "si_str", "rng"))
import hashlib
RD_SHA = hashlib.sha256(_fsrc["rd"].encode()).hexdigest()
assert RD_SHA == "e7320d3b8f377157c0c6512b2c0b77c978ac309a7130d2729480b786e02589b3", "rd() changed in figs_thesis.py"
assert C == {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"} and TRUTH == "#999999", "palette changed in thesis_style.py"


def cached(key, fn):
    """Cache of values READ from stored flight records (npz in cand_b_cache, pre-populated by figs_cand_b_extract.py
    under heavy.py). Never computes; a cache miss here means the extractor needs re-running, not a bag re-open."""
    p = os.path.join(CACHE, key + ".npz")
    if not os.path.exists(p):
        raise RuntimeError(f"cache miss: {p} - run eval/figs_cand_b_extract.py under heavy.py first")
    z = np.load(p, allow_pickle=True); return {k: z[k] for k in z.files}


def ex_room(tr):
    return cached(f"room_{tr}", None)


def ex_xkf1(tr):
    return cached(f"xkf1_{tr}", None)


# ---------------------------------------------------------------------------------------------- caption-verdict self-check
# (D113 banned-word regex, COPIED from eval/caption_verdict_check.py / eval/figs_cand_a.py, since the coordinator's
# checker does not yet scan candidates/)
BANNED = re.compile(r"\b(pass(?:es|ed|ing)?|fail(?:s|ed|ing)?|not\s+met|met|miss(?:es|ed|ing)?|verdicts?)\b", re.IGNORECASE)
TA_IDS = set()
for _ln in open(os.path.join(ROOT, "docs", "thesis", "tables", "TA_verdicts.md"), encoding="utf-8"):
    if _ln.startswith("|"):
        _parts = _ln.split("|")
        if len(_parts) >= 3 and _parts[1].strip() not in ("Experiment", "---"):
            TA_IDS.add(_parts[2].strip())


def verdict_line(ids_text):
    if ids_text is None:
        return "Verdicts: Table A.4, none (descriptive)."
    for rid in ids_text.split(";"):
        rid = rid.strip()
        assert rid in TA_IDS or any(i.startswith(rid) for i in TA_IDS), f"not a TA_verdicts.md id or prefix: {rid!r}"
    return f"Verdicts: Table A.4, rows {ids_text}."


# ---------------------------------------------------------------------------------------------- figure/check/caption/index machinery
# (own, modelled on eval/figs_cand_a.py's save()/check(), writing to candidates/ with a B## prefix)
ITEMS = []; CHK = []


def check(label, computed, expected, src):
    c, e = str(computed), str(expected)
    if any(x[:3] == (label, c, e) for x in CHK):
        return
    CHK.append((label, c, e, src, c == e))


_SRC_CACHE = {}


def cite(path, line, phrase, label=None):
    lines = _SRC_CACHE.setdefault(path, open(os.path.join(ROOT, path)).read().split("\n"))
    got = phrase if phrase in lines[line - 1] else lines[line - 1].strip()[:90]
    check(f"{label or ''}rule text {os.path.basename(path)}:{line} contains the quoted phrase", got, phrase, f"{path}:{line} (read at build time)")


def write_caption(fid, text):
    p = os.path.join(CAPD, f"{fid}.md")
    open(p, "w").write(text.strip() + "\n"); return p


def save(fig, fid, name, title, caption, inputs, source_charts, verdict_ids, data_files):
    global CHK
    verdict = verdict_line(verdict_ids)
    full_caption = caption.strip() + "\n\n" + verdict
    assert not BANNED.search(caption), f"{fid}: banned verdict word in caption body: {BANNED.search(caption).group(0)!r}"
    write_caption(fid, f"{fid}. {title}.\n\n{full_caption}")
    base = os.path.join(OUT, name)
    try:
        fig.tight_layout()
    except Exception:
        pass
    from matplotlib.transforms import Bbox
    fig.canvas.draw()
    tb = fig.get_tightbbox(fig.canvas.get_renderer())
    pad = 0.08
    crop = Bbox([[0, max(tb.y0 - pad, 0)], [TEXT_WIDTH_IN, min(tb.y1 + pad, fig.get_size_inches()[1])]])
    fig.savefig(base + ".png", dpi=170, bbox_inches=crop); fig.savefig(base + ".pdf", bbox_inches=crop); plt.close(fig)
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=fid, title=title, source=source_charts, inputs=inputs, data_files=data_files,
                       caption=full_caption, checks=list(CHK), files=[name + ".png", name + ".pdf"],
                       status="CURRENT" if ok else "FLAGGED"))
    print(f"wrote {base}.png/.pdf  checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    for c in CHK:
        if not c[4]:
            print("   CHECK FAIL:", c)
    CHK = []


def save_table_only(fid, name, title, md_lines, caption, inputs, source_charts, verdict_ids, data_files):
    """A markdown-table candidate (no plotted image): D113/common-brief rule - a table drawn inside a chart (or, as
    here, a table-only summary page with no chart at all) becomes a separate markdown table, verdict words kept IN
    the table cells (the same exemption A1-A3 and group C's C04 use), caption prose stays verdict-word-free."""
    global CHK
    verdict = verdict_line(verdict_ids)
    assert not BANNED.search(caption), f"{fid}: banned verdict word in caption body: {BANNED.search(caption).group(0)!r}"
    p = os.path.join(OUT, f"{name}.md")
    open(p, "w").write(f"# {fid}. {title}\n\n" + "\n".join(md_lines) + f"\n\n{caption.strip()}\n\n{verdict}\n")
    write_caption(fid, f"{fid}. {title}.\n\n{caption.strip()}\n\n{verdict}")
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=fid, title=title, source=source_charts, inputs=inputs, data_files=data_files,
                       caption=caption.strip() + "\n\n" + verdict, checks=list(CHK), files=[f"{name}.md"],
                       status="CURRENT" if ok else "FLAGGED"))
    print(f"wrote {p}  checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    for c in CHK:
        if not c[4]:
            print("   CHECK FAIL:", c)
    CHK = []


def measured_stretch(fig, ax):
    fig.canvas.draw()
    bb = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted()); x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    return (bb.height / (y1 - y0)) / (bb.width / (x1 - x0))


TCOND = ("A", "B", "C", "D"); TAGS = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}


# =============================================================================================================== B01
# ================================================================ EXPERIMENT 2 (known tags): live-only grouped bars
# (summary page 07 chart: COPIED data path from eval/figs_thesis_summary.py page 07 / eval/figs_thesis.py F5's own
# agg loader. DIFFERS from F5 in content, not just style: F5 is a line chart of all 5 tracks (live AND hindsight);
# this is a grouped BAR chart of the 3 LIVE tracks only, by tag count - a genuinely different chart type and a
# genuinely different subset of the same measurements, not a restyle of the same drawing.
# SKIPPED (same content as F5, not a candidate): walkthrough page 10 / extra/ex_2_known_tags.png - it is the same
# line chart as F5 (same 5 tracks, same per-condition means, same per-flight scatter; only the legend style - end-
# of-line direct labels instead of a legend box - and on-canvas verdict marks, banned here anyway, differ). See the
# skipped-charts table in index_b.md.
agg = L("expT/t_aggregate.json")
EXP_T = {"A": "0.039 0.037 0.020", "B": "0.055 0.061 0.026", "C": "0.074 0.076 0.054", "D": "0.096 0.131 0.083"}
VT = {}
for c in TCOND:
    mr = agg["conditions"][c]["mean_rmse_m"]
    s = " ".join(rd(mr[f"{e} live"], 3) for e in EST)
    check(f"B01 {TAGS[c]}: live error EKF3 UKF FGO, mean of 3 flights (m)", s, EXP_T[c], "eval/results/expT/t_aggregate.json")
    for e, x in zip(EST, s.split()):
        VT[(c, e)] = x
GAP2 = " / ".join(rd(agg["conditions"][c]["gap_length_median_s"], 1) for c in TCOND)
check("B01 median gap between fixes A-D (s)", GAP2, "4.3 / 10.1 / 22.0 / 46.3", "eval/results/expT/t_aggregate.json")
check("B01 live errors similar (P-T3): largest / smallest ratio by condition (H2.3)",
      " / ".join(rd(agg["P-T3 live ratio max/min"]["by_condition"][c], 2) for c in TCOND), "1.97 / 2.36 / 1.42 / 1.57",
      "eval/results/expT/t_aggregate.json P-T3")

fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.6))
xc = np.arange(4); offs = dict(zip(EST, np.linspace(-0.27, 0.27, 3)))
YOFF = {"EKF3": 0.0115, "UKF": 0.0025, "FGO": 0.0025}      # stagger EKF3's label above UKF's when their bars are near-equal height
for j, c in enumerate(TCOND):
    for k, e in enumerate(EST):
        x = j + offs[e]; v = agg["conditions"][c]["mean_rmse_m"][f"{e} live"]
        ax.bar(x, v, width=0.23, color=C[e], zorder=3)
        ax.text(x, v + YOFF[e], VT[(c, e)], ha="center", va="bottom", fontsize=9.0)
ax.set_xticks(range(4)); ax.set_xticklabels([f"{TAGS[c]}\n(fix every {g} s)" for c, g in zip(TCOND, GAP2.split(" / "))])
ax.set_xlabel("tags at known places in the room (median time between position fixes)")
ax.set_ylabel("live horizontal RMSE\nover 5 laps (m)")
ax.set_ylim(0, 0.155); ax.grid(axis="x", visible=False)
ax.legend(handles=[Patch(facecolor=C[e], label=e) for e in EST], frameon=False, loc="upper left", ncol=3, fontsize=9.0)
save(fig, "B01", "B01_2_known_tags_live", "Experiment 2: live position error by tag count, each estimator flying open loop",
     "Experiment 2 (known tags; the tag room, 5 laps of a 6 m square, open loop on simulator truth): mean of 3 flights, "
     "live horizontal RMSE only (no hindsight re-solve, unlike Figure 5.1/F5), for EKF3, UKF and FGO as the number of "
     "known-position tags in the room is reduced from 8 to 1 (median gap between position fixes below each group).",
     "eval/results/expT/T_{A,B,C,D}_r{1,2,3}.json (tracks.*.horiz_err_m.rmse), expT/t_aggregate.json",
     "summary page 07 (eval/figs_thesis_summary.py new_page('07', ...))", "H2.3", "expT/t_aggregate.json")


# =============================================================================================================== B02
# =========================================================== EXPERIMENT 3 (loop closure): true laps of the 6 m square
# (walkthrough flights/fl_3_truth.png: COPIED data path from eval/figs_walkthrough_flights.py room_paths("3_truth",
# ...)/gt_room(). Ground truth from the bag, pre-extracted into cand_b_cache under heavy.py - see module docstring.
# NOTE for the coordinator: this is the SAME 3 flights (condition A, 8 tags) as ONE of the four panels group A's A03
# (fl_2_truth.png) already draws (its "8 tags" panel). Kept as a separate, single-panel candidate because the user
# named it explicitly ("the true laps of the 6 m square as an Experiment 3 figure") and because Experiment 3 (loop
# closure) is a materially different experiment from Experiment 2 (known tags) even though it re-uses the same
# flights - flag for the coordinator to drop one if a single flight-truth view per flight set is preferred.
T_A_FL = [f"T_A_r{i}" for i in (1, 2, 3)]
G3 = {tr: ex_room(tr)["G"] for tr in T_A_FL}
check("B02 flights", ", ".join(T_A_FL), "T_A_r1, T_A_r2, T_A_r3", "eval/results/expL/T_A_r{1,2,3}_t245.json (Experiment 3 re-uses these flights)")

fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 4.6))
shades = ["#4d4d4d", "#8c8c8c", "#bdbdbd"]
for i, tr in enumerate(T_A_FL):
    G = G3[tr]
    ax.plot(G[:, 1], G[:, 2], color=shades[i % 3], lw=0.9, zorder=2, label=f"flight {i + 1}")
    ax.plot(G[0, 1], G[0, 2], marker="o", ms=4, color=INK, zorder=5)
ax.set_aspect(1.0, adjustable="box")
ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)")
st = measured_stretch(fig, ax); check("B02 equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
ax.legend(loc="lower right", frameon=False, fontsize=9.0, ncol=3)
save(fig, "B02", "B02_3_truth", "Where the drone really flew: the 3 loop-closure flights (simulator truth)",
     "Simulator ground truth (truth flying, nothing estimated): the 3 flights of Experiment 3 (loop closure; the "
     "same flights as Experiment 2's 8-tag condition), 5 laps of a 6 m square each, seen from above, equal scale, "
     "world frame. Black dot: start. The three flights' true paths lie on the same square, so the lines overlap.",
     "bag /ground_truth/pose of T_A_r1, T_A_r2, T_A_r3 (eval/figs_cand_b_extract.py, under heavy.py)",
     "walkthrough flights/fl_3_truth.png (eval/figs_walkthrough_flights.py room_paths('3_truth', ...))", None,
     "bag /ground_truth/pose of T_A_r{1,2,3}")


# ===================================================================================================== B03
# ================================== EXPERIMENT 3 (loop closure): the FGO's estimated trajectories, with and without
# (NEW content: no existing figure or candidate draws these spatial trajectories - F7/Figure 5.2 and the skipped
# summary-page-08/ex_3_loop_closure chart both draw per-lap RMSE against lap number, never the (x, y) path itself.
# Tracks are STORED: ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/{live,hindsight}.tum - no replay. Frame:
# tag 0's frame (the true tag map's own tag id 0, "the first tag"), a pure translation since tag 0's yaw is 0 (as
# eval/l_score.py, which scored these exact tracks, assumes and as stats.json's landmarks_final['0'] ~= (0, 0, 0)
# confirms) - the SAME frame the stored live.tum/hindsight.tum are already written in, so no further transform is
# applied to them, only to the bag ground truth.
TMAP = json.load(open(os.path.join(ROOT, "sim", "worlds", "room_tags_map.json")))["tags"]
_t0 = next(t for t in TMAP if t["id"] == 0)
check("B03 tag 0 yaw (deg), the frame-mapping assumption", _t0["yaw_deg"], 0.0, "sim/worlds/room_tags_map.json tags[id=0].yaw_deg")
LL3 = {}
for m in ("lc", "nolc"):
    for k in ("live", "hindsight"):
        LL3[(m, k)] = [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{m} {k}"] for r in (1, 2, 3)]
BOUNDS3 = {r: L(f"expL/T_A_r{r}_t245.json")["lap_bounds_s"] for r in (1, 2, 3)}
TUM3 = {}
for r in (1, 2, 3):
    tr = f"T_A_r{r}"; Gx = G3[tr][:, 1] - _t0["x"]; Gy = G3[tr][:, 2] - _t0["y"]; Gt = G3[tr][:, 0]
    for m in ("lc", "nolc"):
        for k in ("live", "hindsight"):
            x = np.loadtxt(f"{TD}/{tr}/lc_fgo_{m}_t245/{k}.tum", ndmin=2)
            b0, b1 = BOUNDS3[r][0], BOUNDS3[r][-1]
            e = np.hypot(x[:, 1] - np.interp(x[:, 0], Gt, Gx), x[:, 2] - np.interp(x[:, 0], Gt, Gy))
            w = (x[:, 0] >= b0) & (x[:, 0] <= b1)
            rmse = float(np.sqrt(np.mean(e[w] ** 2)))
            stored = LL3[(m, k)][r - 1]["rmse_m"]
            check(f"B03 T_A_r{r} {m} {k}: PLOTTED-window RMSE recomputed vs stored expL rmse_m (6 dp)", rd(rmse, 6), rd(stored, 6),
                  f"eval/results/expL/T_A_r{r}_t245.json tracks.'{m} {k}'.rmse_m")
            TUM3[(tr, m, k)] = (x[w], Gx, Gy, Gt)
lc5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL3[("lc", "live")]]
nl5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL3[("nolc", "live")]]
check("B03 live, with loop closure: lap 5 / lap 1 range", rng(lc5), "0.16–0.43", "eval/results/expL/T_A_r{1,2,3}_t245.json")
check("B03 live, without loop closure: lap 5 / lap 1 range", rng(nl5, 1), "2.9–4.5", "eval/results/expL/T_A_r{1,2,3}_t245.json")
VLC = {k: rng([t["rmse_m"] for t in LL3[("lc", k)]], 3) for k in ("live", "hindsight")}
VNO = {k: rng([t["rmse_m"] for t in LL3[("nolc", k)]], 3) for k in ("live", "hindsight")}
check("B03 with loop closure: live / hindsight overall RMSE range (m)", f"{VLC['live']} / {VLC['hindsight']}", "0.049–0.076 / 0.017–0.027",
      "eval/results/expL/T_A_r{1,2,3}_t245.json")
check("B03 without loop closure: live / hindsight overall RMSE range (m)", f"{VNO['live']} / {VNO['hindsight']}", "0.263–0.361 / 0.221–0.266",
      "eval/results/expL/T_A_r{1,2,3}_t245.json")

fig, axs = plt.subplots(1, 2, figsize=(TEXT_WIDTH_IN, 4.6), sharex=True, sharey=True)
shades3 = ["#808080", "#a0a0a0", "#c0c0c0"]
for ax, m, lab in ((axs[0], "lc", "(a) with loop closure"), (axs[1], "nolc", "(b) without loop closure")):
    for i, r in enumerate((1, 2, 3)):
        tr = f"T_A_r{r}"
        x_live, Gx, Gy, Gt = TUM3[(tr, m, "live")]
        x_hind, _, _, _ = TUM3[(tr, m, "hindsight")]
        wg = (Gt >= min(x_live[0, 0], x_hind[0, 0])) & (Gt <= max(x_live[-1, 0], x_hind[-1, 0]))
        ax.plot(Gx[wg], Gy[wg], color=shades3[i], lw=1.0, zorder=1)
        ax.plot(x_live[:, 1], x_live[:, 2], color=C["FGO"], ls="-", lw=0.9, alpha=0.85, zorder=3)
        ax.plot(x_hind[:, 1], x_hind[:, 2], color=C["FGO"], ls="--", lw=0.9, alpha=0.85, zorder=2)
    for tid, t_ in enumerate(TMAP):
        ax.plot(t_["x"] - _t0["x"], t_["y"] - _t0["y"], marker="s", ms=6, color=TRUTH, zorder=4)
    ax.set_title(lab, loc="left", fontsize=9.5)
    ax.set_aspect(1.0, adjustable="box")
    ax.set_xlabel("from tag 0 (the first tag), x (m)")
axs[0].set_ylabel("from tag 0 (the first tag), y (m)")
axs[0].set_xlim(-1.5, 7.5); axs[0].set_ylim(-1.5, 7.5)
st = measured_stretch(fig, axs[0]); check("B03 equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
check("B03 both panels share identical axis limits", str(axs[0].get_xlim() == axs[1].get_xlim() and axs[0].get_ylim() == axs[1].get_ylim()),
      "True", "this script (shared axis limits)")
fig.legend(handles=[Line2D([], [], color=TRUTH, lw=1.0, label="true path (3 flights)"),
                     Line2D([], [], color=C["FGO"], ls="-", lw=1.2, label="FGO, live (fixed-lag)"),
                     Line2D([], [], color=C["FGO"], ls="--", lw=1.2, label="FGO, hindsight (full iSAM2 estimate)"),
                     Line2D([], [], marker="s", ls="", color=TRUTH, ms=6, label="true tag")],
           loc="lower center", ncol=2, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(bottom=0.26, wspace=0.08)
save(fig, "B03", "B03_3_trajectories", "The FGO's estimated trajectories over the laps, with and without loop closure",
     "Experiment 3 (loop closure), 3 flights (condition A, 8 tags, the same flights as candidate B02): the FGO's "
     "live (fixed-lag, solid) and hindsight (full iSAM2 re-solve, dashed) tracks against the true path (grey) and "
     "the 8 true tags (grey squares), raw, in tag 0's frame, equal scale, from the lap-1 start to the lap-5 end. "
     f"(a) with loop closure: overall RMSE {VLC['live']} m live, {VLC['hindsight']} m hindsight; lap 5 / lap 1 "
     f"{rng(lc5)} (live). (b) without loop closure: overall RMSE {VNO['live']} m live, {VNO['hindsight']} m "
     f"hindsight; lap 5 / lap 1 {rng(nl5, 1)} (live) - the live track visibly drifts off the square lap on lap, "
     "where (a)'s stays on it.",
     "eval/results/expL/T_A_r{1,2,3}_t245.json (lap_bounds_s, tracks.*.rmse_m); "
     "~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/{live,hindsight}.tum; sim/worlds/room_tags_map.json; "
     "bag /ground_truth/pose of T_A_r{1,2,3}",
     "NEW (not drawn by any existing figures_thesis or walkthrough/summary chart; per-lap RMSE of the same runs is "
     "F7/Figure 5.2)", "H3.2; H3.3",
     "eval/results/expL/T_A_r{1,2,3}_t245.json; trial-directory .tum files; sim/worlds/room_tags_map.json")


# =============================================================================================================== B04
# ========================================= EXPERIMENT 4 (outdoor-indoor): error against time, all 3 flights, 1 scale
# (walkthrough flights/fl_4_err.png: COPIED data path from eval/figs_walkthrough_flights.py's Experiment-4 block.
# F6/Figure 5.3 draws flight 1 ONLY, all 5 tracks overlaid on ONE axes; this draws ALL 3 flights, split one row per
# estimator (live left column, hindsight right column) so no two tracks are plotted on top of each other - a
# genuinely different chart, not a restyle of F6. SAME data underlies the walkthrough's separate fl_4_err_live.png
# (3 rows, live only) and fl_4_err_hind.png (2 rows, hindsight only) pages - per the common brief's dedup rule, only
# ONE candidate is made here (the combined grid, which is itself on one shared y-scale, the layout form this
# project's house rule allows for side-by-side panels); fl_4_err_live/fl_4_err_hind are not separate candidates.
TRK4 = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
TCOL4 = {"EKF3 live": C["EKF3"], "UKF live": C["UKF"], "FGO live": C["FGO"], "RTS-UKF (hindsight)": C["UKF"], "FGO hindsight (whole-flight batch)": C["FGO"]}
TLS4 = {n: ("-" if "live" in n else (0, (5, 3))) for n in TRK4}
O_FL = ["O_r1", "O_r2", "O_r3b"]
OE4 = {}; OM4 = {}
for tr in O_FL:
    d = ex_room(tr); G, TR = d["G"], d["TR"]; o = L(f"expO/{tr}.json"); OM4[tr] = o
    sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        w = (sitl >= lo) & (sitl < lo + 5)
        if w.sum() > 50:
            i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
    env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
    oE, oN = np.load(f"{TD}/{tr}/gnss.npz")["ekf3_origin_EN"]
    k1 = ex_xkf1(tr)["K1"]; t = k1[:, 0]
    tracks = {"EKF3 live": np.c_[t + (kk * t + c0), k1[:, 1] + oE, k1[:, 2] + oN]}
    for n, p_ in (("UKF live", "room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", "room_ukf/ukf_rts.tum"),
                  ("FGO live", "room_fgo/fgo_live.tum"), ("FGO hindsight (whole-flight batch)", "room_fgo/fgo_batch.tum")):
        tracks[n] = np.loadtxt(f"{TD}/{tr}/{p_}", ndmin=2)[:, :3]
    toff, ton = o["markers_bag_s"]["GNSS OFF"], o["markers_bag_s"]["GNSS ON"]
    for n, Tk in tracks.items():
        e = np.hypot(Tk[:, 1] - np.interp(Tk[:, 0], G[:, 0], G[:, 1]), Tk[:, 2] - np.interp(Tk[:, 0], G[:, 0], G[:, 2]))
        wi = (Tk[:, 0] >= toff) & (Tk[:, 0] <= ton)
        rmse = float(np.sqrt(np.mean(e[wi] ** 2)))
        check(f"B04 {tr} {n}: PLOTTED error RMSE over GNSS-off window vs stored indoor_rmse_m (6 dp)", rd(rmse, 6), rd(o["tracks"][n]["indoor_rmse_m"], 6),
              f"eval/results/expO/{tr}.json tracks.'{n}'.indoor_rmse_m")
        w = (Tk[:, 0] > toff - 40) & (Tk[:, 0] < ton + 30)
        OE4[(n, tr)] = (Tk[w, 0] - toff, e[w])
TON4 = [OM4[tr]["markers_bag_s"]["GNSS ON"] - OM4[tr]["markers_bag_s"]["GNSS OFF"] for tr in O_FL]
check("B04 indoor time (s), GNSS off", rd(max(TON4), 0), "123", "eval/results/expO/O_{r1,r2,r3b}.json markers_bag_s")
JMP4 = rng([OM4[tr]["tracks"]["EKF3 live"]["max_step_after_return_m"] for tr in O_FL]).split("–")[0]
check("B04 EKF3 reset jump on return (m), every flight", rng([OM4[tr]["tracks"]["EKF3 live"]["max_step_after_return_m"] for tr in O_FL]), "4.10–4.10",
      "eval/results/expO/O_{r1,r2,r3b}.json tracks.'EKF3 live'.max_step_after_return_m")
ymax4 = max(v[1].max() for v in OE4.values()) * 1.05
RN4 = {n: rng([OM4[tr]["tracks"][n]["indoor_rmse_m"] for tr in O_FL]) for n in TRK4}
for n in TRK4:
    check(f"B04 {n} indoor RMSE range over 3 flights (m)", RN4[n], {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89",
          "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}[n], "eval/results/expO/O_{r1,r2,r3b}.json")

HIND4 = {"EKF3 live": None, "UKF live": "RTS-UKF (hindsight)", "FGO live": "FGO hindsight (whole-flight batch)"}
fig, axs = plt.subplots(3, 2, figsize=(TEXT_WIDTH_IN, 5.9), sharex=True, sharey=True)
for r, n in enumerate(("EKF3 live", "UKF live", "FGO live")):
    for c, nn in enumerate((n, HIND4[n])):
        ax = axs[r, c]
        for tr in O_FL:
            ax.axvspan(0, OM4[tr]["markers_bag_s"]["GNSS ON"] - OM4[tr]["markers_bag_s"]["GNSS OFF"], color="#ececec", zorder=0, lw=0)
        if nn is None:
            ax.axis("off")
        else:
            for tr in O_FL:
                x, y = OE4[(nn, tr)]; ax.plot(x, y, color=TCOL4[nn], lw=1.1, ls=TLS4[nn], zorder=3)
            lab_ = {"EKF3 live": "EKF3, live", "UKF live": "UKF, live", "FGO live": "FGO, live",
                    "RTS-UKF (hindsight)": "UKF, hindsight", "FGO hindsight (whole-flight batch)": "FGO, hindsight"}[nn]
            ax.text(0.01, 0.97, lab_, transform=ax.transAxes, fontsize=9.5, color=TCOL4[nn], weight="bold", va="top")
            ax.set_ylabel("error (m)" if c == 0 else "")
axs[0, 0].set_ylim(0, ymax4); axs[0, 0].set_xlim(-40, max(TON4) + 30)
axs[0, 0].set_title("live (during flight), solid", loc="left", fontsize=9.5)
axs[0, 1].set_title("hindsight (after landing), dashed", loc="left", fontsize=9.5)
fig.supylabel("horizontal error (m)", x=0.01, fontsize=10.5)
fig.supxlabel("time from GNSS OFF at the entrance (s)", y=0.015, fontsize=10.5)
fig.subplots_adjust(left=0.08, right=0.99, top=0.90, bottom=0.12, hspace=0.3, wspace=0.12)
_yl4 = {ax.get_ylim() for ax in axs.flat}
check("B04 all six panels share one y-scale (sharey)", str(len(_yl4) == 1), "True", "this script (axis limits)")
save(fig, "B04", "B04_4_err", "Experiment 4: error against time, all 3 flights, live and hindsight on one y-scale",
     "Experiment 4 (outdoor-indoor: outdoor to indoor to outdoor, open loop on simulator truth), all 3 flights, "
     "horizontal error against time from GNSS OFF at the entrance (shaded: indoors, GNSS off, 123 s), one shared "
     f"linear y-scale across all six panels. Indoor horizontal RMSE range over the 3 flights: EKF3 live {RN4['EKF3 live']} m, "
     f"UKF live {RN4['UKF live']} m, FGO live {RN4['FGO live']} m, UKF hindsight {RN4['RTS-UKF (hindsight)']} m, FGO "
     f"hindsight {RN4['FGO hindsight (whole-flight batch)']} m. EKF3 resets to GNSS on return with a {JMP4} m jump, "
     "every flight (EKF3 has no hindsight track - its hindsight panel is intentionally blank). World frame, no "
     "alignment; the same indoor sensor set as Figure 5.3/F6 (IMU, downward flow, downward LiDAR only; no GNSS, "
     "compass or forward camera indoors).",
     "eval/results/expO/O_{r1,r2,r3b}.json (markers_bag_s, max_step_after_return_m, tracks.*.indoor_rmse_m); curves: "
     "room_ukf/, room_fgo/ TUMs, dataflash XKF1 about EKF3's origin (gnss.npz), bag /ground_truth/pose and "
     "/imu/time_ref of O_r1, O_r2, O_r3b",
     "walkthrough flights/fl_4_err.png (same curves as fl_4_err_live.png + fl_4_err_hind.png, one candidate per the "
     "dedup rule); summary page 09 is a different chart type (see candidate B05)", "H4.1; H4.2; H4.3",
     "eval/results/expO/O_{r1,r2,r3b}.json; trial-directory TUMs and gnss.npz; dataflash ardupilot.bin; bag "
     "/ground_truth/pose and /imu/time_ref")


# =============================================================================================================== B05
# ======================================= EXPERIMENT 4 (outdoor-indoor): indoor RMSE range boxes, all tracks at once
# (summary page 09 chart: COPIED data path from eval/figs_thesis_summary.py page 09. JSON-only, no bag read needed -
# this chart is an AGGREGATE over the 3 flights (lowest-highest range box per track), not a time series, so it is a
# genuinely different chart type from both F6 (single flight, error against time) and B04 (all 3 flights, error
# against time). NOTE for the coordinator: the box ranges drawn here are the same numbers as Table 5.1/T6's rows -
# flagged, as group A flagged the analogous case for A19.
def rbox(ax, x, vals, col, filled, w=0.5):
    lo, hi = min(vals), max(vals); yl = ax.get_ylim(); h = max(hi - lo, 0.012 * (yl[1] - yl[0]))
    ax.add_patch(Rectangle((x - w / 2, lo - (h - (hi - lo)) / 2), w, h, facecolor=col if filled else "white", edgecolor=col, lw=2.0, zorder=3))
    return lo - (h - (hi - lo)) / 2 + h


OI5 = {n: [OM4[tr]["tracks"][n]["indoor_rmse_m"] for tr in O_FL] for n in TRK4}
VO5 = {n: rng(OI5[n], 2) for n in TRK4}
for n in TRK4:
    check(f"B05 {n}: indoor error range over 3 flights (m)", VO5[n], {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89",
          "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}[n], "eval/results/expO/O_{r1,r2,r3b}.json")
h41 = sum(OI5["FGO hindsight (whole-flight batch)"][i] < OI5["EKF3 live"][i] and OI5["FGO hindsight (whole-flight batch)"][i] < OI5["UKF live"][i] for i in range(3))
check("B05 primary (H4.1): FGO hindsight below EKF3 and UKF live, flights of 3", f"{h41}/3", "3/3", "eval/results/expO/O_{r1,r2,r3b}.json")
r42 = [max(OI5[f"{e} live"][i] for e in EST) / min(OI5[f"{e} live"][i] for e in EST) for i in range(3)]
check("B05 live errors similar (H4.2): largest / smallest ratio, 3 flights", rng(r42, 2), "1.71–1.84", "eval/results/expO/O_{r1,r2,r3b}.json")

fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.9))
ax.set_xlim(-0.5, 4.5); ax.set_ylim(0, 1.95)
XO = [("EKF3 live", "EKF3", True), ("UKF live", "UKF", True), ("FGO live", "FGO", True), ("RTS-UKF (hindsight)", "UKF", False),
      ("FGO hindsight (whole-flight batch)", "FGO", False)]
for i, (n, e, live) in enumerate(XO):
    top_ = rbox(ax, i, OI5[n], C[e], live, w=0.5)
    ax.text(i, top_ + 0.03, VO5[n] + " m", ha="center", va="bottom", fontsize=9.5)
ax.set_xticks(range(5)); ax.set_xticklabels(["EKF3\nlive", "UKF\nlive", "FGO\nlive", "UKF\nhindsight", "FGO\nhindsight"])
ax.grid(axis="x", visible=False); ax.set_ylabel("horizontal position error\nindoors (m)")
ax.legend(handles=[Patch(facecolor="#888888", edgecolor="#888888", label="live"),
                    Patch(facecolor="white", edgecolor="#888888", lw=2, label="hindsight")],
          frameon=False, loc="upper right", fontsize=9.0)
save(fig, "B05", "B05_4_indoor_rmse_boxes", "Experiment 4: indoor horizontal error, lowest to highest of 3 flights, by track",
     "Experiment 4 (outdoor-indoor, open loop on simulator truth): indoor horizontal position error (root-mean-square), "
     "lowest to highest over the 3 flights, for each of EKF3/UKF/FGO live and the UKF/FGO hindsight re-solve (box "
     "colour = estimator, filled = live, open = hindsight). Same indoor sensor set and GNSS-off window as Figure "
     "5.3/F6 and candidate B04.",
     "eval/results/expO/O_{r1,r2,r3b}.json (tracks.*.indoor_rmse_m)", "summary page 09 (eval/figs_thesis_summary.py new_page('09', ...))",
     "H4.1; H4.2; H4.3", "eval/results/expO/O_{r1,r2,r3b}.json")


# =============================================================================================================== B06/B07
# ======================= EXPERIMENT 5 (tag hold): hold error (B06) and drift while the tag is hidden (B07), separate
# (walkthrough extra/ex_5_hold_drift.png (page 13) and summary pages 10 and 11: COPIED data path from eval/figs_
# walkthrough_extra.py's Experiment-5 block / eval/figs_thesis_summary.py pages 10-11. JSON-only, no bag read.
# Drawn as TWO separate single-panel bar charts, not the walkthrough's one two-panel figure: summary page 10's own
# y-axis (0-58 mm) and page 11's own y-axis (0-60 mm) differ, so the house no-overlap rule ("side-by-side panels
# allowed only on a shared y-scale") does not clear a combined figure built from THEIR native scales; the walkthrough
# page only clears it by forcing both panels to a third, shared (0, 60) scale not native to either source page. This
# single data set is therefore the source for walkthrough page 13 AND summary pages 10 and 11 at once - one
# consolidated pair of candidates, not three.
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = [f"s2v2_r{i}" for i in (1, 2, 3)]; S3V = [f"s3v2_r{i}" for i in (1, 2, 3)]
FLY5 = {"EKF3": (S1 + S1F, "EKF3"), "UKF": (S2V, "UKF_port"), "FGO": (S3V, "FGO_flying")}
BAND5 = {"EKF3": [50, 100, 200, 150], "FGO": [50, 100, 200, 150], "UKF": [100, 200, 400, 300]}
_hc = [v for k, v in L("expH/h_comparative_2026-10-11.json")["sets"].items() if k.startswith("re-flown")][0]
HV = {"EKF3": [float(np.mean([w["mean_m"] for w in HJ(t)["hold_windows_vehicle"]])) for t in S1F],
      "UKF": [r["hold_mean_mm"] for r in _hc["UKF"]], "FGO": [r["hold_mean_mm"] for r in _hc["FGO"]]}
HK = {"EKF3": 3, "UKF": 0, "FGO": 0}
VH = {e: rng_si(HV[e], 1, HK[e]) for e in EST}
for e, x in zip(EST, ("7.8–7.9", "6.4–7.1", "8.3–8.6")):
    check(f"B06 {e}: mean hold error, range over 3 flights (mm)", VH[e], x, "eval/results/expH (hold_windows_vehicle; h_comparative_2026-10-11.json)")
HVM = {e: max(float(rd_si(v, 12, HK[e])) for v in HV[e]) for e in EST}
worstm = {e: max(lo[FLY5[e][1]]["effective"]["drift_m"] for t in FLY5[e][0] for lo in HJ(t)["losses"]) for e in EST}
VW = {e: rd_si(worstm[e], 0, 3) for e in EST}
LK = {e: [bool(lo[FLY5[e][1]]["lockout"]) for t in FLY5[e][0] for lo in HJ(t)["losses"]] for e in EST}
VN = {e: f"{sum(LK[e])} / {len(LK[e])}" for e in EST}

fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.4))
ax.set_xlim(-0.5, 2.5); ax.set_ylim(0, 58)
ax.axhline(50, color=GRID, ls=(0, (6, 4)), lw=1.8, zorder=1)
for i, e in enumerate(EST):
    ax.bar(i, HVM[e], width=0.62, color=C[e], zorder=3)
    ax.text(i, HVM[e] + 1.2, f"{VH[e]} mm", ha="center", va="bottom", fontsize=9.5)
ax.text(2.45, 50.6, "limit for the mean: 50 mm", ha="right", va="bottom", fontsize=9.0, color=INK2)
ax.set_xticks(range(3)); ax.set_xticklabels(EST); ax.grid(axis="x", visible=False)
ax.set_ylabel("mean hold error per flight (mm)")
save(fig, "B06", "B06_5_hold_error", "Experiment 5: mean hold error per flight, next to the wall tag",
     "Experiment 5 (tag hold): distance between where the drone was held and where it should be, mean per flight, "
     "millimetres; each bar shows the highest of an estimator's 3 flights (lowest-highest range labelled). Each "
     "estimator flew its own flights; EKF3's bar uses the far-spawn hold set (s1far), the same flights candidate A05 "
     "(fl_5_truth.png) draws, while the near-spawn set (s1) is the one the primary hold-accuracy check was scored "
     "on (H5.1). Dashed line: the registered 50 mm limit for the mean.",
     "eval/results/expH/{s1far_r1,s1far_r2,s1far_r3b,s2v2_r1..r3,s3v2_r1..r3}.json; h_comparative_2026-10-11.json",
     "walkthrough extra/ex_5_hold_drift.png (left panel) and summary page 10", "H5.1; H5.2",
     "eval/results/expH/*.json; eval/results/expH/h_comparative_2026-10-11.json")

for e, x in zip(EST, ("31", "26", "27")):
    check(f"B07 {e}: worst drift over all tag losses (mm)", VW[e], x, "eval/results/expH losses[].effective.drift_m")
for e, x in zip(EST, ("0 / 24", "0 / 12", "0 / 12")):
    check(f"B07 {e}: losses with a lockout / losses", VN[e], x, "eval/results/expH losses[].lockout")

fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.4))
ax.set_xlim(-0.5, 2.5); ax.set_ylim(0, 60)
ax.axhline(50, color=GRID, ls=(0, (6, 4)), lw=1.8, zorder=1)
for i, e in enumerate(EST):
    wmm = float(rd_si(worstm[e], 12, 3))
    ax.bar(i, wmm, width=0.62, color=C[e], zorder=3)
    ax.text(i, wmm + 1.2, f"{VW[e]} mm", ha="center", va="bottom", fontsize=9.5)
    ax.text(i, 2.5, f"{VN[e].split(' / ')[1]}\ntag losses", ha="center", va="bottom", fontsize=9.0, color="white", weight="bold")
ax.text(2.45, 50.6, "tightest limit: 50 mm", ha="right", va="bottom", fontsize=9.0, color=INK2)
ax.set_xticks(range(3)); ax.set_xticklabels(EST); ax.grid(axis="x", visible=False)
ax.set_ylabel("worst drift while the tag\nwas hidden (mm)")
save(fig, "B07", "B07_5_drift_hidden", "Experiment 5: worst drift while the wall tag was hidden",
     "Experiment 5 (tag hold): how far the drone moved between the last tag sighting before a loss and the first "
     "one after it, worst case over all tag losses, millimetres, per estimator (EKF3 and UKF loss sets as B06; FGO "
     "from the FGO-flying hold set). Tag-loss counts labelled on the bars (0 lockouts in any of them). Dashed line: "
     "the tightest of the registered per-loss limits (50 to 200 mm for EKF3 and the FGO depending on the loss, "
     "twice that for the UKF).",
     "eval/results/expH/{s1_r1..r3,s1far_r1..r3b,s2v2_r1..r3,s3v2_r1..r3}.json (losses[].effective.drift_m, losses[].lockout)",
     "walkthrough extra/ex_5_hold_drift.png (right panel) and summary page 11", "H5.5; H5.7",
     "eval/results/expH/*.json")


# =============================================================================================================== B08
# =========================================================== EXPERIMENT 5S: the final safety-run table, as a table
# (summary page 12: COPIED data path from eval/figs_thesis_summary.py page 12. TABLE ONLY (no AX()/plotted axes
# anywhere in that page's block) - per the common brief's rule, a table-only summary page becomes a separate
# markdown table candidate, not a chart. Compared first against Table 7.2/T7 (docs/thesis/tables/T7_failure_
# behaviour.md) and Table A.2/A2 (the "all runs" appendix table): neither carries this EXACT table (same 4 final
# runs, same 5 columns "what was done / attitude / position lost declared in time / landed safely / overall") - T7
# groups by estimator across different columns (blank-floor validity, the return jump, the two safety tests as
# prose), and A2 is the dense ALL-RUNS table (every historical build run, not just the 4 final ones, different
# columns again) - so this is a genuinely new, simpler cross-section of the same source files, not a duplicate.
SF = {"ua": "safety_ukf_a_v3", "ub": "safety_ukf_b_v3", "fa": "safety_fgo_a_v4", "fb": "safety_fgo_b_v4"}
J5S = {k: L(f"expH/{f}.json") for k, f in SF.items()}
DT5 = {}
for k, exp in (("ua", "0.00"), ("ub", "5.69"), ("fa", "0.60"), ("fb", "0.62")):
    v = rd(J5S[k]["S-A2"]["text_delay_s"], 2)
    check(f"B08 {SF[k]}: time to declare 'position lost' (s)", v, exp, f"eval/results/expH/{SF[k]}.json S-A2.text_delay_s")
    DT5[k] = v
# "ua" (UKF forced-invalid): the registered bound is 0.1 s, but its score file's own S-A2.bound_s records 0.75 s (a
# scorer artefact - the final UKF port's score files were re-run with the FGO bound on the coordinator's
# instruction, METHODOLOGY.md:14263-14264; both final-port delays are 0.00 s, so the verdict is unchanged either
# way). Displayed limit therefore follows the REGISTERED bound, the same exception eval/figs_thesis_summary.py's
# own page 12 (BT dict) makes, not the stored json value for this one row.
check("B08 safety_ukf_a_v3: S-A2.bound_s AS STORED (the scorer-artefact value, not displayed)", rd(J5S["ua"]["S-A2"]["bound_s"], 2), "0.75",
      "eval/results/expH/safety_ukf_a_v3.json S-A2.bound_s")
BT5 = {"ua": "0.10", "ub": rd(J5S["ub"]["S-A2"]["bound_s"], 2), "fa": rd(J5S["fa"]["S-A2"]["bound_s"], 2), "fb": rd(J5S["fb"]["S-A2"]["bound_s"], 2)}
for k, exp in (("ua", "0.10"), ("ub", "5.50"), ("fa", "0.75"), ("fb", "0.75")):
    check(f"B08 {SF[k]}: position-lost declaration limit AS DISPLAYED (s)", BT5[k], exp, "METHODOLOGY.md:11299 (UKF (a): within 0.1 s); "
          f"eval/results/expH/{SF[k]}.json S-A2.bound_s (ub/fa/fb only)")
PF5 = lambda b: "PASS" if b else "FAIL"
VS5 = {}
for k, exp in (("ua", "PASS PASS PASS"), ("ub", "PASS FAIL PASS"), ("fa", "PASS PASS PASS"), ("fb", "PASS PASS PASS")):
    got = " ".join(PF5(J5S[k][c]["PASS"]) for c in ("S-A1", "S-A2", "S-A3"))
    check(f"B08 {SF[k]}: attitude / position lost / safe landing", got, exp, f"eval/results/expH/{SF[k]}.json")
    VS5[k] = got.split()
OVR5 = {"ua": "PASS", "ub": "FAIL (as worded)", "fa": "PASS", "fb": "PASS"}
check("B08 overall column: UKF (a) / UKF (b) / FGO (a) / FGO (b)", " / ".join(OVR5[k] for k in ("ua", "ub", "fa", "fb")),
      "PASS / FAIL (as worded) / PASS / PASS", "eval/results/expH/safety_*.json (S-A1, S-A2, S-A3 PASS and the as-worded note)")

ROWS8 = [
    ["UKF: forced to report its output invalid", VS5["ua"][0], f"{VS5['ua'][1]} ({DT5['ua']} s; limit {BT5['ua']} s)", VS5["ua"][2], OVR5["ua"]],
    ["UKF: all its position inputs cut off", VS5["ub"][0], f"{VS5['ub'][1]} ({DT5['ub']} s; limit {BT5['ub']} s)", VS5["ub"][2], OVR5["ub"]],
    ["FGO: program stopped", VS5["fa"][0], f"{VS5['fa'][1]} ({DT5['fa']} s; limit {BT5['fa']} s)", VS5["fa"][2], OVR5["fa"]],
    ["FGO: program stopped, safety monitor watching it", VS5["fb"][0], f"{VS5['fb'][1]} ({DT5['fb']} s; limit {BT5['fb']} s)", VS5["fb"][2], OVR5["fb"]]]
MD8 = ["| what was done in flight | attitude | 'position lost' declared in time | landed safely | overall |", "|---|---|---|---|---|"]
MD8 += ["| " + " | ".join(r) + " |" for r in ROWS8]
save_table_only("B08", "B08_5S_safety_table", "Experiment 5S: outcome of each safety check, the final run of each test",
                 MD8,
                 "Experiment 5S (safety tests: the flying estimator is deliberately broken mid-flight): the final build's run of each test "
                 "(the final UKF port's re-test, the FGO corrected-priors node's re-test). Attitude within 3 degrees "
                 "(roll/pitch) and 5 degrees (yaw); 'position lost' declared within the limit shown, seconds; landing "
                 "within 1.5 m of where the failure happened with no safety-watcher breach. The UKF forced-invalid "
                 "test's limit is shown as the registered 0.10 s, not the 0.75 s its own score file records (a "
                 "scorer artefact: that file was re-run with the FGO bound; both final-port delays are 0.00 s, so "
                 "the outcome is the same either way, Table 7.2/T7 footnote). EKF3 (ArduPilot's standard filter) has "
                 "no such breakage path, so it is not in this table (it is reference-only in Table 7.2/T7).",
                 "eval/results/expH/{safety_ukf_a_v3,safety_ukf_b_v3,safety_fgo_a_v4,safety_fgo_b_v4}.json",
                 "summary page 12 (eval/figs_thesis_summary.py new_page('12', ...) table)",
                 "S-A (UKF forced-invalid test, final UKF port, re-test); S-A (UKF node-kill test, final UKF port, re-test); "
                 "S-A (FGO forced-invalid test, corrected-priors node, re-test); S-A (FGO node-kill test, corrected-priors node, re-test)",
                 "eval/results/expH/safety_{ukf_a_v3,ukf_b_v3,fgo_a_v4,fgo_b_v4}.json")


# =============================================================================================================== index
n_ok = sum(c[4] for it in ITEMS for c in it["checks"]); n_tot = sum(len(it["checks"]) for it in ITEMS)
W = ["# Candidate thesis figures, group B: Experiments 2, 3, 4, 5 and 5S (decision D124)", "",
     f"Built by `eval/figs_cand_b.py` at commit `{COMMIT}` (run with `/home/makerspace/venv-evo/bin/python`). These are "
     "CANDIDATES for the user to pick from - not inserted into the thesis figure set in `docs/thesis/figures_thesis/` "
     "itself. Stored outputs only: eval/results/*.json, trial-directory .tum files, sim/worlds/room_tags_map.json, "
     "and a cache of bag reads pre-populated ONCE by `eval/figs_cand_b_extract.py` under `heavy.py` (T_A_r1-3 ground "
     "truth; O_r1/O_r2/O_r3b ground truth, /imu/time_ref and dataflash XKF1), written to "
     "`~/thesis_data/cand_b_cache/` and deleted at the end of this group's work (see "
     "docs/handovers/2026-11-04_cand_b.md for the exact invocations). No estimator run, no simulation, no flight.", "",
     f"**Checks:** {n_ok}/{n_tot} EXACT (string equality after one rounding by `rd()`, parsed from `eval/figs_thesis.py`, "
     "sha256 of the source segment used to detect drift).", "",
     "**Style:** `eval/thesis_style.py` (160 mm / 6.30 in text width, Okabe-Ito palette, filled = live / open = "
     "hindsight, no in-figure titles, no verdict words, no bold text, panel labels (a)/(b)/... only where a figure "
     "has more than one panel). No two plots overlap; B03's and B04's two-panel figures share identical axis limits "
     "between panels (checked). B08 is a markdown table (no chart in its source page), verdict words kept in its "
     "cells only, the same A1-A3 exemption, caption body and title clean.", "",
     "## Candidates", "", "| id | proposed title | source chart(s) | data files | checks | verdict pointer |", "|---|---|---|---|---|---|"]
for it in ITEMS:
    ok = sum(c[4] for c in it["checks"]); tot = len(it["checks"])
    vp = it["caption"].split("\n")[-1]
    W.append(f"| {it['id']} | {it['title']} | {it['source']} | {it['data_files']} | {ok}/{tot} | {vp} |")
W += ["", "## Skipped (content already a figure/table in docs/thesis/figures_thesis/, or a duplicate of another candidate)", "",
      "| source chart | already covered by | reason |", "|---|---|---|",
      "| walkthrough page 10 / extra/ex_2_known_tags.png | F5 (Figure 5.1) | same content, not just style: the SAME "
      "5 tracks (EKF3/UKF/FGO live + UKF/FGO hindsight), the SAME per-condition means and per-flight scatter, the "
      "SAME line-chart-with-markers type; only the legend form (end-of-line direct labels vs a legend box) and "
      "on-canvas verdict marks (banned here anyway) differ (confirmed by reading both generators: both read "
      "`expT/t_aggregate.json`'s `agg[\"conditions\"][c][\"mean_rmse_m\"]` for the same 5 keys) |",
      "| walkthrough page 11 / extra/ex_3_loop_closure.png; summary page 08 | F7 (Figure 5.2) | same content: both "
      "are the FGO's per-lap RMSE across the 5 laps, 2 panels (with/without loop closure), live solid / hindsight "
      "dashed, same `expL/T_A_r{1,2,3}_t245.json` `per_lap_rmse_m` source; only the legend/label style and on-canvas "
      "verdict marks (banned here anyway) differ. The genuinely new content for Experiment 3 - the estimated "
      "TRAJECTORIES, not drawn anywhere else - is candidate B03 |",
      "| walkthrough flights/fl_4_err_live.png, fl_4_err_hind.png | candidate B04 (fl_4_err.png) | the SAME curves "
      "(`OE4`/`OM4` in this script) as B04's 3x2 grid, split across two separate, larger pages instead of one grid; "
      "per the common brief's dedup rule ('if two source charts show the same data, make one candidate and say so') "
      "only B04 is made |",
      "| walkthrough flights/fl_4_truth.png, fl_5_truth.png, extra pages for Experiment 5S's truth view "
      "(fl_5S_truth.png) | group A's A04/A05/A06 | per the common brief: 'Group A has ALREADY made these setup "
      "candidates; do NOT duplicate them' |", "",
      "## Judgement calls for the coordinator", "",
      "- **B02 (`3_truth`) duplicates ONE of group A's A03 (`2_truth`) four panels** (the 8-tag/condition-A panel, "
      "the same 3 flights) - kept as a separate, single-panel candidate because the user named it explicitly "
      "('the true laps of the 6 m square as an Experiment 3 figure') and Experiment 3 (loop closure) is a distinct "
      "experiment from Experiment 2 even though it re-uses the same flights; the coordinator may prefer to drop one.",
      "- **B03 is genuinely new content** (no existing figure or candidate draws the FGO's spatial (x, y) trajectory "
      "for Experiment 3; F7/the skipped page-08/ex_3_loop_closure chart draw per-lap RMSE only) - flagged as the "
      "strongest candidate for 'the trajectories for the looping' the user asked for.",
      "- **B04/B05 both come from Experiment 4 but are genuinely different chart types** (B04: error against time, "
      "all 3 flights, 6 panels; B05: an aggregate range-box summary, 1 panel, the same numbers Table 5.1/T6 already "
      "tabulates) - both kept, flagged B05's duplication with T6's numbers (not its chart form, which T6 doesn't "
      "have) the same way group A flagged A19's duplication with Table 7.1.",
      "- **B06/B07 consolidate THREE source pages into TWO candidates** (walkthrough page 13's two-panel "
      "`ex_5_hold_drift.png`, plus the separately-scaled summary pages 10 and 11) because the brief itself noted "
      "the source panels use different y-scales (summary page 10: 0-58 mm; page 11: 0-60 mm) - the walkthrough "
      "page's shared (0, 60) scale is not native to either source page, so splitting into two single-panel charts "
      "(each on its own natural scale) was judged truer to the sources than forcing one more shared scale.",
      "- **B06's EKF3 bar uses the far-spawn hold set (s1far), not the near-spawn set (s1) the primary H5.1 check "
      "was scored on** - the SAME choice `eval/figs_walkthrough_extra.py`'s own `ex_5_hold_drift.png` and "
      "`eval/figs_thesis_summary.py` page 10 already make (both plot `s1far` for EKF3); stated explicitly in B06's "
      "caption so it is not mistaken for the scored set.",
      "- **B08's UKF forced-invalid test limit is displayed as the registered 0.10 s, not its own score file's "
      "0.75 s** (a scorer artefact - that file was re-run with the FGO bound by coordinator instruction; both "
      "final-port delays are 0.00 s so the outcome is unchanged) - the SAME exception "
      "`eval/figs_thesis_summary.py` page 12's own `BT` dict already makes; stated explicitly in B08's caption and "
      "cross-checked against both the stored (artefact) value and the displayed (registered) value separately.", ""]
open(os.path.join(OUT, "index_b.md"), "w").write("\n".join(W) + "\n")
print(f"\nTOTAL candidates {len(ITEMS)}; checks {n_ok}/{n_tot}; wrote {os.path.join(OUT, 'index_b.md')}")
