#!/bin/bash
# FGO tilt trace, batch 4: the residual take-off tilt offset, binit0 + window / climb-flow knobs, through the hover window.
cd "$(dirname "$0")"
PY=~/venv-fgo/bin/python
export ROOM_TAG_SIGMA_POS=0.02 DIAG_BINIT_ACC=0 DIAG_BINIT_GYR=0
run() { name=$1; tr=$2; shift 2; echo "== $name"; env FGO_OUT_ROOT=$PWD/out/$name "$@" $PY diag_replay.py $tr --no-batch 2>&1 | tail -2; }
run sfb_b0_win1_full H_safety_fgo_b DIAG_TMAX=73 DIAG_WINDOW=1.0
run sfb_b0_win05_full H_safety_fgo_b DIAG_TMAX=73 DIAG_WINDOW=0.5
run sfa_b0_win1_full H_safety_fgo_a DIAG_TMAX=66.5 DIAG_WINDOW=1.0
run sfa_b0_noflowclimb H_safety_fgo_a DIAG_TMAX=66.5 DIAG_SKIP_FLOW=27,37
run sfb_b0_noflowclimb_full H_safety_fgo_b DIAG_TMAX=73 DIAG_SKIP_FLOW=34,44
