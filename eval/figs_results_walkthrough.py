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
assert len(SUMP) == 20, "expected 20 summary pages (12 + the 7 extension pages of 2026-10-25 + E6, page 20, 2026-11-02)"
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
       "E5": rr("T_A_r"), "ABL": rr("fwdc_tex_r") + rr("fwdplainc_tex_r"),
       "1Bcl": [f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)],
       # E6 (2026-11-02): the three mapping flights (figures of eight) and the three test flights
       "E6": ["E6M_fig8_r1b", "E6M_fig8_r2", "E6M_fig8_r3"] + rr("T_A_r")}          # v3: the closed-loop EKF3 panel of the 1B raw paths
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
        hdw = fit(fig, hd, UW * PAGE_W, 14, weight="bold")
        fig.text(MX, y, hdw, fontsize=14, weight="bold", va="top", ha="left", linespacing=1.15); y -= text_h(fig, hdw, 14, 1.25) + 0.008
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

# =================================================================== pages, v3 (second restructure, user request 2026-10-31; decisions D69 onward)
# User principles: ALL FLIGHTS, RAW FIRST; SELF-EXPLANATORY PLOTS. Every figure page = a small grey experiment label (the summary
# page title, VERBATIM, or a NEW label), the figure (whose one-line finding title, raw / fitted tag, live / hindsight key and verdict
# marks are drawn in the figure itself by figs_walkthrough_flights.py / figs_walkthrough_extra.py; for a figure reused unchanged the
# composer draws the finding title and the tag), and a caption of at most two sentences. The full Metric / Pass rule / Result wording
# of every experiment is printed ONCE, verbatim, in the "Registered results" section (Experiment 5S keeps its page exactly as before,
# user: "Keep the safety tests (Experiment 5S) exactly as they are"). Divider pages can be dropped with one switch (--no-dividers).
DIVIDERS = "--no-dividers" not in sys.argv
SENT = re.compile(r"[.!?](?=\s+[A-Z(']|\s*$)")        # a sentence end: . ! ? before a capitalised word or the end (decimals never match)
VERDICT_TOK = re.compile(r"\b(PASS|NOT MET|FAIL)\b")


def figmeta(plot):
    k = plot["key"]
    if k.startswith("FL_"):
        return FLCHK["figs"][k[3:]]
    if k.startswith("EX_"):
        return EXCHK["figs"][k[3:]]
    return {}


def sumrow19(label):
    """The computed string of a summary page 19 check row (index_summary.md), for the ablation's verdicts (its Result paragraph names none)."""
    sec = IDX_SUM[IDX_SUM.index("## Page 19:"):]
    rows = [r for r in sec.split("\n") if r.startswith(f"| number | {label} |") or r.startswith(f"| display | {label} |")]
    assert len(rows) == 1 and rows[0].rstrip().endswith("| yes |"), f"page 19 row {label}"
    return re.findall(r"`([^`]*)`", rows[0])[0]


