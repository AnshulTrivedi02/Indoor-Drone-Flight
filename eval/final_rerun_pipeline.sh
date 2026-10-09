#!/usr/bin/env bash
# FINAL consolidated offline re-run (user rulings 2026-10-09: METHODOLOGY "RULING (user, 2026-10-09): FGO noise-model
# correction ... consolidated re-run plan" items 4-6; "MODEL AUDIT RESULT ... RULINGS" order 6-9; "RULINGS ... the yaw-cap
# ablation; the cut order"; and the derotation ruling of 2026-10-08 item 3). Every offline UKF and FGO result is re-run
# with ALL FOUR corrections in the code (UKF bias-corrected derotation, UKF jitter only on Cholesky failure, FGO
# setBiasAccOmegaInit = 0, FGO variance-gated yaw cap). EKF3 is unchanged and is GATED to be unchanged. A correction,
# not a tuning pass: every script, job list and setting is the one that produced the committed result.
#
# Stage order (ruled; L last; the protected items first): preflight -> snapshot -> dsn (HARD EKF3 GATE) -> dsn_extra ->
# bands -> paired (confirmatory test, original rule) -> set_p1c / set_fwdc / set_fwdplainc -> phase4 (C0 inputs) -> phase5
# (+ scale, heading share) -> phase5b -> d15_bb (kick, drift, RTF, blank behaviour) -> ftests (F1-F3c, PATnocap) -> f4
# (2(a)) -> h_shadows -> expO -> expT -> [d27item3, opt-in] -> [cl_pred, opt-in] -> L.
# STAGES (for --only / tools/launch_final_rerun.sh), in order:
#   preflight snapshot unpack dsn dsn_extra bands paired set_p1c set_fwdc set_fwdplainc phase4 phase5 phase5b d15_bb ftests
#   repack_corridor f4 h_shadows expO expT d27item3 cl_pred L compare
# Resumable: each stage writes <STATE>/<stage>.done; a re-run skips finished stages, and the replay stages resume per job
# (eval/run_jobs_resumable.sh). The snapshot and the trial-output archive DIE if their targets exist (never skip, never
# overwrite). Flight check at start and between every stage (FLIGHT_LOCK or arducopter / gz sim): waits up to
# FLIGHT_WAIT_S (default 0 = die at once), checking every 60 s, then dies.
#
# Usage:  eval/final_rerun_pipeline.sh [--dry-run] [--only STAGE]
#   --dry-run   print every command (and the job lists) without running any replay or evaluator; writes nothing
#               except to stdout; skips the flight / correction checks' FAILURE (reports them instead)
#   --only S    run stage S only (if its predecessors are .done); for per-stage launching under tools/heavy.py
# Launch ONLY via tools/launch_final_rerun.sh (which wraps tools/heavy.py). Never while a flight runs.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO="$PWD"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
DRY=0; ONLY=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --only) ONLY="$2"; shift;; *) echo "unknown arg $1" >&2; exit 2;; esac; shift; done

STATE="$HOME/thesis_data/batches/final_rerun"
RES=eval/results; OLD=eval/results_pre_final; ARCH="$HOME/thesis_data/pre_final_trials"
TD="$HOME/thesis_data/trials"
EVO="$HOME/venv-evo/bin/python"; AP="$HOME/venv-ardupilot/bin/python"; FGOP="$HOME/venv-fgo/bin/python"; TAGS="$HOME/venv-tags/bin/python"
SHIM="$HOME/.cache/thesis_pyshim"            # pymavlink shim for venv-evo (as eval/d27_regen.sh)
PAR="${PAR:-6}"; FLIGHT_WAIT_S="${FLIGHT_WAIT_S:-0}"
JOBS_DIR=batches/final_rerun                 # vendored, reviewable job lists (see the handover)
[ "$DRY" = 1 ] || mkdir -p "$STATE"

log() { if [ "$DRY" = 1 ]; then echo "# $*"; else echo "$(date +%FT%T)  $*" | tee -a "$STATE/pipeline.log"; fi; }
die() { log "FAILED $1"; [ "$DRY" = 1 ] || echo "$1" > "$STATE/FAILED"; exit 1; }
# run CMD... : execute (or print in dry-run). Output redirection is done by the caller through `runlog FILE CMD...`.
run() { if [ "$DRY" = 1 ]; then printf '  %q' "$@"; echo; else "$@"; fi; }
runlog() { local out="$1"; shift; if [ "$DRY" = 1 ]; then printf '  %q' "$@"; echo "  > $out"; else "$@" > "$out" 2>&1; fi; }
stage() {   # stage NAME : true if NAME should run now
    if [ -n "$ONLY" ] && [ "$ONLY" != "$1" ]; then return 1; fi
    if [ "$DRY" = 0 ] && [ -f "$STATE/$1.done" ]; then log "skip $1 (done)"; return 1; fi
    flight_check "$1"; log "BEGIN $1"; return 0
}
done_() { [ "$DRY" = 1 ] && { log "(dry) DONE $1"; return; }; touch "$STATE/$1.done"; log "DONE  $1"; }
need() { [ "$DRY" = 1 ] && return 0; for s in "$@"; do [ -f "$STATE/$s.done" ] || die "stage requires $s.done"; done; }

