#!/usr/bin/env bash
# Crash-safe, resumable batch runner (Phase 2 onwards). Wraps run_trial.sh.
#
# Written after a kernel panic (USB Wi-Fi dongle, 2026-09-24) froze the machine:
# a batch must survive a hard power-off and resume from the first incomplete
# trial by re-running the SAME command.
#
# Usage:
#   ./run_resumable_batch.sh <config_file> <batch_name>
#
# Config: one trial per line, `<world> <velocity> <altitude> <duration> <trial_name>`
# (trial_name REQUIRED; # comments and blank lines ignored). Order is flight order.
#
# State lives in ~/thesis_data/batches/<batch_name>/:
#   trials.log  append-only, one line per event (START / COMPLETE / ABORTED / FAILED /
#               RESUME / DONE). The ONLY source of truth for "complete": a trial is
#               complete iff trials.log has a COMPLETE line for it.
#   STATUS      one line, overwritten: what the batch is doing right now.
#   DONE        written only when every trial in the config is COMPLETE.
#   FAILED      written if a trial fails twice (the batch stops; nothing is guessed).
#
# Resume rule: a trial directory that exists without a COMPLETE line (a crash, a
# kill, or a failed run) gets ABORTED.txt and is renamed <name>_ABORTED[_N]. Its data
# is kept and never used. The trial is then flown again under its own name.
# A trial that fails in-run is treated the same way and retried ONCE. A second
# failure stops the batch and writes FAILED.
#
# Nothing here touches the network. Every process is local (Gazebo, SITL, MAVProxy
# and ROS 2 on 127.0.0.1 / same-host discovery). Commit and push only after the batch.

set -uo pipefail
# Deliberately NOT set -e: the runner has to record failures, not die on them.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_TRIAL="${RUN_TRIAL:-$SCRIPT_DIR/run_trial.sh}"            # override for dry-run tests only
TRIALS_DIR="${TRIALS_DIR:-$HOME/thesis_data/trials}"          # override for dry-run tests only
BATCHES_DIR="${BATCHES_DIR:-$HOME/thesis_data/batches}"       # override for dry-run tests only
MIN_FREE_GB="${MIN_FREE_GB:-15}"   # a fwd trial is ~3.1 GB; refuse to start below this

