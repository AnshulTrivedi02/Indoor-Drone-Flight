#!/bin/bash
# Re-run of the y0s1 FGO on fwdplainc_tex_r1 without the equivalence dump (the dump refuses F-variants).
SC=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export FGO_OUT_ROOT=$SC/out FGO_BAG_ROOT=$SC/bags
cd /home/makerspace/thesis_ws/.claude/worktrees/agent-a375613081292d466
env F_TAG=y0s1 F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=1 /home/makerspace/venv-fgo/bin/python src/estimators/fgo/fgo_replay.py fwdplainc_tex_r1 0.25 2 heading > $SC/logs/fgo_y0s1_tex_r1.log 2>&1
echo "exit $?" >> $SC/logs/fgo_y0s1_tex_r1.log
