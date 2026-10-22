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
import hashlib, json, os, re, subprocess, sys, textwrap
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


fig_src("R3a", "R3_trajectory_overlay.png", (0, 100, 2020, 902), sep=[(889, 915)])
fig_src("R3b", "R3_trajectory_overlay.png", (0, 902, 2020, 1706), sep=[(889, 915)])
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
TRS = {"1A": [f"dsn_tex_r{i}" for i in range(1, 10)],
       "blank": rr("dsn_blank_r") + rr("ds_blank_r") + ["p1c_fwdc_blank", "p1c_fwdplainc_blank"] + rr("fwdc_blank_r") + rr("fwdplainc_blank_r"),
       "1B": [f"{d}_{f}_r{i}" for d in ("fwdc", "fwdplainc") for f in ("tex", "blank", "trans") for i in (1, 2, 3)],
       "1C": CL,
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


def world_page(pid, short, title, worlds, world_note, world_label, TXT):
    """The page that opens each experiment: the simulated world(s) that plot's flights were flown in, as large as the page allows
    (ruling 2026-10-19: 'one page for the plot/table, and then the next page with the actual world')."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    UW = 1 - 2 * MX; ytop = 0.978
    title = re.sub(r" \(\d+ of \d+\)$", "", title)      # the world page opens the experiment (ruling 2026-10-21): no page counter
    tt = fit(fig, title, UW * PAGE_W, 16.5, weight="bold")
    fig.text(MX, ytop, tt, fontsize=16.5, weight="bold", va="top", ha="left", linespacing=1.12)
    y = ytop - text_h(fig, tt, 16.5, 1.2) - 0.012
    lab = world_label or "The world it was flown in (simulator screenshots):"
    fig.text(MX, y, lab, fontsize=13, weight="bold", va="top", ha="left"); y -= text_h(fig, lab, 13, 1.25) + 0.012
    bottom = 0.04
    if world_note:
        c = fit(fig, world_note["text"], UW * PAGE_W, 12, style="italic")
        fig.text(MX, bottom, c, fontsize=12, va="bottom", ha="left", color=INK2, style="italic", linespacing=1.15)
        bottom += text_h(fig, c, 12, 1.2) + 0.015
        TXT.append(("world note", world_note))
    n = len(worlds); rows = 1 if n <= 2 else 2; cols = -(-n // rows); gx, gy = 0.02, 0.03
    caph = max(text_h(fig, fit(fig, w["cap"]["text"], (UW - gx * (cols - 1)) / cols * PAGE_W, 13), 13, 1.2) for w in worlds) + 0.01
    cw = (UW - gx * (cols - 1)) / cols; ch = ((y - bottom) - gy * (rows - 1)) / rows - caph
    # the grid uses the largest image height that fits every cell; centre it vertically in the free space
    hmax = max(min(cw * PAGE_W, ch * PAGE_H * w["arr"].shape[1] / w["arr"].shape[0]) / (w["arr"].shape[1] / w["arr"].shape[0]) for w in worlds) / PAGE_H
    used = rows * (hmax + caph) + gy * (rows - 1); y -= max(0.0, ((y - bottom) - used) / 2); ch = hmax
    for i, w in enumerate(worlds):
        r, c_ = divmod(i, cols)
        asp = w["arr"].shape[1] / w["arr"].shape[0]
        wi = min(cw * PAGE_W, ch * PAGE_H * asp); hi = wi / asp
        cx = MX + c_ * (cw + gx) + (cw - wi / PAGE_W) / 2
        top = y - r * (ch + caph + gy)
        ax = fig.add_axes([cx, top - hi / PAGE_H, wi / PAGE_W, hi / PAGE_H]); ax.imshow(w["arr"], interpolation="none", aspect="auto"); ax.axis("off")
        cap = fit(fig, w["cap"]["text"], wi, 13)
        fig.text(cx, top - hi / PAGE_H - 0.008, cap, fontsize=13, va="top", ha="left", color=INK2, linespacing=1.15)
        TXT.append((f"world caption {i + 1}", w["cap"]))
    fig.savefig(os.path.join(OUTD, f"wt_{pid}w_{short}_world.png"), dpi=DPI)
    return fig


def page(pid, short, title, what, worlds, wkey, wnames, plot, lines, world_note=None, scope=None, world_label=None, imh=0.92, world=True):
    """Title across the top; 'What this tests' (left) beside the world screenshots (right); the plot full width in the middle;
    About / Metric / Pass rule / Result at the bottom. Every text block is wrapped by measured width."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    base = re.sub(r" \(\d+ of \d+\)$", "", title)
    tsrc = next((k for k, v in SUMP.items() if v["title"] == base), None)
    TXT = [("title", dict(text=title, src=f"summary page {tsrc}, title" + (" + page counter" if base != title else ""), kind="VERBATIM",
                          orig=base, equal=tsrc is not None))]
    if tsrc is None:
        FAIL.append(f"page {pid}: title not a summary title")
    UW = 1 - 2 * MX
    # ---- title and 'What this tests' (full width; the worlds have their own page, ruling 2026-10-19)
    ytop = 0.978; LW = UW * PAGE_W
    tt = fit(fig, title, LW, 16.5, weight="bold")
    fig.text(MX, ytop, tt, fontsize=16.5, weight="bold", va="top", ha="left", linespacing=1.12)
    yb = ytop - text_h(fig, tt, 16.5, 1.2) - 0.014
    wt = fit(fig, "What this tests: " + what["text"], LW, 12.5, style="italic")
    fig.text(MX, yb, wt, fontsize=12.5, style="italic", color=INK2, va="top", ha="left", linespacing=1.22)
    TXT.append(("What this tests", what))
    hdr_bot = yb - text_h(fig, wt, 12.5, 1.27) - 0.01
    # ---- footer (bottom up)
    FS, LS, GAP, LABW = 11, 1.17, 0.007, 0.145
    # a FITTED / NOT FITTED label (request 2026-10-21) is drawn in bold as the first line of the About block; the explanation
    # follows on the next lines (an empty first line in the normal-weight text keeps the two aligned)
    blocks = [(lab, ((d["label"] + "\n") if d.get("label") else "") + fit(fig, d["body"] if d.get("label") else d["text"], (UW - LABW) * PAGE_W, FS), d)
              for lab, d in lines]
    h = sum(text_h(fig, w, FS, LS) + GAP for _, w, _ in blocks)
    y = top = 0.022 + h
    fig.add_artist(Line2D([MX, 1 - MX], [top + 0.008, top + 0.008], color=GRID, lw=1.2, transform=fig.transFigure))
    for lab, w, d in blocks:
        fig.text(MX, y, lab, fontsize=FS, weight="bold", va="top", ha="left")
        if d.get("label"):
            fig.text(MX + LABW, y, d["label"], fontsize=FS, weight="bold", va="top", ha="left", color="#000000")
            fig.text(MX + LABW, y, "\n" + w.split("\n", 1)[1], fontsize=FS, va="top", ha="left", linespacing=LS)
        else:
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
    wfig = world_page(pid, short, title, worlds, world_note, world_label, TXT) if world else None   # once per experiment (ruling 2026-10-21)
    PAGES.append(dict(id=pid, short=short, title=title, file=fn, fig=fig, wfig=wfig, txt=TXT, worlds=worlds, plot=plot, scale=scale,
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
# Ruling 2026-10-21 (user): the world page ONCE per experiment, after its last plot page; every flight of an experiment shown
# (new all-flights plots from eval/figs_walkthrough_flights.py, docs/thesis/summary/flights/); error against time instead of
# against distance; a 'where the drone really flew' page per experiment; Experiment 1C heading-error graphs never overlaid.
FLD = os.path.join(SUM, "flights"); FLIDX = open(os.path.join(FLD, "index_flights.md")).read()
FLCHK = json.load(open(os.path.join(FLD, "checks.json")))
for fid in FLCHK["figs"]:
    p_ = os.path.join(FLD, f"fl_{fid}.png"); arr, b = load(p_, None, trim=True)
    FIG["FL_" + fid] = dict(path=p_, arr=arr, box=b, sha=sha(p_))


def PF(fid, extra=""):
    """An all-flights figure; number-guard corpus = its own checked numbers + the flights index (every printed number is checked there)."""
    d = dict(FIG["FL_" + fid]); d["key"] = "FL_" + fid
    d["corpus"] = " ".join(FLCHK["figs"][fid]["numbers"]) + " " + FLIDX + " " + extra; return d


W_TEX = lambda: world(R + "corridor_textured__interior.jpg", snew("Inside: checkerboard floor, plain walls, no roof"))
W_TEXA = lambda: world(R + "corridor_textured__angled.jpg", snew("Outside view of the same corridor"))
W_FWDC = lambda: world(R + "corridor_textured_fwdc__interior.jpg", snew("Inside: painted-line walls, roof, checkerboard floor"))
CAP_BL = "Blank floor, "
M01 = smod("01", "metric", " (the vertical lines show the range over the flights)", "")
L01 = [("Metric:", M01), ("Pass rule:", sline("01", "rule")), ("Result:", sline("01", "result"))]
T01 = SUMP["01"]["title"]; N1A = 6
A = lambda t: ("About this plot:", snew(t))
YAWS = "aligned by a rotation about the vertical and a shift, which gives the same average error (ATE) as the standard alignment"


# ---- FITTED / NOT FITTED labels (user request 2026-10-21: "make it clear which ones have fitted, maybe put it in bold and also
# explain briefly in the about the plot what the fitting is doing and trying to show"). Every plot page carries exactly one label,
# drawn in bold as the first line of its About block; the explanation follows in plain words.
def AL(label, text):
    """About line with a bold FITTED / NOT FITTED label (NEW text; the label is part of the number-guarded text)."""
    d = snew(label + " " + text); d["label"] = label; d["body"] = text[0].upper() + text[1:]
    return ("About this plot:", d)


def SH(text):
    """'This plot shows:' (NEW): what is drawn, where it differs from the registered Metric line (which is kept as is)."""
    return ("This plot shows:", snew(text))


FIT_L = "FITTED (aligned):"
FIT_X = ("the whole estimated path is slid and turned as one rigid piece, about the vertical only, to lie as close as possible "
         "to the true path; it cannot bend or stretch it. So the error left measures how well the estimator tracked the shape of "
         "the flight, not which way it happened to start pointing. This makes the error smaller than the raw drift (see the "
         "not-fitted pages). This fit gives the same average error (ATE) as the standard alignment used for the score.")
FIT_XC = FIT_X[0].upper() + FIT_X[1:]
RAW_L = "NOT FITTED (raw, from take-off):"
RAW_X = "This is the raw error a drone flying on this estimate would face."
REAL_L = "NOT FITTED (the drone's real path):"
REAL_X = "Nothing is fitted: this is where the drone really was, from the simulator."
SH_TRUTH = SH("where the drone really flew (simulator truth), not an error; the experiment's score below is the estimators' "
              "fitted average error (ATE).")
SH_FPATH = SH("the fitted estimated paths; the experiment's score below is the fitted average error (ATE) between these and the "
              "true paths.")
SH_FERR = SH("the fitted error against time, metres; the root mean square of each line is that flight's score (fitted average "
             "error, ATE).")
SH_RPATH = SH("the raw (not fitted) estimated paths from take-off; the experiment's score below is the fitted average error (ATE).")
SH_RERR = SH("the raw (not fitted) error against time, metres; the experiment's score below is the fitted average error (ATE).")

# ---- 1A
page("01", "1A_truth", f"{T01} (1 of {N1A})", sline("01", "what"), [], None, [], PF("1A_truth"),
     [AL(REAL_L, REAL_X + " It took off, climbed, flew straight up the corridor for about five minutes (the cruise) and landed; "
         "the 9 flights are almost identical. The estimators never steered: they only watched (offline)."), SH_TRUTH] + L01,
     scope=["01"], world=False)
page("02", "1A_aligned_paths", f"{T01} (2 of {N1A})", sline("01", "what"), [], None, [], PF("1A_aligned_paths"),
     [AL(FIT_L, "every flight's estimated path, cruise only, one panel per estimator: " + FIT_X + " Because of the fit, and "
         "because the cruise starts after take-off and climb, the lines do not start at the take-off point."), SH_FPATH] + L01,
     scope=["01"], world=False)
page("02f", "1A_fig42", f"{T01} (3 of {N1A})", sline("01", "what"), [], None, [], P("R3a", "R3"),
     [AL(FIT_L, "Figure 4.2 (a) of the thesis: one example flight (flight 3, chosen beforehand as the median flight), all three estimators on one plot, cruise only. " + FIT_XC), SH_FPATH] + L01, scope=["01"], world=False)
page("03", "1A_aligned_err", f"{T01} (4 of {N1A})", sline("01", "what"), [], None, [], PF("1A_aligned_err"),
     [AL(FIT_L, "the error against time, every flight, cruise only: " + FIT_X + " The shape (large at both ends, small where the "
         "fitted path crosses the true one) comes from the fit."), SH_FERR] + L01, scope=["01"], world=False)
page("04", "1A_unaligned_paths", f"{T01} (5 of {N1A})", sline("01", "what"), [], None, [], PF("1A_unaligned_paths"),
     [AL(RAW_L, "the estimates exactly as they came out, from take-off. " + RAW_X + " With no heading sensor each estimate slowly "
         "turns, so it drifts sideways by tens of metres; the fit used for the score removes this turn. UKF and FGO positions are "
         "in their own take-off frame, relabelled (North, East) = (x, −y)."), SH_RPATH] + L01, scope=["01"], world=False)
page("05", "1A_unaligned_err", f"{T01} (6 of {N1A})", sline("01", "what"), [W_TEX(), W_TEXA()], "1A", ["corridor_textured"],
     PF("1A_unaligned_err"),
     [AL(RAW_L, "the error against time, every flight, with nothing fitted. " + RAW_X + " It grows steadily during the cruise, "
         "mostly sideways (previous page)."), SH_RERR] + L01, scope=["01"])

# ---- blank floor: summary chart (no per-flight plots made here)
page("06", "blank_floor", SUMP["02"]["title"], sline("02", "what"),
     [world(R + "corridor_blank__interior.jpg", snew(CAP_BL + "plain walls, no roof (standard sensors)")),
      world(R + "corridor_blank_fwdc__interior.jpg", snew(CAP_BL + "painted-line walls and roof")),
      world(R + "corridor_blank_fwdplainc__interior.jpg", snew(CAP_BL + "plain walls and roof"))],
     "blank", ["corridor_blank", "corridor_blank_fwdc", "corridor_blank_fwdplainc"], P("S02"),
     [AL("NOT FITTED (raw, from the moment the camera stops):", "Nothing is turned or best-fitted: each estimate is only moved "
         "so that it starts at the true position when the camera stops, so the error shown is the raw drift a drone flying on "
         "it would face from then on."),
      ("Metric:", sline("02", "metric")), ("Pass rule:", sline("02", "rule")), ("Result:", sline("02", "result"))], scope=["02"])

# ---- 1B: heading check (summary table), then accuracy on all 3 flights (fitted, then not fitted); one world page for 1B
T04 = SUMP["04"]["title"]; L04 = [("Metric:", sline("04", "metric")), ("Pass rule:", sline("04", "rule")), ("Result:", sline("04", "result"))]
N1B = 8
# the summary Result says "(see the previous page)", meaning the heading check; true only on the first 1B page (08)
L04b = [L04[0], L04[1], ("Result:", smod("04", "result", "(see the previous page)", "(see the heading-check page just before this experiment)"))]
page("07", "1B_heading_check", SUMP["03"]["title"], sline("03", "what"), [], None, [], P("S03"),
     [AL("NOT FITTED (raw camera heading):", "Nothing is fitted: each heading the camera measured is compared directly with the "
         "true heading."),
      ("Metric:", sline("03", "metric")), ("Pass rule:", sline("03", "rule")), ("Result:", sline("03", "result"))], scope=["03"], world=False)
page("08", "1B_truth", f"{T04} (1 of {N1B})", sline("04", "what"), [], None, [], PF("1B_truth"),
     [AL(REAL_L, REAL_X + " The 3 camera-dataset flights (painted-line walls, checkerboard floor). The same recorded flights are "
         "processed with and without the camera heading."), SH_TRUTH] + L04, scope=["04"], world=False)
page("09", "1B_paths", f"{T04} (2 of {N1B})", sline("04", "what"), [], None, [], PF("1B_aligned_paths"),
     [AL(FIT_L, "every flight's estimated path, cruise only, in five separate panels: without the heading (left three) and with "
         "it (right two; EKF3 has no camera-heading version). " + FIT_XC), SH_FPATH] + L04b, scope=["04"], world=False)
page("09f", "1B_fig42", f"{T04} (3 of {N1B})", sline("04", "what"), [], None, [], P("R3b", "R3"),
     [AL(FIT_L, "Figure 4.2 (b) of the thesis: one example flight (flight 3), without the heading (dashed) and with it (solid, UKF and FGO), cruise only. " + FIT_XC), SH_FPATH] + L04b, scope=["04"], world=False)
page("10", "1B_err_noheading", f"{T04} (4 of {N1B})", sline("04", "what"), [], None, [], PF("1B_err_noheading"),
     [AL(FIT_L, "the error against time WITHOUT the camera heading, every flight: several metres. " + FIT_XC), SH_FERR] + L04b,
     scope=["04"], world=False)
page("11", "1B_err_heading", f"{T04} (5 of {N1B})", sline("04", "what"), [], None, [], PF("1B_err_heading"),
     [AL(FIT_L, "the same error WITH the camera heading (UKF and FGO), every flight: a few hundredths of a metre to about a tenth of a metre; note "
         "the much finer y-scale than on the previous page. " + FIT_XC), SH_FERR] + L04b, scope=["04"], world=False)
page("11a", "1B_unaligned_paths", f"{T04} (6 of {N1B})", sline("04", "what"), [], None, [], PF("1B_unaligned_paths"),
     [AL(RAW_L, "the same 3 flights, the estimates exactly as they came out, from take-off, five separate panels with the same "
         "axes. " + RAW_X + " Without the heading each estimate slowly turns and drifts sideways by tens of metres; with it the "
         "lines lie on the true path at this shared scale (the next two pages show the size of the error). UKF and FGO positions "
         "are in their own take-off frame, relabelled (North, East) = (x, −y)."), SH_RPATH] + L04b, scope=["04"], world=False)
page("11b", "1B_unaligned_err_noheading", f"{T04} (7 of {N1B})", sline("04", "what"), [], None, [], PF("1B_unaligned_err_noheading"),
     [AL(RAW_L, "the error against time WITHOUT the camera heading, every flight, with nothing fitted. " + RAW_X + " It grows "
         "during the cruise to tens of metres, mostly sideways (previous page)."), SH_RERR] + L04b, scope=["04"], world=False)
page("11c", "1B_unaligned_err_heading", f"{T04} (8 of {N1B})", sline("04", "what"),
     [W_FWDC(), world(R + "corridor_textured_fwdc__angled_cutaway.jpg", snew("Outside view, roof cut away")),
      world(OB + "fwdc_tex_r1__fwd_y040.png", snew("Forward camera: painted-line walls, checkerboard floor"), OBX),
      world(OB + "fwdplainc_tex_r1__fwd_y040.png", snew("Forward camera: plain walls, checkerboard floor"), OBX),
      world(OB + "fwdplainc_blank_r1__fwd_y040.png", snew("Forward camera: plain walls, blank floor"), OBX)],
     "1B", ["corridor_textured_fwdc", "corridor_blank_fwdc", "corridor_transition_fwdc", "corridor_textured_fwdplainc",
            "corridor_blank_fwdplainc", "corridor_transition_fwdplainc"], PF("1B_unaligned_err_heading"),
     [AL(RAW_L, "the error against time WITH the camera heading (UKF and FGO), every flight, with nothing fitted. " + RAW_X +
         " It stays below about half a metre; note the much finer y-scale than on the previous page."), SH_RERR] + L04b, scope=["04"],
     world_note=snew("Orange cross in the camera frames: where the camera's heading measurement points. The heading-check flights "
                     "also used the half-and-half floor (not pictured)."),
     world_label="The worlds of Experiment 1B (simulator views, and frames the forward camera recorded):")

# ---- 1C: closed loop; never overlaid
CHECKS = ["finish the corridor without touching a wall", "stay within 6.0 m of the centre line",
          "heading error within 1.0° (95% of the time), 2.0° at most", "sideways speed at most 0.25 m/s", "no oscillation"]
for c in CHECKS:
    assert f'T("• {c}")' in SUM_SRC or f'"• {c}"' in SUM_SRC, f"check text '{c}' not in figs_thesis_summary.py"
T05, T06 = SUMP["05"]["title"], SUMP["06"]["title"]
L05 = [("Metric:", sline("05", "metric")), ("Pass rule:", smod("05", "rule", " (grey)", "")), ("Result:", sline("05", "result"))]
L06 = [("Metric:", smod("06", "metric", "); the bars show the largest sideways distance from the centre line in any of them, metres (simulator at half real time, flight speed unchanged).",
                        "; simulator at half real time, flight speed unchanged).")),
       ("Pass rule:", smod("06", "rule", "all five checks listed on the right", "all five checks (" + "; ".join(CHECKS) + ")")),
       ("Result:", sline("06", "result"))]
RAWH_L = "NOT FITTED (raw heading error):"
RAWH_X = "Nothing is fitted: this is the heading error the drone really flew with."
page("12", "1C_paths", f"{T05} (1 of 3)", sline("05", "what"), [], None, [], PF("1C_paths"),
     [AL(REAL_L, REAL_X + " Each estimator was steering the drone: 12 flights in six separate panels. Left three: without the "
         "camera heading, 1 flight each, ending at the wall (X). Right three: with it, 3 flights each, straight up the centre."),
      SH("the drone's real paths; the score below is the time until the wall contact (X, left three panels).")]
     + L05, scope=["05"], world=False)
page("13", "1C_side_off", f"{T05} (2 of 3)", sline("05", "what"), [], None, [], PF("1C_side_off"),
     [AL(REAL_L, REAL_X + " The same three flights without the heading: how far the drone was from the centre line, against "
         "time, until it touched the west wall."),
      SH("the drone's real distance from the centre line against time; the score below is the time it reached the wall (X).")]
     + L05, scope=["05"], world=False)
page("14", "1C_head_off", f"{T05} (3 of 3)", sline("05", "what"), [], None, [], PF("1C_head_off"),
     [AL(RAWH_L, RAWH_X + " Why it drifted: the estimator's heading error against time, one panel per estimator. A heading "
         "error turns the drone's forward flight sideways; the error grows until the wall."),
      SH("the estimator's heading error against time, degrees; the score below is the time the drone reached the wall (X).")]
     + L05, scope=["05"], world=False)
page("15", "1C_head_on", f"{T06} (1 of 2)", sline("06", "what"), [], None, [], PF("1C_head_on", " ".join(CHECKS)),
     [AL(RAWH_L, RAWH_X + " With the camera heading: the heading error of every flight against time, one panel per estimator "
         "(3 flights each), inside the grey pass band."),
      SH("the heading error against time, degrees (one of the five checks); the score below is pass or fail of all five checks.")]
     + L06, scope=["06"], world=False)
page("16", "1C_side_on", f"{T06} (2 of 2)", sline("06", "what"),
     [world(R + "corridor_textured_half_fwdc__interior.jpg", snew("Inside: painted-line walls, roof, checkerboard floor")),
      world(R + "corridor_textured_half_fwdc__angled_cutaway.jpg", snew("Outside view, roof cut away"))],
     "1C", ["corridor_textured_half_fwdc"], PF("1C_side_on", " ".join(CHECKS)),
     [AL(REAL_L, REAL_X + " With the camera heading: how far the drone was from the centre line against time, every flight, one "
         "panel per estimator."),
      SH("the drone's real sideways position against time (another of the five checks); the score below is pass or fail of all "
         "five checks.")] + L06, scope=["06"])

# ---- 2, 3: the tag room
W_ROOM = lambda: [world(R + "room_tags__angled.jpg", snew("The tag room from above, at an angle")),
                  world(R + "room_tags__top_room.jpg", snew("Floor tags, from above"))]
ROOM_L = "NOT FITTED (raw, room frame):"
ROOM_X = ("Nothing is fitted: errors are measured in the room's own frame, fixed by its known map, so this is the raw error a "
          "drone flying on this estimate would face.")
SH_RTRUTH = SH("where the drone really flew (simulator truth), not an error; the score below is the estimators' position error.")
L07 = [("Metric:", sline("07", "metric")), ("Pass rule:", sline("07", "rule")), ("Result:", sline("07", "result"))]
page("17", "2_truth", f"{SUMP['07']['title']} (1 of 2)", sline("07", "what"), [], None, [], PF("2_truth"),
     [AL(REAL_L, REAL_X + " The same route in all 12 flights, one panel per number of tags."), SH_RTRUTH] + L07, scope=["07"], world=False)
page("18", "2_known_tags", f"{SUMP['07']['title']} (2 of 2)", sline("07", "what"), W_ROOM(), "2", ["room_tags"], P("F5"),
     [AL(ROOM_L, ROOM_X + " Error for each number of tags, in metres. Solid lines, filled marks: live estimates. Dashed "
         "lines, open marks: the flight re-solved afterwards (hindsight). Small marks: every single flight; large marks: their mean.")]
     + L07, scope=["07"])
L08 = [("Metric:", sline("08", "metric")), ("Pass rule:", sline("08", "rule")), ("Result:", sline("08", "result"))]
page("19", "3_truth", f"{SUMP['08']['title']} (1 of 2)", sline("08", "what"), [], None, [], PF("3_truth"),
     [AL(REAL_L, REAL_X + " The 3 loop-closure flights (the 8-tag flights of Experiment 2)."), SH_RTRUTH] + L08, scope=["08"], world=False)
page("20", "3_loop_closure", f"{SUMP['08']['title']} (2 of 2)", sline("08", "what"), W_ROOM(), "3", ["room_tags"], P("F7"),
     [AL(ROOM_L, ROOM_X + " The FGO's error on each lap of the 6 m square, in metres, one line per flight (all 3). Left: "
         "with loop closure. Right: without it. Solid: live. Dashed: hindsight."),
      SH("the error on each lap; the score below is the average over all five laps.")] + L08, scope=["08"])

# ---- 4: outdoor-indoor, all 3 flights
L09 = [("Metric:", sline("09", "metric")), ("Pass rule:", sline("09", "rule")), ("Result:", sline("09", "result"))]
W4_L = "NOT FITTED (raw, world frame):"
SH_4 = SH("the error against time, metres; the score below is its root mean square while indoors (shaded).")
page("21", "4_truth", f"{SUMP['09']['title']} (1 of 3)", sline("09", "what"), [], None, [], PF("4_truth"),
     [AL(REAL_L, REAL_X + " From outdoors along a straight line into the building and back, the same in all 3 flights."), SH_RTRUTH]
     + L09, scope=["09"], world=False)
page("22", "4_err_live", f"{SUMP['09']['title']} (2 of 3)", sline("09", "what"), [], None, [], PF("4_err_live"),
     [AL(W4_L, RAW_X + " Live error against time, every flight, one panel per estimator. Grey shading: indoors without GPS. The "
         "error grows indoors and drops when GPS returns."), SH_4] + L09, scope=["09"], world=False)
page("23", "4_err_hind", f"{SUMP['09']['title']} (3 of 3)", sline("09", "what"),
     [world(R + "outdoor_indoor__entrance.jpg", snew("Outdoors: the building entrance (GPS on)")),
      world(R + "outdoor_indoor__indoor.jpg", snew("Inside the building (GPS off)"))], "4", ["outdoor_indoor"], PF("4_err_hind"),
     [AL(W4_L, "Nothing is fitted. The same flights re-solved afterwards (hindsight), every flight; same y-scale as the previous "
         "page."), SH_4] + L09, scope=["09"])

# ---- 5, 5S: where the drone flew, then the summary charts
W_WALL = lambda note: [world(R + "room_wall_tag_far__angled.jpg", snew(note)),
                       world(R + "room_wall_tag_far__walltag.jpg", snew("The printed tag on the wall"))]
NOTE5 = "The room with the wall tag (two start spots were used; the room is the same)"
L10 = [("Metric:", sline("10", "metric")), ("Pass rule:", sline("10", "rule")), ("Result:", sline("10", "result"))]
page("24", "5_truth", f"{SUMP['10']['title']} (1 of 2)", sline("10", "what"), [], None, [], PF("5_truth"),
     [AL(REAL_L, REAL_X + " The 12 hold flights: hovering, a short move, hovering again, one panel per flying estimator. The same "
         "flights are used on the next two pages."),
      SH("where the drone really flew (simulator truth); the score below is the hold error (next page).")] + L10, scope=["10"], world=False)
page("25", "5_hold", f"{SUMP['10']['title']} (2 of 2)", sline("10", "what"), [], None, [], P("S10"),
     [AL("NOT FITTED (the drone's real position):", "Nothing is fitted: the hold error is where the drone really was against where "
         "it should have been.")] + L10, scope=["10"], world=False)
page("26", "5_tag_loss", SUMP["11"]["title"], sline("11", "what"), W_WALL(NOTE5), "5l", ["room_wall_tag", "room_wall_tag_far"], P("S11"),
     [AL("NOT FITTED (raw, wall-tag frame):", "Nothing is fitted: the drift is measured directly in the frame of the wall tag."),
      ("Metric:", sline("11", "metric")), ("Pass rule:", sline("11", "rule")), ("Result:", sline("11", "result"))], scope=["11"])
L12 = [("Metric:", sline("12", "metric")), ("Pass rule:", sline("12", "rule")), ("Result:", sline("12", "result"))]
page("27", "5S_truth", f"{SUMP['12']['title']} (1 of 2)", sline("12", "what"), [], None, [], PF("5S_truth"),
     [AL(REAL_L, REAL_X + " The 4 final safety runs (one per test)."),
      SH("where the drone really flew (simulator truth); the score below is pass or fail of the safety checks.")] + L12,
     scope=["12"], world=False)
page("28", "5S_safety", f"{SUMP['12']['title']} (2 of 2)", sline("12", "what"), W_WALL("The room with the wall tag"), "5S",
     ["room_wall_tag_far"], P("S12"),
     [AL("NOT FITTED (pass or fail checks):", "Nothing is fitted: each safety check is measured directly on the flight.")] + L12,
     scope=["12"])

# =================================================================== contents + how-to, PDF
figc = plt.figure(figsize=(PAGE_W, PAGE_H))
figc.text(MX + 0.013, 0.945, "Results walkthrough: contents", fontsize=21, weight="bold", va="top")
NOTE = snew("Each experiment starts with the simulated world it was flown in (screenshots), then where the drone really flew, then "
            "its plots showing every flight (one panel per estimator, never drawn on top of each other), each with what it shows, "
            "the metric, the pass rule and the result. Where an experiment has no per-flight plot, its summary chart is shown.")
guard(NOTE["text"], "", "contents note")
figc.text(MX + 0.013, 0.885, wrap(NOTE["text"], 118), fontsize=13, va="top", color=INK2, linespacing=1.3)
# Each experiment's world page comes FIRST, then its plot pages (ruling 2026-10-21). A group ends at the page that carries the world.
GROUPS, cur = [], []
for p in PAGES:
    cur.append(p)
    if p["wfig"] is not None:
        GROUPS.append(cur); cur = []
assert not cur, "pages after the last world page"
SEQ = []; ORDER = []; pn = 3                      # page 1 contents, page 2 how to read
for g in GROUPS:
    wpage = pn; SEQ.append(g[-1]["wfig"]); pn += 1
    for k, p in enumerate(g):
        p["pageno"] = pn; SEQ.append(p["fig"]); pn += 1
        base = re.sub(r" \(\d+ of \d+\)$", "", p["title"])
        if not ORDER or ORDER[-1][1] != base:
            ORDER.append((wpage if k == 0 else p["pageno"], base, 1))
        else:
            ORDER[-1] = (ORDER[-1][0], base, ORDER[-1][2] + 1)
NPAGES = pn - 1
rows_c = [("", "How to read these pages", 2)] + [(str(i + 1), t, n0) for i, (n0, t, k) in enumerate(ORDER)]
for i, (n, t, n0) in enumerate(rows_c):
    yy = 0.74 - i * 0.046
    figc.text(0.07, yy, n, fontsize=13, va="top", ha="right", color=INK2)
    figc.text(0.09, yy, t, fontsize=13, va="top")
    figc.text(0.955, yy, f"page {n0}", fontsize=12, va="top", ha="right", color=INK2)
assert 0.74 - (len(rows_c) - 1) * 0.046 > 0.03, "contents page overflows"
figc.savefig(os.path.join(OUTD, "wt_00a_contents.png"), dpi=DPI)
HOWTO = os.path.join(SUM, "summary_00_how_to_read.png")
figh = plt.figure(figsize=(PAGE_W, PAGE_H)); axh = figh.add_axes([0, 0, 1, 1]); axh.imshow(np.asarray(Image.open(HOWTO).convert("RGB")), interpolation="none", aspect="auto"); axh.axis("off")
figh.savefig(os.path.join(OUTD, "wt_00b_how_to_read.png"), dpi=DPI)
with PdfPages(PDF) as pdf:
    for f in [figc, figh] + SEQ:
        pdf.savefig(f)
plt.close("all")

# =================================================================== provenance index
nverb = sum(d["kind"] == "VERBATIM" for p in PAGES for lab, d in p["txt"]); okverb = sum(d.get("equal", False) for p in PAGES for _, d in p["txt"])
nmod = sum(d["kind"] == "MODIFIED" for p in PAGES for _, d in p["txt"]); nnew = sum(d["kind"] == "NEW" for p in PAGES for _, d in p["txt"]) + 1
md = ["# Results walkthrough: index and provenance", "",
      f"*Generated by `eval/figs_results_walkthrough.py` at commit `{COMMIT}`. This script only COMPOSES pages: it places existing, "
      "cross-checked images (thesis figures, summary charts, and the all-flights plots of `eval/figs_walkthrough_flights.py`, whose own "
      "checks are in `flights/index_flights.md`); nothing is re-plotted, recomputed or re-run here. All provenance is here; the pages carry none.*", "",
      f"**All-flights plots (ruling 2026-10-21):** {sum(c['ok'] for c in FLCHK['checks'])}/{len(FLCHK['checks'])} printed-number checks and "
      f"{sum(c['ok'] for c in FLCHK['dataid'])}/{len(FLCHK['dataid'])} data-identity checks pass (`docs/thesis/summary/flights/index_flights.md`, "
      f"sha256 `{sha(os.path.join(FLD, 'index_flights.md'))}`). The world page appears once per experiment, after its last plot page.", "",
      "**FITTED / NOT FITTED labels (user request 2026-10-21):** every plot page carries exactly one bold label as the first line "
      "of its About block (NEW text, number-guarded); FITTED pages explain the fit (one rigid slide and turn about the vertical, "
      "what it shows, and that it makes the error smaller than the raw drift); NOT FITTED pages say what is raw. Labels by page: " +
      "; ".join(f"{p['id']} {next(d['label'] for _, d in p['txt'] if d.get('label'))}" for p in PAGES) + ". Pages with a NEW "
      "'This plot shows:' line (the plotted quantity differs from the registered Metric line, which is kept unchanged): " +
      ", ".join(p["id"] for p in PAGES if any(lab == "This plot shows" for lab, _ in p["txt"])) + ".", "",
      f"**Checks:** {okverb}/{nverb} reused lines equal their source string exactly; {nmod} lines MODIFIED (each listed with its "
      f"original); {nnew} NEW lines (number guard: every number in a NEW or MODIFIED line occurs in the figure's own index entry or in "
      f"that page's summary strings: {'PASS' if not [f for f in FAIL if 'number' in f] else 'FAIL'}); world check "
      f"{sum(w['ok'] for w in WCHK.values())}/{len(WCHK)} page groups match the trials' recorded worlds. Failures: {FAIL or 'none'}.", "",
      "**Text source.** Reused lines come from `docs/thesis/summary/index_summary.md`, which `eval/figs_thesis_summary.py` writes "
      "from the same strings it draws on the summary pages. Before building, that script was re-run on a scratch copy at HEAD "
      "`441e97c` with only its output folder redirected: the regenerated `index_summary.md` was identical apart from its commit line, "
      "and all 13 summary PNGs were byte-identical to the committed ones; the footer-rule rows used to crop the summary charts "
      "(`top` + 0.012 = 0.2945 / 0.266 / 0.323 / 0.2945 / 0.323 for summary pages 02 / 03 / 10 / 11 / 12) come from that run and are "
      "asserted on the committed PNGs at build time. The five closed-loop check phrases inserted into the with-heading 1C pass rule are "
      "asserted to occur in `eval/figs_thesis_summary.py`.", "",
      "**Layout.** A4 landscape; PNGs at 200 dpi; images embedded unresampled (`interpolation='none'`). Text ≥ 11 pt (Metric, Pass "
      "rule, Result, About, world captions: 11 pt; What this tests: 12.5 pt; titles 16.5 pt). 'scale' below = displayed width ÷ the "
      "image's width at 200 dpi (the summary charts are 150 dpi images and are never enlarged beyond their own size).", "",
      f"**PDF:** `results_walkthrough.pdf` = contents (`walkthrough/wt_00a_contents.png`), 'How to read these pages' (the summary's "
      f"`summary_00_how_to_read.png`, sha256 `{sha(HOWTO)}`, placed full page unchanged), then pages 01–{PAGES[-1]['id']} below ({NPAGES} PDF pages in all).", "",
      f"**Contents-page note (NEW):** {NOTE['text']}", ""]
WTR = {"1A": "dsn_tex_r1–r9 (all 9 plotted)", "blank": "the 14 blank-floor flights of Table 4.2", "1B": "the 18 heading-check flights (fwdc_tex_r1–r3 plotted, fitted and not fitted)",
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
       "- **Summary charts kept** (no per-flight time series made here): the blank floor (page 06), the 1B heading check (07), "
       "Experiment 5 hold (25) and tag loss (26), 5S (28). Their per-flight error-against-time views were not built in this stage "
       "(blank floor: the +10/+30 s values of blank_behaviour.json would be the identity check; Experiment 5: hold and loss windows "
       "from expH json); the blank floor and the 1B heading check also have no 'where the drone flew' page (offline, truth-flying "
       "corridor flights, the same straight line as page 01).",
       "- **Replaced by all-flights plots:** Figure 4.2 (R3, one flight), Figure 4.1c (R5, one flight, error against distance), Figures "
       "4.1 and 4.1b (F2, F9: estimators overlaid) and Figure 5.3 (F6, flight 1 of 3). Experiment 2's error against time per flight was "
       "not built (Figure 5.1 already shows every flight as a small mark).",
       "- **No onboard frame of the half-and-half floor with plain walls** exists (`world_images/index.md` §4); the 1B world page notes that "
       "the half-and-half floor is not pictured.", ""]
open(INDEX, "w").write("\n".join(md))
print(f"verbatim {okverb}/{nverb}, modified {nmod}, new {nnew}; world checks {sum(w['ok'] for w in WCHK.values())}/{len(WCHK)}; "
      f"failures: {FAIL or 'none'}; wrote {PDF}, {INDEX}")
sys.exit(1 if FAIL else 0)
