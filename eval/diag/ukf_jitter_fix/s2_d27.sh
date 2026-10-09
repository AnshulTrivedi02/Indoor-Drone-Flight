#!/bin/sh
set -e
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
cd $J/s2
cp dsn_tex_r2.npz dsn_tex_r2_d27.npz
ln -sfn dsn_tex_r2_replay_out dsn_tex_r2_d27_replay_out
UKF_EQ_QDIAG=dsn_tex_r2.qdiag UKF_EQ_IN=dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_d27_port.bin $J/apukf/build/sitl/examples/UKF_Equiv | tail -2
cd /home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4
/home/makerspace/venv-evo/bin/python3 eval/ukf_equivalence.py $J/s2/dsn_tex_r2_d27 --log tex --json $J/s2/equiv_dsn_tex_r2_d27.json > $J/s2/equiv_d27.log 2>&1 || true
rm -f $J/s2/dsn_tex_r2_d27_replay_out
tail -30 $J/s2/equiv_d27.log
