#!/usr/bin/env python3
"""Checker for docs/thesis/methodology_factsheets/*.md (sheets 3.1-3.9).

Read-only. Exit 0 iff all checks pass. For every sheet it checks:
  (a) every `file:line` or `file:a-b` citation resolves to an existing file and existing line(s) --
      checked everywhere, touched or not;
  (b) numeric-token matching, in two modes:
      - STRICT (Facts/Appendix candidates bullets this pass's `git diff` against BASE_COMMIT touched):
        every "claimed" numeric token in the bullet (decimals, percentages, degree values, k/n counts
        and thousands-grouped integers -- the pragmatic set the brief calls out) must appear as an
        exact substring on a line cited DIRECTLY as numbers.md/numbers_tier1.md, or cited inside a
        `[NOT IN numbers ...: <file:line>]` tag (any file). A direct citation to any other file (M:,
        code, a results/pre-registration file) does not count in strict mode -- wrap it in a NOT-IN
        tag if the value is not really in a numbers file. A touched bullet with a claimed number and
        neither kind of source is itself a failure.
      - LENIENT (Flags (a)/(b) bullets, and any bullet this pass did not touch): every resolved
        citation in the bullet counts (a token already sourced to a direct M:/code citation elsewhere
        in the same bullet is not re-demanded of a numbers file). An untouched bullet with a claimed
        number and no numbers-file/NOT-IN source is reported (counted per sheet), never failed -- it
        predates this pass and was checked, if at all, by an earlier pass's own method.
  (c) prints per-sheet totals and a TOTAL line, including the untouched-untagged report count.

Convention used by the sheets (as written 2026-10-17, extended 2026-10-24/2026-11-02):
  - `numbers.md:123`, `numbers_tier1.md:123-129` : direct file:line citations, any file ending in one of
    the recognised extensions, optionally with a directory prefix (e.g. `tier1/e4_results.md:169`).
  - `M:1234` (and `M:1234-1240`, `M:1234, 1240-1245`) : shorthand for the root `METHODOLOGY.md`.
  - `[NOT IN numbers.md: <file:line...>]` / `[NOT IN numbers files: <file:line...>]` : a value not
    present verbatim in a numbers file; the bracket names where it can be found instead. A citation
    inside the bracket is resolved like any other (check a), and its line's text is admitted to the
    bullet's allowed content for (b) in BOTH modes, whatever file it points at (numbers.md,
    numbers_tier1.md, or an extension's own numbers file such as ablation_numbers.md, e4_results.md,
    e6_numbers.md, a pre-registration file, ...).

"Touched" is determined by `git diff -U0 BASE_COMMIT -- <sheet>` against the working tree (which is the
committed HEAD when this is run after committing): a brand-new file comes back fully touched. If git
cannot be run at all, every bullet is treated as touched (falls back to strict everywhere).

This script does not import or execute anything from the sheets; it only reads text.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SHEETS_DIR = HERE

SHEET_GLOB_PREFIX = "3."
EXTS = r"(?:md|py|parm|sdf|sh|json|yaml|tsv)"

# The commit this pass (2026-11-02) started from. Used only to scope the strict Facts/Appendix
# check (below) to bullets this pass actually added or edited, so a sheet nobody has re-verified
# since 2026-10-17 does not silently fail a rule it was never written against.
BASE_COMMIT = "4861f3d"


def touched_lines(relpath: str):
    """Line numbers (in the CURRENT file) added or changed since BASE_COMMIT, via `git diff -U0
    BASE_COMMIT -- relpath` (working tree vs BASE_COMMIT; the working tree is the committed HEAD
    here). A brand-new file shows as one hunk `@@ -0,0 +1,N @@` and so comes back fully touched.
    Returns None only if git could not be run at all (caller then treats everything as touched,
    i.e. falls back to the strict rule everywhere -- safe, if more demanding)."""
    try:
        proc = subprocess.run(
            ["git", "diff", "-U0", BASE_COMMIT, "--", relpath],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    if proc.returncode not in (0, 1):
        return None
    touched = set()
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for line in proc.stdout.split("\n"):
        m = hunk_re.match(line)
        if not m:
            continue
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        for n in range(start, start + max(count, 1)):
            touched.add(n)
    return touched

# ---------------------------------------------------------------------------
# File index (for resolving citations), built once by walking the repo tree.
# ---------------------------------------------------------------------------
SKIP_DIRS = {".git", ".claude"}  # .claude holds agent worktrees: full repo copies that make every citation ambiguous


def build_file_index(root: str) -> dict:
    """Return {basename: [relpaths]} and a set of all relpaths, for suffix resolution."""
    by_suffix_last = {}
    all_paths = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            all_paths.add(rel)
            by_suffix_last.setdefault(fn, []).append(rel)
    return by_suffix_last, all_paths


BY_BASENAME, ALL_PATHS = build_file_index(REPO_ROOT)
_FILE_LINES_CACHE = {}


def read_lines(relpath: str):
    if relpath not in _FILE_LINES_CACHE:
        full = os.path.join(REPO_ROOT, relpath)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                _FILE_LINES_CACHE[relpath] = f.read().split("\n")
        except OSError:
            _FILE_LINES_CACHE[relpath] = None
    return _FILE_LINES_CACHE[relpath]


def resolve_path(cite_path: str):
    """Resolve a cited path string to a unique repo-relative path, or return (None, reason)."""
    cite_path = cite_path.strip().strip("`")
    if cite_path == "M":
        cite_path = "METHODOLOGY.md"
    # Exact relpath match (as given, possibly with directories).
    cand_exact = cite_path if cite_path in ALL_PATHS else None
    if cand_exact:
        return cand_exact, None
    # Suffix match: any indexed path ending in "/" + cite_path, or equal to it.
    basename = cite_path.split("/")[-1]
    candidates = [
        p for p in BY_BASENAME.get(basename, [])
        if p == cite_path or p.endswith("/" + cite_path) or cite_path in p
    ]
    # Narrow to the ones that actually end with the given (possibly multi-segment) suffix.
    candidates = [p for p in BY_BASENAME.get(basename, []) if p.endswith(cite_path)]
    if not candidates:
        return None, f"no file matches '{cite_path}'"
    if len(candidates) == 1:
        return candidates[0], None
    # Ambiguous: prefer a root-level exact basename match if the citation was a bare basename.
    if cite_path == basename:
        root_level = [p for p in candidates if p == basename]
        if len(root_level) == 1:
            return root_level[0], None
    return None, f"ambiguous: '{cite_path}' matches {candidates}"


def line_exists(relpath: str, lineno: int) -> bool:
    lines = read_lines(relpath)
    if lines is None:
        return False
    # Allow a trailing blank line from the final newline.
    n = len(lines)
    if n > 0 and lines[-1] == "":
        n -= 1
    return 1 <= lineno <= n


def line_text(relpath: str, lineno: int) -> str:
    lines = read_lines(relpath)
    if lines is None or not (1 <= lineno <= len(lines)):
        return ""
    return lines[lineno - 1]


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------
# A citation is: (optional backtick) <path ending in a recognised extension, OR bare "M"> ":" <digit list>
# The digit list is a comma-separated list of integers or integer-integer ranges (hyphen or en/em dash).
PATH_PART = r"[A-Za-z0-9_][A-Za-z0-9_./\-]*\." + EXTS
DIGLIST = r"\d+(?:\s*[-–—]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–—]\s*\d+)?)*"
CITE_RE = re.compile(r"(?P<path>" + PATH_PART + r"|\bM(?=:))" + r":\s*(?P<nums>" + DIGLIST + r")")


def parse_digit_list(nums: str):
    """Return (list_of_individual_ints, list_of_(lo,hi)_ranges) from a comma-separated digit list."""
    singles = []
    ranges = []
    for part in nums.split(","):
        part = part.strip()
        m = re.match(r"^(\d+)\s*[-–—]\s*(\d+)$", part)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            ranges.append((lo, hi))
        elif re.match(r"^\d+$", part):
            singles.append(int(part))
    return singles, ranges


def find_citations(text: str):
    """Yield dicts: {span:(start,end), path, resolved, lines:set_of_ints, ok:bool, reason}."""
    out = []
    for m in CITE_RE.finditer(text):
        path = m.group("path")
        nums = m.group("nums")
        resolved, reason = resolve_path(path)
        singles, ranges = parse_digit_list(nums)
        all_lines = set(singles)
        line_ok = True
        bad = []
        if resolved:
            for n in singles:
                if not line_exists(resolved, n):
                    line_ok = False
                    bad.append(n)
            for lo, hi in ranges:
                if lo > hi:
                    lo, hi = hi, lo
                for n in (lo, hi):
                    if not line_exists(resolved, n):
                        line_ok = False
                        bad.append(n)
                for n in range(lo, hi + 1):
                    all_lines.add(n)
        else:
            line_ok = False
        out.append({
            "span": m.span(),
            "raw": m.group(0),
            "path": path,
            "resolved": resolved,
            "reason": reason,
            "line_ok": line_ok,
            "bad_lines": bad,
            "lines": all_lines,
        })
    return out


NUMBERS_FILE_RE = re.compile(r"^numbers(_tier1)?\.md$")


def is_numbers_file(resolved_path: str) -> bool:
    if not resolved_path:
        return False
    base = resolved_path.split("/")[-1]
    return bool(NUMBERS_FILE_RE.match(base))


NOT_IN_RE = re.compile(r"\[NOT IN numbers(?:\.md| files)[^\]]*\]")

# ---------------------------------------------------------------------------
# Numeric-token extraction and the identifier allowlist (check b)
# ---------------------------------------------------------------------------
ALLOWLIST_PATTERNS = [
    r"D\d+\b",                       # decision numbers D1, D80
    r"FS-\d+\b",                     # this task's own decision labels
    r"[HPSVC]-E\d[\w.]*\b",          # H-E2.1, P-E3b.1, S-E5.5, V-E6 style labels
    r"\b[HPSVC]\d[\w.]*\b",           # H3.1, P-L4, C1, V3
    r"\br\d+[a-z]?\b",               # rung r0 .. r7, r6s
    r"\bs\d+\b",                     # seed s0, s1, s2
    r"T_[A-D]_r\d+[a-z]?\b",         # T_A_r1, T_D_r3
    r"E6[MV]_\w+\b",                 # E6M_fig8_r1b, E6V_fig8_check
    r"\bQ\d+b?\b",                   # Q1 .. Q10, Q11b
    r"A-Q\d+\b",                     # A-Q8 .. A-Q12
    r"§[\d.]+\b",                # section refs §8.4
  r"\b[0-9a-f]{6,40}\b",            # git commit hashes
    r"\b20\d{2}-\d{2}-\d{2}\b",       # ISO dates
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b",  # HH:MM / HH:MM:SS clock times
    r"\blap[- ]?\d\b",                 # lap 1, lap-5
    r"\bk\s*=\s*\d+(?:\.\d+)?\b",     # k = 2.385 (robust kernel constant, cited separately)
    r"\b\d+/\d+\s*Hz\b",              # a rate pair written "400/50 Hz" (two rates, not a count)
]
ALLOW_RE = re.compile("|".join(ALLOWLIST_PATTERNS))

TOKEN_PATTERNS = [
    r"(?<![\w.])\d+\.\d+(?![\w.])",          # decimals: 0.0409, 1.76
    r"\b\d+/\d+\b",                           # counts: 9/9, 0/12
    r"\b\d{1,3}(?:,\d{3})+\b",                 # thousands: 13,253
    r"\b\d+%",                                 # bare integer percent
    r"\b\d+°",                             # bare integer degrees
    r"\b\d+×",                             # bare integer multiplier (2x gap)
]
TOKEN_RE = re.compile("|".join(TOKEN_PATTERNS))


def mask_citation_spans(text: str, citations: list) -> str:
    masked = text
    for c in sorted(citations, key=lambda c: c["span"][0], reverse=True):
        s, e = c["span"]
        masked = masked[:s] + (" " * (e - s)) + masked[e:]
    return masked


def extract_numeric_tokens(text: str):
    toks = []
    for m in TOKEN_RE.finditer(text):
        s, e = m.span()
        # Skip if this exact span is inside an allowlisted identifier match.
        covered = False
        for am in ALLOW_RE.finditer(text):
            if am.start() <= s and e <= am.end():
                covered = True
                break
        if covered:
            continue
        toks.append(m.group(0))
    return toks


# ---------------------------------------------------------------------------
# Bullet-unit segmentation
# ---------------------------------------------------------------------------
BULLET_START = re.compile(r"^(-\s|·\s)")
SECTION_HEADING_RE = re.compile(r"^##\s+(.*)$")


def _section_of(title: str):
    if title.startswith("Facts"):
        return "Facts"
    if title.startswith("Appendix"):
        return "Appendix candidates"
    if "Flags (a)" in title or title.startswith("Flags (a"):
        return "Flags (a)"
    if "Flags (b)" in title or title.startswith("Flags (b"):
        return "Flags (b)"
    return None


def iter_units(lines):
    """Yield (start_line_1based, text, is_bullet, section) for each bullet/sub-item/preamble
    block. `section` is one of Facts/Appendix candidates/Flags (a)/Flags (b)/None, from the
    nearest preceding top-level `## ` heading (a `### ` subheading, as in sheet 3.9, does not
    change it)."""
    cur_text = []
    cur_start = None
    cur_is_bullet = False
    cur_section = None
    units = []
    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        lstripped = raw.lstrip()
        if stripped == "" or stripped.startswith("#"):
            if cur_text:
                units.append(("\n".join(cur_text), cur_start, cur_is_bullet, cur_section))
                cur_text, cur_start = [], None
            if stripped.startswith("## "):
                m = SECTION_HEADING_RE.match(stripped)
                if m:
                    cur_section = _section_of(m.group(1).strip())
            continue
        if BULLET_START.match(lstripped):
            if cur_text:
                units.append(("\n".join(cur_text), cur_start, cur_is_bullet, cur_section))
            cur_text = [raw]
            cur_start = i
            cur_is_bullet = True
        else:
            if cur_text:
                cur_text.append(raw)
            else:
                cur_text = [raw]
                cur_start = i
                cur_is_bullet = False
    if cur_text:
        units.append(("\n".join(cur_text), cur_start, cur_is_bullet, cur_section))
    return units


# ---------------------------------------------------------------------------
# Section / bullet counting (for the (c) totals), mirroring the README convention:
# top-level bullets counted per sheet under Facts / Appendix candidates / Flags (a) / Flags (b).
# ---------------------------------------------------------------------------
SECTION_RE = re.compile(r"^##\s+(.*)$")


def count_sections(lines):
    counts = {"Facts": 0, "Appendix candidates": 0, "Flags (a)": 0, "Flags (b)": 0}
    current = None
    for raw in lines:
        m = SECTION_RE.match(raw.strip())
        if m:
            title = m.group(1).strip()
            if title.startswith("Facts"):
                current = "Facts"
            elif title.startswith("Appendix"):
                current = "Appendix candidates"
            elif "Flags (a)" in title or title.startswith("Flags (a"):
                current = "Flags (a)"
            elif "Flags (b)" in title or title.startswith("Flags (b"):
                current = "Flags (b)"
            else:
                current = None
            continue
        # Top-level bullet: a "- " line at zero indentation. Matches the original README
        # convention: indented "  - " / "  · " sub-items are not counted separately.
        if current and raw.startswith("- "):
            counts[current] += 1
    return counts


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------

def check_sheet(path: str, relpath: str):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    name = os.path.basename(path)

    touched = touched_lines(relpath)  # None => git unavailable; treat every bullet as touched

    failures = []
    citation_checks = 0
    citation_failures = 0
    token_checks = 0
    token_failures = 0
    untouched_untagged = 0  # reported only, never fails: pre-existing bullets outside this pass

    units = iter_units(lines)
    for unit_text, start_line, is_bullet, section in units:
        citations = find_citations(unit_text)
        for c in citations:
            citation_checks += 1
            if not c["resolved"]:
                citation_failures += 1
                failures.append(
                    f"{name}:{start_line}: citation '{c['raw']}' does not resolve ({c['reason']})"
                )
            elif not c["line_ok"]:
                citation_failures += 1
                failures.append(
                    f"{name}:{start_line}: citation '{c['raw']}' -> {c['resolved']} has out-of-range line(s) {c['bad_lines']}"
                )

        if not is_bullet:
            continue

        n_unit_lines = unit_text.count("\n") + 1
        is_touched = touched is None or any(
            (start_line + k) in touched for k in range(n_unit_lines)
        )
        strict = is_touched and section in ("Facts", "Appendix candidates")

        not_in_matches = list(NOT_IN_RE.finditer(unit_text))
        has_numbers_cite = any(
            c["resolved"] and c["line_ok"] and is_numbers_file(c["resolved"]) for c in citations
        )
        has_numbers_source = has_numbers_cite or bool(not_in_matches)

        masked = mask_citation_spans(unit_text, citations)
        tokens = extract_numeric_tokens(masked)

        if not has_numbers_source:
            # No numbers.md/numbers_tier1.md citation and no [NOT IN ...] tag anywhere in this
            # bullet. Facts/Appendix in a touched bullet with a claimed number is a hard failure
            # (brief's rule); everywhere else (Flags, by design cite two non-numbers sources; or
            # an untouched bullet from before this pass) it is reported only, never a failure.
            if tokens:
                if strict:
                    token_checks += len(tokens)
                    token_failures += len(tokens)
                    failures.append(
                        f"{name}:{start_line}: touched Facts/Appendix bullet has claimed number(s) "
                        f"{tokens} but no numbers.md/numbers_tier1.md citation and no [NOT IN ...] tag"
                    )
                else:
                    untouched_untagged += 1
            continue

        # Allowed content for the token match:
        #   - strict (touched Facts/Appendix): only numbers.md/numbers_tier1.md citations, plus
        #     citations named inside a [NOT IN ...] bracket (of any file -- that is what the
        #     bracket is for).
        #   - lenient (Flags, or an untouched bullet): every resolved citation's line text in the
        #     unit counts, so a token already sourced to a direct M:/code citation elsewhere in
        #     the same bullet is not re-demanded of the numbers file.
        allowed_lines_text = []
        for c in citations:
            if not (c["resolved"] and c["line_ok"]):
                continue
            if strict and not is_numbers_file(c["resolved"]):
                continue
            for n in c["lines"]:
                allowed_lines_text.append(line_text(c["resolved"], n))
        for nm in not_in_matches:
            for c in find_citations(nm.group(0)):
                if c["resolved"] and c["line_ok"]:
                    for n in c["lines"]:
                        allowed_lines_text.append(line_text(c["resolved"], n))

        allowed_blob = "\n".join(allowed_lines_text)
        for tok in tokens:
            token_checks += 1
            candidates = [tok]
            if tok.endswith("°"):
                candidates.append(tok[:-1] + " deg")
                candidates.append(tok[:-1] + "deg")
            if not any(cand in allowed_blob for cand in candidates):
                token_failures += 1
                failures.append(
                    f"{name}:{start_line}: numeric token '{tok}' not found on any cited "
                    f"{'numbers-file/NOT-IN' if strict else 'numbers-file'} line"
                    f"{' (strict: touched Facts/Appendix bullet)' if strict else ''}"
                )

    counts = count_sections(lines)
    return {
        "name": name,
        "failures": failures,
        "citation_checks": citation_checks,
        "citation_failures": citation_failures,
        "token_checks": token_checks,
        "token_failures": token_failures,
        "untouched_untagged": untouched_untagged,
        "counts": counts,
    }


def main():
    sheet_paths = sorted(
        os.path.join(SHEETS_DIR, fn)
        for fn in os.listdir(SHEETS_DIR)
        if fn.startswith(SHEET_GLOB_PREFIX) and fn.endswith(".md")
    )
    if not sheet_paths:
        print("No sheets found.", file=sys.stderr)
        return 1

    total_citation_checks = 0
    total_citation_failures = 0
    total_token_checks = 0
    total_token_failures = 0
    total_bullets = 0
    total_untouched_untagged = 0
    any_failures = False

    for path in sheet_paths:
        relpath = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
        result = check_sheet(path, relpath)
        n_bullets = sum(result["counts"].values())
        total_bullets += n_bullets
        total_citation_checks += result["citation_checks"]
        total_citation_failures += result["citation_failures"]
        total_token_checks += result["token_checks"]
        total_token_failures += result["token_failures"]
        total_untouched_untagged += result["untouched_untagged"]

        print(f"== {result['name']} ==")
        print(f"  bullets (Facts/Appendix/Flags a/Flags b): {result['counts']}")
        print(f"  citations checked: {result['citation_checks']}, failed: {result['citation_failures']}")
        print(f"  numeric tokens checked: {result['token_checks']}, failed: {result['token_failures']}")
        if result["untouched_untagged"]:
            print(f"  untouched bullets with a claimed number but no numbers-file/NOT-IN source "
                  f"(pre-existing, not checked, reported only): {result['untouched_untagged']}")
        if result["failures"]:
            any_failures = True
            for f in result["failures"]:
                print(f"  FAIL: {f}")
        print()

    print("TOTAL "
          f"bullets={total_bullets} "
          f"citations={total_citation_checks} citation_failures={total_citation_failures} "
          f"tokens={total_token_checks} token_failures={total_token_failures} "
          f"untouched_untagged_reported_only={total_untouched_untagged}")

    if any_failures or total_citation_failures or total_token_failures:
        print("TOTAL RESULT: FAIL")
        return 1
    print("TOTAL RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
