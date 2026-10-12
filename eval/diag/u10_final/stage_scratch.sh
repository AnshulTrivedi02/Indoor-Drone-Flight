#!/bin/bash
# U10 rule 2: scratch build (one heavy step), then the 5-log Replay driver on the scratch Replay.
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
D=/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c/eval/diag/u10_final
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600"
mkdir -p $S/u10f
$H "U10 rule-2 scratch SITL build (replay-rukx)" -- bash $D/build.sh || { echo "BUILD FAILED"; exit 1; }
bash $D/driver.sh $S/apr/build/sitl/tool/Replay scratch
echo STAGE_DONE
