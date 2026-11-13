#!/usr/bin/env python3
"""Build the complete thesis assets bundle (user request 2026-11-13). Reads existing outputs only: no generator is run and no
number is changed.

Outputs (all under docs/thesis/):
  thesis_assets/thesis_complete.pdf      every numbered item (33) in thesis order: contents page, then per chapter figures
                                         before tables, appendix last; each item's rendered page(s) with its draft caption
  thesis_assets/tables_tex/tab_<n>.tex   every numbered table as LaTeX (booktabs), \\caption and \\label{tab:<n>}
  thesis_assets/figures/fig_<n>.pdf      every figure PDF, named by thesis number, plus figures.tex (one figure block each)
  thesis_assets/index.md                 number, title, files, source generator
  thesis_assets_<date>.zip               the four items above

Check: every numbered item listed in figures_thesis/index.md, index_methods.md and index_results.md appears exactly once in
ITEMS, and ITEMS has nothing else. A miss or a duplicate fails the build.

Table LaTeX: the generator's own .tex where one exists (its \\label rewritten to the thesis number); Table A.4 is converted
from its .md (longtable, booktabs); Tables A.1-A.3 are rendered by their generator as images only (no .md/.tex), so their
LaTeX places the rendered PDF page(s) inside a table environment, stated in the file.

Usage: ~/venv-evo/bin/python eval/build_thesis_assets.py [--date 2026-11-13]"""
import ast, glob, os, re, shutil, sys, textwrap, zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from PIL import Image                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
T = os.path.join(ROOT, "docs", "thesis"); FT = os.path.join(T, "figures_thesis"); TB = os.path.join(T, "tables")
OUT = os.path.join(T, "thesis_assets")
DATE = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else "2026-11-13"
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else DATE
A4 = (8.27, 11.69)


def _load_tex():
    tree = ast.parse(open(os.path.join(HERE, "figs_thesis.py"), encoding="utf-8").read())
    names = {"tex", "TEX_ESC", "TEX_UNI"}
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in names) or
            (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets))]
    ns = {"re": re}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "eval/figs_thesis.py", "exec"), ns)
    return ns["tex"]


tex = _load_tex()
EXTRA_UNI = {"σ": r"$\sigma$", "χ": r"$\chi$", "ψ": r"$\psi$", "√": r"$\surd$", "²": r"$^2$", "µ": r"$\mu$", "≈": r"$\approx$",
             "≠": r"$\neq$", "→": r"$\rightarrow$", "⚑": "", "✓": r"$\checkmark$",
             "δ": r"$\delta$", "Δ": r"$\Delta$", "ν": r"$\nu$", "ε": r"$\varepsilon$", "θ": r"$\theta$", "ω": r"$\omega$",
             "λ": r"$\lambda$", "π": r"$\pi$", "ρ": r"$\rho$", "τ": r"$\tau$", "φ": r"$\phi$", "α": r"$\alpha$",
             "β": r"$\beta$", "γ": r"$\gamma$", "κ": r"$\kappa$", "Σ": r"$\Sigma$", "∞": r"$\infty$", "∈": r"$\in$",
             "⁻": r"$^-$", "¹": r"$^1$", "³": r"$^3$", "⁴": r"$^4$", "⁵": r"$^5$", "⁶": r"$^6$", "⁸": r"$^8$", "⁹": r"$^9$",
             "⁰": r"$^0$", "₀": r"$_0$", "₁": r"$_1$", "₂": r"$_2$", "ᵀ": r"$^T$", "′": r"$'$", "…": r"\ldots{}",
             "←": r"$\leftarrow$", "↔": r"$\leftrightarrow$", "·": r"$\cdot$"}


def ltx(s):
    for k, v in EXTRA_UNI.items():
        s = s.replace(k, "\x00%d\x00" % ord(k))
    try:
        s = tex(s)
    except ValueError as e:
        raise SystemExit(f"unmapped character for LaTeX: {e}")
    for k, v in EXTRA_UNI.items():
        s = s.replace("\x00%d\x00" % ord(k), v)
    return s