flying() {
    [ -e "$HOME/thesis_data/FLIGHT_LOCK" ] && { echo "FLIGHT_LOCK present: $(cat "$HOME/thesis_data/FLIGHT_LOCK" 2>/dev/null)"; return 0; }
    pgrep -fa '[a]rducopter' > /dev/null && { echo "arducopter running"; return 0; }
    pgrep -fa '[g]z sim' > /dev/null && { echo "gz sim running"; return 0; }
    return 1
}
flight_check() {   # before every stage: never replay while a flight runs (the replays load the CPU = the flight confound)
    local why t0=$SECONDS
    while why=$(flying); do
        if [ "$DRY" = 1 ]; then log "flight check before $1: WOULD WAIT/DIE ($why)"; return 0; fi
        [ $((SECONDS - t0)) -ge "$FLIGHT_WAIT_S" ] && die "flight in progress before stage $1 ($why); waited $((SECONDS - t0)) s"
        log "paused before $1: $why"; sleep 60
    done
}
# a job-list stage: copy the vendored list into STATE, run it resumably, die unless all jobs are DONE
jobs_stage() {   # jobs_stage <listfile> <batchname>
    local L="$1" B="$2"
    if [ "$DRY" = 1 ]; then
        echo "  eval/run_jobs_resumable.sh $L $B $PAR   # $(grep -cv -E '^\s*(#|$)' "$L") jobs:"
        grep -v -E '^\s*(#|$)' "$L" | sed 's/^/    job: /'
        return 0
    fi
    [ -e "$HOME/thesis_data/batches/$B" ] && [ ! -f "$STATE/$B.started" ] && die "batch dir $B exists but was not started by this pipeline"
    touch "$STATE/$B.started"
    eval/run_jobs_resumable.sh "$L" "$B" "$PAR" > "$STATE/$B.txt" 2>&1 || die "$B runner"
    [ -f "$HOME/thesis_data/batches/$B/DONE" ] || die "$B: not all jobs DONE (see ~/thesis_data/batches/$B/FAILED)"
}

