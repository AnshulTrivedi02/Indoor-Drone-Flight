#!/usr/bin/env python3
"""CANDIDATE THESIS FIGURES, GROUP E: estimated PATHS over the true path for the thesis extension experiments
(E2 fewer tags, E3 wrong tag IDs, the E4 window sweep, E5 UKF-with-landmarks) and for Experiment 4 (outdoor-indoor
GNSS dropout) and Experiment 5 (tag hold), none of which has a spatial-path candidate yet (B03 already made one,
for Experiment 3's own loop closure; this group is everything else named in the user's extension-paths request).

These are CANDIDATES for the user to pick from - not inserted into the thesis figure set in docs/thesis/figures_thesis/
itself, and not folded into the combined candidates PDF, the thesis_assets bundle or the writing pack.

STORED OUTPUTS ONLY. Every bag and dataflash read needed (ground truth of T_B_r1/T_C_r1/T_D_r1/T_A_r1, O_r1 and the
three Experiment-5 flying-estimator trials; O_r1's and the three H_* trials' /imu/time_ref; O_r1's and H_s1far_r1's
XKF1; H_s2v2_r1's XUKO; H_s3v2_r1's XFGO) was pre-extracted ONCE by eval/figs_cand_e_extract.py under heavy.py into
~/thesis_data/cand_e_cache/*.npz, deleted at the end of this group's work. This generator itself never opens a bag
or a dataflash file. No estimator is run, no replay, no simulation, no flight. gnss.npz (O_r1's EKF3-origin offset)
and eval/results/*.json are read directly - neither is a bag or a dataflash file.

Architecture copied from eval/figs_cand_b.py (ast-parsed rd()/rd_si()/rng_si()/si_str()/rng() from eval/figs_thesis.py,
same check()/cite()/write_caption()/save()/verdict_line() machinery, thesis_style.py for the palette/fonts/width).
B03's track-loading code (tag-0 frame, true tags overlay, equal-scale panels) is reused for every tag-0-frame item
below (E01, E02, E04); B04's track-loading code (clock map, EKF3 dataflash + EKF3-origin offset, world frame) is
reused for E05.

Usage: /home/makerspace/venv-evo/bin/python eval/figs_cand_e.py"""
import ast, json, math, os, re, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from thesis_style import TEXT_WIDTH_IN, C, MK, TRUTH, INK, INK2, GRID, SURF, WALL, EST, RCPARAMS
plt.rcParams.update(RCPARAMS)

RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
T1 = os.path.expanduser("~/thesis_data/tier1")
CACHE = os.path.expanduser("~/thesis_data/cand_e_cache")
OUT = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "candidates"); os.makedirs(OUT, exist_ok=True)
CAPD = os.path.join(OUT, "captions"); os.makedirs(CAPD, exist_ok=True)
SC1 = os.path.join(ROOT, "docs", "thesis", "tier1", "scores")
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
L = lambda f: json.load(open(os.path.join(RES, f)))
L1 = lambda f: json.load(open(os.path.join(SC1, f)))

# ---------------------------------------------------------------------------------------------- rd()/rd_si()/rng_si()/si_str()/rng(),
# ast-parsed (not executed as a script) from eval/figs_thesis.py, exactly as eval/figs_cand_b.py does.
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


def cached(key):
    """Cache of values READ from stored flight records (npz in cand_e_cache, pre-populated by figs_cand_e_extract.py
    under heavy.py). Never computes; a cache miss here means the extractor needs re-running, not a bag re-open."""
    p = os.path.join(CACHE, key + ".npz")
    if not os.path.exists(p):
        raise RuntimeError(f"cache miss: {p} - run eval/figs_cand_e_extract.py under heavy.py first")
    z = np.load(p, allow_pickle=True); return {k: z[k] for k in z.files}


# ---------------------------------------------------------------------------------------------- caption-verdict self-check
# (D113 banned-word regex, COPIED from eval/caption_verdict_check.py / eval/figs_cand_b.py, since the coordinator's
# checker does not yet scan candidates/ - the common-brief caption rule is still enforced here, as the real gate.)
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
ITEMS = []; CHK = []


def check(label, computed, expected, src):
    c, e = str(computed), str(expected)
    if any(x[:3] == (label, c, e) for x in CHK):
        return
    CHK.append((label, c, e, src, c == e))


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


def measured_stretch(fig, ax):
    fig.canvas.draw()
    bb = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted()); x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    return (bb.height / (y1 - y0)) / (bb.width / (x1 - x0))


# ---------------------------------------------------------------------------------------------- shared setup
TMAP = json.load(open(os.path.join(ROOT, "sim", "worlds", "room_tags_map.json")))["tags"]
_t0 = next(t for t in TMAP if t["id"] == 0)
check("tag 0 yaw (deg), the frame-mapping assumption shared by E01/E02/E04", _t0["yaw_deg"], 0.0,
      "sim/worlds/room_tags_map.json tags[id=0].yaw_deg")


def gt_tag0(tr):
    """Ground truth of trial tr, cached (world frame), shifted into tag 0's frame (pure translation)."""
    G = cached(f"room_{tr}")["G"]
    return G[:, 0], G[:, 1] - _t0["x"], G[:, 2] - _t0["y"]


def clock_map(TR):
    sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        w = (sitl >= lo) & (sitl < lo + 5)
        if w.sum() > 50:
            i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
    env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
    return lambda x: x + (kk * x + c0)


def tag_legend_handle():
    return Line2D([], [], color=TRUTH, ls="", marker="D", ms=5.5, label="true tag")


