#!/bin/bash
# FGO tilt trace, batch 2: the safety flights (to the failure) base vs binit0, and the full-length H_s1_r1 binit0.
cd "$(dirname "$0")"
PY=~/venv-fgo/bin/python
export ROOM_TAG_SIGMA_POS=0.02
run() { name=$1; tr=$2; shift 2; echo "== $name"; env FGO_OUT_ROOT=$PWD/out/$name "$@" $PY diag_replay.py $tr --no-batch 2>&1 | tail -2; }
run sfb_base H_safety_fgo_b DIAG_TMAX=73
run sfb_binit0 H_safety_fgo_b DIAG_TMAX=73 DIAG_BINIT_ACC=0 DIAG_BINIT_GYR=0
run sfa_base H_safety_fgo_a DIAG_TMAX=66.5
run sfa_binit0 H_safety_fgo_a DIAG_TMAX=66.5 DIAG_BINIT_ACC=0 DIAG_BINIT_GYR=0
run s1full_binit0 H_s1_r1 DIAG_BINIT_ACC=0 DIAG_BINIT_GYR=0
