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
# D19: every half-speed world runs with gz-transport / ROS 2 discovery on loopback (run_trial.sh LOOPBACK_ONLY)
if [[ "$WORLD" == *_half_* ]]; then export LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST; fi
mkdir -p "$OUT"
export EXTRA_PARM_FILES="$HOME/thesis_ws/closedloop.parm" EXPECT_OVERRIDE="AHRS_EKF_TYPE=3"
WATCH=()
# UKF=1 (ruling D9, 2026-09-30): the thesis UKF as the ACTIVE estimator (AHRS_EKF_TYPE 12) on the port tree,
# replacing closedloop.parm's AHRS_EKF_TYPE 3. UKF=shadow (ruling D17 V2): EKF3 flies (closedloop.parm) and
# the UKF runs in shadow. With HEADING=1 the UKF also fuses the ExtNav yaw (closedloop_ukf_heading.parm).
if [ -n "${UKF:-}" ]; then
    if [ "$UKF" = shadow ]; then
        EXTRA_PARM_FILES="$EXTRA_PARM_FILES,$HOME/thesis_ws/ukf_shadow.parm"
        EXPECT_OVERRIDE="$EXPECT_OVERRIDE,AHRS_UKF_ENABLE=1"
    else
        EXTRA_PARM_FILES="$HOME/thesis_ws/closedloop_ukf.parm"
        EXPECT_OVERRIDE="AHRS_EKF_TYPE=12,AHRS_UKF_ENABLE=1"
    fi
    if [ -n "${HEADING:-}" ]; then
        EXTRA_PARM_FILES="$EXTRA_PARM_FILES,$HOME/thesis_ws/closedloop_ukf_heading.parm"
        EXPECT_OVERRIDE="$EXPECT_OVERRIDE,AHRS_UKF_EXTYAW=1"
    fi
    export ARDUPILOT_TREE="${ARDUPILOT_TREE:-$HOME/ardupilot_ukf}"
fi
# FGO=1 (ruling D19): the thesis FGO as the ACTIVE estimator (AHRS_EKF_TYPE 13; the FGO node runs in the trial,
# FGO_NODE=1). FGO=shadow: EKF3 flies, the FGO node and its in-ArduPilot output predictor run in shadow.
if [ -n "${FGO:-}" ]; then
    [ -n "${UKF:-}" ] && { echo "FGO and UKF together are not supported" >&2; exit 2; }
    if [ "$FGO" = shadow ]; then
        EXTRA_PARM_FILES="$EXTRA_PARM_FILES,$HOME/thesis_ws/fgo_shadow.parm"
        EXPECT_OVERRIDE="$EXPECT_OVERRIDE,AHRS_FGO_ENABLE=1,SERIAL3_PROTOCOL=2"
    else
        EXTRA_PARM_FILES="$HOME/thesis_ws/closedloop_fgo.parm"
        EXPECT_OVERRIDE="AHRS_EKF_TYPE=13,AHRS_FGO_ENABLE=1,SERIAL3_PROTOCOL=2"
    fi
    export FGO_NODE=1 ARDUPILOT_TREE="${ARDUPILOT_TREE:-$HOME/ardupilot_ukf}"
fi
if [ -n "${HEADING:-}" ]; then
    P="${HEADING_PARM:-$HOME/thesis_ws/closedloop_heading.parm}"   # HEADING_PARM: D19 half-speed delay measurement/value
    EXTRA_PARM_FILES="$EXTRA_PARM_FILES,$P"
    # enforce every value in the heading parm file (eeprom self-heal, fly_trial.ensure_params)
    EXPECT_OVERRIDE="$EXPECT_OVERRIDE,$(grep -Ev '^\s*(#|$)' "$P" | awk '{printf "%s%s=%s", (NR>1?",":""), $1, $2}')"
    # Ruling D2 (2026-09-30): the C++ heading node for all closed-loop flights; closedloop_heading.parm
    # carries ITS delay (VISO_DELAY_MS 38), so the Python node must not be flown with it by default.
    export HEADING_IMPL="${HEADING_IMPL:-cpp}"
    export HEADING_BRIDGE=1 HEADING_SIGMA_DEG HEADING_EVERY_N
    WATCH=(--watch-process heading_bridge.py)
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
