#!/bin/bash
# Tier B with the fixed port: Replay of H_s1_r1 (UKF_EXTPOS=1 UKF_EXTYAW=1), then eval/ukf_tag_tierB.py against the
# FIXED-core offline room_ukf live track (tier-A export), via a fake HOME of real copies.
set -e
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
T=/home/makerspace/thesis_data/trials/H_s1_r1
FH=$J/homeB
mkdir -p $FH/thesis_data/trials/H_s1_r1/bag $FH/thesis_data/trials/H_s1_r1/logs $FH/thesis_data/trials/H_s1_r1/room_ukf $J/ub/replay
cp $T/ardupilot.bin $FH/thesis_data/trials/H_s1_r1/
cp $T/bag/metadata.yaml $T/bag/bag_0.db3 $FH/thesis_data/trials/H_s1_r1/bag/
cp $T/logs/fly_trial.log $FH/thesis_data/trials/H_s1_r1/logs/
cp $J/ua/h_s1_r1_trial/room_ukf/ukf_live.tum $FH/thesis_data/trials/H_s1_r1/room_ukf/
cd $J/ub/replay
md5sum $J/apukf/build/sitl/tool/Replay
UKF_EXTPOS=1 UKF_EXTYAW=1 timeout 1500 $J/apukf/build/sitl/tool/Replay $T/ardupilot.bin > replay.log 2>&1 || echo "replay rc=$?"
grep -i "cholesky\|extnav\|anchor" replay.log | head -8 || true
wc -l ukf_shadow.csv ukf_inputs.csv
cd /home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4
HOME=$FH /home/makerspace/venv-tags/bin/python3 eval/ukf_tag_tierB.py H_s1_r1 $J/ub/replay --json $J/ub/tierB.json > $J/ub/tierB.log 2>&1 || echo "tierB rc=$?"
tail -40 $J/ub/tierB.log
rm -f $FH/thesis_data/trials/H_s1_r1/bag/bag_0.db3
echo DONE
