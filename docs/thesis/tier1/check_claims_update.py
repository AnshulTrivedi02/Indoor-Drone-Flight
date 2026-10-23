#!/usr/bin/env python3
"""Exact check of docs/thesis/tier1/claims_update.md (read-only; writes nothing).

Three registries:
  1. QUOTES      every '> "..." — `file:line[-line]`' line in claims_update.md: the quoted text must be a substring
                 of the cited line span (lines joined with one space after stripping), UTF-8 exact.
  2. VERDICTS    every verdict + count typed in claims_update.md, checked against scores/*_verdicts.json.
  3. NUMBERS     every number typed (outside quotes and `code`): registered with a source file in which the same
                 string occurs (token-bounded), or a phrase whose source phrase occurs verbatim.
  + COMPLETENESS every numeric token left in claims_update.md after removing registered phrases and identifiers
                 (hypothesis ids, dates, section numbers, run names) must be zero.
Exit 0 iff everything passes.
"""
import json
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]
T1 = WS / "docs/thesis/tier1"
DOC = T1 / "claims_update.md"
doc = DOC.read_text(encoding="utf-8")


def rd(p):
    return (WS / p).read_text(encoding="utf-8")


def norm(s):
    return re.sub(r"\s+", " ", s)


def has_tok(text, tok):
    return re.search(r"(?<![\d.])" + re.escape(tok) + r"(?![\d])", text) is not None


fails = []
n = {"quotes": 0, "verdicts": 0, "numbers": 0}

# ---------------------------------------------------------------- 1. quotes
qre = re.compile(r'^> "(.*)" — `([^`:]+):(\d+)(?:-(\d+))?`\s*$')
for ln in doc.split("\n"):
    if not ln.startswith('> "'):
        continue
    m = qre.match(ln)
    if not m:
        fails.append(f"QUOTE unparsable: {ln[:80]}")
        continue
    text, f, a, b = m.group(1), m.group(2), int(m.group(3)), int(m.group(4) or m.group(3))
    lines = rd(f).split("\n")[a - 1:b]
    span = " ".join(x.strip() for x in lines)
    n["quotes"] += 1
    if text not in span:
        fails.append(f"QUOTE not found at {f}:{a}-{b}: {text[:70]}")

# ---------------------------------------------------------------- 2. verdicts
S = T1 / "scores"
e2 = json.loads((S / "E2_verdicts.json").read_text())
e3 = json.loads((S / "E3_verdicts.json").read_text())
e4 = json.loads((S / "E4_verdicts.json").read_text())
e5 = json.loads((S / "e5_verdicts.json").read_text())


def e3c(prefix, arm="criteria_a"):
    ks = [k for k in e3[arm] if k.startswith(prefix)]
    assert len(ks) == 1, (prefix, ks)
    return e3[arm][ks[0]]


