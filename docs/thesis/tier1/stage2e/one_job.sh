#!/bin/bash
# Run one E3 job (called by serial_pair.sh / par_batch.sh, inside ONE heavy.py invocation that holds BUILD_LOCK).
# Refuses to start if a flight is on (FLIGHT_LOCK, arducopter, gz sim). Appends start/end/wall/rc to par_timing.tsv,
# then the run's failure status (run_status.py). A non-zero rc gets ONE identical re-run (prereg §0.5), output moved aside.
set -u
S=/home/makerspace/thesis_data/tier1/stage2e; j=$1; T=$S/par_timing.tsv
if [ -e ~/thesis_data/FLIGHT_LOCK ] || pgrep -f '[a]rducopter' >/dev/null || pgrep -f '[g]z sim' >/dev/null; then
  printf '%s\tREFUSED-FLIGHT\t%s\n' "$j" "$(date -Iseconds)" >> $T; exit 75; fi
for attempt in 1 2; do
  s=$(date +%s.%N); si=$(date -Iseconds)
  bash $S/jobs/$j.sh > $S/logs/$j.log.try$attempt 2>&1; rc=$?
  e=$(date +%s.%N)
  printf '%s\t%s\t%s\t%.1f\t%d\ttry%d\n' "$j" "$si" "$(date -Iseconds)" "$(echo "$e - $s" | bc)" "$rc" "$attempt" >> $T
  if [ $rc -eq 0 ]; then cp $S/logs/$j.log.try$attempt $S/logs/$j.log; python3 $S/run_status.py $j >> $S/par_status.tsv 2>&1; exit 0; fi
  if [ $attempt -eq 1 ]; then
    d=$(python3 -c "import sys; sys.path.insert(0,'$S'); import run_status as R; print(R.run_dir('$j')[0])")
    [ -d "$d" ] && mv "$d" "$d.CRASHED_try1"
  fi
done
exit $rc