# ---- packed bags (tools/bag_pack.sh, ruling 2026-10-08): most corridor / f4 / cl bags are stored as bag_0.db3.zst and
# cannot be read until unpacked. Unpack = tools/bag_pack.sh unpack (sha256-verified against PACKED.txt). Repack is done
# HERE, not with `bag_pack.sh pack` (whose sha-mismatch branch deletes the .zst): the restored .db3 is removed ONLY if its
# sha256 equals PACKED.txt's and the .zst is present; otherwise both are kept and a warning is logged.
bag_db() { local b="$TD/$1/bag"; ls "$b"/*.db3 2>/dev/null | head -1; }
unpack_trials() {   # unpack_trials T... : unpack every packed bag among T (skip unpacked ones); disk-space guarded
    local need=0 t m
    for t in "$@"; do m="$TD/$t/bag/PACKED.txt"; [ -f "$m" ] && [ -z "$(bag_db "$t")" ] && need=$((need + $(awk '/^size/{print $2}' "$m"))); done
    if [ "$DRY" = 1 ]; then echo "  unpack (tools/bag_pack.sh unpack) $# trials, $((need / 1000000000)) GB to restore"; return 0; fi
    local free; free=$(df -B1 --output=avail "$TD" | tail -1)
    [ "$free" -gt $((need + 40000000000)) ] || die "unpack: needs $((need / 1000000000)) GB + 40 GB margin, only $((free / 1000000000)) GB free"
    for t in "$@"; do
        [ -f "$TD/$t/bag/PACKED.txt" ] || continue
        tools/bag_pack.sh unpack "$TD/$t" >> "$STATE/bags.log" 2>&1 || die "unpack $t"
        echo "$t" >> "$STATE/unpacked.txt"
    done
}
repack_trials() {   # repack_trials T... : remove a restored .db3 only if it matches PACKED.txt's sha256 and the .zst exists
    local t db want got
    if [ "$DRY" = 1 ]; then echo "  repack (verify sha256 vs PACKED.txt, then remove the restored .db3) $# trials"; return 0; fi
    for t in "$@"; do
        [ -f "$TD/$t/bag/PACKED.txt" ] || continue
        db=$(bag_db "$t"); [ -n "$db" ] || continue
        [ -f "$db.zst" ] || { log "WARN repack $t: no $db.zst; .db3 kept"; continue; }
        want=$(awk '/^sha256/{print $2}' "$TD/$t/bag/PACKED.txt"); got=$(sha256sum "$db" | cut -d' ' -f1)
        if [ "$want" = "$got" ]; then rm -f "$db" && echo "REPACKED $t" >> "$STATE/bags.log"; else log "WARN repack $t: sha256 differs from PACKED.txt; BOTH kept"; fi
    done
}

set_of() { local p="$1"; for r in 1 2 3; do for w in tex trans blank; do echo "${p}_${w}_r$r"; done; done; }
P1C=(p1c_fwdc_tex p1c_fwdplainc_tex p1c_fwdc_trans p1c_fwdplainc_trans p1c_fwdc_blank p1c_fwdplainc_blank)
DSN=($(set_of dsn)); FWDC=($(set_of fwdc)); FWDPC=($(set_of fwdplainc))
EXTRA=(dsn_tex_r4 dsn_tex_r5 dsn_tex_r6 dsn_tex_r7 dsn_tex_r8 dsn_tex_r9 dsn_tex_r10)
F4=(f4_fwdc_tex_r1 f4_fwdc_tex_r2 f4_fwdc_tex_r3 f4_fwdc_tex_r4 f4_fwdc_tex_r5 f4_fwdc_tex_r6
    f4_fwdplainc_tex_r1 f4_fwdplainc_tex_r2 f4_fwdplainc_tex_r3 f4_fwdplainc_tex_r4 f4_fwdplainc_tex_r5 f4_fwdplainc_tex_r6)
# the 10 usable 2(a) flights in the order of the committed run (~/thesis_data/batches/f4_eval.txt; --trials was not recorded)
F4_USABLE=(f4_fwdplainc_tex_r1 f4_fwdplainc_tex_r2 f4_fwdc_tex_r2 f4_fwdc_tex_r3 f4_fwdplainc_tex_r4 f4_fwdc_tex_r4
           f4_fwdplainc_tex_r5 f4_fwdc_tex_r5 f4_fwdplainc_tex_r6 f4_fwdc_tex_r6)
T_TRIALS=(); for c in A B C D; do for r in 1 2 3; do T_TRIALS+=("T_${c}_r$r"); done; done
O_TRIALS=(O_r1 O_r2 O_r3b)
L_TRIALS=(T_A_r1 T_A_r2 T_A_r3)
H_SHADOW=(H_s1_r1 H_s1_r2 H_s1_r3 H_s1far_r1 H_s1far_r2 H_s1far_r3b)   # H_s1far_r3 EXCLUDED (IMU-gap rule: unusable)
EVO_SETS=(rerun_dsn dsn_extra rerun_p1c rerun_fwdc rerun_fwdplainc)
[ "$DRY" = 0 ] && rm -f "$STATE/FAILED"

# ---------------------------------------------------------------------------------------------------------------------
# 0. PREFLIGHT: no flight; provenance (git SHA, md5 of every estimator source + the installed C++ binaries); the four
#    corrections present; no diagnostic env switch set; tracked tree clean; vendored job lists present; every trial
#    the stages replay has an imu_gaps.json (imu_gap_check --write is run for the sets that run_set_eval does not cover).
if stage preflight; then
    for v in UKF_APIN FGO_BAG_ROOT FGO_OUT_ROOT FGO_DUMP_EVENTS UKF_DUMP FGO_COV_LOG F_TAG ROOM_TAG_SIGMA_POS; do
        [ -n "${!v:-}" ] && die "diagnostic/arm env $v is set in the pipeline environment ($v=${!v})"
    done
    if [ "$DRY" = 1 ]; then
        python3 eval/final_rerun_checks.py provenance | sed 's/^/  /'
        python3 eval/final_rerun_checks.py corrections | sed 's/^/  /' || log "corrections check FAILS NOW (expected until the derotation change lands): the real run would DIE here"
    else
        python3 eval/final_rerun_checks.py provenance > "$STATE/provenance.txt" 2>&1 || die provenance
        cat "$STATE/provenance.txt" >> "$STATE/pipeline.log"
        python3 eval/final_rerun_checks.py corrections > "$STATE/corrections.txt" 2>&1 || { cat "$STATE/corrections.txt"; die "corrections not all present"; }
        cat "$STATE/corrections.txt" >> "$STATE/pipeline.log"
        [ -z "$(git status --porcelain --untracked-files=no)" ] || die "tracked files modified: commit first (provenance must be a commit)"
    fi
    for f in "$JOBS_DIR"/{F,room_H,room_O,room_T,L,cl_pred}.jobs batches/phase4_replays.jobs batches/f4_replays_usable.jobs batches/phase5b_replays.jobs; do [ -f "$f" ] || die "missing $f"; done
    # IMU-gap rule: every replayed trial must already carry imu_gaps.json (written by eval/imu_gap_check.py --write; the
    # dsn / forward sets are re-checked by run_set_eval.sh itself). Packed bags cannot be re-checked here, so presence and
    # the verdict are verified instead: an "unusable" trial in a replay list is fatal.
    for t in "${F4_USABLE[@]}" "${T_TRIALS[@]}" "${O_TRIALS[@]}" "${H_SHADOW[@]}"; do
        g="$TD/$t/imu_gaps.json"
        [ -f "$g" ] || { [ "$DRY" = 1 ] && { log "MISSING imu_gaps.json: $t (real run would die)"; continue; }; die "no imu_gaps.json for $t"; }
        v=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['verdict'])" "$g")
        [ "$v" = unusable ] && die "IMU-gap rule: $t is unusable but is in a replay list"
        [ "$DRY" = 1 ] && echo "  imu_gaps $t: $v"
    done
    done_ preflight
fi

# 1. SNAPSHOT (results) and ARCHIVE (every trial's existing UKF/FGO outputs: the old numbers AND the labelled
#    "noise fix only (yaw cap ungated)" ablation outputs). Both DIE if the target exists.
if stage snapshot; then
    need preflight
    [ -e "$OLD" ] && die "snapshot target $OLD already exists (refusing to skip or overwrite)"
    [ -e "$ARCH" ] && die "archive target $ARCH already exists (refusing to skip or overwrite)"
    run cp -a "$RES" "$OLD" || die "snapshot results"
    if [ "$DRY" = 1 ]; then
        echo "  for every ~/thesis_data/trials/<t>: cp -a <t>/{ukf*,fgo*,room_*,lc_fgo_*} $ARCH/<t>/   ($(ls -d "$TD"/*/ukf* "$TD"/*/fgo* "$TD"/*/room_* "$TD"/*/lc_fgo_* 2>/dev/null | wc -l) dirs)"
        echo "  cp -a ~/thesis_data/phase5b_d15 ~/thesis_data/batches/eval_{${EVO_SETS[*]}} $ARCH/_aux/"
    else
        mkdir -p "$ARCH" || die "archive mkdir"
        n=0
        for d in "$TD"/*/; do
            t=$(basename "$d")
            for s in "$d"ukf* "$d"fgo* "$d"room_* "$d"lc_fgo_*; do
                [ -e "$s" ] || continue
                mkdir -p "$ARCH/$t" && cp -a "$s" "$ARCH/$t/" || die "archive $t/$(basename "$s")"; n=$((n + 1))
            done
        done
        mkdir -p "$ARCH/_aux"
        [ -d "$HOME/thesis_data/phase5b_d15" ] && { cp -a "$HOME/thesis_data/phase5b_d15" "$ARCH/_aux/" || die "archive phase5b_d15"; }
        for e in "${EVO_SETS[@]}"; do [ -d "$HOME/thesis_data/batches/eval_$e" ] && { cp -a "$HOME/thesis_data/batches/eval_$e" "$ARCH/_aux/" || die "archive eval_$e"; }; done
        log "archived $n output dirs to $ARCH"
        ( cd "$ARCH" && find . -type f -print0 | sort -z | xargs -0 md5sum ) > "$STATE/archive_md5.txt" || die "archive md5"
    fi
    done_ snapshot
fi

# 1b. Unpack the corridor bags used by the dsn / forward sets / Phase 4 / 5b / D15 / F stages (~79 GB restored).
if stage unpack; then
    need snapshot
    unpack_trials "${DSN[@]}" "${EXTRA[@]}" "${P1C[@]}" "${FWDC[@]}" "${FWDPC[@]}"
    done_ unpack
fi

# 2. dsn r1-r3 (IMU-gap rule, UKF/FGO replays, timing, flow quality, three-way evo, score), then the HARD EKF3 GATE.
if stage dsn; then
    need snapshot
    runlog "$STATE/dsn.txt" eval/run_set_eval.sh rerun_dsn "${DSN[@]}" || die "dsn set eval"
    runlog "$STATE/gate_dsn.txt" python3 eval/final_rerun_checks.py ekf3-gate \
        "$OLD/rerun_dsn_evo.json" "$RES/rerun_dsn_evo.json" \
        "$OLD/input_timing_rerun_dsn.json" "$RES/input_timing_rerun_dsn.json" \
        "$OLD/flow_quality_rerun_dsn.json" "$RES/flow_quality_rerun_dsn.json" \
        || { [ "$DRY" = 1 ] || cat "$STATE/gate_dsn.txt"; die "HARD GATE: an EKF3 entry changed in the dsn stage"; }
    run cp "$RES/rerun_dsn_evo.json" "$RES/dsn_dejitter_baseline.json" || die "dsn refs"
    done_ dsn
fi
if stage dsn_extra; then
    need dsn
    runlog "$STATE/dsn_extra.txt" eval/run_set_eval.sh dsn_extra "${EXTRA[@]}" || die "dsn_extra set eval"
    runlog "$STATE/gate_dsn_extra.txt" python3 eval/final_rerun_checks.py ekf3-gate "$OLD/dsn_extra_evo.json" "$RES/dsn_extra_evo.json" \
        || die "HARD GATE: an EKF3 entry changed in dsn_extra"
    done_ dsn_extra
fi

# 3. P4 bands from the corrected dsn (pre-registered formula; as D15). Exported for every later scoring step.
if stage bands; then
    need dsn
    runlog "$STATE/bands.txt" python3 eval/rerun_bands.py "$RES/rerun_dsn_evo.json" --json "$RES/rerun_p4_bands.json" || die bands
    done_ bands
fi
export P4_BANDS="$RES/rerun_p4_bands.json"

# 4. The confirmatory EKF3-vs-FGO test: the pre-registered script UNCHANGED, original decision rule (ruling item 5).
if stage paired; then
    need dsn dsn_extra
    runlog "$STATE/paired.txt" python3 eval/dsn_paired_test.py "$RES/rerun_dsn_evo.json" "$RES/dsn_extra_evo.json" --json "$RES/dsn_paired_test.json" || die paired
    done_ paired
fi

# 5. Forward-camera sets (replays + P1-P4 scoring with the recomputed bands); EKF3 gated as for dsn.
for s in p1c fwdc fwdplainc; do
    if stage "set_$s"; then
        need bands
        case $s in p1c) T=("${P1C[@]}");; fwdc) T=("${FWDC[@]}");; fwdplainc) T=("${FWDPC[@]}");; esac
        runlog "$STATE/set_$s.txt" eval/run_set_eval.sh "rerun_$s" "${T[@]}" || die "set eval $s"
        runlog "$STATE/gate_set_$s.txt" python3 eval/final_rerun_checks.py ekf3-gate "$OLD/rerun_${s}_evo.json" "$RES/rerun_${s}_evo.json" \
            || die "HARD GATE: an EKF3 entry changed in set $s"
        done_ "set_$s"
    fi
