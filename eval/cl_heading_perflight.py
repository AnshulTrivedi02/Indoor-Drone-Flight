#!/usr/bin/env python3
"""Per-flight closed-loop with-heading values that numbers.md gives only as ranges (user request 2026-11-11).

Read-only extraction from the STORED score files eval/results/closed_loop_<trial>.json (written by
eval/closed_loop_score.py; nothing is re-scored). Writes docs/thesis/numbers_cl_heading_perflight.md, a thesis-facing
numbers file kept apart from the content-frozen numbers.md.

Sets: EKF3 with heading at full speed (RTF 1.0), Python heading node (cl_b_tex_r1-r3) and C++ heading node
(cl_bcpp_tex_r1-r3); EKF3 with heading at half real time (cl_bcpp_tex_r1-r3_half, C++ node); the original FGO at half
real time, hard-gated (cl_fgo_b_tex_r1-r3_half) and robust (cl_fgo_b_robust_tex_r1-r3_half).

Values: B2 max |cross-track| in cruise (m), B3 heading error p95 and max (deg), B4 max lateral speed (m/s), the B1-B5
pass flags and S2 where scored. Rounding: rd() of eval/figs_thesis.py, loaded through the AST (function only), applied
once: m to 2 dp, deg to 2 dp, m/s to 3 dp (the precision of Table 4.3).

Checks (EXACT, string equality after one rounding):
  - every value in the written file equals rd() of the score file (re-parsed from the file, --check);
  - the half real-time EKF3 row equals Table 4.3's EKF3 row (docs/thesis/tables/T4_closed_loop.md);
  - the per-set min-max of B2 and of B3 p95 / max equals numbers.md's recorded ranges (numbers.md §15, lines 484-485)
    for the sets it lists (EKF3 full C++, EKF3 half, FGO hard, FGO robust).
  - the heading-node build of each set from the trial's own metadata.yaml (impl: cpp; no impl field = Python node,
    the metadata predating the C++ port's commit f12bed2).
Usage: python3 eval/cl_heading_perflight.py [--check]"""
import ast, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "thesis", "numbers_cl_heading_perflight.md")
TRIALS = os.path.expanduser("~/thesis_data/trials")


def _load_rd():
    tree = ast.parse(open(os.path.join(HERE, "figs_thesis.py")).read())
    keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd"]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "eval/figs_thesis.py", "exec"), ns)
    return ns["rd"]


rd = _load_rd()
SETS = [
    ("EKF3, full speed (RTF 1.0), Python heading node", ["cl_b_tex_r1", "cl_b_tex_r2", "cl_b_tex_r3"], "python"),
    ("EKF3, full speed (RTF 1.0), C++ heading node", ["cl_bcpp_tex_r1", "cl_bcpp_tex_r2", "cl_bcpp_tex_r3"], "cpp"),
    ("EKF3, half real time (RTF 0.5), C++ heading node", ["cl_bcpp_tex_r1_half", "cl_bcpp_tex_r2_half", "cl_bcpp_tex_r3_half"], "cpp"),
    ("original FGO, hard-gated, half real time", ["cl_fgo_b_tex_r1_half", "cl_fgo_b_tex_r2_half", "cl_fgo_b_tex_r3_half"], None),
    ("original FGO, robust weighting, half real time", ["cl_fgo_b_robust_tex_r1_half", "cl_fgo_b_robust_tex_r2_half",
                                                        "cl_fgo_b_robust_tex_r3_half"], None),
]
CHK = []


def check(label, got, exp):
    CHK.append((label, got == exp))
    if got != exp:
        print(f"CHECK FAIL {label}: {got!r} != {exp!r}")


def score(t):
    return json.load(open(os.path.join(ROOT, "eval", "results", f"closed_loop_{t}.json")))


def node_impl(t):
    txt = open(os.path.join(TRIALS, t, "metadata.yaml")).read()
    m = re.search(r"^heading_bridge:\n(?:  .*\n)*?  impl: (\w+)", txt, re.M)
    return m.group(1) if m else "python"     # no impl field: metadata written before the C++ port existed (f12bed2)


def row(t):
    B = score(t)["B"]
    passes = {k: B[k]["pass"] for k in ("B1", "B2", "B3", "B4", "B5")}
    s2 = B.get("S2", {}).get("pass") if isinstance(B.get("S2"), dict) else None
    return {"trial": t, "B2": rd(B["B2"]["max_abs_x_cruise_m"], 2), "p95": rd(B["B3"]["p95_deg"], 2),
            "max": rd(B["B3"]["max_deg"], 2), "B4": rd(B["B4"]["max_abs_lat_speed_mps"], 3), "passes": passes, "S2": s2,
            "est": B["B3"].get("estimator", ""), "raw": (B["B2"]["max_abs_x_cruise_m"], B["B3"]["p95_deg"],
                                                         B["B3"]["max_deg"], B["B4"]["max_abs_lat_speed_mps"])}


def build():
    data = []
    for name, trials, impl in SETS:
        rows = [row(t) for t in trials]
        if impl is not None:
            for t in trials:
                check(f"heading node {t}", node_impl(t), impl)
        data.append((name, rows))
    return data


