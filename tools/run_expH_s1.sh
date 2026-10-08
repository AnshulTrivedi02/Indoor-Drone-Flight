#!/usr/bin/env bash
# Experiment H S1 (pre-registered): 3 closed-loop flights, EKF3 flying on the wall tag (closed_loop_run.sh H=1).
# Lock protocol (user ruling 2026-10-08): wait while ~/thesis_data/BUILD_LOCK exists (cap 1 h), hold FLIGHT_LOCK
# during each flight. Stops at the first failed or breached flight.
set -u
cd "$(dirname "$0")/.."
source tools/flight_lock.sh
for r in ${REPS:-1 2 3}; do
  name="H_s1_r$r"
  [ -f "$HOME/thesis_data/closed_loop/$name/result.txt" ] && grep -q "run_trial exit 0" "$HOME/thesis_data/closed_loop/$name/result.txt" && { echo "$name done, skipping"; continue; }
  flight_lock_acquire "$name" || { echo "expH S1: cannot take the flight lock; stopping"; exit 1; }
  H=1 HPROFILE="$PWD/batches/expH/s1_profile.json" sim/tools/closed_loop_run.sh room_wall_tag "$name"
  flight_lock_release
  res="$HOME/thesis_data/closed_loop/$name/result.txt"
  if ! grep -q "run_trial exit 0" "$res" || [ -f "$HOME/thesis_data/closed_loop/$name/BREACH.txt" ]; then
    echo "expH S1: $name FAILED or BREACHED - stopping"; cat "$res"; exit 1
  fi
  echo "expH S1: $name complete"
done
echo "expH S1: all done"
