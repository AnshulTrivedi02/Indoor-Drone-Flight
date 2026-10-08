#!/bin/bash
# POST-HOC DIAGNOSTIC (not a pre-registered band): emulate-gemv build, replays on blank/trans exports.
set -euo pipefail
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
B=$S/binit0; SRC=$B/src/estimators; BE=$B/build_emu; D=$B/dump
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
case $1 in
build)
  env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "cmake -S $SRC/fgo_cpp -B $BE -DCMAKE_BUILD_TYPE=Release -DFGO_CPP_EMULATE_NUMPY_GEMV=ON -DFGO_CPP_BUILD_ROS=OFF && make -C $BE -j4 fgo_cpp_replay"
  ;;
replay)
  p=$2
  $BE/fgo_cpp_replay $D/$p $D/emu_$p
  $HOME/venv-fgo/bin/python $SRC/fgo_cpp/tools/compare_kf.py $D/$p $D/emu_$p
  echo "per-keyframe export bit-identical: $(cmp -s $D/$p.kf.f64 $D/emu_$p.kf.f64 && echo yes || echo no)"
  ;;
esac
