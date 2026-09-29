#!/usr/bin/env bash
# Consolidated re-run: the whole analysis pipeline, from scratch, on the re-flown bags
# (user rulings 2026-09-29; METHODOLOGY "CONSOLIDATED RE-RUN"). A correction, not a tuning
# pass: every script and setting is the pre-registered one; the only differences from the
# original pipeline are the batched corrections, which live in the code, parameter files and
# re-flown bags.
#
# Resumable: each stage writes <STATE>/<stage>.done; re-running the script skips finished
# stages (the replay stage also resumes per job). Run only when no trial is flying.
# Usage: eval/rerun_pipeline.sh            (state in ~/thesis_data/batches/rerun_pipeline/)
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
STATE="$HOME/thesis_data/batches/rerun_pipeline"; mkdir -p "$STATE"
RES=eval/results; OLD=eval/results_pre_rerun
EVO="$HOME/venv-evo/bin/python"; AP="$HOME/venv-ardupilot/bin/python"; FWD="$HOME/venv-fwd/bin/python"
PAR=6
log() { echo "$(date +%FT%T)  $*" | tee -a "$STATE/pipeline.log"; }
stage() { [ -f "$STATE/$1.done" ] && { log "skip $1 (done)"; return 1; }; log "BEGIN $1"; return 0; }
done_() { touch "$STATE/$1.done"; log "DONE  $1"; }
die() { log "FAILED $1"; echo "$1" > "$STATE/FAILED"; exit 1; }
set_of() { local p="$1"; for r in 1 2 3; do for w in tex trans blank; do echo "${p}_${w}_r$r"; done; done; }
P1C=(p1c_fwdc_tex p1c_fwdplainc_tex p1c_fwdc_trans p1c_fwdplainc_trans p1c_fwdc_blank p1c_fwdplainc_blank)
DSN=($(set_of dsn)); DS=($(set_of ds)); FWDC=($(set_of fwdc)); FWDPC=($(set_of fwdplainc))

for b in rerun2_main rerun2_ds; do
    [ -f "$HOME/thesis_data/batches/$b/DONE" ] || die "batch $b not DONE"
done

# 0. Keep the pre-re-run results side by side (never overwritten afterwards).
if stage snapshot; then
    [ -d "$OLD" ] || cp -r "$RES" "$OLD" || die snapshot
    done_ snapshot
fi

# 1. dsn baseline (IMU-gap rule, UKF/FGO replays, timing, flow quality, three-way evo).
#    Its phase2_score output (dsn scored against itself) is not used.
if stage dsn; then
    eval/run_set_eval.sh rerun_dsn "${DSN[@]}" > "$STATE/dsn.txt" 2>&1 || die "dsn set eval"
    # new P2 / P3 references for the re-run (the old ones stay in $OLD)
    cp "$RES/input_timing_rerun_dsn.json" "$RES/input_timing_linmap.json" || die "dsn refs"
    cp "$RES/flow_quality_rerun_dsn.json" "$RES/flow_quality_dsn.json" || die "dsn refs"
    cp "$RES/rerun_dsn_evo.json" "$RES/dsn_dejitter_baseline.json" || die "dsn refs"
    done_ dsn
fi

# 2. P4 bands from the re-flown dsn, pre-registered formula.
if stage bands; then
    python3 eval/rerun_bands.py "$RES/rerun_dsn_evo.json" --json "$RES/rerun_p4_bands.json" > "$STATE/bands.txt" || die bands
    done_ bands
fi
export P4_BANDS="$RES/rerun_p4_bands.json"

# 3. ds (compass-active reference): IMU gaps and EKF3 only, as before (no UKF/FGO on ds).
if stage ds; then
    "$EVO" eval/imu_gap_check.py "${DS[@]}" --write > "$STATE/ds_gaps.txt" 2>&1 || die "ds gaps"
    for t in "${DS[@]}"; do "$EVO" eval/extract_gt_tum.py "$t" > /dev/null || die "ds gt tum $t"; done   # cruise window source
    "$AP" eval/three_way_eval.py "${DS[@]}" --only EKF3 --json "$RES/rerun_ds_evo.json" > "$STATE/ds_evo.txt" 2>&1 || die "ds evo"
    done_ ds
fi

