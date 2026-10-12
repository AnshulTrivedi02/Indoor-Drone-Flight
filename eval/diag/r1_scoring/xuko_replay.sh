#!/bin/bash
# One Replay of a log with no UKF FMT records (cl_a_tex_half, EKF3-flown) by the INSTALLED fork Replay (be7c4d18,
# rung1-geometry), to check whether its output log declares XUKO. Scratch cwd; the input log is only read.
set -e
OUT=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/s12/xuko_replay
mkdir -p $OUT && cd $OUT
md5sum /home/makerspace/ardupilot_ukf/build/sitl/tool/Replay > binary.md5
timeout 1500 /home/makerspace/ardupilot_ukf/build/sitl/tool/Replay /home/makerspace/thesis_data/trials/cl_a_tex_half/ardupilot.bin > replay.log 2>&1 || echo "replay rc=$?" >> replay.log
ls -la logs
