#!/bin/bash
# Map-collapse diagnosis, Part 2: two serial counterfactual runs on T_A_r1 1% s0, each alone (one heavy.py call each).
set -u
D=/home/makerspace/thesis_ws/docs/thesis/tier1/stage2e/diag_collapse; O=/home/makerspace/thesis_data/tier1/stage2e/diag_collapse
H=/home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py
for j in i ii; do
  s=$(date +%s); python3 $H --wait-s 1800 "tier1 e3 collapse diag cf_$j" -- bash $D/job_cf_$j.sh > $O/logs/cf_$j.log 2>&1; rc=$?
  echo -e "cf_$j\t$(date -Iseconds -d @$s)\t$(( $(date +%s)-s ))\t$rc" >> $O/timing.tsv; [ $rc -ne 0 ] && exit $rc
done
echo CFDONE >> $O/timing.tsv
