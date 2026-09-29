#!/usr/bin/env bash
# Build a Phase 5b sandbox HOME for the current trials and write its jobs file (the old
# batches/phase5b_replays.jobs with the sandbox path substituted). Outputs go only into the
# sandbox; the trial folders are linked read-only by symlink (bag, fwd_meas, imu_gaps.json).
# Usage: eval/build_5b_sandbox.sh <sandbox_home> <jobs_out>
set -euo pipefail
SBH="$1"; JOBS="$2"; OLD="/home/makerspace/thesis_data/phase5b/home"
mkdir -p "$SBH/thesis_data/trials"; ln -sfn "$HOME/thesis_ws" "$SBH/thesis_ws"
for d in "$HOME"/venv-*; do ln -sfn "$d" "$SBH/$(basename "$d")"; done
for ds in fwdc fwdplainc; do for w in tex trans blank; do for r in 1 2 3; do
  t=${ds}_${w}_r$r; T="$SBH/thesis_data/trials/$t"; mkdir -p "$T"
  for f in bag fwd_meas imu_gaps.json; do [ -e "$HOME/thesis_data/trials/$t/$f" ] && ln -sfn "$HOME/thesis_data/trials/$t/$f" "$T/$f"; done
done; done; done
sed "s#$OLD#$SBH#g" "$HOME/thesis_ws/batches/phase5b_replays.jobs" > "$JOBS"
grep -c "$SBH" "$JOBS"
