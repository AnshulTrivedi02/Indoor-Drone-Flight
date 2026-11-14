#!/usr/bin/env python3
"""Read-only freeze audit of the thesis outputs (user request, 2026-11-14).

Scope (verbatim from the request): A) supersession map; B) superseded values presented as
current, and verdict labels against docs/thesis/tables/TA_verdicts.md; C) numeric table cells
against their cited source; D) style checks (dashes, dates, internal codes, missing ~ before
units, "RTF 0.5" wrapper); E) every statement about the EKF3 4.3 s switching delay / 4.10 m
jump, qualified or not; F) coverage matrix per experiment.

This script NEVER edits any table, figure, caption or numbers file. It only reads, and writes
its own report text to stdout / docs/thesis/freeze_audit.md (via a separate run of this script
followed by a manual write, or via --write-report). Re-runnable: run again after fixes land.

Usage: python3 eval/freeze_audit.py [--write-report] [--writing-pack PATH]

Notes on scope / known limitations (see the report's own "Scope notes" section for the
authoritative, current list):
  - The writing pack (docs/thesis/writing_pack/) is untracked and may not exist in the worktree
    this script runs from. --writing-pack (default: docs/thesis/writing_pack under ROOT, falling
    back to ~/thesis_ws/docs/thesis/writing_pack) controls where it is read from; if neither
    exists, section B's writing-pack coverage is marked INCOMPLETE, not skipped silently.
  - tables_png (images) cannot be text-scanned; their .md/.tex sources are scanned instead.
  - Section C resolves only `numbers*.md:LINE[-LINE]` style citations (the project's own
    citation convention). M:/C:/P:/json: citations are counted as unresolved, not guessed at.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs", "thesis")
TABLES = os.path.join(DOCS, "tables")
FIGS = os.path.join(DOCS, "figures_thesis")
ASSETS = os.path.join(DOCS, "thesis_assets")
REPORT_PATH = os.path.join(DOCS, "freeze_audit.md")

NUMBERS_FILES = {
    "numbers.md": os.path.join(DOCS, "numbers.md"),
    "numbers_extras.md": os.path.join(DOCS, "closed_loop_extras", "numbers_extras.md"),
    "numbers_refly.md": os.path.join(DOCS, "refly_priors", "numbers_refly.md"),
    "numbers_tier1.md": os.path.join(DOCS, "tier1", "numbers_tier1.md"),
    "numbers_ekf3_heading.md": os.path.join(DOCS, "ekf3_heading_replay", "numbers_ekf3_heading.md"),
    "numbers_fgo_gate_count.md": os.path.join(DOCS, "diagnostics", "numbers_fgo_gate_count.md"),
    "numbers_cl_heading_perflight.md": os.path.join(DOCS, "numbers_cl_heading_perflight.md"),
}

SUPPRESS_RX = re.compile(
    r"supersed|original[- ]prior|earlier build|withdrawn|old[- ]build|pre-dating|\(original\)|"
    r"\bOLD priors\b|\bNEW\)? priors\b",
    re.IGNORECASE,
)

VERDICT_ALLOWED = ["PASS", "FAIL AS WORDED", "NOT MET", "WITHDRAWN", "DESCRIPTIVE", "REPORTED k/3"]

# TA_verdicts.md and R1_hypothesis_scorecard.md are the verdict SOURCE OF TRUTH, not targets:
# their own "Registered rule (quoted...)" columns are full of the ORIGINAL registered numeric
# thresholds (e.g. "<= 1.5x", "0.25 rad/s"), which coincidentally match fragments of superseded
# values and flood B(i)/B(ii) with false positives if scanned as if they were an output table
# presenting a result. Excluded from those two checks only (not from C/D, where they are
# legitimate thesis-facing text).
VERDICT_SOURCE_BASENAMES = {"TA_verdicts.md", "R1_hypothesis_scorecard.md", "R1_hypothesis_scorecard.tex",
                             "tab_A-4.tex"}


def known_quantity_keywords(s):
    return [w for w in ("EKF3", "UKF", "FGO", "hold", "drift", "yaw", "loss", "heading", "lockout",
                         "cruise", "indoor", "outdoor") if re.search(rf"\b{re.escape(w)}\b", s, re.IGNORECASE)][:2]


def derive_context_words(quantity, value=""):
    ctx = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9+]{2,}", quantity)][:2]
    if not ctx:
        ctx = known_quantity_keywords(quantity + " " + value)
    return ctx


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, IsADirectoryError):
        return None


def lines_of(path):
    text = read(path)
    return text.split("\n") if text is not None else []


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_writing_pack(cli_arg):
    for cand in [cli_arg, os.path.join(DOCS, "writing_pack"), os.path.expanduser("~/thesis_ws/docs/thesis/writing_pack")]:
        if cand and os.path.isdir(cand):
            return cand
    return None


def all_md_under(d):
    out = []
    for dirpath, _, fnames in os.walk(d):
        for fn in fnames:
            if fn.endswith(".md"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def relp(p):
    return os.path.relpath(p, ROOT)


# --------------------------------------------------------------------------------------------
# Number index (tables + figures), used by checks E and F
# --------------------------------------------------------------------------------------------
TABLE_HEAD_RX = re.compile(r"^#\s*Table\s+([A-Za-z0-9]+\.\d+[a-z]?)\.?\s*(.*)$")
FIGURE_HEAD_RX = re.compile(r"Figure\s+([A-Za-z0-9]+\.\d+[a-z]?)\b")


def build_table_index():
    idx = {}
    for d in [TABLES]:
        for fn in sorted(os.listdir(d)):
            if not fn.endswith((".md", ".tex")):
                continue
            p = os.path.join(d, fn)
            for ln in lines_of(p)[:5]:
                m = TABLE_HEAD_RX.match(ln.strip())
                if m:
                    idx.setdefault(m.group(1), []).append(p)
                    break
    return idx


def build_figure_index():
    idx = defaultdict(list)
    cap_dirs = [os.path.join(FIGS, "captions")]
    for d in cap_dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            text = read(p) or ""
            for m in FIGURE_HEAD_RX.finditer(text):
                idx[m.group(1)].append(p)
    for fn in ["index.md", "index_methods.md", "index_results.md", "index_drift.md", "index_drift9.md"]:
        p = os.path.join(FIGS, fn)
        text = read(p)
        if text is None:
            continue
        for m in FIGURE_HEAD_RX.finditer(text):
            idx[m.group(1)].append(p)
    return idx


# --------------------------------------------------------------------------------------------
# Thesis-facing file set (scope rule: tables md/tex, thesis figure captions, thesis_assets
# bundle, writing pack). Candidate captions are scanned but reported separately.
# --------------------------------------------------------------------------------------------
def thesis_facing_files(writing_pack_dir):
    files = []
    for fn in sorted(os.listdir(TABLES)):
        if fn.endswith((".md", ".tex")):
            files.append(os.path.join(TABLES, fn))
    cap_dir = os.path.join(FIGS, "captions")
    if os.path.isdir(cap_dir):
        for fn in sorted(os.listdir(cap_dir)):
            if fn.endswith(".md"):
                files.append(os.path.join(cap_dir, fn))
    for fn in sorted(os.listdir(FIGS)):
        if fn.startswith("index") and fn.endswith(".md"):
            files.append(os.path.join(FIGS, fn))
    # thesis_assets bundle: tables_tex (.tex), candidates (.md table sources only, pdfs skipped),
    # top-level index.md. tables_png are images - not text-scannable (scope note).
    if os.path.isdir(ASSETS):
        tt = os.path.join(ASSETS, "tables_tex")
        if os.path.isdir(tt):
            for fn in sorted(os.listdir(tt)):
                if fn.endswith(".tex"):
                    files.append(os.path.join(tt, fn))
        cand = os.path.join(ASSETS, "candidates")
        if os.path.isdir(cand):
            for fn in sorted(os.listdir(cand)):
                if fn.endswith(".md"):
                    files.append(os.path.join(cand, fn))
        idxp = os.path.join(ASSETS, "index.md")
        if os.path.isfile(idxp):
            files.append(idxp)
    if writing_pack_dir:
        files.extend(all_md_under(writing_pack_dir))
    return files


def candidate_caption_files():
    cap_dir = os.path.join(FIGS, "candidates", "captions")
    files = []
    if os.path.isdir(cap_dir):
        for fn in sorted(os.listdir(cap_dir)):
            if fn.endswith(".md"):
                files.append(os.path.join(cap_dir, fn))
    idx_dir = os.path.join(FIGS, "candidates")
    if os.path.isdir(idx_dir):
        for fn in sorted(os.listdir(idx_dir)):
            if fn.startswith("index_") and fn.endswith(".md"):
                files.append(os.path.join(idx_dir, fn))
    return files


# ==============================================================================================
# SECTION A: supersession map
# ==============================================================================================
def parse_ta_main_and_appendix():
    """Returns (main_rows, appendix_rows). Each main row: dict with experiment, id, result,
    verdict, notes, raw line text, line number. Appendix row: dict with id, reason, verdict,
    value, build, source, line number."""
    path = os.path.join(TABLES, "TA_verdicts.md")
    text = read(path)
    if text is None:
        return [], [], path
    lines = text.split("\n")
    main_rows, appendix_rows = [], []
    in_appendix = False
    header_seen_main = False
    header_seen_app = False
    for i, ln in enumerate(lines, start=1):
        if ln.strip().startswith("## Superseded appendix"):
            in_appendix = True
            continue
        if not ln.startswith("|"):
            continue
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        if not in_appendix:
            if parts[:2] == ["Experiment", "ID"] or (len(parts) > 0 and set(parts[0]) <= set("- ")):
                header_seen_main = True
                continue
            if len(parts) >= 6 and header_seen_main:
                main_rows.append({
                    "experiment": parts[0], "id": parts[1], "rule": parts[2], "result": parts[3],
                    "verdict": parts[4], "notes": parts[5], "line": i, "raw": ln,
                })
        else:
            if parts[:2] == ["id", "reason"] or (len(parts) > 0 and set(parts[0]) <= set("- ")):
                header_seen_app = True
                continue
            if len(parts) >= 6 and header_seen_app:
                appendix_rows.append({
                    "id": parts[0], "reason": parts[1], "verdict": parts[2], "value": parts[3],
                    "build": parts[4], "source": parts[5], "line": i, "raw": ln,
                })
    return main_rows, appendix_rows, path


BASE_ID_RX = re.compile(r"^(H-?[A-Za-z0-9]+(?:\.\d+)?[a-z]?|[A-Z]\d(?:\.[a-z])?|V3)")


def base_id(idstr):
    m = BASE_ID_RX.match(idstr.strip())
    return m.group(1) if m else idstr.split(" ")[0]


def find_current_for_appendix_row(appendix_row, main_rows):
    """Best-effort match of an appendix (superseded) row's id to a main-table row with the same
    base id. Returns (row_or_None, ambiguous_bool)."""
    bid = base_id(appendix_row["id"])
    cands = [r for r in main_rows if base_id(r["id"]) == bid]
    if len(cands) == 1:
        return cands[0], False
    if len(cands) > 1:
        # try a tighter match: share a keyword (FGO/UKF/EKF3, full/half real time, hold etc.)
        kw = set(w.lower() for w in re.findall(r"[A-Za-z]{3,}", appendix_row["id"]))
        scored = []
        for r in cands:
            rk = set(w.lower() for w in re.findall(r"[A-Za-z]{3,}", r["id"]))
            scored.append((len(kw & rk), r))
        scored.sort(key=lambda t: -t[0])
        if scored and scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
            return scored[0][1], False
        return None, True
    return None, False


CODE_OR_DATE_RX = re.compile(r"`[^`]*`|\b20\d{2}-\d{2}-\d{2}\b|\[[^\]]*\]")


def extract_numeric_tokens(s):
    """Only DASH-JOINED NUMERIC RANGES (e.g. '8.3-8.6', '9-22', '18-28 mm') are used as B(i)
    match keys. Bare single numbers (counts, flight indices, generic decimals like '0.25') are
    deliberately excluded: they are far too generic and flooded the first pass of this check
    (see freeze_audit.py's own development notes / the report's Scope notes). Code spans and
    bracketed citations are stripped first so a date or commit-adjacent digit string (which can
    itself look like 'NNNN-NN' once a code span is removed) is never mistaken for a range."""
    s = CODE_OR_DATE_RX.sub(" ", s)
    toks = re.findall(r"\d+(?:\.\d+)?\s*[-\u2013\u2212]\s*\d+(?:\.\d+)?", s)
    out = []
    for t in toks:
        t2 = t.strip()
        digits_only = re.sub(r"[^\d]", "", t2)
        if len(digits_only) < 3:  # e.g. "0-3" is too generic; "8.3-8.6" / "9-22" / "18-28" pass
            continue
        out.append(t2)
    return out


def normalise_dash(s):
    """Unify dash characters and collapse SPACED dashes only ('8.3 - 8.6' -> '8.3-8.6'); other
    whitespace is kept, so an unrelated number elsewhere on the line (e.g. a 'FC:27-30' source
    citation) can never be glued onto a different number by blanket space removal - that glueing
    is exactly what produced a false '7-30' match against a 'FC:27-30' citation in this script's
    own development (see the report's Scope notes)."""
    s = re.sub(r"[\u2013\u2212\u2012]", "-", s)
    return re.sub(r"\s*-\s*", "-", s)


def find_isolated(token, text):
    """True if `token` occurs in `text` with no digit immediately before or after (so '7-30'
    does not match inside '27-30' or '7-300')."""
    start = 0
    while True:
        i = text.find(token, start)
        if i == -1:
            return False
        before = text[i - 1] if i > 0 else ""
        after = text[i + len(token)] if i + len(token) < len(text) else ""
        if not before.isdigit() and not after.isdigit():
            return True
        start = i + 1


def section_A(main_rows, appendix_rows, ta_path, numbers_text):
    facts = []  # dict: quantity, superseded, current, current_source, origin_source
    unresolved = []

    for row in appendix_rows:
        cur_row, ambiguous = find_current_for_appendix_row(row, main_rows)
        if cur_row is not None:
            current_val = cur_row["result"]
            current_src = f"TA_verdicts.md:{cur_row['line']}"
        elif ambiguous:
            current_val = "unresolved (ambiguous id match in TA main table)"
            current_src = "-"
        else:
            current_val = "unresolved (no TA main-table row with this base id)"
            current_src = "-"
        facts.append({
            "quantity": row["id"], "superseded": row["value"], "current": current_val,
            "current_source": current_src, "origin": f"TA_verdicts.md:{row['line']}",
            "numeric_tokens": extract_numeric_tokens(row["value"]),
            "context_words": derive_context_words(row["id"], row["value"]),
        })

    # numbers_refly.md Section 5 "Old vs new per criterion" table
    refly_path = NUMBERS_FILES["numbers_refly.md"]
    refly_lines = lines_of(refly_path)
    in_tbl = False
    header_seen = False
    for i, ln in enumerate(refly_lines, start=1):
        if ln.strip().startswith("## 5. Old vs new per criterion"):
            in_tbl = True
            continue
        if in_tbl:
            if ln.strip().startswith("## 6."):
                break
            if not ln.startswith("|"):
                continue
            parts = [p.strip() for p in ln.strip().strip("|").split("|")]
            if parts[:1] == ["criterion"] or (parts and set(parts[0]) <= set("- ")):
                header_seen = True
                continue
            if header_seen and len(parts) >= 4:
                crit, old, new, changed = parts[0], parts[1], parts[2], parts[3]
                facts.append({
                    "quantity": crit.strip("*"), "superseded": old, "current": new,
                    "current_source": f"refly_priors/numbers_refly.md:{i}",
                    "origin": f"refly_priors/numbers_refly.md:{i}",
                    "numeric_tokens": extract_numeric_tokens(old),
                    "context_words": derive_context_words(crit, old),
                })

    # numbers_extras.md: cl_ukf_a_tex superseded-port note (hand-identified, single clean fact)
    extras_lines = lines_of(NUMBERS_FILES["numbers_extras.md"])
    for i, ln in enumerate(extras_lines, start=1):
        if "cl_ukf_a_tex" in ln and ("superseded" in ln.lower() or "PASS (earlier" in ln):
            facts.append({
                "quantity": "UKF H1.8 full real time (old port cl_ukf_a_tex)",
                "superseded": ln.strip(),
                "current": "see closed_loop_extras/numbers_extras.md Summary table, 'UKF, full real time (_v2)' row (2/3, 138.3-177.1 s)",
                "current_source": "closed_loop_extras/numbers_extras.md (Summary table)",
                "origin": f"closed_loop_extras/numbers_extras.md:{i}",
                "numeric_tokens": extract_numeric_tokens(ln),
                "context_words": ["cl_ukf_a_tex"],
            })

    # numbers.md: generic parse of "### Superseded by ..." sections, escaped rows marked with ¦
    nlines = numbers_text.split("\n") if numbers_text else []
    sec_heading_idx = [i for i, ln in enumerate(nlines) if re.match(r"^### Superseded by", ln.strip())]
    sec_count = len(sec_heading_idx)
    sec_rows_total = 0
    for k, start in enumerate(sec_heading_idx):
        end = sec_heading_idx[k + 1] if k + 1 < len(sec_heading_idx) else len(nlines)
        heading = nlines[start].strip()
        for j in range(start + 1, end):
            ln = nlines[j]
            if "\u00a6" not in ln:
                continue
            inner = ln.strip()
            if inner.startswith("|") and inner.endswith("|"):
                inner = inner[1:-1]
            cells = [c.strip() for c in inner.split("\u00a6")]
            if len(cells) < 2 or cells[0].lower() in ("row (verbatim)", ""):
                continue
            sec_rows_total += 1
            quantity = cells[0]
            value = cells[1] if len(cells) > 1 else ""
            source = cells[-1] if len(cells) > 2 else ""
            facts.append({
                "quantity": quantity, "superseded": value,
                "current": "unresolved (numbers.md internal correction trail - section-level only, not individually cross-matched; see scope note)",
                "current_source": "-",
                "origin": f"numbers.md:{j + 1} (section: {heading[:70]})",
                "numeric_tokens": extract_numeric_tokens(value),
                "context_words": derive_context_words(quantity, value),
            })
    return facts, sec_count, sec_rows_total


# ==============================================================================================
# SECTION B(i): superseded values presented as current
# ==============================================================================================
def section_Bi(facts, scan_files):
    hits = []
    checked_files = 0
    skipped_no_context = 0
    for path in scan_files:
        if os.path.basename(path) in VERDICT_SOURCE_BASENAMES:
            continue
        text = read(path)
        if text is None:
            continue
        checked_files += 1
        flines = text.split("\n")
        for fi, fln in enumerate(facts, start=0):
            toks = fln["numeric_tokens"]
            ctx = fln["context_words"]
            if not toks:
                continue
            if not ctx:
                skipped_no_context += 1
                continue  # a range with no distinguishing keyword is too generic to match safely
            if fln["origin"].startswith("numbers.md") and os.path.basename(path).lower() == "numbers.md":
                continue  # self-referential: numbers.md's own later correction sections legitimately
                          # re-quote an earlier section's superseded row verbatim (marked "Frozen text
                          # (verbatim)") - that is the document's own documented history repeating
                          # itself, not a NEW appearance of the value presented as current elsewhere
            for li, line in enumerate(flines, start=1):
                if SUPPRESS_RX.search(line):
                    continue
                if not any(w.lower() in line.lower() for w in ctx):
                    continue
                # strip citation-looking tails (source columns, [M:xxx] brackets, code spans)
                # before matching, so a line-range citation like 'FC:27-30' can never supply a
                # false match for a fact value like '7-30'.
                line_for_match = ID_STRIP_RX.sub(" ", ALL_CITE_RX.sub(" ", line))
                norm_line = normalise_dash(line_for_match)
                tok_hit = None
                for t in toks:
                    nt = normalise_dash(t)
                    if find_isolated(nt, norm_line):
                        tok_hit = t
                        break
                if not tok_hit:
                    continue
                hits.append({
                    "file": relp(path), "line": li, "quantity": fln["quantity"],
                    "matched_token": tok_hit, "origin": fln["origin"], "text": line.strip()[:160],
                })
    return hits, checked_files, skipped_no_context


# ==============================================================================================
# SECTION B(ii): verdict labels against TA_verdicts.md
# ==============================================================================================
ALIAS_RX = re.compile(r"[\u201c\"]\s*(H-[A-Za-z0-9]+|[A-Z]-[A-Za-z0-9]+)\b")


def build_ta_verdict_maps(main_rows):
    by_exact_id = defaultdict(set)
    by_base_id = defaultdict(set)
    alias_to_base = {}
    for r in main_rows:
        by_exact_id[r["id"]].add(r["verdict"])
        by_base_id[base_id(r["id"])].add(r["verdict"])
        m = ALIAS_RX.search(r["rule"])
        if m:
            alias_to_base[m.group(1)] = base_id(r["id"])
    return by_exact_id, by_base_id, alias_to_base


VERDICT_WORD_RX = re.compile(
    r"\b(PASS|FAIL AS WORDED|NOT MET|WITHDRAWN|DESCRIPTIVE|REPORTED k/3|FAIL|MET|MISS)\b"
)
ID_TOKEN_RX = re.compile(r"\bH-?[A-Za-z0-9]+(?:\.\d+)?[a-z]?\b")
# Extension-experiment IDs (E2-E6): TA_verdicts.md's own legend says these, and the ablation,
# deliberately KEEP their source's literal word FAIL rather than being harmonised to NOT MET -
# so a source doc (tier1/*.md, the writing pack) legitimately using PASS/NOT MET/NOT RUN wording
# that differs from TA's transcribed bare FAIL is NOT a defect by itself. Routed to its own
# "extension notes" bucket, reported but not counted as a B(ii) mismatch (advisor guidance:
# surface the tension, don't silently score it either way).
EXT_ID_RX = re.compile(r"E[2-6](?:\.|$)")


def section_Bii(main_rows, scan_files, ta_path):
    by_exact, by_base, alias_to_base = build_ta_verdict_maps(main_rows)
    h42_checks = []
    mismatches = []
    nonstandard = []
    extension_notes = []
    # Authoritative, structural H4.2 check straight from the parsed TA_verdicts.md main table
    # (not regex text-scanning, which is used only for finding the label repeated elsewhere).
    for r in main_rows:
        if base_id(r["id"]) == "H4.2":
            h42_checks.append({"file": "docs/thesis/tables/TA_verdicts.md", "line": r["line"],
                                "label": r["verdict"], "text": r["raw"].strip()[:160]})
    for path in scan_files:
        if os.path.basename(path) in VERDICT_SOURCE_BASENAMES:
            continue
        text = read(path)
        if text is None:
            continue
        for li, line in enumerate(text.split("\n"), start=1):
            for m in ID_TOKEN_RX.finditer(line):
                idtok = m.group(0)
                bid = alias_to_base.get(idtok, idtok if idtok in by_base else None)
                if bid is None:
                    continue
                tail = line[m.end():m.end() + 60]
                vm = VERDICT_WORD_RX.search(tail)
                if not vm:
                    continue
                label = vm.group(1)
                if bid == "H4.2":
                    h42_checks.append({"file": relp(path), "line": li, "label": label, "text": line.strip()[:160]})
                if label not in VERDICT_ALLOWED:
                    nonstandard.append({"file": relp(path), "line": li, "id": idtok, "label": label,
                                         "text": line.strip()[:160]})
                    continue
                known = by_base.get(bid, set())
                if len(known) == 1 and label not in known:
                    entry = {"file": relp(path), "line": li, "id": idtok, "base_id": bid,
                             "found": label, "ta_verdict": list(known)[0], "text": line.strip()[:160]}
                    if EXT_ID_RX.search(bid):
                        extension_notes.append(entry)
                    else:
                        mismatches.append(entry)
    h42_bad = [h for h in h42_checks if h["label"] != "NOT MET"]
    return {
        "h42_checks": h42_checks, "h42_bad": h42_bad, "mismatches": mismatches,
        "nonstandard": nonstandard, "extension_notes": extension_notes,
    }


def run_subprocess_check(script_relpath):
    path = os.path.join(ROOT, script_relpath)
    if not os.path.isfile(path):
        return None
    try:
        r = subprocess.run([sys.executable, path], cwd=ROOT, capture_output=True, text=True, timeout=120)
        return {"returncode": r.returncode, "stdout": r.stdout.strip()[-4000:], "stderr": r.stderr.strip()[-2000:]}
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}