VERDICTS = [  # (label, json verdict, json count, expected verdict, expected count, doc phrases that must be present)
    ("H-E5.1", e5["criteria"]["H-E5.1"]["verdict"], e5["criteria"]["H-E5.1"]["count"], "PASS", "3/3", ["H-E5.1 PASS 3/3"]),
    ("H-E5.2", e5["criteria"]["H-E5.2"]["verdict"], e5["criteria"]["H-E5.2"]["count"], "PASS", "3/3", ["H-E5.2 PASS 3/3"]),
    ("H-E5.3", e5["criteria"]["H-E5.3"]["verdict"], e5["criteria"]["H-E5.3"]["count"], "PASS", "3/3", ["H-E5.3 PASS 3/3"]),
    ("P-E5.4", e5["criteria"]["P-E5.4"]["verdict"], e5["criteria"]["P-E5.4"]["count"], "PASS", "3/3", ["P-E5.4 PASS 3/3"]),
    ("S-E5.5", e5["criteria"]["S-E5.5"]["verdict"], e5["criteria"]["S-E5.5"]["count"], "PASS", "3/3", ["S-E5.5 PASS 3/3"]),
    ("S-E5.6", e5["criteria"]["S-E5.6"]["verdict"], e5["criteria"]["S-E5.6"]["count"], "PASS", "3/3", ["S-E5.6 PASS 3/3"]),
    ("H-E3.1", e3c("H-E3.1")["verdict"], e3c("H-E3.1")["count"], "FAIL", "0/9", ["H-E3.1 FAIL 0/9"]),
    ("H-E3.2", e3c("H-E3.2")["verdict"], e3c("H-E3.2")["count"], "FAIL", "0/9", ["H-E3.2 FAIL 0/9"]),
    ("H-E3.3", e3c("H-E3.3")["verdict"], e3c("H-E3.3")["count"], "FAIL", "3/9", ["H-E3.3 FAIL 3/9"]),
    ("P-E3.4", e3c("P-E3.4")["verdict"], e3c("P-E3.4")["count"], "FAIL", "0/9", ["P-E3.4 FAIL 0/9"]),
    ("P-E3.5a", e3c("P-E3.5a")["verdict"], e3c("P-E3.5a")["count"], "FAIL", "0/9", ["P-E3.5a FAIL 0/9"]),
    ("P-E3.5b", e3c("P-E3.5b")["verdict"], e3c("P-E3.5b")["count"], "FAIL", "0/9", ["P-E3.5b FAIL 0/9"]),
    ("P-E3.5c", e3c("P-E3.5c")["verdict"], e3c("P-E3.5c")["count"], "PASS", "9/9", ["P-E3.5c PASS 9/9"]),
    ("P-E3.6", e3c("P-E3.6")["verdict"], e3c("P-E3.6")["count"], "FAIL", "0/3", ["P-E3.6 FAIL 0/3"]),
    ("P-E3b.1 1%", e3c("P-E3b.1 0.01", "criteria_b")["verdict"], e3c("P-E3b.1 0.01", "criteria_b")["count"], "PASS", "9/9",
     ["P-E3b.1 PASS 9/9 at 1%"]),
    ("P-E3b.1 5%", e3c("P-E3b.1 0.05", "criteria_b")["verdict"], e3c("P-E3b.1 0.05", "criteria_b")["count"], "PASS", "9/9",
     ["9/9 at 5%"]),
    ("P-E3b.2", e3c("P-E3b.2", "criteria_b")["verdict"], e3c("P-E3b.2", "criteria_b")["count"], "PASS", "3/3", ["P-E3b.2 PASS 3/3"]),
    ("P-E4.1", e4["P-E4.1"]["verdict"], e4["P-E4.1"]["count"], "PASS", "12/12", ["P-E4.1 PASS 12/12"]),
    ("P-E4.2", e4["P-E4.2"]["verdict"], None, "PASS", None, ["P-E4.2 PASS"]),
    ("H-E4.3", e4["H-E4.3"]["verdict"], e4["H-E4.3"]["count"], "FAIL", "7/12", ["H-E4.3 FAIL 7/12"]),
    ("P-E2.5", e2["P-E2.5"]["verdict"], None, "FAIL", None, ["P-E2.5 FAIL"]),
]
for c in ("H-E2.1", "H-E2.2", "H-E2.3", "P-E2.4"):
    for cond in "BCD":
        v = e2["criteria"][c][cond]
        VERDICTS.append((f"{c} {cond}", v["verdict"], v["count"], "PASS", "3/3", []))
VERDICTS.append(("H-E2.1 headline", None, None, None, None, ["H-E2.1 PASS 3/3 in each of B, C, D (9/9)",
                                                            "PASS 3/3 in B, C and D (9/9)"]))
# P-E4.2: 12/12 at each of 0.25, 1, 2, 5 s on both readings
for w in ("0.25", "1", "2", "5"):
    pw = e4["P-E4.2"]["per_window"][w]
    VERDICTS.append((f"P-E4.2 W={w}", "PASS" if pw.get("count") == "12/12" else pw.get("count"), pw.get("count"),
                     "PASS", "12/12", []))
# E4 convergence: no flag on 10/10 cap-10 runs
pr = e4["convergence"]["per_run"]
nflag = sum(1 for v in pr.values() if v["NOT_CONVERGED"])
VERDICTS.append(("E4 convergence", "OK" if nflag == 0 else "FLAG", f"{len(pr) - nflag}/{len(pr)}", "OK", "10/10",
                 ["no flag at any window, 10/10 cap-10 runs"]))
mx = max(v["max_rms_reading_m"] for v in pr.values())
VERDICTS.append(("E4 convergence max RMS 0.0009", f"{mx:.4f}", None, "0.0009", None, ["largest RMS reading was 0.0009 m"]))

for lab, gv, gc, ev, ec, phrases in VERDICTS:
    n["verdicts"] += 1
    if ev is not None and gv != ev:
        fails.append(f"VERDICT {lab}: json {gv} != {ev}")
    if ec is not None and gc != ec:
        fails.append(f"VERDICT {lab}: json count {gc} != {ec}")
    for p in phrases:
        if p not in doc:
            fails.append(f"VERDICT {lab}: doc phrase missing: {p}")

