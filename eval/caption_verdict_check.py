#!/usr/bin/env python3
"""D113 (2026-11-02, coordinator ruling): every reader-facing caption carries NO verdict sentences or verdict labels
(PASS / FAIL / NOT MET / MET / MISS / "verdict" wording, check counts, registered-window text) anywhere in its body,
and ENDS with a pointer to its docs/thesis/tables/TA_verdicts.md row(s), in the exact form
    Verdicts: Table A.4, rows <ids>.
or, for a figure with no row of its own,
    Verdicts: Table A.4, none (descriptive).

Scope: every docs/thesis/figures_thesis/captions/*.md EXCEPT A1.md/A2.md/A3.md - those are the appendix tables
themselves (Table A.1-A.3), already full of PASS/FAIL/NOT met cells, and the ruling is explicit that "appendix
tables are where verdicts belong"; TA_verdicts.md (Table A.4) is not in captions/ at all. This is the only script
that checks this rule; it does not touch eval/figs_thesis*.py's own cross-checks (unchanged totals, see those
scripts' own output) or A1-A3.

Usage: python3 eval/caption_verdict_check.py"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CAPD = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "captions")
TA = os.path.join(ROOT, "docs", "thesis", "tables", "TA_verdicts.md")

EXEMPT = {"A1", "A2", "A3"}   # appendix tables: keep their verdict cells (D113)

# Whole-word, case-insensitive. Inflections included so "passes"/"passed"/"failing" etc. are also caught, not just
# the bare forms. "verdict(s)" is banned outside the pointer line itself.
BANNED = re.compile(r"\b(pass(?:es|ed|ing)?|fail(?:s|ed|ing)?|not\s+met|met|miss(?:es|ed|ing)?|verdicts?)\b", re.IGNORECASE)
POINTER_RE = re.compile(r"^Verdicts: Table A\.4, (none \(descriptive\)|rows (?P<ids>.+))\.$")


def ta_ids():
    """Every ID-column value in TA_verdicts.md (one row per pre-registered hypothesis/check/prediction)."""
    ids = set()
    for ln in open(TA, encoding="utf-8"):
        if not ln.startswith("|"):
            continue
        parts = ln.split("|")
        if len(parts) < 3 or parts[1].strip() in ("Experiment", "---"):
            continue
        ids.add(parts[2].strip())
    return ids


def check_file(fid, ids):
    path = os.path.join(CAPD, f"{fid}.md")
    text = open(path, encoding="utf-8").read().rstrip("\n")
    lines = [ln for ln in text.split("\n") if ln.strip()]
    results = []
    if not lines:
        return [("has at least one non-empty line", fid, False)]
    pointer = lines[-1]
    m = POINTER_RE.match(pointer)
    results.append((f"{fid}: last non-empty line is the exact pointer form", pointer, m is not None))
    if m and m.group("ids"):
        bad = []
        # ";"-separated (not ","), because some TA_verdicts.md IDs themselves contain a comma (e.g.
        # "H1.8 EKF3, half real-time (RTF 0.5)").
        for rid in [s.strip() for s in m.group("ids").rstrip(".").split(";")]:
            # "Extension E2 H-E2.1" -> the TA_verdicts.md experiment label is a separate column from the id; accept
            # either the bare id or "<Experiment label> <id>" (this script's own pointer-writing convention above).
            bare = rid.split(" ", 2)[-1] if rid.startswith(("Extension ", "Experiment ")) else rid
            if not (rid in ids or bare in ids or any(i.startswith(bare) for i in ids)):
                bad.append(rid)
        results.append((f"{fid}: every pointer id is a TA_verdicts.md ID-column value", ", ".join(bad) if bad else "ok",
                        not bad))
    body = "\n".join(lines[:-1])
    hits = sorted(set(w.group(0) for w in BANNED.finditer(body)))
    results.append((f"{fid}: body (everything above the pointer) has no banned word", ", ".join(hits) if hits else "none",
                    not hits))
    return results


def main():
    ids = ta_ids()
    fids = sorted(f[:-3] for f in os.listdir(CAPD) if f.endswith(".md") and f[:-3] not in EXEMPT)
    all_results = []
    for fid in fids:
        all_results += check_file(fid, ids)
    n_ok = sum(1 for _, _, ok in all_results if ok)
    for label, val, ok in all_results:
        if not ok:
            print("   CHECK FAIL:", label, "->", val)
    print(f"caption_verdict_check: {n_ok}/{len(all_results)} ({len(fids)} caption files checked, {len(EXEMPT)} exempt: "
          f"{', '.join(sorted(EXEMPT))})")
    return 0 if n_ok == len(all_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
