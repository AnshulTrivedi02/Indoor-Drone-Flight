#!/bin/bash
set -u
cd /home/makerspace/thesis_ws
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
exec timeout 86400 /home/makerspace/venv-fgo/bin/python src/estimators/fgo/lc_fgo_replay.py T_A_r3 --mode lc --t-max 245 --tag-ids 0,1,2,3,4,5,6,7 --mislabel-rate 0.05 --mislabel-seed 0 --out-root /home/makerspace/thesis_data/tier1
