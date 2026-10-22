#!/bin/bash
# Stage 2e E3: serial, one heavy.py job at a time, in order.txt order (arm (a) 18, then arm (b) 3 controls + 18).
# Each job is wrapped in timeout 21600 inside its .sh; any non-zero rc (incl. 124 timeout) stops the driver.
set -u
S=/home/makerspace/thesis_data/tier1/stage2e; J=$S/jobs; L=$S/logs; T=$S/timing.tsv
H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
for j in $(cat $S/order.txt); do
  if grep -q "^$j	" $T 2>/dev/null; then continue; fi
  s=$(date +%s.%N); si=$(date -Iseconds)
  python3 $H --wait-s 1800 "tier1 stage2e $j" -- bash $J/$j.sh > $L/$j.log 2>&1; rc=$?
  e=$(date +%s.%N)
  printf '%s\t%s\t%s\t%.1f\t%d\n' "$j" "$si" "$(date -Iseconds)" "$(echo "$e - $s" | bc)" "$rc" >> $T
  if [ $rc -ne 0 ]; then echo "STOP: $j rc=$rc" >> $T; exit $rc; fi
done
echo ALLDONE >> $T
