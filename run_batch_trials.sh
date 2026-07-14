#!/usr/bin/env bash
# Unattended batch trial runner — reads a list of trials from a config file
# and calls run_trial.sh for each, back-to-back, with no manual intervention.
#
# Each trial is fully independent: run_trial.sh's own cleanup trap tears
# down its entire stack (Gazebo, SITL, MAVProxy, bridges, recorder) before
# returning, so trials never overlap. A trial that fails is logged and the
# batch continues to the next row — one bad trial must not abort the rest
# of an unattended, potentially hours-long batch.
#
# Usage:
#   ./run_batch_trials.sh <config_file>
#
# Config file format: one trial per line, whitespace-separated fields:
#   <world> <velocity> <altitude> <duration> [trial_name]
#
# duration is cruise duration in SIM SECONDS (not wall-clock). trial_name
# is optional — omit it to let run_trial.sh auto-increment (trial_001, ...).
# Blank lines and lines starting with # are ignored.
#
# Example config:
#   # world          velocity  altitude  duration  trial_name
#   iris_textured    0.4       2.0       30         nominal_v04
#   iris_textured    0.8       2.0       30         nominal_v08
#   iris_runway      0.4       2.0       30         degraded_v04
#
# Output: each trial's own ~/thesis_data/trials/<trial_name>/ (see
# run_trial.sh), plus a batch summary printed at the end of this run.

set -uo pipefail
# Deliberately NOT set -e: a failing trial must not abort the batch.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <config_file>" >&2
    exit 1
fi

CONFIG_FILE="$1"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE" >&2
    exit 1
fi

declare -a RESULT_NAMES=()
declare -a RESULT_STATUS=()
declare -a RESULT_CODES=()
TOTAL=0
PASS_COUNT=0
FAIL_COUNT=0

echo "=== Batch run: $CONFIG_FILE ==="
echo ""

line_no=0
while IFS= read -r line || [ -n "$line" ]; do
    line_no=$((line_no + 1))

    # Strip comments and surrounding whitespace; skip blank lines.
    trimmed="$(echo "$line" | sed 's/#.*//' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [ -z "$trimmed" ] && continue

    read -r world velocity altitude duration trial_name <<< "$trimmed"

    if [ -z "$world" ] || [ -z "$velocity" ] || [ -z "$altitude" ] || [ -z "$duration" ]; then
        echo "ERROR: config line $line_no malformed, skipping: $line" >&2
        TOTAL=$((TOTAL + 1))
        RESULT_NAMES+=("<line $line_no>")
        RESULT_STATUS+=("SKIPPED")
        RESULT_CODES+=("-")
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi

    TOTAL=$((TOTAL + 1))
    echo "--- Trial $TOTAL (config line $line_no) ---"
    echo "World: $world  Velocity: $velocity m/s  Altitude: $altitude m  Duration: $duration sim-s  Name: ${trial_name:-<auto>}"

    args=(--world "$world" --velocity "$velocity" --altitude "$altitude" --duration "$duration")
    [ -n "${trial_name:-}" ] && args+=(--trial-name "$trial_name")

    "$SCRIPT_DIR/run_trial.sh" "${args[@]}"
    status=$?

    resolved_name="$trial_name"
    if [ -z "$resolved_name" ]; then
        # run_trial.sh auto-incremented; recover the name it picked from
        # the newest trial_NNN directory so the summary can report it.
        resolved_name="$(ls -1dt "$HOME/thesis_data/trials"/trial_[0-9][0-9][0-9] 2>/dev/null | head -1 | xargs -r basename)"
        [ -z "$resolved_name" ] && resolved_name="<unknown>"
    fi

    RESULT_NAMES+=("$resolved_name")
    RESULT_CODES+=("$status")
    if [ "$status" -eq 0 ]; then
        echo "--- Trial $TOTAL ('$resolved_name') PASSED ---"
        RESULT_STATUS+=("PASS")
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "--- Trial $TOTAL ('$resolved_name') FAILED (exit $status) — continuing to next trial ---" >&2
        RESULT_STATUS+=("FAIL")
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    echo ""
done < "$CONFIG_FILE"

echo "=== Batch complete: $PASS_COUNT/$TOTAL passed, $FAIL_COUNT failed ==="
printf '%-24s %-8s %s\n' "TRIAL" "STATUS" "EXIT"
for i in "${!RESULT_NAMES[@]}"; do
    printf '%-24s %-8s %s\n' "${RESULT_NAMES[$i]}" "${RESULT_STATUS[$i]}" "${RESULT_CODES[$i]}"
done

[ "$FAIL_COUNT" -eq 0 ]