REF_TOK = (r"D\d{1,3}(?:\([a-z]\))?(?:\s*(?:item|items)\s*\d+(?:\s*(?:--|[-–])\s*\d+)?)?",
           r"[\w\\./-]+\.(?:md|py|parm|json|conf|cpp|h|jobs):\d+(?:(?:--|[-–])\d+)?", r"\bM:\d+(?:(?:--|[-–])\d+)?",
           r"\b20\d\d-\d\d-\d\d(?:[ T]\d\d:\d\d(?::\d\d)?)?\b", r"\bcommit\s+[0-9a-f]{7,}\b", r"`?[0-9a-f]{7}`?(?=\))")
_REF = re.compile("|".join(REF_TOK))
_PAREN = re.compile(r"\s*[\(\[]\s*(?:(?:" + "|".join(REF_TOK) + r"|ruling|rulings|user|item|items|\d+|ruled|and|,|;|\s)+)[\)\]]")


def clean_refs(t):
    """Remove decision numbers, METHODOLOGY line citations, dates and commit hashes from caption/note text. Parentheticals
    that hold only such references are dropped whole; inline references are removed and the punctuation tidied."""
    t2 = _PAREN.sub("", t)
    t2 = _REF.sub("", t2)
    t2 = re.sub(r"\(\s*[,;]?\s*\)|\[\s*[,;]?\s*\]", "", t2)
    t2 = re.sub(r"\s+([,;.:])", r"\1", t2)
    t2 = re.sub(r"([,;])\s*([,;])", r"\1", t2)
    t2 = re.sub(r"\(\s*[,;]\s*", "(", t2); t2 = re.sub(r"\s*[,;]\s*\)", ")", t2)
    t2 = re.sub(r"\bsince\s*[,;]\s*", "since ", t2)
    t2 = re.sub(r"\s{2,}", " ", t2)
    return t2


def _nums(t):
    return re.findall(r"\d+(?:\.\d+)?", t)


CLEAN_LOG = []


def clean_line(line, where):
    new = clean_refs(line)
    if new != line:
        refnums = [n for m in _REF.finditer(line) for n in _nums(m.group(0))]
        paren = [n for m in _PAREN.finditer(line) for n in _nums(m.group(0))]
        before, after = _nums(line), _nums(new)
        rem = list(before)
        for n in after:
            if n in rem:
                rem.remove(n)
            else:
                raise SystemExit(f"clean_refs introduced number {n} in {where}")
        allowed = list(refnums + paren)
        for n in rem:
            if n in allowed:
                allowed.remove(n)
            else:
                raise SystemExit(f"clean_refs would remove a non-reference number {n} in {where}: {line[:200]}")
        CLEAN_LOG.append((where, len(rem)))
    return new