def fpage(pid, short, header, plot, caption, title=None, tag=None, key=None, scope=(), new_header=False, verdict_scope=None, verdict_extra=""):
    """A v3 figure page. header: the small grey experiment label; title: the bold finding title, ONLY for a figure reused unchanged
    (a v3 figure carries its own); tag / key: drawn by the composer only when the figure does not carry them; caption: <= 2 sentences.
    Verdict words (PASS / NOT MET / FAIL) in the composer's text must occur in the registered Result of the experiment (verdict_scope)."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    corpus = " ".join(SUMP[s][k] for s in scope for k in ("what", "metric", "rule", "result")) + " " + plot.get("corpus", "")
    meta = figmeta(plot)
    TXT = [("label", tline(header, new_header, corpus))]
    UW = 1 - 2 * MX; LW = UW * PAGE_W; y = 0.978
    hd = fit(fig, header, LW, 12.5)
    fig.text(MX, y, hd, fontsize=12.5, color=INK2, va="top", ha="left"); y -= text_h(fig, hd, 12.5, 1.2) + 0.008
    if title:
        for tfs in (16, 15.5, 15, 14.5, 14, 13.5, 13, 12.5, 12):          # one line: shrink the font, never wrap
            tt = fit(fig, title, LW * 0.98, tfs, weight="bold")
            if "\n" not in tt:
                break
        assert "\n" not in tt, f"{pid}: finding title runs over one line: {title}"
        fig.text(MX, y, tt, fontsize=tfs, weight="bold", va="top", ha="left"); y -= text_h(fig, tt, tfs, 1.2) + 0.008
        d = snew(title); TXT.append(("finding title", d))
    has_tag = bool(meta.get("tag")); has_key = bool(meta.get("key"))
    if (tag is None) == (not has_tag):
        FAIL.append(f"page {pid}: raw / fitted tag {'missing' if tag is None else 'given twice (figure and composer)'}")
    if tag or (key and not has_key):
        if tag:
            fig.text(1 - MX, y, tag, fontsize=11, ha="right", va="top", bbox=dict(boxstyle="round,pad=0.3", fc="#f2f2f2", ec="#bbbbbb", lw=0.6))
            TXT.append(("tag", snew(tag)))
        if key and not has_key:
            fig.text(MX, y, key, fontsize=11, ha="left", va="top", bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bbbbbb", lw=0.6))
            TXT.append(("key", snew(key)))
        y -= 0.045
    # caption (bottom up)
    FS, LS = 12, 1.22
    cw = fit(fig, caption, LW, FS)
    ch = text_h(fig, cw, FS, LS)
    fig.text(MX, 0.03, cw, fontsize=FS, va="bottom", ha="left", linespacing=LS)
    fig.add_artist(Line2D([MX, 1 - MX], [0.03 + ch + 0.012, 0.03 + ch + 0.012], color=GRID, lw=1.2, transform=fig.transFigure))
    dcap = snew(caption); TXT.append(("caption", dcap))
    nsent = len(SENT.findall(caption.strip()))
    if nsent > 2 or not caption.strip().endswith((".", ")")):
        FAIL.append(f"page {pid}: caption has {nsent} sentences (at most 2)")
    # plot
    pb, pt = 0.03 + ch + 0.025, y - 0.004
    ph_in = (pt - pb) * PAGE_H; a = plot["arr"]; asp = a.shape[1] / a.shape[0]
    w_in = min(LW, ph_in * asp)
    if plot["key"].startswith("S"):
        w_in = min(w_in, a.shape[1] / 150)
    h_in = w_in / asp
    ax = fig.add_axes([(1 - w_in / PAGE_W) / 2, pt - h_in / PAGE_H - (ph_in - h_in) / PAGE_H / 4, w_in / PAGE_W, h_in / PAGE_H])
    ax.imshow(a, interpolation="none", aspect="auto"); ax.axis("off")
    scale = w_in / (a.shape[1] / DPI)
    assert ph_in > 3.5, f"{pid}: plot area only {ph_in:.2f} in tall"
    for lab, d in TXT:
        if d["kind"] in ("NEW", "MODIFIED") and lab != "label":
            d["guard"] = guard(d["text"], corpus, f"page {pid} {lab}")
    res = " ".join(SUMP[s]["result"] for s in (verdict_scope or scope)) + " " + verdict_extra
    for lab, d in TXT:
        for v in VERDICT_TOK.findall(d["text"]):
            if v not in res:
                FAIL.append(f"page {pid} {lab}: verdict '{v}' does not occur in the registered Result")
    VERDICT_PAGES.append((pid, [v for _, d in TXT for v in VERDICT_TOK.findall(d["text"])], verdict_scope or list(scope)))
    fn = f"wt_{pid}_{short}.png"
    fig.savefig(os.path.join(OUTD, fn), dpi=DPI)
    PAGES.append(dict(kind="plot", id=pid, short=short, title=header, file=fn, fig=fig, txt=TXT, worlds=[], plot=plot, scale=scale, plot_h=h_in,
                      tag=meta.get("tag") or tag, ftitle=title))
    BOOK[-1]["items"].append(fig)
    print(f"wrote {fn}  plot {w_in:.2f} x {h_in:.2f} in, scale {scale:.2f}")


VERDICT_PAGES = []
R = "renders/"; OB = "onboard/"

# ------------------------------------------------------------------ setup: the corridor and the tag room (world pages unchanged)
T01 = SUMP["01"]["title"]
begin("Setup: the corridor and where the drone flew")
world_page("S1", "Setup: the corridor and where the drone flew", [world(R + "corridor_textured__interior.jpg", snew("Inside: checkerboard floor, plain walls, no roof")),
           world(R + "corridor_textured__angled.jpg", snew("Outside view of the same corridor"))], [("1A", ["corridor_textured"])],
           world_label="The corridor of Experiment 1A (simulator screenshots):")
fpage("S1", "setup_corridor_path", "Setup: the corridor and where the drone flew", PF("1A_truth"),
      "The 9 standard-sensor flights of Experiment 1A took off, flew straight up the corridor for about five minutes and landed, while "
      "the estimators only watched. The Experiment 1B camera flights fly the same straight line in the corridors with a roof.",
      tag="the drone's true path, nothing fitted", new_header=True, scope=["01"])
begin("Setup: the tag room and the 6 m square")
world_page("S2", "Setup: the tag room and the 6 m square", [world(R + "room_tags__angled.jpg", snew("The tag room from above, at an angle")),
           world(R + "room_tags__top_room.jpg", snew("Floor tags, from above"))],
           [(k, ["room_tags"]) for k in ("2", "3", "E2", "E3", "E4", "E5", "E6")],
           world_label="The tag room of Experiments 2 and 3 and of the extensions E2 to E6 (simulator screenshots):", corpus=FLIDX)
fpage("S2", "setup_square_path", "Setup: the tag room and the 6 m square", PF("2_truth"),
      "The 12 flights of Experiment 2 flew 5 laps of the 6 m square with 8, 4, 2 or 1 tags in the room. Experiment 3 and the extensions "
      "E2 to E5 replay these same recorded flights.", tag="the drone's true path, nothing fitted", new_header=True, scope=["07"])

# ------------------------------------------------------------------ 1A: all 9 flights, raw first (Figure 4.2 (a) page removed, user TASK 1)
begin(T01)
fpage("01", "1A_paths", T01, PF("1A_unaligned_paths"),
      "Each estimator's raw position estimate from take-off on all 9 standard-sensor flights, against the true path. The registered "
      "score is the fitted cruise ATE in the table; the ranking rule between EKF3 and the FGO was NOT MET, so no estimator is ranked.",
      scope=["01"])
fpage("02", "1A_raw_err", T01, PF("1A_unaligned_err"),
      "The raw horizontal error from take-off of every flight, one panel per estimator, on one y-scale. With no heading sensor each "
      "estimate slowly turns, so the error grows sideways; the fitted score removes that turn.", scope=["01"])

# ------------------------------------------------------------------ blank floor (1A and 1B): world page, the summary table (reused)
begin(SUMP["02"]["title"])
world_page("03", SUMP["02"]["title"], [world(R + "corridor_blank__interior.jpg", snew(CAP_BL + "plain walls, no roof (standard sensors)")),
           world(R + "corridor_blank_fwdc__interior.jpg", snew(CAP_BL + "painted-line walls and roof")),
           world(R + "corridor_blank_fwdplainc__interior.jpg", snew(CAP_BL + "plain walls and roof"))],
           [("blank", ["corridor_blank", "corridor_blank_fwdc", "corridor_blank_fwdplainc"])], new_title=False)
fpage("03", "blank_floor", SUMP["02"]["title"], P("S02"),
      "Error after the downward camera stops giving motion measurements on the blank floor; EKF3 instead reports its own position as "
      "invalid. No pass rule was registered for this descriptive comparison.",
      title="On the blank floor none of the three estimators kept a usable position",
      tag="raw, from the moment the camera stops; no pass rule (descriptive)", scope=["02"])

# ------------------------------------------------------------------ 1B: heading check (reused table), all-flights raw paths (Figure 4.2 (b) page removed, TASK 2)
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
fpage("04", "1B_heading_check", SUMP["03"]["title"], P("S03"),
      "Each flight's camera heading was compared directly with the true heading against the registered limits. It passed on every "
      "floor with painted-line walls; with plain walls it failed on all flights over the checkerboard floor.",
      title="The camera heading passed with painted-line walls; with plain walls it failed over the checkerboard floor",
      tag="raw camera heading, nothing fitted", scope=["03"])
begin(T04)
fpage("05", "1B_paths", T04, PF("1B_unaligned_paths"),
      "The same 3 recorded flights replayed without and with the camera heading, raw from take-off; EKF3 has no offline heading arm, so "
      "its with-heading panel is a closed-loop Experiment 1C flight and is not scored. No pass rule was registered: the table gives the "
      "registered fitted scores and the raw maximum errors.", scope=["04"])

# ------------------------------------------------------------------ 1C: one panel per estimator, before and after (TASK 3)
CHECKS = ["finish the corridor without touching a wall", "stay within 6.0 m of the centre line",
          "heading error within 1.0° (95% of the time), 2.0° at most", "sideways speed at most 0.25 m/s", "no oscillation"]
for c in CHECKS:
    assert f'T("• {c}")' in SUM_SRC or f'"• {c}"' in SUM_SRC, f"check text '{c}' not in figs_thesis_summary.py"
T05, T06 = SUMP["05"]["title"], SUMP["06"]["title"]
T1C = "Experiment 1C: an estimator flies the drone, without and with the camera heading"
begin(T1C)
world_page("07", "The world of Experiment 1C", [world(R + "corridor_textured_half_fwdc__interior.jpg", snew("Inside: painted-line walls, roof, checkerboard floor")),
           world(R + "corridor_textured_half_fwdc__angled_cutaway.jpg", snew("Outside view, roof cut away"))],
           [("1C", ["corridor_textured_half_fwdc"]), ("1Bcl", ["corridor_textured_half_fwdc"])],
           world_note=snew("The same corridor also holds the closed-loop EKF3 flights drawn in the sixth panel of the Experiment 1B paths."),
           corpus=ALLTITLES)
fpage("07", "1C_paths", T1C, PF("1C_paths"),
      "Each estimator steered the drone itself: one flight without the camera heading (dashed) and three with it (solid), drawn where "
      "the drone really flew. Without the heading the UKF and FGO reached the wall inside their predicted windows (PASS) and EKF3 later "
      "than its window (NOT MET); with it every flight passed all five checks.", scope=["05", "06"], new_header=True)
fpage("08", "1C_head_off", T05, PF("1C_head_off"),
      "The heading error of the estimator flying the drone, from the start of the cruise to the wall contact (X), one flight per "
      "estimator. The error grows steadily and turns the forward flight sideways into the west wall.", scope=["05"])
B2MAX = next(c["computed"] for c in FLCHK["checks"] if c["fig"] == "1C_side_on" and c["label"].startswith("largest sideways distance"))
fpage("09", "1C_head_on", T06, PF("1C_head_on", " ".join(CHECKS) + " " + B2MAX),
      "The heading error of all 9 with-heading flights against the registered limit (grey band). Every flight passed all five checks, "
      f"and the drone stayed within {B2MAX} m of the centre line (limit 6.0 m).", scope=["06"])

# ------------------------------------------------------------------ 2, 3 (redrawn, direct labels), 4, 5, 5S
begin(SUMP["07"]["title"])
fpage("10", "2_known_tags", SUMP["07"]["title"], PX("2_known_tags"),
      "Live and re-solved position error, averaged over 5 laps, as the room's known tags are reduced from 8 to 1. The primary rule "
      "passed; the predicted 'live errors similar' was NOT MET, so the live errors are not ranked.", scope=["07"])
begin(SUMP["08"]["title"])
fpage("11", "3_loop_closure", SUMP["08"]["title"], PX("3_loop_closure"),
      "The FGO's error on each lap of the 6 m square, the same 3 flights re-solved with and without recognising tags seen before. All "
      "four registered rules PASS in 3 of 3 flights.", scope=["08"])
begin(SUMP["09"]["title"])
world_page("12", SUMP["09"]["title"], [world(R + "outdoor_indoor__entrance.jpg", snew("Outdoors: the building entrance (GPS on)")),
           world(R + "outdoor_indoor__indoor.jpg", snew("Inside the building (GPS off)"))], [("4", ["outdoor_indoor"])], new_title=False)
fpage("12", "4_err", SUMP["09"]["title"], PF("4_err"),
      "Horizontal error against time for the 3 outdoor-indoor flights, live (left) and re-solved after landing (right), on one y-scale. "
      "The primary rule passed; the live errors were not similar (NOT MET), so they are not ranked.", scope=["09"])
T5M = "Experiment 5: holding the drone still next to a wall tag, and drift while the tag is hidden"
begin(T5M)
world_page("13", "The world of Experiment 5 and 5S", [world(R + "room_wall_tag_far__angled.jpg", snew("The room with the wall tag (two start spots were used; the room is the same)")),
           world(R + "room_wall_tag_far__walltag.jpg", snew("The printed tag on the wall"))],
           [("5h", ["room_wall_tag", "room_wall_tag_far"]), ("5l", ["room_wall_tag", "room_wall_tag_far"]), ("5S", ["room_wall_tag_far"])])
fpage("13", "5_hold_drift", T5M, PX("5_hold_drift"),
      "Left: the mean hold error per flight next to the wall tag; right: the worst drift while the tag was hidden, both in mm on one scale. "
      "All three held far inside both limits; the predicted differences between the estimators were NOT MET.", scope=["10", "11"], new_header=True)
begin(SUMP["12"]["title"])
page("14", "5S_safety", SUMP["12"]["title"], P("S12"),                      # UNCHANGED (user: keep the safety tests exactly as they are)
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
fpage("15", "E2_fewer_tags", SUMP["13"]["title"], PX("E2_fewer_tags"),
      "The FGO's fifth-lap error with loop closure as the room's unknown-place tags are reduced; only the FGO has loop closure in the "
      "thesis (EKF3 and UKF have no landmark states). Means are shown on the live and the re-solved boxes, but no mean test was "
      "registered for the re-solved (hindsight) values.", scope=["13"])
T14 = SUMP["14"]["title"]
begin(T14)
fpage("16", "E3_table", T14, PX("E3_table"),
      "Outcome of every run of the FGO with loop closure when 1% or 5% of tag sightings carry a wrong ID, as built and with robust "
      "weighting. Every registered E3 verdict is in the appendix.", scope=["14", "15"], verdict_scope=["14", "15"])
fpage("16m", "E3_maps", "Extension E3: wrong tag IDs, the tag maps (DESCRIPTIVE)", PF("E3_maps", CORP["E3MAP"]),
      "DESCRIPTIVE, not a registered measure: the FGO's whole-flight re-solve and its final tag map for a clean reference run and one "
      "run with 1% wrong IDs (FGO as built); two more runs are in the appendix. These show the hindsight track and final landmarks, not "
      "the live error used by the registered tests.",
      scope=["14"], new_header=True)
T4M = "Extension E4: a longer FGO window, compute time and live error"
begin(T4M)
fpage("17", "E4_tradeoff", T4M, PX("E4_tradeoff"),
      "Compute time per FGO step (left) and the live error itself (right; the registered metric is its change from the 0.25 s value) as "
      "the window grows from 0.25 s to 5 s on the same 12 flights, windows not to scale. P-E4.1 and P-E4.2 PASS; H-E4.3 FAIL: the longer "
      "window lowered the live error on too few flights.",
      scope=["16", "17"], new_header=True)
begin(SUMP["18"]["title"])
fpage("18", "E5_ukf_landmarks", SUMP["18"]["title"], PX("E5_ukf_landmarks"),
      "A UKF with landmark states (extension E5, not the UKF used elsewhere) on the 3 eight-tag flights, against the stored FGO results. "
      "Its error did not grow with loop closure (H-E5.1 PASS) and stayed above the FGO's (S-E5.5 and S-E5.6 PASS).", scope=["18"])
begin(SUMP["20"]["title"])
fpage("20", "E6_map_reuse", SUMP["20"]["title"], PX("E6_map_reuse"),
      "Live error of each estimator flying on a tag map estimated from an earlier flight (the FGO map), against no map on the first lap "
      "and against the surveyed map over the whole flight, 3 test flights. Map quality, not estimator, decided P3: on all 3 flights the "
      "map with the lower map error gave the lower live error (DESCRIPTIVE, an observation over 3 flights).", scope=["20"])
_p1, _p2, _p3 = (sumrow19(l) for l in ("P1 verdict (needs every rung 6/6) and the r1-r5 counts", "P2 verdict and count", "P3 verdict"))
assert _p1.split()[0] == _p3 == "FAIL" and _p2.split()[0] == "PASS", "ablation verdicts changed in index_summary.md page 19"
ABLV = f"P2 {_p2.split()[0]}; P1 and P3 {_p3}"
begin(SUMP["19"]["title"])
fpage("19", "ablation", SUMP["19"]["title"], P("S19"),
      "The FGO's fitted cruise error with the camera heading for each rung of the window and iteration ablation, against the stored UKF "
      "band. EXPLORATORY, with its own pre-registration; its verdicts are printed on the plot.",
      title=f"Exploratory: a one-keyframe FGO stayed below the UKF with the heading ({ABLV})",
      tag="FITTED (aligned): the fitted cruise error, the ablation's own metric", scope=["19"], verdict_extra=ABLV)

# =================================================================== REGISTERED RESULTS: Metric / Pass rule / Result once per experiment, verbatim
def divider(title, note):
    f_ = plt.figure(figsize=(PAGE_W, PAGE_H))
    f_.text(0.5, 0.56, title, fontsize=28, weight="bold", ha="center", va="center")
    f_.text(0.5, 0.46, wrap(note["text"], 92), fontsize=14, ha="center", va="top", color=INK2, linespacing=1.35)
    return f_


REG_T = "Registered results: metric, pass rule and result"
REG_NOTE = snew("The wording of every experiment as registered, printed once, word for word from the reader summary. Where a line points "
                "at a part of a summary chart (vertical lines, a grey window, bars, a list on the right, or 'the previous page'), that part "
                "is in the reader summary, not in this walkthrough. Experiment 5S keeps its own page.")
REG_NOTE["guard"] = guard(REG_NOTE["text"], ALLTITLES, "registered section note")
figr = divider(REG_T, REG_NOTE); figr.savefig(os.path.join(OUTD, "wt_reg_section.png"), dpi=DPI)
REG_ORDER = [p for p in sorted(SUMP) if p != "12"]
A1_TAB = {e: next(c["computed"] for c in FLCHK["checks"] if c["fig"] == "1A_unaligned_paths" and c["label"].startswith(f"{e} registered cruise ATE"))
          for e in ("EKF3", "UKF", "FGO")}


def reg_page(pid, pids, first=False):
    """A text page of the registered wording: per summary page its title, 'What this tests', Metric, Pass rule and Result, VERBATIM."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=100)
    TXT = [("title", tline("Registered results (" + ", ".join(SUMP[p]["title"].split(":")[0] for p in pids) + ")", True, ALLTITLES))]
    UW = (1 - 2 * MX) * 0.975; FS, LS, GAP, LABW = 11, 1.17, 0.006, 0.13          # 2.5% width margin: measured at 100 dpi, drawn at 200
    y = 0.975
    fig.text(MX, y, "Registered results: metric, pass rule and result (verbatim)", fontsize=12.5, color=INK2, va="top"); y -= 0.04
    for p in pids:
        hdw = fit(fig, SUMP[p]["title"], UW * PAGE_W, 13.5, weight="bold")
        fig.text(MX, y, hdw, fontsize=13.5, weight="bold", va="top"); y -= text_h(fig, hdw, 13.5, 1.22) + 0.006
        TXT.append(("experiment", dict(text=SUMP[p]["title"], src=f"summary page {p}, title", kind="VERBATIM", orig=SUMP[p]["title"], equal=True)))
        rw = (UW - LABW) * PAGE_W - (2.4 if p == "01" else 0)
        for lab, k in (("What this tests:", "what"), ("Metric:", "metric"), ("Pass rule:", "rule"), ("Result:", "result")):
            d = sline(p, k); w = fit(fig, d["text"], rw if k == "result" else (UW - LABW) * PAGE_W, FS, **({"style": "italic"} if k == "what" else {}))
            fig.text(MX, y, lab, fontsize=FS, weight="bold", va="top")
            fig.text(MX + LABW, y, w, fontsize=FS, va="top", linespacing=LS, **({"style": "italic", "color": INK2} if k == "what" else {}))
            if p == "01" and k == "result":           # user TASK 1: the registered cruise ATE table next to the 1A Result
                xt = 1 - MX - 2.25 / PAGE_W
                fig.text(xt, y + 0.005, "cruise ATE (fitted),\nmedian of 9 flights", fontsize=10, weight="bold", va="top", linespacing=1.1)
                for i, e in enumerate(("EKF3", "UKF", "FGO")):
                    fig.text(xt, y - 0.045 - 0.026 * i, e, fontsize=10.5, va="top", color={"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"}[e], weight="bold")
                    fig.text(xt + 0.08, y - 0.045 - 0.026 * i, f"{A1_TAB[e]} m", fontsize=10.5, va="top")
                TXT.append(("1A ATE table", snew("cruise ATE (fitted), median of 9 flights: " + ", ".join(f"{e} {A1_TAB[e]} m" for e in A1_TAB))))
                y -= max(text_h(fig, w, FS, LS), 0.13) + GAP
            else:
                y -= text_h(fig, w, FS, LS) + GAP
            TXT.append((lab.rstrip(":"), d))
        y -= 0.016
        fig.add_artist(Line2D([MX, 1 - MX], [y + 0.008, y + 0.008], color=GRID, lw=1.0, transform=fig.transFigure))
    assert y > 0.015, f"registered page {pid} overflows ({y:.3f})"
    for lab, d in TXT[1:]:
        if d["kind"] == "VERBATIM":
            d["equal"] = d["text"] == d["orig"]
            if not d["equal"]:
                FAIL.append(f"registered page {pid} {lab}: not verbatim")
        else:
            d["guard"] = guard(d["text"], " ".join(FLCHK["figs"]["1A_unaligned_paths"]["numbers"]) + " " + ALLTITLES, f"registered page {pid} {lab}")
    fn = f"wt_{pid}_registered.png"; fig.savefig(os.path.join(OUTD, fn), dpi=DPI)
    PAGES.append(dict(kind="registered", id=pid, short="registered", title=TXT[0][1]["text"], file=fn, fig=fig, txt=TXT, worlds=[], free=y))
    BOOK[-1]["items"].append(fig)
    print(f"wrote {fn} (free {y:.3f})")


