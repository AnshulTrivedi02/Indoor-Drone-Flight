#!/usr/bin/env python3
"""RESULTS WALKTHROUGH, ALL FLIGHTS (2026-10-21): new plots for docs/thesis/summary/results_walkthrough.pdf that show EVERY flight
of an experiment, error against time, and where the drone really flew. Composed into the walkthrough by
eval/figs_results_walkthrough.py.

User request (verbatim, 2026-10-21): "yes show the world page only once per experiment, also why do some of the plots not start
at the origin, and why are we only showing flight three? It should show the summary of all the flights in that experiment right?
Also can we have plots of the error vs time rather than the error vs distance travelled along corridor, also is it possible to
have the plot of the actual drone flying. Also for Experiment 1c I dont want the heading error graphs imposed on each other, keep
the graphs completely separate no overlap, it's ok if we go over multiple pages".

STORED OUTPUTS ONLY: trajectory .tum files, bags (packed bags are decompressed to a temporary copy in the cache directory, never
in ~/thesis_data), dataflash .BIN, eval/results json. No estimator run, no simulation.

Shared code is COPIED, not imported (importing would run those scripts and rewrite their outputs):
  - from eval/figs_thesis.py, parsed with ast and executed in a private namespace (as eval/figs_thesis_drift.py does): rd(),
    the palette, sim_path(), cl_clock(), cl_yaw_err(), cl_meta(), HALF;
  - the cruise-ATE alignment of eval/figs_thesis_results.py aligned() (= eval/three_way_eval.py);
  - the frame map (N, E) = (x, -y) and its check from eval/figs_thesis_drift.py;
  - the Experiment 4 error of eval/o_score.py and the Experiment 2 error of eval/tag_score.py (clock map, windows, tracks).
Every number printed on a figure is listed with its check in docs/thesis/summary/flights/index_flights.md (exact: rd() string
equality against the stored value or a displayed thesis value); every plotted curve has a data-identity check (its RMSE or
maximum recomputed from exactly the plotted samples equals the stored scored value).

Outputs: docs/thesis/summary/flights/fl_<id>.png, docs/thesis/summary/flights/index_flights.md, flights/checks.json.
Usage: /home/makerspace/venv-evo/bin/python eval/figs_walkthrough_flights.py [--cache DIR] [--extract-only]"""
import ast, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile, textwrap
sys.path.insert(0, os.path.expanduser("~/.cache/thesis_pyshim"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUTD = os.path.join(ROOT, "docs", "thesis", "summary", "flights"); os.makedirs(OUTD, exist_ok=True)
INDEX = os.path.join(OUTD, "index_flights.md")
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
args = sys.argv[1:]
CACHE = args[args.index("--cache") + 1] if "--cache" in args else os.path.join(tempfile.gettempdir(), "figs_walkthrough_flights_cache")
os.makedirs(CACHE, exist_ok=True)
tempfile.tempdir = CACHE            # cl_clock() decompresses PACKED bags with mkdtemp(): keep those copies in the cache directory

# ------------------------------------------------------------- shared code from figs_thesis.py, parsed, NOT executed as a script
FT = os.path.join(HERE, "figs_thesis.py"); _src = open(FT).read(); _tree = ast.parse(_src)
_WANT_F = {"rd", "rng", "sim_path", "cl_clock", "cl_yaw_err", "cl_meta"}
_WANT_A = {"C", "MK", "TRUTH", "EST", "INK", "INK2", "GRID", "SURF", "WALL", "L", "_TSF9", "_sim", "HALF", "WIN"}
_nodes, _fsrc = [], {}
for n in _tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in _WANT_F:
        _nodes.append(n); _fsrc[n.name] = ast.get_source_segment(_src, n)
    elif isinstance(n, ast.Assign):
        names = {t.id for t in n.targets if isinstance(t, ast.Name)} | \
                {e.id for t in n.targets if isinstance(t, ast.Tuple) for e in t.elts if isinstance(e, ast.Name)}
        if names & _WANT_A:
            _nodes.append(n)
_ns = {"np": np, "plt": plt, "math": math, "os": os, "json": json, "subprocess": subprocess, "mavutil": mavutil, "Reader": Reader,
       "get_typestore": get_typestore, "Stores": Stores, "TD": TD, "RES": RES}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), FT, "exec"), _ns)
rd, rng, L = _ns["rd"], _ns["rng"], _ns["L"]
C, TRUTH, EST, INK, INK2, GRID, WALL = (_ns[k] for k in ("C", "TRUTH", "EST", "INK", "INK2", "GRID", "WALL"))
HALF, CLWIN = _ns["HALF"], _ns["WIN"]
SRC_SHA = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in _fsrc.items()}
assert C == {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"} and TRUTH == "#999999", "palette changed in figs_thesis.py"
_orig_clock = _ns["cl_clock"]; _clk = {}


def _cl_clock_memo(tr):
    if tr not in _clk:
        _clk[tr] = _orig_clock(tr)
    return _clk[tr]


_ns["cl_clock"] = _cl_clock_memo        # cl_yaw_err() looks cl_clock up in this namespace: one bag read per flight


def cached(key, fn):
    """Cache of values READ from stored flight records (npz in the cache directory); the cache never holds a computed result."""
    p = os.path.join(CACHE, key + ".npz")
    if os.path.exists(p):
        z = np.load(p, allow_pickle=True); return {k: z[k] for k in z.files}
    d = fn(); np.savez(p, **d); return d


# ------------------------------------------------------------- extraction (per flight)
CL_ALL = [(e, tr, k) for e in EST for k, tr in enumerate([HALF[e][0]] + HALF[e][1])]     # k = 0: no heading; 1-3: with heading


def ex_cl(est, tr):
    def f():
        x, e, dc = _ns["cl_yaw_err"](tr, est)
        g = _ns["sim_path"](tr); kk, cc, off = _ns["cl_clock"](tr)
        return dict(yx=x, ye=e, dclk=np.array(dc), sim=g, clk=np.array([kk, cc, off]))
    return cached(f"cl_{tr}", f)


def _bag_open(tr):
    """Return (bag dir, temp dir or None). PACKED bags: decompress a temporary copy into the cache directory (read only)."""
    bag = f"{TD}/{tr}/bag"
    if not os.path.exists(f"{bag}/bag_0.db3") and os.path.exists(f"{bag}/bag_0.db3.zst"):
        tmp = tempfile.mkdtemp(prefix="wt_bag_"); shutil.copy(f"{bag}/metadata.yaml", tmp)
        subprocess.run(["zstd", "-q", "-d", f"{bag}/bag_0.db3.zst", "-o", f"{tmp}/bag_0.db3"], check=True)
        return tmp, tmp
    return bag, None


def ex_room(tr):
    """Experiments 2-4: bag ground truth (t, x E, y N, yaw) and /imu/time_ref, dataflash XKF1 core 0 (TimeUS s, PE, PN, Yaw):
    the inputs of eval/tag_score.py and eval/o_score.py, read the same way."""
    def f():
        ts = get_typestore(Stores.ROS2_JAZZY); G, TR = [], []
        bag, tmp = _bag_open(tr)
        try:
            with Reader(bag) as r:
                cs = {c.topic: c for c in r.connections}
                for con, _, raw in r.messages(connections=[cs[x] for x in ("/ground_truth/pose", "/imu/time_ref") if x in cs]):
                    m = ts.deserialize_cdr(raw, con.msgtype)
                    if con.topic == "/imu/time_ref":
                        TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)); continue
                    q = m.pose.orientation
                    G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y,
                              math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))))
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
        mv = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); k1 = []
        while True:
            r = mv.recv_match(type=["XKF1"])
            if r is None:
                break
            if r.C == 0:
                k1.append((r.TimeUS / 1e6, r.PE, r.PN, r.Yaw))
        return dict(G=np.array(G), TR=np.array(TR), K1=np.array(k1))
    return cached(f"room_{tr}", f)


def ex_sim(tr):
    return cached(f"sim_{tr}", lambda: dict(sim=_ns["sim_path"](tr)))


def ex_xkf1(tr):
    """v3 (2026-10-31): EKF3's own logged position, dataflash XKF1 core 0 (TimeUS s, PN, PE), for the closed-loop EKF3 panel of the
    1B raw paths figure (the drone flew on this estimate)."""
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


T_FL = [f"T_{c}_r{i}" for c in "ABCD" for i in (1, 2, 3)]
O_FL = ["O_r1", "O_r2", "O_r3b"]
H_FL = ["H_s1_r1", "H_s1_r2", "H_s1_r3", "H_s1far_r1", "H_s1far_r2", "H_s1far_r3b"] + [f"H_s2v2_r{i}" for i in (1, 2, 3)] + \
       [f"H_s3v2_r{i}" for i in (1, 2, 3)]
S_FL = ["H_safety_ukf_a_v3", "H_safety_ukf_b_v3", "H_safety_fgo_a_v4", "H_safety_fgo_b_v4"]

if "--extract-only" in args:
    import concurrent.futures as cf
    jobs = [("cl", e, tr) for e, tr, _ in CL_ALL] + [("room", None, t) for t in T_FL + O_FL] + [("sim", None, t) for t in H_FL + S_FL] + \
           [("xkf1", None, t) for t in _ns["HALF"]["EKF3"][1]]
    def run(j):
        kind, e, tr = j
        try:
            (ex_cl(e, tr) if kind == "cl" else ex_room(tr) if kind == "room" else ex_xkf1(tr) if kind == "xkf1" else ex_sim(tr)); return f"ok {tr}"
        except Exception as x:          # reported, not hidden
            return f"FAILED {tr}: {x!r}"
    with cf.ProcessPoolExecutor(max_workers=6) as pool:
        for s in pool.map(run, jobs):
            print(s, flush=True)
    sys.exit(0)

# =============================================================================================== checks and figure registry
NUMS = open(os.path.join(ROOT, "docs", "thesis", "numbers.md")).read().split("\n")
CHK = []; FIGS = {}; DATAID = []


def norm(s):
    return s.replace("**", "").replace("`", "").replace("\\|", "|")


def check(fig, label, computed, expected, src, line=None, inline_str=None):
    """EXACT string equality; with `line` (numbers.md line number) the expected string (or `inline_str`) must also occur in that
    line, so a typing slip cannot pass."""
    inline = True if line is None else norm(str(inline_str or expected)) in norm(NUMS[line - 1])
    ok = str(computed) == str(expected) and inline
    CHK.append(dict(fig=fig, label=label, computed=str(computed), expected=str(expected), src=src + (f":{line}" if line else ""), ok=ok))
    if not ok:
        print("   CHECK FAIL:", fig, label, computed, expected, "" if inline else "NOT IN LINE")
    return ok


EXCL = []      # (figure, flight, arm, yaw-only RMS 2 dp, stored 2 dp): reported, not drawn


def yaw_ok(fig, tr, key, rmse_y, st, src):
    if rd(rmse_y, 2) == rd(st, 2):
        dataid(fig, f"{tr} {key}: PLOTTED yaw-only aligned error, RMS vs stored cruise ATE (displayed precision, 2 dp)", rd(rmse_y, 2), rd(st, 2), src)
        return True
    # Drawn anyway (user ruling 2026-10-21): the yaw-only and SE(3) fits differ by millimetres when the true path is not exactly
    # straight; a difference under 0.005 m is a fit-precision effect, not a data mismatch. Reported in the index.
    ok = abs(rmse_y - st) < 0.005
    EXCL.append((fig, tr, key, rd(rmse_y, 2), rd(st, 2), rmse_y, st)); print(f"   DRAWN, last digit differs: {fig} {tr} {key} yaw-only {rmse_y:.6f} vs stored {st:.6f}")
    dataid(fig, f"{tr} {key}: PLOTTED yaw-only aligned error, RMS within 0.005 m of the stored cruise ATE", str(ok), "True", src)
    return True


def dataid(fig, label, computed, expected, src):
    ok = str(computed) == str(expected)
    DATAID.append(dict(fig=fig, label=label, computed=str(computed), expected=str(expected), src=src, ok=ok))
    if not ok:
        print("   DATA-ID FAIL:", fig, label, computed, expected)
    return ok


plt.rcParams.update({"font.size": 10.5, "axes.titlesize": 10.5, "axes.labelsize": 10.5, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
                     "legend.fontsize": 9.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "pdf.fonttype": 42})
FW, FH = 10.9, 5.0          # figure size (in) = the walkthrough's plot box; drawn at 200 dpi
LW_FL = 0.9                 # one thin line per flight


def save(fid, fig, title, inputs, numbers, tag=None, key=False):
    """numbers: every number printed on the figure (strings); each is the subject of a check() row of this figure.
    tag: the raw / fitted tag drawn ON the figure (v3, 2026-10-31), or None if the composer draws it; key: the figure carries the
    'filled = live, open = hindsight' corner key. Global checks on every figure (v3): no em-dash in any text artist, every axis
    linear, every text inside the figure."""
    fig.set_dpi(200); fig.canvas.draw(); r_ = fig.canvas.get_renderer(); W_, H_ = fig.bbox.width, fig.bbox.height   # measured at the saved dpi
    ticks_ = {id(t) for a_ in fig.axes for t in a_.get_xticklabels() + a_.get_yticklabels()}     # off-range ticks are never drawn
    for t_ in fig.findobj(matplotlib.text.Text):
        s_ = t_.get_text()
        if s_ and t_.get_visible():
            assert "—" not in s_, f"{fid}: em-dash in figure text {s_[:60]!r}"
            if id(t_) in ticks_:
                continue
            b_ = t_.get_window_extent(renderer=r_)
            assert b_.x0 >= -1 and b_.x1 <= W_ + 1 and b_.y0 >= -1 and b_.y1 <= H_ + 1, f"{fid}: text runs off the figure: {s_[:50]!r}"
    for a_ in fig.axes:
        assert a_.get_xscale() == "linear" and a_.get_yscale() == "linear", f"{fid}: a non-linear axis"
    p = os.path.join(OUTD, f"fl_{fid}.png"); fig.savefig(p, dpi=200); plt.close(fig)
    FIGS[fid] = dict(file=os.path.relpath(p, ROOT), title=title, inputs=inputs, numbers=[str(n) for n in numbers], tag=tag, key=key)
    print(f"wrote fl_{fid}.png")


