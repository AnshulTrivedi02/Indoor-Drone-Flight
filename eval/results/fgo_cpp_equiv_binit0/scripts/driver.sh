#!/bin/bash
# binit0 equivalence driver: every step through heavy.py (one bounded step each). Stops at the first failed step
# of a chain only where later steps depend on it.
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
B=$S/binit0
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
DEADLINE=$(date -d "2026-10-09 06:05" +%s)
mkdir -p $B/logs
run() {   # run <name> <step args...>
  local name=$1; shift
  local left=$(( DEADLINE - $(date +%s) ))
  if [ $left -le 60 ]; then echo "[driver] $(date +%T) SKIP $name (time box)"; return 75; fi
  echo "[driver] $(date +%T) START $name"
  $HEAVY --wait-s $left "binit0 $name" -- bash $B/step.sh "$@" > $B/logs/$name.log 2>&1
  local rc=$?
  echo "[driver] $(date +%T) END $name rc=$rc"
  return $rc
}
L=$S/live
run build build || { echo "[driver] build failed"; exit 1; }
run probe probe
# 1. dsn_tex_r1: band A, C, L1
run py_dsn_tex pycorr dsn_tex_r1 baseline && {
  run cpp_dsn_tex cpp dsn_tex_r1_baseline && {
    run fe_dsn_tex fe dsn_tex_r1_baseline
    run L1 live L1 $L/dsn_tex_r1.dj.tape dsn_tex_r1_baseline
  }
}
# 2. T_A_r1, T_D_r1: band B2-B5, C
for t in T_A_r1 T_D_r1; do
  run py_$t pyroom $t && { run cpp_$t cpp $t --rows anchored && run fe_$t fe $t; }
done
# 3. fwdc_tex_r1 heading: B1, C, L2
run py_fwdc pycorr fwdc_tex_r1 heading && {
  run cpp_fwdc cpp fwdc_tex_r1_heading && {
    run fe_fwdc fe fwdc_tex_r1_heading
    run L2 live L2 $L/fwdc_tex_r1.dj.tape fwdc_tex_r1_heading --heading --heading-sigma-rad 0.0025830872929516074
  }
}
# 4. band A blank, trans
for t in dsn_blank_r1 dsn_trans_r1; do
  run py_$t pycorr $t baseline && run cpp_$t cpp ${t}_baseline
done
# 5. B6 (optional): O_r1 GNSS
run py_O_r1 pyroom O_r1 --gnss && run cpp_O_r1 cpp O_r1 --rows anchored
echo "[driver] $(date +%T) ALL DONE"