REG_GROUPS = [["01", "02", "03"], ["04", "05", "06"], ["07", "08", "09"], ["10", "11", "13"], ["14", "15", "16"], ["17", "18", "19"], ["20"]]
assert sorted(p for g in REG_GROUPS for p in g) == REG_ORDER, "registered groups must hold every summary page except 12 (5S) once"
begin(REG_T, heading=REG_T, section=figr)
for i, g in enumerate(REG_GROUPS):
    reg_page(f"R{i + 1}", g)

# =================================================================== APPENDIX: the E3 verdict table (the E4 change plot is dropped, user TASK 6)
APP_T = "Appendix: further plots"
APP_NOTE = snew("Kept for reference, outside the main walkthrough: every registered verdict of extension E3, as a table; two more "
                "E3 tag maps; and five additional Experiment 1C flights without the camera heading (additional flights, not part of the "
                "pre-registered set).")
APP_NOTE["guard"] = guard(APP_NOTE["text"], ALLTITLES, "appendix note")
figa = divider(APP_T, APP_NOTE); figa.savefig(os.path.join(OUTD, "wt_app_section.png"), dpi=DPI)
begin(SUMP["15"]["title"], heading=APP_T, section=figa)
APP_FIRST_ID = "A1"
fpage("A1", "E3_verdicts", SUMP["15"]["title"], P("S15"),
      "Each registered E3 test with its count over the runs; a diverged run counts as not met. The primary H-E3.1 FAIL; the robust "
      "FGO's tests passed.", title="Every registered E3 verdict: the primary test failed, the robust FGO's tests passed",
      tag="pass or fail counts, nothing fitted", scope=["15"])
