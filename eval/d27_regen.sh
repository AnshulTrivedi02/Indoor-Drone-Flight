#!/usr/bin/env bash
# D27 (b): regenerate every offline-UKF-dependent result from the re-run UKF replays (batches/d27_ukf_rerun_v2.jobs),
# WITHOUT re-replaying the FGO (its outputs are unchanged). The old JSONs are copied to eval/results_preD27/ first;
# eval/d27_compare.py then lists every changed number and flags any change outside the UKF fields.
# Commands are those that produced the committed results (eval/d15_pipeline.sh, run_set_eval.sh steps 4-5, and the
# F-test evaluators), minus the replay steps.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
RES=eval/results; OLD=eval/results_preD27; mkdir -p "$OLD"
EVO="$HOME/venv-evo/bin/python"; AP="$HOME/venv-ardupilot/bin/python"; FGOP="$HOME/venv-fgo/bin/python"; TD="$HOME/thesis_data/trials"
LOG="$HOME/thesis_data/batches/d27_regen"; mkdir -p "$LOG"
die() { echo "FAILED: $*" | tee -a "$LOG/regen.log"; exit 1; }
set_of() { local p="$1"; for r in 1 2 3; do for w in tex trans blank; do echo "${p}_${w}_r$r"; done; done; }
DSN=($(set_of dsn)); FWDC=($(set_of fwdc)); FWDPC=($(set_of fwdplainc))
P1C=(p1c_fwdc_tex p1c_fwdplainc_tex p1c_fwdc_trans p1c_fwdplainc_trans p1c_fwdc_blank p1c_fwdplainc_blank)
EXTRA=(dsn_tex_r4 dsn_tex_r5 dsn_tex_r6 dsn_tex_r7 dsn_tex_r8 dsn_tex_r9 dsn_tex_r10)
FILES=(rerun_dsn_evo rerun_dsn_score dsn_extra_evo dsn_extra_score rerun_p1c_evo rerun_p1c_score rerun_fwdc_evo rerun_fwdc_score
       rerun_fwdplainc_evo rerun_fwdplainc_score rerun_p4_bands dsn_paired_test phase4_fwdc_evo phase4_fwdc_arms
       phase4_fwdplainc_evo phase4_fwdplainc_arms phase5_analysis scale_check heading_share_restated phase5b_consistency
       d15_kick d15_drift blank_behaviour rtf_drift_check f1_test f2_test f3_test f3b_test f3c_test dsn_dejitter_baseline)
for f in "${FILES[@]}"; do [ -f "$RES/$f.json" ] && [ ! -f "$OLD/$f.json" ] && cp "$RES/$f.json" "$OLD/$f.json"; done

# 1. three-way evaluation + score per set (run_set_eval.sh steps 4-5; timing/flow-quality inputs unchanged)
evalset() {   # TAG TRIAL...
    local TAG="$1"; shift; local parts=() OK=() BAD=()
    for t in "$@"; do
        v=$(python3 -c "import json;print(json.load(open('$TD/$t/imu_gaps.json'))['verdict'])")
        if [ "$v" = unusable ]; then BAD+=("$t"); else OK+=("$t"); fi
    done
    if [ "${#OK[@]}" -gt 0 ]; then "$AP" eval/three_way_eval.py "${OK[@]}" --json "$LOG/${TAG}_ok.json" > "$LOG/${TAG}_ok.txt" 2>&1 || die "three_way $TAG"; parts+=("$LOG/${TAG}_ok.json"); fi
    for t in "${BAD[@]}"; do "$AP" eval/three_way_eval.py "$t" --only EKF3 --json "$LOG/${TAG}_$t.json" > /dev/null 2>&1 || die "three_way $t"; parts+=("$LOG/${TAG}_$t.json"); done
    python3 - "$RES/${TAG}_evo.json" "${parts[@]}" <<'PYEOF' || die "merge $TAG"
import json, sys
out = None
for p in sys.argv[2:]:
    d = json.load(open(p))
    if out is None: out = d
    else:
        assert d["window_def"] == out["window_def"]; out["trials"].update(d["trials"])
json.dump(out, open(sys.argv[1], "w"), indent=1)
PYEOF
    python3 eval/phase2_score.py --trials "$(IFS=,; echo "$*,")" --timing "input_timing_$TAG.json" --flow "flow_quality_$TAG.json" \
        --evo "${TAG}_evo.json" --json "$RES/${TAG}_score.json" > "$LOG/${TAG}_score.txt" 2>&1 || die "score $TAG"
}
evalset rerun_dsn "${DSN[@]}"; cp "$RES/rerun_dsn_evo.json" "$RES/dsn_dejitter_baseline.json"
evalset dsn_extra "${EXTRA[@]}"
# the P4 bands come from the corrected dsn and MUST be exported before the forward sets are scored, as in
# d15_pipeline.sh (first version of this script exported them afterwards: the forward-set scores then used the
# script's fixed bands; caught by d27_compare.py as non-UKF changes, and the scores were redone with the bands)
python3 eval/rerun_bands.py "$RES/rerun_dsn_evo.json" --json "$RES/rerun_p4_bands.json" > "$LOG/bands.txt" 2>&1 || die bands
export P4_BANDS="$RES/rerun_p4_bands.json"
evalset rerun_p1c "${P1C[@]}"; evalset rerun_fwdc "${FWDC[@]}"; evalset rerun_fwdplainc "${FWDPC[@]}"
python3 eval/dsn_paired_test.py "$RES/rerun_dsn_evo.json" "$RES/dsn_extra_evo.json" --json "$RES/dsn_paired_test.json" > "$LOG/paired.txt" 2>&1 || die paired

