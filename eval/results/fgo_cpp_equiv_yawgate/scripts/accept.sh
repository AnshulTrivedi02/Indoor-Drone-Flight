#!/bin/bash
# Dry run of the handover's functional acceptance check, against the PERMANENT input copy, with this stage's scratch
# build standing in for the installed one (run ONLY through heavy.py). Usage: accept.sh <bin dir>
set -euo pipefail
A=$HOME/thesis_data/acceptance/fgo_yawcap_gate
BIN=${1:-/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate2/build}
O=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate2/accept
mkdir -p $O
(cd $A && sha256sum -c SHA256SUMS)
$BIN/fgo_cpp_replay $A/dsn_tex_r1_baseline $O/accept > $O/replay.log
cmp $A/cpp_dsn_tex_r1_baseline.kf.f64 $O/accept.kf.f64 && cmp $A/cpp_dsn_tex_r1_baseline.yawgate.f64 $O/accept.yawgate.f64 && echo "ACCEPT replay"
$BIN/fgo_cpp_live_replay $A/dsn_tex_r1.dj.tape $A/dsn_tex_r1_baseline.init.json $O/L1 --imu-stamp header --arm-source param --delay 0.20 > $O/live.log
cmp $A/L1.kf.f64 $O/L1.kf.f64 && echo "ACCEPT live (node path)"