fpage("A2", "E3_maps_app", "Extension E3: wrong tag IDs, two more tag maps (DESCRIPTIVE)", PF("E3_maps_app", CORP["E3MAP"]),
      "DESCRIPTIVE, not a registered measure: two more runs with wrong IDs, moved here from the main E3 pages. The FGO as built at 5% "
      "ended with a shrunk map; the one robust run that collapsed ended with a folded map.", scope=["14"], new_header=True)
T1CX = "Experiment 1C: additional flights, not part of the pre-registered set"
begin(T1CX)
fpage("A3", "1C_extra", T1CX, PX("1C_extra"),
      "Wall-contact times of five further no-heading flights (one each; full speed or half real time; older or ablation builds), shown "
      "as recorded; no verdict is drawn. They are not part of the pre-registered set, so their recorded outcomes enter no registered 1C "
      "verdict: every registered 1C verdict uses only the pre-registered flights.", scope=["05"], new_header=True)

# =================================================================== exactly-once rule: every summary page's Metric / Pass rule / Result printed once
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
NTAG = {p["id"]: p.get("tag") for p in PAGES if p["kind"] == "plot"}
for k, v in NTAG.items():
    if not v and k != "14":
        FAIL.append(f"page {k}: no raw / fitted tag")

# =================================================================== contents + how to read, PDF
figc = plt.figure(figsize=(PAGE_W, PAGE_H))
figc.text(MX + 0.013, 0.955, "Results walkthrough: contents", fontsize=21, weight="bold", va="top")
NOTE = snew("A setup section first shows the corridor and the tag room, and where the drone flew in each. Each experiment then shows "
            "all its flights, raw first, with a one-line finding as the title and a short caption; the full metric, pass rule and "
            "result of every experiment are printed once, word for word, in the registered results section near the end (Experiment 5S "
            "keeps its own page, unchanged).")