# 4. Forward-camera sets: set eval (replays, P1-P4 scoring with the re-run bands).
for s in p1c fwdc fwdplainc; do
    if stage "set_$s"; then
        case $s in p1c) T=("${P1C[@]}");; fwdc) T=("${FWDC[@]}");; fwdplainc) T=("${FWDPC[@]}");; esac
        eval/run_set_eval.sh "rerun_$s" "${T[@]}" > "$STATE/set_$s.txt" 2>&1 || die "set eval $s"
        done_ "set_$s"
    fi
done

# 5. Phase 3 with FROZEN parameters (no recalibration): measurements, then validation on the
#    18 datasets and, separately, on the re-flown p1c (second validation). Writes gt_eval_only.
if stage phase3; then
    for t in "${P1C[@]}" "${FWDC[@]}" "${FWDPC[@]}"; do echo "$t cd $PWD && $FWD eval/fwd_run.py $t --frozen"; done > "$STATE/phase3.jobs"
    eval/run_jobs_resumable.sh "$STATE/phase3.jobs" rerun_phase3 "$PAR" > "$STATE/phase3_jobs.txt" 2>&1 || die "phase3 runs"
    [ -f "$HOME/thesis_data/batches/rerun_phase3/DONE" ] || die "rerun_phase3: not all jobs DONE (see ~/thesis_data/batches/rerun_phase3/FAILED)"
    "$FWD" eval/fwd_eval.py --validate "${FWDC[@]}" "${FWDPC[@]}" --json "$RES/fwd_validation.json" > "$STATE/phase3_val.txt" 2>&1 || die "phase3 validate"
    "$FWD" eval/fwd_eval.py --validate "${P1C[@]}" --json "$RES/fwd_validation_p1c.json" > "$STATE/phase3_val_p1c.txt" 2>&1 || die "phase3 validate p1c"
    "$FWD" eval/fwd_transition_segments.py --json "$RES/fwd_transition_segments.json" > "$STATE/phase3_trans.txt" 2>&1 || die "phase3 trans"
    done_ phase3
fi

# 6. Phase 4 arms (the pre-registered job list, unchanged) and evaluation.
if stage phase4; then
    grep -v "^#" batches/phase4_replays.jobs > "$STATE/phase4.jobs"
    eval/run_jobs_resumable.sh "$STATE/phase4.jobs" rerun_phase4 "$PAR" > "$STATE/phase4_jobs.txt" 2>&1 || die "phase4 replays"
    [ -f "$HOME/thesis_data/batches/rerun_phase4/DONE" ] || die "rerun_phase4: not all jobs DONE (see ~/thesis_data/batches/rerun_phase4/FAILED)"
    "$EVO" eval/phase4_eval.py fwdc fwdplainc > "$STATE/phase4_eval.txt" 2>&1 || die "phase4 eval"
    done_ phase4
fi

# 7. Phase 5, the distance-scale check, the heading-share restatement.
if stage phase5; then
    "$AP" eval/phase5_analysis.py --json "$RES/phase5_analysis.json" > "$STATE/phase5.txt" 2>&1 || die phase5
    "$EVO" eval/scale_check.py --json "$RES/scale_check.json" > "$STATE/scale.txt" 2>&1 || die scale
    "$AP" eval/heading_share.py "$RES/rerun_dsn_evo.json" --json "$RES/heading_share_restated.json" > "$STATE/heading_share.txt" 2>&1 || die heading_share
    done_ phase5
fi

# 8. Phase 5b: sandboxed instrumented replays, then consistency.
if stage phase5b; then
    SBH="$HOME/thesis_data/phase5b_rerun/home"
    eval/build_5b_sandbox.sh "$SBH" "$STATE/phase5b.jobs" > "$STATE/phase5b_build.txt" 2>&1 || die "5b sandbox"
    grep -v "^#" "$STATE/phase5b.jobs" > "$STATE/phase5b_clean.jobs"
    eval/run_jobs_resumable.sh "$STATE/phase5b_clean.jobs" rerun_phase5b "$PAR" > "$STATE/phase5b_jobs.txt" 2>&1 || die "5b replays"
    [ -f "$HOME/thesis_data/batches/rerun_phase5b/DONE" ] || die "rerun_phase5b: not all jobs DONE (see ~/thesis_data/batches/rerun_phase5b/FAILED)"
    PHASE5B_SB="$SBH/thesis_data/trials" "$AP" eval/phase5b_consistency.py --json "$RES/phase5b_consistency.json" > "$STATE/phase5b.txt" 2>&1 || die 5b
    done_ phase5b
fi
log "PIPELINE COMPLETE"
touch "$STATE/COMPLETE"
