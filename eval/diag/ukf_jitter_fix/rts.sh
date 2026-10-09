#!/bin/bash
# RTS-UKF smoke check with the fixed core: room_ukf_replay.py H_s1_r1 (RTS ON) under a FAKE HOME of real copies.
set -e
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
WT=/home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4
FH=$J/home
T=/home/makerspace/thesis_data/trials/H_s1_r1
mkdir -p $FH/thesis_data/trials/H_s1_r1/bag $FH/thesis_ws/src/optical_flow_interfaces/msg
cp $WT/src/optical_flow_interfaces/msg/OpticalFlow.msg $FH/thesis_ws/src/optical_flow_interfaces/msg/
cp $T/bag/metadata.yaml $T/bag/bag_0.db3 $FH/thesis_data/trials/H_s1_r1/bag/
cp $T/imu_gaps.json $FH/thesis_data/trials/H_s1_r1/
cd $WT
HOME=$FH ROOM_TAG_SIGMA_POS=0.02 /home/makerspace/venv-evo/bin/python3 -c "
import runpy, sys
sys.path.insert(0, '$WT/src/estimators')
import ukf_core
sys.argv = ['room_ukf_replay.py', 'H_s1_r1']
runpy.run_path('$WT/src/estimators/room_ukf_replay.py', run_name='__main__')
print('CHOL_STATS', ukf_core.CHOL_STATS)
" > $J/rts_H_s1_r1.log 2>&1
tail -15 $J/rts_H_s1_r1.log
ls -la $FH/thesis_data/trials/H_s1_r1/room_ukf/
rm -f $FH/thesis_data/trials/H_s1_r1/bag/bag_0.db3
echo DONE