# =============================================================================================================== E01
# ============================================================= E2 (fewer tags): FGO loop-closure paths by tag count
# Reuses eval/figs_cand_b.py's B03 track-loading pattern (tag 0's frame, true tags overlay). Live tracks only (the
# primary H-E2.1 criterion is scored on the live track); representative flight r1 of each condition B/C/D (4/2/1
# tags) - condition A (8 tags) already has its own live+hindsight candidate, B03. Appendix flights (r2/r3) are
# NOT made here (time-boxed); the per-flight numbers for all 9 runs are already tabulated in e2_results.md.
COND_TAGS = {"B": [0, 1, 2, 3], "C": [0, 2], "D": [0]}
fig, axs = plt.subplots(1, 3, figsize=(TEXT_WIDTH_IN, 3.4), sharex=True, sharey=True)
XY1 = {}
for ax, c in zip(axs, "BCD"):
    tr = f"T_{c}_r1"; ids = COND_TAGS[c]; idstr = "-".join(str(i) for i in ids)
    Gt, Gx, Gy = gt_tag0(tr)
    S = L1(f"E2_{tr}.json"); b0, b1 = S["lap_bounds_s"][0], S["lap_bounds_s"][-1]
    for mode, ls in (("lc", "-"), ("nolc", (0, (1, 1)))):
        x = np.loadtxt(f"{T1}/{tr}/lc_fgo_{mode}_t245_tags{idstr}/live.tum", ndmin=2)
        e = np.hypot(x[:, 1] - np.interp(x[:, 0], Gt, Gx), x[:, 2] - np.interp(x[:, 0], Gt, Gy))
        w = (x[:, 0] >= b0) & (x[:, 0] <= b1)
        rmse = float(np.sqrt(np.mean(e[w] ** 2)))
        check(f"E01 {tr} {mode} live: PLOTTED-window RMSE vs stored E2 rmse_m (6 dp)", rd(rmse, 6),
              rd(S["tracks"][f"{mode} live"]["rmse_m"], 6), f"docs/thesis/tier1/scores/E2_{tr}.json tracks.'{mode} live'.rmse_m")
        d0 = float(math.hypot(x[0, 1] - np.interp(x[0, 0], Gt, Gx), x[0, 2] - np.interp(x[0, 0], Gt, Gy)))
        check(f"E01 {tr} {mode} live: start point within 0.5 m of ground truth (measured {rd(d0, 3)} m)", str(d0 <= 0.5), "True",
              f"this script ({tr} live.tum row 0 vs ground truth)")
        XY1[(c, mode)] = x
    check(f"E01 {tr}: 2 live tracks plotted (lc, nolc)", str(len(XY1[(c, 'lc')]) > 0 and len(XY1[(c, 'nolc')]) > 0), "True",
          f"this script ({tr} track row counts)")
    wg = (Gt >= min(XY1[(c, "lc")][0, 0], XY1[(c, "nolc")][0, 0])) & (Gt <= max(XY1[(c, "lc")][-1, 0], XY1[(c, "nolc")][-1, 0]))
    ax.plot(Gx[wg], Gy[wg], color=TRUTH, lw=1.0, zorder=2)
    for t_ in TMAP:
        if t_["id"] in ids:
            ax.plot(t_["x"] - _t0["x"], t_["y"] - _t0["y"], marker="D", ms=6, color=TRUTH, zorder=4)
    ax.plot(XY1[(c, "lc")][:, 1], XY1[(c, "lc")][:, 2], color=C["FGO"], lw=0.9, ls="-", alpha=0.9, zorder=3)
    ax.plot(XY1[(c, "nolc")][:, 1], XY1[(c, "nolc")][:, 2], color=C["FGO"], lw=0.9, ls=(0, (1, 1)), alpha=0.9, zorder=3)
    ax.set_title(f"({'abc'['BCD'.index(c)]}) {len(ids)} tag{'s' if len(ids) != 1 else ''}", loc="left", fontsize=9.5)
    ax.set_aspect(1.0, adjustable="box")
    ax.set_xlabel("East from tag 0 (m)")