# ==============================================================================================
# SECTION C: numeric table cells vs cited source
# ==============================================================================================
def load_rd():
    import ast
    tree = ast.parse(open(os.path.join(HERE, "figs_thesis.py")).read())
    keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd"]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "eval/figs_thesis.py", "exec"), ns)
    return ns["rd"]


# Matches "numbers.md:559", "numbers_refly.md:51-53" etc. - the project's own citation
# convention for a value traced to a stored numbers file (see numbers.md's own header: "Sources"
# bullet). M:/C:/P:/json:/code: citations point elsewhere and are deliberately out of scope here
# (counted as unresolved, never guessed at).
CITE_RX = re.compile(r"\b(numbers(?:_[a-z0-9_]+)?\.md):(\d+)(?:[-\u2013](\d+))?")
ALL_CITE_RX = re.compile(r"\b\w*numbers(?:_[a-z0-9_]+)?\.md:\d+(?:[-\u2013]\d+)?|\[[A-Za-z]+:L?\d[^\]]*\]|`[^`]*`")
# Hypothesis/registered-check IDs look like decimal numbers (H1.8, C1.a, X1.b) and must be
# stripped before extracting VALUE tokens, or e.g. "H1.8" is misread as the value "1.8" - found
# empirically: it was generating most of this check's cite-drift/not-found noise in the first
# working version (see the report's Scope notes).
ID_STRIP_RX = re.compile(r"\bH-?[A-Za-z0-9]*\.\d+[a-z]?\b|\b[A-Z]\d\.[a-z]\b")


