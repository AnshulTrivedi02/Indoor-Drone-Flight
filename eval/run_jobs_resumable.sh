#!/usr/bin/env bash
# Crash-safe, resumable parallel job runner for offline replays (Phase 4 onwards).
#
# Usage: eval/run_jobs_resumable.sh <jobs_file> <batch_name> [parallel=4]
#
# jobs_file: one job per line, "<job_id> <command...>" (# comments and blank lines
# ignored). A job is DONE iff ~/thesis_data/batches/<batch>/done/<job_id> exists; it is
# written only after the command exits 0. Re-running the same command after a crash or
# kill skips DONE jobs and re-runs every other one from scratch (outputs are derived
# data, so an interrupted job is simply redone). State:
#   jobs.log   append-only START / DONE / FAILED lines, synced to disk after each line
#   logs/      per-job stdout/stderr
#   DONE       written when every job is done; FAILED lists the jobs that failed
set -uo pipefail
[ $# -ge 2 ] || { echo "Usage: $0 <jobs_file> <batch_name> [parallel]" >&2; exit 1; }
JOBS="$1"; NAME="$2"; PAR="${3:-4}"
ST="$HOME/thesis_data/batches/$NAME"; mkdir -p "$ST/done" "$ST/logs"
exec 9> "$ST/.lock"; flock -n 9 || { echo "ERROR: batch '$NAME' already running" >&2; exit 1; }
LOG="$ST/jobs.log"
ts() { date +%Y-%m-%dT%H:%M:%S%z; }
export ST LOG
echo "$(ts)  BEGIN    jobs=$JOBS parallel=$PAR commit=$(git -C "$(dirname "$0")/.." rev-parse --short HEAD)" >> "$LOG"; sync "$LOG"
rm -f "$ST/FAILED"

run_one() {
    local id="$1"; shift
    [ -f "$ST/done/$id" ] && return 0
    echo "$(date +%Y-%m-%dT%H:%M:%S%z)  START    $id" >> "$LOG"; sync "$LOG"
    local s=$SECONDS
    bash -c "$*" > "$ST/logs/$id.log" 2>&1
    local rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "$(date +%Y-%m-%dT%H:%M:%S%z)  DONE     $id  wall=$((SECONDS - s))s" >> "$LOG"
        touch "$ST/done/$id"; sync "$LOG" "$ST/done/$id"
    else
        echo "$(date +%Y-%m-%dT%H:%M:%S%z)  FAILED   $id  rc=$rc  wall=$((SECONDS - s))s" >> "$LOG"; sync "$LOG"
        echo "$id" >> "$ST/FAILED"
    fi
}
export -f run_one

grep -v -E '^\s*(#|$)' "$JOBS" | xargs -P "$PAR" -L 1 bash -c 'run_one "$@"' _

total=$(grep -c -v -E '^\s*(#|$)' "$JOBS"); done_n=$(ls "$ST/done" | wc -l)
if [ "$done_n" -ge "$total" ] && [ ! -f "$ST/FAILED" ]; then
    echo "$(ts)  DONE     all $done_n/$total jobs" >> "$LOG"; echo "DONE $(ts) $done_n/$total" > "$ST/DONE"
else
    echo "$(ts)  STOPPED  $done_n/$total done" >> "$LOG"
fi
sync "$LOG"
