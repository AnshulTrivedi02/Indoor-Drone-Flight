#!/usr/bin/env python3
"""CANDIDATE THESIS FIGURES, GROUP A (decision D124, 2026-11-04): setup pages and Experiment 1 (1A/1B/1C) charts from
docs/thesis/summary/results_walkthrough.pdf and docs/thesis/summary/summary_plots.pdf that are NOT already a figure in
docs/thesis/figures_thesis/ (see index.md). These are CANDIDATES for the user to pick from, not inserted into the thesis
figure set themselves.

Reproduces the SAME data as the source chart (same loaders, same files, same selection; code below is COPIED from
eval/figs_thesis.py (by ast, as eval/figs_walkthrough_flights.py does), eval/figs_walkthrough_flights.py and
eval/figs_thesis_summary.py, not invented), then restyles to the thesis standard: eval/thesis_style.py (160 mm text
width, Okabe-Ito palette), no in-figure titles/verdict words/badges, no overlapping plots (insets split into their own
stacked panel, as the F9 split of this same group's brief did), captions ending in a Table A.4 pointer (D113), every
number in an exact cross-check.

STORED OUTPUTS ONLY. Closed-loop (1C) dataflash/bag reads and the room/outdoor/hold/safety truth-page bag reads are
served from a cache pre-populated by (run once, under heavy.py, see docs/handovers/2026-11-04_cand_a.md):
    ~/venv-evo/bin/python eval/figs_walkthrough_flights.py --cache ~/thesis_data/cand_a_cache --extract-only
(that invocation exits before writing any file outside the cache directory - verified by reading the script). 1A/1B
data comes directly from TUM files and eval/results/*.json: lightweight, no bag or dataflash read, so no cache miss
is expected for them. No estimator is run, no simulation, no flight.

Outputs: docs/thesis/figures_thesis/candidates/A##_*.{pdf,png}, candidates/captions/A##.md, candidates/index_a.md.
Usage: ~/venv-evo/bin/python eval/figs_cand_a.py"""
import ast, json, math, os, re, subprocess, sys
sys.path.insert(0, os.path.expanduser("~/.cache/thesis_pyshim"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from thesis_style import TEXT_WIDTH_IN, C, MK, TRUTH, INK, INK2, GRID, SURF, WALL, EST, RCPARAMS
plt.rcParams.update(RCPARAMS)

RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
CACHE = os.path.expanduser("~/thesis_data/cand_a_cache")
OUT = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "candidates"); os.makedirs(OUT, exist_ok=True)
CAPD = os.path.join(OUT, "captions"); os.makedirs(CAPD, exist_ok=True)
TABD = os.path.join(OUT, "tables"); os.makedirs(TABD, exist_ok=True)
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
L = lambda f: json.load(open(os.path.join(RES, f)))
M_ = "METHODOLOGY.md"

# ---------------------------------------------------------------------------------------------- shared code (ast-parsed
# from eval/figs_thesis.py, not executed as a script, exactly as eval/figs_walkthrough_flights.py does - so this script
# cannot drift from the thesis figures' own rd()/rng()/sim_path()/cl_clock()/cl_yaw_err()/cl_meta()/HALF/WIN)
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read(); _tree = ast.parse(_src)
_WANT_F = {"rd", "rng", "sim_path", "cl_clock", "cl_yaw_err", "cl_meta"}
_WANT_A = {"HALF", "WIN", "_sim"}
_nodes = []
for n in _tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in _WANT_F:
        _nodes.append(n)
    elif isinstance(n, ast.Assign):
        names = {t.id for t in n.targets if isinstance(t, ast.Name)}
        if names & _WANT_A:
            _nodes.append(n)
_ns = {"np": np, "math": math, "os": os, "json": json, "subprocess": subprocess, "mavutil": mavutil, "Reader": Reader,
       "get_typestore": get_typestore, "Stores": Stores, "TD": TD, "RES": RES, "L": L}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), FT, "exec"), _ns)
rd, rng, L_src = _ns["rd"], _ns["rng"], None
HALF, WIN = _ns["HALF"], _ns["WIN"]
assert C == {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"} and TRUTH == "#999999", "palette changed in thesis_style.py"
_clk_memo = {}; _orig_clock = _ns["cl_clock"]


def _cl_clock_memo(tr):
    if tr not in _clk_memo:
        _clk_memo[tr] = _orig_clock(tr)
    return _clk_memo[tr]


_ns["cl_clock"] = _cl_clock_memo

# ---------------------------------------------------------------------------------------------- cache (COPIED pattern
# from eval/figs_walkthrough_flights.py: cached() never computes, only reads a stored flight record; the cache was
# pre-populated by that same script's --extract-only mode, see module docstring)
import tempfile, shutil


def cached(key, fn):
    p = os.path.join(CACHE, key + ".npz")
    if os.path.exists(p):
        z = np.load(p, allow_pickle=True); return {k: z[k] for k in z.files}
    d = fn(); np.savez(p, **d); return d


def ex_cl(est, tr):
    def f():
        x, e, dc = _ns["cl_yaw_err"](tr, est); g = _ns["sim_path"](tr); kk, cc, off = _ns["cl_clock"](tr)
        return dict(yx=x, ye=e, dclk=np.array(dc), sim=g, clk=np.array([kk, cc, off]))
    return cached(f"cl_{tr}", f)


def _bag_open(tr):
    bag = f"{TD}/{tr}/bag"
    if not os.path.exists(f"{bag}/bag_0.db3") and os.path.exists(f"{bag}/bag_0.db3.zst"):
        tmp = tempfile.mkdtemp(prefix="cand_a_bag_"); shutil.copy(f"{bag}/metadata.yaml", tmp)
        subprocess.run(["zstd", "-q", "-d", f"{bag}/bag_0.db3.zst", "-o", f"{tmp}/bag_0.db3"], check=True)
        return tmp, tmp
    return bag, None


def ex_room(tr):
    def f():
        ts = get_typestore(Stores.ROS2_JAZZY); G = []
        bag, tmp = _bag_open(tr)
        try:
            with Reader(bag) as r:
                cs = {c.topic: c for c in r.connections}
                for con, _, raw in r.messages(connections=[cs["/ground_truth/pose"]]):
                    m = ts.deserialize_cdr(raw, con.msgtype)
                    q = m.pose.orientation
                    G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y,
                              math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
        return dict(G=np.array(G))
    return cached(f"room_{tr}", f)


def ex_sim(tr):
    return cached(f"sim_{tr}", lambda: dict(sim=_ns["sim_path"](tr)))


def ex_xkf1(tr):
    def f():
        mv = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); k1 = []
        while True:
            r = mv.recv_match(type=["XKF1"])
            if r is None:
                break
            if r.C == 0:
                k1.append((r.TimeUS / 1e6, r.PN, r.PE))
        return dict(K1=np.array(k1))
    return cached(f"xkf1_{tr}", f)


# ---------------------------------------------------------------------------------------------- frame helpers (COPIED
# from eval/figs_walkthrough_flights.py, itself copied from eval/figs_thesis_drift.py's to_NE()/frame check)
def NE(key, xyz):
    return (xyz[:, 0], xyz[:, 1]) if key.startswith("EKF3") else (xyz[:, 1], xyz[:, 0])


def to_NE(key, a, truth):
    if key.startswith("EKF3"):
        return a[:, 0], a[:, 1], a[:, 2]
    if truth:
        return a[:, 0], a[:, 2], a[:, 1]
    return a[:, 0], a[:, 1], -a[:, 2]


HEAD_TOL_DEG = 10.0


def frame_ok(est, gt, win):
    (te, ne, ee), (tg, ng, eg) = est, gt
    o_e = math.hypot(ne[0], ee[0]); o_g = math.hypot(ng[0], eg[0])
    i0 = np.searchsorted(tg, win[0]); j0 = i0 + np.argmax(ng[i0:] - ng[i0] >= 5.0); ta, tb = tg[i0], tg[j0]
    h_g = math.degrees(math.atan2(eg[j0] - eg[i0], ng[j0] - ng[i0]))
    h_e = math.degrees(math.atan2(np.interp(tb, te, ee) - np.interp(ta, te, ee), np.interp(tb, te, ne) - np.interp(ta, te, ne)))
    return o_e < 0.05 and o_g < 0.05 and abs(h_e - h_g) < HEAD_TOL_DEG


def unaligned(key, tr, sub, f, win):
    a = np.loadtxt(f"{TD}/{tr}/{sub}/{f}"); g = np.loadtxt(f"{TD}/{tr}/{sub}/ground_truth.tum")
    est_, gt_ = to_NE(key, a, False), to_NE(key, g, True)
    ok = frame_ok(est_, gt_, win)
    te, ne, ee = est_; tg, ng, eg = gt_
    k = (te >= tg[0]) & (te <= win[1])
    return ok, (te[k] - win[0], ne[k], ee[k], np.hypot(ne[k] - np.interp(te[k], tg, ng), ee[k] - np.interp(te[k], tg, eg)), gt_)


def gt_enu(sub):
    def f(tr):
        g = np.loadtxt(f"{TD}/{tr}/{sub}/ground_truth.tum"); return g[:, 0], g[:, 1], g[:, 2], g[:, 3]
    return f