guard(NOTE["text"], ALLTITLES, "contents note")
figc.text(MX + 0.013, 0.895, fit(figc, NOTE["text"], (1 - 2 * MX - 0.03) * PAGE_W, 12.5), fontsize=12.5, va="top", color=INK2, linespacing=1.28)
SEQ = []; pn = 3                                   # page 1 contents, page 2 how to read
rows_c = [("", "How to read these pages", 2, False)]; k = 0
for g in BOOK:
    if g["section"] is not None:
        if DIVIDERS:
            SEQ.append(g["section"]); rows_c.append(("", g["heading"], pn, True)); pn += 1
        else:
            rows_c.append(("", g["heading"], pn, True))
    if g["title"] == REG_T:
        rows_c.append(("", "(each experiment's metric, pass rule and result)", pn, False))
        for f in g["items"]:
            SEQ.append(f); pn += 1
        continue
    k += 1; rows_c.append((str(k), g["title"], pn, False))
    for f in g["items"]:
        SEQ.append(f); pn += 1
NPAGES = pn - 1
CSTEP = 0.0255; Y0 = 0.765                       # 2026-11-02: lowered so the four-line note clears the first row
y = Y0
for i, (n, t, n0, hd) in enumerate(rows_c):
    if hd:
        y -= 0.005
    figc.text(0.07, y, n, fontsize=11, va="top", ha="right", color=INK2)
    figc.text(0.09 if not hd else MX + 0.013, y, t, fontsize=11 if not hd else 12, va="top", weight="bold" if hd else "normal")
    figc.text(0.955, y, f"page {n0}", fontsize=10.5, va="top", ha="right", color=INK2)
    y -= CSTEP + (0.003 if hd else 0)