# ---------------------------------------------------------------- 3. numbers
E2R, E3R, E4R, E5R = ("docs/thesis/tier1/e2_results.md", "docs/thesis/tier1/e3_results.md",
                      "docs/thesis/tier1/e4_results.md", "docs/thesis/tier1/e5_results.md")
PRE = "docs/thesis/tier1/preregistration.md"
NUM = "docs/thesis/numbers.md"
TOK = {  # token as typed -> source file where the same token occurs
    E5R: ["0.27", "0.42", "0.30", "0.1193", "0.8738", "0.0911", "1.4112", "0.1335", "0.9262", "0.0445", "0.9162",
          "0.0461", "1.3349", "0.0552", "1.0446", "6.87", "14.62", "6.34", "0.0574", "0.0494", "0.0760", "0.0198",
          "0.0270", "0.0172", "2.08", "1.84", "1.76", "2.25", "1.71", "3.21", "12/12"],
    E3R: ["0.71", "3.58", "2.385", "1.10", "3.7161", "4.2231", "0.3494", "0.2625", "0.3608", "51.26", "85.49",
          "10.77", "16.09", "49.699", "61.795", "0.0114", "0.0179", "0.0763", "0.1072", "3.6419", "1.4769", "4.1849",
          "4.2233", "8,622", "6,266", "144,218", "1.224", "3.674", "0/9", "3/9", "9/9", "0/3", "3/3"],
    E2R: ["0.15", "0.46", "1.35", "0.13", "0.41", "0.0317", "0.0238", "0.0492", "0.0687", "1.25", "2.43"],
    E4R: ["7/12", "10/12", "14.35", "15.13", "26.86", "28.22", "278.25", "303.36", "+0.0000020", "+0.0003395", "0.01",
          "-0.00", "0.02", "0.0009", "0.029"],
    NUM: ["96", "48", "27"],
    "docs/handovers/2026-10-24_tier1_stage2f_final.md": ["0/12"],
}
PHRASES = [  # (doc phrase, source file, source phrase): small counts and structural numbers, checked in context
    ("1.5 ×", PRE, "1.5 × lap-1"),
    ("2 ×", E3R, "≤ 2 × stored clean LC live"),
    ("±10%", E3R, "±10%"),
    ("1%", PRE, "1% and 5%"), ("5%", PRE, "1% and 5%"),
    ("33 ms", PRE, "33 ms"),
    ("0.25 s", PRE, "0.25 s"), ("0.5 s", PRE, "0.5, 1, 2 and 5 s"), ("1, 2 and 5 s", PRE, "0.5, 1, 2 and 5 s"),
    ("0.25–5 s", E4R, "W = 0.5 / 1 / 2 / 5 s"), ("from 0.25 to 5 s", E4R, "W = 0.5 / 1 / 2 / 5 s"),
    ("at 5 s", E4R, "at 5 s"), ("W = 0.5 / 1 / 2 / 5 s", E4R, "W = 0.5 / 1 / 2 / 5 s"),
    ("each of 0.25, 1, 2 and 5 s", E4R, "at 0.25, 1, 2 and 5 s"),
    ("6 of 9", E3R, "6 of 9 runs diverged"), ("0 of 9", E3R, "0 of 9 runs diverged"),
    ("0 of 21", E3R, "0 of 21 runs diverged"), ("17 of 18", E3R, "17 of 18 mislabelled runs"),
    ("6 of the 1% runs", E3R, "6 runs are SATISFIED, flagged"),
    ("the 3 runs that did not diverge pass", E3R, "the 3 non-diverged runs pass"),
    ("All 36 validation gates", E5R, "36/36 PASS"),
    ("after 5 extra updates", E5R, "after 5 extra updates"),
    ("n = 3 flights, 3 seeds each", PRE, "seeds 0, 1 and 2"),
    ("n = 3 flights, all with condition A (8 tags)", PRE, "`T_A_r1`, `T_A_r2`, `T_A_r3` (all 8 tags, as Experiment 3)"),
    ("all 8 tags", PRE, "all 8 tags"), ("8 tags", PRE, "all 8 tags"),
    ("4 tags (B)", PRE, "B (4 corner tags)"), ("2 tags (C)", PRE, "C (2 diagonal tags)"),
    ("4 and 2 tags", PRE, "B (4 corner tags), C (2 diagonal tags)"),
    ("with 4 and with 2 tags", PRE, "B (4 corner tags), C (2 diagonal tags)"),
    ("D (1 tag)", PRE, "D (tag 0 only)"), ("tag 0 only", PRE, "D (tag 0 only)"),
    ("12 Experiment 2 flights", PRE, "All 12 T flights"),
    ("rate 0", E3R, "rate 0"), ("serial 0% pair", E3R, "Serial 0% pair"),
    ("1 thread, nice 19", E4R, "1 thread, nice 19"),
    ("The 2-iteration LM cap", NUM, "capped at 2"), ("cap 2", E4R, "cap 2"), ("cap 10", E4R, "cap 10"),
    ("Cap 10", E4R, "cap 10"), ("cap-10", E4R, "LM-cap-10"),
    ("\"0 wrong ids\"", NUM, "0 wrong ids"),
    ("two room flights", PRE, "on `T_A_r1` (densest fixes) and `T_D_r1`"),
    ("1% wrong ids", PRE, "1% and 5%"),
    ("n = 3, so no reason", E2R, "With n = 3 per condition"),
]