# (number, kind, internal id, base path (no extension), source generator)
ITEMS = [
    ("Figure 3.1", "fig", "METHODS_ARCH", "figures_thesis/methods_architecture", "eval/figs_thesis_methods.py"),
    ("Table 3.1", "tab", "methods_estimator_design", "tables/methods_estimator_design", "eval/figs_thesis_methods.py"),
    ("Table 3.2", "tab", "methods_noise_parity", "tables/methods_noise_parity", "eval/figs_thesis_methods.py"),
    ("Table 3.3", "tab", "methods_noise_exceptions", "tables/methods_noise_exceptions", "eval/figs_thesis_methods.py"),
    ("Table 3.4", "tab", "methods_experiment_matrix", "tables/methods_experiment_matrix", "eval/figs_thesis_methods.py"),
    ("Figure 4.1", "fig", "F2", "figures_thesis/F2_heading_stops_sideways_drift", "eval/figs_thesis.py"),
    ("Figure 4.1b", "fig", "F9", "figures_thesis/F9_heading_error_closed_loop", "eval/figs_thesis.py"),
    ("Figure 4.1c", "fig", "R5", "figures_thesis/R5_drift_unaligned", "eval/figs_thesis_drift.py"),
    ("Figure 4.1d", "fig", "R6", "figures_thesis/R6_drift_9flights", "eval/figs_thesis_drift9.py"),
    ("Figure 4.2", "fig", "R3", "figures_thesis/R3_trajectory_overlay", "eval/figs_thesis_results.py"),
    ("Table 4.1", "tab", "T2", "tables/T2_accuracy_heading", "eval/figs_thesis.py"),
    ("Table 4.1b", "tab", "T2B", "tables/T2B_ekf3_heading_replay", "eval/figs_thesis.py"),
    ("Table 4.2", "tab", "T3", "tables/T3_blank_floor", "eval/figs_thesis.py"),
    ("Table 4.3", "tab", "T4", "tables/T4_closed_loop", "eval/figs_thesis.py"),
    ("Table 4.3b", "tab", "T4F", "tables/T4F_closed_loop_full_speed", "eval/figs_thesis.py"),
    ("Table 4.4", "tab", "T9", "tables/T9_1A_fitted_vs_raw", "eval/figs_thesis.py"),
    ("Figure 5.1", "fig", "F5", "figures_thesis/F5_T_tags_known_positions", "eval/figs_thesis.py"),
    ("Figure 5.2", "fig", "F7", "figures_thesis/F7_L_loop_closure", "eval/figs_thesis.py"),
    ("Figure 5.3", "fig", "F6", "figures_thesis/F6_O_outdoor_indoor", "eval/figs_thesis.py"),
    ("Table 5.1", "tab", "T6", "tables/T6_O_indoor_rmse", "eval/figs_thesis.py"),
    ("Table 5.2", "tab", "T8", "tables/T8_hindsight_ratio", "eval/figs_thesis.py"),
    ("Table 6.1", "tab", "T5", "tables/T5_H_tag_loss_drift", "eval/figs_thesis.py"),
    ("Table 7.1", "tab", "T1", "tables/T1_scorecard", "eval/figs_thesis.py"),
    ("Table 7.2", "tab", "T7", "tables/T7_failure_behaviour", "eval/figs_thesis.py"),
    ("Table 7.3", "tab", "R1", "tables/R1_hypothesis_scorecard", "eval/figs_thesis_results.py"),
    ("Table 7.4", "tab", "R2", "tables/R2_corrections_by_discovery", "eval/figs_thesis_results.py"),
    ("Table 7.5", "tab", "R4", "tables/R4_information_vs_estimator", "eval/figs_thesis_results.py"),
    ("Table 8.1", "tab", "realflight_compute", "tables/realflight_compute", "eval/figs_thesis_methods.py"),
    ("Table 8.2", "tab", "realflight_safety_findings", "tables/realflight_safety_findings", "eval/figs_thesis_methods.py"),
    ("Table A.1", "app", "A1", "figures_thesis/A1_closed_loop_builds", "eval/figs_thesis.py"),
    ("Table A.2", "app", "A2", "figures_thesis/A2_H_and_safety", "eval/figs_thesis.py"),
    ("Table A.3", "app", "A3", "figures_thesis/A3_F1_cost_ablations", "eval/figs_thesis.py"),
    ("Table A.4", "app", "TA", "figures_thesis/tables_extra/TA_verdicts", "eval/ta_verdicts_check.py"),
]
CAPTION_FILE = {"METHODS_ARCH": "methods_architecture", "F2": "F2", "F9": "F9", "R5": "R5", "R6": "R6", "R3": "R3",
                "F5": "F5", "F7": "F7", "F6": "F6", "A1": "A1", "A2": "A2", "A3": "A3"}


def slug(num):                     # "Table 4.3b" -> "4-3b", "Table A.4" -> "A-4"
    return num.split()[1].replace(".", "-")


def index_numbers():
    found = []
    for name, pat in (("index.md", r"^\| (Figure|Table) ([0-9A]\.[0-9]+[a-z]?)"), ("index_methods.md", r"^\| (Figure|Table) ([0-9]\.[0-9]+[a-z]?) "),
                      ("index_results.md", r"^\| \*\*(Figure|Table) ([0-9]\.[0-9]+[a-z]?)\*\*")):
        txt = open(os.path.join(FT, name), encoding="utf-8").read().splitlines()
        seen = set()
        for l in txt:
            m = re.match(pat, l)
            if m:
                seen.add(f"{m.group(1)} {m.group(2)}")
        found.append((name, seen))
    return found


