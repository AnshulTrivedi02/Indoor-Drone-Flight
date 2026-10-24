#!/usr/bin/env python3
"""Exact check of docs/thesis/discussion_material.md §1 against docs/thesis/ablation/ablation_numbers.md (read-only).

Every number in the ruled paragraph and its provenance table is re-read from the T2 (retention), T3 (no-heading control) and
P1/P2 rows of ablation_numbers.md, then compared as strings with a single rounding. Exit 0 iff everything passes.
"""
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]
AN = (WS / "docs/thesis/ablation/ablation_numbers.md").read_text(encoding="utf-8")
DM = (WS / "docs/thesis/discussion_material.md").read_text(encoding="utf-8")
fails, n = [], 0


def ok(label, cond):
    global n
    n += 1
    if not cond:
        fails.append(label)
    print(("PASS" if cond else "FAIL") + ": " + label)


def row(table_head, bag):
    sec = AN.split(table_head, 1)[1]
    line = next(l for l in sec.splitlines() if l.startswith(f"| {bag} |"))
    return [c.strip() for c in line.strip("|").split("|")]


def num(s):
    return float(s.replace("−", "-").split(" ")[0])


def delta(cell):
    return float(re.search(r"\(([−\-0-9.]+)\)", cell).group(1).replace("−", "-"))


PARA = ("An exploratory ablation reduced the FGO to a one-keyframe window and varied its iteration count. On line-textured "
        "walls it retained essentially all of its advantage over the UKF (retention 0.97-1.01), so the advantage is not "
        "explained by window length, retained history or iteration count; it lies in the remaining structural differences "
        "between the estimators, which were not separated. Without a heading source, however, the window did affect results: "
        "beyond the noise band on one flight (by about 0.4 m), and by up to 1.3 m on another, within that flight's wide noise "
        "band.")
flat = re.sub(r"\s+", " ", " ".join(l[2:] if l.startswith("> ") else l for l in DM.splitlines() if l.startswith(">")))
ok("ruled paragraph present verbatim", PARA in flat)

# retention 0.97-1.01: R(r3) on the three fwdc bags (T2 column index 5)
T2 = "## T2. Gap retention"
r3 = [row(T2, f"fwdc_tex_r{i}")[5] for i in (1, 2, 3)]
ok(f"R(r3) fwdc = {r3} -> 1.01 / 0.97 / 0.98", r3 == ["1.01", "0.97", "0.98"])
ok("retention range 0.97-1.01 = min-max of R(r3) fwdc", f"{min(r3)}-{max(r3)}" == "0.97-1.01")
ok("P2 row quotes the same R(r3)", "R(r3) on `fwdc`: 1.01, 0.97, 0.98" in AN)

# "one flight (by about 0.4 m)": fwdplainc_tex_r3 control deltas at r1-r3 beyond the 0.223 band; no other bag beyond its band
T3 = "## T3. Control (no heading)"
pr3 = row(T3, "fwdplainc_tex_r3")
d = [delta(c) for c in pr3[2:5]]
band = num(pr3[7])
ok(f"fwdplainc_tex_r3 deltas r1-r3 = {d}", [f"{x:.3f}" for x in d] == ["-0.399", "-0.365", "-0.403"])
ok("each rounds to 0.4 m at 1 dp ('about 0.4 m')", all(f"{abs(x):.1f}" == "0.4" for x in d))
ok("beyond its band 0.223 m", band == 0.223 and all(abs(x) > band for x in d))
beyond = [b for b in ("fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3", "fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3")
          if any(abs(delta(c)) > num(row(T3, b)[7]) for c in row(T3, b)[2:7])]
ok(f"exactly one flight beyond its band at any window rung (r1-r5): {beyond}", beyond == ["fwdplainc_tex_r3"])

# provenance row: fwdc_tex_r2 control moves within its wide band; FGO overtakes the stored UKF at 1 s and 2 s
c2 = row(T3, "fwdc_tex_r2")
d2 = [delta(c) for c in c2[2:7]]
ok(f"fwdc_tex_r2 deltas r1-r5 = {d2}", [f"{x:.3f}" for x in d2] == ["0.304", "0.300", "0.300", "-0.758", "-1.283"])
ok("provenance row quotes them", "+0.304 / +0.300 / +0.300 / −0.758 / −1.283 m" in DM)
big = max(d2, key=abs)
ok(f"'up to 1.3 m' = largest |delta| on fwdc_tex_r2 ({big}) rounded once to 1 dp", f"{abs(big):.1f}" == "1.3" and "1.283 m" in DM)
ok("every fwdc_tex_r2 delta within its band ('within that flight's wide noise band')", all(abs(x) <= num(c2[7]) for x in d2))
ok("fwdc_tex_r2 is the flight with the largest within-band change among the 5 other bags",
   max(((b, max(abs(delta(x)) for x in row(T3, b)[2:7])) for b in ("fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3", "fwdplainc_tex_r1", "fwdplainc_tex_r2")), key=lambda t: t[1])[0] == "fwdc_tex_r2")
ok("old last sentence no longer in the ruled paragraph", "results on one flight (by about 0.4 m)." not in flat)
ok("scope note removed", "Scope note (coordinator" not in DM)
ok("fwdc_tex_r2 band 2.282 m quoted", num(c2[7]) == 2.282 and "2.282 m" in DM)
f0, f4, f5, u = num(c2[1]), num(c2[5].split(" ")[0]), num(c2[6].split(" ")[0]), num(c2[8])
ok("FGO behind UKF at r0, ahead at r4 and r5", f0 > u and f4 < u and f5 < u)
ok("provenance values 2.262 → 1.504 / 0.979 against 1.783", "2.262 → 1.504 / 0.979 m" in DM and "1.783 m" in DM
   and (f"{f0:.3f}", f"{f4:.3f}", f"{f5:.3f}", f"{u:.3f}") == ("2.262", "1.504", "0.979", "1.783"))

print(f"TOTAL {n - len(fails)}/{n}")
sys.exit(1 if fails else 0)
