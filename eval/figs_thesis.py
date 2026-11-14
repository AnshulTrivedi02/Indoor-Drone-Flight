#!/usr/bin/env python3
"""READER-FACING THESIS FIGURE SET (2026-10-15; REVISED 2026-10-16). Plotting and tabulating only: no number is recomputed,
re-run or changed.

Revision 2026-10-16: F1, F3, F4 and F8 became tables T1, T2, T3 and T5; F2 is one panel (heading-error statistics in T4); F6 is the
time trace only (per-flight RMSE in T6); new T7 (failure behaviour) and T8 (hindsight ratio). Each table is written from ONE row list
as docs/thesis/tables/<name>.tex (booktabs), .md and a rendered page (.png) for the combined PDF.

Plots the FROZEN results that eval/figs_final_pack.py already reads (eval/results/** and, for the flight paths, heading
error and the O time series, the recorded dataflash/bag/TUM files under ~/thesis_data/trials). The loaders below are
COPIED from eval/figs_final_pack.py (that script runs everything at module level, so importing it would regenerate the
frozen pack; it is left untouched, as is docs/thesis/final_results_pack.pdf).

Every figure keeps the numbers.md CROSS-CHECK of figs_final_pack.py: each plotted key value is computed here from the
result file and compared with the value typed from docs/thesis/numbers.md (or METHODOLOGY where numbers.md has no row).
A failed check marks the figure FLAGGED in the index.

Rules (task brief 2026-10-15): one-line takeaway titles; captions in the combined PDF and the index only; NO log axes;
a fixed Okabe-Ito colour per estimator; filled/solid = live, open/dashed = hindsight; no panels with differing y-scales;
thin marks; units on every axis; a legend wherever >= 2 series; no dual axes.

Outputs: docs/thesis/figures_thesis/<id>_*.pdf/.png, thesis_figures_combined.pdf, index.md.
Usage: /home/makerspace/venv-evo/bin/python eval/figs_thesis.py   (pymavlink via ~/.cache/thesis_pyshim, inserted below)"""
import json, math, os, re, subprocess, sys, textwrap
sys.path.insert(0, os.path.expanduser("~/.cache/thesis_pyshim"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch
import matplotlib.patheffects as patheffects
from matplotlib.backends.backend_pdf import PdfPages
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUT = os.path.join(ROOT, "docs", "thesis", "figures_thesis"); os.makedirs(OUT, exist_ok=True)
PDF = os.path.join(OUT, "thesis_figures_combined.pdf"); INDEX = os.path.join(OUT, "index.md")
SCRIPT = "eval/figs_thesis.py"
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------------------------------------------------- style
# Okabe-Ito (colour-blind safe). One fixed colour and one marker shape per estimator, in every figure.
C = {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"}
MK = {"EKF3": "o", "UKF": "^", "FGO": "s"}
TRUTH = "#999999"                      # reserved for truth / references (never an estimator)
INK, INK2, GRID, SURF, WALL = "#111111", "#4d4d4d", "#e4e4e4", "#ffffff", "#5e5e5e"
EST = ("EKF3", "UKF", "FGO")
plt.rcParams.update({"font.size": 10.5, "axes.titlesize": 11, "axes.labelsize": 10.5, "xtick.labelsize": 9.5,
                     "ytick.labelsize": 9.5, "legend.fontsize": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF, "lines.linewidth": 1.2, "lines.markersize": 5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "pdf.fonttype": 42})
L = lambda f: json.load(open(os.path.join(RES, f)))
# Caption sentences fixed by the rulings of 2026-10-16 (METHODOLOGY "RULINGS (user, 2026-10-16)": item 5 and the captions item).
# UPDATED 2026-11-12 regeneration (D149(c)): the corrected-priors re-fly now covers the flown FGO hold AND closed-loop
# corridor results too, not only the safety re-tests - the sentence below is corrected accordingly. Every table/figure
# reporting a CURRENT FGO row uses the corrected priors; every row explicitly marked "superseded: original priors"
# (Table A.1, A.2) keeps its own original-prior values, as recorded.
PRIORS = ("The FGO safety re-tests (corrected-priors node) and the FGO hold and closed-loop corridor results reported as current here "
          "(the 2026-11-12 regeneration) all used the corrected initial priors; every earlier FGO build, recorded as superseded, used "
          "the original priors.")
RTFX = "The simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s."
ITEMS = []; CHK = []; TP_BUF = []
# THESIS NUMBERING (docs/thesis/thesis_vocabulary.md §6: by chapter; 4 = Experiment 1, 5 = Experiments 2-4, 6 = Experiment 5,
# 7 = synthesis, A = appendix). The output FILE NAMES keep the internal ids (§6: "The repository files keep their names. Only
# the printed captions take the new numbers."); index.md carries the mapping thesis number -> internal id -> file.
TNUM = {"F2": "Figure 4.1", "F9": "Figure 4.1b (provisional)", "T2": "Table 4.1", "T3": "Table 4.2", "T4": "Table 4.3", "F5": "Figure 5.1", "F7": "Figure 5.2",
        "F6": "Figure 5.3", "T6": "Table 5.1", "T8": "Table 5.2", "T5": "Table 6.1", "T1": "Table 7.1", "T7": "Table 7.2",
        "A1": "Table A.1", "A2": "Table A.2", "A3": "Table A.3",
        # RESTYLE (2026-11-02): ids for the combined-PDF assembly of items built by SEPARATE generators (not recomputed
        # here - see combine_extra_items() near the end), so the thesis_figures_combined.pdf rebuild includes every
        # restyled reader-facing item, not just this script's own.
        "METHODS_ARCH": "Figure 3.1", "R5": "Figure 4.1c (provisional)", "R6": "Figure 4.1d (provisional)", "R3": "Figure 4.2",
        "TA": "Table A.4"}


def tkey(fid):
    """Sort key in thesis order: chapter, then figures before tables, then number (appendix last)."""
    w, n = TNUM[fid].split(" ")[:2]
    ch, k = n.split(".")
    kn = re.match(r"\d+", k).group()               # a provisional suffix ("4.1b") sorts directly after its base number
    return (99 if ch == "A" else int(ch), 0 if w == "Figure" else 1, int(kn) + (0.5 if k != kn else 0))


def rd(v, n=2, sign=False):
    """THE THESIS ROUNDING RULE (ruling 2026-10-16, item 3; adopted for thesis tables, applied here at generation time; numbers.md
    displays the same single rounding since the ruling of 2026-10-16, option (a)): round the full-precision file value ONCE, to the printed precision, half away from zero. The value is
    read through its shortest decimal form (str), so a value stored at 4 dp (e.g. -0.4885) rounds as written, not as its binary
    neighbour. Every number this script prints goes through here."""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(1).scaleb(-int(n))
    out = str(Decimal(str(float(v))).quantize(q, rounding=ROUND_HALF_UP))
    if out.startswith("-") and Decimal(out) == 0:
        out = out[1:]
    return ("+" + out if sign and not out.startswith("-") else out)


def f2(v, n=2):
    return rd(v, n)


def rng(vals, n=2, unit=""):
    return f"{rd(min(vals), n)}–{rd(max(vals), n)}{unit}"


# ------------------------------------------------------------------------- SI display (2026-10-22, user request: "make sure all the
# plots and the results walkthrough are all in si units, not cm, mm etc"). Figures and their captions print metres and seconds only
# (angles stay in degrees). A value is converted by an EXACT decimal shift of its stored full-precision form (never a float multiply),
# then rounded ONCE at the printed precision; an expected numbers.md string is converted by the same exact decimal shift of the string
# (si_str). Superseded in part by the units pass of 2026-10-23 (below): the tables now follow the same per-quantity units, and
# the Experiment 5 hold quantities and compute times went back to mm and ms (SI prefixes allowed by that ruling).
def rd_si(v, n, k=0, sign=False):
    """rd() of the stored value v shifted exactly by 10**k (k = -3: stored mm or ms -> m or s; k = 0: stored in SI already)."""
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(str(float(v))).scaleb(k).quantize(Decimal(1).scaleb(-int(n)), rounding=ROUND_HALF_UP)
    out = format(d, "f")
    if out.startswith("-") and d == 0:
        out = out[1:]
    return "+" + out if sign and not out.startswith("-") else out


def rng_si(vals, n, k=0):
    return f"{rd_si(min(vals), n, k)}–{rd_si(max(vals), n, k)}"


def si_str(s, k):
    """Every number in the source string s shifted exactly by 10**k as a decimal (e.g. '7.8–7.9' mm, k = -3 -> '0.0078–0.0079' m)."""
    from decimal import Decimal
    return re.sub(r"\d+(?:\.\d+)?", lambda m_: format(Decimal(m_.group(0)).scaleb(k), "f"), s)


def mm_(v_m):
    """A stored metre value as a float in mm by an EXACT decimal shift (10^3), not a float multiply: rd() of the result rounds the
    exact decimal once (units pass 2026-10-23)."""
    from decimal import Decimal
    return float(Decimal(str(float(v_m))).scaleb(3))


NNBSP = "\u202f"     # narrow no-break space: the SI digit-group separator (as eval/figs_thesis_summary.py)


def grp(s_):
    """SI digit grouping (narrow no-break space every three digits) of every whole number of five or more digits."""
    return re.sub(r"(?<![\d.])\d{5,}(?![\d.])", lambda m_: f"{int(m_.group(0)):,}".replace(",", NNBSP), s_)


# UNITS PASS (2026-10-23, user ruling: "Thesis tables use SI units, converted at generation time only; numbers.md stays exactly as is.
# Use one unit per quantity, the same in a table as in its matching figure. SI prefixes are fine where they read better"). The tables
# now use the same unit per quantity as the figures (docs/thesis/units.md): position error, RMSE, cross-track, distance, height in m
# (km values -> m to the nearest 1000 m, digits grouped); the Experiment 5 hold quantities (hold error, tag-loss drift, re-lock jump,
# drift bands) in mm; compute times and filter periods in ms; flight times and durations in s. Every conversion is rd_si()/si_str().


def check(label, computed, expected, src):
    """EXACT cross-check (ruling 2026-10-16, "numbers.md rounding, option (a); a full scan; an exact cross-check"): the
    computed string, i.e. the stored full-precision value rounded ONCE by rd() at the printed precision, must equal the
    typed expected string (numbers.md, or METHODOLOGY where numbers.md has no row) character for character. No numeric
    tolerance and no "last-digit" acceptance (the pack's tolerant checker, figs_final_pack.py, is frozen and unchanged)."""
    c, e = str(computed), str(expected)
    if any(x[:3] == (label, c, e) for x in CHK):      # the same check already in this item (footnote reuse): count it once
        return
    CHK.append((label, c, e, src, c == e))


def save(fig, fid, name, title, caption, inputs, rows, logscale="none needed", uncheck="", foot=(), verdict=None):
    """Writes <name>.pdf and <name>.png; records caption, sources and checks for the combined PDF and the index.
    RESTYLE (2026-11-02): no in-figure title is drawn on the reader-facing image any more (house rule: no in-figure titles or
    synopsis headlines). `title` is kept as metadata only - it is still the index/contents-page/combined-PDF heading. The
    `verdict` pointer (RS-2: "each caption points to its TA_verdicts.md row(s) by id") is folded INTO `caption` before it
    is stored in ITEMS, so it appears both in captions/<fid>.md (write_caption) and on the combined PDF's own caption page
    (caption_page() prints ITEMS[...]["caption"], not a separately-read file) - one source of truth, not two."""
    global CHK
    base = os.path.join(OUT, name)
    if verdict is None:
        # D113 (2026-11-02): exact pointer form; no PASS/FAIL/NOT MET/MET/MISS/"verdict" wording is allowed anywhere
        # else in a reader-facing caption (eval/caption_verdict_check.py enforces this). This line must stay LAST -
        # `foot` is empty for every current save() call, so nothing is appended after it.
        verdict = "Verdicts: Table A.4, none (descriptive)."
    caption = caption + "\n\n" + verdict
    from thesis_style import write_caption
    write_caption(fid, f"{TNUM[fid]}. {title}.\n\n{caption}" + ("".join(f"\n\n{t}" for t in foot)))
    txt = " ".join([title, caption] + list(foot) + [t.get_text() for t in fig.findobj(matplotlib.text.Text)])   # for the mapping's "used in"
    # RESTYLE (2026-11-02): bbox_inches="tight" crops to content and silently defeats the RS-1 text-width figsize (it
    # shrank some figures below 6.30 in and grew others past it, e.g. a wide legend). tight_layout() instead adjusts
    # the internal margins to fit the DECLARED figsize, which savefig(bbox_inches=None, the default) then preserves
    # exactly, so every reader-facing figure is genuinely 6.30 in wide.
    try:
        fig.tight_layout()
    except Exception:
        pass
    fig.savefig(base + ".png", dpi=170); fig.savefig(base + ".pdf"); plt.close(fig)
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=fid, num=TNUM[fid], kind="figure", png=base + ".png", pdf=base + ".pdf", title=title, caption=caption, inputs=inputs,
                      rows=rows, checks=CHK, status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale=logscale, uncheck=uncheck,
                      files=[name + ".png", name + ".pdf"], order=None, text=txt, foot=list(foot)))
    print(f"wrote {base}.png/.pdf  checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    for c in CHK:
        if not c[4]:
            print("   CHECK FAIL:", c)
    CHK = []


def legend_est(ax, ests=EST, extra=(), **kw):
    h = [Line2D([], [], ls="-", marker=MK[e], color=C[e], ms=6, label=e) for e in ests] + list(extra)
    return ax.legend(handles=h, frameon=False, **kw)


# ------------------------------------------------------------------------- tables (revision 2026-10-16): .md + .tex + page
TAB = os.path.join(ROOT, "docs", "thesis", "tables"); os.makedirs(TAB, exist_ok=True)
TEX_ESC = {"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
           "^": r"\textasciicircum{}", "\\": r"\textbackslash{}"}
TEX_UNI = {"–": "--", "—": "---", "−": "$-$", "±": r"$\pm$", "°": r"\textdegree{}", "×": r"$\times$", "†": r"\textdagger{}",
           "σ": r"$\sigma$", "≤": r"$\le$", "≥": r"$\ge$", "→": r"$\rightarrow$", "÷": r"$\div$", "Δ": r"$\Delta$", "≈": r"$\approx$",
           "ρ": r"$\rho$", "§": r"\S{}", "÷": r"$\div$", "’": "'", "‘": "`", "“": "``", "”": "''", "…": r"\ldots{}", "·": r"$\cdot$", "‡": r"\textdaggerdbl{}",
           "|": r"$|$", "<": r"$<$", ">": r"$>$", "\n": r" \newline ", "\u202f": r"\,"}


def tex(s):
    """Escape one cell for LaTeX, character by character (so no macro is escaped twice); every output character is ASCII."""
    out = []
    for ch in str(s):
        if ch in TEX_ESC: out.append(TEX_ESC[ch])
        elif ch in TEX_UNI: out.append(TEX_UNI[ch])
        elif ord(ch) < 128: out.append(ch)
        else: raise ValueError(f"no LaTeX mapping for {ch!r} in {s!r}")
    return "".join(out)


def md(s):
    return str(s).replace("|", "\\|").replace("\n", "<br>")


def tex_selfcheck(txt, ncol):
    """The .tex cannot be compiled on this machine (no TeX installed): check ASCII, balanced braces and the column count of
    every tabular row instead."""
    assert all(ord(c) < 128 for c in txt), "non-ASCII character in .tex"
    depth = 0
    for i, c in enumerate(txt):
        if c in "{}" and (i == 0 or txt[i - 1] != "\\"):
            depth += 1 if c == "{" else -1
            assert depth >= 0, "unbalanced braces"
    assert depth == 0, "unbalanced braces"
    body = txt.split(r"\toprule")[1].split(r"\bottomrule")[0]
    for row in body.split(r"\\"):
        row = row.replace(r"\midrule", "").strip()
        if row:
            n = len(re.findall(r"(?<!\\)&", row))
            assert n == ncol - 1, f"row with {n} '&' (expected {ncol - 1}): {row[:80]}"
    return True


def table_page(title, header, rows, widths, notes=(), fs=8.0, bold=True):
    """One A4-landscape page (or more) of a wrapped text table; returns the list of figures."""
    TP_BUF.append(" ".join([title] + list(header) + [str(c) for r in rows for c in r] + list(notes)))
    figs = []; lh = fs * 1.34 / 72 / 8.27

    def newpage(k):
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.text(0.03, 0.965, title + (f" (continued, {k})" if k > 1 else ""), fontsize=12, weight="bold" if bold else "normal", va="top")
        x = 0.03; y = 0.925; nh = 1
        for h, w in zip(header, widths):
            hw = textwrap.wrap(h, max(6, int(w * 0.95))); nh = max(nh, len(hw))
            fig.text(x, y, "\n".join(hw), fontsize=fs + 0.3, weight="bold" if bold else "normal", va="top"); x += w / sum(widths) * 0.94
        return fig, y - max(3.6, 1.3 * nh + 0.9) * lh
    k = 1; fig, y = newpage(k)
    for row in rows:
        BW = ("FAILED", "FAIL", "MISS", "NOT met")      # bold per paragraph (one '\n'-separated item of a cell)
        cells = [[(ln, bold and any(b in para for b in BW)) for para in str(c).split("\n") for ln in (textwrap.wrap(para, max(6, int(w * 0.95))) or [""])]
                 for c, w in zip(row, widths)]
        n = max(len(c) for c in cells)
        if y - n * lh < 0.05:
            figs.append(fig); k += 1; fig, y = newpage(k)
        fig.add_artist(Line2D([0.03, 0.97], [y + 0.45 * lh, y + 0.45 * lh], color=GRID, lw=0.6, transform=fig.transFigure))
        x = 0.03
        for c, w in zip(cells, widths):
            for i, (ln, bold) in enumerate(c):
                fig.text(x, y - i * lh, ln, fontsize=fs, va="top", weight="bold" if bold else "normal")
            x += w / sum(widths) * 0.94
        y -= (n + 0.65) * lh
    for nt in notes:
        lines = textwrap.wrap(nt, 180)
        if y - len(lines) * lh < 0.025:
            figs.append(fig); k += 1; fig, y = newpage(k)
        fig.text(0.03, y, "\n".join(lines), fontsize=fs - 0.3, va="top", color=INK2); y -= (len(lines) + 0.6) * lh
    figs.append(fig)
    return figs


def save_tab(tid, name, title, caption, header, rows, widths, inputs, nrows_ref, notes=(), uncheck="", fs=8.0, order=None):
    """One table, three outputs from the SAME row list: docs/thesis/tables/<name>.md, <name>.tex (booktabs) and a rendered
    page (<name>.png, + _pN) for the combined PDF. Consumes the pending CHK list as this table's cross-checks."""
    global CHK
    srcs = f"Sources: {inputs}. numbers.md rows: {nrows_ref}."
    # markdown
    m_ = [f"# {TNUM[tid]}. {title}", "", f"{caption}", "", "| " + " | ".join(md(h) for h in header) + " |",
          "|" + "---|" * len(header)]
    m_ += ["| " + " | ".join(md(c) for c in r) + " |" for r in rows]
    m_ += [""] + [f"*{md(n)}*" + "\n" for n in notes] + [f"<!-- generated by {SCRIPT} (commit {COMMIT}); frozen numbers only. Sources, "
                                                        f"numbers.md rows and the cross-checks: docs/thesis/figures_thesis/index.md, {TNUM[tid]} (internal id {tid}). -->", ""]
    open(os.path.join(TAB, name + ".md"), "w").write("\n".join(m_))
    # LaTeX (booktabs)
    tw = sum(widths); spec = "".join(f"p{{\\dimexpr {rd(w / tw * 0.999, 3)}\\linewidth-2\\tabcolsep\\relax}}" for w in widths)
    t_ = [f"% {TNUM[tid]} (internal id {tid}): generated by {SCRIPT} (commit {COMMIT}); frozen numbers only. Sources and cross-checks: docs/thesis/figures_thesis/index.md.",
          "% Needs \\usepackage{booktabs}",
          "% (and textcomp on an old TeX for \\textdegree, \\textdagger). Not compiled on the build machine (no TeX installed);",
          "% checked for ASCII, balanced braces and the column count of every row.",
          r"\begin{table}[htbp]", r"\centering", r"\footnotesize", f"\\caption{{{tex(title)}. {tex(caption)}}}",
          f"\\label{{tab:{tid}}}", f"\\begin{{tabular}}{{{spec}}}", r"\toprule",
          " & ".join(f"\\textbf{{{tex(h)}}}" for h in header) + r" \\", r"\midrule"]
    t_ += [" & ".join(tex(c) for c in r) + r" \\" for r in rows]
    t_ += [r"\bottomrule", r"\end{tabular}", r"\par\smallskip\raggedright"]
    t_ += [f"\\textit{{Note.}} {tex(n)}\\par" for n in notes]
    t_ += [r"\end{table}", ""]
    txt = "\n".join(t_); tex_selfcheck(txt, len(header))
    open(os.path.join(TAB, name + ".tex"), "w").write(txt)
    # rendered page(s) for the combined PDF
    figs = table_page(f"{TNUM[tid]}. {title}", header, rows, widths, notes=notes, fs=fs)
    pngs = []
    for k, f in enumerate(figs):
        base = os.path.join(TAB, name + (f"_p{k + 1}" if len(figs) > 1 else ""))
        f.savefig(base + ".png", dpi=150, bbox_inches="tight", pad_inches=0.25); plt.close(f); pngs.append(base + ".png")
    ok = all(c[4] for c in CHK)
    txt_ = " ".join([caption] + TP_BUF); TP_BUF.clear()
    ITEMS.append(dict(id=tid, num=TNUM[tid], kind="table", png=pngs, pdf=None, title=title, caption=caption, inputs=inputs, rows=nrows_ref,
                      checks=CHK, status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale="none needed (table)", uncheck=uncheck,
                      files=[name + ".md", name + ".tex", name + ".png"] if len(pngs) == 1 else [name + ".md", name + ".tex"] +
                      [os.path.basename(p) for p in pngs], order=order, text=txt_))
    print(f"wrote table {name} (.md/.tex, {len(pngs)} page(s))  checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    for c in CHK:
        if not c[4]:
            print("   CHECK FAIL:", c)
    CHK = []


# ------------------------------------------------------------------ flight-data helpers (COPIED from figs_final_pack.py)
_sim = {}
def sim_path(tr):
    """Simulator-truth path from dataflash SIM: (t s, x East m, y North m, yaw deg), origin at the first sample (spawn)."""
    if tr in _sim:
        return _sim[tr]
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); S = []
    while True:
        r = m.recv_match(type=["SIM"])
        if r is None:
            break
        S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Yaw))
    S = np.array(S); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    _sim[tr] = np.column_stack([S[:, 0], E, N, S[:, 3]]); return _sim[tr]


def log_yaw(tr, est):
    """Heading error of the flying estimator against SIM yaw from cruise start (copied; FGO branch added: XFGO.Yaw, the
    source closed_loop_score.py uses for --est fgo)."""
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); E, S = [], []
    while True:
        r = m.recv_match(type=["SIM", "XKF1", "XUKO", "XFGO"])
        if r is None:
            break
        t = r.get_type()
        if t == "SIM": S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Yaw))
        elif t == "XKF1" and est == "EKF3" and r.C == 0: E.append((r.TimeUS / 1e6, r.Yaw))
        elif t == "XUKO" and est == "UKF": E.append((r.TimeUS / 1e6, r.Yaw))
        elif t == "XFGO" and est == "FGO": E.append((r.TimeUS / 1e6, r.Yaw))
    S, E = np.array(S), np.array(E); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; Ee = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    c0, _ = cruise_bounds(S[:, 0], Ee, N)
    un = lambda d: np.degrees(np.unwrap(np.radians(d)))
    w = E[:, 0] >= c0
    e = (un(E[w, 1]) - np.interp(E[w, 0], S[:, 0], un(S[:, 3])) + 180) % 360 - 180
    return E[w, 0] - c0, e


def cl_meta(tr):
    js = L(f"closed_loop_{tr}.json")
    c0 = js["cruise_s"][0] if "cruise_s" in js else js["cruise_start_s"]
    ct = js.get("contact")
    if ct and "t_rel_cruise_s" not in ct:
        ct = {"x": ct["E_m"], "y": ct["N_m"], "t_rel_cruise_s": ct["cruise_plus_s"]}
    return c0, ct


def draw_corridor(ax):
    for yw in (10, -10):
        ax.axhspan(yw - 0.1, yw + 0.1, color=WALL, lw=0)
    ax.axhline(9.58, color=WALL, lw=0.6, ls=":"); ax.axhline(-9.58, color=WALL, lw=0.6, ls=":")
    ax.set_ylim(-10.6, 10.6); ax.set_xlim(0, 160); ax.set_yticks([-10, -5, 0, 5, 10])


WIN = {"EKF3": (155, 215), "UKF": (146, 218), "FGO": (145, 196)}
# ============================================================================================ data used by several figures
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
pt = L("dsn_paired_test.json")
DSN = {}
for est in EST:
    DSN[est] = [(i, ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"]["+0.00"]) for i in range(1, 10)
                if est in ev[f"dsn_tex_r{i}"]["est"] and ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"].get("+0.00") is not None]
CAMB = [(ds, r) for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)]
P4 = {}
for ds, r in CAMB:
    e = L(f"phase4_{ds}_evo.json")["trials"][f"{ds}_tex_r{r}"]["est"]
    P4[(ds, r)] = {k: e[k]["ate_a_cruise"]["+0.00"] for k in ("EKF3", "UKF_baseline", "FGO_baseline", "UKF_heading", "FGO_heading")}

# ---------------------------------------------------------------------------- RAW (DESCRIPTIVE) corridor error columns
# (raw-tables stage 2, 2026-11-02; D106/D107/D111, user ruling "option 1 on fitted results"). Every raw number used by
# any table below is looked up from eval/results/raw_corridor_errors.json by (trial, estimator, arm) ONLY - never
# recomputed here - so it is identical to the value `docs/thesis/raw_corridor/raw_corridor_numbers.md` already prints and
# already cross-checks (docs/thesis/raw_corridor/check_raw_corridor.py, 154/154 rows, 1860/1860 checks). This script adds
# no new trajectory computation; it only re-displays a subset of that json's already-checked values next to the
# existing registered (evo -a cruise) ones. Metric: evo -a's own pose_relation is the translation part in 3D (confirmed
# from eval/three_way_eval.py: no --pose_relation flag is passed to evo_ape, and "Reference TUMs carry identity
# quaternions, so APE is the translation part" is stated there directly) - so the raw companion columns below use the
# json's rms_3d_m/end_3d_m fields, NOT the horizontal (rms_h_m/end_h_m) ones, per the brief's own rule ("use the
# HORIZONTAL raw values ... unless the table's aligned metric is 3D, in which case use 3D").
RAWJ = L("raw_corridor_errors.json")
RAWIDX = {}
for _rc in RAWJ["cells"]:
    _rk = (_rc["trial"], _rc["estimator"], _rc["arm"])
    assert _rk not in RAWIDX, f"duplicate raw_corridor_errors.json cell {_rk}"
    RAWIDX[_rk] = _rc


def raw_cell(trial, estimator, arm="baseline"):
    """Exactly-one lookup into raw_corridor_errors.json; raises KeyError if the (trial, estimator, arm) triple is not in
    scope and AssertionError if that cell's raw value was withheld (not possible for this scope: D111 validated all
    three estimators, 154/154 cells have a published raw value - asserted anyway, not assumed)."""
    c = RAWIDX[(trial, estimator, arm)]
    assert "raw" in c, f"no raw value published for {trial}/{estimator}/{arm}"
    return c["raw"]


def stored_ate(trial, estimator, arm="baseline"):
    """The json cell's own `stored_ate_a_cruise` (the registered evo -a (cruise) value this cell's raw numbers companion),
    for verifying a raw-row/raw-column's (trial, estimator, arm) selection against the aligned value already displayed."""
    return RAWIDX[(trial, estimator, arm)]["stored_ate_a_cruise"]


def raw_med(trials, estimator, arm="baseline", n=2):
    """'RMS <median>; end <median>' over `trials` (median-only, to mirror a cell that prints a median with no range)."""
    rms = [raw_cell(t, estimator, arm)["rms_3d_m"] for t in trials]
    end = [raw_cell(t, estimator, arm)["end_3d_m"] for t in trials]
    return f"RMS {rd(float(np.median(rms)), n)}; end {rd(float(np.median(end)), n)}"


def raw_rng(trials, estimator, arm="baseline", n=2):
    """'RMS <lo>-<hi>; end <lo>-<hi>' over `trials` (range-only, to mirror a cell that prints a range with no median)."""
    rms = [raw_cell(t, estimator, arm)["rms_3d_m"] for t in trials]
    end = [raw_cell(t, estimator, arm)["end_3d_m"] for t in trials]
    return f"RMS {rng(rms, n)}; end {rng(end, n)}"


def raw_med_rng(trials, estimator, arm="baseline", n=2):
    """'RMS <median> (<lo>-<hi>); end <median> (<lo>-<hi>)' over `trials` (to mirror a cell that prints median (range))."""
    rms = [raw_cell(t, estimator, arm)["rms_3d_m"] for t in trials]
    end = [raw_cell(t, estimator, arm)["end_3d_m"] for t in trials]
    return f"RMS {rd(float(np.median(rms)), n)} ({rng(rms, n)}); end {rd(float(np.median(end)), n)} ({rng(end, n)})"


def raw_list(trials, estimator, arm="baseline", n=2):
    """'RMS a / b / c; end d / e / f' over `trials`, in order (to mirror a cell that lists one value per flight)."""
    rms = [raw_cell(t, estimator, arm)["rms_3d_m"] for t in trials]
    end = [raw_cell(t, estimator, arm)["end_3d_m"] for t in trials]
    return "RMS " + " / ".join(rd(x, n) for x in rms) + "; end " + " / ".join(rd(x, n) for x in end)


RAW_NOTE = ("Raw (DESCRIPTIVE) columns/rows: world-frame position error with NOTHING FITTED (no rotation, translation or "
            "scale alignment), RMS and end-of-cruise, 3D (matching evo -a (cruise)'s own pose_relation, the translation "
            "part) - limitations.md item 5; decisions D106, D111; eval/results/raw_corridor_errors.json via "
            "docs/thesis/raw_corridor/raw_corridor_numbers.md.")
bb = L("blank_behaviour.json")
BLANK = {}
for est, keys in (("UKF", ("ukf", "ukf_baseline")), ("FGO", ("fgo", "fgo_baseline"))):
    rows = []
    for trn, v in bb.items():
        if "blank" not in trn or trn.startswith("ds_"):
            continue
        a = next((v[k] for k in keys if k in v), None)
        if a is None:
            continue
        rows.append([math.hypot(a[t]["along_m"], a[t]["cross_m"]) for t in ("+10s", "+30s", "+60s", "end")])
    BLANK[est] = np.array(rows)
EK_INV = [v["EKF3_invalid_period"]["duration_in_cruise_s"] for k, v in bb.items() if "blank" in k and "EKF3_invalid_period" in v]
agg = L("expT/t_aggregate.json")
TCOND = "ABCD"; TLAB = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
TRK = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
TSTY = {"EKF3 live": ("EKF3", "live"), "UKF live": ("UKF", "live"), "FGO live": ("FGO", "live"),
        "RTS-UKF (hindsight)": ("UKF", "hind"), "FGO hindsight (whole-flight batch)": ("FGO", "hind")}
TSHORT = {"EKF3 live": "EKF3 live", "UKF live": "UKF live", "FGO live": "FGO live", "RTS-UKF (hindsight)": "smoothed UKF (hindsight)",
          "FGO hindsight (whole-flight batch)": "FGO whole-flight batch (hindsight)"}
OFL = ("O_r1", "O_r2", "O_r3b")
OI = {n: [L(f"expO/{t}.json")["tracks"][n]["indoor_rmse_m"] for t in OFL] for n in TRK}
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = ["s2v2_r1", "s2v2_r2", "s2v2_r3"]; S2O = ["s2_r1", "s2_r2", "s2_r3"]
S3V = ["s3v2_r1", "s3v2_r2", "s3v2_r3"]; S3O = ["s3_r1", "s3_r2", "s3_r3"]
# 2026-11-12 regeneration (D149(b)/(c)): the corrected-priors re-fly of the FGO-flying hold set (AMENDMENT 2;
# refly_priors/numbers_refly.md section 4). This is now the CURRENT FGO-flying hold set everywhere in T5/T7/A2; S3V
# (original priors) moves to the appendix as "superseded: original priors" (its own rows are kept, unchanged).
S3RP = ["s3rp_r1", "s3rp_r2", "s3rp_r3"]
HALF = {"EKF3": ("cl_a_tex_half", [f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)]),
        "UKF": ("cl_ukf_a_tex_half_v2", [f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)]),
        # 2026-11-12 regeneration (D149(c), numbers_refly.md): the FGO's current with-heading set and its no-heading
        # "off" flight both move to the corrected-priors re-fly (_rp). The original-priors v3 set is superseded (see
        # Table A.1's new row) and is NOT HALF["FGO"][0] any more - off is now flight 1 of the new corrected-priors
        # no-heading n = 3 cell (there is no single-flight "as recorded" FGO row to preserve here: the whole FGO
        # no-heading cell at this build is new, D149(b)/row-ID-map #4).
        "FGO": ("cl_fgo_a_tex_r1_half_rp", [f"cl_fgo_b_tex_r{i}_half_rp" for i in (1, 2, 3)])}
HBUILD = {"EKF3": "EKF3", "UKF": "final UKF port", "FGO": "final FGO node (corrected priors, 4c07374b/HEAD)"}
# n = 3 no-heading cells (D149(a), numbers_extras.md + numbers_refly.md section 1): every flight of every cell, at
# both real-time factors. HALF_NH3 covers the half real-time cells (the ones T4 reports); FULL_NH3 the full
# real-time cells (reported only in the T4F companion table, never mixed with HALF_NH3 - D21/D98, no cross-speed
# comparison). Flight 1 of each EKF3/UKF cell is the pre-existing single-flight "as recorded" row (unchanged file);
# the FGO half cell has no such sibling (see the HALF["FGO"] comment above).
HALF_NH3 = {"EKF3": ["cl_a_tex_half", "cl_a_tex_half_r2", "cl_a_tex_half_r3"],
            "UKF": ["cl_ukf_a_tex_half_v2", "cl_ukf_a_tex_half_v2_r2", "cl_ukf_a_tex_half_v2_r3"],
            "FGO": [f"cl_fgo_a_tex_r{i}_half_rp" for i in (1, 2, 3)]}
FULL_NH3 = {"EKF3": ["cl_a_tex", "cl_a_tex_r2", "cl_a_tex_r3"], "UKF": [f"cl_ukf_a_tex_v2_r{i}" for i in (1, 2, 3)]}


def nh3(trs, win):
    """k/3, spread (descriptive) and per-flight contact times (s) for one no-heading n = 3 cell, against its own
    pre-registered window (D149(a)). Never mixes real-time factors or estimators (D21/D98)."""
    ts = [cl_meta(t)[1]["t_rel_cruise_s"] for t in trs]
    k = sum(win[0] <= t <= win[1] for t in ts)
    return k, len(trs), ts, f"{rd(min(ts), 1)}–{rd(max(ts), 1)}"
