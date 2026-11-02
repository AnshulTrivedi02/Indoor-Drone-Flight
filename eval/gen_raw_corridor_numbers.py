#!/usr/bin/env python3
"""Generates docs/thesis/raw_corridor/raw_corridor_numbers.md from eval/results/raw_corridor_errors.json
(raw-corridor branch, Stage 1, D106/D107). Read-only on numbers.md (only grepped for citation line numbers,
never edited) and on the json (only read). DESCRIPTIVE ONLY.

Usage: python3 eval/gen_raw_corridor_numbers.py
"""
import ast, hashlib, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JSON_PATH = os.path.join(ROOT, "eval", "results", "raw_corridor_errors.json")
NUMBERS_MD = os.path.join(ROOT, "docs", "thesis", "numbers.md")
OUT_MD = os.path.join(ROOT, "docs", "thesis", "raw_corridor", "raw_corridor_numbers.md")

FT = os.path.join(HERE, "figs_thesis.py")
_src = open(FT).read()
_tree = ast.parse(_src)
_rd_node = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == "rd")
_rd_src = ast.get_source_segment(_src, _rd_node)
_ns = {}
exec(compile(ast.Module(body=[_rd_node], type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
RD_SHA = hashlib.sha256(_rd_src.encode()).hexdigest()

DP = 2   # metres, same decimals numbers.md uses for the aligned dsn/fwdc/phase4 values (§6.1, §6.4, §6.6)

# ------------------------------------------------------------------------------------- numbers.md citation lookup (CURRENT §6 only)
NUM_LINES = open(NUMBERS_MD).read().split("\n")
_sec6_start = next(i for i, l in enumerate(NUM_LINES) if l.startswith("## 6. Baseline results — RESTATED"))
_sec7_start = next(i for i in range(_sec6_start + 1, len(NUM_LINES)) if NUM_LINES[i].startswith("## 7."))
CURRENT = NUM_LINES[_sec6_start:_sec7_start]   # 0-indexed within this slice; absolute line = _sec6_start + i + 1

LABEL_MAP = {
    "EKF3": ("dsn_tex", "EKF3", "baseline"),
    "FGO (0.25 s)": ("dsn_tex", "FGO", "baseline"),
    "UKF": ("dsn_tex", "UKF", "baseline"),
    "`fwdc` textured EKF3": ("fwdc", "EKF3", "baseline"),
    "`fwdc` textured FGO": ("fwdc", "FGO", "baseline"),
    "`fwdc` textured UKF": ("fwdc", "UKF", "baseline"),
    "`fwdplainc` textured EKF3": ("fwdplainc", "EKF3", "baseline"),
    "`fwdplainc` textured FGO": ("fwdplainc", "FGO", "baseline"),
    "`fwdplainc` textured UKF": ("fwdplainc", "UKF", "baseline"),
    "`fwdc` UKF +heading": ("fwdc", "UKF", "heading"),
    "`fwdc` FGO +heading": ("fwdc", "FGO", "heading"),
    "`fwdplainc` UKF +heading": ("fwdplainc", "UKF", "heading"),
    "`fwdplainc` FGO +heading": ("fwdplainc", "FGO", "heading"),
}
# these numbers.md rows only ever cover the TEXTURED repeats (r1/r2/r3), never blank/transition
CITE = {}   # (dataset, estimator, arm, rank 0/1/2) -> (abs_line_no, printed_value_str)
PAT = re.compile(r"^\|\s*(.*?)\s*r1\s*/\s*r2\s*/\s*r3\s*\|\s*([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)")
for i, raw_line in enumerate(CURRENT):
    line = raw_line.replace("**", "")
    m = PAT.match(line)
    if not m:
        continue
    label = m.group(1)
    if label not in LABEL_MAP:
        continue
    dataset, est, arm = LABEL_MAP[label]
    abs_line = _sec6_start + i + 1   # 1-indexed
    for rank in range(3):
        CITE[(dataset, est, arm, rank)] = (abs_line, m.group(2 + rank))


def numbers_citation(dataset, est, arm, trial):
    """trial like 'dsn_tex_r1' or 'fwdc_tex_r2' -> (line, value_str) if numbers.md prints this exact value, else None.
    Only textured r1/r2/r3 rows are ever individually printed (confirmed by grepping numbers.md section 6)."""
    m = re.search(r"_r(\d+)$", trial)
    if not m:
        return None
    rank = int(m.group(1)) - 1
    if rank not in (0, 1, 2):
        return None
    if dataset in ("fwdc", "fwdplainc") and "_tex_" not in trial:
        return None   # numbers.md only prints the textured repeats for these rows
    return CITE.get((dataset, est, arm, rank))


# ------------------------------------------------------------------------------------- load results
D = json.load(open(JSON_PATH))
CELLS = D["cells"]

DATASET_ORDER = ["dsn_tex", "dsn_blank", "dsn_trans", "fwdc", "fwdplainc"]
DATASET_TITLE = {"dsn_tex": "Standard-sensor dataset (`dsn`), textured floor",
                  "dsn_blank": "Standard-sensor dataset (`dsn`), blank floor",
                  "dsn_trans": "Standard-sensor dataset (`dsn`), transition floor",
                  "fwdc": "Forward-camera, line-textured walls (`fwdc`)",
                  "fwdplainc": "Forward-camera, plain walls (`fwdplainc`)"}
EST_ORDER = {"EKF3": 0, "UKF": 1, "FGO": 2}
ARM_ORDER = {"baseline": 0, "heading": 1, "heading_yawrate": 2}
ARM_LABEL = {"baseline": "", "heading": "+heading", "heading_yawrate": "+heading+yaw rate"}


def trial_rank(trial):
    m = re.search(r"_r(\d+)$", trial)
    return int(m.group(1)) if m else 0


def sort_key(c):
    return (trial_rank(c["trial"]), EST_ORDER[c["estimator"]], ARM_ORDER[c["arm"]])


by_dataset = {k: [] for k in DATASET_ORDER}
for c in CELLS:
    by_dataset[c["dataset"]].append(c)

LINES = []
LINES.append("# Raw corridor errors (Stage 1, descriptive; raw-corridor branch, D106/D107)\n")
LINES.append(f"Generated by `eval/gen_raw_corridor_numbers.py` from `eval/results/raw_corridor_errors.json` "
             f"(generated by `eval/raw_corridor_errors.py`). **DESCRIPTIVE ONLY — nothing fitted** (no rotation, "
             "translation or scale alignment); these values do not change, supersede or re-derive any registered "
             "(evo -a, aligned) verdict in `docs/thesis/numbers.md`, which is unchanged by this file.\n")
LINES.append("**Frame convention** (identical to Figure 4.1c / R5, `docs/thesis/figures_thesis/index_drift.md`, "
             "re-derived for this scope, not imported): EKF3 traj + truth are (N, E, D) -> (N, E, U) = "
             "(col1, col2, −col3). UKF/FGO truth files are ENU (E, N, U) -> (N, E, U) = (col2, col1, col3). "
             "UKF/FGO estimate files are the estimator's own frame, x = take-off heading (North), y = West, "
             "z = up (yaw0 = 0.0 by construction: `src/estimators/ukf_core.py` `init_state()`, "
             "`src/estimators/fgo/fgo_core.py` `init(yaw0=0.0)` default) -> (N, E, U) = (col1, −col2, col3). "
             "No other rotation, offset or scale.\n")
LINES.append("**Window source:** the registered cruise window `window_s` stored alongside each cell's own "
              "`ate_a_cruise` (cited per row below) — the same window the registered evo -a (cruise) value was "
              "computed on.\n")
LINES.append(f"**Association:** `evo.core.sync.associate_trajectories`, `t_max_diff = {D['t_max_diff_s']} s`, "
              "identical to `eval/three_way_eval.py`/`eval/figs_thesis_drift.py`. The raw (unaligned) error is a "
              "plain subtraction in the common (N, E, U) frame on this same association — no `.align()` call.\n")
LINES.append(f"**GATE (stop condition):** evo -a (cruise) recomputed in each cell's OWN (un-relabelled) stored "
              f"frame and required to equal the stored `ate_a_cruise` after `rd(.,6)`, string-for-string. "
              f"**{D['n_gate_ok']}/{D['n_cells']} cells passed the gate** (every cell in scope).\n")
LINES.append(f"**Frame check (stop condition per cell):** take-off |NE| < {D['orig_tol_m']} m (own first sample, "
              f"both estimate and truth) and the heading of the first 5 m of TRUE cruise travel (from the window "
              f"start) agrees with the estimate's own heading over the same interval to within "
              f"{D['head_tol_deg']}°. **{D['n_frame_ok']}/{D['n_cells']} cells passed**; "
              f"{D['n_cells'] - D['n_frame_ok']} STOP (raw values withheld; reason given per row) — overwhelmingly "
              "blank-floor cells, where there is no flow from take-off so the estimate's early heading is "
              "meaningless (and, for EKF3, the output is pinned near the origin), plus a handful of textured/"
              "transition UKF/FGO cells whose early yaw drift exceeds the 2.0° tolerance within the first 5 m "
              "(a property of those specific flights, not of the frame map — see the handover, RC-5/RC-6).\n")
LINES.append(f"**Rounding:** `rd()` parsed from `eval/figs_thesis.py` (not executed, matching "
              f"`eval/figs_thesis_drift.py`'s own practice); SHA-256 of its source `{RD_SHA}`. All values below "
              f"are rounded ONCE, to {DP} dp, matching numbers.md §6.1/§6.4/§6.6's own precision for the aligned "
              "cruise ATE.\n")
LINES.append("**Citation:** every row cites `eval/results/raw_corridor_errors.json` (which records, per cell, the "
              "exact source file + JSON key the registered `ate_a_cruise` came from). Where numbers.md ALSO "
              "prints that exact value (confirmed by grep at generation time, §6.1/§6.4/§6.6, textured repeats "
              "r1-r3 only), the line number is given too; blank/transition and r4-r10 individual values, and all "
              "heading-arm transition/blank rows, are not individually printed anywhere in numbers.md (only "
              "aggregate ranges/means are) and are cross-checked against the JSON only, exactly as "
              "`index_drift.md` already notes for its own blank/transition rows.\n")

for dataset in DATASET_ORDER:
    cells = sorted(by_dataset[dataset], key=sort_key)
    LINES.append(f"\n## {DATASET_TITLE[dataset]}\n")
    LINES.append("| flight | estimator/arm | evo -a cruise (registered, cited) | raw RMS (DESCRIPTIVE) | "
                  "raw end-of-cruise (DESCRIPTIVE) | raw horizontal RMS | raw horizontal end |")
    LINES.append("|---|---|---|---|---|---|---|")
    for c in cells:
        label = c["estimator"] + (" " + ARM_LABEL[c["arm"]] if ARM_LABEL[c["arm"]] else "")
        aligned_str = rd(c["stored_ate_a_cruise"], DP)
        cite = numbers_citation(dataset, c["estimator"], c["arm"], c["trial"])
        if cite:
            cite_str = f"json:{c['source']}; numbers.md:{cite[0]}"
        else:
            cite_str = f"json:{c['source']}"
        aligned_cell = f"{aligned_str} ({cite_str})"
        if "raw" not in c:
            fc = c.get("frame_check")
            if fc is not None:
                dh = fc["heading_est_deg"] - fc["heading_truth_deg"]
                reason = f"frame check: heading off {dh:+.1f}° over first 5 m (tol {D['head_tol_deg']}°)"
            else:
                reason = c.get("stop", "STOP")
            cols = [f"STOP — {reason}"] * 4
        else:
            r = c["raw"]
            cols = [rd(r["rms_3d_m"], DP), rd(r["end_3d_m"], DP), rd(r["rms_h_m"], DP), rd(r["end_h_m"], DP)]
        LINES.append(f"| `{c['trial']}` | {label} | {aligned_cell} | " + " | ".join(cols) + " |")

os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
open(OUT_MD, "w").write("\n".join(LINES) + "\n")
print(f"wrote {OUT_MD}")