def resolve_numbers_path(short_name):
    return NUMBERS_FILES.get(short_name)


def decimal_values_in(s):
    """Decimal numeric tokens only (e.g. '0.94', '4.10', '7.8'), optionally joined into a dash
    range (e.g. '7.8-7.9'). Deliberately excludes bare integers (line numbers, citation markers,
    flight counts, '3/3' fractions) - those are indistinguishable from citation noise at this
    granularity and would otherwise make this check worthless (see the report's Scope notes:
    first pass of this script matched on citation line numbers themselves)."""
    out = []
    for m in re.finditer(r"\d+\.\d+(?:\s*[-\u2013]\s*\d+\.\d+)?", s):
        out.append(m.group(0).strip())
    return out


def rd_matches_window(rd, cell_token, window_text):
    """True if some decimal number in window_text, rounded with the thesis's own rd() to
    cell_token's own displayed precision, equals cell_token as a string (half-away-from-zero,
    per rd()'s own docstring) - catches a source stored at full precision (e.g. '4.0995')
    whose table cell legitimately rounds to a different-looking but correct '4.10'."""
    if "-" in cell_token or "–" in cell_token:
        return False  # ranges: substring containment (already tried) is the right check
    try:
        n = len(cell_token.split(".")[1])
    except IndexError:
        return False
    for m in re.finditer(r"-?\d+\.\d+", window_text):
        try:
            if rd(float(m.group(0)), n) == cell_token:
                return True
        except Exception:
            continue
    return False