LL = {}
for mode in ("lc", "nolc"):
    for kind in ("live", "hindsight"):
        LL[(mode, kind)] = [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{mode} {kind}"] for r in (1, 2, 3)]


def drifts(trs, key, metric="eff"):
    out = [[], [], [], []]
    for t in trs:
        for i, lo in enumerate(HJ(t)["losses"]):
            v = lo[key]
            out[i].append(mm_(v["effective"]["drift_m"] if metric == "eff" else v["drift_end_m"]))      # exact m -> mm shift
    return out


# ============================================================================ ORDERING FOOTNOTES (2026-10-17, text only)
# Every place a table or caption claims, or declines to claim, an ordering carries a footnote with (a) the metric and its unit,
# (b) n with its unit of replication, (c) the pre-registered rule with its source line, (d) the result against the rule, and
# one of the fixed verdict phrases below (thesis_vocabulary.md §11; methodology_definitions_draft.md "n" and "Ordering
# verdicts"). Every number in a footnote is either computed from a result file and cross-checked (check()) in the item that
# shows it, or quoted from a source line that is read at build time and checked to contain the quoted phrase (cite()).
OCASE = {
    "met": "RULE MET: the ordering is claimed",
    "met_sim": "RULE MET: the similarity is claimed (no ordering)",
    "i": "case (i), TEST RUN, RULE NOT MET: no ordering is claimed",
    "ii": "case (ii), FAILED AS WORDED: the registered prediction is false as written; a failed criterion does not by itself "
          "establish an ordering, so any ordering shown is descriptive",
    "iii": "case (iii), NO COMPARATIVE TEST REGISTERED: values are descriptive",
    "iiiC": "case (iii), REGISTERED COMPARISON WITHOUT A DECISION RULE (C1.a was registered to be reported, with no decision "
            "rule): the ordering is descriptive, not tested"}
OCASE_KEY = ("Ordering verdicts used in the footnotes: RULE MET = a pre-registered rule was applied and met, so its ordering (or "
             "similarity) is claimed; case (i) TEST RUN, RULE NOT MET = a pre-registered decision rule with a 'no ordering' outcome "
             "was applied and gave that outcome; case (ii) FAILED AS WORDED = a pre-registered prediction of an ordering or a "
             "similarity was scored literally and is false, which does not by itself establish the opposite ordering; case (iii) "
             "NO COMPARATIVE TEST REGISTERED = values are descriptive. n always names its unit (flights, bags, losses).")
_SRC = {}
HB_, HR_ = "FGO hindsight (whole-flight batch)", "RTS-UKF (hindsight)"
# 2026-11-12 regeneration (D149(c)): ob_h5()'s PRIMARY reading is now the corrected-priors re-fly
# (expH/h_comparative_refly_priors.json; refly_priors/numbers_refly.md section 4.3), not the original-priors
# h_comparative_2026-10-11.json this used before. The original-priors "re-flown" set is superseded (Table A.2's
# own historical build-ablation page still cites h_comparative_2026-10-11.json directly, unchanged, labelled
# superseded there).
_HCJ_ = L("expH/h_comparative_refly_priors.json")["new"]; _HE_ = _HCJ_["EKF3 (S1 far, flying)"]
_HSET_ = {("re" if k.startswith("re-flown") else "old"): v for k, v in _HCJ_["sets"].items()}


def cite(path, line, phrase):
    """A cited rule line: read the source at build time and check that line `line` contains `phrase` (the quoted rule text,
    with its numbers). Returns the citation 'file:line'."""
    lines = _SRC.setdefault(path, open(os.path.join(ROOT, path)).read().split("\n"))
    got = phrase if phrase in lines[line - 1] else lines[line - 1].strip()[:90]
    check(f"rule text {os.path.basename(path)}:{line} contains the quoted phrase", got, phrase, f"{path}:{line} (read at build time)")
    return f"{os.path.basename(path)}:{line}"


def vquote(path, a, b, text):
    """A VERBATIM quote (ruling 2026-10-17, Experiment 5 wording): `text` must occur, unbroken, in lines a..b of the source as
    read at build time, with markdown emphasis, code ticks and list bullets removed and whitespace collapsed (no ellipsis, no
    paraphrase). Returns the citation 'file:a' or 'file:a–b'."""
    lines = _SRC.setdefault(path, open(os.path.join(ROOT, path)).read().split("\n"))
    src = " ".join(re.sub(r"^\s*-\s+", "", ln) for ln in lines[a - 1:b])
    src = re.sub(r"\s+", " ", src.replace("**", "").replace("`", "")).strip()
    got = text if text in src else src[:90]
    ref = f"{os.path.basename(path)}:{a}" + (f"–{b}" if b != a else "")
    check(f"verbatim quote {ref}", got, text, f"{path}:{a}-{b} (read at build time; emphasis and bullets removed)")
    return ref


def obasis(tag, what, metric, n, rule, result, case):
    return (f"[{tag}] Ordering basis, {what}. Metric: {metric}. n = {n}. Rule: {rule}. Result: {result}. "
            f"Verdict: {OCASE[case]}.")


M_ = "METHODOLOGY.md"
ATE_M = "cruise ATE (SE(3)-aligned ATE over the pinned cruise window), m"


def ob_h11(tag):
    """H1.1, the confirmatory EKF3-vs-FGO test (1A, no heading)."""
    nf, nu = len(pt["new_flights"]), len(pt["usable_for_FGO"])
    check("H1.1: flights in the test / usable for the FGO", f"{nf} / {nu}", "7 / 6", "numbers.md §6.1 confirmatory row ('r4–r10 … r10 unusable for FGO')")
    check("H1.1: flights with d < 0 (EKF3 lower), of all flights", f"{pt['n_neg']}/{nf}", "5/7", "numbers.md §6.1 confirmatory row ('d < 0 on 5/7')")
    check("H1.1 confirmatory mean d, CI (m)", f"{rd(pt['mean_d_m'], 3)} [{rd(pt['t95_ci_m'][0], 3)}, {rd(pt['t95_ci_m'][1], 3)}]", "-0.021 [-0.989, 0.947]", "numbers.md §6.1")
    check("H1.1 confirmatory EKF3 − FGO verdict", pt["verdict"], "no ordering claimed", "numbers.md §6.1 confirmatory row; claim 2")
    src = ", ".join([cite(M_, 5650, "at least 6 of 7"), cite(M_, 5652, "the 95% t-interval (df 6) of mean `d` excludes 0"),
                     cite(M_, 5653, "by the mirror rule"), cite(M_, 5654, "Otherwise: no ordering is claimed"),
                     cite(M_, 6237, "r10 has no FGO value, so it is counted as **NOT**"), cite(M_, 6239, "the **6 usable** flights (df 5)")])
    return obasis(tag, "no heading, EKF3 against the FGO (H1.1, the confirmatory test)", ATE_M,
                  f"{nf} flights (flights 4–10 of the standard-sensor dataset: independent repeats of the same flight profile on the "
                  f"textured floor, every estimator on the same flights, paired); flight 10 has no FGO value, so it counts as 'not "
                  f"lower' in the sign count and the 95% t-interval uses the {nu} usable flights (df 5)",
                  "claim 'EKF3 lower' (or, by the mirror rule, 'FGO lower') only if (a) the paired difference d = EKF3 − FGO is "
                  "negative on at least 6 of 7 flights AND (b) the 95% t-interval of mean d excludes 0; otherwise no ordering is "
                  f"claimed (pre-registered, H1.1; {src})",
                  f"EKF3 lower on {pt['n_neg']} of {nf}; mean d {rd(pt['mean_d_m'], 3, sign=True)} m, 95% CI {rd(pt['t95_ci_m'][0], 3, sign=True)} "
                  f"to {rd(pt['t95_ci_m'][1], 3, sign=True)} m (includes 0); (a) and (b) both fail", "i")


def ob_ukf1a(tag):
    """1A: the UKF's standing (no test) and the medians over flights 1-9."""
    hi = sum(dict(DSN["UKF"])[i] > max(dict(DSN["EKF3"])[i], dict(DSN["FGO"])[i]) for i in range(1, 10))
    check("1A: flights on which the UKF has the highest cruise ATE, of flights 1–9", f"{hi}/{len(DSN['UKF'])}", "6/9", "numbers.md §6.1 UKF standing row ('UKF highest on 6/9 flights')")
    check("standard-sensor dataset, textured floor, median of flights 1–9, EKF3 / UKF / FGO (m)", " / ".join(f2(med[e]) for e in EST), "4.10 / 5.13 / 4.46", "numbers.md §6.1 standing row")
    return obasis(tag, "no heading, the UKF against EKF3 and the FGO, and the medians over flights 1–9", ATE_M,
                  f"{len(DSN['UKF'])} flights (flights 1–9 of the standard-sensor dataset, textured floor; every estimator on the same "
                  "flights)",
                  f"none: 'descriptive; no pre-registered UKF ordering test' ({cite(M_, 7187, 'descriptive; no pre-registered UKF ordering test')}); "
                  "the medians over flights 1–9 are descriptive for all three, the confirmatory test being H1.1 on flights 4–10",
                  f"medians EKF3 {f2(med['EKF3'])}, UKF {f2(med['UKF'])}, FGO {f2(med['FGO'])} m; the UKF highest on {hi} of "
                  f"{len(DSN['UKF'])} flights", "iii")


def ob_c1a(tag):
    """C1.a: FGO vs UKF with heading (1B, offline)."""
    u6_ = [P4[b]["UKF_heading"] for b in CAMB]; g6_ = [P4[b]["FGO_heading"] for b in CAMB]
    check("C1.a with heading UKF / FGO range, 6 textured-floor bags (m)", f"{rng(u6_)} / {rng(g6_)}", "0.13–0.25 / 0.06–0.22", "numbers.md §6.6 heading-arm rows")
    check("C1.a FGO lower than UKF", f"{sum(a < b for a, b in zip(g6_, u6_))}/{len(CAMB)}", "6/6", "numbers.md §6.6 C0 row; claim 7")
    return obasis(tag, "with the camera heading, the FGO against the UKF (C1.a)", ATE_M,
                  f"{len(CAMB)} bags (textured floor, flights 1–3 of the textured-wall and of the plain-wall camera dataset; the UKF "
                  "and the FGO replayed offline on the same bags, paired; on the 3 plain-wall bags the heading failed its validation, H1.2)",
                  f"none: C1.a was registered as 'REPORT, no decision rule' ({cite(M_, 7892, 'REPORT, no decision rule')})",
                  f"FGO lower on {sum(a < b for a, b in zip(g6_, u6_))} of {len(CAMB)} bags (UKF {rng(u6_)} m, FGO {rng(g6_)} m)", "iiiC")


def ob_blank(tag):
    """Blank floor: not an accuracy comparison (ruling)."""
    check("n flights UKF / FGO", f"{len(BLANK['UKF'])}/{len(BLANK['FGO'])}", "11/11", "numbers.md §6.2")
    check("EKF3 blank invalid for (s of cruise), all 14", rng(EK_INV, 0) + f" (n {len(EK_INV)})", "301–310 (n 14)", "numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s')")
    return obasis(tag, "blank floor (no flow aiding), all three estimators",
                  "error magnitude hypot(along, cross) after the flow-loss point, m, and EKF3's invalid period, s of cruise",
                  f"{len(BLANK['UKF'])} flights for the UKF and the FGO (both replayed on the same {len(BLANK['FGO'])} blank-floor bags) and "
                  f"{len(EK_INV)} flights for EKF3 (all blank-floor flights, Experiments 1A and 1B pooled)",
                  "none: the blank floor is ruled 'Not accuracy comparisons' "
                  f"({cite(M_, 5551, '**Not accuracy comparisons** (ruling)')}); no comparative test was pre-registered",
                  "no estimator bounds position (UKF and FGO runaways, EKF3 position invalid), so no ordering is formed", "iii")


def ob_h23(tag):
    """Experiment 2 live: H2.3 (similarity) FAILS; no ordering test; condition D descriptive. Metres (units pass 2026-10-23: one unit
    per quantity in tables and figures; position error in m)."""
    r = [agg["P-T3 live ratio max/min"]["by_condition"][c] for c in TCOND]
    check("H2.3 live max/min ratio A / B / C / D", " / ".join(rd(x, 2) for x in r), "1.97 / 2.36 / 1.42 / 1.57", "numbers.md §16.1 P-T3")
    nfl = [len([rr for rr in (1, 2, 3) if os.path.exists(os.path.join(RES, f"expT/T_{c}_r{rr}.json"))]) for c in TCOND]
    check("Experiment 2: flights per condition A / B / C / D", " / ".join(map(str, nfl)), "3 / 3 / 3 / 3", "numbers.md §16.1 heading ('3 repeats per condition')")
    check("Experiment 2 condition D live EKF3 / UKF / FGO (m)", " / ".join(f"{rd(mrD[k], 3)}" for k in ("EKF3 live", "UKF live", "FGO live")), "0.096 / 0.131 / 0.083", "numbers.md §16.1 table")
    return obasis(tag, "Experiment 2 live tracks, EKF3, UKF and FGO (H2.3)",
                  "horizontal RMSE over the 5 laps in the world frame, no alignment, mean of the flights in each condition, m",
                  f"{nfl[0]} flights per condition, 4 conditions ({sum(nfl)} flights; every estimator on the same flights, open loop on "
                  "simulator truth, paired)",
                  "H2.3 'live errors are similar': in every condition the largest live RMSE (mean over repeats) is ≤ 1.5 × the "
                  f"smallest ({cite(M_, 10178, 'live errors are similar')}, {cite(M_, 10179, 'is ≤ 1.5 × the smallest')}); no "
                  f"ordering test was registered, and the condition-D ordering is 'descriptive only (n = 3)' ({cite(M_, 12803, 'is descriptive only (n = 3)')})",
                  f"max ÷ min {' / '.join(rd(x, 2) for x in r)} (conditions A / B / C / D): H2.3 FAILS (C inside the band); "
                  f"condition D: FGO {rd_si(mrD['FGO live'], 3)}, EKF3 {rd_si(mrD['EKF3 live'], 3)}, UKF {rd_si(mrD['UKF live'], 3)} m, descriptive", "ii")


def ob_h24(tag):
    p4_ = agg["P-T4 hindsight ratio max/min"]
    check("H2.4 max/min ratio A / B / C / D", " / ".join(f"{rd(p4_['by_condition'][c], 2)}" for c in TCOND), "1.31 / 2.14 / 2.06 / 3.89", "numbers.md §16.1 P-T4")
    return obasis(tag, "Experiment 2 hindsight, the FGO whole-flight batch against the smoothed UKF (H2.4)",
                  "horizontal RMSE over the 5 laps in the world frame, mean of the flights in each condition, m",
                  "3 flights per condition, 4 conditions (both hindsight tracks from the same flights, paired)",
                  "H2.4 'FGO hindsight ≈ RTS-UKF': in every condition the larger RMSE (mean over repeats) is ≤ 1.5 × the smaller "
                  f"({cite(M_, 10180, 'FGO hindsight ≈ RTS-UKF')}, {cite(M_, 10181, 'is ≤ 1.5 × the smaller')}); no ordering test was registered",
                  f"max ÷ min {' / '.join(rd(p4_['by_condition'][c], 2) for c in TCOND)}: H2.4 FAILS; the FGO whole-flight batch is the "
                  "lower in every condition (descriptive)", "ii")


def ob_h42(tag):
    check("Experiment 4 H4.2 live max/min ratio; largest = EKF3 in every flight", f"{rng(ho2)}; {ho2_max_is_ekf3}", "1.71–1.84; True", "numbers.md §16.2 H-O2 bullet")
    ne = sum(max(EST, key=lambda e: OI[f"{e} live"][i]) == "EKF3" for i in range(3))
    check("Experiment 4: flights in which EKF3 live has the largest indoor RMSE", f"{ne}/{len(OFL)}", "3/3", "numbers.md §16.2 H-O2 bullet (EKF3 largest in every flight)")
    return obasis(tag, "Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2)",
                  "indoor horizontal RMSE in the world frame, no alignment, over the 123 s without GNSS, m",
                  f"{len(OFL)} flights (every estimator on the same flights, open loop on simulator truth, paired)",
                  "H4.2 'live indoor errors are similar': in every flight the largest live indoor RMSE is ≤ 1.5 × the smallest "
                  f"({cite(M_, 10360, 'live indoor errors are similar')}, {cite(M_, 10361, 'is ≤ 1.5 × the smallest')}); no ordering test was registered",
                  f"max ÷ min {rng(ho2)}: H4.2 NOT MET; EKF3 largest in {ne} of {len(OFL)} flights; UKF {rng(OI['UKF live'])} m and "
                  f"FGO {rng(OI['FGO live'])} m (both descriptive)", "ii")


def ob_h41(tag):
    k = sum(OI["FGO hindsight (whole-flight batch)"][i] < min(OI["EKF3 live"][i], OI["UKF live"][i]) for i in range(3))
    check("H4.1: FGO whole-flight batch below both filters' live tracks, flights", f"{k}/3", "3/3", "numbers.md §16.2 (H-O1 PASS 3/3)")
    return obasis(tag, "Experiment 4, the FGO whole-flight batch (hindsight) against the EKF3 and UKF live tracks (H4.1)",
                  "indoor horizontal RMSE in the world frame, no alignment, m", f"{len(OFL)} flights (same flights, paired)",
                  "H4.1: PASS iff in 3/3 flights the FGO-batch indoor RMSE is < both EKF3's and the UKF's live indoor RMSE "
                  f"({cite(M_, 10358, 'PASS iff in 3/3')}, {cite(M_, 10359, 'is < both EKF3')})",
                  f"lower than both in {k} of {len(OFL)} flights: H4.1 PASSES (a hindsight track against live tracks, not like with like)", "met")


def ob_h43(tag):
    o3_ = [max(OI[HB_][i], OI[HR_][i]) / min(OI[HB_][i], OI[HR_][i]) for i in range(3)]
    check("Experiment 4 FGO whole-flight batch vs smoothed UKF ratio, max/min per flight (capped)", rng(o3_), "1.01–1.02", "numbers.md §16.2 P-O3")
    return obasis(tag, "Experiment 4, the FGO whole-flight batch against the smoothed UKF (H4.3)",
                  "indoor horizontal RMSE in the world frame, no alignment, m", f"{len(OFL)} flights (same flights, paired)",
                  f"H4.3: the two RMSEs within 1.5× of each other in every flight ({cite(M_, 10362, 'within 1.5× of each other in every')})",
                  f"max ÷ min {rng(o3_)}: H4.3 PASSES; which is lower changes between flights (descriptive)", "met_sim")


def ob_ret(tag):
    st = {e: [L(f"expO/{t}.json")["tracks"][f"{e} live"]["max_step_after_return_m"] for t in OFL] for e in EST}
    check("Experiment 4 largest step in 10 s after return EKF3 / UKF / FGO live (m)", " / ".join(rng(st[e]) for e in EST), "4.10–4.10 / 2.30–2.44 / 2.14–2.28", "numbers.md §16.2 table")
    return obasis(tag, "Experiment 4, the jump on the return to GNSS", "largest position step in the 10 s after GNSS returns, m",
                  f"{len(OFL)} flights (same flights for every estimator)",
                  f"none: EKF3's jump is 'Reported regardless' ({cite(M_, 10365, 'Reported regardless')}); no comparative test was pre-registered",
                  f"EKF3 {rng(st['EKF3'])}, UKF {rng(st['UKF'])}, FGO {rng(st['FGO'])} m. EKF3's jump is measured once the simulation's "
                  "GNSS switching script moves EKF3 off its indoor source set, about 4.3 s after GNSS returns (the script waits for 40 "
                  "consecutive GPS-status checks, 100 ms apart, about 4.0 s, plus about 0.3 s of simulated GPS latency). The UKF and FGO "
                  "replays take every GNSS sample as it is recorded, with no gate and no reset on return, so they carry no equivalent "
                  "delay", "iii")


def ob_l(tag, t1=False):
    lc = [t["rmse_m"] for t in LL[("lc", "live")]]; nl = [t["rmse_m"] for t in LL[("nolc", "live")]]
    lch = [t["rmse_m"] for t in LL[("lc", "hindsight")]]; nlh = [t["rmse_m"] for t in LL[("nolc", "hindsight")]]
    r5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("lc", "live")]]
    q5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("nolc", "live")]]
    cnt = [sum(x <= 1.5 for x in r5), sum(a < b for a, b in zip(lc, nl)), sum(a < b for a, b in zip(lch, nlh)), sum(x > 1.5 for x in q5)]
    check("Experiment 3 H3.1 / H3.2 / H3.3 / H3.4: flights passing, of 3", " ".join(f"{c}/3" for c in cnt), "3/3 3/3 3/3 3/3", "numbers.md §16.3 ('H-L1 (primary), H-L2, H-L3 and P-L4: PASS 3/3')")
    check("Experiment 3 with loop closure, live overall (m)", rng(lc, 3), "0.049–0.076", "numbers.md §16.3")
    check("Experiment 3 without loop closure, live overall (m)", rng(nl, 3), "0.263–0.361", "numbers.md §16.3")
    return obasis(tag, "Experiment 3, the keyframe FGO with against without loop closure (H3.1–H3.4; one estimator, not a comparison of estimators)",
                  "horizontal RMSE in the first tag's frame, overall and per 6 m lap, m",
                  "3 flights (each flight replayed with and without loop closure, paired)",
                  f"H3.2 'LC live overall RMSE < no-LC live overall RMSE in 3/3 flights' ({cite(M_, 10503, 'LC live overall RMSE < no-LC live overall RMSE in 3/3 flights')}); "
                  f"H3.3 the same for hindsight ({cite(M_, 10504, 'LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights')}); "
                  f"H3.1 with loop closure lap 5 ≤ 1.5 × lap 1 in 3/3 ({cite(M_, 10501, 'the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3')}); "
                  f"H3.4 without, lap 5 > 1.5 × lap 1 in 3/3 ({cite(M_, 10505, 'lap 5 > 1.5 × lap 1 in 3/3 flights')})",
                  f"H3.1 / H3.2 / H3.3 / H3.4 pass on {' / '.join(str(c) for c in cnt)} of 3 flights (live {rng(lc, 3)} m with loop "
                  f"closure, {rng(nl, 3)} m without); scope: all 8 tags and correct tag IDs" + ("; extensions in footnote [k]" if t1 else
                  " (extensions in the caption)"), "met")


# Experiment 5 comparative hypotheses, VERBATIM (ruling 2026-10-17): their only pre-registration is the design draft §e
# (docs/tag_hold_design.md), committed in c11fcf3 (2026-10-08 15:17), before the first Experiment 5 flight; checked unchanged below.
_THD = "docs/tag_hold_design.md"
H5V = {"H-H2": (_THD, 180, 180, "H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights."),
       "P-H3": (_THD, 183, 183, "P-H3 (smoothness, prediction): gyro activity in the hold windows within 1.5× across estimators."),
       "H-H4 (15 s)": (_THD, 185, 186, "After the 15 s occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's "
                                       "and the FGO's in 3/3 flights."),
       "H-H4 (5 s)": (_THD, 187, 187, "After the 5 s occlusion (no timeout), the jumps are within 1.5× of each other.")}
H5V_C = "c11fcf3"
H5V_DATE = subprocess.run(["git", "-C", ROOT, "show", "-s", "--format=%ad", "--date=format:%Y-%m-%d %H:%M", H5V_C],
                          capture_output=True, text=True).stdout.strip()


def h5v_unchanged():
    """The design draft's §e hypothesis lines (176-188) are identical at c11fcf3 and now (so the quoted wording predates the runs)."""
    old = subprocess.run(["git", "-C", ROOT, "show", f"{H5V_C}:{_THD}"], capture_output=True, text=True).stdout.split("\n")[175:188]
    now = open(os.path.join(ROOT, _THD)).read().split("\n")[175:188]
    check(f"{_THD}:176-188 (§e hypotheses) identical at {H5V_C} ({H5V_DATE}) and at build time", old == now, True, f"git show {H5V_C}:{_THD}")


def ob_h5(tag, short=False):
    """Experiment 5 comparative hypotheses on the final-build sets (H5.2, H5.3, H5.4a, H5.4b). Hold error and jump in mm everywhere
    (units pass 2026-10-23; the figure-set A.2 image returned from m to mm)."""
    h5v_unchanged()
    v = _HSET_["re"]; runs = v["criteria"]["runs"]
    hu = [r["hold_mean_mm"] for r in v["UKF"]]; hf = [r["hold_mean_mm"] for r in v["FGO"]]; he = [r["hold_mean_mm"] for r in _HE_]
    fl = sum(r["lowest_hold"] == "FGO" for r in runs); ul = sum(r["lowest_hold"] == "UKF" for r in runs)
    je = [r["jump_15s_mm"] for r in _HE_]
    p3 = [r["ph3_ratio"] for r in runs]; p4b = [r["hh4b_ratio"] for r in runs]
    check("Experiment 5 (final-build sets, corrected priors): flights with the FGO / the UKF lowest mean hold error", f"{fl}/3 / {ul}/3", "0/3 / 3/3",
          "numbers_refly.md §4.3 criteria table (H-H2: 'FAIL (0/3 FGO lowest)'; lowest_hold = UKF on all 3)")
    check("Experiment 5 hold UKF / FGO / EKF3, final-build sets, corrected priors (mm)", f"{rng(hu, 1)} / {rng(hf, 1)} / {rng(he, 1)}", "6.4–7.1 / 7.3–8.3 / 7.8–7.9",
          "numbers_refly.md §4.3 (FGO 7.308/8.340/7.488; UKF, EKF3 unchanged)")
    check("H5.3 / H5.4b max/min, final-build sets, corrected priors", f"{rng(p3)} / {rng(p4b, 1)}", "2.40–2.58 / 2.1–5.1", "numbers_refly.md §4.3 (ratios 2.1-5.1, narrowed from 3.2-7.7)")
    check("H5.4a EKF3 15 s re-lock jump per flight (mm)", " / ".join(rd(x, 0) for x in je), "5 / 5 / 7", "numbers_refly.md §4.3 (unchanged: not driven by the FGO)")
    check("Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors)", "; ".join(v["criteria"][k].split()[0] for k in ("H-H2", "P-H3", "H-H4 (15 s)", "H-H4 (5 s)")),
          "FAIL; FAIL; FAIL; FAIL", "numbers_refly.md §4.3 (unchanged verdict category; underlying FGO values narrower)")
    q = {k: (H5V[k][3], vquote(*H5V[k])) for k in H5V}
    return obasis(tag, "Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b)",
                  "H5.2 mean hold error, mm; H5.3 hold gyro activity, max ÷ min across the estimators; H5.4a/b re-lock jump after the "
                  "15 s / 5 s tag loss, mm",
                  "3 flights per estimator (each estimator flew its own 3 flights, paired by run index, not trajectory; EKF3 = the "
                  "EKF3-flying hold set at the far spawn)",
                  "the pre-registered wording, verbatim: H5.2 '" + q["H-H2"][0] + f"' ({q['H-H2'][1]}); H5.3 '" + q["P-H3"][0] +
                  f"' ({q['P-H3'][1]}); H5.4a, under 'H-H4 (tag loss)': '" + q["H-H4 (15 s)"][0] + f"' ({q['H-H4 (15 s)'][1]}); H5.4b: '" +
                  q["H-H4 (5 s)"][0] + f"' ({q['H-H4 (5 s)'][1]}) (design §e, the only pre-registration of these four: they have no "
                  f"METHODOLOGY pre-registration line; §e is unchanged since {H5V_C} ({H5V_DATE}), before the first Experiment 5 flight; "
                  f"verdicts {cite(M_, 12236, 'H-H2 FAILS')}, {cite(M_, 13549, 'ALL FAIL')})",
                  f"FGO lowest in {fl} of 3 flights (hold UKF {rng(hu, 1)}, EKF3 {rng(he, 1)}, FGO {rng(hf, 1)} mm; UKF lowest in {ul} of 3); "
                  f"H5.3 max ÷ min {rng(p3)}; H5.4a EKF3's 15 s jump {' / '.join(rd(x, 0) for x in je)} mm, the smallest; H5.4b max ÷ min "
                  f"{rng(p4b, 1)}: all four FAIL", "ii")


def ob_safe(tag):
    """5S safety tests: per-estimator criteria; no comparison across estimators registered."""
    src = ", ".join([cite(M_, 11295, "S-A1 (attitude correct, not frozen)"), cite(M_, 11297, "S-A2 (trigger)"),
                     cite(M_, 11300, "within **5.5 s** of the kill"), cite(M_, 11301, "S-A3 (safe landing)"), cite(M_, 11307, "S-A4 (b runs only)")])
    return obasis(tag, "5S safety tests, the UKF and FGO runs (and the EKF3 reference kill)",
                  "as-worded pass/fail of the attitude criterion, the position-lost declaration (delay, s, against its bound), safe "
                  "landing (drift to touchdown, m) and single landing",
                  "1 flight per run (each test flown once per build, some re-flown; every run is its own flight, unpaired)",
                  f"per-run criteria only ({src}); no comparison between the estimators was pre-registered",
                  "the as-worded verdicts per run, as tabulated", "iii")


def ob_cl(tag, with_contact=True, clean=False):
    """1C closed loop: per-estimator criteria only; the cross-estimator comparison is descriptive.

    `clean=True` (task 8, T4/T4F restyle): returns a footnote text for direct use in a table footnote, with (a) the
    n-statement corrected to n = 3 per estimator without heading (the no-heading cells became a k/3 count over the
    SAME 3 flights each estimator flies with heading, not a single flight, in the regeneration that added the n = 3
    no-heading cells - this function's own "n" text was never updated to match, which is the bug task 8 asks fixed),
    and (b) no METHODOLOGY line citations spliced into the printed text (the cite() calls below still run, for their
    own check() side effects, so the check count this figure/table reports from ob_cl() is unchanged either way)."""
    check("closed loop, half real-time, with heading: flights passing all five criteria (+ estimator validity)", " / ".join(f"{passh[e]}/3" for e in EST), "3/3 / 3/3 / 3/3", "numbers.md §15")
    check("closed loop, half real-time, with heading: max cross-track range EKF3 / final UKF port / final FGO node (m)", " / ".join(rng(B2h[e]) for e in EST), "0.24–0.33 / 0.22–0.25 / 0.04–0.32",
          "numbers.md §15 B2 row (EKF3 half) and re-flown rows")
    src = ", ".join([cite(M_, 4948, "[+155, +215] s"), cite(M_, 7513, "[+146, +218] s"), cite(M_, 8995, "[+145, +196] s"),
                     cite(M_, 4951, "B1."), cite(M_, 4966, "B5."), cite(M_, 7362, "S2 is the estimator valid throughout")])
    desc_cite = cite(M_, 9355, 'DESCRIPTIVE; separate flights, n = 3 each, no ordering claim')
    if clean:
        return obasis(tag, "Experiment 1C closed loop, EKF3, final UKF port and final FGO node",
                      "without heading: wall-contact time after cruise start against each estimator's own contact window, s; with heading: "
                      "pass/fail of the five closed-loop criteria and the estimator-validity criterion, with max |cross-track| in cruise (m), "
                      "heading error p95 and max (°) and max lateral speed (m/s)",
                      "3 flights per estimator without heading and 3 flights per estimator with heading (each estimator flew its own "
                      "flights: separate, unpaired flights)",
                      "per-estimator criteria only (H1.8 contact window and H1.9 the five criteria); no comparative test between the "
                      "estimators was pre-registered, and the comparison across the with-heading sets is descriptive: separate flights, "
                      "n = 3 each, no ordering claim",
                      f"with heading {' / '.join(f'{passh[e]}/3' for e in EST)} flights pass (EKF3 / UKF / FGO); max cross-track "
                      f"{' / '.join(rng(B2h[e]) for e in EST)} m", "iii")
    return obasis(tag, "Experiment 1C closed loop, EKF3, final UKF port and final FGO node",
                  "without heading: wall-contact time after cruise start against each estimator's own contact window, s; with heading: "
                  "pass/fail of the five closed-loop criteria and the estimator-validity criterion, with max |cross-track| in cruise (m), "
                  "heading error p95 and max (°) and max lateral speed (m/s)",
                  "1 flight per estimator without heading and 3 flights per estimator with heading (each estimator flew its own "
                  "flights: separate, unpaired flights)",
                  f"per-estimator criteria only (H1.8 contact window and H1.9 the five criteria; {src}); no comparative test "
                  f"between the estimators was pre-registered, and the comparison across the with-heading sets is 'DESCRIPTIVE; separate "
                  f"flights, n = 3 each, no ordering claim' ({desc_cite})",
                  f"with heading {' / '.join(f'{passh[e]}/3' for e in EST)} flights pass (EKF3 / UKF / FGO); max cross-track "
                  f"{' / '.join(rng(B2h[e]) for e in EST)} m", "iii")


# =============================================================================================== FIG 1 scorecard
# Ruling 2026-10-17 (scorecard): an ordering label (BEST / BEHIND, and TIED, which claims equality) is printed ONLY where a
# pre-registered decision rule was met; no comparison in this table met one, so the ordering labels are gone. The status words
# below are not orderings: BLANK_ST (the blank-floor status, ruling 2026-10-18: replaces the word FAILED), PASSED (met its own
# pre-registered criteria), N/A (not run).
BLANK_ST = "no estimator bounds position (EKF3 flags invalid; UKF and FGO diverge)"
CAT = {BLANK_ST: ("#ffffff", "no bound"), "PASSED": ("#f0f0f0", "passed"), "N/A": ("#ffffff", "n/a")}
med = {e: float(np.median([v for _, v in DSN[e]])) for e in EST}
check("standard-sensor dataset, textured floor, median of flights 1–9, EKF3 / UKF / FGO (m)", " / ".join(f2(med[e]) for e in EST), "4.10 / 5.13 / 4.46", "numbers.md §6.1 standing row")
check("H1.1 confirmatory EKF3 − FGO verdict", pt["verdict"], "no ordering claimed", "numbers.md §6.1 confirmatory row; claim 2")
u6 = [P4[b]["UKF_heading"] for b in CAMB]; g6 = [P4[b]["FGO_heading"] for b in CAMB]
check("C1.a with heading UKF / FGO range, 6 textured-floor bags (m)", f"{rng(u6)} / {rng(g6)}", "0.13–0.25 / 0.06–0.22", "numbers.md §6.6 heading-arm rows")
check("C1.a FGO lower than UKF", f"{sum(a < b for a, b in zip(g6, u6))}/6", "6/6", "numbers.md §6.6 C0 row; claim 7")
BLK = {e: grp(rng_si(BLANK[e][:, 3], -3)) for e in ("UKF", "FGO")}       # m to the nearest 1000 m (units pass 2026-10-23; was km)
check("blank end-of-cruise UKF / FGO (m, nearest 1000 m; numbers.md km × 10^3, digits grouped) †", f"{BLK['UKF']} / {BLK['FGO']}",
      grp(si_str("29–40 / 23–41", 3)), "numbers.md §6.2 erratum E6 ('29–40 / 23–41' km)")
