#!/usr/bin/env python3
"""RESULTS WALKTHROUGH (2026-10-18): the original detailed result plots, each beside the simulated world it was flown in, with
the plain-language Metric / Pass rule / Result lines of the reader summary underneath.

User request (verbatim): "keep the original plots with distance vs time and error over time etc but still keep the metric pass
rule and result descriptions for each of those plots, also combine the world screenshots into the results so I can see the
results and the world the screenshot was part of". Earlier: "make sure everything is easy to understand and simple, it should be
easy to understand for someone looking at it for the first time".

COMPOSITION ONLY. Nothing is re-plotted, recomputed or re-run. The pages place existing, already cross-checked images:
  - detailed result figures: docs/thesis/figures_thesis/{R3,R5,F2,F9,F5,F7,F6}.png (R3 and R5 are cropped into their panels,
    crop boxes fixed below and asserted against blank separator rows);
  - summary charts (for experiments with no detailed time-series/path plot): docs/thesis/summary/summary_NN_*.png, cropped to the
    chart band (between the "What this tests" line and the footer rule, whose row is asserted);
  - world screenshots: docs/thesis/world_images/{renders,onboard}/ (onboard frames cropped below their text strip).
Text: "What this tests", Metric, Pass rule and Result are taken VERBATIM from docs/thesis/summary/index_summary.md (written by
eval/figs_thesis_summary.py; its content at HEAD 441e97c was re-generated in scratch and is identical apart from the commit line).
Lines adapted because they point at elements of the summary chart are marked MODIFIED (original kept in the index); lines written
here ("About this plot", world captions, the contents note) are marked NEW, and every number in them must occur in the figure's own
index entry or in that page's summary strings (number guard). The world of every page is checked against the trials' recorded
world (~/thesis_data/trials/<t>/metadata.yaml or run_trial.log, read only).

Outputs: docs/thesis/summary/results_walkthrough.pdf, docs/thesis/summary/walkthrough/wt_NN_<short>.png,
docs/thesis/summary/index_walkthrough.md.
Usage: python3 eval/figs_results_walkthrough.py   (numpy, matplotlib, Pillow)."""
import hashlib, os, re, subprocess, sys, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SUM = os.path.join(ROOT, "docs", "thesis", "summary"); OUTD = os.path.join(SUM, "walkthrough"); os.makedirs(OUTD, exist_ok=True)
FIGD = os.path.join(ROOT, "docs", "thesis", "figures_thesis"); WI = os.path.join(ROOT, "docs", "thesis", "world_images")
PDF = os.path.join(SUM, "results_walkthrough.pdf"); INDEX = os.path.join(SUM, "index_walkthrough.md")
TRIALS = os.path.expanduser("~/thesis_data/trials")
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
PAGE_W, PAGE_H = 11.69, 8.27
DPI = 200
INK = "#111111"; INK2 = "#444444"; GRID = "#e6e6e6"
plt.rcParams.update({"font.size": 12, "text.color": INK, "figure.facecolor": "white", "savefig.facecolor": "white", "pdf.fonttype": 42})
FAIL = []


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rel(p):
    return os.path.relpath(p, ROOT)


# ------------------------------------------------------------------ summary strings (verbatim source)
IDX_SUM = open(os.path.join(SUM, "index_summary.md")).read()
SUMP = {}
for m in re.finditer(r"^## Page (\d\d): (.+)$", IDX_SUM, re.M):
    pid, title = m.group(1), m.group(2)
    blk = IDX_SUM[m.end():].split("\n## ", 1)[0]
    d = {"title": title}
    for lab, k in (("File", "file"), ("What this tests", "what"), ("Metric", "metric"), ("Pass rule", "rule"), ("Result", "result")):
        mm = re.search(r"^- \*\*" + re.escape(lab) + r":\*\* (.+)$", blk, re.M)
        d[k] = mm.group(1).strip("`")
    SUMP[pid] = d
assert len(SUMP) == 12, "expected 12 summary pages"
SUM_SRC = open(os.path.join(HERE, "figs_thesis_summary.py")).read()
# footer-rule rows of the summary PNGs (top + 0.012 of each page, from a scratch run of figs_thesis_summary.py at 441e97c)
SUM_TOP = {"02": 0.2825, "03": 0.254, "10": 0.311, "11": 0.2825, "12": 0.311}


def sline(pid, field):
    """A reused summary line, verbatim."""
    return dict(text=SUMP[pid][field], src=f"summary page {pid}, {field}", kind="VERBATIM", orig=SUMP[pid][field])


def smod(pid, field, old, new):
    """A reused summary line with one adaptation (the original refers to the summary chart)."""
    o = SUMP[pid][field]
    assert old in o, f"{pid} {field}: '{old}' not in source"
    return dict(text=o.replace(old, new), src=f"summary page {pid}, {field}", kind="MODIFIED", orig=o)


def snew(text):
    return dict(text=text, src="new (this script)", kind="NEW", orig="")


# ------------------------------------------------------------------ number guard corpora (figure index entries)
def section(path, start, stop_pat):
    t = open(path).read(); i = t.index(start); j = t.find(stop_pat, i + len(start))
    return t[i:] if j < 0 else t[i:j]


