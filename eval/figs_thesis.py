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
PRIORS = ("The FGO safety re-tests (v4) used the NEW initial priors, while the flown FGO hold (S3v2) and corridor (v3) results "
          "used the OLD priors.")
RTFX = "The simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s."
ITEMS = []; CHK = []


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


def check(label, computed, expected, src):
    """EXACT cross-check (ruling 2026-10-16, "numbers.md rounding, option (a); a full scan; an exact cross-check"): the
    computed string, i.e. the stored full-precision value rounded ONCE by rd() at the printed precision, must equal the
    typed expected string (numbers.md, or METHODOLOGY where numbers.md has no row) character for character. No numeric
    tolerance and no "last-digit" acceptance (the pack's tolerant checker, figs_final_pack.py, is frozen and unchanged)."""
    c, e = str(computed), str(expected)
    CHK.append((label, c, e, src, c == e))


def save(fig, fid, name, title, caption, inputs, rows, logscale="none needed", uncheck=""):
    """Writes <name>.pdf and <name>.png; records caption, sources and checks for the combined PDF and the index."""
    global CHK
    fig.suptitle(title, x=0.01, ha="left", fontsize=12.5, weight="bold")
    base = os.path.join(OUT, name)
    fig.savefig(base + ".png", dpi=170, bbox_inches="tight"); fig.savefig(base + ".pdf", bbox_inches="tight"); plt.close(fig)
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=fid, kind="figure", png=base + ".png", pdf=base + ".pdf", title=title, caption=caption, inputs=inputs, rows=rows,
                      checks=CHK, status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale=logscale, uncheck=uncheck,
                      files=[name + ".png", name + ".pdf"], order=None))
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
           "|": r"$|$", "<": r"$<$", ">": r"$>$", "\n": r" \newline "}


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


def table_page(title, header, rows, widths, notes=(), fs=8.0):
    """One A4-landscape page (or more) of a wrapped text table; returns the list of figures."""
    figs = []; lh = fs * 1.34 / 72 / 8.27

    def newpage(k):
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.text(0.03, 0.965, title + (f" (continued, {k})" if k > 1 else ""), fontsize=12, weight="bold", va="top")
        x = 0.03; y = 0.925; nh = 1
        for h, w in zip(header, widths):
            hw = textwrap.wrap(h, max(6, int(w * 0.95))); nh = max(nh, len(hw))
            fig.text(x, y, "\n".join(hw), fontsize=fs + 0.3, weight="bold", va="top"); x += w / sum(widths) * 0.94
        return fig, y - max(3.6, 1.3 * nh + 0.9) * lh
    k = 1; fig, y = newpage(k)
    for row in rows:
        BW = ("FAILED", "FAIL", "MISS", "NOT met")      # bold per paragraph (one '\n'-separated item of a cell)
        cells = [[(ln, any(b in para for b in BW)) for para in str(c).split("\n") for ln in (textwrap.wrap(para, max(6, int(w * 0.95))) or [""])]
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
        lines = textwrap.wrap(nt, 190)
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
    m_ = [f"# Table {tid}. {title}", "", f"{caption}", "", "| " + " | ".join(md(h) for h in header) + " |",
          "|" + "---|" * len(header)]
    m_ += ["| " + " | ".join(md(c) for c in r) + " |" for r in rows]
    m_ += [""] + [f"*{md(n)}*" + "\n" for n in notes] + [f"<!-- generated by {SCRIPT} (commit {COMMIT}); frozen numbers only. Sources, "
                                                        f"numbers.md rows and the cross-checks: docs/thesis/figures_thesis/index.md, {tid}. -->", ""]
    open(os.path.join(TAB, name + ".md"), "w").write("\n".join(m_))
    # LaTeX (booktabs)
    tw = sum(widths); spec = "".join(f"p{{\\dimexpr {rd(w / tw * 0.999, 3)}\\linewidth-2\\tabcolsep\\relax}}" for w in widths)
    t_ = [f"% {tid}: generated by {SCRIPT} (commit {COMMIT}); frozen numbers only. Sources and cross-checks: docs/thesis/figures_thesis/index.md.",
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
    figs = table_page(f"Table {tid}. {title}", header, rows, widths, notes=notes, fs=fs)
    pngs = []
    for k, f in enumerate(figs):
        base = os.path.join(TAB, name + (f"_p{k + 1}" if len(figs) > 1 else ""))
        f.savefig(base + ".png", dpi=150, bbox_inches="tight", pad_inches=0.25); plt.close(f); pngs.append(base + ".png")
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=tid, kind="table", png=pngs, pdf=None, title=title, caption=caption, inputs=inputs, rows=nrows_ref, checks=CHK,
                      status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale="none needed (table)", uncheck=uncheck,
                      files=[name + ".md", name + ".tex"], order=order))
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
TSHORT = {"EKF3 live": "EKF3 live", "UKF live": "UKF live", "FGO live": "FGO live", "RTS-UKF (hindsight)": "RTS-UKF (hindsight)",
          "FGO hindsight (whole-flight batch)": "FGO batch (hindsight)"}
OFL = ("O_r1", "O_r2", "O_r3b")
OI = {n: [L(f"expO/{t}.json")["tracks"][n]["indoor_rmse_m"] for t in OFL] for n in TRK}
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = ["s2v2_r1", "s2v2_r2", "s2v2_r3"]; S2O = ["s2_r1", "s2_r2", "s2_r3"]
S3V = ["s3v2_r1", "s3v2_r2", "s3v2_r3"]; S3O = ["s3_r1", "s3_r2", "s3_r3"]
HALF = {"EKF3": ("cl_a_tex_half", [f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)]),
        "UKF": ("cl_ukf_a_tex_half_v2", [f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)]),
        "FGO": ("cl_fgo_a_tex_half_v3", [f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)])}
