#!/bin/bash
# Attribution: the branch BASE's Replay (~/ardupilot_ukf build, ukf-port-tag 00b597dd, run read-only) on H_s1_r1.
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
mkdir -p $J/ub/replay_base && cd $J/ub/replay_base
md5sum /home/makerspace/ardupilot_ukf/build/sitl/tool/Replay
UKF_EXTPOS=1 UKF_EXTYAW=1 timeout 1500 /home/makerspace/ardupilot_ukf/build/sitl/tool/Replay /home/makerspace/thesis_data/trials/H_s1_r1/ardupilot.bin > replay.log 2>&1; echo "rc=$?"
grep -i "anchor\|cholesky" replay.log | head -3
cut -d, -f1 ukf_inputs.csv | sort | uniq -c
