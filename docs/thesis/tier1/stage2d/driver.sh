#!/bin/bash
# Stage 2d E2: serial, one heavy.py job at a time. Order: LC (B r1-3, C r1-3, D r1-3), then no-LC (same order).
# Each job is wrapped in timeout 21600 inside its .sh; any non-zero rc (incl. 124 timeout) stops the driver.
set -u
S=/home/makerspace/thesis_data/tier1/stage2d; J=$S/jobs; L=$S/logs; T=$S/timing.tsv
H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
order=""
for m in lc nolc; do for c in B C D; do for r in 1 2 3; do order="$order e2_${m}_T_${c}_r$r"; done; done; done
for j in $order; do
  if grep -q "^$j	" $T 2>/dev/null; then continue; fi
  s=$(date +%s.%N); si=$(date -Iseconds)
  python3 $H --wait-s 1800 "tier1 stage2d $j" -- bash $J/$j.sh > $L/$j.log 2>&1; rc=$?
  e=$(date +%s.%N)
  printf '%s\t%s\t%s\t%.1f\t%d\n' "$j" "$si" "$(date -Iseconds)" "$(echo "$e - $s" | bc)" "$rc" >> $T
  if [ $rc -ne 0 ]; then echo "STOP: $j rc=$rc" >> $T; exit $rc; fi
done
echo ALLDONE >> $T