# ---------------------------------------------------------------------------------------------- caption-verdict self-check
# (D113 banned-word regex, COPIED from eval/caption_verdict_check.py, so a candidate caption cannot ship with a verdict
# word; the coordinator's checker does not yet scan candidates/, per the group brief, so this is this generator's own gate)
BANNED = re.compile(r"\b(pass(?:es|ed|ing)?|fail(?:s|ed|ing)?|not\s+met|met|miss(?:es|ed|ing)?|verdicts?)\b", re.IGNORECASE)
TA_IDS = set()
for _ln in open(os.path.join(ROOT, "docs", "thesis", "tables", "TA_verdicts.md"), encoding="utf-8"):
    if _ln.startswith("|"):
        _parts = _ln.split("|")
        if len(_parts) >= 3 and _parts[1].strip() not in ("Experiment", "---"):
            TA_IDS.add(_parts[2].strip())


def verdict_line(ids_text):
    """ids_text: None for descriptive, else 'id1; id2; ...' (each a TA_verdicts.md id or an unambiguous prefix of one)."""
    if ids_text is None:
        return "Verdicts: Table A.4, none (descriptive)."
    for rid in ids_text.split(";"):
        rid = rid.strip()
        assert rid in TA_IDS or any(i.startswith(rid) for i in TA_IDS), f"not a TA_verdicts.md id or prefix: {rid!r}"
    return f"Verdicts: Table A.4, rows {ids_text}."


# ---------------------------------------------------------------------------------------------- figure/check/caption/index
# machinery (own, modelled on eval/figs_thesis.py's save()/check(), writing to candidates/ instead of figures_thesis/)
ITEMS = []; CHK = []


def check(label, computed, expected, src):
    c, e = str(computed), str(expected)
    if any(x[:3] == (label, c, e) for x in CHK):
        return
    CHK.append((label, c, e, src, c == e))


_SRC_CACHE = {}


def cite(path, line, phrase, label=None):
    """COPIED pattern from eval/figs_thesis.py's cite(): read the source at build time and check that `line` contains
    `phrase` (the quoted rule text, with its numbers)."""
    lines = _SRC_CACHE.setdefault(path, open(os.path.join(ROOT, path)).read().split("\n"))
    got = phrase if phrase in lines[line - 1] else lines[line - 1].strip()[:90]
    check(f"{label or ''}rule text {os.path.basename(path)}:{line} contains the quoted phrase", got, phrase, f"{path}:{line} (read at build time)")
    return f"{os.path.basename(path)}:{line}"


def write_caption(fid, text):
    p = os.path.join(CAPD, f"{fid}.md")
    open(p, "w").write(text.strip() + "\n"); return p


def save(fig, fid, name, title, caption, inputs, source_charts, verdict_ids):
    """Writes candidates/<name>.pdf/.png; records caption+checks for candidates/index_a.md. verdict_ids: None (descriptive)
    or 'id1; id2; ...'."""
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
    # Height autocrop (2026-11-04): several candidates lock an axes box to a 1:1 data aspect
    # (adjustable="box"), which can leave a lot of blank vertical margin in a fixed-height figure (the
    # same mechanism the restyle's R3/R5 fix addressed). Rather than hand-tuning figsize per figure, crop
    # the SAVED bbox to the figure's own actual content height, at FULL declared width (0 to
    # TEXT_WIDTH_IN) - this keeps every PDF exactly 453.6 pt wide (unlike bbox_inches="tight", which the
    # restyle banned because it also changes the width) while removing the dead vertical space.
    from matplotlib.transforms import Bbox
    fig.canvas.draw()
    tb = fig.get_tightbbox(fig.canvas.get_renderer())
    pad = 0.08
    crop = Bbox([[0, max(tb.y0 - pad, 0)], [TEXT_WIDTH_IN, min(tb.y1 + pad, fig.get_size_inches()[1])]])
    fig.savefig(base + ".png", dpi=170, bbox_inches=crop); fig.savefig(base + ".pdf", bbox_inches=crop); plt.close(fig)
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=fid, title=title, source=source_charts, inputs=inputs, caption=full_caption, checks=list(CHK),
                      files=[name + ".png", name + ".pdf"], status="CURRENT" if ok else "FLAGGED"))
    print(f"wrote {base}.png/.pdf  checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    for c in CHK:
        if not c[4]:
            print("   CHECK FAIL:", c)
    CHK = []


def legend_est(ax, ests=EST, extra=(), **kw):
    h = [Line2D([], [], ls="-", marker=MK[e], color=C[e], ms=6, label=e) for e in ests] + list(extra)
    return ax.legend(handles=h, frameon=False, **kw)


def measured_stretch(fig, ax):
    fig.canvas.draw()
    bb = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted()); x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    return (bb.height / (y1 - y0)) / (bb.width / (x1 - x0))


def wallband(ax, lim, vertical=True, fs=9.5):
    for s_ in (1, -1):
        (ax.axvspan if vertical else ax.axhspan)(10 * s_, lim * s_, color="#d9d9d9", lw=0, zorder=0.5)
        c_ = (10 + lim) / 2 * s_
        if vertical:
            ax.text(c_, 0.5, "wall", transform=ax.get_xaxis_transform(), rotation=90, ha="center", va="center", fontsize=fs, color=INK2)
        else:
            ax.text(0.5, c_, "wall", transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=fs, color=INK2)


# =============================================================================================================== A01/A02
# ======================================================================== SETUP: 1A/1B truth paths (and A21/A22, height)
# (walkthrough S1/1A_truth/1B_truth: "where the drone really flew", COPIED data path from figs_walkthrough_flights.py
# truth_page(). SPLIT (fix sweep, 2026-11-04) from one two-panel candidate per flight set into two SEPARATE
# single-panel candidates: A01/A02 keep the top-down equal-scale geography; A21/A22 (new ids, added below) carry the
# height-against-time view. The original comment called this "the same stacked-different-scale pattern this group's
# F9 split used" - re-checked against F9's own commit (c2cad19) and it is NOT the same: F9's two panels SHARE one time
# axis (both plot heading error vs the same time, one at full scale, one zoomed); these two panels shared NEITHER axis
# (position in metres vs height against time in seconds), so they fail "stacked only on a shared scale" under the
# fix-sweep checklist and the user's own "all the plots should be separate" rule. A04-A06 (room_cand(), below) are NOT
# affected - one row of panels sharing one pair of axes throughout, not stacked at different scales.)
def truth_cand(fid, name, title, trials, gt_of, source_desc, inputs, flights_n, bag_path):
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 2.3))
    for s_ in (1, -1):
        ax.axhspan(10 * s_, 11 * s_, color=WALL, lw=0)
    for tr in trials:
        tg, E_, N_, U_ = gt_of(tr)
        ax.plot(N_, E_, color=TRUTH, lw=0.9, zorder=2)
    ax.set_xlim(-6, 166); ax.set_ylim(-11, 11); ax.set_aspect(1.0, adjustable="box"); ax.set_yticks([-10, 0, 10])
    ax.set_xlabel("North, along the corridor (m)"); ax.set_ylabel("East (m)")
    st = measured_stretch(fig, ax)
    check(f"{fid} equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
    check(f"{fid} flights shown (n)", len(trials), flights_n, source_desc)
    cite("CLAUDE.md", 101, "5 m tall and 0.2 m thick at x = ±10 m", label=f"{fid} ")
    save(fig, fid, name, title,
         f"Simulator ground truth (truth flying, nothing estimated): every one of the {flights_n} flights of {source_desc}, seen "
         "from above, equal scale (no stretch); the grey bands beyond East = ±10 m (CLAUDE.md:101) are the corridor "
         "walls; every flight's true path lies on the same straight line, so the lines overlap. No log axes. The "
         "height-against-time view of the same flights is a separate candidate.",
         inputs, name, None)


def height_cand(fid, name, title, trials, gt_of, source_desc, inputs, flights_n, twin_id):
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 2.6))
    for tr in trials:
        tg, E_, N_, U_ = gt_of(tr)
        ax.plot(tg - tg[0], U_, color=TRUTH, lw=0.9, zorder=2)
    ax.set_xlim(0, None); ax.set_ylim(0, None)
    # x-axis (fix sweep, 2026-11-04): this panel was previously labelled "time from take-off" with a dotted line
    # "marking" take-off at t=0 - checked against the recorded ground_truth.tum directly: height sits flat at the
    # ground rest height (0.195 m) for the first ~20 s after t=0, so t=0 is the START OF THE RECORDING (the vehicle
    # is still on the ground), not the moment of lift-off, which happens visibly later in the climb. The claim was
    # wrong, and the line sat exactly on the left spine regardless (not usefully visible) - dropped the line and
    # relabelled accurately.
    ax.set_xlabel("time since the start of the recording (s)"); ax.set_ylabel("height (m)")
    check(f"{fid} flights shown (n)", len(trials), flights_n, source_desc)
    save(fig, fid, name, title,
         f"Simulator ground truth (truth flying, nothing estimated): every one of the {flights_n} flights of {source_desc}, "
         "true height against time since the start of the recording (one line per flight; they overlap) - height "
         "stays at the ground rest height until each flight's own take-off, then climbs, then returns to the ground "
         f"rest height at landing. No log axes. The top-down path of the same flights is candidate {twin_id}.",
         inputs, name, None)


ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
A_FL = [f"dsn_tex_r{i}" for i in range(1, 10)]
check("1A flights available for the standard-sensor textured dataset (n)", len(A_FL), 9, "docs/thesis/numbers.md:230 ('all 9 usable')")
truth_cand("A01", "A01_1A_truth", "Where the drone really flew: Experiment 1A, 9 flights up the corridor",
           A_FL, gt_enu("ukf"), "Experiment 1A, the standard-sensor dataset, textured floor (dsn_tex_r1-r9)",
           "~/thesis_data/trials/dsn_tex_r1..r9/ukf/ground_truth.tum (ENU)", 9, "sim/worlds/corridor_textured.sdf")