# ---- v3 visual language (user request 2026-10-31, "SELF-EXPLANATORY PLOTS"): one-line finding title, the raw / fitted tag and the
# live / hindsight key on the figure itself, walls as a labelled medium-grey band beyond +-10 m, limits grey and labelled.
WALLC = "#bdbdbd"          # medium grey wall band
KEY_LH = "filled = live (during flight), open = hindsight (after landing)"


def title1(fig, text, x=0.01, y=0.985, fs=12.5):
    """The figure's one-line finding title; asserted to fit on one line inside the figure."""
    assert "\n" not in text
    while True:                         # shrink the font (not below 11 pt) until the one line fits
        t_ = fig.text(x, y, text, fontsize=fs, weight="bold", ha="left", va="top")
        fig.canvas.draw(); bb = t_.get_window_extent(renderer=fig.canvas.get_renderer())
        if bb.x1 <= fig.bbox.x1 * 0.97:          # 3% margin: text measured at 100 dpi runs slightly wider at the saved 200 dpi
            return t_
        t_.remove(); fs -= 0.5
        assert fs >= 11, f"title does not fit on one line: {text}"


def corner(fig, tag, key=None, y=0.925):
    """Raw / fitted tag (right) and, where used, the filled / open key (left of it), in small grey boxes below the title."""
    fig.text(0.99, y, tag, fontsize=9.5, ha="right", va="top", color=INK, bbox=dict(boxstyle="round,pad=0.3", fc="#f2f2f2", ec="#bbbbbb", lw=0.6))
    if key:
        fig.text(0.01, y, key, fontsize=9.5, ha="left", va="top", color=INK, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bbbbbb", lw=0.6))


def wallband(ax, lim, vertical=True, label=True, fs=9):
    """Shade everything beyond +-10 m East as the wall (medium grey), labelled 'wall'."""
    for s in (1, -1):
        if vertical:
            ax.axvspan(10 * s, lim * s, color=WALLC, lw=0, zorder=0.5)
        else:
            ax.axhspan(10 * s, lim * s, color=WALLC, lw=0, zorder=0.5)
    if label:
        for s in (1, -1):
            c_ = (10 + lim) / 2 * s
            if vertical:
                ax.text(c_, 0.5, "wall", transform=ax.get_xaxis_transform(), rotation=90, ha="center", va="center", fontsize=fs, color=INK2)
            else:
                ax.text(0.5, c_, "wall", transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=fs, color=INK2)


def measured_stretch(fig, ax):
    fig.canvas.draw()
    bb = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted()); x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    return (bb.height / (y1 - y0)) / (bb.width / (x1 - x0))


def walls(ax, horiz=True):
    for yw in (10, -10):
        (ax.axhspan if horiz else ax.axvspan)(yw - 0.1, yw + 0.1, color=WALL, lw=0)


def head(fig, title, note=None, left=0.07):
    fig.suptitle(title, x=left, ha="left", fontsize=11.5, weight="bold", y=0.995)
    if note:
        t_ = fig.text(left, 0.935, note, fontsize=9.5, color=INK2)
        bb_ = t_.get_window_extent(renderer=fig.canvas.get_renderer())
        assert bb_.x1 <= fig.bbox.x1 - 2, f"note runs off the figure: {note[:60]}"


# =============================================================================================== evo: cruise-ATE alignment (copied)
from evo.core import sync, metrics
from evo.core.trajectory import PoseTrajectory3D


def tum_traj(a):
    return PoseTrajectory3D(positions_xyz=a[:, 1:4], orientations_quat_wxyz=a[:, [7, 4, 5, 6]], timestamps=a[:, 0])


def aligned(trial, sub, f, win):
    """COPIED from eval/figs_thesis_results.py aligned() (= eval/three_way_eval.py): crop both TUMs to the stored cruise window,
    associate (0.05 s), Umeyama SE(3) without scale (evo -a), translation RMSE. Returns (t, aligned est xyz, ref xyz, rmse)."""
    ref = np.loadtxt(f"{TD}/{trial}/{sub}/ground_truth.tum"); est = np.loadtxt(f"{TD}/{trial}/{sub}/{f}")
    c = lambda a: a[(a[:, 0] >= win[0]) & (a[:, 0] <= win[1])]
    r, e = sync.associate_trajectories(tum_traj(c(ref)), tum_traj(c(est)), 0.05)
    e.align(r, correct_scale=False)
    m = metrics.APE(metrics.PoseRelation.translation_part); m.process_data((r, e))
    rmse_se3 = m.get_statistic(metrics.StatisticsType.rmse)
    # YAW-ONLY placement (coordinator finding 2026-10-21): the SE(3) fit is degenerate about the corridor axis (truth is a near-
    # straight line), so evo may roll the sideways error into the vertical. For DRAWING, the same associated samples (before the
    # SE(3) fit) are aligned by a rotation about the vertical axis plus a 3-D shift (least squares). Both TUMs of a pair share the
    # vertical axis (EKF3: NED and NED; UKF/FGO: take-off frame z up and ENU z up), so a rotation about z is the right family.
    r2, e2 = sync.associate_trajectories(tum_traj(c(ref)), tum_traj(c(est)), 0.05)
    P, Q = e2.positions_xyz, r2.positions_xyz; pm, qm = P.mean(0), Q.mean(0); Pc, Qc = P - pm, Q - qm
    th = math.atan2((Pc[:, 0] * Qc[:, 1] - Pc[:, 1] * Qc[:, 0]).sum(), (Pc[:, 0] * Qc[:, 0] + Pc[:, 1] * Qc[:, 1]).sum())
    Rz = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    Y = Pc @ Rz.T + qm
    rmse_yaw = float(np.sqrt(np.mean(np.sum((Y - Q) ** 2, 1))))
    return e2.timestamps, Y, Q, rmse_se3, rmse_yaw


def NE(key, xyz):
    """(North, East) of an ALIGNED path: EKF3's TUMs are (N, E, D); the UKF/FGO TUMs are ENU (E, N, U) (figs_thesis_results.py)."""
    return (xyz[:, 0], xyz[:, 1]) if key.startswith("EKF3") else (xyz[:, 1], xyz[:, 0])


def to_NE(key, a, truth):
    """UNALIGNED (t, North, East), COPIED from eval/figs_thesis_drift.py: EKF3 and its truth (N, E, D); UKF/FGO truth ENU;
    UKF/FGO estimates own frame, x = take-off heading (North), y = West -> (N, E) = (x, -y)."""
    if key.startswith("EKF3"):
        return a[:, 0], a[:, 1], a[:, 2]
    if truth:
        return a[:, 0], a[:, 2], a[:, 1]
    return a[:, 0], a[:, 1], -a[:, 2]


HEAD_TOL_DEG = 10.0     # see frame_ok()


def frame_ok(est, gt, win):
    """The frame check of eval/figs_thesis_drift.py: take-off |NE| < 0.05 m (estimate and truth) and the heading of the first 5 m of
    true cruise travel close to truth's. R5 (one flight) used 2.0 deg; over all 9 flights the UKF and FGO of flights 2 and 6 show a
    genuine early heading error of 2.7-3.5 deg (their known different yaw behaviour on those two flights), so the tolerance here is
    HEAD_TOL_DEG = 10 deg: still far below the >= 90 deg that any axis swap or sign error of the relabel would give. Both counts
    (at 2.0 deg and at 10 deg) are reported in the index."""
    (te, ne, ee), (tg, ng, eg) = est, gt
    o_e = math.hypot(ne[0], ee[0]); o_g = math.hypot(ng[0], eg[0])
    i0 = np.searchsorted(tg, win[0]); j0 = i0 + np.argmax(ng[i0:] - ng[i0] >= 5.0); ta, tb = tg[i0], tg[j0]
    h_g = math.degrees(math.atan2(eg[j0] - eg[i0], ng[j0] - ng[i0]))
    h_e = math.degrees(math.atan2(np.interp(tb, te, ee) - np.interp(ta, te, ee), np.interp(tb, te, ne) - np.interp(ta, te, ne)))
    return o_e < 0.05 and o_g < 0.05 and abs(h_e - h_g) < HEAD_TOL_DEG, (o_e, o_g, h_e, h_g)


# =============================================================================================== shared figure builders
def truth_page(fid, trials, gt_of, title, win_of, n_txt, inputs, numbers, xlim=(-6, 166)):
    """'Where the drone really flew' (corridor): true paths top-down at equal scale (walls drawn) and true height against time."""
    fig = plt.figure(figsize=(FW, FH)); gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.25], hspace=0.6)
    ax = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1])
    walls(ax)
    for tr in trials:
        tg, E_, N_, U_ = gt_of(tr)
        ax.plot(N_, E_, color=TRUTH, lw=LW_FL)
        ax2.plot(tg - win_of(tr)[0], U_, color=TRUTH, lw=LW_FL)
    ax.set_xlim(*xlim); ax.set_ylim(-11, 11); ax.set_aspect(1.0, adjustable="box"); ax.set_yticks([-10, 0, 10])
    ax.set_xlabel("North, along the corridor (m)"); ax.set_ylabel("East (m)")
    ax.set_title(f"Seen from above, equal scale (no stretch; dark bands: the walls): {n_txt}", loc="left")
    ax2.axvline(0, color=INK2, lw=0.8, ls=":"); ax2.set_xlabel("time since the start of the cruise (s)"); ax2.set_ylabel("height (m)")
    ax2.set_title("Height against time: take-off, climb, the cruise (from the dotted line at 0 s), stop and landing", loc="left")
    ax2.set_ylim(0, None)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.9, bottom=0.11)
    s = measured_stretch(fig, ax)
    check(fid, "top-down panel drawn at equal scale (measured stretch)", rd(s, 1), "1.0", "set_aspect(1.0) of the top panel")
    head(fig, title)
    save(fid, fig, title, inputs, numbers)


def stacked_paths(fid, panels, data, lat, title, note, stretch=3.0):
    """One column per arm, North up, shared axes, sideways (East) axis stretched; every flight a thin line in the arm's colour;
    truth grey."""
    fig, axs = plt.subplots(1, len(panels), figsize=(FW, FH), sharex=True, sharey=True)
    axs = np.atleast_1d(axs)
    for ax, (key, col, ptitle, ls) in zip(axs, panels):
        for (k2, tr), v in data.items():
            if k2 == key:
                ax.plot(v[2][1], v[2][0], color=TRUTH, lw=2.2, zorder=2, solid_capstyle="round")
        for (k2, tr), v in data.items():
            if k2 == key:
                ax.plot(v[1][1], v[1][0], color=col, lw=LW_FL, ls=ls, zorder=3)
        ax.set_title(ptitle, loc="left", pad=4); ax.set_xlabel("East (m)")
        ax.set_aspect(1.0 / stretch, adjustable="box")
    axs[0].set_ylim(-2, 162); axs[0].set_xlim(-lat, lat)
    axs[0].set_ylabel("North, along the corridor (m)")
    nl = max(p_[2].count("\n") for p_ in panels)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.85 - 0.045 * nl, bottom=0.11, wspace=0.15)
    s = 1.0 / measured_stretch(fig, axs[0])        # width per East metre / height per North metre
    check(fid, "sideways (East) stretch printed on the figure vs drawn axes geometry", rd(s, 1), rd(stretch, 1), f"set_aspect(1/{stretch:g})")
    head(fig, title, note.format(s=rd(s, 1)))
    return fig


def err_rows(rows, data, title, ylab, xlab, ylim=None, xlim=None, band=None, marks=None, note=None, vline=None):
    """One row per arm, shared x and y; every flight a thin line in the arm's colour."""
    fig, axs = plt.subplots(len(rows), 1, figsize=(FW, FH), sharex=True, sharey=True)
    axs = np.atleast_1d(axs)
    for ax, (key, col, ptitle, ls) in zip(axs, rows):
        if band is not None:
            ax.axhspan(-band, band, color=TRUTH, alpha=0.2, lw=0, zorder=1)
        ax.axhline(0, color=INK2, lw=0.6, zorder=1)
        if vline is not None:
            ax.axvline(vline, color=INK2, lw=0.8, ls=":", zorder=1)
        for (k2, tr), (x, y) in data.items():
            if k2 == key:
                ax.plot(x, y, color=col, lw=LW_FL, ls=ls, zorder=3)
        for (k2, xm, ym, txt) in (marks or []):
            if k2 == key:
                ax.plot(xm, ym, marker="X", ms=9, color=col, mec=INK, mew=0.9, zorder=6, ls="")
                ax.annotate(txt, (xm, ym), xytext=(-10, 0), textcoords="offset points", ha="right", va="center", fontsize=9.5)
        ax.set_title(ptitle, loc="left", pad=3); ax.set_ylabel(ylab)
    if ylim:
        axs[0].set_ylim(*ylim)
    if xlim:
        axs[0].set_xlim(*xlim)
    axs[-1].set_xlabel(xlab)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.88 if note else 0.92, bottom=0.1, hspace=0.5)
    head(fig, title, note, left=0.08)
    lims = [ax.get_ylim() for ax in axs]
    assert all(l == lims[0] for l in lims), "rows do not share the y-scale"
    return fig


# =============================================================================================== EXPERIMENT 1A: standard sensors, n = 9
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
EVSRC = lambda tr: "rerun_dsn_evo.json" if tr in L("rerun_dsn_evo.json")["trials"] else "dsn_extra_evo.json"
A_FL = [f"dsn_tex_r{i}" for i in range(1, 10)]
SUB1 = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF": ("ukf", "ukf_traj.tum"), "FGO": ("fgo", "fgo_traj.tum")}
check("1A", "flights shown: the usable standard-sensor textured flights ('all 9 usable dsn_tex flights')", f"all {len(A_FL)} usable", "all 9 usable",
      "docs/thesis/numbers.md", 230)
