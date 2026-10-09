#!/bin/bash
set -e
R=/home/makerspace/thesis_ws/.claude/worktrees/agent-aa29cfc08768a86c5/eval/results/fgo_cpp_equiv_yawgate
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
mkdir -p $R/logs $R/gatelogs $R/scripts $R/scripts_stopped_agent
cp $S/yawgate2/logs/*.log $R/logs/
cp $S/yawgate2/driver.log $S/yawgate2/driver2.log $S/yawgate2/fi10.json $S/yawgate2/fi60.json $R/
cp $S/yawgate2/*.sh $S/yawgate2/*.py $R/scripts/
cp $S/yawgate2/dump/*.yawgate.f64 $R/gatelogs/
cp $S/yawgate2/dump/probe_py.txt $S/yawgate2/dump/probe_cpp.txt $R/
cp $S/yawgate/*.py $S/yawgate/*.sh $R/scripts_stopped_agent/
python3 $S/yawgate2/ratios.py $S/yawgate2/fi10.json $S/yawgate2/fi60.json > $R/ratios.txt
python3 $S/yawgate2/timing.py > $R/timing.txt
md5sum $S/yawgate2/build/fgo_cpp_* > $R/md5.txt
du -sh $R
