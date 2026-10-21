#!/bin/bash
# Stage 2c E5 result runs: start ONLY after all 36 V-E5 gates PASS (checked here). Serial heavy.py, T_A_r1..r3, lc then nolc.
set -u
S=/home/makerspace/thesis_data/tier1/stage2c; J=$S/jobs; L=$S/logs; T=$S/timing.tsv
H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
grep -q ALLDONE_VAL $T || { echo "REFUSED: V-E5 not complete" >> $T; exit 8; }
[ $(grep -c '^judge_ve5.*	True$' $T) -eq 36 ] || { echo "REFUSED: not 36 PASS judges" >> $T; exit 8; }
for r in 1 2 3; do for m in lc nolc; do j=e5_${m}_T_A_r$r
  if grep -q "^$j	" $T; then continue; fi
  s=$(date +%s.%N); si=$(date -Iseconds)
  python3 $H --wait-s 1800 "tier1 stage2c $j" -- bash $J/$j.sh > $L/$j.log 2>&1; rc=$?
  e=$(date +%s.%N)
  printf '%s\t%s\t%s\t%.1f\t%d\n' "$j" "$si" "$(date -Iseconds)" "$(echo "$e - $s" | bc)" "$rc" >> $T
  if [ $rc -ne 0 ]; then echo "STOP: $j rc=$rc" >> $T; exit $rc; fi
done; done
echo ALLDONE_RES >> $T
