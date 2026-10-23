#!/bin/bash
set -u
cd /home/makerspace/thesis_ws
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
LOCK=$(date -d '2026-11-04T23:59:00+11:00' +%s); REM=$(( LOCK - $(date +%s) ))
if [ $REM -le 0 ]; then echo "NOT RUN: lock passed"; exit 99; fi
TO=172800; [ $REM -lt $TO ] && TO=$REM
exec timeout $TO /home/makerspace/venv-fgo/bin/python src/estimators/fgo/room_fgo_replay.py T_D_r2 --no-batch --window 1 --out-root /home/makerspace/thesis_data/tier1
