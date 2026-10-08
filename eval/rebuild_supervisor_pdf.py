#!/usr/bin/env python3
"""Rebuild a supervisor figure set's combined figures.pdf from its existing PNGs and INDEX.md captions (same page
layout as eval/figs_supervisor_2026_10_01.py), without re-reading any flight data (many bags are now zstd-packed).
Used 2026-10-08 so fig6's caption carries the divergence note (user request). The PNGs are unchanged.
Usage (venv-evo): python3 eval/rebuild_supervisor_pdf.py plots/supervisor_2026-10-01"""
import os, re, subprocess, sys, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
D = sys.argv[1]; INK2 = "#52514e"
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
commit = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
txt = open(os.path.join(D, "INDEX.md")).read()
figs = re.findall(r"## (\S+\.png): (.+?)\n\n- \*\*Status:\*\* (.+?)\n- \*\*Caption:\*\* (.+?)\n- \*\*Data source:\*\* (.+?)\n- \*\*Commit:\*\* `(\w+)`", txt, re.S)
with PdfPages(os.path.join(D, "figures.pdf")) as P:
    for png, title, kind, cap, src, fig_commit in figs:
        img = plt.imread(os.path.join(D, png))
        fig = plt.figure(figsize=(11.69, 8.27))
        ax = fig.add_axes([0.03, 0.26, 0.94, 0.70]); ax.imshow(img); ax.axis("off")
        fig.text(0.03, 0.235, "\n".join(textwrap.wrap(f"{title}  —  {kind}", 120)), fontsize=11.5, weight="bold", va="top")
        fig.text(0.03, 0.175, "\n".join(textwrap.wrap(cap, 165)), fontsize=9.5, va="top")
        fig.text(0.03, 0.045, "\n".join(textwrap.wrap(f"Source: {src}. Figure commit {fig_commit}; PDF rebuilt at {commit}.", 180)),
                 fontsize=8.5, va="top", color=INK2)
        P.savefig(fig); plt.close(fig)
print(f"rebuilt {D}/figures.pdf with {len(figs)} pages")