if [ $# -ne 2 ]; then
    echo "Usage: $0 <config_file> <batch_name>" >&2
    exit 1
fi
CONFIG_FILE="$1"
BATCH_NAME="$2"
[ -f "$CONFIG_FILE" ] || { echo "ERROR: config not found: $CONFIG_FILE" >&2; exit 1; }

STATE_DIR="$BATCHES_DIR/$BATCH_NAME"
LOG="$STATE_DIR/trials.log"
mkdir -p "$STATE_DIR" "$TRIALS_DIR"

# One runner per batch: a second copy (e.g. started while the first is still in
# tmux) exits instead of flying the same trial twice.
exec 9> "$STATE_DIR/.lock"
if ! flock -n 9; then
    echo "ERROR: batch '$BATCH_NAME' is already running (lock held: $STATE_DIR/.lock)" >&2
    exit 1
fi

ts() { date +%Y-%m-%dT%H:%M:%S%z; }
# sync after every line: a hard power-off must not lose a COMPLETE line (that would
# only cost a re-flight, since resume treats it as incomplete, but it is avoidable).
log_event() { printf '%s  %-8s %s\n' "$(ts)" "$1" "$2" | tee -a "$LOG"; sync "$LOG"; }
set_status() { printf '%s  %s\n' "$(ts)" "$1" > "$STATE_DIR/STATUS"; }

is_complete() { grep -qE "^[^ ]+  COMPLETE +$1( |$)" "$LOG" 2>/dev/null; }

# Rename an incomplete trial dir aside with ABORTED.txt. Never deletes anything.
abort_dir() {
    local name="$1" reason="$2"
    local src="$TRIALS_DIR/$name"
    [ -d "$src" ] || return 0
    cat > "$src/ABORTED.txt" <<EOF
ABORTED — do not use this trial's data.
trial: $name
batch: $BATCH_NAME
marked: $(ts)
reason: $reason
The data is kept, not deleted. The trial was re-flown under its own name.
EOF
    local dst="$TRIALS_DIR/${name}_ABORTED" n=2
    while [ -e "$dst" ]; do dst="$TRIALS_DIR/${name}_ABORTED_$n"; n=$((n + 1)); done
    mv "$src" "$dst"
    log_event ABORTED "$name  reason=\"$reason\"  moved_to=$(basename "$dst")"
}

# Post-run validation, beyond run_trial.sh's exit code: the bag must have been closed
# cleanly (rosbag2 writes bag/metadata.yaml only on a clean stop) and hold every
# expected topic with messages. Prints a reason and returns 1 on failure.
validate_trial() {
    local dir="$TRIALS_DIR/$1" world="$2"
    [ -f "$dir/metadata.yaml" ]     || { echo "no trial metadata.yaml"; return 1; }
    [ -f "$dir/ardupilot.bin" ]     || { echo "no ardupilot.bin"; return 1; }
    [ -f "$dir/bag/metadata.yaml" ] || { echo "bag not closed cleanly (no bag/metadata.yaml)"; return 1; }
    local topics=(/clock /ground_truth/pose /ekf/pose /downward_lidar/range
                  /attitude/angular_rates /imu/data_raw /imu/time_ref /optical_flow/measurement)
    [[ "$world" == *_fwd ]] && topics+=(/forward_camera/image /forward_camera/camera_info)
    python3 - "$dir/bag/metadata.yaml" "${topics[@]}" <<'PYEOF'
import sys, yaml
info = yaml.safe_load(open(sys.argv[1]))["rosbag2_bagfile_information"]
counts = {t["topic_metadata"]["name"]: t["message_count"] for t in info["topics_with_message_count"]}
bad = [t for t in sys.argv[2:] if counts.get(t, 0) == 0]
if bad:
    print("missing or empty topics: " + " ".join(bad)); sys.exit(1)
PYEOF
}

# ── Load config ──────────────────────────────────────────────────────────
declare -a W=() V=() A=() D=() N=()
while IFS= read -r line || [ -n "$line" ]; do
    t="$(echo "$line" | sed 's/#.*//;s/^[[:space:]]*//;s/[[:space:]]*$//')"
    [ -z "$t" ] && continue
    read -r w v a d n extra <<< "$t"
    if [ -z "${n:-}" ] || [ -n "${extra:-}" ]; then
        echo "ERROR: malformed config line (need 5 fields): $line" >&2; exit 1
    fi
    W+=("$w"); V+=("$v"); A+=("$a"); D+=("$d"); N+=("$n")
done < "$CONFIG_FILE"
TOTAL=${#N[@]}
[ "$TOTAL" -gt 0 ] || { echo "ERROR: no trials in $CONFIG_FILE" >&2; exit 1; }

COMMIT="$(git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"
if [ -f "$LOG" ]; then
    log_event RESUME "batch=$BATCH_NAME  commit=$COMMIT  config=$CONFIG_FILE  trials=$TOTAL"
else
    log_event BEGIN "batch=$BATCH_NAME  commit=$COMMIT  config=$CONFIG_FILE  trials=$TOTAL"
fi

# ── Run ──────────────────────────────────────────────────────────────────
for i in "${!N[@]}"; do
    name="${N[$i]}"; k=$((i + 1))
    if is_complete "$name"; then
        echo "[$k/$TOTAL] $name already COMPLETE, skipping"
        continue
    fi
    # Present but not COMPLETE = interrupted (crash/kill) or failed earlier.
    [ -d "$TRIALS_DIR/$name" ] && abort_dir "$name" "found incomplete on batch start/resume (interrupted run: crash, power-off or kill)"

    for attempt in 1 2; do
        # Leftover sim processes would collide on ports with the new trial.
        if pgrep -f "build/sitl/bin/arducopter|gz sim -v4 -s" >/dev/null; then
            reason="stale Gazebo/SITL processes running before $name; refusing to start"
            log_event FAILED "$name  $reason"; set_status "FAILED: $reason"
            echo "$reason" > "$STATE_DIR/FAILED"; exit 1
        fi
        free_gb=$(df -BG --output=avail "$TRIALS_DIR" | tail -1 | tr -dc 0-9)
        if [ "$free_gb" -lt "$MIN_FREE_GB" ]; then
            reason="only ${free_gb} GB free (< ${MIN_FREE_GB} GB) before $name"
            log_event FAILED "$name  $reason"; set_status "FAILED: $reason"
            echo "$reason" > "$STATE_DIR/FAILED"; exit 1
        fi

        log_event START "$name  ($k/$TOTAL, attempt $attempt)  world=${W[$i]}  free=${free_gb}G"
        set_status "RUNNING $name ($k/$TOTAL, attempt $attempt) since $(date +%T)"
        t0=$SECONDS
        "$RUN_TRIAL" --world "${W[$i]}" --velocity "${V[$i]}" --altitude "${A[$i]}" \
            --duration "${D[$i]}" --trial-name "$name"
        rc=$?
        wall=$((SECONDS - t0))

        if [ "$rc" -eq 0 ] && why="$(validate_trial "$name" "${W[$i]}")"; then
            size=$(du -sh "$TRIALS_DIR/$name" | cut -f1)
            log_event COMPLETE "$name  ($k/$TOTAL)  wall=${wall}s  size=$size"
            break
        fi
        [ "$rc" -ne 0 ] && why="run_trial.sh exit $rc"
        abort_dir "$name" "attempt $attempt failed: $why (wall ${wall}s)"
        if [ "$attempt" -eq 2 ]; then
            reason="$name failed twice; batch stopped (last: $why)"
            log_event FAILED "$reason"; set_status "FAILED: $reason"
            echo "$reason" > "$STATE_DIR/FAILED"; exit 1
        fi
    done
done

n_done=0
for name in "${N[@]}"; do is_complete "$name" && n_done=$((n_done + 1)); done
if [ "$n_done" -eq "$TOTAL" ]; then
    log_event DONE "$n_done/$TOTAL trials COMPLETE"
    { echo "DONE $(ts)"; grep -E "  COMPLETE " "$LOG"; } > "$STATE_DIR/DONE"
    set_status "DONE: $n_done/$TOTAL complete"
    rm -f "$STATE_DIR/FAILED"
else
    set_status "STOPPED: $n_done/$TOTAL complete (see trials.log)"
    exit 1
fi
