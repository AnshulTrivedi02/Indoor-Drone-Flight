#!/bin/bash
set -u
cd /home/makerspace/thesis_ws
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
exec timeout 21600 /home/makerspace/venv-fgo/bin/python src/estimators/fgo/lc_fgo_replay.py T_A_r1 --mode lc --t-max 245 --tag-ids 0,1,2,3,4,5,6,7 --mislabel-rate 0.01 --mislabel-seed 0 --mislabel-keep 59.995,60.127,72.964,89.893,97.384,108.703,114.280,121.243,132.397,144.871,151.174,163.945,180.874,210.739,228.328,246.808,246.841 --out-root /home/makerspace/thesis_data/tier1/stage2e/diag_collapse