done

# 6. Phase 4 arms (pre-registered job list, unchanged) and evaluation; C0 is read from these outputs.
if stage phase4; then
    need set_fwdc set_fwdplainc
    jobs_stage batches/phase4_replays.jobs final_phase4
    runlog "$STATE/phase4_eval.txt" "$EVO" eval/phase4_eval.py fwdc fwdplainc || die "phase4 eval"
    runlog "$STATE/gate_phase4.txt" python3 eval/final_rerun_checks.py ekf3-gate \
        "$OLD/phase4_fwdc_evo.json" "$RES/phase4_fwdc_evo.json" "$OLD/phase4_fwdplainc_evo.json" "$RES/phase4_fwdplainc_evo.json" \
        || die "HARD GATE: an EKF3 entry changed in Phase 4"
    done_ phase4
fi

# 7. Phase 5, the distance-scale check, the heading-share restatement.
if stage phase5; then
    need phase4
    runlog "$STATE/phase5.txt" "$AP" eval/phase5_analysis.py --json "$RES/phase5_analysis.json" || die phase5
    runlog "$STATE/scale.txt" "$EVO" eval/scale_check.py --json "$RES/scale_check.json" || die scale
    runlog "$STATE/heading_share.txt" "$AP" eval/heading_share.py "$RES/rerun_dsn_evo.json" --json "$RES/heading_share_restated.json" || die heading_share
    done_ phase5
