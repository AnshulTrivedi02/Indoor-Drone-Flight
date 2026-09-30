#!/usr/bin/env bash
# D15 re-run (user ruling 2026-09-30, option (b)): the ground-proximity flow rule (METHODOLOGY
# "Ruling D15"), applied identically to the offline UKF and FGO, re-run on every affected bag with
# the same pre-registered scripts as the consolidated re-run (eval/rerun_pipeline.sh). A correction,
# not a tuning pass. EKF3-only stages (ds, Phase 3) are unaffected and are not re-run.
#
# Resumable: each stage writes <STATE>/<stage>.done. Run only when no trial is flying.
# Usage: eval/d15_pipeline.sh            (state in ~/thesis_data/batches/d15_pipeline/)
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
STATE="$HOME/thesis_data/batches/d15_pipeline"; mkdir -p "$STATE"
RES=eval/results; OLD=eval/results_pre_d15; ARCH="$HOME/thesis_data/pre_d15_trials"
EVO="$HOME/venv-evo/bin/python"; AP="$HOME/venv-ardupilot/bin/python"
PAR=6
log() { echo "$(date +%FT%T)  $*" | tee -a "$STATE/pipeline.log"; }
stage() { [ -f "$STATE/$1.done" ] && { log "skip $1 (done)"; return 1; }; log "BEGIN $1"; return 0; }
done_() { touch "$STATE/$1.done"; log "DONE  $1"; }
die() { log "FAILED $1"; echo "$1" > "$STATE/FAILED"; exit 1; }
set_of() { local p="$1"; for r in 1 2 3; do for w in tex trans blank; do echo "${p}_${w}_r$r"; done; done; }
P1C=(p1c_fwdc_tex p1c_fwdplainc_tex p1c_fwdc_trans p1c_fwdplainc_trans p1c_fwdc_blank p1c_fwdplainc_blank)
DSN=($(set_of dsn)); FWDC=($(set_of fwdc)); FWDPC=($(set_of fwdplainc))
EXTRA=(dsn_tex_r4 dsn_tex_r5 dsn_tex_r6 dsn_tex_r7 dsn_tex_r8 dsn_tex_r9 dsn_tex_r10)
rm -f "$STATE/FAILED"

# 0. Keep the pre-D15 results and every trial's UKF/FGO outputs (never overwritten afterwards).
if stage snapshot; then
    [ -d "$OLD" ] || cp -r "$RES" "$OLD" || die "snapshot results"
    for t in "${DSN[@]}" "${EXTRA[@]}" "${P1C[@]}" "${FWDC[@]}" "${FWDPC[@]}"; do
        mkdir -p "$ARCH/$t"
        for d in "$HOME/thesis_data/trials/$t"/ukf* "$HOME/thesis_data/trials/$t"/fgo*; do
            [ -e "$d" ] || continue
            [ -e "$ARCH/$t/$(basename "$d")" ] || cp -a "$d" "$ARCH/$t/" || die "snapshot $t"
        done
    done
    [ -d "$HOME/thesis_data/phase5b_rerun" ] && { [ -d "$ARCH/phase5b_rerun" ] || cp -a "$HOME/thesis_data/phase5b_rerun" "$ARCH/" || die "snapshot 5b"; }
    done_ snapshot
fi

# 1. dsn r1-r3 and the r4-r10 repeats (IMU-gap rule, replays, timing, flow quality, three-way evo).
if stage dsn; then
    eval/run_set_eval.sh rerun_dsn "${DSN[@]}" > "$STATE/dsn.txt" 2>&1 || die "dsn set eval"
    cp "$RES/rerun_dsn_evo.json" "$RES/dsn_dejitter_baseline.json" || die "dsn refs"
    done_ dsn
fi
if stage dsn_extra; then
    eval/run_set_eval.sh dsn_extra "${EXTRA[@]}" > "$STATE/dsn_extra.txt" 2>&1 || die "dsn_extra set eval"
    done_ dsn_extra
fi

# 2. P4 bands, pre-registered formula, from the corrected dsn.
if stage bands; then
    python3 eval/rerun_bands.py "$RES/rerun_dsn_evo.json" --json "$RES/rerun_p4_bands.json" > "$STATE/bands.txt" || die bands
    done_ bands
fi
export P4_BANDS="$RES/rerun_p4_bands.json"

# 3. The confirmatory EKF3-vs-FGO test and the noise floor (pre-registered script, unchanged).
if stage paired; then
    python3 eval/dsn_paired_test.py "$RES/rerun_dsn_evo.json" "$RES/dsn_extra_evo.json" --json "$RES/dsn_paired_test.json" > "$STATE/paired.txt" 2>&1 || die paired
    done_ paired
fi

# 4. Forward-camera sets.
for s in p1c fwdc fwdplainc; do
    if stage "set_$s"; then
        case $s in p1c) T=("${P1C[@]}");; fwdc) T=("${FWDC[@]}");; fwdplainc) T=("${FWDPC[@]}");; esac
        eval/run_set_eval.sh "rerun_$s" "${T[@]}" > "$STATE/set_$s.txt" 2>&1 || die "set eval $s"
        done_ "set_$s"
    fi
done

# 5. Phase 4 arms and evaluation.
if stage phase4; then
    grep -v "^#" batches/phase4_replays.jobs > "$STATE/phase4.jobs"
    eval/run_jobs_resumable.sh "$STATE/phase4.jobs" d15_phase4 "$PAR" > "$STATE/phase4_jobs.txt" 2>&1 || die "phase4 replays"
    [ -f "$HOME/thesis_data/batches/d15_phase4/DONE" ] || die "d15_phase4: not all jobs DONE"
    "$EVO" eval/phase4_eval.py fwdc fwdplainc > "$STATE/phase4_eval.txt" 2>&1 || die "phase4 eval"
    done_ phase4
fi

# 6. Phase 5, the distance-scale check, the heading-share restatement.
if stage phase5; then
    "$AP" eval/phase5_analysis.py --json "$RES/phase5_analysis.json" > "$STATE/phase5.txt" 2>&1 || die phase5
    "$EVO" eval/scale_check.py --json "$RES/scale_check.json" > "$STATE/scale.txt" 2>&1 || die scale
    "$AP" eval/heading_share.py "$RES/rerun_dsn_evo.json" --json "$RES/heading_share_restated.json" > "$STATE/heading_share.txt" 2>&1 || die heading_share
    done_ phase5
fi

# 7. Phase 5b: sandboxed instrumented replays (fresh sandbox), then consistency.
if stage phase5b; then
    SBH="$HOME/thesis_data/phase5b_d15/home"
    eval/build_5b_sandbox.sh "$SBH" "$STATE/phase5b.jobs" > "$STATE/phase5b_build.txt" 2>&1 || die "5b sandbox"
    grep -v "^#" "$STATE/phase5b.jobs" > "$STATE/phase5b_clean.jobs"
    eval/run_jobs_resumable.sh "$STATE/phase5b_clean.jobs" d15_phase5b "$PAR" > "$STATE/phase5b_jobs.txt" 2>&1 || die "5b replays"
    [ -f "$HOME/thesis_data/batches/d15_phase5b/DONE" ] || die "d15_phase5b: not all jobs DONE"
    PHASE5B_SB="$SBH/thesis_data/trials" "$AP" eval/phase5b_consistency.py --json "$RES/phase5b_consistency.json" > "$STATE/phase5b.txt" 2>&1 || die 5b
    done_ phase5b
fi
log "PIPELINE COMPLETE"
touch "$STATE/COMPLETE"
