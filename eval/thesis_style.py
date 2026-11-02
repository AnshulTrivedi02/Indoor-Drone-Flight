#!/usr/bin/env python3
"""Shared style constants for the restyled reader-facing thesis figure set (figures_thesis/).

RS-1 (2026-11-02, restyle brief): text width = 160 mm (6.30 in) at A4 with 25 mm margins. Full-width figures are
drawn at this physical width so that, placed in the thesis at 100%% (no LaTeX width= scaling needed beyond
\\textwidth), their already-set point-sized fonts (9-10 pt tick/annotation, 10-11 pt axis label) read as 11 pt
body text. Change TEXT_WIDTH_IN here to change the decision everywhere that imports it.

RS-2 (2026-11-02): each figure's draft caption lives at docs/thesis/figures_thesis/captions/<figure_id>.md.

Palette, markers and rcParams here are copied from eval/figs_thesis.py's existing style block (unchanged by the
restyle: palette, font sizes and line weights were already within the house rules) so every generator shares one
definition instead of four near-duplicates.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CAPTIONS_DIR = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "captions")  # RS-2
os.makedirs(CAPTIONS_DIR, exist_ok=True)

# RS-1: text width at final print size.
TEXT_WIDTH_IN = 6.30          # 160 mm
TEXT_WIDTH_MM = 160.0
HALF_WIDTH_IN = 3.02          # two side-by-side panels with a small gutter (not used unless noted)

# Okabe-Ito (colour-blind safe). One fixed colour and one marker shape per estimator, in every figure.
C = {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"}
MK = {"EKF3": "o", "UKF": "^", "FGO": "s"}
TRUTH = "#999999"                      # reserved for truth / references (never an estimator)
INK, INK2, GRID, SURF, WALL = "#111111", "#4d4d4d", "#e4e4e4", "#ffffff", "#5e5e5e"
EST = ("EKF3", "UKF", "FGO")

RCPARAMS = {"font.size": 10.5, "axes.titlesize": 11, "axes.labelsize": 10.5, "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5, "legend.fontsize": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
            "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.grid": True, "grid.color": GRID,
            "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.facecolor": SURF, "axes.facecolor": SURF,
            "savefig.facecolor": SURF, "lines.linewidth": 1.2, "lines.markersize": 5, "axes.spines.top": False,
            "axes.spines.right": False, "axes.linewidth": 0.8, "pdf.fonttype": 42}


def write_caption(fig_id, text):
    """RS-2: write the draft caption for one figure to captions/<fig_id>.md, plain text, one paragraph."""
    path = os.path.join(CAPTIONS_DIR, f"{fig_id}.md")
    with open(path, "w") as f:
        f.write(text.strip() + "\n")
    return path
