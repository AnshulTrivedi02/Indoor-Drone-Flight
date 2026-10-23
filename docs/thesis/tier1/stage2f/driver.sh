#!/bin/bash
# Stage 2f (E4): serial, ONE heavy.py job at a time (decision D1), in order.txt order (decision D10: main sweep
# flight-major T_A_r1..T_D_r3, windows ascending 0.5/1/2/5 within each flight; then LM-cap-10 on T_A_r1 then T_D_r1,
# windows 0.25..5 ascending). Resumable: a job with a final line in timing.tsv is skipped.
# Each job script wraps the replay in `timeout min(48 h, time to the 2026-11-04 23:59 AEDT lock)`; after the lock it
# exits 99 without running (NOT RUN).
# rc != 0 (not 99, not a timeout at the lock): ONE identical re-run (prereg §0.5) after moving the output aside to
# <dir>.CRASHED_try1 (never deleted). A second failure is recorded "crashed" and the queue CONTINUES.
# timing.tsv columns: job, start, end, wall_s, rc, try, loadavg_start, loadavg_end, outcome
set -u
S=/home/makerspace/thesis_data/tier1/stage2f; J=$S/jobs; L=$S/logs; T=$S/timing.tsv
H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
LOCK=$(date -d '2026-11-04T23:59:00+11:00' +%s)
la() { cut -d' ' -f1-3 /proc/loadavg | tr ' ' '/'; }
for j in $(cat $S/order.txt); do
  if grep -qP "^$j\t.*\t(completed|crashed|NOT RUN|timeout)\$" $T 2>/dev/null; then continue; fi
  d=$(python3 -c "import sys; sys.path.insert(0,'$S'); import run_status as R; print(R.run_dir('$j')[0])")
  for attempt in 1 2; do
    if [ $(date +%s) -ge $LOCK ]; then
      printf '%s\t%s\t-\t-\t-\ttry%d\t-\t-\tNOT RUN\n' "$j" "$(date -Iseconds)" $attempt >> $T; break; fi
    if [ -e "$d" ] && [ -n "$(ls -A "$d" 2>/dev/null)" ]; then mv "$d" "$d.CRASHED_try$attempt.$(date +%s)"; fi
    s=$(date +%s.%N); si=$(date -Iseconds); l0=$(la)
    python3 $H --wait-s 86400 "tier1 stage2f $j" -- bash $J/$j.sh > $L/$j.log.try$attempt 2>&1; rc=$?
    e=$(date +%s.%N); l1=$(la)
    w=$(echo "$e - $s" | bc)
    if [ $rc -eq 0 ]; then out=completed
    elif [ $rc -eq 99 ] || { [ $rc -eq 124 ] && [ $(date +%s) -ge $((LOCK-5)) ]; }; then out="NOT RUN"
    elif [ $rc -eq 124 ]; then out=timeout
    elif [ $attempt -eq 1 ]; then out=retry
    else out=crashed; fi
    printf '%s\t%s\t%s\t%.1f\t%d\ttry%d\t%s\t%s\t%s\n' "$j" "$si" "$(date -Iseconds)" "$w" "$rc" "$attempt" "$l0" "$l1" "$out" >> $T
    if [ "$out" = completed ]; then
      cp $L/$j.log.try$attempt $L/$j.log
      python3 $S/run_status.py $j >> $S/status.tsv 2>&1
      python3 $S/projection.py >> $S/projection.log 2>&1
    fi
    [ "$out" = retry ] || break
  done
done
echo "ALLDONE $(date -Iseconds)" >> $T