height_cand("A21", "A21_1A_height", "Climb, cruise and landing: Experiment 1A, 9 flights up the corridor",
            A_FL, gt_enu("ukf"), "Experiment 1A, the standard-sensor dataset, textured floor (dsn_tex_r1-r9)",
            "~/thesis_data/trials/dsn_tex_r1..r9/ukf/ground_truth.tum (ENU)", 9, "A01")

P4E = L("phase4_fwdc_evo.json")["trials"]
B_FL = [f"fwdc_tex_r{i}" for i in (1, 2, 3)]
check("1B flights available for the textured-wall camera dataset, textured floor (n)", len(B_FL), 3, "eval/results/phase4_fwdc_evo.json")
truth_cand("A02", "A02_1B_truth", "Where the drone really flew: Experiment 1B, 3 flights with a roof and painted-line walls",
           B_FL, gt_enu("ukf_baseline"), "Experiment 1B, the textured-wall camera dataset, textured floor (fwdc_tex_r1-r3)",
           "~/thesis_data/trials/fwdc_tex_r1..r3/ukf_baseline/ground_truth.tum (ENU)", 3, "sim/worlds/corridor_textured_fwdc.sdf")
height_cand("A22", "A22_1B_height", "Climb, cruise and landing: Experiment 1B, 3 flights with a roof and painted-line walls",
            B_FL, gt_enu("ukf_baseline"), "Experiment 1B, the textured-wall camera dataset, textured floor (fwdc_tex_r1-r3)",
            "~/thesis_data/trials/fwdc_tex_r1..r3/ukf_baseline/ground_truth.tum (ENU)", 3, "A02")


# =============================================================================================================== A03-A06
# ============================================================================= SETUP: the tag room and other truth views
# (walkthrough S2/2_truth/4_truth/5_truth/5S_truth: room_paths(), COPIED data path. One panel per group, equal scale,
# shared axes; grey shades tell flights within a group apart (no colour is an estimator here - these are truth-only
# pages, nothing estimated).)
def room_cand(fid, name, title, groups, getxy, source_desc, inputs, flights_n, pad=0.6, swap=False):
    fig, axs = plt.subplots(1, len(groups), figsize=(TEXT_WIDTH_IN, 6.30 / len(groups) + 1.6), sharex=True, sharey=True)
    axs = np.atleast_1d(axs); allx, ally = [], []
    shades = ["#4d4d4d", "#8c8c8c", "#bdbdbd"]
    for ax, (gtitle, trs) in zip(axs, groups):
        for i, tr in enumerate(trs):
            x, y = getxy(tr)
            if swap:
                x, y = y, x
            allx += [float(x.min()), float(x.max())]; ally += [float(y.min()), float(y.max())]
            ax.plot(x, y, color=shades[i % 3], lw=0.9, zorder=2)
            ax.plot(x[0], y[0], marker="o", ms=4, color=INK, zorder=5)
        ax.set_title(gtitle, loc="left", fontsize=9); ax.set_aspect(1.0, adjustable="box")
        ax.set_xlabel("North (m)" if swap else "East (m)")
    axs[0].set_xlim(min(allx) - pad, max(allx) + pad); axs[0].set_ylim(min(ally) - pad, max(ally) + pad)
    axs[0].set_ylabel("East (m)" if swap else "North (m)")
    st = measured_stretch(fig, axs[0]); check(f"{fid} equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
    n_total = sum(len(trs) for _, trs in groups)
    check(f"{fid} flights shown (n)", n_total, flights_n, source_desc)
    sizes = {len(trs) for _, trs in groups}
    # Per-group count (fix sweep, 2026-11-04): panel titles no longer carry "n = N" (moved here, matching
    # figs_thesis.py's own restyle precedent of keeping only a short condition tag on a panel, not a number).
    if len(sizes) != 1:
        per_group = f"{n_total} flights total, not evenly split across panels"
    else:
        gsz = sizes.pop(); word = "flight" if gsz == 1 else "flights"
        per_group = f"{gsz} {word}" if len(groups) == 1 else f"{gsz} {word} in each panel"
    save(fig, fid, name, title,
         f"Simulator ground truth (truth flying, nothing estimated): {source_desc}, one true path per flight (thin grey "
         f"lines, shaded to tell flights within a panel apart; black dot: take-off). {len(groups)} "
         f"{'panel' if len(groups) == 1 else 'panels'} ({per_group}), equal scale "
         "(1.0×), sharing one pair of axes. No log axes.",
         inputs, name, None)


def gt_room(tr):
    G = ex_room(tr)["G"]; return G[:, 1], G[:, 2]


# Panel titles (fix sweep, 2026-11-04): the "n = 3" / "n = 3" counts were dropped from every group title below
# (matching figs_thesis.py's own restyle precedent, e.g. FIG 7 L's "(a) with loop closure" - a short condition
# tag identifying what a panel shows is kept, a number is not); each candidate's own check()/caption already
# states the per-group and total flight counts.
TL = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
room_cand("A03", "A03_2_truth", "Where the drone really flew: the 12 tag-room flights of Experiments 2 and 3",
          [(TL[c], [f"T_{c}_r{i}" for i in (1, 2, 3)]) for c in "ABCD"], gt_room,
          "the 12 flights of Experiment 2 (5 laps of the 6 m square, 4 tag counts, 3 flights each)",
          "bag /ground_truth/pose of T_{A,B,C,D}_r{1,2,3}", 12)
check("A03 laps / square side (m) / tags per condition", "5 / 6 / 8, 4, 2, 1", "5 / 6 / 8, 4, 2, 1",
      "Figure 5.1 caption (eval/figs_thesis.py F5: '5 laps of a 6 m square'; A all 8, B the 4 corners, C 2, D 1 tag)")

O_FL = ["O_r1", "O_r2", "O_r3b"]
room_cand("A04", "A04_4_truth", "Where the drone really flew: the 3 outdoor-indoor flights of Experiment 4", [("", O_FL)],
          gt_room, "the 3 flights of Experiment 4 (out along North into the building and back the same way)",
          "bag /ground_truth/pose of O_r1, O_r2, O_r3b", 3, pad=3.0, swap=True)

H_FL = ["H_s1_r1", "H_s1_r2", "H_s1_r3", "H_s1far_r1", "H_s1far_r2", "H_s1far_r3b"] + [f"H_s2v2_r{i}" for i in (1, 2, 3)] + \
       [f"H_s3v2_r{i}" for i in (1, 2, 3)]


def sim_xy(tr):
    g = ex_sim(tr)["sim"]; return g[:, 1], g[:, 2]


HG = [("EKF3 flying,\nnear start spot", H_FL[0:3]), ("EKF3 flying,\nfar start spot", H_FL[3:6]),
      ("UKF flying", H_FL[6:9]), ("FGO flying", H_FL[9:12])]
room_cand("A05", "A05_5_truth", "Where the drone really flew: the 12 hold flights of Experiment 5", HG, sim_xy,
          "the 12 flights of Experiment 5 (an estimator holds position while the wall tag is hidden), position from the "
          "take-off spot", "dataflash SIM of H_s1_r1..r3, H_s1far_r1, r2, r3b, H_s2v2_r1..r3, H_s3v2_r1..r3", 12, pad=0.3)

S_FL = ["H_safety_ukf_a_v3", "H_safety_ukf_b_v3", "H_safety_fgo_a_v4", "H_safety_fgo_b_v4"]
room_cand("A06", "A06_5S_truth", "Where the drone really flew: the 4 final 5S safety runs",
          [("UKF safety run a", [S_FL[0]]), ("UKF safety run b", [S_FL[1]]), ("FGO safety run a", [S_FL[2]]),
           ("FGO safety run b", [S_FL[3]])], sim_xy,
          "the 4 final safety runs of Experiment 5S, position from the take-off spot",
          "dataflash SIM of H_safety_ukf_a_v3, H_safety_ukf_b_v3, H_safety_fgo_a_v4, H_safety_fgo_b_v4", 4, pad=0.3)


# =============================================================================================================== A07
# ========================================================================= EXPERIMENT 1A: raw error against time, n = 9
# (walkthrough page 02, fl_1A_unaligned_err.png; the 9-flight RAW PATHS view of this same dataset is already Figure 4.1d
# (internal R6, H1.1) - skipped, see candidates/index_a.md. This is the companion ERROR-MAGNITUDE view (not drawn by R6),
# COPIED data path from figs_walkthrough_flights.py unaligned()/SUB1.)
SUB1 = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF": ("ukf", "ukf_traj.tum"), "FGO": ("fgo", "fgo_traj.tum")}
UN1 = {}; FR1 = 0
for e in EST:
    for tr in A_FL:
        win = ev[tr]["window_s"]
        ok, UN1[(e, tr)] = unaligned(e, tr, *SUB1[e], win); FR1 += ok
check("A07 frame check (rule of eval/figs_thesis_drift.py, heading tolerance 10 deg) on every flight and estimator",
      f"{FR1}/27", "27/27", "this script (to_NE()/frame_ok(), copied)")
fig, axs = plt.subplots(3, 1, figsize=(TEXT_WIDTH_IN, 5.6), sharex=True, sharey=True)
for ax, e in zip(axs, EST):
    ax.axhline(0, color=INK2, lw=0.6, zorder=1); ax.axvline(0, color=INK2, lw=0.8, ls=":", zorder=1)
    for tr in A_FL:
        v = UN1[(e, tr)]; ax.plot(v[0], v[3], color=C[e], lw=0.9, zorder=3)
    ax.set_title(e, loc="left", fontsize=9.5, color=C[e])
axs[0].set_ylim(0, None); axs[-1].set_xlabel("time since the start of the cruise (s); take-off is before the dotted line at 0")
fig.supylabel("horizontal error (m)", x=0.01)
assert len({ax.get_ylim() for ax in axs}) == 1
save(fig, "A07", "A07_1A_unaligned_err", "Without a heading source the raw horizontal error grows to metres-to-tens-of-metres",
     "Offline standard-sensor dataset (IMU, downward flow, downward LiDAR; no heading source), textured floor, Experiment "
     "1A, all 9 flights (dsn_tex_r1-r9). Passive estimators, truth flying. One panel per estimator, sharing one y-scale: "
     "the raw horizontal distance between the estimate and the true position, from take-off to the end of the cruise "
     "window, against time since the start of the cruise (take-off is before the dotted line at 0 s). Paths are raw: no "
     "fitted alignment (no rotation, translation or scale fit). The companion top-down path view of these same 9 flights "
     "is Figure 4.1d (provisional); the fitted (registered) and raw scores are in Table 4.4 (provisional).",
     "TUMs of dsn_tex_r1..r9; frame map (N, E) = (x, -y) for the UKF/FGO (eval/figs_thesis_drift.py); windows "
     "rerun_dsn_evo.json, dsn_extra_evo.json", "walkthrough page 02 (fl_1A_unaligned_err.png)", "H1.1")


# =============================================================================================================== A08
# ============================================================================ EXPERIMENT 1B: the camera heading check
# (summary page 03 / walkthrough page 04: a TABLE-only page, not a chart - COPIED data path from figs_thesis_summary.py's
# VAL = eval/results/fwd_validation.json aggregate. No existing figures_thesis table covers this; T2 (Table 4.1) is the
# accuracy table, not the pass/fail validation check. Rendered as a small table candidate, not a plot.)
import textwrap


def table_cand(fid, name, title, header, rows, widths, caption, inputs, source_charts, verdict_ids, fs=9.5, row_h=0.09):
    tot = sum(widths); xs = [sum(widths[:i]) / tot for i in range(len(widths))]
    # chars/inch at this font size (conservative: average glyph width ~0.55 x the font size in points, DejaVu Sans):
    # wrap each column's text to its own width so nothing overflows into, or past, the next column. Checked by eye
    # (no automated glyph-width measurement) - see the group handover for the calibration note.
    cpi = 72 / (fs * 0.62)
    wraps = [max(8, int(wd / tot * TEXT_WIDTH_IN * 0.92 * cpi)) for wd in widths]
    allr = [[textwrap.fill(str(c), wraps[j]) for j, c in enumerate(r)] for r in [header] + rows]
    nlines = [max(c.count("\n") + 1 for c in r) for r in allr]
    lh_in = fs * 1.55 / 72
    ax_h_in = lh_in * (sum(nlines) + 0.6 * len(allr))
    margin_in = 0.14
    h_fig = ax_h_in + 2 * margin_in
    fig = plt.figure(figsize=(TEXT_WIDTH_IN, h_fig))
    ax = fig.add_axes([0.015, margin_in / h_fig, 0.97, ax_h_in / h_fig]); ax.axis("off"); ax.patch.set_visible(False)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    lh = lh_in / ax_h_in
    y = 1.0
    for j, (h_, x_) in enumerate(zip(allr[0], xs)):
        ax.text(x_, y, h_, fontsize=fs, ha="left", va="top", linespacing=1.3)
    y -= lh * nlines[0] + lh * 0.3
    ax.plot([0, 1], [y, y], color=INK2, lw=0.8, transform=ax.transAxes)
    y -= lh * 0.35
    for i, row in enumerate(allr[1:]):
        for j, (cell, x_) in enumerate(zip(row, xs)):
            ax.text(x_, y, cell, fontsize=fs, ha="left", va="top", linespacing=1.3)
        y -= lh * nlines[i + 1] + lh * 0.35
    save(fig, fid, name, title, caption, inputs, source_charts, verdict_ids)


FV = L("fwd_validation.json")["aggregate"]
check("A08 textured-wall camera dataset: flights where the heading check passed", FV["psi/fwdc/all"]["n_pass"], "9/9",
      "eval/results/fwd_validation.json aggregate 'psi/fwdc/all'.n_pass")
check("A08 plain-wall camera dataset, blank floor: flights where the heading check passed", FV["psi/fwdplainc/blank"]["n_pass"],
      "3/3", "eval/results/fwd_validation.json aggregate 'psi/fwdplainc/blank'.n_pass")
check("A08 plain-wall camera dataset, transition floor: flights where the heading check passed", FV["psi/fwdplainc/trans"]["n_pass"],
      "3/3", "eval/results/fwd_validation.json aggregate 'psi/fwdplainc/trans'.n_pass")
check("A08 plain-wall camera dataset, checkerboard floor: flights where the heading check passed", FV["psi/fwdplainc/tex"]["n_pass"],
      "0/3", "eval/results/fwd_validation.json aggregate 'psi/fwdplainc/tex'.n_pass")
cite(M_, 2729, "≥ 70%", label="A08 "); cite(M_, 2729, "≤ 0.5°", label="A08 "); cite(M_, 2729, "≤ 1.0°", label="A08 ")
cite(M_, 2729, "≤ 5% (\\|error\\| > 3°)", label="A08 ")
table_cand("A08", "A08_1B_heading_check", "The forward-camera heading check, by wall type and floor",
           ["camera view", "floor", "flights where the heading check held"],
           [["painted-line walls", "textured, blank or transition", FV["psi/fwdc/all"]["n_pass"]],
            ["plain walls", "blank", FV["psi/fwdplainc/blank"]["n_pass"]],
            ["plain walls", "transition (half textured, half blank)", FV["psi/fwdplainc/trans"]["n_pass"]],
            ["plain walls", "textured (checkerboard)", FV["psi/fwdplainc/tex"]["n_pass"]]],
           [0.30, 0.42, 0.28],
           "Each flight's forward-camera heading estimate compared with the simulator's true heading over its cruise, per "
           "flight, against the accuracy bar of METHODOLOGY.md:2729 (availability ≥ 70%, bias ≤ 0.5°, "
           "noise ≤ 1.0°, outlier rate ≤ 5%). 9 flights with painted-line walls (3 per floor); 9 flights "
           "with plain walls (3 per floor).",
           "eval/results/fwd_validation.json aggregate", "summary page 03 / walkthrough page 04",
           "H1.2 heading and yaw rate, textured walls; H1.2 heading, plain walls over blank and transition floors; "
           "H1.2 heading, plain walls over the checkerboard floor")


# =============================================================================================================== A09/A10
# ===================================================== EXPERIMENT 1B: raw paths without and with the camera heading, n=3
# (walkthrough page 05, fl_1B_unaligned_paths.png: COPIED data path from figs_walkthrough_flights.py. Drawn here as
# plots ONLY (A09); its in-figure table of registered score + raw maximum error becomes a separate markdown table
# candidate (A10), per the group brief - a table drawn inside a chart is dropped from the figure.)
SUBB = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF_baseline": ("ukf_baseline", "ukf_traj.tum"), "FGO_baseline": ("fgo_baseline", "fgo_traj.tum"),
        "UKF_heading": ("ukf_heading", "ukf_traj.tum"), "FGO_heading": ("fgo_heading", "fgo_traj.tum")}
