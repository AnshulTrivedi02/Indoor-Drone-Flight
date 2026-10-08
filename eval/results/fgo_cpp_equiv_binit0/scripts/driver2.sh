#!/bin/bash
# fwdc chain re-run (the first attempt failed: fwd_calibration.json missing in the scratch tree)
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
B=$S/binit0
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
DEADLINE=$(date -d "2026-10-09 06:05" +%s)
run() {
  local name=$1; shift
  local left=$(( DEADLINE - $(date +%s) ))
  if [ $left -le 60 ]; then echo "[driver2] $(date +%T) SKIP $name (time box)"; return 75; fi
  echo "[driver2] $(date +%T) START $name"
  $HEAVY --wait-s $left "binit0 $name" -- bash $B/step.sh "$@" > $B/logs/$name.log 2>&1
  local rc=$?
  echo "[driver2] $(date +%T) END $name rc=$rc"
  return $rc
}
L=$S/live
run py_fwdc pycorr fwdc_tex_r1 heading && {
  run cpp_fwdc cpp fwdc_tex_r1_heading && {
    run fe_fwdc fe fwdc_tex_r1_heading
    run L2 live L2 $L/fwdc_tex_r1.dj.tape fwdc_tex_r1_heading --heading --heading-sigma-rad 0.0025830872929516074
  }
}
echo "[driver2] $(date +%T) ALL DONE"