check("EKF3 blank invalid for (s of cruise), all 14", rng(EK_INV, 0) + f" (n {len(EK_INV)})", "301–310 (n 14)", "numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s')")
mrD = agg["conditions"]["D"]["mean_rmse_m"]
check("Experiment 2 condition D live EKF3 / UKF / FGO (m)", " / ".join(f"{rd(mrD[k], 3)}" for k in ("EKF3 live", "UKF live", "FGO live")), "0.096 / 0.131 / 0.083", "numbers.md §16.1 table")
check("Experiment 2 FGO whole-flight batch A–D (m)", rng([agg["conditions"][c]["mean_rmse_m"]["FGO hindsight (whole-flight batch)"] for c in TCOND], 3), "0.010–0.028", "numbers.md §16.1 table")
check("Experiment 4 indoor live RMSE EKF3 / UKF / FGO (m)", " / ".join(rng(OI[f"{e} live"]) for e in EST), "1.42–1.43 / 0.77–0.84 / 0.83–0.89", "numbers.md §16.2 table")
ho2 = [max(OI[f"{e} live"][i] for e in EST) / min(OI[f"{e} live"][i] for e in EST) for i in range(3)]
ho2_max_is_ekf3 = all(max(EST, key=lambda e: OI[f"{e} live"][i]) == "EKF3" for i in range(3))
check("Experiment 4 H4.2 live max/min ratio; largest = EKF3 in every flight", f"{rng(ho2)}; {ho2_max_is_ekf3}", "1.71–1.84; True", "numbers.md §16.2 H-O2 bullet")
check("Experiment 4 FGO whole-flight batch / smoothed UKF indoor (m)", f"{rng(OI['FGO hindsight (whole-flight batch)'])} / {rng(OI['RTS-UKF (hindsight)'])}", "0.59–0.59 / 0.58–0.60", "numbers.md §16.2 table")
check("Experiment 3 live with / without loop closure (m)", f"{rng([t['rmse_m'] for t in LL[('lc', 'live')]], 3)} / {rng([t['rmse_m'] for t in LL[('nolc', 'live')]], 3)}",
      "0.049–0.076 / 0.263–0.361", "numbers.md §16.3")
_hc = _HSET_["re"]       # 2026-11-12 regeneration: the same corrected-priors set ob_h5() uses (repointed above)
hE = [mm_(np.mean([w["mean_m"] for w in HJ(t)["hold_windows_vehicle"]])) for t in S1F]      # mm, exact shift
hU = [r["hold_mean_mm"] for r in _hc["UKF"]]; hF = [r["hold_mean_mm"] for r in _hc["FGO"]]
check("Experiment 5 run-mean hold error EKF3 (far spawn) / final UKF port / final FGO node (mm), corrected priors", f"{rng(hE, 1)} / {rng(hU, 1)} / {rng(hF, 1)}", "7.8–7.9 / 6.4–7.1 / 7.3–8.3", "numbers_refly.md §4.3 table")
check("Experiment 5 comparative H5.2; H5.3; H5.4a (15 s); H5.4b (5 s) (final builds, corrected priors)", "; ".join(_hc["criteria"][k].split()[0] for k in ("H-H2", "P-H3", "H-H4 (15 s)", "H-H4 (5 s)")),
      "FAIL; FAIL; FAIL; FAIL", "numbers_refly.md §4.3 (final-build sets primary; corrected priors)")
B2h = {e: [L(f"closed_loop_{t}.json")["B"]["B2"]["max_abs_x_cruise_m"] for t in HALF[e][1]] for e in EST}
passh = {e: sum(L(f"closed_loop_{t}.json")["B"]["pass"] and L(f"closed_loop_{t}.json").get("S2", {}).get("pass", True) for t in HALF[e][1]) for e in EST}
check("closed loop, half real-time, with heading: max cross-track range EKF3 / final UKF port / final FGO node (m)", " / ".join(rng(B2h[e]) for e in EST), "0.24–0.33 / 0.22–0.25 / 0.04–0.32",
      "numbers.md §15 B2 row (EKF3 half) and re-flown rows (UKF v2 0.231/0.253/0.219; FGO v3 0.118/0.033/0.392)")
check("closed loop, half real-time, with heading: flights passing all five criteria (+ estimator validity)", " / ".join(f"{passh[e]}/3" for e in EST), "3/3 / 3/3 / 3/3", "numbers.md §15")


# CLAIMS UPDATE APPLIED (user ruling 2026-10-24: "C1-C5: accepted as proposed"; D17 follow-up: the Experiment 3 UKF cell names the
# extension variant). Values from the tier-1 extension experiments (pre-registered 2026-10-21; signed off with amendments 2026-10-22),
# read from their verdict jsons and checked EXACTLY against the strings typed from e2/e3/e5_results.md (single rounding, rd()).
T1D = os.path.join(ROOT, "docs", "thesis", "tier1", "scores")
E5V = json.load(open(os.path.join(T1D, "e5_verdicts.json"))); E3V = json.load(open(os.path.join(T1D, "E3_verdicts.json")))
E2V = json.load(open(os.path.join(T1D, "E2_verdicts.json")))
E5R = [E5V["flights"][f]["descriptive ratios UKF/FGO"]["lc live"] for f in ("T_A_r1", "T_A_r2", "T_A_r3")]
_h31 = [v for k, v in E3V["criteria_a"].items() if k.startswith("H-E3.1")][0]
_b1 = [v for k, v in E3V["criteria_b"].items() if k.startswith("P-E3b.1 0.01")][0]
_b5 = [v for k, v in E3V["criteria_b"].items() if k.startswith("P-E3b.1 0.05")][0]


def ext_checks():
    check("E5 UKF with landmark states ÷ FGO, live overall RMSE with loop closure, range over 3 flights (DESCRIPTIVE)", rng(E5R, 2), "1.76–2.08",
          "tier1/e5_results.md §2 (UKF ÷ FGO 2.08 / 1.84 / 1.76, LC live); tier1/scores/e5_verdicts.json")
    check("E5 UKF ÷ FGO LC live per flight, each rounded once to an integer (the cell's '~2x')", " / ".join(rd(r, 0) for r in E5R), "2 / 2 / 2",
          "tier1/e5_results.md §2 (2.08 / 1.84 / 1.76)")
    check("E5 H-E5.1 (UKF-LC live lap 5 ≤ 1.5 × lap 1; the cell's 'bounded'); S-E5.5 (UKF-LC live > FGO-LC live)",
          f"{E5V['criteria']['H-E5.1']['verdict']} {E5V['criteria']['H-E5.1']['count']}; {E5V['criteria']['S-E5.5']['verdict']} {E5V['criteria']['S-E5.5']['count']}",
          "PASS 3/3; PASS 3/3", "tier1/e5_results.md §1 (H-E5.1 PASS 3/3; S-E5.5 PASS 3/3)")
    check("E3 H-E3.1 at 1% wrong ids: verdict, count; diverged runs", f"{_h31['verdict']} {_h31['count']}; {_h31['divergence']['total']}",
          "FAIL 0/9; 6 of 9 runs diverged", "tier1/e3_results.md §1 (H-E3.1 FAIL 0/9; 6 of 9 runs diverged)")
    check("E3 robust arm (b): P-E3b.1 at 1% / 5%; diverged runs", f"{_b1['verdict']} {_b1['count']} / {_b5['verdict']} {_b5['count']}; {E3V['divergence']['arm b']['total']}",
          "PASS 9/9 / PASS 9/9; 0 of 21 runs diverged", "tier1/e3_results.md §4 (P-E3b.1 PASS 9/9 at 1% and 9/9 at 5%; 0 of 21)")
    check("E2 H-E2.1 with 4 tags (B) / 2 tags (C)", " / ".join(f"{E2V['criteria']['H-E2.1'][c]['verdict']} {E2V['criteria']['H-E2.1'][c]['count']}" for c in "BC"),
          "PASS 3/3 / PASS 3/3", "tier1/e2_results.md §1 (H-E2.1 PASS 3/3 in each of B, C, D)")


def ob_ext(tag):
    ext_checks()
    return (f"[{tag}] Extensions to Experiment 3 (extension experiments, pre-registered 2026-10-21, signed off with amendments 2026-10-22; "
            f"condition A unless stated, n = 3 flights; claims C1–C3, ruling 2026-10-24). UKF cell: an extension variant, not the UKF used "
            f"elsewhere in this table: a UKF with each tag in its state, re-identification and an RTS smoother (E5). 'bounded' = H-E5.1 "
            f"{E5V['criteria']['H-E5.1']['verdict']} {E5V['criteria']['H-E5.1']['count']} (live lap 5 ≤ 1.5 × lap 1); '~2x FGO error' = UKF ÷ FGO "
            f"live overall RMSE with loop closure {rng(E5R, 2)}× (LC live, descriptive). That the variant's error is higher than the FGO's was "
            f"registered as a secondary direction (S-E5.5) and held {E5V['criteria']['S-E5.5']['count']}; no ordering label is printed, because "
            f"the magnitude is descriptive and the variant is not the thesis UKF. The thesis EKF3 and UKF, as configured, have no landmark "
            f"states; EKF3 with landmark states was not tested. FGO cell: with 4 tags and with 2 tags (E2), loop closure also bounded live drift "
            f"(H-E2.1 PASS 3/3 in each). The FGO result assumes correct tag IDs: with wrong IDs in 1% of the eligible detections (E3), the FGO "
            f"as built lost its loop-closure advantage (H-E3.1 {_h31['verdict']} {_h31['count']}; {_h31['divergence']['total']}); see the "
            f"limitations list, item 3.")

COLS = ["Experiment 1A: standard sensors (textured floor, no heading)", "Experiment 1B: with the camera heading (offline)",
        "Experiment 1: blank floor (no flow; 1A and 1B flights pooled)", "Experiment 2: known tags", "Experiment 4: outdoor–indoor (GNSS outside only)",
        "Experiment 3: loop closure (tags at unknown positions)", "Experiment 5: tag hold", "Experiment 1C: closed loop (the estimator flies)"]
CELLS = {
    "EKF3": [("", f"median {rd(med['EKF3'], 2)} m", "confirmatory test: no ordering"),
             ("N/A", "no offline heading arm", "the fixed no-heading baseline"),
             (BLANK_ST, "position invalid from take-off", "origin output, unscored"),
             ("", f"1 tag: {rd_si(mrD['EKF3 live'], 3)} m live", "no live ordering claimed"),
             ("", f"indoor {rng(OI['EKF3 live'])} m", "no live ordering claimed; 4.10 m jump, about 4.3 s after GNSS returns (the switching script's delay)"),
             ("N/A", "no landmark states", "the thesis EKF3 as configured has no loop closure; EKF3 with landmark states not tested"),
             ("", f"hold {rng(hE, 1)} mm", "bands PASS; comparatives FAIL"),
             ("", f"{passh['EKF3']}/3 pass; max cross-track ≤ {rd(max(B2h['EKF3']), 2)} m", "no ordering claimed")],
    "UKF": [("", f"median {rd(med['UKF'], 2)} m", "descriptive, 9 flights"),
            ("", f"{rng(u6)} m", "the FGO lower on 6/6; C1.a descriptive"),
            (BLANK_ST, f"{BLK['UKF']} m at end †", "no flow aiding"),
            ("", f"1 tag: {rd_si(mrD['UKF live'], 3)} m live", "no live ordering claimed"),
            ("", f"indoor {rng(OI['UKF live'])} m", "no live ordering claimed"),
            ("", "UKF with landmark states (extension E5): bounded; ~2x FGO error [k]", ""),
            ("", f"hold {rng(hU, 1)} mm", "bands PASS; comparatives FAIL"),
            ("", f"{passh['UKF']}/3 pass; max cross-track ≤ {rd(max(B2h['UKF']), 2)} m", "final UKF port")],
    "FGO": [("", f"median {rd(med['FGO'], 2)} m", "confirmatory test: no ordering"),
            ("", f"{rng(g6)} m", "lower than the UKF on 6/6; C1.a descriptive"),
            (BLANK_ST, f"{BLK['FGO']} m at end †", "no flow aiding"),
            ("", f"1 tag: {rd_si(mrD['FGO live'], 3)} m live", f"batch {rng_si([agg['conditions'][c]['mean_rmse_m']['FGO hindsight (whole-flight batch)'] for c in TCOND], 3)} m, H2.1 PASS"),
            ("", f"indoor {rng(OI['FGO live'])} m", "batch 0.59, within 1.5× of the smoothed UKF: H4.3 PASS"),
            ("PASSED", f"live {rng_si([t['rmse_m'] for t in LL[('lc', 'live')]], 3)} m", "H3.1–H3.4 PASS 3/3; 8 tags, correct tag IDs [k]"),
            ("", f"hold {rng(hF, 1)} mm", "bands PASS; comparatives FAIL"),
            ("", f"{passh['FGO']}/3 pass; max cross-track ≤ {rd(max(B2h['FGO']), 2)} m", "final FGO node, corrected priors")]}
T1MK = ["[a, b]", "[c]", "[d]", "[e]", "[f, g]", "[h]", "[i]", "[j]"]      # ordering footnotes per row (2026-10-17)
T1FN = [ob_h11("a"), ob_ukf1a("b"), ob_c1a("c"), ob_blank("d"), ob_h23("e"), ob_h42("f"), ob_h43("g"), ob_l("h", t1=True), ob_h5("i"), ob_cl("j", clean=True)]
rowsT1 = [[f"{col} {T1MK[j]}"] + [(f"{CELLS[e][j][0]}: " if CELLS[e][j][0] else "") + CELLS[e][j][1] + (f" ({CELLS[e][j][2]})" if CELLS[e][j][2] else "") for e in EST]
          for j, col in enumerate(COLS)]
# RAW (DESCRIPTIVE) companion rows for 1A and 1B (raw-tables stage 2; RAW_NOTE above). T1 is a matrix (experiment x
# estimator), so there is no per-estimator "column" to put a raw value beside; the structural equivalent is a row,
# directly under the aligned row it companions, over the SAME flights/bags that row's own aligned cell uses.
_T1A_TR = [f"dsn_tex_r{i}" for i in range(1, 10)]           # same 9 flights as med[e]/CELLS[e][0] (1A median)
_T1B_TR = [f"{ds}_tex_r{r}" for ds, r in CAMB]               # same 6 bags as u6/g6/CELLS[e][1] (1B with-heading range)
check("T1/T9 1A raw-row selection matches the aligned 1A median's own 9 flights (EKF3/UKF/FGO stored_ate_a_cruise == med input)",
      str(all(abs(stored_ate(f"dsn_tex_r{i}", e, "baseline") - v) < 1e-6 for e in EST for i, v in DSN[e])),
      "True", "eval/results/raw_corridor_errors.json cells vs this file's own DSN (rerun_dsn_evo.json, dsn_extra_evo.json)")
check("T1 1B raw-row selection matches the aligned 1B with-heading cells' own 6 bags (UKF/FGO stored_ate_a_cruise == u6/g6 input)",
      str(all(abs(stored_ate(f"{ds}_tex_r{r}", e, "heading") - P4[(ds, r)][f"{e}_heading"]) < 1e-6
              for e in ("UKF", "FGO") for ds, r in CAMB)),
      "True", "eval/results/raw_corridor_errors.json cells vs this file's own P4 (phase4_{fwdc,fwdplainc}_evo.json)")
rowsT1.insert(1, ["Experiment 1A: raw world-frame error, nothing fitted, DESCRIPTIVE [l]"] +
              [raw_med(_T1A_TR, e, "baseline") for e in EST])
rowsT1.insert(3, ["Experiment 1B: raw world-frame error, nothing fitted, DESCRIPTIVE [l]",
                  "no offline heading arm", raw_rng(_T1B_TR, "UKF", "heading"), raw_rng(_T1B_TR, "FGO", "heading")])
save_tab("T1", "T1_scorecard", "Scorecard of the restated verdicts by experiment and estimator",
         "Each cell gives the key number and the verdict it rests on, with a status (PASSED, N/A, or on the blank floor '" + BLANK_ST + "') where one applies. "
         "No ordering label is printed: an ordering (BEST / BEHIND / TIED) is shown only where a pre-registered decision rule was met, "
         "and no comparison of the displayed key numbers met one (H4.1 and H4.3 are met, but concern the hindsight tracks, footnote [g]; S-E5.5, the extension UKF variant's error higher than the FGO's, is met, but concerns an extension variant, not the thesis UKF, footnote [k]); any ordering visible in the numbers is descriptive (footnotes [a]–[k]). No estimator "
         "bounds position on a blank floor. The blank-floor row pools the standard-sensor flights (1A) with the forward-camera "
         "flights (1B: the camera calibration flights and both camera datasets).",
         ["experiment", "EKF3", "UKF", "FGO"], rowsT1, [30, 40, 40, 40],
         "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json, dsn_paired_test.json, phase4_{fwdc,fwdplainc}_evo.json, blank_behaviour.json, "
         "expT/t_aggregate.json, expO/O_*.json, expL/T_A_r*_t245.json, expH/s1far_r*.json, expH/h_comparative_2026-10-11.json, "
         "closed_loop_cl_*_half(_v2/_v3).json, raw_corridor_errors.json (the two raw rows only)",
         "§6.1, §6.2, §6.6, §15, §16.1–§16.3, §17.2; claims 1a, 1b, 2, 7, 10, 14, 17–19, 23, 25",
         notes=["Statuses (not orderings): '" + BLANK_ST + "' = the blank-floor status (ruling 2026-10-18; the blank floor is ruled 'not accuracy comparisons'); PASSED = met "
                "its pre-registered criteria with no comparison (Experiment 3, the FGO: H3.1–H3.4); N/A = not run (Experiment 3: the thesis EKF3 has no landmark states). Ordering labels (BEST / "
                "BEHIND / TIED) are printed only where a pre-registered decision rule was met (ruling 2026-10-17); none is printed here.",
                "Experiment 4's EKF3 jump: the 4.10 m figure is measured once the simulation's GNSS switching script moves EKF3 off its "
                "indoor source set, about 4.3 s after GNSS returns (the script waits for 40 consecutive GPS-status checks, 100 ms apart, "
                "about 4.0 s, plus about 0.3 s of simulated GPS latency). The UKF and FGO replays take every GNSS sample as it is recorded, "
                "with no gate and no reset on return, so they carry no equivalent delay.",
                "Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians "
                "descriptive [b]; with the camera heading, C1.a registered with no decision rule [c]; blank floor, no comparative test [d]; "
                "Experiment 2 live, H2.3 FAIL [e]; Experiment 4 live, H4.2 NOT MET [f] (H4.3, the FGO whole-flight batch "
                "within 1.5× of the smoothed UKF, PASSES [g], and H4.1, the batch below both filters' live tracks, PASSES (hindsight against "
                "live, not like with like); neither concerns the live key numbers); Experiment 3, one thesis estimator [h], the UKF cell an extension variant [k]; Experiment 5, H5.2 / H5.3 / "
                "H5.4a–b FAIL on the final-build hold sets, identical to the original-build verdicts, all drift bands PASS [i]; "
                "closed loop, no comparative test registered, every set at half real-time (RTF 0.5) passes 3/3 [j].",
                "Key numbers: 1A = cruise ATE, median of the 9 textured-floor flights of the standard-sensor dataset; 1B = the 6 textured-floor "
                "bags of the two camera datasets; Experiment 2 = horizontal RMSE with 1 tag; Experiment 4 = indoor RMSE; Experiment 3 = with "
                "loop closure (the UKF cell: extension E5, footnote [k]); Experiment 5 = mean hold error; 1C = at half real-time "
                "(RTF 0.5). " + RTFX + " "
                "† runaway magnitude (order only). No cell restates a WITHDRAWN claim.",
                "Ordering footnotes [a]–[j] (one per comparison; the letters in the experiment column): each footnote states the rule, "
                "the result and why no ordering label is printed. " + OCASE_KEY] + T1FN + [ob_ext("k"),
               "[l] " + RAW_NOTE + " 1A raw row: median only, over the same 9 flights (flights 1-9 of the standard-sensor dataset) as "
               "the aligned 1A median directly above; flight 10 (EKF3 only, IMU-gap rule) is excluded, matching the aligned cell. 1B "
               "raw row: range only, over the same 6 bags (the 6 textured-floor bags of the two camera datasets) as the aligned 1B "
               "with-heading cells directly above; EKF3 has no offline heading arm, same as the aligned row. See Table 4.4 "
               "(provisional) for the fitted-vs-raw companion table, median and range together."], order=10)

# =============================================================================================== TABLE T9 (new, raw-tables stage 2):
# Figure 4.1c (1A drift paths) companion table: fitted cruise ATE next to the raw world-frame error, from the user's raw
# re-scoring ruling (2026-11-02, task 3). "Table 4.4 (provisional)", same provisional status as the figure it companions
# (that figure's own caption says a companion table follows - that caption string belongs to the parallel figure-restyle/
# caption work and is not edited here; this is the table it refers to).
TNUM["T9"] = "Table 4.4 (provisional)"
check("T9 fitted medians EKF3/UKF/FGO, flights 1-9 (m) (same quantity as T1/T2's 1A median)", " / ".join(f2(med[e]) for e in EST),
      "4.10 / 5.13 / 4.46", "numbers.md §6.1 standing row (same check as T2's own)")
check("T9 fitted UKF range, flights 1-9 (m) (numbers.md D15 wording row)", rng([v for _, v in DSN["UKF"]]), "1.17–5.85", "numbers.md:232")
rowsT9 = []
for e in EST:
    v = [x for _, x in DSN[e]]
    rms = [raw_cell(t, e, "baseline")["rms_3d_m"] for t in _T1A_TR]
    end = [raw_cell(t, e, "baseline")["end_3d_m"] for t in _T1A_TR]
    rowsT9.append([e, "9", rd(med[e], 2), rng(v), rd(float(np.median(rms)), 2), rng(rms, 2), rd(float(np.median(end)), 2), rng(end, 2)])
save_tab("T9", "T9_1A_fitted_vs_raw", "Experiment 1A, standard-sensor dataset, textured floor, flights 1-9: fitted cruise ATE and raw world-frame error, per estimator",
         "Companion table to Figure 4.1d (the 9-flight drift paths): the registered fitted cruise ATE (evo -a, SE(3)-aligned) next to the raw "
         "world-frame error, nothing fitted (no rotation, translation or scale alignment), median and range over the same 9 flights, "
         "from the raw re-scoring ruling. The raw columns are DESCRIPTIVE and change no registered value or verdict.",
         ["estimator", "n (flights)", "fitted cruise ATE median, registered (m)", "fitted cruise ATE range, registered (m)",
          "raw world-frame error, nothing fitted, DESCRIPTIVE: RMS median (m)", "raw RMS range, nothing fitted, DESCRIPTIVE (m)",
          "raw end-of-cruise median, nothing fitted, DESCRIPTIVE (m)", "raw end-of-cruise range, nothing fitted, DESCRIPTIVE (m)"],
         rowsT9, [12, 14, 26, 24, 24, 24, 26, 26],
         "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); eval/results/raw_corridor_errors.json (raw columns)",
         "numbers.md:230 (fitted medians, D15 claim-wording row, CURRENT); numbers.md:232 (UKF fitted range, D15 wording row); EKF3 and FGO fitted "
         "ranges have no numbers.md line (confirmed by grep at generation time: numbers.md never prints them individually, only the "
         "three medians and the UKF range - RC-6 in raw_corridor_numbers.md's own coverage note states the same for the raw values), "
         "so they are cited to the json only",
         notes=["n = 9 flights (flights 1-9 of the standard-sensor dataset), the same population as the registered 1A median in "
                "Table 4.1, Table 7.1 and Table 7.5. Flight 10 (EKF3 only, under the IMU-gap rule) enters the confirmatory H1.1 test "
                "(flights 4-10, a different, paired population), not this table's 9-flight median.",
                "The fitted medians (EKF3 4.10, UKF 5.13, FGO 4.46 m) are printed, as separate tokens, at numbers.md:230 (the D15 "
                "claim-wording row, CURRENT); the UKF fitted range (1.17–5.85 m) at numbers.md:232 (D15 wording row). EKF3's "
                "(3.11–4.12 m) and FGO's (1.27–4.61 m) fitted ranges are not printed anywhere in numbers.md as an individual range; "
                "they are the same ranges Table 4.1 already prints in its 9-flight column, cross-checked there against the json "
                "(rerun_dsn_evo.json, dsn_extra_evo.json), reused here unchanged.",
                RAW_NOTE], order=15)

# =============================================================================================== FIG 2 heading stops drift (ONE panel)
from thesis_style import TEXT_WIDTH_IN
fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.0))
for yw in (10, -10):
    ax.axhspan(yw - 0.1, yw + 0.1, color=WALL, lw=0)
ax.axhline(9.58, color=WALL, lw=0.6, ls=":"); ax.axhline(-9.58, color=WALL, lw=0.6, ls=":")
# D118 (2026-11-03): wall and direct labels raised to the 9 pt floor (RS-1). LAYOUT FIX (2026-11-02): both "wall" labels get a white stroke halo so the glyphs stay legible where the dotted
# contact line or the grey wall band (WALL, similar value to INK2) runs behind/through them.
_WALL_HALO = [patheffects.withStroke(linewidth=2.5, foreground=SURF)]
ax.text(163, 10.05, "wall", ha="right", va="bottom", fontsize=9, color=INK2, path_effects=_WALL_HALO)
# va="top" at y=-10.05 let the glyphs (no descenders, so most of their height sits BELOW the anchor) run down past
# the bottom spine (ylim -10.6) and sit on top of it. Centred inside the wall band itself (-10.1..-9.9) instead,
# well clear of the spine.
ax.text(163, -10.0, "wall", ha="right", va="center", fontsize=9, color=INK2, path_effects=_WALL_HALO)
CT2 = {}; PATHD = {}; XB2 = {}
for est in EST:                                   # with heading first (solid, thin), so the dashed no-heading paths sit on top
    off, ons = HALF[est]
    for k, tr in enumerate(ons):
        gg = sim_path(tr); js = L(f"closed_loop_{tr}.json"); c0b, c1b = js["cruise_s"]
        ww = gg[:, 0] >= 20
        ax.plot(gg[ww, 2], gg[ww, 1], color=C[est], lw=1.0, ls="-", alpha=0.9, zorder=3)
        wc = (gg[:, 0] >= c0b) & (gg[:, 0] <= c1b); XB2.setdefault(est, []).append(float(np.abs(gg[wc, 1]).max()))
for est in EST:
    off, ons = HALF[est]
    g = sim_path(off); c0, ct = cl_meta(off); t = ct["t_rel_cruise_s"]; CT2[est] = t
    ww = (g[:, 0] >= 20) & (g[:, 0] <= c0 + t)
    ax.plot(g[ww, 2], g[ww, 1], color=C[est], lw=1.6, ls=(0, (5, 3)), zorder=4)
    PATHD[est] = float(math.hypot(g[ww, 2][-1] - ct["y"], g[ww, 1][-1] - ct["x"]))
    ax.plot(ct["y"], ct["x"], marker="X", ms=10, color=C[est], mec=INK, mew=1.0, zorder=6)
ax.set_xlim(-2, 165); ax.set_ylim(-10.6, 10.6); ax.set_yticks([-10, -5, 0, 5, 10])
ax.set_xlabel("North, along the corridor (m)"); ax.set_ylabel("East (m)")
ax.set_aspect(3.0, adjustable="box")
fig.canvas.draw()
axbb = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
x0_, x1_ = ax.get_xlim(); y0_, y1_ = ax.get_ylim()
STRETCH = (axbb.height / (y1_ - y0_)) / (axbb.width / (x1_ - x0_))
# RESTYLE (2026-11-02): per-estimator annotate() boxes and the two explanatory ax.text() notes (stretch factor, "9 flights
# overlap") removed - that content is in the caption (house rule: no explanatory notes/badges inside axes). Estimator names
# are kept as minimal direct labels at each wall-contact X (house rule: "minimal direct labels" are allowed).
LABXY = {"UKF": (4, -8.9, "left"), "FGO": (4, -6.6, "left"), "EKF3": (160, -3.2, "right")}
for est in EST:
    c0, ct = cl_meta(HALF[est][0]); lx, ly, ha_ = LABXY[est]
    ax.annotate(est, (ct["y"], ct["x"]), xytext=(lx, ly), fontsize=9, color=INK, ha=ha_, va="center",
                arrowprops=dict(arrowstyle="-", color=C[est], lw=0.9, shrinkA=2, shrinkB=6))
h = [Line2D([], [], color=C[e], lw=1.6, label=e) for e in EST] + \
    [Line2D([], [], color=INK2, lw=1.6, ls=(0, (5, 3)), label="no heading"),
     Line2D([], [], color=INK2, lw=1.0, ls="-", label="with heading"),
     Line2D([], [], color=INK2, ls="", marker="X", ms=8, mec=INK, label="wall contact")]
ax.legend(handles=h, loc="upper left", frameon=True, framealpha=0.95, edgecolor=GRID, ncol=2, fontsize=9.0)
cite("docs/thesis/numbers.md", 428, "\\|x\\| ≥ 9.58 m")       # side-effect check only; no longer placed in the caption (caption restyle, task 7)
cite("CLAUDE.md", 101, "5 m tall and 0.2 m thick at x = ±10 m")  # side-effect check only; no longer placed in the caption (caption restyle, task 7)
check("no-heading wall contact EKF3 / final UKF port / final FGO node (s)", " / ".join(f"+{rd(CT2[e], 1)}" for e in EST), "+242.1 / +165.9 / +166.7", "numbers.md §15 contact rows")
check("with heading, max cross-track per estimator EKF3 / final UKF port / final FGO node (m)", " / ".join(rng(B2h[e]) for e in EST),
      "0.24–0.33 / 0.22–0.25 / 0.04–0.32", "numbers.md §15 B2 row (EKF3 half) and re-flown rows")
dPB = max(abs(a - b) for e in EST for a, b in zip(XB2[e], B2h[e]))
check("plotted with-heading paths: max |x| in cruise vs scored max cross-track, all 9 flights, |Δ| <= 0.05 m", "ok" if dPB <= 0.05 else f"{rd(dPB, 3)}", "ok",
      "curve source (dataflash SIM) vs closed_loop_*.json B2")
check("plotted no-heading paths end at the scored contact point, all 3, |Δ| <= 0.5 m", "ok" if max(PATHD.values()) <= 0.5 else
      f"{rd(max(PATHD.values()), 2)}", "ok", "curve source (dataflash SIM, cut at cruise start + contact time) vs closed_loop_*.json contact")
_B2ALL_MAX = max(max(B2h[e]) for e in EST)
check("with heading, max |cross-track| over all 9 flights (m)", rd(_B2ALL_MAX, 2), "0.33", "this file's own B2h (EKF3 flight 1)")
print(f"F2 stretch {rd(STRETCH, 3)}; path-B2 max |Δ| {rd(dPB, 4)} m; path end vs contact {PATHD}")
ob_cl("a")   # D113 (2026-11-02): runs the underlying numeric cross-checks only; the obasis() text it returns is no
             # longer placed in this figure's caption (verdict wording and the pre-registered window now live only in
             # Table A.4, docs/thesis/tables/TA_verdicts.md).
save(fig, "F2", "F2_heading_stops_sideways_drift",
     "The camera heading stops the sideways drift: without it every estimator flies into the west wall",
     # CAPTION (second shortening, 2026-11-14): 1-3 plain sentences, what is plotted and how to read it only; the
     # removed sentences (contact times, the 0.33 m centreline figure) are kept verbatim in caption_detail.md.
     f"Each estimator's flown path through the textured corridor, top-down, with the lateral (East) axis stretched "
     f"{rd(STRETCH, 1)}x and walls at x = ±10 m; the dotted line marks the 9.58 m contact threshold. Colour shows the "
     f"flying estimator: dashed lines are one no-heading flight each, run to wall contact (marked by X); solid lines "
     f"are three with-heading flights per estimator, which overlap near the centreline at this scale. Heading-error "
     f"detail is in {TNUM['T4']} and {TNUM['F9']}.",
     "paths: dataflash SIM of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_r1_half_rp, "
     "cl_fgo_b_tex_r1–r3_half_rp; contact and B2: eval/results/closed_loop_<trial>.json",
     "§15 (contact rows, B2 row, re-flown B1/B2/B4 rows); numbers_refly.md §1-2; claim 14", foot=[],
     verdict="Verdicts: Table A.4, rows H1.8 n = 3 EKF3, half real-time (RTF 0.5); H1.8 n = 3 UKF, half real-time (final port, abb0357d); "
             "H1.8 n = 3 FGO, half real-time (corrected priors, 4c07374b/HEAD); H1.9 EKF3; H1.9 UKF (final UKF port, half real-time); "
             "H1.9 FGO (corrected priors, "
             "4c07374b/HEAD, half real-time).")

# =============================================================================================== FIG F9 heading error, same flights as F2
# (2026-10-17) Figure 4.2. The curves are READ from the stored flight records (dataflash and bag of each trial); no estimator output
# is recomputed. The heading error is the B3 computation of eval/closed_loop_score.py, COPIED below (importing the scorer would run it
# and rewrite the result files): the flying estimator's logged yaw (EKF3 XKF1 core 0, UKF XUKO, FGO XFGO) minus SIM yaw, wrapped to
# ±180°, on the SITL clock mapped to sim time by the scorer's own clock map (rebuilt here from /imu/time_ref and checked against the
# stored clock_map), then cut to the stored cruise window (with heading) or to the stored wall-contact time (without heading).
_TSF9 = get_typestore(Stores.ROS2_JAZZY)


def cl_clock(tr):
    """SITL -> sim clock of closed_loop_score.py (copied): lower envelope of receipt - time_usec in 5 s bins, linear fit."""
    import shutil, tempfile
    tref = []; bag = f"{TD}/{tr}/bag"; tmp = None
    if not os.path.exists(f"{bag}/bag_0.db3") and os.path.exists(f"{bag}/bag_0.db3.zst"):
        # PACKED bag (PACKED.txt): decompress a temporary copy to read it; the stored trial directory is not touched
        tmp = tempfile.mkdtemp(prefix="figs_thesis_bag_"); shutil.copy(f"{bag}/metadata.yaml", tmp)
        subprocess.run(["zstd", "-q", "-d", f"{bag}/bag_0.db3.zst", "-o", f"{tmp}/bag_0.db3"], check=True); bag = tmp
    try:
        with Reader(bag) as r:
            cs = [c for c in r.connections if c.topic == "/imu/time_ref"]
            for con, _, raw in r.messages(connections=cs):
                m = _TSF9.deserialize_cdr(raw, con.msgtype)
                tref.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    tref = np.array(sorted(tref)); sitl, dd = tref[:, 0], tref[:, 1] - tref[:, 0]; env = []
    for lo in np.arange(sitl.min(), sitl.max(), 5.0):
        q = (sitl >= lo) & (sitl < lo + 5)
        if q.sum() > 50:
            i = np.argmin(dd[q]); env.append((sitl[q][i], dd[q][i]))
    env = np.array(env); kk, cc = np.polyfit(env[:, 0], env[:, 1], 1)
    return kk, cc, float(1e3 * (kk * env[0, 0] + cc))


def cl_yaw_err(tr, est):
    """Signed heading error (deg, estimate - truth) of the flying estimator against time since the STORED cruise start (s)."""
    typ = {"EKF3": "XKF1", "UKF": "XUKO", "FGO": "XFGO"}[est]
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); sim, ek = [], []
    while True:
        r = m.recv_match(type=["SIM", typ])
        if r is None:
            break
        if r.get_type() == "SIM":
            sim.append((r.TimeUS / 1e6, r.Yaw))
        elif typ != "XKF1" or r.C == 0:
            ek.append((r.TimeUS / 1e6, r.Yaw))
    sim, ek = np.array(sim), np.array(ek)
    kk, cc, off = cl_clock(tr); js = L(f"closed_loop_{tr}.json")
    te = ek[:, 0] + kk * ek[:, 0] + cc
    simy = np.interp(ek[:, 0], sim[:, 0], np.unwrap(np.radians(sim[:, 1])))
    err = np.degrees((np.radians(ek[:, 1]) - simy + np.pi) % (2 * np.pi) - np.pi)
    dclk = max(abs(1e6 * kk - js["clock_map"]["rate_ppm"]) / 1e3, abs(off - js["clock_map"]["offset_ms_start"]))
    return te - js["cruise_s"][0], err, dclk