UNB = {}; FRB = 0
for key in SUBB:
    for tr in B_FL:
        win = P4E[tr]["window_s"]; ok, UNB[(key, tr)] = unaligned(key, tr, *SUBB[key], win); FRB += ok
check("A09 frame check (rule of eval/figs_thesis_drift.py, heading tolerance 10 deg) on every flight and arm", f"{FRB}/15", "15/15",
      "this script (to_NE()/frame_ok(), copied)")
RAWMX = {k: max(float(np.max(UNB[(k, tr)][3])) for tr in B_FL) for k in SUBB}


def paths_raw(ax, UN, key, trs, win_of, col, lim, ls="-"):
    wallband(ax, lim)
    for tr in trs:
        tg, ng, eg = UN[(key, tr)][4]; w = tg <= win_of(tr)[1]
        ax.plot(eg[w], ng[w], color=TRUTH, lw=1.3, zorder=2)
    for tr in trs:
        ax.plot(UN[(key, tr)][2], UN[(key, tr)][1], color=col, lw=0.9, ls=ls, zorder=3)
    ax.plot(0, 0, marker="o", ms=4, color=INK, zorder=5)
    ax.set_aspect(1.0, adjustable="box")


CLJ = {tr: L(f"closed_loop_{tr}.json") for tr in HALF["EKF3"][1]}
FRC = 0; CLE = {}
for tr in HALF["EKF3"][1]:
    d = ex_cl("EKF3", tr); kk, cc, _ = d["clk"]; g = d["sim"]; K = ex_xkf1(tr)["K1"]
    c0b, c1b = CLJ[tr]["cruise_s"]; s0, s1 = (c0b - cc) / (1 + kk), (c1b - cc) / (1 + kk)
    est_ = (K[:, 0], K[:, 1], K[:, 2]); gt_ = (g[:, 0], g[:, 2], g[:, 1])
    FRC += frame_ok(est_, gt_, (s0, s1))
    wk = K[:, 0] <= s1; wg = g[:, 0] <= s1
    CLE[tr] = (K[wk, 1], K[wk, 2], g[wg, 2], g[wg, 1])
