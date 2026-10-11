#!/bin/bash
# Install the switch-OFF D18 C++ FGO (ruling 2026-10-11 item 1, after the forced Band C PASS). Run ONLY via heavy.py.
# Established recipe (2026-10-09 yaw-gate install): back up, default cmake line (NO FGO_CPP_FORCED_GATE), make install,
# new acceptance set in a NEW directory, replay / live cmp acceptance.
set -euo pipefail
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
WT=/home/makerspace/thesis_ws/.claude/worktrees/agent-a77df11041902ee58
D=$S/d18/dump
BK=$HOME/opt/fgo_cpp_backup_f642cd37_2026-10-11
A=$HOME/thesis_data/acceptance/fgo_d18_bandc
B=$HOME/opt/src/build-fgo_cpp-d18
echo "== source: $WT/src/estimators/fgo_cpp (branch worktree-agent-a77df11041902ee58, switch commit 2610bdb)"
echo "== old installed md5s"
md5sum $HOME/opt/fgo_cpp/bin/*
[ -e $BK ] && { echo "backup dir exists already: $BK"; exit 3; }
mkdir -p $BK && cp -a $HOME/opt/fgo_cpp/bin $BK/
echo "== backup $BK"; md5sum $BK/bin/*
env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "source /opt/ros/jazzy/setup.bash && cmake -S $WT/src/estimators/fgo_cpp -B $B -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$HOME/opt/fgo_cpp -DPython3_EXECUTABLE=/usr/bin/python3 '-DCMAKE_PREFIX_PATH=/opt/ros/jazzy;$HOME/thesis_ws/install/optical_flow_interfaces' >/dev/null && make -C $B -j4 >/dev/null && make -C $B install"
grep -c FORCED_GATE $B/CMakeCache.txt || true
grep "FGO_CPP_FORCED_GATE:" $B/CMakeCache.txt
echo "== new installed md5s"
md5sum $HOME/opt/fgo_cpp/bin/*
echo "== forced-gate symbols/strings in installed binaries (expect 0)"
for b in $HOME/opt/fgo_cpp/bin/*; do echo "$(basename $b) $(strings $b | grep -c FORCED_GATE) $(nm -C $b 2>/dev/null | grep -c forced_gate_fire)"; done
# acceptance set (NEW directory), from the 2d dump (2d build outputs = switch-OFF outputs, ident_switch_off.txt)
[ -e $A ] && { echo "acceptance dir exists already: $A"; exit 4; }
mkdir -p $A
cp $D/dsn_tex_r1_baseline.init.json $D/dsn_tex_r1_baseline.events.f64 $D/dsn_tex_r1_baseline.raw.f64 \
   $D/cpp_dsn_tex_r1_baseline.kf.f64 $D/cpp_dsn_tex_r1_baseline.yawgate.f64 $D/L1.kf.f64 $S/live/dsn_tex_r1.dj.tape $A/
(cd $A && sha256sum * > SHA256SUMS && cat SHA256SUMS)
O=$(mktemp -d -p $S)
(cd $A && sha256sum -c --quiet SHA256SUMS && echo "inputs OK")
$HOME/opt/fgo_cpp/bin/fgo_cpp_replay $A/dsn_tex_r1_baseline $O/accept >/dev/null 2>&1 && cmp $A/cpp_dsn_tex_r1_baseline.kf.f64 $O/accept.kf.f64 && cmp $A/cpp_dsn_tex_r1_baseline.yawgate.f64 $O/accept.yawgate.f64 && echo "ACCEPT replay"
$HOME/opt/fgo_cpp/bin/fgo_cpp_live_replay $A/dsn_tex_r1.dj.tape $A/dsn_tex_r1_baseline.init.json $O/L1 --imu-stamp header --arm-source param --delay 0.20 >/dev/null 2>&1 && cmp $A/L1.kf.f64 $O/L1.kf.f64 && echo "ACCEPT live (node path)"
