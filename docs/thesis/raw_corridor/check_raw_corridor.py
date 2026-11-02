#!/usr/bin/env python3
"""Exact cross-check for docs/thesis/raw_corridor/raw_corridor_numbers.md against
eval/results/raw_corridor_errors.json and the original registered-result JSONs (rerun_dsn_evo.json,
dsn_extra_evo.json, phase4_fwdc_arms.json, phase4_fwdplainc_arms.json). stdlib + json only (ast, hashlib,
json, os, re, sys, decimal — no third-party imports), per the brief.

Stage 1b (D111): Stage 1's per-cell frame-check gate is replaced by per-estimator frame validation. This
checker independently RECOMPUTES that per-estimator validation from each cell's own
`strict_frame_check_info` in the json (never trusting the json's own `estimator_validation` block without
reproducing it), and checks the md's header states it correctly.

Checks, per data row of raw_corridor_numbers.md:
  1. the printed aligned value (evo -a cruise) equals rd(cell.stored_ate_a_cruise, 2) from the json;
  2. cell.stored_ate_a_cruise itself equals the value at the ORIGINAL source file + key path (re-derived
     independently from the cell's dataset/trial/estimator/arm, not from the free-text "source" string);
  3. where a numbers.md line number is cited, that numbers.md line contains the printed aligned value
     string;
  4. the printed early-heading-offset column equals rd(cell.strict_frame_check_info.heading_diff_deg, 1);
  5. if the row is a STOP, the json has no "raw" entry for that cell and either its gate failed or its
     estimator failed D111 validation; if the row is not a STOP, the four printed raw values equal
     rd(json value, 2) exactly, and the cell's estimator is independently recomputed as VALIDATED.

Independent per-estimator validation check: for each of EKF3/UKF/FGO, recompute from every one of that
estimator's cells' `strict_frame_check_info` (i) origin_ok count (o_est < orig_tol_m and o_gt < orig_tol_m)
and (ii) strict ok count (fc["ok"]), and require both the json's own `estimator_validation` block AND the
md's printed header line to match the independent recomputation exactly.

Exit 0 iff every check across every row passes.
"""
import ast, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RES = os.path.join(ROOT, "eval", "results")
MD_PATH = os.path.join(HERE, "raw_corridor_numbers.md")
JSON_PATH = os.path.join(RES, "raw_corridor_errors.json")
NUMBERS_MD = os.path.join(ROOT, "docs", "thesis", "numbers.md")

