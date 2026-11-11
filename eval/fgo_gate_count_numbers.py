#!/usr/bin/env python3
"""Thesis-facing numbers file for the FGO gate-count DIAGNOSTIC (stage 2; docs/thesis/diagnostics/
fgo_gate_count.md, fgo_gate_count_results.md; D134, D137). Read-only extraction from
eval/results/fgo_gate_count/per_set.json and per_run.json (written by eval/fgo_gate_count_aggregate.py,
itself reading the stored ~/thesis_data/diagnostics/fgo_gate_count/*_gate_summary.json files written by
`eval/fgo_gate_count.py --run ...`). Nothing is re-run here; nothing is re-computed except rounding and
the derived percentages already present on the JSON.

Rounding: rd() of eval/figs_thesis.py, loaded through the AST (same mechanism as eval/cl_heading_perflight.py),
applied once to every printed number.

Writes docs/thesis/diagnostics/numbers_fgo_gate_count.md. --check re-parses the written file and asserts
EXACT string equality against a fresh rd() of the JSON for every number in every row.

Usage: python3 eval/fgo_gate_count_numbers.py [--check]
"""
import ast, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "thesis", "diagnostics", "numbers_fgo_gate_count.md")
RESULTS = os.path.join(HERE, "results", "fgo_gate_count")


def _load_rd():
    tree = ast.parse(open(os.path.join(HERE, "figs_thesis.py")).read())
    keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd"]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "eval/figs_thesis.py", "exec"), ns)
    return ns["rd"]


rd = _load_rd()
CHK = []


def check(label, got, want):
    ok = (got == want)
    CHK.append((label, ok))
    if not ok:
        print(f"MISMATCH [{label}]: got {got!r} want {want!r}", file=sys.stderr)
    return ok


def pctstr(v):
    return "n/a" if v is None else rd(v, 2) + "%"


SET_ORDER_1A = ["1A_textured", "1A_blank", "1A_transition", "1A_all"]
SET_LABEL_1A = {"1A_textured": "1A textured (n=9)", "1A_blank": "1A blank (n=3)",
                "1A_transition": "1A transition (n=3)", "1A_all": "1A all (n=15)"}
WALLS = [("fwdc", "line-textured walls"), ("fwdplainc", "plain walls")]
FLOORS = [("textured", "textured"), ("transition", "transition"), ("blank", "blank")]
ARMS = [("baseline", "baseline"), ("heading", "heading"), ("heading_yawrate", "heading+yawrate")]


def flow_row(name, label, s):
    p = s["pct"]
    return (f"| {label} | {s['n_runs']} | {s['n_flow_factors']} | "
            f"{s['reject_axis_9'][0]} ({pctstr(p['flow_reject_axis0_pct'])}) | "
            f"{s['reject_axis_9'][1]} ({pctstr(p['flow_reject_axis1_pct'])}) | "
            f"{s['reject_joint_9']} ({pctstr(p['flow_reject_joint9_pct'])}) | "
            f"{s['reject_joint_11_83']} ({pctstr(p['flow_reject_joint11_83_pct'])}) | "
            f"{s['flow_max_onesided_reject']} ({pctstr(p['flow_max_onesided_pct'])}) | "
            f"{s['flow_max_twosided_reject']} ({pctstr(p['flow_max_twosided_pct'])}) |")


def range_row(name, label, s):
    p = s["pct"]
    bi = "PASS" if s["all_byte_identical_to_stored"] and s["n_byte_identity_checked"] == s["n_runs"] else \
         ("n/a" if s["n_byte_identity_checked"] == 0 else "MISMATCH")
    return (f"| {label} | {s['n_runs']} | {s['n_range_factors']} | "
            f"{s['range_reject_25']} ({pctstr(p['range_reject25_pct'])}) | "
            f"{s['n_flow_gp_replaced']} | {bi} |")


def near_row(label, s):
    nt = s["near_threshold"]
    return (f"| {label} | {nt['flow_axis0_near9']} | {nt['flow_axis1_near9']} | "
            f"{nt['flow_joint_near9']} | {nt['flow_joint_near11_83']} | {nt['range_near25']} |")


