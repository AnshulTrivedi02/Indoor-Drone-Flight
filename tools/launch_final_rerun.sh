#!/usr/bin/env bash
# Launcher for the FINAL consolidated offline re-run (eval/final_rerun_pipeline.sh). WRITTEN, NOT LAUNCHED (2026-10-09).
#
# Each stage is ONE tools/heavy.py invocation (src/estimators/fgo_cpp/tools/heavy.py, ruling 2026-10-08: "one invocation =
# one bounded step, so the lock is released between steps"):
#   python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "final_rerun <stage>" -- ~/thesis_ws/eval/final_rerun_pipeline.sh --only <stage>
# heavy.py waits (up to 6 h) while FLIGHT_LOCK exists or arducopter / gz sim runs, then holds BUILD_LOCK for that stage only,
# so a flight can take the machine BETWEEN stages (flight_lock_acquire waits up to 1 h for BUILD_LOCK). The pipeline itself
# re-checks for a flight before the stage and dies if one is running. Stages already .done are skipped. The launcher stops at
# the first failing stage; re-running this file resumes.
#
# Run from a tmux session, in the MAIN checkout (~/thesis_ws) after this branch is merged and the derotation change has landed:
#   tmux new -s final_rerun 'bash ~/thesis_ws/tools/launch_final_rerun.sh 2>&1 | tee -a ~/thesis_data/batches/final_rerun_console.log'
# Opt-in stages (need a user ruling first): FINAL_D27I3=1 (D27 item 3 heading-gate re-measurement), FINAL_CL_PRED=1
# (offline closed-loop prediction input). Single-shot alternative (holds BUILD_LOCK for the whole run, ~10-12 h; blocks
# flights): python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "final_rerun all" -- ~/thesis_ws/eval/final_rerun_pipeline.sh
set -uo pipefail
TW="$HOME/thesis_ws"
HEAVY="$TW/src/estimators/fgo_cpp/tools/heavy.py"
PIPE="$TW/eval/final_rerun_pipeline.sh"
# FGO-only pass (ruling 2026-10-10 item 3): FINAL_FGO_ONLY=1 (exported, so the pipeline sees it) -> state final_rerun2.
# Labelled sensitivity check: FINAL_SENS_YAW0=1 adds stage sens_yaw0 after ftests.
export FINAL_FGO_ONLY="${FINAL_FGO_ONLY:-0}" FINAL_SENS_YAW0="${FINAL_SENS_YAW0:-0}"
if [ "$FINAL_FGO_ONLY" = 1 ]; then STATE="$HOME/thesis_data/batches/final_rerun2"; else STATE="$HOME/thesis_data/batches/final_rerun"; fi
STAGES=(preflight snapshot unpack dsn dsn_extra sens bands paired set_p1c set_fwdc set_fwdplainc phase4 phase5 phase5b d15_bb ftests)
[ "$FINAL_SENS_YAW0" = 1 ] && STAGES+=(sens_yaw0)
STAGES+=(repack_corridor f4 h_shadows expO expT)
[ "${FINAL_D27I3:-0}" = 1 ] && STAGES+=(d27item3)
[ "${FINAL_CL_PRED:-0}" = 1 ] && STAGES+=(cl_pred)
STAGES+=(L compare)                           # L LAST of the replays (ruled: its cost); compare is light
[ "$(git -C "$TW" rev-parse --abbrev-ref HEAD)" != "" ] || { echo "not a git checkout: $TW" >&2; exit 1; }
for s in "${STAGES[@]}"; do
    if [ -f "$STATE/$s.done" ]; then echo "$(date +%FT%T) launcher: $s already done"; continue; fi
    echo "$(date +%FT%T) launcher: submitting $s"
    python3 "$HEAVY" "final_rerun $s" -- "$PIPE" --only "$s"
    rc=$?
    if [ "$rc" -ne 0 ] || [ ! -f "$STATE/$s.done" ]; then
        echo "$(date +%FT%T) launcher: stage $s FAILED or blocked (rc=$rc); stopping. See $STATE/pipeline.log"; exit 1
    fi
done
echo "$(date +%FT%T) launcher: all stages done"; touch "$STATE/COMPLETE"