IDXF = os.path.join(FIGD, "index.md"); IDXR = os.path.join(FIGD, "index_results.md"); IDXD = os.path.join(FIGD, "index_drift.md")
CORP = {"R3": section(IDXR, "## Figure 4.2 (figure", "\n## Table") + section(IDXR, "## Figure 4.2 selection", "\n## Source checks"),
        "R5": open(IDXD).read(),
        "F2": section(IDXF, "### Figure 4.1 (internal F2", "\n### "), "F9": section(IDXF, "### Figure 4.1b", "\n### "),
        "F5": section(IDXF, "### Figure 5.1 (internal F5", "\n### "), "F7": section(IDXF, "### Figure 5.2 (internal F7", "\n### "),
        "F6": section(IDXF, "### Figure 5.3 (internal F6", "\n### ")}
NUM = re.compile(r"\d+(?:\.\d+)?")


def guard(text, corpus, label):
    stray = sorted({n for n in NUM.findall(text)} - set(NUM.findall(corpus)))
    if stray:
        FAIL.append(f"{label}: number(s) {stray} not found in the source")
    return not stray


# ------------------------------------------------------------------ images
def load(path, box=None, trim=False):
    im = Image.open(path).convert("RGB")
    if box:
        im = im.crop(box)
    if trim:                      # trim white margins (keep 12 px)
        a = np.asarray(im.convert("L")); nz = np.where(a < 245)
        x0, x1 = max(nz[1].min() - 12, 0), min(nz[1].max() + 12, a.shape[1]); y0, y1 = max(nz[0].min() - 12, 0), min(nz[0].max() + 12, a.shape[0])
        im = im.crop((x0, y0, x1, y1)); box = (box[0] + x0, box[1] + y0, box[0] + x1, box[1] + y1) if box else (x0, y0, x1, y1)
    return np.asarray(im), box


def squeeze(arr, keep=24, longer=36):
    """Shorten every run of fully blank rows longer than `longer` px to `keep` px (whitespace only; no ink is removed)."""
    blank = (arr.min(2) >= 245).all(1); rows = []; i = 0; runs = []
    while i < len(blank):
        j = i
        while j < len(blank) and blank[j] == blank[i]:
            j += 1
        if blank[i] and j - i > longer:
            rows += list(range(i, i + keep)); runs.append((i, j))
        else:
            rows += list(range(i, j))
        i = j
    return arr[rows], runs


def blank_rows(path, r0, r1):
    a = np.asarray(Image.open(path).convert("L"))
    return bool((a[r0:r1] >= 245).all())


# detailed figures: crops fixed here, each separator band asserted blank
FIG = {}
def fig_src(key, fname, box=None, sep=()):
    p = os.path.join(FIGD, fname)
    for r0, r1 in sep:
        assert blank_rows(p, r0, r1), f"{fname}: rows {r0}-{r1} not blank, crop box would cut a panel"
    arr, b = load(p, box, trim=True)
    arr, runs = squeeze(arr)
    FIG[key] = dict(path=p, arr=arr, box=b, sha=sha(p), squeezed=runs)


fig_src("R3a", "R3_trajectory_overlay.png", (0, 100, 2060, 902), sep=[(889, 915)])
fig_src("R3b", "R3_trajectory_overlay.png", (0, 902, 2060, 1706), sep=[(889, 915), (1688, 1706)])
fig_src("R5a", "R5_drift_unaligned.png", (0, 80, 2379, 817), sep=[(46, 94), (787, 847)])
fig_src("R5bc", "R5_drift_unaligned.png", (0, 817, 2379, 1947), sep=[(787, 847)])
for k, f in (("F2", "F2_heading_stops_sideways_drift.png"), ("F9", "F9_heading_error_closed_loop.png"), ("F5", "F5_T_tags_known_positions.png"),
             ("F7", "F7_L_loop_closure.png"), ("F6", "F6_O_outdoor_indoor.png")):
    fig_src(k, f)


def sum_src(pid):
    """Summary page chart band: from just below the 'What this tests' line to just above the footer rule (asserted)."""
    p = os.path.join(SUM, SUMP[pid]["file"]); a = np.asarray(Image.open(p).convert("RGB")).astype(int); H = a.shape[0]
    row = round((1 - (SUM_TOP[pid] + 0.012)) * H)
    assert (np.abs(a[row, 100:1600] - 230).sum(1) < 6).mean() > 0.99, f"summary {pid}: footer rule not at row {row}"
    blank = (a.min(2) >= 245).all(1)                 # rows with no ink
    r = round((1 - 0.885) * H)                         # top of the 'What this tests' line
    while blank[r]:
        r += 1
    while not blank[r:r + 8].all():                    # end of that text block: first run of 8 blank rows
        r += 1
    y0 = r + 4
    assert y0 < round((1 - 0.755) * H), f"summary {pid}: 'What this tests' text runs into the chart area"
    arr, b = load(p, (0, y0, a.shape[1], row - 4), trim=True)
    FIG["S" + pid] = dict(path=p, arr=arr, box=b, sha=sha(p))


for pid in SUM_TOP:
    sum_src(pid)


