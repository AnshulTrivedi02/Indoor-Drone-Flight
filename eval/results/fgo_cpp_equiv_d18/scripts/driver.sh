#!/bin/bash
# D18 equivalence re-check (item 2d): every step through heavy.py, one bounded step each, in the yaw-gate stage's order
# (fgo_cpp_equiv_yawgate/scripts/driver.sh) minus the free-inertial runs (not bands). Bounded by DEADLINE.
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
Y=$S/d18
SC=/home/makerspace/thesis_ws/.claude/worktrees/agent-a16391ff0a1144fd8/eval/results/fgo_cpp_equiv_d18/scripts
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
DEADLINE=$(( $(date +%s) + ${DRIVER_HOURS:-5} * 3600 ))
L=$S/live
mkdir -p $Y/logs
run() {   # run <name> <args...>
  local name=$1; shift
  local left=$(( DEADLINE - $(date +%s) ))
  if [ $left -le 60 ]; then echo "[driver] $(date +%T) SKIP $name (time box)"; return 75; fi
  echo "[driver] $(date +%T) START $name"
  $HEAVY --wait-s $left "d18 equiv $name" -- bash $SC/step.sh "$@" > $Y/logs/$name.log 2>&1
  local rc=$?
  echo "[driver] $(date +%T) END $name rc=$rc"
  return $rc
}
run build build || { echo "[driver] build failed"; exit 1; }
run probe probe
run py_dsn_tex pycorr dsn_tex_r1 baseline && {
  run cpp_dsn_tex cpp dsn_tex_r1_baseline && {
    run fe_dsn_tex fe dsn_tex_r1_baseline
    run L1 live L1 $L/dsn_tex_r1.dj.tape dsn_tex_r1_baseline
  }
}
run py_fwdc pycorr fwdc_tex_r1 heading && {
  run cpp_fwdc cpp fwdc_tex_r1_heading && {
    run fe_fwdc fe fwdc_tex_r1_heading
    run L2 live L2 $L/fwdc_tex_r1.dj.tape fwdc_tex_r1_heading --heading --heading-sigma-rad 0.0025830872929516074
  }
}
for t in T_A_r1 T_D_r1; do
  run py_$t pyroom $t && { run cpp_$t cpp $t --rows anchored && run fe_$t fe $t; }
done
for t in dsn_blank_r1 dsn_trans_r1; do
  run py_$t pycorr $t baseline && run cpp_$t cpp ${t}_baseline
done
run py_O_r1 pyroom O_r1 --gnss && run cpp_O_r1 cpp O_r1 --rows anchored
run emu_build emu_build && run emu_dsn_tex_r1 emu dsn_tex_r1_baseline
echo "[driver] $(date +%T) ALL DONE"
