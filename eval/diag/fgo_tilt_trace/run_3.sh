#!/bin/bash
# FGO tilt trace, batch 3: the residual take-off pitch offset on H_safety_fgo_b (binit0 + one more knob each), to 60 s.
cd "$(dirname "$0")"
PY=~/venv-fgo/bin/python
export ROOM_TAG_SIGMA_POS=0.02 DIAG_TMAX=60 DIAG_BINIT_ACC=0 DIAG_BINIT_GYR=0
run() { name=$1; tr=$2; shift 2; echo "== $name"; env FGO_OUT_ROOT=$PWD/out/$name "$@" $PY diag_replay.py $tr --no-batch 2>&1 | tail -2; }
run sfb_b0_lm10 H_safety_fgo_b DIAG_LM=10
run sfb_b0_win1 H_safety_fgo_b DIAG_WINDOW=1.0
run sfb_b0_noflowclimb H_safety_fgo_b DIAG_SKIP_FLOW=34,44
