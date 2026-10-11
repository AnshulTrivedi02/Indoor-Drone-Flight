#!/bin/bash
# Item 2f (FGO Pi path): ONE bounded step of the aarch64 cross-build of GTSAM 4.2.1 + the C++ FGO, and of its
# emulated (qemu-user) correctness check against the x86 scratch build of item 2d. Run the heavy steps ONLY through
#   python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "<desc>" -- bash <this file> <step> [args]
# Build products stay in scratch ($A); nothing is installed. Source: this worktree (fwd-camera; src/estimators
# identical to cca8e90, the source of the x86 scratch build 28636bf9 / replay 0981e455).
set -euo pipefail
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
A=$S/arm64
WT=/home/makerspace/thesis_ws/.claude/worktrees/agent-abdbe0a2aa823633d
SRC=$WT/src/estimators
SC=$WT/eval/results/fgo_cpp_arm64/scripts
SC2=$WT/eval/results/fgo_cpp_equiv_d18/scripts
TC=$SC/aarch64.toolchain.cmake
export ARM_SYSROOT_EXTRA=$A/sysroot
export ARM_PREFIX=$A/gtsam-4.2.1
GS=$HOME/opt/src/gtsam-4.2.1          # the same GTSAM 4.2.1 source tree the x86 build used (read only)
GB=$A/build-gtsam
FB=$A/build-fgo
D=$S/d18/dump                          # Python exports + x86 C++ outputs of item 2d (read only)
OUT=$A/out
PY=$HOME/venv-fgo/bin/python
QEMU="qemu-aarch64 -L /usr/aarch64-linux-gnu"
export QEMU_LD_PREFIX=/usr/aarch64-linux-gnu
RUNLIB=$ARM_PREFIX/lib:$A/sysroot/usr/lib/aarch64-linux-gnu
mkdir -p $OUT
step=$1; shift || true
case $step in
gtsam_configure)   # flags copied from ~/opt/src/configure_gtsam.sh (x86), plus the toolchain file
  env -i HOME=$HOME PATH=/usr/bin:/bin ARM_SYSROOT_EXTRA=$ARM_SYSROOT_EXTRA ARM_PREFIX=$ARM_PREFIX \
    cmake -S $GS -B $GB -DCMAKE_TOOLCHAIN_FILE=$TC -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$ARM_PREFIX \
    -DGTSAM_WITH_TBB=OFF -DGTSAM_USE_SYSTEM_EIGEN=OFF -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF \
    -DGTSAM_BUILD_UNSTABLE=ON -DGTSAM_BUILD_PYTHON=OFF -DGTSAM_UNSTABLE_BUILD_PYTHON=OFF \
    -DGTSAM_BUILD_TESTS=OFF -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF -DGTSAM_BUILD_TIMING_ALWAYS=OFF \
    -DGTSAM_BUILD_DOCS=OFF -DGTSAM_BUILD_WITH_CCACHE=OFF -DGTSAM_INSTALL_MATLAB_TOOLBOX=OFF \
    -DBoost_DIR=$A/sysroot/usr/lib/aarch64-linux-gnu/cmake/Boost-1.83.0
  ;;
gtsam_build)
  env -i HOME=$HOME PATH=/usr/bin:/bin make -C $GB -j4 gtsam gtsam_unstable
  env -i HOME=$HOME PATH=/usr/bin:/bin make -C $GB install
  echo GTSAM_ARM_OK
  ;;
fgo_build)         # replay, live_replay, frontend, probe (no ROS node: no ROS 2 Jazzy arm64 here); rpath stripped
  env -i HOME=$HOME PATH=/usr/bin:/bin ARM_SYSROOT_EXTRA=$ARM_SYSROOT_EXTRA ARM_PREFIX=$ARM_PREFIX \
    cmake -S $SRC/fgo_cpp -B $FB -DCMAKE_TOOLCHAIN_FILE=$TC -DCMAKE_BUILD_TYPE=Release \
    -DGTSAM_DIR=$ARM_PREFIX/lib/cmake/GTSAM -DGTSAM_UNSTABLE_DIR=$ARM_PREFIX/lib/cmake/GTSAM_UNSTABLE \
    -DBoost_DIR=$A/sysroot/usr/lib/aarch64-linux-gnu/cmake/Boost-1.83.0 \
    -DFGO_CPP_BUILD_ROS=OFF -DCMAKE_SKIP_RPATH=ON
  env -i HOME=$HOME PATH=/usr/bin:/bin make -C $FB -j4 fgo_cpp_replay fgo_cpp_live_replay fgo_cpp_frontend fgo_cpp_probe
  md5sum $FB/fgo_cpp_replay $FB/fgo_cpp_live_replay $FB/fgo_cpp_frontend $FB/fgo_cpp_probe
  ;;