def unaligned(key, tr, sub, f, win):
    """UNALIGNED (not fitted) path and horizontal error of one flight-arm, from take-off to the end of the cruise window; the
    frame map of eval/figs_thesis_drift.py (to_NE) and its frame check. Shared by the 1A and 1B not-fitted pages."""
    a = np.loadtxt(f"{TD}/{tr}/{sub}/{f}"); g = np.loadtxt(f"{TD}/{tr}/{sub}/ground_truth.tum")
    est_, gt_ = to_NE(key, a, False), to_NE(key, g, True)
    ok, diag = frame_ok(est_, gt_, win)
    te, ne, ee = est_; tg, ng, eg = gt_
    k = (te >= tg[0]) & (te <= win[1])
    return (ok,) + diag, (te[k] - win[0], ne[k], ee[k], np.hypot(ne[k] - np.interp(te[k], tg, ng), ee[k] - np.interp(te[k], tg, eg)), gt_)


med = {}; AL1 = {}; UN1 = {}; FR = []; YAWD = []
for e in EST:
    for tr in A_FL:
        win = ev[tr]["window_s"]; st = ev[tr]["est"][e]["ate_a_cruise"]["+0.00"]
        t, xyz, ref, rmse, rmse_y = aligned(tr, *SUB1[e], win)
        dataid("1A", f"{tr} {e}: same samples, standard SE(3) cruise ATE recomputed vs stored (6 dp)", rd(rmse, 6), rd(st, 6),
               f"eval/results/{EVSRC(tr)}:{tr}.est.{e}.ate_a_cruise")
        YAWD.append((tr, e, rmse_y - rmse))
        if yaw_ok("1A", tr, e, rmse_y, st, f"eval/results/{EVSRC(tr)}:{tr}.est.{e}.ate_a_cruise"):
            AL1[(e, tr)] = (t - win[0], NE(e, xyz), NE(e, ref), np.linalg.norm(xyz - ref, axis=1))
        fr_, UN1[(e, tr)] = unaligned(e, tr, *SUB1[e], win); FR.append((tr, e) + fr_)
    med[e] = rd(float(np.median([ev[tr]["est"][e]["ate_a_cruise"]["+0.00"] for tr in A_FL])), 2)
for e in EST:
    check("1A", f"{e} median cruise ATE over the 9 flights (m), printed in the panel title", med[e], {"EKF3": "4.10", "UKF": "5.13", "FGO": "4.46"}[e],
          "docs/thesis/numbers.md", 236, inline_str=f"{e} {med[e]}")
if not all(f[2] for f in FR):
    sys.exit("FRAME CHECK FAILED on " + str([f for f in FR if not f[2]]))
dataid("1A", f"frame check (rule of eval/figs_thesis_drift.py, heading tolerance {HEAD_TOL_DEG:g} deg) on every flight and estimator",
       f"{sum(f[2] for f in FR)}/{len(FR)}", "27/27", "this script")
FRAME_NOTE = (f"at R5's 2.0 deg tolerance {sum(abs(f[5] - f[6]) < 2.0 for f in FR)}/{len(FR)} pass; the others "
              + ", ".join(f"{f[0]} {f[1]} {f[5] - f[6]:+.2f} deg" for f in FR if abs(f[5] - f[6]) >= 2.0))


def gt_enu(sub):
    def f(tr):
        g = np.loadtxt(f"{TD}/{tr}/{sub}/ground_truth.tum"); return g[:, 0], g[:, 1], g[:, 2], g[:, 3]
    return f


truth_page("1A_truth", A_FL, gt_enu("ukf"), "All 9 flights flew the same straight line up the corridor (simulator truth)", lambda tr: ev[tr]["window_s"],
           "n = 9 flights, one grey line each (they lie on top of each other)", "~/thesis_data/trials/dsn_tex_r1..r9/ukf/ground_truth.tum (ENU)",
           ["9", "1.0", "0"])
# v3 (2026-10-31, user: "The fitted (ATE) path and error-against-time plots are removed, but the fitted ATE numbers must still appear
# as text or in a table"): the 1A fitted paths and fitted error figures are no longer drawn. The SE(3) cruise-ATE recomputation and the
# yaw-only rows above stay: they back the registered-score table printed on the raw paths figure.
TABN = {e: (len(A_FL), med[e]) for e in EST}


def paths_raw(ax, UN, key, trs, win_of, col, lim, ls="-"):
    """Raw (not fitted) estimated paths from take-off to the end of the cruise, truth grey, take-off black dot, walls as bands."""
    wallband(ax, lim)
    for tr in trs:
        tg, ng, eg = UN[(key, tr)][4]; w = tg <= win_of(tr)[1]
        ax.plot(eg[w], ng[w], color=TRUTH, lw=2.2, zorder=2)
    for tr in trs:
        ax.plot(UN[(key, tr)][2], UN[(key, tr)][1], color=col, lw=LW_FL, ls=ls, zorder=3)
    ax.plot(0, 0, marker="o", ms=5, color=INK, zorder=5)
    ax.set_aspect(1.0, adjustable="box")


LIM1 = max(abs(min(v[2].min() for v in UN1.values())), abs(max(v[2].max() for v in UN1.values())), 10.0) + 4.0
fig = plt.figure(figsize=(FW, FH))
gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.3], wspace=0.12)
axs = [fig.add_subplot(gs[0, i]) for i in range(3)]
for ax in axs[1:]:
    ax.sharex(axs[0]); ax.sharey(axs[0])
for ax, e in zip(axs, EST):
    paths_raw(ax, UN1, e, A_FL, lambda tr: ev[tr]["window_s"], C[e], LIM1)
    ax.set_title(f"{e}, 9 flights", loc="left", color=C[e], weight="bold")
    ax.set_xlabel("sideways, East (m)")
for ax in axs[1:]:
    plt.setp(ax.get_yticklabels(), visible=False)
axs[0].set_ylabel("along the corridor, North (m)")
axs[0].set_xlim(-LIM1, LIM1); axs[0].set_ylim(-3, 163)
at = fig.add_subplot(gs[0, 3]); at.axis("off")
at.text(0.0, 0.99, "grey line: true path\nblack dot: take-off", fontsize=9, color=INK2, va="top", transform=at.transAxes)
at.text(0.0, 0.85, "Registered score (fitted):\ncruise ATE, median of\nExperiment 1A flights 1-9\n(textured floor)", fontsize=10.5, weight="bold", va="top", transform=at.transAxes)
for i, e in enumerate(EST):
    at.text(0.04, 0.62 - 0.09 * i, e, fontsize=11, color=C[e], weight="bold", va="center", transform=at.transAxes)
    at.text(0.55, 0.62 - 0.09 * i, f"{TABN[e][1]} m", fontsize=11, va="center", ha="left", transform=at.transAxes)
at.text(0.0, 0.31, "Ranking rule\n(EKF3 against FGO):\nNOT MET, no\nestimator ranked", fontsize=10.5, va="top", transform=at.transAxes,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#888888", lw=0.8))
at.text(0.0, 0.09, "Paths: raw. Score: after a\nbest-fit turn and shift\nof each cruise.", fontsize=9, color=INK2, va="top",
        transform=at.transAxes)
fig.subplots_adjust(left=0.06, right=0.99, top=0.83, bottom=0.11)
s = measured_stretch(fig, axs[0]); check("1A_unaligned_paths", "equal scale (measured stretch)", rd(s, 1), "1.0", "set_aspect(1.0)")
check("1A_unaligned_paths", "x-axis symmetric about 0 (left and right limits, m)", f"{-axs[0].get_xlim()[0]:.6f}", f"{axs[0].get_xlim()[1]:.6f}", "set_xlim(-LIM1, LIM1)")
for e in EST:
    check("1A_unaligned_paths", f"{e} registered cruise ATE, median of 9 flights (m), printed in the table", TABN[e][1],
          {"EKF3": "4.10", "UKF": "5.13", "FGO": "4.46"}[e], "docs/thesis/numbers.md", 236, inline_str=f"{e} {TABN[e][1]}")
check("1A_unaligned_paths", "ranking verdict printed: NOT MET (summary page 01 Result)", "NOT MET", "NOT MET",
      "docs/thesis/summary/index_summary.md page 01 Result ('NOT MET: on the further flights ...')")
title1(fig, "Without a heading source every estimate drifts sideways off the true path, on all 9 flights")
corner(fig, "raw, nothing fitted (paths)")
save("1A_unaligned_paths", fig, "", "TUMs of dsn_tex_r1..r9; frame map (N, E) = (x, −y) for the UKF/FGO (eval/figs_thesis_drift.py); "
     "cruise ATEs rerun_dsn_evo.json, dsn_extra_evo.json", ["9", "1", "1.0"] + [med[e] for e in EST], tag="raw, nothing fitted (paths)")
fig, axs = plt.subplots(3, 1, figsize=(FW, FH), sharex=True, sharey=True)
for ax, e in zip(axs, EST):
    ax.axhline(0, color=INK2, lw=0.6, zorder=1); ax.axvline(0, color=INK2, lw=0.8, ls=":", zorder=1)
    for tr in A_FL:
        v = UN1[(e, tr)]; ax.plot(v[0], v[3], color=C[e], lw=LW_FL, zorder=3)
    ax.text(0.005, 0.93, f"{e}, 9 flights", transform=ax.transAxes, color=C[e], weight="bold", fontsize=10.5, va="top")
axs[0].set_ylim(0, None); axs[-1].set_xlabel("time since the start of the cruise (s); take-off is before the dotted line at 0")
fig.supylabel("horizontal error (m)", x=0.012, fontsize=10.5)
fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.11, hspace=0.25)
assert len({ax.get_ylim() for ax in axs}) == 1
title1(fig, "Without a heading source the raw error reaches metres to tens of metres in the cruise, for all three estimators")
corner(fig, "raw, nothing fitted")
save("1A_unaligned_err", fig, "", "as 1A_unaligned_paths", ["9", "0"], tag="raw, nothing fitted")

# =============================================================================================== EXPERIMENT 1B: camera heading, n = 3
P4E = L("phase4_fwdc_evo.json")["trials"]
B_FL = [f"fwdc_tex_r{i}" for i in (1, 2, 3)]
SUBB = {"EKF3": ("ekf3", "ekf3_traj.tum"), "UKF_baseline": ("ukf_baseline", "ukf_traj.tum"), "FGO_baseline": ("fgo_baseline", "fgo_traj.tum"),
        "UKF_heading": ("ukf_heading", "ukf_traj.tum"), "FGO_heading": ("fgo_heading", "fgo_traj.tum")}
NLB = {"EKF3": (269, ["4.09", "3.60", "4.08"]), "FGO_baseline": (270, ["4.47", "2.26", "4.54"]), "UKF_baseline": (271, ["4.96", "1.78", "4.96"]),
       "UKF_heading": (291, ["0.13", "0.13", "0.14"]), "FGO_heading": (292, ["0.06", "0.06", "0.06"])}
ALB = {}; SCB = {}
for key in SUBB:
    for tr in B_FL:
        win = P4E[tr]["window_s"]; st = P4E[tr]["est"][key]["ate_a_cruise"]["+0.00"]
        t, xyz, ref, rmse, rmse_y = aligned(tr, *SUBB[key], win)
        dataid("1B", f"{tr} {key}: same samples, standard SE(3) cruise ATE recomputed vs stored (6 dp)", rd(rmse, 6), rd(st, 6),
               f"eval/results/phase4_fwdc_evo.json:{tr}.est.{key}.ate_a_cruise")
        YAWD.append((tr, key, rmse_y - rmse))
        if yaw_ok("1B", tr, key, rmse_y, st, f"eval/results/phase4_fwdc_evo.json:{tr}.est.{key}.ate_a_cruise"):
            ALB[(key, tr)] = (t - win[0], NE(key, xyz), NE(key, ref), np.linalg.norm(xyz - ref, axis=1))
    ln, vals = NLB[key]; SCB[key] = " / ".join(rd(P4E[tr]["est"][key]["ate_a_cruise"]["+0.00"], 2) for tr in B_FL)
    check("1B", f"{key} cruise ATE flights 1 / 2 / 3 (m), printed in the panel title", SCB[key], " / ".join(vals), "docs/thesis/numbers.md", ln)
check("1B", "flights shown (textured-wall camera dataset, textured floor)", len(B_FL), 3, "docs/thesis/numbers.md", 269, inline_str="r1 / r2 / r3")
truth_page("1B_truth", B_FL, gt_enu("ukf_baseline"), "Where the drone really flew: all 3 camera-dataset flights (simulator truth)",
           lambda tr: P4E[tr]["window_s"], "n = 3 flights, one grey line each (they lie on top of each other)",
           "~/thesis_data/trials/fwdc_tex_r1..r3/ukf_baseline/ground_truth.tum (ENU)", ["3", "1.0", "0"])
LBB = {"EKF3": "EKF3\nno heading", "UKF_baseline": "UKF\nno heading", "FGO_baseline": "FGO\nno heading",
       "UKF_heading": "UKF\nwith heading", "FGO_heading": "FGO\nwith heading"}
COLB = {k: C[k.split("_")[0]] for k in SUBB}
NTX = lambda k: "n = 3 flights"
# v3 (2026-10-31): the 1B fitted paths and fitted error figures (1B_aligned_paths, 1B_err_noheading, 1B_err_heading) are no longer
# drawn; their SE(3) recompute rows above stay and back the registered cruise-ATE ranges in the table of 1B_unaligned_paths. The
# '30 times finer' check belonged to the removed 1B_err_heading and is dropped with it.

