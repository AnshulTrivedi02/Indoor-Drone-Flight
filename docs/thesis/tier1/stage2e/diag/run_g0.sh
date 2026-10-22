#!/bin/bash
set -u
S=/home/makerspace/thesis_data/tier1/stage2e/diag; H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
for j in g0l_i g0l_ii; do
  s=$(date +%s); python3 $H --wait-s 1800 "tier1 stage2e diag $j" -- bash $S/jobs/$j.sh > $S/logs/$j.log 2>&1; rc=$?
  echo -e "$j\t$(( $(date +%s)-s ))\t$rc" >> $S/timing.tsv; [ $rc -ne 0 ] && exit $rc
done
echo G0DONE >> $S/timing.tsv