fi

# 8. Phase 5b: a FRESH sandbox (phase5b_final), instrumented replays, then consistency.
if stage phase5b; then
    need phase4
    SBH="$HOME/thesis_data/phase5b_final/home"
    [ "$DRY" = 0 ] && [ -e "$SBH" ] && [ ! -f "$STATE/final_phase5b.started" ] && die "sandbox $SBH exists but was not built by this pipeline"
    runlog "$STATE/phase5b_build.txt" eval/build_5b_sandbox.sh "$SBH" "$STATE/phase5b.jobs" || die "5b sandbox"
    if [ "$DRY" = 1 ]; then
        echo "  (jobs = batches/phase5b_replays.jobs with $HOME/thesis_data/phase5b/home -> $SBH; $(grep -cv '^#' batches/phase5b_replays.jobs) jobs)"
        echo "  eval/run_jobs_resumable.sh $STATE/phase5b_clean.jobs final_phase5b $PAR"
    else
        grep -v "^#" "$STATE/phase5b.jobs" > "$STATE/phase5b_clean.jobs"
        jobs_stage "$STATE/phase5b_clean.jobs" final_phase5b
    fi
    PHASE5B_SB="$SBH/thesis_data/trials" runlog "$STATE/phase5b.txt" "$AP" eval/phase5b_consistency.py --json "$RES/phase5b_consistency.json" || die 5b
    done_ phase5b