# ---- 1B NOT FITTED (user request 2026-10-21: "add the unaligned 1B pages"): the estimates exactly as they came out, from take-off,
# the same code path as the 1A not-fitted pages (unaligned(): frame map and frame check of eval/figs_thesis_drift.py)
UNB = {}; FRB = []
for key in SUBB:
    for tr in B_FL:
        win = P4E[tr]["window_s"]; fr_, UNB[(key, tr)] = unaligned(key, tr, *SUBB[key], win); FRB.append((tr, key) + fr_)
        tt, ne, ee, er, (tg, ng, eg) = UNB[(key, tr)]; w = tt >= 0; fl = P4E[tr]["est"][key]["failure"]
        src = f"eval/results/phase4_fwdc_evo.json:{tr}.est.{key}.failure"
        # stored displacement over the cruise window (eval/three_way_eval.py failure_metrics, origin at the window start): the
        # PLOTTED not-fitted path samples, restricted to the window, must give the same estimated and true travel (6 dp)
        dataid("1B_unaligned", f"{tr} {key}: PLOTTED not-fitted path, estimated displacement over the cruise window vs stored final_disp (6 dp)",
               rd(float(np.hypot(ne[w][-1] - ne[w][0], ee[w][-1] - ee[w][0])), 6), rd(fl["final_disp"], 6), src + ".final_disp")
        gn, ge = np.interp(tt[w] + win[0], tg, ng), np.interp(tt[w] + win[0], tg, eg)
        dataid("1B_unaligned", f"{tr} {key}: PLOTTED truth at the plotted samples, true travel over the cruise window vs stored true_travel (6 dp)",
               rd(float(np.hypot(gn[-1] - gn[0], ge[-1] - ge[0])), 6), rd(fl["true_travel"], 6), src + ".true_travel")
        # end-of-cruise not-fitted error: the plotted curve's last value vs a direct recomputation from the raw TUM rows
        a = np.loadtxt(f"{TD}/{tr}/{SUBB[key][0]}/{SUBB[key][1]}"); g = np.loadtxt(f"{TD}/{tr}/{SUBB[key][0]}/ground_truth.tum")
        r_ = a[a[:, 0] <= win[1]][-1]
        if key.startswith("EKF3"):
            e_end = math.hypot(r_[1] - np.interp(r_[0], g[:, 0], g[:, 1]), r_[2] - np.interp(r_[0], g[:, 0], g[:, 2]))
        else:      # own frame (x, y) = (North, West); truth ENU (x, y) = (East, North)
            e_end = math.hypot(r_[1] - np.interp(r_[0], g[:, 0], g[:, 2]), -r_[2] - np.interp(r_[0], g[:, 0], g[:, 1]))
        dataid("1B_unaligned", f"{tr} {key}: PLOTTED not-fitted error at the end of the cruise vs direct recomputation from the raw TUM rows (6 dp)",
               rd(float(er[-1]), 6), rd(e_end, 6), f"~/thesis_data/trials/{tr}/{SUBB[key][0]}/{SUBB[key][1]} + ground_truth.tum")
if not all(f[2] for f in FRB):
    sys.exit("1B FRAME CHECK FAILED on " + str([f for f in FRB if not f[2]]))
dataid("1B_unaligned", f"frame check (rule of eval/figs_thesis_drift.py, heading tolerance {HEAD_TOL_DEG:g} deg) on every flight and arm",
       f"{sum(f[2] for f in FRB)}/{len(FRB)}", "15/15", "this script")
FRAME_NOTE_B = (f"at R5's 2.0 deg tolerance {sum(abs(f[5] - f[6]) < 2.0 for f in FRB)}/{len(FRB)} pass" +
                ("; the others " + ", ".join(f"{f[0]} {f[1]} {f[5] - f[6]:+.2f} deg" for f in FRB if abs(f[5] - f[6]) >= 2.0)
                 if any(abs(f[5] - f[6]) >= 2.0 for f in FRB) else ""))
# v3 (2026-10-31): the 1B raw paths figure is drawn after the 1C flights are loaded (its optional sixth panel is the closed-loop
# EKF3 with heading); here the raw maximum error per arm for its table. Span: take-off to the end of the cruise window, exactly the
# plotted not-fitted error (the same span as the 0.54 m with-heading value, D63); each is cross-checked against a direct
# recomputation from the raw TUM rows (6 dp).


def _raw_max(k):
    mx = 0.0
    for tr in B_FL:
        win = P4E[tr]["window_s"]; a = np.loadtxt(f"{TD}/{tr}/{SUBB[k][0]}/{SUBB[k][1]}"); g = np.loadtxt(f"{TD}/{tr}/{SUBB[k][0]}/ground_truth.tum")
        a = a[(a[:, 0] >= g[0, 0]) & (a[:, 0] <= win[1])]
        if k.startswith("EKF3"):           # EKF3 and its truth: (N, E, D)
            e_ = np.hypot(a[:, 1] - np.interp(a[:, 0], g[:, 0], g[:, 1]), a[:, 2] - np.interp(a[:, 0], g[:, 0], g[:, 2]))
        else:                               # own frame (x, y) = (North, West); truth ENU (x, y) = (East, North)
            e_ = np.hypot(a[:, 1] - np.interp(a[:, 0], g[:, 0], g[:, 2]), -a[:, 2] - np.interp(a[:, 0], g[:, 0], g[:, 1]))
        mx = max(mx, float(e_.max()))
    return mx


RAWMX = {}
for k in SUBB:
    RAWMX[k] = max(float(np.max(UNB[(k, tr)][3])) for tr in B_FL)
    dataid("1B_unaligned", f"{k}, all 3 flights: largest PLOTTED not-fitted error, take-off to the end of the cruise, vs direct recomputation "
           "from the raw TUM rows (6 dp)", rd(RAWMX[k], 6), rd(_raw_max(k), 6), f"~/thesis_data/trials/fwdc_tex_r1..r3/{SUBB[k][0]} TUM + ground_truth.tum")
fig = err_rows([(k, COLB[k], f"{LBB[k].replace(chr(10), ', ')}: {NTX(k)}, one line each", "-") for k in ("EKF3", "UKF_baseline", "FGO_baseline")],
               {k: (v[0], v[3]) for k, v in UNB.items()}, "WITHOUT the camera heading, no fitting: error against time from take-off, all 3 flights",
               "horizontal error (m)", "time since the start of the cruise (s; take-off is before 0)", ylim=(0, None), vline=0,
               note="Same y-scale in all three panels (not the same as the next page). Distance between the estimated and the true position, seen from above.")
save("1B_unaligned_err_noheading", fig, "", "as 1B_unaligned_paths", ["3", "0"])
fig = err_rows([(k, COLB[k], f"{LBB[k].replace(chr(10), ', ')}: {NTX(k)}, one line each", "-") for k in ("UKF_heading", "FGO_heading")],
               {k: (v[0], v[3]) for k, v in UNB.items()}, "WITH the camera heading, no fitting: error against time from take-off, all 3 flights",
               "horizontal error (m)", "time since the start of the cruise (s; take-off is before 0)", ylim=(0, None), vline=0,
               note="Same y-scale in both panels. NOTE: this y-scale is much finer than on the previous page. EKF3 has no camera-heading version.")
save("1B_unaligned_err_heading", fig, "", "as 1B_unaligned_paths", ["3", "0"])
# 2026-10-29 (walkthrough restructure, D63): the with-heading not-fitted error pages were dropped from the walkthrough; their size is
# stated in text instead ("below about 0.5 m", user's wording). The printed value = the largest PLOTTED with-heading not-fitted error
# over every flight and both arms (take-off to the end of the cruise), rounded once to 2 dp, cross-checked against a direct
# recomputation from the raw TUM rows over the same span (data identity, 6 dp). It is 0.54 m, so the walkthrough says "about 0.5 m at
# most", not "below 0.5 m" (flagged to the user, D63).
UBH = max(float(np.max(UNB[(k, tr)][3])) for k in ("UKF_heading", "FGO_heading") for tr in B_FL)


def _raw_max_heading():
    mx = 0.0
    for k in ("UKF_heading", "FGO_heading"):
        for tr in B_FL:
            win = P4E[tr]["window_s"]; a = np.loadtxt(f"{TD}/{tr}/{SUBB[k][0]}/{SUBB[k][1]}"); g = np.loadtxt(f"{TD}/{tr}/{SUBB[k][0]}/ground_truth.tum")
            a = a[(a[:, 0] >= g[0, 0]) & (a[:, 0] <= win[1])]      # own frame (x, y) = (North, West); truth ENU (x, y) = (East, North)
            e_ = np.hypot(a[:, 1] - np.interp(a[:, 0], g[:, 0], g[:, 2]), -a[:, 2] - np.interp(a[:, 0], g[:, 0], g[:, 1]))
            mx = max(mx, float(e_.max()))
    return mx


dataid("1B_unaligned", "WITH heading (UKF, FGO), all 3 flights: largest PLOTTED not-fitted error, take-off to the end of the cruise, vs direct "
       "recomputation from the raw TUM rows (6 dp)", rd(UBH, 6), rd(_raw_max_heading(), 6), "~/thesis_data/trials/fwdc_tex_r1..r3/{ukf,fgo}_heading TUMs + ground_truth.tum")
check("1B_unaligned_err_heading", "largest with-heading not-fitted error over the 3 flights and both arms (m, 2 dp), printed in the walkthrough text",
      rd(UBH, 2), rd(UBH, 2), "the plotted curves (this script; data-identity row 1B_unaligned)")
check("1B_unaligned_err_heading", "the largest with-heading not-fitted error rounded once to 1 dp ('about 0.5 m at most', walkthrough text; the "
      "user's 'below about 0.5 m' is not met: the largest is 0.54 m, UKF fwdc_tex_r3)", rd(UBH, 1), "0.5", "the plotted curves (this script)")
UBH_S = rd(UBH, 2)

# =============================================================================================== EXPERIMENT 1C: closed loop, n = 12
CL = {(e, k): (tr, ex_cl(e, tr)) for e, tr, k in CL_ALL}
CLJ = {tr: L(f"closed_loop_{tr}.json") for _, tr, _ in CL_ALL}
CT_LINE = {"EKF3": (470, "+242.1"), "UKF": (471, "+165.9"), "FGO": (473, "+169.9")}
for e in EST:
    t = CLJ[HALF[e][0]]["contact"]["t_rel_cruise_s"]
    check("1C", f"{e} no-heading wall contact (s after cruise start), printed on the figures", f"+{rd(t, 1)}", CT_LINE[e][1], "docs/thesis/numbers.md", CT_LINE[e][0])
dclk = max(float(v[1]["dclk"]) for v in CL.values())
dataid("1C", "clock map rebuilt from /imu/time_ref vs stored clock_map, all 12 flights, max |delta| <= 1e-6 (F9 rule)", "ok" if dclk <= 1e-6 else f"{dclk:.2e}", "ok",
       "closed_loop_*.json clock_map")
check("1C", "flights: 1 without heading and 3 with heading per estimator", " / ".join(f"{e} 1/{len(HALF[e][1])}" for e in EST), "EKF3 1/3 / UKF 1/3 / FGO 1/3",
      "eval/figs_thesis.py HALF (Figure 4.1 / 4.1b caption: n = 1 flight per estimator without heading; 3 flights each with)")


def sim_t(d):
    """SITL time of the SIM rows -> bag (sim) time, with the stored-equivalent clock map (cl_clock, rebuilt and checked above)."""
    kk, cc, _ = d["clk"]; t = d["sim"][:, 0]; return t + kk * t + cc


# (a) v3 (2026-10-31, user TASK 3): ONE panel per estimator, the same axes, overlaying all of its flights: the single no-heading
# flight (dashed) and the three with-heading flights (solid). North along x, equal scale (no stretch); walls as labelled grey bands
# beyond +-10 m; the 9.58 m contact line; each wall contact an X with its time, its registered window and its verdict.
IDXS = open(os.path.join(ROOT, "docs", "thesis", "summary", "index_summary.md")).read()


def sumrow(page, label):
    """COPIED from eval/figs_walkthrough_extra.py: the computed string of summary page `page`'s check row `label` (index_summary.md)."""
    sec = IDXS[IDXS.index(f"## Page {page}:"):]; sec = sec[:sec.find("\n## Page ", 5)]
    rows = [r for r in sec.split("\n") if r.startswith(f"| number | {label} |") or r.startswith(f"| display | {label} |")
            or r.startswith(f"| count | {label} |")]
    assert len(rows) == 1, f"summary page {page}: check row '{label}' found {len(rows)} times"
    assert rows[0].rstrip().endswith("| yes |"), f"summary page {page}: check row '{label}' did not pass"
    return re.findall(r"`([^`]*)`", rows[0])[0]


VERD = {"PASS": "PASS", "MISS": "NOT MET"}       # summary page 05 check-row token -> the registered Result wording (page 05 Result)
LIMC = 12.5
fig, axs = plt.subplots(3, 1, figsize=(FW, 5.7), sharex=True, sharey=True)
PATHD = {}; DB2 = []; CTV = {}; VP3 = {}
for ax, e in zip(axs, EST):
    wallband(ax, LIMC, vertical=False, label=False)
    for yw in (9.58, -9.58):
        ax.axhline(yw, color=INK2, lw=0.7, ls=":", zorder=1)
    for k in (1, 2, 3):
        tr, d = CL[(e, k)]; g = d["sim"]; c0b, c1b = CLJ[tr]["cruise_s"]; w = g[:, 0] >= 20
        ax.plot(g[w, 2], g[w, 1], color=C[e], lw=1.1, zorder=3)
        wc = (g[:, 0] >= c0b) & (g[:, 0] <= c1b); DB2.append(abs(float(np.abs(g[wc, 1]).max()) - CLJ[tr]["B"]["B2"]["max_abs_x_cruise_m"]))
    tr, d = CL[(e, 0)]; g = d["sim"]; c0, ct = _ns["cl_meta"](tr); tc = ct["t_rel_cruise_s"]
    w = (g[:, 0] >= 20) & (g[:, 0] <= c0 + tc)
    ax.plot(g[w, 2], g[w, 1], color=C[e], lw=1.5, ls=(0, (5, 3)), zorder=4)
    ax.plot(ct["y"], ct["x"], marker="X", ms=10, color=C[e], mec=INK, mew=0.9, zorder=6)
    PATHD[e] = math.hypot(g[w, 2][-1] - ct["y"], g[w, 1][-1] - ct["x"])
    lo, hi = CLWIN[e]; inwin = lo <= tc <= hi and tc >= 100
    CTV[e] = f"+{rd(tc, 1)} {'PASS' if inwin else 'MISS'}"
    check("1C_paths", f"{e}: wall contact (s after cruise start) and verdict against its window, printed at the X", CTV[e],
          sumrow("05", f"{e}: wall contact after cruise start (s) and verdict against its window"), "docs/thesis/summary/index_summary.md page 05 check row")
    check("1C_paths", f"{e}: registered contact window printed (s)", f"{lo} to {hi}", {"EKF3": "155 to 215", "UKF": "146 to 218", "FGO": "145 to 196"}[e],
          "docs/thesis/numbers.md", {"EKF3": 470, "UKF": 471, "FGO": 472}[e], inline_str=f"[+{lo}, +{hi}]")
    vt = VERD[CTV[e].split()[1]]
    ax.text(2, 7.4, f"dashed, no heading (1 flight): wall contact at the X, {CTV[e].split()[0]} s; window {lo} to {hi} s: {vt}", fontsize=9.5,
            ha="left", va="center", color=INK, weight="bold")
    ax.text(ct["y"] + 2.5, -7.0, f"X: {CTV[e].split()[0]} s", fontsize=9, ha="left", va="center", color=INK, weight="bold")
    npass = sum(1 for t in HALF[e][1] if CLJ[t]["B"]["pass"] and CLJ[t].get("S2", {}).get("pass", True))   # as figs_thesis_summary.py passh
    VP3[e] = f"{npass}/{len(HALF[e][1])}"
    check("1C_paths", f"{e}: with-heading flights passing all five checks (recounted from the stored B.pass flags), printed", VP3[e],
          sumrow("06", f"{e}: flights passing all five checks"), "eval/results/closed_loop_<trial>.json B.pass; index_summary.md page 06 check row")
    ax.text(163, 3.6, f"solid, with heading (3 flights): all five checks PASS on {VP3[e].replace('/', ' of ')}", fontsize=9.5, ha="right",
            va="center", color=INK, weight="bold")
    ax.text(-3.0, 0.0, e, fontsize=12, color=C[e], weight="bold", ha="right", va="center")
    ax.set_aspect(1.0, adjustable="box"); ax.set_yticks([-10, 0, 10])
    for s_ in (1, -1):
        ax.text(1.0, 11.25 * s_, "wall", fontsize=8.5, color=INK2, ha="left", va="center")
