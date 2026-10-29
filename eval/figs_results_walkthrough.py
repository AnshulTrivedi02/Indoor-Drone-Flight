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
assert len(SUMP) == 19, "expected 19 summary pages (12 + the 7 extension pages of 2026-10-25)"
SUM_SRC = open(os.path.join(HERE, "figs_thesis_summary.py")).read()
# footer-rule rows of the summary PNGs (top + 0.012 of each page, from a scratch run of figs_thesis_summary.py at 441e97c)
SUM_TOP = {"02": 0.2825, "03": 0.254, "10": 0.311, "11": 0.2825, "12": 0.311,
           # extension pages (2026-10-25): the footer tops printed by figs_thesis_summary.py ("extension page NN: footer top");
           # 15 is 0.2255 + 0.0003 because its rule row falls on a half pixel (945.5) and round() would pick row 946, not the drawn 945
           "13": 0.3395, "14": 0.3395, "15": 0.2258, "16": 0.2540, "17": 0.3395, "18": 0.3395, "19": 0.3965}


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


def sum_src(pid, gap=8):
    """Summary page chart band: from just below the 'What this tests' line to just above the footer rule (asserted)."""
    p = os.path.join(SUM, SUMP[pid]["file"]); a = np.asarray(Image.open(p).convert("RGB")).astype(int); H = a.shape[0]
    row = round((1 - (SUM_TOP[pid] + 0.012)) * H)
    assert (np.abs(a[row, 100:1600] - 230).sum(1) < 6).mean() > 0.99, f"summary {pid}: footer rule not at row {row}"
    blank = (a.min(2) >= 245).all(1)                 # rows with no ink
    r = round((1 - 0.885) * H)                         # top of the 'What this tests' line
    while blank[r]:
        r += 1
    while not blank[r:r + gap].all():                  # end of that text block: first run of `gap` blank rows (8; 10 for the
                                                       # extension pages, whose italic lines can lack descenders, 2026-10-25)
        r += 1
    y0 = r + 4
    assert y0 < round((1 - 0.755) * H), f"summary {pid}: 'What this tests' text runs into the chart area"
    arr, b = load(p, (0, y0, a.shape[1], row - 4), trim=True)
    FIG["S" + pid] = dict(path=p, arr=arr, box=b, sha=sha(p))


for pid in SUM_TOP:
    sum_src(pid, gap=10 if int(pid) >= 13 else 8)


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
       "5S": ["H_safety_ukf_a_v3", "H_safety_ukf_b_v3", "H_safety_fgo_a_v4", "H_safety_fgo_b_v4"],
       # extension experiments (2026-10-25): offline replays of these recorded flights
       "E2": [f"T_{c}_r{i}" for c in "BCD" for i in (1, 2, 3)], "E3": rr("T_A_r"), "E4": [f"T_{c}_r{i}" for c in "ABCD" for i in (1, 2, 3)],
       "E5": rr("T_A_r"), "ABL": rr("fwdc_tex_r") + rr("fwdplainc_tex_r")}
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


PAGES = []                     # every page record (kind "plot" or "world"), in PDF order
BOOK = []                      # contents groups: dict(title, items=[figs], heading=section heading or None, section=fig or None)
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


def begin(title, heading=None, section=None):
    """Open a contents group (one contents row). heading/section: a section heading row and its full-page figure placed before it."""
    BOOK.append(dict(title=title, items=[], heading=heading, section=section))


ALLTITLES = " ".join(v["title"] for v in SUMP.values())


def tline(title, new, corpus=""):
    """The title record: VERBATIM (a summary page title, with an optional '(k of n)' counter) or NEW (number-guarded)."""
    base = re.sub(r" \(\d+ of \d+\)$", "", title)
    if new:
        # a NEW title may carry experiment numbers: its corpus also holds every summary page title
        d = snew(title); d["guard"] = guard(title, corpus + " " + ALLTITLES, f"title '{title}'"); return d
    tsrc = next((k for k, v in SUMP.items() if v["title"] == base), None)
    if tsrc is None:
        FAIL.append(f"title '{title}' is not a summary title")
    return dict(text=title, src=f"summary page {tsrc}, title" + (" + page counter" if base != title else ""), kind="VERBATIM", orig=base,
                equal=tsrc is not None)