# 2. Phase 4, Phase 5, scale, heading share, Phase 5b (D15 sandbox)
"$EVO" eval/phase4_eval.py fwdc fwdplainc > "$LOG/phase4_eval.txt" 2>&1 || die phase4
"$AP" eval/phase5_analysis.py --json "$RES/phase5_analysis.json" > "$LOG/phase5.txt" 2>&1 || die phase5
"$EVO" eval/scale_check.py --json "$RES/scale_check.json" > "$LOG/scale.txt" 2>&1 || die scale
"$AP" eval/heading_share.py "$RES/rerun_dsn_evo.json" --json "$RES/heading_share_restated.json" > "$LOG/heading_share.txt" 2>&1 || die heading_share
PHASE5B_SB="$HOME/thesis_data/phase5b_d15/home/thesis_data/trials" "$AP" eval/phase5b_consistency.py --json "$RES/phase5b_consistency.json" > "$LOG/phase5b.txt" 2>&1 || die phase5b

# 3. D15 kick and drift, the RTF check
"$AP" eval/d15_kick.py dsn_tex_r{1,2,3,4,5,6,7,8,9,10} --json "$RES/d15_kick.json" > "$LOG/kick.txt" 2>&1 || die kick
"$AP" eval/d15_drift.py dsn_tex_r{1,2,3,4,5,6,7,8,9,10} dsn_trans_r{1,2,3} --json "$RES/d15_drift.json" > "$LOG/drift.txt" 2>&1 || die drift
python3 eval/rtf_drift_check.py --json "$RES/rtf_drift_check.json" > "$LOG/rtf.txt" 2>&1 || die rtf

# 4. blank behaviour (venv-evo + the pymavlink shim: it needs rosbags AND pymavlink): regenerate per arm group, then replace ONLY the ukf* entries of the committed file
PYTHONPATH="$HOME/.cache/thesis_pyshim" "$EVO" eval/blank_behaviour.py dsn_blank_r{1,2,3} dsn_trans_r{1,2,3} p1c_fwdc_blank p1c_fwdc_trans p1c_fwdplainc_blank p1c_fwdplainc_trans \
    --arms ukf,fgo --json "$LOG/bb_plain.json" > "$LOG/bb_plain.txt" 2>&1 || die bb_plain
PYTHONPATH="$HOME/.cache/thesis_pyshim" "$EVO" eval/blank_behaviour.py fwdc_blank_r{1,2,3} fwdc_trans_r{1,2,3} fwdplainc_blank_r{1,2,3} fwdplainc_trans_r{1,2,3} \
    --arms ukf_baseline,fgo_baseline,ukf_heading,fgo_heading --json "$LOG/bb_arms.json" > "$LOG/bb_arms.txt" 2>&1 || die bb_arms
python3 - "$OLD/blank_behaviour.json" "$LOG/bb_plain.json" "$LOG/bb_arms.json" "$RES/blank_behaviour.json" "$LOG/bb_check.txt" <<'PYEOF' || die bb_merge
import json, sys
old = json.load(open(sys.argv[1])); new = {**json.load(open(sys.argv[2])), **json.load(open(sys.argv[3]))}
out = json.loads(json.dumps(old)); notes = []
for t, d in new.items():
    for k, v in d.items():
        if k.startswith("ukf"):
            out[t][k] = v
        elif json.dumps(v, sort_keys=True) != json.dumps(old[t].get(k), sort_keys=True):
            notes.append(f"NON-UKF FIELD DIFFERS: {t}.{k}")
json.dump(out, open(sys.argv[4], "w"), indent=1)
open(sys.argv[5], "w").write("\n".join(notes) + ("\n" if notes else "all non-UKF fields identical\n"))
PYEOF

# 5. F-tests (offline UKF arms re-replayed in the batch; FGO arms unchanged)
"$FGOP" eval/f1_eval.py test cauchy:2.385 --json "$RES/f1_test.json" > "$LOG/f1.txt" 2>&1 || die f1
"$FGOP" eval/f23_eval.py f2 --json "$RES/f2_test.json" > "$LOG/f2.txt" 2>&1 || die f2
"$FGOP" eval/f23_eval.py f3 --json "$RES/f3_test.json" > "$LOG/f3.txt" 2>&1 || die f3
"$FGOP" eval/f3b_eval.py --json "$RES/f3b_test.json" > "$LOG/f3b.txt" 2>&1 || die f3b
"$FGOP" eval/f3c_eval.py --tag F3cd --deltas 10,30 --json "$RES/f3c_test.json" > "$LOG/f3c.txt" 2>&1 || die f3c
echo "REGEN COMPLETE" | tee -a "$LOG/regen.log"