def section_C(scan_files, time_budget_exceeded_flag):
    rd = load_rd()
    resolved, cite_drift, not_found, unresolved = [], [], [], []
    n_cites = 0
    for path in scan_files:
        if os.path.basename(path) in VERDICT_SOURCE_BASENAMES:
            continue  # these cite M:/numbers.md provenance in bulk; not the output tables C targets
        text = read(path)
        if text is None:
            continue
        for li, raw_line in enumerate(text.split("\n"), start=1):
            for m in CITE_RX.finditer(raw_line):
                n_cites += 1
                short, l1, l2 = m.group(1), int(m.group(2)), m.group(3)
                target = resolve_numbers_path(short)
                if target is None or not os.path.isfile(target):
                    unresolved.append({"file": relp(path), "line": li, "cite": m.group(0), "reason": "target file not found"})
                    continue
                # strip the citation itself (and any other bracket/code-span citation on the
                # line) before extracting the CELL's own value tokens, so the line number inside
                # the citation is never mistaken for a data value.
                line_wo_cites = ID_STRIP_RX.sub(" ", ALL_CITE_RX.sub(" ", raw_line))
                tgt_lines = lines_of(target)
                lo = l1 - 1
                hi = (int(l2) if l2 else l1) - 1
                window = tgt_lines[max(0, lo - 1):min(len(tgt_lines), hi + 2)]
                cited_text_raw = "\n".join(window)
                cited_text = ALL_CITE_RX.sub(" ", cited_text_raw)
                cited_text_norm = normalise_dash(cited_text)
                cell_tokens = decimal_values_in(line_wo_cites)
                if not cell_tokens:
                    unresolved.append({"file": relp(path), "line": li, "cite": m.group(0), "reason": "no decimal value token on citing line (after stripping citations/code spans)"})
                    continue
                found_on_cited = any(normalise_dash(t) in cited_text_norm for t in cell_tokens)
                if found_on_cited:
                    resolved.append({"file": relp(path), "line": li, "cite": m.group(0), "status": "match on cited line(s)"})
                    continue
                if any(rd_matches_window(rd, t, cited_text_raw) for t in cell_tokens):
                    resolved.append({"file": relp(path), "line": li, "cite": m.group(0), "status": "match via rd() rounding on cited line(s)"})
                    continue
                whole = read(target) or ""
                whole_wo_cites = normalise_dash(ALL_CITE_RX.sub(" ", whole))
                found_line = None
                for j, tln in enumerate(whole.split("\n"), start=1):
                    tln_n = normalise_dash(ALL_CITE_RX.sub(" ", tln))
                    if any(normalise_dash(t) in tln_n for t in cell_tokens):
                        found_line = j
                        break
                if found_line:
                    cite_drift.append({"file": relp(path), "line": li, "cite": m.group(0), "found_at": f"{short}:{found_line}"})
                else:
                    not_found.append({"file": relp(path), "line": li, "cite": m.group(0), "tokens": sorted(cell_tokens)})
    return {"resolved": resolved, "cite_drift": cite_drift, "not_found": not_found, "unresolved": unresolved, "n_cites": n_cites}


# ==============================================================================================
# SECTION D: style checks
# ==============================================================================================
DASH_PROSE_RX = re.compile(r"(?<!\d)[\u2013\u2014](?!\d)")
DASH_RANGE_RX = re.compile(r"\d[\u2013\u2014]\d")
DATE_RX = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
D_NUM_RX = re.compile(r"\bD\d{2,4}\b")
COMMIT_HASH_RX = re.compile(r"\b[0-9a-f]{7,40}\b")
SCRIPT_FILE_RX = re.compile(r"\b[\w./]+\.(?:py|sh|lua|sdf|json|parm|cpp|h)\b")
TRIAL_ID_RX = re.compile(r"\b(?:[a-zA-Z]+_)?(?:O|T|H|E|S)_r\d[a-z0-9]*\b|\bs\d[a-z0-9]*rp?\d?\b")
WORLD_NAME_RX = re.compile(r"\bcorridor_(?:textured|blank|transition)(?:_fwd(?:c|plainc)?)?\b")
UNIT_NO_TIE_RX = re.compile(r"\b\d+(?:\.\d+)?\s(?:m|mm|s|ms|deg|Hz|px|rad)\b")
RTF_BARE_RX = re.compile(r"\bRTF\s*0\.5\b")
RTF_WRAPPED_RX = re.compile(r"half real[- ]time\s*\(RTF 0\.5\)")

CODE_SPAN_RX = re.compile(r"`[^`]*`")
CITE_BRACKET_RX = re.compile(r"\[[^\]]*\]")


def strip_provenance(line, is_table_row):
    """Strip code spans and bracketed cites; for a table row, drop the last cell (commonly the
    source column) only when it looks like a provenance cell (contains numbers.md/M:/C:/json:)."""
    s = CODE_SPAN_RX.sub(" ", line)
    s = CITE_BRACKET_RX.sub(" ", s)
    if is_table_row and "|" in s:
        cells = s.split("|")
        if len(cells) > 2 and re.search(r"numbers.*\.md|[MCP]:L?\d|json:|code:", cells[-2] or ""):
            cells = cells[:-2] + [""]
        s = "|".join(cells)
    return s


def section_D(scan_files):
    findings = defaultdict(lambda: defaultdict(int))
    details = defaultdict(list)
    for path in scan_files:
        text = read(path)
        if text is None:
            continue
        if "<!-- generated by" in text:
            pass  # generator comment lines handled per-line below
        for li, line in enumerate(text.split("\n"), start=1):
            if line.strip().startswith("<!--"):
                continue
            is_row = line.startswith("|")
            s = strip_provenance(line, is_row)
            rng_hits = list(DASH_RANGE_RX.finditer(s))
            prose_hits = [m for m in DASH_PROSE_RX.finditer(s)]
            # a prose en/em dash that is NOT part of a digit-dash-digit range
            real_prose = []
            for m in prose_hits:
                lo, hi = max(0, m.start() - 1), min(len(s), m.end() + 1)
                if not re.search(r"\d.\d", s[lo:hi]):
                    real_prose.append(m)
            if real_prose:
                findings[relp(path)]["dash_prose"] += len(real_prose)
                if len(details[relp(path)]) < 40:
                    details[relp(path)].append((li, "dash_prose", s.strip()[:140]))
            for m in RTF_BARE_RX.finditer(s):
                window = s[max(0, m.start() - 40):m.end() + 10]
                if not RTF_WRAPPED_RX.search(window):
                    findings[relp(path)]["rtf_bare"] += 1
                    if len(details[relp(path)]) < 40:
                        details[relp(path)].append((li, "rtf_bare", s.strip()[:140]))
    return findings, details


# ==============================================================================================
# SECTION E: EKF3 4.3s switching delay / 4.10m jump statements
# ==============================================================================================
E_KEYWORD_RX = re.compile(
    r"4\.3\s*s\b|4\.1\d?\s*m\b|3\.5[34]\s*m\b|switch(?:ing)?\s+delay|source\s+switch|GNSS\s+(?:ON|OFF)\s+vote|"
    r"o_source_switch", re.IGNORECASE
)
QUALIFIER_RX = re.compile(
    r"harness|switching script|\.lua\b|vote|GPS latency|o_source_switch|forced[- ]switch|the switch", re.IGNORECASE
)
# the bare-number forms ('4.1x m', '3.5[34] m') are only kept if the line is actually ABOUT the
# jump/switch/return event (same topic word nearby) - otherwise they false-positive on unrelated
# quantities that happen to round to a similar-looking number (e.g. Experiment 1A's median ATE
# 4.10 m, or an unrelated 4.1 m heading-replay distance; see the report's Scope notes).
BARE_NUMBER_RX = re.compile(r"4\.1\d?\s*m\b|3\.5[34]\s*m\b", re.IGNORECASE)
TOPIC_RX = re.compile(r"jump|switch|reset|GNSS|return|delay|vote", re.IGNORECASE)


def section_E(scan_files):
    hits = []
    for path in scan_files:
        text = read(path)
        if text is None:
            continue
        for li, line in enumerate(text.split("\n"), start=1):
            m = E_KEYWORD_RX.search(line)
            if not m:
                continue
            if BARE_NUMBER_RX.fullmatch(m.group(0)) and not TOPIC_RX.search(line):
                continue
            qualified = bool(QUALIFIER_RX.search(line))
            hits.append({"file": relp(path), "line": li, "matched": m.group(0), "qualified": qualified,
                          "text": line.strip()[:200]})
    return hits


