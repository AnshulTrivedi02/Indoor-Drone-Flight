#!/usr/bin/env python3
"""Map-collapse diagnosis: run status of a counterfactual with the E3 definitions (stage2e/run_status.py, imported
unchanged; only its output directory is redirected to diag_collapse/status), plus the prefix-identity harness check:
the counterfactual's live.tum rows must equal the original T_A_r1 1% s0 rows for every keyframe BEFORE the keyframe of
the first kept detection. Usage: status_cf.py NAME RUN_DIR LOG FIRST_KEPT_KEYFRAME_T"""
import sys, json
sys.path.insert(0, "/home/makerspace/thesis_data/tier1/stage2e"); import run_status as R
O = "/home/makerspace/thesis_data/tier1/stage2e/diag_collapse"; R.S = O
name, rdir, log, tk = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
d = R.status(name, log=log, rdir=rdir)
orig = open("/home/makerspace/thesis_data/tier1/T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s0/live.tum").read().splitlines()
cf = open(f"{rdir}/live.tum").read().splitlines()
pre_o = [l for l in orig if float(l.split()[0]) < tk - 1e-6]; pre_c = [l for l in cf if float(l.split()[0]) < tk - 1e-6]
first_diff = next((i for i, (a, b) in enumerate(zip(orig, cf)) if a != b), None)
res = {"prefix_rows_before_first_kept_keyframe": len(pre_o), "prefix_identical": pre_o == pre_c,
       "first_differing_row_t": None if first_diff is None else float(orig[first_diff].split()[0])}
d["prefix_check"] = res; json.dump(d, open(f"{O}/status/{name}.json", "w"), indent=1); print(res)
