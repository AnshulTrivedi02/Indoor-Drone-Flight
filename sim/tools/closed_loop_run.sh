#!/usr/bin/env bash
# Closed-loop flight launcher (METHODOLOGY "Closed loop"). Runs ONE flight with EKF3 as the
# active estimator (closedloop.parm via EXTRA_PARM_FILES, AHRS_EKF_TYPE=3 enforced by
# EXPECT_OVERRIDE), in its own process group, with the ground-truth wall watcher.
# No retry: a breach stops the flight and it is reported.
#
# HEADING=1 adds the live forward-camera heading (closed-loop Part 1): closedloop_heading.parm
# (VISO_TYPE 1, EK3_SRC1_YAW 6, VISO_DELAY_MS) is appended and enforced, run_trial.sh starts
# heading_bridge.py (HEADING_BRIDGE=1; HEADING_SIGMA_DEG and HEADING_EVERY_N must be set), and
# the watcher also stops the flight if heading_bridge.py dies while airborne.
# Usage: [HEADING=1 HEADING_SIGMA_DEG=.. HEADING_EVERY_N=..] sim/tools/closed_loop_run.sh <world> <trial_name>
set -uo pipefail
WORLD="$1"; NAME="$2"; OUT="$HOME/thesis_data/closed_loop/$NAME"
mkdir -p "$OUT"
export EXTRA_PARM_FILES="$HOME/thesis_ws/closedloop.parm" EXPECT_OVERRIDE="AHRS_EKF_TYPE=3"
WATCH=()
if [ -n "${HEADING:-}" ]; then
    P="$HOME/thesis_ws/closedloop_heading.parm"
    EXTRA_PARM_FILES="$EXTRA_PARM_FILES,$P"
    # enforce every value in the heading parm file (eeprom self-heal, fly_trial.ensure_params)
    EXPECT_OVERRIDE="$EXPECT_OVERRIDE,$(grep -Ev '^\s*(#|$)' "$P" | awk '{printf "%s%s=%s", (NR>1?",":""), $1, $2}')"
    # Ruling D2 (2026-09-30): the C++ heading node for all closed-loop flights; closedloop_heading.parm
    # carries ITS delay (VISO_DELAY_MS 38), so the Python node must not be flown with it by default.
    export HEADING_IMPL="${HEADING_IMPL:-cpp}"
    export HEADING_BRIDGE=1 HEADING_SIGMA_DEG HEADING_EVERY_N
    WATCH=(--watch-process heading_bridge.py)
fi
# UKF=1 (ruling D9, 2026-09-30): the thesis UKF as the ACTIVE estimator (AHRS_EKF_TYPE 12) on the port tree,
# replacing closedloop.parm's AHRS_EKF_TYPE 3. Not combinable with HEADING (the port has no heading input yet).
if [ -n "${UKF:-}" ]; then
    [ -n "${HEADING:-}" ] && { echo "UKF=1 with HEADING=1 is not supported yet" >&2; exit 2; }
    EXTRA_PARM_FILES="$HOME/thesis_ws/closedloop_ukf.parm"
    EXPECT_OVERRIDE="AHRS_EKF_TYPE=12,AHRS_UKF_ENABLE=1"
    export ARDUPILOT_TREE="${ARDUPILOT_TREE:-$HOME/ardupilot_ukf}"
fi
# GROUND_TEST (ground test only): disable ArduCopter's landed auto-disarm so the armed hold lasts
if [ -n "${GROUND_TEST:-}" ]; then
    EXTRA_PARM_FILES="$EXTRA_PARM_FILES,$HOME/thesis_ws/groundtest.parm"
    EXPECT_OVERRIDE="$EXPECT_OVERRIDE,DISARM_DELAY=0"
fi
echo "EXTRA_PARM_FILES=$EXTRA_PARM_FILES" > "$OUT/launch.txt"; echo "EXPECT_OVERRIDE=$EXPECT_OVERRIDE" >> "$OUT/launch.txt"
echo "ARDUPILOT_TREE=${ARDUPILOT_TREE:-}" >> "$OUT/launch.txt"
setsid "$HOME/thesis_ws/run_trial.sh" --world "$WORLD" --velocity 0.5 --altitude 2.0 --duration 300 --trial-name "$NAME" &
RT=$!
set +u; source /opt/ros/jazzy/setup.bash; set -u
# The watcher gets run_trial's PID (not its group) and stops the flight itself on a breach; it
# exits only once run_trial has exited AND no sim process remains, so it is waited for, never killed.
python3 "$HOME/thesis_ws/sim/tools/wall_watch.py" "$OUT" "$RT" "${WATCH[@]}" > "$OUT/wall_watch.log" 2>&1 &
WW=$!
wait "$RT"; RC=$?
wait "$WW"; WRC=$?
echo "run_trial exit $RC; watcher exit $WRC" | tee "$OUT/result.txt"
[ -f "$OUT/BREACH.txt" ] && { echo "BREACH:"; cat "$OUT/BREACH.txt"; } | tee -a "$OUT/result.txt"
cat "$OUT/wall_watch_summary.txt" 2>/dev/null | tee -a "$OUT/result.txt"
# A stopped flight skips run_trial's normal-exit log copy: copy the dataflash log it wrote.
T="$HOME/thesis_data/trials/$NAME"; L="${ARDUPILOT_TREE:-$HOME/ardupilot}/ArduCopter/logs"
if [ -d "$T" ] && [ ! -f "$T/ardupilot.bin" ] && [ -f "$L/LASTLOG.TXT" ]; then
    n=$(tr -d '[:space:]' < "$L/LASTLOG.TXT"); f=$(printf "%s/%08d.BIN" "$L" "$n")
    [ -f "$f" ] && cp "$f" "$T/ardupilot.bin" && echo "ardupilot.bin copied from $f (flight stopped before run_trial's own copy)" | tee -a "$OUT/result.txt"
fi