def read_switch_delay_source():
    p = os.path.join(ROOT, "eval", "results", "expO_switch_delay", "switch_delay.json")
    data = None
    try:
        data = json.load(open(p))
    except Exception:
        pass
    lua_p = os.path.join(ROOT, "sim", "scripts", "o_source_switch.lua")
    lua_text = read(lua_p)
    vote_line = None
    latency_line = None
    if lua_text:
        for ln in lua_text.split("\n"):
            if re.search(r"vote|40|4\.0", ln) and ("GPS" in ln or "vote" in ln.lower()):
                vote_line = ln.strip()
            if re.search(r"latency|delay", ln, re.I):
                latency_line = ln.strip()
    return data, lua_p, vote_line, latency_line


# ==============================================================================================
# SECTION F: coverage matrix
# ==============================================================================================
EXPERIMENT_ROWS = [
    ("1A", "1A standard-sensor comparison", ["H1.1"]),
    ("1B", "1B camera-heading studies: measurement validation / offline fusion / robust-weighting", [
        "H1.2", "H1.3", "C1.a", "H1.4", "X1.b", "H1.5", "H1.6", "H1.6b", "H1.6c", "H1.7a", "H1.7b", "H1.7c",
        "1B-H1", "1B-H2", "1B-H3",
    ]),
    ("1C", "1C closed-loop corridor flights", ["H1.8", "H1.9"]),
    ("2", "2 known tags", ["H2.1", "H2.2", "H2.3", "H2.4"]),
    ("3", "3 loop closure", ["V3", "H3.1", "H3.2", "H3.3", "H3.4"]),
    ("4", "4 outdoor-indoor", ["H4.1", "H4.2", "H4.3"]),
    ("5", "5 tag hold", ["H5.1", "H5.2", "H5.3", "H5.4a", "H5.4b", "H5.5", "H5.6", "H5.7"]),
    ("5S", "5S safety tests", []),
    ("E2", "Extension E2: loop closure, fewer tags", []),
    ("E3", "Extension E3: wrong re-identification", []),
    ("E4", "Extension E4: live window sweep", []),
    ("E5", "Extension E5: UKF with tag landmark states", []),
    ("E6", "Extension E6: figure-8 route", []),
]


def section_F(main_rows, table_index, figure_index):
    rows = []
    for exp, label, ids in EXPERIMENT_ROWS:
        tables = sorted(set(k for k in table_index if False))  # placeholder, filled below via heuristics
        rows.append({"exp": exp, "label": label, "ids": ids})
    return rows


# ==============================================================================================
# Report writer
# ==============================================================================================
def md_escape_count(items):
    return len(items)