# SPLIT (2026-11-04, group A candidate-figure brief): panel (b) was a linear ±1° inset drawn on top of panel (a) - an overlapping
# plot under the no-overlap house rule. Now two STACKED panels sharing one time axis: (a) is the former main axis unchanged (both
# arms, to the wall contact); (b) is the former inset's content (the 9 with-heading flights only) as its own full-width panel on
# its own ±1° scale, below (a) rather than drawn on top of it. No pixel of panel (a) or of the with-heading curves/scale changes.
fig, (ax, axi) = plt.subplots(2, 1, figsize=(TEXT_WIDTH_IN, 5.6), gridspec_kw={"height_ratios": [1.5, 1.0]})
ax.axhspan(-2.0, 2.0, color=TRUTH, alpha=0.16, lw=0, zorder=1)
ax.axhline(0, color=INK2, lw=0.6, zorder=2)
DB3 = []; DCLK = []; INSF9 = []; ENDF9 = {}; WALLF9 = {}; B3F9 = {e: [] for e in EST}
for est in EST:                                   # with heading first (solid, thin), so the dashed no-heading lines sit on top
    for tr in HALF[est][1]:
        x, e, dc = cl_yaw_err(tr, est); js = L(f"closed_loop_{tr}.json"); c0b, c1b = js["cruise_s"]; b3 = js["B"]["B3"]
        w = (x >= 0) & (x <= c1b - c0b); a = np.abs(e[w])
        ax.plot(x[w], e[w], color=C[est], lw=1.0, ls="-", alpha=0.9, zorder=3); INSF9.append((est, x[w], e[w]))
        DB3.append(max(abs(float(np.percentile(a, 95)) - b3["p95_deg"]), abs(float(a.max()) - b3["max_deg"]))); DCLK.append(dc)
        B3F9[est].append(b3)
for est in EST:
    off = HALF[est][0]; x, e, dc = cl_yaw_err(off, est); DCLK.append(dc)
    c0, ct = cl_meta(off); t = ct["t_rel_cruise_s"]; w = (x >= 0) & (x <= t)
    ax.plot(x[w], e[w], color=C[est], lw=1.6, ls=(0, (5, 3)), zorder=4)
    ax.plot(x[w][-1], e[w][-1], marker="X", ms=10, color=C[est], mec=INK, mew=1.0, zorder=6)
    ENDF9[est] = (float(x[w][-1]), float(e[w][-1]), t); WALLF9[est] = L(f"closed_loop_{off}.json")["contact"]["wall"]
# RESTYLE (2026-11-02): per-estimator annotate() boxes and the grey-band explanatory note removed (house rule: no
# explanatory notes inside axes); wall-contact times are in the caption. Estimator names kept as minimal direct labels.
LABF9 = {"UKF": (8, 21.6, "left"), "FGO": (8, 19.4, "left"), "EKF3": (308, 10.0, "right")}
for est in EST:
    xe, ye, t = ENDF9[est]; lx, ly, ha_ = LABF9[est]
    ax.annotate(est, (xe, ye), xytext=(lx, ly), fontsize=9, color=INK, ha=ha_,
                va="center", arrowprops=dict(arrowstyle="-", color=C[est], lw=0.9, shrinkA=2, shrinkB=6))
P95F9 = max(b["p95_deg"] for e in EST for b in B3F9[e]); MAXF9 = max(b["max_deg"] for e in EST for b in B3F9[e])
ax.set_xlim(0, 310); ax.set_ylim(-17, 23)
# LAYOUT FIX (restyle, task 1): the panel label used to be an above-axes set_title(), which left the legend (then
# loc="lower left", inside the axes) the only place to put the panel marker. Moved to a minimal direct label inside
# the axes (bottom-left corner, clear of every line at this early time/low value) so the space above the axes is
# free for the legend (below).
ax.text(0.012, 0.025, "(a)", transform=ax.transAxes, ha="left", va="bottom", fontsize=9.5, color=INK)
plt.setp(ax.get_xticklabels(), visible=False)
# PANEL (b) (2026-11-04 split of the former inset): the 9 with-heading flights only, same units and time axis, its own ±1° scale -
# a separate full-width panel below (a), not drawn on top of it.
axi.axhspan(-2.0, 2.0, color=TRUTH, alpha=0.16, lw=0, zorder=1)
for est, xx, ee in INSF9:
    axi.plot(xx, ee, color=C[est], lw=1.0, ls="-", alpha=0.9, zorder=3)
axi.axhline(0, color=INK2, lw=0.6, zorder=2)
axi.set_xlim(0, 310); axi.set_ylim(-1.0, 1.0); axi.set_yticks([-1, -0.5, 0, 0.5, 1])
axi.text(0.012, 0.025, "(b)", transform=axi.transAxes, ha="left", va="bottom", fontsize=9.5, color=INK)
axi.set_ylabel("heading error (°)")
axi.set_xlabel("time since cruise start (s)")
ax.set_ylabel("heading error, estimate − truth (°)")
h = [Line2D([], [], color=C[e], lw=1.6, label=e) for e in EST] + \
    [Line2D([], [], color=INK2, lw=1.6, ls=(0, (5, 3)), label="no heading"),
     Line2D([], [], color=INK2, lw=1.0, ls="-", label="with heading"),
     Line2D([], [], color=INK2, ls="", marker="X", ms=8, mec=INK, label="wall contact"),
     Patch(color=TRUTH, alpha=0.3, label="heading-error bound (±2.0°)")]
# LAYOUT FIX (restyle, task 1): the legend used to sit inside the axes at "lower left", which covered the
# with-heading lines (they stay near zero for the whole flight) for roughly the first 120 s. Moved outside the
# axes, above panel (a) (an axes-anchored legend via bbox_to_anchor, which tight_layout() still reserves room
# for, unlike a figure-level fig.legend()); 4 columns so it stays inside the 160 mm text width at this font size.
ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0.0, 1.02, 1.0, 0.2), mode="expand", frameon=True,
          framealpha=0.95, edgecolor=GRID, ncol=4, fontsize=9.0, handlelength=1.4, labelspacing=0.3,
          borderpad=0.35, columnspacing=1.0)
check("no-heading wall contact EKF3 / final UKF port / final FGO node (s)", " / ".join(f"+{rd(ENDF9[e][2], 1)}" for e in EST), "+242.1 / +165.9 / +166.7", "numbers.md §15 contact rows")
# ruling 2026-10-17 (F9 caption): EKF3's no-heading contact fell AFTER its pre-registered window; the window and the outcome are
# checked by string equality against numbers.md:470, read at build time
F9W = f"[+{WIN['EKF3'][0]}, +{WIN['EKF3'][1]}]"
F9C = f"+{rd(ENDF9['EKF3'][2], 1)} ({'PASS' if WIN['EKF3'][0] <= ENDF9['EKF3'][2] <= WIN['EKF3'][1] else 'MISS'}"
check("EKF3 no-heading contact at half real-time against its pre-registered window", f"{F9C}), window {F9W}", "+242.1 (MISS), window [+155, +215]",
      "numbers.md:470 ('+186.2 (PASS, window [+155, +215]) / +242.1 (MISS, D21)')")
F9SRC = cite("docs/thesis/numbers.md", 470, f"window {F9W}"); cite("docs/thesis/numbers.md", 470, f"{F9C}, D21)")
check("with heading, all 9 flights: max of the heading error p95 / max of the heading error max (deg)", f"{rd(P95F9, 2)} / {rd(MAXF9, 2)}", "0.40 / 0.73",
      "numbers.md §15 re-flown B3 row (final UKF port r1 p95 0.382; final FGO node r3 max 0.682) and B3 row (EKF3 half 0.28–0.32 / 0.33–0.39); Table 4.3")
fb3 = lambda e: "; ".join(f"{rd(b['p95_deg'], 3)} / {rd(b['max_deg'], 3)} / {rd(b['mean_deg'], 3)}" for b in B3F9[e])
check("final UKF port heading error p95/max/mean per flight (deg)", fb3("UKF"), "0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250", "numbers.md §15 re-flown B3 row")
check("final FGO node heading error p95/max/mean per flight (deg)", fb3("FGO"), "0.398 / 0.459 / 0.197; 0.264 / 0.332 / 0.203; 0.300 / 0.726 / 0.182", "numbers.md §15 re-flown B3 row")
check("EKF3 half real-time heading error p95 / max range (deg)", f"{rng([b['p95_deg'] for b in B3F9['EKF3']])}/{rng([b['max_deg'] for b in B3F9['EKF3']])}", "0.28–0.32/0.33–0.39", "numbers.md §15 B3 row")
B3SRC = cite(M_, 4958, "95th percentile ≤ 1.0°, maximum ≤ 2.0°")
check("flights plotted: without / with heading, per estimator", " / ".join(f"{e} 1/{len(HALF[e][1])}" for e in EST), "EKF3 1/3 / UKF 1/3 / FGO 1/3", "numbers.md §15 (n = 1 per no-heading cell; 3 flights per heading set)")
check("plotted with-heading curves: |heading error| p95 and max in the stored cruise window vs stored B3, all 9 flights, |Δ| <= 0.001°",
      "ok" if max(DB3) <= 0.001 else rd(max(DB3), 4), "ok", "curve source (dataflash, read here) vs closed_loop_*.json B3")
check("clock map rebuilt from /imu/time_ref vs stored clock_map, all 12 flights (rate ppm/1000 and offset ms), |Δ| <= 1e-6",
      "ok" if max(DCLK) <= 1e-6 else f"{max(DCLK):.2e}", "ok", "closed_loop_*.json clock_map")
check("plotted no-heading curves end within 0.1 s of the stored contact time, all 3", "ok" if max(ENDF9[e][2] - ENDF9[e][0] for e in EST) <= 0.1 else
      rd(max(ENDF9[e][2] - ENDF9[e][0] for e in EST), 3), "ok", "curve source vs closed_loop_*.json contact.t_rel_cruise_s")
check("no-heading: drift side implied by the heading-error sign at contact (positive = estimate clockwise of truth, so the vehicle turns west) "
      "vs the stored contact wall", " / ".join("west" if ENDF9[e][1] > 0 else "east" for e in EST), " / ".join(WALLF9[e] for e in EST),
      "closed_loop_*.json contact.wall")
print(f"F9 curve vs B3 max |Δ| {max(DB3):.2e} deg; clock max |Δ| {max(DCLK):.2e}; ends {ENDF9}")
ob_cl("a")   # D113 (2026-11-02): side-effect checks only; see the F2 note above.
save(fig, "F9", "F9_heading_error_closed_loop",
     "Without a heading source the heading error grows until the wall; with the camera heading it stays near zero",
     # CAPTION (second shortening, 2026-11-14): 1-3 plain sentences; the contact-time event markers and the grey band
     # stay (both are read directly off the plot). Dropped: "textured corridor at half real time" and the p95/max
     # degree figures (a result, not a plotted reference); both kept verbatim in caption_detail.md.
     f"Heading error of the flying estimator (current yaw minus the simulator's true yaw) against time since cruise start, on the same "
     f"closed-loop flights as {TNUM['F2']}. Colour shows the flying estimator; dashed lines are one no-heading flight each, ending at "
     f"wall contact at +{rd(ENDF9['EKF3'][2], 1)} s (EKF3), +{rd(ENDF9['UKF'][2], 1)} s (UKF) and +{rd(ENDF9['FGO'][2], 1)} s (FGO); "
     f"solid lines are three with-heading flights per estimator. With the camera heading, in panel (a) all 9 flights' lines sit on zero "
     "against the grey ±2.0° heading-error band; panel (b) shows the same with-heading flights alone, on a linear ±1° scale.",
     "curves: dataflash XKF1 (core 0) / XUKO / XFGO and SIM, and bag /imu/time_ref (clock map), of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, "
     "cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_r1_half_rp, cl_fgo_b_tex_r1–r3_half_rp; cruise window, contact, B3 and "
     f"clock_map: eval/results/closed_loop_<trial>.json; heading-error bound: {B3SRC}",
     "§15 (contact rows, B3 row, re-flown B3 row); numbers_refly.md §1-2; claim 14",
     uncheck="the curves themselves are read from the flight records, not numbers.md rows; they are checked against the stored B3 "
             "p95/max, clock map and contact times (the 'ok' checks)", foot=[],
     verdict="Verdicts: Table A.4, rows H1.8 n = 3 EKF3, half real-time (RTF 0.5); H1.8 n = 3 UKF, half real-time (final port, abb0357d); "
             "H1.8 n = 3 FGO, half real-time (corrected priors, 4c07374b/HEAD); H1.9 EKF3; H1.9 UKF (final UKF port, half real-time); "
             "H1.9 FGO (corrected priors, 4c07374b/HEAD, half real-time).")

# =============================================================================================== TABLE T4 closed loop per estimator
B3h = {e: [L(f"closed_loop_{t}.json")["B"]["B3"] for t in HALF[e][1]] for e in EST}
B4h = {e: [L(f"closed_loop_{t}.json")["B"]["B4"]["max_abs_lat_speed_mps"] for t in HALF[e][1]] for e in EST}
fmtb3 = lambda e: "; ".join(f"{rd(b['p95_deg'], 3)} / {rd(b['max_deg'], 3)} / {rd(b['mean_deg'], 3)}" for b in B3h[e])
check("closed loop, half real-time, with heading: flights passing all five criteria (+ estimator validity)", " / ".join(f"{passh[e]}/3" for e in EST), "3/3 / 3/3 / 3/3", "numbers.md §15")
check("final UKF port max cross-track, flights 1/2/3 (m)", " / ".join(f"{rd(x, 3)}" for x in B2h["UKF"]), "0.231 / 0.253 / 0.219", "numbers.md §15 re-flown row")
check("final FGO node max cross-track, flights 1/2/3 (m)", " / ".join(f"{rd(x, 3)}" for x in B2h["FGO"]), "0.218 / 0.038 / 0.318", "numbers_refly.md §2 table (corrected priors)")
check("EKF3 half real-time max cross-track range (m)", rng(B2h["EKF3"]), "0.24–0.33", "numbers.md §15 B2 row")
check("final UKF port heading error p95/max/mean per flight (deg)", fmtb3("UKF"), "0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250", "numbers.md §15 re-flown B3 row")
check("final FGO node heading error p95/max/mean per flight (deg)", fmtb3("FGO"), "0.398 / 0.459 / 0.197; 0.264 / 0.332 / 0.203; 0.300 / 0.726 / 0.182", "numbers.md §15 re-flown B3 row")
check("EKF3 half real-time heading error p95 / max range (deg)", f"{rng([b['p95_deg'] for b in B3h['EKF3']])}/{rng([b['max_deg'] for b in B3h['EKF3']])}", "0.28–0.32/0.33–0.39", "numbers.md §15 B3 row")
check("no-heading wall contact EKF3 / final UKF port / final FGO node (s)", " / ".join(f"+{rd(CT2[e], 1)}" for e in EST), "+242.1 / +165.9 / +166.7", "numbers.md §15 contact rows")
check("final FGO node flight 3 max lateral speed (m/s)", f"{rd(B4h['FGO'][2], 3)}", "0.196", "numbers_refly.md §2 table (corrected priors)")
# D149(c): the corrected priors remove the former "closest call" (FGO v3 flight 3, 0.246 m/s against the 0.25 m/s
# bound) - the largest with-heading lateral speed over all 9 flights is now computed, not assumed, and is well
# clear of the bound.
_B4ALL = {e: B4h[e] for e in EST}; _B4MAXE = max(EST, key=lambda e: max(_B4ALL[e])); _B4MAXV = max(_B4ALL[_B4MAXE])
_B4MAXI = _B4ALL[_B4MAXE].index(_B4MAXV) + 1
check("largest with-heading lateral speed over all 9 flights (m/s), estimator, flight", f"{rd(_B4MAXV, 3)}, {_B4MAXE}, flight {_B4MAXI}",
      "0.196, FGO, flight 3", "this file's own B4h (corrected priors); bound 0.25 m/s")
#   2026-11-12 regeneration (D149(a), row-ID map #19-23): the no-heading column now reports the n = 3 "REPORTED k/3
#   (no set rule)" cell for each estimator at half real-time, never the word "MISS" inside the n = 3 row itself
#   (D149(a); EKF3 half is "1/3", with its spread, never "a miss"). Flight 1 of the EKF3/UKF cells is the original
#   single flight, kept "as recorded" with its own historical PASS/MISS word (D149(b)); the FGO half cell has no
#   such sibling (HALF["FGO"] comment above) and is reported as the corrected-priors re-fly only.
NH3 = {e: nh3(HALF_NH3[e], WIN[e]) for e in EST}
check("half real-time n = 3 no-heading cells: k/3 EKF3 / UKF / FGO", " / ".join(f"{NH3[e][0]}/{NH3[e][1]}" for e in EST), "1/3 / 3/3 / 2/3",
      "numbers_extras.md summary table (EKF3, UKF); numbers_refly.md lead item (FGO, PRIMARY k/3 = 2/3)")
check("half real-time n = 3 no-heading cells: per-flight contact (s) EKF3 / UKF / FGO", " | ".join(" / ".join(f"{rd(t, 1)}" for t in NH3[e][2]) for e in EST),
      "242.1 / 178.9 / 268.3 | 165.9 / 163.7 / 152.9 | 166.7 / 193.9 / 203.5",
      "numbers_extras.md per-estimator tables (EKF3, UKF); numbers_refly.md section 1 table (FGO)")
check("half real-time n = 3 no-heading cells: spread (min-max, s) EKF3 / UKF / FGO", " / ".join(NH3[e][3] for e in EST), "178.9–268.3 / 152.9–165.9 / 166.7–203.5",
      "numbers_extras.md summary table (EKF3 178.9-268.3, UKF 152.9-165.9); numbers_refly.md section 1 (FGO 166.7-203.5)")
rowsT4 = []
for e in EST:
    a, b = WIN[e]
    k, n, ts, spread = NH3[e]
    verdicts = ["PASS" if a <= t <= b else ("before window" if t < a else "after window") for t in ts]
    per_flight = " / ".join(f"+{rd(t, 1)} s ({v})" for t, v in zip(ts, verdicts))
    # task 8: the "flight 1 as recorded (n = 1; ...)" aside is removed - flight 1's own outcome is already carried by
    # `per_flight` above (every flight in the n = 3 cell, including flight 1, already gets its own window verdict
    # there); no value is lost by dropping the extra restatement.
    nh_cell = f"k/3 = {k}/{n} (window [+{a}, +{b}] s); flights {per_flight}; spread {spread} s"
    rowsT4.append([HBUILD[e] + (" (unmodified)" if e == "EKF3" else ""),
                   nh_cell,
                   f"{passh[e]}/3 PASS",
                   " / ".join(f"{rd(x, 2)}" for x in B2h[e]),
                   " / ".join(f"{rd(x['p95_deg'], 2)}" for x in B3h[e]),
                   " / ".join(f"{rd(x['max_deg'], 2)}" for x in B3h[e]),
                   " / ".join(f"{rd(x, 3)}" for x in B4h[e])])
save_tab("T4", "T4_closed_loop", "Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle",
         "Without a heading source, every flying estimator's n = 3 cell is reported as the count of flights meeting its own "
         "contact-window criterion (k/3, REPORTED, no set-level rule), with the per-flight contacts and the spread; with the camera "
         "heading every flight passes all five closed-loop criteria (mission completion and the cross-track, heading-error, "
         "lateral-speed and oscillation bounds) and the estimator-validity criterion, with the per-flight cross-track, heading-error "
         "and lateral-speed values shown (flights 1 / 2 / 3). This table is half real-time (RTF 0.5) only; the matching full "
         "real-time (RTF 1.0) no-heading n = 3 cells are a separate companion table (" + TNUM.get("T4F", "Table 4.3b") + "), kept out "
         "of this table so its own title stays accurate and no cross-speed comparison is drawn. No ordering between the "
         "estimators is claimed [a].",
         ["flying estimator (build)", "no heading: n = 3 cell (k/3, window, per-flight contact, spread)",
          "with heading: flights passing all five criteria", "max |cross-track| in cruise (m)",
          "heading error p95 (°)", "heading error max (°)", "max lateral speed (m/s)"],
         rowsT4, [26, 50, 16, 16, 14, 14, 16],
         "eval/results/closed_loop_cl_a_tex_half*.json, closed_loop_cl_bcpp_tex_r{1,2,3}_half.json, "
         "closed_loop_cl_ukf_a_tex_half_v2*.json, closed_loop_cl_ukf_b_tex_r{1,2,3}_half_v2.json, "
         "closed_loop_cl_fgo_a_tex_r{1,2,3}_half_rp.json, closed_loop_cl_fgo_b_tex_r{1,2,3}_half_rp.json",
         "§15 (contact rows, B1–B5 counts, B2, B3, B4 re-flown rows); numbers_extras.md; numbers_refly.md §1-2; claim 14",
         notes=["Contact windows are pre-registered per estimator (EKF3 [+155, +215] s, UKF [+146, +218] s, FGO [+145, +196] s). " + RTFX + " "
                "No comparison across real-time factors is claimed; closed-loop run-to-run variability over the n = 3 cells is "
                "descriptive (the spread), not a registered criterion. Bounds: heading-error bound max ≤ 2°; lateral-speed bound ≤ 0.25 m/s. "
                f"The corrected FGO priors remove the former near-miss on this bound: the largest with-heading lateral speed over all 9 "
                f"flights is now {rd(_B4MAXV, 3)} m/s ({_B4MAXE}, flight {_B4MAXI}), comfortably inside the bound. Heading error mean per flight: " +
                "; ".join(f"{e} " + " / ".join(f"{rd(x['mean_deg'], 2)}" for x in B3h[e]) for e in EST) + " °. The with-heading FGO flights used "
                "the corrected initial priors; every earlier build, including the original-priors final FGO node, is in "
                "Table A.1 (superseded).", OCASE_KEY, ob_cl("a", clean=True)], order=40)

# -------------------------------------------------------------------------------- TABLE T4F (new, companion to T4): full real-time
# (RTF 1.0) no-heading n = 3 cells (D149(a)/D21: kept OUT of T4 so T4's own "half real-time" title stays accurate and no
# cross-speed comparison is drawn between this table and T4). FGO has no full real-time no-heading n = 3 cell (none was
# pre-registered or flown at RTF 1.0 for the FGO; only the half real-time cell exists for the FGO, in T4 above).
TNUM["T4F"] = "Table 4.3b"
FNH3 = {e: nh3(FULL_NH3[e], WIN[e]) for e in ("EKF3", "UKF")}
check("full real-time n = 3 no-heading cells: k/3 EKF3 / UKF", " / ".join(f"{FNH3[e][0]}/{FNH3[e][1]}" for e in ("EKF3", "UKF")), "3/3 / 2/3",
      "numbers_extras.md summary table")
check("full real-time n = 3 no-heading cells: per-flight contact (s) EKF3 / UKF", " | ".join(" / ".join(f"{rd(t, 1)}" for t in FNH3[e][2]) for e in ("EKF3", "UKF")),
      "186.2 / 174.9 / 181.4 | 177.1 / 138.3 / 162.8", "numbers_extras.md per-estimator tables")
rowsT4F = []
for e in ("EKF3", "UKF"):
    a, b = WIN[e]; k, n, ts, spread = FNH3[e]
    verdicts = ["PASS" if a <= t <= b else ("before window" if t < a else "after window") for t in ts]
    per_flight = " / ".join(f"+{rd(t, 1)} s ({v})" for t, v in zip(ts, verdicts))
    # task 8: "flight 1 as recorded (n = 1; ...)" aside removed, same reasoning as rowsT4 above - `per_flight`
    # already carries flight 1's own window verdict.
    rowsT4F.append([HBUILD[e] + (" (unmodified)" if e == "EKF3" else ""), f"k/3 = {k}/{n} (window [+{a}, +{b}] s); flights {per_flight}; "
                     f"spread {spread} s"])
save_tab("T4F", "T4F_closed_loop_full_speed", "Closed loop at full real-time (RTF 1.0): the no-heading n = 3 cells, companion to " + TNUM["T4"],
         "No-heading n = 3 cells at full real-time (RTF 1.0), reported the same way as " + TNUM["T4"] + "'s half real-time cells "
         "(REPORTED k/3, no set-level rule), kept as a separate table so neither table's title implies a cross-speed comparison. "
         "The FGO has no full real-time no-heading cell: none was pre-registered or flown at this real-time factor.",
         ["flying estimator (build)", "no heading: n = 3 cell (k/3, window, per-flight contact, spread)"], rowsT4F, [26, 90],
         "eval/results/closed_loop_cl_a_tex.json, closed_loop_cl_a_tex_r{2,3}.json, closed_loop_cl_ukf_a_tex_v2_r{1,2,3}.json",
         "numbers_extras.md (EKF3, UKF full real-time tables); claim 14",
         notes=["EKF3's full real-time flight 1 is the same pre-existing single flight already reported elsewhere; the UKF full "
                "real-time port has no flight 1 of its own (an earlier, pre-jitter-correction build's full real-time flight, "
                "+163.0 s, is a different build and is superseded, Table A.1) - this cell is 3 new flights in total, as "
                "pre-registered.", OCASE_KEY], order=41)

# =============================================================================================== TABLE T2 accuracy without / with heading (was F3)
dec = L("phase5_analysis.json")["decomposition"]
hd = {a: [abs(dec[f"fwdc_tex_r{r}"][a]["xtrack_head_m"]) for r in (1, 2, 3)] for a in ("EKF3", "UKF_baseline", "FGO_baseline", "UKF_heading", "FGO_heading")}
nh = [x for a in ("EKF3", "UKF_baseline", "FGO_baseline") for x in hd[a]]
# Phase 5 decomposition: restated in numbers.md §6.3 (ruling 2026-10-16 on the open items, 6: phase5_analysis.json is the phase5-stage
# output of the FGO-only re-run, written 2026-10-10 14:08 after that run's phase4 stage and committed in 819caab).
check("|heading-driven cross-track|, textured-wall camera dataset, textured floor, flights 1/2/3, EKF3 | UKF | FGO without heading (m)",
      " | ".join(" / ".join(rd(x, 3) for x in hd[a]) for a in ("EKF3", "UKF_baseline", "FGO_baseline")),
      "36.276 / 29.508 / 36.070 | 45.980 / 3.171 / 46.120 | 41.002 / 8.630 / 42.121", "numbers.md §6.3 Phase 5 decomposition row")
check("|heading-driven cross-track|, textured-wall camera dataset, textured floor, flights 1/2/3, UKF | FGO with heading (m)",
      " | ".join(" / ".join(rd(x, 3) for x in hd[a]) for a in ("UKF_heading", "FGO_heading")),
      "0.065 / 0.064 / 0.068 | 0.065 / 0.063 / 0.067", "numbers.md §6.3 Phase 5 decomposition row")
check("standard-sensor dataset, textured floor, median of flights 1–9, EKF3 / UKF / FGO (m)", " / ".join(f2(med[e]) for e in EST), "4.10 / 5.13 / 4.46", "numbers.md §6.1 standing row")
check("standard-sensor dataset, textured floor, mean of flights 1–3, EKF3 / UKF / FGO (m)", " / ".join(f2(np.mean([v for i, v in DSN[e] if i <= 3])) for e in EST), "4.00 / 3.59 / 3.44", "numbers.md §6.1; claim 1a")
check("standard-sensor dataset, textured floor, UKF flights 1–9 range (m)", rng([v for _, v in DSN["UKF"]]), "1.17–5.85", "numbers.md §6.1 D15 wording row")
check("H1.1 confirmatory mean d, CI (m)", f"{rd(pt['mean_d_m'], 3)} [{rd(pt['t95_ci_m'][0], 3)}, {rd(pt['t95_ci_m'][1], 3)}]", "-0.021 [-0.989, 0.947]", "numbers.md §6.1")
check("no heading EKF3 textured-wall / plain-wall camera datasets, flights 1–3 (m)", " / ".join(f2(P4[b]["EKF3"]) for b in CAMB), "4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08", "numbers.md §6.4")
check("no heading FGO textured-wall / plain-wall camera datasets, flights 1–3 (m)", " / ".join(f2(P4[b]["FGO_baseline"]) for b in CAMB), "4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74", "numbers.md §6.4")
check("no heading UKF textured-wall / plain-wall camera datasets, flights 1–3 (m)", " / ".join(f2(P4[b]["UKF_baseline"]) for b in CAMB), "4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82", "numbers.md §6.4")
check("with heading UKF textured-wall / plain-wall camera datasets, flights 1–3 (m)", " / ".join(f2(P4[b]["UKF_heading"]) for b in CAMB), "0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25", "numbers.md §6.6")
check("with heading FGO textured-wall / plain-wall camera datasets, flights 1–3 (m)", " / ".join(f2(P4[b]["FGO_heading"]) for b in CAMB), "0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22", "numbers.md §6.6")
mism = 0
for ds, r in CAMB:
    a = L(f"phase4_{ds}_arms.json")[f"{ds}_tex_r{r}"]
    for arm in ("UKF_heading", "FGO_heading"):
        try:
            mism += abs(a[arm]["evo"]["ate_a_cruise"]["+0.00"] - P4[(ds, r)][arm]) > 1e-6
        except (KeyError, TypeError):
            pass
check("1B offline fusion: evo vs arms result files agreement (mismatches)", mism, 0, "phase4_*_evo.json vs phase4_*_arms.json")
BK = {"EKF3": "EKF3", "UKF": "UKF_baseline", "FGO": "FGO_baseline"}
cam = lambda e, ds, key: " / ".join(f2(P4[(ds, r)][key]) for r in (1, 2, 3))
_T2_FWDC_TR = [f"fwdc_tex_r{r}" for r in (1, 2, 3)]; _T2_FWDPC_TR = [f"fwdplainc_tex_r{r}" for r in (1, 2, 3)]
check("T2 raw-companion selection matches the aligned no-heading camera cells (fwdc/fwdplainc, baseline arm)",
      str(all(abs(stored_ate(f"{ds}_tex_r{r}", e, "baseline") - P4[(ds, r)][BK[e]]) < 1e-6
              for e in EST for ds, r in CAMB)),
      "True", "eval/results/raw_corridor_errors.json cells vs this file's own P4 (phase4_{fwdc,fwdplainc}_evo.json), baseline arm")
check("T2 raw-companion selection matches the aligned with-heading camera cells (fwdc/fwdplainc, UKF/FGO, heading arm)",
      str(all(abs(stored_ate(f"{ds}_tex_r{r}", e, "heading") - P4[(ds, r)][f"{e}_heading"]) < 1e-6
              for e in ("UKF", "FGO") for ds, r in CAMB)),
      "True", "eval/results/raw_corridor_errors.json cells vs this file's own P4 (phase4_{fwdc,fwdplainc}_evo.json), heading arm")
rowsT2 = []
for e in EST:
    v = [x for _, x in DSN[e]]
    rowsT2.append([e, f"{rd(med[e], 2)} ({rng(v)})", raw_med_rng(_T1A_TR, e, "baseline"),
                   cam(e, "fwdc", BK[e]), raw_list(_T2_FWDC_TR, e, "baseline"),
                   cam(e, "fwdplainc", BK[e]), raw_list(_T2_FWDPC_TR, e, "baseline"),
                   "no offline heading arm" if e == "EKF3" else cam(e, "fwdc", f"{e}_heading"),
                   "n/a" if e == "EKF3" else raw_list(_T2_FWDC_TR, e, "heading"),
                   "no offline heading arm" if e == "EKF3" else cam(e, "fwdplainc", f"{e}_heading") + " *",
                   "n/a" if e == "EKF3" else raw_list(_T2_FWDPC_TR, e, "heading"),
                   " / ".join(f"{rd(x, 1)}" for x in hd[BK[e]]) + "; " +
                   ("—" if e == "EKF3" else " / ".join(f"{rd_si(x, 3)}" for x in hd[f"{e}_heading"]))])      # m, 3 dp (units pass; was cm)
save_tab("T2", "T2_accuracy_heading", "Position error without and with the camera heading (textured floor)",
         "Without a heading source all three drift by metres and no ordering is claimed [a, b, d]; with the camera heading the UKF and the FGO "
         "stay within 0.25 m, the FGO lower on all 6 bags (C1.a) [c]. The heading-error decomposition of sideways drift attributes metres "
         "of the cross-track to each estimator's own heading error without the heading, and hundredths of a metre with it.",
         ["estimator", "no heading: standard-sensor dataset, 9 flights, median (range) (m)", "9 flights, raw, nothing fitted, DESCRIPTIVE (m) [e]",
          "no heading: textured walls, flights 1 / 2 / 3 (m)", "textured walls, raw, nothing fitted, DESCRIPTIVE (m)",
          "no heading: plain walls, flights 1 / 2 / 3 (m)", "plain walls, raw, nothing fitted, DESCRIPTIVE (m)",
          "with heading: textured walls, flights 1 / 2 / 3 (m)", "with heading, textured walls, raw, nothing fitted, DESCRIPTIVE (m)",
          "with heading: plain walls, flights 1 / 2 / 3 (m)", "with heading, plain walls, raw, nothing fitted, DESCRIPTIVE (m)",
          "textured walls, flights 1 / 2 / 3: heading-driven end-of-cruise cross-track, without; with heading (m)"],
         rowsT2, [10, 12, 16, 10, 16, 10, 16, 10, 14, 10, 14, 16],
         "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json; phase4_{fwdc,fwdplainc}_evo.json, "
         "cross-checked against phase4_*_arms.json; phase5_analysis.json (decomposition, xtrack_head_m); raw_corridor_errors.json (raw columns)",
         "§6.1, §6.3 (Phase 5 decomposition), §6.4, §6.6; claims 1a, 1b, 2, 5, 7",
         notes=["Metric: cruise ATE, which aligns away a constant yaw offset (so metres, not tens of metres). No ordering is claimed "
                f"without the heading: the pre-registered EKF3 − FGO test (H1.1) on flights 4–10 gives '{pt['verdict']}' (mean d {rd(pt['mean_d_m'], 3, sign=True)} m, "
                f"95% CI [{rd(pt['t95_ci_m'][0], 3, sign=True)}, {rd(pt['t95_ci_m'][1], 3, sign=True)}] m); the former 'EKF3 beats the FGO' is WITHDRAWN; the UKF "
                "medians are descriptive (9 flights). EKF3 has no offline heading arm at the UKF/FGO's own heading sigma (by ruling, it is the "
                "fixed no-heading baseline offline at that sigma); it flies with one closed loop (Table 4.3), and a separate Replay run gives "
                "it a DESCRIPTIVE offline heading arm at a shared 5° sigma, with matched 5° UKF/FGO arms (Table 4.1b; not the 0.148°/0.126° "
                "arms on this page). Camera columns: the textured-wall and plain-wall camera datasets, all on the textured floor.",
                "* Plain walls over the checkerboard floor: the heading FAILED the heading-measurement validation (H1.2) there, so no heading "
                "benefit is claimed (conditional on the initial yaw σ). C1.a (FGO lower than the UKF with heading) holds on 6/6, margin "
                "0.03–0.06 m on plain walls.",
                "Heading-error decomposition of sideways drift: |cross-track| at the end of cruise driven by the estimator's own heading "
                "error, from the analysis that the heading-fusion prediction (H1.3) is judged on, on the FGO-only re-run (the final estimator builds).",
                OCASE_KEY, ob_h11("a"), ob_ukf1a("b"), ob_c1a("c"),
                obasis("d", "no heading, the three estimators on the camera datasets (the two no-heading camera columns)", ATE_M,
                       f"{len(CAMB)} bags (textured floor, flights 1–3 of the textured-wall and of the plain-wall camera dataset; every "
                       "estimator on the same bags)", "none: no comparative test was pre-registered on these bags without heading "
                       "(the registered no-heading test is H1.1, on the standard-sensor dataset)",
                       "the per-bag values in the two no-heading camera columns", "iii"),
                "[e] " + RAW_NOTE + " Each raw column companions the aligned column directly to its left, over the exact same "
                "flights/bags/arm: the 9-flight column is median (range), matching its aligned column's own format; the per-flight columns "
                "list one raw value per flight, in the same 1/2/3 order. 'n/a' in a with-heading raw cell matches EKF3's 'no offline heading "
                "arm' (no estimator, not a withheld value)."],
         fs=7.6, order=20)