axs[0].set_xlim(-16, 166); axs[0].set_ylim(-LIMC, LIMC)
axs[-1].text(165, -8.6, "dotted: wall-contact line, 9.58 m", fontsize=8.5, color=INK2, ha="right", va="bottom")
axs[-1].set_xlabel("along the corridor, North (m)")
fig.supylabel("sideways, East (m)", x=0.012, fontsize=10.5)
fig.subplots_adjust(left=0.07, right=0.99, top=0.86, bottom=0.1, hspace=0.12)
s = measured_stretch(fig, axs[0])
check("1C_paths", "equal scale (measured stretch)", rd(s, 1), "1.0", "set_aspect(1.0)")
title1(fig, "Without a heading each estimator flew the drone into the wall; with the camera heading all 9 flights stayed straight")
corner(fig, "raw: the drone's true path, nothing fitted")
dataid("1C_paths", "plotted no-heading paths end at the scored contact point, all 3, |delta| <= 0.5 m (F2 rule)",
       "ok" if max(PATHD.values()) <= 0.5 else rd(max(PATHD.values()), 2), "ok", "dataflash SIM vs closed_loop_*.json contact")
dataid("1C_paths", "plotted with-heading paths: max |East| in the cruise vs stored B2, all 9 flights, |delta| <= 0.05 m (F2 rule)",
       "ok" if max(DB2) <= 0.05 else rd(max(DB2), 3), "ok", "dataflash SIM vs closed_loop_*.json B.B2")
check("1C_paths", "wall position and contact line (m)", "10 / 9.58", "10 / 9.58", "eval/figs_thesis.py F2 (walls ±10 m; 9.58 m contact threshold)")
save("1C_paths", fig, "", "dataflash SIM of the 12 closed-loop flights; contact and B2 from eval/results/closed_loop_<trial>.json; verdicts: "
     "index_summary.md pages 05, 06", ["1", "3", "9.58", "10"] + [CTV[e].split()[0] for e in EST] + [str(v) for e in EST for v in CLWIN[e]],
     tag="raw: the drone's true path, nothing fitted")

# ---- 1B raw paths (v3, user TASK 2): five offline panels + the closed-loop EKF3 with heading (Experiment 1C flights, comparable as a
# picture only; decision D70), walls as labelled bands, the x axis symmetric about 0, and the table of registered scores and raw maxima.
FRC = []; CLE = {}
for i_, tr in enumerate(HALF["EKF3"][1]):
    d = CL[("EKF3", i_ + 1)][1]; kk, cc, _ = d["clk"]; g = d["sim"]; K = ex_xkf1(tr)["K1"]
    c0b, c1b = CLJ[tr]["cruise_s"]; s0, s1 = (c0b - cc) / (1 + kk), (c1b - cc) / (1 + kk)     # bag (sim) time -> SITL TimeUS (inverse map)
    est_ = (K[:, 0], K[:, 1], K[:, 2]); gt_ = (g[:, 0], g[:, 2], g[:, 1])                    # (t, North, East): XKF1 (PN, PE); SIM (N, E)
    ok, diag = frame_ok(est_, gt_, (s0, s1)); FRC.append((tr, ok) + diag)
    wk = K[:, 0] <= s1; wg = g[:, 0] <= s1
    CLE[tr] = (K[wk, 1], K[wk, 2], g[wg, 2], g[wg, 1])        # est N, est E, true N, true E
    wcr = (g[:, 0] >= s0) & (g[:, 0] <= s1)
    dataid("1B_paths_cl", f"{tr}: PLOTTED truth, max |East| in the cruise vs stored B2 (|delta| <= 0.05 m, F2 rule)",
           "ok" if abs(float(np.abs(g[wcr, 1]).max()) - CLJ[tr]["B"]["B2"]["max_abs_x_cruise_m"]) <= 0.05 else "differs", "ok",
           f"dataflash SIM vs eval/results/closed_loop_{tr}.json B.B2")
if not all(f[1] for f in FRC):
    sys.exit("1B closed-loop EKF3 FRAME CHECK FAILED on " + str([f for f in FRC if not f[1]]))
dataid("1B_paths_cl", f"frame check of the closed-loop EKF3 panel (XKF1 core 0 vs SIM, take-off < 0.05 m, heading tolerance {HEAD_TOL_DEG:g} deg)",
       f"{sum(f[1] for f in FRC)}/{len(FRC)}", "3/3", "this script")
PAN = [("EKF3", "EKF3, no heading"), ("UKF_baseline", "UKF, no heading"), ("FGO_baseline", "FGO, no heading"),
       ("EKF3_cl", "EKF3 with heading, flown\nclosed-loop (Experiment 1C),\nnot a replay of the same\nrecorded flights"),
       ("UKF_heading", "UKF, with heading"), ("FGO_heading", "FGO, with heading")]
LIMB = max([float(np.abs(v[2]).max()) for v in UNB.values()] + [float(np.abs(v[1]).max()) for v in CLE.values()] + [10.0]) + 4.0
fig = plt.figure(figsize=(FW, 6.6))
gs = fig.add_gridspec(2, 6, height_ratios=[3.3, 1.0], hspace=0.24, wspace=0.1)
axs = [fig.add_subplot(gs[0, i]) for i in range(6)]
for ax in axs[1:]:
    ax.sharex(axs[0]); ax.sharey(axs[0])
for ax, (key, lab) in zip(axs, PAN):
    if key == "EKF3_cl":
        wallband(ax, LIMB, fs=8)
        ax.set_facecolor("#f4f4f4")
        for tr in HALF["EKF3"][1]:
            en, ee, gn, ge = CLE[tr]; ax.plot(ge, gn, color=TRUTH, lw=2.2, zorder=2)
        for tr in HALF["EKF3"][1]:
            en, ee, gn, ge = CLE[tr]; ax.plot(ee, en, color=C["EKF3"], lw=LW_FL, zorder=3)
        ax.plot(0, 0, marker="o", ms=5, color=INK, zorder=5)
        ax.set_aspect(1.0, adjustable="box")
        ax.set_title(lab, loc="left", fontsize=8.8, color=C["EKF3"], weight="bold")
    else:
        paths_raw(ax, UNB, key, B_FL, lambda tr: P4E[tr]["window_s"], COLB[key], LIMB)
        ax.set_title(lab, loc="left", fontsize=9.5, color=COLB[key], weight="bold")
    ax.set_xlabel("East (m)", fontsize=9.5)
for ax in axs[1:]:
    plt.setp(ax.get_yticklabels(), visible=False)
axs[0].set_ylabel("along the corridor, North (m)")
axs[0].set_xlim(-LIMB, LIMB); axs[0].set_ylim(-3, 163)
check("1B_unaligned_paths", "x-axis symmetric about 0 (left and right limits, m)", f"{-axs[0].get_xlim()[0]:.6f}", f"{axs[0].get_xlim()[1]:.6f}", "set_xlim(-LIMB, LIMB)")
check("1B_unaligned_paths", "flights shown (textured-wall camera dataset, textured floor)", len(B_FL), 3, "docs/thesis/numbers.md", 269, inline_str="r1 / r2 / r3")
check("1B_unaligned_paths", "closed-loop EKF3 with-heading flights shown", len(HALF["EKF3"][1]), 3, "eval/figs_thesis.py HALF (cl_bcpp_tex_r1..r3_half)")
RNGB = {}; RAWS = {}
for k in SUBB:
    RNGB[k] = rng([P4E[tr]["est"][k]["ate_a_cruise"]["+0.00"] for tr in B_FL])
    check("1B_unaligned_paths", f"{k}: registered cruise ATE, lowest–highest over the 3 flights (m), printed in the table", RNGB[k],
          sumrow("04", f"{k}, painted-line walls, range over flights 1–3 (m)"), "docs/thesis/summary/index_summary.md page 04 check row")
    RAWS[k] = rd(RAWMX[k], 2)
    check("1B_unaligned_paths", f"{k}: raw maximum error over the 3 flights, take-off to the end of the cruise (m, 2 dp), printed in the table",
          RAWS[k], rd(RAWMX[k], 2), "the plotted curves (data-identity row 1B_unaligned: direct TUM recomputation)")
check("1B_unaligned_paths", "largest with-heading raw error over UKF and FGO equals the 0.54 m of the 2026-10-29 walkthrough (D63)",
      max(RAWS["UKF_heading"], RAWS["FGO_heading"], key=float), UBH_S, "this script, UBH (data-identity row 1B_unaligned)")
check("1B_unaligned_paths", "EKF3 has no offline heading arm (table text)", "no offline heading arm", sumrow("04", "EKF3 has no offline heading input"),
      "docs/thesis/summary/index_summary.md page 04")
at = fig.add_subplot(gs[1, :]); at.axis("off"); at.set_xlim(0, 1); at.set_ylim(0, 1)
GX = (0.0, 0.5)                 # two groups side by side: without heading | with heading
CX = (0.0, 0.165, 0.335)
HDR = ["estimator", "registered score:\ncruise ATE (fitted),\nlowest to highest", "raw maximum\nerror, take-off\nto end of cruise"]
for gx in GX:
    for cx, h_ in zip(CX, HDR):
        at.text(gx + cx, 1.04, h_, fontsize=9.5, weight="bold", va="top", linespacing=1.05)
GRP = [[("EKF3", "EKF3, no heading"), ("UKF_baseline", "UKF, no heading"), ("FGO_baseline", "FGO, no heading")],
       [(None, "EKF3, with heading"), ("UKF_heading", "UKF, with heading"), ("FGO_heading", "FGO, with heading")]]
for gx, grp in zip(GX, GRP):
    for i, (k, lab) in enumerate(grp):
        y_ = 0.47 - 0.19 * i; col = C[lab.split(",")[0]]
        at.text(gx + CX[0], y_, lab, fontsize=9.5, color=col, weight="bold", va="center")
        if k is None:
            at.text(gx + CX[1], y_, "no offline heading arm (the closed-loop\npanel is a picture, not scored)", fontsize=8.5, va="center", color=INK2,
                    linespacing=1.05)
        else:
            r_ = RNGB[k]; lo_, hi_ = r_.split("–")
            at.text(gx + CX[1], y_, (f"{lo_} m (all 3 flights)" if lo_ == hi_ else f"{lo_} to {hi_} m"), fontsize=9.5, va="center")
            at.text(gx + CX[2], y_, f"{RAWS[k]} m", fontsize=9.5, va="center")
at.text(0.0, -0.2, "Experiment 1B flights 1-3: textured walls over the textured floor",
        fontsize=9, ha="left", va="bottom", color=INK2)   # flight set named (user, 2026-11-03; D121)
at.text(1.0, -0.2, "no pass rule (descriptive comparison)", fontsize=9, ha="right", va="bottom", color=INK2, style="italic")
fig.subplots_adjust(left=0.065, right=0.99, top=0.85, bottom=0.04)
s = measured_stretch(fig, axs[0]); check("1B_unaligned_paths", "equal scale (measured stretch)", rd(s, 1), "1.0", "set_aspect(1.0)")
title1(fig, "With the camera heading the UKF and FGO stay on the true path; without it every estimate drifts sideways")
corner(fig, "raw, nothing fitted (paths)")
save("1B_unaligned_paths", fig, "", "TUMs of fwdc_tex_r1..r3 ({ekf3,ukf_baseline,fgo_baseline,ukf_heading,fgo_heading}/*.tum); frame map (N, E) = (x, −y) "
     "for the UKF/FGO (eval/figs_thesis_drift.py); windows and cruise ATEs phase4_fwdc_evo.json; closed-loop panel: dataflash XKF1 (core 0) and SIM "
     "of cl_bcpp_tex_r1..r3_half, cruise window closed_loop_<trial>.json mapped to SITL time by the rebuilt clock map",
     ["3", "1", "1.0"] + [x for k in SUBB for x in RNGB[k].split("–")] + [RAWS[k] for k in SUBB], tag="raw, nothing fitted (paths)")