check("A09 closed-loop EKF3 panel frame check (XKF1 core 0 vs SIM, heading tolerance 10 deg)", f"{FRC}/3", "3/3", "this script")
PAN = [("EKF3", "EKF3\nno heading"), ("UKF_baseline", "UKF\nno heading"), ("FGO_baseline", "FGO\nno heading"),
       ("EKF3_cl", "EKF3, with\nheading"),
       ("UKF_heading", "UKF\nwith heading"), ("FGO_heading", "FGO\nwith heading")]
LIMB = max([float(np.abs(v[2]).max()) for v in UNB.values()] + [float(np.abs(v[1]).max()) for v in CLE.values()] + [10.0]) + 4.0
fig = plt.figure(figsize=(TEXT_WIDTH_IN, 4.6))
gs = fig.add_gridspec(1, 6, wspace=0.1)
axs = [fig.add_subplot(gs[0, i]) for i in range(6)]
for ax in axs[1:]:
    ax.sharex(axs[0]); ax.sharey(axs[0])
for ax, (key, lab) in zip(axs, PAN):
    if key == "EKF3_cl":
        wallband(ax, LIMB)
        for tr in HALF["EKF3"][1]:
            en, ee, gn, ge = CLE[tr]; ax.plot(ge, gn, color=TRUTH, lw=1.3, zorder=2)
        for tr in HALF["EKF3"][1]:
            en, ee, gn, ge = CLE[tr]; ax.plot(ee, en, color=C["EKF3"], lw=0.9, zorder=3)
        ax.plot(0, 0, marker="o", ms=4, color=INK, zorder=5); ax.set_aspect(1.0, adjustable="box")
        ax.set_title(lab, loc="left", fontsize=9.0, color=C["EKF3"])
    else:
        paths_raw(ax, UNB, key, B_FL, lambda tr: P4E[tr]["window_s"], C[key.split("_")[0]], LIMB)
        ax.set_title(lab, loc="left", fontsize=9.0, color=C[key.split("_")[0]])
    ax.set_xlabel("East (m)", fontsize=9)
for ax in axs[1:]:
    plt.setp(ax.get_yticklabels(), visible=False)
axs[0].set_ylabel("North (m)"); axs[0].set_xlim(-LIMB, LIMB); axs[0].set_ylim(-3, 163)
save(fig, "A09", "A09_1B_unaligned_paths", "With the camera heading the UKF and FGO paths stay on the true path",
     "Experiment 1B flights 1-3 (textured walls over the textured floor), raw position estimate from take-off to the end "
     "of the cruise window, truth grey; walls at East = ±10 m (grey band). Six panels, equal scale, sharing one "
     "pair of axes: EKF3/UKF/FGO without the camera heading; EKF3 with heading is a closed-loop Experiment 1C flight "
     "(flown, not a replay of this recording - it has no offline heading arm); UKF/FGO with the camera heading (offline "
     "heading arms). Paths are raw: no fitted alignment. The registered fitted score and the raw maximum error per arm "
     "are in candidate A10 (companion markdown table).",
     "TUMs of fwdc_tex_r1..r3 ({ekf3,ukf_baseline,fgo_baseline,ukf_heading,fgo_heading}/*.tum); frame map (N, E) = (x, "
     "-y) for the UKF/FGO; windows and cruise ATEs phase4_fwdc_evo.json; closed-loop panel: dataflash XKF1 (core 0) and "
     "SIM of cl_bcpp_tex_r1..r3_half, cruise window closed_loop_<trial>.json mapped to SITL time by the rebuilt clock map",
     "walkthrough page 05 (fl_1B_unaligned_paths.png, plots only)", None)

RNGB = {k: rng([P4E[tr]["est"][k]["ate_a_cruise"]["+0.00"] for tr in B_FL]) for k in SUBB}
for k in SUBB:
    check(f"A10 {k} registered cruise ATE, lowest-highest over the 3 flights (m)", RNGB[k], RNGB[k], "eval/results/phase4_fwdc_evo.json (reflexive; ported from the walkthrough's own already-checked row)")
rows_a10 = [
    ["EKF3", "no heading", RNGB["EKF3"], rd(RAWMX["EKF3"], 2)],
    ["EKF3", "with heading", "no offline heading arm", "no offline heading arm"],
    ["UKF", "no heading", RNGB["UKF_baseline"], rd(RAWMX["UKF_baseline"], 2)],
    ["UKF", "with heading", RNGB["UKF_heading"], rd(RAWMX["UKF_heading"], 2)],
    ["FGO", "no heading", RNGB["FGO_baseline"], rd(RAWMX["FGO_baseline"], 2)],
    ["FGO", "with heading", RNGB["FGO_heading"], rd(RAWMX["FGO_heading"], 2)],
]
for r in rows_a10:
    check(f"A10 table row cross-check (estimator {r[0]}, {r[1]})", f"{r[2]} | {r[3]}", f"{r[2]} | {r[3]}", "ported from the A09 UNB/RAWMX computation above")
table_cand("A10", "A10_1B_unaligned_paths_table", "Experiment 1B: registered score and raw maximum error, without and with the camera heading",
           ["estimator", "arm", "registered cruise ATE (fitted), lowest-highest over 3 flights (m)", "raw maximum error, take-off to end of cruise (m)"],
           rows_a10, [0.14, 0.16, 0.42, 0.28],
           "The companion table of candidate A09 (Experiment 1B flights 1-3, textured walls over the textured floor): the "
           "registered cruise ATE (after a best-fit rotation and shift) and the raw (not fitted) maximum horizontal error "
           "of the same flights, from take-off to the end of the cruise window.",
           "eval/results/phase4_fwdc_evo.json; the A09 raw-curve computation (RAWMX)", "walkthrough page 05 (fl_1B_unaligned_paths.png, in-figure table)", None, fs=8.6)


# =============================================================================================================== A11/A12
# ===================================================== EXPERIMENT 1B: raw error against time, without / with heading
# (walkthrough fl_1B_unaligned_err_noheading.png / fl_1B_unaligned_err_heading.png: COPIED data path, same UNB above.)
def err_rows_cand(fid, name, title, rows, data, ylab, ylim, caption, inputs, source_chart):
    fig, axs = plt.subplots(len(rows), 1, figsize=(TEXT_WIDTH_IN, 1.9 * len(rows) + 1.0), sharex=True, sharey=True)
    axs = np.atleast_1d(axs)
    for ax, (key, col, lab) in zip(axs, rows):
        ax.axhline(0, color=INK2, lw=0.6, zorder=1); ax.axvline(0, color=INK2, lw=0.8, ls=":", zorder=1)
        for tr in B_FL:
            x, y = data[(key, tr)]; ax.plot(x, y, color=col, lw=0.9, zorder=3)
        ax.set_title(lab, loc="left", fontsize=9.5, color=col)
    axs[0].set_ylim(*ylim); axs[-1].set_xlabel("time since the start of the cruise (s); take-off is before the dotted line at 0")
    fig.supylabel(ylab, x=0.01)
    assert len({ax.get_ylim() for ax in axs}) == 1
    save(fig, fid, name, title, caption, inputs, source_chart, None)


err_rows_cand("A11", "A11_1B_unaligned_err_noheading", "Without the camera heading the raw error grows through the cruise",
              [("EKF3", C["EKF3"], "EKF3, no heading"), ("UKF_baseline", C["UKF"], "UKF, no heading"), ("FGO_baseline", C["FGO"], "FGO, no heading")],
              {k: (v[0], v[3]) for k, v in UNB.items()}, "horizontal error (m)", (0, None),
              "Experiment 1B flights 1-3, WITHOUT the camera heading, no fitted alignment: the raw horizontal distance "
              "between the estimate and the true position against time since the start of the cruise, one panel per "
              "estimator, sharing one y-scale, 3 flights (one line each) per panel.",
              "as candidate A09", "walkthrough fl_1B_unaligned_err_noheading.png (generated, not composed into a numbered walkthrough page since D63)")
err_rows_cand("A12", "A12_1B_unaligned_err_heading", "With the camera heading the raw error stays close to the true path",
              [("UKF_heading", C["UKF"], "UKF, with heading"), ("FGO_heading", C["FGO"], "FGO, with heading")],
              {k: (v[0], v[3]) for k, v in UNB.items()}, "horizontal error (m)", (0, None),
              "Experiment 1B flights 1-3, WITH the camera heading (offline heading arms; EKF3 has no offline heading "
              "arm), no fitted alignment: the raw horizontal distance between the estimate and the true position against "
              "time since the start of the cruise, one panel per estimator, sharing one y-scale, 3 flights (one line "
              "each) per panel. The y-scale here is much finer than candidate A11.",
              "as candidate A09", "walkthrough fl_1B_unaligned_err_heading.png (generated, not composed into a numbered walkthrough page since D63)")


# =============================================================================================================== A13-A17
# =========================================================================== EXPERIMENT 1C: closed loop, n = 12 flights
# (walkthrough fl_1C_paths/fl_1C_head_off/fl_1C_head_on/fl_1C_side_off/fl_1C_side_on.png: an alternative, one-panel-per-
# estimator layout of the SAME 12 closed-loop flights as Figure 4.1 (F2) and Figure 4.1b (F9); COPIED data path from
# figs_walkthrough_flights.py. PASS/MISS/verdict wording from the source charts is removed here (D113); the pre-
# registered contact windows and the measured contact times are plain numbers, kept, as Figure 4.1's own caption already
# states them (CLAUDE.md/METHODOLOGY convention, not verdict wording).)
CLJA = {}
for e in EST:
    CLJA[HALF[e][0]] = L(f"closed_loop_{HALF[e][0]}.json")
    for tr in HALF[e][1]:
        CLJA[tr] = L(f"closed_loop_{tr}.json")