fi

# 9. D15 take-off kick and drift, the RTF check, blank behaviour (all arms regenerated; d27_regen.sh replaced only the
#    UKF fields because the FGO was unchanged then; now both change, so the whole file is regenerated).
if stage d15_bb; then
    need dsn dsn_extra set_p1c set_fwdc set_fwdplainc phase4
    runlog "$STATE/kick.txt" "$AP" eval/d15_kick.py dsn_tex_r{1,2,3,4,5,6,7,8,9,10} --json "$RES/d15_kick.json" || die kick
    runlog "$STATE/drift.txt" "$AP" eval/d15_drift.py dsn_tex_r{1,2,3,4,5,6,7,8,9,10} dsn_trans_r{1,2,3} --json "$RES/d15_drift.json" || die drift
    runlog "$STATE/rtf.txt" python3 eval/rtf_drift_check.py --json "$RES/rtf_drift_check.json" || die rtf
    PYTHONPATH="$SHIM" runlog "$STATE/bb_plain.txt" "$EVO" eval/blank_behaviour.py dsn_blank_r{1,2,3} dsn_trans_r{1,2,3} p1c_fwdc_blank p1c_fwdc_trans p1c_fwdplainc_blank p1c_fwdplainc_trans \
        --arms ukf,fgo --json "$STATE/bb_plain.json" || die bb_plain
    PYTHONPATH="$SHIM" runlog "$STATE/bb_arms.txt" "$EVO" eval/blank_behaviour.py fwdc_blank_r{1,2,3} fwdc_trans_r{1,2,3} fwdplainc_blank_r{1,2,3} fwdplainc_trans_r{1,2,3} \
        --arms ukf_baseline,fgo_baseline,ukf_heading,fgo_heading --json "$STATE/bb_arms.json" || die bb_arms
    runlog "$STATE/bb_merge.txt" python3 eval/final_rerun_merge_bb.py "$OLD/blank_behaviour.json" "$STATE/bb_plain.json" "$STATE/bb_arms.json" "$RES/blank_behaviour.json" || die bb_merge
    done_ d15_bb
fi

# 10. F-tests: F1 (robust, k = 2.385 fixed by the original calibration), F2, F3, F3b, F3c, and the C0/F2-pattern run
#     PATnocap; UKF and FGO arms of each (batches/final_rerun/F.jobs), then the pre-registered evaluators.
if stage ftests; then
    need set_fwdc set_fwdplainc phase4
    jobs_stage "$JOBS_DIR/F.jobs" final_F
    runlog "$STATE/f1.txt" "$FGOP" eval/f1_eval.py test cauchy:2.385 --json "$RES/f1_test.json" || die f1
    runlog "$STATE/f2.txt" "$FGOP" eval/f23_eval.py f2 --json "$RES/f2_test.json" || die f2
    runlog "$STATE/f3.txt" "$FGOP" eval/f23_eval.py f3 --json "$RES/f3_test.json" || die f3
    runlog "$STATE/f3b.txt" "$FGOP" eval/f3b_eval.py --json "$RES/f3b_test.json" || die f3b
    runlog "$STATE/f3c.txt" "$FGOP" eval/f3c_eval.py --tag F3cd --deltas 10,30 --json "$RES/f3c_test.json" || die f3c
    done_ ftests
fi