# (b) heading error WITHOUT heading (v3 style): 3 rows, shared axes, to the wall contact; the y label once; direct labels
D = {}; ENDD = []
fig, axs = plt.subplots(3, 1, figsize=(FW, FH), sharex=True, sharey=True)
for e in EST:
    tr, d = CL[(e, 0)]; tc = CLJ[tr]["contact"]["t_rel_cruise_s"]; x, y = d["yx"], d["ye"]; w = (x >= 0) & (x <= tc)
    D[(e, tr)] = (x[w], y[w]); ENDD.append(tc - x[w][-1])
for ax, e in zip(axs, EST):
    tr = HALF[e][0]; x, y = D[(e, tr)]
    ax.axhline(0, color=INK2, lw=0.6, zorder=1)
    ax.plot(x, y, color=C[e], lw=1.3, ls=(0, (5, 3)), zorder=3)
    ax.plot(x[-1], y[-1], marker="X", ms=10, color=C[e], mec=INK, mew=0.9, zorder=6, ls="")
    ax.annotate(f"wall at {CTV[e].split()[0]} s ({VERD[CTV[e].split()[1]]})", (x[-1], y[-1]), xytext=(12, 0), textcoords="offset points",
                ha="left", va="center", fontsize=9.5, weight="bold")
    ax.text(0.005, 0.93, f"{e}, no heading, 1 flight", transform=ax.transAxes, color=C[e], weight="bold", fontsize=10.5, va="top")
axs[0].set_xlim(0, 310); axs[-1].set_xlabel("time since the start of the cruise (s)")
fig.supylabel("heading error, estimate minus truth (°)", x=0.012, fontsize=10.5)
fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.11, hspace=0.25)
assert len({ax.get_ylim() for ax in axs}) == 1
title1(fig, "Without a heading source each estimator's heading error grew until the drone touched the wall (X)")
corner(fig, "raw heading error, nothing fitted")
dataid("1C_head_off", "plotted no-heading curves end within 0.1 s of the stored contact time, all 3 (F9 rule)", "ok" if max(ENDD) <= 0.1 else rd(max(ENDD), 3),
       "ok", "curve source vs closed_loop_*.json contact.t_rel_cruise_s")
for e in EST:
    check("1C_head_off", f"{e}: wall contact and verdict printed at the X (same string as 1C_paths)", CTV[e],
          sumrow("05", f"{e}: wall contact after cruise start (s) and verdict against its window"), "index_summary.md page 05 check row")
save("1C_head_off", fig, "", "dataflash XKF1 (core 0) / XUKO / XFGO and SIM, bag /imu/time_ref (clock map), of cl_a_tex_half, cl_ukf_a_tex_half_v2, "
     "cl_fgo_a_tex_half_v3; contact from closed_loop_<trial>.json", ["1"] + [CTV[e].split()[0] for e in EST], tag="raw heading error, nothing fitted")

# (c) heading error WITH heading (v3 style): 3 rows, shared axes, the grey +-2.0 deg band labelled as the limit, PASS per panel
D = {}; DB3 = []; P95 = {}; MX = {}
for e in EST:
    for k in (1, 2, 3):
        tr, d = CL[(e, k)]; c0b, c1b = CLJ[tr]["cruise_s"]; b3 = CLJ[tr]["B"]["B3"]; x, y = d["yx"], d["ye"]; w = (x >= 0) & (x <= c1b - c0b)
        D[(e, tr)] = (x[w], y[w]); a = np.abs(y[w])
        DB3.append(max(abs(float(np.percentile(a, 95)) - b3["p95_deg"]), abs(float(a.max()) - b3["max_deg"])))
    P95[e] = max(CLJ[HALF[e][1][i]]["B"]["B3"]["p95_deg"] for i in range(3)); MX[e] = max(CLJ[HALF[e][1][i]]["B"]["B3"]["max_deg"] for i in range(3))
check("1C_head_on", "largest heading-error p95 / max over all 9 with-heading flights (deg), printed in the note",
      f"{rd(max(P95.values()), 2)} / {rd(max(MX.values()), 2)}", "0.38 / 0.68", "eval/figs_thesis.py F9 check (numbers.md §15 re-flown B3 rows; Table 4.3)")
check("1C_head_on", "heading-error bound printed (p95 / max, deg)", "1.0 / 2.0", "1.0 / 2.0", "METHODOLOGY.md:4958 ('95th percentile ≤ 1.0°, maximum ≤ 2.0°')")
dataid("1C_head_on", "plotted with-heading curves: |error| p95 and max in the stored cruise window vs stored B3, all 9 flights, |delta| <= 0.001 deg (F9 rule)",
       "ok" if max(DB3) <= 0.001 else rd(max(DB3), 4), "ok", "curve source vs closed_loop_*.json B3")
fig, axs = plt.subplots(3, 1, figsize=(FW, FH), sharex=True, sharey=True)
for ax, e in zip(axs, EST):
    ax.axhspan(-2.0, 2.0, color=TRUTH, alpha=0.2, lw=0, zorder=1); ax.axhline(0, color=INK2, lw=0.6, zorder=1)
    for tr in HALF[e][1]:
        x, y = D[(e, tr)]; ax.plot(x, y, color=C[e], lw=LW_FL, zorder=3)
    ax.text(0.005, 0.95, f"{e}, with heading, 3 flights", transform=ax.transAxes, color=C[e], weight="bold", fontsize=10.5, va="top")
    ax.text(0.995, 0.95, f"PASS on {VP3[e].replace('/', ' of ')} flights (all five checks)", transform=ax.transAxes, fontsize=9.5, weight="bold",
            ha="right", va="top")
    ax.text(305, -1.85, f"grey band: limit ±2.0° (and within 1.0° 95% of the time; largest 95th percentile {rd(max(P95.values()), 2)}°)",
            fontsize=8.5, color=INK2, ha="right", va="bottom")
axs[0].set_xlim(0, 310); axs[0].set_ylim(-2.6, 2.9); axs[-1].set_xlabel("time since the start of the cruise (s)")
fig.supylabel("heading error, estimate minus truth (°)", x=0.012, fontsize=10.5)
fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.11, hspace=0.25)
assert len({ax.get_ylim() for ax in axs}) == 1
title1(fig, f"With the camera heading the heading error stayed inside the ±2.0° limit on all 9 flights (largest {rd(max(MX.values()), 2)}°)")
corner(fig, "raw heading error, nothing fitted")
save("1C_head_on", fig, "", "as 1C_head_off, for the 9 with-heading flights; B3 from closed_loop_<trial>.json",
     ["3", "2.0", "1.0", "95", "9", rd(max(MX.values()), 2), rd(max(P95.values()), 2)], tag="raw heading error, nothing fitted")
check("1C_head_on", "'95% of the time' (the p95 statistic) and '9 flights'", "95 / 9", "95 / 9", "B3 definition (p95); 3 estimators x 3 flights")
for e in EST:
    check("1C_head_on", f"{e}: flights passing all five checks, printed per panel", VP3[e], sumrow("06", f"{e}: flights passing all five checks"),
          "index_summary.md page 06 check row")

# (d) sideways distance from the centre line against time
D = {}; MK_ = []
for e in EST:
    tr, d = CL[(e, 0)]; tc = CLJ[tr]["contact"]["t_rel_cruise_s"]; tt = sim_t(d) - CLJ[tr]["cruise_s"][0]; w = (tt >= 0) & (tt <= tc)
    D[(e, tr)] = (tt[w], d["sim"][w, 1]); MK_.append((e, tt[w][-1], d["sim"][w, 1][-1], f"wall contact at +{rd(tc, 1)} s"))
fig = err_rows([(e, C[e], f"{e}, no heading: 1 flight", (0, (5, 3))) for e in EST], D,
               "WITHOUT a heading source: true sideways position against time, until the wall", "true East (m)",
               "time since the start of the cruise (s)", xlim=(0, 310), ylim=(-11, 11), marks=MK_,
               note="Three separate panels with the same axes. 0 m is the centre line; the walls are at ±10 m (contact counted at 9.58 m).")
save("1C_side_off", fig, "", "dataflash SIM of cl_a_tex_half, cl_ukf_a_tex_half_v2, cl_fgo_a_tex_half_v3", ["1", "0", "10", "9.58"] +
     [f"+{rd(CLJ[HALF[e][0]]['contact']['t_rel_cruise_s'], 1)}" for e in EST])
D = {}; DB2b = []
for e in EST:
    for k in (1, 2, 3):
        tr, d = CL[(e, k)]; c0b, c1b = CLJ[tr]["cruise_s"]; tt = sim_t(d) - c0b; w = (tt >= 0) & (tt <= c1b - c0b)
        D[(e, tr)] = (tt[w], d["sim"][w, 1]); DB2b.append(abs(float(np.abs(d["sim"][w, 1]).max()) - CLJ[tr]["B"]["B2"]["max_abs_x_cruise_m"]))
dataid("1C_side_on", "plotted curves (clock-mapped): max |East| in the cruise vs stored B2, all 9 flights, |delta| <= 0.05 m", "ok" if max(DB2b) <= 0.05 else rd(max(DB2b), 3),
       "ok", "dataflash SIM vs closed_loop_*.json B.B2")
B2MAX = rd(max(CLJ[tr]["B"]["B2"]["max_abs_x_cruise_m"] for e in EST for tr in HALF[e][1]), 2)
check("1C_side_on", "largest sideways distance over the 9 with-heading flights (m), printed in the note", B2MAX, "0.39",
      "eval/figs_thesis.py F2 caption ('all 9 stay within 0.39 m of the centreline'); numbers.md §15 B2 rows")
check("1C_side_on", "pass-rule bound printed (m)", "6.0", "6.0", "summary page 06 pass rule ('stay within 6.0 m of the centre line')")
fig = err_rows([(e, C[e], f"{e}, with the camera heading: 3 flights, one line each", "-") for e in EST], D,
               "WITH the camera heading: true sideways position against time stays near the centre line", "true East (m)",
               "time since the start of the cruise (s)", xlim=(0, 310), ylim=(-0.6, 0.6),
               note=f"Same axes in all three panels; y-scale 20 times finer than the previous page. Largest: {B2MAX} m (pass rule: within 6.0 m).")
save("1C_side_on", fig, "", "dataflash SIM of the 9 with-heading flights; B2 from closed_loop_<trial>.json", ["3", "20", B2MAX, "6.0"])
check("1C_side_on", "'20 times finer': y half-range of the previous page / this page", str(round(11 / 0.6, -1)).rstrip("0").rstrip("."), "20",
      "axis limits ±11 m and ±0.6 m (this script)")


# =============================================================================================== ROOM EXPERIMENTS: where the drone flew
def room_paths(fid, groups, getxy, title, note, numbers, inputs, pad=0.6, swap=False):
    """One panel per group, equal scale, shared axes; one thin grey line per flight (shades tell the flights apart)."""
    fig, axs = plt.subplots(1, len(groups), figsize=(FW, FH), sharex=True, sharey=True)
    axs = np.atleast_1d(axs); allx, ally = [], []
    shades = ["#4d4d4d", "#8c8c8c", "#bdbdbd"]
    for ax, (gtitle, trs) in zip(axs, groups):
        for i, tr in enumerate(trs):
            x, y = getxy(tr)
            if swap:
                x, y = y, x
            allx += [x.min(), x.max()]; ally += [y.min(), y.max()]
            ax.plot(x, y, color=shades[i % 3], lw=LW_FL, label=f"flight {i + 1}")
            ax.plot(x[0], y[0], marker="o", ms=4, color=INK, zorder=5)
        ax.set_title(gtitle, loc="left", fontsize=10); ax.set_aspect(1.0, adjustable="box"); ax.set_xlabel("North (m)" if swap else "East (m)")
    axs[0].set_xlim(min(allx) - pad, max(allx) + pad); axs[0].set_ylim(min(ally) - pad, max(ally) + pad); axs[0].set_ylabel("East (m)" if swap else "North (m)")
    leg = max(len(g[1]) for g in groups) > 1
    if leg:
        h_, l_ = axs[-1].get_legend_handles_labels()
        fig.legend(h_, l_, loc="lower right", ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.99, 0.0))
    nl = max(g[0].count("\n") for g in groups)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.85 - 0.045 * nl, bottom=0.17 if leg else 0.11, wspace=0.15)
    st = measured_stretch(fig, axs[0]); check(fid, "equal scale (measured stretch)", rd(st, 1), "1.0", "set_aspect(1.0)")
    head(fig, title, note)
    save(fid, fig, title, inputs, numbers)


def gt_room(tr):
    G = ex_room(tr)["G"]; return G[:, 1], G[:, 2]


TL = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
room_paths("2_truth", [(f"{TL[c]}\nn = 3 flights", [f"T_{c}_r{i}" for i in (1, 2, 3)]) for c in "ABCD"], gt_room,
           "All 12 flights flew the same 5 laps of the 6 m square (simulator truth)",
           "Four separate panels (tags available), the same axes, equal scale (1.0). Black dot: start. The lines lie on top of each other.",
           ["5", "6", "12", "8", "4", "2", "1", "3", "1.0"], "bag /ground_truth/pose of T_{A,B,C,D}_r{1,2,3}")
check("2_truth", "flights: 4 conditions x 3", len(T_FL), 12, "eval/figs_thesis.py F5 (3 flights per condition A-D)")
check("2_truth", "laps / square side (m) / tags per condition", "5 / 6 / 8, 4, 2, 1", "5 / 6 / 8, 4, 2, 1",
      "Figure 5.1 caption (eval/figs_thesis.py F5: '5 laps of a 6 m square'; A all 8, B the 4 corners, C 2, D 1 tag)")
room_paths("3_truth", [("8 tags (the same flights as\nExperiment 2, 8 tags)\nn = 3 flights", [f"T_A_r{i}" for i in (1, 2, 3)])], gt_room,
           "Where the drone really flew: the 3 loop-closure flights (simulator truth)",
           "Equal scale (1.0). Black dot: start. 5 laps of the 6 m square; the lines lie on top of each other.",
           ["8", "2", "3", "1.0", "5", "6"], "bag /ground_truth/pose of T_A_r{1,2,3} (Experiment 3 re-uses these flights: eval/results/expL/T_A_r*_t245.json)")
check("3_truth", "flights", "T_A_r1, T_A_r2, T_A_r3", "T_A_r1, T_A_r2, T_A_r3", "eval/figs_thesis.py LL (expL/T_A_r{1,2,3}_t245.json)")

