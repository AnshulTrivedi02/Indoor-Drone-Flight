#!/usr/bin/env python3
"""Exact cross-check for docs/thesis/raw_corridor/raw_corridor_numbers.md against
eval/results/raw_corridor_errors.json and the original registered-result JSONs (rerun_dsn_evo.json,
dsn_extra_evo.json, phase4_fwdc_arms.json, phase4_fwdplainc_arms.json). stdlib + json only (ast, hashlib,
json, os, re, sys, decimal — no third-party imports), per the brief.

Checks, per data row of raw_corridor_numbers.md:
  1. the printed aligned value (evo -a cruise) equals rd(cell.stored_ate_a_cruise, 2) from the json;
  2. cell.stored_ate_a_cruise itself equals the value at the ORIGINAL source file + key path (re-derived
     independently from the cell's dataset/trial/estimator/arm, not from the free-text "source" string);
  3. where a numbers.md line number is cited, that numbers.md line contains the printed aligned value
     string;
  4. if the row is a STOP, the json has no "raw" entry for that cell and its frame_check failed (or the
     gate failed); if the row is not a STOP, the four printed raw values equal rd(json value, 2) exactly.

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


# ------------------------------------------------------------------------------------- load json + markdown
J = json.load(open(JSON_PATH))
CELLS = {(c["trial"], c["estimator"], c["arm"]): c for c in J["cells"]}
check("rd() SHA matches the json's recorded rd_sha256", RD_SHA == J["rd_sha256"], f"{RD_SHA} vs {J['rd_sha256']}")

NUM_LINES = open(NUMBERS_MD).read().split("\n")

ARM_LABEL_REV = {"": "baseline", "+heading": "heading", "+heading+yaw rate": "heading_yawrate"}

md_lines = open(MD_PATH).read().split("\n")
row_re = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$")
n_rows = 0
for line in md_lines:
    m = row_re.match(line)
    if not m or m.group(1) == "flight":
        continue
    trial, est_arm, aligned_cell, c_rms, c_end, c_rmsh, c_endh = m.groups()
    toks = est_arm.split(" ", 1)
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
    cell = CELLS[key]

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

    # 3: numbers.md citation, if present
    mline = re.search(r"numbers\.md:(\d+)", aligned_cell)
    if mline:
        lineno = int(mline.group(1))
        text = NUM_LINES[lineno - 1] if 0 < lineno <= len(NUM_LINES) else ""
        check(f"{trial}/{est}/{arm} numbers.md:{lineno} contains the printed aligned value",
              am is not None and am.group(1) in text.replace("**", ""), text)

    # 4: raw values vs STOP
    is_stop = c_rms.startswith("STOP")
    has_raw = "raw" in cell
    check(f"{trial}/{est}/{arm} STOP-in-md matches no-raw-in-json", is_stop != has_raw,
          f"is_stop={is_stop} has_raw={has_raw}")
    if is_stop:
        fc = cell.get("frame_check")
        gate_ok = cell.get("gate", {}).get("ok", False)
        check(f"{trial}/{est}/{arm} STOP row has a failing gate or frame_check",
              (fc is not None and not fc.get("ok", True)) or not gate_ok)
    else:
        r = cell["raw"]
        pairs = [("rms", c_rms, r["rms_3d_m"]), ("end", c_end, r["end_3d_m"]),
                 ("rms_h", c_rmsh, r["rms_h_m"]), ("end_h", c_endh, r["end_h_m"])]
        for name, printed, val in pairs:
            check(f"{trial}/{est}/{arm} {name} == rd(json, {DP})", printed == rd(val, DP),
                  f"printed={printed} rd={rd(val, DP)}")

print(f"\nrows checked: {n_rows}; checks {n_ok} OK, {n_fail} FAIL")
sys.exit(0 if n_fail == 0 else 1)