axs[0].set_ylabel("North from tag 0 (m)")
axs[0].set_xlim(-2.0, 8.0); axs[0].set_ylim(-2.0, 8.0)
st = measured_stretch(fig, axs[0]); check("E01 equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
check("E01 all three panels share identical axis limits", str(axs[0].get_xlim() == axs[1].get_xlim() == axs[2].get_xlim() and
      axs[0].get_ylim() == axs[1].get_ylim() == axs[2].get_ylim()), "True", "this script (shared axis limits)")
fig.legend(handles=[Line2D([], [], color=TRUTH, lw=1.0, label="true path"), tag_legend_handle(),
                     Line2D([], [], color=C["FGO"], ls="-", lw=1.2, label="FGO live, with loop closure"),
                     Line2D([], [], color=C["FGO"], ls=(0, (1, 1)), lw=1.2, label="FGO live, without loop closure")],
           loc="lower center", ncol=2, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(bottom=0.32, wspace=0.08)
save(fig, "E01", "E01_e2_fewer_tags_paths",
     "Extension E2 (loop closure with fewer tags): the FGO's live path, with and without loop closure, by tag count",
     "Extension E2 (fewer known tags), one flight per condition: the FGO's live path in orange, solid with loop "
     "closure and dotted without it, against the true path in grey and that condition's true tags as grey "
     "diamonds, raw, in tag 0's frame, equal scale. (a) 4 tags, (b) 2 tags, (c) 1 tag, the known-map case where "
     "the only tag is tag 0 itself. With loop closure the live path stays close to the square on every lap; "
     "without it, the path drifts further away each lap, most visibly in (c).",
     "docs/thesis/tier1/scores/E2_T_{B,C,D}_r1.json (lap_bounds_s, tracks.'{lc,nolc} live'.rmse_m, per_lap_rmse_m); "
     "~/thesis_data/tier1/T_{B,C,D}_r1/lc_fgo_{lc,nolc}_t245_tags<ids>/live.tum; sim/worlds/room_tags_map.json; "
     "bag /ground_truth/pose of T_B_r1, T_C_r1, T_D_r1",
     "NEW (not drawn by any existing figure or candidate; B03 draws the equivalent for condition A, 8 tags)", None,
     "docs/thesis/tier1/scores/E2_T_{B,C,D}_r1.json; ~/thesis_data/tier1/T_{B,C,D}_r1/lc_fgo_*/live.tum")


# =============================================================================================================== E02
# ======================================================= E3 (wrong tag IDs): live paths, clean reference + collapse
# Genuinely different content from the already-made candidates C05/C06 (Extension E3 tag-map candidates): C05/C06
# plot the HINDSIGHT track plus the final landmark map, for non-diverged runs only. This candidate plots the LIVE
# track, including a DIVERGED run's excursion (masked to a sane time/space window after the onset, per its own
# stored divergence onset) - the live-divergence story C05/C06 do not show. Flight T_A_r1 only (time-boxed).
_Gt3, _Gx3, _Gy3 = gt_tag0("T_A_r1")
S_clean = L(os.path.join("expL", "T_A_r1_t245.json")); b0c, b1c = S_clean["lap_bounds_s"][0], S_clean["lap_bounds_s"][-1]
x_clean = np.loadtxt(f"{TD}/T_A_r1/lc_fgo_lc_t245/live.tum", ndmin=2)
e_clean = np.hypot(x_clean[:, 1] - np.interp(x_clean[:, 0], _Gt3, _Gx3), x_clean[:, 2] - np.interp(x_clean[:, 0], _Gt3, _Gy3))
wc = (x_clean[:, 0] >= b0c) & (x_clean[:, 0] <= b1c)
check("E02 clean T_A_r1 lc live: PLOTTED-window RMSE vs stored expL rmse_m (6 dp)", rd(float(np.sqrt(np.mean(e_clean[wc] ** 2))), 6),
      rd(S_clean["tracks"]["lc live"]["rmse_m"], 6), "eval/results/expL/T_A_r1_t245.json tracks.'lc live'.rmse_m")
_d0_clean = float(math.hypot(x_clean[0, 1] - np.interp(x_clean[0, 0], _Gt3, _Gx3), x_clean[0, 2] - np.interp(x_clean[0, 0], _Gt3, _Gy3)))
check(f"E02 clean T_A_r1 lc live: start point within 0.5 m of ground truth (measured {rd(_d0_clean, 3)} m)", str(_d0_clean <= 0.5),
      "True", "this script (T_A_r1 clean live.tum row 0 vs ground truth)")

S_s0 = L1("E3a_T_A_r1_0.01_s0.json"); b0s, b1s = S_s0["lap_bounds_s"][0], S_s0["lap_bounds_s"][-1]
x_s0 = np.loadtxt(f"{T1}/T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s0/live.tum", ndmin=2)
e_s0 = np.hypot(x_s0[:, 1] - np.interp(x_s0[:, 0], _Gt3, _Gx3), x_s0[:, 2] - np.interp(x_s0[:, 0], _Gt3, _Gy3))
ws0 = (x_s0[:, 0] >= b0s) & (x_s0[:, 0] <= b1s)
check("E02 collapse (1% s0) T_A_r1 lc live: PLOTTED-window RMSE vs stored E3a rmse_m (6 dp)", rd(float(np.sqrt(np.mean(e_s0[ws0] ** 2))), 6),
      rd(S_s0["tracks"]["lc live"]["rmse_m"], 6), "docs/thesis/tier1/scores/E3a_T_A_r1_0.01_s0.json tracks.'lc live'.rmse_m")
_d0_s0 = float(math.hypot(x_s0[0, 1] - np.interp(x_s0[0, 0], _Gt3, _Gx3), x_s0[0, 2] - np.interp(x_s0[0, 0], _Gt3, _Gy3)))
check(f"E02 collapse (1% s0) T_A_r1 lc live: start point within 0.5 m of ground truth (measured {rd(_d0_s0, 3)} m)", str(_d0_s0 <= 0.5),
      "True", "this script (T_A_r1 collapse s0 live.tum row 0 vs ground truth)")

V3 = json.load(open(os.path.join(SC1, "E3_verdicts.json")))
rs1 = V3["runs"]["E3a_T_A_r1_0.01_s1"]["run_status"]
onset = rs1["live divergence onset t_s (headline; |x| or |y| > 10 m or non-finite)"]
check("E02 diverged (1% s1) T_A_r1: stored live-divergence onset (s)", rd(onset, 3), "49.699",
      "docs/thesis/tier1/scores/E3_verdicts.json runs.'E3a_T_A_r1_0.01_s1'.run_status")
x_s1 = np.loadtxt(f"{T1}/T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s1/live.tum", ndmin=2)
nf_s1 = rs1["nonfinite"]["live.tum"]
check("E02 diverged (1% s1) T_A_r1: loaded live.tum row count vs stored run_status row count", str(len(x_s1)), str(nf_s1["rows"]),
      "docs/thesis/tier1/scores/E3_verdicts.json runs.'E3a_T_A_r1_0.01_s1'.run_status.nonfinite.'live.tum'.rows")
check("E02 diverged (1% s1) T_A_r1: loaded live.tum non-finite count vs stored run_status (0, the excursion is large but finite)",
      str(int((~np.isfinite(x_s1[:, 1:3])).any(axis=1).sum())), str(nf_s1["rows_nonfinite"]),
      "docs/thesis/tier1/scores/E3_verdicts.json runs.'E3a_T_A_r1_0.01_s1'.run_status.nonfinite.'live.tum'.rows_nonfinite")
_d0_s1 = float(math.hypot(x_s1[0, 1] - np.interp(x_s1[0, 0], _Gt3, _Gx3), x_s1[0, 2] - np.interp(x_s1[0, 0], _Gt3, _Gy3)))
check(f"E02 diverged (1% s1) T_A_r1: start point within 0.5 m of ground truth (measured {rd(_d0_s1, 3)} m)", str(_d0_s1 <= 0.5),
      "True", "this script (T_A_r1 diverged s1 live.tum row 0 vs ground truth, before the onset)")
mask_s1 = np.isfinite(x_s1[:, 1]) & np.isfinite(x_s1[:, 2]) & (x_s1[:, 0] <= onset + 3.0) & (np.abs(x_s1[:, 1]) < 50) & (np.abs(x_s1[:, 2]) < 50)

fig, axs = plt.subplots(1, 3, figsize=(TEXT_WIDTH_IN, 3.4), sharex=True, sharey=True)
for ax, (xx, mm, lab, cap) in zip(axs, (
        (x_clean, np.ones(len(x_clean), bool), "(a) no wrong IDs", "no wrong IDs (clean reference)"),
        (x_s0, np.ones(len(x_s0), bool), "(b) 1% wrong IDs", "1% wrong IDs, seed 0 (non-diverged)"),
        (x_s1, mask_s1, "(c) 1% wrong IDs", "1% wrong IDs, seed 1 (diverged)"))):
    wg = (_Gt3 >= xx[mm, 0].min()) & (_Gt3 <= min(xx[mm, 0].max(), _Gt3.max()))
    ax.plot(_Gx3[wg], _Gy3[wg], color=TRUTH, lw=1.0, zorder=2)
    for t_ in TMAP:
        ax.plot(t_["x"] - _t0["x"], t_["y"] - _t0["y"], marker="D", ms=6, color=TRUTH, zorder=4)
    ax.plot(xx[mm, 1], xx[mm, 2], color=C["FGO"], lw=0.9, ls="-", alpha=0.9, zorder=3)
    ax.set_title(lab, loc="left", fontsize=9.0)
    ax.set_aspect(1.0, adjustable="box")
    ax.set_xlabel("East from tag 0 (m)")
axs[0].set_ylabel("North from tag 0 (m)")
axs[0].set_xlim(-2.0, 10.0); axs[0].set_ylim(-2.0, 10.0)
st = measured_stretch(fig, axs[0]); check("E02 equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
fig.legend(handles=[Line2D([], [], color=TRUTH, lw=1.0, label="true path"), tag_legend_handle(),
                     Line2D([], [], color=C["FGO"], ls="-", lw=1.2, label="FGO live")],
           loc="lower center", ncol=3, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(bottom=0.30, wspace=0.08)
save(fig, "E02", "E02_e3_wrong_ids_paths", "Extension E3 (wrong tag IDs): the FGO's live path, clean reference and two 1% runs",
     "Extension E3 (wrong tag IDs), one flight, the FGO's live path in orange against the true path in grey and "
     "the 8 true tags as grey diamonds, raw, in tag 0's frame, equal scale. (a) no wrong IDs: the live path stays "
     "on the square. (b) 1% wrong IDs, one seed: the live path does not diverge, but is pulled inward, off the "
     "square. (c) 1% wrong IDs, a different seed: the solver diverges; the path is drawn only up to shortly after "
     "the divergence, after which the live estimate leaves the room and is not shown.",
     "eval/results/expL/T_A_r1_t245.json (tracks.'lc live'.rmse_m); docs/thesis/tier1/scores/E3a_T_A_r1_0.01_{s0,s1}.json, "
     "E3_verdicts.json (run_status); ~/thesis_data/trials/T_A_r1/lc_fgo_lc_t245/live.tum; "
     "~/thesis_data/tier1/T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_{s0,s1}/live.tum; "
     "sim/worlds/room_tags_map.json; bag /ground_truth/pose of T_A_r1",
     "NEW (not drawn by any existing figure or candidate; C05/C06 draw the hindsight track + final landmark map "
     "for non-diverged runs only)", None,
     "docs/thesis/tier1/scores/E3a_T_A_r1_0.01_{s0,s1}.json, E3_verdicts.json; eval/results/expL/T_A_r1_t245.json")


# =============================================================================================================== E03
# ============================================================= UKF with landmark states (Extension E5) vs FGO paths
S_fgo5 = L(os.path.join("expL", "T_A_r1_t245.json")); S_ukf5 = L1("e5_T_A_r1.json")
check("E03 FGO and UKF score the same lap_bounds_s (T_A_r1)", str(S_fgo5["lap_bounds_s"] == S_ukf5["lap_bounds_s"]), "True",
      "eval/results/expL/T_A_r1_t245.json; docs/thesis/tier1/scores/e5_T_A_r1.json")
b0e, b1e = S_fgo5["lap_bounds_s"][0], S_fgo5["lap_bounds_s"][-1]
TR5 = {}
for mode in ("lc", "nolc"):
    for kind, fgo_f, ukf_f in (("live", "live.tum", "live.tum"), ("hindsight", "hindsight.tum", "hindsight.tum")):
        xf = np.loadtxt(f"{TD}/T_A_r1/lc_fgo_{mode}_t245/{fgo_f}", ndmin=2)
        ef = np.hypot(xf[:, 1] - np.interp(xf[:, 0], _Gt3, _Gx3), xf[:, 2] - np.interp(xf[:, 0], _Gt3, _Gy3))
        wf = (xf[:, 0] >= b0e) & (xf[:, 0] <= b1e)
        check(f"E03 FGO {mode} {kind}: PLOTTED-window RMSE vs stored expL rmse_m (6 dp)", rd(float(np.sqrt(np.mean(ef[wf] ** 2))), 6),
              rd(S_fgo5["tracks"][f"{mode} {kind}"]["rmse_m"], 6), f"eval/results/expL/T_A_r1_t245.json tracks.'{mode} {kind}'.rmse_m")
        xu = np.loadtxt(f"{T1}/T_A_r1/lc_ukf_{mode}_t245/{ukf_f}", ndmin=2)
        eu = np.hypot(xu[:, 1] - np.interp(xu[:, 0], _Gt3, _Gx3), xu[:, 2] - np.interp(xu[:, 0], _Gt3, _Gy3))
        wu = (xu[:, 0] >= b0e) & (xu[:, 0] <= b1e)
        check(f"E03 UKF {mode} {kind}: PLOTTED-window RMSE vs stored e5 rmse_m (6 dp)", rd(float(np.sqrt(np.mean(eu[wu] ** 2))), 6),
              rd(S_ukf5["tracks"][f"{mode} {kind}"]["rmse_m"], 6), f"docs/thesis/tier1/scores/e5_T_A_r1.json tracks.'{mode} {kind}'.rmse_m")
        if kind == "live":
            d0f = float(math.hypot(xf[0, 1] - np.interp(xf[0, 0], _Gt3, _Gx3), xf[0, 2] - np.interp(xf[0, 0], _Gt3, _Gy3)))
            d0u = float(math.hypot(xu[0, 1] - np.interp(xu[0, 0], _Gt3, _Gx3), xu[0, 2] - np.interp(xu[0, 0], _Gt3, _Gy3)))
            check(f"E03 FGO {mode} live: start point within 0.5 m of ground truth (measured {rd(d0f, 3)} m)", str(d0f <= 0.5), "True", "this script")
            check(f"E03 UKF {mode} live: start point within 0.5 m of ground truth (measured {rd(d0u, 3)} m)", str(d0u <= 0.5), "True", "this script")
        TR5[(mode, kind, "FGO")] = xf; TR5[(mode, kind, "UKF")] = xu
check("E03 4 tracks plotted per panel (UKF/FGO x live/hindsight)",
      str(all(len(TR5[(m, k, e)]) > 0 for m in ("lc", "nolc") for k in ("live", "hindsight") for e in ("UKF", "FGO"))), "True", "this script")

fig, axs = plt.subplots(1, 2, figsize=(TEXT_WIDTH_IN, 4.9), sharex=True, sharey=True)
for ax, mode, lab in ((axs[0], "lc", "(a) with loop closure"), (axs[1], "nolc", "(b) without loop closure")):
    xlo = min(TR5[(mode, "live", "FGO")][0, 0], TR5[(mode, "live", "UKF")][0, 0])
    xhi = max(TR5[(mode, "live", "FGO")][-1, 0], TR5[(mode, "live", "UKF")][-1, 0])
    wg = (_Gt3 >= xlo) & (_Gt3 <= xhi)
    ax.plot(_Gx3[wg], _Gy3[wg], color=TRUTH, lw=1.0, zorder=1)
    for t_ in TMAP:
        ax.plot(t_["x"] - _t0["x"], t_["y"] - _t0["y"], marker="D", ms=6, color=TRUTH, zorder=5)
    for e, kind, ls, zo in (("UKF", "live", "-", 3), ("UKF", "hindsight", (0, (4, 2)), 2),
                             ("FGO", "live", "-", 4), ("FGO", "hindsight", (0, (4, 2)), 2)):
        xx = TR5[(mode, kind, e)]
        ax.plot(xx[:, 1], xx[:, 2], color=C[e], lw=0.9, ls=ls, alpha=0.9, zorder=zo)
    ax.set_title(lab, loc="left", fontsize=9.5)
    ax.set_aspect(1.0, adjustable="box")
    ax.set_xlabel("East from tag 0 (m)")
axs[0].set_ylabel("North from tag 0 (m)")
_xmax = max(TR5[(m, k, e)][:, 1].max() for m in ("lc", "nolc") for k in ("live", "hindsight") for e in ("UKF", "FGO"))
_ymax = max(TR5[(m, k, e)][:, 2].max() for m in ("lc", "nolc") for k in ("live", "hindsight") for e in ("UKF", "FGO"))
_xmin = min(TR5[(m, k, e)][:, 1].min() for m in ("lc", "nolc") for k in ("live", "hindsight") for e in ("UKF", "FGO"))
_ymin = min(TR5[(m, k, e)][:, 2].min() for m in ("lc", "nolc") for k in ("live", "hindsight") for e in ("UKF", "FGO"))
LIM4 = (math.floor(min(_xmin, _ymin) - 0.5), math.ceil(max(_xmax, _ymax) + 0.5))
axs[0].set_xlim(*LIM4); axs[0].set_ylim(*LIM4)
check("E03 axis limits contain every plotted track (no clipping)",
      str(_xmin >= LIM4[0] and _xmax <= LIM4[1] and _ymin >= LIM4[0] and _ymax <= LIM4[1]), "True", "this script (data bounds vs set_xlim/set_ylim)")
st = measured_stretch(fig, axs[0]); check("E03 equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
fig.legend(handles=[Line2D([], [], color=TRUTH, lw=1.0, label="true path"), tag_legend_handle(),
                     Line2D([], [], color=C["UKF"], ls="-", lw=1.2, label="UKF live"),
                     Line2D([], [], color=C["UKF"], ls=(0, (4, 2)), lw=1.2, label="UKF RTS (hindsight)"),
                     Line2D([], [], color=C["FGO"], ls="-", lw=1.2, label="FGO live"),
                     Line2D([], [], color=C["FGO"], ls=(0, (4, 2)), lw=1.2, label="FGO hindsight")],
           loc="lower center", ncol=3, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(bottom=0.24, wspace=0.08)
save(fig, "E03", "E03_e5_ukf_vs_fgo_paths", "Extension E5 (UKF with tag landmark states): UKF and FGO paths, with and without loop closure",
     "Extension E5, a UKF carrying its own tag-landmark states (teal) against the FGO (orange), one flight, raw, "
     "in tag 0's frame, equal scale. Live paths are solid and hindsight paths are dashed, against the true path "
     "in grey and the 8 true tags as grey diamonds. (a) with loop closure: both live paths stay near the square, "
     "the FGO's visibly closer to it than the UKF's. (b) without loop closure: both live paths drift away from "
     "the square lap on lap, the UKF's by more.",
     "eval/results/expL/T_A_r1_t245.json (lap_bounds_s, tracks.*.rmse_m); docs/thesis/tier1/scores/e5_T_A_r1.json "
     "(tracks.*.rmse_m); ~/thesis_data/trials/T_A_r1/lc_fgo_{lc,nolc}_t245/{live,hindsight}.tum; "
     "~/thesis_data/tier1/T_A_r1/lc_ukf_{lc,nolc}_t245/{live,hindsight}.tum; sim/worlds/room_tags_map.json; "
     "bag /ground_truth/pose of T_A_r1",
     "NEW (not drawn by any existing figure or candidate; B03 draws the FGO-only equivalent)", None,
     "docs/thesis/tier1/scores/e5_T_A_r1.json; eval/results/expL/T_A_r1_t245.json; "
     "~/thesis_data/tier1/T_A_r1/lc_ukf_{lc,nolc}_t245/*.tum; ~/thesis_data/trials/T_A_r1/lc_fgo_{lc,nolc}_t245/*.tum")


# =============================================================================================================== E04
# ============================================= Experiment 4 (outdoor-indoor): estimated paths, dropout/return marked
# Reuses eval/figs_cand_b.py's B04 track-loading code (clock map, EKF3 dataflash + EKF3-origin offset). One flight
# (O_r1) of 3, time-boxed; the other two flights' error-against-time curves are already candidate B04.
d_o = cached("room_O_r1"); G4, TR4 = d_o["G"], d_o["TR"]
o4 = L(os.path.join("expO", "O_r1.json"))
to_bag4 = clock_map(TR4)
k1_o = cached("xkf1_O_r1")["K1"]; t4 = to_bag4(k1_o[:, 0])
oE4, oN4 = np.load(f"{TD}/O_r1/gnss.npz")["ekf3_origin_EN"]
TRK4 = {"EKF3 live": np.c_[t4, k1_o[:, 2] + oE4, k1_o[:, 1] + oN4]}   # k1_o cols: t, PN, PE, yaw -> x=East=PE+oE, y=North=PN+oN
for n, p_ in (("UKF live", "room_ukf/ukf_live.tum"), ("FGO live", "room_fgo/fgo_live.tum")):
    TRK4[n] = np.loadtxt(f"{TD}/O_r1/{p_}", ndmin=2)[:, :3]
toff4, ton4 = o4["markers_bag_s"]["GNSS OFF"], o4["markers_bag_s"]["GNSS ON"]
for n, Tk in TRK4.items():
    e = np.hypot(Tk[:, 1] - np.interp(Tk[:, 0], G4[:, 0], G4[:, 1]), Tk[:, 2] - np.interp(Tk[:, 0], G4[:, 0], G4[:, 2]))
    wi = (Tk[:, 0] >= toff4) & (Tk[:, 0] <= ton4)
    rmse4 = float(np.sqrt(np.mean(e[wi] ** 2)))
    check(f"E04 O_r1 {n}: PLOTTED indoor-window RMSE vs stored indoor_rmse_m (6 dp)", rd(rmse4, 6), rd(o4["tracks"][n]["indoor_rmse_m"], 6),
          f"eval/results/expO/O_r1.json tracks.'{n}'.indoor_rmse_m")
    d0 = float(math.hypot(Tk[0, 1] - np.interp(Tk[0, 0], G4[:, 0], G4[:, 1]), Tk[0, 2] - np.interp(Tk[0, 0], G4[:, 0], G4[:, 2])))
    check(f"E04 O_r1 {n}: start point within 2.0 m of ground truth (outdoor, GPS-aided; measured {rd(d0, 3)} m)", str(d0 <= 2.0), "True",
          "this script (first plotted sample vs ground truth)")
check("E04 3 tracks plotted (EKF3, UKF, FGO)", str(len(TRK4) == 3), "True", "this script")

# This flight is almost due north-south (East range < 5 m against a North range of about 65 m). An honest
# equal-scale plot is therefore inherently tall and narrow if cropped tightly to the flight; instead the x-axis is
# widened (symmetrically, centred on the flight) to match the figure's own physical aspect ratio, so the equal-
# scale axes box fills the whole figure (no narrow box with a legend stranded in blank canvas beside it) and the
# legend sits in the resulting blank margin alongside the flight line, inside the axes.
FIGW4, FIGH4 = TEXT_WIDTH_IN, 8.2
ylo4, yhi4 = -18.0, 54.0
xmid4 = float(np.nanmean(G4[:, 1])); xr4 = (yhi4 - ylo4) * (FIGW4 / FIGH4)
xlo4, xhi4 = xmid4 - xr4 / 2, xmid4 + xr4 / 2
fig, ax = plt.subplots(figsize=(FIGW4, FIGH4))
wg4 = (G4[:, 0] >= min(t4.min(), TRK4["UKF live"][0, 0]) - 10) & (G4[:, 0] <= max(t4.max(), TRK4["UKF live"][-1, 0]) + 10)
ax.plot(G4[wg4, 1], G4[wg4, 2], color=TRUTH, lw=1.2, zorder=2, label="true path")
for e, ls in (("EKF3", "-"), ("UKF", "-"), ("FGO", "-")):
    Tk = TRK4[f"{e} live"]
    ax.plot(Tk[:, 1], Tk[:, 2], color=C[e], lw=0.9, ls=ls, alpha=0.9, zorder=3, label=f"{e} live")
for lbl, t_m, mk, col in (("GNSS OFF (dropout)", toff4, "v", INK), ("GNSS ON (return)", ton4, "^", INK)):
    gx, gy = np.interp(t_m, G4[:, 0], G4[:, 1]), np.interp(t_m, G4[:, 0], G4[:, 2])
    ax.plot(gx, gy, marker=mk, ms=9, color=col, mec=SURF, mew=1.0, zorder=6, ls="", label=lbl)
ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)")
ax.set_xlim(xlo4, xhi4); ax.set_ylim(ylo4, yhi4)
ax.set_aspect(1.0, adjustable="box")
_xmaxd4 = max(TRK4[f"{e} live"][:, 1].max() for e in EST); _xmind4 = min(TRK4[f"{e} live"][:, 1].min() for e in EST)
check("E04 widened x-axis still contains every plotted track (no clipping)", str(xlo4 <= _xmind4 and _xmaxd4 <= xhi4), "True",
      "this script (data bounds vs the widened set_xlim)")
st4 = measured_stretch(fig, ax); check("E04 equal scale (measured stretch)", rd(st4, 1), "1.0", "set_aspect(1.0)")
ax.legend(loc="center left", frameon=False, fontsize=9.0, bbox_to_anchor=(0.02, 0.32))
save(fig, "E04", "E04_exp4_outdoor_indoor_paths", "Experiment 4 (outdoor-indoor): each estimator's live path over the true path, dropout and return marked",
     "Experiment 4 (outdoor to indoor to outdoor, open loop on simulator truth), one flight: the live path of "
     "EKF3 (blue), UKF (teal) and FGO (orange) against the true path in grey, world frame, no alignment, equal "
     "scale. The downward triangle marks where GNSS was switched off at the building entrance; the upward "
     "triangle marks where it came back on, outdoors again - the drone goes by the same entrance on the way in "
     "and the way out, so the two markers sit almost on top of each other. EKF3's path visibly separates from "
     "the true path indoors and snaps back once GNSS returns; the UKF and FGO stay closer to the true path "
     "throughout.",
     "eval/results/expO/O_r1.json (markers_bag_s, tracks.*.indoor_rmse_m); ~/thesis_data/trials/O_r1/room_ukf/ukf_live.tum, "
     "room_fgo/fgo_live.tum, gnss.npz; dataflash ardupilot.bin (XKF1); bag /ground_truth/pose and /imu/time_ref of O_r1",
     "NEW spatial-path view (B04 draws the same data as error against time, not a path)", None,
     "eval/results/expO/O_r1.json; ~/thesis_data/trials/O_r1/room_ukf/ukf_live.tum, room_fgo/fgo_live.tum, gnss.npz")


# =============================================================================================================== E05
# =============================================== Experiment 5 (tag hold): estimated vs true hold position over time
# New dataflash path (not B06/B07, which are aggregate bars): EKF3's own navigation state IS the wall-tag frame W
# via ExtNav (XKF1 core 0); the flying UKF port's and FGO node's own live outputs (XUKO, XFGO OV==1) are also
# natively in W. Ground truth is read from each flight's own bag and shifted into W (translation only - the wall
# tag's yaw convention already matches the world axes, confirmed in eval/h_score.py, so no rotation is needed).
# One flight per estimator (time-boxed): EKF3 flying = H_s1far_r1 (the far-spawn set, matching candidate B06's
# choice for EKF3); UKF flying = H_s2v2_r1; FGO flying = H_s3rp_r2, the CORRECTED-priors FGO node (eval/figs_thesis.py's
# current set for the H5.x rows), NOT the original-priors set (s3v2) candidates B06/B07 still use. The first repeat
# of the corrected-priors set, H_s3rp_r1, has no stored bag (only ardupilot.bin), but H_s3rp_r2 and H_s3rp_r3 do, so
# this candidate uses s3rp_r2 rather than falling back to the superseded set - flagged in index_e.md.
TAG_W = (0.0, 4.998)   # eval/h_score.py: N_W = world y - 4.998, E_W = world x (translation only)


def gt_W(tr):
    G = cached(f"room_{tr}")["G"]
    return G[:, 0], G[:, 1], G[:, 2] - TAG_W[1]   # t, E_W (=world x), N_W


HOLD = {"EKF3": ("H_s1far_r1", "xkf1", "EKF3"), "UKF": ("H_s2v2_r1", "xuko", "UKF_port"), "FGO": ("H_s3rp_r2", "xfgo", "FGO_flying")}
HOLD_JSON = {"EKF3": "s1far_r1", "UKF": "s2v2_r1", "FGO": "s3rp_r2"}
fig, axs = plt.subplots(3, 1, figsize=(TEXT_WIDTH_IN, 6.2), sharex=False)
PAN5 = {}
for e in EST:
    tr, cachekey, jkey = HOLD[e]
    Gt, GE, GN = gt_W(tr)
    TRc = cached(f"room_{tr}")["TR"]; to_bag5 = clock_map(TRc)
    k1 = cached(f"{cachekey}_{tr}")["K1"]; t5 = to_bag5(k1[:, 0])   # cols: t_sitl, PN, PE, yaw
    XE, XN = k1[:, 2], k1[:, 1]   # East = PE, North = PN (already in W)
    hj = L(os.path.join("expH", f"{HOLD_JSON[e]}.json"))
    lo0 = hj["losses"][0]; ton, toff = lo0["t_on"], lo0["t_off"]
    i_off = int(np.argmin(np.abs(t5 - toff)))
    drift = float(math.hypot(XE[i_off] - np.interp(t5[i_off], Gt, GE), XN[i_off] - np.interp(t5[i_off], Gt, GN)))
    check(f"E05 {e} ({tr}): PLOTTED drift at first loss t_off vs stored losses[0].{jkey}.drift_end_m (6 dp)", rd(drift, 6),
          rd(lo0[jkey]["drift_end_m"], 6), f"eval/results/expH/{HOLD_JSON[e]}.json losses[0].'{jkey}'.drift_end_m")
    err5 = np.hypot(XE - np.interp(t5, Gt, GE), XN - np.interp(t5, Gt, GN))
    check(f"E05 {e} ({tr}): track sample count > 1000 (not an empty or truncated track)", str(len(t5) > 1000), "True",
          f"this script ({cachekey}_{tr}.npz)")
    # Plot from shortly before the first pre-loss hold window starts (hold_windows_vehicle[0].t0), not from takeoff:
    # the climb/approach segment before the drone first reaches the hold point has its own large transient error
    # that is unrelated to tag loss and would otherwise swamp the y-scale needed to see the loss-window effect.
    t_start5 = hj["hold_windows_vehicle"][0]["t0"] - 15.0
    w5 = (t5 >= t_start5) & (t5 <= Gt.max())
    # start-point agreement: the estimator's own first PLOTTED sample against ground truth at that instant.
    i0 = np.flatnonzero(w5)[0]
    d0 = float(math.hypot(XE[i0] - np.interp(t5[i0], Gt, GE), XN[i0] - np.interp(t5[i0], Gt, GN)))
    check(f"E05 {e} ({tr}): first plotted sample within 0.5 m of ground truth (measured {rd(d0, 3)} m)", str(d0 <= 0.5), "True",
          f"this script ({cachekey}_{tr}.npz vs room_{tr}.npz, t = {rd(float(t5[i0]), 1)} s)")
    PAN5[e] = (t5, w5, err5)
Y5MAX = max(60.0, max(float(np.nanmax(PAN5[e][2][PAN5[e][1]])) for e in EST) * 1e3 * 1.1)
for ax, e in zip(axs, EST):
    t5, w5, err5 = PAN5[e]
    tr, _, jkey = HOLD[e]
    hj = L(os.path.join("expH", f"{HOLD_JSON[e]}.json"))
    for lo in hj["losses"]:
        ax.axvspan(lo["t_on"], lo["t_off"], color="#ececec", zorder=0, lw=0)
    ax.plot(t5[w5], err5[w5] * 1e3, color=C[e], lw=0.9, zorder=3)
    # "estimate error", not "hold error" - the registered "hold error" (B06) is ground truth's distance from the
    # hold target; this is a different quantity, the estimator's own distance from ground truth.
    ax.set_ylabel(f"{e}\nestimate error (mm)")
    ax.set_xlim(t5[w5].min(), t5[w5].max())
    ax.set_ylim(0, Y5MAX)
axs[-1].set_xlabel("time (s, each flight's own clock)")
_yl5 = {ax.get_ylim() for ax in axs}
check("E05 all three panels share one y-scale", str(len(_yl5) == 1), "True", "this script (axis limits)")
# "occluder in place", not "tag hidden": eval/h_score.py notes the occluder's render lag means ON/OFF is not
# exactly the estimator's own detection-loss window (see losses[].effective in the stored json).
fig.legend(handles=[Line2D([], [], color="#ececec", lw=8, label="occluder in place over the wall tag")],
           loc="lower center", ncol=1, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(bottom=0.12, hspace=0.35)
save(fig, "E05", "E05_exp5_tag_hold_timeseries", "Experiment 5 (tag hold): each flying estimator's own distance from ground truth over time, occluder intervals shaded",
     "Experiment 5 (tag hold), one flight per flying estimator: EKF3 in blue, UKF in teal, FGO in orange, each on "
     "its own flight's clock, one shared y-scale across all three. The distance between each estimator's own live "
     "position estimate and the drone's true position, millimetres, against time; shaded bands mark when the "
     "occluder covered the wall tag. This is each estimator's own error against ground truth, not the registered "
     "hold error (ground truth's own distance from the hold target), because the lateral moves built into the "
     "hold profile are far larger than this millimetre-scale effect and would hide it if positions were plotted "
     "directly. The line moves away from its settled level during a shaded band and returns to it once the "
     "occluder is removed, though not always in the same direction. Each panel starts shortly before that "
     "flight's first steady hold period, leaving out the initial climb and approach to the hold point.",
     "eval/results/expH/{s1far_r1,s2v2_r1,s3rp_r2}.json (losses[].t_on/t_off, losses[0].<estimator>.drift_end_m, "
     "hold_windows_vehicle[0].t0); dataflash ardupilot.bin (XKF1 for EKF3, XUKO for the UKF port, XFGO for the FGO "
     "node); bag /ground_truth/pose and /imu/time_ref of H_s1far_r1, H_s2v2_r1, H_s3rp_r2",
     "NEW (B06/B07 draw aggregate bars over all losses/flights, not a per-flight time series)", None,
     "eval/results/expH/{s1far_r1,s2v2_r1,s3rp_r2}.json")


# =============================================================================================================== E06
# ============================================================== E4 extension (window sweep): FGO live paths, by W
# Lowest-value item (per the common brief's own time-box priority). Flight T_D_r1 (condition D, 1 tag), not T_A_r1:
# on T_A, live RMSE is identical to 4 dp across all five windows (e4_results.md), so three near-identical paths
# would not show anything; on T_D the windows differ at the millimetre level (0.0931 / 0.0863 / 0.0887 m, the
# largest spread of the four conditions), giving three paths that are not simply on top of each other. The
# "shortest" window IS the registered window (0.25 s); there is no separate "shortest" distinct from "registered"
# in the tested set, stated here rather than invented. W = 1 s is the middle of the five tested windows
# (0.25/0.5/1/2/5 s), not the longest; W = 5 s is the longest.
W5 = ("0.25", "1", "5")
E6 = {}; RMSE_W6 = {}
for w in W5:
    sc = L1(f"E4_T_D_r1_w{w}.json")
    x = np.loadtxt(f"{T1}/T_D_r1/room_fgo_w{w}/fgo_live.tum", ndmin=2)
    # world frame, no alignment (eval/tag_score.py's own convention) - world-frame ground truth, NOT the tag-0-
    # shifted arrays used elsewhere in this file, to avoid a silent frame mismatch with the stored score.
    Gt6, Gx6, Gy6 = cached("room_T_D_r1")["G"][:, 0], cached("room_T_D_r1")["G"][:, 1], cached("room_T_D_r1")["G"][:, 2]
    e6 = np.hypot(x[:, 1] - np.interp(x[:, 0], Gt6, Gx6), x[:, 2] - np.interp(x[:, 0], Gt6, Gy6))
    w0, w1 = sc["window_s"]
    ww = (x[:, 0] >= w0) & (x[:, 0] <= w1)
    rmse6 = float(np.sqrt(np.mean(e6[ww] ** 2)))
    check(f"E06 W={w}s: PLOTTED-window RMSE (world frame) vs stored E4 'FGO live' rmse (6 dp)", rd(rmse6, 6),
          rd(sc["tracks"]["FGO live"]["horiz_err_m"]["rmse"], 6), f"docs/thesis/tier1/scores/E4_T_D_r1_w{w}.json tracks.'FGO live'.horiz_err_m.rmse")
    d0_6 = float(math.hypot(x[0, 1] - np.interp(x[0, 0], Gt6, Gx6), x[0, 2] - np.interp(x[0, 0], Gt6, Gy6)))
    check(f"E06 W={w}s: start point within 0.5 m of ground truth (measured {rd(d0_6, 3)} m)", str(d0_6 <= 0.5), "True", "this script")
    E6[w] = (x, Gt6, Gx6, Gy6, w0, w1); RMSE_W6[w] = rd(sc["tracks"]["FGO live"]["horiz_err_m"]["rmse"], 4)
check("E06 the three plotted windows are distinguishable (not all equal to 4 dp, unlike T_A_r1)",
      str(len({rd(np.sqrt(np.mean(np.hypot(E6[w][0][:, 1] - np.interp(E6[w][0][:, 0], E6[w][1], E6[w][2]),
      E6[w][0][:, 2] - np.interp(E6[w][0][:, 0], E6[w][1], E6[w][3]))[(E6[w][0][:, 0] >= E6[w][4]) & (E6[w][0][:, 0] <= E6[w][5])] ** 2)), 4) for w in W5}) == 1),
      "False", "this script (distinct 4 dp RMSE across the three plotted windows)")
check("E06 3 tracks plotted (W = 0.25, 1, 5 s)", str(len(E6) == 3), "True", "this script")

fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 5.0))
_, Gt6, Gx6, Gy6, w0, w1 = E6["0.25"]
wg6 = (Gt6 >= w0) & (Gt6 <= w1)
ax.plot(Gx6[wg6], Gy6[wg6], color=TRUTH, lw=1.2, zorder=2, label="true path")
for w, ls in (("0.25", "-"), ("1", (0, (4, 2))), ("5", (0, (1, 1)))):
    x6 = E6[w][0]
    ax.plot(x6[:, 1], x6[:, 2], color=C["FGO"], lw=0.9, ls=ls, alpha=0.85, zorder=3, label=f"FGO live, W = {w} s")
ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)")
ax.set_xlim(-4.5, 4.5); ax.set_ylim(-4.5, 4.5)   # a little blank margin above the square, for the legend below
ax.set_aspect(1.0, adjustable="box")
st6 = measured_stretch(fig, ax); check("E06 equal scale (measured stretch)", rd(st6, 1), "1.0", "set_aspect(1.0)")
ax.legend(loc="lower center", ncol=1, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, 0.0))
save(fig, "E06", "E06_e4_window_sweep_paths", "Extension E4 (live window sweep): the FGO's live path at three window lengths",
     "Extension E4 (how far back the live FGO's fixed-lag window reaches), one flight with 1 known tag: the FGO "
     "in orange against the true path in grey, world frame, no alignment, equal scale. Solid is the registered "
     "window (W = 0.25 s, also the shortest tested), dashed is the middle window tested (W = 1 s) and dotted is "
     "the longest tested (W = 5 s). The three paths mostly overlap, but separate visibly along the bottom edge "
     "and near two corners of the square.",
     "docs/thesis/tier1/scores/E4_T_D_r1_w{0.25,1,5}.json (window_s, tracks.'FGO live'.horiz_err_m.rmse); "
     "~/thesis_data/tier1/T_D_r1/room_fgo_w{0.25,1,5}/fgo_live.tum; bag /ground_truth/pose of T_D_r1",
     "NEW (not drawn by any existing figure or candidate)", None,
     "docs/thesis/tier1/scores/E4_T_D_r1_w{0.25,1,5}.json")


# =============================================================================================================== index
n_ok = sum(c[4] for it in ITEMS for c in it["checks"]); n_tot = sum(len(it["checks"]) for it in ITEMS)
W = ["# Candidate thesis figures, group E: extension-experiment and Experiment 4/5 PATH candidates", "",
     f"Built by `eval/figs_cand_e.py` at commit `{COMMIT}` (run with `/home/makerspace/venv-evo/bin/python`). These are "
     "CANDIDATES for the user to pick from - not inserted into the thesis figure set in `docs/thesis/figures_thesis/` "
     "itself, and not folded into the combined candidates PDF, the thesis_assets bundle or the writing pack. Stored "
     "outputs only: `eval/results/*.json`, `docs/thesis/tier1/scores/*.json`, trial-directory `.tum` files, "
     "`sim/worlds/room_tags_map.json`, `gnss.npz`, and a cache of bag/dataflash reads pre-populated ONCE by "
     "`eval/figs_cand_e_extract.py` under `heavy.py`, written to `~/thesis_data/cand_e_cache/` and deleted at the "
     "end of this group's work. No estimator is run, no replay, no simulation, no flight.", "",
     f"**Checks:** {n_ok}/{n_tot} EXACT (string equality after one rounding by `rd()`, parsed from `eval/figs_thesis.py`, "
     "sha256 of the source segment used to detect drift).", "",
     "**Style:** `eval/thesis_style.py` (160 mm / 6.30 in text width, Okabe-Ito palette, no in-figure titles, no "
     "verdict words, no bold text, equal-scale top-down axes labelled East/North for every spatial-path candidate; "
     "E05 is a time series, not a spatial path, and is labelled accordingly). No two plots overlap.", "",
     "## Candidates", "", "| id | proposed title | source chart(s) | data files | checks | verdict pointer |", "|---|---|---|---|---|---|"]
for it in ITEMS:
    ok = sum(c[4] for c in it["checks"]); tot = len(it["checks"])
    vp = it["caption"].split("\n")[-1]
    W.append(f"| {it['id']} | {it['title']} | {it['source']} | {it['data_files']} | {ok}/{tot} | {vp} |")
W += ["", "## Skipped or time-boxed (not in any candidate's caption - process notes belong here, not on the figure)", "",
      "- E01 (Extension E2): only flight 1 of 3 per condition B/C/D is plotted; flights 2 and 3 are not. Their "
      "per-lap numbers are already in the Extension E2 results.",
      "- E02 (Extension E3): only flight T_A_r1 is plotted; one non-diverged (1% seed 0) and one diverged "
      "(1% seed 1) run of the 6 diverged and 12 non-diverged arm (a) runs are shown.",
      "- E03 (Extension E5): only flight T_A_r1 of 3 is plotted.",
      "- E04 (Experiment 4): only flight O_r1 of 3 is plotted; flights O_r2/O_r3b are not - their error-against-"
      "time curves for all three flights are already candidate B04.",
      "- E05 (Experiment 5): only the first loss of each flight is cross-checked against the stored per-loss "
      "drift; the later shaded intervals on each flight's own timeline are read directly from its own stored "
      "result file, not independently re-checked.",
      "- E06 (Extension E4, window sweep): lowest-value item per the common brief's time-box priority; only one "
      "tag count (condition D) and three of the five tested windows are plotted.", "",
      "## Judgement calls for the coordinator", "",
      "- **E02 vs C05/C06**: both groups draw Extension E3 paths for T_A_r1's 1% seed 0 run. C05 draws its "
      "hindsight track plus the final landmark map (a non-diverged, already-settled view); E02 draws its live "
      "track (the same run, different track) alongside a genuinely diverged run's live excursion, which no "
      "existing candidate shows. Kept as complementary, not flagged as a duplicate to drop.",
      "- **E05's FGO flight uses the corrected-priors hold set (s3rp_r2), not the original-priors set (s3v2) "
      "candidates B06/B07 use.** `H_s3rp_r1` (the first repeat of that set) has no stored bag, only `ardupilot.bin` "
      "- but `H_s3rp_r2` and `H_s3rp_r3` do have full stored bags, so E05 uses `s3rp_r2` rather than falling back "
      "to the superseded set. Flagged here because B06/B07 (an earlier group) still plot the superseded set; the "
      "coordinator may want to redraw B06/B07's FGO bar onto s3rp as a separate, later fix.",
      f"- **E06 uses flight T_D_r1 (condition D, 1 tag), not T_A_r1.** On T_A, the live RMSE is identical to 4 dp "
      "across all five tested windows (e4_results.md), so three plotted paths would be visually and numerically "
      f"indistinguishable there; T_D has the largest spread across windows ({RMSE_W6['0.25']} / {RMSE_W6['1']} / "
      f"{RMSE_W6['5']} m) of the four tested conditions.", ""]
open(os.path.join(OUT, "index_e.md"), "w").write("\n".join(W) + "\n")
print(f"\nTOTAL candidates {len(ITEMS)}; checks {n_ok}/{n_tot}; wrote {os.path.join(OUT, 'index_e.md')}")