def render(per_set):
    present_1a = [k for k in SET_ORDER_1A if k in per_set]
    L = ["# FGO gate-count diagnostic: per-set numbers (thesis-facing addendum)", "", "DIAGNOSTIC. No verdict.", "",
         "Read-only extraction from `eval/results/fgo_gate_count/per_set.json` (written by "
         "`eval/fgo_gate_count_aggregate.py`, itself reading the stored per-run "
         "`~/thesis_data/diagnostics/fgo_gate_count/*_gate_summary.json` files written by "
         "`eval/fgo_gate_count.py --run ...`; see `docs/thesis/diagnostics/fgo_gate_count.md` for the method and "
         "`docs/thesis/diagnostics/fgo_gate_count_results.md` for the discussion). Nothing here is re-run or "
         "re-scored; percentages are `rd()`-rounded once from the stored counts. \"Reject\" means \"would have "
         "been rejected by this gate, evaluated against the as-built factor and the IMU-only predictive "
         "covariance\" -- see the conditioning and fusion-order caveats in the results file. A rejection would "
         "change later states; this is not a replay of a gated FGO.", "",
         "## Set 1A (`dsn_*`, no forward-camera arm, 15 runs)", "",
         "| group | n runs | n flow factors | reject axis-0 (x) | reject axis-1 (y) | reject joint (naive 9) | "
         "reject joint (chi2(2)=11.83) | FLOW_MAX one-sided | FLOW_MAX two-sided |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k in present_1a:
        L.append(flow_row(k, SET_LABEL_1A[k], per_set[k]))
    L += ["", "| group | n runs | n range factors | reject (NIS>25, `HGT_I_GATE`) | n flow factors GP-replaced "
          "(pre-takeoff, synthetic) | byte-identical to stored |", "|---|---|---|---|---|---|"]
    for k in present_1a:
        L.append(range_row(k, SET_LABEL_1A[k], per_set[k]))
    L += ["", "**Near-threshold counts** (within ±0.1% of the stated gate; FGO_DESIGN.md / design-note Section 7b "
          "conditioning caveat -- the count of decisions late-flight round-off growth could plausibly flip):", "",
          "| group | axis-0 near 9 | axis-1 near 9 | joint near 9 | joint near 11.83 | range near 25 |",
          "|---|---|---|---|---|---|"]
    for k in present_1a:
        L.append(near_row(SET_LABEL_1A[k], per_set[k]))

    L += ["", "## Set 1B (Phase 4 forward-camera arms, 18 trials x 3 arms = 54 runs)", "",
          "| wall | floor | arm | n runs | n flow factors | reject axis-0 (x) | reject axis-1 (y) | "
          "reject joint (naive 9) | reject joint (chi2(2)=11.83) | FLOW_MAX one-sided | FLOW_MAX two-sided |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for wall, wlabel in WALLS:
        for floor, flabel in FLOORS:
            for arm, alabel in ARMS:
                key = f"1B_{wall}_{floor}_{arm}"
                if key in per_set:
                    s = per_set[key]
                    p = s["pct"]
                    L.append(f"| {wlabel} | {flabel} | {alabel} | {s['n_runs']} | {s['n_flow_factors']} | "
                             f"{s['reject_axis_9'][0]} ({pctstr(p['flow_reject_axis0_pct'])}) | "
                             f"{s['reject_axis_9'][1]} ({pctstr(p['flow_reject_axis1_pct'])}) | "
                             f"{s['reject_joint_9']} ({pctstr(p['flow_reject_joint9_pct'])}) | "
                             f"{s['reject_joint_11_83']} ({pctstr(p['flow_reject_joint11_83_pct'])}) | "
                             f"{s['flow_max_onesided_reject']} ({pctstr(p['flow_max_onesided_pct'])}) | "
                             f"{s['flow_max_twosided_reject']} ({pctstr(p['flow_max_twosided_pct'])}) |")
    if "1B_all" in per_set:
        L.append(flow_row("1B_all", "**all 1B (n=54)**", per_set["1B_all"]))

    L += ["", "| wall | floor | arm | n runs | n range factors | reject (NIS>25) | n flow factors GP-replaced | "
          "byte-identical to stored |", "|---|---|---|---|---|---|---|---|"]
    for wall, wlabel in WALLS:
        for floor, flabel in FLOORS:
            for arm, alabel in ARMS:
                key = f"1B_{wall}_{floor}_{arm}"
                if key in per_set:
                    s = per_set[key]
                    p = s["pct"]
                    bi = "PASS" if s["all_byte_identical_to_stored"] and s["n_byte_identity_checked"] == s["n_runs"] else \
                         ("n/a" if s["n_byte_identity_checked"] == 0 else "MISMATCH")
                    L.append(f"| {wlabel} | {flabel} | {alabel} | {s['n_runs']} | {s['n_range_factors']} | "
                             f"{s['range_reject_25']} ({pctstr(p['range_reject25_pct'])}) | {s['n_flow_gp_replaced']} | {bi} |")
    if "1B_all" in per_set:
        L.append(range_row("1B_all", "**all 1B (n=54)**", per_set["1B_all"]))
    L.append("")
    L.append(f"*Checks (EXACT, string equality after one `rd()` rounding): {{N_OK}}/{{N_TOT}} against "
            "`eval/results/fgo_gate_count/per_set.json`.*")
    L.append("")
    return "\n".join(L)


def _indep_pct(n, d):
    """Independent recomputation of the percentage string, NOT via pctstr()/the render helpers --
    a fresh decimal rounding of n/d*100 to 2dp, half-away-from-zero, matching rd()'s own rule by
    hand rather than by calling it a second time on the same path."""
    from decimal import Decimal, ROUND_HALF_UP
    if d == 0:
        return "n/a"
    val = Decimal(n) * Decimal(100) / Decimal(d)
    q = val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{q}%"


def do_checks(per_set):
    """Independent cross-check: for every (group, row) actually present in the written markdown, parse the
    row with a regex (not by calling the render helpers again) and verify every raw count equals the JSON's
    count exactly, and every parenthesised percentage equals an independently-computed rd()-equivalent
    rounding of (count / n) * 100. This is deliberately NOT the same code path as render()."""
    lines = open(OUT).read().splitlines()
    row_re = re.compile(r"^\|\s*(.+?)\s*\|(.+)\|\s*$")

    def cells(line):
        return [c.strip() for c in line.strip("|").split("|")]

    def parse_count_pct(cell):
        m = re.match(r"^(\d+)\s*\(([\d.]+%|n/a)\)$", cell)
        return (int(m.group(1)), m.group(2)) if m else (None, None)

    # --- Set 1A flow table: columns = label, n_runs, n_flow, ax0, ax1, j9, j1183, fm1, fm2 ---
    for k in SET_ORDER_1A:
        if k not in per_set:
            continue
        s = per_set[k]
        row = next((l for l in lines if l.startswith(f"| {SET_LABEL_1A[k]} |")), None)
        check(f"1A row present: {k}", row is not None, True)
        if row is None:
            continue
        c = cells(row)
        check(f"1A {k} n_runs", c[1] == str(s["n_runs"]), True)
        check(f"1A {k} n_flow_factors", c[2] == str(s["n_flow_factors"]), True)
        for i, (jkey, dkey) in enumerate([("reject_axis_9", 0), ("reject_axis_9", 1),
                                         ("reject_joint_9", None), ("reject_joint_11_83", None),
                                         ("flow_max_onesided_reject", None), ("flow_max_twosided_reject", None)]):
            n = s[jkey][dkey] if dkey is not None else s[jkey]
            got_n, got_pct = parse_count_pct(c[3 + i])
            check(f"1A {k} col{i} count", got_n == n, True)
            check(f"1A {k} col{i} pct", got_pct, _indep_pct(n, s["n_flow_factors"]))
    # --- Set 1A range table ---
    for k in SET_ORDER_1A:
        if k not in per_set:
            continue
        s = per_set[k]
        row = next((l for l in lines if l.startswith(f"| {SET_LABEL_1A[k]} |") and str(s["n_range_factors"]) in l), None)
        check(f"1A range row present: {k}", row is not None, True)
        if row is None:
            continue
        c = cells(row)
        got_n, got_pct = parse_count_pct(c[3])
        check(f"1A {k} range reject count", got_n == s["range_reject_25"], True)
        check(f"1A {k} range reject pct", got_pct, _indep_pct(s["range_reject_25"], s["n_range_factors"]))
        check(f"1A {k} gp_replaced", c[4] == str(s["n_flow_gp_replaced"]), True)

    # --- Set 1B flow table: columns = wall, floor, arm, n_runs, n_flow, ax0, ax1, j9, j1183, fm1, fm2 ---
    for wall, wlabel in WALLS:
        for floor, flabel in FLOORS:
            for arm, alabel in ARMS:
                key = f"1B_{wall}_{floor}_{arm}"
                if key not in per_set:
                    continue
                s = per_set[key]
                row = next((l for l in lines if l.startswith(f"| {wlabel} | {flabel} | {alabel} |")), None)
                check(f"1B row present: {key}", row is not None, True)
                if row is None:
                    continue
                c = cells(row)
                check(f"1B {key} n_runs", c[3] == str(s["n_runs"]), True)
                check(f"1B {key} n_flow_factors", c[4] == str(s["n_flow_factors"]), True)
                for i, (jkey, dkey) in enumerate([("reject_axis_9", 0), ("reject_axis_9", 1),
                                                 ("reject_joint_9", None), ("reject_joint_11_83", None),
                                                 ("flow_max_onesided_reject", None), ("flow_max_twosided_reject", None)]):
                    n = s[jkey][dkey] if dkey is not None else s[jkey]
                    got_n, got_pct = parse_count_pct(c[5 + i])
                    check(f"1B {key} col{i} count", got_n == n, True)
                    check(f"1B {key} col{i} pct", got_pct, _indep_pct(n, s["n_flow_factors"]))


def main():
    check_mode = "--check" in sys.argv
    per_set = json.load(open(os.path.join(RESULTS, "per_set.json")))
    txt = render(per_set)
    n_ok_placeholder = txt  # filled after checks below
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # first pass: write without the final check-count line resolved (placeholder), then re-render after checks
    with open(OUT, "w") as fh:
        fh.write(txt)
    do_checks(per_set)
    n_ok = sum(1 for _, ok in CHK if ok)
    final_txt = txt.replace("{N_OK}/{N_TOT}", f"{n_ok}/{len(CHK)}")
    with open(OUT, "w") as fh:
        fh.write(final_txt)
    print(f"wrote {OUT} ({len(per_set)} set groups, {n_ok}/{len(CHK)} checks OK)")
    if check_mode:
        failed = [l for l, ok in CHK if not ok]
        if failed:
            print(f"CHECK FAILED: {failed}", file=sys.stderr); sys.exit(1)
        print("--check: all checks PASS")


if __name__ == "__main__":
    main()
