#!/usr/bin/env python3
"""Check that docs/thesis/numbers.md is unchanged above its Errata section (CONTENT-FROZEN 2026-10-16, user ruling:
METHODOLOGY "RULINGS (user, 2026-10-16): the three mismatched numbers.md rows; thesis-facing untraceable values;
numbers.md CONTENT-FROZEN").

Everything above the line "## Errata" must hash to FROZEN_SHA256. The one normalisation is the frozen-commit token in
the header notice ("Frozen at commit `<sha>`"), which is masked so that recording the commit SHA after committing does
not change the hash. Appending erratum entries below "## Errata" is allowed. The git commit in the notice is provenance
only: if it resolves, its content is also compared; if it does not (e.g. after a squash merge), only a warning is printed.

Usage: python3 tools/check_numbers_frozen.py [--file PATH] [--print-hash]
Exit status: 0 = unchanged; 1 = changed, or the Errata heading is missing or duplicated."""
import argparse, hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMBERS = os.path.join(ROOT, "docs", "thesis", "numbers.md")
ERRATA = "## Errata"
FROZEN_SHA256 = "6a77b9abf19b668c6b9e11e021b460c11b4cc7ca844b75193a7a96e18fe17b5a"
COMMIT_RX = re.compile(r"Frozen at commit `([^`]*)`")


def frozen_part(text):
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.rstrip() == ERRATA]
    if len(idx) != 1:
        raise ValueError(f"expected exactly one '{ERRATA}' heading, found {len(idx)}")
    return "\n".join(lines[:idx[0]])


def normalise(part):
    return COMMIT_RX.sub("Frozen at commit `<sha>`", part, count=1)


def digest(text):
    return hashlib.sha256(normalise(frozen_part(text)).encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=NUMBERS)
    ap.add_argument("--print-hash", action="store_true")
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read()
    try:
        h = digest(text)
    except ValueError as e:
        print(f"FAIL: {e}"); return 1
    if a.print_hash:
        print(h); return 0
    ok = h == FROZEN_SHA256
    print(("PASS" if ok else "FAIL") + f": numbers.md above '{ERRATA}' sha256 {h} (frozen {FROZEN_SHA256})")
    m = COMMIT_RX.search(text)
    sha = m.group(1) if m else ""
    if re.fullmatch(r"[0-9a-f]{7,40}", sha):
        r = subprocess.run(["git", "-C", ROOT, "show", f"{sha}:docs/thesis/numbers.md"], capture_output=True, text=True)
        if r.returncode == 0:
            try:
                same = digest(r.stdout) == FROZEN_SHA256
            except ValueError:
                same = False
            print(f"{'ok' if same else 'MISMATCH'}: frozen commit {sha} has the frozen content" if same
                  else f"WARNING: the content at frozen commit {sha} does not hash to FROZEN_SHA256")
        else:
            print(f"WARNING: frozen commit {sha} not found in this repository (provenance only; the hash check stands)")
    else:
        print(f"WARNING: no frozen commit SHA recorded in the notice (found {sha!r})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
