#!/bin/bash
# yaw-cap-gate stage (continuation, fresh): every step through heavy.py, one bounded step each, in priority order.
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
Y=$S/yawgate2
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
DEADLINE=$(date -d "2026-10-09 15:10" +%s)
L=$S/live
run() {   # run <name> <script> <args...>
  local name=$1 sc=$2; shift 2
  local left=$(( DEADLINE - $(date +%s) ))
  if [ $left -le 60 ]; then echo "[driver] $(date +%T) SKIP $name (time box)"; return 75; fi
  echo "[driver] $(date +%T) START $name"
  $HEAVY --wait-s $left "yawgate2 $name" -- bash $Y/$sc "$@" > $Y/logs/$name.log 2>&1
  local rc=$?
  echo "[driver] $(date +%T) END $name rc=$rc"
  return $rc
}
run build step.sh build || { echo "[driver] build failed"; exit 1; }
run probe step.sh probe
run fi10 step2.sh fi10
run fi60 step2.sh fi60
run py_dsn_tex step.sh pycorr dsn_tex_r1 baseline && {
  run cpp_dsn_tex step.sh cpp dsn_tex_r1_baseline && {
    run fe_dsn_tex step.sh fe dsn_tex_r1_baseline
    run L1 step.sh live L1 $L/dsn_tex_r1.dj.tape dsn_tex_r1_baseline
  }
}
run py_fwdc step.sh pycorr fwdc_tex_r1 heading && {
  run cpp_fwdc step.sh cpp fwdc_tex_r1_heading && {
    run fe_fwdc step.sh fe fwdc_tex_r1_heading
    run L2 step.sh live L2 $L/fwdc_tex_r1.dj.tape fwdc_tex_r1_heading --heading --heading-sigma-rad 0.0025830872929516074
  }
}
for t in dsn_blank_r1 dsn_trans_r1; do
  run py_$t step.sh pycorr $t baseline && run cpp_$t step.sh cpp ${t}_baseline
done
run emu_build step.sh emu_build && for t in dsn_blank_r1 dsn_trans_r1 dsn_tex_r1; do run emu_$t step.sh emu ${t}_baseline; done
for t in T_A_r1 T_D_r1; do
  run py_$t step.sh pyroom $t && { run cpp_$t step.sh cpp $t --rows anchored && run fe_$t step.sh fe $t; }
done
run py_O_r1 step.sh pyroom O_r1 --gnss && run cpp_O_r1 step.sh cpp O_r1 --rows anchored
echo "[driver] $(date +%T) ALL DONE"