def world_page(pid, title, worlds, wkeys, world_note=None, world_label=None, new_title=True, corpus=""):
    """A world page: the simulated world(s), once each in the whole PDF (restructure 2026-10-29: a world is pictured on the first page
    that needs it; experiments flown in a world already shown carry no world page). wkeys: [(trial-set key, worlds pictured)]."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    TXT = [("title", tline(title, new_title, corpus))]
    UW = 1 - 2 * MX; ytop = 0.978
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
    for lab_, d in TXT[1:]:
        d["guard"] = guard(d["text"], corpus, f"world page {pid} {lab_}")
    for key, shown in wkeys:
        world_check(key, shown)
    fn = f"wt_{pid}_world.png"
    fig.savefig(os.path.join(OUTD, fn), dpi=DPI)
    PAGES.append(dict(kind="world", id=pid, short="world", title=title, file=fn, fig=fig, txt=TXT, worlds=worlds, wkeys=[k for k, _ in wkeys]))
    BOOK[-1]["items"].append(fig)
    print(f"wrote {fn}")


def page(pid, short, title, plot, lines, what=(), scope=None, new_title=False, labw=0.145):
    """Title across the top; 'What this tests' (first page of an experiment only); the plot full width in the middle; About /
    This plot shows / Metric / Pass rule / Result at the bottom (the Metric / Pass rule / Result block ONCE per experiment, on its
    first page: restructure 2026-10-29). Every text block is wrapped by measured width."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    corpus = " ".join(SUMP[s][k] for s in (scope or []) for k in ("what", "metric", "rule", "result")) + " " + plot.get("corpus", "")
    TXT = [("title", tline(title, new_title, corpus))]
    UW = 1 - 2 * MX
    ytop = 0.978; LW = UW * PAGE_W
    tt = fit(fig, title, LW, 16.5, weight="bold")
    fig.text(MX, ytop, tt, fontsize=16.5, weight="bold", va="top", ha="left", linespacing=1.12)
    hdr_bot = ytop - text_h(fig, tt, 16.5, 1.2) - 0.014
    if what:
        wt = fit(fig, "What this tests: " + " ".join(w["text"] for w in what), LW, 12.5, style="italic")
        fig.text(MX, hdr_bot, wt, fontsize=12.5, style="italic", color=INK2, va="top", ha="left", linespacing=1.22)
        for w in what:
            TXT.append(("What this tests", w))
        hdr_bot = hdr_bot - text_h(fig, wt, 12.5, 1.27) - 0.01
    # ---- footer (bottom up)
    FS, LS, GAP = 11, 1.17, 0.007
    blocks = [(lab, ((d["label"] + "\n") if d.get("label") else "") + fit(fig, d["body"] if d.get("label") else d["text"], (UW - labw) * PAGE_W, FS), d)
              for lab, d in lines]
    h = sum(text_h(fig, w, FS, LS) + GAP for _, w, _ in blocks)
    y = top = 0.022 + h
    fig.add_artist(Line2D([MX, 1 - MX], [top + 0.008, top + 0.008], color=GRID, lw=1.2, transform=fig.transFigure))
    for lab, w, d in blocks:
        fig.text(MX, y, lab, fontsize=FS, weight="bold", va="top", ha="left")
        if d.get("label"):
            fig.text(MX + labw, y, d["label"], fontsize=FS, weight="bold", va="top", ha="left", color="#000000")
            fig.text(MX + labw, y, "\n" + w.split("\n", 1)[1], fontsize=FS, va="top", ha="left", linespacing=LS)
        else:
            fig.text(MX + labw, y, w, fontsize=FS, va="top", ha="left", linespacing=LS)
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
    # ---- number guard on NEW / MODIFIED text; verbatim equality
    for lab, d in TXT:
        if d["kind"] in ("NEW", "MODIFIED") and lab != "title":
            d["guard"] = guard(d["text"], corpus, f"page {pid} {lab}")
        elif d["kind"] == "VERBATIM" and lab != "title":
            d["equal"] = d["text"] == d["orig"]
            if not d["equal"]:
                FAIL.append(f"page {pid} {lab}: verbatim line differs from its source")
    nlab = sum(1 for _, d in TXT if d.get("label"))
    if nlab != 1:
        FAIL.append(f"page {pid}: {nlab} FITTED / NOT FITTED labels (exactly one required)")
    fn = f"wt_{pid}_{short}.png"
    fig.savefig(os.path.join(OUTD, fn), dpi=DPI)
    PAGES.append(dict(kind="plot", id=pid, short=short, title=title, file=fn, fig=fig, txt=TXT, worlds=[], plot=plot, scale=scale, plot_h=h_in))
    BOOK[-1]["items"].append(fig)
    print(f"wrote {fn}  plot {w_in:.2f} x {h_in:.2f} in, scale {scale:.2f}")