# ------------------------------------------------------------------------------------- rd(), parsed (not hand-copied)
FT = os.path.join(ROOT, "eval", "figs_thesis.py")
_src = open(FT).read()
_tree = ast.parse(_src)
_rd_node = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd")
_rd_src = ast.get_source_segment(_src, _rd_node)
_ns = {}
exec(compile(ast.Module(body=[_rd_node], type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
RD_SHA = hashlib.sha256(_rd_src.encode()).hexdigest()

DP = 2
HDP = 1
ORIG_TOL_M = 0.05

n_ok = n_fail = 0


def check(label, ok, extra=""):
    global n_ok, n_fail
    if ok:
        n_ok += 1
    else:
        n_fail += 1
        print(f"FAIL: {label} {extra}")
    return ok


# ------------------------------------------------------------------------------------- re-derive each cell's ORIGINAL source
_JSON_CACHE = {}


def _load(name):
    if name not in _JSON_CACHE:
        _JSON_CACHE[name] = json.load(open(os.path.join(RES, name)))
    return _JSON_CACHE[name]


def original_stored_value(cell):
    """Re-derive the (file, value) the registered ate_a_cruise came from, independently of raw_corridor_errors.json,
    by the SAME branching eval/raw_corridor_errors.py's dsn_cells()/phase4_cells() used."""
    dataset, trial, est, arm = cell["dataset"], cell["trial"], cell["estimator"], cell["arm"]
    if dataset in ("dsn_tex", "dsn_blank", "dsn_trans"):
        for fname in ("rerun_dsn_evo.json", "dsn_extra_evo.json"):
            d = _load(fname)
            if trial in d["trials"] and est in d["trials"][trial]["est"]:
                return fname, d["trials"][trial]["est"][est]["ate_a_cruise"]["+0.00"]
        return None, None
    arms_file = {"fwdc": "phase4_fwdc_arms.json", "fwdplainc": "phase4_fwdplainc_arms.json"}[dataset]
    d = _load(arms_file)
    key = "EKF3" if est == "EKF3" else f"{est}_{arm}"
    kd = d[trial][key]
    v = kd["ate_a_cruise"]["+0.00"] if "ate_a_cruise" in kd else kd["evo"]["ate_a_cruise"]["+0.00"]
    return arms_file, v


# ------------------------------------------------------------------------------------- numbers.md citation lookup
# (duplicated, independently, from eval/gen_raw_corridor_numbers.py — positional rank comparison, not substring,
# so that e.g. a line with repeated values like "0.06 / 0.06 / 0.06" cannot pass a weak substring check)
NUM_LINES = open(NUMBERS_MD).read().split("\n")
_sec6_start = next(i for i, l in enumerate(NUM_LINES) if l.startswith("## 6. Baseline results — RESTATED"))
_sec7_start = next(i for i in range(_sec6_start + 1, len(NUM_LINES)) if NUM_LINES[i].startswith("## 7."))
CURRENT = NUM_LINES[_sec6_start:_sec7_start]
LABEL_MAP = {
    "EKF3": ("dsn_tex", "EKF3", "baseline"), "FGO (0.25 s)": ("dsn_tex", "FGO", "baseline"),
    "UKF": ("dsn_tex", "UKF", "baseline"),
    "`fwdc` textured EKF3": ("fwdc", "EKF3", "baseline"), "`fwdc` textured FGO": ("fwdc", "FGO", "baseline"),
    "`fwdc` textured UKF": ("fwdc", "UKF", "baseline"),
    "`fwdplainc` textured EKF3": ("fwdplainc", "EKF3", "baseline"),
    "`fwdplainc` textured FGO": ("fwdplainc", "FGO", "baseline"),
    "`fwdplainc` textured UKF": ("fwdplainc", "UKF", "baseline"),
    "`fwdc` UKF +heading": ("fwdc", "UKF", "heading"), "`fwdc` FGO +heading": ("fwdc", "FGO", "heading"),
    "`fwdplainc` UKF +heading": ("fwdplainc", "UKF", "heading"),
    "`fwdplainc` FGO +heading": ("fwdplainc", "FGO", "heading"),
}
CITE = {}
PAT = re.compile(r"^\|\s*(.*?)\s*r1\s*/\s*r2\s*/\s*r3\s*\|\s*([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)")
for i, raw_line in enumerate(CURRENT):
    m = PAT.match(raw_line.replace("**", ""))
    if not m or m.group(1) not in LABEL_MAP:
        continue
    dataset, est, arm = LABEL_MAP[m.group(1)]
    abs_line = _sec6_start + i + 1
    for rank in range(3):
        CITE[(dataset, est, arm, rank)] = (abs_line, m.group(2 + rank))


def numbers_citation(dataset, est, arm, trial):
    m = re.search(r"_r(\d+)$", trial)
    if not m:
        return None
    rank = int(m.group(1)) - 1
    if rank not in (0, 1, 2) or (dataset in ("fwdc", "fwdplainc") and "_tex_" not in trial):
        return None
    return CITE.get((dataset, est, arm, rank))


# ------------------------------------------------------------------------------------- independent source_consistency recompute
def recompute_source_consistency():
    out = {}
    for dataset in ("fwdc", "fwdplainc"):
        rerun = _load(f"rerun_{dataset}_evo.json")["trials"]
        arms = _load(f"phase4_{dataset}_arms.json")
        evo2 = _load(f"phase4_{dataset}_evo.json")["trials"]
        n_checked = n_mismatch = 0
        for trial, t in arms.items():
            if not (t["window_s"] == rerun[trial]["window_s"] == evo2[trial]["window_s"]):
                n_mismatch += 1
            for key, kd in t.items():
                if key == "window_s" or (key != "EKF3" and not key.endswith("_baseline")):
                    continue
                est = "EKF3" if key == "EKF3" else key.split("_", 1)[0]
                va = kd["ate_a_cruise"]["+0.00"] if "ate_a_cruise" in kd else kd["evo"]["ate_a_cruise"]["+0.00"]
                vr = rerun[trial]["est"][est]["ate_a_cruise"]["+0.00"]
                ve2 = evo2[trial]["est"][key]
                ve = ve2["ate_a_cruise"]["+0.00"] if "ate_a_cruise" in ve2 else ve2["evo"]["ate_a_cruise"]["+0.00"]
                n_checked += 1
                if not (va == vr == ve):
                    n_mismatch += 1
        out[dataset] = {"n_checked": n_checked, "n_mismatch": n_mismatch}
    return out


# ------------------------------------------------------------------------------------- independent per-estimator D111 validation recompute
def recompute_estimator_validation(cells):
    """Reproduce eval/raw_corridor_errors.py's validate_estimator(), independently, straight from each
    cell's strict_frame_check_info — never from the json's own precomputed estimator_validation block."""
    by_family = {}
    for c in cells:
        by_family.setdefault(c["estimator"], []).append(c)
    out = {}
    for family in ("EKF3", "UKF", "FGO"):
        infos = [c["strict_frame_check_info"] for c in by_family.get(family, [])
                 if "strict_frame_check_info" in c]
        origin_total = len(infos)
        origin_ok = sum(1 for fc in infos
                         if fc.get("o_est", float("inf")) < ORIG_TOL_M and fc.get("o_gt", float("inf")) < ORIG_TOL_M)
        strict_ok = sum(1 for fc in infos if fc.get("ok"))
        validated = origin_total > 0 and origin_ok == origin_total and strict_ok > 0
        out[family] = {"origin_ok": origin_ok, "origin_total": origin_total, "origin_all_ok": origin_ok == origin_total,
                        "strict_ok": strict_ok, "strict_total": origin_total, "strict_any_ok": strict_ok > 0,
                        "validated": bool(validated)}
    return out


# ------------------------------------------------------------------------------------- load json + markdown
J = json.load(open(JSON_PATH))
CELLS = {(c["trial"], c["estimator"], c["arm"]): c for c in J["cells"]}
check("rd() SHA matches the json's recorded rd_sha256", RD_SHA == J["rd_sha256"], f"{RD_SHA} vs {J['rd_sha256']}")

sc_recomputed = recompute_source_consistency()
for dataset, v in sc_recomputed.items():
    jv = J["source_consistency"][dataset]
    check(f"source_consistency[{dataset}] independently recomputed matches json",
          v["n_checked"] == jv["n_checked"] and v["n_mismatch"] == jv["n_mismatch"], f"{v} vs {jv}")
check("index_drift_reproduction: 3/3 OK in json",
      sum(1 for v in J["index_drift_reproduction"].values() if v.get("ok")) == 3)

# D111: independently recompute the per-estimator validation and require it to match the json's own block
ev_recomputed = recompute_estimator_validation(J["cells"])
for family, rv in ev_recomputed.items():
    jv = J["estimator_validation"][family]
    check(f"estimator_validation[{family}] independently recomputed matches json", rv == jv, f"{rv} vs {jv}")
n_raw_json = sum(1 for c in J["cells"] if "raw" in c)
check("json n_raw_published matches actual count of cells with a raw entry",
      n_raw_json == J["n_raw_published"], f"{n_raw_json} vs {J['n_raw_published']}")
# cross-check: a cell has raw iff its gate passed AND its estimator validated (D111's exact rule)
for c in J["cells"]:
    gate_ok = c.get("gate", {}).get("ok", False)
    est_validated = ev_recomputed[c["estimator"]]["validated"]
    should_have_raw = gate_ok and est_validated
    check(f"{c['trial']}/{c['estimator']}/{c['arm']} has raw iff (gate_ok and estimator validated)",
          ("raw" in c) == should_have_raw,
          f"gate_ok={gate_ok} validated={est_validated} has_raw={'raw' in c}")

md_text = open(MD_PATH).read()
md_lines = md_text.split("\n")
check("header states n_cells", str(J["n_cells"]) in md_text)
check("header states n_gate_ok/n_cells", f"{J['n_gate_ok']}/{J['n_cells']}" in md_text)
check("header states n_raw_published/n_cells", f"{J['n_raw_published']}/{J['n_cells']}" in md_text)
check("header states n_withheld_by_estimator_validation",
      f"({J['n_withheld_by_estimator_validation']} withheld by estimator-level validation failure)" in md_text)
check("header states orig_tol_m as a strict-check tolerance phrase",
      f"< {J['orig_tol_m']} m (both estimate and truth) AND" in md_text)
check("header states head_tol_deg as a strict-check tolerance phrase",
      f"within {J['head_tol_deg']}° of truth" in md_text)
# D111 per-estimator lines are rebuilt EXACTLY (not substring-matched) and required to be a full line of the
# md, so a swapped/garbled count for one family cannot pass just because its numbers appear somewhere else.
for family in ("EKF3", "UKF", "FGO"):
    ev = J["estimator_validation"][family]
    expected_line = (f"**{family}**: origin OK {ev['origin_ok']}/{ev['origin_total']} "
                      f"({'all cells' if ev['origin_all_ok'] else 'NOT all cells'} < {J['orig_tol_m']} m); "
                      f"strict (origin + heading) OK {ev['strict_ok']}/{ev['strict_total']} "
                      f"({'>=1 cell' if ev['strict_any_ok'] else 'no cell'} passed) -> "
                      f"**{'VALIDATED' if ev['validated'] else 'NOT VALIDATED'}**")
    check(f"header has the exact {family} per-estimator validation line", expected_line in md_lines,
          expected_line)

ARM_LABEL_REV = {"": "baseline", "+heading": "heading", "+heading+yaw rate": "heading_yawrate"}

row_re = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$")
n_rows = 0
seen_keys = set()
for line in md_lines:
    m = row_re.match(line)
    if not m or m.group(1) == "flight":
        continue
    trial, est_arm, aligned_cell, c_head, c_rms, c_end, c_rmsh, c_endh = m.groups()
    est_arm_clean = re.sub(r"\s*\[\w+\]\s*$", "", est_arm)   # strip footnote markers like " [a]"
    toks = est_arm_clean.split(" ", 1)
    est = toks[0]
    arm_label = toks[1] if len(toks) > 1 else ""
    arm = ARM_LABEL_REV.get(arm_label)
    if arm is None:
        check(f"row parses (unknown arm label) {trial}/{est_arm}", False)
        continue
    n_rows += 1
    key = (trial, est, arm)
    if key not in CELLS:
        check(f"row has a matching json cell {trial}/{est}/{arm}", False)
        continue
    seen_keys.add(key)
    cell = CELLS[key]
    dataset = cell["dataset"]

    # 1 + 2: aligned value
    am = re.match(r"^([-\d.]+)\s*\(", aligned_cell)
    check(f"{trial}/{est}/{arm} aligned cell has a leading number", am is not None, aligned_cell)
    if am:
        printed = am.group(1)
        check(f"{trial}/{est}/{arm} aligned == rd(json stored_ate_a_cruise, {DP})",
              printed == rd(cell["stored_ate_a_cruise"], DP),
              f"printed={printed} rd={rd(cell['stored_ate_a_cruise'], DP)}")
        src_file, src_val = original_stored_value(cell)
        check(f"{trial}/{est}/{arm} json stored_ate_a_cruise == original source ({src_file})",
              src_val is not None and cell["stored_ate_a_cruise"] == src_val,
              f"json={cell['stored_ate_a_cruise']} source={src_val}")
        if "extra_sources" in cell:
            for extra in cell["extra_sources"]:
                check(f"{trial}/{est}/{arm} extra source cited: {extra}", f"json:{extra}" in aligned_cell)

    # 3: numbers.md citation — POSITIONAL (rank-exact), not substring
    cite = numbers_citation(dataset, est, arm, trial)
    mline = re.search(r"numbers\.md:(\d+)", aligned_cell)
    if cite:
        check(f"{trial}/{est}/{arm} numbers.md citation present and line matches", mline is not None and
              int(mline.group(1)) == cite[0], f"mline={mline} expected_line={cite[0]}")
        check(f"{trial}/{est}/{arm} printed aligned value == numbers.md's own (positional) value",
              am is not None and am.group(1) == cite[1], f"printed={am.group(1) if am else None} md={cite[1]}")
    else:
        check(f"{trial}/{est}/{arm} no numbers.md citation expected and none printed", mline is None,
              f"unexpected citation {mline}")

    # 4: early heading offset column — DESCRIPTIVE, always printed, never a gate
    fc = cell.get("strict_frame_check_info")
    if fc is not None and "heading_diff_deg" in fc:
        check(f"{trial}/{est}/{arm} heading offset == rd(strict_frame_check_info.heading_diff_deg, {HDP})",
              c_head == rd(fc["heading_diff_deg"], HDP), f"printed={c_head} rd={rd(fc['heading_diff_deg'], HDP)}")
    else:
        check(f"{trial}/{est}/{arm} heading offset column is '—' (no heading_diff_deg available)",
              c_head == "—", c_head)

    # 5: raw values vs STOP
    is_stop = c_rms.startswith("STOP")
    has_raw = "raw" in cell
    check(f"{trial}/{est}/{arm} STOP-in-md matches no-raw-in-json", is_stop != has_raw,
          f"is_stop={is_stop} has_raw={has_raw}")
    if is_stop:
        gate_ok = cell.get("gate", {}).get("ok", False)
        est_validated = ev_recomputed[est]["validated"]
        check(f"{trial}/{est}/{arm} STOP row has a failing gate or a failed-validation estimator",
              (not gate_ok) or (not est_validated), f"gate_ok={gate_ok} est_validated={est_validated}")
    else:
        r = cell["raw"]
        pairs = [("rms", c_rms, r["rms_3d_m"]), ("end", c_end, r["end_3d_m"]),
                 ("rms_h", c_rmsh, r["rms_h_m"]), ("end_h", c_endh, r["end_h_m"])]
        for name, printed, val in pairs:
            check(f"{trial}/{est}/{arm} {name} == rd(json, {DP})", printed == rd(val, DP),
                  f"printed={printed} rd={rd(val, DP)}")

# completeness: every json cell appears exactly once in the md, and vice versa (already enforced by seen_keys)
json_keys = set(CELLS.keys())
check("every json cell appears exactly once in the md", json_keys == seen_keys,
      f"missing from md: {json_keys - seen_keys}; extra in md: {seen_keys - json_keys}")
check("row count == json cell count", n_rows == len(J["cells"]), f"{n_rows} vs {len(J['cells'])}")

print(f"\nrows checked: {n_rows}; checks {n_ok} OK, {n_fail} FAIL")
sys.exit(0 if n_fail == 0 else 1)
