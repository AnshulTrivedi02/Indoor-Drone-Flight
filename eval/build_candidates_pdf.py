#!/usr/bin/env python3
"""Build docs/thesis/figures_thesis/candidates/thesis_figures_candidates.pdf (decision D124, 2026-11-04).

One page per candidate figure (A01-A20, B01-B08, C01-C07, D01-D08): its id and proposed title (from the group's
index_<g>.md), the figure (its PNG, scaled to the page width) and its draft caption (captions/<id>.md, verbatim).
Markdown-only table candidates (e.g. B08, C03, C04) are rendered as table pages from their .md file. A contents page
comes first. Reads only the candidate outputs; changes nothing else. Every caption is already checked by
eval/caption_verdict_check.py, and every number in it by its group generator (eval/figs_cand_<g>.py).

Usage: python3 eval/build_candidates_pdf.py"""
import glob
import os
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from PIL import Image                                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CD = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "candidates")
OUT = os.path.join(CD, "thesis_figures_candidates.pdf")
A4 = (8.27, 11.69)
GROUP = {"A": "Setup and Experiment 1", "B": "Experiments 2 to 5 and 5S", "C": "Extensions E2, E3 and E5",
         "D": "Extensions E4 and E6, and the exploratory ablation"}


def titles():
    t = {}
    for f in sorted(glob.glob(os.path.join(CD, "index_*.md"))):
        for ln in open(f, encoding="utf-8"):
            m = re.match(r"^\|\s*([A-D]\d\d)\s*\|\s*([^|]+?)\s*\|", ln)
            if m and m.group(1) not in t:
                t[m.group(1)] = m.group(2).replace("`", "")
    return t


def source(cid):
    pngs = [p for p in glob.glob(os.path.join(CD, f"{cid}*.png")) if re.match(rf"{cid}(_|\.)", os.path.basename(p))]
    if pngs:
        return "png", sorted(pngs)[0]
    mds = [p for p in glob.glob(os.path.join(CD, f"{cid}*.md")) if re.match(rf"{cid}_", os.path.basename(p))]
    if mds:
        return "md", sorted(mds)[0]
    raise SystemExit(f"{cid}: no figure or table file found")


def wrap_block(text, width):
    out = []
    for para in text.strip().split("\n"):
        para = para.strip().replace("**", "").replace("`", "")
        out += textwrap.wrap(para, width) if para else [""]
    return out


def table_rows(md):
    rows = []
    for ln in open(md, encoding="utf-8"):
        if ln.startswith("|") and not re.match(r"^\|\s*-{3}", ln):
            rows.append([c.strip().replace("**", "").replace("`", "") for c in ln.strip().strip("|").split("|")])
    return rows


def header(fig, cid, title):
    fig.text(0.06, 0.965, f"{cid}  {title}", fontsize=11, weight="bold", va="top", ha="left", wrap=True)
    fig.text(0.94, 0.985, f"candidate {cid} (group {cid[0]}: {GROUP[cid[0]]})", fontsize=7, color="#666666",
             va="top", ha="right")


def caption_text(fig, cap, top):
    lines = wrap_block(cap, 105)
    y = top
    for ln in lines:
        fig.text(0.06, y, ln, fontsize=8, va="top", ha="left")
        y -= 0.0145
    return y


def figure_page(pdf, cid, title, png, cap):
    fig = plt.figure(figsize=A4)
    header(fig, cid, title)
    im = Image.open(png)
    w, h = im.size
    aw = 0.88
    ah = aw * (h / w) * (A4[0] / A4[1])
    cap_lines = len(wrap_block(cap, 105))
    room = 0.92 - 0.04 - cap_lines * 0.0145 - 0.03
    if ah > room:                    # very tall figure or long caption: shrink to fit, keep the aspect
        aw *= room / ah
        ah = room
    ax = fig.add_axes([0.5 - aw / 2, 0.92 - ah, aw, ah])
    ax.imshow(im)
    ax.axis("off")
    caption_text(fig, cap, 0.92 - ah - 0.02)
    pdf.savefig(fig)
    plt.close(fig)


def table_pages(pdf, cid, title, md, cap):
    rows = table_rows(md)
    head, body = rows[0], rows[1:]
    per = 22
    chunks = [body[i:i + per] for i in range(0, len(body), per)] or [[]]
    for k, chunk in enumerate(chunks):
        fig = plt.figure(figsize=A4)
        header(fig, cid, title + (f" (part {k + 1} of {len(chunks)})" if len(chunks) > 1 else ""))
        ax = fig.add_axes([0.04, 0.42, 0.92, 0.50])
        ax.axis("off")
        cells = [["\n".join(textwrap.wrap(c, 22)) for c in r] for r in chunk]
        tb = ax.table(cellText=cells, colLabels=["\n".join(textwrap.wrap(c, 22)) for c in head], loc="upper center",
                      cellLoc="left")
        tb.auto_set_font_size(False)
        tb.set_fontsize(6.5)
        tb.scale(1, 2.4)
        if k == len(chunks) - 1:
            caption_text(fig, cap, 0.38)
        pdf.savefig(fig)
        plt.close(fig)


def main():
    t = titles()
    ids = sorted(os.path.basename(f)[:-3] for f in glob.glob(os.path.join(CD, "captions", "*.md")))
    with PdfPages(OUT) as pdf:
        fig = plt.figure(figsize=A4)
        fig.text(0.06, 0.95, "Candidate thesis figures", fontsize=18, weight="bold", va="top")
        fig.text(0.06, 0.915, "Every walkthrough and summary plot not yet in figures_thesis/, at thesis quality, to "
                 "pick from (decision D124).", fontsize=9, va="top", color="#444444")
        fig.text(0.06, 0.898, "Each page: the figure (or table) and its draft caption, which ends with its Table A.4 "
                 "verdict pointer.", fontsize=9, va="top", color="#444444")
        y = 0.86
        for cid in ids:
            fig.text(0.08, y, f"{cid}   {t.get(cid, '')}"[:118], fontsize=7.6, va="top")
            y -= 0.0178
        pdf.savefig(fig)
        plt.close(fig)
        for cid in ids:
            kind, path = source(cid)
            cap = open(os.path.join(CD, "captions", f"{cid}.md"), encoding="utf-8").read()
            if kind == "png":
                figure_page(pdf, cid, t.get(cid, ""), path, cap)
            else:
                table_pages(pdf, cid, t.get(cid, ""), path, cap)
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(ids)} candidates")


if __name__ == "__main__":
    main()
