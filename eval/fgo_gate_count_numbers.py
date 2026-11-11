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
         "**dagger (floor-level, not per-row): transition and blank are, in every one of the 60 runs checked, in "
         "`numbers.md`'s own documented \"Diverging (unaided) FGO results\" category (km-scale ATE once flow "
         "aiding is lost) -- only textured stays bounded.** Low rejection counts on transition/blank reflect a "
         "hugely inflated `P_pred` at least as much as flow-factor quality; see the results file Section 6a "
         "before reading those rows as \"the sensor is fine on this floor\". `1B all achievable` sums flow/range "
         "factors across baseline/heading/heading_yawrate for the SAME trial, which share the same underlying "
         "flow/range measurements (Section 4 of the results file: the factor count is identical per arm) -- it "
         "is a sum of three passes over the same measurements under three different trajectories/covariances, "
         "not a count of 3x as many distinct factors.", "",
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

    L += ["", "## Set 1B (Phase 4 forward-camera arms, 18 trials x up to 3 arms = 54 registered, 45 achievable)", "",
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
        L.append(flow_row("1B_all", "**all 1B achievable (n=45)**", per_set["1B_all"]))

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
        L.append(range_row("1B_all", "**all 1B achievable (n=45)**", per_set["1B_all"]))

    L += ["", "**Set 1B near-threshold counts** (within +/-0.1% of the stated gate; see the Section 6 "
          "conditioning caveat in the results file):", "",
          "| wall | floor | arm | axis-0 near 9 | axis-1 near 9 | joint near 9 | joint near 11.83 | range near 25 |",
          "|---|---|---|---|---|---|---|---|"]
    for wall, wlabel in WALLS:
        for floor, flabel in FLOORS:
            for arm, alabel in ARMS:
                key = f"1B_{wall}_{floor}_{arm}"
                if key in per_set:
                    s = per_set[key]; nt = s["near_threshold"]
                    L.append(f"| {wlabel} | {flabel} | {alabel} | {nt['flow_axis0_near9']} | "
                             f"{nt['flow_axis1_near9']} | {nt['flow_joint_near9']} | "
                             f"{nt['flow_joint_near11_83']} | {nt['range_near25']} |")
    if "1B_all" in per_set:
        L.append(near_row("**all 1B achievable (n=45)**", per_set["1B_all"]))

    L.append("")
    L.append(f"*Checks (EXACT, string equality after one `rd()` rounding, both against `rd()` of the JSON value "
            "directly and against an independently-recomputed decimal rounding, per the brief): {{N_OK}}/{{N_TOT}} "
            "against `eval/results/fgo_gate_count/per_set.json`.*")
    L.append("")
    L.append("## Appendix: every registered run (set 1A + set 1B, 69 combinations, 60 ran / 9 N/A)")
    L.append("")
    L.append("Per-RUN (not aggregated) counts, one row per registered trial x arm combination. The 9 "
            "`fwdplainc_*` x `heading_yawrate` combinations are N/A (do not exist in the production code; "
            "`docs/thesis/diagnostics/fgo_gate_count_results.md` Section 3) and carry no counts.")
    L.append("")
    L.append("| trial | arm | n flow factors | reject axis-0 | reject axis-1 | reject joint-9 | "
            "reject joint-11.83 | FLOW_MAX 1-sided | FLOW_MAX 2-sided | n range factors | range reject-25 | "
            "GP-replaced | byte-identical |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    return "\n".join(L), L


def per_run_rows(runs):
    out = []
    DSN = ["dsn_blank_r1", "dsn_blank_r2", "dsn_blank_r3", "dsn_tex_r1", "dsn_tex_r2", "dsn_tex_r3",
           "dsn_tex_r4", "dsn_tex_r5", "dsn_tex_r6", "dsn_tex_r7", "dsn_tex_r8", "dsn_tex_r9",
           "dsn_trans_r1", "dsn_trans_r2", "dsn_trans_r3"]
    FLOOR_TAG = {"textured": "tex", "transition": "trans", "blank": "blank"}   # trial-name tag, not the
    # per_set.json floor key (per_set.json uses "textured"/"transition"/"blank"; trial directory names use
    # the abbreviated "tex"/"trans"/"blank")
    F4 = []
    for wall, _ in WALLS:
        for floor, _ in FLOORS:
            for rep in (1, 2, 3):
                F4.append(f"{wall}_{FLOOR_TAG[floor]}_r{rep}")
    by_key = {(r["trial"], r.get("arm")): r for r in runs}
    rows = []
    for t in DSN:
        rows.append((t, None))
    for t in F4:
        for arm, _ in ARMS:
            rows.append((t, arm))
    lines = []
    for trial, arm in rows:
        r = by_key.get((trial, arm))
        armlabel = arm or "-"
        if r is None:
            lines.append(f"| {trial} | {armlabel} | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |")
            continue
        p = r["_pct"]; f = r["flow"]; rg = r["range"]
        bi = "PASS" if r.get("instrumented_vs_stored_byte_identical") is True else str(r.get("instrumented_vs_stored_byte_identical"))
        lines.append(
            f"| {trial} | {armlabel} | {r['n_flow_factors']} | "
            f"{f['reject_axis_9'][0]} ({pctstr(p['flow_reject_axis0_pct'])}) | "
            f"{f['reject_axis_9'][1]} ({pctstr(p['flow_reject_axis1_pct'])}) | "
            f"{f['reject_joint_9']} ({pctstr(p['flow_reject_joint9_pct'])}) | "
            f"{f['reject_joint_11_83']} ({pctstr(p['flow_reject_joint11_83_pct'])}) | "
            f"{f['flow_max_onesided_reject']} ({pctstr(p['flow_max_onesided_pct'])}) | "
            f"{f['flow_max_twosided_reject']} ({pctstr(p['flow_max_twosided_pct'])}) | "
            f"{r['n_range_factors']} | {rg['reject_25']} ({pctstr(p['range_reject25_pct'])}) | "
            f"{r.get('n_flow_gp_replaced')} | {bi} |")
    return lines


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


PCT_KEY = {("reject_axis_9", 0): "flow_reject_axis0_pct", ("reject_axis_9", 1): "flow_reject_axis1_pct",
           ("reject_joint_9", None): "flow_reject_joint9_pct", ("reject_joint_11_83", None): "flow_reject_joint11_83_pct",
           ("flow_max_onesided_reject", None): "flow_max_onesided_pct", ("flow_max_twosided_reject", None): "flow_max_twosided_pct",
           ("range_reject_25", None): "range_reject25_pct"}


def _check_pct_cell(label, got_pct, stored_pct_value, n, d):
    """Checks a parenthesised percentage TWO ways: (1) directly against rd() of the JSON's OWN STORED
    percentage field (the brief's literal ask: 'compare against rd() of the JSON value'); (2) against a
    fresh, from-scratch Decimal rounding of (n/d)*100 that reads neither rd() nor the stored field at all
    (an independent recompute, catching a bug in either the stored field or in rd() itself, which (1)
    alone cannot catch)."""
    check(f"{label} (vs rd(json pct field))", got_pct, pctstr(stored_pct_value))
    check(f"{label} (vs independent recompute)", got_pct, _indep_pct(n, d))


def do_checks(per_set, runs):
    """Independent cross-check: for every (group, row) actually present in the written markdown, parse the
    row with a regex (not by calling the render helpers again) and verify every raw count equals the JSON's
    count exactly, and every parenthesised percentage equals BOTH rd() of the JSON's own percentage AND an
    independently-computed decimal rounding of (count / n) * 100. This is deliberately NOT the same code
    path as render()."""
    lines = open(OUT).read().splitlines()

    def cells(line):
        return [c.strip() for c in line.strip("|").split("|")]

    def parse_count_pct(cell):
        m = re.match(r"^(\d+)\s*\(([\d.]+%|n/a)\)$", cell)
        return (int(m.group(1)), m.group(2)) if m else (None, None)

    def flow_cols(label_prefix, row, s, col0):
        c = cells(row)
        for i, (jkey, dkey) in enumerate([("reject_axis_9", 0), ("reject_axis_9", 1),
                                          ("reject_joint_9", None), ("reject_joint_11_83", None),
                                          ("flow_max_onesided_reject", None), ("flow_max_twosided_reject", None)]):
            n = s[jkey][dkey] if dkey is not None else s[jkey]
            got_n, got_pct = parse_count_pct(c[col0 + i])
            check(f"{label_prefix} col{i} count", got_n == n, True)
            _check_pct_cell(f"{label_prefix} col{i} pct", got_pct, s["pct"][PCT_KEY[(jkey, dkey)]], n, s["n_flow_factors"])

    def range_cols(label_prefix, row, s, col0):
        c = cells(row)
        got_n, got_pct = parse_count_pct(c[col0])
        check(f"{label_prefix} range reject count", got_n == s["range_reject_25"], True)
        _check_pct_cell(f"{label_prefix} range reject pct", got_pct, s["pct"]["range_reject25_pct"],
                       s["range_reject_25"], s["n_range_factors"])
        check(f"{label_prefix} gp_replaced", c[col0 + 1] == str(s["n_flow_gp_replaced"]), True)

    def near_cols(label_prefix, row, s):
        c = cells(row)
        nt = s["near_threshold"]
        want = [nt["flow_axis0_near9"], nt["flow_axis1_near9"], nt["flow_joint_near9"],
               nt["flow_joint_near11_83"], nt["range_near25"]]
        got = c[-5:]
        check(f"{label_prefix} near-threshold", got == [str(w) for w in want], True)

    # --- Set 1A: flow, range, near-threshold tables ---
    for k in SET_ORDER_1A:
        if k not in per_set:
            continue
        s = per_set[k]
        flow_row_line = next((l for l in lines if l.startswith(f"| {SET_LABEL_1A[k]} |")), None)
        check(f"1A row present: {k}", flow_row_line is not None, True)
        if flow_row_line is not None:
            check(f"1A {k} n_runs", cells(flow_row_line)[1] == str(s["n_runs"]), True)
            check(f"1A {k} n_flow_factors", cells(flow_row_line)[2] == str(s["n_flow_factors"]), True)
            flow_cols(f"1A {k}", flow_row_line, s, 3)
        range_row_line = next((l for l in lines if l.startswith(f"| {SET_LABEL_1A[k]} |") and str(s["n_range_factors"]) in l), None)
        check(f"1A range row present: {k}", range_row_line is not None, True)
        if range_row_line is not None:
            range_cols(f"1A {k}", range_row_line, s, 3)
        near_row_line = next((l for l in lines if l.startswith(f"| {SET_LABEL_1A[k]} |")
                              and len(cells(l)) == 6 and all(x.isdigit() for x in cells(l)[1:])), None)
        check(f"1A near row present: {k}", near_row_line is not None, True)
        if near_row_line is not None:
            near_cols(f"1A {k}", near_row_line, s)

    # --- Set 1B: flow, range, near-threshold tables, including 1B_all ---
    for wall, wlabel in WALLS:
        for floor, flabel in FLOORS:
            for arm, alabel in ARMS:
                key = f"1B_{wall}_{floor}_{arm}"
                if key not in per_set:
                    continue
                s = per_set[key]
                flow_row_line = next((l for l in lines if l.startswith(f"| {wlabel} | {flabel} | {alabel} |")), None)
                check(f"1B row present: {key}", flow_row_line is not None, True)
                if flow_row_line is not None:
                    c = cells(flow_row_line)
                    check(f"1B {key} n_runs", c[3] == str(s["n_runs"]), True)
                    check(f"1B {key} n_flow_factors", c[4] == str(s["n_flow_factors"]), True)
                    flow_cols(f"1B {key}", flow_row_line, s, 5)
                range_row_line = next((l for l in lines if l.startswith(f"| {wlabel} | {flabel} | {alabel} |")
                                       and str(s["n_range_factors"]) in l), None)
                check(f"1B range row present: {key}", range_row_line is not None, True)
                if range_row_line is not None:
                    range_cols(f"1B {key}", range_row_line, s, 5)
                near_row_line = next((l for l in lines if l.startswith(f"| {wlabel} | {flabel} | {alabel} |")
                                      and len(cells(l)) == 8 and all(x.isdigit() for x in cells(l)[3:])), None)
                check(f"1B near row present: {key}", near_row_line is not None, True)
                if near_row_line is not None:
                    near_cols(f"1B {key}", near_row_line, s)
    if "1B_all" in per_set:
        s = per_set["1B_all"]
        flow_row_line = next((l for l in lines if l.startswith("| **all 1B achievable (n=45)**") and str(s["n_flow_factors"]) in l), None)
        check("1B_all flow row present", flow_row_line is not None, True)
        if flow_row_line is not None:
            flow_cols("1B_all", flow_row_line, s, 3)
        range_row_line = next((l for l in lines if l.startswith("| **all 1B achievable (n=45)**") and str(s["n_range_factors"]) in l), None)
        check("1B_all range row present", range_row_line is not None, True)
        if range_row_line is not None:
            range_cols("1B_all", range_row_line, s, 3)
        near_row_line = next((l for l in lines if l.startswith("| **all 1B achievable (n=45)**")
                              and len(cells(l)) == 6 and all(x.isdigit() for x in cells(l)[1:])), None)
        check("1B_all near row present", near_row_line is not None, True)
        if near_row_line is not None:
            near_cols("1B_all", near_row_line, s)

    # --- Appendix: per-run table, every one of the 69 registered combinations ---
    na_rows = [l for l in lines if "| N/A | N/A | N/A |" in l]
    check("appendix: exactly 9 N/A rows", len(na_rows), 9)
    for r in runs:
        trial = r["trial"]; arm = r.get("arm")
        armlabel = arm or "-"
        row = next((l for l in lines if l.startswith(f"| {trial} | {armlabel} |")), None)
        check(f"appendix row present: {trial}/{armlabel}", row is not None, True)
        if row is None:
            continue
        c = cells(row)
        check(f"appendix {trial}/{armlabel} n_flow", c[2] == str(r["n_flow_factors"]), True)
        check(f"appendix {trial}/{armlabel} n_range", c[9] == str(r["n_range_factors"]), True)
        bi_want = "PASS" if r.get("instrumented_vs_stored_byte_identical") is True else str(r.get("instrumented_vs_stored_byte_identical"))
        check(f"appendix {trial}/{armlabel} byte-identical", c[12] == bi_want, True)
        # per-run reject/pct columns, reusing the same flow_cols/range_cols helpers used for the
        # per-set tables (the appendix row's column layout matches: n_flow at 2, ax0 at 3, ..., fm2 at
        # 8, n_range at 9, range-reject at 10, gp-replaced at 11). flow_cols/range_cols expect the
        # per-SET object's shape (top-level reject_* keys, a "pct" dict); per_run.json's records are
        # shaped differently (reject_* nested under "flow"/"range", the pct dict is "_pct"), so adapt.
        s_shaped = {
            "reject_axis_9": r["flow"]["reject_axis_9"], "reject_joint_9": r["flow"]["reject_joint_9"],
            "reject_joint_11_83": r["flow"]["reject_joint_11_83"],
            "flow_max_onesided_reject": r["flow"]["flow_max_onesided_reject"],
            "flow_max_twosided_reject": r["flow"]["flow_max_twosided_reject"],
            "range_reject_25": r["range"]["reject_25"], "n_flow_factors": r["n_flow_factors"],
            "n_range_factors": r["n_range_factors"], "n_flow_gp_replaced": r["n_flow_gp_replaced"],
            "pct": r["_pct"],
        }
        flow_cols(f"appendix {trial}/{armlabel}", row, s_shaped, 3)
        range_cols(f"appendix {trial}/{armlabel}", row, s_shaped, 10)


def main():
    check_mode = "--check" in sys.argv
    per_set = json.load(open(os.path.join(RESULTS, "per_set.json")))
    runs = json.load(open(os.path.join(RESULTS, "per_run.json")))
    _, L = render(per_set)
    L = L + per_run_rows(runs) + [""]
    txt = "\n".join(L)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # first pass: write without the final check-count line resolved (placeholder), then re-render after checks
    with open(OUT, "w") as fh:
        fh.write(txt)
    do_checks(per_set, runs)
    n_ok = sum(1 for _, ok in CHK if ok)
    final_txt = txt.replace("{N_OK}/{N_TOT}", f"{n_ok}/{len(CHK)}")
    with open(OUT, "w") as fh:
        fh.write(final_txt)
    print(f"wrote {OUT} ({len(per_set)} set groups, {len(runs)} runs, {n_ok}/{len(CHK)} checks OK)")
    if check_mode:
        failed = [l for l, ok in CHK if not ok]
        if failed:
            print(f"CHECK FAILED: {failed}", file=sys.stderr); sys.exit(1)
        print("--check: all checks PASS")


if __name__ == "__main__":
    main()
