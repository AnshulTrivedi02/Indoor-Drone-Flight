#!/bin/bash
# POST-HOC DIAGNOSTIC steps + the 60 s free-inertial run (run ONLY through heavy.py).
#   forced <prefix> <script> <args...> : Python replay with the gate decisions forced to cpp_<prefix>'s, vs cpp_<prefix>
#   fi60                              : free_inertial.py 60 s
set -euo pipefail
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
Y=$S/yawgate2
SRC=/home/makerspace/thesis_ws/.claude/worktrees/agent-aa29cfc08768a86c5/src/estimators
D=$Y/dump
PY=$HOME/venv-fgo/bin/python
export FGO_BAG_ROOT=$S/bags
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
case $1 in
forced)
  p=$2; script=$3; shift 3
  FGO_OUT_ROOT=$Y/out_forced FGO_DUMP_EVENTS=$D/forced_$p $PY $Y/forced_gate.py $D/cpp_$p.yawgate.f64 $SRC/fgo/$script "$@"
  echo "==== POST-HOC: Python with the C++ gate decisions forced vs C++ replay cpp_$p"
  $PY $SRC/fgo_cpp/tools/compare_kf.py $D/forced_$p $D/cpp_$p
  if [ "$script" = "room_fgo_replay.py" ]; then $PY $SRC/fgo_cpp/tools/compare_kf.py $D/forced_$p $D/cpp_$p --rows anchored; fi
  $PY $Y/cmp_gate.py $D/forced_$p.yawgate.f64 $D/cpp_$p.yawgate.f64 || true
  ;;
forcedemu)
  p=$2; script=$3; shift 3
  FGO_OUT_ROOT=$Y/out_forcedemu FGO_DUMP_EVENTS=$D/forcedemu_$p $PY $Y/forced_gate.py $D/emu_$p.yawgate.f64 $SRC/fgo/$script "$@"
  echo "==== POST-HOC: Python with the emulate-gemv C++ gate decisions forced vs emu_$p"
  $PY $SRC/fgo_cpp/tools/compare_kf.py $D/forcedemu_$p $D/emu_$p
  echo "per-keyframe export bit-identical: $(cmp -s $D/forcedemu_$p.kf.f64 $D/emu_$p.kf.f64 && echo yes || echo no)"
  $PY $Y/cmp_gate.py $D/forcedemu_$p.yawgate.f64 $D/emu_$p.yawgate.f64 || true
  ;;
fi60)
  bash $Y/fi.sh 60 fi60
  ;;
fi10)
  bash $Y/fi.sh 10 fi10
  ;;
esac