# =============================================================================================== EXTENSION E3: tag maps (v3, user TASK 4)
# DESCRIPTIVE, not a registered measure: the FGO's hindsight track and final landmarks (stats.json landmarks_final, keyed by creation
# order, so drawn unlabelled) against the true track and the true tags, in tag 0's frame (bag ground truth minus tag 0's position, as
# eval/l_score.py; true tags from sim/worlds/room_tags_map.json, the same shift). Runs: one clean reference (Experiment 3, flight 1, no
# wrong IDs) and the three already shown in the 2026-10-29 walkthrough (docs/thesis/tier1/stage2e/diag_collapse/figs.py). Each plotted
# hindsight track is checked: its RMSE over the stored lap window, recomputed from exactly the plotted samples, equals the stored score.
T1D = os.path.expanduser("~/thesis_data/tier1"); T1S = os.path.join(ROOT, "docs", "thesis", "tier1", "scores")
TMAP = json.load(open(os.path.join(ROOT, "sim", "worlds", "room_tags_map.json")))["tags"]
_t0 = next(t for t in TMAP if t["id"] == 0)
TRUEMAP = {t["id"]: (t["x"] - _t0["x"], t["y"] - _t0["y"]) for t in TMAP}
_rc = json.load(open(os.path.join(T1D, "stage2e", "diag_collapse", "recon_T_A_r1_0.01_s0.json")))["true_map_tag0_frame"]
dataid("E3_maps", "true tag map in tag 0's frame (room_tags_map.json shifted) equals the E3 diagnosis's true_map_tag0_frame (6 dp)",
       str(all(rd(TRUEMAP[int(k)][0], 6) == rd(v[0], 6) and rd(TRUEMAP[int(k)][1], 6) == rd(v[1], 6) for k, v in _rc.items()) and len(_rc) == len(TRUEMAP)),
       "True", "sim/worlds/room_tags_map.json vs ~/thesis_data/tier1/stage2e/diag_collapse/recon_T_A_r1_0.01_s0.json")
B3_ = "lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7"
E3M = [("T_A_r1", os.path.join(TD, "T_A_r1", "lc_fgo_lc_t245"), os.path.join(RES, "expL", "T_A_r1_t245.json"),
        "No wrong IDs, FGO as built\n(Experiment 3, flight 1):\nreference, map matches the room"),
       ("T_A_r1", os.path.join(T1D, "T_A_r1", f"{B3_}_mis0.01_s0"), os.path.join(T1S, "E3a_T_A_r1_0.01_s0.json"),
        "1% wrong IDs, FGO as built\n(flight 1, seed 0):\nfinished, map shrunk"),
       ("T_A_r3", os.path.join(T1D, "T_A_r3", f"{B3_}_mis0.05_s0"), os.path.join(T1S, "E3a_T_A_r3_0.05_s0.json"),
        "5% wrong IDs, FGO as built\n(flight 3, seed 0):\nfinished, map shrunk"),
       ("T_A_r2", os.path.join(T1D, "T_A_r2", f"{B3_}_mis0.05_s1_robcauchy2.385"), os.path.join(T1S, "E3b_T_A_r2_0.05_s1.json"),
        "5% wrong IDs, robust FGO\n(flight 2, seed 1):\nthe one robust run that collapsed")]
# 2026-11-02 (user answer 4; decision D100): the main material shows ONE collapse example (T_A_r1 1% s0, FGO as built: the H-E3.1
# primary condition and the run the E3 diagnosis studied, e3_results.md §7) beside the clean reference (kept: the user asked earlier
# for a clean reference "so success is visible"); the other two maps move to the appendix figure E3_maps_app. Same drawing, same checks.
E3TAG = "DESCRIPTIVE, not a registered measure: hindsight track and final map (raw, from the start tag)"


def e3_maps(fid, runs, title, width):
    fig, axs = plt.subplots(1, len(runs), figsize=(width, 4.9), sharex=True, sharey=True)
    for ax, (tr, rd_, sc, lab) in zip(axs, runs):
        G = ex_room(tr)["G"]; Gx, Gy = G[:, 1] - _t0["x"], G[:, 2] - _t0["y"]
        H = np.loadtxt(f"{rd_}/hindsight.tum", ndmin=2); S = json.load(open(sc)); lb = S["lap_bounds_s"]
        e_ = np.hypot(H[:, 1] - np.interp(H[:, 0], G[:, 0], Gx), H[:, 2] - np.interp(H[:, 0], G[:, 0], Gy)); wl = (H[:, 0] >= lb[0]) & (H[:, 0] <= lb[-1])
        dataid(fid, f"{os.path.basename(rd_)} ({tr}): PLOTTED hindsight track, RMSE over the stored lap window vs the stored 'lc hindsight' rmse_m (6 dp)",
               rd(float(np.sqrt(np.mean(e_[wl] ** 2))), 6), rd(S["tracks"]["lc hindsight"]["rmse_m"], 6), f"{os.path.relpath(sc, ROOT) if sc.startswith(ROOT) else sc}")
        wg = (G[:, 0] >= H[0, 0]) & (G[:, 0] <= H[-1, 0])
        ax.plot(Gx[wg], Gy[wg], color=TRUTH, lw=1.6, zorder=2)
        ax.plot(H[:, 1], H[:, 2], color=C["FGO"], lw=0.8, alpha=0.85, zorder=3)
        for tid, (x_, y_) in TRUEMAP.items():
            ax.plot(x_, y_, marker="s", ms=8, color=TRUTH, zorder=4)
        lm = json.load(open(f"{rd_}/stats.json"))["landmarks_final"]
        for v in lm.values():
            ax.plot(v[0], v[1], marker="o", ms=7, mfc="white", mec=C["FGO"], mew=1.6, ls="", zorder=5)
        check(fid, f"{os.path.basename(rd_)}: final landmarks drawn = true tags", f"{len(lm)} / {len(TRUEMAP)}", "8 / 8", "stats.json landmarks_final; room_tags_map.json")
        ax.set_title(lab, loc="left", fontsize=9.3)
        ax.set_aspect(1.0, adjustable="box"); ax.set_xlabel("from the start tag, x (m)")
    axs[0].set_ylabel("from the start tag, y (m)")
    axs[0].set_xlim(-1.5, 7.5); axs[0].set_ylim(-1.5, 7.5)
    fig.text(0.01, 0.035, "grey line and grey squares: the true track and the 8 true tags.\nOrange line and open circles: the FGO's "
             "whole-flight re-solve (hindsight) and its final tag map.", fontsize=9.5, color=INK2, ha="left", va="bottom")
    fig.subplots_adjust(left=0.10, right=0.99, top=0.74, bottom=0.2, wspace=0.12)
    title1(fig, title)
    corner(fig, E3TAG)
    return fig


fig = e3_maps("E3_maps", E3M[:2], "With 1% wrong tag IDs the FGO's final tag map shrank; with correct IDs it matched the room", FW)
check("E3_maps", "runs shown: the clean reference + one collapse example (T_A_r1 1% s0, FGO as built)", "2", "2", "user answer 4 (2026-11-02), D100")
save("E3_maps", fig, "", "bag /ground_truth/pose of T_A_r1 (tag 0 frame), hindsight.tum and stats.json landmarks_final of the two runs, "
     "sim/worlds/room_tags_map.json; scores: eval/results/expL/T_A_r1_t245.json, docs/thesis/tier1/scores/E3a_T_A_r1_0.01_s0.json", ["1", "3", "8", "0"],
     tag=E3TAG)
fig = e3_maps("E3_maps_app", E3M[2:], "Two more wrong-ID runs: the plain FGO's map shrank, the one collapsed robust run's map folded", FW)
check("E3_maps_app", "runs shown: the other two maps of the 2026-10-31 walkthrough (moved to the appendix)", "2", "2", "user answer 4 (2026-11-02), D100")
save("E3_maps_app", fig, "", "bag /ground_truth/pose of T_A_r2, T_A_r3 (tag 0 frame), hindsight.tum and stats.json landmarks_final of the two runs, "
     "sim/worlds/room_tags_map.json; scores: docs/thesis/tier1/scores/E3a_T_A_r3_0.05_s0.json, E3b_T_A_r2_0.05_s1.json", ["2", "3", "5", "8", "1", "0"],
     tag=E3TAG)



def sim_xy(tr):
    g = ex_sim(tr)["sim"]; return g[:, 1], g[:, 2]


HG = [("EKF3 flying\nnear start spot\nn = 3", H_FL[0:3]), ("EKF3 flying\nfar start spot\nn = 3", H_FL[3:6]),
      ("UKF flying\nn = 3", H_FL[6:9]), ("FGO flying\nn = 3", H_FL[9:12])]
room_paths("5_truth", HG, sim_xy, "Where the drone really flew: the 12 hold flights of Experiment 5 (simulator truth)",
           "Four separate panels, the same axes, equal scale (1.0); position from the take-off spot. Black dot: take-off.",
           ["5", "12", "3", "1.0"], "dataflash SIM of H_s1_r1..r3, H_s1far_r1, r2, r3b, H_s2v2_r1..r3, H_s3v2_r1..r3", pad=0.3)
check("5_truth", "flights: 3 per set, 4 sets", len(H_FL), 12, "eval/figs_results_walkthrough.py TRS['5h'] (the flights of summary pages 10 and 11)")
room_paths("5S_truth", [("UKF safety run a", [S_FL[0]]), ("UKF safety run b", [S_FL[1]]), ("FGO safety run a", [S_FL[2]]), ("FGO safety run b", [S_FL[3]])],
           sim_xy, "Where the drone really flew: the 4 final safety runs (simulator truth)",
           "Four separate panels, the same axes, equal scale (1.0); position from the take-off spot. Black dot: take-off.",
           ["4", "1.0"], "dataflash SIM of H_safety_ukf_a_v3, H_safety_ukf_b_v3, H_safety_fgo_a_v4, H_safety_fgo_b_v4", pad=0.3)
check("5S_truth", "flights", len(S_FL), 4, "eval/figs_results_walkthrough.py TRS['5S'] (summary page 12)")

# =============================================================================================== EXPERIMENT 4: outdoor-indoor, n = 3
TRK = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
TSH = {"EKF3 live": "EKF3, live", "UKF live": "UKF, live", "FGO live": "FGO, live", "RTS-UKF (hindsight)": "smoothed UKF (hindsight)",
       "FGO hindsight (whole-flight batch)": "FGO whole-flight batch (hindsight)"}
TCOL = {"EKF3 live": C["EKF3"], "UKF live": C["UKF"], "FGO live": C["FGO"], "RTS-UKF (hindsight)": C["UKF"], "FGO hindsight (whole-flight batch)": C["FGO"]}
TLS = {n: ("-" if "live" in n else (0, (5, 3))) for n in TRK}
OE = {}; OM = {}
for tr in O_FL:
    d = ex_room(tr); G, TR, K1 = d["G"], d["TR"], d["K1"]; o = L(f"expO/{tr}.json"); OM[tr] = o
    # clock map, COPIED from eval/o_score.py
    sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        w = (sitl >= lo) & (sitl < lo + 5)
        if w.sum() > 50:
            i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
    env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
    oE, oN = np.load(f"{TD}/{tr}/gnss.npz")["ekf3_origin_EN"]
    tracks = {"EKF3 live": np.c_[K1[:, 0] + (kk * K1[:, 0] + c0), K1[:, 1] + oE, K1[:, 2] + oN]}
    for n, p_ in (("UKF live", "room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", "room_ukf/ukf_rts.tum"), ("FGO live", "room_fgo/fgo_live.tum"),
                  ("FGO hindsight (whole-flight batch)", "room_fgo/fgo_batch.tum")):
        tracks[n] = np.loadtxt(f"{TD}/{tr}/{p_}", ndmin=2)[:, :3]
    toff, ton = o["markers_bag_s"]["GNSS OFF"], o["markers_bag_s"]["GNSS ON"]
    for n, T in tracks.items():
        e = np.hypot(T[:, 1] - np.interp(T[:, 0], G[:, 0], G[:, 1]), T[:, 2] - np.interp(T[:, 0], G[:, 0], G[:, 2]))
        wi = (T[:, 0] >= toff) & (T[:, 0] <= ton)
        dataid("4", f"{tr} {n}: indoor RMSE of the plotted error (o_score method) vs stored indoor_rmse_m (6 dp)",
               rd(float(np.sqrt(np.mean(e[wi] ** 2))), 6), rd(o["tracks"][n]["indoor_rmse_m"], 6), f"eval/results/expO/{tr}.json:tracks.{n}.indoor_rmse_m")
        w = (T[:, 0] > toff - 40) & (T[:, 0] < ton + 30)
        OE[(n, tr)] = (T[w, 0] - toff, e[w])
TON = [OM[tr]["markers_bag_s"]["GNSS ON"] - OM[tr]["markers_bag_s"]["GNSS OFF"] for tr in O_FL]
check("4", "indoor time (s), GNSS off", rd(max(TON), 0), "123", "eval/figs_thesis.py F6 check ('numbers.md §16.2 heading: 123 s, GNSS off')")
OIX = {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89", "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}
for n in TRK:
    check("4", f"{n} indoor RMSE range over the 3 flights (m), printed in the panel title", rng([OM[tr]["tracks"][n]["indoor_rmse_m"] for tr in O_FL]), OIX[n],
          "eval/figs_thesis.py T6 check (numbers.md §16.2 table)")
ymax = max(v[1].max() for v in OE.values()) * 1.05


def o_page(names, title, note):
    fig, axs = plt.subplots(len(names), 1, figsize=(FW, FH), sharex=True, sharey=True)
    for ax, n in zip(axs, names):
        for k in range(len(O_FL)):
            ax.axvspan(0, TON[k], color="#ececec", zorder=0, lw=0)
        for tr in O_FL:
            x, y = OE[(n, tr)]; ax.plot(x, y, color=TCOL[n], lw=LW_FL, ls=TLS[n], zorder=3)
        ax.set_title(f"{TSH[n]}: n = 3 flights; indoor error (RMSE) {rng([OM[tr]['tracks'][n]['indoor_rmse_m'] for tr in O_FL])} m", loc="left", pad=3)
        ax.set_ylabel("error (m)")
    axs[0].set_ylim(0, ymax); axs[0].set_xlim(-40, max(TON) + 30); axs[-1].set_xlabel("time from GNSS OFF at the entrance (s)")
    fig.subplots_adjust(left=0.08, right=0.985, top=0.88, bottom=0.1, hspace=0.5)
    head(fig, title, note, left=0.08)
    return fig