def world(path, cap, box=None):
    p = os.path.join(WI, path); arr, b = load(p, box)
    return dict(path=p, arr=arr, box=b, sha=sha(p), cap=cap)


R = "renders/"; OB = "onboard/"
OBX = (0, 31, 640, 480)   # onboard frames: drop the white top text strip, rows 0-30 (trial id and measurement label)
for f in ("fwdc_tex_r1__fwd_y040.png", "fwdplainc_tex_r1__fwd_y040.png", "fwdplainc_blank_r1__fwd_y040.png"):
    a = np.asarray(Image.open(os.path.join(WI, OB, f)).convert("L"))
    assert (a[28:31] == 255).all() and (a[31:40] < 140).all(), f"{f}: the text strip does not end at row 30; crop would be wrong"

# ------------------------------------------------------------------ world check against the recorded trials (read only)
def trial_world(t):
    m = os.path.join(TRIALS, t, "metadata.yaml")
    if os.path.exists(m):
        for ln in open(m):
            if ln.startswith("world:"):
                return ln.split(":", 1)[1].strip(), "metadata.yaml"
    lg = os.path.join(TRIALS, t, "run_trial.log")
    if os.path.exists(lg):
        txt = open(lg, errors="replace").read() + "".join(open(os.path.join(TRIALS, t, "logs", f), errors="replace").read()
                                                            for f in sorted(os.listdir(os.path.join(TRIALS, t, "logs"))) if f.endswith(".log")) if os.path.isdir(os.path.join(TRIALS, t, "logs")) else open(lg, errors="replace").read()
        w = set(re.findall(r"sim/worlds/([a-z_]+)\.sdf", txt))
        if len(w) == 1:
            return w.pop(), "run_trial.log"
    return None, "not found"


rr = lambda pre, post="", reps=(1, 2, 3): [f"{pre}{i}{post}" for i in reps]
CL = ["cl_a_tex_half", "cl_ukf_a_tex_half_v2", "cl_fgo_a_tex_half_v3"] + rr("cl_bcpp_tex_r", "_half") + rr("cl_ukf_b_tex_r", "_half_v2") + rr("cl_fgo_b_tex_r", "_half_v3")
TRS = {"1A": ["dsn_tex_r3"], "1Ab": ["fwdc_tex_r3"],
       "blank": rr("dsn_blank_r") + rr("ds_blank_r") + ["p1c_fwdc_blank", "p1c_fwdplainc_blank"] + rr("fwdc_blank_r") + rr("fwdplainc_blank_r"),
       "1Bh": [f"{d}_{f}_r{i}" for d in ("fwdc", "fwdplainc") for f in ("tex", "blank", "trans") for i in (1, 2, 3)],
       "1Ba": ["dsn_tex_r3"] + rr("fwdc_tex_r"), "1C": CL,
       "2": [f"T_{c}_r{i}" for c in "ABCD" for i in (1, 2, 3)], "3": rr("T_A_r"), "4": ["O_r1", "O_r2", "O_r3b"],
       "5h": ["H_s1_r1", "H_s1_r2", "H_s1_r3", "H_s1far_r1", "H_s1far_r2", "H_s1far_r3b"] + rr("H_s2v2_r") + rr("H_s3v2_r"),
       "5l": ["H_s1_r1", "H_s1_r2", "H_s1_r3", "H_s1far_r1", "H_s1far_r2", "H_s1far_r3b"] + rr("H_s2v2_r") + rr("H_s3v2_r"),
       "5S": ["H_safety_ukf_a_v3", "H_safety_ukf_b_v3", "H_safety_fgo_a_v4", "H_safety_fgo_b_v4"]}
WCHK = {}


def world_check(key, shown):
    """shown: worlds pictured on the page. Every trial's recorded world must be pictured (or be visually identical to a pictured
    one, listed in `same`)."""
    res = []
    for t in TRS[key]:
        w, how = trial_world(t); res.append((t, w, how))
    got = {w for _, w, _ in res}
    WCHK[key] = dict(trials=res, shown=sorted(shown), ok=None not in got and got <= set(shown))
    if not WCHK[key]["ok"]:
        FAIL.append(f"world check {key}: recorded {sorted(map(str, got))} vs pictured {sorted(shown)}")
    return res


# ------------------------------------------------------------------ page layout
def wrap(s, w):
    return "\n".join(textwrap.wrap(s, w, break_long_words=False, break_on_hyphens=False))


PAGES = []
MX = 0.032                     # side margin (figure fraction)


def fit(fig, s, width_in, fs, **kw):
    """Wrap s so that, drawn at font size fs, every line is at most width_in wide (measured with the renderer)."""
    r = fig.canvas.get_renderer()
    for w in range(140, 10, -2):
        t = wrap(s, w)
        tt = fig.text(0, 0, t, fontsize=fs, **kw)
        wd = tt.get_window_extent(renderer=r).width / fig.dpi; tt.remove()
        if wd <= width_in:
            return t
    return wrap(s, 10)


def text_h(fig, t, fs, ls):
    return (t.count("\n") + 1) * fs * ls / 72 / PAGE_H        # height in figure fraction