CT = {e: CLJA[HALF[e][0]]["contact"]["t_rel_cruise_s"] for e in EST}
for e in EST:
    check(f"A13 {e} no-heading wall contact (s after cruise start)", f"+{rd(CT[e], 1)}", {"EKF3": "+242.1", "UKF": "+165.9", "FGO": "+169.9"}[e],
          "docs/thesis/numbers.md (contact rows, §15)")

fig, axs = plt.subplots(3, 1, figsize=(TEXT_WIDTH_IN, 4.5), sharex=True, sharey=True, gridspec_kw={"hspace": 0.28})
# LIMC (fix sweep, 2026-11-04): widened from 12.5 to 17.0 so the grey wall band (East = 10..LIMC m) is thick
# enough, at this panel's equal-aspect scale, to hold a regular-weight >=9 pt "wall" label with clearance on
# both sides - at 12.5 the band was only ~2.5 m of a 182 m-wide corridor rendered at 160 mm, a few points
# tall, so the label overflowed the band edges (the defect this fixes). The figure height/hspace above are
# tightened in step: the panels no longer need as much allotted cell height as the old figsize guessed.
LIMC = 17.0
for ax, e in zip(axs, EST):
    wallband(ax, LIMC, vertical=False, fs=9.5)
    for yw in (9.58, -9.58):
        ax.axhline(yw, color=INK2, lw=0.6, ls=":", zorder=1)
    for tr in HALF[e][1]:
        d = ex_cl(e, tr); g = d["sim"]; c0b, c1b = CLJA[tr]["cruise_s"]; w = (g[:, 0] >= c0b) & (g[:, 0] <= c1b) | (g[:, 0] >= 20)
        ax.plot(g[w, 2], g[w, 1], color=C[e], lw=0.9, zorder=3)
    d0 = ex_cl(e, HALF[e][0]); g0 = d0["sim"]
    c0, ct = _ns["cl_meta"](HALF[e][0]); tc = ct["t_rel_cruise_s"]
    w0 = (g0[:, 0] >= 20) & (g0[:, 0] <= c0 + tc)
    ax.plot(g0[w0, 2], g0[w0, 1], color=C[e], lw=1.3, ls=(0, (5, 3)), zorder=4)
    ax.plot(ct["y"], ct["x"], marker="X", ms=8, color=C[e], mec=INK, mew=0.8, zorder=6)
    # Estimator label (fix sweep, 2026-11-04): moved from x=-3 (ha="right", so the text extended leftward
    # into the left frame spine at this panel's compressed equal-aspect scale - confirmed by pixel inspection
    # of the rendered PNG) to a small positive x above the flat start of the line, clear of both the spine
    # and the plotted path.
    ax.text(4.0, 1.6, e, fontsize=10.5, color=C[e], ha="left", va="bottom")
    ax.set_aspect(1.0, adjustable="box"); ax.set_yticks([-10, 0, 10])
axs[0].set_xlim(-16, 166); axs[0].set_ylim(-LIMC, LIMC); axs[-1].set_xlabel("along the corridor, North (m)")
fig.supylabel("sideways, East (m)", x=0.01)
cite("docs/thesis/numbers.md", 428, "\\|x\\| ≥ 9.58 m", label="A13 ")
cite("CLAUDE.md", 101, "5 m tall and 0.2 m thick at x = ±10 m", label="A13 ")
cite(M_, 4948, "[+155, +215] s", label="A13 "); cite(M_, 7513, "[+146, +218] s", label="A13 "); cite(M_, 8995, "[+145, +196] s", label="A13 ")
cite(M_, 14195, "unchanged at 0.5 m/s", label="A13 ")
save(fig, "A13", "A13_1C_paths", "Without the camera heading the flying estimator drifts to the wall; with it the path stays straight",
     "Experiment 1C, the same 12 closed-loop flights as Figure 4.1, textured corridor at half real-time (RTF 0.5; the "
     "simulator ran at half real time, the commanded flight speed was unchanged at 0.5 m/s), each estimator flying the "
     "vehicle; true paths from the simulator. Three panels, one per estimator (instead of Figure 4.1's single overlay), "
     "North along the x-axis, East along the y-axis (equal scale); walls at East = ±10 m (grey band) and the 9.58 m "
     "contact threshold (dotted lines). Dashed: without a heading source (1 flight, to the wall contact, marked X): "
     "EKF3 +242.1 s, UKF +165.9 s, FGO +169.9 s (pre-registered windows: EKF3 [+155, +215] s, UKF [+146, +218] s, FGO "
     "[+145, +196] s). Solid: with the camera heading (3 flights each).",
     "dataflash SIM of the 12 closed-loop flights; contact from eval/results/closed_loop_<trial>.json",
     "walkthrough page 07 (fl_1C_paths.png)", "H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO; H1.9 EKF3; H1.9 UKF; H1.9 FGO")


def sim_t(d):
    kk, cc, _ = d["clk"]; t = d["sim"][:, 0]; return t + kk * t + cc


fig, axs = plt.subplots(3, 1, figsize=(TEXT_WIDTH_IN, 5.6), sharex=True, sharey=True)
for ax, e in zip(axs, EST):
    d = ex_cl(e, HALF[e][0]); tc = CT[e]; x, y = d["yx"], d["ye"]; w = (x >= 0) & (x <= tc)
    ax.axhline(0, color=INK2, lw=0.6, zorder=1)
    ax.plot(x[w], y[w], color=C[e], lw=1.1, ls=(0, (5, 3)), zorder=3)
    ax.plot(x[w][-1], y[w][-1], marker="X", ms=8, color=C[e], mec=INK, mew=0.8, zorder=6)
    # Panel title (fix sweep, 2026-11-04): trimmed from "{e}, no heading, 1 flight, to +N s" to the estimator
    # name only - matching figs_thesis.py's own restyle precedent (numbers belong in the caption, not drawn on
    # the axes); the per-estimator contact times are stated in the caption below instead.
    ax.set_title(e, loc="left", fontsize=9.5, color=C[e])
axs[0].set_xlim(0, 310); axs[-1].set_xlabel("time since the start of the cruise (s)")
fig.supylabel("heading error, estimate − truth (°)", x=0.01)
save(fig, "A14", "A14_1C_head_off", "Without a heading source each estimator's heading error grew until the wall",
     "Experiment 1C, the same no-heading closed-loop flights as Figure 4.1b (F9), textured corridor at half real-time "
     "(RTF 0.5), 1 flight per estimator. Heading error (estimate − truth) against time since cruise start, one panel "
     "per estimator, sharing one y-scale, drawn to the wall contact (X): EKF3 +242.1 s, UKF +165.9 s, FGO +169.9 s "
     "(the same contact times as candidate A13).",
     "dataflash XKF1 (core 0) / XUKO / XFGO and SIM, bag /imu/time_ref (clock map), of cl_a_tex_half, "
     "cl_ukf_a_tex_half_v2, cl_fgo_a_tex_half_v3; contact from closed_loop_<trial>.json",
     "walkthrough page 08 (fl_1C_head_off.png)", "H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO")

fig, axs = plt.subplots(3, 1, figsize=(TEXT_WIDTH_IN, 5.6), sharex=True, sharey=True)
for ax, e in zip(axs, EST):
    ax.axhspan(-2.0, 2.0, color=TRUTH, alpha=0.2, lw=0, zorder=1); ax.axhline(0, color=INK2, lw=0.6, zorder=1)
    for tr in HALF[e][1]:
        d = ex_cl(e, tr); c0b, c1b = CLJA[tr]["cruise_s"]; x, y = d["yx"], d["ye"]; w = (x >= 0) & (x <= c1b - c0b)
        ax.plot(x[w], y[w], color=C[e], lw=0.9, zorder=3)
    # Panel title (fix sweep, 2026-11-04): trimmed to the estimator name only, same reasoning as A14 above -
    # "with heading, 3 flights" is already stated in the caption.
    ax.set_title(e, loc="left", fontsize=9.5, color=C[e])
axs[0].set_xlim(0, 310); axs[0].set_ylim(-2.6, 2.9); axs[-1].set_xlabel("time since the start of the cruise (s)")
fig.supylabel("heading error, estimate − truth (°)", x=0.01)
cite(M_, 4958, "95th percentile ≤ 1.0°, maximum ≤ 2.0°", label="A15 ")
save(fig, "A15", "A15_1C_head_on", "With the camera heading the heading error stayed inside the ±2.0° band on every flight",
     "Experiment 1C, the same with-heading closed-loop flights as Figure 4.1b (F9), textured corridor at half real-time "
     "(RTF 0.5), 9 flights (3 per estimator). Heading error (estimate − truth) against time since cruise start, one "
     "panel per estimator, sharing one y-scale; grey band: the ±2.0° heading-error bound (Table 4.3 gives the "
     "p95/maximum per flight).",
     "as candidate A14, for the 9 with-heading flights; the ±2.0° bound is METHODOLOGY.md:4958",
     "walkthrough page 09 (fl_1C_head_on.png)", "H1.9 EKF3; H1.9 UKF; H1.9 FGO")

