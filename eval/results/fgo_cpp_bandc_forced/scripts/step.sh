#!/bin/bash
# Band C forced-decision stage (ruling 2026-10-11 item 1). One bounded heavy step; run ONLY through heavy.py.
# Inputs: the 2d dump ($S/d18/dump, READ ONLY). Outputs: $S/bcf/. Usage: step.sh <step> [args]
set -euo pipefail
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
WT=/home/makerspace/thesis_ws/.claude/worktrees/agent-a77df11041902ee58
SRC=$WT/src/estimators
SC=$WT/eval/results/fgo_cpp_bandc_forced/scripts
SC2D=$WT/eval/results/fgo_cpp_equiv_d18/scripts
D=$S/d18/dump                 # read only
Y=$S/bcf
BUILD=$Y/build                # default build (switch OFF): control (HEAD b908abf) then the switch source
BF=$Y/build_forced            # -DFGO_CPP_FORCED_GATE=ON, no ROS
O=$Y/out
TOOLS=$SRC/fgo_cpp/tools
PY=$HOME/venv-fgo/bin/python
PYA=$HOME/venv-ardupilot/bin/python
mkdir -p $O
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
step=$1; shift || true
case $step in
build)        # build <tag>: default build (ROS on), md5s saved as $Y/md5_<tag>.txt, binaries copied to $Y/bin_<tag>/
  tag=$1
  env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "source /opt/ros/jazzy/setup.bash && cmake -S $SRC/fgo_cpp -B $BUILD -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$Y/install_unused -DPython3_EXECUTABLE=/usr/bin/python3 '-DCMAKE_PREFIX_PATH=/opt/ros/jazzy;$HOME/thesis_ws/install/optical_flow_interfaces' && make -C $BUILD -j4"
  mkdir -p $Y/bin_$tag
  for b in fgo_cpp_node fgo_cpp_replay fgo_cpp_live_replay fgo_cpp_frontend fgo_cpp_probe; do cp $BUILD/$b $Y/bin_$tag/; done
  (cd $Y/bin_$tag && md5sum *) | tee $Y/md5_$tag.txt
  ;;
build_forced)
  env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "cmake -S $SRC/fgo_cpp -B $BF -DCMAKE_BUILD_TYPE=Release -DFGO_CPP_FORCED_GATE=ON -DFGO_CPP_BUILD_ROS=OFF && make -C $BF -j4 fgo_cpp_replay fgo_cpp_frontend"
  md5sum $BF/fgo_cpp_replay $BF/fgo_cpp_frontend
  ;;
ident)        # ident <tag>: replay + front end on the four Band C bags, and L1, with $Y/bin_<tag>; outputs $O/<tag>/
  tag=$1; B=$Y/bin_$tag; OT=$O/$tag; mkdir -p $OT
  for p in dsn_tex_r1_baseline fwdc_tex_r1_heading T_A_r1 T_D_r1; do
    $B/fgo_cpp_replay $D/$p $OT/cpp_$p > $OT/cpp_$p.stdout
    $B/fgo_cpp_frontend $D/$p $OT/fe_$p > $OT/fe_$p.stdout
  done
  $B/fgo_cpp_live_replay $S/live/dsn_tex_r1.dj.tape $D/dsn_tex_r1_baseline.init.json $OT/L1 --imu-stamp header --arm-source param --delay 0.20 > $OT/L1.stdout
  ;;
forced)       # forced <prefix>: forced replay + forced front end, decisions from Python's <prefix>.yawgate.f64
  p=$1; OT=$O/forced; mkdir -p $OT
  export FGO_CPP_FORCED_GATE_LOG=$D/$p.yawgate.f64
  $BF/fgo_cpp_replay $D/$p $OT/cpp_$p
  $BF/fgo_cpp_frontend $D/$p $OT/fe_$p
  unset FGO_CPP_FORCED_GATE_LOG
  echo "==== construction check: Python vs forced export-driven C++"
  $PY $SC2D/cmp_gate.py $D/$p.yawgate.f64 $OT/cpp_$p.yawgate.f64 || true
  echo "==== construction check: Python vs forced front end"
  $PY $SC2D/cmp_gate.py $D/$p.yawgate.f64 $OT/fe_$p.yawgate.f64 || true
  echo "==== FORCED BAND C: forced export-driven C++ vs forced native front end"
  $PY $TOOLS/compare_kf.py $OT/cpp_$p $OT/fe_$p || true
  echo "==== positive control: forced export-driven C++ vs unforced (2d build 0981e455) cpp_$p"
  echo "kf bit-identical: $(cmp -s $OT/cpp_$p.kf.f64 $D/cpp_$p.kf.f64 && echo yes || echo no)"
  $PY $TOOLS/compare_kf.py $D/cpp_$p $OT/cpp_$p || true
  ;;
*) echo "unknown step $step"; exit 2;;
esac
