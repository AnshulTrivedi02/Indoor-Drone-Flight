#!/usr/bin/env python3
"""Post-process docs/thesis/figures_thesis/captions/<fid>.md to replace the generic "Verdict: see TA_verdicts.md" line
with a specific pointer naming the exact TA_verdicts.md row ids (restyle brief: "Each caption points to its row(s) by
id"). RESTYLE (2026-11-02 v2): F2/F9/F5/F6/F7/A1/A2/A3 now get their verdict pointer from a `verdict=` kwarg baked
directly into their save()/save_table() call (eval/figs_thesis.py), so it shows on the combined PDF's own caption page
too, not just the standalone caption file - this script no longer touches them (listing them here would double-append).
Only R3, R5, R6 and methods_architecture are NOT built via save()/save_table() (they're figs_thesis_results.py /
figs_thesis_drift.py / figs_thesis_drift9.py / figs_thesis_methods.py, which call thesis_style.write_caption() directly),
so this script still patches those four. Idempotent. Run from the repo root after regenerating those four:
    python3 eval/add_caption_verdict_pointers.py"""
import os
D = "docs/thesis/figures_thesis/captions"
# D113 (2026-11-02, coordinator ruling): captions carry no verdict sentences/labels anywhere in the body; each one
# ENDS with exactly this pointer form. R3, R5 and methods_architecture are all descriptive (no TA_verdicts.md row of
# their own), so they share the "none (descriptive)" wording rather than each writing its own explanation inline -
# the reason each is descriptive is in index_results.md / index_drift.md / index_methods.md, not on the caption.
# R6 (2026-11-03, figs-1a-drift9 brief): the 9-flight restyled copy of fl_1A_unaligned_paths. Unlike R3/R5 (one
# representative flight, a different population from any registered test's own sample), R6 shows all 9 flights of
# Experiment 1A - the population H1.1's own registered sample (flights 4-10) is drawn from, even though it is not itself
# identical to that 7-flight sample (see index_drift9.md's notes and R6-2 in the handover for the exact distinction).
POINTERS = {
    "R3": "Verdicts: Table A.4, none (descriptive).",
    "R5": "Verdicts: Table A.4, none (descriptive).",
    "methods_architecture": "Verdicts: Table A.4, none (descriptive).",
    "R6": "Verdicts: Table A.4, rows H1.1.",
}
# Every generic/placeholder/earlier pointer form this script (or save()/save_table()'s own default) has ever written,
# so a re-run after any of those wordings changes is still idempotent.
OLD_FORMS = (
    "Verdict: see docs/thesis/tables/TA_verdicts.md.",
    "Verdict rows: see docs/thesis/tables/TA_verdicts.md.",
    "Verdicts: Table A.4, none (descriptive).",
    "Verdict rows (docs/thesis/tables/TA_verdicts.md): no verdict row attaches to this figure (descriptive; flight 3's "
    "sample differs from H1.1's registered 7-flight sample, so this is not H1.1 evidence). See TA_verdicts.md Experiment 1 "
    "rows for the scored Experiment 1 hypotheses.",
    "Verdict rows (docs/thesis/tables/TA_verdicts.md): no verdict row attaches to this figure (descriptive; it shows the "
    "mechanism behind the heading-error decomposition, not a scored test in its own right).",
    "No hypothesis/check verdict attaches to this figure (architecture description only); see "
    "docs/thesis/tables/TA_verdicts.md for the full verdict table.",
)
for fid, line in POINTERS.items():
    p = os.path.join(D, fid + ".md")
    c = open(p).read().rstrip("\n")
    for generic in OLD_FORMS:
        if c.endswith(generic):
            c = c[: -len(generic)].rstrip("\n")
            break
    c = c + "\n\n" + line + "\n"
    open(p, "w").write(c)
    print("updated", fid)
