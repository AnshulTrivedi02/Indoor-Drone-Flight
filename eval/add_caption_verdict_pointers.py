#!/usr/bin/env python3
"""Post-process docs/thesis/figures_thesis/captions/<fid>.md to replace the generic "Verdict: see TA_verdicts.md" line
with a specific pointer naming the exact TA_verdicts.md row ids (restyle brief: "Each caption points to its row(s) by
id"). RESTYLE (2026-11-02 v2): F2/F9/F5/F6/F7/A1/A2/A3 now get their verdict pointer from a `verdict=` kwarg baked
directly into their save()/save_table() call (eval/figs_thesis.py), so it shows on the combined PDF's own caption page
too, not just the standalone caption file - this script no longer touches them (listing them here would double-append).
Only R3, R5 and methods_architecture are NOT built via save()/save_table() (they're figs_thesis_results.py /
figs_thesis_drift.py / figs_thesis_methods.py, which call thesis_style.write_caption() directly), so this script still
patches those three. Idempotent. Run from the repo root after regenerating those three:
    python3 eval/add_caption_verdict_pointers.py"""
import os
D = "docs/thesis/figures_thesis/captions"
POINTERS = {
    "R3": "Verdict rows (docs/thesis/tables/TA_verdicts.md): no verdict row attaches to this figure (descriptive; flight 3's "
          "sample differs from H1.1's registered 7-flight sample, so this is not H1.1 evidence). See TA_verdicts.md Experiment 1 "
          "rows for the scored Experiment 1 hypotheses.",
    "R5": "Verdict rows (docs/thesis/tables/TA_verdicts.md): no verdict row attaches to this figure (descriptive; it shows the "
          "mechanism behind the heading-error decomposition, not a scored test in its own right).",
    "methods_architecture": "No hypothesis/check verdict attaches to this figure (architecture description only); see "
          "docs/thesis/tables/TA_verdicts.md for the full verdict table.",
}
for fid, line in POINTERS.items():
    p = os.path.join(D, fid + ".md")
    c = open(p).read().rstrip("\n")
    for generic in ("Verdict: see docs/thesis/tables/TA_verdicts.md.", "Verdict rows: see docs/thesis/tables/TA_verdicts.md.", line):
        if c.endswith(generic):
            c = c[: -len(generic)].rstrip("\n")
            break
    c = c + "\n\n" + line + "\n"
    open(p, "w").write(c)
    print("updated", fid)
