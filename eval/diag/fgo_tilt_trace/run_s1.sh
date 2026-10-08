#!/bin/bash
# FGO tilt trace: diagnostic replays of H_s1_r1 (to t = 130 s), one knob at a time. Scratch output only.
cd "$(dirname "$0")"
PY=~/venv-fgo/bin/python
export ROOM_TAG_SIGMA_POS=0.02 DIAG_TMAX=130
run() { name=$1; shift; echo "== $name"; env FGO_OUT_ROOT=$PWD/out/$name "$@" $PY diag_replay.py H_s1_r1 --no-batch 2>&1 | tail -2; }
run s1_base
run s1_binit0 DIAG_BINIT_ACC=0 DIAG_BINIT_GYR=0
run s1_binit_gyr0 DIAG_BINIT_GYR=0
run s1_binit_acc0 DIAG_BINIT_ACC=0
