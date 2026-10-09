#!/bin/bash
# free-inertial audit harness with the gated FGO core (one bounded heavy step). Usage: fi.sh <T_TOTAL> <tag>
set -euo pipefail
Y=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-add36c43f1fbc72e3
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd $W
$HOME/venv-fgo/bin/python3 eval/diag/model_audit/free_inertial.py $Y/win60_tex_r1.npz $Y/ekf3_cov_harness $Y/$2.json $1