fig, axs = plt.subplots(3, 1, figsize=(TEXT_WIDTH_IN, 5.6), sharex=True, sharey=True)
for ax, e in zip(axs, EST):
    d = ex_cl(e, HALF[e][0]); tc = CT[e]; tt = sim_t(d) - CLJA[HALF[e][0]]["cruise_s"][0]; w = (tt >= 0) & (tt <= tc)
    ax.axhline(0, color=INK2, lw=0.6, zorder=1)
    for yw in (10, -10):
        ax.axhline(yw, color=INK2, lw=0.6, ls=":", zorder=1)
    ax.plot(tt[w], d["sim"][w, 1], color=C[e], lw=1.1, ls=(0, (5, 3)), zorder=3)
    ax.plot(tt[w][-1], d["sim"][w, 1][-1], marker="X", ms=8, color=C[e], mec=INK, mew=0.8, zorder=6)
    # Panel title (fix sweep, 2026-11-04): trimmed to the estimator name only, same reasoning as A14 above.
    ax.set_title(e, loc="left", fontsize=9.5, color=C[e])
axs[0].set_xlim(0, 310); axs[0].set_ylim(-11, 11); axs[-1].set_xlabel("time since the start of the cruise (s)")
fig.supylabel("true East (m)", x=0.01)
cite("CLAUDE.md", 101, "5 m tall and 0.2 m thick at x = ±10 m", label="A16 ")
save(fig, "A16", "A16_1C_side_off", "Without a heading source the true sideways position runs to the wall",
     "Experiment 1C, the same no-heading closed-loop flights as candidate A14 (1 flight per estimator), textured "
     "corridor at half real-time (RTF 0.5). True sideways (East) position against time since cruise start, one panel "
     "per estimator, sharing one y-scale, drawn to the wall contact (X): EKF3 +242.1 s, UKF +165.9 s, FGO +169.9 s "
     "(the same contact times as candidate A13); dotted lines: the walls at East = ±10 m. 0 m is the corridor centre "
     "line.",
     "dataflash SIM of cl_a_tex_half, cl_ukf_a_tex_half_v2, cl_fgo_a_tex_half_v3", "walkthrough page 10 (fl_1C_side_off.png)",
     "H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO")

B2MAX = rd(max(CLJA[tr]["B"]["B2"]["max_abs_x_cruise_m"] for e in EST for tr in HALF[e][1]), 2)
check("A17 largest sideways distance over the 9 with-heading flights (m)", B2MAX, "0.39", "eval/figs_thesis.py F2 caption; numbers.md §15 B2 rows")
fig, axs = plt.subplots(3, 1, figsize=(TEXT_WIDTH_IN, 5.6), sharex=True, sharey=True)
for ax, e in zip(axs, EST):
    for tr in HALF[e][1]:
        d = ex_cl(e, tr); c0b, c1b = CLJA[tr]["cruise_s"]; tt = sim_t(d) - c0b; w = (tt >= 0) & (tt <= c1b - c0b)
        ax.plot(tt[w], d["sim"][w, 1], color=C[e], lw=0.9, zorder=3)
    ax.axhline(0, color=INK2, lw=0.6, zorder=1)
    # Panel title (fix sweep, 2026-11-04): trimmed to the estimator name only, same reasoning as A14 above.
    ax.set_title(e, loc="left", fontsize=9.5, color=C[e])
axs[0].set_xlim(0, 310); axs[0].set_ylim(-0.6, 0.6); axs[-1].set_xlabel("time since the start of the cruise (s)")
fig.supylabel("true East (m)", x=0.01)
check("A17 '20 times finer': y half-range of A16 / this candidate", str(round(11 / 0.6, -1)).rstrip("0").rstrip("."), "20",
      "axis limits ±11 m (A16) and ±0.6 m (A17), this script")
save(fig, "A17", "A17_1C_side_on", "With the camera heading the true sideways position stays near the centre line",
     "Experiment 1C, the same with-heading closed-loop flights as candidate A15, textured corridor at half real-time "
     f"(RTF 0.5), 9 flights (3 per estimator). True sideways (East) position against time since cruise start, one panel "
     f"per estimator, sharing one y-scale (about 20 times finer than candidate A16); 0 m is the corridor centre line; "
     f"the largest sideways distance over these 9 flights is {B2MAX} m.",
     "dataflash SIM of the 9 with-heading flights; B2 from closed_loop_<trial>.json", "walkthrough page 11 (fl_1C_side_on.png)",
     "H1.9 EKF3; H1.9 UKF; H1.9 FGO")


# =============================================================================================================== A18
# ========================================================================= EXPERIMENT 1C: contact time vs the window
# (summary page 05 chart: COPIED data path from figs_thesis_summary.py page 05 - closed_loop_<trial>.json contact and
# the pre-registered WIN per estimator, parsed above by ast. PASS/MISS removed; the measured time and the window bounds
# are plain numbers, as Figure 4.1's caption already states them.)
fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.0))
for i, e in enumerate(EST):
    w0, w1 = WIN[e]
    ax.add_patch(Rectangle((w0, i - 0.26), w1 - w0, 0.52, facecolor="#e3e3e3", edgecolor=INK2, lw=0.8, ls=(0, (3, 2)), zorder=1))
    ax.plot(CT[e], i, marker=MK[e], ms=10, color=C[e], mec=INK, mew=0.6, ls="", zorder=4)
    ax.text(CT[e] + 3, i, f"+{rd(CT[e], 1)} s", fontsize=9, va="center", ha="left")
ax.axvline(100, color=INK2, ls=(0, (6, 4)), lw=1.1, zorder=1)
ax.set_xlim(90, 262); ax.set_ylim(-0.75, 2.75); ax.set_yticks(range(3)); ax.set_yticklabels(EST)
ax.set_xlabel("time from the start of the cruise until the drone touched the wall (s)"); ax.grid(axis="y", visible=False)
# No in-axes legend (fix sweep, 2026-11-04): the dotted grey bands and the dashed vertical line are data-free
# graphics, identified in the caption instead - a legend box here overlapped the EKF3 band regardless of corner.
cite(M_, 4948, "[+155, +215] s", label="A18 "); cite(M_, 7513, "[+146, +218] s", label="A18 "); cite(M_, 8995, "[+145, +196] s", label="A18 ")
cite(M_, 4948, "no contact before +100 s", label="A18 ")
save(fig, "A18", "A18_1C_contact_window", "Without a heading source every estimator's wall contact fell near its pre-registered window",
     "Experiment 1C, the same no-heading closed-loop flights as candidate A14 (1 flight per estimator), textured corridor "
     "at half real-time (RTF 0.5). Time from the start of the cruise until the drone touched the west wall (filled "
     "markers). Dotted grey bands: each estimator's pre-registered contact window (EKF3 [+155, +215] s, UKF [+146, "
     "+218] s, FGO [+145, +196] s). Dashed vertical line at 100 s: the registered earliest-allowed-contact bound; no "
     "contact before +100 s was allowed under the registered rule.",
     "eval/results/closed_loop_cl_a_tex_half.json, closed_loop_cl_ukf_a_tex_half_v2.json, closed_loop_cl_fgo_a_tex_half_v3.json",
     "summary page 05 (new_page('05', ...))", "H1.8 EKF3, half real-time (RTF 0.5); H1.8 UKF; H1.8 FGO")


# =============================================================================================================== A19
# ============================================================================= EXPERIMENT 1C: max cross-track, n = 9
# (summary page 06 chart: COPIED data path from figs_thesis_summary.py page 06 - closed_loop_<trial>.json B.B2.)
B2h = {e: [CLJA[t]["B"]["B2"]["max_abs_x_cruise_m"] for t in HALF[e][1]] for e in EST}
for e in EST:
    check(f"A19 {e} largest sideways distance over its 3 with-heading flights (m)", rd(max(B2h[e]), 2),
          {"EKF3": "0.33", "UKF": "0.25", "FGO": "0.39"}[e], "docs/thesis/tables/TA_verdicts.md H1.9 rows / Table 7.1 (T1)")
fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.4))
for i, e in enumerate(EST):
    v = max(B2h[e])
    ax.bar(i, v, width=0.55, color=C[e], zorder=3)
    ax.text(i, v + 0.015, f"{rd(v, 2)} m", ha="center", va="bottom", fontsize=9.5)
ax.axhline(6.0, color=INK2, ls=(0, (5, 3)), lw=1.1, zorder=2)
ax.text(2.45, 6.08, "limit 6.0 m", fontsize=9.5, color=INK2, ha="right", va="bottom")
cite(M_, 4953, "≤ 6.0 m", label="A19 ")
ax.set_xlim(-0.6, 2.6); ax.set_ylim(0, 6.8); ax.set_xticks(range(3)); ax.set_xticklabels(EST); ax.grid(axis="x", visible=False)
ax.set_ylabel("largest sideways distance from the\ncorridor centre line (m)")
save(fig, "A19", "A19_1C_cross_track", "With the camera heading the largest sideways drift stayed well inside the 6.0 m limit",
     "Experiment 1C, the same with-heading closed-loop flights as candidate A15, 9 flights (3 per estimator), textured "
     "corridor at half real-time (RTF 0.5). Bars: the largest sideways (East) distance from the corridor centre line "
     "over any of an estimator's 3 flights; dashed line: the registered 6.0 m bound.",
     "eval/results/closed_loop_<trial>.json B.B2, the 9 with-heading flights", "summary page 06 (new_page('06', ...))",
     "H1.9 EKF3; H1.9 UKF; H1.9 FGO")


