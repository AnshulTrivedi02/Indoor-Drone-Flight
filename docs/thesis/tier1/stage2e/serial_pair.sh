#!/bin/bash
# Serial matched (a)/(b) runtime pair, nothing else running.
set -u; S=/home/makerspace/thesis_data/tier1/stage2e
bash $S/one_job.sh e3a_T_A_r2_0.01_s0 && bash $S/one_job.sh e3b_T_A_r2_0.01_s0; rc=$?
echo "PAIRDONE rc=$rc" >> $S/par_timing.tsv; exit $rc