# Heading arm vs its own baseline at +60 s, 6 blank camera flights (ruling 2026-10-18, item 5): DESCRIPTIVE, no registered rule
_HB = {}
for _e in ("ukf", "fgo"):
    _m = []
    for _ds in ("fwdc", "fwdplainc"):
        for _i in (1, 2, 3):
            _t = bb[f"{_ds}_blank_r{_i}"]
            _h, _b = _t[_e + "_heading"]["+60s"], _t[_e + "_baseline"]["+60s"]
            _m.append(float(np.hypot(_b["along_m"], _b["cross_m"]) - np.hypot(_h["along_m"], _h["cross_m"])))
    _HB[_e] = _m
HB_UKF_N = f"{sum(m > 0 for m in _HB['ukf'])} of {len(_HB['ukf'])}"
HB_UKF_RNG = f"{rd(min(_HB['ukf']), 1)}–{rd(max(_HB['ukf']), 1)}"
HB_FGO_N = f"{sum(m > 0 for m in _HB['fgo'])} of {len(_HB['fgo'])}"
check("blank camera flights, UKF heading arm below its baseline at +60 s (new value; blank_behaviour.json)", HB_UKF_N, "6 of 6",
      "eval/results/blank_behaviour.json {fwdc,fwdplainc}_blank_r1-3 ukf_heading/ukf_baseline +60s (no numbers.md row)")
check("blank camera flights, UKF margin baseline − heading at +60 s (m) (new value)", HB_UKF_RNG, "0.6–17.5",
      "eval/results/blank_behaviour.json (no numbers.md row)")
check("blank camera flights, FGO heading arm below its baseline at +60 s (new value)", HB_FGO_N, "5 of 6",
      "eval/results/blank_behaviour.json (no numbers.md row)")

# =============================================================================================== TABLE T2B (new, companion to T2): EKF3 +
# heading via Replay, at a shared 5 deg sigma, with the matched UKF/FGO arms (1B, DESCRIPTIVE; D149(d), ekf3_heading_replay/
# preregistration.md sections 0/7). Every EKF3 + heading value carries the unconditional 5 deg angErr floor
# (AP_NavEKF3_Measurements.cpp:1118); the stored 0.148 deg (fwdc) / 0.126 deg (fwdplainc) UKF/FGO heading arms quoted on T2/numbers.md
# section 6.6 are NOT re-run here - these are a SEPARATE run, at a shared 5 deg sigma, so EKF3's forced floor is compared fairly.
TNUM["T2B"] = "Table 4.1b"
_EHJ = L("ekf3_heading_replay/scored.json")
_EHB = [f"{ds}_{c}_r{r}" for ds in ("fwdc", "fwdplainc") for c in ("tex", "trans", "blank") for r in (1, 2, 3)]
_EHARM = {"EKF3 (i)": "EKF3_baseline_arm_i", "EKF3 (ii)": "EKF3_heading_arm_ii", "UKF (iii)": "UKF_heading5_arm_iii", "FGO (iv)": "FGO_heading5_arm_iv"}
# advisor review: the dagger (runaway, numbers.md convention) marks UKF (iii)/FGO (iv) on transition/blank bags only -
# EKF3 (i)/(ii) stay FROZEN there (position invalid/stationary, a qualitatively different, well-defined failure mode,
# confirmed by numbers_ekf3_heading.md's own "evo cannot separate the two there - position is frozen" section), not
# diverging, so the dagger never attaches to the EKF3 columns.
DAGGER_ARMS = ("UKF (iii)", "FGO (iv)"); RUNAWAY_COND = {"trans", "blank"}


def eh_cell(bag, arm):
    v = _EHJ[bag][_EHARM[arm]]["evo_a_cruise"]
    if isinstance(v, float) and math.isnan(v):
        return "undefined (degenerate alignment)"
    dagger = " †" if (arm in DAGGER_ARMS and any(c in bag for c in RUNAWAY_COND)) else ""
    return f"{rd(v, 3)}{dagger}"


EH_EXP = {      # literally transcribed from docs/thesis/ekf3_heading_replay/numbers_ekf3_heading.md's own per-bag table (section
                # "Per-bag table: evo -a (cruise), m"), the thesis's own 5 deg-sigma run - cross-check #1
    "fwdc_tex_r1": ("4.093", "0.125", "0.126", "0.055"), "fwdc_tex_r2": ("3.603", "0.139", "0.133", "0.063"),
    "fwdc_tex_r3": ("4.076", "0.157", "0.136", "0.063"),
    "fwdc_trans_r1": ("41.482", "41.496", "130.882 †", "626.443 †"), "fwdc_trans_r2": ("41.489", "41.505", "134.401 †", "592.484 †"),
    "fwdc_trans_r3": ("41.466", "41.479", "132.965 †", "600.150 †"),
    "fwdc_blank_r1": ("43.573", "43.573", "10682.141 †", "7781.439 †"), "fwdc_blank_r2": ("43.543", "43.543", "11048.696 †", "7078.449 †"),
    "fwdc_blank_r3": ("43.612", "43.612", "9774.324 †", "12068.773 †"),
    "fwdplainc_tex_r1": ("4.075", "0.360", "0.355", "0.335"), "fwdplainc_tex_r2": ("4.057", "0.296", "0.291", "0.271"),
    "fwdplainc_tex_r3": ("4.082", "0.318", "0.309", "0.287"),
    "fwdplainc_trans_r1": ("41.479", "41.494", "127.139 †", "580.628 †"), "fwdplainc_trans_r2": ("41.440", "41.454", "127.001 †", "590.678 †"),
    "fwdplainc_trans_r3": ("41.441", "41.456", "126.454 †", "609.021 †"),
    "fwdplainc_blank_r1": ("43.453", "undefined (degenerate alignment)", "10065.715 †", "5659.032 †"),
    "fwdplainc_blank_r2": ("43.511", "undefined (degenerate alignment)", "9358.105 †", "8010.980 †"),
    "fwdplainc_blank_r3": ("43.540", "undefined (degenerate alignment)", "11108.363 †", "6742.646 †"),
}
rowsT2B = []
_eh_mismatch = []
for bag in _EHB:
    row = [bag] + [eh_cell(bag, a) for a in ("EKF3 (i)", "EKF3 (ii)", "UKF (iii)", "FGO (iv)")]
    rowsT2B.append(row)
    exp = EH_EXP[bag]
    got = tuple(row[1:])
    if got != exp:
        _eh_mismatch.append((bag, got, exp))
check("1B EKF3 + heading (T2B): every (bag, arm) cell == numbers_ekf3_heading.md's own per-bag table (18 bags x 4 arms, EXACT)",
      str(not _eh_mismatch), "True", "docs/thesis/ekf3_heading_replay/numbers_ekf3_heading.md 'Per-bag table: evo -a (cruise), m'; "
      "cross-check #1 against the document text")
# cross-check #2: the same 72 cells against the score JSON directly via rd(), independent of the document transcription above
_eh_mismatch2 = []
for bag in _EHB:
    for arm in ("EKF3 (i)", "EKF3 (ii)", "UKF (iii)", "FGO (iv)"):
        v = _EHJ[bag][_EHARM[arm]]["evo_a_cruise"]
        want_nan = arm == "EKF3 (ii)" and bag.startswith("fwdplainc_blank")
        if want_nan != (isinstance(v, float) and math.isnan(v)):
            _eh_mismatch2.append((bag, arm, v))
check("1B EKF3 + heading (T2B): every cell's nan/non-nan status matches the expected degenerate-alignment pattern (EXACT, via rd(json))",
      str(not _eh_mismatch2), "True", "eval/results/ekf3_heading_replay/scored.json (rd() of evo_a_cruise directly)")
# The textured-floor note's ranges (fwdc tex only; the fwdplainc tex heading failed validation, no benefit claimed), EXACT from the json
def _eh_rng(arm, n=2):
    vs = [_EHJ[f"fwdc_tex_r{r}"][_EHARM[arm]]["evo_a_cruise"] for r in (1, 2, 3)]
    lo, hi = rd(min(vs), n), rd(max(vs), n)
    return lo if lo == hi else f"{lo}-{hi}"
for _arm, _exp in (("EKF3 (ii)", "0.13-0.16"), ("EKF3 (i)", "3.6-4.1"), ("UKF (iii)", "0.13-0.14"), ("FGO (iv)", "0.05-0.06")):
    check(f"1B EKF3 + heading (T2B) note: fwdc tex {_arm} range (m)", _eh_rng(_arm, 1 if _arm == "EKF3 (i)" else 2), _exp,
          "eval/results/ekf3_heading_replay/scored.json (rd() of evo_a_cruise, fwdc_tex_r1-r3)")
save_tab("T2B", "T2B_ekf3_heading_replay", "Experiment 1B accuracy with the camera heading: EKF3 (via Replay) and matched 5° UKF/FGO arms (DESCRIPTIVE)",
         "A SEPARATE Replay run of EKF3 with the camera heading, at a shared 5° heading sigma so it can be set beside the UKF and FGO under "
         "the SAME sigma; the UKF/FGO columns here are NOT the stored 0.148°/0.126° arms quoted in " + TNUM["T2"] + "/numbers.md §6.6. DESCRIPTIVE "
         "(1B-H1/H2/H3; no verdict). EKF3's forced 5° angErr floor (AP_NavEKF3_Measurements.cpp:1118) applies to every EKF3 (ii) value "
         "unconditionally. † = the transition/blank runaway category (numbers.md convention; position is frozen or diverging once flow "
         "aiding is lost or never starts, so the metre-scale value is evidence of the category, not a precise measurement); it is never "
         "attached to EKF3 (i)/(ii), which stay frozen rather than diverging. fwdplainc_blank, EKF3 (ii): undefined (degenerate alignment) "
         "- the replayed EKF3 position is exactly stationary over the pinned cruise window, so evo's Umeyama alignment has no basis. "
         "fwdplainc_tex: the heading measurement FAILED Phase 3 validation on this floor/wall combination (0/3, numbers.md §6.6/8), so no "
         "heading benefit is claimed there even though EKF3 (ii)/(iii)/(iv) are computed and shown as recorded.",
         ["bag", "EKF3 (i) no heading", "EKF3 (ii) +heading (5° floor)", "UKF (iii) +heading (5°, matched)", "FGO (iv) +heading (5°, matched)"],
         rowsT2B, [20, 20, 24, 24, 24],
         "eval/results/ekf3_heading_replay/scored.json (evo_a_cruise, all 18 bags x 4 arms); docs/thesis/ekf3_heading_replay/numbers_ekf3_heading.md",
         "docs/thesis/ekf3_heading_replay/preregistration.md §0/§7; D149(d)",
         notes=["Gates (preregistration §0): round-trip check PASS; arm (i) reproduction 18/18 bags PASS; sign check (node convention) PASS; "
                "sigma-option byte-identity proof PASS (the default path is byte-identical for both estimators; the additive "
                "FWD_SIGMA_PSI_DEG option is what lets arms (iii)/(iv) run at 5°).",
                "Every EKF3 (ii) value carries the unconditional 5° angErr floor; this is a standing caveat on every number in that column, "
                "not a per-row exception.",
                "fwdc tex (textured walls, textured floor): EKF3 (ii) 0.13-0.16 m with the heading against 3.6-4.1 m without; on the same "
                "bags the matched 5° arms give UKF 0.13-0.14 m and FGO 0.05-0.06 m.",
                "fwdplainc tex (plain walls over the checkerboard floor): values shown for completeness only; the heading failed Phase 3 "
                "validation on this floor (H1.2), so no heading benefit is claimed there (restatement ruling 4).",
                "fwdc/fwdplainc trans, blank: all four arms are in the runaway category (position frozen once flow aiding is lost, or "
                "diverging once never gained); the metre-scale values are evidence of that category, from numbers_ekf3_heading.md's own "
                "per-bag table, not a precise ranking between arms.",
                "OQ-R3 (both pictures of EKF3 + heading, labelled): the D70 closed-loop panel (EKF3 flown with the camera heading in Experiment "
                "1C, raw from take-off, labelled 'closed loop, picture only, not scored' - a different trajectory, no score printed) is candidate "
                f"figure A20 (docs/thesis/figures_thesis/candidates/), not yet in the numbered set; this table is the scored offline arm, labelled "
                "'offline Replay, 5° floor'.", OCASE_KEY], order=21)

# =============================================================================================== TABLE T3 blank floor (was F4)
check("UKF +10/+30/+60 s ranges (m)", f"{rng(BLANK['UKF'][:, 0], 1)} / {rng(BLANK['UKF'][:, 1], 1)} / {rng(BLANK['UKF'][:, 2], 0)}", "0.7–1.8 / 15.3–26.8 / 30–100", "numbers.md §6.2 erratum E4")
check("FGO +10/+30/+60 s ranges (m)", f"{rng(BLANK['FGO'][:, 0], 1)} / {rng(BLANK['FGO'][:, 1], 1)} / {rng(BLANK['FGO'][:, 2], 0)}", "0.7–1.8 / 16.6–27.7 / 145–201", "numbers.md §6.2 erratum E5")
check("n flights UKF / FGO", f"{len(BLANK['UKF'])}/{len(BLANK['FGO'])}", "11/11", "numbers.md §6.2")
check("end of cruise UKF / FGO (m, nearest 1000 m; numbers.md km × 10^3, digits grouped) †", f"{BLK['UKF']} / {BLK['FGO']}", grp(si_str("29–40 / 23–41", 3)),
      "numbers.md §6.2 erratum E6 ('29–40 / 23–41' km)")
check("EKF3 invalid, s of cruise, all 14 blank", rng(EK_INV, 0), "301–310", "numbers.md §6.2")
nvalid = [v["valid_frames_in_cruise"] for k, v in bb.items() if "blank" in k]
check("valid airborne flow frames in cruise, all blank bags", f"max {max(nvalid)} over {len(nvalid)}", "max 0 over 14", "numbers.md §6.2 ('0', all 14 blank bags)")
rowsT3 = [[e, f"{len(BLANK[e])}", f"{rng(BLANK[e][:, 0], 1)} (median {rd(np.median(BLANK[e][:, 0]), 1)})",
           f"{rng(BLANK[e][:, 1], 1)} (median {rd(np.median(BLANK[e][:, 1]), 1)})", f"{rng(BLANK[e][:, 2], 0)} (median {rd(np.median(BLANK[e][:, 2]), 0)}) †",
           f"{BLK[e]} †"] for e in ("UKF", "FGO")]
rowsT3.insert(0, ["EKF3", f"{len(EK_INV)}", "invalid", "invalid", "invalid", f"invalid (for {rng(EK_INV, 0)} s of cruise)"])
save_tab("T3", "T3_blank_floor", "Blank floor: position error after the loss of flow aiding",
         "On a blank floor nothing bounds position [a]: the UKF and the FGO dead-reckon away to errors of tens of thousands of metres by the end of the cruise, and "
         "EKF3 flags its own position invalid, so it has no scored error. Behaviour under total loss of flow aiding, not accuracy. "
         "The blank-floor flights pool Experiment 1A (standard sensors) and 1B (forward camera).",
         ["estimator", "flights", "+10 s (m)", "+30 s (m)", "+60 s (m)", "end of cruise (m)"], rowsT3, [14, 10, 26, 26, 26, 30],
         "eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60 s and end; EKF3_invalid_period; valid_frames_in_cruise)",
         "§6.2; claim 10",
         notes=["Error magnitude = hypot(along, cross) at each time after the flow-loss point; UKF and FGO baselines (no heading), 11 "
                "flights each (blank floor, pooled across Experiments 1A and 1B: the standard-sensor dataset (1A), the camera calibration flights and both camera datasets (1B)). † runaway magnitudes: evidence of divergence with its order of "
                "magnitude, not bit-reproducible values.",
                f"EKF3 'invalid': on all {len(EK_INV)} blank flights there are {max(nvalid)} valid airborne flow frames in the cruise, so flow "
                f"aiding never starts; EKF3 flags its position invalid from take-off ({rng(EK_INV, 0)} s of cruise) and outputs exactly the "
                "origin, which is not scored (evaluation rule). This is a declared failure, not a small error.",
                "With the camera heading the yaw is held but position still is not (+60 s: UKF 21–71 m, FGO 130–172 m †; quoted from "
                "the results record (numbers.md erratum E8), not re-derived here). "
                f"Descriptive only (no registered rule uses it): the UKF heading arm is below its own baseline at +60 s on {HB_UKF_N} blank "
                f"camera flights (margin {HB_UKF_RNG} m), the FGO on {HB_FGO_N}. Three of the six are plain-wall flights over the blank "
                "floor, where the heading PASSED the heading-measurement validation (3/3, numbers.md §6.6); position is not bounded on any.", OCASE_KEY, ob_blank("a")], order=30)

# =============================================================================================== FIG 5 T
fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.4)); xc = np.arange(4); offs = dict(zip(TRK, np.linspace(-0.16, 0.16, 5)))
TT = {}
for n in TRK:
    est, kind = TSTY[n]
    per = np.array([[L(f"expT/T_{c}_r{r}.json")["tracks"][n]["horiz_err_m"]["rmse"] for r in (1, 2, 3)] for c in TCOND])     # m (SI, 2026-10-22)
    mn = np.array([agg["conditions"][c]["mean_rmse_m"][n] for c in TCOND]); TT[n] = mn
    x = xc + offs[n]
    ax.plot(x, mn, color=C[est], ls="-" if kind == "live" else "--", lw=1.4, marker=MK[est], ms=6,
            mfc=C[est] if kind == "live" else SURF, mec=C[est], mew=1.2, label=TSHORT[n] + " (mean of 3)", zorder=3)
    for j in range(4):
        ax.scatter([x[j]] * 3, per[j], s=10, marker=MK[est], color=C[est] if kind == "live" else SURF, edgecolor=C[est], lw=0.6, zorder=2, alpha=0.8)
gm = [agg["conditions"][c]["gap_length_median_s"] for c in TCOND]
ax.set_xticks(xc); ax.set_xticklabels([TLAB[c] for c in TCOND])  # median gaps are in the caption, not repeated on the ticks
ax.set_xlabel("tags available (condition A → D)"); ax.set_ylabel("horizontal RMSE over the 5 laps (m)")
ax.set_ylim(0, 0.155); ax.set_xlim(-0.45, 3.45)
ax.legend(loc="upper left", frameon=False, ncol=2, fontsize=9.0)
# RESTYLE (2026-11-02): the on-canvas hindsight-gain/PASS-FAIL fig.text() block is removed (house rule: no verdict text on
# any plot); the gain numbers are in the caption, the H2.1/H2.2 verdicts are in docs/thesis/tables/TA_verdicts.md.
h1 = agg["H-T1 (FGO live -> whole-flight batch)"]; p2 = agg["P-T2 (UKF live -> RTS)"]
exp10 = {"A": "0.039 0.037 0.020 0.014 0.010", "B": "0.055 0.061 0.026 0.031 0.015", "C": "0.074 0.076 0.054 0.039 0.019", "D": "0.096 0.131 0.083 0.109 0.028"}
for c in TCOND:
    mr = agg["conditions"][c]["mean_rmse_m"]
    check(f"Experiment 2 {TLAB[c]}: EKF3 / UKF / FGO live / smoothed UKF / FGO whole-flight batch (m)", " ".join(f"{rd(mr[k], 3)}" for k in TRK), exp10[c], "numbers.md §16.1 table")
check("Experiment 2 median gaps A–D (s)", " / ".join(f"{rd(g, 1)}" for g in gm), "4.3 / 10.1 / 22.0 / 46.3", "numbers.md §16.1 table header")
check("tags per lap in condition B", str(L("expT/T_B_r1.json")["gates"]["laps_ids"][0]), "[0, 1, 2, 3]", "T_B_r1.json gates (4 corner tags)")
check("H2.1 median gain A–D (m), rho, PASS", " / ".join(f"{rd(h1['median_gain_m'][c], 3)}" for c in TCOND) + f" {rd(h1['spearman_rho'], 2, sign=True)} {h1['PASS']}",
      "0.010 / 0.011 / 0.023 / 0.052 +0.30 True", "numbers.md §16.1")
check("H2.2 gain A–D (m), PASS", " / ".join(f"{rd(p2['median_gain_m'][c], 3, sign=True)}" for c in TCOND) + f" {p2['PASS']}", "+0.020 / +0.032 / +0.037 / +0.029 False", "numbers.md §16.1")
# RESTYLE (2026-11-02): the caption prints these same gains via rd_si() (SI-prefixed rounding), not the rd() the checks
# above use - assert the two formatters agree character-for-character at these values before the caption trusts rd_si().
check("H2.1 gain A–D: rd_si() caption string == rd() check string", ", ".join(rd_si(h1["median_gain_m"][c], 3) for c in TCOND),
      " / ".join(f"{rd(h1['median_gain_m'][c], 3)}" for c in TCOND).replace(" / ", ", "), "this file: rd_si() vs rd() on the same values")
check("H2.2 gain A–D: rd_si() caption string == rd() check string", ", ".join(rd_si(p2["median_gain_m"][c], 3, sign=True) for c in TCOND),
      " / ".join(f"{rd(p2['median_gain_m'][c], 3, sign=True)}" for c in TCOND).replace(" / ", ", "), "this file: rd_si() vs rd() on the same values")
P3S = " / ".join(rd(agg["P-T3 live ratio max/min"]["by_condition"][c], 2) for c in TCOND)   # was a hard-coded caption literal (D 1.58, double rounding)
check("H2.3 live max/min ratio A / B / C / D", P3S, "1.97 / 2.36 / 1.42 / 1.57", "numbers.md §16.1 P-T3")
# SI (2026-10-22): the former cm caption literals '1–3', '2–4', '8–13' are now computed from the stored means (2 dp in m) and checked
# against the literal shifted exactly by 10^-2
F5B = rng_si([agg["conditions"][c]["mean_rmse_m"]["FGO hindsight (whole-flight batch)"] for c in TCOND], 2)
F5A = rng_si([agg["conditions"]["A"]["mean_rmse_m"][f"{e} live"] for e in EST], 2)
F5D = rng_si([agg["conditions"]["D"]["mean_rmse_m"][f"{e} live"] for e in EST], 2)
check("F5 title: FGO whole-flight batch over A–D, 2 dp (m) = former caption literal '1–3' cm × 10^-2", F5B, si_str("1–3", -2), "eval/results/expT/t_aggregate.json; former F5 title")
check("F5 caption: live errors, condition A / condition D, 2 dp (m) = former literals '2–4' / '8–13' cm × 10^-2", f"{F5A} / {F5D}",
      f"{si_str('2–4', -2)} / {si_str('8–13', -2)}", "eval/results/expT/t_aggregate.json; former F5 caption")
ob_h23("a"); ob_h24("b")   # D113 (2026-11-02): side-effect checks only; see the F2 note above.
save(fig, "F5", "F5_T_tags_known_positions",
     f"Fewer tags, larger live errors; the FGO's hindsight batch stays at {F5B} m",
     # CAPTION (second shortening, 2026-11-14): 1-3 plain sentences; the live/hindsight error ranges (a result, not a
     # plotted reference) are dropped from the body (the title still states the hindsight-batch figure); the removed
     # sentence is kept verbatim in caption_detail.md.
     "Experiment 2 (known tags): horizontal RMSE in the world frame against which tags are available (condition A "
     "all 8, B the four corners, C two diagonal, D one tag). Colour and marker show the estimator; solid filled lines "
     "are live, dashed open lines are hindsight (the FGO whole-flight batch and the smoothed UKF); small marks show "
     "each of three flights, with a line through their mean. Live errors grow as tags thin out from condition A to "
     "D, while the FGO's hindsight batch stays flat across all four conditions.",
     "eval/results/expT/T_{A,B,C,D}_r{1,2,3}.json (tracks.*.horiz_err_m.rmse), expT/t_aggregate.json",
     "§16.1 table and bullets (H-T1, P-T2, P-T3, P-T4, condition D); claims 17, 18", foot=[],
     verdict="Verdicts: Table A.4, rows H2.1; H2.2; H2.3; H2.4.")

# =============================================================================================== FIG 6 O
ts = get_typestore(Stores.ROS2_JAZZY)
tr = "O_r1"; D = f"{TD}/{tr}"
o = L(f"expO/{tr}.json"); mk = o["markers_bag_s"]; toff, ton = mk["GNSS OFF"], mk["GNSS ON"]
G = np.loadtxt(f"{D}/room_ukf/ground_truth.tum")
TR = []
with Reader(f"{D}/bag") as rdr:
    cs = [c for c in rdr.connections if c.topic == "/imu/time_ref"]
    for con, _, raw in rdr.messages(connections=cs):
        m = ts.deserialize_cdr(raw, con.msgtype)
        TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
    tag_topics = [c.topic for c in rdr.connections if "tag" in c.topic]
TR = np.array(TR); sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
oE, oN = np.load(f"{D}/gnss.npz")["ekf3_origin_EN"]
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1 = []
while True:
    r = mv.recv_match(type=["XKF1"])
    if r is None: break
    if r.C == 0:
        t = r.TimeUS / 1e6; k1.append((t + kk * t + c0, r.PE + oE, r.PN + oN))
tracks = {"EKF3 live": np.array(k1)}
for n, p in (("UKF live", "room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", "room_ukf/ukf_rts.tum"), ("FGO live", "room_fgo/fgo_live.tum"),
             ("FGO hindsight (whole-flight batch)", "room_fgo/fgo_batch.tum")):
    tracks[n] = np.loadtxt(f"{D}/{p}")[:, :3]
fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.4))
ax.axvspan(0, ton - toff, color="#f2f2f2", zorder=0)
t_far = mk["OUTBACK BACK START"] - 3.0 - toff; t_back = mk["OUTBACK BACK START"] - toff; t_on = ton - toff
for tv in (0.0, t_far, t_back, t_on):
    ax.axvline(tv, color=TRUTH, lw=0.9, ls=":", zorder=1)
# RESTYLE (2026-11-02): route-event labels shortened to minimal direct labels (no multi-line descriptive clauses, no badge
# backgrounds); the full description of each event is in the caption.
EV = [(0.0, "GNSS OFF", "center"), (t_far, "far end", "right"), (t_back, "return", "left"), (t_on, "GNSS ON", "center")]
for tv, txt, al in EV:
    ax.text(tv + (-1.0 if al == "right" else 1.0 if al == "left" else 0.0), 4.62, txt, ha=al, va="top", fontsize=9.0, color=INK2)
ax.text(-38, 4.62, "outdoors", ha="left", va="top", fontsize=9.0, color=INK2)
ax.text(t_on + 38, 4.62, "outdoors", ha="right", va="top", fontsize=9.0, color=INK2)
ax.text(78, 2.9, "indoors", ha="center", va="bottom", fontsize=9.0, color=INK2)
rm_ind = {}
for n, Tk in tracks.items():
    est, kind = TSTY[n]; w = (Tk[:, 0] > toff - 40) & (Tk[:, 0] < ton + 30)
    e = np.hypot(Tk[w, 1] - np.interp(Tk[w, 0], G[:, 0], G[:, 1]), Tk[w, 2] - np.interp(Tk[w, 0], G[:, 0], G[:, 2]))
    ax.plot(Tk[w, 0] - toff, e, color=C[est], ls="-" if kind == "live" else "--", lw=1.2, label=TSHORT[n], zorder=3)
    wi = (Tk[:, 0] >= toff) & (Tk[:, 0] <= ton)
    ei = np.hypot(Tk[wi, 1] - np.interp(Tk[wi, 0], G[:, 0], G[:, 1]), Tk[wi, 2] - np.interp(Tk[wi, 0], G[:, 0], G[:, 2]))
    rm_ind[n] = float(np.sqrt(np.mean(ei ** 2)))
ax.set_xlabel("time from GNSS OFF at the entrance (s)"); ax.set_ylabel("horizontal error (m)")
ax.set_xlim(-40, t_on + 40); ax.set_ylim(0, 4.7)
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.80), fontsize=8.6, frameon=True, framealpha=0.95, edgecolor=GRID)
jump = o["tracks"]["EKF3 live"]["max_step_after_return_m"]
_k = tracks["EKF3 live"]; _w = (_k[:, 0] > ton) & (_k[:, 0] < ton + 30)
_ek = np.hypot(_k[_w, 1] - np.interp(_k[_w, 0], G[:, 0], G[:, 1]), _k[_w, 2] - np.interp(_k[_w, 0], G[:, 0], G[:, 2])); _i = int(np.argmax(_ek))
ax.annotate("EKF3 reset", (_k[_w, 0][_i] - toff + 0.5, _ek[_i] - 0.6), xytext=(t_on + 8, 2.4), fontsize=9.0,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7))
jumps = [L(f"expO/{t}.json")["tracks"]["EKF3 live"]["max_step_after_return_m"] for t in OFL]
check("Experiment 4 EKF3 reset jump (m), about 4.3 s after GNSS returns (the switching script's delay)", rng(jumps), "4.10–4.10", "numbers.md §16.2 ('4.10 m, every flight')")
check("Experiment 4 indoor duration (s)", f"{rd(t_on, 0)}", "123", "numbers.md §16.2 heading ('123 s, GNSS off')")
dO = max(abs(rm_ind[n] - o["tracks"][n]["indoor_rmse_m"]) for n in TRK)
check("flight 1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m", "ok" if dO <= 0.05 else f"{rd(dO, 3)}", "ok", "curve source vs scorer")
check("flight 1 bag has no tag topics", len(tag_topics), 0, "O design: no tags in outdoor_indoor.sdf")
ob_h41("a"); ob_h42("b"); ob_h43("c"); ob_ret("d")   # D113 (2026-11-02): side-effect checks only; see the F2 note above.
save(fig, "F6", "F6_O_outdoor_indoor",
     "Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return, about 4.3 s after GNSS returns (the switching script's delay); hindsight keeps the error near 1 m",
     # CAPTION (second shortening, 2026-11-14): 1-3 plain sentences; the route-event times stay (dotted-line markers
     # on the plot), and the switching-script qualifier on the 4.10 m / 4.3 s jump is KEPT, shortened but not
     # dropped (eval/freeze_audit.py check E). Dropped: "with no alignment" and the Table 5.1 pointer (moved
     # verbatim to caption_detail.md).
     "Experiment 4 (outdoor-indoor), flight 1: horizontal error against time in the world frame, as the vehicle "
     "flies outdoors, through a GNSS-denied indoor section, and back outdoors. Route events (dotted lines): GNSS "
     f"OFF at the entrance (0 s); the far end reached at about {rd(t_far, 0)} s; the return starting at "
     f"{rd(t_back, 0)} s; GNSS ON at {rd(t_on, 0)} s. Solid lines are live, dashed lines are hindsight; EKF3 resets "
     "to GNSS on return with a 4.10 m jump, about 4.3 s after GNSS returns once the simulation's GNSS switching "
     "script moves EKF3 off its indoor source set, with no such delay for the UKF or FGO.",
     "eval/results/expO/O_r1.json (markers_bag_s, max_step_after_return_m), O_r2.json, O_r3b.json; curves: O_r1 room_ukf/, room_fgo/ TUMs, "
     "dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref (clock map); design: METHODOLOGY 'Experiment O: pre-registration', "
     "sim/worlds/outdoor_indoor.sdf, fly_trial.py outback(), o_gnss.parm", "§16.2 table and bullets; claims 19–22",
     foot=[],
     verdict="Verdicts: Table A.4, rows H4.1; H4.2; H4.3.")

# =============================================================================================== TABLE T6 O indoor RMSE per flight
exO = {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89", "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}
for n in TRK:
    check(f"Experiment 4 indoor RMSE {TSHORT[n]} (m)", rng(OI[n]), exO[n], "numbers.md §16.2 table")
check("Experiment 4 H4.2 live max/min ratio; largest = EKF3 in every flight", f"{rng(ho2)}; {ho2_max_is_ekf3}", "1.71–1.84; True", "numbers.md §16.2 H-O2 bullet")
h1ok = all(OI["FGO hindsight (whole-flight batch)"][i] < min(OI["EKF3 live"][i], OI["UKF live"][i]) for i in range(3))
check("H4.1: FGO whole-flight batch below both filters' live tracks, flights", f"{sum(OI['FGO hindsight (whole-flight batch)'][i] < min(OI['EKF3 live'][i], OI['UKF live'][i]) for i in range(3))}/3",
      "3/3", "numbers.md §16.2 (H-O1 PASS 3/3)")
rowsT6 = [[TSHORT[n], "live" if TSTY[n][1] == "live" else "hindsight"] + [f"{rd(v, 2)}" for v in OI[n]] + [rng(OI[n])] for n in TRK]
rowsT6.append(["live max ÷ min (H4.2)", "—"] + [f"{rd(v, 2)}" for v in ho2] + [rng(ho2)])
save_tab("T6", "T6_O_indoor_rmse", "Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off)",
         "Indoors without GNSS the live errors are 0.8–1.4 m and not similar across estimators (EKF3 largest in every flight, H4.2 NOT MET) [a]; "
         "the two hindsight tracks agree at 0.58–0.60 m (H4.3 PASS) [b].",
         ["track", "kind", "flight 1 (m)", "flight 2 (m)", "flight 3 (m)", "range (m)"], rowsT6, [36, 14, 14, 14, 14, 18],
         "eval/results/expO/O_r1.json, O_r2.json, O_r3b.json (tracks.*.indoor_rmse_m)", "§16.2 table and bullets; claims 19–22",
         notes=["World frame, no alignment; same GNSS samples for every estimator; indoor sensor set: IMU, downward flow and downward LiDAR "
                "only. H4.1 PASS 3/3 (the FGO whole-flight batch is below both filters' live tracks) [c]; H4.3 PASS (the FGO whole-flight batch "
                "against the smoothed UKF within 1–5%, Table 5.2). The former 'FGO whole-flight batch ~2× better than the smoothed UKF' is "
                "WITHDRAWN (a noise-model artefact).", OCASE_KEY, ob_h42("a"), ob_h43("b"), ob_h41("c")], order=60)

