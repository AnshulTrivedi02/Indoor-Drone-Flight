#!/bin/bash
# XUKO FMT + Replay stamp fix (2026-10-12): rebuild the scratch tree (one heavy step), the 5-log CSV byte-identity
# driver (one heavy step per Replay), then a SECOND Replay of cl_a_tex_half for the determinism check.
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
D=/home/makerspace/thesis_ws/.claude/worktrees/agent-a60b4a326e4fb1d35/eval/diag/xuko_fmt
H="python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600"
BIN=$S/apx/build/sitl/tool/Replay
$H "xuko-fmt scratch SITL build 2 (stamp fix)" -- bash $D/build.sh || { echo "BUILD FAILED"; exit 1; }
bash $D/driver.sh $BIN scratch2
$H "xuko-fmt determinism repeat cl_a_tex_half" -- bash $D/run_one_keep.sh $S/s12/xuko_scratch2_rep/cl_a_tex_half $BIN /home/makerspace/thesis_data/trials/cl_a_tex_half/ardupilot.bin X=0
cmp $S/s12/xuko_scratch2/cl_a_tex_half/logs/00000001.BIN $S/s12/xuko_scratch2_rep/cl_a_tex_half/logs/00000001.BIN && echo "RESULT determinism: two Replays of cl_a_tex_half give byte-identical logs" || echo "RESULT determinism: logs DIFFER"
echo STAGE2_DONE
