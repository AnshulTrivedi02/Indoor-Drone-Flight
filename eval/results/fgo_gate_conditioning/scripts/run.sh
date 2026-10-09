#!/bin/bash
# Gate-conditioning diagnostic (run ONLY through heavy.py). Scratch builds/outputs only.
set -uo pipefail
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
G=$S/gatecond
D=$S/yawgate2/dump
SRC=/home/makerspace/thesis_ws/.claude/worktrees/agent-a9aad2e9b298caf92/src/estimators
PY=$HOME/venv-fgo/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export FGO_BAG_ROOT=$S/bags
P=dsn_tex_r1_baseline
mkdir -p $G/out $G/pyout
echo "== build emu + default (patched scratch copy, replay target only) $(date +%T)"
env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "cmake -S $G/src_fgo_cpp -B $G/build_emu -DCMAKE_BUILD_TYPE=Release -DFGO_CPP_EMULATE_NUMPY_GEMV=ON -DFGO_CPP_BUILD_ROS=OFF >/dev/null && make -C $G/build_emu -j4 fgo_cpp_replay 2>&1 | tail -2" || exit 1
env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "cmake -S $G/src_fgo_cpp -B $G/build_def -DCMAKE_BUILD_TYPE=Release -DFGO_CPP_BUILD_ROS=OFF >/dev/null && make -C $G/build_def -j4 fgo_cpp_replay 2>&1 | tail -2" || exit 1
echo "== C++ emu replay $(date +%T)"
FGO_CONDDUMP=$G/out/emu.cond.f64 $G/build_emu/fgo_cpp_replay $D/$P $G/out/emu_$P
echo "non-perturbing (emu kf vs existing emu_): $(cmp -s $G/out/emu_$P.kf.f64 $D/emu_$P.kf.f64 && echo identical || echo DIFFERENT)"
echo "non-perturbing (emu yawgate vs existing): $(cmp -s $G/out/emu_$P.yawgate.f64 $D/emu_$P.yawgate.f64 && echo identical || echo DIFFERENT)"
echo "== C++ default replay $(date +%T)"
FGO_CONDDUMP=$G/out/def.cond.f64 $G/build_def/fgo_cpp_replay $D/$P $G/out/def_$P
echo "default kf vs existing cpp_: $(cmp -s $G/out/def_$P.kf.f64 $D/cpp_$P.kf.f64 && echo identical || echo DIFFERENT)"
echo "default yawgate vs existing cpp_: $(cmp -s $G/out/def_$P.yawgate.f64 $D/cpp_$P.yawgate.f64 && echo identical || echo DIFFERENT)"
echo "== Python forced to emu decisions $(date +%T)"
FGO_OUT_ROOT=$G/pyout FGO_DUMP_EVENTS=$G/out/pyemu_$P $PY $G/py_conddump.py $D/emu_$P.yawgate.f64 $G/out/pyemu $SRC/fgo/fgo_replay.py dsn_tex_r1 0.25 2 baseline > $G/out/pyemu.log 2>&1
echo "non-perturbing (py-forced-emu kf vs existing forcedemu_): $(cmp -s $G/out/pyemu_$P.kf.f64 $D/forcedemu_$P.kf.f64 && echo identical || echo DIFFERENT)"
echo "py-forced-emu kf vs C++ emu kf: $(cmp -s $G/out/pyemu_$P.kf.f64 $G/out/emu_$P.kf.f64 && echo identical || echo DIFFERENT)"
echo "== Python forced to default-build decisions $(date +%T)"
FGO_OUT_ROOT=$G/pyout FGO_DUMP_EVENTS=$G/out/pydef_$P $PY $G/py_conddump.py $D/cpp_$P.yawgate.f64 $G/out/pydef $SRC/fgo/fgo_replay.py dsn_tex_r1 0.25 2 baseline > $G/out/pydef.log 2>&1
echo "non-perturbing (py-forced-def kf vs existing forced_): $(cmp -s $G/out/pydef_$P.kf.f64 $D/forced_$P.kf.f64 && echo identical || echo DIFFERENT)"
echo "== done $(date +%T)"
