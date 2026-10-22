#!/bin/bash
# EXTRA, timing-only arm (a) run at rate 0 (user ruling R3, 2026-10-22): the arm (b) control command without --tag-robust.
# Not scored; enters no criterion. Output under ~/thesis_data/tier1 only (tier1_paths guard refuses trials/ and existing dirs).
set -u
cd /home/makerspace/thesis_ws
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
exec timeout 86400 /home/makerspace/venv-fgo/bin/python src/estimators/fgo/lc_fgo_replay.py T_A_r2 --mode lc --t-max 245 --tag-ids 0,1,2,3,4,5,6,7 --out-root /home/makerspace/thesis_data/tier1