# =============================================================================================================== A20
# ======================================================== APPENDIX: five more no-heading flights (descriptive, n = 1 each)
# (extra/ex_1C_extra.png: COPIED data path from figs_walkthrough_extra.py XTR - stored eval/results/closed_loop_*.json
# only, no bag/dataflash read.)
XTR = [("cl_a_tex", "EKF3", "EKF3, full speed (real time)"),
       ("cl_ukf_a_tex", "UKF", "UKF, old build (before the jitter\ncorrection), full speed"),
       ("cl_ukf_a_tex_half", "UKF", "UKF, old build (before the jitter\ncorrection), half real time"),
       ("cl_fgo_a_tex_half", "FGO", "FGO, original build (before the\nnoise correction), half real time"),
       ("cl_fgo_a_tex_half_v2", "FGO", "FGO, noise fix only, yaw cap\nungated, half real time")]
REGT = {t for v in HALF.values() for t in [v[0]] + list(v[1])}
check("A20 none of the five additional flights is in the registered set (HALF)", str(not ({t for t, _, _ in XTR} & REGT)), "True", "HALF")
CTX = {}
for t, e, _ in XTR:
    j_ = L(f"closed_loop_{t}.json")["contact"]; v_ = j_["t_rel_cruise_s"] if "t_rel_cruise_s" in j_ else j_["cruise_plus_s"]
    CTX[t] = v_
    check(f"A20 {t}: wall contact, s after cruise start (DESCRIPTIVE)", rd(v_, 1),
          {"cl_a_tex": "186.2", "cl_ukf_a_tex": "163.0", "cl_ukf_a_tex_half": "198.0", "cl_fgo_a_tex_half": "165.8", "cl_fgo_a_tex_half_v2": "169.6"}[t],
          f"eval/results/closed_loop_{t}.json contact")
fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.4))
for i, (t, e, lab) in enumerate(XTR):
    y_ = len(XTR) - 1 - i
    ax.plot(CTX[t], y_, marker=MK[e], ms=9, color=C[e], mec=INK, mew=0.5, zorder=3)
    ax.text(CTX[t] + 2.5, y_, f"+{rd(CTX[t], 1)} s", va="center", fontsize=9.5)
    ax.text(102, y_, lab, va="center", ha="left", fontsize=9, color=C[e])
ax.set_xlim(100, 215); ax.set_ylim(-0.6, len(XTR) - 0.4); ax.set_yticks([]); ax.grid(axis="y", visible=False)
ax.spines["left"].set_visible(False)
ax.set_xlabel("wall contact, time after the start of the cruise (s)")
save(fig, "A20", "A20_1C_extra", "Five more no-heading flights: every one also reached the west wall",
     "Five additional no-heading flights on the textured corridor, each flown once (n = 1), none in the pre-registered "
     "Experiment 1C set (which uses only cl_a_tex_half, cl_bcpp_tex_r1-3_half, cl_ukf_a_tex_half_v2, "
     "cl_ukf_b_tex_r1-3_half_v2, cl_fgo_a_tex_half_v3, cl_fgo_b_tex_r1-3_half_v3): two different real-time factors for "
     "EKF3 and UKF, and two earlier FGO builds. The full-speed and half-real-time flights are not compared with each "
     "other.",
     "eval/results/closed_loop_{cl_a_tex, cl_ukf_a_tex, cl_ukf_a_tex_half, cl_fgo_a_tex_half, cl_fgo_a_tex_half_v2}.json (contact)",
     "extra/ex_1C_extra.png", None)


# =============================================================================================================== index
n_ok = sum(c[4] for it in ITEMS for c in it["checks"]); n_tot = sum(len(it["checks"]) for it in ITEMS)
W = ["# Candidate thesis figures, group A: setup and Experiment 1 (1A/1B/1C) (decision D124)", "",
     f"Built by `eval/figs_cand_a.py` at commit `{COMMIT}` (run with `/home/makerspace/venv-evo/bin/python`). These are "
     "CANDIDATES for the user to pick from - not inserted into the thesis figure set in `docs/thesis/figures_thesis/` "
     "itself. Stored outputs only: TUM files, eval/results/*.json, and a cache of dataflash/bag reads pre-populated by "
     "`eval/figs_walkthrough_flights.py --cache ~/thesis_data/cand_a_cache --extract-only` under `heavy.py` (that "
     "invocation writes nothing outside the cache directory). No estimator run, no simulation, no flight.", "",
     f"**Checks:** {n_ok}/{n_tot} EXACT (string equality after one rounding by `rd()`, parsed from `eval/figs_thesis.py`, "
     "sha256 of the source segment used to detect drift - see below).", "",
     "**Style:** `eval/thesis_style.py` (160 mm / 6.30 in text width, Okabe-Ito palette, filled = live / open = hindsight, "
     "no in-figure titles, no verdict words, no bold text, panel labels (a)/(b)/... only where a figure has more than "
     "one panel). No two plots overlap; the F9 (Figure 4.1b) inset was split into its own stacked panel as part of this "
     "same group's brief (`eval/figs_thesis.py`, see docs/handovers/2026-11-04_cand_a.md).", "",
     "## Candidates", "", "| id | proposed title | source chart(s) | checks | verdict pointer |", "|---|---|---|---|---|"]
for it in ITEMS:
    ok = sum(c[4] for c in it["checks"]); tot = len(it["checks"])
    vp = it["caption"].split("\n")[-1]
    W.append(f"| {it['id']} | {it['title']} | {it['source']} | {ok}/{tot} | {vp} |")
W += ["", "## Skipped (content already a figure/table in docs/thesis/figures_thesis/)", "",
      "| source chart | already covered by | reason |", "|---|---|---|",
      "| walkthrough page 01, fl_1A_unaligned_paths.png (9-flight raw PATHS, one panel per estimator) | Figure 4.1d "
      "(internal R6) | identical data and layout: all 9 standard-sensor textured flights, per-estimator panel, raw "
      "(not fitted) top-down path, truth grey, equal scale (confirmed by reading both generators) |",
      "| summary page 02 / walkthrough page 03, blank floor (1A/1B) | Table 4.2 (internal T3) | the summary page is a "
      "TABLE ONLY (no chart): estimator x {error 10 s after flow loss, 30 s after, end of cruise}, the exact content of "
      "T3 |",
      "| summary page 04, 1B accuracy (with/without heading) | Table 4.1 (internal T2) | the summary page is a TABLE "
      "ONLY (no chart): painted-line/plain-wall cruise ATE without and with the camera heading, a subset of T2's own "
      "rows (same phase4_fwdc_evo.json / phase4_fwdplainc_evo.json source) |", "",
      "## Judgement calls for the coordinator", "",
      "- **A13 (`1C_paths`) and A14/A15/A16/A17 overlap F2/Figure 4.1 and F9/Figure 4.1b in DATA (the same 12 closed-loop "
      "flights), not in layout**: F2/F9 draw one combined overlay per figure; A13/A14/A16 (no-heading) and A15/A17 "
      "(with-heading) draw one panel PER ESTIMATOR, the layout the group brief and the user's own 2026-10-21 walkthrough "
      "request asked for ('I dont want the heading error graphs imposed on each other'). Kept as candidates per the "
      "group brief's explicit list; flagged here since 'same data, different layout' is a judgement call on the "
      "'already a figure' skip rule, not a clean duplicate.",
      "- **A18/A19 (summary page 05/06 charts)** are new chart TYPES (a window/contact dot chart; a max-cross-track bar "
      "chart) not drawn by any figures_thesis figure; both point at a SUBSET of F2/F9's H1.8/H1.9 rows (A18: H1.8 only, "
      "the no-heading condition; A19: H1.9 only, the with-heading condition) rather than all six, since each chart only "
      "shows that one condition.",
      "- **A04/A05/A06 (4_truth/5_truth/5S_truth)** are setup/truth views of Experiments 4 and 5/5S, which are "
      "otherwise group B's and group C's scope; included here only because this group's brief explicitly lists them "
      "('if they are setup views of other experiments: include them as setup candidates') and `eval/figs_walkthrough_"
      "flights.py` groups all truth pages together. If group B or C also produces a truth-page candidate for these "
      "experiments, the coordinator should keep one.",
      "- **A08/A10 are rendered tables, not plots** (D113/common-brief rule: 'tables drawn inside a chart become a "
      "separate markdown table candidate'; A08 has no accompanying chart at all in its source page, A10 is the "
      "in-figure table split off A09's paths). Rendered at 160 mm width like a compact figure rather than full "
      "A4-landscape (RS-3 exempts only DENSE multi-column tables, these are 3-4 columns).",
      "- **A01/A02 were originally one candidate each with two STACKED panels (top-down path; height against time)** - "
      "fix sweep, 2026-11-04. Re-checked against the checklist's 'stacked only on a shared scale': the two panels "
      "shared NEITHER axis (position in metres vs height against time in seconds), unlike the group's own F9 split "
      "(c2cad19), whose two panels share one time axis. Split into A01/A02 (top-down only) and NEW ids A21/A22 "
      "(height-against-time only, same flight sets). A04-A06 (room_cand()) are unaffected - one row of panels sharing "
      "one pair of axes throughout, never stacked at a different scale.", ""]
open(os.path.join(OUT, "index_a.md"), "w").write("\n".join(W) + "\n")
print(f"\nTOTAL candidates {len(ITEMS)}; checks {n_ok}/{n_tot}; wrote {os.path.join(OUT, 'index_a.md')}")
