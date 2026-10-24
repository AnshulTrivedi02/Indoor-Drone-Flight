#!/bin/bash
# Attribution ablation (EXPLORATORY) serial driver, stage2f style (docs/thesis/ablation/preregistration.md §4, §9).
# ONE heavy.py job at a time, in order.txt order. Resumable: a job with a final line in timing.tsv is skipped.
# GATE entry: gate_check.py must pass (12/12 byte-identical r0 trajectories), else GATE_FAILED is written and the
# driver exits without running any other rung (STOP).
# rc 99 = past the lock (NOT RUN); rc 98 = output dir non-empty (REFUSED, not retried); rc 124 = timeout.
# Other rc != 0: ONE identical re-run after moving the output aside to <dir>.CRASHED_try1.<epoch> (never deleted);
# a second failure is "crashed" and the queue continues.
# timing.tsv columns: job, start, end, wall_s, rc, try, loadavg_start, loadavg_end, outcome
set -u
S=/home/makerspace/thesis_data/ablation; J=$S/jobs; L=$S/logs; T=$S/timing.tsv
H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
LOCK=$(date -d '2026-11-04T23:59:00+11:00' +%s)
la() { cut -d' ' -f1-3 /proc/loadavg | tr ' ' '/'; }
echo "DRIVER START $(date -Iseconds) pid $$" >> $S/driver.events
for j in $(cat $S/order.txt); do
  if [ "$j" = GATE ]; then
    if [ -e $S/GATE_PASSED ]; then continue; fi
    if python3 $S/gate_check.py > $S/gate.out 2>&1 && python3 $S/gate_scores.py >> $S/gate.out 2>&1; then date -Iseconds > $S/GATE_PASSED; echo "GATE PASS $(date -Iseconds)" >> $S/driver.events
    else date -Iseconds > $S/GATE_FAILED; echo "GATE FAIL $(date -Iseconds): STOP" >> $S/driver.events; exit 3; fi
    continue
  fi
  if grep -qP "^$j\t.*\t(completed|crashed|NOT RUN|timeout|REFUSED)\$" $T 2>/dev/null; then continue; fi
  d=$(python3 -c "import sys; sys.path.insert(0,'$S'); import rungs as R; print(R.parse('$j')[3])")
  for attempt in 1 2; do
    if [ $(date +%s) -ge $LOCK ]; then
      printf '%s\t%s\t-\t-\t-\ttry%d\t-\t-\tNOT RUN\n' "$j" "$(date -Iseconds)" $attempt >> $T; break; fi
    if [ $attempt -eq 2 ] && [ -e "$d" ] && [ -n "$(ls -A "$d" 2>/dev/null)" ]; then mv "$d" "$d.CRASHED_try1.$(date +%s)"; fi
    s=$(date +%s.%N); si=$(date -Iseconds); l0=$(la)
    python3 $H --wait-s 86400 "ablation $j" -- bash $J/$j.sh > $L/$j.log.try$attempt 2>&1; rc=$?
    l1=$(la); w=$(echo "$(date +%s.%N) - $s" | bc)
    if [ $rc -eq 0 ]; then out=completed
    elif [ $rc -eq 99 ] || { [ $rc -eq 124 ] && [ $(date +%s) -ge $((LOCK-5)) ]; }; then out="NOT RUN"
    elif [ $rc -eq 98 ]; then out=REFUSED
    elif [ $rc -eq 124 ]; then out=timeout
    elif [ $attempt -eq 1 ]; then out=retry
    else out=crashed; fi
    printf '%s\t%s\t%s\t%.1f\t%d\ttry%d\t%s\t%s\t%s\n' "$j" "$si" "$(date -Iseconds)" "$w" "$rc" "$attempt" "$l0" "$l1" "$out" >> $T
    python3 $S/run_status.py $j $rc $L/$j.log.try$attempt >> $S/status.tsv 2>&1
    [ "$out" = completed ] && cp $L/$j.log.try$attempt $L/$j.log
    [ "$out" = retry ] || break
  done
done
echo "ALLDONE $(date -Iseconds)" >> $T
echo "DRIVER END $(date -Iseconds)" >> $S/driver.events
