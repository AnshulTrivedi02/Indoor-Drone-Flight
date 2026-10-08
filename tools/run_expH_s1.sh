#!/usr/bin/env bash
# Experiment H S1 (pre-registered): 3 closed-loop flights, EKF3 flying on the wall tag (closed_loop_run.sh H=1).
# Lock protocol (user ruling 2026-10-08): wait while ~/thesis_data/BUILD_LOCK exists (cap 1 h), hold FLIGHT_LOCK
# during each flight. Stops at the first failed or breached flight.
set -u
cd "$(dirname "$0")/.."
for r in ${REPS:-1 2 3}; do
  name="H_s1_r$r"
  [ -f "$HOME/thesis_data/closed_loop/$name/result.txt" ] && grep -q "run_trial exit 0" "$HOME/thesis_data/closed_loop/$name/result.txt" && { echo "$name done, skipping"; continue; }
  SECONDS=0; while [ -e ~/thesis_data/BUILD_LOCK ] && [ $SECONDS -lt 3600 ]; do sleep 20; done
  [ -e ~/thesis_data/BUILD_LOCK ] && { echo "BUILD_LOCK held > 1 h; stopping"; exit 1; }
  echo "$name $(date -Is)" > ~/thesis_data/FLIGHT_LOCK; sleep 5
  [ -e ~/thesis_data/BUILD_LOCK ] && { rm -f ~/thesis_data/FLIGHT_LOCK; echo "BUILD_LOCK raced; stopping"; exit 1; }
  H=1 HPROFILE="$PWD/batches/expH/s1_profile.json" sim/tools/closed_loop_run.sh room_wall_tag "$name"
  rm -f ~/thesis_data/FLIGHT_LOCK
  res="$HOME/thesis_data/closed_loop/$name/result.txt"
  if ! grep -q "run_trial exit 0" "$res" || [ -f "$HOME/thesis_data/closed_loop/$name/BREACH.txt" ]; then
    echo "expH S1: $name FAILED or BREACHED - stopping"; cat "$res"; exit 1
  fi
  echo "expH S1: $name complete"
done
echo "expH S1: all done"