# 10b. Repack the corridor bags (their last reader is the ftests stage; L unpacks dsn_tex_r1 again for V-L).
if stage repack_corridor; then
    need ftests d15_bb phase5b
    repack_trials "${DSN[@]}" "${EXTRA[@]}" "${P1C[@]}" "${FWDC[@]}" "${FWDPC[@]}"
    done_ repack_corridor
fi

# 11. Plan step 2(a) (F4): the three arms on the 10 usable fresh flights (batches/f4_replays_usable.jobs, unchanged), then
#     f4_eval (P1/S1/S2 as registered; the 2 IMU-gap exclusions count against, as recorded).
if stage f4; then
    need snapshot
    unpack_trials "${F4[@]}"
    jobs_stage batches/f4_replays_usable.jobs final_f4
    runlog "$STATE/f4_eval.txt" "$FGOP" eval/f4_eval.py test cauchy:2.385 --trials "$(IFS=,; echo "${F4_USABLE[*]}")" --json "$RES/f4_test.json" || die f4_eval
    repack_trials "${F4[@]}"
    done_ f4
fi

# 12. Experiment H offline shadows (S1 original + S1 far re-fly, incl. the NEW r3b shadows), then h_score.py as for the
#     committed results (sigma 0.02; S1 profile / S1-far profile).
if stage h_shadows; then
    need snapshot
    unpack_trials "${H_SHADOW[@]}"                # no-op unless they have been packed since 2026-10-09
    jobs_stage "$JOBS_DIR/room_H.jobs" final_room_H
    for r in 1 2 3; do
        runlog "$STATE/h_s1_r$r.txt" "$TAGS" eval/h_score.py "H_s1_r$r" --profile batches/expH/s1_profile.json --sigma 0.02 --json "$RES/expH/s1_r$r.json" || die "h_score H_s1_r$r"
    done
    for r in 1 2 3b; do
        runlog "$STATE/h_s1far_r$r.txt" "$TAGS" eval/h_score.py "H_s1far_r$r" --profile batches/expH/s1_far_profile.json --sigma 0.02 --json "$RES/expH/s1far_r$r.json" || die "h_score H_s1far_r$r"
    done
    G=(); for f in s1_r1 s1_r2 s1_r3 s1far_r1 s1far_r2; do G+=("$OLD/expH/$f.json" "$RES/expH/$f.json"); done
    runlog "$STATE/gate_h.txt" python3 eval/final_rerun_checks.py ekf3-gate "${G[@]}" || die "HARD GATE: an EKF3 entry changed in the H scores"
    done_ h_shadows
fi

# 13. Experiment O (GNSS; RTS-UKF and its cap-free check; FGO live + batch), then o_score.py.
if stage expO; then
    need snapshot
    unpack_trials "${O_TRIALS[@]}"                # no-op unless they have been packed since 2026-10-09
    jobs_stage "$JOBS_DIR/room_O.jobs" final_room_O
    for t in "${O_TRIALS[@]}"; do runlog "$STATE/o_$t.txt" "$TAGS" eval/o_score.py "$t" --json "$RES/expO/$t.json" || die "o_score $t"; done
    G=(); for t in "${O_TRIALS[@]}"; do G+=("$OLD/expO/$t.json" "$RES/expO/$t.json"); done
    runlog "$STATE/gate_o.txt" python3 eval/final_rerun_checks.py ekf3-gate "${G[@]}" || die "HARD GATE: an EKF3 entry changed in O"
    done_ expO
fi

# 14. Experiment T (12 flights; FGO batch ~35 min per flight), then tag_score.py and t_aggregate.py.
if stage expT; then
    need snapshot
    unpack_trials "${T_TRIALS[@]}"                # no-op unless they have been packed since 2026-10-09
    jobs_stage "$JOBS_DIR/room_T.jobs" final_room_T
    for t in "${T_TRIALS[@]}"; do runlog "$STATE/t_$t.txt" "$TAGS" eval/tag_score.py "$t" --json "$RES/expT/$t.json" || die "tag_score $t"; done
    runlog "$STATE/t_aggregate.txt" python3 eval/t_aggregate.py --json "$RES/expT/t_aggregate.json" || die t_aggregate
    G=(); for t in "${T_TRIALS[@]}" t_aggregate; do G+=("$OLD/expT/$t.json" "$RES/expT/$t.json"); done
    runlog "$STATE/gate_t.txt" python3 eval/final_rerun_checks.py ekf3-gate "${G[@]}" || die "HARD GATE: an EKF3 entry changed in T"
    done_ expT
fi

