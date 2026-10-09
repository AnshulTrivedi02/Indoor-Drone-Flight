#!/bin/sh
# Step 2 as worded with the OLD (pre-fix, post-D27) core and the OLD port (UR1 export of 2026-10-08): real copies.
set -e
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
J=$S/jfix
mkdir -p $J/s2_old
cp $S/ur1/dsn_tex_r2.npz $J/s2_old/old.npz
cp $S/ur1/new.bin $J/s2_old/old_port.bin
cp -r $S/ur1/dsn_tex_r2_replay_out $J/s2_old/old_replay_out
cd /home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4
/home/makerspace/venv-evo/bin/python3 eval/ukf_equivalence.py $J/s2_old/old --log tex --json $J/s2_old/equiv_old.json > $J/s2_old/equiv_old.log 2>&1 || true
grep -v '^ \|^{\|^}' $J/s2_old/equiv_old.log | tail -12
cp $J/s2_old/equiv_old.json /home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4/eval/diag/ukf_jitter_fix/results/equiv_dsn_tex_r2_PREFIX_oldcore_oldport.json
cp $J/cfi60_A.bin $J/cfi60_A.pdiag /home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4/eval/diag/ukf_jitter_fix/results/