HBUILD = {"EKF3": "EKF3", "UKF": "UKF v2", "FGO": "FGO v3 (OLD priors)"}
LL = {}
for mode in ("lc", "nolc"):
    for kind in ("live", "hindsight"):
        LL[(mode, kind)] = [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{mode} {kind}"] for r in (1, 2, 3)]


def drifts(trs, key, metric="eff"):
    out = [[], [], [], []]
    for t in trs:
        for i, lo in enumerate(HJ(t)["losses"]):
            v = lo[key]
            out[i].append(1e3 * (v["effective"]["drift_m"] if metric == "eff" else v["drift_end_m"]))
    return out


# =============================================================================================== FIG 1 scorecard
CAT = {"BEST": ("#cfcfcf", "best"), "TIED": ("#f0f0f0", "tied"), "BEHIND": ("#ffffff", "behind"),
       "FAILED": ("#ffffff", "failed"), "PASSED": ("#f0f0f0", "passed"), "N/A": ("#ffffff", "n/a")}
med = {e: float(np.median([v for _, v in DSN[e]])) for e in EST}
check("dsn_tex median r1–r9 EKF3 / UKF / FGO (m)", " / ".join(f2(med[e]) for e in EST), "4.10 / 5.13 / 4.46", "numbers.md §6.1 standing row")
check("confirmatory EKF3 − FGO verdict", pt["verdict"], "no ordering claimed", "numbers.md §6.1 confirmatory row; claim 2")
u6 = [P4[b]["UKF_heading"] for b in CAMB]; g6 = [P4[b]["FGO_heading"] for b in CAMB]
check("C0 with heading UKF / FGO range, 6 textured bags (m)", f"{rng(u6)} / {rng(g6)}", "0.13–0.25 / 0.06–0.22", "numbers.md §6.6 heading-arm rows")
check("C0 FGO lower than UKF", f"{sum(a < b for a, b in zip(g6, u6))}/6", "6/6", "numbers.md §6.6 C0 row; claim 7")
check("blank end-of-cruise UKF / FGO (km) †", f"{rng(BLANK['UKF'][:, 3] / 1e3, 0)} / {rng(BLANK['FGO'][:, 3] / 1e3, 0)}", "29–40 / 22–41", "numbers.md §6.2")
check("EKF3 blank invalid for (s of cruise), all 14", rng(EK_INV, 0) + f" (n {len(EK_INV)})", "301–310 (n 14)", "numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s')")
mrD = agg["conditions"]["D"]["mean_rmse_m"]
check("T condition D live EKF3 / UKF / FGO (m)", " / ".join(f"{rd(mrD[k], 3)}" for k in ("EKF3 live", "UKF live", "FGO live")), "0.096 / 0.131 / 0.083", "numbers.md §16.1 table")
check("T FGO batch A–D (m)", rng([agg["conditions"][c]["mean_rmse_m"]["FGO hindsight (whole-flight batch)"] for c in TCOND], 3), "0.010–0.028", "numbers.md §16.1 table")
check("O indoor live RMSE EKF3 / UKF / FGO (m)", " / ".join(rng(OI[f"{e} live"]) for e in EST), "1.42–1.43 / 0.77–0.84 / 0.83–0.89", "numbers.md §16.2 table")
ho2 = [max(OI[f"{e} live"][i] for e in EST) / min(OI[f"{e} live"][i] for e in EST) for i in range(3)]
ho2_max_is_ekf3 = all(max(EST, key=lambda e: OI[f"{e} live"][i]) == "EKF3" for i in range(3))
check("O H-O2 live max/min ratio; largest = EKF3 in every flight", f"{rng(ho2)}; {ho2_max_is_ekf3}", "1.71–1.84; True", "numbers.md §16.2 H-O2 bullet")
check("O FGO batch / RTS-UKF indoor (m)", f"{rng(OI['FGO hindsight (whole-flight batch)'])} / {rng(OI['RTS-UKF (hindsight)'])}", "0.59–0.59 / 0.58–0.60", "numbers.md §16.2 table")
check("L live with / without loop closure (m)", f"{rng([t['rmse_m'] for t in LL[('lc', 'live')]], 3)} / {rng([t['rmse_m'] for t in LL[('nolc', 'live')]], 3)}",
      "0.049–0.076 / 0.263–0.361", "numbers.md §16.3")
_hc = [v for k, v in L("expH/h_comparative_2026-10-11.json")["sets"].items() if k.startswith("re-flown")][0]
hE = [np.mean([w["mean_m"] * 1e3 for w in HJ(t)["hold_windows_vehicle"]]) for t in S1F]
hU = [r["hold_mean_mm"] for r in _hc["UKF"]]; hF = [r["hold_mean_mm"] for r in _hc["FGO"]]
check("H run-mean hold error EKF3 (S1 far) / UKF (S2v2) / FGO (S3v2) (mm)", f"{rng(hE, 1)} / {rng(hU, 1)} / {rng(hF, 1)}", "7.8–7.9 / 6.4–7.1 / 8.3–8.6", "numbers.md §17.2 table")
check("H comparative H-H2; P-H3; H-H4 15 s; H-H4 5 s (re-flown)", "; ".join(_hc["criteria"][k].split()[0] for k in ("H-H2", "P-H3", "H-H4 (15 s)", "H-H4 (5 s)")),
      "FAIL; FAIL; FAIL; FAIL", "numbers.md §17.2 (final-build sets primary, ruling 2026-10-16)")
B2h = {e: [L(f"closed_loop_{t}.json")["B"]["B2"]["max_abs_x_cruise_m"] for t in HALF[e][1]] for e in EST}
passh = {e: sum(L(f"closed_loop_{t}.json")["B"]["pass"] and L(f"closed_loop_{t}.json").get("S2", {}).get("pass", True) for t in HALF[e][1]) for e in EST}
check("closed loop half, with heading: B2 range EKF3 / UKF v2 / FGO v3 (m)", " / ".join(rng(B2h[e]) for e in EST), "0.24–0.33 / 0.22–0.25 / 0.03–0.39",
      "numbers.md §15 B2 row (EKF3 half) and re-flown rows (UKF v2 0.231/0.253/0.219; FGO v3 0.118/0.033/0.392)")
check("closed loop half, with heading: flights passing B1–B5 (+S2)", " / ".join(f"{passh[e]}/3" for e in EST), "3/3 / 3/3 / 3/3", "numbers.md §15")

COLS = ["Standard sensors (textured, no heading)", "With the camera heading (offline)", "Blank floor (no flow)", "T: tags at known positions",
        "O: GNSS outside, indoors without", "L: tags at unknown positions", "H: hold on a wall tag", "Closed loop (the estimator flies)"]
CELLS = {
    "EKF3": [("TIED", f"median {rd(med['EKF3'], 2)} m", "confirmatory test: no ordering"),
             ("N/A", "no offline heading arm", "the fixed no-heading baseline"),
             ("FAILED", "position invalid from take-off", "origin output, unscored"),
             ("TIED", f"1 tag: {rd(mrD['EKF3 live'] * 100, 1)} cm live", "no live ordering claimed"),
             ("BEHIND", f"indoor {rng(OI['EKF3 live'])} m", "H-O2 FAIL; 4.10 m jump"),
             ("N/A", "FGO capability only", "the filters have no loop closure"),
             ("TIED", f"hold {rng(hE, 1)} mm", "bands PASS; comparatives FAIL"),
             ("TIED", f"{passh['EKF3']}/3 pass; B2 ≤ {rd(max(B2h['EKF3']), 2)} m", "no ordering claimed")],
    "UKF": [("TIED", f"median {rd(med['UKF'], 2)} m", "descriptive, n = 9"),
            ("BEHIND", f"{rng(u6)} m", "C0: the FGO is lower on 6/6"),
            ("FAILED", f"{rng(BLANK['UKF'][:, 3] / 1e3, 0)} km at end †", "no flow aiding"),
            ("TIED", f"1 tag: {rd(mrD['UKF live'] * 100, 1)} cm live", "no live ordering claimed"),
            ("TIED", f"indoor {rng(OI['UKF live'])} m", "UKF ≈ FGO live"),
            ("N/A", "no loop-closure equivalent", "FGO capability only"),
            ("TIED", f"hold {rng(hU, 1)} mm", "bands PASS; comparatives FAIL"),
            ("TIED", f"{passh['UKF']}/3 pass; B2 ≤ {rd(max(B2h['UKF']), 2)} m", "final UKF port, v2")],
    "FGO": [("TIED", f"median {rd(med['FGO'], 2)} m", "confirmatory test: no ordering"),
            ("BEST", f"{rng(g6)} m", "lower than the UKF on 6/6 (C0)"),
            ("FAILED", f"{rng(BLANK['FGO'][:, 3] / 1e3, 0)} km at end †", "no flow aiding"),
            ("TIED", f"1 tag: {rd(mrD['FGO live'] * 100, 1)} cm live", f"batch {rng([100 * agg['conditions'][c]['mean_rmse_m']['FGO hindsight (whole-flight batch)'] for c in TCOND], 1)} cm, H-T1 PASS"),
            ("TIED", f"indoor {rng(OI['FGO live'])} m", "batch 0.59 = RTS-UKF"),
            ("PASSED", f"live {rng([t['rmse_m'] * 100 for t in LL[('lc', 'live')]], 1)} cm", "H-L1–P-L4 PASS 3/3"),
            ("TIED", f"hold {rng(hF, 1)} mm", "bands PASS; comparatives FAIL"),
            ("TIED", f"{passh['FGO']}/3 pass; B2 ≤ {rd(max(B2h['FGO']), 2)} m", "FGO v3, OLD priors")]}
rowsT1 = [[col] + [f"{CELLS[e][j][0]}: {CELLS[e][j][1]} ({CELLS[e][j][2]})" for e in EST] for j, col in enumerate(COLS)]
save_tab("T1", "T1_scorecard", "Which estimator wins where (scorecard of the restated verdicts)",
         "Each cell gives the category, the key number and the verdict it rests on; the categories come only from the restated verdicts. "
         "Mostly ties: the FGO is best only with the camera heading, and no estimator "
         "bounds position on a blank floor.",
         ["experiment", "EKF3", "UKF", "FGO"], rowsT1, [30, 40, 40, 40],
         "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json, dsn_paired_test.json, phase4_{fwdc,fwdplainc}_evo.json, blank_behaviour.json, "
         "expT/t_aggregate.json, expO/O_*.json, expL/T_A_r*_t245.json, expH/s1far_r*.json, expH/h_comparative_2026-10-11.json, "
         "closed_loop_cl_*_half(_v2/_v3).json",
         "§6.1, §6.2, §6.6, §15, §16.1–§16.3, §17.2; claims 1a, 1b, 2, 7, 10, 14, 17–19, 23, 25",
         notes=["Categories: BEST = a stated ordering puts it first; TIED = no ordering is claimed (or all pass the same criteria); BEHIND = a "
                "stated ordering or a failed similarity verdict puts it below; FAILED = does not bound position; PASSED = met its "
                "pre-registered criteria with no comparison (L, FGO only); N/A = not run. BEHIND, PASSED and N/A are additions to "
                "best / tied / failed, used where those three do not fit.",
                "TIED where no ordering is claimed: standard sensors (the confirmatory test; the UKF medians are descriptive), T live "
                "(n = 3, descriptive), H (all drift bands PASS; the comparative criteria H-H2 / P-H3 / H-H4 FAIL on the final-build hold "
                "sets, identical to the original-build verdicts) and the closed loop (every set at half real-time (RTF 0.5) passes 3/3). BEHIND: the UKF with heading (C0: the FGO is lower on 6/6) "
                "and EKF3 in O (H-O2 FAIL; EKF3 the largest in every flight).",
                "Key numbers: standard sensors = evo -a (cruise), median of the 9 textured dsn flights; heading = the 6 textured camera bags; "
                "T = horizontal RMSE with 1 tag; O = indoor RMSE; L = with loop closure; H = mean hold error; closed loop = at half real-time "
                "(RTF 0.5). " + RTFX + " "
                "† runaway magnitude (order only). No cell restates a WITHDRAWN claim."], order=10)

# =============================================================================================== FIG 2 heading stops drift (ONE panel)
fig, ax = plt.subplots(figsize=(15.5, 6.4))
for yw in (10, -10):
    ax.axhspan(yw - 0.1, yw + 0.1, color=WALL, lw=0)
ax.axhline(9.58, color=WALL, lw=0.6, ls=":"); ax.axhline(-9.58, color=WALL, lw=0.6, ls=":")
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
ax.set_xlim(-2, 162); ax.set_ylim(-10.6, 10.6); ax.set_yticks([-10, -5, 0, 5, 10])
ax.set_xlabel("distance along the corridor, true North y (m)"); ax.set_ylabel("true East x (m)  [lateral axis stretched]")
ax.set_aspect(3.0, adjustable="box")
fig.canvas.draw()
axbb = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
x0_, x1_ = ax.get_xlim(); y0_, y1_ = ax.get_ylim()
STRETCH = (axbb.height / (y1_ - y0_)) / (axbb.width / (x1_ - x0_))
# contact labels: placed in the free middle of the corridor, linked to their X
LABXY = {"UKF": (4, -8.9, "left"), "FGO": (4, -6.6, "left"), "EKF3": (160, -3.2, "right")}
for est in EST:
    c0, ct = cl_meta(HALF[est][0]); a, b = WIN[est]; t = CT2[est]; lx, ly, ha_ = LABXY[est]
    ax.annotate(f"{est}, no heading: wall contact at cruise +{rd(t, 1)} s\n(registered window +{a}…+{b} s: {'inside' if a <= t <= b else 'after it'})",
                (ct["y"], ct["x"]), xytext=(lx, ly), fontsize=8.6, color=INK, ha=ha_, va="center",
                arrowprops=dict(arrowstyle="-", color=C[est], lw=0.9, shrinkA=2, shrinkB=6))
ax.text(161, 0.9, f"with the camera heading: 9 flights (3 per estimator) overlap on the centreline, max |cross-track| "
        f"{rd(max(max(B2h[e]) for e in EST), 2)} m", ha="right", va="bottom", fontsize=8.6, color=INK)
ax.text(0.0, 1.02, f"Lateral (East) axis stretched {rd(STRETCH, 1)}× relative to the along-corridor axis. Walls at x = ±10 m; dotted = the "
        "9.58 m contact threshold.", transform=ax.transAxes, fontsize=8.6, color=INK2)
h = [Line2D([], [], color=C[e], lw=1.6, label=e) for e in EST] + \
    [Line2D([], [], color=INK2, lw=1.6, ls=(0, (5, 3)), label="no heading (1 flight each), to wall contact"),
     Line2D([], [], color=INK2, lw=1.0, ls="-", label="with the camera heading (3 flights each)"),
     Line2D([], [], color=INK2, ls="", marker="X", ms=8, mec=INK, label="wall contact")]
ax.legend(handles=h, loc="upper left", frameon=True, framealpha=0.95, edgecolor=GRID, ncol=2, fontsize=8.5)
check("no-heading wall contact EKF3 / UKF v2 / FGO v3 (s)", " / ".join(f"+{rd(CT2[e], 1)}" for e in EST), "+242.1 / +165.9 / +169.9", "numbers.md §15 contact rows")
check("with heading, B2 max cross-track per estimator EKF3 / UKF v2 / FGO v3 (m)", " / ".join(rng(B2h[e]) for e in EST),
      "0.24–0.33 / 0.22–0.25 / 0.03–0.39", "numbers.md §15 B2 row (EKF3 half) and re-flown rows")
dPB = max(abs(a - b) for e in EST for a, b in zip(XB2[e], B2h[e]))
check("plotted with-heading paths: max |x| in cruise vs scored B2, all 9 flights, |Δ| <= 0.05 m", "ok" if dPB <= 0.05 else f"{rd(dPB, 3)}", "ok",
      "curve source (dataflash SIM) vs closed_loop_*.json B2")
check("plotted no-heading paths end at the scored contact point, all 3, |Δ| <= 0.5 m", "ok" if max(PATHD.values()) <= 0.5 else
      f"{rd(max(PATHD.values()), 2)}", "ok", "curve source (dataflash SIM, cut at cruise start + contact time) vs closed_loop_*.json contact")
print(f"F2 stretch {rd(STRETCH, 3)}; path-B2 max |Δ| {rd(dPB, 4)} m; path end vs contact {PATHD}")
save(fig, "F2", "F2_heading_stops_sideways_drift",
     "The camera heading stops the sideways drift: without it every estimator flies into the west wall",
     f"Textured corridor at half real-time (RTF 0.5; {RTFX[0].lower() + RTFX[1:-1]}), each estimator flying the vehicle (closed loop); "
     f"true paths from the simulator, top-down, with the lateral (East) axis stretched {rd(STRETCH, 1)}× (stated on the figure). Colour = the "
     "flying estimator. Dashed: without a heading source (1 flight each), drawn up to the wall contact (X): EKF3 +242.1 s (after its "
     "pre-registered window), UKF v2 +165.9 s, FGO v3 +169.9 s. Solid: with the camera heading (3 flights each); all 9 stay within "
     "0.39 m of the centreline and pass B1–B5, so they overlap on the centreline at this scale. Heading-error statistics (B3) are in Table "
     "T4. Builds: the jitter-corrected UKF port (v2) and the final FGO (v3, flown with the OLD FGO priors); earlier builds are in A1. n = 1 "
     "per no-heading flight; closed-loop run-to-run variability is unmeasured; no comparison across real-time factors.",
     "paths: dataflash SIM of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_half_v3, "
     "cl_fgo_b_tex_r1–r3_half_v3; contact and B2: eval/results/closed_loop_<trial>.json",
     "§15 (contact rows, B2 row, re-flown B1/B2/B4 rows); claim 14")

# =============================================================================================== TABLE T4 closed loop per estimator
B3h = {e: [L(f"closed_loop_{t}.json")["B"]["B3"] for t in HALF[e][1]] for e in EST}
B4h = {e: [L(f"closed_loop_{t}.json")["B"]["B4"]["max_abs_lat_speed_mps"] for t in HALF[e][1]] for e in EST}
fmtb3 = lambda e: "; ".join(f"{rd(b['p95_deg'], 3)} / {rd(b['max_deg'], 3)} / {rd(b['mean_deg'], 3)}" for b in B3h[e])
check("closed loop half, with heading: flights passing B1–B5 (+S2)", " / ".join(f"{passh[e]}/3" for e in EST), "3/3 / 3/3 / 3/3", "numbers.md §15")
check("UKF v2 B2 r1/r2/r3 (m)", " / ".join(f"{rd(x, 3)}" for x in B2h["UKF"]), "0.231 / 0.253 / 0.219", "numbers.md §15 re-flown row")
check("FGO v3 B2 r1/r2/r3 (m)", " / ".join(f"{rd(x, 3)}" for x in B2h["FGO"]), "0.118 / 0.033 / 0.392", "numbers.md §15 re-flown row")
check("EKF3 half B2 range (m)", rng(B2h["EKF3"]), "0.24–0.33", "numbers.md §15 B2 row")
check("UKF v2 B3 p95/max/mean per flight (deg)", fmtb3("UKF"), "0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250", "numbers.md §15 re-flown B3 row")
check("FGO v3 B3 p95/max/mean per flight (deg)", fmtb3("FGO"), "0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187", "numbers.md §15 re-flown B3 row")
check("EKF3 half B3 p95 / max range (deg)", f"{rng([b['p95_deg'] for b in B3h['EKF3']])}/{rng([b['max_deg'] for b in B3h['EKF3']])}", "0.28–0.32/0.33–0.39", "numbers.md §15 B3 row")
check("no-heading wall contact EKF3 / UKF v2 / FGO v3 (s)", " / ".join(f"+{rd(CT2[e], 1)}" for e in EST), "+242.1 / +165.9 / +169.9", "numbers.md §15 contact rows")
check("FGO v3 r3 B4 (m/s)", f"{rd(B4h['FGO'][2], 3)}", "0.246", "numbers.md §15 re-flown row (closest call)")
rowsT4 = []
for e in EST:
    a, b = WIN[e]; t = CT2[e]
    rowsT4.append([HBUILD[e] + (" (unmodified)" if e == "EKF3" else ""),
                   f"+{rd(t, 1)} s; window [+{a}, +{b}] s: {'PASS' if a <= t <= b else 'MISS'}",
                   f"{passh[e]}/3 PASS",
                   " / ".join(f"{rd(x, 2)}" for x in B2h[e]),
                   " / ".join(f"{rd(x['p95_deg'], 2)}" for x in B3h[e]),
                   " / ".join(f"{rd(x['max_deg'], 2)}" for x in B3h[e]),
                   " / ".join(f"{rd(x, 3)}" for x in B4h[e])])
save_tab("T4", "T4_closed_loop", "Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle",
         "Without a heading source every flying estimator reaches the west wall; with the camera heading every flight passes B1–B5 (+S2), "
         "with the per-flight cross-track, heading-error and lateral-speed values shown (flights 1 / 2 / 3). No ordering between the "
         "estimators is claimed.",
         ["flying estimator (build)", "no heading: wall contact (cruise +)", "with heading: flights passing B1–B5", "max |cross-track| in cruise, B2 (m)",
          "heading error p95, B3 (°)", "heading error max, B3 (°)", "max lateral speed, B4 (m/s)"],
         rowsT4, [26, 34, 16, 18, 16, 16, 18],
         "eval/results/closed_loop_cl_a_tex_half.json, closed_loop_cl_bcpp_tex_r{1,2,3}_half.json, closed_loop_cl_ukf_{a,b}_tex*_half_v2.json, "
         "closed_loop_cl_fgo_{a,b}_tex*_half_v3.json", "§15 (contact rows, B1–B5 counts, B2, B3, B4 re-flown rows); claim 14",
         notes=["Contact windows are pre-registered per estimator (EKF3 [+155, +215] s, UKF [+146, +218] s, FGO [+145, +196] s); EKF3's "
                "+242.1 s at half real-time (RTF 0.5) is after its registered window. " + RTFX + " n = 1 per no-heading flight; closed-loop "
                "run-to-run variability is "
                "unmeasured; no comparison across real-time factors. Bands: B3 max ≤ 2°; B4 ≤ 0.25 m/s (the final FGO's flight 3, 0.246 m/s, is the "
                "closest call: a start-of-climb flow-validity event, a shared limitation of the sensor pipeline). Heading error B3 mean per flight: " +
                "; ".join(f"{e} " + " / ".join(f"{rd(x['mean_deg'], 2)}" for x in B3h[e]) for e in EST) + " °. Every flown FGO "
                "flight used the OLD FGO priors (initial yaw σ 1e-3 rad). Earlier builds: Appendix A1."], order=40)

# =============================================================================================== TABLE T2 accuracy without / with heading (was F3)
dec = L("phase5_analysis.json")["decomposition"]
hd = {a: [abs(dec[f"fwdc_tex_r{r}"][a]["xtrack_head_m"]) for r in (1, 2, 3)] for a in ("EKF3", "UKF_baseline", "FGO_baseline", "UKF_heading", "FGO_heading")}
nh = [x for a in ("EKF3", "UKF_baseline", "FGO_baseline") for x in hd[a]]
# Phase 5 decomposition: restated in numbers.md §6.3 (ruling 2026-10-16 on the open items, 6: phase5_analysis.json is the phase5-stage
# output of the FGO-only re-run, written 2026-10-10 14:08 after that run's phase4 stage and committed in 819caab).
check("Phase 5 |heading-driven cross-track| fwdc_tex r1/r2/r3, EKF3 | UKF | FGO without heading (m)",
      " | ".join(" / ".join(rd(x, 3) for x in hd[a]) for a in ("EKF3", "UKF_baseline", "FGO_baseline")),
      "36.276 / 29.508 / 36.070 | 45.980 / 3.171 / 46.120 | 41.002 / 8.630 / 42.121", "numbers.md §6.3 Phase 5 decomposition row")
check("Phase 5 |heading-driven cross-track| fwdc_tex r1/r2/r3, UKF | FGO with heading (m)",
      " | ".join(" / ".join(rd(x, 3) for x in hd[a]) for a in ("UKF_heading", "FGO_heading")),
      "0.065 / 0.064 / 0.068 | 0.065 / 0.063 / 0.067", "numbers.md §6.3 Phase 5 decomposition row")
check("dsn_tex median r1–r9 EKF3 / UKF / FGO (m)", " / ".join(f2(med[e]) for e in EST), "4.10 / 5.13 / 4.46", "numbers.md §6.1 standing row")
check("dsn_tex mean r1–r3 EKF3 / UKF / FGO (m)", " / ".join(f2(np.mean([v for i, v in DSN[e] if i <= 3])) for e in EST), "4.00 / 3.59 / 3.44", "numbers.md §6.1; claim 1a")
check("dsn_tex UKF r1–r9 range (m)", rng([v for _, v in DSN["UKF"]]), "1.17–5.85", "numbers.md §6.1 D15 wording row")
check("confirmatory mean d, CI (m)", f"{rd(pt['mean_d_m'], 3)} [{rd(pt['t95_ci_m'][0], 3)}, {rd(pt['t95_ci_m'][1], 3)}]", "-0.021 [-0.989, 0.947]", "numbers.md §6.1")
check("no heading EKF3 fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["EKF3"]) for b in CAMB), "4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08", "numbers.md §6.4")
check("no heading FGO fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["FGO_baseline"]) for b in CAMB), "4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74", "numbers.md §6.4")
check("no heading UKF fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["UKF_baseline"]) for b in CAMB), "4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82", "numbers.md §6.4")
check("with heading UKF fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["UKF_heading"]) for b in CAMB), "0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25", "numbers.md §6.6")
check("with heading FGO fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["FGO_heading"]) for b in CAMB), "0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22", "numbers.md §6.6")
mism = 0
for ds, r in CAMB:
    a = L(f"phase4_{ds}_arms.json")[f"{ds}_tex_r{r}"]
    for arm in ("UKF_heading", "FGO_heading"):
        try:
            mism += abs(a[arm]["evo"]["ate_a_cruise"]["+0.00"] - P4[(ds, r)][arm]) > 1e-6
        except (KeyError, TypeError):
            pass
check("phase4 evo vs arms json agreement (mismatches)", mism, 0, "phase4_*_evo.json vs phase4_*_arms.json")
BK = {"EKF3": "EKF3", "UKF": "UKF_baseline", "FGO": "FGO_baseline"}
cam = lambda e, ds, key: " / ".join(f2(P4[(ds, r)][key]) for r in (1, 2, 3))
rowsT2 = []
for e in EST:
    v = [x for _, x in DSN[e]]
    rowsT2.append([e, f"{rd(med[e], 2)} ({rng(v)})", cam(e, "fwdc", BK[e]), cam(e, "fwdplainc", BK[e]),
                   "no offline heading arm" if e == "EKF3" else cam(e, "fwdc", f"{e}_heading"),
                   "no offline heading arm" if e == "EKF3" else cam(e, "fwdplainc", f"{e}_heading") + " *",
                   " / ".join(f"{rd(x, 1)}" for x in hd[BK[e]]) + " m; " +
                   ("—" if e == "EKF3" else " / ".join(f"{rd(100 * x, 1)}" for x in hd[f"{e}_heading"]) + " cm")])
save_tab("T2", "T2_accuracy_heading", "Position error without and with the camera heading (textured floor)",
         "Without a heading source all three drift by metres and no ordering is claimed; with the camera heading the UKF and the FGO "
         "stay within 0.25 m, the FGO lower on all 6 bags (C0). The Phase 5 decomposition attributes metres of cross-track to each "
         "estimator's own heading error without the heading, and centimetres with it.",
         ["estimator", "no heading: dsn_tex, 9 flights, median (range) (m)", "no heading: fwdc, flights 1 / 2 / 3 (m)",
          "no heading: fwdplainc, flights 1 / 2 / 3 (m)", "with heading: fwdc, flights 1 / 2 / 3 (m)",
          "with heading: fwdplainc, flights 1 / 2 / 3 (m)",
          "Phase 5, fwdc textured floor, flights 1 / 2 / 3: heading-driven end-of-cruise cross-track, without; with heading"],
         rowsT2, [12, 24, 20, 22, 20, 22, 34],
         "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json; phase4_{fwdc,fwdplainc}_evo.json, "
         "cross-checked against phase4_*_arms.json; phase5_analysis.json (decomposition, xtrack_head_m)",
         "§6.1, §6.3 (Phase 5 decomposition), §6.4, §6.6; claims 1a, 1b, 2, 5, 7",
         notes=["Metric: evo -a (cruise), which aligns away a constant yaw offset (so metres, not tens of metres). No ordering is claimed "
                f"without the heading: the pre-registered EKF3 − FGO test on flights 4–10 gives '{pt['verdict']}' (mean d {rd(pt['mean_d_m'], 3, sign=True)} m, "
                f"95% CI [{rd(pt['t95_ci_m'][0], 3, sign=True)}, {rd(pt['t95_ci_m'][1], 3, sign=True)}] m); the former 'EKF3 beats the FGO' is WITHDRAWN; the UKF "
                "medians are descriptive (n = 9). EKF3 has no offline heading arm (by ruling, it is the fixed no-heading baseline offline); it flies "
                "with one (T4).",
                "* Plain walls over the checkerboard floor: the heading FAILED Phase 3 validation there, so no heading benefit is claimed "
                "(conditional on the initial yaw σ). C0 (FGO lower than the UKF with heading) holds on 6/6, margin "
                "0.03–0.06 m on plain walls.",
                "Phase 5 decomposition: |cross-track| at the end of cruise driven by the estimator's own heading error, from the Phase 5 "
                "analysis of the FGO-only re-run (the final estimator builds)."],
         fs=7.6, order=20)

# =============================================================================================== TABLE T3 blank floor (was F4)
check("UKF +10/+30/+60 s ranges (m)", f"{rng(BLANK['UKF'][:, 0], 1)} / {rng(BLANK['UKF'][:, 1], 1)} / {rng(BLANK['UKF'][:, 2], 0)}", "6.4–8.2 / 27.3–36.5 / 60–108", "numbers.md §6.2")
check("FGO +10/+30/+60 s ranges (m)", f"{rng(BLANK['FGO'][:, 0], 1)} / {rng(BLANK['FGO'][:, 1], 1)} / {rng(BLANK['FGO'][:, 2], 0)}", "6.4–8.2 / 28.0–37.0 / 154–204", "numbers.md §6.2")
check("n flights UKF / FGO", f"{len(BLANK['UKF'])}/{len(BLANK['FGO'])}", "11/11", "numbers.md §6.2")
check("end of cruise UKF / FGO (km) †", f"{rng(BLANK['UKF'][:, 3] / 1e3, 0)} / {rng(BLANK['FGO'][:, 3] / 1e3, 0)}", "29–40 / 22–41", "numbers.md §6.2")
check("EKF3 invalid, s of cruise, all 14 blank", rng(EK_INV, 0), "301–310", "numbers.md §6.2")
nvalid = [v["valid_frames_in_cruise"] for k, v in bb.items() if "blank" in k]
check("valid airborne flow frames in cruise, all blank bags", f"max {max(nvalid)} over {len(nvalid)}", "max 0 over 14", "numbers.md §6.2 ('0', all 14 blank bags)")
rowsT3 = [[e, f"{len(BLANK[e])}", f"{rng(BLANK[e][:, 0], 1)} (median {rd(np.median(BLANK[e][:, 0]), 1)})",
           f"{rng(BLANK[e][:, 1], 1)} (median {rd(np.median(BLANK[e][:, 1]), 1)})", f"{rng(BLANK[e][:, 2], 0)} (median {rd(np.median(BLANK[e][:, 2]), 0)}) †",
           f"{rng(BLANK[e][:, 3] / 1e3, 0)} km †"] for e in ("UKF", "FGO")]
rowsT3.insert(0, ["EKF3", f"{len(EK_INV)}", "invalid", "invalid", "invalid", f"invalid (for {rng(EK_INV, 0)} s of cruise)"])
save_tab("T3", "T3_blank_floor", "Blank floor: position error after the loss of flow aiding",
         "On a blank floor nothing bounds position: the UKF and the FGO dead-reckon away to km-scale errors by the end of the cruise, and "
         "EKF3 flags its own position invalid, so it has no scored error. Behaviour under total loss of flow aiding, not accuracy.",
         ["estimator", "flights", "+10 s (m)", "+30 s (m)", "+60 s (m)", "end of cruise"], rowsT3, [14, 10, 26, 26, 26, 30],
         "eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60 s and end; EKF3_invalid_period; valid_frames_in_cruise)",
         "§6.2; claim 10",
         notes=["Error magnitude = hypot(along, cross) at each time after the flow-loss point; UKF and FGO baselines (no heading), 11 "
                "flights each (dsn, p1c, fwdc and fwdplainc blank). † runaway magnitudes: evidence of divergence with its order of "
                "magnitude, not bit-reproducible values.",
                f"EKF3 'invalid': on all {len(EK_INV)} blank flights there are {max(nvalid)} valid airborne flow frames in the cruise, so flow "
                f"aiding never starts; EKF3 flags its position invalid from take-off ({rng(EK_INV, 0)} s of cruise) and outputs exactly the "
                "origin, which is not scored (evaluation rule). This is a declared failure, not a small error.",
                "With the camera heading the yaw is held but position still is not (+60 s: UKF 40–89 m, FGO 135–190 m †; quoted from "
                "the results record, not re-derived here)."], order=30)

# =============================================================================================== FIG 5 T
fig, ax = plt.subplots(figsize=(12.5, 6.0)); xc = np.arange(4); offs = dict(zip(TRK, np.linspace(-0.16, 0.16, 5)))
TT = {}
for n in TRK:
    est, kind = TSTY[n]
    per = np.array([[1e2 * L(f"expT/T_{c}_r{r}.json")["tracks"][n]["horiz_err_m"]["rmse"] for r in (1, 2, 3)] for c in TCOND])
    mn = np.array([1e2 * agg["conditions"][c]["mean_rmse_m"][n] for c in TCOND]); TT[n] = mn
    x = xc + offs[n]
    ax.plot(x, mn, color=C[est], ls="-" if kind == "live" else "--", lw=1.4, marker=MK[est], ms=6,
            mfc=C[est] if kind == "live" else SURF, mec=C[est], mew=1.2, label=TSHORT[n] + " (mean of 3)", zorder=3)
    for j in range(4):
        ax.scatter([x[j]] * 3, per[j], s=10, marker=MK[est], color=C[est] if kind == "live" else SURF, edgecolor=C[est], lw=0.6, zorder=2, alpha=0.8)
gm = [agg["conditions"][c]["gap_length_median_s"] for c in TCOND]
ax.set_xticks(xc); ax.set_xticklabels([f"{TLAB[c]}\n(median gap {rd(g, 1)} s)" for c, g in zip(TCOND, gm)])
ax.set_xlabel("tags available (condition A → D)"); ax.set_ylabel("horizontal RMSE over the 5 laps (cm)")
ax.set_ylim(0, 15.5); ax.set_xlim(-0.45, 3.45)
ax.legend(loc="upper left", frameon=False, ncol=2)
h1 = agg["H-T1 (FGO live -> whole-flight batch)"]; p2 = agg["P-T2 (UKF live -> RTS)"]
fig.text(0.98, -0.03, f"hindsight gain (median per gap): FGO batch vs FGO live {', '.join(f'{rd(100 * h1['median_gain_m'][c], 1)}' for c in TCOND)} cm "
        f"(H-T1 {'PASS' if h1['PASS'] else 'FAIL'}, grows with the gap)\nRTS-UKF vs UKF live {', '.join(f'{rd(100 * p2['median_gain_m'][c], 1, sign=True)}' for c in TCOND)} cm "
        f"(P-T2 {'PASS' if p2['PASS'] else 'FAIL'}, not increasing)", ha="right", va="top", fontsize=9, color=INK2)
exp10 = {"A": "0.039 0.037 0.020 0.014 0.010", "B": "0.055 0.061 0.026 0.031 0.015", "C": "0.074 0.076 0.054 0.039 0.019", "D": "0.096 0.131 0.083 0.109 0.028"}
for c in TCOND:
    mr = agg["conditions"][c]["mean_rmse_m"]
    check(f"T {TLAB[c]}: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m)", " ".join(f"{rd(mr[k], 3)}" for k in TRK), exp10[c], "numbers.md §16.1 table")
check("T median gaps A–D (s)", " / ".join(f"{rd(g, 1)}" for g in gm), "4.3 / 10.1 / 22.0 / 46.3", "numbers.md §16.1 table header")
check("tags per lap in B", str(L("expT/T_B_r1.json")["gates"]["laps_ids"][0]), "[0, 1, 2, 3]", "T_B_r1.json gates (4 corner tags)")
check("H-T1 median gain A–D (m), rho, PASS", " / ".join(f"{rd(h1['median_gain_m'][c], 3)}" for c in TCOND) + f" {rd(h1['spearman_rho'], 2, sign=True)} {h1['PASS']}",
      "0.010 / 0.011 / 0.023 / 0.052 +0.30 True", "numbers.md §16.1")
check("P-T2 gain A–D (m), PASS", " / ".join(f"{rd(p2['median_gain_m'][c], 3, sign=True)}" for c in TCOND) + f" {p2['PASS']}", "+0.020 / +0.032 / +0.037 / +0.029 False", "numbers.md §16.1")
P3S = " / ".join(rd(agg["P-T3 live ratio max/min"]["by_condition"][c], 2) for c in TCOND)   # was a hard-coded caption literal (D 1.58, double rounding)
check("P-T3 live max/min ratio A / B / C / D", P3S, "1.97 / 2.36 / 1.42 / 1.57", "numbers.md §16.1 P-T3")
save(fig, "F5", "F5_T_tags_known_positions",
     "Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm",
     "Experiment T (the tag room, 5 laps of a 6 m square, open loop on simulator truth): horizontal RMSE in the world frame, no alignment, "
     "against the tags sent (A all 8, B the 4 corners, C 2 diagonal, D 1 tag; median gap between fixes 4.3 / 10.1 / 22.0 / 46.3 s). Solid, "
     "filled = live; dashed, open = hindsight (the FGO whole-flight batch and the RTS-smoothed UKF); small marks = each of 3 flights, line = "
     "their mean. Live errors grow from 2–4 cm to 8–13 cm as tags thin out; no live ordering is claimed (in D the FGO live 8.3 cm against "
     "EKF3 9.6 cm is descriptive, n = 3). P-T3 FAILS (live max/min " + P3S + "). The FGO batch stays at " + rng([100 * agg["conditions"][c]["mean_rmse_m"]["FGO hindsight (whole-flight batch)"] for c in TCOND], 1) + " cm; "
     "its hindsight gain grows with the gap (H-T1 PASS), the RTS-UKF's does not (P-T2 FAIL), and the batch-to-RTS ratio is 1.31–3.89 (P-T4 "
     "FAIL). Same tag fixes for every estimator.",
     "eval/results/expT/T_{A,B,C,D}_r{1,2,3}.json (tracks.*.horiz_err_m.rmse), expT/t_aggregate.json",
     "§16.1 table and bullets (H-T1, P-T2, P-T3, P-T4, condition D); claims 17, 18")

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
fig, ax = plt.subplots(figsize=(15.5, 6.4))
ax.axvspan(0, ton - toff, color="#f2f2f2", zorder=0)
t_far = mk["OUTBACK BACK START"] - 3.0 - toff; t_back = mk["OUTBACK BACK START"] - toff; t_on = ton - toff
for tv in (0.0, t_far, t_back, t_on):
    ax.axvline(tv, color=TRUTH, lw=0.9, ls=":", zorder=1)
EV = [(0.0, "GNSS OFF\n(entrance, y = 20 m)", "center"), (t_far, f"far end reached,\n~{rd(t_far, 0)} s (y = 50 m,\n30 m inside); 3 s hold", "right"),
      (t_back, f"return starts, {rd(t_back, 0)} s:\nreverse at the same\nheading (no yaw turn)", "left"), (t_on, f"GNSS ON at {rd(t_on, 0)} s\n(re-crossing the entrance)", "center")]
for tv, txt, al in EV:
    ax.text(tv + (-1.0 if al == "right" else 1.0 if al == "left" else 0.0), 4.62, txt, ha=al, va="top", fontsize=8.4, color=INK2,
            bbox=dict(boxstyle="round,pad=0.25", fc="#f2f2f2" if 0 < tv < t_on else SURF, ec="none"))
ax.text(-38, 4.62, "outdoors,\nGNSS on", ha="left", va="top", fontsize=8.4, color=INK2)
ax.text(t_on + 29, 4.62, "outdoors,\nGNSS on", ha="right", va="top", fontsize=8.4, color=INK2)
ax.text(30, 2.9, f"indoors, GNSS off ({rd(t_on, 0)} s):\nIMU + downward flow + downward LiDAR only", ha="center", va="bottom", fontsize=8.6, color=INK2)
rm_ind = {}
for n, Tk in tracks.items():
    est, kind = TSTY[n]; w = (Tk[:, 0] > toff - 40) & (Tk[:, 0] < ton + 30)
    e = np.hypot(Tk[w, 1] - np.interp(Tk[w, 0], G[:, 0], G[:, 1]), Tk[w, 2] - np.interp(Tk[w, 0], G[:, 0], G[:, 2]))
    ax.plot(Tk[w, 0] - toff, e, color=C[est], ls="-" if kind == "live" else "--", lw=1.2, label=TSHORT[n], zorder=3)
    wi = (Tk[:, 0] >= toff) & (Tk[:, 0] <= ton)
    ei = np.hypot(Tk[wi, 1] - np.interp(Tk[wi, 0], G[:, 0], G[:, 1]), Tk[wi, 2] - np.interp(Tk[wi, 0], G[:, 0], G[:, 2]))
    rm_ind[n] = float(np.sqrt(np.mean(ei ** 2)))
ax.set_xlabel("time from GNSS OFF at the entrance (s)"); ax.set_ylabel("horizontal error, world frame, no alignment (m)")
ax.set_xlim(-40, t_on + 30); ax.set_ylim(0, 4.7)
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.80), fontsize=8.6, frameon=True, framealpha=0.95, edgecolor=GRID)
jump = o["tracks"]["EKF3 live"]["max_step_after_return_m"]
_k = tracks["EKF3 live"]; _w = (_k[:, 0] > ton) & (_k[:, 0] < ton + 30)
_ek = np.hypot(_k[_w, 1] - np.interp(_k[_w, 0], G[:, 0], G[:, 1]), _k[_w, 2] - np.interp(_k[_w, 0], G[:, 0], G[:, 2])); _i = int(np.argmax(_ek))
ax.annotate(f"EKF3 resets to GNSS on return:\n{rd(jump, 2)} m jump (every flight)", (_k[_w, 0][_i] - toff + 0.5, _ek[_i] - 0.6), xytext=(t_on + 8, 2.4), fontsize=8.5,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7))
jumps = [L(f"expO/{t}.json")["tracks"]["EKF3 live"]["max_step_after_return_m"] for t in OFL]
check("O EKF3 reset jump (m)", rng(jumps), "4.10–4.10", "numbers.md §16.2 ('4.10 m, every flight')")
check("O indoor duration (s)", f"{rd(t_on, 0)}", "123", "numbers.md §16.2 heading ('123 s, GNSS off')")
dO = max(abs(rm_ind[n] - o["tracks"][n]["indoor_rmse_m"]) for n in TRK)
check("O_r1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m", "ok" if dO <= 0.05 else f"{rd(dO, 3)}", "ok", "curve source vs scorer")
check("O_r1 bag has no tag topics", len(tag_topics), 0, "O design: no tags in outdoor_indoor.sdf")
save(fig, "F6", "F6_O_outdoor_indoor",
     "Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m",
     "Experiment O (outdoor → indoor → outdoor, open loop on simulator truth), flight 1: horizontal error against time in the world "
     "frame, no alignment. Indoor sensor set, the same for all three estimators: IMU (accelerometer and gyro), downward optical flow and "
     "the downward LiDAR rangefinder only; no GNSS (switched off at the entrance), no compass, no forward-camera heading (descoped) and no "
     f"tags (none in the world). Route events (dotted): GNSS OFF at the entrance (0 s); the far end, 30 m inside, reached at ~{rd(t_far, 0)} s "
     f"and held 3 s; the return in reverse at the same heading (no yaw turn) from {rd(t_back, 0)} s; GNSS ON on re-crossing the entrance at "
     f"{rd(t_on, 0)} s. EKF3 resets to GNSS on return with a 4.10 m jump (every flight). Solid = live, dashed = hindsight. The per-flight "
     "indoor RMSE of all three flights is in Table T6 (H-O1 PASS 3/3; H-O2 FAIL; P-O3 PASS).",
     "eval/results/expO/O_r1.json (markers_bag_s, max_step_after_return_m), O_r2.json, O_r3b.json; curves: O_r1 room_ukf/, room_fgo/ TUMs, "
     "dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref (clock map); design: METHODOLOGY 'Experiment O: pre-registration', "
     "sim/worlds/outdoor_indoor.sdf, fly_trial.py outback(), o_gnss.parm", "§16.2 table and bullets; claims 19–22")

# =============================================================================================== TABLE T6 O indoor RMSE per flight
exO = {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89", "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}
for n in TRK:
    check(f"O indoor RMSE {TSHORT[n]} (m)", rng(OI[n]), exO[n], "numbers.md §16.2 table")
check("O H-O2 live max/min ratio; largest = EKF3 in every flight", f"{rng(ho2)}; {ho2_max_is_ekf3}", "1.71–1.84; True", "numbers.md §16.2 H-O2 bullet")
h1ok = all(OI["FGO hindsight (whole-flight batch)"][i] < min(OI["EKF3 live"][i], OI["UKF live"][i]) for i in range(3))
check("H-O1: FGO batch below both filters' live tracks, flights", f"{sum(OI['FGO hindsight (whole-flight batch)'][i] < min(OI['EKF3 live'][i], OI['UKF live'][i]) for i in range(3))}/3",
      "3/3", "numbers.md §16.2 (H-O1 PASS 3/3)")
rowsT6 = [[TSHORT[n], "live" if TSTY[n][1] == "live" else "hindsight"] + [f"{rd(v, 2)}" for v in OI[n]] + [rng(OI[n])] for n in TRK]
rowsT6.append(["live max ÷ min (H-O2)", "—"] + [f"{rd(v, 2)}" for v in ho2] + [rng(ho2)])
save_tab("T6", "T6_O_indoor_rmse", "Experiment O: indoor horizontal RMSE per flight (123 s, GNSS off)",
         "Indoors without GNSS the live errors are 0.8–1.4 m and not similar across estimators (EKF3 largest in every flight, H-O2 FAIL); "
         "the two hindsight tracks agree at 0.58–0.60 m (P-O3 PASS).",
         ["track", "kind", "flight 1 (m)", "flight 2 (m)", "flight 3 (m)", "range (m)"], rowsT6, [36, 14, 14, 14, 14, 18],
         "eval/results/expO/O_r1.json, O_r2.json, O_r3b.json (tracks.*.indoor_rmse_m)", "§16.2 table and bullets; claims 19–22",
         notes=["World frame, no alignment; same GNSS samples for every estimator; indoor sensor set: IMU, downward flow and downward LiDAR "
                "only. H-O1 PASS 3/3 (the FGO batch is below both filters' live tracks); P-O3 PASS (batch FGO against RTS-UKF within 1–5%, "
                "Table T8). The former 'FGO batch ~2× better than the RTS-UKF' is WITHDRAWN (a noise-model artefact)."], order=60)

# =============================================================================================== FIG 7 L
fig, axs = plt.subplots(1, 2, figsize=(14.5, 5.6), sharey=True)
for ax, mode, lab in ((axs[0], "lc", "with loop closure (tags re-identified)"), (axs[1], "nolc", "without loop closure")):
    for kind in ("live", "hindsight"):
        for r, tk in enumerate(LL[(mode, kind)]):
            v = np.array(tk["per_lap_rmse_m"]) * 100
            ax.plot(range(1, 6), v, color=C["FGO"], ls="-" if kind == "live" else "--", marker=MK["FGO"], ms=5,
                    mfc=C["FGO"] if kind == "live" else SURF, mec=C["FGO"], lw=1.1,
                    label=f"{'live (fixed-lag)' if kind == 'live' else 'hindsight (full iSAM2 estimate)'}" if r == 0 else None)
    ax.set_title(f"keyframe FGO, {lab}: flights 1–3", loc="left", fontsize=10)
    ax.set_xticks(range(1, 6)); ax.set_xlabel("lap of the 6 m square")
    ax.legend(loc="upper left", frameon=False)
axs[0].set_ylabel("horizontal RMSE per lap (cm)"); axs[0].set_ylim(0, None)
lc5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("lc", "live")]]
nl5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("nolc", "live")]]
axs[0].text(5, axs[0].get_ylim()[1] * 0.55, f"live lap 5 ÷ lap 1: {rng(lc5)}\n(error falls after lap 1)", ha="right", fontsize=9)
axs[1].text(5, axs[0].get_ylim()[1] * 0.08, f"live lap 5 ÷ lap 1: {rng(nl5, 1)}\n(error grows over the laps)", ha="right", fontsize=9)
check("L lc live overall (m)", rng([t["rmse_m"] for t in LL[("lc", "live")]], 3), "0.049–0.076", "numbers.md §16.3")
check("L lc hindsight overall (m)", rng([t["rmse_m"] for t in LL[("lc", "hindsight")]], 3), "0.017–0.027", "numbers.md §16.3")
check("L nolc live overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "live")]], 3), "0.263–0.361", "numbers.md §16.3")
check("L nolc hindsight overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "hindsight")]], 3), "0.221–0.266", "numbers.md §16.3")
check("L lap5/lap1 lc live; nolc live", rng(lc5) + "; " + rng(nl5, 1), "0.16–0.43; 2.9–4.5", "numbers.md §16.3")
save(fig, "F7", "F7_L_loop_closure",
     "Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps",
     "Experiment L: the keyframe FGO with AprilTags at UNKNOWN positions (each tag a landmark), flights 1–3, horizontal RMSE per 6 m lap in "
     f"the first tag's frame, one shared linear axis. Left: with loop closure the live error falls after lap 1 (lap 5 ÷ lap 1 {rng(lc5)}; "
     f"overall {rng([t['rmse_m'] * 100 for t in LL[('lc', 'live')]], 1)} cm live, {rng([t['rmse_m'] * 100 for t in LL[('lc', 'hindsight')]], 1)} cm "
     f"hindsight). Right: without re-identification it grows {rng(nl5, 1)}× over five laps (overall "
     f"{rng([t['rmse_m'] * 100 for t in LL[('nolc', 'live')]], 1)} cm live). H-L1, H-L2, H-L3 and P-L4 PASS 3/3. This is an FGO capability, not an FGO-against-filter result (the filters have no "
     "loop-closure equivalent); one estimator, so one colour, with live solid/filled and hindsight dashed/open. V-L is not re-scorable on the "
     "corrected FGO (its labels were never recorded).",
     "eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)", "§16.3 table and bullets; claims 23, 24")

# =============================================================================================== TABLE T5 H tag-loss drift (was F8)
LOSS = ["5 s hover", "15 s hover", "30 s hover", "~7 s during a move"]
FLY = {"EKF3": (S1 + S1F, "EKF3", "EKF3 (S1 + S1 far, 6 flights)"), "UKF": (S2V, "UKF_port", "UKF v2 port (S2v2, 3 flights)"),
       "FGO": (S3V, "FGO_flying", "FGO v3 node (S3v2, 3 flights; OLD priors)")}
BAND = {"EKF3": [50, 100, 200, 150], "FGO": [50, 100, 200, 150], "UKF": [100, 200, 400, 300]}
DR = {(est, li): drifts(FLY[est][0], FLY[est][1])[li] for est in EST for li in range(4)}
dd_ = drifts(S1, "EKF3"); check("S1 EKF3 flying drift 5/15/30/move (mm, effective)", " | ".join(rng(x, 0) for x in dd_), "13–27 | 6–25 | 3–11 | 7–31", "numbers.md §17 table")
for met, exp in (("eff", "15/12/3/4 | 17/12/26/20 | 11/17/11/13"), ("end", "15/10/3/7 | 19/12/26/23 | 12/17/11/16")):
    df_ = drifts(S1F, "EKF3", met)
    check(f"S1 far EKF3 flying drift r1 | r2 | r3b, 5 s/15 s/30 s/move (mm, {'effective' if met == 'eff' else 'end of loss'})",
          " | ".join("/".join(rd(df_[li][i], 0) for li in range(4)) for i in range(3)), exp, "numbers.md §17 S1 far row (ruling 2026-10-16, open items 7)")
for nm, trs, key, exp in (("S2v2 UKF", S2V, "UKF_port", "5/7/8 | 19/7/26 | 6/10/10 | 26/4/5"), ("S3v2 FGO", S3V, "FGO_flying", "13/20/17 | 7/25/27 | 22/15/9 | 17/11/18")):
    de = drifts(trs, key, "end")
    check(f"{nm} flying end-of-loss drift r1/r2/r3 (mm)", " | ".join("/".join(f"{rd(x, 0)}" for x in row) for row in de), exp, "numbers.md §17.1 table")
dmax = max(abs(a - b) for trs, key in ((S1 + S1F, "EKF3"), (S2V, "UKF_port"), (S3V, "FGO_flying"))
           for ra, rb in zip(drifts(trs, key), drifts(trs, key, "end")) for a, b in zip(ra, rb))
check("effective vs end-of-loss drift, max |Δ| at printed (mm) precision", f"≤ {rd(dmax, 0)} mm", "≤ 5 mm",
      f"numbers.md §17.1 ('differ by ≤ 5 mm'); unrounded {rd(dmax, 1)} mm (S2v2 r1, move loss)")
inband = all(v <= BAND[e][li] for (e, li), d in DR.items() for v in d)
check("every drift inside its pre-registered band (P-H5)", inband, True, "numbers.md §17, §17.1 (every band PASSES)")
LK = {e: [bool(lo[FLY[e][1]]["lockout"]) for t in FLY[e][0] for lo in HJ(t)["losses"]] for e in EST}
check("lockouts in any loss (flying estimators)", sum(sum(v) for v in LK.values()), 0, "numbers.md §17 (P-H7 PASS)")
rowsT5 = [[f"tag lost: {LOSS[li]}"] + [f"{rd(max(DR[(e, li)]), 0)} / {BAND[e][li]} (range {rng(DR[(e, li)], 0)}; n {len(DR[(e, li)])})" for e in EST]
          for li in range(4)]
rowsT5.append(["lockouts (losses with a lockout / losses)"] + [f"{sum(LK[e])} / {len(LK[e])}" for e in EST])
rowsT5.append(["P-H5 drift bands"] + ["every loss inside its band" if all(v <= BAND[e][li] for li in range(4) for v in DR[(e, li)]) else "band FAIL"
                                       for e in EST])
save_tab("T5", "T5_H_tag_loss_drift", "Experiment H: drift while the wall tag is hidden, flying estimators",
         "Holding on a wall tag, every flying estimator drifts at most about 3 cm while the tag is hidden, inside every pre-registered "
         "band, and none locks out; each cell gives the maximum drift / its band in mm, with the range over the losses. The comparative "
         "criteria (H-H2, P-H3, H-H4) FAIL on these final-build sets, identical to the original-build verdicts (superseded builds: "
         "Table A2), so no ordering is claimed. " + PRIORS,
         ["tag-loss condition", FLY["EKF3"][2] + ": max / band (mm)", FLY["UKF"][2] + ": max / band (mm)", FLY["FGO"][2] + ": max / band (mm)"],
         rowsT5, [28, 40, 40, 40],
         "eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s3v2_r*.json (losses[*].<est>.effective.drift_m, drift_end_m, lockout)",
         "§17 (S1 table, S1 far row, P-H5, P-H7), §17.1 (S2v2, S3v2), §17.2; claims 25, 26",
         notes=["Drift = the EFFECTIVE metric (last fix → first returning fix); the end-of-loss metric differs by ≤ 5 mm "
                f"(unrounded {rd(dmax, 1)} mm). Pre-registered bands (P-H5): EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm, UKF ≤ 100 / 200 / 400 / "
                "300 mm. P-H5 and P-H7 PASS. The comparative criteria (H-H2, P-H3, H-H4) are reported on these final-build sets (primary); "
                "their verdicts are identical to the original-build verdicts (all FAIL). Each estimator flew its own flights: pairing by run "
                "index, not trajectory.",
                "EKF3 = S1 near spawn (3 flights) and S1 far spawn (3 flights). UKF = the jitter-corrected port (S2v2); FGO = the final "
                "C++ node (S3v2, flown with the OLD FGO priors)."],
         order=50)

# =============================================================================================== APPENDIX tables
def setb(trs):
    B = [L(f"closed_loop_{t}.json")["B"] for t in trs]
    r_ = lambda f: f"{rd(min(f(b) for b in B), 2)}–{rd(max(f(b) for b in B), 2)}"
    js = [L(f"closed_loop_{t}.json") for t in trs]
    fails = [f"flight {i + 1} {k}" for i, b in enumerate(B) for k in ("B1", "B2", "B3", "B4", "B5") if not b[k]["pass"]]
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
    ("EKF3, real time (RTF 1.0)", "unmodified; Python bridge", "—", *setb([f"cl_b_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, real time (RTF 1.0)", "unmodified; C++ bridge", seta("cl_a_tex", WIN["EKF3"]), *setb([f"cl_bcpp_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, half real-time (RTF 0.5)", "unmodified; C++ bridge", seta("cl_a_tex_half", WIN["EKF3"]), *setb([f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, real time (RTF 1.0)", "v1 port (pre-jitter fix)", seta("cl_ukf_a_tex", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}" for i in (1, 2, 3)])),
    ("UKF, half real-time (RTF 0.5)", "v1 port (pre-jitter fix)", seta("cl_ukf_a_tex_half", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, half real-time (RTF 0.5)", "v2 port (jitter-corrected) FINAL", seta("cl_ukf_a_tex_half_v2", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "original (old noise model), hard gate", seta("cl_fgo_a_tex_half", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "original, robust heading weight", "not flown", *setb([f"cl_fgo_b_robust_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "v2: noise fix only (ABLATION)", seta("cl_fgo_a_tex_half_v2", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO, half real-time (RTF 0.5)", "v3: noise fix + gated yaw cap FINAL", seta("cl_fgo_a_tex_half_v3", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)])),
]
check("EKF3 half contact MISS", rowsA[2][2].split(",")[1].strip().split()[0], "MISS", "numbers.md §15 (D21)")
check("UKF v1 half heading set", rowsA[4][3].split()[0], "2/3", "numbers.md §15 (r3 B4 0.296 m/s)")
check("UKF v2 / FGO v3 heading sets", f"{rowsA[5][3]} / {rowsA[9][3]}", "3/3 PASS / 3/3 PASS", "numbers.md §15 (re-flown sets)")
check("FGO v2 ablation heading set", rowsA[8][3], "3/3 PASS", "numbers.md §15")
check("FGO original hard / robust heading sets (D28)", f"{rowsA[6][3]} / {rowsA[7][3]}", "3/3 PASS / 3/3 PASS", "numbers.md §15 (D28)")
check("contacts UKF v1 half / UKF v2 / FGO orig / FGO v2 / FGO v3 (s)",
      " / ".join(r[2].split(",")[0].replace(" s", "") for r in (rowsA[4], rowsA[5], rowsA[6], rowsA[8], rowsA[9])), "+198.0 / +165.9 / +165.8 / +169.6 / +169.9", "numbers.md §15 contact rows")
check("EKF3 full no-heading contact; UKF v1 full contact", f"{rowsA[1][2].split(',')[0].replace(' s', '')}; {rowsA[3][2].split(',')[0].replace(' s', '')}", "+186.2; +163.0", "numbers.md §15 rows 1–2")
check("UKF v1 half / FGO original B3 p95/max ranges", f"{rowsA[4][5]}; {rowsA[6][5]}", "0.18–0.21° / 0.28–1.32°; 0.26–0.38° / 1.28–1.88°", "numbers.md §15 B3 row (original builds)")
APP_A = ITEMS_A = None
CHK_A = CHK; CHK = []


def hsum(trs, key):
    hm = [1e3 * w["mean_m"] for t in trs for w in HJ(t)["hold_windows_vehicle"]]
    dr = [1e3 * lo[key]["effective"]["drift_m"] for t in trs for lo in HJ(t)["losses"]]
    lk = sum(lo[key]["lockout"] for t in trs for lo in HJ(t)["losses"])
    return f"{rd(min(hm), 1)}–{rd(max(hm), 1)} mm", f"{rd(min(dr), 0)}–{rd(max(dr), 0)} mm", f"{lk}", "every band PASS" if all(
        1e3 * lo[key]["effective"]["drift_m"] <= BAND[{"EKF3": "EKF3", "UKF_port": "UKF", "FGO_flying": "FGO"}[key]][i]
        for t in trs for i, lo in enumerate(HJ(t)["losses"])) else "band FAIL"


rowsH = [("S1, EKF3 flying (near spawn)", "unmodified EKF3", *hsum(S1, "EKF3")),
         ("S1 far re-fly, EKF3 flying", "unmodified EKF3", *hsum(S1F, "EKF3")),
         ("S2, UKF flying", "v1 port (pre-jitter fix)", *hsum(S2O, "UKF_port")),
         ("S2v2, UKF flying", "v2 port (jitter-corrected) FINAL", *hsum(S2V, "UKF_port")),
         ("S3, FGO flying", "noise fix only (ABLATION); OLD priors", *hsum(S3O, "FGO_flying")),
         ("S3v2, FGO flying", "v3 final node f642cd37; OLD priors", *hsum(S3V, "FGO_flying"))]
check("S2 / S2v2 / S3 / S3v2 hold window means (mm)", " ; ".join(r[2].replace(" mm", "") for r in rowsH[2:]), "4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0", "numbers.md §17.1 table")
check("lockouts S1 / S1far / S2v2 / S3v2", " / ".join(rowsH[i][4] for i in (0, 1, 3, 5)), "0 / 0 / 0 / 0", "numbers.md §17, §17.1")

SAFE = [  # (test, file, build, notes)
    ("UKF (a) PARAM", "safety_ukf_a", "v1 port; first run", "first run"),
    ("UKF (a) PARAM", "safety_ukf_a_rerun", "v1 port; re-run", ""),
    ("UKF (a) PARAM", "safety_ukf_a_v2", "v2 port (jitter-corrected)", "earlier final-build run"),
    ("UKF (a) PARAM", "safety_ukf_a_v3", "v2 port abb0357d (re-test)", "FINAL"),
    ("UKF (b) KILL", "safety_ukf_b", "v1 port", ""),
    ("UKF (b) KILL", "safety_ukf_b_v2", "v2 port (jitter-corrected)", "earlier final-build run; S-A2 relay drain"),
    ("UKF (b) KILL", "safety_ukf_b_v3", "v2 port abb0357d (re-test)", "FINAL; S-A2 relay drain"),
    ("FGO (a) KILL", "safety_fgo_a", "original FGO; old hold", ""),
    ("FGO (a) KILL", "safety_fgo_a_v2", "noise fix only (ABLATION); OLD priors", ""),
    ("FGO (a) KILL", "safety_fgo_a_v3", "v3 node f642cd37; OLD priors", "earlier final-build run"),
    ("FGO (a) KILL", "safety_fgo_a_v4", "corrected node 4c07374b; NEW priors", "FINAL; S-A3 1.45 m near its 1.5 m bound"),
    ("FGO (b) KILL", "safety_fgo_b", "original FGO; old hold", "room-box breach in the landing"),
    ("FGO (b) KILL", "safety_fgo_b2", "original FGO; 2 m-clearance hold", ""),
    ("FGO (b) KILL", "safety_fgo_b_v2", "noise fix only (ABLATION); OLD priors", ""),
    ("FGO (b) KILL", "safety_fgo_b_v3", "v3 node f642cd37; OLD priors", "earlier final-build run"),
    ("FGO (b) KILL", "safety_fgo_b_v4", "corrected node 4c07374b; NEW priors", "FINAL"),
    ("EKF3 reference KILL", "safety_ekf3_ref", "unmodified EKF3", "drift 1.40 m against a ≤ 0.5 m prediction (wrong); no breach"),
]


def srow(test, f, build, note):
    j = HJ(f); fl = []
    for k, nm in (("S-A1", "A1"), ("S-A2", "A2"), ("S-A3", "A3"), ("S-A4_single_landing", "A4")):
        if f == "safety_ekf3_ref" and k == "S-A2":
            fl.append("A2 n/a"); continue
        raw = (k == "S-A4_single_landing" and not j[k]["PASS"] and j[k].get("rearmed_after_disarm") is None)
        fl.append(f"{nm} {'PASS' if j[k]['PASS'] else 'FAIL'}" + (" (score file: rearmed_after_disarm null) ‡" if raw else ""))
    s2 = j["S-A2"]; s3 = j["S-A3"]
    t2 = f"{rd(s2['text_delay_s'], 2)} s (bound {rd(s2['bound_s'], 2)})" if s2.get("text_delay_s") is not None else "—"
    d3 = f"{rd(s3['horiz_disp_m'], 2)} m" if s3.get("horiz_disp_m") is not None else ("breach" if s3.get("breach") else "—")
    allp = all(j[k]["PASS"] for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing")) if f != "safety_ekf3_ref" else None
    verdict = "reference (no criteria)" if allp is None else ("ALL PASS" if allp else "FAILED AS WORDED")
    return (test, j["trial"], build, ", ".join(fl), t2, d3, verdict, note)


rowsS = [srow(*s) for s in SAFE]
SV = {r[1]: r for r in rowsS}
check("UKF (b) v2 / v3 S-A2 delay (s), verdict", f"{rd(HJ('safety_ukf_b_v2')['S-A2']['text_delay_s'], 2)} / {rd(HJ('safety_ukf_b_v3')['S-A2']['text_delay_s'], 2)}, "
      f"{SV['H_safety_ukf_b_v2'][6]} / {SV['H_safety_ukf_b_v3'][6]}", "5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("UKF (a) v2 / v3 verdict", f"{SV['H_safety_ukf_a_v2'][6]} / {SV['H_safety_ukf_a_v3'][6]}", "ALL PASS / ALL PASS", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("FGO (a) v3 S-A2 / disp; (b) v3", f"{rd(HJ('safety_fgo_a_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v3')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v3')['S-A3']['horiz_disp_m'], 2)} m", "0.54 s / 0.83 m; 0.25 s / 1.19 m", "numbers.md §15 history row (v3, earlier final-build run)")
check("FGO (a) v4 S-A2 / disp; (b) v4", f"{rd(HJ('safety_fgo_a_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v4')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v4')['S-A3']['horiz_disp_m'], 2)} m", "0.60 s / 1.45 m; 0.62 s / 0.21 m",
      "numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS'")
check("FGO v4 a / b verdict", f"{SV['H_safety_fgo_a_v4'][6]} / {SV['H_safety_fgo_b_v4'][6]}", "ALL PASS / ALL PASS", "numbers.md §15 safety row (v4, final)")
check("FGO v2 ablation a / b: S-A2 s, disp m", f"{rd(HJ('safety_fgo_a_v2')['S-A2']['text_delay_s'], 2)} s, {rd(HJ('safety_fgo_a_v2')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v2')['S-A2']['text_delay_s'], 2)} s, {rd(HJ('safety_fgo_b_v2')['S-A3']['horiz_disp_m'], 2)} m", "0.29 s, 0.78 m; 0.43 s, 1.27 m", "numbers.md §15 history row")
check("history: UKF a rerun / UKF b / FGO a / FGO b2 disp (m); UKF b S-A2 (s)",
      f"{rd(HJ('safety_ukf_a_rerun')['S-A3']['horiz_disp_m'], 2)} / {rd(HJ('safety_ukf_b')['S-A3']['horiz_disp_m'], 2)} / {rd(HJ('safety_fgo_a')['S-A3']['horiz_disp_m'], 2)} / "
      f"{rd(HJ('safety_fgo_b2')['S-A3']['horiz_disp_m'], 2)}; {rd(HJ('safety_ukf_b')['S-A2']['text_delay_s'], 2)}", "0.42 / 0.28 / 0.37 / 1.25; 4.81", "numbers.md §15 history row")
check("FGO (b) first run S-A3; UKF (a) first run S-A2 / S-A3", f"{HJ('safety_fgo_b')['S-A3']['PASS']}; {HJ('safety_ukf_a')['S-A2']['PASS']} / {HJ('safety_ukf_a')['S-A3']['PASS']}",
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
HCW = {"H-H2": "FGO < EKF3 and FGO < UKF mean hold error, 3/3", "P-H3": "hold gyro activity within 1.5× across estimators",
       "H-H4 (15 s)": "EKF3's 15 s re-lock jump larger than the UKF's and the FGO's, 3/3", "H-H4 (5 s)": "5 s re-lock jumps within 1.5× of each other"}
rowsHC = [(k, HCW[k], hctxt(HCR[k]), hctxt(HCO[k]), "no" if HCR[k][0].split()[0] == HCO[k][0].split()[0] else "YES") for k in HCW]
check("H comparative verdicts, final-build sets (primary) / superseded builds", " ; ".join(HCR[k][0].split()[0] for k in HCW) + " / " +
      " ; ".join(HCO[k][0].split()[0] for k in HCW), "FAIL ; FAIL ; FAIL ; FAIL / FAIL ; FAIL ; FAIL ; FAIL", "numbers.md §17.2 criteria table (both sets)")
check("H hold UKF / FGO / EKF3, final-build sets (mm)", f"{HCR['H-H2'][1]} / {HCR['H-H2'][2]} / {HCR['H-H2'][3]}", "6.4–7.1 / 8.3–8.6 / 7.8–7.9",
      "numbers.md §17.2 criteria table (re-flown)")
check("H hold UKF, superseded builds (mm)", HCO["H-H2"][1], "5.5–6.1", "numbers.md §17.2 criteria table (earlier sets)")
check("P-H3 max/min, final-build / superseded", f"{rng([r['ph3_ratio'] for r in _HSET['re']['criteria']['runs']])} / "
      f"{rng([r['ph3_ratio'] for r in _HSET['old']['criteria']['runs']])}", "2.40–2.58 / 2.37–2.43", "numbers.md §17.2 criteria table")
check("H-H4 (5 s) max/min, final-build / superseded", f"{rng([r['hh4b_ratio'] for r in _HSET['re']['criteria']['runs']], 1)} / "
      f"{rng([r['hh4b_ratio'] for r in _HSET['old']['criteria']['runs']], 1)}", "3.2–7.7 / 3.4–5.9", "numbers.md §17.2 criteria table")
check("final safety runs: drift to touchdown UKF (a) v3 / UKF (b) v3 / FGO (a) v4 / FGO (b) v4 (m)",
      " / ".join(rd(HJ(f)["S-A3"]["horiz_disp_m"], 2) for f in ("safety_ukf_a_v3", "safety_ukf_b_v3", "safety_fgo_a_v4", "safety_fgo_b_v4")),
      "0.58 / 1.07 / 1.45 / 0.21", "numbers.md §15 safety row (final runs, restated 2026-10-16)")
A4ART = [f for f in ("safety_ukf_a", "safety_fgo_b") if not HJ(f)["S-A4_single_landing"]["PASS"]]
check("raw S-A4 entries in the early score files (PASS, n_land_entries_after_t_f, rearmed_after_disarm)",
      ", ".join(f"{f}: {HJ(f)['S-A4_single_landing']['PASS']}, {HJ(f)['S-A4_single_landing']['n_land_entries_after_t_f']}, "
                f"{HJ(f)['S-A4_single_landing']['rearmed_after_disarm']}" for f in A4ART),
      "safety_ukf_a: False, 1, None, safety_fgo_b: False, 1, None", "eval/results/expH/safety_ukf_a.json, safety_fgo_b.json (the score files)")
CHK_HS = CHK; CHK = []

f1 = L("f1_test.json"); dec1 = f1["decision"]
bagsF = ["fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3"]
check("F1 robust lower yaw max on", f"{dec1['robust_lower_yaw_max_on']}/6", "6/6", "numbers.md §15.2 F1 row")
check("F1 lockouts FGO_robust = UKF_hard", json.dumps(dec1["lockout_total"], sort_keys=True), json.dumps({"FGO_robust": 3, "UKF_hard": 3}, sort_keys=True), "numbers.md §15.2")
check("F1 verdict robust_FGO_better", dec1["robust_FGO_better"], False, "numbers.md §15.2 (NOT met, lockout tie)")
check("FGO_hard plain-wall yaw max (deg)", rng([f1[b]["FGO_hard"]["yaw_max_deg"] for b in bagsF]), "4.59–5.03", "numbers.md §15.2 F1 row")
ST = {}
for mode in ("lc", "nolc"):
    for key in ("step_median_ms", "step_p99_ms", "wall_s"):
        ST[(mode, key)] = [json.load(open(f"{TD}/T_A_r{r}/lc_fgo_{mode}_t245/stats.json"))[key] for r in (1, 2, 3)]
check("L LC median (ms)", rng(ST[("lc", "step_median_ms")], 0), "35–41", "numbers.md §16.3 (restated 2026-10-11)")
check("L no-LC median (ms)", rng(ST[("nolc", "step_median_ms")], 0), "50–61", "numbers.md §16.3")
check("L LC p99 (ms)", rng(ST[("lc", "step_p99_ms")], 0), "80–94", "numbers.md §16.3")
check("L no-LC wall (s)", rng(ST[("nolc", "wall_s")], 0), "7276–9583", "numbers.md §16.3")
CHK_F = CHK; CHK = []

ABL = [  # build ablations: (ablation, measure, earlier build, final build, verdict)
    ("UKF v1 → v2 (jitter correction)", "closed loop, no heading: wall contact", rowsA[4][2].split(",")[0] + " (PASS)", rowsA[5][2].split(",")[0] + " (PASS)", "both inside the window"),
    ("UKF v1 → v2", "closed loop, with heading: B1–B5", rowsA[4][3], rowsA[5][3], "v1 flight 3 failed B4 (flow validity)"),
    ("UKF v1 → v2", "H hold, window means / drift", f"{rowsH[2][2]} / {rowsH[2][3]}", f"{rowsH[3][2]} / {rowsH[3][3]}", "every band PASS in both"),
    ("FGO v2 (noise fix only) → v3 (+ gated yaw cap)", "closed loop, no heading: wall contact", rowsA[8][2].split(",")[0] + " (PASS)", rowsA[9][2].split(",")[0] + " (PASS)", "gating alone: +0.3 s"),
    ("FGO v2 → v3", "closed loop, with heading: B1–B5; B3 max", f"{rowsA[8][3]}; {rowsA[8][5].split('/ ')[1]}", f"{rowsA[9][3]}; {rowsA[9][5].split('/ ')[1]}", "v3 flight 3 B4 0.246 m/s (band 0.25)"),
    ("FGO v2 → v3", "H hold, window means / drift", f"{rowsH[4][2]} / {rowsH[4][3]}", f"{rowsH[5][2]} / {rowsH[5][3]}", "few-mm level only"),
    ("FGO v2 → v3 → v4 node", "safety (a) / (b)", f"{SV['H_safety_fgo_a_v2'][6]} / {SV['H_safety_fgo_b_v2'][6]}",
     f"v3 {SV['H_safety_fgo_a_v3'][6]} / {SV['H_safety_fgo_b_v3'][6]}; v4 {SV['H_safety_fgo_a_v4'][6]} / {SV['H_safety_fgo_b_v4'][6]}", "v4 = NEW priors"),
    ("Flown FGO priors", "closed loop, H S3/S3v2, safety v2/v3", "OLD priors: initial yaw σ 1e-3 rad, roll/pitch 2°", "offline FGO: 1°, 5° (= UKF)",
     "no re-fly before the freeze; only safety v4 used the NEW priors"),
]


def save_table(figs, fid, name, title, caption, inputs, rows_, checks):
    global CHK
    pngs = []
    for k, f in enumerate(figs):
        base = os.path.join(OUT, name + (f"_p{k + 1}" if len(figs) > 1 else ""))
        f.savefig(base + ".png", dpi=150); f.savefig(base + ".pdf"); plt.close(f); pngs.append(base + ".png")
    ok = all(c[4] for c in checks)
    ITEMS.append(dict(id=fid, kind="appendix", png=pngs, pdf=None, title=title, caption=caption, inputs=inputs, rows=rows_, checks=checks,
                      status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale="none needed (table)", uncheck="",
                      files=[os.path.basename(p) for p in pngs], order=None))
    print(f"wrote {name} ({len(pngs)} page(s))  checks {sum(c[4] for c in checks)}/{len(checks)}")
    for c in checks:
        if not c[4]:
            print("   CHECK FAIL:", c)


figs = table_page("Appendix A1. Closed loop in the textured corridor: every flown build, pass/fail against the pre-registered criteria",
                  ["flying estimator", "build", "no heading: wall contact (window)", "with heading: B1–B5 (+S2)", "B2 max cross-track",
                   "B3 yaw error p95 / max", "B4 max lateral speed"], rowsA, [16, 30, 30, 22, 13, 22, 14],
                  notes=["Contact windows are pre-registered per estimator (EKF3 [+155, +215] s, UKF [+146, +218] s, FGO [+145, +196] s). n = 1 per "
                         "no-heading flight; closed-loop run-to-run variability is unmeasured; no comparison across real-time factors. " + RTFX + " "
                         "FINAL builds are the "
                         "UKF v2 port and the FGO v3 node; the rest are recorded earlier builds and the FGO v2 ablation. ALL flown FGO flights used the "
                         "OLD FGO priors (initial yaw σ 1e-3 rad, roll/pitch 2°). The UKF v1 half real-time flight 3 B4 failure (0.296 m/s) and the FGO v3 "
                         "flight 3 near-miss (0.246 m/s against 0.25) are a shared flow-validity limitation of the sensor pipeline. Robust heading weighting (FGO): F1 'NOT met (lockout tie)', "
                         "see A3."])
save_table(figs, "A1", "A1_closed_loop_builds", "Closed loop: every flown build against B1–B5 and the contact window",
           "Pass/fail of every closed-loop corridor set, computed from the closed-loop score files, with the build ablations "
           "labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix only, ABLATION) and v3 (final, OLD priors).",
           "eval/results/closed_loop_<trial>.json", "§15 (contacts, B1–B5 counts, B2, B3, re-flown sets); claim 14", CHK_A)
figs = table_page("Appendix A2. Experiment H hold sets and the safety tests (all runs, as-worded verdicts)",
                  ["H flight set", "build", "hold error (window means)", "tag-loss drift (effective, all losses)", "lockouts", "P-H5 drift bands"],
                  rowsH, [26, 34, 20, 26, 10, 18], fs=8.0) + \
       table_page("Appendix A2 (cont.). Safety tests: failure injected in the hold; the FC must declare position lost",
                  ["test", "trial", "build", "criteria as worded", "S-A2 'position lost' delay", "S-A3 drift to touchdown", "verdict", "note"],
                  rowsS, [13, 21, 25, 30, 18, 12, 15, 26], fs=7.0,
                  notes=["FINAL = the latest run of each test on the final build (UKF v3, FGO v4). UKF (b) S-A2 FAILS AS WORDED in v2 (5.75 s) and v3 "
                         "(5.69 s) against 5.5 s: relay drain in MAVProxy (the ground-station message relay) after the SIGKILL (the forced process "
                         "kill); both stay FAILED, by ruling. " + PRIORS + " ‡ Raw score-file entries for the first UKF (a) and FGO (b) runs: S-A4 FAIL, "
                         "one LAND entry, rearmed_after_disarm null (the scorer recorded no disarm). The results record calls these not applicable "
                         "(an (a) run) and not scored (no touchdown); Table T7 shows them so. The EKF3 reference has no thesis-nav text (S-A2 not applicable)."]) + \
       table_page("Appendix A2 (cont.). Experiment H comparative criteria: the final-build sets (primary) and the superseded builds",
                  ["criterion", "pre-registered wording", "final-build sets: UKF S2v2, FGO S3v2 (PRIMARY)",
                   "superseded builds: UKF S2 (v1 port), FGO S3 (ablation build)", "verdict differs?"], rowsHC, [14, 34, 50, 50, 12], fs=8.0,
                  notes=["The final-build verdicts are reported as primary; they are identical to the original-build verdicts (all three comparative "
                         "criteria FAIL on both). EKF3 is the EKF3-flying far-spawn hold set in both columns (3 flights); each estimator flew its "
                         "own flights, paired by run index, not trajectory. Two wordings change with the final builds: the FGO hold is now the "
                         "highest, not tied with EKF3, and EKF3's 15 s jump is strictly the smallest. " + PRIORS])
save_table(figs, "A2", "A2_H_and_safety", "H hold sets and the safety tests (all runs)",
           "Experiment H sets (S1, S1 far, S2/S2v2, S3/S3v2) with hold error, drift, lockouts and the P-H5 bands, and every safety-test run with its "
           "as-worded verdict; the final runs are the v3 (UKF) and v4 (FGO, NEW priors) re-tests. " + PRIORS + " The comparative criteria page "
           "gives the final-build sets (primary) beside the superseded builds; the final-build verdicts are identical to the "
           "original-build verdicts (all FAIL).",
           "eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json, safety_*.json", "§15 safety rows, §17, §17.1; METHODOLOGY 2d and 'Band C … FGO safety re-tests'", CHK_HS)
rowsF = [("F1 (k = 2.385)", "robust FGO better than the hard-gated UKF on the heading", "NOT met (lockout tie)",
          f"robust FGO lower worst-case yaw on {dec1['robust_lower_yaw_max_on']}/6 bags, but lockouts FGO_robust {dec1['lockout_total']['FGO_robust']} = UKF_hard "
          f"{dec1['lockout_total']['UKF_hard']}; FGO_hard plain-wall yaw max {rng([f1[b]['FGO_hard']['yaw_max_deg'] for b in bagsF])}° (= UKF_hard to 0.01°)"),
         ("L compute cost (DIAGNOSTIC)", "per-update solve time and wall time, keyframe FGO, workstation Python, 6 parallel jobs", "no criterion",
          f"median LC {rng(ST[('lc', 'step_median_ms')], 1)} ms, no-LC {rng(ST[('nolc', 'step_median_ms')], 1)} ms; p99 LC {rng(ST[('lc', 'step_p99_ms')], 0)} ms, "
          f"no-LC {rng(ST[('nolc', 'step_p99_ms')], 0)} ms; no-LC wall {rng(ST[('nolc', 'wall_s')], 0)} s. Says nothing about onboard feasibility")]
figs = table_page("Appendix A3. The F1 robust-weighting test, the L compute cost, and the build ablations",
                  ["item", "what is tested", "verdict", "key numbers"], rowsF, [24, 46, 24, 96])
figs2 = table_page("Appendix A3 (cont.). Build ablations: earlier build against the final build, same experiment",
                   ["ablation", "measure", "earlier build", "final build", "note"], ABL, [36, 34, 38, 42, 40],
                   notes=["Earlier builds are kept as recorded and labelled; the thesis cites the final builds. Attribution: the corrections were applied "
                          "jointly and are not attributed individually, apart from the traced plain-wall case and the O partial attribution."])
save_table(figs + figs2, "A3", "A3_F1_cost_ablations", "F1, the L compute cost and the build ablations",
           "Pass/fail table for the F1 robust-weighting test, the L compute cost (diagnostic; linear values, no plot) and the build ablations: "
           "UKF v1 against v2; FGO v2 (noise fix only) against v3 (final) and the v4 node; the flown-FGO OLD-priors note. " + PRIORS,
           "eval/results/f1_test.json; ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json; closed_loop_*, expH/*",
           "§15.2 F1 row; §16.3 cost bullets; §15, §17.1", CHK_F)

# =============================================================================================== TABLE T7 failure behaviour (new)
# Ruling 2026-10-16 (open items, 10): the early S-A4 flags are shown as the results record has them, quoted with file:line;
# the raw score-file entries are in Appendix A2.
A4NA = {"safety_ukf_a": "not applicable", "safety_fgo_b": "not scored"}
A4Q = {11490: "- **S-A4:** not applicable (an (a) run).",
       11827: "- **S-A4:** not scored (no touchdown). One LAND entry, no conflict between the two paths."}


def sfail(f):
    """As-worded outcome of one safety score file, with the S-A4 scorer artefact flagged (METHODOLOGY L11307, L11490, L11827)."""
    j = HJ(f); out = []
    for k, nm in (("S-A1", "S-A1"), ("S-A2", "S-A2"), ("S-A3", "S-A3"), ("S-A4_single_landing", "S-A4")):
        if f == "safety_ekf3_ref" and k == "S-A2":
            continue
        if not j[k]["PASS"]:
            if k == "S-A4_single_landing" and j[k].get("rearmed_after_disarm") is None and f in A4NA:
                out.append(f"S-A4 {A4NA[f]} ‡")
            elif k == "S-A2":
                out.append(f"S-A2 FAIL as worded ({rd(j[k]['text_delay_s'], 2)} s, bound {rd(j[k]['bound_s'], 2)} s)")
            elif k == "S-A3":
                out.append("S-A3 FAIL (" + ("watcher breach" if j[k].get("breach") else "criterion") + ")")
            else:
                out.append(f"{nm} FAIL")
    s3 = j["S-A3"]; d = f", {rd(s3['horiz_disp_m'], 2)} m" if s3.get("horiz_disp_m") is not None else ""
    return ("ALL PASS" + d) if not out else "; ".join(out)


_ML = open(os.path.join(ROOT, "METHODOLOGY.md")).read().split("\n")
check("METHODOLOGY.md:11490 and :11827 (the S-A4 reasons quoted in T7)", " | ".join(_ML[n - 1] for n in sorted(A4Q)),
      " | ".join(A4Q[n] for n in sorted(A4Q)), "METHODOLOGY.md lines 11490, 11827 (read at build time)")
check("EKF3 blank invalid (s of cruise); valid airborne flow frames", f"{rng(EK_INV, 0)}; max {max(nvalid)}", "301–310; max 0", "numbers.md §6.2")
stepO = {e: [L(f"expO/{t}.json")["tracks"][f"{e} live"]["max_step_after_return_m"] for t in OFL] for e in EST}
check("O largest step in 10 s after return EKF3 / UKF / FGO live (m)", " / ".join(rng(stepO[e]) for e in EST), "4.10–4.10 / 2.30–2.44 / 2.14–2.28", "numbers.md §16.2 table")
check("UKF (b) v2 / v3 S-A2 delay (s), verdict", f"{rd(HJ('safety_ukf_b_v2')['S-A2']['text_delay_s'], 2)} / {rd(HJ('safety_ukf_b_v3')['S-A2']['text_delay_s'], 2)}, "
      f"{SV['H_safety_ukf_b_v2'][6]} / {SV['H_safety_ukf_b_v3'][6]}", "5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("UKF (a) v2 / v3 verdict", f"{SV['H_safety_ukf_a_v2'][6]} / {SV['H_safety_ukf_a_v3'][6]}", "ALL PASS / ALL PASS", "numbers.md §15 history row (v2) and safety row (v3, final)")
check("FGO (a) v4 S-A2 / disp; (b) v4", f"{rd(HJ('safety_fgo_a_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v4')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v4')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v4')['S-A3']['horiz_disp_m'], 2)} m", "0.60 s / 1.45 m; 0.62 s / 0.21 m",
      "numbers.md §15 safety row (v4, final); METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS'")
check("FGO (a) v3 S-A2 / disp; (b) v3", f"{rd(HJ('safety_fgo_a_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_a_v3')['S-A3']['horiz_disp_m'], 2)} m; "
      f"{rd(HJ('safety_fgo_b_v3')['S-A2']['text_delay_s'], 2)} s / {rd(HJ('safety_fgo_b_v3')['S-A3']['horiz_disp_m'], 2)} m", "0.54 s / 0.83 m; 0.25 s / 1.19 m", "numbers.md §15 history row (v3, earlier final-build run)")
check("FGO (b) first run S-A3; UKF (a) first run S-A2 / S-A3", f"{HJ('safety_fgo_b')['S-A3']['PASS']}; {HJ('safety_ukf_a')['S-A2']['PASS']} / {HJ('safety_ukf_a')['S-A3']['PASS']}",
      "False; False / False", "numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL)")
check("EKF3 reference drift (m)", f"{rd(HJ('safety_ekf3_ref')['S-A3']['horiz_disp_m'], 2)}", "1.40", "numbers.md §15 history row")
SA = {"UKF (a) PARAM": [("v1 run 1", "safety_ukf_a"), ("v1 re-run", "safety_ukf_a_rerun"), ("v2", "safety_ukf_a_v2"), ("v3 re-test (FINAL)", "safety_ukf_a_v3")],
      "UKF (b) KILL": [("v1", "safety_ukf_b"), ("v2", "safety_ukf_b_v2"), ("v3 re-test (FINAL)", "safety_ukf_b_v3")],
      "FGO (a) KILL": [("original", "safety_fgo_a"), ("v2 ablation", "safety_fgo_a_v2"), ("v3", "safety_fgo_a_v3"), ("v4 re-test (FINAL), NEW priors", "safety_fgo_a_v4")],
      "FGO (b) KILL": [("original, run 1", "safety_fgo_b"), ("original, 2 m hold", "safety_fgo_b2"), ("v2 ablation", "safety_fgo_b_v2"),
                       ("v3", "safety_fgo_b_v3"), ("v4 re-test (FINAL), NEW priors", "safety_fgo_b_v4")]}
sa = lambda key: "\n".join(f"{lab}: {sfail(f)}" for lab, f in SA[key])
rowsT7 = [
    ["EKF3", f"position flagged INVALID from take-off on all {len(EK_INV)} blank flights ({rng(EK_INV, 0)} s of cruise; {max(nvalid)} valid "
             "airborne flow frames); outputs the origin, not scored: a DECLARED failure",
     f"resets to GNSS on return: {rng(stepO['EKF3'])} m jump (every flight)", "not run (EKF3 has no thesis-nav position-lost path)",
     f"reference KILL only (no criteria): drift {rd(HJ('safety_ekf3_ref')['S-A3']['horiz_disp_m'], 2)} m against a ≤ 0.5 m prediction "
     "(the prediction was wrong); no breach"],
    ["UKF", f"no invalid period recorded; position runs away: +60 s {rng(BLANK['UKF'][:, 2], 0)} m, end of cruise {rng(BLANK['UKF'][:, 3] / 1e3, 0)} km †",
     f"largest step in 10 s after return {rng(stepO['UKF'])} m", sa("UKF (a) PARAM"), sa("UKF (b) KILL")],
    ["FGO", f"no invalid period recorded; position runs away: +60 s {rng(BLANK['FGO'][:, 2], 0)} m, end of cruise {rng(BLANK['FGO'][:, 3] / 1e3, 0)} km †",
     f"largest step in 10 s after return {rng(stepO['FGO'])} m", sa("FGO (a) KILL"), sa("FGO (b) KILL")]]
save_tab("T7", "T7_failure_behaviour", "Failure behaviour: blank-floor validity, the O return jump and the safety tests",
         "How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the FGO run away with no invalid period recorded; on the "
         "return to GNSS EKF3 jumps 4.1 m; in the hold safety tests the final run of each test (the latest on the final build: UKF v3, FGO v4) "
         "passes as worded except UKF (b) S-A2, which fails as worded in v2 and v3 (a relay-drain timing fault in the bound). " + PRIORS,
         ["estimator", "blank floor: position validity", "O: return to GNSS", "safety (a): PARAM failure / KILL (FGO), as worded",
          "safety (b): KILL, as worded"], rowsT7, [10, 34, 20, 44, 44],
         "eval/results/blank_behaviour.json; expO/O_r1.json, O_r2.json, O_r3b.json (max_step_after_return_m); expH/safety_*.json",
         "§6.2, §15 safety and history rows, §16.2; METHODOLOGY 'H safety test …' entries, 2d, rulings 2026-10-11, 'Band C … FGO safety re-tests'",
         notes=["Safety criteria (pre-registered): S-A1 attitude error; S-A2 'position lost' declared within the bound (0.75 s; UKF (b) 5.5 s); "
                "S-A3 safe landing (≤ 1.5 m drift to touchdown, no watcher breach); S-A4 a single landing, pre-registered for (b) runs only. "
                "UKF (b) v2 / v3 S-A2: the trigger fired 5.0 s after the last flow received (the UKF's 5 s timeout), plus relay drain in MAVProxy "
                "(the ground-station message relay) after the SIGKILL (the forced process kill); both stay FAILED AS WORDED, by ruling. The final "
                "runs are the latest run of each test on the final build (UKF v3 re-test, FGO v4 re-test); v2 (UKF) and v3 (FGO) are the earlier "
                "final-build runs. FGO v4 flew the corrected-priors node; every earlier FGO run flew the OLD priors.",
                "‡ S-A4 is shown as the results record gives it for these two runs: UKF (a) run 1, 'S-A4: not applicable (an (a) run).' "
                "(METHODOLOGY.md:11490); FGO (b) run 1, 'S-A4: not scored (no touchdown). One LAND entry, no conflict between the two "
                "paths.' (METHODOLOGY.md:11827; the run was stopped at the room-box breach). The raw score-file entries (S-A4 FAIL, no "
                "disarm recorded) are in Appendix A2.",
                "UKF (a) run 1 is the v1 port; the S-A2 bound in its score file is 0.10 s (0.75 s in the later runs), shown as recorded. "
                "† runaway magnitude (order only). 'No invalid period recorded': the blank-floor scoring records an invalid period for "
                "EKF3 only; the UKF / FGO runaway positions are scored as errors (Table T3)."], fs=7.2, order=70)

# =============================================================================================== TABLE T8 hindsight: FGO batch vs RTS-UKF
HB, HR = "FGO hindsight (whole-flight batch)", "RTS-UKF (hindsight)"
p4 = agg["P-T4 hindsight ratio max/min"]
rowsT8 = []
for c in TCOND:
    mr = agg["conditions"][c]["mean_rmse_m"]; b_, r_ = mr[HB], mr[HR]
    rowsT8.append([f"T {c}: {TLAB[c]} (mean of 3)", f"{rd(100 * b_, 1)}", f"{rd(100 * r_, 1)}", "FGO batch" if b_ < r_ else "RTS-UKF",
                   f"{rd(max(b_, r_) / min(b_, r_), 2)}", f"P-T4 {'PASS' if p4['PASS'] else 'FAIL'}"])
o3 = []
for i, t in enumerate(OFL):
    b_, r_ = OI[HB][i], OI[HR][i]; o3.append(max(b_, r_) / min(b_, r_))
    rowsT8.append([f"O: flight {i + 1} (indoor)", f"{rd(100 * b_, 1)}", f"{rd(100 * r_, 1)}", "FGO batch" if b_ < r_ else "RTS-UKF", f"{rd(o3[-1], 2)}", "P-O3 PASS"])
check("P-T4 max/min ratio A / B / C / D", " / ".join(f"{rd(p4['by_condition'][c], 2)}" for c in TCOND), "1.31 / 2.14 / 2.06 / 3.89", "numbers.md §16.1 P-T4")
check("T8 table ratio = stored P-T4 ratio, all 4 conditions", all(abs(float(r[4]) - p4["by_condition"][c]) < 0.006 for r, c in zip(rowsT8, TCOND)), True,
      "t_aggregate.json P-T4 vs mean_rmse_m")
check("T RTS-UKF A–D (m)", " / ".join(f"{rd(agg['conditions'][c]['mean_rmse_m'][HR], 3)}" for c in TCOND), "0.014 / 0.031 / 0.039 / 0.109", "numbers.md §16.1 table")
check("T FGO batch A–D (m)", " / ".join(f"{rd(agg['conditions'][c]['mean_rmse_m'][HB], 3)}" for c in TCOND), "0.010 / 0.015 / 0.019 / 0.028", "numbers.md §16.1 table")
check("O batch FGO vs RTS-UKF ratio, max/min per flight (capped)", rng(o3), "1.01–1.02", "numbers.md §16.2 P-O3")
cf = [max(OI[HB][i], L(f"expO/{t}.json")["tracks"]["RTS-UKF (hindsight, cap-free forward pass)"]["indoor_rmse_m"]) /
      min(OI[HB][i], L(f"expO/{t}.json")["tracks"]["RTS-UKF (hindsight, cap-free forward pass)"]["indoor_rmse_m"]) for i, t in enumerate(OFL)]
check("O batch FGO vs cap-free RTS-UKF ratio, max/min per flight", rng(cf), "1.01–1.05", "numbers.md §16.2 P-O3 (cap-free)")
save_tab("T8", "T8_hindsight_ratio", "Hindsight: the FGO whole-flight batch against the RTS-smoothed UKF",
         "With tags at known positions (T) the FGO batch is below the RTS-UKF in every condition, by 1.3–3.9× (largest with 1 tag; P-T4 "
         "FAIL as pre-registered); indoors without GNSS (O) the two hindsight tracks are equal within 1–2% (P-O3 PASS).",
         ["case", "FGO batch RMSE (cm)", "RTS-UKF RMSE (cm)", "lower", "max ÷ min", "pre-registered test"], rowsT8, [40, 18, 18, 16, 14, 18],
         "eval/results/expT/t_aggregate.json (conditions.*.mean_rmse_m, 'P-T4 hindsight ratio max/min'); expO/O_r1.json, O_r2.json, O_r3b.json "
         "(tracks.*.indoor_rmse_m)", "§16.1 (table, P-T4), §16.2 (table, P-O3); claims 18, 21",
         notes=["Ratio = max ÷ min of the two hindsight RMSEs (the pre-registered definition of P-T4 and P-O3), so it is ≥ 1 and the 'lower' "
                "column gives the direction: in O the RTS-UKF is lower on flights 1 and 2 and the FGO batch on flight 3. Aggregation differs: T is "
                "per condition from the means of 3 repeats (the RMSE over the 5 laps); O is per flight (indoor RMSE, 123 s). T is in the "
                "world frame with tag fixes at known positions; O in the world frame with GNSS outside only.",
                f"Cap-free RTS-UKF variant in O: max ÷ min {rng(cf)}. The former 'FGO batch ~2× better than the "
                "RTS-UKF' in O is WITHDRAWN (a noise-model artefact). Hindsight here = the FGO whole-flight batch and the single-pass RTS "
                "smoother; L's keyframe-FGO hindsight (iSAM2 full estimate) is a different estimator and is not in this table."], order=80)

# =============================================================================================== combined PDF + index
PAL = "EKF3 #0072B2 (blue, circle) · UKF #009E73 (bluish green, triangle) · FGO #D55E00 (vermilion, square) · truth / references #999999 (grey)"
# order: figures (by id), then tables T1–T8, then the appendix
FIGS_ = sorted([it for it in ITEMS if it["kind"] == "figure"], key=lambda it: it["id"])
TABS_ = sorted([it for it in ITEMS if it["kind"] == "table"], key=lambda it: it["order"])
APPX_ = [it for it in ITEMS if it["kind"] == "appendix"]
ITEMS[:] = FIGS_ + TABS_ + APPX_
REMOVED = [("F1", "F1_scorecard", "T1"), ("F3", "F3_accuracy_without_and_with_heading", "T2"), ("F4", "F4_blank_floor_flow_loss", "T3"),
           ("F8", "F8_H_tag_loss_drift", "T5")]
PREV = "7778cd6"


def caption_page(P, it):
    pngs = it["png"] if isinstance(it["png"], list) else [it["png"]]
    word = {"figure": "Figure", "table": "Table", "appendix": "Appendix table"}[it["kind"]]
    for pi, png in enumerate(pngs):
        img = plt.imread(png); h, w = img.shape[:2]
        fig = plt.figure(figsize=(11.69, 8.27))
        top = 0.965; avail = 0.70 if it["kind"] == "figure" else 0.78; aw = 0.95; ah = aw * (h / w) * 11.69 / 8.27
        if ah > avail: aw *= avail / ah; ah = avail
        ax = fig.add_axes([0.5 - aw / 2, top - ah, aw, ah]); ax.imshow(img); ax.axis("off")
        y = top - ah - 0.02
        if pi == len(pngs) - 1:
            cap = "\n".join(textwrap.wrap(f"{word} {it['id']}. {it['caption']}", 175))
            fig.text(0.03, y, cap, fontsize=8.6, va="top"); y -= 0.0185 * (cap.count("\n") + 1) + 0.01
            okc = sum(c[4] for c in it["checks"])
            src = "\n".join(textwrap.wrap(f"Cross-check against the results record: {okc}/{len(it['checks'])} values match. The sources, "
                                          "the rows they are checked against and the build are listed in the figure index.", 200))
            fig.text(0.03, max(y, 0.02 + 0.0165 * (src.count("\n") + 1)), src, fontsize=7.2, va="top", color=INK2)
        P.savefig(fig); plt.close(fig)


with PdfPages(PDF) as P:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.06, 0.88, "Thesis figures and tables", fontsize=24, weight="bold")
    fig.text(0.06, 0.835, "EKF3, UKF and FGO for indoor UAV state estimation under degraded sensing (simulation; results FROZEN 2026-10-11)", fontsize=12)
    intro = ("Reader-facing set (revision 2026-10-16), plotted and tabulated from the frozen result files (no number recomputed). Four "
             "figures (F2, F5, F6, F7), eight tables (T1–T8; each also as LaTeX booktabs and markdown in docs/thesis/tables/) and the "
             "appendix tables A1–A3. F1, F3, F4 and F8 of the 2026-10-15 set became tables T1, T2, T3 and T5 (the old figures are in the "
             "repository history). Every key value is cross-checked against the results record; the match count is under each caption, "
             "and the sources are listed in the figure index. Conventions: one fixed colour and marker per estimator; solid "
             "lines and filled marks = live, dashed lines and open marks = hindsight; linear axes only (no log axes); evo = evo -a (cruise). "
             "† = a runaway magnitude from a diverging estimate (order of magnitude only). " + PRIORS + " Half real-time (RTF 0.5): " + RTFX)
    fig.text(0.06, 0.79, "\n".join(textwrap.wrap(intro, 140)), fontsize=9.6, va="top")
    fig.text(0.06, 0.615, "Colours", fontsize=12, weight="bold")
    for k, e in enumerate(EST):
        fig.add_artist(Line2D([0.07, 0.10], [0.585 - 0.026 * k] * 2, color=C[e], lw=2, marker=MK[e], ms=7, transform=fig.transFigure))
        fig.text(0.11, 0.585 - 0.026 * k, f"{e}  {C[e]}", fontsize=10, va="center")
    fig.add_artist(Line2D([0.07, 0.10], [0.507] * 2, color=TRUTH, lw=2, transform=fig.transFigure)); fig.text(0.11, 0.507, f"truth / reference  {TRUTH}", fontsize=10, va="center")
    y = 0.465; fig.text(0.06, y, "Contents", fontsize=12, weight="bold"); y -= 0.024
    for it in ITEMS:
        okc = sum(c[4] for c in it["checks"])
        fig.text(0.07, y, f"{it['id']}  {it['title']}   [checks {okc}/{len(it['checks'])}]", fontsize=8.6); y -= 0.0215
    P.savefig(fig); plt.close(fig)
    for it in ITEMS:
        caption_page(P, it)
print("wrote", PDF)

with open(INDEX, "w") as f:
    f.write("# Thesis figures and tables: index (revision 2026-10-16)\n\n")
    f.write(f"Built by `{SCRIPT}` at commit `{COMMIT}` (run with `/home/makerspace/venv-evo/bin/python`; plotting and tabulating only, no "
            "number recomputed). Combined PDF for the supervisor (figures, then the tables rendered as pages, then the appendix): "
            "`docs/thesis/figures_thesis/thesis_figures_combined.pdf`. Figures are here as `.pdf` and `.png`; tables T1–T8 are in "
            "`docs/thesis/tables/` as LaTeX (`.tex`, booktabs; NOT compiled on the build machine, which has no TeX: checked for ASCII, "
            "balanced braces and the column count of every row), markdown (`.md`) and a rendered page (`.png`). The frozen pack "
            "(`docs/thesis/final_results_pack.pdf`, `eval/figs_final_pack.py`) is untouched.\n\n")
    f.write("**Revision 2026-10-16.** " + "; ".join(f"{a} (`{b}`) became table {c}" for a, b, c in REMOVED) +
            f". The old figure files are removed from this folder; they remain in the git history (commit `{PREV}`, "
            f"`git show {PREV}:docs/thesis/figures_thesis/<name>.png`). F2 is now one panel (the heading-error panel moved to table T4); F6 is "
            "the time trace only (the per-flight RMSE moved to table T6); F5 and F7 are unchanged. T7 (failure behaviour) and T8 (hindsight "
            "ratio) are new.\n\n")
    f.write(f"**Colour mapping (Okabe–Ito, colour-blind safe; fixed across every figure):** {PAL}. Solid lines / filled marks = live; dashed lines / "
            "open marks = hindsight. No log axes anywhere.\n\n")
    f.write("**Scorecard categories (T1):** BEST = a stated ordering puts it first; TIED = no ordering is claimed (or all pass the same criteria); "
            "BEHIND = a stated ordering or failed similarity verdict puts it below; FAILED = does not bound position; PASSED = met its pre-registered "
            "criteria with no comparison (L, FGO only); N/A = not run. BEHIND, PASSED and N/A are additions to best / tied / failed, used "
            "where those three do not fit.\n\n")
    f.write("| id | kind | files | title | status | checks | log-scale handling |\n|---|---|---|---|---|---|---|\n")
    for it in ITEMS:
        okc = sum(c[4] for c in it["checks"])
        files = ", ".join(f"`{x}`" for x in it["files"])
        f.write(f"| {it['id']} | {it['kind']} | {files} | {it['title']} | {it['status']} | {okc}/{len(it['checks'])} | {it['logscale']} |\n")
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
        f.write(f"### {it['id']} ({it['kind']}): {it['title']}\n\n- **Caption:** {it['caption']}\n- **Inputs:** {it['inputs']}\n- **numbers.md rows:** {it['rows']}\n")
        if it["uncheck"]:
            f.write(f"- **Not cross-checkable:** {it['uncheck']}\n")
        f.write("\n| check | computed | expected | source | match |\n|---|---|---|---|---|\n")
        for c in it["checks"]:
            f.write(f"| {c[0]} | `{c[1]}` | `{c[2]}` | {c[3]} | {'yes' if c[4] else '**NO**'} |\n")
        f.write("\n")
print("wrote", INDEX)
for it in ITEMS:
    print(f"  {it['id']:3s} {it['kind']:8s} checks {sum(c[4] for c in it['checks'])}/{len(it['checks'])}")