# 15. OPT-IN (needs a user ruling; off unless FINAL_D27I3=1): the D27 item 3 / D26 FGO heading-gate re-measurement with the
#     corrected core (eval/fgo_core_replay.py --save-npz + eval/d26_fgo_gate.py) on the same D26 flights. The UKF side used
#     the port's SITL Replay (not an offline Python replay) and is NOT in this pipeline. The F3 prior-induced lockout is
#     re-measured by f23_eval.py f3 in the ftests stage.
if [ "${FINAL_D27I3:-0}" = 1 ] || [ "$DRY" = 1 ]; then
    if stage d27item3; then
        need ftests
        [ "$DRY" = 1 ] && echo "  # (opt-in: FINAL_D27I3=1)"
        unpack_trials cl_fgo_b_tex_r1_half cl_fgo_b_tex_r3_half
        for t in cl_fgo_b_tex_r1_half cl_fgo_b_tex_r3_half; do
            runlog "$STATE/core_$t.txt" "$FGOP" eval/fgo_core_replay.py "$t" --save-npz || die "fgo_core_replay $t"
            runlog "$STATE/d26gate_$t.txt" "$FGOP" eval/d26_fgo_gate.py "$t" || die "d26_fgo_gate $t"
        done
        repack_trials cl_fgo_b_tex_r1_half cl_fgo_b_tex_r3_half
        done_ d27item3
    fi
fi

# 16. OPT-IN (needs a user ruling; off unless FINAL_CL_PRED=1): the offline FGO no-heading contact prediction input
#     (batches/fgo_half_pred.jobs) with the corrected FGO, written to a NEW file (the pre-registered bands are not touched).
if [ "${FINAL_CL_PRED:-0}" = 1 ] || [ "$DRY" = 1 ]; then
    if stage cl_pred; then
        need snapshot
        [ "$DRY" = 1 ] && echo "  # (opt-in: FINAL_CL_PRED=1)"
        CLP=(cl_a_tex_half cl_bcpp_tex_r{1,2,3}_half cl_ukf_a_tex_half cl_ukf_b_tex_r{1,2,3}_half)
        unpack_trials "${CLP[@]}"
        runlog "$STATE/cl_gaps.txt" "$EVO" eval/imu_gap_check.py "${CLP[@]}" --write || die "cl imu gaps"   # no imu_gaps.json yet
        jobs_stage "$JOBS_DIR/cl_pred.jobs" final_cl_pred
        PYTHONPATH="$SHIM" runlog "$STATE/cl_pred.txt" "$EVO" eval/fgo_contact_prediction.py cl_a_tex_half cl_bcpp_tex_r{1,2,3}_half cl_ukf_a_tex_half cl_ukf_b_tex_r{1,2,3}_half \
            --json "$RES/fgo_contact_prediction_half_final.json" || die cl_pred
        repack_trials "${CLP[@]}"
        done_ cl_pred
    fi
fi

# 17. L LAST (its cost): keyframe FGO with/without loop closure on T_A_r1..r3, cut at anchor + 245 s (the recorded deviation),
#     plus the V-L replay on dsn_tex_r1 (no tags); then l_score.py. V-L scoring: see the handover (labels not recorded).
if stage L; then
    need expT
    unpack_trials dsn_tex_r1 "${L_TRIALS[@]}"    # the V-L job; T_A_* are not packed (no-op)
    jobs_stage "$JOBS_DIR/L.jobs" final_L
    repack_trials dsn_tex_r1
    for t in "${L_TRIALS[@]}"; do runlog "$STATE/l_$t.txt" "$TAGS" eval/l_score.py "$t" --suffix _t245 --json "$RES/expL/${t}_t245.json" || die "l_score $t"; done
    done_ L
fi

# 18. Old against new (light): the corridor headline comparison of the consolidated re-run (eval/rerun_compare.py: numbers.md
#     sections 6-9, Phase 4/5/5b, scale, heading share). T/O/L/H/F/2(a) old-vs-new rows are NOT covered by it (handover gap).
if stage compare; then
    need L
    repack_trials "${DSN[@]}" "${EXTRA[@]}" "${P1C[@]}" "${FWDC[@]}" "${FWDPC[@]}" "${F4[@]}"   # idempotent safety net
    runlog "$STATE/compare.txt" python3 eval/rerun_compare.py "$OLD" "$RES" --md "$STATE/final_old_vs_new.md" --json "$RES/final_old_vs_new.json" || die compare
    done_ compare
fi

if [ -z "$ONLY" ]; then log "PIPELINE COMPLETE"; [ "$DRY" = 1 ] || touch "$STATE/COMPLETE"; fi
