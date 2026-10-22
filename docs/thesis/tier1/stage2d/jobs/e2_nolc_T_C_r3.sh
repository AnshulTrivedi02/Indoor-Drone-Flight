#!/bin/bash
set -u
cd /home/makerspace/thesis_ws
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
exec timeout 21600 /home/makerspace/venv-fgo/bin/python src/estimators/fgo/lc_fgo_replay.py T_C_r3 --mode nolc --t-max 245 --tag-ids 0,2 --out-root /home/makerspace/thesis_data/tier1