fig = o_page(["EKF3 live", "UKF live", "FGO live"], "Live estimates: error against time, all 3 flights (shaded: indoors, GNSS off)",
             f"Same y-scale in all panels here and on the next page; no alignment. Indoors {rd(max(TON), 0)} s. EKF3's drop just after "
             "the shading: its reset to GNSS.")
save("4_err_live", fig, "", "eval/results/expO/O_r1/O_r2/O_r3b.json; O_* room_ukf, room_fgo TUMs; dataflash XKF1 + gnss.npz; bag GT and /imu/time_ref",
     ["3", "123"] + [rng([OM[tr]["tracks"][n]["indoor_rmse_m"] for tr in O_FL]) for n in TRK[:3]])
fig = o_page(["RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)"],
             "Hindsight (after the flight): error against time, all 3 flights (shaded: indoors, GNSS off)",
             "Same y-scale in both panels and as the previous page. Horizontal error, world frame, no alignment.")
save("4_err_hind", fig, "", "as 4_err_live", ["3"] + [rng([OM[tr]["tracks"][n]["indoor_rmse_m"] for tr in O_FL]) for n in TRK[3:]])

# 2026-10-29 (walkthrough restructure, user: "Exp 4: merge the live and hindsight error plots into one figure with a shared y-axis"):
# the same curves (OE), one figure, three rows (EKF3 / UKF / FGO) by two columns (live, solid / hindsight, dashed), ONE y-scale for
# all six panels (sharey, asserted). EKF3 has no hindsight version: that panel carries a note and no curve.
HIND = {"EKF3 live": None, "UKF live": "RTS-UKF (hindsight)", "FGO live": "FGO hindsight (whole-flight batch)"}
# v3 (2026-10-31): the same curves (OE), 3 rows (EKF3 / UKF / FGO) by 2 columns (live, solid / hindsight, dashed), ONE y-scale for all six
# panels (sharey, asserted); the indoor shading labelled on the plot, direct labels with the indoor RMSE range, the verdicts on the panels
# they concern (index_summary.md page 09 check rows), the y label once.
JMP4 = rng([OM[tr]["tracks"]["EKF3 live"]["max_step_after_return_m"] for tr in O_FL]).split("–")[0]
check("4_err", "EKF3 reset jump on return (m), every flight, printed", rng([OM[tr]["tracks"]["EKF3 live"]["max_step_after_return_m"] for tr in O_FL]),
      "4.10–4.10", "eval/figs_thesis.py F6 check ('numbers.md §16.2: 4.10 m, every flight')")
_p4 = f"{sum(OM[tr]['tracks']['FGO hindsight (whole-flight batch)']['indoor_rmse_m'] < min(OM[tr]['tracks']['EKF3 live']['indoor_rmse_m'], OM[tr]['tracks']['UKF live']['indoor_rmse_m']) for tr in O_FL)}/3"
check("4_err", "primary: FGO hindsight below EKF3 and UKF live, flights of 3 (printed on the FGO hindsight panel)", _p4,
      sumrow("09", "primary: FGO hindsight below EKF3 and UKF live, flights of 3"), "index_summary.md page 09 check row")
V4 = {"prim": _p4, "live": sumrow("09", "live errors similar (≤ 1.5× every flight): verdict"),
      "hind": sumrow("09", "two hindsight errors within 1.5× (every flight): verdict")}
check("4_err", "live errors similar: verdict (FAIL in the check row, printed as the Result's 'NOT MET')", V4["live"], "FAIL", "index_summary.md page 09")
check("4_err", "hindsight errors similar: verdict", V4["hind"], "PASS", "index_summary.md page 09")
_prim_ok = V4["prim"] == "3/3"
fig, axs = plt.subplots(3, 2, figsize=(FW, 5.9), sharex=True, sharey=True)
RN4 = {}
for r, n in enumerate(("EKF3 live", "UKF live", "FGO live")):
    for c, nn in enumerate((n, HIND[n])):
        ax = axs[r, c]
        for k_ in range(len(O_FL)):
            ax.axvspan(0, TON[k_], color="#ececec", zorder=0, lw=0)
        if r == 0:
            ax.text(2, 0.97 * ymax, f"indoors, GPS off ({rd(max(TON), 0)} s)", ha="left", va="top", fontsize=9, color=INK2)
        e_ = n.split()[0]
        if nn is None:
            ax.text(0.5, 0.5, "EKF3: no hindsight version", transform=ax.transAxes, ha="center", va="center", fontsize=10.5, color=C["EKF3"], weight="bold")
            pass                          # the centred note names the panel; no corner label (it would collide with the indoor label)
        else:
            for tr in O_FL:
                x, y = OE[(nn, tr)]; ax.plot(x, y, color=TCOL[nn], lw=1.1, ls=TLS[nn], zorder=3)
            RN4[nn] = rng([OM[tr]['tracks'][nn]['indoor_rmse_m'] for tr in O_FL])
            lab_ = {"EKF3 live": "EKF3, live", "UKF live": "UKF, live", "FGO live": "FGO, live", "RTS-UKF (hindsight)": "UKF, re-solved after landing",
                    "FGO hindsight (whole-flight batch)": "FGO, whole flight re-solved"}[nn]
            ax.text(0.01, 0.97, lab_, transform=ax.transAxes, fontsize=10, color=TCOL[nn], weight="bold", va="top")
            ax.text(0.27, 0.80, f"indoor RMSE {RN4[nn].replace('–', ' to ')} m", transform=ax.transAxes, fontsize=9.5, ha="left", va="top")
        if nn == "EKF3 live":
            ax.annotate(f"EKF3 resets to GPS\non return: {JMP4} m jump", (TON[0] + 1, 2.0), xytext=(0.01, 0.52), textcoords="axes fraction",
                        fontsize=9, ha="left", va="center", color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7))
        if nn == "FGO hindsight (whole-flight batch)":
            ax.text(0.99, 0.40, f"PASS (primary): below EKF3 and UKF live\nin {V4['prim'].replace('/', ' of ')} flights", transform=ax.transAxes,
                    fontsize=9.5, weight="bold", ha="right", va="top")
axs[0, 0].set_ylim(0, ymax); axs[0, 0].set_xlim(-40, max(TON) + 30)
axs[0, 0].set_title("live (during flight), solid", loc="left", fontsize=10.5)
axs[0, 1].set_title("hindsight (after landing), dashed", loc="left", fontsize=10.5)
for c in range(2):
    axs[-1, c].set_xlabel("time from GPS OFF at the entrance (s)")
fig.text(0.075, 0.035, f"Live errors within 1.5× of each other: NOT MET (live errors not ranked).    Hindsight errors within 1.5×: {V4['hind']}.",
         fontsize=9.5, weight="bold", ha="left", va="bottom")
fig.supylabel("horizontal error (m)", x=0.012, fontsize=10.5)
fig.subplots_adjust(left=0.075, right=0.99, top=0.85, bottom=0.15, hspace=0.3, wspace=0.08)
title1(fig, "Indoors without GPS every live error grows; the FGO re-solved after landing stays below both filters' live errors")
corner(fig, "raw, nothing fitted")
_yl = {ax.get_ylim() for ax in axs.flat}
check("4_err", "all six panels share one y-scale (sharey)", str(len(_yl) == 1), "True", "this script (axis limits)")
check("4_err", "y-axis upper limit equals that of the two separate pages (m, 2 dp)", rd(axs[0, 0].get_ylim()[1], 2), rd(ymax, 2), "this script (ymax of 4_err_live / 4_err_hind)")
for nn in RN4:
    check("4_err", f"{nn}: indoor RMSE range printed on its panel (m)", RN4[nn], sumrow("09", f"{nn}: indoor error range over 3 flights (m)"),
          "index_summary.md page 09 check row")
save("4_err", fig, "", "as 4_err_live (the curves of 4_err_live and 4_err_hind, one figure); verdicts index_summary.md page 09",
     ["3", "1.5", "123", JMP4] + [x for v in RN4.values() for x in v.split("–")], tag="raw, nothing fitted")
room_paths("4_truth", [("n = 3 flights (out and back along the same line, so the lines lie on top of each other)", O_FL)], gt_room,
           "Where the drone really flew: the 3 outdoor–indoor flights (simulator truth)",
           "Seen from above, equal scale (1.0). Black dot: start. Out along North into the building, back the same way at the same heading.",
           ["3", "1.0"], "bag /ground_truth/pose of O_r1, O_r2, O_r3b", pad=3.0, swap=True)

# =============================================================================================== index
n_ok = sum(c["ok"] for c in CHK); n_id = sum(c["ok"] for c in DATAID)
W = ["# Results walkthrough, all flights: index and provenance", "",
     f"*Generated by `eval/figs_walkthrough_flights.py` at commit `{COMMIT}`. Stored outputs only (TUMs, bags, dataflash, eval/results json); "
     "no estimator run, no simulation; packed bags decompressed to a temporary copy outside ~/thesis_data.*", "",
     f"**Checks:** {n_ok}/{len(CHK)} printed-number checks EXACT (rd() string equality, half away from zero; a numbers.md source must also "
     f"contain the string in the cited line); {n_id}/{len(DATAID)} data-identity checks (each plotted curve recomputed from exactly the plotted "
     "samples matches its stored scored value).", "",
     "**Shared code (copied, not imported):** from `eval/figs_thesis.py` by ast, sha256 of each function's source: " +
     "; ".join(f"`{k}` `{v}`" for k, v in sorted(SRC_SHA.items())) + ". `aligned()` copied from `eval/figs_thesis_results.py`; `to_NE()` and the "
     "frame check from `eval/figs_thesis_drift.py`; the Experiment 4 clock map and error from `eval/o_score.py`.", "",
     "**Aligned (fitted) recomputation:** since v3 (2026-10-31, D79) no fitted path or error figure is drawn; the registered fitted "
     "cruise ATEs are printed in the tables of `fl_1A_unaligned_paths` and `fl_1B_unaligned_paths`. The SE(3) cruise ATE is still "
     "recomputed from the same samples, and a YAW-ONLY alignment (rotation about the vertical + 3-D shift, least squares on the same "
     "associated samples in the pinned window; the SE(3) fit is degenerate about the corridor axis) still reproduces it at 2 dp on every flight "
     f"(data-identity rows); largest (yaw-only − SE(3)) RMS difference {max(abs(d[2]) for d in YAWD):.2e} m. The SE(3) value is still "
     "recomputed to 6 dp as the input-identity check.", "",
     f"**Frame check (1A, unaligned):** heading tolerance {HEAD_TOL_DEG:g}°; {FRAME_NOTE}. Any relabel error would give ≥ 90°.", "",
     f"**Frame check (1B, unaligned; added 2026-10-21):** the same rule and code path (`unaligned()`), {sum(f[2] for f in FRB)}/{len(FRB)} "
     f"flight-arms pass at {HEAD_TOL_DEG:g}°; {FRAME_NOTE_B}. Each plotted not-fitted 1B path also reproduces the stored cruise-window "
     "displacement (`failure.final_disp`, `failure.true_travel` of `phase4_fwdc_evo.json`, eval/three_way_eval.py `failure_metrics`) to 6 dp, and "
     "its end-of-cruise error equals a direct recomputation from the raw TUM rows to 6 dp (data-identity rows `1B_unaligned`).", "",
     "**Origin:** every path figure (raw, not fitted) starts at take-off (0, 0); the fitted scores are computed on the cruise only.", "",
     "**v3 (2026-10-31):** finding titles, raw / fitted tags and verdict marks are drawn on the figures; `save()` asserts no em-dash, linear "
     "axes and every text inside the figure (measured at 200 dpi). Verdict marks equal the summary check rows (`sumrow`, index_summary.md).",
     "", "## Figures", "", "| figure | file | sha256 | inputs | numbers printed |", "|---|---|---|---|---|"]
for k, f in FIGS.items():
    W.append(f"| {k} | `{f['file']}` | `{hashlib.sha256(open(os.path.join(ROOT, f['file']), 'rb').read()).hexdigest()}` | {f['inputs']} | {', '.join(f['numbers'])} |")
W += ["", "## Printed-number checks", "", "| figure | check | computed | expected | source | result |", "|---|---|---|---|---|---|"]
W += [f"| {c['fig']} | {c['label']} | {c['computed']} | {c['expected']} | {c['src']} | {'OK' if c['ok'] else 'FAIL'} |" for c in CHK]
W += ["", "## Drawn; the yaw-only RMS differs from the stored score in the last displayed digit (under 0.005 m)", "",
      "| figure | flight | arm | yaw-only RMS (2 dp) | stored cruise ATE (2 dp) | yaw-only (full) | stored (full) |", "|---|---|---|---|---|---|---|"]
W += [f"| {a} | {b} | {c} | {d} | {e} | {f:.6f} | {g:.6f} |" for a, b, c, d, e, f, g in EXCL] or ["| none | | | | | | |"]
W += ["", "## Data-identity checks", "", "| figure | check | computed | expected | source | result |", "|---|---|---|---|---|---|"]
W += [f"| {c['fig']} | {c['label']} | {c['computed']} | {c['expected']} | {c['src']} | {'OK' if c['ok'] else 'FAIL'} |" for c in DATAID]
open(INDEX, "w").write("\n".join(W) + "\n")
json.dump(dict(figs=FIGS, checks=CHK, dataid=DATAID), open(os.path.join(OUTD, "checks.json"), "w"), indent=1)
print(f"printed-number checks {n_ok}/{len(CHK)}; data-identity {n_id}/{len(DATAID)}; wrote {INDEX}")
sys.exit(0 if n_ok == len(CHK) and n_id == len(DATAID) else 1)