def page(pid, short, title, what, worlds, wkey, wnames, plot, lines, world_note=None, scope=None, world_label=None, imh=0.92):
    """Title across the top; 'What this tests' (left) beside the world screenshots (right); the plot full width in the middle;
    About / Metric / Pass rule / Result at the bottom. Every text block is wrapped by measured width."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    base = re.sub(r" \(\d of \d\)$", "", title)
    tsrc = next((k for k, v in SUMP.items() if v["title"] == base), None)
    TXT = [("title", dict(text=title, src=f"summary page {tsrc}, title" + (" + page counter" if base != title else ""), kind="VERBATIM",
                          orig=base, equal=tsrc is not None))]
    if tsrc is None:
        FAIL.append(f"page {pid}: title not a summary title")
    UW = 1 - 2 * MX
    # ---- worlds (top right, from the top of the page)
    n = len(worlds); gap = 0.010; IMH = imh                   # image height, inches
    wws = [IMH * w["arr"].shape[1] / w["arr"].shape[0] / PAGE_W for w in worlds]
    x1 = 1 - MX; x0 = x1 - sum(wws) - gap * (n - 1); ytop = 0.978
    lab = fit(fig, world_label or "The world it was flown in (simulator screenshots):", (x1 - x0) * PAGE_W, 11, weight="bold")
    fig.text(x0, ytop, lab, fontsize=11, weight="bold", va="top", ha="left", linespacing=1.15)
    iy = ytop - text_h(fig, lab, 11, 1.25) - 0.006 - IMH / PAGE_H; x = x0; capbot = iy
    for i, (wd, ww) in enumerate(zip(worlds, wws)):
        ax = fig.add_axes([x, iy, ww, IMH / PAGE_H]); ax.imshow(wd["arr"], interpolation="none", aspect="auto"); ax.axis("off")
        c = fit(fig, wd["cap"]["text"], ww * PAGE_W, 11)
        fig.text(x, iy - 0.005, c, fontsize=11, va="top", ha="left", linespacing=1.12, color=INK2)
        capbot = min(capbot, iy - 0.005 - text_h(fig, c, 11, 1.17))
        TXT.append((f"world caption {i + 1}", wd["cap"])); x += ww + gap
    if world_note:
        c = fit(fig, world_note["text"], (x1 - x0) * PAGE_W, 11, style="italic")
        fig.text(x0, capbot - 0.005, c, fontsize=11, va="top", ha="left", color=INK2, style="italic", linespacing=1.12)
        capbot -= 0.005 + text_h(fig, c, 11, 1.17)
        TXT.append(("world note", world_note))
    # ---- title and 'What this tests' (top left, beside the worlds)
    LW = (x0 - MX - 0.02) * PAGE_W
    tt = fit(fig, title, LW, 16.5, weight="bold")
    fig.text(MX, ytop, tt, fontsize=16.5, weight="bold", va="top", ha="left", linespacing=1.12)
    yb = ytop - text_h(fig, tt, 16.5, 1.2) - 0.014
    wt = fit(fig, "What this tests: " + what["text"], LW, 12.5, style="italic")
    fig.text(MX, yb, wt, fontsize=12.5, style="italic", color=INK2, va="top", ha="left", linespacing=1.22)
    TXT.append(("What this tests", what))
    hdr_bot = min(yb - text_h(fig, wt, 12.5, 1.27), capbot) - 0.01
    # ---- footer (bottom up)
    FS, LS, GAP, LABW = 11, 1.17, 0.007, 0.13
    blocks = [(lab, fit(fig, d["text"], (UW - LABW) * PAGE_W, FS), d) for lab, d in lines]
    h = sum(text_h(fig, w, FS, LS) + GAP for _, w, _ in blocks)
    y = top = 0.022 + h
    fig.add_artist(Line2D([MX, 1 - MX], [top + 0.008, top + 0.008], color=GRID, lw=1.2, transform=fig.transFigure))
    for lab, w, d in blocks:
        fig.text(MX, y, lab, fontsize=FS, weight="bold", va="top", ha="left")
        fig.text(MX + LABW, y, w, fontsize=FS, va="top", ha="left", linespacing=LS)
        y -= text_h(fig, w, FS, LS) + GAP
        TXT.append((lab.rstrip(":"), d))
    # ---- plot
    pb, pt = top + 0.016, hdr_bot
    ph_in = (pt - pb) * PAGE_H; pw_max = UW * PAGE_W
    a = plot["arr"]; asp = a.shape[1] / a.shape[0]
    w_in = min(pw_max, ph_in * asp)
    if plot["key"].startswith("S"):
        w_in = min(w_in, a.shape[1] / 150)    # summary charts (150 dpi): never enlarged
    h_in = w_in / asp
    ax = fig.add_axes([(1 - w_in / PAGE_W) / 2, pt - h_in / PAGE_H - (ph_in - h_in) / PAGE_H / 2, w_in / PAGE_W, h_in / PAGE_H])
    ax.imshow(a, interpolation="none", aspect="auto"); ax.axis("off")
    scale = w_in / (a.shape[1] / DPI)          # displayed size relative to the figure's native 200 dpi size
    assert ph_in > 3.0, f"{pid}: plot area only {ph_in:.2f} in tall"
    # ---- number guard on NEW / MODIFIED text
    corpus = " ".join(SUMP[s][k] for s in (scope or []) for k in ("what", "metric", "rule", "result")) + " " + plot.get("corpus", "")
    for lab, d in TXT:
        if d["kind"] in ("NEW", "MODIFIED"):
            d["guard"] = guard(d["text"], corpus, f"page {pid} {lab}")
        elif d["kind"] == "VERBATIM" and lab != "title":
            d["equal"] = d["text"] == d["orig"]
            if not d["equal"]:
                FAIL.append(f"page {pid} {lab}: verbatim line differs from its source")
    if wkey:
        world_check(wkey, wnames)
    fn = f"wt_{pid}_{short}.png"
    fig.savefig(os.path.join(OUTD, fn), dpi=DPI)
    PAGES.append(dict(id=pid, short=short, title=title, file=fn, fig=fig, txt=TXT, worlds=worlds, plot=plot, scale=scale,
                      plot_h=h_in, wkey=wkey))
    print(f"wrote {fn}  plot {w_in:.2f} x {h_in:.2f} in, scale {scale:.2f}")


def P(key, corpus_key=None, extra=""):
    d = dict(FIG[key]); d["key"] = key; d["corpus"] = CORP.get(corpus_key or key, "") + " " + extra; return d


# world screenshots (captions are NEW text)
W_TEX = lambda: world(R + "corridor_textured__interior.jpg", snew("Inside: checkerboard floor, plain walls, no roof"))
W_TEXA = lambda: world(R + "corridor_textured__angled.jpg", snew("Outside view of the same corridor"))
W_FWDC = lambda: world(R + "corridor_textured_fwdc__interior.jpg", snew("Inside: painted-line walls, roof, checkerboard floor"))
CAP_BL = "Blank floor, "

# =================================================================== pages
# 1A: aligned paths (R3 a), then the same flight unaligned (R5 a, R5 b+c)
S01 = [("Pass rule:", sline("01", "rule")), ("Result:", sline("01", "result"))]
M01 = smod("01", "metric", " (the vertical lines show the range over the flights)", "")
page("01", "1A_paths", SUMP["01"]["title"] + " (1 of 3)", sline("01", "what"), [W_TEX(), W_TEXA()], "1A", ["corridor_textured"], P("R3a", "R3"),
     [("About this plot:", snew("one example flight (flight 3 of the 9), seen from above. Grey: the true path. Dashed: each "
                                "estimate after the best-fit alignment used for scoring; the key gives that flight's score. "
                                "The sideways axis is stretched 3.0× so the errors are visible.")), ("Metric:", M01)] + S01, scope=["01"])
page("02", "1A_drift", SUMP["01"]["title"] + " (2 of 3)", sline("01", "what"), [W_TEX(), W_TEXA()], "1A", ["corridor_textured"], P("R5a", "R5"),
     [("About this plot:", snew("the same flight 3 drawn WITHOUT the alignment, so the sideways drift caused by heading error is "
                                "visible: it reaches tens of metres by the end of the corridor. The scored error (previous page) "
                                "removes this constant turn first.")), ("Metric:", M01)] + S01, scope=["01"])
page("03", "1A_error_vs_distance", SUMP["01"]["title"] + " (3 of 3)", sline("01", "what"), [W_TEX(), W_TEXA()], "1A", ["corridor_textured"],
     P("R5bc", "R5"),
     [("About this plot:", snew("the same flight 3, without the alignment: error along the corridor (top) and sideways (bottom) "
                                "against the distance flown, metres. The sideways error grows fastest.")), ("Metric:", M01)] + S01,
     scope=["01"])

# blank floor: summary chart
page("04", "blank_floor", SUMP["02"]["title"], sline("02", "what"),
     [world(R + "corridor_blank__interior.jpg", snew(CAP_BL + "plain walls, no roof (standard sensors)")),
      world(R + "corridor_blank_fwdc__interior.jpg", snew(CAP_BL + "painted-line walls and roof")),
      world(R + "corridor_blank_fwdplainc__interior.jpg", snew(CAP_BL + "plain walls and roof"))],
     "blank", ["corridor_blank", "corridor_blank_fwdc", "corridor_blank_fwdplainc"], P("S02"),
     [("Metric:", sline("02", "metric")), ("Pass rule:", sline("02", "rule")), ("Result:", sline("02", "result"))], scope=["02"])

# 1B heading check: summary table, with what the forward camera sees
page("05", "1B_heading_check", SUMP["03"]["title"], sline("03", "what"),
     [world(OB + "fwdc_tex_r1__fwd_y040.png", snew("Painted-line walls, checkerboard floor"), OBX),
      world(OB + "fwdplainc_tex_r1__fwd_y040.png", snew("Plain walls, checkerboard floor"), OBX),
      world(OB + "fwdplainc_blank_r1__fwd_y040.png", snew("Plain walls, blank floor"), OBX)],
     "1Bh", ["corridor_textured_fwdc", "corridor_blank_fwdc", "corridor_transition_fwdc", "corridor_textured_fwdplainc",
             "corridor_blank_fwdplainc", "corridor_transition_fwdplainc"], P("S03"),
     [("Metric:", sline("03", "metric")), ("Pass rule:", sline("03", "rule")), ("Result:", sline("03", "result"))],
     world_note=snew("Orange cross: where the camera's heading measurement points. The flights also used the half-and-half floor "
                     "(not pictured)."), scope=["03"],
     world_label="What the forward camera saw in these worlds (frames from the recorded flights):", imh=1.3)

# 1B accuracy: R3 b
page("06", "1B_accuracy", SUMP["04"]["title"], sline("04", "what"), [W_FWDC(), world(R + "corridor_textured_fwdc__angled_cutaway.jpg",
     snew("Outside view, roof cut away"))], "1Ab", ["corridor_textured_fwdc"], P("R3b", "R3"),
     [("About this plot:", snew("one example flight (flight 3), seen from above after the best-fit alignment. Grey: the true path. "
                                "Dashed: without the camera heading. Solid: with it (UKF and FGO only); the solid lines lie on "
                                "the true path. The key gives each line's score. Sideways axis stretched 3.0×.")),
      ("Metric:", sline("04", "metric")), ("Pass rule:", sline("04", "rule")), ("Result:", sline("04", "result"))], scope=["04"])

# 1C: F2 (without the heading: wall contact) and F9 (with the heading: five checks)
W_HALF = lambda: [world(R + "corridor_textured_half_fwdc__interior.jpg", snew("Inside: painted-line walls, roof, checkerboard floor")),
                  world(R + "corridor_textured_half_fwdc__angled_cutaway.jpg", snew("Outside view, roof cut away"))]
CHECKS = ["finish the corridor without touching a wall", "stay within 6.0 m of the centre line",
          "heading error within 1.0° (95% of the time), 2.0° at most", "sideways speed at most 0.25 m/s", "no oscillation"]
for c in CHECKS:
    assert f'T("• {c}")' in SUM_SRC or f'"• {c}"' in SUM_SRC, f"check text '{c}' not in figs_thesis_summary.py"
page("07", "1C_no_heading", SUMP["05"]["title"], sline("05", "what"), W_HALF(), "1C", ["corridor_textured_half_fwdc"], P("F2"),
     [("About this plot:", snew("the true path of every flight seen from above (sideways axis stretched 3.0×). Dashed: without "
                                "the camera heading, 1 flight each, ending where the drone touched the wall (X). Solid: with the "
                                "camera heading, 3 flights each (their result is on the next page).")),
      ("Metric:", sline("05", "metric")),
      ("Pass rule:", smod("05", "rule", " (grey)", " (written next to each wall contact on the plot)")),
      ("Result:", sline("05", "result"))], scope=["05"])
page("08", "1C_with_heading", SUMP["06"]["title"], sline("06", "what"), W_HALF(), "1C", ["corridor_textured_half_fwdc"], P("F9", extra=" ".join(CHECKS)),
     [("About this plot:", snew("heading error (the estimated direction the drone faces minus the true one) against time. Dashed: "
                                "without the camera heading, growing until the wall (X). Solid: with the camera heading, 3 flights "
                                "each, staying near zero inside the grey band; the inset enlarges them.")),
      ("Metric:", smod("06", "metric", "); the bars show the largest sideways distance from the centre line in any of them, metres (simulator at half real time, flight speed unchanged).",
                       "; simulator at half real time, flight speed unchanged).")),
      ("Pass rule:", smod("06", "rule", "all five checks listed on the right", "all five checks (" + "; ".join(CHECKS) + ")")),
      ("Result:", sline("06", "result"))], scope=["06"])

# 2, 3: the tag room
W_ROOM = lambda: [world(R + "room_tags__angled.jpg", snew("The tag room from above, at an angle")),
                  world(R + "room_tags__top_room.jpg", snew("Floor tags, from above"))]
page("09", "2_known_tags", SUMP["07"]["title"], sline("07", "what"), W_ROOM(), "2", ["room_tags"], P("F5"),
     [("About this plot:", snew("error for each number of tags, in centimetres. Solid lines, filled marks: live estimates. Dashed "
                                "lines, open marks: the flight re-solved afterwards (hindsight). Small marks: the single flights; "
                                "large marks: their mean.")),
      ("Metric:", sline("07", "metric")), ("Pass rule:", sline("07", "rule")), ("Result:", sline("07", "result"))], scope=["07"])
page("10", "3_loop_closure", SUMP["08"]["title"], sline("08", "what"), W_ROOM(), "3", ["room_tags"], P("F7"),
     [("About this plot:", snew("the FGO's error on each lap of the 6 m square, in centimetres, one line per flight. Left: with "
                                "loop closure. Right: without it. Solid: live. Dashed: hindsight.")),
      ("Metric:", sline("08", "metric")), ("Pass rule:", sline("08", "rule")), ("Result:", sline("08", "result"))], scope=["08"])

# 4: outdoor-indoor
page("11", "4_outdoor_indoor", SUMP["09"]["title"], sline("09", "what"),
     [world(R + "outdoor_indoor__entrance.jpg", snew("Outdoors: the building entrance (GPS on)")),
      world(R + "outdoor_indoor__indoor.jpg", snew("Inside the building (GPS off)"))], "4", ["outdoor_indoor"], P("F6"),
     [("About this plot:", snew("error against time for flight 1 (of 3). Grey shading: indoors without GPS. Solid: live "
                                "estimates. Dashed: hindsight. EKF3's sudden drop at the end is its reset to GPS outdoors.")),
      ("Metric:", sline("09", "metric")), ("Pass rule:", sline("09", "rule")), ("Result:", sline("09", "result"))], scope=["09"])

# 5, 5S: summary charts with the wall-tag room
W_WALL = lambda note: [world(R + "room_wall_tag_far__angled.jpg", snew(note)),
                       world(R + "room_wall_tag_far__walltag.jpg", snew("The printed tag on the wall"))]
for pid, sp, short, key, worlds_, note in (
        ("12", "10", "5_hold", "5h", ["room_wall_tag", "room_wall_tag_far"], "The room with the wall tag (two start spots were used; the room is the same)"),
        ("13", "11", "5_tag_loss", "5l", ["room_wall_tag", "room_wall_tag_far"], "The room with the wall tag (two start spots were used; the room is the same)"),
        ("14", "12", "5S_safety", "5S", ["room_wall_tag_far"], "The room with the wall tag")):
    page(pid, short, SUMP[sp]["title"], sline(sp, "what"), W_WALL(note), key, worlds_, P("S" + sp),
         [("Metric:", sline(sp, "metric")), ("Pass rule:", sline(sp, "rule")), ("Result:", sline(sp, "result"))], scope=[sp])

# =================================================================== contents + how-to, PDF
figc = plt.figure(figsize=(PAGE_W, PAGE_H))
figc.text(MX + 0.013, 0.945, "Results walkthrough: contents", fontsize=21, weight="bold", va="top")
NOTE = snew("Each page shows one experiment: what it tests, the simulated world it was flown in (screenshots, top right), the "
            "original detailed plot, and under it what the plot shows, the metric, the pass rule and the result. In the corridor "
            "plots, dashed lines mean without the camera heading and solid lines with it. Where an experiment has no detailed "
            "plot, its summary chart is shown instead.")
guard(NOTE["text"], "", "contents note")
figc.text(MX + 0.013, 0.885, wrap(NOTE["text"], 118), fontsize=13, va="top", color=INK2, linespacing=1.3)
rows_c = [("", "How to read these pages")] + [(str(i + 1), p["title"]) for i, p in enumerate(PAGES)]
for i, (n, t) in enumerate(rows_c):
    yy = 0.74 - i * 0.046
    figc.text(0.07, yy, n, fontsize=13, va="top", ha="right", color=INK2)
    figc.text(0.09, yy, t, fontsize=13, va="top")
    figc.text(0.955, yy, f"page {i + 2}", fontsize=12, va="top", ha="right", color=INK2)
assert 0.74 - (len(rows_c) - 1) * 0.046 > 0.03, "contents page overflows"
figc.savefig(os.path.join(OUTD, "wt_00a_contents.png"), dpi=DPI)
HOWTO = os.path.join(SUM, "summary_00_how_to_read.png")
figh = plt.figure(figsize=(PAGE_W, PAGE_H)); axh = figh.add_axes([0, 0, 1, 1]); axh.imshow(np.asarray(Image.open(HOWTO).convert("RGB")), interpolation="none", aspect="auto"); axh.axis("off")
figh.savefig(os.path.join(OUTD, "wt_00b_how_to_read.png"), dpi=DPI)
with PdfPages(PDF) as pdf:
    for f in [figc, figh] + [p["fig"] for p in PAGES]:
        pdf.savefig(f)
plt.close("all")

# =================================================================== provenance index
nverb = sum(d["kind"] == "VERBATIM" for p in PAGES for lab, d in p["txt"]); okverb = sum(d.get("equal", False) for p in PAGES for _, d in p["txt"])
nmod = sum(d["kind"] == "MODIFIED" for p in PAGES for _, d in p["txt"]); nnew = sum(d["kind"] == "NEW" for p in PAGES for _, d in p["txt"]) + 1
md = ["# Results walkthrough: index and provenance", "",
      f"*Generated by `eval/figs_results_walkthrough.py` at commit `{COMMIT}`. COMPOSITION ONLY: existing, cross-checked images are "
      "placed on pages; nothing is re-plotted, recomputed or re-run. All provenance is here; the pages carry none.*", "",
      f"**Checks:** {okverb}/{nverb} reused lines equal their source string exactly; {nmod} lines MODIFIED (each listed with its "
      f"original); {nnew} NEW lines (number guard: every number in a NEW or MODIFIED line occurs in the figure's own index entry or in "
      f"that page's summary strings: {'PASS' if not [f for f in FAIL if 'number' in f] else 'FAIL'}); world check "
      f"{sum(w['ok'] for w in WCHK.values())}/{len(WCHK)} page groups match the trials' recorded worlds. Failures: {FAIL or 'none'}.", "",
      "**Text source.** Reused lines come from `docs/thesis/summary/index_summary.md`, which `eval/figs_thesis_summary.py` writes "
      "from the same strings it draws on the summary pages. Before building, that script was re-run on a scratch copy at HEAD "
      "`441e97c` with only its output folder redirected: the regenerated `index_summary.md` was identical apart from its commit line, "
      "and all 13 summary PNGs were byte-identical to the committed ones; the footer-rule rows used to crop the summary charts "
      "(`top` + 0.012 = 0.2945 / 0.266 / 0.323 / 0.2945 / 0.323 for summary pages 02 / 03 / 10 / 11 / 12) come from that run and are "
      "asserted on the committed PNGs at build time. The five closed-loop check phrases inserted into page 08's pass rule are "
      "asserted to occur in `eval/figs_thesis_summary.py`.", "",
      "**Layout.** A4 landscape; PNGs at 200 dpi; images embedded unresampled (`interpolation='none'`). Text ≥ 11 pt (Metric, Pass "
      "rule, Result, About, world captions: 11 pt; What this tests: 12.5 pt; titles 16.5 pt). 'scale' below = displayed width ÷ the "
      "image's width at 200 dpi (the summary charts are 150 dpi images and are never enlarged beyond their own size).", "",
      f"**PDF:** `results_walkthrough.pdf` = contents (`walkthrough/wt_00a_contents.png`), 'How to read these pages' (the summary's "
      f"`summary_00_how_to_read.png`, sha256 `{sha(HOWTO)}`, placed full page unchanged), then pages 01–14 below.", "",
      f"**Contents-page note (NEW):** {NOTE['text']}", ""]
WTR = {"1A": "dsn_tex_r3 (R3 a, R5)", "1Ab": "fwdc_tex_r3 (R3 b)", "blank": "the 14 blank-floor flights of Table 4.2", "1Bh": "the 18 heading-check flights",
       "1C": "the 12 closed-loop flights of Figures 4.1 / 4.1b", "2": "T_A–D r1–3", "3": "T_A r1–3", "4": "O_r1, O_r2, O_r3b",
       "5h": "S1 near and far, S2v2, S3v2", "5l": "S1 near and far, S2v2, S3v2", "5S": "the four final safety runs"}
for p in PAGES:
    pl = p["plot"]
    md += [f"## Page {p['id']}: {p['title']}", "", f"- **File:** `walkthrough/{p['file']}`",
           f"- **Plot:** `{rel(pl['path'])}` (sha256 `{pl['sha']}`), crop box (x0, y0, x1, y1) px: {tuple(int(v) for v in pl['box']) if pl['box'] else 'none (whole image)'}; "
           f"shown {p['plot_h']:.2f} in tall, scale {p['scale']:.2f}" +
           (f"; blank-row runs (start, end; rows of the cropped image) shortened to 24 px, whitespace only: {[(int(x), int(y)) for x, y in pl['squeezed']]}" if pl.get("squeezed") else "")]
    for i, w in enumerate(p["worlds"]):
        md.append(f"- **World image {i + 1}:** `{rel(w['path'])}` (sha256 `{w['sha']}`)" + (f", crop box {w['box']} (drops the frame's text strip)" if w["box"] else ""))
    if p["wkey"]:
        wc = WCHK[p["wkey"]]
        md.append(f"- **World check ({'PASS' if wc['ok'] else 'FAIL'}):** pictured {', '.join(wc['shown'])}; flights {WTR[p['wkey']]}: " +
                  "; ".join(f"{t} → {w} ({how})" for t, w, how in wc["trials"]))
    md += ["", "| line | kind | source | check | text |", "|---|---|---|---|---|"]
    for lab, d in p["txt"]:
        chk = ("equal" if d.get("equal") else "**DIFFERS**") if d["kind"] == "VERBATIM" else ("numbers found" if d.get("guard", True) else "**stray number**")
        t = d["text"].replace("|", "¦")
        if d["kind"] == "MODIFIED":
            t += f" — ORIGINAL: {d['orig'].replace('|', '¦')}"
        md.append(f"| {lab} | {d['kind']} | {d['src']} | {chk} | {t} |")
    md.append("")
md += ["## Not included, and why", "",
       "- **Figure 3.1 (system architecture):** method, not a result.",
       "- **Tables A.1–A.3 and the other thesis tables:** tables, not time-series or path plots; their pass/fail content is in the "
       "summary lines already shown.",
       "- **Experiments with no detailed time-series or path plot** use their summary chart (cropped to the chart): the blank floor "
       "(page 04), the 1B heading check (05), Experiment 5 hold (12) and tag loss (13), and 5S (14).",
       "- **No onboard frame of the half-and-half floor with plain walls** exists (`world_images/index.md` §4); page 05 notes that "
       "the half-and-half floor is not pictured.", ""]
open(INDEX, "w").write("\n".join(md))
print(f"verbatim {okverb}/{nverb}, modified {nmod}, new {nnew}; world checks {sum(w['ok'] for w in WCHK.values())}/{len(WCHK)}; "
      f"failures: {FAIL or 'none'}; wrote {PDF}, {INDEX}")
sys.exit(1 if FAIL else 0)