def check_coverage():
    mine = [n for n, *_ in ITEMS]
    dup = {n for n in mine if mine.count(n) > 1}
    allidx = set()
    for name, s in index_numbers():
        allidx |= s
    missing = sorted(allidx - set(mine)); extra = sorted(set(mine) - allidx)
    ok = not dup and not missing and not extra and len(mine) == 33
    print(f"coverage: {len(mine)} items; indexes list {len(allidx)} distinct; duplicates {sorted(dup)}; missing {missing}; "
          f"not in any index {extra}: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)


def pngs(base):
    p = os.path.join(T, base)
    one = p + ".png"
    pages = sorted(glob.glob(p + "_p[0-9]*.png"), key=lambda s: int(re.search(r"_p(\d+)\.png$", s).group(1)))
    pages = [q for q in pages if "_sup_" not in q]
    if not pages and os.path.exists(one):
        pages = [one]
    if not pages:
        raise SystemExit(f"no PNG for {base}")
    # superseded-section pages (D149) follow the main pages
    sup = sorted(glob.glob(p + "_sup_p[0-9]*.png")) + ([p + "_superseded.png"] if os.path.exists(p + "_superseded.png") else [])
    return pages + sup


def md_parts(base):
    """(title, intro paragraphs, notes) from a generated table .md"""
    txt = open(os.path.join(T, base + ".md"), encoding="utf-8").read().splitlines()
    title = re.sub(r"^#\s*", "", txt[0]).strip()
    intro, notes, in_tab = [], [], False
    for l in txt[1:]:
        if l.startswith("|"):
            in_tab = True; continue
        if l.startswith("<!--") or not l.strip():
            continue
        (notes if in_tab else intro).append(l.strip())
    return title, intro, notes


def caption_of(num, kind, iid, base):
    if iid in CAPTION_FILE:
        return open(os.path.join(FT, "captions", CAPTION_FILE[iid] + ".md"), encoding="utf-8").read().strip()
    title, intro, _ = md_parts("tables/TA_verdicts" if iid == "TA" else base)
    return title + ("\n\n" + "\n\n".join(intro) if intro else "")


def wrap(text, width=110):
    out = []
    for para in text.split("\n"):
        para = para.replace("**", "").replace("`", "")
        out += textwrap.wrap(para, width) if para.strip() else [""]
    return out


def build_pdf(path):
    with PdfPages(path) as pdf:
        fig = plt.figure(figsize=A4)
        fig.text(0.07, 0.95, "Thesis figures and tables: complete set", fontsize=17, weight="bold", va="top")
        fig.text(0.07, 0.918, f"All {len(ITEMS)} numbered items in thesis order, each with its draft caption.", fontsize=8.5,
                 va="top", color="#444444")
        fig.text(0.07, 0.903, f"Built {DATE} by eval/build_thesis_assets.py from the committed outputs (no generator run).",
                 fontsize=8.5, va="top", color="#444444")
        y = 0.87
        for num, kind, iid, base, gen in ITEMS:
            title = caption_of(num, kind, iid, base).split("\n")[0]
            title = re.sub(r"^(Figure|Table) [0-9A]\.[0-9]+[a-z]?(\s*\(provisional\))?\.\s*", "", title)
            fig.text(0.08, y, f"{num:<12} {title}"[:120], fontsize=7.6, va="top", family="DejaVu Sans")
            y -= 0.0235
        pdf.savefig(fig); plt.close(fig)
        for num, kind, iid, base, gen in ITEMS:
            pages = pngs(base); cap = caption_of(num, kind, iid, base)
            for k, png in enumerate(pages):
                last = k == len(pages) - 1
                fig = plt.figure(figsize=A4)
                fig.text(0.94, 0.985, f"{num}  ({iid}; {gen})  page {k + 1}/{len(pages)}", fontsize=6.5, color="#777777",
                         ha="right", va="top")
                im = Image.open(png); w, h = im.size
                lines = wrap(cap) if last else []
                cap_h = min(0.55, 0.0135 * len(lines) + (0.02 if lines else 0))
                room = 0.95 - 0.03 - cap_h
                aw = 0.90; ah = aw * (h / w) * (A4[0] / A4[1])
                if ah > room:
                    aw *= room / ah; ah = room
                ax = fig.add_axes([0.5 - aw / 2, 0.95 - ah, aw, ah]); ax.imshow(im); ax.axis("off")
                yy = 0.95 - ah - 0.02
                for ln in lines:
                    if yy < 0.02:
                        fig.text(0.06, yy, "[caption continues in index.md]", fontsize=6.5, color="#777777", va="top"); break
                    fig.text(0.06, yy, ln, fontsize=7.2, va="top"); yy -= 0.0135
                pdf.savefig(fig); plt.close(fig)


def relabel_tex(src, num):
    s = open(src, encoding="utf-8").read()
    lab = f"tab:{slug(num)}"
    s, n = re.subn(r"\\label\{[^}]*\}", lambda m: "\\label{" + lab + "}", s)
    if n == 0:
        s = s.replace("\\end{table}", f"\\label{{{lab}}}\n\\end{{table}}", 1)
    pre = "\\caption{" + ltx(num) + ". "
    s, nc = re.subn(r"\\caption\{", lambda m: pre, s, count=1)
    out = []
    for ln in s.splitlines():
        if ln.lstrip().startswith("\\caption{") or ln.lstrip().startswith("\\textit{Note.}"):
            ln = clean_line(ln, num)
        elif ln.startswith("%"):
            ln = re.sub(r"\s*\(commit [0-9a-f]{7,}\)", "", ln)
        out.append(ln)
    head = f"% {num}: exported by eval/build_thesis_assets.py from {os.path.relpath(src, ROOT)}; label {lab}.\n"
    return head + "\n".join(out) + "\n"


def _cells(line):
    parts = re.split(r"(?<!\\)\|", line.strip())[1:-1]
    return [c.strip().replace("\\\\|", "|").replace("\\|", "|") for c in parts]


def md_to_longtable(base, num, cap_first):
    """Every markdown table block in the file becomes its own longtable (Table A.4: the register, then its superseded
    appendix section); cells are split on unescaped pipes only."""
    txt = open(os.path.join(T, base + ".md"), encoding="utf-8").read().splitlines()
    blocks, cur, lead, lead_txt = [], [], [], ""
    for l in txt:
        if l.startswith("|"):
            if not cur:
                lead_txt = " ".join(x.strip() for x in lead if x.strip() and not x.startswith(("#", "<!--")))[:400]
            if not re.match(r"^\|\s*-{3}", l):
                cur.append(_cells(l))
        else:
            if cur:
                blocks.append((lead_txt, cur)); cur = []; lead = []
            lead.append(l)
    if cur:
        blocks.append((lead_txt, cur))
    L = [f"% {num}: exported by eval/build_thesis_assets.py ({DATE}) from {base}.md (converted; needs booktabs, longtable).",
         f"% {len(blocks)} table block(s) in the source, each a longtable below.", "\\footnotesize"]
    for bi, (lt, rows) in enumerate(blocks):
        hdr, body = rows[0], rows[1:]
        nc = len(hdr)
        colspec = "".join(f"p{{\\dimexpr {1 / nc:.3f}\\linewidth-2\\tabcolsep\\relax}}" for _ in range(nc))
        hrow = " & ".join("\\textbf{" + ltx(h) + "}" for h in hdr) + " \\\\"
        if bi == 0:
            cap = f"\\caption{{{ltx(num)}. {ltx(clean_line(cap_first, num))}}}\\label{{tab:{slug(num)}}}\\\\"
        else:
            cap = f"\\multicolumn{{{nc}}}{{p{{\\linewidth}}}}{{\\textit{{{ltx(num)} (continued). {ltx(lt)}}}}}\\\\"
        L += [f"\\begin{{longtable}}{{{colspec}}}", cap, "\\toprule", hrow, "\\midrule", "\\endfirsthead",
              "\\toprule", hrow, "\\midrule", "\\endhead"]
        for r in body:
            r = (r + [""] * nc)[:nc]
            L.append(" & ".join(ltx(c.replace("**", "").replace("`", "")) for c in r) + " \\\\")
        L += ["\\bottomrule", "\\end{longtable}", ""]
    L += ["\\normalsize"]
    return "\n".join(L) + "\n"


def image_table(base, num, cap):
    pages = sorted(glob.glob(os.path.join(T, base + "_p[0-9]*.pdf"))) or [os.path.join(T, base + ".pdf")]
    lab = f"tab:{slug(num)}"
    L = [f"% {num}: its generator renders this table as an image only (no .md/.tex source), so the rendered page(s) are placed",
         "% in a table environment. Copy the PDFs from figures/ alongside (named below).", "\\begin{table}[p]", "\\centering"]
    for k, p in enumerate(pages, 1):
        L.append(f"\\includegraphics[width=\\linewidth]{{figures/tab_{slug(num)}_p{k}.pdf}}\\par\\medskip")
    L += [f"\\caption{{{ltx(num)}. {ltx(clean_line(cap, num))}}}", f"\\label{{{lab}}}", "\\end{table}"]
    return "\n".join(L) + "\n", pages


def main():
    check_coverage()
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "tables_tex")); os.makedirs(os.path.join(OUT, "figures"))
    idx = ["# Thesis assets: index", "", f"Built {DATE} by `eval/build_thesis_assets.py` from the committed outputs; no generator run, "
           "no number changed. `thesis_complete.pdf` holds all items in this order with their draft captions.", "",
           "| number | title | file(s) in this bundle | source generator | source output |", "|---|---|---|---|---|"]
    figtex = [f"% Figures exported by eval/build_thesis_assets.py ({DATE}). Needs graphicx. Captions from figures_thesis/captions/*.md.", ""]
    for num, kind, iid, base, gen in ITEMS:
        cap = caption_of(num, kind, iid, base)
        first, *rest = cap.split("\n", 1)
        title = re.sub(r"^(Figure|Table) [0-9A]\.[0-9]+[a-z]?(\s*\(provisional\))?\.\s*", "", first).strip()
        body = rest[0].strip() if rest else ""
        files = []
        if kind == "fig":
            dst = f"figures/fig_{slug(num)}.pdf"
            shutil.copy2(os.path.join(T, base + ".pdf"), os.path.join(OUT, dst)); files.append(dst)
            figtex += ["\\begin{figure}[htbp]", "\\centering", f"\\includegraphics[width=\\linewidth]{{{dst}}}",
                       f"\\caption[{ltx(title)}]{{{ltx(title)} {ltx(' '.join(body.split()))}}}", f"\\label{{fig:{slug(num)}}}",
                       "\\end{figure}", ""]
        elif kind == "tab":
            dst = f"tables_tex/tab_{slug(num)}.tex"
            open(os.path.join(OUT, dst), "w", encoding="utf-8").write(relabel_tex(os.path.join(T, base + ".tex"), num)); files.append(dst)
        elif iid == "TA":
            title_md, intro, _ = md_parts("tables/TA_verdicts")
            dst = f"tables_tex/tab_{slug(num)}.tex"
            t = re.sub(r"^Table A\.4\.\s*", "", title_md)
            open(os.path.join(OUT, dst), "w", encoding="utf-8").write(md_to_longtable("tables/TA_verdicts", num, t)); files.append(dst)
        else:
            t = title + (" " + " ".join(body.split()) if body else "")
            s, pages = image_table(base, num, t)
            dst = f"tables_tex/tab_{slug(num)}.tex"
            open(os.path.join(OUT, dst), "w", encoding="utf-8").write(s); files.append(dst)
            for k, p in enumerate(pages, 1):
                d2 = f"figures/tab_{slug(num)}_p{k}.pdf"; shutil.copy2(p, os.path.join(OUT, d2)); files.append(d2)
        if kind in ("tab", "app"):
            os.makedirs(os.path.join(OUT, "tables_png"), exist_ok=True)
            for k, png in enumerate(pngs(base), 1):
                d3 = f"tables_png/tab_{slug(num)}_p{k}.png"; shutil.copy2(png, os.path.join(OUT, d3)); files.append(d3)
        srcs = sorted(os.path.relpath(f, T) for f in glob.glob(os.path.join(T, base) + "*") if not f.endswith(".png"))
        idx.append(f"| {num} | {title.replace('|', '/')} | " + ", ".join(f"`{f}`" for f in files) + f" | `{gen}` | "
                   + ", ".join(f"`{s}`" for s in srcs[:4]) + " |")
    open(os.path.join(OUT, "figures", "figures.tex"), "w", encoding="utf-8").write("\n".join(figtex))
    idx += ["", "Notes:", "- Tables A.1-A.3 are rendered by their generator as images only; their LaTeX places the rendered page(s) "
            "(`figures/tab_A-*_p*.pdf`) in a table environment.",
            "- Table A.4 is converted from `tables/TA_verdicts.md` (longtable).",
            "- Labels: `tab:<n>` and `fig:<n>`, with `.` replaced by `-` (e.g. `tab:4-3b`, `fig:4-1b`, `tab:A-4`).",
            "- The `.tex` files need `booktabs` (and `longtable` for Table A.4, `graphicx` for figures and Tables A.1-A.3); "
            "they were checked for balanced braces only (no TeX on the build machine)."]
    open(os.path.join(OUT, "index.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
    build_pdf(os.path.join(OUT, "thesis_complete.pdf"))
    # Part II: every candidate figure (not yet numbered), its own PDF/table and caption, and the candidates PDF appended
    CD = os.path.join(FT, "candidates"); cdst = os.path.join(OUT, "candidates")
    os.makedirs(os.path.join(cdst, "captions"))
    ncand = 0
    for f in sorted(glob.glob(os.path.join(CD, "[A-D][0-9][0-9]_*.pdf")) + glob.glob(os.path.join(CD, "[A-D][0-9][0-9]_*.md"))):
        shutil.copy2(f, cdst); ncand += 1
    for f in sorted(glob.glob(os.path.join(CD, "captions", "*.md"))):
        shutil.copy2(f, os.path.join(cdst, "captions"))
    for f in sorted(glob.glob(os.path.join(CD, "index_*.md"))):
        shutil.copy2(f, cdst)
    ncap = len(glob.glob(os.path.join(cdst, "captions", "*.md")))
    cpdf = os.path.join(CD, "thesis_figures_candidates.pdf")
    tmp = os.path.join(OUT, "_part1.pdf"); os.replace(os.path.join(OUT, "thesis_complete.pdf"), tmp)
    import subprocess
    subprocess.run(["pdfunite", tmp, cpdf, os.path.join(OUT, "thesis_complete.pdf")], check=True)
    os.remove(tmp)
    with open(os.path.join(OUT, "index.md"), "a", encoding="utf-8") as fh:
        fh.write(f"\n## Part II: candidate figures (not yet numbered)\n\n{ncap} candidates (`candidates/`: each candidate's own PDF or "
                 "table and its caption under `candidates/captions/`; the indexes `candidates/index_*.md` give titles and sources). "
                 "They are appended to `thesis_complete.pdf` after the numbered items, as Part II, at their original quality. Their "
                 "captions are the candidate drafts and have not been through the plain-words caption pass.\n")
    print(f"Part II: {ncap} candidate captions, {ncand} candidate files; candidates PDF appended")
    # brace balance check on every .tex
    bad = []
    for f in glob.glob(os.path.join(OUT, "**", "*.tex"), recursive=True):
        s = re.sub(r"\\[{}]", "", open(f, encoding="utf-8").read())
        if s.count("{") != s.count("}"):
            bad.append(os.path.relpath(f, OUT))
    print("tex brace balance:", "PASS" if not bad else f"FAIL {bad}")
    print(f"caption/note reference cleaning: {len(CLEAN_LOG)} lines changed; every removed number was a reference (checked)")
    z = os.path.join(T, f"thesis_assets_{TAG}.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(glob.glob(os.path.join(OUT, "**", "*"), recursive=True)):
            if os.path.isfile(f):
                zf.write(f, os.path.join("thesis_assets", os.path.relpath(f, OUT)))
    print(f"wrote {os.path.relpath(OUT, ROOT)} and {os.path.relpath(z, ROOT)}")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