assert y > 0.0, "contents page overflows"
figc.savefig(os.path.join(OUTD, "wt_00a_contents.png"), dpi=DPI)

# How to read (v3, NEW, composer-drawn): the visual language of every figure
figh = plt.figure(figsize=(PAGE_W, PAGE_H))
figh.text(MX + 0.013, 0.955, "How to read these pages", fontsize=21, weight="bold", va="top")
HOW = [("Estimators", "the same colour and shape everywhere: EKF3 (ArduPilot's standard filter) blue circle, UKF (unscented Kalman "
        "filter) green triangle, FGO (factor-graph optimiser) orange square; the true path and every limit are grey."),
       ("Live or hindsight", "filled marks and solid lines are live estimates (made during the flight, fixed-lag); open marks and dashed "
        "lines are hindsight (the whole flight re-solved after landing). Figures that use both carry the key in their top-left corner."),
       ("Raw or fitted", "a grey tag in the top-right corner of every figure says whether anything was fitted. Raw means nothing was "
        "moved or turned: the error a drone flying on that estimate would face. Fitted (aligned) means the estimate was slid and "
        "turned as one rigid piece onto the true path before scoring; the Experiment 1 cruise scores (ATE) are fitted."),
       ("Titles and marks", "each figure's title states its main finding. Registered verdicts are printed on the data, worded as "
        "registered (PASS, NOT MET, FAIL); limits are labelled grey lines or bands."),
       ("Registered wording", "the full metric, pass rule and result of every experiment are printed once, word for word, in the "
        "registered results section; the captions under the figures are short summaries of them."),
       ("Units", "position errors in metres (m); Experiment 5 hold quantities in millimetres (mm); compute time in milliseconds (ms); "
        "times in seconds (s). Every axis is linear.")]
