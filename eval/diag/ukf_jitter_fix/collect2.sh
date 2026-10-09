#!/bin/sh
set -e
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
R=/home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4/eval/diag/ukf_jitter_fix
cp $J/tierB_run.log $R/results/tierB_fixed_run.log
cp $J/ub/replay_base/replay.log $R/results/tierB_base_replay.log
cp $J/ub/replay/replay.log $R/results/tierB_fixed_replay.log
cp $J/tierB_build.sh $J/tierB_run.sh $J/tierB_base.sh $J/s2_old.sh $J/collect.sh $J/collect2.sh $J/copymods.sh $R/
grep -v "Compiling\|Linking\|^\[ *[0-9]\|waiting" $J/tierB_build.log > $R/results/tierB_build.log
rm -f $J/homeB/thesis_data/trials/H_s1_r1/ardupilot.bin $J/homeB/thesis_data/trials/H_s1_r1/bag/bag_0.db3
echo "symlinks under jfix:"; find $J -path $J/apukf -prune -o -type l -print
sh $J/stat_live.sh > $J/after_stat2.txt 2>&1
diff $J/before_stat.txt $J/after_stat2.txt && echo LIVE_UNCHANGED
cp $J/after_stat2.txt $R/results/
