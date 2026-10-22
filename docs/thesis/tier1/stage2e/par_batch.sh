#!/bin/bash
# Remaining 31 E3 runs, at most 4 at a time (ruling 2026-10-22; no E3 timing hypothesis). Arm (a) entries come first.
set -u; S=/home/makerspace/thesis_data/tier1/stage2e; W=${1:-4}
xargs -P $W -n 1 bash $S/one_job.sh < $S/par_order.txt; rc=$?
echo "PARDONE rc=$rc" >> $S/par_timing.tsv; exit $rc