def cross_checks(data):
    # Table 4.3 EKF3 row (half real time): cross-track, p95, max, lateral speed, flights 1 / 2 / 3
    t4 = open(os.path.join(ROOT, "docs", "thesis", "tables", "T4_closed_loop.md")).read()
    m = re.search(r"\| EKF3 \(unmodified\) \|[^|]*\|[^|]*\| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", t4)
    half = dict(data)["EKF3, half real time (RTF 0.5), C++ heading node"]
    for i, key in enumerate(["B2", "p95", "max", "B4"]):
        check(f"T4 EKF3 half {key}", " / ".join(r[key] for r in half), m.group(i + 1).strip())
    # numbers.md §15 ranges (B2; B3 p95/max), order: EKF3 full C++, EKF3 half, UKF full, UKF half, FGO hard, FGO robust
    N = open(os.path.join(ROOT, "docs", "thesis", "numbers.md")).read().splitlines()
    rb2 = next(l for l in N if l.startswith("| With heading, B2 max cross-track (EKF3 full C++"))
    rb3 = next(l for l in N if l.startswith("| With heading, B3 yaw error p95 / max (same order)"))
    b2 = re.findall(r"[\d.]+–[\d.]+", rb2.split("|")[2])
    b3 = re.findall(r"([\d.]+–[\d.]+)/([\d.]+–[\d.]+)", rb3.split("|")[2])
    idx = {"EKF3, full speed (RTF 1.0), C++ heading node": 0, "EKF3, half real time (RTF 0.5), C++ heading node": 1,
           "original FGO, hard-gated, half real time": 4, "original FGO, robust weighting, half real time": 5}
    D = dict(data)
    for name, k in idx.items():
        rows = D[name]
        rng = lambda key, n: f"{rd(min(float(r[key]) for r in rows), n)}–{rd(max(float(r[key]) for r in rows), n)}"
        check(f"numbers.md B2 range, {name}", rng("B2", 2), b2[k])
        check(f"numbers.md B3 p95 range, {name}", rng("p95", 2), b3[k][0])
        check(f"numbers.md B3 max range, {name}", rng("max", 2), b3[k][1])


def render(data):
    L = ["# Closed loop with heading: per-flight values (thesis-facing numbers addendum)", "",
         "Read-only extraction from the stored score files `eval/results/closed_loop_<trial>.json` (written by "
         "`eval/closed_loop_score.py`; nothing re-scored), by `eval/cl_heading_perflight.py`. numbers.md is content-frozen "
         "and gives these sets only as ranges (§15, lines 476-485); this file adds the per-flight values. Rounding: "
         "`rd()` of `eval/figs_thesis.py`, once (m and degrees to 2 dp, m/s to 3 dp). Experiment 1C, textured corridor, "
         "0.5 m/s, 300 s cruise. Every set below is CURRENT as recorded (the B5 window is D28's).", "",
         "**Heading-node build of each EKF3 set**, from each trial's own `metadata.yaml`: `cl_bcpp_tex_r1–r3` and "
         "`cl_bcpp_tex_r1–r3_half` record `impl: cpp` (the C++ heading node); `cl_b_tex_r1–r3` have no `impl` field: "
         "their metadata (2026-09-29 23:52) predates the commit that added the C++ port and the field (`f12bed2`, "
         "2026-09-30 00:18), so they flew the Python heading node, the only one that existed. This confirms D70's "
         "`cl_bcpp_tex_r1..r3_half` as the C++ node.", "",
         "| set | flight | B2 max \\|cross-track\\| in cruise (m) | B3 heading error p95 (°) | B3 heading error max (°) | "
         "B4 max lateral speed (m/s) | B1–B5 | S2 |", "|---|---|---|---|---|---|---|---|"]
    for name, rows in data:
        for i, r in enumerate(rows, 1):
            allp = "all pass" if all(r["passes"].values()) else ", ".join(k for k, v in r["passes"].items() if not v) + " fail"
            s2 = "—" if r["S2"] is None else ("pass" if r["S2"] else "fail")
            L.append(f"| {name} | {i} (`{r['trial']}`) | {r['B2']} | {r['p95']} | {r['max']} | {r['B4']} | {allp} | {s2} |")
    L += ["", "*B3 uses EKF3's yaw for the EKF3 sets and the FGO's current-time yaw for the FGO sets (`--est fgo`). "
          "Bounds: B2 ≤ 6.0 m; B3 p95 ≤ 1.0°, max ≤ 2.0°; B4 ≤ 0.25 m/s. S2 (estimator validity) is scored for the FGO sets "
          "only where the score file carries it.*", "",
          f"*Checks (EXACT): {sum(ok for _, ok in CHK)}/{len(CHK)} — every value against its score file; the half "
          "real-time EKF3 row against Table 4.3; the per-set min–max against numbers.md's recorded ranges; the heading-node "
          "build against each trial's metadata.yaml.*", ""]
    return "\n".join(L)


def main():
    data = build()
    cross_checks(data)
    if "--check" in sys.argv:
        txt = open(OUT, encoding="utf-8").read()
        for name, rows in data:
            for i, r in enumerate(rows, 1):
                check(f"file row {r['trial']}", all(f"| {r[k]} " in txt.split(f"`{r['trial']}`)", 1)[1].split("\n")[0]
                                                    for k in ("B2", "p95", "max", "B4")), True)
    else:
        open(OUT, "w", encoding="utf-8").write(render(data))
        print(f"wrote {os.path.relpath(OUT, ROOT)}")
    n_ok = sum(ok for _, ok in CHK)
    print(f"checks {n_ok}/{len(CHK)}")
    sys.exit(0 if n_ok == len(CHK) else 1)


if __name__ == "__main__":
    main()