body = "\n".join(l for l in doc.split("\n") if not l.startswith('> "'))
body = re.sub(r"`[^`]*`", " ", body)

for src, toks in TOK.items():
    text = rd(src)
    for t in toks:
        n["numbers"] += 1
        if not has_tok(text, t):
            fails.append(f"NUMBER {t} not in {src}")
        if not has_tok(body, t):
            fails.append(f"NUMBER {t} registered but not typed in claims_update.md")
for dp, src, sp in PHRASES:
    n["numbers"] += 1
    if norm(sp) not in norm(rd(src)):
        fails.append(f"PHRASE source missing in {src}: {sp}")
    if dp not in norm(body):
        fails.append(f"PHRASE not typed in claims_update.md: {dp}")

# ---------------------------------------------------------------- completeness scan
scan = norm(body)
VPH = [p for v in VERDICTS for p in v[5]]
for dp in sorted([x[0] for x in PHRASES] + VPH, key=len, reverse=True):
    scan = re.sub(r"(?<![\d.])" + re.escape(dp) + r"(?!\.?\d)", " ", scan)
IDS = [r"\d{4}-\d{2}-\d{2}", r"\b[HPSV]-E\d[a-c]?(?:\.\d)?[a-c]?\b", r"\b[HPV]-L\d\b", r"\bG0?-[LE]\d?\b",
       r"\b[HV]\d(?:\.\d)?(?:–[HV]\d\.\d)?\b", r"\bE\d(?:–E?\d)?\b", r"\bC\d(?:\(b\))?\b", r"\bD\d+\b", r"\bQ\d+\b",
       r"\bT_[A-D]_r\d\b", r"\br\d\b", r"\bs\d\b", r"§\d+(?:\.\d+)?(?:–§?\d+)?", r"\bF\d+\b", r"\b[TR]\d\b",
       r"Experiments? \d(?:(?:–| and )\d)?", r"rules? \d(?:–\d)?", r"rows? \d+(?: and \d+)?", r"open\s+point \d",
       r"Figure \d\.\d", r"\b3D\b", r"lap[- ]\d", r"(?m)(?:^|\s)\d+\. ", r"stage \d[a-z]", r"F\(W\)",
       r"one-tag", r"tag 0", r"\b0 wrong", r"tier-1", r"EKF3", r"iSAM2"]
for p in IDS:
    scan = re.sub(p, " ", scan)
for src, toks in TOK.items():
    for t in sorted(toks, key=len, reverse=True):
        scan = re.sub(r"(?<![\d.])" + re.escape(t) + r"(?![\d])", " ", scan)
left = re.findall(r"[+-]?\d[\d,]*(?:\.\d+)?(?:/\d+)?", scan)
for m in re.finditer(r"[+-]?\d[\d,]*(?:\.\d+)?(?:/\d+)?", scan):
    print("  LEFT", repr(scan[max(0, m.start() - 40):m.end() + 15]))
n_left = len(left)
if left:
    fails.append(f"COMPLETENESS: {n_left} unregistered numeric token(s): {sorted(set(left))}")

print(f"quotes checked: {n['quotes']}")
print(f"verdict checks: {n['verdicts']}")
print(f"numbers registered and checked: {n['numbers']} "
      f"({sum(len(v) for v in TOK.values())} tokens + {len(PHRASES)} phrases)")
print(f"unregistered numeric tokens: {n_left}")
print(f"mismatches: {len(fails)}")
for f in fails:
    print("  FAIL", f)
sys.exit(1 if fails else 0)