probe)             # factor-level numerics: arm C++ probe vs the x86 C++ probe of 2d (and vs Python)
  LD_LIBRARY_PATH=$RUNLIB $QEMU $FB/fgo_cpp_probe > $OUT/probe_cpp_arm64.txt
  echo "==== arm64 C++ probe vs x86 C++ probe (2d, d18/dump/probe_cpp.txt)"
  $PY $SRC/fgo_cpp/tools/compare_probe.py $D/probe_cpp.txt $OUT/probe_cpp_arm64.txt || true
  echo "==== arm64 C++ probe vs Python probe (2d, d18/dump/probe_py.txt)"
  $PY $SRC/fgo_cpp/tools/compare_probe.py $D/probe_py.txt $OUT/probe_cpp_arm64.txt || true
  ;;
replay)            # export-driven replay under qemu: replay <prefix>; compared with the x86 C++ output cpp_<prefix>
  p=$1
  /usr/bin/time -v env LD_LIBRARY_PATH=$RUNLIB $QEMU $FB/fgo_cpp_replay $D/$p $OUT/arm_$p 2> $OUT/arm_$p.time.txt
  tail -25 $OUT/arm_$p.time.txt
  echo "==== arm64 C++ vs x86 C++ (cpp_$p, 2d scratch build replay 0981e455)"
  $PY $SRC/fgo_cpp/tools/compare_kf.py $D/cpp_$p $OUT/arm_$p || true
  echo "per-keyframe export bit-identical: $(cmp -s $D/cpp_$p.kf.f64 $OUT/arm_$p.kf.f64 && echo yes || echo no)"
  echo "==== yaw-cap gate: x86 C++ vs arm64 C++"
  $PY $SC2/cmp_gate.py $D/cpp_$p.yawgate.f64 $OUT/arm_$p.yawgate.f64 || true
  echo "==== onset (before / after the first gate decision mismatch)"
  $PY $SC/onset_arm.py $D/cpp_$p $OUT/arm_$p || true
  echo "==== arm64 C++ vs the Python export ($p)"
  $PY $SRC/fgo_cpp/tools/compare_kf.py $D/$p $OUT/arm_$p || true
  ;;
live)              # live adapter (the flown node's path, live_adapter.cpp) under qemu, same args as 2d band L1:
                   # live <row> <tape> <prefix>; compared with the x86 adapter output d18/dump/<row> and cpp_<prefix>
  row=$1; tape=$2; p=$3
  /usr/bin/time -v env LD_LIBRARY_PATH=$RUNLIB $QEMU $FB/fgo_cpp_live_replay $tape $D/$p.init.json $OUT/arm_$row \
    --imu-stamp header --arm-source param --delay 0.20 2> $OUT/arm_$row.time.txt
  grep -E "Maximum resident|Elapsed" $OUT/arm_$row.time.txt
  echo "==== arm64 live adapter vs x86 live adapter ($row): files bit-identical?"
  for e in kf.f64 live.f64 mav.bin; do echo "$e: $(cmp -s $D/$row.$e $OUT/arm_$row.$e && echo yes || echo no)"; done
  echo "==== arm64 live adapter checked by compare_live.py against the x86 export-driven C++ cpp_$p"
  $HOME/venv-ardupilot/bin/python $SRC/fgo_cpp/tools/compare_live.py $tape $OUT/arm_$row $D/cpp_$p || true
  echo "==== arm64 live kf vs x86 live kf ($row)"
  $PY $SRC/fgo_cpp/tools/compare_kf.py $D/$row $OUT/arm_$row || true
  ;;
*) echo "unknown step $step"; exit 2;;
esac
