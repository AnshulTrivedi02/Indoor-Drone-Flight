#!/bin/bash
# One bounded heavy step of the binit0 equivalence re-check. Run ONLY through heavy.py.
# Usage: step.sh <step> [args]
set -euo pipefail
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
B=$S/binit0
SRC=$B/src/estimators            # PATCHED scratch copy (both cores corrected)
BUILD=$B/build
D=$B/dump
OUT=$B/out
LOG=$B/logs
TOOLS=$SRC/fgo_cpp/tools
PY=$HOME/venv-fgo/bin/python
PYA=$HOME/venv-ardupilot/bin/python
mkdir -p $D $OUT $LOG
# never write into the trial directories: bags from scratch copies, outputs to scratch
export FGO_BAG_ROOT=$S/bags
export FGO_OUT_ROOT=$OUT
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

step=$1; shift || true
case $step in
build)
  env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "source /opt/ros/jazzy/setup.bash && cmake -S $SRC/fgo_cpp -B $BUILD -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$B/install_unused -DPython3_EXECUTABLE=/usr/bin/python3 '-DCMAKE_PREFIX_PATH=/opt/ros/jazzy;$HOME/thesis_ws/install/optical_flow_interfaces' && make -C $BUILD -j4"
  md5sum $BUILD/fgo_cpp_node $BUILD/fgo_cpp_live_replay $BUILD/fgo_cpp_replay $BUILD/fgo_cpp_frontend $BUILD/fgo_cpp_probe
  ;;
probe)
  $PY $TOOLS/fgo_cpp_probe.py > $D/probe_py.txt
  $BUILD/fgo_cpp_probe > $D/probe_cpp.txt
  $PY $TOOLS/compare_probe.py $D/probe_py.txt $D/probe_cpp.txt
  echo "--- new python probe vs OLD python probe (expect the preintegration covariance to differ)"
  $PY $TOOLS/compare_probe.py $S/probe_py.txt $D/probe_py.txt || true
  ;;
pycorr)      # corridor Python reference + export: pycorr <trial> <arm>
  t=$1; arm=$2
  FGO_DUMP_EVENTS=$D/${t}_$arm $PY $SRC/fgo/fgo_replay.py $t 0.25 2 $arm
  ;;
pyroom)      # room Python reference + export (live + batch): pyroom <trial> [--gnss]
  t=$1; shift
  FGO_DUMP_EVENTS=$D/${t} $PY $SRC/fgo/room_fgo_replay.py $t "$@"
  ;;
cpp)         # export-driven C++ replay + band A/B comparison: cpp <prefix> [--rows anchored]
  p=$1; shift
  $BUILD/fgo_cpp_replay $D/$p $D/cpp_$p
  echo "==== band A/B: Python export $p vs C++ replay (all rows)"
  $PY $TOOLS/compare_kf.py $D/$p $D/cpp_$p
  if [ "${1:-}" = "--rows" ]; then
    echo "==== band B: anchored rows"
    $PY $TOOLS/compare_kf.py $D/$p $D/cpp_$p --rows anchored
  fi
  echo "per-keyframe export bit-identical: $(cmp -s $D/$p.kf.f64 $D/cpp_$p.kf.f64 && echo yes || echo no)"
  ;;
fe)          # native front end vs export-driven C++ (band C): fe <prefix>
  p=$1
  $BUILD/fgo_cpp_frontend $D/$p $D/fe_$p
  echo "==== band C: export-driven C++ cpp_$p vs native front end fe_$p"
  $PY $TOOLS/compare_kf.py $D/cpp_$p $D/fe_$p
  echo "==== stream diagnostics: Python export vs front end"
  $PY $TOOLS/compare_stream.py $D/$p $D/fe_$p
  ;;
live)        # band L: live <row> <tape> <prefix> [extra adapter args]
  row=$1; tape=$2; p=$3; shift 3
  $BUILD/fgo_cpp_live_replay $tape $D/$p.init.json $D/$row --imu-stamp header --arm-source param --delay 0.20 "$@"
  echo "==== band $row: live adapter vs export-driven C++ cpp_$p"
  $PYA $TOOLS/compare_live.py $tape $D/$row $D/cpp_$p
  ;;
*) echo "unknown step $step"; exit 2;;
esac