yy = 0.86
for lab, t in HOW:
    figh.text(MX + 0.013, yy, lab, fontsize=13.5, weight="bold", va="top")
    w = fit(figh, t, (1 - 2 * MX - 0.24) * PAGE_W, 13)
    figh.text(MX + 0.22, yy, w, fontsize=13, va="top", linespacing=1.3)
    yy -= text_h(figh, w, 13, 1.3) + 0.035
axk = figh.add_axes([MX + 0.22, 0.04, 0.6, 0.1]); axk.axis("off"); axk.set_xlim(0, 6); axk.set_ylim(0, 2)
for i, (e, c_, m_) in enumerate((("EKF3", "#0072B2", "o"), ("UKF", "#009E73", "^"), ("FGO", "#D55E00", "s"))):
    axk.plot(i * 2 + 0.2, 1.4, marker=m_, ms=12, color=c_, ls=""); axk.plot(i * 2 + 0.6, 1.4, marker=m_, ms=12, mfc="white", mec=c_, mew=2, ls="")
    axk.text(i * 2 + 0.95, 1.4, e, fontsize=13, va="center", color=c_, weight="bold")
axk.text(0.0, 0.4, "left mark: filled = live; right mark: open = hindsight", fontsize=12, va="center", color=INK2)
HOWD = [snew(lab + ": " + t) for lab, t in HOW]
for d in HOWD:
    d["guard"] = guard(d["text"], ALLTITLES, "how to read")
    if "—" in d["text"]:
        FAIL.append("how to read: em-dash")
figh.savefig(os.path.join(OUTD, "wt_00b_how_to_read.png"), dpi=DPI)
with PdfPages(PDF) as pdf:
    for f in [figc, figh] + SEQ:
        pdf.savefig(f)
plt.close("all")
pno = 3
for g in BOOK:                                     # PDF page number of every page record
    pno += (g["section"] is not None) and DIVIDERS
    for f in g["items"]:
        for p in PAGES:
            if p["fig"] is f:
                p["pageno"] = pno
        pno += 1

WRITTEN = {p["file"] for p in PAGES} | {"wt_00a_contents.png", "wt_00b_how_to_read.png", "wt_ext_section.png", "wt_reg_section.png", "wt_app_section.png"}
ORPHAN = sorted(f for f in os.listdir(OUTD) if f.endswith(".png") and f not in WRITTEN)     # stale pages of earlier versions
if ORPHAN:
    FAIL.append(f"stale page images in walkthrough/ (delete them): {ORPHAN}")

# =================================================================== provenance index
ALLT = [d for p in PAGES for _, d in p["txt"]] + [NOTE, APP_NOTE, REG_NOTE] + HOWD
nverb = sum(d["kind"] == "VERBATIM" for d in ALLT); okverb = sum(d.get("equal", False) for d in ALLT if d["kind"] == "VERBATIM")
nmod = sum(d["kind"] == "MODIFIED" for d in ALLT); nnew = sum(d["kind"] == "NEW" for d in ALLT)
nplot = sum(p["kind"] == "plot" for p in PAGES); nworld = sum(p["kind"] == "world" for p in PAGES); nreg = sum(p["kind"] == "registered" for p in PAGES)
md = ["# Results walkthrough: index and provenance", "",
      f"*Generated by `eval/figs_results_walkthrough.py` at commit `{COMMIT}`{'' if DIVIDERS else ' with --no-dividers'}. This script only COMPOSES "
      "pages: it places existing, cross-checked images (summary charts, the all-flights plots of `eval/figs_walkthrough_flights.py` and the "
      "redrawn figures of `eval/figs_walkthrough_extra.py`, whose own checks are in `flights/index_flights.md` and `extra/index_extra.md`); "
      "nothing is re-plotted, recomputed or re-run here. All provenance is here; the pages carry none.*", "",
      "**Second restructure (user request 2026-10-31; decisions D69 onward in `docs/thesis/tier1/decisions_log.md`):** all flights, raw "
      "first; every figure self-explanatory (a one-line finding title, the raw / fitted tag and the live / hindsight key on the figure, "
      "direct labels, the registered verdicts on the data); captions of at most two sentences (asserted); the Metric / Pass rule / "
      "Result of every summary page printed exactly once, verbatim (asserted: "
      f"{sum(v == 1 for v in ONCE.values())}/{3 * len(SUMP)} lines once), in the registered results section, except Experiment 5S, whose "
      "page is unchanged. Removed: the Figure 4.2 (a) and (b) pages, the E3 outcome strip plot (now a table), the two intro pages and the "
      "appendix E4 change plot. Divider pages: " + ("included (drop them with --no-dividers)." if DIVIDERS else "dropped (--no-dividers)."), "",
      f"**All-flights plots:** {sum(c['ok'] for c in FLCHK['checks'])}/{len(FLCHK['checks'])} printed-number checks and "
      f"{sum(c['ok'] for c in FLCHK['dataid'])}/{len(FLCHK['dataid'])} data-identity checks pass (`docs/thesis/summary/flights/index_flights.md`, "
      f"sha256 `{sha(os.path.join(FLD, 'index_flights.md'))}`).", "",
      f"**Redrawn and composite figures:** {sum(c['ok'] for c in EXCHK['checks'])}/{len(EXCHK['checks'])} checks pass "
      f"(`docs/thesis/summary/extra/index_extra.md`, sha256 `{sha(os.path.join(EXD, 'index_extra.md'))}`).", "",
      "**Raw / fitted tags:** every figure page carries exactly one tag, drawn in the figure or by the composer (asserted). Tags by page: "
      + "; ".join(f"{p['id']} {p.get('tag') or '(5S page unchanged: its NOT FITTED label)'}" for p in PAGES if p["kind"] == "plot") + ".", "",
      "**Verdict words:** every PASS / NOT MET / FAIL in the composer's titles and captions occurs in the registered Result of its "
      "experiment (asserted); the verdict marks drawn in the figures are each equal to the summary page's check row (`sumrow` checks in "
      "the two figure indexes). Pages and their verdict words: " + "; ".join(f"{pid} {', '.join(v) or 'none'} (Result of {', '.join(sc)})"
                                                                            for pid, v, sc in VERDICT_PAGES) + ".", "",
      f"**Checks:** {okverb}/{nverb} reused lines equal their source string exactly; {nmod} lines MODIFIED; {nnew} NEW lines (number "
      f"guard: every number in a NEW or MODIFIED line occurs in the figure's own checked numbers and index or in that page's summary "
      f"strings: {'PASS' if not [f for f in FAIL if 'number' in f] else 'FAIL'}); world check {sum(w['ok'] for w in WCHK.values())}/{len(WCHK)} "
      f"trial sets match the worlds pictured on their world page. Failures: {FAIL or 'none'}.", "",
      "**Text source.** Reused lines come from `docs/thesis/summary/index_summary.md`, which `eval/figs_thesis_summary.py` writes from the "
      "same strings it draws on the summary pages.", "",
      "**Layout.** A4 landscape; PNGs at 200 dpi; images embedded unresampled (`interpolation='none'`). The composer's own text is >= 11 pt; "
      "text inside a figure is scaled with the figure ('scale'). 'scale' below = "
      "displayed width / the image's width at 200 dpi (the summary charts are 150 dpi images and are never enlarged beyond their own size).", "",
      f"**PDF:** `results_walkthrough.pdf` = contents, 'How to read these pages' (NEW, `walkthrough/wt_00b_how_to_read.png`), then {nplot} "
      f"figure pages, {nworld} world pages and {nreg} registered-results pages in contents order" +
      (f", with the section pages 'Extension experiments (pre-registered)' (the summary's `summary_ext_section.png`, sha256 `{sha(SECPNG)}`, "
       f"placed unchanged) before page {EXT_FIRST_ID}, '{REG_T}' (`walkthrough/wt_reg_section.png`) and '{APP_T}' "
       f"(`walkthrough/wt_app_section.png`) before page {APP_FIRST_ID}" if DIVIDERS else ", no section pages") + f": {NPAGES} PDF pages in all.", "",
      f"**Contents-page note (NEW):** {NOTE['text']}", "", f"**Registered-section note (NEW):** {REG_NOTE['text']}", "",
      f"**Appendix section note (NEW):** {APP_NOTE['text']}", "", "**How to read (NEW):** " + " ".join(d["text"] for d in HOWD), ""]