# =============================================================================================== FIG 7 L
fig, axs = plt.subplots(1, 2, figsize=(TEXT_WIDTH_IN, 2.9), sharey=True)
# RESTYLE (2026-11-02): per-panel titles shortened to panel labels (a)/(b) only; "flights 1-3" and the lap5/lap1 ratios
# already in the caption, so the on-canvas text notes are removed rather than relocated.
for ax, mode, lab in ((axs[0], "lc", "(a) with loop closure"), (axs[1], "nolc", "(b) without loop closure")):
    for kind in ("live", "hindsight"):
        for r, tk in enumerate(LL[(mode, kind)]):
            v = np.array(tk["per_lap_rmse_m"])          # m (SI, 2026-10-22)
            ax.plot(range(1, 6), v, color=C["FGO"], ls="-" if kind == "live" else "--", marker=MK["FGO"], ms=5,
                    mfc=C["FGO"] if kind == "live" else SURF, mec=C["FGO"], lw=1.1,
                    label=f"{'live (fixed-lag)' if kind == 'live' else 'hindsight (full iSAM2 estimate)'}" if r == 0 else None)
    ax.set_title(lab, loc="left", fontsize=9.5)
    ax.set_xticks(range(1, 6)); ax.set_xlabel("lap of the 6 m square")
