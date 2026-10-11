#!/bin/bash
# board-h743: show why the ChibiOS_lib make step fails (verbose, one job)
W=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/aph7
export PATH=/opt/gcc-arm-none-eabi-10-2020-q4-major/bin:$PATH
cd $W
./waf copter -v -j1 > /tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/h7/dbg_chibios.log 2>&1
grep -v "^expanding" /tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/h7/dbg_chibios.log | grep -i -B3 -A3 "error\|No rule\|not found\|Stop" | cut -c1-400 | head -40