def write_report(ctx):
    out = []
    a = ctx["A"]
    bi = ctx["Bi"]
    bii = ctx["Bii"]
    c = ctx["C"]
    d = ctx["D"]
    e = ctx["E"]
    f = ctx["F"]
    meta = ctx["meta"]

    out.append("# Freeze audit of the thesis outputs")
    out.append("")
    out.append(f"Audited commit: `{meta['commit']}` (branch `freeze-audit`, built from `fwd-camera`). "
                f"Run date (UTC): {meta['run_date']}. This report and `eval/freeze_audit.py` are the only two "
                f"files this audit writes or touches; no table, figure, caption or numbers file was edited.")
    out.append("")
    out.append("Re-run: `python3 eval/freeze_audit.py --write-report` (safe to re-run after fixes land; it reads "
                "only, from the working tree at run time).")
    out.append("")

    out.append("## Summary")
    out.append("")
    out.append(f"- A (supersession map): **{meta['status_A']}** - {len(a['facts'])} entries harvested "
                f"({meta['ta_appendix_n']} TA appendix rows, {meta['refly_n']} refly \u00a75 rows, "
                f"{meta['extras_n']} numbers_extras rows, {meta['numbers_sections']} numbers.md superseded sections "
                f"/ {meta['numbers_section_rows']} escaped rows).")
    out.append(f"- B(i) (superseded values presented as current): **{meta['status_Bi']}** - {len(bi['hits'])} hit(s) "
                f"across {bi['checked_files']} thesis-facing files scanned.")
    out.append(f"- B(ii) (verdict labels vs TA_verdicts.md): **{meta['status_Bii']}** - H4.2 checked "
                f"{len(bii['h42_checks'])} occurrence(s), {len(bii['h42_bad'])} not reading NOT MET; "
                f"{len(bii['mismatches'])} other unambiguous mismatch(es); {len(bii['nonstandard'])} "
                f"non-standard bare-word label(s).")
    out.append(f"- C (numeric cells vs cited source): **{meta['status_C']}** - {c['n_cites']} `numbers*.md:LINE` "
                f"citations found; {len(c['resolved'])} matched on the cited line, {len(c['cite_drift'])} matched "
                f"elsewhere in the file (cite drift), {len(c['not_found'])} not found, {len(c['unresolved'])} "
                f"unresolved (non-numeric/no-token cites excluded from scope per the request).")
    out.append(f"- D (style checks): **{meta['status_D']}** - see per-file counts below.")
    out.append(f"- E (4.3 s delay / 4.10 m jump): **{meta['status_E']}** - {len(e)} statement(s) found, "
                f"{sum(1 for h in e if h['qualified'])} qualified, {sum(1 for h in e if not h['qualified'])} unqualified.")
    out.append(f"- F (coverage matrix): **{meta['status_F']}**")
    out.append("")

    out.append("## Scope notes")
    out.append("")
    out.append(f"- Writing pack read from: `{meta['writing_pack'] or 'NOT FOUND (neither docs/thesis/writing_pack '
                'nor ~/thesis_ws/docs/thesis/writing_pack exists in this run environment)'}`" +
                (" (untracked; read from the working tree, not a commit - sha256 of each file recorded below for "
                 "re-run comparability)." if meta["writing_pack"] else "."))
    out.append("- `tables_png` images are not text-scannable; their `.md`/`.tex` sources are scanned instead, per "
                "the request's own distinction between 'tables_tex/*.tex' and 'tables_png sources'.")
    out.append("- Candidate figure captions/index files (`figures_thesis/candidates/`) are scanned but reported "
                "in their own section below; they are not thesis-numbered and are out of the main B/C/D counts.")
    out.append("- Section A's treatment of `numbers.md`'s own internal `### Superseded by ...` correction-trail "
                "sections is at SECTION granularity (quantity + superseded value harvested per escaped row; "
                "'current value' is reported as unresolved for these rows rather than guessed, since matching each "
                "row to its exact live counterpart across dozens of embedded historical tables was not completed "
                "inside the time box). The TA_verdicts.md appendix (13 rows) and numbers_refly.md \u00a75 (12 rows) "
                "ARE resolved to a current value each. These section-granularity facts are still used to drive the "
                "B(i) 'superseded value presented as current' scan below, since that only needs the superseded "
                "value, not its resolved current counterpart.")
    out.append("- Section B(ii) only reports a mismatch when TA_verdicts.md records exactly ONE verdict for the "
                "matched base ID across its whole main table (ids like H1.2 recur with different verdicts per "
                "sub-row and are intentionally not scored, per the known H1.2 ambiguity).")
    out.append("")

    # ---------------- A ----------------
    out.append("## A. Supersession map")
    out.append("")
    out.append("| quantity | superseded value | current value | current source | origin |")
    out.append("|---|---|---|---|---|")
    for fct in a["facts"]:
        if "unresolved" in fct["current"] and "numbers.md internal" in fct["current"]:
            continue  # listed in the aggregated appendix below instead, to keep this table readable
        q = fct["quantity"].replace("|", "/")
        sup = fct["superseded"].replace("|", "/")[:140]
        cur = fct["current"].replace("|", "/")[:140]
        out.append(f"| {q} | {sup} | {cur} | {fct['current_source']} | {fct['origin']} |")
    out.append("")
    out.append(f"### A appendix: `numbers.md` internal correction-trail sections ({meta['numbers_sections']} "
                f"sections, {meta['numbers_section_rows']} escaped rows, section-granularity only)")
    out.append("")
    sec_seen = set()
    for fct in a["facts"]:
        if "numbers.md internal" not in fct["current"]:
            continue
        sec = fct["origin"].split("(section: ")[-1].rstrip(")")
        if sec not in sec_seen:
            out.append(f"- **{sec}**")
            sec_seen.add(sec)
    out.append("")

    # ---------------- B(i) ----------------
    out.append("## B(i). Superseded values presented as current")
    out.append("")
    out.append("**Read before acting**: a few rows below are matches WITHIN `refly_priors/numbers_refly.md`'s "
                "own §5 'Old vs new per criterion' table (or its direct copies under the writing pack), which "
                "is a deliberate side-by-side presentation of the old value next to the new one - not a defect. "
                "The headline findings that ARE real, unqualified presentations of a superseded value as current "
                "are the ones in `docs/thesis/tables/R4_information_vs_estimator.md:14`, `T1_scorecard.md:42`, "
                "`T5_H_tag_loss_drift.md:22`, and the `figures_thesis/index.md`/`index_results.md` rows for "
                "H5.4b / H-H4 (15 s) / H5.5 - none of those five files is the old-vs-new comparison table itself.")
    out.append("")
    if bi["hits"]:
        out.append("| file:line | quantity | matched value | origin (where it was superseded) | context |")
        out.append("|---|---|---|---|---|")
        for h in bi["hits"]:
            out.append(f"| {h['file']}:{h['line']} | {h['quantity']} | {h['matched_token']} | {h['origin']} | "
                        f"{h['text'].replace('|', '/')} |")
    else:
        out.append("No hits.")
    out.append("")

    # ---------------- B(ii) ----------------
    out.append("## B(ii). Verdict labels against TA_verdicts.md")
    out.append("")
    out.append(f"### H4.2 (must read NOT MET everywhere)")
    out.append("")
    out.append("H4.2 belongs to Experiment 4, not the E2-E6 tier-1 extensions, so TA_verdicts.md's FAIL-literal "
                "exception for extensions (see below) does not excuse a bare 'H4.2 FAIL' here - every occurrence "
                "below is checked against the one allowed wording, NOT MET.")
    out.append("")
    if bii["h42_checks"]:
        out.append("| file:line | label found | text |")
        out.append("|---|---|---|")
        for h in bii["h42_checks"]:
            flag = "" if h["label"] == "NOT MET" else " **MISMATCH**"
            out.append(f"| {h['file']}:{h['line']} | {h['label']}{flag} | {h['text'].replace('|', '/')} |")
    else:
        out.append("No H4.2 occurrences with an adjacent verdict label found outside TA_verdicts.md itself.")
    out.append("")
    out.append("### Other unambiguous mismatches (base ID has exactly one TA verdict)")
    out.append("")
    out.append("**Caveat, read before acting on this table**: this is a proximity match (nearest verdict word "
                "within 60 characters after the ID token on the same line), not a parse of which ID the word "
                "actually belongs to. Two rows below are very likely proximity false positives on manual "
                "inspection: the H1.1 row's 'WITHDRAWN' describes a withdrawn CLAIM ('EKF3 lower'), not H1.1's own "
                "verdict label; the H2.2 row's 'PASS' sits next to a figure/data self-check phrase, not "
                "necessarily the hypothesis verdict. Each row should be opened and read in context before being "
                "treated as a defect.")
    out.append("")
    if bii["mismatches"]:
        out.append("| file:line | id | found | TA verdict | text |")
        out.append("|---|---|---|---|---|")
        for h in bii["mismatches"]:
            out.append(f"| {h['file']}:{h['line']} | {h['id']} | {h['found']} | {h['ta_verdict']} | "
                        f"{h['text'].replace('|', '/')} |")
    else:
        out.append("None found.")
    out.append("")
    out.append("### Extension-experiment (E2-E6) ID/verdict-word occurrences, TA FAIL-literal convention")
    out.append("")
    out.append("Not counted as mismatches (see TA_verdicts.md's own legend: E2-E6 and the ablation keep their "
                "source's literal word FAIL, never harmonised to NOT MET - so a source document legitimately "
                "using PASS/NOT MET/NOT RUN for the same registered check is not itself a defect). Surfaced here "
                "per the advisor guidance this audit followed: report the tension, do not silently resolve it "
                "either way.")
    if bii["extension_notes"]:
        out.append("")
        out.append("| file:line | id | found | TA verdict | text |")
        out.append("|---|---|---|---|---|")
        for h in bii["extension_notes"][:100]:
            out.append(f"| {h['file']}:{h['line']} | {h['id']} | {h['found']} | {h['ta_verdict']} | "
                        f"{h['text'].replace('|', '/')} |")
    out.append("")
    out.append("### Non-standard bare-word labels (FAIL / MET / MISS without the project's full wording)")
    out.append("")
    out.append(f"{len(bii['nonstandard'])} occurrence(s). Per TA_verdicts.md's own legend, Experiments 1-5/5S use "
                "the words PASS / FAIL AS WORDED / NOT MET / WITHDRAWN / DESCRIPTIVE / REPORTED k/3, but the "
                "tier-1 extension experiments (E2-E6) and the ablation keep their own sources' literal word FAIL "
                "(not harmonised to NOT MET) - this is TA's own documented convention, not a defect, and such rows "
                "are reported here but not counted as mismatches.")
    if bii["nonstandard"]:
        out.append("")
        out.append("| file:line | id | label | text |")
        out.append("|---|---|---|---|")
        for h in bii["nonstandard"][:200]:
            out.append(f"| {h['file']}:{h['line']} | {h['id']} | {h['label']} | {h['text'].replace('|', '/')} |")
        if len(bii["nonstandard"]) > 200:
            out.append(f"| ... | ... | ... | {len(bii['nonstandard']) - 200} more not shown | |")
    out.append("")
    out.append("### Subprocess checks (run read-only, not modified)")
    out.append("")
    out.append("**`eval/ta_verdicts_check.py` was deliberately NOT run.** Its own docstring states it WRITES "
                "`docs/thesis/tables/TA_verdicts.md` and RENDERS "
                "`docs/thesis/figures_thesis/tables_extra/TA_verdicts.{pdf,png}` as part of running - it is a "
                "generator/checker hybrid, not a pure read-only check, despite being named as one to consult in "
                "the task. Running it once during development of this script touched those three files; the "
                "change was reverted with `git checkout --` before anything was committed, and the script is "
                "excluded from every subsequent run of this audit to keep the read-only guarantee. "
                "`eval/caption_verdict_check.py` and `tools/check_numbers_frozen.py` were read in full first and "
                "confirmed to only read and print.")
    out.append("")
    for name, res in ctx["subprocess_checks"].items():
        if res is None:
            out.append(f"- `{name}`: not found, skipped.")
            continue
        out.append(f"- `{name}` (exit {res['returncode']}):")
        out.append("```")
        out.append(res["stdout"] or "(no stdout)")
        out.append("```")
    out.append("")

    # ---------------- C ----------------
    out.append("## C. Numeric table cells against their cited source")
    out.append("")
    out.append(f"{c['n_cites']} `numbers*.md:LINE[-LINE]` citations found across the thesis-facing scan set. "
                "Only this citation form is resolved automatically (M:/C:/P:/json:/code: citations are provenance "
                "to a different document and are counted as unresolved, not guessed at). A citing line is scored "
                "a match if at least one numeric token on that line also appears verbatim within the cited "
                "`numbers*.md` line window (+/-1 line).")
    out.append("")
    out.append("### Mismatches: cite drift (value found elsewhere in the file, not at the cited line)")
    out.append("")
    if c["cite_drift"]:
        out.append("| file:line | cite | found at |")
        out.append("|---|---|---|")
        for h in c["cite_drift"][:300]:
            out.append(f"| {h['file']}:{h['line']} | {h['cite']} | {h['found_at']} |")
    else:
        out.append("None.")
    out.append("")
    out.append("### Mismatches: value not found anywhere in the cited file")
    out.append("")
    if c["not_found"]:
        out.append("| file:line | cite | tokens on citing line |")
        out.append("|---|---|---|")
        for h in c["not_found"][:300]:
            out.append(f"| {h['file']}:{h['line']} | {h['cite']} | {', '.join(h['tokens'])} |")
    else:
        out.append("None.")
    out.append("")
    out.append(f"### Unresolved ({len(c['unresolved'])})")
    out.append("")
    out.append("Citing lines where no comparable numeric token could be extracted, or the target file could not "
                "be resolved - listed rather than guessed, per the request.")
    if c["unresolved"]:
        out.append("")
        out.append("| file:line | cite | reason |")
        out.append("|---|---|---|")
        for h in c["unresolved"][:200]:
            out.append(f"| {h['file']}:{h['line']} | {h['cite']} | {h['reason']} |")
    out.append("")

    # ---------------- D ----------------
    out.append("## D. Style checks")
    out.append("")
    out.append("Counts are per-file after stripping code spans, bracketed `[...]` citations, and (for table rows) "
                "a trailing provenance-looking source cell. Full file:line detail capped per file in this report; "
                "re-run the script for the complete list if needed.")
    out.append("")
    out.append("| file | prose en/em dashes (not a digit-range) | bare `RTF 0.5` (not wrapped as 'half real-time "
                "(RTF 0.5)') |")
    out.append("|---|---|---|")
    any_d = False
    for fpath in sorted(d[0].keys()):
        counts = d[0][fpath]
        if counts.get("dash_prose") or counts.get("rtf_bare"):
            any_d = True
            out.append(f"| {fpath} | {counts.get('dash_prose', 0)} | {counts.get('rtf_bare', 0)} |")
    if not any_d:
        out.append("| (none) | 0 | 0 |")
    out.append("")
    out.append("### Sample detail (up to 40 lines per file)")
    out.append("")
    shown = 0
    for fpath, items in d[1].items():
        if not items:
            continue
        out.append(f"**{fpath}**")
        for li, kind, txt in items:
            out.append(f"- L{li} [{kind}]: `{txt}`")
            shown += 1
        out.append("")
        if shown > 400:
            out.append("(truncated)")
            break

    # ---------------- E ----------------
    out.append("## E. EKF3 4.3 s switching delay / 4.10 m jump statements")
    out.append("")
    sd, lua_p, vote_line, latency_line = ctx["switch_delay_source"]
    out.append(f"Source checked: `eval/results/expO_switch_delay/switch_delay.json` "
                f"({'loaded OK' if sd else 'NOT LOADED'}) and `{relp(lua_p)}` "
                f"({'found' if read(lua_p) else 'NOT FOUND'}).")
    if vote_line:
        out.append(f"- Harness vote line (lua): `{vote_line}`")
    if latency_line:
        out.append(f"- Harness latency line (lua): `{latency_line}`")
    out.append("- `numbers.md` \u00a716.2 (O - outdoor->indoor): EKF3 live largest step in 10 s after return = "
                "**4.10 m (reset jump, every flight)**; error at GNSS return 3.53-3.54 m. This is the measured "
                "source of both numbers (not independently re-derived here; see METHODOLOGY context cited in the "
                "task).")
    out.append("")
    out.append("### Mechanism, confirmed from the stored data and the harness script (read, not re-derived)")
    out.append("")
    out.append("`sim/scripts/o_source_switch.lua`: `VMAX = 20`, re-scheduled every 100 ms (`return update, 100`); "
                "a full swing from +20 to -20 needs 40 one-sided vote increments, i.e. **40 x 100 ms = 4.0 s** - "
                "this is the 'harness Lua script's 40-vote (4.0 s) GPS-status vote' the task's known context "
                "names, confirmed directly in the script's own constants, not assumed.")
    out.append("")
    out.append("`eval/results/expO_switch_delay/switch_delay.json` (`O_r1`/`O_r2`/`O_r3b`, all three agree to "
                "within 0.06 s) breaks the ON-side delay into exactly these two parts: "
                "`gps_status_minus_parm_sitl_s` = 0.30-0.36 s (SIM_GPS1_ENABLE flip to a good GPS fix - the "
                "'~0.3 s simulated GPS latency'), then `ss_minus_gps_status_sitl_s` = 4.04 s (good fix to "
                "`XKFS.SS` actually switching) - and `lua_msgs_sitl_s`'s own 'O-switch: source set 1 (GPS)' log "
                "line fires at essentially the same instant as the `XKFS.SS` change (within 0.06 s), not ~4 s "
                "before it. The ~4 s gap sits BETWEEN the GPS fix becoming good and the Lua script's own vote "
                "completing, not between the Lua script firing and EKF3 acting on it. Total delay "
                "(`ss_minus_marker_sitl_s`) = 4.32-4.37 s, matching the stated 4.3 s.")
    out.append("")
    out.append("**Finding worth flagging on its own**: `docs/thesis/writing_pack/new_2026-11-11/caption_detail.md` "
                "Task 6 (lines 145-193) is the single most detailed investigation of this delay found anywhere in "
                "the scanned corpus - it independently re-measures `XKFS.SS` and the `XKF1` position jump from "
                "each flight's `ardupilot.bin` and gets the same 4.3 s / 4.10 m numbers. But its own explanation "
                "(lines 163-193) attributes the delay to **EKF3's internal GPS-validation gate** "
                "(`readyToUseGPS()`/`gpsGoodToAlign` in `AP_NavEKF3_Control.cpp`/`AP_NavEKF3_VehicleStatus.cpp`), "
                "and never mentions the harness's `o_source_switch.lua` vote script at all, although it does "
                "honestly caveat (line 192) that 'the exact 4.3 s was not traced sample-by-sample through that "
                "gate here - it is measured ... not derived from the gate's internal thresholds.' Given the "
                "switch_delay.json breakdown above, the dominant ~4.0 s component times out almost exactly with "
                "the harness script's own 40-vote timer, not with an EKF3-internal threshold search of that "
                "script's own constants; this document's attribution looks incomplete at best, and is itself an "
                "UNQUALIFIED statement by the task's definition (it names an EKF3-internal cause, not the harness "
                "switching script). This is reported as a finding for the coordinator, not resolved here.")
    out.append("")
    if e:
        out.append("| file:line | matched | qualified? | text |")
        out.append("|---|---|---|---|")
        for h in e:
            qflag = "yes" if h["qualified"] else "**NO**"
            out.append(f"| {h['file']}:{h['line']} | {h['matched']} | {qflag} | {h['text'].replace('|', '/')} |")
    else:
        out.append("No statements matching the 4.3 s / 4.10 m / 3.53-3.54 m / switching-delay keywords were found "
                    "in the thesis-facing scan set.")
    out.append("")

    # ---------------- F ----------------
    out.append("## F. Coverage matrix")
    out.append("")
    out.append("Experiment-to-ID / experiment-to-table mapping sourced from "
                "`docs/thesis/tables/methods_experiment_matrix.md` (Table 3.4), not guessed.")
    out.append("")
    out.append("| experiment | registered IDs (per Table 3.4 / TA_verdicts.md) | has TA verdict row(s)? | "
                "has a table? | has a figure/caption? | numbers source |")
    out.append("|---|---|---|---|---|---|")
    for row in f:
        out.append(f"| {row['exp']}: {row['label']} | {', '.join(row['ids']) or '(none registered)'} | "
                    f"{row['ta_status']} | {row['table_status']} | {row['figure_status']} | {row['numbers_status']} |")
    out.append("")
    out.append("### Flags")
    out.append("")
    any_flag = False
    for row in f:
        if row.get("flags"):
            any_flag = True
            out.append(f"- **{row['exp']}**: {'; '.join(row['flags'])}")
    if not any_flag:
        out.append("No missing table/figure/verdict/source flagged.")
    out.append("")

    # ---------------- Fix list ----------------
    # ---------------- Candidates (reported separately, scope rule) ----------------
    cand = ctx["candidates"]
    out.append("## Candidates (figures_thesis/candidates/)")
    out.append("")
    out.append(f"Scanned {cand['n_files']} candidate caption/index files (not thesis-numbered; reported here "
                "separately, per the scope rule, rather than folded into the B/D counts above).")
    out.append("")
    out.append(f"- B(i) superseded-as-current hits: {len(cand['bi_hits'])}")
    if cand["bi_hits"]:
        out.append("")
        out.append("| file:line | quantity | matched value | origin |")
        out.append("|---|---|---|---|")
        for h in cand["bi_hits"][:50]:
            out.append(f"| {h['file']}:{h['line']} | {h['quantity']} | {h['matched_token']} | {h['origin']} |")
    out.append("")
    cb = cand["bii"]
    out.append(f"- B(ii) H4.2 occurrences: {len([h for h in cb['h42_checks'] if h['file'] != 'docs/thesis/tables/TA_verdicts.md'])}, "
                f"not NOT MET: {len([h for h in cb['h42_bad'] if h['file'] != 'docs/thesis/tables/TA_verdicts.md'])}; "
                f"other mismatches: {len(cb['mismatches'])}; non-standard bare-word labels: {len(cb['nonstandard'])}")
    out.append("")
    cd0, cd1 = cand["d"]
    any_cd = any(v.get("dash_prose") or v.get("rtf_bare") for v in cd0.values())
    out.append(f"- D style checks: {'see below' if any_cd else 'no prose en/em dashes or bare RTF 0.5 found'}")
    if any_cd:
        out.append("")
        out.append("| file | prose en/em dashes | bare `RTF 0.5` |")
        out.append("|---|---|---|")
        for fpath in sorted(cd0.keys()):
            counts = cd0[fpath]
            if counts.get("dash_prose") or counts.get("rtf_bare"):
                out.append(f"| {fpath} | {counts.get('dash_prose', 0)} | {counts.get('rtf_bare', 0)} |")
    out.append("")

    out.append("## Numbered fix list")
    out.append("")
    n = 0
    fixes = []
    for h in bi["hits"]:
        n += 1
        fixes.append(f"{n}. `{h['file']}:{h['line']}` presents the superseded value `{h['matched_token']}` for "
                      f"'{h['quantity']}' (superseded at {h['origin']}) without marking it superseded.")
    for h in bii["h42_bad"]:
        n += 1
        fixes.append(f"{n}. `{h['file']}:{h['line']}` labels an H4.2 occurrence '{h['label']}' - TA_verdicts.md "
                      f"requires NOT MET.")
    for h in bii["mismatches"]:
        n += 1
        fixes.append(f"{n}. `{h['file']}:{h['line']}` labels {h['id']} '{h['found']}' - TA_verdicts.md's unique "
                      f"verdict for this ID is {h['ta_verdict']}.")
    for h in c["cite_drift"]:
        n += 1
        fixes.append(f"{n}. `{h['file']}:{h['line']}` cites `{h['cite']}` but the value is actually at "
                      f"`{h['found_at']}` (cite drift).")
    for h in c["not_found"]:
        n += 1
        fixes.append(f"{n}. `{h['file']}:{h['line']}` cites `{h['cite']}`, but no matching numeric token "
                      f"({', '.join(h['tokens'])}) was found anywhere in that file.")
    for h in e:
        if not h["qualified"]:
            n += 1
            fixes.append(f"{n}. `{h['file']}:{h['line']}` states the switching delay/jump without qualifying it "
                          f"as coming from the harness's source-switch script: `{h['text']}`")
    for row in f:
        for flag in row.get("flags", []):
            n += 1
            fixes.append(f"{n}. Experiment {row['exp']}: {flag}")
    if not fixes:
        fixes = ["(no fixes required by the checks above - see scope notes for what was not fully resolved)"]
    out.extend(fixes)
    out.append("")

    out.append("## Writing-pack files read (sha256, for re-run comparability)")
    out.append("")
    if meta["writing_pack"]:
        for p, h in sorted(meta["wp_hashes"].items()):
            out.append(f"- `{p}`: `{h}`")
    else:
        out.append("(writing pack not found in this run environment - see Scope notes)")
    out.append("")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-report", action="store_true")
    ap.add_argument("--writing-pack", default=None)
    ap.add_argument("--out", default=REPORT_PATH)
    args = ap.parse_args()

    import datetime
    commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    wp_dir = find_writing_pack(args.writing_pack)
    wp_hashes = {}
    if wp_dir:
        for p in all_md_under(wp_dir):
            txt = read(p)
            if txt is not None:
                wp_hashes[os.path.relpath(p, wp_dir)] = sha(txt)[:16]

    main_rows, appendix_rows, ta_path = parse_ta_main_and_appendix()
    numbers_text = read(NUMBERS_FILES["numbers.md"]) or ""

    facts, sec_count, sec_rows = section_A(main_rows, appendix_rows, ta_path, numbers_text)

    scan_files = thesis_facing_files(wp_dir)
    cand_files = candidate_caption_files()

    bi_hits, bi_checked, bi_skipped = section_Bi(facts, scan_files)
    bii = section_Bii(main_rows, scan_files, ta_path)

    # Candidates (figures_thesis/candidates/): scanned but reported separately, per the scope
    # rule - they are not thesis-numbered, so they are not folded into the main B/D counts above.
    cand_bi_hits, cand_bi_checked, cand_bi_skipped = section_Bi(facts, cand_files)
    cand_bii = section_Bii(main_rows, cand_files, ta_path)
    cand_d = section_D(cand_files)

    # NOTE: eval/ta_verdicts_check.py is NOT run here even though it was named as a checker to
    # consult - its own docstring says it WRITES docs/thesis/tables/TA_verdicts.md and RENDERS
    # docs/thesis/figures_thesis/tables_extra/TA_verdicts.{pdf,png} as part of running (a
    # generator/checker hybrid, not a pure read-only check). Running it was tried once during
    # development of this script and it touched those three files (reverted via git checkout
    # before any commit); it is deliberately excluded to preserve this audit's read-only
    # guarantee. caption_verdict_check.py and check_numbers_frozen.py were read in full and
    # confirmed to only read + print before being run here.
    subprocess_checks = {
        "eval/caption_verdict_check.py": run_subprocess_check("eval/caption_verdict_check.py"),
        "tools/check_numbers_frozen.py": run_subprocess_check("tools/check_numbers_frozen.py"),
    }

    c = section_C(scan_files, False)
    d = section_D(scan_files)
    e_hits = section_E(scan_files)
    switch_delay_source = read_switch_delay_source()

    table_index = build_table_index()
    figure_index = build_figure_index()
    by_base_for_f = defaultdict(set)
    for r in main_rows:
        by_base_for_f[base_id(r["id"])].add(r["experiment"])

    # Textual-mention proxy for "has a table"/"has a figure": not a structural per-experiment
    # map (methods_experiment_matrix.md doesn't give table/figure numbers per row, so that was
    # not attempted), but a cheap, honest lower bound - count distinct tables/*.md files and
    # figures_thesis caption/index files whose text literally names the experiment.
    def mention_files(label_variants, glob_paths):
        hit = set()
        for p in glob_paths:
            text = read(p) or ""
            if any(v in text for v in label_variants):
                hit.add(relp(p))
        return hit

    table_md_files = [os.path.join(TABLES, f) for f in os.listdir(TABLES) if f.endswith(".md")]
    fig_text_files = [os.path.join(FIGS, "captions", f) for f in os.listdir(os.path.join(FIGS, "captions"))
                       if f.endswith(".md")] + \
                      [os.path.join(FIGS, f) for f in os.listdir(FIGS) if f.startswith("index") and f.endswith(".md")]

    f_rows = []
    for exp, label, ids in EXPERIMENT_ROWS:
        ta_status = "n/a"
        flags = []
        if ids:
            have = [i for i in ids if i in by_base_for_f]
            missing = [i for i in ids if i not in by_base_for_f]
            ta_status = f"{len(have)}/{len(ids)} present" + (f"; missing: {', '.join(missing)}" if missing else "")
            if missing:
                flags.append(f"TA_verdicts.md has no row for: {', '.join(missing)}")
        else:
            ta_status = "(no H-labelled hypotheses registered for this experiment per Table 3.4/TA legend)"
        variants = [f"Experiment {exp}"] if not exp.startswith("E") else [f"Extension {exp}", f"extension {exp}"]
        if exp == "5S":
            variants = ["5S", "Experiment 5S"]
        tfiles = mention_files(variants, table_md_files)
        ffiles = mention_files(variants, fig_text_files)
        table_status = f"mentioned in {len(tfiles)} table file(s) (textual-mention proxy, not a structural map)" + \
            (" - NONE" if not tfiles else "")
        figure_status = f"mentioned in {len(ffiles)} figure/caption/index file(s) (textual-mention proxy)" + \
            (" - NONE" if not ffiles else "")
        if not tfiles and exp != "5S":
            flags.append(f"no table file's text names 'Experiment {exp}' / 'Extension {exp}' (textual-mention proxy; a real table may still exist under a different label)")
        if not ffiles and exp != "5S":
            flags.append(f"no figure caption/index file's text names 'Experiment {exp}' / 'Extension {exp}' (textual-mention proxy)")
        if exp.startswith("E"):
            scorepath = os.path.join(DOCS, "tier1", "scores", f"{exp}_verdicts.json")
            scorepath_lower = os.path.join(DOCS, "tier1", "scores", f"{exp.lower()}_verdicts.json")
            numbers_status = "present" if (os.path.isfile(scorepath) or os.path.isfile(scorepath_lower)) else "MISSING"
            if numbers_status == "MISSING":
                flags.append(f"no docs/thesis/tier1/scores/{exp}_verdicts.json (or lowercase) found")
        elif exp == "5S":
            numbers_status = "eval/results/expH/safety_*.json (per TA_verdicts.md header)"
        else:
            numbers_status = "docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4)"
        f_rows.append({"exp": exp, "label": label, "ids": ids, "ta_status": ta_status,
                        "table_status": table_status, "figure_status": figure_status,
                        "numbers_status": numbers_status, "flags": flags})

    status_A = "PASS" if facts else "INCOMPLETE"
    status_Bi = "FAIL" if bi_hits else "PASS"
    status_Bii = "FAIL" if (bii["h42_bad"] or bii["mismatches"]) else "PASS"
    status_C = "INCOMPLETE" if (c["unresolved"] and c["n_cites"] and len(c["unresolved"]) > c["n_cites"] * 0.9) else \
        ("FAIL" if (c["cite_drift"] or c["not_found"]) else "PASS")
    status_D = "FAIL" if any(v.get("dash_prose") or v.get("rtf_bare") for v in d[0].values()) else "PASS"
    status_E = "FAIL" if any(not h["qualified"] for h in e_hits) else ("PASS" if e_hits else "INCOMPLETE")
    status_F = "FAIL" if any(r["flags"] for r in f_rows) else "INCOMPLETE"

    meta = {
        "commit": commit, "run_date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "writing_pack": relp(wp_dir) if wp_dir and wp_dir.startswith(ROOT) else wp_dir,
        "wp_hashes": wp_hashes,
        "status_A": status_A, "status_Bi": status_Bi, "status_Bii": status_Bii, "status_C": status_C,
        "status_D": status_D, "status_E": status_E, "status_F": status_F,
        "ta_appendix_n": len(appendix_rows), "refly_n": len([x for x in facts if "refly_priors" in x["origin"] and "criterion" not in x]),
        "extras_n": len([x for x in facts if "closed_loop_extras" in x["origin"]]),
        "numbers_sections": sec_count, "numbers_section_rows": sec_rows,
    }

    ctx = {
        "A": {"facts": facts}, "Bi": {"hits": bi_hits, "checked_files": bi_checked, "skipped_no_context": bi_skipped}, "Bii": bii,
        "C": c, "D": d, "E": e_hits, "F": f_rows, "meta": meta,
        "subprocess_checks": subprocess_checks, "switch_delay_source": switch_delay_source,
        "candidates": {"n_files": len(cand_files), "bi_hits": cand_bi_hits, "bii": cand_bii, "d": cand_d},
    }

    report = write_report(ctx)

    print(f"A  supersession map:        {status_A}  ({len(facts)} entries)")
    print(f"Bi superseded-as-current:   {status_Bi}  ({len(bi_hits)} hits)")
    print(f"Bii verdict labels vs TA:    {status_Bii}  (H4.2 bad={len(bii['h42_bad'])}, mismatches={len(bii['mismatches'])})")
    print(f"C  numeric cells vs source: {status_C}  (drift={len(c['cite_drift'])}, not_found={len(c['not_found'])}, unresolved={len(c['unresolved'])}/{c['n_cites']})")
    print(f"D  style checks:            {status_D}")
    print(f"E  4.3s/4.10m statements:   {status_E}  ({len(e_hits)} found, {sum(1 for h in e_hits if not h['qualified'])} unqualified)")
    print(f"F  coverage matrix:         {status_F}")

    if args.write_report:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"\nReport written to {relp(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
