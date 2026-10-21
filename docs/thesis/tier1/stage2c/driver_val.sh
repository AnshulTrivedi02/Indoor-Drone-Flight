#!/bin/bash
# Stage 2c V-E5 gates: serial, one heavy.py job at a time; per flight V-E5a (world), V-E5b (known-map), V-E5c (augmented),
# each judged by eval/e5_val_compare.py right after it runs. STOP on any non-zero rc or a judged FAIL.
set -u
S=/home/makerspace/thesis_data/tier1/stage2c; J=$S/jobs; L=$S/logs; T=$S/timing.tsv
H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
R=/home/makerspace/thesis_ws; SC=$R/docs/thesis/tier1/scores; PY=/home/makerspace/venv-evo/bin/python
for c in A B C D; do for r in 1 2 3; do t=T_${c}_r$r
 for v in world known-map augmented; do
  case $v in world) task=world; g=ve5a;; known-map) task=knownmap; g=ve5b;; augmented) task=augmented; g=ve5c;; esac
  j=ve5_${v}_$t
  if ! grep -q "^$j	" $T 2>/dev/null; then
   s=$(date +%s.%N); si=$(date -Iseconds)
   python3 $H --wait-s 1800 "tier1 stage2c $j" -- bash $J/$j.sh > $L/$j.log 2>&1; rc=$?
   e=$(date +%s.%N)
   printf '%s\t%s\t%s\t%.1f\t%d\n' "$j" "$si" "$(date -Iseconds)" "$(echo "$e - $s" | bc)" "$rc" >> $T
   if [ $rc -ne 0 ]; then echo "STOP: $j rc=$rc" >> $T; exit $rc; fi
  fi
  jj=judge_${g}_$t
  if ! grep -q "^$jj	" $T 2>/dev/null; then
   s=$(date +%s.%N); si=$(date -Iseconds)
   (cd $R && $PY eval/e5_val_compare.py $t --task $task --delta-rmse --json $SC/${g}_$t.json) > $L/$jj.log 2>&1; rc=$?
   e=$(date +%s.%N)
   pass=$($PY -c "import json,sys; print(json.load(open('$SC/${g}_$t.json'))['PASS'])" 2>/dev/null || echo MISSING)
   printf '%s\t%s\t%s\t%.1f\t%d\t%s\n' "$jj" "$si" "$(date -Iseconds)" "$(echo "$e - $s" | bc)" "$rc" "$pass" >> $T
   if [ "$pass" != "True" ]; then echo "STOP: $jj rc=$rc PASS=$pass" >> $T; exit 9; fi
  fi
 done
done; done
echo ALLDONE_VAL >> $T