# RESTYLE (2026-11-02): one shared legend for the figure (house rule: anything repeated across panels appears once),
# not duplicated on both panels - both panels use the same one estimator/colour and the same live/hindsight styles.
axs[0].legend(loc="upper left", frameon=False, fontsize=9.0)
axs[0].set_ylabel("horizontal RMSE per lap (m)"); axs[0].set_ylim(0, None)
lc5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("lc", "live")]]
nl5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("nolc", "live")]]
check("Experiment 3 with loop closure, live overall (m)", rng([t["rmse_m"] for t in LL[("lc", "live")]], 3), "0.049–0.076", "numbers.md §16.3")
check("Experiment 3 with loop closure, hindsight overall (m)", rng([t["rmse_m"] for t in LL[("lc", "hindsight")]], 3), "0.017–0.027", "numbers.md §16.3")
check("Experiment 3 without loop closure, live overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "live")]], 3), "0.263–0.361", "numbers.md §16.3")
check("Experiment 3 without loop closure, hindsight overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "hindsight")]], 3), "0.221–0.266", "numbers.md §16.3")
check("Experiment 3 lap5/lap1, live with loop closure; live without", rng(lc5) + "; " + rng(nl5, 1), "0.16–0.43; 2.9–4.5", "numbers.md §16.3")
ext_checks()
# Title (user answer 3, 2026-11-02; decision D99): the no-loop-closure growth range is printed from the stored values (live lap 5 ÷ lap 1,
# rng(nl5, 1), the same string as the check row above and numbers.md:574 "2.9–4.5"), worded "2.9 to 4.5 times" as the user asked.
F7_GROW = rng(nl5, 1).replace("–", " to ")
assert F7_GROW == "2.9 to 4.5", f"F7 title range changed: {F7_GROW}"
ob_l("a")   # D113 (2026-11-02): side-effect checks only; see the F2 note above.
save(fig, "F7", "F7_L_loop_closure",
     f"Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows {F7_GROW} times over five laps",
     # CAPTION (second shortening, 2026-11-14): 1-3 plain sentences; the 3 clauses docs/thesis/tier1/check_claims_applied.py
     # asserts character-for-character (C1-C3: the no-landmark-states clause, the 3/3-in-each clause, the 0/9-runs
     # clause) are KEPT verbatim in sentence 3 below - this is why F7 stays longer than the other captions in this
     # stage (see caption_detail.md). Everything else removed (the lap-ratio numbers; the extension UKF-variant
     # drift-count detail) is kept verbatim in caption_detail.md.
     "Experiment 3 (loop closure): the keyframe FGO with AprilTags at unknown positions, each tag treated as a landmark, flights 1 to 3, "
     "horizontal RMSE per 6 m lap in the first tag's frame, on one shared linear axis; live is solid and filled, hindsight is dashed and "
     "open. Left: with loop closure the live error falls after lap 1; right: without re-identification it grows over five laps. "
     "The thesis's EKF3 and UKF, as configured, have no landmark states, so only the FGO shows loop closure here; in extension tests "
     f"with 4 tags and with 2 tags, the FGO's loop closure also bounded live drift in 3/3 flights in each, but with 1% wrong tag IDs its "
     f"live error with loop closure was below the no-loop-closure error on the same flight in {_h31['count']} runs "
     f"({_h31['divergence']['total']}).",
     "eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)", "§16.3 table and bullets; claims 23, 24", foot=[],
     verdict="Verdicts: Table A.4, rows V3; H3.1; H3.2; H3.3; H3.4; Extension E2 H-E2.1; Extension E3 H-E3.1; Extension E5 H-E5.1; Extension E5 S-E5.5.")

# =============================================================================================== TABLE T5 H tag-loss drift (was F8)
LOSS = ["5 s hover", "15 s hover", "30 s hover", "~7 s during a move"]
FLY = {"EKF3": (S1 + S1F, "EKF3", "EKF3 (EKF3-flying hold sets, near and far spawn, 6 flights)"),
       "UKF": (S2V, "UKF_port", "final UKF port (UKF-flying hold set, 3 flights)"),
       "FGO": (S3RP, "FGO_flying", "final FGO node (FGO-flying hold set, 3 flights; corrected priors)")}
BAND = {"EKF3": [50, 100, 200, 150], "FGO": [50, 100, 200, 150], "UKF": [100, 200, 400, 300]}
DR = {(est, li): drifts(FLY[est][0], FLY[est][1])[li] for est in EST for li in range(4)}
dd_ = drifts(S1, "EKF3"); check("EKF3-flying hold set (near spawn) drift 5/15/30/move (mm, effective)", " | ".join(rng(x, 0) for x in dd_), "13–27 | 6–25 | 3–11 | 7–31", "numbers.md §17 table")
for met, exp in (("eff", "15/12/3/4 | 17/12/26/20 | 11/17/11/13"), ("end", "15/10/3/7 | 19/12/26/23 | 12/17/11/16")):
    df_ = drifts(S1F, "EKF3", met)
    check(f"EKF3-flying hold set (far spawn) drift, flights 1 | 2 | 3, 5 s/15 s/30 s/move (mm, {'effective' if met == 'eff' else 'end of loss'})",
          " | ".join("/".join(rd(df_[li][i], 0) for li in range(4)) for i in range(3)), exp, "numbers.md §17 S1 far row (ruling 2026-10-16, open items 7)")
for nm, trs, key, exp in (("UKF-flying hold set (final build)", S2V, "UKF_port", "5/7/8 | 19/7/26 | 6/10/10 | 26/4/5"),
                          ("FGO-flying hold set (final build, corrected priors)", S3RP, "FGO_flying", "20/20/19 | 22/7/6 | 9/12/28 | 3/24/1")):
    de = drifts(trs, key, "end")
    check(f"{nm}: end-of-loss drift, flights 1/2/3 (mm)", " | ".join("/".join(f"{rd(x, 0)}" for x in row) for row in de), exp, "numbers.md §17.1 table")
dmax = max(abs(a - b) for trs, key in ((S1 + S1F, "EKF3"), (S2V, "UKF_port"), (S3RP, "FGO_flying"))
           for ra, rb in zip(drifts(trs, key), drifts(trs, key, "end")) for a, b in zip(ra, rb))
check("effective vs end-of-loss drift, max |Δ| at printed (mm) precision (FGO: corrected-priors hold set)", f"≤ {rd(dmax, 0)} mm", "≤ 5 mm",
      f"numbers.md §17.1 ('differ by ≤ 5 mm'); unrounded {rd(dmax, 1)} mm")
inband = all(v <= BAND[e][li] for (e, li), d in DR.items() for v in d)
check("every drift inside its pre-registered drift band (H5.5)", inband, True, "numbers.md §17, §17.1 (every band PASSES)")
LK = {e: [bool(lo[FLY[e][1]]["lockout"]) for t in FLY[e][0] for lo in HJ(t)["losses"]] for e in EST}
check("lockouts in any loss (flying estimators)", sum(sum(v) for v in LK.values()), 0, "numbers.md §17 (P-H7 PASS)")
rowsT5 = [[f"tag lost: {LOSS[li]}"] + [f"{rd(max(DR[(e, li)]), 0)} / {BAND[e][li]} (range {rng(DR[(e, li)], 0)}; {len(DR[(e, li)])} losses, one per flight)" for e in EST]
          for li in range(4)]
rowsT5.append(["lockouts (losses with a lockout / losses)"] + [f"{sum(LK[e])} / {len(LK[e])}" for e in EST])
rowsT5.append(["drift band (H5.5)"] + ["every loss inside its band" if all(v <= BAND[e][li] for li in range(4) for v in DR[(e, li)]) else "band FAIL"
                                       for e in EST])
save_tab("T5", "T5_H_tag_loss_drift", "Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators",
         "Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered "
         "band, and none locks out; each cell gives the maximum drift / its band in mm, with the range over the losses. The comparative "
         "hypotheses (H5.2, H5.3, H5.4a–b) FAIL on these final-build sets, the same category of verdict as the superseded original-prior "
         "sets (Table A.2), so no ordering is claimed [a]. " + PRIORS,
         ["tag-loss condition", FLY["EKF3"][2] + ": max / band (mm)", FLY["UKF"][2] + ": max / band (mm)", FLY["FGO"][2] + ": max / band (mm)"],
         rowsT5, [28, 40, 40, 40],
         "eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s3rp_r*.json (losses[*].<est>.effective.drift_m, drift_end_m, lockout)",
         "§17 (S1 table, S1 far row, P-H5, P-H7), §17.1 (S2v2); refly_priors/numbers_refly.md §4 (S3rp); claims 25, 26",
         notes=["Drift = the EFFECTIVE metric (last fix → first returning fix); the end-of-loss metric differs by ≤ 5 mm "
                f"(unrounded {rd(dmax, 1)} mm). Pre-registered drift bands (H5.5): EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm, UKF ≤ 100 / 200 / 400 / "
                "300 mm. H5.5 (drift band) and H5.7 (no lockout) PASS. The comparative hypotheses (H5.2, H5.3, H5.4a–b) are reported on these "
                "final-build sets (primary); "
                "their verdicts are identical to the original-build verdicts (all FAIL). Each estimator flew its own flights: pairing by run "
                "index, not trajectory.",
                "EKF3 = the EKF3-flying hold set at the near spawn (3 flights) and at the far spawn (3 flights). UKF = the final UKF port "
                "(jitter-corrected); FGO = the final FGO node (C++, corrected priors, 4c07374b/HEAD; the original-priors hold set, "
                "s3v2_r*, is superseded, Table A.2).",
                "The drift bands (H5.5) and the lockout criterion (H5.7) are per-estimator criteria, not comparisons (the UKF's "
                "bands are twice the others'); their n is the number of tag losses (one of each kind per flight).",
                OCASE_KEY, ob_h5("a")],
         order=50)

# =============================================================================================== APPENDIX tables
# closed-loop criteria B1-B5 by their thesis names (thesis_vocabulary.md terms 23-27)
BNAME = {"B1": "mission completion", "B2": "cross-track bound", "B3": "heading-error bound", "B4": "lateral-speed bound",
         "B5": "oscillation bound"}


def setb(trs):
    B = [L(f"closed_loop_{t}.json")["B"] for t in trs]
    r_ = lambda f: f"{rd(min(f(b) for b in B), 2)}–{rd(max(f(b) for b in B), 2)}"
    js = [L(f"closed_loop_{t}.json") for t in trs]
    fails = [f"flight {i + 1} {BNAME[k]}" for i, b in enumerate(B) for k in ("B1", "B2", "B3", "B4", "B5") if not b[k]["pass"]]
    n = sum(b["pass"] and j.get("S2", {}).get("pass", True) for b, j in zip(B, js))
    return (f"{n}/3 " + ("PASS" if n == 3 else "FAIL") + (f" ({', '.join(fails)})" if fails else ""),
            r_(lambda b: b["B2"]["max_abs_x_cruise_m"]) + " m", r_(lambda b: b["B3"]["p95_deg"]) + "° / " + r_(lambda b: b["B3"]["max_deg"]) + "°",
            r_(lambda b: b["B4"]["max_abs_lat_speed_mps"]) + " m/s")


def seta(tr, win):
    if tr is None:
        return "not flown"
    c0, ct = cl_meta(tr); t_ = ct["t_rel_cruise_s"]
    return f"+{rd(t_, 1)} s, {'PASS' if win[0] <= t_ <= win[1] else 'MISS'} [+{win[0]}, +{win[1]}]"


rowsA = [
    ("EKF3, real time (RTF 1.0)", "unmodified; Python heading node", "—", *setb([f"cl_b_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, real time (RTF 1.0)", "unmodified; C++ heading node", seta("cl_a_tex", WIN["EKF3"]), *setb([f"cl_bcpp_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, half real-time (RTF 0.5)", "unmodified; C++ heading node", seta("cl_a_tex_half", WIN["EKF3"]), *setb([f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, real time (RTF 1.0)", "superseded: earlier build (pre-jitter fix)", seta("cl_ukf_a_tex", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}" for i in (1, 2, 3)])),
    ("UKF, half real-time (RTF 0.5)", "superseded: earlier build (pre-jitter fix)", seta("cl_ukf_a_tex_half", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, half real-time (RTF 0.5)", "final UKF port (jitter-corrected)", seta("cl_ukf_a_tex_half_v2", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "superseded: earlier build (original FGO, old noise model), hard gate", seta("cl_fgo_a_tex_half", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "superseded: earlier build (original FGO), robust heading weight", "not flown", *setb([f"cl_fgo_b_robust_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "superseded: earlier build, ablation build: noise fix only", seta("cl_fgo_a_tex_half_v2", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "superseded: original priors; noise fix + gated yaw cap", seta("cl_fgo_a_tex_half_v3", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)])),
]
# 2026-11-12 regeneration (D149(b)/(c)): the corrected-priors FGO re-fly, CURRENT. Appended (not inserted) so every
# existing rowsA[n]/ABL index above keeps pointing at the same row. No-heading column shows flight 1 of the new n = 3
# cell only (the full k/3 spread, 2/3, is reported in Table 4.3/4.3's own no-heading column and TA_verdicts.md).
rowsA.append(("FGO, half real-time (RTF 0.5)", "CURRENT: corrected priors (4c07374b/HEAD), noise fix + gated yaw cap",
              seta("cl_fgo_a_tex_r1_half_rp", WIN["FGO"]) + " (flight 1 of 3; k/3 = 2/3, Table 4.3)",
              *setb([f"cl_fgo_b_tex_r{i}_half_rp" for i in (1, 2, 3)])))
check("EKF3 half real-time contact MISS", rowsA[2][2].split(",")[1].strip().split()[0], "MISS", "numbers.md §15 (D21)")
check("UKF earlier build, half real-time, with-heading set", rowsA[4][3].split()[0], "2/3", "numbers.md §15 (r3 B4 0.296 m/s)")
check("final UKF port / final FGO node with-heading sets", f"{rowsA[5][3]} / {rowsA[9][3]}", "3/3 PASS / 3/3 PASS", "numbers.md §15 (re-flown sets)")
check("FGO ablation build with-heading set", rowsA[8][3], "3/3 PASS", "numbers.md §15")
check("FGO earlier build, hard-gated / robust with-heading sets", f"{rowsA[6][3]} / {rowsA[7][3]}", "3/3 PASS / 3/3 PASS", "numbers.md §15 (D28)")
check("contacts UKF earlier build (half real-time) / final UKF port / FGO earlier build / FGO ablation build / final FGO node (s)",
      " / ".join(r[2].split(",")[0].replace(" s", "") for r in (rowsA[4], rowsA[5], rowsA[6], rowsA[8], rowsA[9])), "+198.0 / +165.9 / +165.8 / +169.6 / +169.9", "numbers.md §15 contact rows")
check("real-time no-heading contact: EKF3; UKF earlier build", f"{rowsA[1][2].split(',')[0].replace(' s', '')}; {rowsA[3][2].split(',')[0].replace(' s', '')}", "+186.2; +163.0", "numbers.md §15 rows 1–2")
check("UKF earlier build (half real-time) / FGO earlier build heading error p95/max ranges", f"{rowsA[4][5]}; {rowsA[6][5]}", "0.18–0.21° / 0.28–1.32°; 0.26–0.38° / 1.28–1.88°", "numbers.md §15 B3 row (original builds)")
A1FN = [OCASE_KEY,
        obasis("a", "every flown build: earlier, ablation and final builds, and real time against half real-time",
               "as for Table 4.3: wall-contact time against the contact window (s) without heading; pass/fail of the five closed-loop "
               "criteria with max |cross-track| (m), yaw error p95 / max (°) and max lateral speed (m/s) with heading",
               "1 flight per build without heading and 3 flights per build with heading (every set its own flights, unpaired)",
               "per-set criteria only (H1.8, H1.9); no comparison between builds, between estimators or between real-time factors "
               f"was pre-registered (the comparison across the with-heading sets is descriptive, {cite(M_, 9355, 'no ordering claim')}; "
               "the final builds' basis is footnote [a] of Table 4.3)", "pass/fail per set, as tabulated", "iii")]
APP_A = ITEMS_A = None
CHK_A = CHK; CHK = []


def hsum(trs, key):
    """Units pass (2026-10-23): hold error at 1 dp and drift at 0 dp in mm (the Experiment 5 hold quantities are in mm in every table
    and figure; docs/thesis/units.md), converted from the stored metre values by an exact decimal shift."""
    hm = [w["mean_m"] for t in trs for w in HJ(t)["hold_windows_vehicle"]]
    dr = [lo[key]["effective"]["drift_m"] for t in trs for lo in HJ(t)["losses"]]
    lk = sum(lo[key]["lockout"] for t in trs for lo in HJ(t)["losses"])
    return f"{rng_si(hm, 1, 3)} mm", f"{rng_si(dr, 0, 3)} mm", f"{lk}", "every band PASS" if all(
        mm_(lo[key]["effective"]["drift_m"]) <= BAND[{"EKF3": "EKF3", "UKF_port": "UKF", "FGO_flying": "FGO"}[key]][i]
        for t in trs for i, lo in enumerate(HJ(t)["losses"])) else "band FAIL"


rowsH = [("EKF3-flying hold set (near spawn)", "unmodified EKF3", *hsum(S1, "EKF3")),
         ("EKF3-flying hold set (far spawn, re-fly)", "unmodified EKF3", *hsum(S1F, "EKF3")),
         ("UKF-flying hold set (earlier build)", "superseded: earlier build (pre-jitter fix)", *hsum(S2O, "UKF_port")),
         ("UKF-flying hold set (final build)", "final UKF port (jitter-corrected)", *hsum(S2V, "UKF_port")),
         ("FGO-flying hold set (ablation build)", "superseded: earlier build; ablation build: noise fix only; original priors", *hsum(S3O, "FGO_flying")),
         ("FGO-flying hold set (final build)", "superseded: original priors; final FGO node f642cd37", *hsum(S3V, "FGO_flying")),
         ("FGO-flying hold set (final build, corrected priors)", "CURRENT: corrected priors (4c07374b/HEAD)", *hsum(S3RP, "FGO_flying"))]
check("hold window means, UKF-flying earlier / final build; FGO-flying ablation / final build, original priors (mm)", " ; ".join(r[2].replace(" mm", "") for r in rowsH[2:6]),
      "4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0", "numbers.md §17.1 table")
check("hold window means, FGO-flying final build, corrected priors (mm)", rowsH[6][2].replace(" mm", ""), "7.1–8.7", "numbers_refly.md §4.1 table")
check("lockouts, EKF3-flying near / far spawn; UKF-flying final; FGO-flying final (corrected priors)", " / ".join(rowsH[i][4] for i in (0, 1, 3, 6)), "0 / 0 / 0 / 0", "numbers.md §17, §17.1; numbers_refly.md §4.2 (no lockout)")

SAFE = [  # (test, file, build, notes)
    ("UKF forced-invalid", "safety_ukf_a", "earlier UKF build; first run", "first run"),
    ("UKF forced-invalid", "safety_ukf_a_rerun", "earlier UKF build; re-run", ""),
    ("UKF forced-invalid", "safety_ukf_a_v2", "final UKF port (jitter-corrected)", "earlier final-build run"),
    ("UKF forced-invalid", "safety_ukf_a_v3", "final UKF port abb0357d (re-test)", "FINAL"),
    ("UKF node-kill", "safety_ukf_b", "earlier UKF build", ""),
    ("UKF node-kill", "safety_ukf_b_v2", "final UKF port (jitter-corrected)", "earlier final-build run; relay drain"),
    ("UKF node-kill", "safety_ukf_b_v3", "final UKF port abb0357d (re-test)", "FINAL; relay drain"),
    ("FGO forced-invalid", "safety_fgo_a", "earlier FGO build; old hold", ""),
    ("FGO forced-invalid", "safety_fgo_a_v2", "ablation build: noise fix only; original priors", ""),
    ("FGO forced-invalid", "safety_fgo_a_v3", "final FGO node f642cd37; original priors", "earlier final-build run"),
    ("FGO forced-invalid", "safety_fgo_a_v4", "corrected-priors node 4c07374b", "FINAL; safe landing 1.45 m near its 1.5 m bound"),
    ("FGO node-kill", "safety_fgo_b", "earlier FGO build; old hold", "room-box breach in the landing"),
    ("FGO node-kill", "safety_fgo_b2", "earlier FGO build; 2 m-clearance hold", ""),
    ("FGO node-kill", "safety_fgo_b_v2", "ablation build: noise fix only; original priors", ""),
    ("FGO node-kill", "safety_fgo_b_v3", "final FGO node f642cd37; original priors", "earlier final-build run"),
    ("FGO node-kill", "safety_fgo_b_v4", "corrected-priors node 4c07374b", "FINAL"),
    ("EKF3 reference kill", "safety_ekf3_ref", "unmodified EKF3", "drift 1.40 m against a ≤ 0.5 m prediction (wrong); no breach"),
]


# The position-lost (S-A2) bounds EXACTLY as pre-registered (ruling 2026-10-17, Table 7.2 bound), METHODOLOGY.md:11298-11300. The
# final UKF port's forced-invalid score files (safety_ukf_a_v2, _v3) were scored with the FGO bound 0.75 s on the coordinator's
# instruction (M:14263-14264) and record bound_s 0.75; the tables show the registered 0.1 s. The score files are not changed.
A2PRE = (("safety_fgo", 0.75, 11298, "FGO: within **0.75 s** of the kill"), ("safety_ukf_a", 0.1, 11299, "UKF (a): within **0.1 s** of TFAIL"),
         ("safety_ukf_b", 5.5, 11300, "UKF (b): within **5.5 s** of the kill"))


def a2pre(f):
    return next((b for p_, b, _, _ in A2PRE if f.startswith(p_)), None)


def a2cite():
    return ", ".join(cite(M_, ln, ph) for _, _, ln, ph in A2PRE)


def srow(test, f, build, note):
    j = HJ(f); fl = []
    for k, nm in (("S-A1", "attitude"), ("S-A2", "position lost"), ("S-A3", "safe landing"), ("S-A4_single_landing", "single landing")):
        if f == "safety_ekf3_ref" and k == "S-A2":
            fl.append("n/a"); continue
        raw = (k == "S-A4_single_landing" and not j[k]["PASS"] and j[k].get("rearmed_after_disarm") is None)
        fl.append(f"{'PASS' if j[k]['PASS'] else 'FAIL'}" + (" (no disarm in the score file) ‡" if raw else ""))
    s2 = j["S-A2"]; s3 = j["S-A3"]
    t2 = f"{rd(s2['text_delay_s'], 2)} s (bound {rd(a2pre(f), 2)})" if s2.get("text_delay_s") is not None else "—"
    d3 = f"{rd(s3['horiz_disp_m'], 2)} m" if s3.get("horiz_disp_m") is not None else ("breach" if s3.get("breach") else "—")
    allp = all(j[k]["PASS"] for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing")) if f != "safety_ekf3_ref" else None
    verdict = "reference (no criteria)" if allp is None else ("ALL PASS" if allp else "FAILED AS WORDED")
    return (test, j["trial"], build, " / ".join(fl), t2, d3, verdict, note)


rowsS = [srow(*s) for s in SAFE]
SV = {r[1]: r for r in rowsS}
_a2s = a2cite()
check("score-file bound_s differs from the pre-registered S-A2 bound only for the final UKF port's forced-invalid runs",
      ", ".join(f for _, f, _, _ in SAFE if f != "safety_ekf3_ref" and HJ(f)["S-A2"]["bound_s"] != a2pre(f)), "safety_ukf_a_v2, safety_ukf_a_v3",
      "eval/results/expH/safety_*.json (S-A2 bound_s) against METHODOLOGY.md:11298-11300; M:14263-14264 (scored with the 0.75 s bound)")
check("UKF forced-invalid, final UKF port runs: position-lost delay (s) against the pre-registered 0.1 s; verdict unchanged",
      " / ".join(f"{rd(HJ(f)['S-A2']['text_delay_s'], 2)} ≤ 0.1: {HJ(f)['S-A2']['text_delay_s'] <= 0.1}, score file {HJ(f)['S-A2']['PASS']}" for f in ("safety_ukf_a_v2", "safety_ukf_a_v3")),
      "0.00 ≤ 0.1: True, score file True / 0.00 ≤ 0.1: True, score file True", "M:11299; numbers.md §15 safety and history rows ('trigger 0.00 s from effect')")
check("UKF node-kill test, earlier final-build run / final re-test: position-lost delay (s), verdict", f"{rd(HJ('safety_ukf_b_v2')['S-A2']['text_delay_s'], 2)} / {rd(HJ('safety_ukf_b_v3')['S-A2']['text_delay_s'], 2)}, "
      f"{SV['H_safety_ukf_b_v2'][6]} / {SV['H_safety_ukf_b_v3'][6]}", "5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("UKF forced-invalid test, earlier final-build run / final re-test: verdict", f"{SV['H_safety_ukf_a_v2'][6]} / {SV['H_safety_ukf_a_v3'][6]}", "ALL PASS / ALL PASS", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("final FGO node runs: forced-invalid position-lost delay / drift; node-kill", f"{rd(HJ('safety_fgo_a_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v3')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v3')['S-A3']['horiz_disp_m'], 2)} m", "0.54 s / 0.83 m; 0.25 s / 1.19 m", "numbers.md §15 history row (v3, earlier final-build run)")
check("corrected-priors node: forced-invalid position-lost delay / drift; node-kill", f"{rd(HJ('safety_fgo_a_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v4')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v4')['S-A3']['horiz_disp_m'], 2)} m", "0.60 s / 1.45 m; 0.62 s / 0.21 m",
      "numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS'")
check("corrected-priors node forced-invalid / node-kill verdict", f"{SV['H_safety_fgo_a_v4'][6]} / {SV['H_safety_fgo_b_v4'][6]}", "ALL PASS / ALL PASS", "numbers.md §15 safety row (v4, final)")
check("FGO ablation build forced-invalid / node-kill: position-lost delay s, drift m", f"{rd(HJ('safety_fgo_a_v2')['S-A2']['text_delay_s'], 2)} s, {rd(HJ('safety_fgo_a_v2')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v2')['S-A2']['text_delay_s'], 2)} s, {rd(HJ('safety_fgo_b_v2')['S-A3']['horiz_disp_m'], 2)} m", "0.29 s, 0.78 m; 0.43 s, 1.27 m", "numbers.md §15 history row")
check("history: drift (m) UKF forced-invalid re-run / UKF node-kill / FGO forced-invalid / FGO node-kill (2 m hold); UKF node-kill position-lost delay (s)",
      f"{rd(HJ('safety_ukf_a_rerun')['S-A3']['horiz_disp_m'], 2)} / {rd(HJ('safety_ukf_b')['S-A3']['horiz_disp_m'], 2)} / {rd(HJ('safety_fgo_a')['S-A3']['horiz_disp_m'], 2)} / "
      f"{rd(HJ('safety_fgo_b2')['S-A3']['horiz_disp_m'], 2)}; {rd(HJ('safety_ukf_b')['S-A2']['text_delay_s'], 2)}", "0.42 / 0.28 / 0.37 / 1.25; 4.81", "numbers.md §15 history row")
check("FGO node-kill first run safe landing; UKF forced-invalid first run position lost / safe landing", f"{HJ('safety_fgo_b')['S-A3']['PASS']}; {HJ('safety_ukf_a')['S-A2']['PASS']} / {HJ('safety_ukf_a')['S-A3']['PASS']}",
      "False; False / False", "numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL)")
check("EKF3 reference drift (m)", f"{rd(HJ('safety_ekf3_ref')['S-A3']['horiz_disp_m'], 2)}", "1.40", "numbers.md §15 history row")
# H comparative criteria (ruling 2026-10-16, item 1): the final-build sets (S2v2, S3v2) are PRIMARY; the S2/S3 verdicts move here as
# "superseded builds". Reduced from the stored eval/results/expH/h_comparative_2026-10-11.json (both sets); nothing recomputed.
_HCJ = L("expH/h_comparative_2026-10-11.json"); _HE = _HCJ["EKF3 (S1 far, flying)"]
_HSET = {("re" if k.startswith("re-flown") else "old"): v for k, v in _HCJ["sets"].items()}


def hcomp(v):
    cr = v["criteria"]; runs = cr["runs"]
    hu = [r["hold_mean_mm"] for r in v["UKF"]]; hf = [r["hold_mean_mm"] for r in v["FGO"]]; he = [r["hold_mean_mm"] for r in _HE]
    ju = [r["jump_15s_mm"] for r in v["UKF"]]; jf = [r["jump_15s_mm"] for r in v["FGO"]]; je = [r["jump_15s_mm"] for r in _HE]
    lw = sum(r["lowest_hold"] == "UKF" for r in runs)
    return {"H-H2": (f"{cr['H-H2'].split()[0]} (0/3): UKF lowest {lw}/3", rng(hu, 1), rng(hf, 1), rng(he, 1)),
            "P-H3": (f"{cr['P-H3'].split()[0]} (0/3): gyro activity max/min {rng([r['ph3_ratio'] for r in runs])}",),
            "H-H4 (15 s)": (f"{cr['H-H4 (15 s)'].split()[0]} (0/3): EKF3 jump {' / '.join(rd(x, 0) for x in je)} mm against UKF "
                            f"{rng(ju, 0)}, FGO {rng(jf, 0)} mm",),
            "H-H4 (5 s)": (f"{cr['H-H4 (5 s)'].split()[0]} (0/3): jump max/min {rng([r['hh4b_ratio'] for r in runs], 1)}",)}


def hctxt(t):
    return t[0] if len(t) == 1 else f"{t[0]} (UKF {t[1]}, FGO {t[2]}, EKF3 {t[3]} mm)"


HCR, HCO = hcomp(_HSET["re"]), hcomp(_HSET["old"])
# the pre-registered wording, VERBATIM (ruling 2026-10-17), with its design-draft line; H5.4a/b sit under "H-H4 (tag loss)"
HCW = {k: ("'" + H5V[k][3] + "' (" + vquote(*H5V[k]) + ")") for k in H5V}
h5v_unchanged()
# Table A.2 page 1: the per-estimator Experiment 5 hypotheses, VERBATIM from the S0/S1 pre-registration (M:10623, "written before
# any H flight"), with the earlier design-draft wordings of H5.1 and H5.5 quoted beside them (two wordings; both PASS).
_H51 = "H-H1 (primary, EKF3 flying): mean hold error ≤ 0.05 m and max ≤ 0.15 m in every pre-loss hold window, 3/3 flights."
_H55 = ("P-H5 (drift during loss, per estimator): EKF3 and FGO: drift at the end of the 5 / 15 / 30 s hover losses ≤ 0.05 / 0.10 / "
        "0.20 m. UKF: ≤ 2× those. Loss during the move (12 s): ≤ 0.15 m for EKF3 and FGO, 0.30 m for the UKF.")
_H57 = "P-H7 (lockout): no estimator locks out the returning tag in any loss."
_D51 = ("H-H1 (primary): every estimator holds within tag-fix accuracy. Mean hold error ≤ 0.05 m and max ≤ 0.15 m in 3/3 flights "
        "per estimator.")
_D55 = "P-H5 (drift during loss, prediction): GT drift during the 15 s occlusion ≤ 0.3 m for every estimator."
# Item 5 (ruling 2026-10-18): the METHODOLOGY S0/S1 pre-registration is dated by its commit; check that the heading and the scored
# H5.1 / H5.5 text are in METHODOLOGY.md at c11fcf3, and that c11fcf3 predates the first Experiment 5 flight (H_s0a; the earlier
# attempt H_s0a_ABORTED aborted before take-off, M:10711-10712).
_PRH = "Experiment H (marker-relative position holding): pre-registration of S0 and S1 (written before any H flight)"
_MC11 = re.sub(r"\s+", " ", " ".join(re.sub(r"^\s*-\s+", "", ln) for ln in subprocess.run(["git", "-C", ROOT, "show", f"{H5V_C}:{M_}"],
               capture_output=True, text=True).stdout.split("\n")).replace("**", "").replace("`", ""))
check(f"{M_} at {H5V_C}: the S0/S1 pre-registration heading and the scored H5.1 / H5.5 wording present", all(t in _MC11 for t in (_PRH, _H51, _H55)), True,
      f"git show {H5V_C}:{M_}")
_c11 = subprocess.run(["git", "-C", ROOT, "show", "-s", "--format=%cI", H5V_C], capture_output=True, text=True).stdout.strip()
_s0a = re.search(r"timestamp_utc:\s*(\S+)", open(os.path.expanduser("~/thesis_data/trials/H_s0a/metadata.yaml")).read()).group(1)
import datetime as _dt
_c11t = _dt.datetime.fromisoformat(_c11); _s0at = _dt.datetime.fromisoformat(_s0a.replace("Z", "+00:00"))
_S0A = _s0at.astimezone(_c11t.tzinfo).strftime("%Y-%m-%d %H:%M")
check(f"{H5V_C} ({_c11}) predates the first Experiment 5 flight H_s0a ({_s0a})", _c11t < _s0at, True, "git log; ~/thesis_data/trials/H_s0a/metadata.yaml")
H5A2NOTE = ("Experiment 5 hypotheses scored on this page, the pre-registered wording verbatim (Experiment 5 S0/S1 pre-registration, "
            f"written before any Experiment 5 flight): H5.1 '{_H51}' ({vquote(M_, 10687, 10688, _H51)}); H5.5 '{_H55}' "
            f"({vquote(M_, 10689, 10692, _H55)}; the flying UKF and FGO keep these bands, {cite(M_, 10969, 'These are the S1 bands.')}); "
            f"H5.7 '{_H57}' ({vquote(M_, 10700, 10700, _H57)}). The METHODOLOGY wording is the one scored (ruling 2026-10-18): it is "
            f"the formal pre-registration ('{_PRH}', {cite(M_, 10623, _PRH)}), committed in {H5V_C} ({H5V_DATE}), before the first "
            f"Experiment 5 flight (H_s0a, {_S0A}). Design-draft wording (not scored), tag_hold_design.md §e: H5.1 '{_D51}' "
            f"({vquote(_THD, 176, 177, _D51)}) and H5.5 '{_D55}' ({vquote(_THD, 188, 188, _D55)}). Under either wording both PASS: every hold window of every flying hold set on this page is inside 50 mm mean "
            "and 150 mm max, and every drift is inside its band (columns above), the 15 s drifts far below 300 mm. H5.6 (re-lock time "
            "and jump) is in Table 7.3.")
_HW = [w for trs in (S1, S1F, S2O, S2V, S3O, S3V, S3RP) for t in trs for w in HJ(t)["hold_windows_vehicle"]]
check("every hold window of every flying hold set: mean ≤ 50 mm and max ≤ 150 mm (H5.1 under either wording)",
      all(w["mean_m"] <= 0.05 and w["max_m"] <= 0.15 for w in _HW), True, "numbers.md §17, §17.1 (H-H1 PASS)")
check("15 s loss drift of the flying final-build sets ≤ 300 mm (H5.5, design-draft wording '≤ 0.3 m')", all(v <= 300 for e in EST for v in DR[(e, 1)]), True,
      "METHODOLOGY.md:12243 ('P-H5 PASSES: every estimator drifted ≤ 30 mm over the 15 s loss (≤ 0.3 m)')")
HCL = {"H-H2": "H5.2 FGO holds tightest", "P-H3": "H5.3 smoothness similar", "H-H4 (15 s)": "H5.4a after a 15 s loss, EKF3 jumps most",
       "H-H4 (5 s)": "H5.4b after a 5 s loss, jumps similar"}       # thesis_vocabulary.md §5, Experiment 5
rowsHC = [(HCL[k], HCW[k], hctxt(HCR[k]), hctxt(HCO[k]), "no" if HCR[k][0].split()[0] == HCO[k][0].split()[0] else "YES") for k in HCW]
check("Experiment 5 comparative verdicts, final-build sets (primary) / superseded builds", " ; ".join(HCR[k][0].split()[0] for k in HCW) + " / " +
      " ; ".join(HCO[k][0].split()[0] for k in HCW), "FAIL ; FAIL ; FAIL ; FAIL / FAIL ; FAIL ; FAIL ; FAIL", "numbers.md §17.2 criteria table (both sets)")
check("Experiment 5 hold UKF / FGO / EKF3, final-build sets (mm)", f"{HCR['H-H2'][1]} / {HCR['H-H2'][2]} / {HCR['H-H2'][3]}",
      "6.4–7.1 / 8.3–8.6 / 7.8–7.9", "numbers.md §17.2 criteria table (re-flown)")
check("Experiment 5 hold UKF, superseded builds (mm)", HCO["H-H2"][1], "5.5–6.1", "numbers.md §17.2 criteria table (earlier sets)")
check("Experiment 5 H5.4a 15 s re-lock jump, EKF3 per flight / UKF / FGO, final-build sets (mm; original priors; the FGO "
      "figure 7–30 is superseded by the corrected-prior re-fly, 7–24, numbers_refly.md §4.3)",
      HCR["H-H4 (15 s)"][0].split("EKF3 jump ")[1].replace(" mm against UKF ", " / ").replace(", FGO ", " / ").replace(" mm", ""),
      "5 / 5 / 7 / 20–30 / 7–30", "numbers.md:677 ('5 / 5 / 7 against UKF 20–30, FGO 7–30 mm')")
check("H5.3 max/min, final-build / superseded", f"{rng([r['ph3_ratio'] for r in _HSET['re']['criteria']['runs']])} / "
      f"{rng([r['ph3_ratio'] for r in _HSET['old']['criteria']['runs']])}", "2.40–2.58 / 2.37–2.43", "numbers.md §17.2 criteria table")
check("H5.4b max/min, final-build / superseded", f"{rng([r['hh4b_ratio'] for r in _HSET['re']['criteria']['runs']], 1)} / "
      f"{rng([r['hh4b_ratio'] for r in _HSET['old']['criteria']['runs']], 1)}", "3.2–7.7 / 3.4–5.9", "numbers.md §17.2 criteria table")
check("final safety runs: drift to touchdown, UKF forced-invalid / UKF node-kill / FGO forced-invalid / FGO node-kill (m)",
      " / ".join(rd(HJ(f)["S-A3"]["horiz_disp_m"], 2) for f in ("safety_ukf_a_v3", "safety_ukf_b_v3", "safety_fgo_a_v4", "safety_fgo_b_v4")),
      "0.58 / 1.07 / 1.45 / 0.21", "numbers.md §15 safety row (final runs, restated 2026-10-16)")
A4ART = [f for f in ("safety_ukf_a", "safety_fgo_b") if not HJ(f)["S-A4_single_landing"]["PASS"]]
check("raw single-landing entries in the early score files (PASS, LAND entries, disarm recorded)",
      ", ".join(f"{f}: {HJ(f)['S-A4_single_landing']['PASS']}, {HJ(f)['S-A4_single_landing']['n_land_entries_after_t_f']}, "
                f"{HJ(f)['S-A4_single_landing']['rearmed_after_disarm']}" for f in A4ART),
      "safety_ukf_a: False, 1, None, safety_fgo_b: False, 1, None", "eval/results/expH/safety_ukf_a.json, safety_fgo_b.json (the score files)")
A2FN = [OCASE_KEY, ob_h5("a"), ob_safe("b")]
CHK_HS = CHK; CHK = []

f1 = L("f1_test.json"); dec1 = f1["decision"]
bagsF = ["fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3"]
check("H1.4 robust FGO lower yaw max on", f"{dec1['robust_lower_yaw_max_on']}/6", "6/6", "numbers.md §15.2 F1 row")
check("H1.4 lockouts robust FGO = hard-gated UKF", json.dumps(dec1["lockout_total"], sort_keys=True), json.dumps({"FGO_robust": 3, "UKF_hard": 3}, sort_keys=True), "numbers.md §15.2")
check("H1.4 verdict (robust FGO better)", dec1["robust_FGO_better"], False, "numbers.md §15.2 (NOT met, lockout tie)")
check("hard-gated FGO plain-wall yaw max (deg)", rng([f1[b]["FGO_hard"]["yaw_max_deg"] for b in bagsF]), "4.59–5.03", "numbers.md §15.2 F1 row")
ST = {}
for mode in ("lc", "nolc"):
    for key in ("step_median_ms", "step_p99_ms", "wall_s"):
        ST[(mode, key)] = [json.load(open(f"{TD}/T_A_r{r}/lc_fgo_{mode}_t245/stats.json"))[key] for r in (1, 2, 3)]
check("Experiment 3 with loop closure, median (ms)", rng(ST[("lc", "step_median_ms")], 0), "35–41", "numbers.md §16.3 (restated 2026-10-11)")
check("Experiment 3 without loop closure, median (ms)", rng(ST[("nolc", "step_median_ms")], 0), "50–61", "numbers.md §16.3")
check("Experiment 3 with loop closure, p99 (ms)", rng(ST[("lc", "step_p99_ms")], 0), "80–94", "numbers.md §16.3")
check("Experiment 3 without loop closure, wall time (s)", rng(ST[("nolc", "wall_s")], 0), "7276–9583", "numbers.md §16.3")
NB14 = len([k for k in f1 if k.startswith(("fwdc_tex", "fwdplainc_tex"))])
check("H1.4 bags in the test", f"{NB14}", "6", "numbers.md §15.2 F1 row (over the 6 bags)")
A3FN = [OCASE_KEY,
        obasis("a", "the robust FGO against the hard-gated UKF on the camera heading (H1.4, the robust-weighting test)",
               "lockout episodes (total over the bags) and yaw-error maximum per bag, °",
               f"{NB14} bags (textured floor, flights 1–3 of the plain-wall camera dataset (whole cruise) and of the textured-wall "
               "camera dataset (end-wall region); both arms replayed offline on the same bags, paired)",
               "'robust FGO better than hard-gated UKF' iff, over the 6 bags, it has fewer lockout episodes in total AND a lower "
               f"yaw-error max on ≥ 4 of 6 (pre-registered, H1.4; {cite(M_, 7921, 'robust FGO better than hard-gated UKF')}, "
               f"{cite(M_, 7922, 'episodes in total AND a lower yaw-error max on ≥ 4 of 6')})",
               f"lower yaw max on {dec1['robust_lower_yaw_max_on']} of {NB14}, but lockouts {dec1['lockout_total']['FGO_robust']} (robust FGO) = "
               f"{dec1['lockout_total']['UKF_hard']} (hard-gated UKF), so not fewer: NOT met", "i"),
        obasis("b", "the build ablations (earlier build against final build)",
               "as in each row (contact time, s; criteria pass/fail; hold error and drift, mm)",
               "the flights of each set (1 flight without heading, 3 with heading, 3 per hold set; separate flights, unpaired)",
               "none: no comparison between builds was pre-registered", "as tabulated", "iii")]
CHK_F = CHK; CHK = []

ABL = [  # build ablations: (ablation, measure, earlier build, final build, verdict)
    ("UKF earlier build → final UKF port (jitter correction)", "closed loop, no heading: wall contact", rowsA[4][2].split(",")[0] + " (PASS)", rowsA[5][2].split(",")[0] + " (PASS)", "both inside the window"),
    ("UKF earlier build → final UKF port", "closed loop, with heading: all five criteria", rowsA[4][3], rowsA[5][3], "earlier build: flight 3 failed the lateral-speed bound (flow validity)"),
    ("UKF earlier build → final UKF port", "Experiment 5 hold, window means / drift", f"{rowsH[2][2]} / {rowsH[2][3]}", f"{rowsH[3][2]} / {rowsH[3][3]}", "every band PASS in both"),
    ("FGO ablation build (noise fix only) → final FGO node (+ gated yaw cap)", "closed loop, no heading: wall contact", rowsA[8][2].split(",")[0] + " (PASS)", rowsA[9][2].split(",")[0] + " (PASS)", "gating alone: +0.3 s"),
    ("FGO ablation build → final FGO node", "closed loop, with heading: all five criteria; heading error max", f"{rowsA[8][3]}; {rowsA[8][5].split('/ ')[1]}", f"{rowsA[9][3]}; {rowsA[9][5].split('/ ')[1]}", "final node: flight 3 lateral speed 0.246 m/s (bound 0.25)"),
    ("FGO ablation build → final FGO node", "Experiment 5 hold, window means / drift", f"{rowsH[4][2]} / {rowsH[4][3]}", f"{rowsH[5][2]} / {rowsH[5][3]}", "few-mm level only"),
    ("FGO ablation build → final FGO node → corrected-priors node", "forced-invalid / node-kill tests", f"{SV['H_safety_fgo_a_v2'][6]} / {SV['H_safety_fgo_b_v2'][6]}",
     f"final node {SV['H_safety_fgo_a_v3'][6]} / {SV['H_safety_fgo_b_v3'][6]}; corrected-priors node {SV['H_safety_fgo_a_v4'][6]} / {SV['H_safety_fgo_b_v4'][6]}",
     "the corrected-priors node flew the corrected priors"),
    ("Flown FGO priors (initial-uncertainty correction)", "closed loop, Experiment 5 FGO-flying hold sets, safety tests of the ablation build and final node, "
     "and (2026-11-12 regeneration) the full closed-loop corridor and hold re-fly",
     "original priors: initial yaw σ 1e-3 rad, roll/pitch 2°", "offline FGO: 1°, 5° (= UKF)",
     "re-flown after the freeze (2026-11-12 regeneration): the closed-loop corridor (H1.8, H1.9; Table 4.3, Table 4.3b, Table A.1's last "
     "row) and the hold set (H5.1, H5.5-H5.7 and the comparatives; Table 6.1, Table A.2's new row) now also fly the corrected priors, "
     "matching the safety tests' corrected-priors node"),
]


def save_table(figs, fid, name, title, caption, inputs, rows_, checks, verdict=None):
    """RESTYLE (2026-11-02): A1-A3 are already rendered as appendix data tables (per-build/per-run criteria, not a
    narrative chart) - kept as the existing multi-page A4 text-table layout rather than resized to text width, since
    collapsing a dense multi-column table to 160 mm would make it unreadable; documented as RS-3 in the handover. A
    caption file is still written (RS-2) for consistency with every other item in the set; `verdict` (RS-2 pointer) is
    folded into `caption` before ITEMS stores it, so it shows on the combined PDF's own caption page too."""
    global CHK
    if verdict is None:
        verdict = "Verdict rows: see docs/thesis/tables/TA_verdicts.md."
    caption = caption + "\n\n" + verdict
    from thesis_style import write_caption
    write_caption(fid, f"{TNUM[fid]}. {title}.\n\n{caption}")
    pngs = []
    for k, f in enumerate(figs):
        base = os.path.join(OUT, name + (f"_p{k + 1}" if len(figs) > 1 else ""))
        f.savefig(base + ".png", dpi=150); f.savefig(base + ".pdf"); plt.close(f); pngs.append(base + ".png")
    ok = all(c[4] for c in checks)
    txt_ = " ".join([title, caption] + TP_BUF); TP_BUF.clear()
    ITEMS.append(dict(id=fid, num=TNUM[fid], kind="appendix", png=pngs, pdf=None, title=title, caption=caption, inputs=inputs, rows=rows_,
                      checks=checks, status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale="none needed (table)", uncheck="",
                      files=[x for p in pngs for x in (os.path.basename(p), os.path.basename(p)[:-4] + ".pdf")], order=None, text=txt_))
    print(f"wrote {name} ({len(pngs)} page(s))  checks {sum(c[4] for c in checks)}/{len(checks)}")
    for c in checks:
        if not c[4]:
            print("   CHECK FAIL:", c)


figs = table_page("Table A.1. Closed loop (Experiment 1C): every flown build, pass/fail against the pre-registered criteria",
                  ["flying estimator", "build", "without heading: wall contact (contact window)", "with heading: all five criteria (+ estimator validity)",
                   "max cross-track", "yaw error p95 / max", "max lateral speed"], rowsA, [16, 30, 30, 22, 13, 22, 14],
                  notes=["Contact windows are pre-registered per estimator (EKF3 [+155, +215] s, UKF [+146, +218] s, FGO [+145, +196] s). Rows "
                         "marked 'superseded' are kept as recorded, not counted as current (the n = 3 no-heading cells and their k/3 counts are "
                         "reported in Table 4.3/4.3b and TA_verdicts.md, not on this per-build page). " + RTFX + " "
                         "The CURRENT builds are the final UKF port and the final FGO node (corrected priors, 4c07374b/HEAD, last row); every "
                         "other row, including the final FGO node's own original-priors flights (noise fix + gated yaw cap, before the prior "
                         "correction), is superseded as labelled. Only the CURRENT FGO row used the corrected initial priors (initial yaw σ 1°, "
                         "roll/pitch 5°); every superseded FGO row used the original priors (initial yaw σ 1e-3 rad, roll/pitch 2°). The UKF "
                         "earlier build's half real-time flight 3 lateral-speed failure (0.296 m/s) is a flow-validity limitation of the sensor "
                         "pipeline; under the corrected priors the largest with-heading lateral speed over all 9 current flights is "
                         f"{rd(_B4MAXV, 3)} m/s ({_B4MAXE}, flight {_B4MAXI}), comfortably inside the 0.25 m/s bound (Table 4.3). The five criteria: "
                         "mission completion and the cross-track, heading-error, lateral-speed and oscillation bounds. Robust heading weighting "
                         "(FGO): the robust-weighting test (H1.4) 'NOT met (lockout tie)', see Table A.3."] + A1FN, bold=False)
save_table(figs, "A1", "A1_closed_loop_builds", "Closed loop: every flown build against the five closed-loop criteria and the contact window",
           "Pass/fail of every closed-loop corridor set flown, against the five closed-loop criteria and the contact window, with the "
           "build ablations labelled: the UKF earlier build (superseded) against the final UKF port (CURRENT); the FGO earlier build "
           "(original, superseded), the ablation build (superseded) and the final FGO node, superseded on the original priors and then "
           "CURRENT once re-flown on the corrected priors. No ordering between builds or estimators is claimed [a].",
           "eval/results/closed_loop_<trial>.json", "§15 (contacts, B1–B5 counts, B2, B3, re-flown sets); claim 14", CHK_A,
           verdict="Verdict rows: as Figure 4.1/4.1b (H1.8, H1.9, per build; Table A.4).")
figs = table_page("Table A.2. Experiment 5 (tag hold): hold sets and the 5S safety tests (all runs, as-worded verdicts)",
                  ["hold set", "build", "hold error (window means)", "tag-loss drift (effective, all losses)", "lockouts", "drift band (H5.5)"],
                  rowsH, [26, 34, 20, 26, 10, 18], fs=8.0, notes=[H5A2NOTE], bold=False) + \
       table_page("Table A.2 (cont.). Experiment 5S safety tests: failure injected in the hold; the FC must declare position lost",
                  ["test", "trial", "build", "as worded: attitude / position lost / safe landing / single landing", "'position lost' delay", "drift to touchdown", "verdict", "note"],
                  rowsS, [19, 19, 35, 27, 22, 12, 14, 26], fs=6.8,
                  notes=["Bounds as pre-registered: 'FGO: within 0.75 s of the kill'; 'UKF (a): within 0.1 s of TFAIL'; 'UKF (b): within 5.5 s "
                         f"of the kill' ({_a2s}). The final UKF port's forced-invalid score files record 0.75 s (scored with the FGO bound on "
                         "instruction, METHODOLOGY.md:14263-14264); shown at the registered 0.10 s; delays 0.00 s, verdict unchanged.",
                         "FINAL = the latest run of each test on the final build (the final UKF port's re-test; the FGO corrected-priors node). The UKF "
                         "node-kill test's position-lost declaration FAILS AS WORDED in the earlier final-build run (5.75 s) and the re-test "
                         "(5.69 s) against 5.5 s: relay drain in MAVProxy (the ground-station message relay) after the SIGKILL (the forced process "
                         "kill); both stay FAILED, by ruling. " + PRIORS + " ‡ Raw score-file entries for the first UKF forced-invalid and FGO node-kill runs: "
                         "single landing FAIL, one LAND entry, no disarm recorded by the scorer. The results record calls these not applicable "
                         "(a forced-invalid run) and not scored (no touchdown); Table 7.2 shows them so. "
                         "For the FGO the forced-invalid test is also a node kill (without the "
                         "safety watcher watching the node). The EKF3 reference has no thesis-nav text (not applicable). Ordering footnote [b] "
                         "(the safety tests are per-run criteria, not comparisons): on the next page."], bold=False) + \
       table_page("Table A.2 (cont.). Experiment 5 comparative hypotheses: the final-build sets (primary) and the superseded builds",
                  ["hypothesis", "pre-registered wording (verbatim; design draft §e)", "final-build sets: final UKF port, final FGO node (PRIMARY)",
                   "superseded builds: UKF earlier build, FGO ablation build", "verdict differs?"], rowsHC, [14, 34, 50, 50, 12], fs=8.0,
                  notes=["The final-build verdicts are reported as primary; they are identical to the original-build verdicts (all three comparative "
                         "criteria FAIL on both). EKF3 is the EKF3-flying far-spawn hold set in both columns (3 flights); each estimator flew its "
                         "own flights, paired by run index, not trajectory. Two wordings change with the final builds: the FGO hold is now the "
                         "highest, not tied with EKF3, and EKF3's 15 s jump is strictly the smallest. " + PRIORS, OCASE_KEY, A2FN[1], A2FN[2]], bold=False)
save_table(figs, "A2", "A2_H_and_safety", "Experiment 5 hold sets and the 5S safety tests (all runs)",
           "Experiment 5 hold sets (EKF3-flying, near and far spawn; UKF-flying, earlier and final builds; FGO-flying, ablation and final "
           "builds) with hold error, drift, lockouts and the drift bands (H5.5), and every 5S safety-test run with its as-worded verdict; "
           "the final runs are the re-tests of the final UKF port and of the FGO corrected-priors node. The comparative criteria page "
           "gives this build-ablation record's own final-build sets beside the superseded earlier builds; the verdict category is "
           "identical in both and in the corrected-priors re-fly (all FAIL), though the FGO hold value narrows under the corrected "
           "priors [a]; the safety verdicts are per run [b].",
           "eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json, safety_*.json", "§15 safety rows, §17, §17.1; METHODOLOGY 2d and 'Band C … FGO safety re-tests'", CHK_HS,
           verdict="Verdict rows (Table A.4, Experiment 5 and 5S): H5.1-H5.7 and the five 5S safety rows.")
rowsF = [("H1.4 robust-weighting test (k = 2.385)", "robust FGO better than the hard-gated UKF on the heading", "NOT met (lockout tie)",
          f"robust FGO lower worst-case yaw on {dec1['robust_lower_yaw_max_on']}/6 bags, but lockouts robust FGO {dec1['lockout_total']['FGO_robust']} = hard-gated UKF "
          f"{dec1['lockout_total']['UKF_hard']}; hard-gated FGO plain-wall yaw max {rng([f1[b]['FGO_hard']['yaw_max_deg'] for b in bagsF])}° (= hard-gated UKF to 0.01°)"),
         ("Experiment 3 compute cost (DIAGNOSTIC)", "per-update solve time and wall time, keyframe FGO, workstation Python, 6 parallel jobs", "no criterion",
          f"median with loop closure {rng(ST[('lc', 'step_median_ms')], 1)} ms, without {rng(ST[('nolc', 'step_median_ms')], 1)} ms; p99 with {rng(ST[('lc', 'step_p99_ms')], 0)} ms, "
          f"without {rng(ST[('nolc', 'step_p99_ms')], 0)} ms; wall time without loop closure {rng(ST[('nolc', 'wall_s')], 0)} s. Says nothing about onboard feasibility")]
figs = table_page("Table A.3. The robust-weighting test (H1.4), the Experiment 3 compute cost, and the build ablations",
                  ["item", "what is tested", "verdict", "key numbers"], rowsF, [24, 42, 30, 94], notes=A3FN[:2], bold=False)
figs2 = table_page("Table A.3 (cont.). Build ablations: earlier build against the final build, same experiment",
                   ["ablation", "measure", "earlier build", "final build", "note"], ABL, [36, 42, 36, 38, 38],
                   notes=["Earlier builds are kept as recorded and labelled; the thesis cites the final builds. Attribution: the corrections were applied "
                          "jointly and are not attributed individually, apart from the traced plain-wall case and the Experiment 4 partial attribution.", OCASE_KEY, A3FN[2]], bold=False)
save_table(figs + figs2, "A3", "A3_F1_cost_ablations", "The robust-weighting test (H1.4), the Experiment 3 compute cost and the build ablations",
           "Pass/fail table for the robust-weighting test (H1.4), the Experiment 3 compute cost (diagnostic; linear values, no plot) and the "
           "build ablations: the UKF earlier build against the final UKF port; the FGO ablation build against the final FGO node and the "
           "corrected-priors node. H1.4 NOT met [a]; ablations descriptive [b].",
           "eval/results/f1_test.json; ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json; closed_loop_*, expH/*",
           "§15.2 F1 row; §16.3 cost bullets; §15, §17.1", CHK_F,
           verdict="Verdict rows (Table A.4): H1.4 (robust-weighting test). The Experiment 3 compute cost and the "
                   "build ablations on this page (earlier build vs final build) have no pre-registered hypothesis id and so no row of their "
                   "own - do not confuse with the separate EXPLORATORY attribution-ablation rows in Table A.4, which score a different "
                   "study (which correction caused which change).")

# =============================================================================================== TABLE T7 failure behaviour (new)
# Ruling 2026-10-16 (open items, 10): the early S-A4 flags are shown as the results record has them, quoted with file:line;
# the raw score-file entries are in Appendix A2.
A4NA = {"safety_ukf_a": "not applicable", "safety_fgo_b": "not scored"}
A4Q = {11490: "- **S-A4:** not applicable (an (a) run).",
       11827: "- **S-A4:** not scored (no touchdown). One LAND entry, no conflict between the two paths."}


def sfail(f):
    """As-worded outcome of one safety score file, with the S-A4 scorer artefact flagged (METHODOLOGY L11307, L11490, L11827)."""
    j = HJ(f); out = []
    for k, nm in (("S-A1", "attitude"), ("S-A2", "position lost"), ("S-A3", "safe landing"), ("S-A4_single_landing", "single landing")):
        if f == "safety_ekf3_ref" and k == "S-A2":
            continue
        if not j[k]["PASS"]:
            if k == "S-A4_single_landing" and j[k].get("rearmed_after_disarm") is None and f in A4NA:
                out.append(f"single landing {A4NA[f]} ‡")
            elif k == "S-A2":
                out.append(f"position lost FAIL as worded ({rd(j[k]['text_delay_s'], 2)} s, bound {rd(a2pre(f), 2)} s)")
            elif k == "S-A3":
                out.append("safe landing FAIL (" + ("safety-watcher breach" if j[k].get("breach") else "criterion") + ")")
            else:
                out.append(f"{nm} FAIL")
    s3 = j["S-A3"]; d = f", {rd(s3['horiz_disp_m'], 2)} m" if s3.get("horiz_disp_m") is not None else ""
    return ("ALL PASS" + d) if not out else "; ".join(out)


_ML = open(os.path.join(ROOT, "METHODOLOGY.md")).read().split("\n")
check("METHODOLOGY.md:11490 and :11827 (the single-landing reasons cited in Table 7.2)", " | ".join(_ML[n - 1] for n in sorted(A4Q)),
      " | ".join(A4Q[n] for n in sorted(A4Q)), "METHODOLOGY.md lines 11490, 11827 (read at build time)")
check("EKF3 blank invalid (s of cruise); valid airborne flow frames", f"{rng(EK_INV, 0)}; max {max(nvalid)}", "301–310; max 0", "numbers.md §6.2")
stepO = {e: [L(f"expO/{t}.json")["tracks"][f"{e} live"]["max_step_after_return_m"] for t in OFL] for e in EST}
check("Experiment 4 largest step in 10 s after return EKF3 / UKF / FGO live (m)", " / ".join(rng(stepO[e]) for e in EST), "4.10–4.10 / 2.30–2.44 / 2.14–2.28", "numbers.md §16.2 table")
check("UKF node-kill test, earlier final-build run / final re-test: position-lost delay (s), verdict", f"{rd(HJ('safety_ukf_b_v2')['S-A2']['text_delay_s'], 2)} / {rd(HJ('safety_ukf_b_v3')['S-A2']['text_delay_s'], 2)}, "
      f"{SV['H_safety_ukf_b_v2'][6]} / {SV['H_safety_ukf_b_v3'][6]}", "5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("UKF forced-invalid test, earlier final-build run / final re-test: verdict", f"{SV['H_safety_ukf_a_v2'][6]} / {SV['H_safety_ukf_a_v3'][6]}", "ALL PASS / ALL PASS", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("corrected-priors node: forced-invalid position-lost delay / drift; node-kill", f"{rd(HJ('safety_fgo_a_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v4')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v4')['S-A3']['horiz_disp_m'], 2)} m", "0.60 s / 1.45 m; 0.62 s / 0.21 m",
      "numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS'")
check("final FGO node runs: forced-invalid position-lost delay / drift; node-kill", f"{rd(HJ('safety_fgo_a_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v3')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v3')['S-A3']['horiz_disp_m'], 2)} m", "0.54 s / 0.83 m; 0.25 s / 1.19 m", "numbers.md §15 history row (v3, earlier final-build run)")
check("FGO node-kill first run safe landing; UKF forced-invalid first run position lost / safe landing", f"{HJ('safety_fgo_b')['S-A3']['PASS']}; {HJ('safety_ukf_a')['S-A2']['PASS']} / {HJ('safety_ukf_a')['S-A3']['PASS']}",
      "False; False / False", "numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL)")
check("EKF3 reference drift (m)", f"{rd(HJ('safety_ekf3_ref')['S-A3']['horiz_disp_m'], 2)}", "1.40", "numbers.md §15 history row")
SA = {"UKF (a) PARAM": [("earlier build, run 1", "safety_ukf_a"), ("earlier build, re-run", "safety_ukf_a_rerun"), ("final UKF port", "safety_ukf_a_v2"),
                        ("final UKF port, re-test (FINAL)", "safety_ukf_a_v3")],
      "UKF (b) KILL": [("earlier build", "safety_ukf_b"), ("final UKF port", "safety_ukf_b_v2"), ("final UKF port, re-test (FINAL)", "safety_ukf_b_v3")],
      "FGO (a) KILL": [("earlier build", "safety_fgo_a"), ("ablation build", "safety_fgo_a_v2"), ("final FGO node", "safety_fgo_a_v3"),
                       ("corrected-priors node, re-test (FINAL)", "safety_fgo_a_v4")],
      "FGO (b) KILL": [("earlier build, run 1", "safety_fgo_b"), ("earlier build, 2 m hold", "safety_fgo_b2"), ("ablation build", "safety_fgo_b_v2"),
                       ("final FGO node", "safety_fgo_b_v3"), ("corrected-priors node, re-test (FINAL)", "safety_fgo_b_v4")]}
sa = lambda key: "\n".join(f"{lab}: {sfail(f)}" for lab, f in SA[key])
check("end of cruise UKF / FGO (m, nearest 1000 m; numbers.md km × 10^3, digits grouped) †", f"{BLK['UKF']} / {BLK['FGO']}", grp(si_str("29–40 / 23–41", 3)),
      "numbers.md §6.2 erratum E6 ('29–40 / 23–41' km)")
rowsT7 = [
    ["EKF3", f"position flagged INVALID from take-off on all {len(EK_INV)} blank flights ({rng(EK_INV, 0)} s of cruise; {max(nvalid)} valid "
             "airborne flow frames); outputs the origin, not scored: a DECLARED failure",
     f"resets to GNSS on return: {rng(stepO['EKF3'])} m jump (every flight, the switching script's delay) [b]", "not run (EKF3 has no thesis-nav position-lost path)",
     f"reference KILL only (no criteria): drift {rd(HJ('safety_ekf3_ref')['S-A3']['horiz_disp_m'], 2)} m against a ≤ 0.5 m prediction "
     "(the prediction was wrong); no breach"],
    ["UKF", f"no invalid period recorded; position runs away: +60 s {rng(BLANK['UKF'][:, 2], 0)} m, end of cruise {BLK['UKF']} m †",
     f"largest step in 10 s after return {rng(stepO['UKF'])} m", sa("UKF (a) PARAM"), sa("UKF (b) KILL")],
    ["FGO", f"no invalid period recorded; position runs away: +60 s {rng(BLANK['FGO'][:, 2], 0)} m, end of cruise {BLK['FGO']} m †",
     f"largest step in 10 s after return {rng(stepO['FGO'])} m", sa("FGO (a) KILL"), sa("FGO (b) KILL")]]
save_tab("T7", "T7_failure_behaviour", "Failure behaviour: blank-floor validity, the Experiment 4 return jump and the 5S safety tests",
         "How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the FGO run away with no invalid period recorded [a]; on the "
         "return to GNSS EKF3 jumps 4.1 m, about 4.3 s after GNSS returns once the simulation's GNSS switching script moves EKF3 off its indoor source set "
         "(the UKF and FGO carry no such delay) [b]; in the hold safety tests (5S) the final run of each test (the latest on the final build: the "
         "final UKF port's re-test, the FGO corrected-priors node) passes as worded except the UKF node-kill test's position-lost "
         "declaration, which fails as worded in both final-port runs (a relay-drain timing fault in the bound) [c]. " + PRIORS,
         ["estimator", "blank floor: position validity", "Experiment 4: return to GNSS", "forced-invalid test (FGO: node kill), as worded",
          "node-kill test, as worded"], rowsT7, [10, 34, 20, 44, 44],
         "eval/results/blank_behaviour.json; expO/O_r1.json, O_r2.json, O_r3b.json (max_step_after_return_m); expH/safety_*.json",
         "§6.2, §15 safety and history rows, §16.2; METHODOLOGY 'H safety test …' entries, 2d, rulings 2026-10-11, 'Band C … FGO safety re-tests'",
         notes=["Safety criteria (pre-registered): attitude criterion; position-lost declaration within the bound, as pre-registered: "
                "'FGO: within 0.75 s of the kill'; 'UKF (a): within 0.1 s of TFAIL' (the UKF forced-invalid test); 'UKF (b): within 5.5 s of "
                f"the kill' (the UKF node-kill test) ({a2cite()}); safe landing (≤ 1.5 m drift to touchdown, no safety-watcher breach); single landing, pre-registered for "
                "node-kill runs only. UKF node-kill test, both final-port runs, position-lost declaration: the trigger fired 5.0 s after the last flow received (the UKF's 5 s timeout), plus relay drain in MAVProxy "
                "(the ground-station message relay) after the SIGKILL (the forced process kill); both stay FAILED AS WORDED, by ruling. The final "
                "runs are the latest run of each test on the final build (the final UKF port's re-test, the FGO corrected-priors node's "
                "re-test); the final UKF port's first runs and the final FGO node's runs are the earlier final-build runs. The FGO re-tests "
                "flew the corrected-priors node; every earlier FGO run flew the original priors. For the FGO the forced-invalid test is also "
                "a node kill (without the safety watcher watching the node).",
                "‡ The single landing is shown as the results record gives it for these two runs: UKF forced-invalid test run 1, not "
                "applicable to a forced-invalid run (METHODOLOGY.md:11490); FGO node-kill test run 1, not scored (no touchdown; one LAND "
                "entry, no conflict between the two paths) (METHODOLOGY.md:11827; the run was stopped at the room-box breach). The raw "
                "score-file entries (single landing FAIL, no disarm recorded) are in Table A.2.",
                "UKF forced-invalid test: the bound is the pre-registered 0.1 s ('UKF (a): within 0.1 s of TFAIL', METHODOLOGY.md:11299). The "
                "earlier UKF build's score files record 0.10 s; the final UKF port's (both runs) record 0.75 s, the scorer having been run with "
                "the FGO bound on the coordinator's instruction (METHODOLOGY.md:14263-14264). Both final-port delays are 0.00 s, so the verdict "
                "(PASS) is the same under the registered bound. "
                "† runaway magnitude (order only). 'No invalid period recorded': the blank-floor scoring records an invalid period for "
                "EKF3 only; the UKF / FGO runaway positions are scored as errors (Table 4.2).",
                OCASE_KEY, ob_blank("a"), ob_ret("b"), ob_safe("c")], fs=7.2, order=70)

# =============================================================================================== TABLE T8 hindsight: FGO batch vs RTS-UKF
HB, HR = "FGO hindsight (whole-flight batch)", "RTS-UKF (hindsight)"
p4 = agg["P-T4 hindsight ratio max/min"]
rowsT8 = []
for c in TCOND:
    mr = agg["conditions"][c]["mean_rmse_m"]; b_, r_ = mr[HB], mr[HR]
    rowsT8.append([f"Experiment 2, condition {c}: {TLAB[c]} (mean of 3)", f"{rd_si(b_, 3)}", f"{rd_si(r_, 3)}", "FGO whole-flight batch" if b_ < r_ else "smoothed UKF",
                   f"{rd(max(b_, r_) / min(b_, r_), 2)}", f"H2.4 {'PASS' if p4['PASS'] else 'FAIL'}"])
o3 = []
for i, t in enumerate(OFL):
    b_, r_ = OI[HB][i], OI[HR][i]; o3.append(max(b_, r_) / min(b_, r_))
    rowsT8.append([f"Experiment 4: flight {i + 1} (indoor)", f"{rd_si(b_, 3)}", f"{rd_si(r_, 3)}", "FGO whole-flight batch" if b_ < r_ else "smoothed UKF", f"{rd(o3[-1], 2)}", "H4.3 PASS"])
check("H2.4 max/min ratio A / B / C / D", " / ".join(f"{rd(p4['by_condition'][c], 2)}" for c in TCOND), "1.31 / 2.14 / 2.06 / 3.89", "numbers.md §16.1 P-T4")
check("Table 5.2 ratio = stored H2.4 ratio, all 4 conditions", all(abs(float(r[4]) - p4["by_condition"][c]) < 0.006 for r, c in zip(rowsT8, TCOND)), True,
      "t_aggregate.json P-T4 vs mean_rmse_m")
check("Experiment 2 smoothed UKF A–D (m)", " / ".join(f"{rd(agg['conditions'][c]['mean_rmse_m'][HR], 3)}" for c in TCOND), "0.014 / 0.031 / 0.039 / 0.109", "numbers.md §16.1 table")
check("Experiment 2 FGO whole-flight batch A–D (m)", " / ".join(f"{rd(agg['conditions'][c]['mean_rmse_m'][HB], 3)}" for c in TCOND), "0.010 / 0.015 / 0.019 / 0.028", "numbers.md §16.1 table")
check("Experiment 4 FGO whole-flight batch vs smoothed UKF ratio, max/min per flight (capped)", rng(o3), "1.01–1.02", "numbers.md §16.2 P-O3")
cf = [max(OI[HB][i], L(f"expO/{t}.json")["tracks"]["RTS-UKF (hindsight, cap-free forward pass)"]["indoor_rmse_m"]) /
      min(OI[HB][i], L(f"expO/{t}.json")["tracks"]["RTS-UKF (hindsight, cap-free forward pass)"]["indoor_rmse_m"]) for i, t in enumerate(OFL)]
check("Experiment 4 FGO whole-flight batch vs cap-free smoothed UKF ratio, max/min per flight", rng(cf), "1.01–1.05", "numbers.md §16.2 P-O3 (cap-free)")
save_tab("T8", "T8_hindsight_ratio", "Hindsight: the FGO whole-flight batch against the smoothed UKF",
         "With tags at known positions (Experiment 2) the FGO whole-flight batch is below the smoothed UKF in every condition, by 1.3–3.9× "
         "(largest with 1 tag; H2.4 FAIL as pre-registered) [a]; indoors without GNSS (Experiment 4) the two hindsight tracks are equal within "
         "1–2% (H4.3 PASS) [b].",
         ["case", "FGO whole-flight batch RMSE (m)", "smoothed UKF RMSE (m)", "lower [c]", "max ÷ min", "pre-registered test"], rowsT8, [40, 18, 18, 16, 14, 18],
         "eval/results/expT/t_aggregate.json (conditions.*.mean_rmse_m, 'P-T4 hindsight ratio max/min'); expO/O_r1.json, O_r2.json, O_r3b.json "
         "(tracks.*.indoor_rmse_m)", "§16.1 (table, P-T4), §16.2 (table, P-O3); claims 18, 21",
         notes=["Ratio = max ÷ min of the two hindsight RMSEs (the pre-registered definition in H2.4 and H4.3), so it is ≥ 1 and the 'lower' "
                "column gives the direction: in Experiment 4 the smoothed UKF is lower on flights 1 and 2 and the FGO whole-flight batch on "
                "flight 3. Aggregation differs: Experiment 2 is per condition from the means of 3 repeats (the RMSE over the 5 laps); "
                "Experiment 4 is per flight (indoor RMSE, 123 s). Experiment 2 is in the world frame with tag fixes at known positions; "
                "Experiment 4 in the world frame with GNSS outside only.",
                f"Cap-free smoothed-UKF variant in Experiment 4: max ÷ min {rng(cf)}. The former 'FGO whole-flight batch ~2× better than the "
                "smoothed UKF' in Experiment 4 is WITHDRAWN (a noise-model artefact). Hindsight here = the FGO whole-flight batch and the "
                "smoothed UKF (single-pass RTS smoother); Experiment 3's keyframe-FGO hindsight (iSAM2 full estimate) is a different "
                "estimator and is not in this table.", OCASE_KEY, ob_h24("a"), ob_h43("b"),
                obasis("c", "the 'lower' column (which hindsight track has the smaller RMSE in each row)",
                       "horizontal RMSE, m (Experiment 2: mean of the flights in each condition; Experiment 4: per flight, indoor)",
                       "3 flights per condition in Experiment 2 (4 conditions) and 3 flights in Experiment 4; both hindsight tracks "
                       "from the same flights", "none: H2.4 and H4.3 test similarity (within 1.5×), not an ordering; no ordering "
                       "test was pre-registered", "the direction per row, as tabulated", "iii")], order=80)

# =============================================================================================== combined PDF + index
PAL = "EKF3 #0072B2 (blue, circle) · UKF #009E73 (bluish green, triangle) · FGO #D55E00 (vermilion, square) · truth / references #999999 (grey)"


def combine_extra_items():
    """RESTYLE (2026-11-02): pull in the items built by the three OTHER figures_thesis generators (figs_thesis_methods.py,
    figs_thesis_drift.py, figs_thesis_results.py) plus the new TA_verdicts appendix table, so the rebuilt
    thesis_figures_combined.pdf carries every restyled reader-facing item, not just this script's own. Nothing is
    recomputed: each item's PNG and caption text are read back from what its own generator already wrote and checked
    (that generator's own index_*.md / eval/ta_verdicts_check.py has the cross-check detail for it)."""
    CAPD = os.path.join(OUT, "captions")

    def cap_of(fid, drop_prefix):
        """Read captions/<fid>.md and strip the leading '{num}. {title}.' line write_caption() prefixed, since the
        combined PDF's caption_page() prints '{num}. {caption}' itself and would otherwise double it."""
        txt = open(os.path.join(CAPD, f"{fid}.md")).read().strip()
        if drop_prefix and txt.startswith(drop_prefix):
            txt = txt[len(drop_prefix):].lstrip()
        return txt

    extra = []
    ma_cap = cap_of("methods_architecture", None)
    ma_title = "System architecture: sensors, bridges, the three estimators and where each one runs"
    ma_prefix = f"{TNUM['METHODS_ARCH']}. {ma_title}.\n\n"
    extra.append(dict(id="METHODS_ARCH", num=TNUM["METHODS_ARCH"], kind="figure",
                      png=[os.path.join(OUT, "methods_architecture_a.png"), os.path.join(OUT, "methods_architecture_b.png")],
                      pdf=os.path.join(OUT, "methods_architecture.pdf"),   # two panels, each legible at page width
                      title=ma_title, caption=cap_of("methods_architecture", ma_prefix), inputs="see docs/thesis/figures_thesis/index_methods.md",
                      rows="checks: see index_methods.md (built by eval/figs_thesis_methods.py)", checks=[],
                      status="CURRENT", logscale="none needed", uncheck="", foot=[],
                      files=["methods_architecture.png", "methods_architecture.pdf"]))
    # Figure 4.1c (R5) dropped from the numbered set (user 2026-11-13; it repeated 4.1d, its only unique panel uncited);
    # its files stay in docs/thesis/figures_thesis/ and its own generator is unchanged.
    # RESTYLE (2026-11-03): R6 - the 9-flight restyled copy of the results-walkthrough's fl_1A_unaligned_paths (page 01),
    # built by eval/figs_thesis_drift9.py. The walkthrough figure itself is unchanged.
    r6_title = "Without a heading source, every one of the 9 flights drifts sideways off the true path"
    r6_prefix = f"{r6_title}.\n\n"
    extra.append(dict(id="R6", num=TNUM["R6"], kind="figure",
                      png=os.path.join(OUT, "R6_drift_9flights.png"), pdf=os.path.join(OUT, "R6_drift_9flights.pdf"),
                      title=r6_title, caption=cap_of("R6", r6_prefix), inputs="see docs/thesis/figures_thesis/index_drift9.md",
                      rows="checks: see index_drift9.md (built by eval/figs_thesis_drift9.py)", checks=[],
                      status="CURRENT", logscale="none needed", uncheck="", foot=[],
                      files=["R6_drift_9flights.png", "R6_drift_9flights.pdf"]))
    r3_title = "True and estimated paths, top-down: with the camera heading the UKF and FGO paths lie on the true path"
    r3_prefix = f"{TNUM['R3']}. {r3_title}.\n\n"
    extra.append(dict(id="R3", num=TNUM["R3"], kind="figure",
                      png=os.path.join(OUT, "R3_trajectory_overlay.png"), pdf=os.path.join(OUT, "R3_trajectory_overlay.pdf"),
                      title=r3_title, caption=cap_of("R3", r3_prefix), inputs="see docs/thesis/figures_thesis/index_results.md",
                      rows="checks: see index_results.md (built by eval/figs_thesis_results.py)", checks=[],
                      status="CURRENT", logscale="none needed", uncheck="", foot=[],
                      files=["R3_trajectory_overlay.png", "R3_trajectory_overlay.pdf"]))
    ta_title = "Verdict register: every registered hypothesis/check across Experiments 1-5/5S, the tier-1 extension experiments E2-E6 and the exploratory attribution ablation"
    ta_png = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "tables_extra", "TA_verdicts.png")
    ta_pdf = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "tables_extra", "TA_verdicts.pdf")
    ta_cap = open(os.path.join(ROOT, "docs", "thesis", "tables", "TA_verdicts.md")).read().split("\n\n")[1].strip()
    extra.append(dict(id="TA", num=TNUM["TA"], kind="appendix", png=ta_png, pdf=ta_pdf, title=ta_title, caption=ta_cap,
                      inputs="docs/thesis/tables/R1_hypothesis_scorecard.md, tier1/scores/*.json, ablation/ablation_results.json",
                      rows="checks: eval/ta_verdicts_check.py (146/146 EXACT)", checks=[], status="CURRENT", logscale="none needed (table)",
                      uncheck="", foot=[], files=["tables_extra/TA_verdicts.png", "tables_extra/TA_verdicts.pdf"]))
    for it in extra:
        it["text"] = " ".join([it["title"], it["caption"]])
        ITEMS.append(it)


combine_extra_items()
# order: the thesis order (thesis_vocabulary.md §6): chapter, figures before tables, then number; the appendix last
ITEMS.sort(key=lambda it: tkey(it["id"]))
REMOVED = [("F1", "F1_scorecard", "T1"), ("F3", "F3_accuracy_without_and_with_heading", "T2"), ("F4", "F4_blank_floor_flow_loss", "T3"),
           ("F8", "F8_H_tag_loss_drift", "T5")]
PREV = "7778cd6"
VOC = "docs/thesis/thesis_vocabulary.md"
# APPENDIX MAPPING (thesis_vocabulary.md §2-§5 and §9): thesis label -> internal code(s). "Used in" is found by searching the printed
# text of each item (title, caption, headers, cells, notes, figure text) for the search pattern; nothing is typed by hand.
MAPT = [  # (thesis label, internal code(s), search pattern, vocabulary row)
    ("Experiment 1, corridor comparison", "(no single code: the `dsn` / `fwdc` / `fwdplainc` datasets, Phases 3–5, the F tests, the closed-loop \"Part 2\")", r"Experiment 1(?![\dABC.])", "§1; §2 row 1"),
    ("Experiment 1A, standard-sensor comparison", "`dsn_*` batch", r"\b1A\b", "§2 row 6"),
    ("Experiment 1B, camera-heading studies", "Phase 3, 4, 5; F1–F3c; plan step 2", r"\b1B\b", "§2 row 7"),
    ("Experiment 1C, closed-loop corridor flights", "`cl_*`; \"Part 2\"", r"\b1C\b", "§2 row 8"),
    ("Experiment 2, known tags", "Experiment T", r"Experiment 2\b", "§2 row 2"),
    ("Experiment 3, loop closure", "Experiment L", r"Experiment 3\b", "§2 row 3"),
    ("Experiment 4, outdoor–indoor", "Experiment O", r"Experiment 4\b", "§2 row 4"),
    ("Experiment 5, tag hold", "Experiment H", r"Experiment 5\b", "§2 row 5"),
    ("5S safety tests", "`H_safety_*`; safety (a) / (b)", r"\b5S\b", "§2 row 9"),
    ("condition A–D (8 / 4 / 2 / 1 tags; kept as letters)", "Experiment T conditions A–D; `T_A` … `T_D`", r"condition [A-D]", "§8.1 row 29; §10 row 21"),
    ("standard-sensor dataset", "`dsn`", r"standard-sensor dataset", "§2 row 11"),
    ("heading-error decomposition of sideways drift", "Phase 5 decomposition (`plots/lateral_checks.py` method)", r"heading-error decomposition", "§5 (under H1.3)"),
    ("thesis-nav position-lost path (the Copter landing trigger)", "`thesis_nav_check`", r"thesis-nav", "§8.3"),
    ("textured-wall camera dataset (upper bound)", "`fwdc`", r"textured-wall|textured walls|camera datasets", "§2 row 13"),
    ("plain-wall camera dataset (featureless case)", "`fwdplainc`", r"plain-wall|plain walls|camera datasets", "§2 row 14"),
    ("camera calibration flights", "`p1c_*`", r"camera calibration flights", "§2 row 15"),
    ("cruise ATE", "`evo -a (cruise)`", r"cruise ATE", "§3 row 17"),
    ("contact window", "closed-loop set (a) PRIMARY window; U3", r"contact window|registered window", "§3 row 20"),
    ("mission completion", "B1", r"mission completion|all five", "§3 row 23"),
    ("cross-track bound", "B2", r"cross-track bound|max \|?cross-track|all five", "§3 row 24"),
    ("heading-error bound", "B3", r"heading-error bound|heading error (p95|max|mean)|yaw error p95|all five", "§3 row 25"),
    ("lateral-speed bound", "B4", r"lateral-speed bound|lateral speed|all five", "§3 row 26"),
    ("oscillation bound", "B5", r"oscillation bound|all five", "§3 row 27"),
    ("estimator-validity criterion", "closed-loop S2 (\"+S2\")", r"estimator.validity|estimator validity", "§3 row 28"),
    ("drift band", "P-H5", r"drift band", "§3 row 30"),
    ("lockout criterion (no lockout)", "P-H7", r"no lockout", "§3 row 32"),
    ("attitude criterion", "S-A1", r"attitude", "§3 row 33"),
    ("position-lost declaration", "S-A2", r"position.lost", "§3 row 34"),
    ("safe landing", "S-A3", r"safe landing", "§3 row 35"),
    ("single landing", "S-A4", r"single landing|single-landing", "§3 row 35"),
    ("forced-invalid test", "safety (a) PARAM (the FGO's (a) is a node kill)", r"forced-invalid", "§4 row 46"),
    ("node-kill test", "safety (b) KILL", r"node-kill", "§4 row 46"),
    ("with / without heading", "closed-loop set (b) / set (a)", r"with heading|no heading|without heading|without a heading", "§4 set letters"),
    ("with / without loop closure", "LC / no-LC / `nolc`", r"loop closure", "§8.1 row 31"),
    ("smoothed UKF", "RTS-UKF", r"smoothed UKF|smoothed-UKF", "§4 row 38"),
    ("FGO whole-flight batch (hindsight)", "FGO batch", r"whole-flight batch", "§4 row 37; §8.1 row 33"),
    ("hard-gated FGO / hard-gated UKF / robust FGO", "`FGO_hard` / `UKF_hard` / `FGO_robust`", r"hard-gated|robust FGO", "§8.1 row 34"),
    ("final build (final UKF port / final FGO node)", "UKF v2 (`_v2`); FGO v3 (`_v3`); hold sets S2v2 / S3v2", r"final UKF port|final FGO node|final build|final-build", "§4 row 40"),
    ("ablation build", "FGO v2 (`_v2`); hold set S3; ABLATION", r"ablation build", "§4 row 41"),
    ("earlier build", "UKF v1 (\"old UKF\"); original FGO; hold set S2", r"earlier build|earlier UKF build|earlier FGO build", "§4 row 42"),
    ("corrected-priors node", "FGO v4 (`4c07374b`)", r"corrected-priors node", "§4 row 43"),
    ("original / corrected priors (initial-uncertainty correction)", "OLD / NEW priors; D18 model correction", r"original (FGO )?priors|corrected priors|initial-uncertainty", "§4 row 44"),
    ("EKF3-flying hold set (near / far spawn)", "H stage S1 / S1 far", r"EKF3-flying", "§8.1 row 18"),
    ("UKF-flying hold set (earlier / final build)", "H stage S2 / S2v2", r"UKF-flying", "§8.1 row 18"),
    ("FGO-flying hold set (ablation / final build)", "H stage S3 / S3v2", r"FGO-flying", "§8.1 row 18"),
    ("half real-time (RTF 0.5)", "`_half`; \"half speed\" (banned)", r"half real.time", "§4 row 45"),
    ("runaway magnitude (†)", "†", r"†", "§4 row 47"),
    ("EKF3 with the Python / C++ heading node", "Python / C++ bridge; `bcpp`", r"heading node", "§8.1 row 40"),
    ("safety watcher", "watcher", r"safety.watcher", "§8.1 row 41"),
]
MAPH = [  # (thesis label, name in words, internal code) - thesis_vocabulary.md §5
    ("H1.1", "standard-sensor ordering, EKF3 vs FGO (confirmatory)", "the r4–r10 paired test"),
    ("H1.2", "heading-measurement validation", "Phase 3 validation"),
    ("H1.3", "heading-fusion prediction (judged on the heading-error decomposition of sideways drift)", "Phase 5 prediction; Phase 5 decomposition"),
    ("C1.a", "FGO vs UKF with heading (comparison, no decision rule)", "C0"),
    ("H1.4", "robust-weighting test", "F1 (pre-registered)"),
    ("H2.1", "FGO hindsight gain grows with the gap", "H-T1"), ("H2.2", "the same for the smoothed UKF", "P-T2"),
    ("H2.3", "live errors similar", "P-T3"), ("H2.4", "FGO hindsight ≈ smoothed UKF", "P-T4"),
    ("V3", "estimator validation check", "V-L"),
    ("H3.1", "loop closure bounds live drift", "H-L1"), ("H3.2", "live error lower with loop closure", "H-L2"),
    ("H3.3", "hindsight error lower with loop closure", "H-L3"), ("H3.4", "without loop closure, drift grows lap on lap", "P-L4"),
    ("H4.1", "FGO hindsight beats the filters' live tracks indoors", "H-O1"), ("H4.2", "live indoor errors similar", "H-O2"),
    ("H4.3", "FGO batch ≈ smoothed UKF", "P-O3"),
    ("H5.2", "FGO holds tightest", "H-H2"), ("H5.3", "smoothness similar", "P-H3"),
    ("H5.4a", "after a 15 s loss, EKF3 jumps most", "H-H4 (15 s)"), ("H5.4b", "after a 5 s loss, jumps similar", "H-H4 (5 s)"),
    ("H5.5", "drift band", "P-H5"), ("H5.7", "no lockout", "P-H7"),
]
HPAT = {"H5.4a": r"H5\.4a", "H5.4b": r"H5\.4b|H5\.4a–b", "H3.2": r"H3\.2|H3\.1–H3\.4", "H3.3": r"H3\.3|H3\.1–H3\.4"}


def used_in(pat):
    return ", ".join(it["num"] for it in ITEMS if re.search(pat, it["text"])) or "—"


def caption_page(P, it):
    pngs = it["png"] if isinstance(it["png"], list) else [it["png"]]
    for pi, png in enumerate(pngs):
        img = plt.imread(png); h, w = img.shape[:2]
        fig = plt.figure(figsize=(11.69, 8.27))
        top = 0.965; avail = 0.70 if it["kind"] == "figure" else 0.78; aw = 0.95; ah = aw * (h / w) * 11.69 / 8.27
        last = pi == len(pngs) - 1
        cap = "\n".join(textwrap.wrap(f"{it['num']}. {it['caption']}", 175))
        fn = "\n".join(ln for t in it.get("foot", []) for ln in textwrap.wrap(t, 188))
        if last and fn:          # ordering footnotes (2026-10-17): shrink the image so caption + footnotes fit on the page
            need = 0.0185 * (cap.count("\n") + 1) + 0.0142 * (fn.count("\n") + 1) + 0.075
            avail = min(avail, top - 0.02 - need)
        if ah > avail: aw *= avail / ah; ah = avail
        ax = fig.add_axes([0.5 - aw / 2, top - ah, aw, ah]); ax.imshow(img); ax.axis("off")
        y = top - ah - 0.02
        if last:
            fig.text(0.03, y, cap, fontsize=8.6, va="top"); y -= 0.0185 * (cap.count("\n") + 1) + 0.01
            if fn:
                fig.text(0.03, y, fn, fontsize=7.0, va="top", color=INK); y -= 0.0142 * (fn.count("\n") + 1) + 0.008
            # D113 (2026-11-02, coordinator ruling, advisor-review fix): a reader-facing figure's caption text in the
            # combined PDF must END with its "Verdicts: Table A.4, ..." pointer - nothing after it. The cross-check
            # line below is a check COUNT ("N/M values match"), one of the categories D113 names explicitly, and
            # previously printed on every page regardless of kind, including the 8 figures this ruling covers
            # (F2/F9/F5/F6/F7/METHODS_ARCH/R5/R3 - every `kind == "figure"` item in this PDF, confirmed: tables and
            # the TA appendix page are `kind == "table"`/`"appendix"` and keep it). Tables/appendix pages are not in
            # scope for D113 (same exemption as A1-A3's cells) and keep this line unchanged.
            if it["kind"] != "figure":
                if it["checks"]:
                    okc = sum(c[4] for c in it["checks"])
                    src = "\n".join(textwrap.wrap(f"Cross-check against the results record: {okc}/{len(it['checks'])} values match. The sources, "
                                                  "the rows they are checked against and the build are listed in the figure index.", 200))
                else:
                    # RESTYLE (2026-11-02): items from another generator (figs_thesis_drift.py / figs_thesis_results.py /
                    # figs_thesis_methods.py / eval/ta_verdicts_check.py) - their own cross-checks are reported there, not
                    # duplicated here; "rows" names where to look.
                    src = "\n".join(textwrap.wrap(f"Cross-checked by its own generator, not duplicated here: {it['rows']}.", 200))
                fig.text(0.03, max(y, 0.02 + 0.0165 * (src.count("\n") + 1)), src, fontsize=7.2, va="top", color=INK2)
        P.savefig(fig); plt.close(fig)


NFIG = ", ".join(it["num"].split()[1] for it in ITEMS if it["kind"] == "figure")
NTAB = ", ".join(it["num"].split()[1] for it in ITEMS if it["kind"] == "table")
NAPP = ", ".join(it["num"].split()[1] for it in ITEMS if it["kind"] == "appendix")
with PdfPages(PDF) as P:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.06, 0.88, "Thesis figures and tables", fontsize=24, weight="bold")
    fig.text(0.06, 0.835, "EKF3, UKF and FGO for indoor UAV state estimation under degraded sensing (simulation; results FROZEN 2026-10-11)", fontsize=12)
    intro = ("Reader-facing set (revision 2026-10-16; thesis numbering and names 2026-10-17), plotted and tabulated from the frozen "
             f"result files (no number recomputed): Figures {NFIG}; Tables {NTAB} (also as LaTeX and markdown in docs/thesis/tables/); "
             f"appendix Tables {NAPP}. Numbered by chapter: 3 method; 4 Experiment 1 (corridor comparison); 5 Experiments 2–4 (known tags, loop "
             "closure, outdoor–indoor); 6 Experiment 5 (tag hold); 7 synthesis; A appendix. Each table caption gives its cross-check "
             "count; a figure's cross-checks, and every item's sources, are in the figure index. Figure captions end with a pointer to "
             "their scored hypothesis/check row(s) in Table A.4 (docs/thesis/tables/TA_verdicts.md). Conventions: one fixed colour and "
             "marker per estimator; solid lines and filled marks = live, dashed lines and open marks = hindsight; linear axes only; "
             "cruise ATE = the aligned ATE over the pinned cruise window. "
             "† = a runaway magnitude from a diverging estimate (order of magnitude only). Lettered footnotes [a], [b], … under each "
             "table give the metric, n (with its unit), the pre-registered rule and the result for every ordering "
             "claimed or not claimed. " + PRIORS + " Half real-time (RTF 0.5): " + RTFX)
    _intro_lines = textwrap.wrap(intro, 140)
    fig.text(0.06, 0.79, "\n".join(_intro_lines), fontsize=9.6, va="top")
    # RESTYLE (2026-11-02): "Colours" (and everything below) used a fixed y that assumed a fixed intro line count;
    # combine_extra_items() adds Figures 3.1/4.1c/4.2 to NFIG, which wraps the intro one line longer and collided with
    # "Colours" at the old fixed position. Position it below the intro's ACTUAL wrapped height instead.
    y0 = 0.79 - 0.0205 * len(_intro_lines) - 0.012
    fig.text(0.06, y0, "Colours", fontsize=12, weight="bold")
    for k, e in enumerate(EST):
        fig.add_artist(Line2D([0.07, 0.10], [y0 - 0.030 - 0.026 * k] * 2, color=C[e], lw=2, marker=MK[e], ms=7, transform=fig.transFigure))
        fig.text(0.11, y0 - 0.030 - 0.026 * k, f"{e}  {C[e]}", fontsize=10, va="center")
    fig.add_artist(Line2D([0.07, 0.10], [y0 - 0.108] * 2, color=TRUTH, lw=2, transform=fig.transFigure)); fig.text(0.11, y0 - 0.108, f"truth / reference  {TRUTH}", fontsize=10, va="center")
    y = y0 - 0.150; fig.text(0.06, y, "Contents", fontsize=12, weight="bold"); y -= 0.024
    # RESTYLE (2026-11-03, found while adding R6/Figure 4.1d): the per-item step (and, if that is not enough on its own,
    # the font size) shrink to fit however many items ITEMS holds, so a future addition to the figure/table set cannot
    # silently run the list off the bottom of the page the way a fixed 0.0215 step already had (Table 7.2 and later rows
    # were cut off at 22 items, confirmed against the committed PDF before this fix, which already clipped from Table A.2
    # on at 21 items) - same shrink-to-fit principle as results-walkthrough's own title1().
    CONTENTS_BOTTOM = 0.02
    step = min(0.0215, (y - CONTENTS_BOTTOM) / len(ITEMS))
    fs = 8.6 if step >= 0.0215 else max(6.0, 8.6 * (step / 0.0215))
    assert step > 0, f"Contents list ({len(ITEMS)} items) does not fit on the cover page at all - needs a second page"
    for it in ITEMS:
        clabel = f"checks {sum(c[4] for c in it['checks'])}/{len(it['checks'])}" if it["checks"] else "checks: own generator, see index"
        fig.text(0.07, y, f"{it['num']}  {it['title']}   [{clabel}]", fontsize=fs); y -= step
    P.savefig(fig); plt.close(fig)
    for it in ITEMS:
        caption_page(P, it)
print("wrote", PDF)

with open(INDEX, "w") as f:
    f.write("# Thesis figures and tables: index (revision 2026-10-16; thesis numbering and names 2026-10-17)\n\n")
    f.write(f"Built by `{SCRIPT}` at commit `{COMMIT}` (run with `/home/makerspace/venv-evo/bin/python`; plotting and tabulating only, no "
            "number recomputed). Combined PDF for the supervisor (in thesis order: chapter by chapter, figures before tables, then the "
            "appendix): `docs/thesis/figures_thesis/thesis_figures_combined.pdf`. Figures are here as `.pdf` and `.png`; tables are in "
            "`docs/thesis/tables/` as LaTeX (`.tex`, booktabs; NOT compiled on the build machine, which has no TeX: checked for ASCII, "
            "balanced braces and the column count of every row), markdown (`.md`) and a rendered page (`.png`). The frozen pack "
            "(`docs/thesis/final_results_pack.pdf`, `eval/figs_final_pack.py`) is untouched.\n\n")
    f.write(f"**Thesis numbering and names (2026-10-17).** Captions, titles, headers, cells and notes use the thesis vocabulary "
            f"(`{VOC}`): experiments 1–5 (1A/1B/1C, 5S), hypotheses H1.1–H5.7 (with C1.a and V3), criteria named in words, and the "
            "numbering by chapter of its §6 (Figure n.m, Table n.m, appendix Table A.m). **The output file names keep the internal ids** "
            "(F2, T1 … T8, A1 … A3), as §6 specifies (\"The repository files keep their names. Only the printed captions take the new "
            "numbers.\"); the LaTeX `\\label{tab:Tn}` keys also keep them. The appendix mapping at the end of this index leads from every "
            "thesis number and name back to the internal id or code and the output file. The Inputs, numbers.md rows and the check "
            "sources below are the data statement: they keep the record's own codes so each value can be found in the record.\n\n")
    f.write("**Revision 2026-10-16.** " + "; ".join(f"{a} (`{b}`) became table {c} (now {TNUM[c]})" for a, b, c in REMOVED) +
            f". The old figure files are removed from this folder; they remain in the git history (commit `{PREV}`, "
            f"`git show {PREV}:docs/thesis/figures_thesis/<name>.png`). F2 ({TNUM['F2']}) is now one panel (the heading-error panel moved to "
            f"{TNUM['T4']}); F6 ({TNUM['F6']}) is the time trace only (the per-flight RMSE moved to {TNUM['T6']}); F5 and F7 are unchanged. "
            f"T7 ({TNUM['T7']}, failure behaviour) and T8 ({TNUM['T8']}, hindsight ratio) are new.\n\n")
    f.write(f"**Added 2026-10-17: F9, PROVISIONAL label \"{TNUM['F9']}\"** (heading error against time on the same closed-loop "
            f"flights as {TNUM['F2']}, with a second panel at a linear ±1° scale of the with-heading flights, split from a former "
            "inset on 2026-11-04). By user ruling no figure or table is renumbered "
            "now: every existing number is unchanged, and the final number is assigned once, after the chapter plan is locked. "
            "The provisional label sorts directly after Figure 4.1. Note: the results-chapter trajectory figure R3 "
            "(`eval/figs_thesis_results.py`, `index_results.md`) also proposes \"Figure 4.2\" provisionally; both are resolved in "
            "that final numbering pass.\n\n")
    f.write(f"**Colour mapping (Okabe–Ito, colour-blind safe; fixed across every figure):** {PAL}. Solid lines / filled marks = live; dashed lines / "
            "open marks = hindsight. No log axes anywhere.\n\n")
    f.write(f"**Scorecard labels ({TNUM['T1']}; ruling 2026-10-17):** an ordering label (BEST / BEHIND / TIED) is printed only where a "
            "pre-registered decision rule was met; no comparison of the scorecard's key numbers met one (H4.1 and H4.3 are met but concern the hindsight tracks), so none is printed and the cells give the "
            "numbers and the verdict they rest on. Statuses, not orderings: on the blank floor '" + BLANK_ST + "' (ruling 2026-10-18, "
            "replacing the word FAILED); PASSED = met its "
            "pre-registered criteria with no comparison (Experiment 3, FGO only); N/A = not run.\n\n")
    f.write("**Ordering footnotes (2026-10-17).** Every place a table or caption claims, or declines to claim, an ordering carries a "
            "lettered footnote ([a], [b], …) giving the metric and unit, n with its unit of replication, the "
            "pre-registered rule with its source line (each cited line is read at build time and checked to contain the quoted "
            "phrase; those checks are in the lists below as 'rule text …') and the result against the rule. Tables carry them "
            "as notes below the table; figures carry them below the caption (here as *Footnote* lines, and on the caption page of "
            "the combined PDF). " + OCASE_KEY + " Definitions: `docs/thesis/thesis_vocabulary.md` §11 and "
            "`docs/thesis/methodology_definitions_draft.md` ('n' and 'Ordering verdicts').\n\n")
    f.write("| thesis no. | internal id | kind | files | title | status | checks | log-scale handling |\n|---|---|---|---|---|---|---|---|\n")
    for it in ITEMS:
        clabel = f"{sum(c[4] for c in it['checks'])}/{len(it['checks'])}" if it["checks"] else "own generator"
        files = ", ".join(f"`{x}`" for x in it["files"])
        f.write(f"| {it['num']} | {it['id']} | {it['kind']} | {files} | {it['title']} | {it['status']} | {clabel} | {it['logscale']} |\n")
    tot = sum(len(it["checks"]) for it in ITEMS); okt = sum(sum(c[4] for c in it["checks"]) for it in ITEMS)
    f.write(f"\n**Total: {okt}/{tot} checks match** (a check repeated in two items is counted in each). **EXACT comparison** "
            "(ruling 2026-10-16): the computed string is the stored full-precision value rounded once by `rd()` (half away from "
            "zero) at the printed precision, and it must equal the expected string character for character; no tolerance, no "
            "last-digit acceptance.\n")
    bad = [c for it in ITEMS for c in it["checks"] if not c[4]]
    if bad:
        f.write("\n**Failures (not forced):** " + "; ".join(f"{c[0]}: computed `{c[1]}`, expected `{c[2]}`" for c in bad) + ".\n")
    f.write("\n## Captions, sources and checks\n\n")
    for it in ITEMS:
        f.write(f"### {it['num']} (internal {it['id']}, {it['kind']}): {it['title']}\n\n- **Caption:** {it['caption']}\n")
        for t in it.get("foot", []):
            f.write(f"  - *Footnote:* {t}\n")
        f.write(f"- **Inputs:** {it['inputs']}\n- **numbers.md rows:** {it['rows']}\n")
        if it["uncheck"]:
            f.write(f"- **Not cross-checkable:** {it['uncheck']}\n")
        f.write("\n| check | computed | expected | source | match |\n|---|---|---|---|---|\n")
        for c in it["checks"]:
            f.write(f"| {c[0]} | `{c[1]}` | `{c[2]}` | {c[3]} | {'yes' if c[4] else '**NO**'} |\n")
        f.write("\n")
    # ------------------------------------------------------------------------------------------------ appendix mapping
    f.write("## Appendix mapping: thesis label → internal code → output file\n\n")
    f.write(f"Generated from the item list and the printed text of each item (no hand-typed \"used in\" cell). Source of every thesis "
            f"name: `{VOC}` (row cited). The internal codes in this section are the point of the section: they are the trace back to the "
            "repository, the results record (`docs/thesis/numbers.md`) and METHODOLOGY.\n\n")
    f.write("### 1. Figures and tables\n\n| thesis label | internal id | output files | title |\n|---|---|---|---|\n")
    for it in ITEMS:
        f.write(f"| {it['num']} | {it['id']} | " + ", ".join(f"`{x}`" for x in it["files"]) + f" | {it['title']} |\n")
    f.write("\n### 2. Experiments, datasets, criteria, labels and builds\n\n| thesis label | internal code(s) | used in | vocabulary row |\n"
            "|---|---|---|---|\n")
    for lab, code, pat, row in MAPT:
        f.write(f"| {lab} | {code} | {used_in(pat)} | {row} |\n")
    f.write("\n### 3. Hypotheses and comparisons (thesis_vocabulary.md §5)\n\n| thesis label | name in words | internal code | used in |\n"
            "|---|---|---|---|\n")
    for lab, name, code in MAPH:
        pat = HPAT.get(lab, re.escape(lab) + r"(?![\d.])")
        f.write(f"| {lab} | {name} | {code} | {used_in(pat)} |\n")
    f.write("\n")
print("wrote", INDEX)
for it in ITEMS:
    print(f"  {it['num']:10s} ({it['id']:3s}) {it['kind']:8s} checks {sum(c[4] for c in it['checks'])}/{len(it['checks'])}")
print("TOTAL checks", sum(sum(c[4] for c in it["checks"]) for it in ITEMS), "/", sum(len(it["checks"]) for it in ITEMS))