def intro_page(pid, title, parts, scope):
    """A text page that opens a MERGED experiment (2026-10-29): one figure carries two summary pages' results, and their two Metric /
    Pass rule / Result blocks do not fit under it with the plot still readable. Each part: (panel heading (NEW), 'What this tests'
    line, the block). The figure page that follows carries the About lines only."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    corpus = " ".join(SUMP[s_][k] for s_ in scope for k in ("what", "metric", "rule", "result"))
    TXT = [("title", tline(title, True, corpus))]
    UW = 1 - 2 * MX; FS, LS, GAP, LABW = 12.5, 1.2, 0.009, 0.165
    tt = fit(fig, title, UW * PAGE_W, 16.5, weight="bold")
    fig.text(MX, 0.978, tt, fontsize=16.5, weight="bold", va="top", ha="left", linespacing=1.12)
    y = 0.978 - text_h(fig, tt, 16.5, 1.2) - 0.02
    sub = "The results of this experiment, shown in the figure on the next page:"
    fig.text(MX, y, sub, fontsize=13, style="italic", color=INK2, va="top", ha="left"); y -= text_h(fig, sub, 13, 1.25) + 0.02
    for hd, what, blk in parts:
        d = snew(hd); TXT.append(("panel heading", d))
        fig.text(MX, y, hd, fontsize=14, weight="bold", va="top", ha="left"); y -= text_h(fig, hd, 14, 1.25) + 0.008
        for lab, dd in [("What this tests:", what)] + blk:
            w = fit(fig, dd["text"], (UW - LABW) * PAGE_W, FS, **({"style": "italic"} if lab.startswith("What") else {}))
            fig.text(MX, y, lab, fontsize=FS, weight="bold", va="top", ha="left")
            fig.text(MX + LABW, y, w, fontsize=FS, va="top", ha="left", linespacing=LS, **({"style": "italic", "color": INK2} if lab.startswith("What") else {}))
            y -= text_h(fig, w, FS, LS) + GAP
            TXT.append((lab.rstrip(":"), dd))
        y -= 0.025
        fig.add_artist(Line2D([MX, 1 - MX], [y + 0.012, y + 0.012], color=GRID, lw=1.0, transform=fig.transFigure))
    assert y > 0.02, f"{pid}: intro page overflows"
    for lab, d in TXT[1:]:
        if d["kind"] in ("NEW", "MODIFIED"):
            d["guard"] = guard(d["text"], corpus, f"page {pid} {lab}")
        elif d["kind"] == "VERBATIM":
            d["equal"] = d["text"] == d["orig"]
    fn = f"wt_{pid}_intro.png"; fig.savefig(os.path.join(OUTD, fn), dpi=DPI)
    PAGES.append(dict(kind="intro", id=pid, short="intro", title=title, file=fn, fig=fig, txt=TXT, worlds=[]))
    BOOK[-1]["items"].append(fig)
    print(f"wrote {fn}")


def P(key, corpus_key=None, extra=""):
    d = dict(FIG[key]); d["key"] = key; d["corpus"] = CORP.get(corpus_key or key, "") + " " + extra; return d


# =================================================================== figure sources
# All-flights plots (eval/figs_walkthrough_flights.py) and the composite figures (eval/figs_walkthrough_extra.py, 2026-10-29)
FLD = os.path.join(SUM, "flights"); FLIDX = open(os.path.join(FLD, "index_flights.md")).read()
FLCHK = json.load(open(os.path.join(FLD, "checks.json")))
for fid in FLCHK["figs"]:
    p_ = os.path.join(FLD, f"fl_{fid}.png"); arr, b = load(p_, None, trim=True)
    FIG["FL_" + fid] = dict(path=p_, arr=arr, box=b, sha=sha(p_))
EXD = os.path.join(SUM, "extra"); EXIDX = open(os.path.join(EXD, "index_extra.md")).read()
EXCHK = json.load(open(os.path.join(EXD, "checks.json")))
for fid in EXCHK["figs"]:
    p_ = os.path.join(EXD, f"ex_{fid}.png"); arr, b = load(p_, None, trim=True)
    FIG["EX_" + fid] = dict(path=p_, arr=arr, box=b, sha=sha(p_))
T1FIG = os.path.join(ROOT, "docs", "thesis", "tier1", "figs", "e3_collapse_maps.png")
_a, _b = load(T1FIG, None, trim=True)
FIG["E3MAP"] = dict(path=T1FIG, arr=_a, box=_b, sha=sha(T1FIG))
_e3r = open(os.path.join(ROOT, "docs", "thesis", "tier1", "e3_results.md")).read()
CORP["E3MAP"] = _e3r[_e3r.index("## 7. Map-collapse diagnosis"):]


def PF(fid, extra=""):
    """An all-flights figure; number-guard corpus = its own checked numbers + the flights index (every printed number is checked there)."""
    d = dict(FIG["FL_" + fid]); d["key"] = "FL_" + fid
    d["corpus"] = " ".join(FLCHK["figs"][fid]["numbers"]) + " " + FLIDX + " " + extra; return d


def PX(fid, extra=""):
    """A composite figure; number-guard corpus = its checked numbers + its index (every drawn number is checked there)."""
    d = dict(FIG["EX_" + fid]); d["key"] = "EX_" + fid
    d["corpus"] = " ".join(EXCHK["figs"][fid]["numbers"]) + " " + EXIDX + " " + extra; return d


# ---- text helpers (unchanged wording from 2026-10-21 where a line is kept)
R = "renders/"; OB = "onboard/"
CAP_BL = "Blank floor, "
A = lambda t: ("About this plot:", snew(t))


def AL(label, text):
    """About line with a bold FITTED / NOT FITTED label (NEW text; the label is part of the number-guarded text)."""
    d = snew(label + " " + text); d["label"] = label; d["body"] = text[0].upper() + text[1:]
    return ("About this plot:", d)


def SH(text):
    """'This plot shows:' (NEW): what is drawn, where it differs from the registered Metric line (which is kept as is)."""
    return ("This plot shows:", snew(text))


def BLK(pid, metric=None, rule=None, result=None, tag=""):
    """The Metric / Pass rule / Result block of summary page pid (once per experiment). tag: ', left' / ', right' on a merged page."""
    return [("Metric" + tag + ":", metric or sline(pid, "metric")), ("Pass rule" + tag + ":", rule or sline(pid, "rule")),
            ("Result" + tag + ":", result or sline(pid, "result"))]


FIT_L = "FITTED (aligned):"
FIT_X = ("the whole estimated path is slid and turned as one rigid piece, about the vertical only, to lie as close as possible "
         "to the true path; it cannot bend or stretch it. So the error left measures how well the estimator tracked the shape of "
         "the flight, not which way it happened to start pointing. This makes the error smaller than the raw drift (see the "
         "not-fitted page). This fit gives the same average error (ATE) as the standard alignment used for the score.")
FIT_XC = FIT_X[0].upper() + FIT_X[1:]
RAW_L = "NOT FITTED (raw, from take-off):"
RAW_X = "This is the raw error a drone flying on this estimate would face."
REAL_L = "NOT FITTED (the drone's real path):"
REAL_X = "Nothing is fitted: this is where the drone really was, from the simulator."
SH_FPATH = SH("the fitted estimated paths; the experiment's score below is the fitted average error (ATE) between these and the "
              "true paths.")
FRAME_X = "UKF and FGO positions are in their own take-off frame, relabelled (North, East) = (x, −y)."
ROOM_L = "NOT FITTED (raw, room frame):"
ROOM_X = ("Nothing is fitted: errors are measured in the room's own frame, fixed by its known map, so this is the raw error a "
          "drone flying on this estimate would face.")
TAG0_L = "NOT FITTED (raw, start-tag frame):"
TAG0_X = "Nothing is fitted: the error is measured in the frame of the start tag, with no alignment."
RAWH_L = "NOT FITTED (raw heading error):"
RAWH_X = "Nothing is fitted: this is the heading error the drone really flew with."

# =================================================================== pages (restructure 2026-10-29, user request; decisions D61 onward)
# Setup section: the two worlds and flight paths used by several experiments, shown ONCE: the corridor (1A; 1B flies the same
# straight line) and the tag room with the 6 m square (Experiments 2, 3 and E2 to E5). An experiment flown in a world not shown
# before opens with its own world page; no world is pictured twice.
T01 = SUMP["01"]["title"]
begin("Setup: the corridor and where the drone flew")
world_page("S1", "Setup: the corridor and where the drone flew", [world(R + "corridor_textured__interior.jpg", snew("Inside: checkerboard floor, plain walls, no roof")),
           world(R + "corridor_textured__angled.jpg", snew("Outside view of the same corridor"))], [("1A", ["corridor_textured"])],
           world_label="The corridor of Experiment 1A (simulator screenshots):")
page("S1", "setup_corridor_path", "Setup: the corridor and where the drone flew", PF("1A_truth"),
     [AL(REAL_L, REAL_X + " The 9 standard-sensor flights of Experiment 1A: each took off, climbed, flew straight up the corridor for "
         "about five minutes (the cruise) and landed; the 9 flights are almost identical. The Experiment 1B camera-dataset flights fly "
         "the same straight line in the corridors with a roof. The estimators never steered: they only watched (offline). Experiment "
         "1C, where an estimator flies the drone, shows its own paths.")], new_title=True)
begin("Setup: the tag room and the 6 m square")
world_page("S2", "Setup: the tag room and the 6 m square", [world(R + "room_tags__angled.jpg", snew("The tag room from above, at an angle")),
           world(R + "room_tags__top_room.jpg", snew("Floor tags, from above"))],
           [(k, ["room_tags"]) for k in ("2", "3", "E2", "E3", "E4", "E5")],
           world_label="The tag room of Experiments 2 and 3 and of the extensions E2 to E5 (simulator screenshots):", corpus=FLIDX)
page("S2", "setup_square_path", "Setup: the tag room and the 6 m square", PF("2_truth"),
     [AL(REAL_L, REAL_X + " The 12 flights of Experiment 2: 5 laps of the 6 m square, one panel per number of tags (8, 4, 2, 1). "
         "Experiment 3 and the extensions E2 to E5 replay these same recorded flights, so their routes are the ones drawn here.")],
     new_title=True)

# ---- 1A: Figure 4.2a (fitted) and the raw error (the raw-against-fitted contrast is a key methodological point, user)
begin(T01)
page("01", "1A_fig42", f"{T01} (1 of 2)", P("R3a", "R3"),
     [AL(FIT_L, "Figure 4.2 (a) of the thesis: one example flight (flight 3, chosen beforehand as the median flight), all three "
         "estimators on one plot, cruise only. " + FIT_XC), SH_FPATH]
     + BLK("01", metric=smod("01", "metric", " (the vertical lines show the range over the flights)", "")),
     what=[sline("01", "what")], scope=["01"])
page("02", "1A_unaligned_err", f"{T01} (2 of 2)", PF("1A_unaligned_err"),
     [AL(RAW_L, "the error against time, every flight (9), with nothing fitted. " + RAW_X + " It grows steadily during the cruise, "
         "mostly sideways: with no heading sensor each estimate slowly turns, and the fit used for the score removes that turn. "
         + FRAME_X),
      SH("the raw (not fitted) error against time, metres; the experiment's score (fitted average error, ATE) is on the previous page.")],
     scope=["01"])

# ---- blank floor (1A and 1B): its own world page (three blank-floor corridors), the summary table
begin(SUMP["02"]["title"])
world_page("03", SUMP["02"]["title"], [world(R + "corridor_blank__interior.jpg", snew(CAP_BL + "plain walls, no roof (standard sensors)")),
           world(R + "corridor_blank_fwdc__interior.jpg", snew(CAP_BL + "painted-line walls and roof")),
           world(R + "corridor_blank_fwdplainc__interior.jpg", snew(CAP_BL + "plain walls and roof"))],
           [("blank", ["corridor_blank", "corridor_blank_fwdc", "corridor_blank_fwdplainc"])], new_title=False)
page("03", "blank_floor", SUMP["02"]["title"], P("S02"),
     [AL("NOT FITTED (raw, from the moment the camera stops):", "Nothing is turned or best-fitted: each estimate is only moved "
         "so that it starts at the true position when the camera stops, so the error shown is the raw drift a drone flying on "
         "it would face from then on.")] + BLK("02"), what=[sline("02", "what")], scope=["02"])

# ---- 1B: the heading check (table), then accuracy: Figure 4.2b and the five-panel raw paths
T04 = SUMP["04"]["title"]
begin(SUMP["03"]["title"])
world_page("04", "The worlds of Experiment 1B and the ablation", [
    world(R + "corridor_textured_fwdc__interior.jpg", snew("Inside: painted-line walls, roof, checkerboard floor")),
    world(R + "corridor_textured_fwdc__angled_cutaway.jpg", snew("Outside view, roof cut away")),
    world(R + "corridor_textured_fwdplainc__interior.jpg", snew("Inside: plain walls, roof, checkerboard floor")),
    world(OB + "fwdc_tex_r1__fwd_y040.png", snew("Forward camera: painted-line walls, checkerboard floor"), OBX),
    world(OB + "fwdplainc_tex_r1__fwd_y040.png", snew("Forward camera: plain walls, checkerboard floor"), OBX),
    world(OB + "fwdplainc_blank_r1__fwd_y040.png", snew("Forward camera: plain walls, blank floor"), OBX)],
    [("1B", ["corridor_textured_fwdc", "corridor_blank_fwdc", "corridor_transition_fwdc", "corridor_textured_fwdplainc",
             "corridor_blank_fwdplainc", "corridor_transition_fwdplainc"]),
     ("ABL", ["corridor_textured_fwdc", "corridor_textured_fwdplainc"])],
    world_note=snew("Orange cross in the camera frames: where the camera's heading measurement points. The heading-check flights "
                    "also used the half-and-half floor (not pictured). The ablation replays the checkerboard-floor flights of both "
                    "corridors."),
    world_label="The worlds of Experiment 1B and the ablation (simulator views, and frames the forward camera recorded):")
page("04", "1B_heading_check", SUMP["03"]["title"], P("S03"),
     [AL("NOT FITTED (raw camera heading):", "Nothing is fitted: each heading the camera measured is compared directly with the "
         "true heading.")] + BLK("03"), what=[sline("03", "what")], scope=["03"])
begin(T04)
L04b = BLK("04", result=smod("04", "result", "(see the previous page)", "(see the heading-check page just before this experiment)"))
page("05", "1B_fig42", f"{T04} (1 of 2)", P("R3b", "R3"),
     [AL(FIT_L, "Figure 4.2 (b) of the thesis: one example flight (flight 3), without the heading (dashed) and with it (solid, UKF "
         "and FGO), cruise only. " + FIT_XC), SH_FPATH] + L04b, what=[sline("04", "what")], scope=["04"])
UBH = next(c["computed"] for c in FLCHK["checks"] if c["fig"] == "1B_unaligned_err_heading" and c["label"].startswith("largest with-heading"))
page("06", "1B_unaligned_paths", f"{T04} (2 of 2)", PF("1B_unaligned_paths"),
     [AL(RAW_L, "the 3 flights of the previous page, the estimates exactly as they came out, from take-off, five separate panels with "
         "the same axes. " + RAW_X + " Without the heading each estimate slowly turns and drifts sideways by tens of metres. With the "
         f"heading the lines lie on the true path at this scale: the raw error is about 0.5 m at most (largest {UBH} m, UKF and FGO, "
         "every flight, from take-off to the end of the cruise). " + FRAME_X),
      SH("the raw (not fitted) estimated paths from take-off; the experiment's score (fitted average error, ATE) is on the previous page.")],
     scope=["04"])

# ---- 1C: closed loop; never overlaid
CHECKS = ["finish the corridor without touching a wall", "stay within 6.0 m of the centre line",
          "heading error within 1.0° (95% of the time), 2.0° at most", "sideways speed at most 0.25 m/s", "no oscillation"]
for c in CHECKS:
    assert f'T("• {c}")' in SUM_SRC or f'"• {c}"' in SUM_SRC, f"check text '{c}' not in figs_thesis_summary.py"
T05, T06 = SUMP["05"]["title"], SUMP["06"]["title"]
begin(T05)
world_page("07", "The world of Experiment 1C", [world(R + "corridor_textured_half_fwdc__interior.jpg", snew("Inside: painted-line walls, roof, checkerboard floor")),
           world(R + "corridor_textured_half_fwdc__angled_cutaway.jpg", snew("Outside view, roof cut away"))], [("1C", ["corridor_textured_half_fwdc"])])
page("07", "1C_paths", f"{T05} (1 of 2)", PF("1C_paths"),
     [AL(REAL_L, REAL_X + " Each estimator was steering the drone: 12 flights in six separate panels. Left three: without the "
         "camera heading, 1 flight each, ending at the wall (X). Right three: with it, 3 flights each, straight up the centre."),
      SH("the drone's real paths; the score below is the time until the wall contact (X, left three panels).")]
     + BLK("05", rule=smod("05", "rule", " (grey)", "")), what=[sline("05", "what")], scope=["05"])
page("08", "1C_head_off", f"{T05} (2 of 2)", PF("1C_head_off"),
     [AL(RAWH_L, RAWH_X + " Why it drifted: the estimator's heading error against time, one panel per estimator. A heading "
         "error turns the drone's forward flight sideways; the error grows until the wall."),
      SH("the estimator's heading error against time, degrees; the score (time to the wall contact, X) is on the previous page.")],
     scope=["05"])
begin(T06)
B2MAX = next(c["computed"] for c in FLCHK["checks"] if c["fig"] == "1C_side_on" and c["label"].startswith("largest sideways distance"))
page("09", "1C_head_on", T06, PF("1C_head_on", " ".join(CHECKS) + " " + B2MAX),
     [AL(RAWH_L, RAWH_X + " With the camera heading: the heading error of every flight against time, one panel per estimator "
         f"(3 flights each), inside the grey pass band. The drone's largest distance from the centre line over the 9 flights was "
         f"{B2MAX} m (pass rule: within 6.0 m)."),
      SH("the heading error against time, degrees (one of the five checks); the score below is pass or fail of all five checks.")]
     + BLK("06", metric=smod("06", "metric", "); the bars show the largest sideways distance from the centre line in any of them, metres (simulator at half real time, flight speed unchanged).",
                             "; simulator at half real time, flight speed unchanged)."),
           rule=smod("06", "rule", "all five checks listed on the right", "all five checks (" + "; ".join(CHECKS) + ")")),
     what=[sline("06", "what")], scope=["06"])

# ---- 2, 3: the tag room (pictured in the setup section)
begin(SUMP["07"]["title"])
page("10", "2_known_tags", SUMP["07"]["title"], P("F5"),
     [AL(ROOM_L, ROOM_X + " Error for each number of tags, in metres. Solid lines, filled marks: live estimates. Dashed "
         "lines, open marks: the flight re-solved afterwards (hindsight). Small marks: every single flight; large marks: their mean.")]
     + BLK("07"), what=[sline("07", "what")], scope=["07"])
begin(SUMP["08"]["title"])
page("11", "3_loop_closure", SUMP["08"]["title"], P("F7"),
     [AL(ROOM_L, ROOM_X + " The FGO's error on each lap of the 6 m square, in metres, one line per flight (all 3). Left: "
         "with loop closure. Right: without it. Solid: live. Dashed: hindsight."),
      SH("the error on each lap; the score below is the average over all five laps.")] + BLK("08"), what=[sline("08", "what")], scope=["08"])

# ---- 4: outdoor-indoor, live and hindsight in ONE figure with one y-scale (user)
begin(SUMP["09"]["title"])
world_page("12", SUMP["09"]["title"], [world(R + "outdoor_indoor__entrance.jpg", snew("Outdoors: the building entrance (GPS on)")),
           world(R + "outdoor_indoor__indoor.jpg", snew("Inside the building (GPS off)"))], [("4", ["outdoor_indoor"])], new_title=False)
page("12", "4_err", SUMP["09"]["title"], PF("4_err"),
     [AL("NOT FITTED (raw, world frame):", RAW_X + " Error against time, every flight (3), one row per estimator. Left: live "
         "estimates (solid). Right: the same flights re-solved afterwards (hindsight, dashed). One y-scale in all six panels. Grey "
         "shading: indoors without GPS. The live error grows indoors and drops when GPS returns."),
      SH("the error against time, metres; the score below is its root mean square while indoors (shaded).")]
     + BLK("09"), what=[sline("09", "what")], scope=["09"])

# ---- 5: hold error and drift while the tag is hidden, ONE two-panel figure (user); 5S: the results table only
T5M = "Experiment 5: holding the drone still next to a wall tag, and drift while the tag is hidden"
begin(T5M)
world_page("13", "The world of Experiment 5 and 5S", [world(R + "room_wall_tag_far__angled.jpg", snew("The room with the wall tag (two start spots were used; the room is the same)")),
           world(R + "room_wall_tag_far__walltag.jpg", snew("The printed tag on the wall"))],
           [("5h", ["room_wall_tag", "room_wall_tag_far"]), ("5l", ["room_wall_tag", "room_wall_tag_far"]), ("5S", ["room_wall_tag_far"])])
intro_page("13i", T5M, [("Left panel: holding the drone still next to a wall tag", sline("10", "what"), BLK("10")),
                        ("Right panel: drift while the wall tag is hidden", sline("11", "what"), BLK("11"))], scope=["10", "11"])
page("13", "5_hold_drift", T5M, PX("5_hold_drift"),
     [AL("NOT FITTED (the drone's real position):", "Nothing is fitted: the hold error is where the drone really was against where "
         "it should have been, and the drift is measured directly in the frame of the wall tag. Both panels share one y-scale, in mm.")]
     , scope=["10", "11"], new_title=True)
begin(SUMP["12"]["title"])
page("14", "5S_safety", SUMP["12"]["title"], P("S12"),
     [AL("NOT FITTED (pass or fail checks):", "Nothing is fitted: each safety check is measured directly on the flight.")]
     + BLK("12"), what=[sline("12", "what")], scope=["12"])

# =================================================================== EXTENSION EXPERIMENTS (pre-registered) + the exploratory ablation
SECPNG = os.path.join(SUM, "summary_ext_section.png")      # the summary's section page, placed full page unchanged (2026-10-25)
figs_ = plt.figure(figsize=(PAGE_W, PAGE_H)); axs_ = figs_.add_axes([0, 0, 1, 1])
axs_.imshow(np.asarray(Image.open(SECPNG).convert("RGB")), interpolation="none", aspect="auto"); axs_.axis("off")
figs_.savefig(os.path.join(OUTD, "wt_ext_section.png"), dpi=DPI)
SEC_T = "Extension experiments (pre-registered)"
begin(SUMP["13"]["title"], heading=SEC_T, section=figs_)
EXT_FIRST_ID = "15"
page("15", "E2_fewer_tags", SUMP["13"]["title"], P("S13"),
     [AL(TAG0_L, TAG0_X + " Error on the fifth lap for each number of tags; filled boxes live, open boxes hindsight.")] + BLK("13"),
     what=[sline("13", "what")], scope=["13"])
T14 = SUMP["14"]["title"]
begin(T14)
page("16", "E3_wrong_ids", T14, P("S14"),
     [AL(TAG0_L, TAG0_X + " One mark per run; diverged runs have no finite error and are drawn in the band at the top. Every "
         "registered E3 verdict, and the tag maps, are in the appendix.")] + BLK("14"), what=[sline("14", "what")], scope=["14", "15"])
T4M = "Extension E4: a longer FGO window, compute time and live error"
begin(T4M)
intro_page("17i", T4M, [("Left panel: compute time", sline("16", "what"), BLK("16")),
                        ("Right panel: live error", sline("17", "what"), BLK("17"))], scope=["16", "17"])
page("17", "E4_tradeoff", T4M, PX("E4_tradeoff"),
     [AL("NOT FITTED (compute time; live error in the room frame):", "Nothing is fitted: the left panel is the measured compute "
         "time per step; the right panel is the live error in the room's frame with no alignment, as registered. The change "
         "against the 0.25 s window, on a narrow y-scale, is in the appendix."),
      SH("left, as its Metric; right, the live horizontal error itself (root-mean-square over the laps, metres) at every window, "
         "one line per flight, rather than its change from the 0.25 s value.")]
     , scope=["16", "17"], new_title=True)
begin(SUMP["18"]["title"])
page("18", "E5_ukf_landmarks", SUMP["18"]["title"], P("S18"),
     [AL(TAG0_L, TAG0_X + " The UKF here is the UKF with landmark states (extension E5), not the UKF used elsewhere.")] + BLK("18"),
     what=[sline("18", "what")], scope=["18"])
begin(SUMP["19"]["title"])
page("19", "ablation", SUMP["19"]["title"], P("S19"),
     [AL("FITTED (aligned):", "each value is the standard fitted cruise error: the whole estimated cruise path is slid and turned as "
         "one rigid piece to lie as close as possible to the true path before the error is measured, the score used for every cruise "
         "error in Experiments 1A and 1B. The ablation is EXPLORATORY. Its worlds are on the Experiment 1B world page; the plotted "
         "flights are the painted-line-wall flights, and the plain-wall flights enter the P1 and P3 verdicts.")] + BLK("19"),
     what=[sline("19", "what")], scope=["19"])

# =================================================================== APPENDIX (2026-10-29): the E3 verdict table, the E3 maps (optional), the E4 change plot
figa = plt.figure(figsize=(PAGE_W, PAGE_H))
APP_T = "Appendix: further plots"
figa.text(0.5, 0.56, APP_T, fontsize=30, weight="bold", ha="center", va="center")
APP_NOTE = snew("Kept for reference, outside the main walkthrough: every registered verdict of extension E3 (a table), the E3 tag maps "
                "(optional, descriptive), and the E4 change in live error from its 0.25 s value, whose narrow y-range makes "
                "millimetre differences look large.")
APP_NOTE["guard"] = guard(APP_NOTE["text"], "0.25 " + ALLTITLES, "appendix note")
figa.text(0.5, 0.46, wrap(APP_NOTE["text"], 92), fontsize=14, ha="center", va="top", color=INK2, linespacing=1.35)
figa.savefig(os.path.join(OUTD, "wt_app_section.png"), dpi=DPI)
begin(SUMP["15"]["title"], heading=APP_T, section=figa)
APP_FIRST_ID = "A1"
page("A1", "E3_verdicts", SUMP["15"]["title"], P("S15"),
     [AL("NOT FITTED (pass or fail counts):", "Nothing is fitted: each registered test is a pass or fail count over the runs.")]
     + BLK("15"), what=[sline("15", "what")], scope=["15"])
TA2 = "Appendix: Extension E3, the tag maps (optional, descriptive)"
begin(TA2)
page("A2", "E3_collapse_maps", TA2, P("E3MAP"),
     [AL(TAG0_L, "DESCRIPTIVE, after scoring, not a registered measure. Nothing is fitted: the FGO's re-solved path (orange) and its final "
         "tag positions (dots) against the true path and tags (grey), in the frame of the start tag, for three runs: two plain runs that "
         "finished (T_A_r1 at 1%, T_A_r3 at 5%) and the one robust run that collapsed (T_A_r2 at 5%). The two plain maps are shrunk, "
         "consistent with a least-squares compromise between the wrong and the correct tag measurements; the robust map is folded, "
         "which the E3 diagnosis reads as a wrong basin, not a cheaper compromise."),
      SH("the tag map each run ended with; the E3 score (the live error of every run) is on the Extension E3 page.")],
     scope=["14"], new_title=True)
TA3 = "Appendix: Extension E4, the change in live error from the 0.25 s window"
begin(TA3)
page("A3", "E4_change", TA3, P("S17"),
     [AL("NOT FITTED (raw, room frame):", "Nothing is fitted: the error is measured in the room's frame with no alignment, as "
         "registered. This is each flight's live error minus its value with the 0.25 s window, one panel per number of tags. It was "
         "moved here because its narrow y-range (about 0.009 m either way) makes millimetre differences look meaningful; the "
         "Extension E4 page shows the errors themselves on a y-axis from 0."),
      SH("the change in the FGO's live error from its 0.25 s value (the Metric on the Extension E4 page describes this plot); the "
         "registered result is on the Extension E4 page.")],
     scope=["17"], new_title=True)

# =================================================================== exactly-once rule (user: "print the Metric / Pass rule / Result block once per experiment")
ONCE = {}
for p in PAGES:
    for lab, d in p["txt"]:
        m_ = re.match(r"summary page (\d\d), (metric|rule|result)$", d["src"])
        if m_:
            ONCE[m_.groups()] = ONCE.get(m_.groups(), 0) + 1
for pid in SUMP:
    for f in ("metric", "rule", "result"):
        if ONCE.get((pid, f), 0) != 1:
            FAIL.append(f"summary page {pid} {f}: printed {ONCE.get((pid, f), 0)} times (exactly once required)")
for p in PAGES:                                 # no em-dash anywhere in the walkthrough text
    for lab, d in p["txt"]:
        if "—" in d["text"]:
            FAIL.append(f"page {p['id']} {lab}: em-dash")

# =================================================================== contents + how-to, PDF
figc = plt.figure(figsize=(PAGE_W, PAGE_H))
figc.text(MX + 0.013, 0.955, "Results walkthrough: contents", fontsize=21, weight="bold", va="top")
NOTE = snew("A setup section first shows the corridor and the tag room, and where the drone flew in each. Each experiment then shows "
            "its plots, with the metric, the pass rule and the result printed once, on its first page; a world page opens an "
            "experiment flown in a world not shown before. Section pages open the extension experiments (pre-registered) and the appendix.")
guard(NOTE["text"], "", "contents note")
figc.text(MX + 0.013, 0.895, wrap(NOTE["text"], 122), fontsize=12.5, va="top", color=INK2, linespacing=1.28)
SEQ = []; pn = 3                                   # page 1 contents, page 2 how to read
rows_c = [("", "How to read these pages", 2, False)]; k = 0
for g in BOOK:
    if g["section"] is not None:
        SEQ.append(g["section"]); rows_c.append(("", g["heading"], pn, True)); pn += 1
    k += 1; rows_c.append((str(k), g["title"], pn, False))
    for f in g["items"]:
        SEQ.append(f); pn += 1
NPAGES = pn - 1
CSTEP = 0.0285; Y0 = 0.775
y = Y0
for i, (n, t, n0, hd) in enumerate(rows_c):
    if hd:
        y -= 0.006
    figc.text(0.07, y, n, fontsize=11.5, va="top", ha="right", color=INK2)
    figc.text(0.09 if not hd else MX + 0.013, y, t, fontsize=11.5 if not hd else 12.5, va="top", weight="bold" if hd else "normal")
    figc.text(0.955, y, f"page {n0}", fontsize=11, va="top", ha="right", color=INK2)
    y -= CSTEP + (0.004 if hd else 0)
assert y > 0.0, "contents page overflows"
figc.savefig(os.path.join(OUTD, "wt_00a_contents.png"), dpi=DPI)
HOWTO = os.path.join(SUM, "summary_00_how_to_read.png")
figh = plt.figure(figsize=(PAGE_W, PAGE_H)); axh = figh.add_axes([0, 0, 1, 1]); axh.imshow(np.asarray(Image.open(HOWTO).convert("RGB")), interpolation="none", aspect="auto"); axh.axis("off")
figh.savefig(os.path.join(OUTD, "wt_00b_how_to_read.png"), dpi=DPI)
with PdfPages(PDF) as pdf:
    for f in [figc, figh] + SEQ:
        pdf.savefig(f)
plt.close("all")
pno = 3
for g in BOOK:                                     # PDF page number of every page record
    pno += g["section"] is not None
    for f in g["items"]:
        for p in PAGES:
            if p["fig"] is f:
                p["pageno"] = pno
        pno += 1

# =================================================================== provenance index
ALLT = [d for p in PAGES for _, d in p["txt"]] + [NOTE, APP_NOTE]
nverb = sum(d["kind"] == "VERBATIM" for d in ALLT); okverb = sum(d.get("equal", False) for d in ALLT if d["kind"] == "VERBATIM")
nmod = sum(d["kind"] == "MODIFIED" for d in ALLT); nnew = sum(d["kind"] == "NEW" for d in ALLT)
nplot = sum(p["kind"] == "plot" for p in PAGES); nworld = sum(p["kind"] == "world" for p in PAGES)
md = ["# Results walkthrough: index and provenance", "",
      f"*Generated by `eval/figs_results_walkthrough.py` at commit `{COMMIT}`. This script only COMPOSES pages: it places existing, "
      "cross-checked images (thesis figures, summary charts, the all-flights plots of `eval/figs_walkthrough_flights.py` and the composite "
      "figures of `eval/figs_walkthrough_extra.py`, whose own checks are in `flights/index_flights.md` and `extra/index_extra.md`); nothing "
      "is re-plotted, recomputed or re-run here. All provenance is here; the pages carry none.*", "",
      "**Restructure (user request 2026-10-29; decisions D61 onward in `docs/thesis/tier1/decisions_log.md`):** redundant plots removed; "
      "a setup section shows the corridor and the tag room, and where the drone flew in each, once; every world is pictured once; the "
      "Metric / Pass rule / Result block of each summary page is printed exactly once in the PDF (asserted: "
      f"{sum(v == 1 for v in ONCE.values())}/{3 * len(SUMP)} lines once); Experiment 4 (live and hindsight) and Experiment 5 (hold and "
      "drift) are merged figures with one y-scale each; Extension E4 is a redesigned two-panel figure (compute time | live error); the "
      "E3 verdict table, the E3 maps and the E4 change plot are in an appendix. No em-dash in any page text (asserted).", "",
      f"**All-flights plots:** {sum(c['ok'] for c in FLCHK['checks'])}/{len(FLCHK['checks'])} printed-number checks and "
      f"{sum(c['ok'] for c in FLCHK['dataid'])}/{len(FLCHK['dataid'])} data-identity checks pass (`docs/thesis/summary/flights/index_flights.md`, "
      f"sha256 `{sha(os.path.join(FLD, 'index_flights.md'))}`).", "",
      f"**Composite figures:** {sum(c['ok'] for c in EXCHK['checks'])}/{len(EXCHK['checks'])} checks pass "
      f"(`docs/thesis/summary/extra/index_extra.md`, sha256 `{sha(os.path.join(EXD, 'index_extra.md'))}`).", "",
      "**FITTED / NOT FITTED labels:** every plot page carries exactly one bold label as the first line of its About block (asserted). "
      "Labels by page: " + "; ".join(f"{p['id']} {next(d['label'] for _, d in p['txt'] if d.get('label'))}" for p in PAGES if p["kind"] == "plot") + ".", "",
      f"**Checks:** {okverb}/{nverb} reused lines equal their source string exactly; {nmod} lines MODIFIED (each listed with its "
      f"original); {nnew} NEW lines (number guard: every number in a NEW or MODIFIED line occurs in the figure's own index entry or in "
      f"that page's summary strings: {'PASS' if not [f for f in FAIL if 'number' in f] else 'FAIL'}); world check "
      f"{sum(w['ok'] for w in WCHK.values())}/{len(WCHK)} trial sets match the worlds pictured on their world page. Failures: {FAIL or 'none'}.", "",
      "**Text source.** Reused lines come from `docs/thesis/summary/index_summary.md`, which `eval/figs_thesis_summary.py` writes "
      "from the same strings it draws on the summary pages. The five closed-loop check phrases inserted into the with-heading 1C pass "
      "rule are asserted to occur in `eval/figs_thesis_summary.py`.", "",
      "**Layout.** A4 landscape; PNGs at 200 dpi; images embedded unresampled (`interpolation='none'`). Text ≥ 11 pt. 'scale' below = "
      "displayed width ÷ the image's width at 200 dpi (the summary charts are 150 dpi images and are never enlarged beyond their own size).", "",
      f"**PDF:** `results_walkthrough.pdf` = contents (`walkthrough/wt_00a_contents.png`), 'How to read these pages' (the summary's "
      f"`summary_00_how_to_read.png`, sha256 `{sha(HOWTO)}`, placed full page unchanged), then {nplot} plot pages and {nworld} world pages "
      f"in contents order, with the section page 'Extension experiments (pre-registered)' (the summary's `summary_ext_section.png`, sha256 "
      f"`{sha(SECPNG)}`, placed full page unchanged) before page {EXT_FIRST_ID} and the section page '{APP_T}' "
      f"(`walkthrough/wt_app_section.png`) before page {APP_FIRST_ID}: {NPAGES} PDF pages in all.", "",
      f"**Contents-page note (NEW):** {NOTE['text']}", "", f"**Appendix section note (NEW):** {APP_NOTE['text']}", ""]
WTR = {"1A": "dsn_tex_r1–r9", "blank": "the 14 blank-floor flights of Table 4.2", "1B": "the 18 heading-check flights",
       "1C": "the 12 closed-loop flights of Figures 4.1 / 4.1b", "2": "T_A–D r1–3", "3": "T_A r1–3", "4": "O_r1, O_r2, O_r3b",
       "5h": "S1 near and far, S2v2, S3v2", "5l": "S1 near and far, S2v2, S3v2", "5S": "the four final safety runs",
       "E2": "T_B-D r1-3 (E2 replays; the 8-tag values are the stored Experiment 3 T_A flights)", "E3": "T_A r1-3 (E3 replays)",
       "E4": "T_A-D r1-3 (E4 replays)", "E5": "T_A r1-3 (E5 replays)", "ABL": "fwdc_tex_r1-r3 and fwdplainc_tex_r1-r3 (ablation replays)"}
for p in PAGES:
    md += [f"## Page {p['id']} ({p['kind']}, PDF page {p['pageno']}): {p['title']}", "", f"- **File:** `walkthrough/{p['file']}`"]
    if p["kind"] == "plot":
        pl = p["plot"]
        md.append(f"- **Plot:** `{rel(pl['path'])}` (sha256 `{pl['sha']}`), crop box (x0, y0, x1, y1) px: {tuple(int(v) for v in pl['box']) if pl['box'] else 'none (whole image)'}; "
                  f"shown {p['plot_h']:.2f} in tall, scale {p['scale']:.2f}" +
                  (f"; blank-row runs (start, end; rows of the cropped image) shortened to 24 px, whitespace only: {[(int(x), int(y)) for x, y in pl['squeezed']]}" if pl.get("squeezed") else ""))
    for i, w in enumerate(p["worlds"]):
        md.append(f"- **World image {i + 1}:** `{rel(w['path'])}` (sha256 `{w['sha']}`)" + (f", crop box {w['box']} (drops the frame's text strip)" if w["box"] else ""))
    for key in p.get("wkeys", []):
        wc = WCHK[key]
        md.append(f"- **World check {key} ({'PASS' if wc['ok'] else 'FAIL'}):** pictured {', '.join(wc['shown'])}; flights {WTR[key]}: " +
                  "; ".join(f"{t} → {w} ({how})" for t, w, how in wc["trials"]))
    md += ["", "| line | kind | source | check | text |", "|---|---|---|---|---|"]
    for lab, d in p["txt"]:
        if d["kind"] == "VERBATIM":
            chk = "equal" if d.get("equal") else "**DIFFERS**"
        else:
            chk = "numbers found" if d.get("guard", True) else "**stray number**"
        t = d["text"].replace("|", "¦")
        if d["kind"] == "MODIFIED":
            t += f"; ORIGINAL: {d['orig'].replace('|', '¦')}"
        md.append(f"| {lab} | {d['kind']} | {d['src']} | {chk} | {t} |")
    md.append("")
md += ["## Removed in the 2026-10-29 restructure (user request), and why", "",
       "- **1A:** fitted paths of all flights, fitted error against time (its U-shape comes from the alignment), raw paths from take-off "
       "(the raw error against time covers the drift). Kept: Figure 4.2 (a) and the raw error against time.",
       "- **1B:** five-panel fitted paths, fitted error against time and raw error against time (with and without the heading); the "
       "with-heading raw error is stated in text on the five-panel raw paths page (checked in `flights/index_flights.md`).",
       "- **1C:** both 'true sideways position' plots; the with-heading largest sideways distance is one sentence on the with-heading page.",
       "- **'Where the drone really flew'** pages of 1B, 1C (other than the kept paths plot), 2, 3, 4, 5 and 5S: the corridor path and the "
       "6 m square are shown once, in the setup section. The outdoor-indoor route and the hold routes are no longer drawn anywhere.",
       "- **Repeated world pages:** the tag room once (setup), the wall-tag room once (Experiment 5, also for 5S), the forward-camera "
       "corridors once (1B, also for the ablation).",
       "- **Standalone E4 compute-time page:** its plot is the left panel of the new E4 figure.",
       "- **Moved to the appendix:** the E3 verdict table, the E3 tag maps (optional), the E4 change-from-0.25 s plot.", ""]
open(INDEX, "w").write("\n".join(md))
print(f"verbatim {okverb}/{nverb}, modified {nmod}, new {nnew}; world checks {sum(w['ok'] for w in WCHK.values())}/{len(WCHK)}; "
      f"pages {NPAGES}; failures: {FAIL or 'none'}; wrote {PDF}, {INDEX}")
sys.exit(1 if FAIL else 0)
