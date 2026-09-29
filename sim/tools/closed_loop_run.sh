#!/usr/bin/env bash
# Closed-loop smoke test launcher (METHODOLOGY "Closed loop - EKF3 flying"). Runs ONE flight
# with EKF3 as the active estimator (closedloop.parm via EXTRA_PARM_FILES, AHRS_EKF_TYPE=3
# enforced by EXPECT_OVERRIDE), in its own process group, with the ground-truth wall watcher.
# No retry: a breach stops the flight and it is reported.
# Usage: sim/tools/closed_loop_run.sh <world> <trial_name>
set -uo pipefail
WORLD="$1"; NAME="$2"; OUT="$HOME/thesis_data/closed_loop/$NAME"
mkdir -p "$OUT"
export EXTRA_PARM_FILES="$HOME/thesis_ws/closedloop.parm" EXPECT_OVERRIDE="AHRS_EKF_TYPE=3"
setsid "$HOME/thesis_ws/run_trial.sh" --world "$WORLD" --velocity 0.5 --altitude 2.0 --duration 300 --trial-name "$NAME" &
RT=$!
sleep 2
PGID=$(ps -o pgid= "$RT" | tr -d ' ')
set +u; source /opt/ros/jazzy/setup.bash; set -u
python3 "$HOME/thesis_ws/sim/tools/wall_watch.py" "$OUT" "$PGID" > "$OUT/wall_watch.log" 2>&1 &
WW=$!
wait "$RT"; RC=$?
kill "$WW" 2>/dev/null
echo "run_trial exit $RC" | tee "$OUT/result.txt"
[ -f "$OUT/BREACH.txt" ] && { echo "BREACH:"; cat "$OUT/BREACH.txt"; } | tee -a "$OUT/result.txt"
cat "$OUT/wall_watch_summary.txt" 2>/dev/null | tee -a "$OUT/result.txt"