WTR = {"1A": "dsn_tex_r1–r9", "blank": "the 14 blank-floor flights of Table 4.2", "1B": "the 18 heading-check flights",
       "1C": "the 12 closed-loop flights of Figures 4.1 / 4.1b", "1Bcl": "the 3 closed-loop EKF3 with-heading flights in the sixth 1B panel",
       "2": "T_A–D r1–3", "3": "T_A r1–3", "4": "O_r1, O_r2, O_r3b",
       "5h": "S1 near and far, S2v2, S3v2", "5l": "S1 near and far, S2v2, S3v2", "5S": "the four final safety runs",
       "E2": "T_B-D r1-3 (E2 replays; the 8-tag values are the stored Experiment 3 T_A flights)", "E3": "T_A r1-3 (E3 replays)",
       "E4": "T_A-D r1-3 (E4 replays)", "E5": "T_A r1-3 (E5 replays)", "ABL": "fwdc_tex_r1-r3 and fwdplainc_tex_r1-r3 (ablation replays)",
       "E6": "E6M_fig8_r1b, r2, r3 (E6 mapping flights) and T_A r1-3 (E6 test replays)"}
for p in PAGES:
    md += [f"## Page {p['id']} ({p['kind']}, PDF page {p['pageno']}): {p['title']}", "", f"- **File:** `walkthrough/{p['file']}`"]
    if p["kind"] == "plot":
        pl = p["plot"]
        md.append(f"- **Plot:** `{rel(pl['path'])}` (sha256 `{pl['sha']}`), crop box (x0, y0, x1, y1) px: {tuple(int(v) for v in pl['box']) if pl['box'] else 'none (whole image)'}; "
                  f"shown {p['plot_h']:.2f} in tall, scale {p['scale']:.2f}")
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
md += ["## Removed or merged in the 2026-10-31 restructure (user request), and why", "",
       "- **Figure 4.2 (a) page (1A) and Figure 4.2 (b) page (1B):** fitted, one example flight; replaced by the all-flights raw paths "
       "with the registered fitted scores in a table (user TASKS 1 and 2). Figure 4.2 itself stays a thesis figure.",
       "- **E3 outcome strip plot:** replaced by the outcome table; the tag maps moved from the appendix into the main E3 section, with a "
       "clean reference run added (user TASK 4).",
       "- **Intro pages of Experiment 5 and Extension E4:** their Metric / Pass rule / Result blocks moved to the registered results section.",
       "- **Appendix E4 change-in-live-error plot:** dropped (user TASK 6).",
       "- **'About this plot' and 'This plot shows' lines and the per-page Metric / Pass rule / Result blocks:** replaced by on-figure "
       "tags and marks and two-sentence captions; the registered wording is printed once in the registered results section.", ""]
open(INDEX, "w").write("\n".join(md))
print(f"verbatim {okverb}/{nverb}, modified {nmod}, new {nnew}; world checks {sum(w['ok'] for w in WCHK.values())}/{len(WCHK)}; "
      f"pages {NPAGES}; failures: {FAIL or 'none'}; wrote {PDF}, {INDEX}")
sys.exit(1 if FAIL else 0)
